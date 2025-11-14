from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.logging import logger
from app.services.data_ingestion import data_ingestion_service
from app.core.config import settings

router = APIRouter()

@router.post("/ingest/stocks")
async def ingest_stock_data(
    symbols: List[str],
    days_back: int = Query(default=365, ge=1, le=1825),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Ingest historical stock data for given symbols"""
    
    if not settings.POLYGON_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Polygon API key not configured"
        )
    
    try:
        # Run ingestion in background if requested
        if background_tasks:
            background_tasks.add_task(
                data_ingestion_service.ingest_stock_data,
                db,
                symbols,
                days_back
            )
            return {
                "message": "Data ingestion started in background",
                "symbols": symbols,
                "days_back": days_back
            }
        else:
            # Synchronous ingestion
            count = await data_ingestion_service.ingest_stock_data(db, symbols, days_back)
            return {
                "message": f"Successfully ingested data for {count} symbols",
                "symbols_processed": count,
                "total_symbols": len(symbols)
            }
    
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Data ingestion failed: {str(e)}"
        )

@router.post("/ingest/stock-list")
async def update_stock_list(
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Update stock list from Polygon API"""
    
    if not settings.POLYGON_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Polygon API key not configured"
        )
    
    try:
        if background_tasks:
            background_tasks.add_task(
                data_ingestion_service.update_stock_info,
                db
            )
            return {
                "message": "Stock list update started in background"
            }
        else:
            count = await data_ingestion_service.update_stock_info(db)
            return {
                "message": f"Updated {count} stocks",
                "stocks_updated": count
            }
    
    except Exception as e:
        logger.error(f"Error updating stock list: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Stock list update failed: {str(e)}"
        )

@router.get("/symbols/available")
async def get_available_symbols(
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available symbols for data ingestion"""
    
    try:
        symbols = await data_ingestion_service.get_symbols_for_ingestion(db, limit)
        return {
            "symbols": symbols,
            "count": len(symbols)
        }
    
    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get symbols: {str(e)}"
        )

@router.post("/ingest/scheduled")
async def run_scheduled_ingestion(
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Run scheduled data ingestion task"""
    
    if background_tasks:
        background_tasks.add_task(
            data_ingestion_service.scheduled_ingestion,
            db
        )
        return {
            "message": "Scheduled ingestion started in background"
        }
    else:
        await data_ingestion_service.scheduled_ingestion(db)
        return {
            "message": "Scheduled ingestion completed"
        }

@router.get("/status")
async def get_ingestion_status():
    """Get data ingestion service status"""
    
    return {
        "service": "operational",
        "polygon_api_configured": bool(settings.POLYGON_API_KEY),
        "tiingo_api_configured": bool(settings.TIINGO_API_KEY),
        "features": {
            "real_time_data": settings.FEATURE_REAL_TIME_DATA,
            "advanced_charts": settings.FEATURE_ADVANCED_CHARTS,
            "model_insights": settings.FEATURE_MODEL_INSIGHTS
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for data ingestion service"""
    
    return {
        "status": "healthy",
        "timestamp": "2024-11-13T10:00:00Z",
        "services": {
            "database": "connected",
            "polygon_api": "configured" if settings.POLYGON_API_KEY else "not_configured",
            "redis": "connected"  # This would check Redis connection
        }
    }