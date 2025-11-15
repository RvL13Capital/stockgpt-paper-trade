"""
Test Pattern Chart with Real Data

This script tests the pattern-focused charting with subtle highlighting
and temporal context windows.
"""

import asyncio
import os
from datetime import datetime, timedelta
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set API keys
os.environ['TWELVEDATA_API_KEY'] = '5361b6392f4941d99f08d14d22551cb2'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'FPG7DCR33BFK2HDP'
os.environ['FMP_API_KEY'] = 'smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm'
os.environ['FINNHUB_API_KEY'] = 'd2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80'


async def test_pattern_visualization():
    """Test the enhanced pattern visualization with real market data."""

    from stockgpt.visualization.pattern_chart import (
        PatternChart, PatternPeriod,
        analyze_historical_patterns,
        create_pattern_analysis_chart
    )
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    print("\n" + "="*70)
    print("PATTERN CHART TESTING")
    print("Subtle Highlighting + Temporal Context Windows")
    print("="*70)

    symbols_to_test = ["AAPL", "MSFT", "TSLA"]

    for symbol in symbols_to_test:
        print(f"\nAnalyzing {symbol}...")

        try:
            # 1. Analyze historical patterns
            patterns = await analyze_historical_patterns(symbol, lookback_days=365)

            if patterns:
                print(f"  Found {len(patterns)} patterns:")
                for i, pattern in enumerate(patterns[:3]):  # Show first 3
                    status = f"{pattern.outcome}"
                    if pattern.gain_percentage:
                        status += f" ({pattern.gain_percentage:.1f}% gain)"
                    print(f"    Pattern {i+1}: {status}")
                    print(f"      Period: {pattern.qualification_start} to {pattern.completion_date or 'ongoing'}")
                    if pattern.breakout_date:
                        print(f"      Breakout: {pattern.breakout_date}")

                # 2. Create overview chart with all patterns
                print(f"\n  Creating overview chart...")
                fig_overview = await create_pattern_analysis_chart(
                    symbol,
                    show_all_patterns=True
                )
                filename_overview = f"{symbol.lower()}_patterns_overview.html"
                fig_overview.write_html(filename_overview)
                print(f"  [OK] Saved: {filename_overview}")

                # 3. Create focused chart for most recent successful pattern
                successful_patterns = [p for p in patterns if p.outcome == 'success']
                if successful_patterns:
                    recent_success = successful_patterns[-1]
                    print(f"\n  Creating focused chart for successful pattern...")

                    # Check data availability
                    provider = EnhancedMarketProvider()
                    prices = await provider.get_prices(symbol, days=500)

                    # Calculate how many days we have after breakout
                    if recent_success.breakout_date:
                        prices_df = {p.date: p for p in prices}
                        days_after_breakout = 0
                        for price in reversed(prices):
                            if price.date > recent_success.breakout_date:
                                days_after_breakout += 1

                        print(f"    Data available: {days_after_breakout} days after breakout")
                        if days_after_breakout < 100:
                            print(f"    Note: Only {days_after_breakout} days available (100 requested)")

                    fig_focused = await create_pattern_analysis_chart(
                        symbol,
                        pattern_id=recent_success.pattern_id
                    )
                    filename_focused = f"{symbol.lower()}_pattern_focused.html"
                    fig_focused.write_html(filename_focused)
                    print(f"  [OK] Saved: {filename_focused}")
                else:
                    print(f"  No successful patterns found to focus on")

            else:
                print(f"  No patterns detected in {symbol}")

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            print(f"  [ERROR] {e}")

    # Test with a synthetic pattern for demonstration
    print("\n" + "="*70)
    print("SYNTHETIC PATTERN DEMONSTRATION")
    print("="*70)

    try:
        provider = EnhancedMarketProvider()
        prices = await provider.get_prices("SPY", days=200)

        if prices and len(prices) > 150:
            # Create a synthetic pattern for demonstration
            today = pd.Timestamp.now()
            pattern = PatternPeriod(
                symbol="SPY",
                pattern_id="SPY_DEMO",
                qualification_start=today - timedelta(days=60),
                active_start=today - timedelta(days=50),
                breakout_date=today - timedelta(days=30),
                completion_date=today,
                pattern_type='consolidation',
                upper_boundary=prices[-40].high * 1.02,
                lower_boundary=prices[-40].low * 0.98,
                power_boundary=prices[-40].high * 1.025,
                outcome='success',
                gain_percentage=12.5
            )

            # Create focused chart
            pattern_chart = PatternChart()
            fig = pattern_chart.create_pattern_focused_chart(
                prices=prices,
                pattern=pattern,
                context_before=40,
                context_after=30  # Limited to available data
            )

            fig.write_html("spy_demo_pattern.html")
            print("  [OK] Synthetic pattern demonstration saved: spy_demo_pattern.html")
            print("  This shows:")
            print("    - Subtle blue shading for qualification period")
            print("    - Light gold shading for active period")
            print("    - Light green shading for successful breakout")
            print("    - Boundary lines (upper, lower, power target)")
            print("    - Annotations for key events")

    except Exception as e:
        logger.error(f"Error creating demo: {e}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("Pattern charts created with:")
    print("- Subtle highlighting of pattern periods")
    print("- 40 days context before pattern activation")
    print("- Up to 100 days after breakout (when data available)")
    print("- Safe handling of limited future data")
    print("- Navigation between multiple patterns")
    print("\nOpen the HTML files to view interactive charts")


async def test_individual_pattern_focus():
    """Test focusing on individual patterns with full temporal context."""

    from stockgpt.visualization.pattern_chart import PatternChart, PatternPeriod
    from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

    print("\n" + "="*70)
    print("INDIVIDUAL PATTERN FOCUS TEST")
    print("="*70)

    symbol = "AAPL"
    provider = EnhancedMarketProvider()

    try:
        # Get 500 days of data to ensure we have context
        prices = await provider.get_prices(symbol, days=500)
        print(f"\nLoaded {len(prices)} days of data for {symbol}")

        # Create a test pattern from 100 days ago
        if len(prices) > 150:
            # Create pattern that started ~100 days ago
            pattern_start_idx = len(prices) - 100
            pattern = PatternPeriod(
                symbol=symbol,
                pattern_id=f"{symbol}_TEST",
                qualification_start=pd.Timestamp(prices[pattern_start_idx - 10].date),
                active_start=pd.Timestamp(prices[pattern_start_idx].date),
                breakout_date=pd.Timestamp(prices[pattern_start_idx + 20].date) if pattern_start_idx + 20 < len(prices) else None,
                completion_date=pd.Timestamp(prices[-1].date),
                pattern_type='consolidation',
                upper_boundary=prices[pattern_start_idx].high * 1.02,
                lower_boundary=prices[pattern_start_idx].low * 0.98,
                power_boundary=prices[pattern_start_idx].high * 1.025,
                outcome='ongoing' if pattern_start_idx + 20 >= len(prices) else 'success',
                gain_percentage=8.5
            )

            # Create chart with full context
            pattern_chart = PatternChart()

            # Test different context windows
            context_scenarios = [
                (40, 100, "standard"),  # Standard view
                (20, 50, "compact"),    # Compact view
                (60, 150, "extended")   # Extended view (may not have full data)
            ]

            for before, after, name in context_scenarios:
                print(f"\nCreating {name} view: {before} days before, {after} days after...")

                fig = pattern_chart.create_pattern_focused_chart(
                    prices=prices,
                    pattern=pattern,
                    context_before=before,
                    context_after=after,
                    show_indicators=True
                )

                filename = f"{symbol.lower()}_pattern_{name}.html"
                fig.write_html(filename)
                print(f"  [OK] Saved: {filename}")

            print("\nPattern Focus Features:")
            print("- Automatic adjustment when insufficient future data")
            print("- Warning messages about data availability")
            print("- Subtle period highlighting (qualification, active, post-breakout)")
            print("- Technical indicators in context")
            print("- Clear boundary visualization")

    except Exception as e:
        logger.error(f"Error in individual pattern test: {e}")
        print(f"[ERROR] {e}")


async def main():
    """Run all pattern chart tests."""

    print("\n" + "="*80)
    print("PATTERN CHART TESTING SUITE")
    print("="*80)
    print("Testing subtle highlighting and temporal context windows...")

    # Test 1: Pattern visualization with real data
    await test_pattern_visualization()

    # Test 2: Individual pattern focus with different context windows
    await test_individual_pattern_focus()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nFeatures demonstrated:")
    print("1. Subtle pattern period highlighting")
    print("2. Pattern-focused view (40 days before + 100 days after)")
    print("3. Safe handling of limited future data")
    print("4. Multiple pattern navigation")
    print("5. Boundary and event annotations")
    print("\nCheck the generated HTML files for interactive charts")


if __name__ == "__main__":
    asyncio.run(main())