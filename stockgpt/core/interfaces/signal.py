"""
Signal Generator Interface

Defines the contract for signal generation strategies.
"""

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime
from stockgpt.core.entities.signal import Signal, SignalAction
from stockgpt.core.entities.stock import Stock, Price


class ISignalGenerator(Protocol):
    """Interface for trading signal generation."""

    async def generate_signals(
        self,
        symbols: Optional[List[str]] = None,
        min_confidence: float = 0.6,
        lookback_days: int = 100,
    ) -> List[Signal]:
        """
        Generate trading signals for specified symbols.

        Args:
            symbols: List of stock symbols to analyze (None = all active)
            min_confidence: Minimum confidence threshold for signal generation
            lookback_days: Number of days of historical data to consider

        Returns:
            List of generated signals
        """
        ...

    async def generate_signal_for_symbol(
        self,
        symbol: str,
        price_data: List[Price],
        features: Dict[str, float],
    ) -> Optional[Signal]:
        """
        Generate signal for a single symbol.

        Args:
            symbol: Stock symbol
            price_data: Historical price data
            features: Calculated technical features

        Returns:
            Signal if confidence meets threshold, None otherwise
        """
        ...

    def calculate_price_levels(
        self,
        action: SignalAction,
        current_price: float,
        features: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Calculate entry, target, and stop loss prices.

        Args:
            action: Signal action (BUY/SELL)
            current_price: Current stock price
            features: Technical features for calculation

        Returns:
            Dictionary with 'entry', 'target', and 'stop_loss' prices
        """
        ...

    def determine_action(
        self,
        prediction: Dict[str, Any],
        features: Dict[str, float],
    ) -> SignalAction:
        """
        Determine signal action from prediction and features.

        Args:
            prediction: Model prediction dictionary
            features: Technical features

        Returns:
            Signal action (BUY/SELL/HOLD)
        """
        ...

    async def evaluate_signal_performance(
        self,
        signal_id: str,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Evaluate performance of a previously generated signal.

        Args:
            signal_id: Unique signal identifier
            current_price: Current price for evaluation

        Returns:
            Performance metrics dictionary
        """
        ...