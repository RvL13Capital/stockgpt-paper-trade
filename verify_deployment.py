#!/usr/bin/env python3
"""
StockGPT Deployment Verification Script
Verifies that all components are properly deployed and functional.
"""

import requests
import sys
import time
from typing import Dict, List, Tuple


def test_endpoint(url: str, method: str = "GET", headers: Dict = None, data: Dict = None, timeout: int = 10) -> Tuple[bool, Dict]:
    """Test an API endpoint and return result."""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        return response.status_code == 200, {
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "content_length": len(response.content)
        }
    except Exception as e:
        return False, {"error": str(e)}


def main():
    """Main verification function."""
    print("🔍 StockGPT Deployment Verification")
    print("=" * 50)
    
    base_url = "http://localhost"
    api_base = f"{base_url}/api/v1"
    
    tests = [
        # Health checks
        ("Simple Health Check", f"{base_url}/health", "GET"),
        ("Detailed Health Check", f"{api_base}/health/health", "GET"),
        ("Metrics Check", f"{api_base}/health/metrics", "GET"),
        
        # API endpoints
        ("API Documentation", f"{base_url}/api/docs", "GET"),
        ("Frontend", f"{base_url}", "GET"),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_name, url, method in tests:
        print(f"\n📋 Testing: {test_name}")
        print(f"   URL: {url}")
        
        success, details = test_endpoint(url, method)
        
        if success:
            print(f"   ✅ PASSED")
            if "response_time" in details:
                print(f"      Response time: {details['response_time']:.3f}s")
            passed += 1
        else:
            print(f"   ❌ FAILED")
            if "status_code" in details:
                print(f"      Status code: {details['status_code']}")
            if "error" in details:
                print(f"      Error: {details['error']}")
            failed += 1
        
        results.append({
            "name": test_name,
            "url": url,
            "method": method,
            "success": success,
            "details": details
        })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print(f"   Total Tests: {len(results)}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Success Rate: {(passed/len(results))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! StockGPT is ready for use.")
        print("\n🌐 Access the application:")
        print("   Frontend: http://localhost")
        print("   API Docs: http://localhost/api/docs")
        print("   Health:   http://localhost/api/health/health")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())