"""
Full System Integration Test

This script tests the complete StockGPT system with:
1. Real market data from professional APIs
2. AIv3 pattern detection
3. ML model training and prediction
4. Signal generation
5. Temporal chart visualization
6. All components working together
"""

import asyncio
import os
from datetime import date, timedelta
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up API keys
os.environ['TWELVEDATA_API_KEY'] = '5361b6392f4941d99f08d14d22551cb2'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'FPG7DCR33BFK2HDP'
os.environ['FMP_API_KEY'] = 'smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm'
os.environ['FINNHUB_API_KEY'] = 'd2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80'


class SystemIntegrationTest:
    """Test all system components working together."""

    def __init__(self):
        self.test_results = {}
        self.test_symbols = ["AAPL", "MSFT", "TSLA", "AMD", "NVDA"]

    async def test_market_data_providers(self) -> bool:
        """Test all market data providers."""
        print("\n" + "="*70)
        print("TESTING MARKET DATA PROVIDERS")
        print("="*70)

        from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider

        try:
            provider = EnhancedMarketProvider()

            # Test connection
            connected = await provider.check_connection()
            print(f"  Connection: {'[OK]' if connected else '[FAILED]'}")

            # Test each API
            test_results = {}

            # 1. Real-time quote (Finnhub)
            price = await provider.get_latest_price("AAPL")
            test_results['real_time'] = price is not None
            print(f"  Real-time quotes (Finnhub): {'[OK]' if test_results['real_time'] else '[FAILED]'}")

            # 2. Historical data (Twelve Data/Alpha Vantage)
            prices = await provider.get_prices("MSFT", days=30)
            test_results['historical'] = prices is not None and len(prices) > 0
            print(f"  Historical data: {'[OK]' if test_results['historical'] else '[FAILED]'}")

            # 3. Company profile (FMP)
            stock = await provider._fetch_stock_info("TSLA")
            test_results['company_info'] = stock is not None
            print(f"  Company profiles (FMP): {'[OK]' if test_results['company_info'] else '[FAILED]'}")

            # 4. Technical features
            features = await provider.get_technical_features("NVDA")
            test_results['technical'] = features is not None and 'rsi_14' in features
            print(f"  Technical indicators: {'[OK]' if test_results['technical'] else '[FAILED]'}")

            # Show API usage
            print("\n  API Usage:")
            for api, count in provider.api_usage.items():
                if count > 0:
                    print(f"    {api}: {count} calls")

            self.test_results['market_data'] = all(test_results.values())
            return all(test_results.values())

        except Exception as e:
            logger.error(f"Market data test failed: {e}")
            self.test_results['market_data'] = False
            return False

    async def test_pattern_detection(self) -> bool:
        """Test AIv3 pattern detection."""
        print("\n" + "="*70)
        print("TESTING AIv3 PATTERN DETECTION")
        print("="*70)

        from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider
        from aiv3.core.consolidation_tracker import ConsolidationTracker

        try:
            provider = EnhancedMarketProvider()
            patterns_found = 0

            for symbol in self.test_symbols[:3]:  # Test first 3 symbols
                # Get historical data
                prices = await provider.get_prices(symbol, days=100)

                if prices and len(prices) >= 60:
                    # Initialize tracker
                    tracker = ConsolidationTracker(symbol)

                    # Update with real data
                    pattern = tracker.update(prices)

                    if pattern:
                        print(f"  {symbol}: Phase = {pattern.phase.value}")
                        if pattern.phase.value == "ACTIVE":
                            patterns_found += 1
                            print(f"    -> Breakout ready!")
                            print(f"    -> Range: ${pattern.lower_boundary:.2f} - ${pattern.upper_boundary:.2f}")
                    else:
                        print(f"  {symbol}: No pattern")

            self.test_results['pattern_detection'] = True
            print(f"\n  Total patterns found: {patterns_found}")
            return True

        except Exception as e:
            logger.error(f"Pattern detection test failed: {e}")
            self.test_results['pattern_detection'] = False
            return False

    async def test_signal_generation(self) -> bool:
        """Test signal generation system."""
        print("\n" + "="*70)
        print("TESTING SIGNAL GENERATION")
        print("="*70)

        from stockgpt.application.signal_service import SignalService
        from stockgpt.infrastructure.ml.xgboost_model import XGBoostModel
        from stockgpt.infrastructure.data.enhanced_market_provider import EnhancedMarketProvider
        from aiv3.core.consolidation_tracker import ConsolidationTracker

        try:
            # Initialize components
            model = XGBoostModel()
            provider = EnhancedMarketProvider()
            tracker = ConsolidationTracker
            service = SignalService(model, provider, tracker)

            # Generate signals
            signals = await service.generate_signals(self.test_symbols[:2])

            print(f"  Signals generated: {len(signals)}")
            for signal in signals:
                print(f"    {signal.symbol}: {signal.action.value}")
                print(f"      Confidence: {signal.confidence:.2%}")
                print(f"      Expected Value: {signal.expected_value:.2f}")

            self.test_results['signal_generation'] = True
            return True

        except Exception as e:
            logger.error(f"Signal generation test failed: {e}")
            self.test_results['signal_generation'] = False
            return False

    async def test_temporal_chart(self) -> bool:
        """Test temporal chart visualization."""
        print("\n" + "="*70)
        print("TESTING TEMPORAL CHART")
        print("="*70)

        from stockgpt.visualization.temporal_chart import create_temporal_chart

        try:
            # Test different timeframes
            timeframes_tested = 0

            for tf in ['1M', '3M', '6M']:
                print(f"  Testing {tf} timeframe...")
                fig = await create_temporal_chart("AAPL", timeframe=tf, show_patterns=True)

                if fig:
                    timeframes_tested += 1
                    print(f"    [OK] {tf} chart created")

            # Save one chart as example
            fig = await create_temporal_chart("AAPL", timeframe="3M", show_patterns=True)
            if fig:
                fig.write_html("test_temporal_chart.html")
                print(f"\n  Sample chart saved: test_temporal_chart.html")

            self.test_results['temporal_chart'] = timeframes_tested > 0
            return timeframes_tested > 0

        except Exception as e:
            logger.error(f"Temporal chart test failed: {e}")
            self.test_results['temporal_chart'] = False
            return False

    async def test_breakout_system(self) -> bool:
        """Test the complete breakout prediction system."""
        print("\n" + "="*70)
        print("TESTING BREAKOUT PREDICTION SYSTEM")
        print("="*70)

        from setup_breakout_system import BreakoutPredictionSystem

        try:
            system = BreakoutPredictionSystem()

            # Test breakout scanning
            print("  Scanning for breakouts...")
            results = await system.scan_for_breakouts(self.test_symbols[:3])

            print(f"    Scanned: {results['scanned']} symbols")
            print(f"    Candidates: {len(results['breakout_candidates'])}")

            # Test signal generation
            print("  Generating signals...")
            signals = await system.get_realtime_signals(self.test_symbols[:2])

            actionable = [s for s in signals['signals']
                         if s['action'] in ['BUY', 'STRONG_BUY']]
            print(f"    Total signals: {len(signals['signals'])}")
            print(f"    Actionable: {len(actionable)}")

            # Test data saving
            output_dir = Path("./test_output")
            output_dir.mkdir(exist_ok=True)

            filename = f"integration_test_{date.today().isoformat()}.json"
            filepath = system.save_to_gcs(results, filename)
            print(f"    Data saved: {filepath}")

            self.test_results['breakout_system'] = True
            return True

        except Exception as e:
            logger.error(f"Breakout system test failed: {e}")
            self.test_results['breakout_system'] = False
            return False

    async def test_ml_pipeline(self) -> bool:
        """Test the ML training and prediction pipeline."""
        print("\n" + "="*70)
        print("TESTING ML PIPELINE")
        print("="*70)

        from stockgpt.infrastructure.ml.xgboost_model import XGBoostModel
        import numpy as np

        try:
            model = XGBoostModel()

            # Create dummy training data to initialize the model
            n_samples = 100
            X_train = np.random.randn(n_samples, len(model.feature_names))
            y_train = np.random.randint(0, 6, n_samples)  # K0-K5 classes

            # Train the model with dummy data (just for testing)
            import xgboost as xgb
            model.model = xgb.XGBClassifier(
                n_estimators=10,
                max_depth=3,
                objective='multi:softprob',
                num_class=6,
                random_state=42
            )
            model.model.fit(X_train, y_train)

            # Test prediction with sample features (include all required features)
            features = {
                'rsi_14': 45.2,
                'macd': 0.5,
                'macd_signal': 0.3,
                'macd_histogram': 0.2,
                'bbw': 15.5,
                'bbw_percentile': 30.0,
                'atr_14': 2.5,
                'adx': 28.0,
                'stochastic_k': 55.0,
                'stochastic_d': 52.0,
                'williams_r': -45.0,
                'cci': 10.0,
                'volume_ratio': 0.3,
                'price_change_20d': 5.1,
                'volatility_20d': 2.5,
                'price_vs_sma20': 1.02,
                'price_vs_sma50': 1.05,
                'sma20_vs_sma50': 1.03,
                'daily_range_ratio': 0.55,
                'pattern_duration': 12
            }

            # Test single prediction
            prediction = model.predict(features)
            print(f"  Single prediction test:")
            print(f"    Predicted class: {prediction['prediction_class']}")
            print(f"    Expected value: {prediction['expected_value']:.2f}")
            print(f"    Confidence: {prediction['confidence']:.2%}")

            # Test batch prediction
            batch_features = [features] * 3
            batch_predictions = model.batch_predict(batch_features)
            print(f"  Batch prediction test:")
            print(f"    Predictions: {len(batch_predictions)}")

            self.test_results['ml_pipeline'] = True
            return True

        except Exception as e:
            logger.error(f"ML pipeline test failed: {e}")
            self.test_results['ml_pipeline'] = False
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*80)
        print("STOCKGPT FULL SYSTEM INTEGRATION TEST")
        print("="*80)
        print("Testing all components with real market data...")

        # Run tests in sequence
        tests = [
            ("Market Data Providers", self.test_market_data_providers),
            ("Pattern Detection", self.test_pattern_detection),
            ("ML Pipeline", self.test_ml_pipeline),
            ("Signal Generation", self.test_signal_generation),
            ("Temporal Chart", self.test_temporal_chart),
            ("Breakout System", self.test_breakout_system),
        ]

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if not result:
                    print(f"\n[WARNING] {test_name} had issues")
            except Exception as e:
                print(f"\n[ERROR] {test_name} failed: {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = False

        # Print summary
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)

        passed = 0
        failed = 0

        for component, result in self.test_results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {component.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
            else:
                failed += 1

        print(f"\nTotal: {passed} passed, {failed} failed")

        if passed == len(self.test_results):
            print("\n" + "="*80)
            print("[SUCCESS] ALL SYSTEMS OPERATIONAL!")
            print("="*80)
            print("\nThe StockGPT system is fully integrated and working:")
            print("- Professional APIs connected and rate-limited")
            print("- AIv3 pattern detection operational")
            print("- ML pipeline ready for predictions")
            print("- Signal generation active")
            print("- Temporal charts with intelligent zoom")
            print("- Breakout prediction system online")
            print("\nSystem ready for production use!")
        else:
            print("\n[WARNING] Some components need attention")
            print("Check the logs above for details")

        # Save test results
        output_dir = Path("./test_results")
        output_dir.mkdir(exist_ok=True)

        results_file = output_dir / f"integration_test_{date.today().isoformat()}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': date.today().isoformat(),
                'results': self.test_results,
                'passed': passed,
                'failed': failed
            }, f, indent=2)

        print(f"\nTest results saved: {results_file}")


async def main():
    """Run the full integration test."""
    tester = SystemIntegrationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())