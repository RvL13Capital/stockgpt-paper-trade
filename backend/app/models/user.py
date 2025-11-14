from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(20))
    
    # Trading preferences
    risk_tolerance = Column(String(20), default="medium")  # low, medium, high
    preferred_sectors = Column(Text)  # JSON array of sectors
    max_position_size = Column(Integer, default=10000)  # Max $ per position
    
    # OTP related fields
    otp_secret = Column(String(32))
    otp_backup_codes = Column(Text)  # JSON array of backup codes
    otp_enabled = Column(Boolean, default=True)
    
    # Notification preferences
    email_signals = Column(Boolean, default=True)
    email_portfolio_updates = Column(Boolean, default=True)
    email_market_updates = Column(Boolean, default=False)

    # Relationships
    signals = relationship("Signal", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    backtests = relationship("Backtest", back_populates="user")
    backtest_comparisons = relationship("BacktestComparison", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"