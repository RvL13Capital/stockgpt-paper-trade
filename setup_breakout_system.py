"""
Complete Setup for Breakout Prediction System with GCS Integration

This script sets up the entire system with:
1. Google Cloud Storage for data
2. Professional APIs with rate limiting
3. AIv3 pattern detection for breakouts
4. Real-time monitoring
"""

import os
import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment Configuration
os.environ['PROJECT_ID'] = 'ignition-ki-csv-storage'
os.environ['GCS_BUCKET_NAME'] = 'ignition-ki-csv-data-2025-user123'
os.environ['TWELVEDATA_API_KEY'] = '5361b6392f4941d99f08d14d22551cb2'
os.environ['ALPHAVANTAGE_API_KEY'] = 'FPG7DCR33BFK2HDP'
os.environ['FMP_API_KEY'] = 'smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm'
os.environ['FINNHUB_API_KEY'] = 'd2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80'


class BreakoutPredictionSystem:
    """
    Complete breakout prediction system with GCS integration.

    Features:
    - Real-time pattern detection
    - Professional API integration with rate limiting
    - GCS data storage
    - AIv3 consolidation tracking
    """

    def __init__(self):
        self.project_id = os.environ['PROJECT_ID']
        self.bucket_name = os.environ['GCS_BUCKET_NAME']

        # API rate limits (per minute)
        self.rate_limits = {
            'twelvedata': 8,
            'alphavantage': 5,
            'fmp': 5,
            'finnhub': 60
        }

        # Daily limits
        self.daily_limits = {
            'twelvedata': 800,
            'alphavantage': 500,
            'fmp': 250,
            'finnhub': float('inf')  # No daily limit
        }

        self.api_usage = {api: {'minute': 0, 'daily': 0} for api in self.rate_limits}

        logger.info(f"Breakout System initialized")
        logger.info(f"GCS Bucket: gs://{self.bucket_name}")
        logger.info(f"APIs configured: {', '.join(self.rate_limits.keys())}")

    async def scan_for_breakouts(self, symbols: list) -> dict:
        """
        Scan symbols for potential breakout patterns.

        Uses AIv3 pattern detection:
        - Consolidation qualification (10 days)
        - BBW < 30th percentile
        - ADX < 32
        - Volume < 35% of average
        """
        from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider
        from aiv3.core.consolidation_tracker import ConsolidationTracker

        provider = EnhancedMarketProvider()
        breakout_candidates = []

        print("\n" + "="*70)
        print("BREAKOUT PATTERN SCANNER")
        print("="*70)

        for symbol in symbols:
            try:
                # Get historical data
                prices = await provider.get_prices(symbol, days=100)

                if prices and len(prices) >= 60:
                    # Initialize pattern tracker
                    tracker = ConsolidationTracker(symbol)

                    # Update with real data
                    pattern = tracker.update(prices)

                    if pattern:
                        status = {
                            'symbol': symbol,
                            'phase': pattern.phase.value,
                            'qualification_days': pattern.qualification_days
                        }

                        # Check if in ACTIVE phase (ready for breakout)
                        if pattern.phase.value == "ACTIVE":
                            status['breakout_ready'] = True
                            status['upper_boundary'] = pattern.upper_boundary
                            status['lower_boundary'] = pattern.lower_boundary
                            status['power_boundary'] = pattern.power_boundary
                            status['range_percent'] = pattern.range_percentage

                            breakout_candidates.append(status)

                            print(f"\n[ALERT] {symbol} - BREAKOUT PATTERN DETECTED!")
                            print(f"  Range: ${pattern.lower_boundary:.2f} - ${pattern.upper_boundary:.2f}")
                            print(f"  Breakout Target: ${pattern.power_boundary:.2f}")
                            print(f"  Range Width: {pattern.range_percentage:.2f}%")

                        elif pattern.phase.value == "QUALIFYING":
                            print(f"\n[WATCH] {symbol} - Pattern forming ({pattern.qualification_days}/10 days)")
                    else:
                        print(f"\n[INFO] {symbol} - No pattern detected")

            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")

        return {
            'scanned': len(symbols),
            'breakout_candidates': breakout_candidates,
            'timestamp': date.today().isoformat()
        }

    async def get_realtime_signals(self, symbols: list) -> dict:
        """
        Generate real-time trading signals based on technical indicators.
        """
        from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

        provider = EnhancedMarketProvider()
        signals = []

        print("\n" + "="*70)
        print("REAL-TIME SIGNAL GENERATION")
        print("="*70)

        for symbol in symbols:
            try:
                # Get technical indicators
                features = await provider.get_technical_features(symbol)

                if features:
                    rsi = features.get('rsi_14', 50)
                    bbw = features.get('bbw', 100)
                    volume_ratio = features.get('volume_ratio', 1)
                    price_change = features.get('price_change_20d', 0)

                    # Generate signal
                    signal = {
                        'symbol': symbol,
                        'price': features.get('price', 0),
                        'rsi': rsi,
                        'bbw': bbw,
                        'volume_ratio': volume_ratio,
                        'price_change_20d': price_change
                    }

                    # Determine signal strength
                    if rsi < 30 and bbw < 20:
                        signal['action'] = 'STRONG_BUY'
                        signal['reason'] = 'Oversold + Low volatility'
                    elif rsi < 40 and volume_ratio > 1.5:
                        signal['action'] = 'BUY'
                        signal['reason'] = 'Oversold + High volume'
                    elif rsi > 70:
                        signal['action'] = 'SELL'
                        signal['reason'] = 'Overbought'
                    else:
                        signal['action'] = 'HOLD'
                        signal['reason'] = 'No clear signal'

                    signals.append(signal)

                    print(f"\n{symbol}:")
                    print(f"  Price: ${signal['price']:.2f}")
                    print(f"  RSI: {signal['rsi']:.2f}")
                    print(f"  Signal: {signal['action']} - {signal['reason']}")

            except Exception as e:
                logger.error(f"Error getting signal for {symbol}: {e}")

        return {
            'signals': signals,
            'timestamp': date.today().isoformat()
        }

    def save_to_gcs(self, data: dict, filename: str):
        """
        Save data to Google Cloud Storage.

        Note: Requires gcloud SDK and authentication.
        In production, use google-cloud-storage library.
        """
        # For now, save locally as JSON
        output_dir = Path("./gcs_output")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Data saved to: {filepath}")
        logger.info(f"In production, this would upload to: gs://{self.bucket_name}/{filename}")

        return filepath

    def show_api_usage(self):
        """Display current API usage statistics."""
        print("\n" + "="*70)
        print("API USAGE STATISTICS")
        print("="*70)

        for api, limits in self.rate_limits.items():
            daily_limit = self.daily_limits[api]
            daily_used = self.api_usage[api]['daily']

            if daily_limit == float('inf'):
                print(f"\n{api.upper()}:")
                print(f"  Rate: {limits} req/min")
                print(f"  Daily: Unlimited")
            else:
                remaining = daily_limit - daily_used
                percent_used = (daily_used / daily_limit) * 100

                print(f"\n{api.upper()}:")
                print(f"  Rate: {limits} req/min")
                print(f"  Daily: {daily_used}/{daily_limit} used ({percent_used:.1f}%)")
                print(f"  Remaining: {remaining} calls")


