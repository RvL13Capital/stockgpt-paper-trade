from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from app.models.portfolio import Portfolio, Position, Trade
from app.models.user import User
from app.schemas.portfolio import PortfolioCreate, TradeCreate, PositionUpdate
from app.core.cache import cache_manager
from app.core.database import SessionLocal
from app.services.trade_engine import TradeEngine


class PortfolioService:
    """Portfolio management service with intelligent caching."""
    
    def __init__(self):
        self.trade_engine = TradeEngine()
    
    async def create_portfolio(self, db: Session, user_id: uuid.UUID, portfolio_data: PortfolioCreate) -> Portfolio:
        """Create a new portfolio with caching."""
        portfolio = Portfolio(
            id=uuid.uuid4(),
            user_id=user_id,
            name=portfolio_data.name,
            description=portfolio_data.description,
            initial_capital=portfolio_data.initial_capital,
            current_value=portfolio_data.initial_capital,
            cash_balance=portfolio_data.initial_capital
        )
        
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        # Invalidate user portfolios cache
        await cache_manager.invalidate_by_tag(f"user:{user_id}")
        
        # Cache the new portfolio
        await cache_manager.set_portfolio(str(portfolio.id), portfolio.to_dict())
        
        return portfolio
    
    async def get_portfolio(self, db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Portfolio]:
        """Get portfolio with intelligent caching."""
        # Try cache first
        cached_portfolio = await cache_manager.get_portfolio(str(portfolio_id))
        if cached_portfolio:
            return Portfolio(**cached_portfolio)
        
        # Fetch from database
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()
        
        if portfolio:
            # Cache for future requests
            await cache_manager.set_portfolio(str(portfolio_id), portfolio.to_dict())
        
        return portfolio
    
    async def get_user_portfolios(self, db: Session, user_id: uuid.UUID) -> List[Portfolio]:
        """Get all user portfolios with caching."""
        cache_key = f"user:{user_id}:portfolios"
        cached_portfolios = await cache_manager.get(cache_key)
        
        if cached_portfolios:
            return [Portfolio(**p) for p in cached_portfolios]
        
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        
        # Cache portfolios list
        portfolio_data = [p.to_dict() for p in portfolios]
        await cache_manager.set(cache_key, portfolio_data, tags=[f"user:{user_id}"])
        
        return portfolios
    
    async def execute_trade(self, db: Session, trade_data: TradeCreate, user_id: uuid.UUID) -> Dict[str, Any]:
        """Execute a trade with cache invalidation."""
        # Verify portfolio ownership
        portfolio = await self.get_portfolio(db, trade_data.portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found or access denied")
        
        # Execute trade through trade engine
        result = await self.trade_engine.execute_trade(db, trade_data)
        
        # Invalidate related caches
        await cache_manager.invalidate_portfolio_cache(str(portfolio.id))
        await cache_manager.invalidate_by_tag(f"symbol:{trade_data.symbol}")
        
        return result
    
    async def get_portfolio_performance(self, db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get portfolio performance with caching."""
        # Verify portfolio ownership
        portfolio = await self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found or access denied")
        
        # Try cache first
        cached_performance = await cache_manager.get_portfolio_performance(str(portfolio_id))
        if cached_performance:
            return cached_performance
        
        # Calculate performance metrics
        performance = await self._calculate_performance_metrics(db, portfolio)
        
        # Cache for 5 minutes (performance data changes frequently)
        await cache_manager.set_portfolio_performance(
            str(portfolio_id), 
            performance, 
            ttl=timedelta(minutes=5)
        )
        
        return performance
    
    async def _calculate_performance_metrics(self, db: Session, portfolio: Portfolio) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        # Get all trades for the portfolio
        trades = db.query(Trade).filter(Trade.portfolio_id == portfolio.id).all()
        
        if not trades:
            return {
                "total_return": 0.0,
                "total_return_pct": 0.0,
                "current_value": float(portfolio.current_value),
                "initial_capital": float(portfolio.initial_capital),
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_return_per_trade": 0.0
            }
        
        # Calculate returns
        total_return = portfolio.current_value - portfolio.initial_capital
        total_return_pct = (total_return / portfolio.initial_capital) * 100
        
        # Calculate trade statistics
        winning_trades = sum(1 for trade in trades if trade.pnl > 0)
        losing_trades = sum(1 for trade in trades if trade.pnl < 0)
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average return per trade
        avg_return_per_trade = sum(trade.pnl for trade in trades) / total_trades if total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = [trade.pnl for trade in trades]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            sharpe_ratio = mean_return / (variance ** 0.5) if variance > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate max drawdown (simplified)
        cumulative_returns = []
        running_total = portfolio.initial_capital
        for trade in trades:
            running_total += trade.pnl
            cumulative_returns.append(running_total)
        
        if cumulative_returns:
            max_drawdown = max(portfolio.initial_capital - min(cumulative_returns), 0)
        else:
            max_drawdown = 0
        
        return {
            "total_return": float(total_return),
            "total_return_pct": float(total_return_pct),
            "current_value": float(portfolio.current_value),
            "initial_capital": float(portfolio.initial_capital),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": float(win_rate),
            "avg_return_per_trade": float(avg_return_per_trade)
        }
    
    async def update_portfolio_value(self, db: Session, portfolio_id: uuid.UUID, new_value: float) -> None:
        """Update portfolio value and invalidate caches."""
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if portfolio:
            portfolio.current_value = new_value
            portfolio.updated_at = datetime.utcnow()
            db.commit()
            
            # Invalidate caches
            await cache_manager.invalidate_portfolio_cache(str(portfolio_id))
    
    async def get_portfolio_positions(self, db: Session, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get current portfolio positions with caching."""
        # Verify portfolio ownership
        portfolio = await self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found or access denied")
        
        # Try cache first
        cache_key = f"portfolio:{portfolio_id}:positions"
        cached_positions = await cache_manager.get(cache_key)
        if cached_positions:
            return cached_positions
        
        # Get positions from database
        positions = db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.quantity > 0
        ).all()
        
        # Convert to dict format
        positions_data = []
        for position in positions:
            positions_data.append({
                "symbol": position.symbol,
                "quantity": float(position.quantity),
                "avg_cost_basis": float(position.avg_cost_basis),
                "current_price": float(position.current_price or 0),
                "market_value": float(position.market_value or 0),
                "unrealized_pnl": float(position.unrealized_pnl or 0),
                "unrealized_pnl_pct": float(position.unrealized_pnl_pct or 0)
            })
        
        # Cache for 2 minutes (positions change frequently)
        await cache_manager.set(cache_key, positions_data, ttl=timedelta(minutes=2))
        
        return positions_data

# Global portfolio service instance
portfolio_service = PortfolioService()