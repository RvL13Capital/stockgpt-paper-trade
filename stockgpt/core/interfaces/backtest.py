"""
Backtesting Engine Interface

Defines the contract for backtesting strategies.
"""

from typing import Protocol, List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum
from stockgpt.core.entities.backtest import BacktestResult, StrategyType


class IBacktestEngine(Protocol):
    """Interface for backtesting trading strategies."""

    async def run_backtest(
        self,
        strategy_type: StrategyType,
        symbols: List[str],
        start_date: date,
        end_date: date,
        initial_capital: float = 10000.0,
        position_size: float = 0.1,
        **strategy_params: Any,
    ) -> BacktestResult:
        """
        Run a backtest for a specific strategy.

        Args:
            strategy_type: Type of strategy to test
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            position_size: Position size as fraction of capital
            **strategy_params: Strategy-specific parameters

        Returns:
            Backtest result with metrics and trade history
        """
        ...

    async def run_walk_forward_analysis(
        self,
        strategy_type: StrategyType,
        symbols: List[str],
        start_date: date,
        end_date: date,
        training_window: int,
        testing_window: int,
        retraining_frequency: int,
        **strategy_params: Any,
    ) -> List[BacktestResult]:
        """
        Run walk-forward analysis with periodic retraining.

        Args:
            strategy_type: Strategy to test
            symbols: Symbols to trade
            start_date: Analysis start date
            end_date: Analysis end date
            training_window: Days for training period
            testing_window: Days for testing period
            retraining_frequency: Days between retraining
            **strategy_params: Strategy parameters

        Returns:
            List of backtest results for each period
        """
        ...

    def calculate_performance_metrics(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float,
    ) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.

        Args:
            trades: List of executed trades
            initial_capital: Starting capital

        Returns:
            Dictionary of performance metrics:
                - total_return
                - annualized_return
                - sharpe_ratio
                - sortino_ratio
                - max_drawdown
                - win_rate
                - profit_factor
                - average_win
                - average_loss
        """
        ...

    def generate_equity_curve(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float,
    ) -> List[Dict[str, Any]]:
        """
        Generate equity curve from trades.

        Args:
            trades: Trade history
            initial_capital: Starting capital

        Returns:
            Time series of portfolio value
        """
        ...

    async def compare_strategies(
        self,
        results: List[BacktestResult],
    ) -> Dict[str, Any]:
        """
        Compare multiple backtest results.

        Args:
            results: List of backtest results to compare

        Returns:
            Comparison metrics and rankings
        """
        ...

    def get_available_strategies(self) -> List[StrategyType]:
        """
        Get list of available strategies.

        Returns:
            List of strategy types
        """
        ...

    def validate_parameters(
        self,
        strategy_type: StrategyType,
        parameters: Dict[str, Any],
    ) -> bool:
        """
        Validate strategy parameters.

        Args:
            strategy_type: Strategy type
            parameters: Parameters to validate

        Returns:
            True if valid, raises ValueError if not
        """
        ...