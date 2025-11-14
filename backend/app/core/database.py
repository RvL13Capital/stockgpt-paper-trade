from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

class Base(DeclarativeBase):
    pass

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Initialize with sample data if needed
        # Disabled for production - enable only for development if needed
        # await init_sample_data(conn)
        pass

async def init_sample_data(conn):
    """Initialize database with sample data for development"""
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.signal import Signal
    from sqlalchemy import select
    
    # Check if data already exists
    result = await conn.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        return
    
    # Create sample user
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    sample_user = User(
        email="demo@stockgpt.com",
        hashed_password=pwd_context.hash("demo123"),
        is_active=True,
    )
    
    conn.add(sample_user)
    await conn.commit()