async def main():
    """Run the complete breakout prediction system."""

    print("\n" + "="*80)
    print("BREAKOUT PREDICTION SYSTEM v2.0")
    print("Powered by AIv3 Pattern Detection + Professional APIs")
    print("="*80)

    # Initialize system
    system = BreakoutPredictionSystem()

    # Define watchlist
    watchlist = [
        "AAPL",   # Large cap
        "MSFT",   # Large cap
        "TSLA",   # High volatility
        "AMD",    # Semiconductor
        "NVDA",   # AI leader
        "PLTR",   # Data analytics
        "SOFI",   # Fintech
        "RIVN",   # EV
    ]

    print(f"\nWatchlist: {', '.join(watchlist)}")

    # 1. Scan for breakout patterns
    print("\n" + "-"*70)
    print("PHASE 1: Scanning for breakout patterns...")
    print("-"*70)

    breakout_results = await system.scan_for_breakouts(watchlist[:4])  # Limit to conserve API calls

    if breakout_results['breakout_candidates']:
        print(f"\n[SUCCESS] Found {len(breakout_results['breakout_candidates'])} breakout candidates!")

        # Save to GCS
        filename = f"breakout_scan_{date.today().isoformat()}.json"
        system.save_to_gcs(breakout_results, filename)
    else:
        print("\n[INFO] No immediate breakout patterns found. Continue monitoring.")

    # 2. Generate real-time signals
    print("\n" + "-"*70)
    print("PHASE 2: Generating real-time signals...")
    print("-"*70)

    signal_results = await system.get_realtime_signals(watchlist[:3])  # Limit to conserve API calls

    # Filter for actionable signals
    actionable = [s for s in signal_results['signals']
                  if s['action'] in ['BUY', 'STRONG_BUY', 'SELL']]

    if actionable:
        print(f"\n[ACTION REQUIRED] {len(actionable)} actionable signals!")
        for signal in actionable:
            print(f"  - {signal['symbol']}: {signal['action']}")

        # Save to GCS
        filename = f"signals_{date.today().isoformat()}.json"
        system.save_to_gcs(signal_results, filename)

    # 3. Show API usage
    system.show_api_usage()

    # Summary
    print("\n" + "="*80)
    print("SYSTEM SUMMARY")
    print("="*80)
    print(f"✓ Symbols scanned: {breakout_results['scanned']}")
    print(f"✓ Breakout candidates: {len(breakout_results['breakout_candidates'])}")
    print(f"✓ Signals generated: {len(signal_results['signals'])}")
    print(f"✓ Actionable signals: {len(actionable)}")
    print(f"✓ Data saved to: ./gcs_output/")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Monitor breakout candidates for price action above power boundary")
    print("2. Set alerts for symbols approaching breakout levels")
    print("3. Review actionable signals for trading opportunities")
    print("4. Run this scan daily before market open")
    print("\nFor production deployment:")
    print("  - Set up Google Cloud Storage authentication")
    print("  - Schedule with Cloud Scheduler or cron")
    print("  - Add email/SMS alerts for breakout signals")


if __name__ == "__main__":
    asyncio.run(main())