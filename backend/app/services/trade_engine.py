import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from decimal import Decimal
from app.core.config import settings
from app.core.logging import logger
from app.models.portfolio import Portfolio, Position, Trade, PortfolioHistory
from app.models.signal import Signal, SignalStatus
from app.models.stock import StockPrice

class TradeEngine:
    def __init__(self):
        self.commission_rate = 0.001  # 0.1% commission
        self.slippage_rate = 0.0005   # 0.05% slippage
        self.paper_trade_enabled = True
        
    async def execute_paper_trade(self, db: AsyncSession, signal: Signal, portfolio_id: int) -> Optional[Trade]:
        """Execute a paper trade based on a signal"""
        
        try:
            # Get portfolio
            portfolio = await db.get(Portfolio, portfolio_id)
            if not portfolio:
                logger.error(f"Portfolio {portfolio_id} not found")
                return None
            
            # Validate signal
            if signal.status != SignalStatus.ACTIVE:
                logger.warning(f"Signal {signal.id} is not active")
                return None
            
            # Calculate trade parameters
            trade_params = await self._calculate_trade_parameters(db, signal, portfolio)
            if not trade_params:
                return None
            
            # Create trade
            trade = await self._create_trade(db, signal, portfolio, trade_params)
            
            # Update portfolio
            await self._update_portfolio_for_trade(db, portfolio, trade, trade_params)
            
            # Update position
            await self._update_position_for_trade(db, signal.symbol, portfolio, trade, trade_params)
            
            # Update signal status
            signal.status = SignalStatus.EXECUTED
            signal.executed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(f"Paper trade executed: {trade.id} for signal {signal.id}")
            return trade
            
        except Exception as e:
            logger.error(f"Error executing paper trade for signal {signal.id}: {e}")
            await db.rollback()
            return None
    
    async def _calculate_trade_parameters(self, db: AsyncSession, signal: Signal, portfolio: Portfolio) -> Optional[Dict[str, Any]]:
        """Calculate trade parameters including quantity and price"""
        
        # Get current price
        current_price = await self._get_current_price(db, signal.symbol)
        if not current_price:
            return None
        
        # Calculate position size (risk-based)
        risk_per_trade = portfolio.total_value * 0.02  # 2% risk per trade
        stop_loss_distance = abs(current_price - signal.stop_loss)
        
        if stop_loss_distance == 0:
            return None
        
        # Calculate quantity
        quantity = int(risk_per_trade / stop_loss_distance)
        
        # Apply position limits
        max_position_value = portfolio.total_value * 0.1  # Max 10% per position
        max_quantity = int(max_position_value / current_price)
        
        quantity = min(quantity, max_quantity)
        
        if quantity < 1:
            return None
        
        # Calculate costs
        trade_value = quantity * current_price
        commission = trade_value * self.commission_rate
        slippage = trade_value * self.slippage_rate
        total_cost = trade_value + commission + slippage
        
        # Check if sufficient funds
        if signal.action.value == 'BUY' and total_cost > portfolio.cash_balance:
            # Reduce quantity to fit available cash
            max_affordable = int(portfolio.cash_balance / (current_price * (1 + self.commission_rate + self.slippage_rate)))
            quantity = min(quantity, max_affordable)
            
            if quantity < 1:
                return None
            
            # Recalculate with new quantity
            trade_value = quantity * current_price
            commission = trade_value * self.commission_rate
            slippage = trade_value * self.slippage_rate
            total_cost = trade_value + commission + slippage
        
        return {
            'quantity': quantity,
            'price': current_price,
            'trade_value': trade_value,
            'commission': commission,
            'slippage': slippage,
            'total_cost': total_cost
        }
    
    async def _get_current_price(self, db: AsyncSession, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        
        result = await db.execute(
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(desc(StockPrice.date))
            .limit(1)
        )
        
        price = result.scalar_one_or_none()
        
        return price.close if price else None
    
    async def _create_trade(self, db: AsyncSession, signal: Signal, portfolio: Portfolio, params: Dict[str, Any]) -> Trade:
        """Create trade record"""
        
        trade = Trade(
            portfolio_id=portfolio.id,
            symbol=signal.symbol,
            signal_id=signal.id,
            action=signal.action.value,
            quantity=params['quantity'],
            price=params['price'],
            commission=params['commission'],
            fees=params['slippage'],
            total_cost=params['total_cost'],
            trade_date=datetime.utcnow().date(),
            status='OPEN',
            rationale=signal.rationale
        )
        
        db.add(trade)
        await db.flush()
        
        return trade
    
    async def _update_portfolio_for_trade(self, db: AsyncSession, portfolio: Portfolio, trade: Trade, params: Dict[str, Any]):
        """Update portfolio after trade execution"""
        
        if trade.action == 'BUY':
            portfolio.cash_balance -= params['total_cost']
            portfolio.invested_value += params['trade_value']
        elif trade.action == 'SELL':
            portfolio.cash_balance += params['trade_value'] - params['commission'] - params['slippage']
            portfolio.invested_value -= params['trade_value']
        
        portfolio.total_value = portfolio.cash_balance + portfolio.invested_value
        portfolio.total_trades += 1
        
        await db.flush()
    
    async def _update_position_for_trade(self, db: AsyncSession, symbol: str, portfolio: Portfolio, trade: Trade, params: Dict[str, Any]):
        """Update or create position for trade"""
        
        # Find existing position
        result = await db.execute(
            select(Position)
            .where(
                and_(
                    Position.portfolio_id == portfolio.id,
                    Position.symbol == symbol,
                    Position.status == 'ACTIVE'
                )
            )
        )
        
        position = result.scalar_one_or_none()
        
        if trade.action == 'BUY':
            if position:
                # Update existing position
                total_value = (position.quantity * position.avg_cost) + params['total_cost']
                position.quantity += params['quantity']
                position.avg_cost = total_value / position.quantity
            else:
                # Create new position
                position = Position(
                    portfolio_id=portfolio.id,
                    symbol=symbol,
                    quantity=params['quantity'],
                    avg_cost=params['price'],
                    current_price=params['price'],
                    market_value=params['trade_value'],
                    entry_date=datetime.utcnow().date(),
                    signal_id=trade.signal_id,
                    signal_confidence=trade.signal.confidence if trade.signal else None
                )
                db.add(position)
        
        elif trade.action == 'SELL':
            if position and position.quantity >= params['quantity']:
                # Reduce position
                position.quantity -= params['quantity']
                
                if position.quantity == 0:
                    # Close position
                    position.status = 'CLOSED'
                    position.exit_trade_id = trade.id
                    position.exit_price = params['price']
                    position.exit_date = datetime.utcnow().date()
            
        await db.flush()
    
    async def update_portfolio_metrics(self, db: AsyncSession, portfolio_id: int):
        """Update portfolio metrics including P&L and performance"""
        
        portfolio = await db.get(Portfolio, portfolio_id)
        if not portfolio:
            return
        
        # Update position values
        await self._update_position_values(db, portfolio)
        
        # Calculate portfolio P&L
        await self._calculate_portfolio_pnl(db, portfolio)
        
        # Update performance metrics
        await self._update_performance_metrics(db, portfolio)
        
        # Create portfolio history record
        await self._create_portfolio_history(db, portfolio)
        
        await db.commit()
    
    async def _update_position_values(self, db: AsyncSession, portfolio: Portfolio):
        """Update current values for all positions"""
        
        result = await db.execute(
            select(Position)
            .where(
                and_(
                    Position.portfolio_id == portfolio.id,
                    Position.status == 'ACTIVE'
                )
            )
        )
        
        positions = result.scalars().all()
        total_market_value = 0
        
        for position in positions:
            current_price = await self._get_current_price(db, position.symbol)
            
            if current_price:
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = (current_price - position.avg_cost) * position.quantity
                position.unrealized_pnl_percent = (position.unrealized_pnl / (position.avg_cost * position.quantity)) * 100
                
                total_market_value += position.market_value
        
        portfolio.invested_value = total_market_value
        portfolio.total_value = portfolio.cash_balance + portfolio.invested_value
    
    async def _calculate_portfolio_pnl(self, db: AsyncSession, portfolio: Portfolio):
        """Calculate portfolio P&L"""
        
        # Get closed trades for P&L calculation
        result = await db.execute(
            select(Trade)
            .where(
                and_(
                    Trade.portfolio_id == portfolio.id,
                    Trade.status == 'CLOSED'
                )
            )
        )
        
        closed_trades = result.scalars().all()
        
        total_realized_pnl = sum(trade.realized_pnl for trade in closed_trades)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in portfolio.positions if pos.status == 'ACTIVE')
        
        portfolio.total_pnl = total_realized_pnl + total_unrealized_pnl
        
        if portfolio.total_pnl != 0:
            portfolio.total_pnl_percent = (portfolio.total_pnl / (portfolio.total_value - portfolio.total_pnl)) * 100
    
    async def _update_performance_metrics(self, db: AsyncSession, portfolio: Portfolio):
        """Update performance metrics"""
        
        # Calculate win rate
        result = await db.execute(
            select(Trade)
            .where(
                and_(
                    Trade.portfolio_id == portfolio.id,
                    Trade.status == 'CLOSED',
                    Trade.realized_pnl.isnot(None)
                )
            )
        )
        
        closed_trades = result.scalars().all()
        
        if closed_trades:
            winning_trades = sum(1 for trade in closed_trades if trade.realized_pnl > 0)
            portfolio.winning_trades = winning_trades
            portfolio.losing_trades = len(closed_trades) - winning_trades
            
            if len(closed_trades) > 0:
                portfolio.win_rate = winning_trades / len(closed_trades)
        
        # Calculate Sharpe ratio (simplified)
        if len(closed_trades) > 1:
            returns = [trade.realized_pnl for trade in closed_trades if trade.realized_pnl is not None]
            if returns and len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    portfolio.sharpe_ratio = avg_return / std_return
    
    async def _create_portfolio_history(self, db: AsyncSession, portfolio: Portfolio):
        """Create portfolio history record"""
        
        today = datetime.utcnow().date()
        
        # Check if record already exists for today
        existing = await db.execute(
            select(PortfolioHistory)
            .where(
                and_(
                    PortfolioHistory.portfolio_id == portfolio.id,
                    PortfolioHistory.date == today
                )
            )
        )
        
        if existing.scalar_one_or_none():
            return
        
        # Create history record
        history = PortfolioHistory(
            portfolio_id=portfolio.id,
            date=today,
            total_value=portfolio.total_value,
            cash_balance=portfolio.cash_balance,
            invested_value=portfolio.invested_value,
            total_pnl=portfolio.total_pnl,
            total_pnl_percent=portfolio.total_pnl_percent,
            num_positions=len([p for p in portfolio.positions if p.status == 'ACTIVE']),
            max_drawdown=portfolio.max_drawdown,
            volatility=portfolio.volatility
        )
        
        db.add(history)
    
    async def close_position(self, db: AsyncSession, position_id: int, exit_price: float, reason: str = None) -> Optional[Trade]:
        """Close a position"""
        
        position = await db.get(Position, position_id)
        if not position or position.status != 'ACTIVE':
            return None
        
        # Create exit trade
        exit_trade = Trade(
            portfolio_id=position.portfolio_id,
            symbol=position.symbol,
            action='SELL' if position.quantity > 0 else 'BUY',
            quantity=abs(position.quantity),
            price=exit_price,
            commission=abs(position.quantity * exit_price * self.commission_rate),
            fees=abs(position.quantity * exit_price * self.slippage_rate),
            total_cost=abs(position.quantity * exit_price),
            trade_date=datetime.utcnow().date(),
            status='CLOSED',
            rationale=reason or 'Position closed manually'
        )
        
        db.add(exit_trade)
        await db.flush()
        
        # Update position
        position.status = 'CLOSED'
        position.exit_trade_id = exit_trade.id
        position.exit_price = exit_price
        position.exit_date = datetime.utcnow().date()
        
        # Calculate realized P&L
        if position.quantity > 0:
            realized_pnl = (exit_price - position.avg_cost) * position.quantity - exit_trade.commission - exit_trade.fees
        else:
            realized_pnl = (position.avg_cost - exit_price) * abs(position.quantity) - exit_trade.commission - exit_trade.fees
        
        exit_trade.realized_pnl = realized_pnl
        exit_trade.realized_pnl_percent = (realized_pnl / (position.avg_cost * abs(position.quantity))) * 100
        
        # Update portfolio
        portfolio = await db.get(Portfolio, position.portfolio_id)
        if portfolio:
            if exit_trade.action == 'SELL':
                portfolio.cash_balance += exit_trade.total_cost - exit_trade.commission - exit_trade.fees
            portfolio.invested_value -= position.market_value
            portfolio.total_value = portfolio.cash_balance + portfolio.invested_value
        
        await db.commit()
        
        return exit_trade
    
    async def get_portfolio_analytics(self, db: AsyncSession, portfolio_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed portfolio analytics"""
        
        # Get portfolio history
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        result = await db.execute(
            select(PortfolioHistory)
            .where(
                and_(
                    PortfolioHistory.portfolio_id == portfolio_id,
                    PortfolioHistory.date >= cutoff_date
                )
            )
            .order_by(PortfolioHistory.date)
        )
        
        history = result.scalars().all()
        
        # Calculate analytics
        if len(history) < 2:
            return {}
        
        values = [h.total_value for h in history]
        returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
        
        total_return = (values[-1] - values[0]) / values[0]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Calculate drawdown
        running_max = np.maximum.accumulate(values)
        drawdown = (np.array(values) - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        return {
            'period': f"{days} days",
            'total_return': total_return,
            'annualized_return': total_return * (365 / days),
            'volatility': volatility,
            'sharpe_ratio': (total_return * (365 / days)) / volatility if volatility > 0 else 0,
            'max_drawdown': max_drawdown,
            'current_value': values[-1],
            'history': [
                {
                    'date': h.date.isoformat(),
                    'total_value': h.total_value,
                    'cash_balance': h.cash_balance,
                    'invested_value': h.invested_value,
                    'total_pnl': h.total_pnl,
                    'total_pnl_percent': h.total_pnl_percent
                }
                for h in history
            ]
        }

# Global instance
trade_engine = TradeEngine()