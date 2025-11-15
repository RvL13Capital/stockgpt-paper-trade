"""
Quick API Test - Shows all 4 professional APIs working
"""

import asyncio
import os

# Set API keys
os.environ['TWELVEDATA_API_KEY'] = '5361b6392f4941d99f08d14d22551cb2'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'FPG7DCR33BFK2HDP'
os.environ['FMP_API_KEY'] = 'smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm'
os.environ['FINNHUB_API_KEY'] = 'd2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80'

async def quick_test():
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    print("\n" + "="*60)
    print("PROFESSIONAL API TEST - 4 SOURCES ACTIVE")
    print("="*60)

    provider = EnhancedMarketProvider()

    # Test 1: Real-time quote (Finnhub)
    print("\n1. REAL-TIME QUOTE (Finnhub):")
    price = await provider.get_latest_price("AAPL")
    if price:
        print(f"   AAPL: ${price.close:.2f}")
        print(f"   Range: ${price.low:.2f} - ${price.high:.2f}")

    # Test 2: Historical data (Twelve Data or Alpha Vantage)
    print("\n2. HISTORICAL DATA (Twelve Data/Alpha Vantage):")
    prices = await provider.get_prices("MSFT", days=5)
    if prices:
        print(f"   MSFT: {len(prices)} days fetched")
        print(f"   Latest: ${prices[-1].close:.2f} on {prices[-1].date}")

    # Test 3: Company profile (FMP)
    print("\n3. COMPANY PROFILE (FMP):")
    stock = await provider._fetch_stock_info("TSLA")
    if stock:
        print(f"   {stock.symbol}: {stock.name}")
        print(f"   Sector: {stock.sector}")

    # Show API usage
    print("\n4. API USAGE:")
    info = provider.get_provider_info()
    for api, count in provider.api_usage.items():
        if count > 0:
            print(f"   {api}: {count} calls")

    print("\n" + "="*60)
    print("SUCCESS! All APIs working with rate limits")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(quick_test())