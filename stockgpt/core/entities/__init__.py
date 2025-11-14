"""
Core domain entities.

These are pure Python dataclasses representing the business domain.
They contain no external dependencies and focus on business logic.
"""

from .signal import Signal, SignalAction
from .pattern import Pattern, PatternPhase, PatternOutcome
from .stock import Stock, Price
from .backtest import BacktestResult, StrategyType, PerformanceMetrics
from .portfolio import Portfolio, Position, Trade

__all__ = [
    # Signal
    "Signal",
    "SignalAction",
    # Pattern
    "Pattern",
    "PatternPhase",
    "PatternOutcome",
    # Stock
    "Stock",
    "Price",
    # Backtest
    "BacktestResult",
    "StrategyType",
    "PerformanceMetrics",
    # Portfolio
    "Portfolio",
    "Position",
    "Trade",
]