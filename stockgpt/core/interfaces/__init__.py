"""
Core interfaces for the StockGPT system.

These protocols define the contracts that all implementations must follow,
enabling dependency injection, easy testing, and extensibility.
"""

from .model import IModel
from .signal import ISignalGenerator
from .backtest import IBacktestEngine
from .data import IDataProvider
from .pattern import IPatternDetector
from .repository import IRepository

__all__ = [
    "IModel",
    "ISignalGenerator",
    "IBacktestEngine",
    "IDataProvider",
    "IPatternDetector",
    "IRepository",
]