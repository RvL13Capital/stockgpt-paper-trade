"""
Signal Service - Application layer for signal generation

This service orchestrates signal generation using models, market data, and pattern detection.
"""

from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from dataclasses import dataclass
import logging

from stockgpt.core.entities.signal import Signal, SignalAction
from stockgpt.core.interfaces.model import IModel


logger = logging.getLogger(__name__)


class SignalService:
    """
    Service for generating trading signals.

    Combines market data, pattern detection, and ML models to generate signals.
    """

    def __init__(self,
                 model: IModel,
                 market_provider,
                 pattern_tracker):
        """
        Initialize signal service.

        Args:
            model: ML model for predictions
            market_provider: Market data provider
            pattern_tracker: Pattern detection tracker class
        """
        self.model = model
        self.market_provider = market_provider
        self.pattern_tracker_class = pattern_tracker

    async def generate_signals(self,
                              symbols: List[str],
                              min_confidence: float = 0.6,
                              min_expected_value: float = 1.0) -> List[Signal]:
        """
        Generate trading signals for a list of symbols.

        Args:
            symbols: List of stock symbols
            min_confidence: Minimum confidence threshold
            min_expected_value: Minimum expected value threshold

        Returns:
            List of Signal objects
        """
        signals = []

        for symbol in symbols:
            try:
                # Get market data
                prices = await self.market_provider.get_prices(symbol, days=100)

                if not prices or len(prices) < 60:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue

                # Detect patterns
                tracker = self.pattern_tracker_class(symbol)
                pattern = tracker.update(prices)

                # Get technical features
                features = await self.market_provider.get_technical_features(symbol)

                if not features:
                    logger.warning(f"No technical features for {symbol}")
                    continue

                # Prepare features for model
                model_features = self._prepare_features(features, pattern)

                # Get prediction
                prediction = self.model.predict(model_features)

                # Generate signal if criteria met
                if (prediction['confidence'] >= min_confidence and
                    prediction['expected_value'] >= min_expected_value):

                    signal = self._create_signal(
                        symbol=symbol,
                        prediction=prediction,
                        current_price=prices[-1].close,
                        pattern=pattern
                    )
                    signals.append(signal)

            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")

        return signals

    def _prepare_features(self,
                         technical_features: Dict[str, float],
                         pattern: Any) -> Dict[str, float]:
        """
        Prepare features for model prediction.

        Args:
            technical_features: Technical indicators
            pattern: Detected pattern

        Returns:
            Features dictionary for model
        """
        features = technical_features.copy()

        # Add pattern-based features if available
        if pattern:
            features['pattern_days'] = pattern.qualification_days
            features['consolidation_strength'] = pattern.consolidation_strength
            features['breakout_readiness'] = pattern.breakout_readiness
            features['range_percentage'] = pattern.range_percentage
        else:
            # Default values if no pattern
            features['pattern_days'] = 0
            features['consolidation_strength'] = 0
            features['breakout_readiness'] = 0
            features['range_percentage'] = 0

        # Add default values for any missing features
        default_features = {
            'bbw': 50,
            'adx': 25,
            'volume_ratio': 1.0,
            'daily_range_ratio': 1.0,
            'rsi_14': 50,
            'price_position': 0.5,
            'sma_20': features.get('price', 0),
            'sma_50': features.get('price', 0),
            'volume_20d_avg': 1000000,
            'price_change_5d': 0,
            'price_change_20d': 0,
            'volatility_20d': 0.02,
            'price': features.get('price', 0),
            'volume': features.get('volume', 1000000),
            'market_cap': 1000000000,
            'sector_performance': 0,
            # Additional features for XGBoost
            'macd': 0,
            'macd_signal': 0,
            'macd_histogram': 0,
            'bbw_percentile': 50,
            'atr_14': 1.0,
            'stochastic_k': 50,
            'stochastic_d': 50,
            'williams_r': -50,
            'cci': 0,
            'price_vs_sma20': 1.0,
            'price_vs_sma50': 1.0,
            'sma20_vs_sma50': 1.0,
            'pattern_duration': features.get('pattern_days', 0)
        }

        # Merge with defaults
        for key, default_value in default_features.items():
            if key not in features:
                features[key] = default_value

        return features

    def _create_signal(self,
                      symbol: str,
                      prediction: Dict[str, Any],
                      current_price: float,
                      pattern: Any) -> Signal:
        """
        Create a Signal object from prediction and pattern.

        Args:
            symbol: Stock symbol
            prediction: Model prediction
            current_price: Current stock price
            pattern: Detected pattern

        Returns:
            Signal object
        """
        # Determine action based on expected value
        expected_value = prediction['expected_value']

        if expected_value >= 5.0:
            action = SignalAction.STRONG_BUY
        elif expected_value >= 3.0:
            action = SignalAction.BUY
        elif expected_value >= 1.0:
            action = SignalAction.HOLD
        elif expected_value <= -3.0:
            action = SignalAction.STRONG_SELL
        elif expected_value <= -1.0:
            action = SignalAction.SELL
        else:
            action = SignalAction.HOLD

        # Calculate price targets
        if pattern and hasattr(pattern, 'power_boundary'):
            target_price = pattern.power_boundary
        else:
            # Default 10% target
            target_price = current_price * 1.10

        # Calculate stop loss (5% below current)
        stop_loss = current_price * 0.95

        # Handle optional fields
        metadata = prediction.get('metadata', {})
        if pattern:
            metadata['pattern_phase'] = pattern.phase.value if hasattr(pattern, 'phase') else 'NONE'
            metadata['range_percentage'] = pattern.range_percentage if hasattr(pattern, 'range_percentage') else 0

        return Signal(
            symbol=symbol,
            action=action,
            confidence=prediction['confidence'],
            entry_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            expected_value=expected_value,
            reason=prediction.get('reason', f"EV={expected_value:.2f}"),
            metadata=metadata
        )