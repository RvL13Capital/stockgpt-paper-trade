from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class SignalAction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class SignalConfidence(enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(Enum(SignalAction), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence_level = Column(Enum(SignalConfidence), nullable=False)
    
    # Price levels
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float)
    stop_loss = Column(Float)
    
    # Model information
    model_version = Column(String(50), nullable=False)
    model_confidence = Column(Float, nullable=False)
    feature_importance = Column(Text)  # JSON of SHAP values
    
    # Signal rationale
    rationale = Column(Text)
    technical_analysis = Column(Text)
    fundamental_analysis = Column(Text)
    
    # Risk metrics
    risk_reward_ratio = Column(Float)
    expected_return = Column(Float)
    volatility_estimate = Column(Float)
    
    # Status and timing
    status = Column(Enum(SignalStatus), default=SignalStatus.ACTIVE, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    valid_until = Column(DateTime(timezone=True))
    executed_at = Column(DateTime(timezone=True))
    
    # Performance tracking
    actual_return = Column(Float)
    max_drawdown = Column(Float)
    holding_period = Column(Integer)  # days
    
    # User interaction
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_action = Column(String(20))  # ACCEPTED, REJECTED, IGNORED
    user_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")
    positions = relationship("Position", back_populates="signal")
    
    def __repr__(self):
        return f"<Signal(id={self.id}, symbol='{self.symbol}', action='{self.action}', confidence={self.confidence})>"

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False, index=True)
    
    # Performance metrics
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    auc_roc = Column(Float, nullable=False)
    
    # Business metrics
    total_signals = Column(Integer, nullable=False)
    profitable_signals = Column(Integer, nullable=False)
    avg_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    # Data quality
    data_drift_score = Column(Float)
    concept_drift_score = Column(Float)
    feature_drift_scores = Column(Text)  # JSON
    
    # Timing
    training_date = Column(Date, nullable=False)
    evaluation_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ModelPerformance(id={self.id}, model_version='{self.model_version}', accuracy={self.accuracy})>"