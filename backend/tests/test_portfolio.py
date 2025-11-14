import pytest
from fastapi.testclient import TestClient


def test_create_portfolio(client: TestClient, auth_headers: dict):
    """Test creating a new portfolio."""
    portfolio_data = {
        "name": "Test Portfolio",
        "description": "Test portfolio description",
        "initial_capital": 100000.0
    }
    
    response = client.post("/api/v1/portfolios", json=portfolio_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == portfolio_data["name"]
    assert data["initial_capital"] == portfolio_data["initial_capital"]
    assert data["current_value"] == portfolio_data["initial_capital"]


def test_get_portfolios(client: TestClient, auth_headers: dict):
    """Test getting user portfolios."""
    # Create a portfolio first
    portfolio_data = {
        "name": "Test Portfolio 2",
        "description": "Another test portfolio",
        "initial_capital": 50000.0
    }
    client.post("/api/v1/portfolios", json=portfolio_data, headers=auth_headers)
    
    # Get portfolios
    response = client.get("/api/v1/portfolios", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_portfolio_details(client: TestClient, auth_headers: dict):
    """Test getting detailed portfolio information."""
    # Create a portfolio
    portfolio_data = {
        "name": "Detailed Portfolio",
        "description": "Portfolio for detailed testing",
        "initial_capital": 75000.0
    }
    response = client.post("/api/v1/portfolios", json=portfolio_data, headers=auth_headers)
    portfolio_id = response.json()["id"]
    
    # Get detailed information
    response = client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == portfolio_id
    assert "positions" in data
    assert "trades" in data
    assert "performance" in data


def test_portfolio_performance_calculation(client: TestClient, auth_headers: dict):
    """Test portfolio performance calculations."""
    # Create a portfolio
    portfolio_data = {
        "name": "Performance Portfolio",
        "description": "Portfolio for performance testing",
        "initial_capital": 100000.0
    }
    response = client.post("/api/v1/portfolios", json=portfolio_data, headers=auth_headers)
    portfolio_id = response.json()["id"]
    
    # Get performance metrics
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/performance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_return" in data
    assert "total_return_pct" in data
    assert "sharpe_ratio" in data
    assert "max_drawdown" in data
    assert "current_value" in data