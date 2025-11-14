"""
StockGPT - Modular Stock Analysis and Trading System

A clean, testable, and extensible architecture for stock pattern detection,
signal generation, and paper trading.
"""

__version__ = "2.0.0"
__author__ = "StockGPT Team"

from stockgpt.core.entities import (
    Signal,
    SignalAction,
    Pattern,
    PatternPhase,
    Stock,
    Price,
)

from stockgpt.core.interfaces import (
    IModel,
    ISignalGenerator,
    IBacktestEngine,
    IDataProvider,
    IPatternDetector,
    IRepository,
)

__all__ = [
    # Entities
    "Signal",
    "SignalAction",
    "Pattern",
    "PatternPhase",
    "Stock",
    "Price",
    # Interfaces
    "IModel",
    "ISignalGenerator",
    "IBacktestEngine",
    "IDataProvider",
    "IPatternDetector",
    "IRepository",
]