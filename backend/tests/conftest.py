import pytest
import asyncio
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.core.config import settings

# Test database URL
SQLALCHEMY_DATABASE_URL = "postgresql://stockgpt_user:stockgpt_password@localhost:5432/stockgpt_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db() -> Generator:
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db) -> Generator:
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client) -> dict:
    """Get authentication headers for testing."""
    # Create a test user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    response = client.post("/api/v1/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}