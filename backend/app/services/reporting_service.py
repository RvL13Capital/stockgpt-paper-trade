import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from app.core.config import settings
from app.core.logging import logger
from app.models.portfolio import Portfolio, Trade, Position, PortfolioHistory
from app.models.signal import Signal, SignalStatus
from app.models.backtest import Backtest
from app.models.user import User

class ReportingService:
    def __init__(self):
        self.report_templates = {
            'portfolio_summary': self._generate_portfolio_summary,
            'performance_analysis': self._generate_performance_analysis,
            'signal_analysis': self._generate_signal_analysis,
            'risk_analysis': self._generate_risk_analysis,
            'trading_journal': self._generate_trading_journal,
            'backtest_report': self._generate_backtest_report,
        }
    
    async def generate_portfolio_report(self, db: AsyncSession, portfolio_id: int, 
                                      report_type: str = 'comprehensive', 
                                      period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        
        portfolio = await db.get(Portfolio, portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        report = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.name,
            'report_type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': period_days,
        }
        
        # Generate different report sections based on type
        if report_type in ['summary', 'comprehensive']:
            report['summary'] = await self._generate_portfolio_summary(db, portfolio, period_days)
        
        if report_type in ['performance', 'comprehensive']:
            report['performance'] = await self._generate_performance_analysis(db, portfolio, period_days)
        
        if report_type in ['signals', 'comprehensive']:
            report['signals'] = await self._generate_signal_analysis(db, portfolio, period_days)
        
        if report_type in ['risk', 'comprehensive']:
            report['risk'] = await self._generate_risk_analysis(db, portfolio, period_days)
        
        if report_type in ['journal', 'comprehensive']:
            report['journal'] = await self._generate_trading_journal(db, portfolio, period_days)
        
        return report
    
    async def _generate_portfolio_summary(self, db: AsyncSession, portfolio: Portfolio, period_days: int) -> Dict[str, Any]:
        """Generate portfolio summary section"""
        
        # Current metrics
        current_metrics = {
            'total_value': portfolio.total_value,
            'cash_balance': portfolio.cash_balance,
            'invested_value': portfolio.invested_value,
            'total_pnl': portfolio.total_pnl,
            'total_pnl_percent': portfolio.total_pnl_percent,
            'day_pnl': portfolio.day_pnl,
            'day_pnl_percent': portfolio.day_pnl_percent,
        }
        
        # Performance metrics
        performance_metrics = {
            'sharpe_ratio': portfolio.sharpe_ratio,
            'max_drawdown': portfolio.max_drawdown,
            'volatility': portfolio.volatility,
            'win_rate': portfolio.win_rate,
            'total_trades': portfolio.total_trades,
            'winning_trades': portfolio.winning_trades,
            'losing_trades': portfolio.losing_trades,
        }
        
        # Current positions
        positions_result = await db.execute(
            select(Position)
            .where(
                and_(
                    Position.portfolio_id == portfolio.id,
                    Position.status == 'ACTIVE'
                )
            )
        )
        
        positions = positions_result.scalars().all()
        
        current_positions = []
        sector_allocation = {}
        
        for position in positions:
            current_positions.append({
                'symbol': position.symbol,
                'quantity': position.quantity,
                'avg_cost': position.avg_cost,
                'current_price': position.current_price,
                'market_value': position.market_value,
                'unrealized_pnl': position.unrealized_pnl,
                'unrealized_pnl_percent': position.unrealized_pnl_percent,
                'target_price': position.target_price,
                'stop_loss': position.stop_loss,
            })
            
            # Sector allocation
            sector = 'Unknown'  # This would come from stock data
            if sector not in sector_allocation:
                sector_allocation[sector] = 0
            sector_allocation[sector] += position.market_value
        
        # Calculate sector percentages
        total_position_value = sum(sector_allocation.values())
        for sector in sector_allocation:
            sector_allocation[sector] = {
                'value': sector_allocation[sector],
                'percentage': (sector_allocation[sector] / total_position_value * 100) if total_position_value > 0 else 0
            }
        
        return {
            'current_metrics': current_metrics,
            'performance_metrics': performance_metrics,
            'current_positions': current_positions,
            'sector_allocation': sector_allocation,
            'num_positions': len(current_positions),
        }
    
    async def _generate_performance_analysis(self, db: AsyncSession, portfolio: Portfolio, period_days: int) -> Dict[str, Any]:
        """Generate performance analysis section"""
        
        # Get historical data
        cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)
        
        history_result = await db.execute(
            select(PortfolioHistory)
            .where(
                and_(
                    PortfolioHistory.portfolio_id == portfolio.id,
                    PortfolioHistory.date >= cutoff_date
                )
            )
            .order_by(PortfolioHistory.date)
        )
        
        history = history_result.scalars().all()
        
        if len(history) < 2:
            return {'error': 'Insufficient historical data'}
        
        # Calculate performance metrics
        values = [h.total_value for h in history]
        dates = [h.date for h in history]
        
        # Total return
        total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
        
        # Annualized return
        days_diff = (dates[-1] - dates[0]).days
        years_diff = days_diff / 365.25
        annualized_return = (1 + total_return) ** (1 / years_diff) - 1 if years_diff > 0 else 0
        
        # Daily returns
        daily_returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        
        # Volatility (annualized)
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        # Sharpe ratio
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        running_max = np.maximum.accumulate(values)
        drawdowns = (np.array(values) - running_max) / running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        # Best and worst months
        monthly_returns = self._calculate_monthly_returns_from_history(history)
        best_month = max(monthly_returns, key=lambda x: x['return']) if monthly_returns else None
        worst_month = min(monthly_returns, key=lambda x: x['return']) if monthly_returns else None
        
        # Performance vs benchmarks (simplified)
        benchmarks = {
            'sp500': 0.08,  # 8% annual return
            'nasdaq': 0.12,  # 12% annual return
        }
        
        performance_vs_benchmarks = {}
        for benchmark_name, benchmark_return in benchmarks.items():
            performance_vs_benchmarks[benchmark_name] = {
                'portfolio_return': annualized_return,
                'benchmark_return': benchmark_return,
                'excess_return': annualized_return - benchmark_return,
                'outperformed': annualized_return > benchmark_return
            }
        
        return {
            'period_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'best_month': best_month,
            'worst_month': worst_month,
            'performance_vs_benchmarks': performance_vs_benchmarks,
            'equity_curve': [{'date': d.isoformat(), 'value': v} for d, v in zip(dates, values)],
            'monthly_returns': monthly_returns,
        }
    
    async def _generate_signal_analysis(self, db: AsyncSession, portfolio: Portfolio, period_days: int) -> Dict[str, Any]:
        """Generate signal analysis section"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get signals for the period
        signals_result = await db.execute(
            select(Signal)
            .where(
                and_(
                    Signal.symbol.in_([p.symbol for p in portfolio.positions if p.status == 'ACTIVE']),
                    Signal.generated_at >= cutoff_date
                )
            )
            .order_by(desc(Signal.generated_at))
        )
        
        signals = signals_result.scalars().all()
        
        # Signal statistics
        total_signals = len(signals)
        signals_by_action = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        signals_by_confidence = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for signal in signals:
            signals_by_action[signal.action.value] += 1
            signals_by_confidence[signal.confidence_level.value] += 1
        
        # Average confidence
        avg_confidence = np.mean([s.confidence for s in signals]) if signals else 0
        
        # Signal performance (simplified)
        executed_signals = [s for s in signals if s.status == SignalStatus.EXECUTED]
        execution_rate = len(executed_signals) / total_signals if total_signals > 0 else 0
        
        # Top performing signals
        top_signals = sorted(signals, key=lambda s: s.confidence, reverse=True())[:10]
        
        return {
            'total_signals': total_signals,
            'signals_by_action': signals_by_action,
            'signals_by_confidence': signals_by_confidence,
            'avg_confidence': avg_confidence,
            'execution_rate': execution_rate,
            'top_signals': [
                {
                    'id': s.id,
                    'symbol': s.symbol,
                    'action': s.action.value,
                    'confidence': s.confidence,
                    'confidence_level': s.confidence_level.value,
                    'generated_at': s.generated_at.isoformat(),
                    'rationale': s.rationale,
                }
                for s in top_signals
            ],
        }
    
    async def _generate_risk_analysis(self, db: AsyncSession, portfolio: Portfolio, period_days: int) -> Dict[str, Any]:
        """Generate risk analysis section"""
        
        # Get historical data for risk calculations
        cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)
        
        history_result = await db.execute(
            select(PortfolioHistory)
            .where(
                and_(
                    PortfolioHistory.portfolio_id == portfolio.id,
                    PortfolioHistory.date >= cutoff_date
                )
            )
            .order_by(PortfolioHistory.date)
        )
        
        history = history_result.scalars().all()
        
        if len(history) < 2:
            return {'error': 'Insufficient data for risk analysis'}
        
        values = [h.total_value for h in history]
        daily_returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        
        # Value at Risk (VaR) - 95% confidence
        var_95 = np.percentile(daily_returns, 5) if daily_returns else 0
        
        # Expected Shortfall (Conditional VaR)
        expected_shortfall = np.mean([r for r in daily_returns if r <= var_95]) if daily_returns else 0
        
        # Portfolio Beta (simplified - would need market data)
        portfolio_beta = 1.0  # Placeholder
        
        # Risk-adjusted returns
        risk_adjusted_return = portfolio.sharpe_ratio if portfolio.sharpe_ratio else 0
        
        # Position concentration risk
        positions_result = await db.execute(
            select(Position)
            .where(
                and_(
                    Position.portfolio_id == portfolio.id,
                    Position.status == 'ACTIVE'
                )
            )
        )
        
        positions = positions_result.scalars().all()
        
        # Calculate concentration metrics
        position_values = [p.market_value for p in positions]
        total_position_value = sum(position_values)
        
        concentration_metrics = {
            'num_positions': len(positions),
            'largest_position_pct': (max(position_values) / total_position_value * 100) if position_values else 0,
            'herfindahl_index': sum((v / total_position_value) ** 2 for v in position_values) if total_position_value > 0 else 0,
        }
        
        # Correlation risk (simplified)
        correlation_risk = 'Medium'  # Would need historical correlation data
        
        # Liquidity risk
        liquidity_risk = 'Low'  # Would need volume and bid-ask spread data
        
        return {
            'var_95': var_95,
            'expected_shortfall': expected_shortfall,
            'portfolio_beta': portfolio_beta,
            'risk_adjusted_return': risk_adjusted_return,
            'concentration_metrics': concentration_metrics,
            'correlation_risk': correlation_risk,
            'liquidity_risk': liquidity_risk,
            'max_drawdown': portfolio.max_drawdown,
            'volatility': portfolio.volatility,
        }
    
    async def _generate_trading_journal(self, db: AsyncSession, portfolio: Portfolio, period_days: int) -> Dict[str, Any]:
        """Generate trading journal section"""
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)
        
        # Get trades for the period
        trades_result = await db.execute(
            select(Trade)
            .where(
                and_(
                    Trade.portfolio_id == portfolio.id,
                    Trade.trade_date >= cutoff_date
                )
            )
            .order_by(desc(Trade.trade_date))
        )
        
        trades = trades_result.scalars().all()
        
        # Trade statistics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade.realized_pnl and trade.realized_pnl > 0)
        losing_trades = sum(1 for trade in trades if trade.realized_pnl and trade.realized_pnl < 0)
        
        # Average holding period
        holding_periods = []
        for trade in trades:
            if trade.holding_period:
                holding_periods.append(trade.holding_period)
        
        avg_holding_period = np.mean(holding_periods) if holding_periods else 0
        
        # Best and worst trades
        trades_with_pnl = [t for t in trades if t.realized_pnl is not None]
        
        best_trade = max(trades_with_pnl, key=lambda t: t.realized_pnl) if trades_with_pnl else None
        worst_trade = min(trades_with_pnl, key=lambda t: t.realized_pnl) if trades_with_pnl else None
        
        # Recent trades
        recent_trades = trades[:20]  # Last 20 trades
        
        # Trading patterns
        trading_patterns = self._analyze_trading_patterns(trades)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'avg_holding_period': avg_holding_period,
            'best_trade': {
                'symbol': best_trade.symbol if best_trade else None,
                'pnl': best_trade.realized_pnl if best_trade else None,
                'pnl_percent': best_trade.realized_pnl_percent if best_trade else None,
                'date': best_trade.trade_date.isoformat() if best_trade else None,
            },
            'worst_trade': {
                'symbol': worst_trade.symbol if worst_trade else None,
                'pnl': worst_trade.realized_pnl if worst_trade else None,
                'pnl_percent': worst_trade.realized_pnl_percent if worst_trade else None,
                'date': worst_trade.trade_date.isoformat() if worst_trade else None,
            },
            'recent_trades': [
                {
                    'id': t.id,
                    'symbol': t.symbol,
                    'action': t.action,
                    'quantity': t.quantity,
                    'price': t.price,
                    'pnl': t.realized_pnl,
                    'pnl_percent': t.realized_pnl_percent,
                    'date': t.trade_date.isoformat(),
                    'rationale': t.rationale,
                    'notes': t.notes,
                }
                for t in recent_trades
            ],
            'trading_patterns': trading_patterns,
        }
    
    def _analyze_trading_patterns(self, trades: List[Trade]) -> Dict[str, Any]:
        """Analyze trading patterns and behaviors"""
        
        if not trades:
            return {}
        
        # Trading frequency
        trade_dates = [t.trade_date for t in trades]
        trading_days = len(set(trade_dates))
        avg_trades_per_day = len(trades) / trading_days if trading_days > 0 else 0
        
        # Most traded symbols
        symbol_counts = {}
        for trade in trades:
            symbol_counts[trade.symbol] = symbol_counts.get(trade.symbol, 0) + 1
        
        most_traded = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True())[:5]
        
        # Trading time patterns
        # This would analyze time of day, day of week patterns
        
        return {
            'trading_days': trading_days,
            'avg_trades_per_day': avg_trades_per_day,
            'most_traded_symbols': most_traded,
            'total_unique_symbols': len(symbol_counts),
        }
    
    async def _generate_backtest_report(self, db: AsyncSession, backtest_id: int) -> Dict[str, Any]:
        """Generate backtest report"""
        
        backtest = await db.get(Backtest, backtest_id)
        if not backtest:
            return {'error': 'Backtest not found'}
        
        return {
            'backtest_id': backtest.id,
            'name': backtest.name,
            'strategy_type': backtest.strategy_type.value,
            'status': backtest.status.value,
            'start_date': backtest.start_date.isoformat(),
            'end_date': backtest.end_date.isoformat(),
            'initial_capital': backtest.initial_capital,
            'final_value': backtest.equity_curve[-1]['value'] if backtest.equity_curve else backtest.initial_capital,
            'total_return': backtest.total_return,
            'annualized_return': backtest.annualized_return,
            'sharpe_ratio': backtest.sharpe_ratio,
            'max_drawdown': backtest.max_drawdown,
            'win_rate': backtest.win_rate,
            'total_trades': backtest.total_trades,
            'profit_factor': backtest.profit_factor,
            'strategy_config': backtest.strategy_config,
            'equity_curve': backtest.equity_curve,
            'monthly_returns': backtest.monthly_returns,
        }
    
    def _calculate_monthly_returns_from_history(self, history: List[PortfolioHistory]) -> List[Dict[str, Any]]:
        """Calculate monthly returns from portfolio history"""
        
        if not history:
            return []
        
        monthly_data = {}
        
        for record in history:
            date = record.date
            month_key = f"{date.year}-{date.month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'start_value': record.total_value,
                    'end_value': record.total_value
                }
            else:
                monthly_data[month_key]['end_value'] = record.total_value
        
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
    
    async def export_report(self, report: Dict[str, Any], format: str = 'json') -> str:
        """Export report in specified format"""
        
        if format == 'json':
            import json
            return json.dumps(report, indent=2, default=str)
        
        elif format == 'csv':
            # Convert to CSV format
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Flatten the report structure for CSV
            self._flatten_report_for_csv(report, writer)
            
            return output.getvalue()
        
        elif format == 'pdf':
            # This would require a PDF library like ReportLab
            return "PDF export not implemented yet"
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _flatten_report_for_csv(self, report: Dict[str, Any], writer: Any):
        """Flatten report structure for CSV export"""
        
        # This is a simplified implementation
        # In production, this would handle nested structures properly
        
        if 'summary' in report and 'current_metrics' in report['summary']:
            metrics = report['summary']['current_metrics']
            writer.writerow(['Metric', 'Value'])
            for key, value in metrics.items():
                writer.writerow([key, value])

# Global instance
reporting_service = ReportingService()