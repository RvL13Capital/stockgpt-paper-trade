"""
Signal Entity

Represents a trading signal with validation logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4


class SignalAction(Enum):
    """Trading signal actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Signal:
    """
    Immutable trading signal entity.

    Attributes:
        id: Unique identifier
        symbol: Stock symbol
        action: Signal action (BUY/SELL/HOLD)
        confidence: Model confidence (0-1)
        entry_price: Suggested entry price
        target_price: Target price for profit taking
        stop_loss: Stop loss price for risk management
        expected_value: Calculated expected value
        created_at: Signal creation timestamp
        metadata: Additional signal metadata
    """

    symbol: str
    action: SignalAction
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    expected_value: float
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[str] = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate signal after initialization."""
        self.validate()

    def validate(self) -> bool:
        """
        Validate signal constraints.

        Raises:
            ValueError: If validation fails

        Returns:
            True if valid
        """
        # Validate confidence bounds
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")

        # Validate prices are positive
        if any(p <= 0 for p in [self.entry_price, self.target_price, self.stop_loss]):
            raise ValueError("All prices must be positive")

        # Validate price relationships based on action
        if self.action == SignalAction.BUY:
            if self.target_price <= self.entry_price:
                raise ValueError(
                    f"Target price ({self.target_price}) must be above "
                    f"entry price ({self.entry_price}) for BUY signal"
                )
            if self.stop_loss >= self.entry_price:
                raise ValueError(
                    f"Stop loss ({self.stop_loss}) must be below "
                    f"entry price ({self.entry_price}) for BUY signal"
                )

        elif self.action == SignalAction.SELL:
            if self.target_price >= self.entry_price:
                raise ValueError(
                    f"Target price ({self.target_price}) must be below "
                    f"entry price ({self.entry_price}) for SELL signal"
                )
            if self.stop_loss <= self.entry_price:
                raise ValueError(
                    f"Stop loss ({self.stop_loss}) must be above "
                    f"entry price ({self.entry_price}) for SELL signal"
                )

        return True

    @property
    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio."""
        if self.action == SignalAction.HOLD:
            return 0.0

        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.target_price - self.entry_price)

        if risk == 0:
            return float('inf')

        return reward / risk

    @property
    def potential_return(self) -> float:
        """Calculate potential return percentage."""
        if self.action == SignalAction.HOLD:
            return 0.0

        return abs(self.target_price - self.entry_price) / self.entry_price * 100

    @property
    def risk_percentage(self) -> float:
        """Calculate risk as percentage of entry price."""
        if self.action == SignalAction.HOLD:
            return 0.0

        return abs(self.entry_price - self.stop_loss) / self.entry_price * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'action': self.action.value,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'expected_value': self.expected_value,
            'risk_reward_ratio': self.risk_reward_ratio,
            'potential_return': self.potential_return,
            'risk_percentage': self.risk_percentage,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
        }