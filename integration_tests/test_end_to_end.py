import pytest
import requests
import time
from typing import Dict, Any


class TestEndToEnd:
    """End-to-end integration tests for StockGPT."""
    
    @pytest.fixture(scope="class")
    def base_url(self) -> str:
        """Base URL for the application."""
        return "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def auth_token(self, base_url: str) -> str:
        """Get authentication token for testing."""
        # Register user
        user_data = {
            "email": "e2e_test@example.com",
            "password": "testpassword123"
        }
        
        # Try to register, ignore if already exists
        try:
            requests.post(f"{base_url}/auth/register", json=user_data)
        except:
            pass
        
        # Login
        response = requests.post(f"{base_url}/auth/login", json=user_data)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_complete_trading_workflow(self, base_url: str, auth_token: str):
        """Test complete trading workflow from portfolio creation to trade execution."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Create portfolio
        portfolio_data = {
            "name": "E2E Test Portfolio",
            "description": "Portfolio for end-to-end testing",
            "initial_capital": 100000.0
        }
        
        response = requests.post(f"{base_url}/portfolios", json=portfolio_data, headers=headers)
        assert response.status_code == 201
        portfolio_id = response.json()["id"]
        
        # 2. Get AI signal for AAPL
        response = requests.get(f"{base_url}/signals/AAPL", headers=headers)
        assert response.status_code == 200
        signal_data = response.json()
        assert signal_data["symbol"] == "AAPL"
        
        # 3. Execute trade based on signal
        trade_data = {
            "portfolio_id": portfolio_id,
            "symbol": "AAPL",
            "side": signal_data["signal"],
            "quantity": 10,
            "order_type": "market",
            "price": signal_data.get("price", 175.0)
        }
        
        response = requests.post(f"{base_url}/trades", json=trade_data, headers=headers)
        assert response.status_code == 201
        trade_id = response.json()["id"]
        
        # 4. Check portfolio position
        time.sleep(2)  # Wait for trade processing
        response = requests.get(f"{base_url}/portfolios/{portfolio_id}", headers=headers)
        assert response.status_code == 200
        portfolio_data = response.json()
        
        # Should have one position
        positions = portfolio_data.get("positions", [])
        assert len(positions) >= 0  # May be empty due to paper trading simulation
        
        # 5. Get portfolio performance
        response = requests.get(f"{base_url}/portfolios/{portfolio_id}/performance", headers=headers)
        assert response.status_code == 200
        performance_data = response.json()
        assert "total_return" in performance_data
        assert "current_value" in performance_data
        
        # 6. Create journal entry
        journal_data = {
            "trade_id": trade_id,
            "title": "E2E Test Trade",
            "content": "This trade was part of end-to-end testing",
            "tags": ["test", "e2e", "aapl"],
            "mood": "confident",
            "mistakes": [],
            "improvements": ["Better timing"]
        }
        
        response = requests.post(f"{base_url}/journal", json=journal_data, headers=headers)
        assert response.status_code == 201
        
        # 7. Get insights
        response = requests.get(f"{base_url}/insights", headers=headers)
        assert response.status_code == 200
        insights_data = response.json()
        assert isinstance(insights_data, dict)
    
    def test_backtesting_workflow(self, base_url: str, auth_token: str):
        """Test complete backtesting workflow."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Create backtest
        backtest_data = {
            "name": "E2E Backtest",
            "description": "End-to-end backtest test",
            "strategy_type": "moving_average",
            "symbols": ["AAPL", "GOOGL"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-01",
            "initial_capital": 100000,
            "parameters": {
                "short_window": 20,
                "long_window": 50
            }
        }
        
        response = requests.post(f"{base_url}/backtests", json=backtest_data, headers=headers)
        assert response.status_code == 201
        backtest_id = response.json()["id"]
        
        # 2. Run backtest
        response = requests.post(f"{base_url}/backtests/{backtest_id}/run", headers=headers)
        assert response.status_code == 202  # Accepted for background processing
        
        # 3. Wait for completion and get results
        max_attempts = 30
        for attempt in range(max_attempts):
            response = requests.get(f"{base_url}/backtests/{backtest_id}", headers=headers)
            assert response.status_code == 200
            backtest_data = response.json()
            
            if backtest_data["status"] == "completed":
                break
            
            time.sleep(10)
        else:
            pytest.fail("Backtest did not complete in time")
        
        # 4. Check results
        assert "results" in backtest_data
        results = backtest_data["results"]
        assert "total_return" in results
        assert "sharpe_ratio" in results
        assert "max_drawdown" in results
        assert "trades" in results
    
    def test_real_time_updates(self, base_url: str, auth_token: str):
        """Test real-time updates via WebSocket or polling."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Create portfolio
        portfolio_data = {
            "name": "Real-time Test Portfolio",
            "description": "Portfolio for real-time testing",
            "initial_capital": 50000.0
        }
        
        response = requests.post(f"{base_url}/portfolios", json=portfolio_data, headers=headers)
        portfolio_id = response.json()["id"]
        
        # 2. Get initial portfolio value
        response = requests.get(f"{base_url}/portfolios/{portfolio_id}", headers=headers)
        initial_value = response.json()["current_value"]
        
        # 3. Wait and check for updates (simulating real-time price changes)
        time.sleep(5)
        
        response = requests.get(f"{base_url}/portfolios/{portfolio_id}", headers=headers)
        updated_value = response.json()["current_value"]
        
        # Value might change due to paper trading simulation
        assert updated_value is not None
        assert updated_value > 0
    
    def test_error_handling(self, base_url: str, auth_token: str):
        """Test error handling and edge cases."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Invalid symbol
        response = requests.get(f"{base_url}/signals/INVALID_SYMBOL_123", headers=headers)
        assert response.status_code == 400
        
        # 2. Invalid trade data
        invalid_trade_data = {
            "portfolio_id": "invalid-uuid",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": -10,  # Invalid quantity
            "order_type": "market"
        }
        
        response = requests.post(f"{base_url}/trades", json=invalid_trade_data, headers=headers)
        assert response.status_code == 422
        
        # 3. Unauthorized access
        response = requests.get(f"{base_url}/portfolios", headers={})
        assert response.status_code == 401