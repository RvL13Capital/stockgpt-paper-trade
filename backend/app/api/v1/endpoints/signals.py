from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def get_signals(
    symbol: Optional[str] = None,
    action: Optional[str] = None,
    confidence_min: Optional[float] = Query(default=0.0, ge=0.0, le=1.0),
    confidence_max: Optional[float] = Query(default=1.0, ge=0.0, le=1.0),
    sector: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get trading signals with filtering"""
    
    # Mock data for demo
    mock_signals = [
        {
            "id": 1,
            "symbol": "AAPL",
            "company": "Apple Inc.",
            "action": "BUY",
            "confidence": 0.87,
            "entry_price": 175.43,
            "target_price": 185.00,
            "stop_loss": 170.00,
            "sector": "Technology",
            "rationale": "Strong momentum in AI services revenue growth, technical breakout above 200-day MA",
            "model_version": "v2.1.3",
            "expected_return": 5.45,
            "risk_level": "MEDIUM",
            "generated_at": "2024-11-13T10:30:00Z"
        },
        {
            "id": 2,
            "symbol": "MSFT",
            "company": "Microsoft Corporation",
            "action": "BUY",
            "confidence": 0.92,
            "entry_price": 378.85,
            "target_price": 395.00,
            "stop_loss": 365.00,
            "sector": "Technology",
            "rationale": "Azure growth acceleration, cloud market share expansion, strong fundamentals",
            "model_version": "v2.1.3",
            "expected_return": 4.26,
            "risk_level": "LOW",
            "generated_at": "2024-11-13T09:15:00Z"
        }
    ]
    
    return {
        "signals": mock_signals,
        "total": len(mock_signals)
    }

@router.get("/{signal_id}")
async def get_signal_details(
    signal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed signal information"""
    
    # Mock signal details
    return {
        "id": signal_id,
        "symbol": "AAPL",
        "company": "Apple Inc.",
        "action": "BUY",
        "confidence": 0.87,
        "model_confidence": 0.89,
        "entry_price": 175.43,
        "target_price": 185.00,
        "stop_loss": 170.00,
        "sector": "Technology",
        "rationale": "Strong momentum in AI services revenue growth, technical breakout above 200-day MA",
        "technical_analysis": "RSI at 65, MACD bullish crossover, price above 200-day SMA",
        "fundamental_analysis": "Strong Q3 earnings, AI services revenue growth of 25% YoY",
        "model_version": "v2.1.3",
        "expected_return": 5.45,
        "risk_reward_ratio": 2.1,
        "volatility_estimate": 3.2,
        "risk_level": "MEDIUM",
        "feature_importance": {
            "rsi_14": 0.15,
            "macd": 0.12,
            "volume_ratio": 0.09,
            "price_momentum": 0.11
        },
        "generated_at": "2024-11-13T10:30:00Z",
        "valid_until": "2024-11-14T10:30:00Z"
    }

@router.post("/{signal_id}/action")
async def take_signal_action(
    signal_id: int,
    action: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Take action on a signal (accept/reject/ignore)"""
    
    return {
        "message": f"Signal {signal_id} {action}d successfully",
        "signal_id": signal_id,
        "action": action,
        "notes": notes
    }

@router.get("/performance/summary")
async def get_signal_performance_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get signal performance summary"""
    
    return {
        "total_signals": 1247,
        "active_signals": 247,
        "accuracy": 0.847,
        "avg_return": 4.23,
        "win_rate": 0.681,
        "sharpe_ratio": 1.856,
        "max_drawdown": 0.123,
        "by_sector": {
            "Technology": {"signals": 456, "accuracy": 0.856, "avg_return": 4.5},
            "Healthcare": {"signals": 234, "accuracy": 0.823, "avg_return": 3.8},
            "Finance": {"signals": 312, "accuracy": 0.834, "avg_return": 3.2}
        },
        "by_confidence": {
            "high": {"signals": 234, "accuracy": 0.923, "avg_return": 5.1},
            "medium": {"signals": 567, "accuracy": 0.834, "avg_return": 4.2},
            "low": {"signals": 446, "accuracy": 0.756, "avg_return": 3.1}
        }
    }