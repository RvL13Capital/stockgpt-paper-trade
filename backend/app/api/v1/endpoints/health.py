from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from typing import Dict, Any
import asyncio
import time
from datetime import datetime

from app.database import get_db
from app.core.redis import get_redis
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "services": {}
    }
    
    # Check database connectivity
    try:
        db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Will be measured if needed
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    try:
        redis.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "memory_usage": redis.info("memory").get("used_memory_human", "unknown")
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check external API connectivity
    try:
        # Test Finnhub API
        import requests
        test_response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={"symbol": "AAPL"},
            headers={"X-Finnhub-Token": settings.FINNHUB_API_KEY},
            timeout=5
        )
        
        if test_response.status_code == 200:
            health_status["services"]["finnhub_api"] = {
                "status": "healthy",
                "response_time_ms": test_response.elapsed.total_seconds() * 1000
            }
        else:
            health_status["services"]["finnhub_api"] = {
                "status": "unhealthy",
                "error": f"HTTP {test_response.status_code}"
            }
    except Exception as e:
        health_status["services"]["finnhub_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # System metrics
    try:
        import psutil
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent
        }
    except:
        health_status["system"] = {
            "cpu_percent": "unknown",
            "memory_percent": "unknown",
            "disk_usage_percent": "unknown"
        }
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/health/simple")
async def simple_health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def get_metrics(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """Get application metrics."""
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {},
        "redis": {},
        "application": {}
    }
    
    # Database metrics
    try:
        db_stats = db.execute("""
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables
        """).fetchall()
        
        metrics["database"]["table_stats"] = [
            {
                "schema": row[0],
                "table": row[1],
                "inserts": row[2],
                "updates": row[3],
                "deletes": row[4]
            }
            for row in db_stats
        ]
    except Exception as e:
        metrics["database"]["error"] = str(e)
    
    # Redis metrics
    try:
        redis_info = redis.info()
        metrics["redis"] = {
            "used_memory_human": redis_info.get("used_memory_human"),
            "connected_clients": redis_info.get("connected_clients"),
            "total_commands_processed": redis_info.get("total_commands_processed"),
            "instantaneous_ops_per_sec": redis_info.get("instantaneous_ops_per_sec")
        }
    except Exception as e:
        metrics["redis"]["error"] = str(e)
    
    # Application metrics
    try:
        # Get user count
        user_count = db.execute("SELECT COUNT(*) FROM users").scalar()
        portfolio_count = db.execute("SELECT COUNT(*) FROM portfolios").scalar()
        trade_count = db.execute("SELECT COUNT(*) FROM trades").scalar()
        
        metrics["application"] = {
            "total_users": user_count,
            "total_portfolios": portfolio_count,
            "total_trades": trade_count,
            "uptime_seconds": time.time() - settings.START_TIME
        }
    except Exception as e:
        metrics["application"]["error"] = str(e)
    
    return metrics