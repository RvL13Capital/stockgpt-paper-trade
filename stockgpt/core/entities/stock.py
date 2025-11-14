"""
Stock and Price Entities

Core entities for stock metadata and price data.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class Stock:
    """
    Immutable stock metadata entity.

    Attributes:
        symbol: Stock ticker symbol
        name: Company name
        sector: Business sector
        industry: Specific industry
        market_cap: Market capitalization in USD
        exchange: Stock exchange
        is_active: Whether stock is actively traded
        metadata: Additional stock information
    """

    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    exchange: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate stock data."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")

        if not self.name:
            raise ValueError("Name cannot be empty")

        if self.market_cap and self.market_cap < 0:
            raise ValueError("Market cap cannot be negative")

    @property
    def is_micro_cap(self) -> bool:
        """Check if stock is micro-cap (<$300M)."""
        if not self.market_cap:
            return False
        return self.market_cap < 300_000_000

    @property
    def is_small_cap(self) -> bool:
        """Check if stock is small-cap ($300M-$2B)."""
        if not self.market_cap:
            return False
        return 300_000_000 <= self.market_cap < 2_000_000_000

    @property
    def market_cap_category(self) -> str:
        """Get market cap category."""
        if not self.market_cap:
            return "Unknown"

        if self.market_cap < 300_000_000:
            return "Micro"
        elif self.market_cap < 2_000_000_000:
            return "Small"
        elif self.market_cap < 10_000_000_000:
            return "Mid"
        elif self.market_cap < 100_000_000_000:
            return "Large"
        else:
            return "Mega"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'sector': self.sector,
            'industry': self.industry,
            'market_cap': self.market_cap,
            'market_cap_category': self.market_cap_category,
            'exchange': self.exchange,
            'is_active': self.is_active,
            'is_micro_cap': self.is_micro_cap,
            'is_small_cap': self.is_small_cap,
            'metadata': self.metadata,
        }


@dataclass(frozen=True)
class Price:
    """
    Immutable price data entity (OHLCV).

    Attributes:
        symbol: Stock symbol
        date: Price date
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        adjusted_close: Adjusted closing price (for splits/dividends)
    """

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None

    def __post_init__(self):
        """Validate price data."""
        if any(p < 0 for p in [self.open, self.high, self.low, self.close]):
            raise ValueError("Prices cannot be negative")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

        if self.low > self.high:
            raise ValueError(f"Low ({self.low}) cannot be greater than high ({self.high})")

        if self.open > self.high or self.open < self.low:
            raise ValueError("Open must be between low and high")

        if self.close > self.high or self.close < self.low:
            raise ValueError("Close must be between low and high")

    @property
    def daily_range(self) -> float:
        """Calculate daily price range."""
        return self.high - self.low

    @property
    def daily_range_percentage(self) -> float:
        """Calculate daily range as percentage of close."""
        if self.close == 0:
            return 0.0
        return (self.daily_range / self.close) * 100

    @property
    def daily_change(self) -> float:
        """Calculate daily change (close - open)."""
        return self.close - self.open

    @property
    def daily_change_percentage(self) -> float:
        """Calculate daily change as percentage."""
        if self.open == 0:
            return 0.0
        return (self.daily_change / self.open) * 100

    @property
    def is_bullish(self) -> bool:
        """Check if day was bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if day was bearish (close < open)."""
        return self.close < self.open

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close,
            'daily_range': self.daily_range,
            'daily_range_percentage': self.daily_range_percentage,
            'daily_change': self.daily_change,
            'daily_change_percentage': self.daily_change_percentage,
            'is_bullish': self.is_bullish,
            'is_bearish': self.is_bearish,
        }