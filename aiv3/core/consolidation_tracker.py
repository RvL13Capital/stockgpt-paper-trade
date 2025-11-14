"""
Consolidation Pattern Tracker

Real-time pattern detection using actual market data.
Tracks consolidation patterns through qualification, active, and completion phases.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from stockgpt.core.entities.pattern import Pattern, PatternPhase, PatternOutcome, OutcomeClass
from stockgpt.core.entities.stock import Price

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationMetrics:
    """Real-time metrics for consolidation pattern analysis."""
    bbw: float  # Bollinger Band Width
    bbw_percentile: float  # BBW percentile over lookback period
    adx: float  # Average Directional Index
    volume_ratio: float  # Current volume vs 20-day average
    daily_range_ratio: float  # Current range vs 20-day average
    atr: float  # Average True Range
    volatility: float  # 20-day volatility
    price_position: float  # Position within consolidation range (0-1)


class ConsolidationTracker:
    """
    Tracks consolidation patterns using real market data.

    This is the core of the AIv3 system - it detects when stocks enter
    tight consolidation patterns that often precede explosive moves.
    """

    # Qualification thresholds (from AIv3 specification)
    QUALIFICATION_THRESHOLDS = {
        'bbw_percentile': 30.0,  # BBW must be below 30th percentile
        'adx': 32.0,  # ADX must be below 32 (low trending)
        'volume_ratio': 0.35,  # Volume below 35% of average
        'daily_range_ratio': 0.65,  # Range below 65% of average
        'min_qualification_days': 10,  # Minimum days to qualify
    }

    def __init__(
        self,
        symbol: str,
        lookback_days: int = 60,
        evaluation_window: int = 100,
    ):
        """
        Initialize tracker for a specific symbol.

        Args:
            symbol: Stock symbol to track
            lookback_days: Days to look back for percentile calculations
            evaluation_window: Days to track after pattern completion
        """
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.evaluation_window = evaluation_window

        # Current pattern being tracked
        self.current_pattern: Optional[Pattern] = None

        # Historical patterns for this symbol
        self.completed_patterns: List[Pattern] = []
        self.pattern_outcomes: List[PatternOutcome] = []

        # Price history for analysis
        self.price_history: List[Price] = []
        self.metrics_history: List[ConsolidationMetrics] = []

    def update(self, price_data: List[Price]) -> Optional[Pattern]:
        """
        Update tracker with new price data.

        Args:
            price_data: Historical price data (must be at least lookback_days)

        Returns:
            Current pattern if one exists
        """
        if len(price_data) < self.lookback_days:
            logger.warning(f"Insufficient data for {self.symbol}: {len(price_data)} days")
            return None

        self.price_history = price_data
        latest_price = price_data[-1]

        # Calculate current metrics
        metrics = self._calculate_metrics(price_data)
        self.metrics_history.append(metrics)

        # Update pattern state machine
        self._update_pattern_state(latest_price, metrics)

        return self.current_pattern

    def _calculate_metrics(self, prices: List[Price]) -> ConsolidationMetrics:
        """
        Calculate real consolidation metrics from price data.

        Args:
            prices: Historical price data

        Returns:
            Consolidation metrics
        """
        # Convert to DataFrame for easier calculation
        df = pd.DataFrame([p.to_dict() for p in prices])

        # Bollinger Band Width
        sma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        upper_band = sma20 + 2 * std20
        lower_band = sma20 - 2 * std20
        bbw = ((upper_band - lower_band) / sma20 * 100).iloc[-1]

        # BBW Percentile (how tight is current BBW vs history)
        bbw_series = (upper_band - lower_band) / sma20 * 100
        bbw_percentile = (bbw <= bbw_series).mean() * 100

        # ADX Calculation
        adx = self._calculate_adx(df)

        # Volume Ratio
        current_volume = df['volume'].iloc[-1]
        avg_volume_20 = df['volume'].rolling(20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

        # Daily Range Ratio
        current_range = (df['high'].iloc[-1] - df['low'].iloc[-1]) / df['close'].iloc[-1]
        avg_range_20 = ((df['high'] - df['low']) / df['close']).rolling(20).mean().iloc[-1]
        daily_range_ratio = current_range / avg_range_20 if avg_range_20 > 0 else 1.0

        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]

        # Volatility
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1] * 100

        # Price position within current range
        if self.current_pattern and self.current_pattern.upper_boundary:
            price_position = ((df['close'].iloc[-1] - self.current_pattern.lower_boundary) /
                            (self.current_pattern.upper_boundary - self.current_pattern.lower_boundary))
        else:
            price_position = 0.5

        return ConsolidationMetrics(
            bbw=bbw,
            bbw_percentile=bbw_percentile,
            adx=adx,
            volume_ratio=volume_ratio,
            daily_range_ratio=daily_range_ratio,
            atr=atr,
            volatility=volatility,
            price_position=price_position,
        )

    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """
        Calculate Average Directional Index (ADX).

        Args:
            df: Price DataFrame

        Returns:
            ADX value
        """
        # Simplified ADX calculation
        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Directional Movement
        up = high - high.shift()
        down = low.shift() - low

        pos_dm = pd.Series(0.0, index=df.index)
        neg_dm = pd.Series(0.0, index=df.index)

        pos_dm[up > down] = up[up > down]
        pos_dm[pos_dm < 0] = 0

        neg_dm[down > up] = down[down > up]
        neg_dm[neg_dm < 0] = 0

        # Smoothed DI
        pos_di = 100 * (pos_dm.rolling(14).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(14).mean() / atr)

        # ADX
        dx = 100 * ((pos_di - neg_di).abs() / (pos_di + neg_di))
        adx = dx.rolling(14).mean().iloc[-1]

        return adx if not pd.isna(adx) else 25.0  # Default if calculation fails

    def _update_pattern_state(self, latest_price: Price, metrics: ConsolidationMetrics) -> None:
        """
        Update pattern state machine based on real metrics.

        Args:
            latest_price: Latest price data
            metrics: Current consolidation metrics
        """
        if not self.current_pattern:
            # No pattern - check for qualification
            if self._check_qualification(metrics):
                self._start_qualification(latest_price)

        elif self.current_pattern.phase == PatternPhase.QUALIFYING:
            # In qualification - check if still qualifying
            if self._check_qualification(metrics):
                self.current_pattern.qualification_days += 1

                # Check if qualified for active phase
                if self.current_pattern.qualification_days >= self.QUALIFICATION_THRESHOLDS['min_qualification_days']:
                    self._activate_pattern(latest_price)
            else:
                # Failed qualification - reset
                logger.info(f"{self.symbol}: Failed qualification after {self.current_pattern.qualification_days} days")
                self.current_pattern = None

        elif self.current_pattern.phase == PatternPhase.ACTIVE:
            # Active pattern - check for breakout or breakdown
            if latest_price.close > self.current_pattern.power_boundary:
                # Breakout detected!
                logger.info(f"{self.symbol}: BREAKOUT at {latest_price.close} (power: {self.current_pattern.power_boundary})")
                self._complete_pattern(latest_price, success=True)

            elif latest_price.close < self.current_pattern.lower_boundary * 0.98:
                # Breakdown detected (2% below lower boundary)
                logger.info(f"{self.symbol}: BREAKDOWN at {latest_price.close} (lower: {self.current_pattern.lower_boundary})")
                self._complete_pattern(latest_price, success=False)

    def _check_qualification(self, metrics: ConsolidationMetrics) -> bool:
        """
        Check if metrics meet qualification criteria.

        All conditions must be met for qualification.
        """
        return (
            metrics.bbw_percentile < self.QUALIFICATION_THRESHOLDS['bbw_percentile'] and
            metrics.adx < self.QUALIFICATION_THRESHOLDS['adx'] and
            metrics.volume_ratio < self.QUALIFICATION_THRESHOLDS['volume_ratio'] and
            metrics.daily_range_ratio < self.QUALIFICATION_THRESHOLDS['daily_range_ratio']
        )

    def _start_qualification(self, latest_price: Price) -> None:
        """Start pattern qualification phase."""
        self.current_pattern = Pattern(
            symbol=self.symbol,
            phase=PatternPhase.QUALIFYING,
            start_date=latest_price.date,
            qualification_days=1,
        )
        logger.info(f"{self.symbol}: Started qualification phase")

    def _activate_pattern(self, latest_price: Price) -> None:
        """
        Activate pattern after successful qualification.

        Establishes boundaries based on price range during qualification.
        """
        # Calculate boundaries from qualification period
        qual_prices = self.price_history[-self.current_pattern.qualification_days:]

        high = max(p.high for p in qual_prices)
        low = min(p.low for p in qual_prices)

        self.current_pattern.upper_boundary = high
        self.current_pattern.lower_boundary = low
        self.current_pattern.power_boundary = high * 1.005  # 0.5% above upper

        # Calculate pattern metrics
        self.current_pattern.pattern_metrics = {
            'range_percent': (high - low) / low * 100,
            'qualification_days': self.current_pattern.qualification_days,
            'avg_volume': np.mean([p.volume for p in qual_prices]),
            'avg_bbw': np.mean([m.bbw for m in self.metrics_history[-self.current_pattern.qualification_days:]]),
        }

        self.current_pattern.update_phase(PatternPhase.ACTIVE)
        logger.info(
            f"{self.symbol}: Pattern ACTIVATED - "
            f"Range: {low:.2f}-{high:.2f} ({self.current_pattern.pattern_metrics['range_percent']:.2f}%)"
        )

    def _complete_pattern(self, latest_price: Price, success: bool) -> None:
        """
        Complete pattern and start tracking outcome.

        Args:
            latest_price: Price at completion
            success: True for breakout, False for breakdown
        """
        if success:
            self.current_pattern.update_phase(PatternPhase.COMPLETED)
        else:
            self.current_pattern.update_phase(PatternPhase.FAILED)

        # Store completed pattern
        self.completed_patterns.append(self.current_pattern)

        # Start tracking outcome (will be evaluated over next evaluation_window days)
        # This is where we would track the actual gain over the next 100 days
        # to label the pattern for training

        logger.info(
            f"{self.symbol}: Pattern {'COMPLETED' if success else 'FAILED'} after "
            f"{self.current_pattern.days_active} active days"
        )

        # Reset for next pattern
        self.current_pattern = None

    def evaluate_pattern_outcome(
        self,
        pattern: Pattern,
        future_prices: List[Price],
    ) -> PatternOutcome:
        """
        Evaluate actual pattern outcome using future price data.

        This is used for training - we look at what actually happened
        after the pattern completed to label it properly.

        Args:
            pattern: Completed pattern to evaluate
            future_prices: Prices after pattern completion

        Returns:
            Pattern outcome with actual results
        """
        if not future_prices:
            return None

        # Get price at pattern completion
        completion_price = pattern.upper_boundary if pattern.phase == PatternPhase.COMPLETED else pattern.lower_boundary

        # Track maximum gain over evaluation window
        max_gain = 0.0
        max_loss = 0.0
        final_gain = 0.0

        for price in future_prices[:self.evaluation_window]:
            gain = (price.high - completion_price) / completion_price * 100
            loss = (price.low - completion_price) / completion_price * 100

            max_gain = max(max_gain, gain)
            max_loss = min(max_loss, loss)

        # Final gain at end of window
        if len(future_prices) >= self.evaluation_window:
            final_gain = ((future_prices[self.evaluation_window - 1].close - completion_price) /
                         completion_price * 100)
        else:
            final_gain = ((future_prices[-1].close - completion_price) /
                         completion_price * 100)

        # Create outcome based on actual performance
        outcome = PatternOutcome.from_gain(
            pattern_id=pattern.id,
            gain=max_gain,  # Use maximum gain achieved
            days=len(future_prices[:self.evaluation_window]),
        )

        # Update with actual tracking
        outcome.max_gain = max_gain
        outcome.max_loss = max_loss
        outcome.actual_gain = final_gain

        return outcome

    def get_pattern_features(self, pattern: Pattern) -> Dict[str, float]:
        """
        Extract features for ML model training from real pattern data.

        Args:
            pattern: Pattern to extract features from

        Returns:
            Feature dictionary for model training
        """
        # Get metrics during pattern formation
        pattern_metrics = []
        for i, price in enumerate(self.price_history):
            if price.date >= pattern.start_date:
                if i < len(self.metrics_history):
                    pattern_metrics.append(self.metrics_history[i])

        if not pattern_metrics:
            return {}

        # Aggregate features over pattern duration
        features = {
            # Pattern characteristics
            'pattern_duration': pattern.qualification_days + pattern.days_active,
            'range_percentage': pattern.range_percentage,

            # Average metrics during pattern
            'avg_bbw': np.mean([m.bbw for m in pattern_metrics]),
            'min_bbw': np.min([m.bbw for m in pattern_metrics]),
            'avg_bbw_percentile': np.mean([m.bbw_percentile for m in pattern_metrics]),

            'avg_adx': np.mean([m.adx for m in pattern_metrics]),
            'max_adx': np.max([m.adx for m in pattern_metrics]),

            'avg_volume_ratio': np.mean([m.volume_ratio for m in pattern_metrics]),
            'min_volume_ratio': np.min([m.volume_ratio for m in pattern_metrics]),

            'avg_daily_range_ratio': np.mean([m.daily_range_ratio for m in pattern_metrics]),
            'avg_atr': np.mean([m.atr for m in pattern_metrics]),
            'avg_volatility': np.mean([m.volatility for m in pattern_metrics]),

            # Trend of metrics (are they improving/deteriorating)
            'bbw_slope': self._calculate_slope([m.bbw for m in pattern_metrics]),
            'adx_slope': self._calculate_slope([m.adx for m in pattern_metrics]),
            'volume_slope': self._calculate_slope([m.volume_ratio for m in pattern_metrics]),
        }

        return features

    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear regression slope of values."""
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        y = np.array(values)

        # Simple linear regression
        n = len(values)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)

        return float(slope)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pattern detection statistics for this symbol.

        Returns:
            Statistics about pattern detection performance
        """
        if not self.completed_patterns:
            return {
                'total_patterns': 0,
                'success_rate': 0.0,
                'avg_duration': 0,
            }

        successful = [p for p in self.completed_patterns if p.phase == PatternPhase.COMPLETED]
        failed = [p for p in self.completed_patterns if p.phase == PatternPhase.FAILED]

        # Calculate outcome statistics if available
        outcome_stats = {}
        if self.pattern_outcomes:
            gains = [o.actual_gain for o in self.pattern_outcomes]
            outcome_stats = {
                'avg_gain': np.mean(gains),
                'max_gain': np.max(gains),
                'min_gain': np.min(gains),
                'positive_rate': sum(1 for g in gains if g > 0) / len(gains),
                'k4_rate': sum(1 for o in self.pattern_outcomes if o.outcome_class == OutcomeClass.K4) / len(self.pattern_outcomes),
            }

        return {
            'total_patterns': len(self.completed_patterns),
            'successful_breakouts': len(successful),
            'failed_breakdowns': len(failed),
            'success_rate': len(successful) / len(self.completed_patterns) if self.completed_patterns else 0.0,
            'avg_qualification_days': np.mean([p.qualification_days for p in self.completed_patterns]),
            'avg_active_days': np.mean([p.days_active for p in self.completed_patterns]),
            'current_pattern': self.current_pattern.phase.value if self.current_pattern else 'NONE',
            **outcome_stats,
        }