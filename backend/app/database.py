from sqlalchemy import create_engine, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Composite indexes for performance optimization
COMPOSITE_INDEXES = [
    # Portfolio performance queries
    Index('idx_portfolio_performance', 'portfolio_id', 'created_at'),
    
    # Trade queries by portfolio and symbol
    Index('idx_trade_portfolio_symbol', 'portfolio_id', 'symbol', 'created_at'),
    
    # Position queries by portfolio and symbol
    Index('idx_position_portfolio_symbol', 'portfolio_id', 'symbol', 'updated_at'),
    
    # Signal history queries
    Index('idx_signal_history', 'symbol', 'created_at', 'strategy_type'),
    
    # User activity queries
    Index('idx_user_activity', 'user_id', 'created_at'),
    
    # Journal entry queries
    Index('idx_journal_trade', 'trade_id', 'created_at'),
    
    # Backtest queries
    Index('idx_backtest_user', 'user_id', 'created_at', 'status'),
]

def create_indexes():
    """Create composite indexes for performance optimization."""
    for index in COMPOSITE_INDEXES:
        index.create(engine, checkfirst=True)

def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database tables and indexes."""
    # Import all models to ensure they're registered
    from app.models import user, portfolio, trade, position, signal, journal, backtest
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create performance indexes
    create_indexes()
    
    print("✅ Database initialized with performance indexes")