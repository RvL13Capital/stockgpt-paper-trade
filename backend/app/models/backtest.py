from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class BacktestStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class StrategyType(enum.Enum):
    MOVING_AVERAGE = "MOVING_AVERAGE"
    RSI_DIVERGENCE = "RSI_DIVERGENCE"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    ML_SIGNALS = "ML_SIGNALS"
    CUSTOM = "CUSTOM"

class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Strategy configuration
    strategy_type = Column(Enum(StrategyType), nullable=False)
    strategy_config = Column(JSON)  # Strategy parameters
    
    # Backtest parameters
    symbols = Column(JSON)  # List of symbols to test
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, default=100000.0)
    
    # Risk management
    max_position_size = Column(Float, default=0.1)  # 10% max per position
    stop_loss_pct = Column(Float, default=0.05)     # 5% stop loss
    take_profit_pct = Column(Float, default=0.1)    # 10% take profit
    
    # Execution parameters
    commission_rate = Column(Float, default=0.001)  # 0.1% commission
    slippage_rate = Column(Float, default=0.0005)   # 0.05% slippage
    
    # Status and timing
    status = Column(Enum(BacktestStatus), default=BacktestStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Performance metrics
    total_return = Column(Float)
    annualized_return = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)
    
    # Risk metrics
    var_95 = Column(Float)  # Value at Risk (95% confidence)
    expected_shortfall = Column(Float)
    calmar_ratio = Column(Float)
    sortino_ratio = Column(Float)
    
    # Additional metrics
    avg_holding_period = Column(Float)
    max_consecutive_wins = Column(Integer, default=0)
    max_consecutive_losses = Column(Integer, default=0)
    
    # Results storage
    equity_curve = Column(JSON)  # List of {date, value} pairs
    trades_history = Column(JSON)  # Complete trade log
    monthly_returns = Column(JSON)  # Monthly return breakdown
    
    # Error information
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="backtests")
    
    def __repr__(self):
        return f"<Backtest(id={self.id}, name='{self.name}', strategy='{self.strategy_type}', status='{self.status}')>"

class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    strategy_type = Column(Enum(StrategyType), nullable=False)
    
    # Strategy parameters with defaults
    parameters = Column(JSON)  # Parameter definitions and defaults
    
    # Rules and conditions
    entry_conditions = Column(JSON)  # Conditions for entering trades
    exit_conditions = Column(JSON)   # Conditions for exiting trades
    
    # Risk management defaults
    default_stop_loss = Column(Float, default=0.05)
    default_take_profit = Column(Float, default=0.1)
    default_position_size = Column(Float, default=0.1)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_public = Column(Boolean, default=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    avg_performance = Column(Float)
    
    def __repr__(self):
        return f"<StrategyTemplate(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"

class BacktestComparison(Base):
    __tablename__ = "backtest_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Compared backtests
    backtest_ids = Column(JSON)  # List of backtest IDs to compare
    
    # Comparison metrics
    comparison_data = Column(JSON)  # Detailed comparison results
    
    # Visualization data
    charts_data = Column(JSON)  # Data for comparison charts
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="backtest_comparisons")
    
    def __repr__(self):
        return f"<BacktestComparison(id={self.id}, name='{self.name}')>"