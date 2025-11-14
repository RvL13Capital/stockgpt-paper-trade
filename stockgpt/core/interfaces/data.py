"""
Data Provider Interface

Defines the contract for data providers (APIs, databases, files).
"""

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime, date
from stockgpt.core.entities.stock import Stock, Price


class IDataProvider(Protocol):
    """Interface for market data providers."""

    async def get_stocks(
        self,
        symbols: Optional[List[str]] = None,
        sector: Optional[str] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
    ) -> List[Stock]:
        """
        Get stock metadata.

        Args:
            symbols: Specific symbols to fetch
            sector: Filter by sector
            market_cap_min: Minimum market cap
            market_cap_max: Maximum market cap

        Returns:
            List of stock entities
        """
        ...

    async def get_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
    ) -> List[Price]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            days: Alternative to dates - get last N days

        Returns:
            List of price records ordered by date
        """
        ...

    async def get_latest_price(self, symbol: str) -> Optional[Price]:
        """
        Get latest price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Latest price or None if not found
        """
        ...

    async def get_technical_features(
        self,
        symbol: str,
        date: Optional[date] = None,
    ) -> Dict[str, float]:
        """
        Get pre-calculated technical features.

        Args:
            symbol: Stock symbol
            date: Date for features (None = latest)

        Returns:
            Dictionary of feature names to values
        """
        ...

    async def refresh_data(
        self,
        symbols: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Refresh data from source.

        Args:
            symbols: Symbols to refresh (None = all)
            force: Force refresh even if cache is fresh

        Returns:
            Refresh status and statistics
        """
        ...

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the data provider.

        Returns:
            Provider name, version, capabilities, etc.
        """
        ...

    async def check_connection(self) -> bool:
        """
        Check if data provider is accessible.

        Returns:
            True if connected, False otherwise
        """
        ...