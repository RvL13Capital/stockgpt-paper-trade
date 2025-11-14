import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_get_ai_signals(client: TestClient, auth_headers: dict):
    """Test getting AI-generated trading signals."""
    with patch('app.services.signal_service.SignalService.generate_signals') as mock_generate:
        # Mock signal generation
        mock_generate.return_value = {
            "symbol": "AAPL",
            "signal": "BUY",
            "confidence": 0.85,
            "reasoning": "Technical indicators suggest upward trend",
            "price": 175.50,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        response = client.get("/api/v1/signals/AAPL", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["signal"] in ["BUY", "SELL", "HOLD"]
        assert 0 <= data["confidence"] <= 1


def test_get_signals_history(client: TestClient, auth_headers: dict):
    """Test getting signal history."""
    response = client.get("/api/v1/signals/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "symbol" in data[0]
        assert "signal" in data[0]
        assert "timestamp" in data[0]


def test_get_signal_performance(client: TestClient, auth_headers: dict):
    """Test getting signal performance metrics."""
    response = client.get("/api/v1/signals/performance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_signals" in data
    assert "accuracy_rate" in data
    assert "avg_return" in data
    assert "win_rate" in data


def test_signal_explanation(client: TestClient, auth_headers: dict):
    """Test getting signal explanation with SHAP values."""
    with patch('app.services.signal_service.SignalService.explain_signal') as mock_explain:
        # Mock SHAP explanation
        mock_explain.return_value = {
            "symbol": "AAPL",
            "prediction": 0.85,
            "features": {
                "rsi": {"value": 0.7, "impact": 0.15},
                "macd": {"value": 0.5, "impact": 0.25},
                "volume": {"value": 1.2, "impact": -0.05}
            },
            "base_value": 0.5
        }
        
        response = client.get("/api/v1/signals/AAPL/explain", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "features" in data
        assert isinstance(data["features"], dict)


def test_bulk_signals(client: TestClient, auth_headers: dict):
    """Test getting bulk signals for multiple symbols."""
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    with patch('app.services.signal_service.SignalService.generate_bulk_signals') as mock_bulk:
        # Mock bulk signal generation
        mock_bulk.return_value = [
            {
                "symbol": symbol,
                "signal": "BUY" if i % 2 == 0 else "SELL",
                "confidence": 0.75 + i * 0.05,
                "reasoning": f"Analysis for {symbol}",
                "price": 100.0 + i * 10.0,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            for i, symbol in enumerate(symbols)
        ]
        
        response = client.post("/api/v1/signals/bulk", 
                             json={"symbols": symbols}, 
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(symbols)