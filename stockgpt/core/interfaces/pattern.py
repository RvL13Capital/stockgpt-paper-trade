"""
Pattern Detection Interface

Defines the contract for pattern detection strategies,
including consolidation patterns for the AIv3 system.
"""

from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime
from stockgpt.core.entities.pattern import Pattern, PatternPhase, PatternOutcome
from stockgpt.core.entities.stock import Price


class IPatternDetector(Protocol):
    """Interface for pattern detection in price data."""

    def detect(
        self,
        symbol: str,
        prices: List[Price],
        min_days: int = 10,
    ) -> List[Pattern]:
        """
        Detect patterns in price data.

        Args:
            symbol: Stock symbol
            prices: Historical price data
            min_days: Minimum days for pattern formation

        Returns:
            List of detected patterns
        """
        ...

    def get_active_patterns(self) -> List[Pattern]:
        """
        Get all currently active patterns being tracked.

        Returns:
            List of active patterns
        """
        ...

    def update_pattern(
        self,
        pattern_id: str,
        price_data: Dict[str, float],
    ) -> Pattern:
        """
        Update pattern state with new price data.

        Args:
            pattern_id: Unique pattern identifier
            price_data: Latest price and indicator data

        Returns:
            Updated pattern
        """
        ...

    def evaluate_pattern(
        self,
        pattern_id: str,
        evaluation_window: int = 100,
    ) -> PatternOutcome:
        """
        Evaluate pattern outcome after completion.

        Args:
            pattern_id: Pattern to evaluate
            evaluation_window: Days to track after pattern completion

        Returns:
            Pattern outcome with performance metrics
        """
        ...

    def calculate_pattern_features(
        self,
        pattern: Pattern,
        prices: List[Price],
    ) -> Dict[str, float]:
        """
        Calculate features for pattern analysis.

        Args:
            pattern: Pattern to analyze
            prices: Price data during pattern formation

        Returns:
            Dictionary of pattern features
        """
        ...

    def get_qualification_criteria(self) -> Dict[str, Any]:
        """
        Get pattern qualification criteria.

        Returns:
            Dictionary of qualification thresholds
        """
        ...

    def set_qualification_criteria(
        self,
        bbw_percentile: float = 30.0,
        adx_threshold: float = 32.0,
        volume_ratio: float = 0.35,
        range_ratio: float = 0.65,
    ) -> None:
        """
        Set pattern qualification criteria.

        Args:
            bbw_percentile: Bollinger Band Width percentile threshold
            adx_threshold: ADX indicator threshold
            volume_ratio: Volume ratio vs 20-day average
            range_ratio: Daily range ratio vs 20-day average
        """
        ...