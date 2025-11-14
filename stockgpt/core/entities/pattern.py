"""
Pattern Entity

Represents consolidation patterns for the AIv3 system.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import uuid4


class PatternPhase(Enum):
    """Pattern lifecycle phases."""
    NONE = "NONE"
    QUALIFYING = "QUALIFYING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OutcomeClass(Enum):
    """Pattern outcome classifications."""
    K0 = "K0"  # <5% gain (Stagnant)
    K1 = "K1"  # 5-15% gain (Minimal)
    K2 = "K2"  # 15-35% gain (Quality)
    K3 = "K3"  # 35-75% gain (Strong)
    K4 = "K4"  # >75% gain (Exceptional)
    K5 = "K5"  # Breakdown (Failed)


@dataclass
class Pattern:
    """
    Consolidation pattern tracking entity.

    Attributes:
        id: Unique identifier
        symbol: Stock symbol
        phase: Current pattern phase
        start_date: Pattern start date
        qualification_days: Days in qualification phase
        upper_boundary: Upper price boundary
        lower_boundary: Lower price boundary
        power_boundary: Breakout trigger level (upper * 1.005)
        pattern_metrics: Calculated pattern metrics
        created_at: Pattern detection timestamp
    """

    symbol: str
    phase: PatternPhase
    start_date: date
    qualification_days: int = 0
    upper_boundary: Optional[float] = None
    lower_boundary: Optional[float] = None
    power_boundary: Optional[float] = None
    pattern_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid4()))

    def update_phase(self, new_phase: PatternPhase) -> None:
        """
        Update pattern phase with validation.

        Args:
            new_phase: New phase to transition to

        Raises:
            ValueError: If transition is invalid
        """
        valid_transitions = {
            PatternPhase.NONE: [PatternPhase.QUALIFYING],
            PatternPhase.QUALIFYING: [PatternPhase.ACTIVE, PatternPhase.NONE],
            PatternPhase.ACTIVE: [PatternPhase.COMPLETED, PatternPhase.FAILED],
            PatternPhase.COMPLETED: [],
            PatternPhase.FAILED: [],
        }

        if new_phase not in valid_transitions.get(self.phase, []):
            raise ValueError(
                f"Invalid phase transition from {self.phase.value} to {new_phase.value}"
            )

        self.phase = new_phase

    def establish_boundaries(self, high: float, low: float) -> None:
        """
        Establish pattern boundaries when entering ACTIVE phase.

        Args:
            high: Highest price during qualification
            low: Lowest price during qualification
        """
        if self.phase != PatternPhase.QUALIFYING:
            raise ValueError("Can only establish boundaries from QUALIFYING phase")

        self.upper_boundary = high
        self.lower_boundary = low
        self.power_boundary = high * 1.005  # 0.5% buffer above upper

    @property
    def days_active(self) -> int:
        """Calculate days pattern has been active."""
        if self.phase in [PatternPhase.NONE, PatternPhase.QUALIFYING]:
            return 0

        return (datetime.now().date() - self.start_date).days - 10

    @property
    def range_percentage(self) -> float:
        """Calculate pattern range as percentage."""
        if not self.upper_boundary or not self.lower_boundary:
            return 0.0

        return (self.upper_boundary - self.lower_boundary) / self.lower_boundary * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'phase': self.phase.value,
            'start_date': self.start_date.isoformat(),
            'qualification_days': self.qualification_days,
            'upper_boundary': self.upper_boundary,
            'lower_boundary': self.lower_boundary,
            'power_boundary': self.power_boundary,
            'days_active': self.days_active,
            'range_percentage': self.range_percentage,
            'pattern_metrics': self.pattern_metrics,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class PatternOutcome:
    """
    Pattern outcome after completion/failure.

    Attributes:
        pattern_id: Reference to original pattern
        outcome_class: Classification (K0-K5)
        actual_gain: Actual percentage gain/loss
        days_to_outcome: Days from pattern start to outcome
        max_gain: Maximum gain achieved during evaluation
        max_loss: Maximum loss during evaluation
        strategic_value: Value based on outcome class
    """

    pattern_id: str
    outcome_class: OutcomeClass
    actual_gain: float
    days_to_outcome: int
    max_gain: float
    max_loss: float
    strategic_value: float

    @classmethod
    def from_gain(cls, pattern_id: str, gain: float, days: int) -> 'PatternOutcome':
        """
        Create outcome from gain percentage.

        Args:
            pattern_id: Pattern identifier
            gain: Percentage gain
            days: Days to outcome

        Returns:
            PatternOutcome instance
        """
        # Classify based on gain
        if gain < 0:
            outcome_class = OutcomeClass.K5
            value = -10
        elif gain < 5:
            outcome_class = OutcomeClass.K0
            value = -2
        elif gain < 15:
            outcome_class = OutcomeClass.K1
            value = -0.2
        elif gain < 35:
            outcome_class = OutcomeClass.K2
            value = 1
        elif gain < 75:
            outcome_class = OutcomeClass.K3
            value = 3
        else:
            outcome_class = OutcomeClass.K4
            value = 10

        return cls(
            pattern_id=pattern_id,
            outcome_class=outcome_class,
            actual_gain=gain,
            days_to_outcome=days,
            max_gain=gain,  # Will be updated with actual tracking
            max_loss=0,  # Will be updated with actual tracking
            strategic_value=value,
        )