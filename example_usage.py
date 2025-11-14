"""
Example Usage of Refactored StockGPT System

This script demonstrates how to use the refactored architecture
with real market data for pattern detection and signal generation.
"""

import asyncio
import logging
from datetime import date, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_pattern_detection():
    """Example: Detect consolidation patterns in real market data."""
    from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
    from aiv3.core.consolidation_tracker import ConsolidationTracker

    print("\n" + "="*60)
    print("EXAMPLE 1: Real-Time Pattern Detection")
    print("="*60)

    # Initialize data provider (uses Yahoo Finance as free fallback)
    provider = MarketDataProvider(
        cache_dir="./data/cache",
        use_cache=True
    )

    # Check connection
    if await provider.check_connection():
        print("✓ Connected to market data provider")
    else:
        print("✗ Failed to connect to data provider")
        return

    # Symbols to scan (micro/small caps that often show patterns)
    symbols = ["AAPL", "TSLA", "AMD", "NVDA", "PLTR"]

    for symbol in symbols:
        print(f"\nScanning {symbol}...")

        # Get 100 days of real price data
        prices = await provider.get_prices(symbol, days=100)

        if len(prices) < 60:
            print(f"  Insufficient data for {symbol}")
            continue

        # Initialize pattern tracker
        tracker = ConsolidationTracker(symbol)

        # Update tracker with real price data
        pattern = tracker.update(prices)

        if pattern:
            print(f"  Pattern Status: {pattern.phase.value}")
            if pattern.phase.value == "ACTIVE":
                print(f"  Range: ${pattern.lower_boundary:.2f} - ${pattern.upper_boundary:.2f}")
                print(f"  Power Breakout Level: ${pattern.power_boundary:.2f}")
                print(f"  Days Active: {pattern.days_active}")
        else:
            print(f"  No pattern detected")

        # Get statistics
        stats = tracker.get_statistics()
        if stats['total_patterns'] > 0:
            print(f"  Historical: {stats['total_patterns']} patterns, "
                  f"{stats['success_rate']:.1%} success rate")


async def example_technical_analysis():
    """Example: Calculate real technical indicators from market data."""
    from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider

    print("\n" + "="*60)
    print("EXAMPLE 2: Technical Analysis with Real Data")
    print("="*60)

    provider = MarketDataProvider()

    symbol = "SPY"  # S&P 500 ETF
    print(f"\nAnalyzing {symbol}...")

    # Get latest technical features
    features = await provider.get_technical_features(symbol)

    if features:
        print("\nKey Technical Indicators (Real Values):")
        print(f"  Price: ${features.get('price', 0):.2f}")
        print(f"  RSI(14): {features.get('rsi_14', 0):.2f}")
        print(f"  MACD: {features.get('macd', 0):.4f}")
        print(f"  BBW: {features.get('bbw', 0):.2f}%")
        print(f"  Volume Ratio: {features.get('volume_ratio', 0):.2f}x")
        print(f"  20-day Change: {features.get('price_change_20d', 0):.2f}%")
        print(f"  Volatility: {features.get('volatility_20d', 0):.2f}%")
        print(f"  Price vs SMA20: {features.get('price_vs_sma20', 0):.2f}%")

        # Determine market condition
        if features.get('rsi_14', 50) > 70:
            print("\n⚠️  Market appears OVERBOUGHT")
        elif features.get('rsi_14', 50) < 30:
            print("\n⚠️  Market appears OVERSOLD")
        else:
            print("\n✓ Market in normal range")


async def example_model_training():
    """Example: Train model on real historical patterns."""
    from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
    from aiv3.ml.model_training_pipeline import ModelTrainingPipeline

    print("\n" + "="*60)
    print("EXAMPLE 3: Model Training on Real Patterns")
    print("="*60)

    provider = MarketDataProvider()
    pipeline = ModelTrainingPipeline(
        data_provider=provider,
        model_path="./models/example_model.pkl"
    )

    # Train on 6 months of data (for demo - use 2+ years in production)
    symbols = ["AAPL", "MSFT", "GOOGL"]
    start_date = date.today() - timedelta(days=180)
    end_date = date.today()

    print(f"\nTraining on {len(symbols)} symbols")
    print(f"Date range: {start_date} to {end_date}")
    print("This will take a few minutes...")

    try:
        results = await pipeline.train_model(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            optimize_hyperparameters=False  # Faster for demo
        )

        print("\n✓ Training Complete!")
        print(f"  Patterns found: {results['total_patterns']}")
        print(f"  Training accuracy: {results['train_accuracy']:.2%}")
        if 'val_accuracy' in results:
            print(f"  Validation accuracy: {results['val_accuracy']:.2%}")

        # Show class distribution
        print("\nPattern Outcome Distribution:")
        for class_name, count in results['class_distribution'].items():
            print(f"  {class_name}: {count} patterns")

    except ValueError as e:
        print(f"\n✗ Training failed: {e}")
        print("Note: Need more historical data for proper training")


async def example_signal_generation():
    """Example: Generate trading signals from patterns."""
    from stockgpt.infrastructure.data.market_data_provider import MarketDataProvider
    from stockgpt.infrastructure.ml.xgboost_model import XGBoostModel

    print("\n" + "="*60)
    print("EXAMPLE 4: Signal Generation")
    print("="*60)

    # Check if model exists
    model_path = "./models/example_model.pkl"
    if not Path(model_path).exists():
        print("✗ No trained model found. Run training example first.")
        return

    provider = MarketDataProvider()
    model = XGBoostModel(model_path)

    # Analyze current market
    symbols = ["AAPL", "TSLA", "AMD"]

    for symbol in symbols:
        print(f"\nAnalyzing {symbol}...")

        # Get current features
        features = await provider.get_technical_features(symbol)

        if not features:
            print(f"  Failed to get features for {symbol}")
            continue

        # Generate prediction
        try:
            prediction = model.predict(features)

            print(f"  Prediction: {prediction['prediction_class']}")
            print(f"  Confidence: {prediction['confidence']:.2%}")
            print(f"  Expected Value: {prediction['expected_value']:.2f}")
            print(f"  Signal: {prediction['signal_strength']}")

            # Show probability distribution
            print("  Probabilities:")
            for class_name, prob in prediction['probabilities'].items():
                print(f"    {class_name}: {prob:.2%}")

            # Trading recommendation
            if prediction['signal_strength'] == 'STRONG_SIGNAL':
                print(f"\n  💚 STRONG BUY SIGNAL for {symbol}!")
            elif prediction['signal_strength'] == 'GOOD_SIGNAL':
                print(f"\n  ✓ Good opportunity for {symbol}")
            elif prediction['failure_probability'] > 0.3:
                print(f"\n  🔴 AVOID {symbol} - High failure risk")

        except Exception as e:
            print(f"  Prediction failed: {e}")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("StockGPT Refactored System - Real Data Examples")
    print("="*60)

    # Run examples
    await example_pattern_detection()
    await example_technical_analysis()

    # Training takes longer, make it optional
    response = input("\n\nRun training example? (y/n): ")
    if response.lower() == 'y':
        await example_model_training()
        await example_signal_generation()

    print("\n" + "="*60)
    print("Examples Complete!")
    print("="*60)
    print("\nKey Takeaways:")
    print("✓ All data comes from real markets (Yahoo Finance)")
    print("✓ Pattern detection based on actual price movements")
    print("✓ Technical indicators calculated from real OHLCV data")
    print("✓ Model training uses historical patterns with real outcomes")
    print("✓ No mock data or random values in production code")


if __name__ == "__main__":
    asyncio.run(main())