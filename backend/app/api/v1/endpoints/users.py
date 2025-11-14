from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.logging import logger

router = APIRouter()

@router.get("/me")
async def get_current_user():
    """Get current user profile"""
    return {
        "id": 1,
        "email": "demo@stockgpt.com",
        "first_name": "Demo",
        "last_name": "User",
        "is_active": True,
        "is_verified": True,
        "risk_tolerance": "medium",
        "preferred_sectors": ["Technology", "Finance"],
        "max_position_size": 10000
    }

@router.put("/me")
async def update_user_profile():
    """Update user profile"""
    return {"message": "Profile updated successfully"}

@router.get("/preferences")
async def get_user_preferences():
    """Get user preferences"""
    return {
        "email_signals": True,
        "email_portfolio_updates": True,
        "email_market_updates": False,
        "otp_enabled": True
    }

@router.put("/preferences")
async def update_user_preferences():
    """Update user preferences"""
    return {"message": "Preferences updated successfully"}