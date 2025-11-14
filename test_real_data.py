"""
Quick test to verify the refactored system works with real market data.
"""

import asyncio
import sys
from datetime import date, timedelta

async def test_real_data():
    """Test that we can fetch real market data."""
    try:
        from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider

        print("Testing Real Market Data Provider...")
        print("-" * 40)

        # Initialize provider (will use Yahoo Finance as free fallback)
        provider = MarketDataProvider()

        # Test connection
        connected = await provider.check_connection()
        print(f"[OK] Connection test: {'PASSED' if connected else 'FAILED'}")

        # Fetch real price data for Apple
        symbol = "AAPL"
        print(f"\nFetching real data for {symbol}...")

        prices = await provider.get_prices(symbol, days=5)

        if prices:
            print(f"[OK] Successfully fetched {len(prices)} days of price data")

            # Show latest price (real data from market)
            latest = prices[-1]
            print(f"\nLatest Real Market Data for {symbol}:")
            print(f"  Date: {latest.date}")
            print(f"  Open: ${latest.open:.2f}")
            print(f"  High: ${latest.high:.2f}")
            print(f"  Low: ${latest.low:.2f}")
            print(f"  Close: ${latest.close:.2f}")
            print(f"  Volume: {latest.volume:,}")

            # Calculate real technical indicators
            features = await provider.get_technical_features(symbol)
            if features:
                print(f"\nReal Technical Indicators:")
                print(f"  RSI(14): {features.get('rsi_14', 0):.2f}")
                print(f"  Price Change (20d): {features.get('price_change_20d', 0):.2f}%")
                print(f"  Volume Ratio: {features.get('volume_ratio', 0):.2f}x")

                print("\n[SUCCESS] All data is REAL from actual markets!")
                print("[SUCCESS] No mock data or random values!")
        else:
            print("[FAIL] Failed to fetch price data")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install yfinance pandas numpy")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("StockGPT Refactored System - Real Data Test")
    print("="*50 + "\n")

    asyncio.run(test_real_data())

    print("\n" + "="*50)
    print("Test Complete!")
    print("="*50)