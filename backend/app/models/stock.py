from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    sector = Column(String(100), index=True)
    industry = Column(String(200))
    market_cap = Column(Float)
    currency = Column(String(10), default="USD")
    exchange = Column(String(50))
    country = Column(String(50), default="US")
    is_active = Column(Boolean, default=True)
    
    # Company information
    description = Column(Text)
    website = Column(String(500))
    employees = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"

class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Adjusted prices
    adjusted_open = Column(Float)
    adjusted_high = Column(Float)
    adjusted_low = Column(Float)
    adjusted_close = Column(Float)
    adjusted_volume = Column(Integer)
    
    # Technical indicators (stored as JSON)
    technical_indicators = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
    )
    
    def __repr__(self):
        return f"<StockPrice(id={self.id}, symbol='{self.symbol}', date='{self.date}', close={self.close})>"

class StockFeature(Base):
    __tablename__ = "stock_features"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Technical indicators
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    atr_14 = Column(Float)
    stochastic_k = Column(Float)
    stochastic_d = Column(Float)
    williams_r = Column(Float)
    cci = Column(Float)
    obv = Column(Float)
    vwap = Column(Float)
    
    # Volume indicators
    volume_sma_20 = Column(Float)
    volume_ratio = Column(Float)
    
    # Price momentum
    price_change_1d = Column(Float)
    price_change_5d = Column(Float)
    price_change_20d = Column(Float)
    price_change_60d = Column(Float)
    
    # Volatility
    volatility_20d = Column(Float)
    volatility_60d = Column(Float)
    
    # Market regime
    market_regime = Column(String(20))  # bull, bear, sideways
    sector_momentum = Column(Float)
    relative_strength = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_symbol_date_features', 'symbol', 'date'),
    )
    
    def __repr__(self):
        return f"<StockFeature(id={self.id}, symbol='{self.symbol}', date='{self.date}')>"