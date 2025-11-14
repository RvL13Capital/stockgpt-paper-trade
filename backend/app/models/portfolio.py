from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TradeAction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

class PositionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Portfolio metrics
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=100000.0)  # Start with $100k
    invested_value = Column(Float, default=0.0)
    
    # Performance metrics
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    day_pnl = Column(Float, default=0.0)
    day_pnl_percent = Column(Float, default=0.0)
    
    # Statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}')>"

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Position details
    quantity = Column(Integer, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Market value
    market_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    
    # Risk management
    target_price = Column(Float)
    stop_loss = Column(Float)
    risk_reward_ratio = Column(Float)
    
    # Analysis
    entry_rationale = Column(Text)
    technical_analysis = Column(Text)
    fundamental_analysis = Column(Text)
    
    # Status and timing
    status = Column(Enum(PositionStatus), default=PositionStatus.ACTIVE)
    entry_date = Column(Date, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Signal reference
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    signal_confidence = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    signal = relationship("Signal", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(id={self.id}, portfolio_id={self.portfolio_id}, symbol='{self.symbol}', quantity={self.quantity})>"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    
    # Trade details
    action = Column(Enum(TradeAction), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Fees and costs
    commission = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    
    # Exit details (for closed trades)
    exit_trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    exit_price = Column(Float)
    exit_date = Column(Date)
    
    # Performance
    realized_pnl = Column(Float, default=0.0)
    realized_pnl_percent = Column(Float, default=0.0)
    
    # Analysis
    holding_period = Column(Integer)  # days
    r_multiple = Column(Float)  # Risk multiple
    
    # Notes and rationale
    rationale = Column(Text)
    notes = Column(Text)
    tags = Column(Text)  # JSON array of tags
    
    # Status and timing
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    trade_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    signal = relationship("Signal", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id={self.id}, portfolio_id={self.portfolio_id}, symbol='{self.symbol}', action='{self.action}')>"

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Daily metrics
    date = Column(Date, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    
    # Performance
    day_pnl = Column(Float, default=0.0)
    day_pnl_percent = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    
    # Composition
    num_positions = Column(Integer, default=0)
    sector_allocation = Column(Text)  # JSON
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PortfolioHistory(id={self.id}, portfolio_id={self.portfolio_id}, date='{self.date}', total_value={self.total_value})>"