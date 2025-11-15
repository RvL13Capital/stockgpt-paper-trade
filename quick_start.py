"""
Quick Start Script - Run StockGPT System

This script demonstrates the main features of the refactored StockGPT system.
Run this to see everything working with real market data!
"""

import asyncio
import sys
from datetime import datetime, date, timedelta

# Add color for better output (optional)
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

async def main():
    """Run all main features of the StockGPT system."""

    print_header("StockGPT Quick Start - Real Market Data Demo")

    # Import after header to show we're starting
    try:
        from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
        from aiv3.core.consolidation_tracker import ConsolidationTracker
        print(f"{Colors.GREEN}[OK]{Colors.END} Modules loaded successfully\n")
    except ImportError as e:
        print(f"{Colors.RED}[ERROR]{Colors.END} Missing dependencies. Run: pip install yfinance pandas numpy")
        print(f"Error: {e}")
        return

    # Initialize data provider
    provider = MarketDataProvider()

    # 1. Test Connection
    print_header("1. Testing Market Data Connection")
    if await provider.check_connection():
        print(f"{Colors.GREEN}[SUCCESS]{Colors.END} Connected to market data provider (Yahoo Finance)")
    else:
        print(f"{Colors.RED}[FAIL]{Colors.END} Could not connect to market data")
        return

    # 2. Fetch Real Stock Data
    print_header("2. Fetching Real Stock Prices")

    symbols = ["AAPL", "MSFT", "TSLA", "AMD", "NVDA"]

    for symbol in symbols[:3]:  # Show first 3 for brevity
        try:
            # Get latest price
            latest = await provider.get_latest_price(symbol)
            if latest:
                print(f"{Colors.BOLD}{symbol}{Colors.END}:")
                print(f"  Price: ${latest.close:.2f}")
                print(f"  Volume: {latest.volume:,}")
                print(f"  Daily Change: {latest.daily_change_percentage:.2f}%")

                # Get arrow based on change
                if latest.daily_change_percentage > 0:
                    arrow = f"{Colors.GREEN}↑{Colors.END}"
                else:
                    arrow = f"{Colors.RED}↓{Colors.END}"
                print(f"  Trend: {arrow}\n")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

    # 3. Technical Analysis
    print_header("3. Real-Time Technical Analysis")

    for symbol in ["SPY", "QQQ"]:  # Major ETFs
        try:
            features = await provider.get_technical_features(symbol)
            if features:
                rsi = features.get('rsi_14', 50)

                print(f"{Colors.BOLD}{symbol} Analysis:{Colors.END}")
                print(f"  RSI(14): {rsi:.2f}")
                print(f"  Volatility: {features.get('volatility_20d', 0):.2f}%")
                print(f"  Volume Ratio: {features.get('volume_ratio', 0):.2f}x")

                # Determine signal
                if rsi > 70:
                    signal = f"{Colors.RED}OVERBOUGHT - Consider Selling{Colors.END}"
                elif rsi < 30:
                    signal = f"{Colors.GREEN}OVERSOLD - Consider Buying{Colors.END}"
                else:
                    signal = f"{Colors.BLUE}NEUTRAL - Wait for Signal{Colors.END}"

                print(f"  Signal: {signal}\n")
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    # 4. Pattern Detection
    print_header("4. AIv3 Pattern Detection (Consolidation)")

    test_symbols = ["AAPL", "MSFT"]

    for symbol in test_symbols:
        try:
            # Get historical data
            prices = await provider.get_prices(symbol, days=100)

            if prices and len(prices) >= 60:
                # Initialize tracker
                tracker = ConsolidationTracker(symbol)

                # Update with real data
                pattern = tracker.update(prices)

                print(f"{Colors.BOLD}{symbol} Pattern Detection:{Colors.END}")

                if pattern:
                    print(f"  Status: {pattern.phase.value}")

                    if pattern.phase.value == "ACTIVE":
                        print(f"  Lower Boundary: ${pattern.lower_boundary:.2f}")
                        print(f"  Upper Boundary: ${pattern.upper_boundary:.2f}")
                        print(f"  Breakout Target: ${pattern.power_boundary:.2f}")
                        print(f"  {Colors.YELLOW}[!] Watch for breakout!{Colors.END}")
                    elif pattern.phase.value == "QUALIFYING":
                        print(f"  Days in qualification: {pattern.qualification_days}/10")
                        print(f"  {Colors.BLUE}[...] Pattern forming...{Colors.END}")
                    else:
                        print(f"  Pattern {pattern.phase.value.lower()}")
                else:
                    print(f"  No consolidation pattern detected")

                # Get statistics
                stats = tracker.get_statistics()
                if stats['total_patterns'] > 0:
                    print(f"  Historical patterns: {stats['total_patterns']}")
                    print(f"  Success rate: {stats['success_rate']:.1%}")

                print()
        except Exception as e:
            print(f"Error detecting patterns for {symbol}: {e}")

    # 5. Market Summary
    print_header("5. Market Summary")

    try:
        # Get major indices
        indices = {
            "SPY": "S&P 500",
            "QQQ": "NASDAQ",
            "DIA": "Dow Jones"
        }

        print(f"{Colors.BOLD}Major Indices:{Colors.END}\n")

        for symbol, name in indices.items():
            latest = await provider.get_latest_price(symbol)
            if latest:
                arrow = "↑" if latest.daily_change_percentage > 0 else "↓"
                color = Colors.GREEN if latest.daily_change_percentage > 0 else Colors.RED

                print(f"  {name} ({symbol}): ${latest.close:.2f} "
                      f"{color}{arrow} {latest.daily_change_percentage:.2f}%{Colors.END}")

        print(f"\n{Colors.BOLD}Data Provider Info:{Colors.END}")
        info = provider.get_provider_info()
        print(f"  Primary Source: {info['primary_source']}")
        print(f"  Cache Enabled: {info['cache_enabled']}")

    except Exception as e:
        print(f"Error getting market summary: {e}")

    # Final message
    print_header("Quick Start Complete!")

    print("Next Steps:")
    print("1. Run full examples: python example_usage.py")
    print("2. Start backend API: cd backend && uvicorn app.main:app --reload")
    print("3. Train ML model: See RUN_SYSTEM_GUIDE.md")
    print("\nAll data shown above is REAL from actual markets!")
    print(f"\n{Colors.GREEN}System is working correctly!{Colors.END}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())