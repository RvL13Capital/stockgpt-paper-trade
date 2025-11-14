from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, stocks, signals, portfolio, data, backtests, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(health.router, prefix="/health", tags=["health"])