from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from app.core.database import get_db
from app.core.logging import logger
from app.models.stock import Stock, StockPrice, StockFeature

router = APIRouter()

@router.get("/")
async def get_stocks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    sector: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of stocks with optional filtering"""
    
    query = select(Stock).where(Stock.is_active == True)
    
    if sector:
        query = query.where(Stock.sector == sector)
    
    if search:
        query = query.where(
            Stock.symbol.ilike(f"%{search}%") | 
            Stock.name.ilike(f"%{search}%")
        )
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return {
        "stocks": [
            {
                "id": stock.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector,
                "industry": stock.industry,
                "market_cap": stock.market_cap,
                "currency": stock.currency,
                "exchange": stock.exchange,
                "country": stock.country,
                "is_active": stock.is_active
            }
            for stock in stocks
        ],
        "total": len(stocks)
    }

@router.get("/{symbol}/prices")
async def get_stock_prices(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=365, ge=1, le=1825),
    db: AsyncSession = Depends(get_db)
):
    """Get historical price data for a stock"""
    
    query = select(StockPrice).where(StockPrice.symbol == symbol)
    
    if start_date and end_date:
        query = query.where(
            and_(
                StockPrice.date >= start_date,
                StockPrice.date <= end_date
            )
        )
    else:
        query = query.order_by(desc(StockPrice.date)).limit(limit)
    
    result = await db.execute(query)
    prices = result.scalars().all()
    
    return {
        "symbol": symbol,
        "prices": [
            {
                "date": price.date.isoformat(),
                "open": price.open,
                "high": price.high,
                "low": price.low,
                "close": price.close,
                "volume": price.volume,
                "adjusted_close": price.adjusted_close,
                "adjusted_volume": price.adjusted_volume
            }
            for price in prices
        ],
        "count": len(prices)
    }

@router.get("/{symbol}/features")
async def get_stock_features(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=365, ge=1, le=1825),
    db: AsyncSession = Depends(get_db)
):
    """Get technical features for a stock"""
    
    query = select(StockFeature).where(StockFeature.symbol == symbol)
    
    if start_date and end_date:
        query = query.where(
            and_(
                StockFeature.date >= start_date,
                StockFeature.date <= end_date
            )
        )
    else:
        query = query.order_by(desc(StockFeature.date)).limit(limit)
    
    result = await db.execute(query)
    features = result.scalars().all()
    
    return {
        "symbol": symbol,
        "features": [
            {
                "date": feature.date.isoformat(),
                "sma_20": feature.sma_20,
                "sma_50": feature.sma_50,
                "sma_200": feature.sma_200,
                "ema_12": feature.ema_12,
                "ema_26": feature.ema_26,
                "rsi_14": feature.rsi_14,
                "macd": feature.macd,
                "macd_signal": feature.macd_signal,
                "macd_histogram": feature.macd_histogram,
                "bollinger_upper": feature.bollinger_upper,
                "bollinger_middle": feature.bollinger_middle,
                "bollinger_lower": feature.bollinger_lower,
                "atr_14": feature.atr_14,
                "stochastic_k": feature.stochastic_k,
                "stochastic_d": feature.stochastic_d,
                "williams_r": feature.williams_r,
                "cci": feature.cci,
                "obv": feature.obv,
                "vwap": feature.vwap,
                "volume_sma_20": feature.volume_sma_20,
                "volume_ratio": feature.volume_ratio,
                "price_change_1d": feature.price_change_1d,
                "price_change_5d": feature.price_change_5d,
                "price_change_20d": feature.price_change_20d,
                "price_change_60d": feature.price_change_60d,
                "volatility_20d": feature.volatility_20d,
                "volatility_60d": feature.volatility_60d,
                "market_regime": feature.market_regime,
                "sector_momentum": feature.sector_momentum,
                "relative_strength": feature.relative_strength
            }
            for feature in features
        ],
        "count": len(features)
    }

@router.get("/{symbol}/latest")
async def get_latest_price(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Get latest price for a stock"""
    
    query = (
        select(StockPrice)
        .where(StockPrice.symbol == symbol)
        .order_by(desc(StockPrice.date))
        .limit(1)
    )
    
    result = await db.execute(query)
    price = result.scalar_one_or_none()
    
    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for symbol {symbol}"
        )
    
    return {
        "symbol": symbol,
        "date": price.date.isoformat(),
        "open": price.open,
        "high": price.high,
        "low": price.low,
        "close": price.close,
        "volume": price.volume,
        "adjusted_close": price.adjusted_close,
        "adjusted_volume": price.adjusted_volume
    }

@router.get("/sectors")
async def get_sectors(
    db: AsyncSession = Depends(get_db)
):
    """Get list of available sectors"""
    
    query = select(Stock.sector).distinct().where(Stock.sector.isnot(None))
    
    result = await db.execute(query)
    sectors = result.scalars().all()
    
    return {
        "sectors": list(sectors),
        "count": len(sectors)
    }

@router.get("/industries")
async def get_industries(
    db: AsyncSession = Depends(get_db)
):
    """Get list of available industries"""
    
    query = select(Stock.industry).distinct().where(Stock.industry.isnot(None))
    
    result = await db.execute(query)
    industries = result.scalars().all()
    
    return {
        "industries": list(industries),
        "count": len(industries)
    }