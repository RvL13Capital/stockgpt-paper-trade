import pytest
import time
import asyncio
import aiohttp
from typing import List, Dict, Any
import statistics


class TestPerformance:
    """Performance tests for StockGPT."""
    
    @pytest.fixture(scope="class")
    def base_url(self) -> str:
        """Base URL for the application."""
        return "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def auth_token(self, base_url: str) -> str:
        """Get authentication token for testing."""
        import requests
        
        user_data = {
            "email": "perf_test@example.com",
            "password": "testpassword123"
        }
        
        try:
            requests.post(f"{base_url}/auth/register", json=user_data)
        except:
            pass
        
        response = requests.post(f"{base_url}/auth/login", json=user_data)
        return response.json()["access_token"]
    
    def measure_response_time(self, func, *args, **kwargs) -> float:
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result
    
    def test_api_response_times(self, base_url: str, auth_token: str):
        """Test API endpoint response times."""
        import requests
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        endpoints = [
            ("GET", f"{base_url}/portfolios"),
            ("GET", f"{base_url}/signals/AAPL"),
            ("GET", f"{base_url}/insights"),
            ("GET", f"{base_url}/journal"),
        ]
        
        response_times = []
        
        for method, url in endpoints:
            response_time, response = self.measure_response_time(
                requests.get if method == "GET" else requests.post,
                url, headers=headers
            )
            
            assert response.status_code == 200
            response_times.append(response_time)
            
            print(f"{method} {url}: {response_time:.3f}s")
        
        # Assert average response time is under 2 seconds
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s is too high"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, base_url: str, auth_token: str):
        """Test handling of concurrent requests."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async def make_request(session: aiohttp.ClientSession, url: str) -> float:
            """Make a single request and return response time."""
            start_time = time.time()
            async with session.get(url, headers=headers) as response:
                assert response.status == 200
                await response.json()
                return time.time() - start_time
        
        async with aiohttp.ClientSession() as session:
            # Test concurrent requests to different endpoints
            urls = [
                f"{base_url}/portfolios",
                f"{base_url}/signals/AAPL",
                f"{base_url}/insights",
                f"{base_url}/journal",
            ] * 5  # 20 total requests
            
            start_time = time.time()
            tasks = [make_request(session, url) for url in urls]
            response_times = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            print(f"Concurrent requests: {len(urls)} requests in {total_time:.3f}s")
            print(f"Average response time: {statistics.mean(response_times):.3f}s")
            
            # All requests should complete within reasonable time
            assert total_time < 10.0, f"Concurrent requests took too long: {total_time:.3f}s"
    
    def test_database_query_performance(self, base_url: str, auth_token: str):
        """Test database query performance."""
        import requests
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create multiple portfolios to test query performance
        for i in range(10):
            portfolio_data = {
                "name": f"Performance Portfolio {i}",
                "description": f"Portfolio {i} for performance testing",
                "initial_capital": 100000.0
            }
            requests.post(f"{base_url}/portfolios", json=portfolio_data, headers=headers)
        
        # Measure time to fetch all portfolios
        response_time, response = self.measure_response_time(
            requests.get, f"{base_url}/portfolios", headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 10
        
        print(f"Fetching {len(data)} portfolios: {response_time:.3f}s")
        assert response_time < 1.0, f"Database query took too long: {response_time:.3f}s"
    
    def test_ml_model_performance(self, base_url: str, auth_token: str):
        """Test ML model inference performance."""
        import requests
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test multiple symbol predictions
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        response_times = []
        
        for symbol in symbols:
            response_time, response = self.measure_response_time(
                requests.get, f"{base_url}/signals/{symbol}", headers=headers
            )
            
            if response.status_code == 200:
                response_times.append(response_time)
                print(f"ML prediction for {symbol}: {response_time:.3f}s")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            assert avg_time < 3.0, f"ML model inference too slow: {avg_time:.3f}s"
    
    def test_memory_usage(self, base_url: str, auth_token: str):
        """Test memory usage patterns."""
        import requests
        import psutil
        import os
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make multiple requests
        for i in range(100):
            response = requests.get(f"{base_url}/signals/AAPL", headers=headers)
            assert response.status_code == 200
            
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"Memory usage after {i} requests: {current_memory:.2f}MB")
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Memory increase: {memory_increase:.2f}MB")
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.2f}MB"