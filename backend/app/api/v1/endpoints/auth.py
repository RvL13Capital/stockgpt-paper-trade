from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.config import settings
from app.core.logging import logger
from app.models.user import User
from passlib.context import CryptContext
import secrets
from jose import jwt

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

@router.post("/login")
async def login(
    email: str,
    otp: str,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and OTP"""
    
    # Validate OTP format
    if len(otp) != settings.OTP_LENGTH or not otp.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP format"
        )
    
    # For demo purposes, accept any 4-digit OTP
    # In production, this would validate against stored OTP
    
    # Get or create user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user for demo
        user = User(
            email=email,
            hashed_password=pwd_context.hash(secrets.token_urlsafe(16)),
            is_active=True,
            is_verified=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
    
    # Generate JWT token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    }

@router.post("/request-otp")
async def request_otp(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Request OTP for login"""
    
    # In production, this would generate and send OTP via email
    # For demo purposes, we'll just return a success message
    
    logger.info(f"OTP requested for email: {email}")
    
    return {
        "message": "OTP sent successfully",
        "expires_in": settings.OTP_EXPIRE_MINUTES * 60
    }

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user (invalidate token)"""
    
    # In production, this would invalidate the token
    # For demo purposes, we'll just return a success message
    
    return {"message": "Logged out successfully"}

@router.get("/verify-token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify JWT token"""
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "expires_at": payload.get("exp")
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.get("/status")
async def auth_status():
    """Get authentication service status"""
    
    return {
        "service": "operational",
        "otp_enabled": settings.OTP_LENGTH > 0,
        "otp_length": settings.OTP_LENGTH,
        "token_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
    }