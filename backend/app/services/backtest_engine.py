import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from decimal import Decimal
from app.core.config import settings
from app.core.logging import logger
from app.models.stock import StockPrice, StockFeature
from app.models.backtest import Backtest, BacktestStatus, StrategyType
from app.models.portfolio import Trade, TradeAction, TradeStatus
from app.services.technical_analysis import technical_analysis_service

class BacktestEngine:
    def __init__(self):
        self.strategies = {
            StrategyType.MOVING_AVERAGE: self._moving_average_strategy,
            StrategyType.RSI_DIVERGENCE: self._rsi_divergence_strategy,
            StrategyType.MACD_CROSSOVER: self._macd_crossover_strategy,
            StrategyType.BOLLINGER_BANDS: self._bollinger_bands_strategy,
            StrategyType.ML_SIGNALS: self._ml_signals_strategy,
        }
    
    async def run_backtest(self, db: AsyncSession, backtest_id: int) -> Dict[str, Any]:
        """Run a complete backtest"""
        
        backtest = await db.get(Backtest, backtest_id)
        if not backtest:
            raise ValueError(f"Backtest {backtest_id} not found")
        
        try:
            # Update status
            backtest.status = BacktestStatus.RUNNING
            backtest.started_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Starting backtest: {backtest.name} ({backtest.id})")
            
            # Prepare data
            data = await self._prepare_backtest_data(db, backtest)
            
            # Run strategy
            strategy_func = self.strategies.get(backtest.strategy_type)
            if not strategy_func:
                raise ValueError(f"Unknown strategy type: {backtest.strategy_type}")
            
            results = await strategy_func(data, backtest)
            
            # Calculate performance metrics
            metrics = self._calculate_performance_metrics(results)
            
            # Update backtest with results
            await self._update_backtest_results(db, backtest, results, metrics)
            
            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Backtest completed: {backtest.name} - Return: {metrics['total_return']:.2f}%")
            
            return {
                'backtest_id': backtest_id,
                'status': 'completed',
                'metrics': metrics,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error running backtest {backtest_id}: {e}")
            backtest.status = BacktestStatus.FAILED
            backtest.error_message = str(e)
            backtest.completed_at = datetime.utcnow()
            await db.commit()
            raise
    
    async def _prepare_backtest_data(self, db: AsyncSession, backtest: Backtest) -> Dict[str, Any]:
        """Prepare data for backtesting"""
        
        symbols = backtest.symbols or []
        start_date = backtest.start_date
        end_date = backtest.end_date
        
        data = {
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': backtest.initial_capital,
            'data': {}
        }
        
        # Fetch price data for all symbols
        for symbol in symbols:
            result = await db.execute(
                select(StockPrice)
                .where(
                    and_(
                        StockPrice.symbol == symbol,
                        StockPrice.date >= start_date,
                        StockPrice.date <= end_date
                    )
                )
                .order_by(StockPrice.date)
            )
            
            prices = result.scalars().all()
            
            if prices:
                df = pd.DataFrame([
                    {
                        'date': p.date,
                        'open': p.open,
                        'high': p.high,
                        'low': p.low,
                        'close': p.close,
                        'volume': p.volume
                    }
                    for p in prices
                ])
                
                # Calculate technical indicators
                df = technical_analysis_service.calculate_indicators(df)
                data['data'][symbol] = df
        
        return data
    
    async def _moving_average_strategy(self, data: Dict[str, Any], backtest: Backtest) -> Dict[str, Any]:
        """Moving Average Crossover Strategy"""
        
        config = backtest.strategy_config or {}
        short_ma = config.get('short_ma', 20)
        long_ma = config.get('long_ma', 50)
        
        trades = []
        equity_curve = []
        portfolio_value = backtest.initial_capital
        positions = {}
        
        # Get all trading days
        all_dates = set()
        for symbol, df in data['data'].items():
            all_dates.update(df['date'].tolist())
        
        trading_dates = sorted(list(all_dates))
        
        for current_date in trading_dates:
            daily_trades = []
            
            for symbol, df in data['data'].items():
                # Get current data
                current_data = df[df['date'] == current_date]
                if current_data.empty:
                    continue
                
                row = current_data.iloc[0]
                current_price = row['close']
                sma_short = row.get(f'sma_{short_ma}')
                sma_long = row.get(f'sma_{long_ma}')
                
                if pd.isna(sma_short) or pd.isna(sma_long):
                    continue
                
                # Check for signals
                if symbol not in positions:
                    # Entry signal: short MA crosses above long MA
                    prev_data = df[df['date'] < current_date].tail(2)
                    if len(prev_data) >= 2:
                        prev_short = prev_data.iloc[-1][f'sma_{short_ma}']
                        prev_long = prev_data.iloc[-1][f'sma_{long_ma}']
                        
                        if (sma_short > sma_long and prev_short <= prev_long):
                            # Buy signal
                            trade = self._create_trade(
                                symbol=symbol,
                                action='BUY',
                                price=current_price,
                                date=current_date,
                                backtest=backtest
                            )
                            trades.append(trade)
                            daily_trades.append(trade)
                            positions[symbol] = trade
                
                else:
                    # Exit signal: short MA crosses below long MA
                    prev_data = df[df['date'] < current_date].tail(2)
                    if len(prev_data) >= 2:
                        prev_short = prev_data.iloc[-1][f'sma_{short_ma}']
                        prev_long = prev_data.iloc[-1][f'sma_{long_ma}']
                        
                        if (sma_short < sma_long and prev_short >= prev_long):
                            # Sell signal
                            trade = self._create_trade(
                                symbol=symbol,
                                action='SELL',
                                price=current_price,
                                date=current_date,
                                backtest=backtest
                            )
                            trades.append(trade)
                            daily_trades.append(trade)
                            del positions[symbol]
            
            # Update portfolio value
            if daily_trades:
                portfolio_value = self._update_portfolio_value(
                    portfolio_value, daily_trades, positions, data['data']
                )
            
            equity_curve.append({
                'date': current_date,
                'value': portfolio_value
            })
        
        # Close remaining positions at the end
        for symbol, position in positions.items():
            last_date = trading_dates[-1]
            last_price = data['data'][symbol][data['data'][symbol]['date'] == last_date]['close'].iloc[0]
            
            trade = self._create_trade(
                symbol=symbol,
                action='SELL',
                price=last_price,
                date=last_date,
                backtest=backtest
            )
            trades.append(trade)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_value': portfolio_value
        }
    
    async def _rsi_divergence_strategy(self, data: Dict[str, Any], backtest: Backtest) -> Dict[str, Any]:
        """RSI Divergence Strategy"""
        
        config = backtest.strategy_config or {}
        rsi_period = config.get('rsi_period', 14)
        rsi_oversold = config.get('rsi_oversold', 30)
        rsi_overbought = config.get('rsi_overbought', 70)
        
        trades = []
        equity_curve = []
        portfolio_value = backtest.initial_capital
        positions = {}
        
        all_dates = set()
        for symbol, df in data['data'].items():
            all_dates.update(df['date'].tolist())
        
        trading_dates = sorted(list(all_dates))
        
        for current_date in trading_dates:
            daily_trades = []
            
            for symbol, df in data['data'].items():
                current_data = df[df['date'] == current_date]
                if current_data.empty:
                    continue
                
                row = current_data.iloc[0]
                current_price = row['close']
                rsi = row.get(f'rsi_{rsi_period}')
                
                if pd.isna(rsi):
                    continue
                
                # Entry signals
                if symbol not in positions:
                    if rsi < rsi_oversold:
                        # Buy when RSI is oversold
                        trade = self._create_trade(
                            symbol=symbol,
                            action='BUY',
                            price=current_price,
                            date=current_date,
                            backtest=backtest
                        )
                        trades.append(trade)
                        daily_trades.append(trade)
                        positions[symbol] = trade
                
                else:
                    # Exit signals
                    if rsi > rsi_overbought:
                        # Sell when RSI is overbought
                        trade = self._create_trade(
                            symbol=symbol,
                            action='SELL',
                            price=current_price,
                            date=current_date,
                            backtest=backtest
                        )
                        trades.append(trade)
                        daily_trades.append(trade)
                        del positions[symbol]
            
            # Update portfolio value
            if daily_trades:
                portfolio_value = self._update_portfolio_value(
                    portfolio_value, daily_trades, positions, data['data']
                )
            
            equity_curve.append({
                'date': current_date,
                'value': portfolio_value
            })
        
        # Close remaining positions
        for symbol, position in positions.items():
            last_date = trading_dates[-1]
            last_price = data['data'][symbol][data['data'][symbol]['date'] == last_date]['close'].iloc[0]
            
            trade = self._create_trade(
                symbol=symbol,
                action='SELL',
                price=last_price,
                date=last_date,
                backtest=backtest
            )
            trades.append(trade)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_value': portfolio_value
        }
    
    async def _macd_crossover_strategy(self, data: Dict[str, Any], backtest: Backtest) -> Dict[str, Any]:
        """MACD Crossover Strategy"""
        
        trades = []
        equity_curve = []
        portfolio_value = backtest.initial_capital
        positions = {}
        
        all_dates = set()
        for symbol, df in data['data'].items():
            all_dates.update(df['date'].tolist())
        
        trading_dates = sorted(list(all_dates))
        
        for current_date in trading_dates:
            daily_trades = []
            
            for symbol, df in data['data'].items():
                current_data = df[df['date'] == current_date]
                if current_data.empty:
                    continue
                
                row = current_data.iloc[0]
                current_price = row['close']
                macd = row.get('macd')
                macd_signal = row.get('macd_signal')
                
                if pd.isna(macd) or pd.isna(macd_signal):
                    continue
                
                # Entry signals
                if symbol not in positions:
                    # Buy when MACD crosses above signal line
                    prev_data = df[df['date'] < current_date].tail(2)
                    if len(prev_data) >= 2:
                        prev_macd = prev_data.iloc[-1]['macd']
                        prev_signal = prev_data.iloc[-1]['macd_signal']
                        
                        if (macd > macd_signal and prev_macd <= prev_signal):
                            trade = self._create_trade(
                                symbol=symbol,
                                action='BUY',
                                price=current_price,
                                date=current_date,
                                backtest=backtest
                            )
                            trades.append(trade)
                            daily_trades.append(trade)
                            positions[symbol] = trade
                
                else:
                    # Exit signals
                    # Sell when MACD crosses below signal line
                    prev_data = df[df['date'] < current_date].tail(2)
                    if len(prev_data) >= 2:
                        prev_macd = prev_data.iloc[-1]['macd']
                        prev_signal = prev_data.iloc[-1]['macd_signal']
                        
                        if (macd < macd_signal and prev_macd >= prev_signal):
                            trade = self._create_trade(
                                symbol=symbol,
                                action='SELL',
                                price=current_price,
                                date=current_date,
                                backtest=backtest
                            )
                            trades.append(trade)
                            daily_trades.append(trade)
                            del positions[symbol]
            
            # Update portfolio value
            if daily_trades:
                portfolio_value = self._update_portfolio_value(
                    portfolio_value, daily_trades, positions, data['data']
                )
            
            equity_curve.append({
                'date': current_date,
                'value': portfolio_value
            })
        
        # Close remaining positions
        for symbol, position in positions.items():
            last_date = trading_dates[-1]
            last_price = data['data'][symbol][data['data'][symbol]['date'] == last_date]['close'].iloc[0]
            
            trade = self._create_trade(
                symbol=symbol,
                action='SELL',
                price=last_price,
                date=last_date,
                backtest=backtest
            )
            trades.append(trade)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_value': portfolio_value
        }
    
    async def _bollinger_bands_strategy(self, data: Dict[str, Any], backtest: Backtest) -> Dict[str, Any]:
        """Bollinger Bands Mean Reversion Strategy"""
        
        trades = []
        equity_curve = []
        portfolio_value = backtest.initial_capital
        positions = {}
        
        all_dates = set()
        for symbol, df in data['data'].items():
            all_dates.update(df['date'].tolist())
        
        trading_dates = sorted(list(all_dates))
        
        for current_date in trading_dates:
            daily_trades = []
            
            for symbol, df in data['data'].items():
                current_data = df[df['date'] == current_date]
                if current_data.empty:
                    continue
                
                row = current_data.iloc[0]
                current_price = row['close']
                bb_upper = row.get('bollinger_upper')
                bb_lower = row.get('bollinger_lower')
                bb_middle = row.get('bollinger_middle')
                
                if pd.isna(bb_upper) or pd.isna(bb_lower):
                    continue
                
                # Entry signals
                if symbol not in positions:
                    # Buy when price touches lower band
                    if current_price <= bb_lower:
                        trade = self._create_trade(
                            symbol=symbol,
                            action='BUY',
                            price=current_price,
                            date=current_date,
                            backtest=backtest
                        )
                        trades.append(trade)
                        daily_trades.append(trade)
                        positions[symbol] = trade
                
                else:
                    # Exit signals
                    # Sell when price touches middle band or upper band
                    if current_price >= bb_middle or current_price >= bb_upper:
                        trade = self._create_trade(
                            symbol=symbol,
                            action='SELL',
                            price=current_price,
                            date=current_date,
                            backtest=backtest
                        )
                        trades.append(trade)
                        daily_trades.append(trade)
                        del positions[symbol]
            
            # Update portfolio value
            if daily_trades:
                portfolio_value = self._update_portfolio_value(
                    portfolio_value, daily_trades, positions, data['data']
                )
            
            equity_curve.append({
                'date': current_date,
                'value': portfolio_value
            })
        
        # Close remaining positions
        for symbol, position in positions.items():
            last_date = trading_dates[-1]
            last_price = data['data'][symbol][data['data'][symbol]['date'] == last_date]['close'].iloc[0]
            
            trade = self._create_trade(
                symbol=symbol,
                action='SELL',
                price=last_price,
                date=last_date,
                backtest=backtest
            )
            trades.append(trade)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_value': portfolio_value
        }
    
    async def _ml_signals_strategy(self, data: Dict[str, Any], backtest: Backtest) -> Dict[str, Any]:
        """ML-based Signals Strategy"""
        
        # This would use the actual ML model
        # For now, we'll use a simplified version based on technical indicators
        
        trades = []
        equity_curve = []
        portfolio_value = backtest.initial_capital
        positions = {}
        
        all_dates = set()
        for symbol, df in data['data'].items():
            all_dates.update(df['date'].tolist())
        
        trading_dates = sorted(list(all_dates))
        
        for current_date in trading_dates:
            daily_trades = []
            
            for symbol, df in data['data'].items():
                current_data = df[df['date'] == current_date]
                if current_data.empty:
                    continue
                
                row = current_data.iloc[0]
                current_price = row['close']
                rsi = row.get('rsi_14')
                macd = row.get('macd')
                macd_signal = row.get('macd_signal')
                
                # Generate ML-like signal
                signal_strength = 0
                
                if not pd.isna(rsi):
                    if rsi < 30:
                        signal_strength += 1
                    elif rsi > 70:
                        signal_strength -= 1
                
                if not pd.isna(macd) and not pd.isna(macd_signal):
                    if macd > macd_signal:
                        signal_strength += 0.5
                    else:
                        signal_strength -= 0.5
                
                # Entry signals
                if symbol not in positions and signal_strength > 0.5:
                    trade = self._create_trade(
                        symbol=symbol,
                        action='BUY',
                        price=current_price,
                        date=current_date,
                        backtest=backtest
                    )
                    trades.append(trade)
                    daily_trades.append(trade)
                    positions[symbol] = trade
                
                # Exit signals
                elif symbol in positions and signal_strength < -0.5:
                    trade = self._create_trade(
                        symbol=symbol,
                        action='SELL',
                        price=current_price,
                        date=current_date,
                        backtest=backtest
                    )
                    trades.append(trade)
                    daily_trades.append(trade)
                    del positions[symbol]
            
            # Update portfolio value
            if daily_trades:
                portfolio_value = self._update_portfolio_value(
                    portfolio_value, daily_trades, positions, data['data']
                )
            
            equity_curve.append({
                'date': current_date,
                'value': portfolio_value
            })
        
        # Close remaining positions
        for symbol, position in positions.items():
            last_date = trading_dates[-1]
            last_price = data['data'][symbol][data['data'][symbol]['date'] == last_date]['close'].iloc[0]
            
            trade = self._create_trade(
                symbol=symbol,
                action='SELL',
                price=last_price,
                date=last_date,
                backtest=backtest
            )
            trades.append(trade)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_value': portfolio_value
        }
    
    def _create_trade(self, symbol: str, action: str, price: float, date: datetime, backtest: Backtest) -> Dict[str, Any]:
        """Create a trade record"""
        
        # Calculate position size based on risk management
        position_size = backtest.max_position_size
        max_position_value = backtest.initial_capital * position_size
        
        # Simple position sizing (in production, this would be more sophisticated)
        quantity = int(max_position_value / price)
        
        if quantity < 1:
            quantity = 1
        
        trade_value = quantity * price
        commission = trade_value * backtest.commission_rate
        slippage = trade_value * backtest.slippage_rate
        total_cost = trade_value + commission + slippage
        
        return {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'trade_value': trade_value,
            'commission': commission,
            'slippage': slippage,
            'total_cost': total_cost,
            'date': date,
            'backtest_id': backtest.id
        }
    
    def _update_portfolio_value(self, current_value: float, daily_trades: List[Dict[str, Any]], 
                              positions: Dict[str, Any], price_data: Dict[str, pd.DataFrame]) -> float:
        """Update portfolio value after trades"""
        
        for trade in daily_trades:
            if trade['action'] == 'BUY':
                current_value -= trade['total_cost']
            elif trade['action'] == 'SELL':
                current_value += trade['trade_value'] - trade['commission'] - trade['slippage']
        
        return current_value
    
    def _calculate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        
        trades = results['trades']
        equity_curve = results['equity_curve']
        final_value = results['final_value']
        
        if not trades or not equity_curve:
            return {}
        
        # Basic metrics
        initial_value = equity_curve[0]['value']
        total_return = (final_value - initial_value) / initial_value
        
        # Annualized return
        start_date = equity_curve[0]['date']
        end_date = equity_curve[-1]['date']
        days_diff = (end_date - start_date).days
        years_diff = days_diff / 365.25
        annualized_return = (1 + total_return) ** (1 / years_diff) - 1 if years_diff > 0 else 0
        
        # Trade statistics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade['action'] == 'SELL' and self._calculate_trade_pnl(trade) > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate average win/loss
        trade_pnls = [self._calculate_trade_pnl(trade) for trade in trades if trade['action'] == 'SELL']
        winning_pnls = [pnl for pnl in trade_pnls if pnl > 0]
        losing_pnls = [pnl for pnl in trade_pnls if pnl < 0]
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = np.mean(losing_pnls) if losing_pnls else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Volatility and Sharpe ratio
        equity_values = [point['value'] for point in equity_curve]
        returns = [(equity_values[i] - equity_values[i-1]) / equity_values[i-1] 
                  for i in range(1, len(equity_values))]
        
        volatility = np.std(returns) * np.sqrt(252) if returns else 0  # Annualized
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0  # Assuming 2% risk-free rate
        
        # Maximum drawdown
        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (np.array(equity_values) - running_max) / running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def _calculate_trade_pnl(self, trade: Dict[str, Any]) -> float:
        """Calculate P&L for a trade"""
        # This is a simplified calculation
        # In a real implementation, this would track the full trade lifecycle
        return 0  # Placeholder
    
    async def _update_backtest_results(self, db: AsyncSession, backtest: Backtest, results: Dict[str, Any], metrics: Dict[str, float]):
        """Update backtest with results"""
        
        # Update performance metrics
        backtest.total_return = metrics.get('total_return')
        backtest.annualized_return = metrics.get('annualized_return')
        backtest.volatility = metrics.get('volatility')
        backtest.sharpe_ratio = metrics.get('sharpe_ratio')
        backtest.max_drawdown = metrics.get('max_drawdown')
        backtest.calmar_ratio = metrics.get('calmar_ratio')
        
        # Update trade statistics
        backtest.total_trades = metrics.get('total_trades', 0)
        backtest.winning_trades = metrics.get('winning_trades', 0)
        backtest.losing_trades = metrics.get('losing_trades', 0)
        backtest.win_rate = metrics.get('win_rate')
        backtest.avg_win = metrics.get('avg_win')
        backtest.avg_loss = metrics.get('avg_loss')
        backtest.profit_factor = metrics.get('profit_factor')
        
        # Store results
        backtest.equity_curve = results['equity_curve']
        backtest.trades_history = results['trades']
        
        # Calculate monthly returns
        monthly_returns = self._calculate_monthly_returns(results['equity_curve'])
        backtest.monthly_returns = monthly_returns
    
    def _calculate_monthly_returns(self, equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate monthly returns from equity curve"""
        
        if not equity_curve:
            return []
        
        monthly_data = {}
        
        for point in equity_curve:
            date = point['date']
            month_key = f"{date.year}-{date.month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'start_value': point['value'],
                    'end_value': point['value']
                }
            else:
                monthly_data[month_key]['end_value'] = point['value']
        
        monthly_returns = []
        for month_key, data in monthly_data.items():
            year, month = map(int, month_key.split('-'))
            monthly_return = (data['end_value'] - data['start_value']) / data['start_value']
            
            monthly_returns.append({
                'year': year,
                'month': month,
                'return': monthly_return,
                'start_value': data['start_value'],
                'end_value': data['end_value']
            })
        
        return sorted(monthly_returns, key=lambda x: (x['year'], x['month']))
    
    async def compare_backtests(self, db: AsyncSession, backtest_ids: List[int]) -> Dict[str, Any]:
        """Compare multiple backtests"""
        
        backtests = []
        for backtest_id in backtest_ids:
            backtest = await db.get(Backtest, backtest_id)
            if backtest and backtest.status == BacktestStatus.COMPLETED:
                backtests.append(backtest)
        
        if not backtests:
            return {'error': 'No completed backtests found'}
        
        comparison = {
            'backtests': [],
            'summary': {},
            'charts': {}
        }
        
        # Collect metrics for comparison
        for backtest in backtests:
            comparison['backtests'].append({
                'id': backtest.id,
                'name': backtest.name,
                'strategy_type': backtest.strategy_type.value,
                'total_return': backtest.total_return,
                'annualized_return': backtest.annualized_return,
                'sharpe_ratio': backtest.sharpe_ratio,
                'max_drawdown': backtest.max_drawdown,
                'win_rate': backtest.win_rate,
                'profit_factor': backtest.profit_factor,
                'total_trades': backtest.total_trades
            })
        
        # Create comparison summary
        if comparison['backtests']:
            metrics = ['total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'win_rate']
            
            for metric in metrics:
                values = [bt[metric] for bt in comparison['backtests'] if bt[metric] is not None]
                if values:
                    comparison['summary'][metric] = {
                        'best': max(values),
                        'worst': min(values),
                        'average': np.mean(values),
                        'values': values
                    }
        
        return comparison

# Global instance
backtest_engine = BacktestEngine()