"""
Portfolio Management Entities

Entities for portfolio, positions, and trades.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import uuid4


class TradeStatus(Enum):
    """Trade execution status."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PositionStatus(Enum):
    """Position status."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"


@dataclass
class Trade:
    """
    Individual trade entity.

    Attributes:
        id: Unique identifier
        symbol: Stock symbol
        action: BUY or SELL
        quantity: Number of shares
        price: Execution price
        commission: Trading commission
        status: Trade status
        executed_at: Execution timestamp
        signal_id: Reference to originating signal
        notes: Trade notes
    """

    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float = 0.0
    status: TradeStatus = TradeStatus.PENDING
    executed_at: Optional[datetime] = None
    signal_id: Optional[str] = None
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        """Validate trade data."""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if self.price <= 0:
            raise ValueError("Price must be positive")

        if self.commission < 0:
            raise ValueError("Commission cannot be negative")

        if self.action not in ['BUY', 'SELL']:
            raise ValueError("Action must be 'BUY' or 'SELL'")

    @property
    def gross_value(self) -> float:
        """Calculate gross trade value."""
        return self.quantity * self.price

    @property
    def net_value(self) -> float:
        """Calculate net trade value (including commission)."""
        if self.action == 'BUY':
            return self.gross_value + self.commission
        else:
            return self.gross_value - self.commission

    def execute(self) -> None:
        """Mark trade as executed."""
        if self.status != TradeStatus.PENDING:
            raise ValueError(f"Cannot execute trade with status {self.status.value}")

        self.status = TradeStatus.EXECUTED
        self.executed_at = datetime.now()

    def cancel(self) -> None:
        """Cancel pending trade."""
        if self.status != TradeStatus.PENDING:
            raise ValueError(f"Cannot cancel trade with status {self.status.value}")

        self.status = TradeStatus.CANCELLED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'commission': self.commission,
            'gross_value': self.gross_value,
            'net_value': self.net_value,
            'status': self.status.value,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'signal_id': self.signal_id,
            'notes': self.notes,
        }


@dataclass
class Position:
    """
    Stock position in portfolio.

    Attributes:
        id: Unique identifier
        symbol: Stock symbol
        quantity: Current share quantity
        average_price: Average entry price
        current_price: Latest market price
        status: Position status
        opened_at: Position open timestamp
        closed_at: Position close timestamp
        trades: List of trades for this position
    """

    symbol: str
    quantity: int
    average_price: float
    current_price: float
    status: PositionStatus = PositionStatus.OPEN
    opened_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    trades: List[Trade] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def cost_basis(self) -> float:
        """Calculate total cost basis."""
        return self.quantity * self.average_price

    @property
    def market_value(self) -> float:
        """Calculate current market value."""
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss."""
        if self.status != PositionStatus.OPEN:
            return 0.0
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_percentage(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def add_trade(self, trade: Trade) -> None:
        """
        Add a trade to this position and update metrics.

        Args:
            trade: Trade to add
        """
        if trade.symbol != self.symbol:
            raise ValueError(f"Trade symbol {trade.symbol} doesn't match position {self.symbol}")

        self.trades.append(trade)

        # Update position based on trade
        if trade.action == 'BUY':
            # Recalculate average price
            total_cost = self.cost_basis + trade.net_value
            self.quantity += trade.quantity
            self.average_price = total_cost / self.quantity if self.quantity > 0 else 0
        else:  # SELL
            self.quantity -= trade.quantity
            if self.quantity <= 0:
                self.close()

    def close(self) -> None:
        """Close the position."""
        self.status = PositionStatus.CLOSED
        self.closed_at = datetime.now()
        self.quantity = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'current_price': self.current_price,
            'cost_basis': self.cost_basis,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percentage': self.unrealized_pnl_percentage,
            'status': self.status.value,
            'opened_at': self.opened_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'trades': [t.to_dict() for t in self.trades],
        }


@dataclass
class Portfolio:
    """
    Complete portfolio entity.

    Attributes:
        id: Unique identifier
        name: Portfolio name
        initial_capital: Starting capital
        cash_balance: Current cash balance
        positions: List of open positions
        closed_positions: List of closed positions
        all_trades: Complete trade history
        created_at: Portfolio creation timestamp
    """

    name: str
    initial_capital: float
    cash_balance: float
    positions: List[Position] = field(default_factory=list)
    closed_positions: List[Position] = field(default_factory=list)
    all_trades: List[Trade] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def total_market_value(self) -> float:
        """Calculate total portfolio market value."""
        positions_value = sum(p.market_value for p in self.positions)
        return self.cash_balance + positions_value

    @property
    def total_pnl(self) -> float:
        """Calculate total profit/loss."""
        return self.total_market_value - self.initial_capital

    @property
    def total_pnl_percentage(self) -> float:
        """Calculate total P&L percentage."""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_pnl / self.initial_capital) * 100

    @property
    def num_positions(self) -> int:
        """Count open positions."""
        return len(self.positions)

    def execute_trade(self, trade: Trade) -> None:
        """
        Execute a trade and update portfolio.

        Args:
            trade: Trade to execute
        """
        trade.execute()
        self.all_trades.append(trade)

        # Find or create position
        position = self.get_position(trade.symbol)
        if not position:
            position = Position(
                symbol=trade.symbol,
                quantity=0,
                average_price=trade.price,
                current_price=trade.price,
            )
            self.positions.append(position)

        # Update position
        position.add_trade(trade)

        # Update cash balance
        if trade.action == 'BUY':
            self.cash_balance -= trade.net_value
        else:
            self.cash_balance += trade.net_value

        # Move closed positions
        if position.status == PositionStatus.CLOSED:
            self.positions.remove(position)
            self.closed_positions.append(position)

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        for position in self.positions:
            if position.symbol == symbol:
                return position
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'initial_capital': self.initial_capital,
            'cash_balance': self.cash_balance,
            'total_market_value': self.total_market_value,
            'total_pnl': self.total_pnl,
            'total_pnl_percentage': self.total_pnl_percentage,
            'num_positions': self.num_positions,
            'positions': [p.to_dict() for p in self.positions],
            'closed_positions': [p.to_dict() for p in self.closed_positions],
            'all_trades': [t.to_dict() for t in self.all_trades],
            'created_at': self.created_at.isoformat(),
        }