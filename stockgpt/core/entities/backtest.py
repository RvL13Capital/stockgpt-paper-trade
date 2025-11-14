"""
Backtesting Entities

Entities for backtest configuration and results.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class StrategyType(Enum):
    """Available trading strategies."""
    MOVING_AVERAGE = "MOVING_AVERAGE"
    RSI_DIVERGENCE = "RSI_DIVERGENCE"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"
    ML_SIGNALS = "ML_SIGNALS"
    PATTERN_BREAKOUT = "PATTERN_BREAKOUT"
    CONSOLIDATION = "CONSOLIDATION"


@dataclass(frozen=True)
class PerformanceMetrics:
    """
    Comprehensive performance metrics for backtesting.

    Attributes:
        total_return: Total return percentage
        annualized_return: Annualized return percentage
        sharpe_ratio: Risk-adjusted return metric
        sortino_ratio: Downside risk-adjusted return
        max_drawdown: Maximum peak-to-trough decline
        win_rate: Percentage of winning trades
        profit_factor: Ratio of gross profit to gross loss
        average_win: Average winning trade return
        average_loss: Average losing trade return
        total_trades: Total number of trades
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
        best_trade: Best trade return
        worst_trade: Worst trade return
        recovery_factor: Total return / max drawdown
        calmar_ratio: Annualized return / max drawdown
    """

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    best_trade: float
    worst_trade: float
    recovery_factor: float
    calmar_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'recovery_factor': self.recovery_factor,
            'calmar_ratio': self.calmar_ratio,
        }


@dataclass
class BacktestResult:
    """
    Complete backtest result with configuration and outcomes.

    Attributes:
        id: Unique identifier
        strategy_type: Strategy that was tested
        symbols: List of traded symbols
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital
        final_capital: Ending capital
        metrics: Performance metrics
        trades: List of executed trades
        equity_curve: Time series of portfolio value
        parameters: Strategy-specific parameters
        created_at: Backtest execution timestamp
    """

    strategy_type: StrategyType
    symbols: List[str]
    start_date: date
    end_date: date
    initial_capital: float
    final_capital: float
    metrics: PerformanceMetrics
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[str] = None

    @property
    def trading_days(self) -> int:
        """Calculate number of trading days."""
        return (self.end_date - self.start_date).days

    @property
    def total_return_percentage(self) -> float:
        """Calculate total return percentage."""
        return ((self.final_capital - self.initial_capital) /
                self.initial_capital * 100)

    @property
    def is_profitable(self) -> bool:
        """Check if backtest was profitable."""
        return self.final_capital > self.initial_capital

    def add_trade(self, trade: Dict[str, Any]) -> None:
        """
        Add a trade to the backtest.

        Args:
            trade: Trade dictionary with entry/exit details
        """
        self.trades.append(trade)

    def add_equity_point(self, date: date, value: float) -> None:
        """
        Add a point to the equity curve.

        Args:
            date: Date of the equity value
            value: Portfolio value at this date
        """
        self.equity_curve.append({
            'date': date.isoformat(),
            'value': value,
            'return': (value - self.initial_capital) / self.initial_capital * 100,
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'strategy_type': self.strategy_type.value,
            'symbols': self.symbols,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'trading_days': self.trading_days,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return_percentage': self.total_return_percentage,
            'is_profitable': self.is_profitable,
            'metrics': self.metrics.to_dict(),
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat(),
        }