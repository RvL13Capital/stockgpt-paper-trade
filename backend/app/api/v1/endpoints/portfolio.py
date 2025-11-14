from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db

router = APIRouter()

@router.get("/summary")
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio summary and key metrics"""
    
    return {
        "total_value": 73016.40,
        "cash_balance": 25000.00,
        "invested_value": 48016.40,
        "total_pnl": 1539.40,
        "total_pnl_percent": 2.15,
        "day_pnl": 1250.30,
        "day_pnl_percent": 1.74,
        "total_trades": 47,
        "winning_trades": 32,
        "losing_trades": 15,
        "win_rate": 68.1,
        "sharpe_ratio": 1.856,
        "max_drawdown": 12.3,
        "volatility": 18.5
    }

@router.get("/positions")
async def get_positions(
    symbol: Optional[str] = None,
    sector: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current open positions"""
    
    positions = [
        {
            "id": 1,
            "symbol": "AAPL",
            "company": "Apple Inc.",
            "quantity": 100,
            "avg_cost": 170.50,
            "current_price": 175.43,
            "market_value": 17543.00,
            "unrealized_pnl": 493.00,
            "unrealized_pnl_percent": 2.89,
            "target_price": 185.00,
            "stop_loss": 165.00,
            "sector": "Technology",
            "entry_date": "2024-10-15",
            "last_signal": "BUY",
            "confidence": 0.87,
            "risk_reward_ratio": 2.1
        },
        {
            "id": 2,
            "symbol": "MSFT",
            "company": "Microsoft Corporation",
            "quantity": 50,
            "avg_cost": 365.20,
            "current_price": 378.85,
            "market_value": 18942.50,
            "unrealized_pnl": 682.50,
            "unrealized_pnl_percent": 3.74,
            "target_price": 395.00,
            "stop_loss": 350.00,
            "sector": "Technology",
            "entry_date": "2024-10-20",
            "last_signal": "BUY",
            "confidence": 0.92,
            "risk_reward_ratio": 2.8
        }
    ]
    
    return {
        "positions": positions,
        "total": len(positions)
    }

@router.get("/positions/{position_id}")
async def get_position_details(
    position_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed position information"""
    
    return {
        "id": position_id,
        "symbol": "AAPL",
        "company": "Apple Inc.",
        "quantity": 100,
        "avg_cost": 170.50,
        "current_price": 175.43,
        "market_value": 17543.00,
        "unrealized_pnl": 493.00,
        "unrealized_pnl_percent": 2.89,
        "target_price": 185.00,
        "stop_loss": 165.00,
        "sector": "Technology",
        "entry_date": "2024-10-15",
        "last_updated": "2024-11-13T10:30:00Z",
        "signal_id": 1,
        "signal_confidence": 0.87,
        "risk_reward_ratio": 2.1,
        "entry_rationale": "Technical breakout above 200-day MA with strong volume confirmation",
        "technical_analysis": "RSI at 65, MACD bullish crossover, price above 200-day SMA",
        "fundamental_analysis": "Strong Q3 earnings, AI services revenue growth of 25% YoY"
    }

@router.get("/allocation")
async def get_portfolio_allocation(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio allocation by sector"""
    
    return {
        "by_sector": [
            {"sector": "Technology", "value": 59557.50, "percentage": 81.6},
            {"sector": "Finance", "value": 13458.40, "percentage": 18.4}
        ],
        "by_market_cap": [
            {"category": "Large Cap", "value": 65000.00, "percentage": 89.0},
            {"category": "Mid Cap", "value": 8000.00, "percentage": 11.0}
        ],
        "by_style": [
            {"style": "Growth", "value": 45000.00, "percentage": 61.6},
            {"style": "Value", "value": 28016.40, "percentage": 38.4}
        ]
    }

@router.get("/performance")
async def get_portfolio_performance(
    period: str = Query(default="1M", regex="^(1D|1W|1M|3M|6M|1Y|ALL)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio performance history"""
    
    performance_data = [
        {"date": "2024-10-15", "value": 70000, "pnl": 0},
        {"date": "2024-10-20", "value": 71200, "pnl": 1200},
        {"date": "2024-10-25", "value": 72500, "pnl": 2500},
        {"date": "2024-10-30", "value": 71800, "pnl": 1800},
        {"date": "2024-11-05", "value": 73500, "pnl": 3500},
        {"date": "2024-11-10", "value": 72800, "pnl": 2800},
        {"date": "2024-11-13", "value": 73016.40, "pnl": 3016.40}
    ]
    
    return {
        "period": period,
        "performance": performance_data,
        "total_return": 4.31,
        "annualized_return": 15.2,
        "volatility": 18.5,
        "max_drawdown": 12.3,
        "sharpe_ratio": 1.856
    }

@router.post("/positions")
async def create_position(
    symbol: str,
    quantity: int,
    price: float,
    db: AsyncSession = Depends(get_db)
):
    """Create a new position"""
    
    return {
        "message": "Position created successfully",
        "position_id": 123,
        "symbol": symbol,
        "quantity": quantity,
        "price": price
    }

@router.put("/positions/{position_id}")
async def update_position(
    position_id: int,
    target_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Update position parameters"""
    
    return {
        "message": "Position updated successfully",
        "position_id": position_id,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "notes": notes
    }

@router.delete("/positions/{position_id}")
async def close_position(
    position_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Close a position"""
    
    return {
        "message": "Position closed successfully",
        "position_id": position_id
    }