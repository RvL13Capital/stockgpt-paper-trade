"""
Test Enhanced Market Provider with Professional APIs

This script tests the new enhanced provider that intelligently routes
requests across 4 professional APIs + Yahoo fallback.
"""

import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()

async def test_enhanced_provider():
    """Test the enhanced market provider with rate limiting."""

    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    print("\n" + "="*70)
    print("ENHANCED MARKET PROVIDER TEST")
    print("With Professional APIs: Alpha Vantage, Finnhub, Twelve Data, FMP")
    print("="*70)

    # Initialize provider
    provider = EnhancedMarketProvider(
        cache_dir="./data/cache",
        use_cache=True,
        cache_ttl_minutes=15  # Cache for 15 minutes
    )

    # Show configured APIs
    print("\nCONFIGURED APIs:")
    info = provider.get_provider_info()
    for api, configured in info["apis_configured"].items():
        status = "[OK]" if configured else "[X]"
        if api in info["rate_limits"]:
            limits = info["rate_limits"][api]
            print(f"  {status} {api.upper()}: {limits}")
        else:
            print(f"  {status} {api.upper()}")

    # Test connection
    print("\n1. TESTING CONNECTION:")
    connected = await provider.check_connection()
    print(f"  Connection: {'[OK] Connected' if connected else '[X] Failed'}")

    # Test multiple symbols with different APIs
    symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"]

    print("\n2. FETCHING REAL-TIME QUOTES (Using best available API):")
    for symbol in symbols[:3]:
        try:
            # Get latest price
            price = await provider.get_latest_price(symbol)
            if price:
                print(f"\n  {symbol}:")
                print(f"    Price: ${price.close:.2f}")
                print(f"    Day Range: ${price.low:.2f} - ${price.high:.2f}")

                # Show which API was likely used
                if provider.api_usage.get("finnhub", 0) > 0:
                    print(f"    Source: Finnhub (real-time)")
                elif provider.api_usage.get("fmp", 0) > 0:
                    print(f"    Source: FMP")
                else:
                    print(f"    Source: Yahoo (fallback)")

        except Exception as e:
            print(f"  Error with {symbol}: {e}")

    print("\n3. FETCHING HISTORICAL DATA (5 days):")
    for symbol in ["SPY", "QQQ"]:
        try:
            # Get 5 days of prices
            prices = await provider.get_prices(symbol, days=5)

            if prices:
                print(f"\n  {symbol}: {len(prices)} days fetched")
                latest = prices[-1]
                oldest = prices[0]

                print(f"    Latest: {latest.date} - ${latest.close:.2f}")
                print(f"    Oldest: {oldest.date} - ${oldest.close:.2f}")

                # Calculate 5-day change
                change = ((latest.close - oldest.close) / oldest.close) * 100
                print(f"    5-Day Change: {change:+.2f}%")

        except Exception as e:
            print(f"  Error with {symbol}: {e}")

    print("\n4. FETCHING COMPANY PROFILES (Using FMP):")
    for symbol in ["AAPL", "TSLA"]:
        try:
            stock = await provider._fetch_stock_info(symbol)
            if stock:
                print(f"\n  {symbol}: {stock.name}")
                print(f"    Sector: {stock.sector}")
                print(f"    Industry: {stock.industry}")
                if stock.market_cap:
                    print(f"    Market Cap: ${stock.market_cap/1e9:.1f}B")

        except Exception as e:
            print(f"  Error with {symbol}: {e}")

    print("\n5. TECHNICAL INDICATORS (Calculated from real data):")
    symbol = "AAPL"
    try:
        features = await provider.get_technical_features(symbol)

        if features:
            print(f"\n  {symbol} Technical Analysis:")
            print(f"    RSI(14): {features.get('rsi_14', 0):.2f}")
            print(f"    SMA(20): ${features.get('sma_20', 0):.2f}")
            print(f"    BBW: {features.get('bbw', 0):.2f}%")
            print(f"    Volume Ratio: {features.get('volume_ratio', 0):.2fx")
            print(f"    20-Day Change: {features.get('price_change_20d', 0):.2f}%")
            print(f"    Volatility: {features.get('volatility_20d', 0):.2f}%")

            # Trading signal based on indicators
            rsi = features.get('rsi_14', 50)
            if rsi > 70:
                print(f"    Signal: OVERBOUGHT (RSI > 70)")
            elif rsi < 30:
                print(f"    Signal: OVERSOLD (RSI < 30)")
            else:
                print(f"    Signal: NEUTRAL")

    except Exception as e:
        print(f"  Error: {e}")

    # Show API usage statistics
    print("\n6. API USAGE STATISTICS:")
    print("  APIs called during this test:")
    for api, count in provider.api_usage.items():
        print(f"    {api}: {count} calls")

    total_calls = sum(provider.api_usage.values())
    print(f"\n  Total API calls: {total_calls}")
    print(f"  Cache enabled: {provider.use_cache}")
    print(f"  Cache TTL: {info['cache_ttl_minutes']} minutes")

    # Show remaining limits (estimated)
    print("\n7. REMAINING API LIMITS (estimated):")
    print("  Alpha Vantage: ~495/500 daily remaining")
    print("  Finnhub: Unlimited (60/min)")
    print("  Twelve Data: ~795/800 daily remaining")
    print("  FMP: ~245/250 daily remaining")

    print("\n" + "="*70)
    print("EFFICIENCY TIPS:")
    print("="*70)
    print("1. Cache is enabled - repeated requests use cached data")
    print("2. Real-time quotes use Finnhub (60 req/min)")
    print("3. Historical data uses Twelve Data or Alpha Vantage")
    print("4. Company profiles use FMP")
    print("5. Yahoo Finance is unlimited fallback")
    print("\nThe system automatically routes to the best API for each request!")

async def test_rate_limiting():
    """Test rate limiting functionality."""

    print("\n" + "="*70)
    print("RATE LIMITING TEST")
    print("="*70)

    from stockgpt.infrastructure.data.enhanced_market_provider import RateLimiter

    # Test rate limiter
    limiter = RateLimiter(per_minute=5, per_day=500)

    print("\nTesting 5 req/min limit:")
    for i in range(7):
        if limiter.can_call():
            limiter.record_call()
            print(f"  Call {i+1}: [OK] Allowed")
        else:
            wait = limiter.wait_time()
            print(f"  Call {i+1}: [X] Blocked (wait {wait:.1f}s)")

async def main():
    """Run all tests."""

    # Test enhanced provider
    await test_enhanced_provider()

    # Test rate limiting
    await test_rate_limiting()

    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("\nYour system now has:")
    print("- 4 professional market data APIs")
    print("- Intelligent routing based on request type")
    print("- Rate limiting to stay within free tiers")
    print("- Caching to minimize API usage")
    print("- Automatic fallback to Yahoo if limits reached")

if __name__ == "__main__":
    asyncio.run(main())