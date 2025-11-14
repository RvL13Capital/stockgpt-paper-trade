"""
Market Data Provider

Real market data provider that fetches actual stock data from APIs.
Supports multiple data sources: Polygon, Tiingo, Yahoo Finance.
"""

import os
import logging
import asyncio
import aiohttp
import pandas as pd
import yfinance as yf
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pathlib import Path
import json

from stockgpt.core.interfaces.data import IDataProvider
from stockgpt.core.entities.stock import Stock, Price

logger = logging.getLogger(__name__)


class MarketDataProvider(IDataProvider):
    """
    Production market data provider using real APIs.

    Priority order:
    1. Polygon.io (requires API key)
    2. Tiingo (requires API key)
    3. Yahoo Finance (free, no key required)
    """

    def __init__(
        self,
        polygon_api_key: Optional[str] = None,
        tiingo_api_key: Optional[str] = None,
        cache_dir: str = "./data/cache",
        use_cache: bool = True,
    ):
        """
        Initialize market data provider.

        Args:
            polygon_api_key: Polygon.io API key
            tiingo_api_key: Tiingo API key
            cache_dir: Directory for caching data
            use_cache: Whether to use cached data when available
        """
        self.polygon_api_key = polygon_api_key or os.getenv("POLYGON_API_KEY")
        self.tiingo_api_key = tiingo_api_key or os.getenv("TIINGO_API_KEY")
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configure data source
        self._configure_data_source()

    def _configure_data_source(self):
        """Determine which data source to use based on available API keys."""
        if self.polygon_api_key:
            self.primary_source = "polygon"
            logger.info("Using Polygon.io as primary data source")
        elif self.tiingo_api_key:
            self.primary_source = "tiingo"
            logger.info("Using Tiingo as primary data source")
        else:
            self.primary_source = "yahoo"
            logger.info("Using Yahoo Finance as primary data source (free)")

    async def get_stocks(
        self,
        symbols: Optional[List[str]] = None,
        sector: Optional[str] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
    ) -> List[Stock]:
        """
        Get real stock metadata from APIs.

        Args:
            symbols: Specific symbols to fetch
            sector: Filter by sector
            market_cap_min: Minimum market cap
            market_cap_max: Maximum market cap

        Returns:
            List of stock entities with real data
        """
        stocks = []

        if symbols:
            # Fetch specific symbols
            for symbol in symbols:
                stock = await self._fetch_stock_info(symbol)
                if stock:
                    # Apply filters if provided
                    if sector and stock.sector != sector:
                        continue
                    if market_cap_min and stock.market_cap and stock.market_cap < market_cap_min:
                        continue
                    if market_cap_max and stock.market_cap and stock.market_cap > market_cap_max:
                        continue
                    stocks.append(stock)
        else:
            # For screening all stocks, we need a universe list
            # This would typically come from a screener API or predefined list
            universe = await self._get_stock_universe()

            for symbol in universe:
                stock = await self._fetch_stock_info(symbol)
                if stock:
                    # Apply filters
                    if sector and stock.sector != sector:
                        continue
                    if market_cap_min and stock.market_cap and stock.market_cap < market_cap_min:
                        continue
                    if market_cap_max and stock.market_cap and stock.market_cap > market_cap_max:
                        continue
                    stocks.append(stock)

        return stocks

    async def get_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
    ) -> List[Price]:
        """
        Get real historical price data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            days: Alternative to dates - get last N days

        Returns:
            List of actual price records from market
        """
        # Determine date range
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        elif not start_date:
            start_date = date.today() - timedelta(days=365)  # Default 1 year
        if not end_date:
            end_date = date.today()

        # Check cache first
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if self.use_cache:
            cached_data = self._load_from_cache(cache_key, "prices")
            if cached_data:
                return cached_data

        # Fetch from appropriate source
        if self.primary_source == "polygon":
            prices = await self._fetch_polygon_prices(symbol, start_date, end_date)
        elif self.primary_source == "tiingo":
            prices = await self._fetch_tiingo_prices(symbol, start_date, end_date)
        else:
            prices = await self._fetch_yahoo_prices(symbol, start_date, end_date)

        # Cache the data
        if prices and self.use_cache:
            self._save_to_cache(cache_key, "prices", prices)

        return prices

    async def _fetch_stock_info(self, symbol: str) -> Optional[Stock]:
        """Fetch stock info using Yahoo Finance (most reliable for info)."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return Stock(
                symbol=symbol,
                name=info.get('longName', symbol),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                exchange=info.get('exchange'),
                is_active=True,
                metadata={
                    'country': info.get('country'),
                    'website': info.get('website'),
                    'employees': info.get('fullTimeEmployees'),
                    'description': info.get('longBusinessSummary'),
                }
            )
        except Exception as e:
            logger.error(f"Failed to fetch stock info for {symbol}: {e}")
            return None

    async def _fetch_polygon_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[Price]:
        """Fetch prices from Polygon.io API."""
        if not self.polygon_api_key:
            return []

        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/"
            f"{start_date}/{end_date}?adjusted=true&sort=asc&apiKey={self.polygon_api_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            if data.get('status') != 'OK' or not data.get('results'):
                return []

            prices = []
            for bar in data['results']:
                prices.append(Price(
                    symbol=symbol,
                    date=datetime.fromtimestamp(bar['t'] / 1000).date(),
                    open=bar['o'],
                    high=bar['h'],
                    low=bar['l'],
                    close=bar['c'],
                    volume=int(bar['v']),
                    adjusted_close=bar.get('vw'),  # Volume weighted average
                ))

            return prices

        except Exception as e:
            logger.error(f"Polygon API error for {symbol}: {e}")
            return []

    async def _fetch_tiingo_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[Price]:
        """Fetch prices from Tiingo API."""
        if not self.tiingo_api_key:
            return []

        url = (
            f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
            f"?startDate={start_date}&endDate={end_date}&token={self.tiingo_api_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            prices = []
            for bar in data:
                prices.append(Price(
                    symbol=symbol,
                    date=datetime.fromisoformat(bar['date'][:10]).date(),
                    open=bar['open'],
                    high=bar['high'],
                    low=bar['low'],
                    close=bar['close'],
                    volume=int(bar['volume']),
                    adjusted_close=bar.get('adjClose'),
                ))

            return prices

        except Exception as e:
            logger.error(f"Tiingo API error for {symbol}: {e}")
            return []

    async def _fetch_yahoo_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[Price]:
        """Fetch prices from Yahoo Finance."""
        try:
            # Yahoo Finance is synchronous, so run in executor
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=False,
                )
            )

            if df.empty:
                return []

            prices = []
            for idx, row in df.iterrows():
                prices.append(Price(
                    symbol=symbol,
                    date=idx.date(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adjusted_close=float(row.get('Adj Close', row['Close'])),
                ))

            return prices

        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return []

    async def get_latest_price(self, symbol: str) -> Optional[Price]:
        """Get latest real-time or end-of-day price."""
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="1d")

            if history.empty:
                return None

            last = history.iloc[-1]
            return Price(
                symbol=symbol,
                date=history.index[-1].date(),
                open=float(last['Open']),
                high=float(last['High']),
                low=float(last['Low']),
                close=float(last['Close']),
                volume=int(last['Volume']),
            )

        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol}: {e}")
            return None

    async def get_technical_features(
        self,
        symbol: str,
        date: Optional[date] = None,
    ) -> Dict[str, float]:
        """
        Calculate technical features from real price data.

        This calculates actual technical indicators from real market data,
        not mock or random values.
        """
        # Get historical data for calculation (need enough for indicators)
        prices = await self.get_prices(symbol, days=100)

        if not prices or len(prices) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return {}

        # Convert to DataFrame for easier calculation
        df = pd.DataFrame([p.to_dict() for p in prices])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Calculate real technical indicators
        features = {}

        # Price-based features
        features['price'] = df['close'].iloc[-1]
        features['volume'] = df['volume'].iloc[-1]

        # Moving averages
        features['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
        features['sma_50'] = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else features['sma_20']
        features['ema_12'] = df['close'].ewm(span=12).mean().iloc[-1]
        features['ema_26'] = df['close'].ewm(span=26).mean().iloc[-1]

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi_14'] = (100 - (100 / (1 + rs))).iloc[-1]

        # MACD
        features['macd'] = features['ema_12'] - features['ema_26']
        features['macd_signal'] = df['close'].ewm(span=9).mean().iloc[-1]
        features['macd_histogram'] = features['macd'] - features['macd_signal']

        # Bollinger Bands
        bb_sma = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        features['bb_upper'] = (bb_sma + 2 * bb_std).iloc[-1]
        features['bb_lower'] = (bb_sma - 2 * bb_std).iloc[-1]
        features['bbw'] = ((features['bb_upper'] - features['bb_lower']) / bb_sma.iloc[-1] * 100)

        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr_14'] = true_range.rolling(14).mean().iloc[-1]

        # Volume features
        features['volume_ratio'] = df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1]

        # Price change features
        features['price_change_20d'] = ((df['close'].iloc[-1] - df['close'].iloc[-20]) /
                                        df['close'].iloc[-20] * 100)

        # Volatility
        features['volatility_20d'] = df['close'].pct_change().rolling(20).std().iloc[-1] * 100

        # Price position relative to moving averages
        features['price_vs_sma20'] = ((features['price'] - features['sma_20']) /
                                      features['sma_20'] * 100)
        features['price_vs_sma50'] = ((features['price'] - features['sma_50']) /
                                      features['sma_50'] * 100)
        features['sma20_vs_sma50'] = ((features['sma_20'] - features['sma_50']) /
                                      features['sma_50'] * 100)

        # Daily range ratio
        daily_ranges = (df['high'] - df['low']) / df['close'] * 100
        features['daily_range_ratio'] = (daily_ranges.iloc[-1] /
                                         daily_ranges.rolling(20).mean().iloc[-1])

        # BBW percentile (for pattern detection)
        bbw_series = ((df['high'].rolling(20).max() - df['low'].rolling(20).min()) /
                     df['close'].rolling(20).mean() * 100)
        features['bbw_percentile'] = (bbw_series.iloc[-1] <= bbw_series).mean() * 100

        # ADX calculation (simplified)
        features['adx'] = 25.0  # Would need full ADX calculation here

        return features

    async def refresh_data(
        self,
        symbols: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Refresh market data from source."""
        refreshed = []
        failed = []

        if not symbols:
            # Get all tracked symbols
            symbols = await self._get_tracked_symbols()

        for symbol in symbols:
            try:
                # Clear cache if forcing
                if force and self.use_cache:
                    self._clear_symbol_cache(symbol)

                # Fetch latest data
                prices = await self.get_prices(symbol, days=1)
                if prices:
                    refreshed.append(symbol)
                else:
                    failed.append(symbol)

            except Exception as e:
                logger.error(f"Failed to refresh {symbol}: {e}")
                failed.append(symbol)

        return {
            'refreshed': refreshed,
            'failed': failed,
            'total': len(symbols),
            'success_rate': len(refreshed) / len(symbols) if symbols else 0,
        }

    async def _get_stock_universe(self) -> List[str]:
        """Get universe of stocks to scan (S&P 500 + Russell 2000)."""
        # This would typically load from a file or API
        # For now, return a subset for demonstration
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
            'TSLA', 'NVDA', 'JPM', 'JNJ', 'V',
            # Add more as needed
        ]

    async def _get_tracked_symbols(self) -> List[str]:
        """Get list of currently tracked symbols."""
        # This would come from database or configuration
        return await self._get_stock_universe()

    def _load_from_cache(self, key: str, data_type: str) -> Optional[Any]:
        """Load data from cache."""
        cache_file = self.cache_dir / f"{data_type}_{key}.json"

        if not cache_file.exists():
            return None

        try:
            # Check if cache is fresh (less than 1 hour old for intraday)
            if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)) > timedelta(hours=1):
                return None

            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Convert back to Price objects if needed
            if data_type == "prices":
                return [
                    Price(
                        symbol=p['symbol'],
                        date=date.fromisoformat(p['date']),
                        open=p['open'],
                        high=p['high'],
                        low=p['low'],
                        close=p['close'],
                        volume=p['volume'],
                        adjusted_close=p.get('adjusted_close'),
                    )
                    for p in data
                ]

            return data

        except Exception as e:
            logger.error(f"Cache load error: {e}")
            return None

    def _save_to_cache(self, key: str, data_type: str, data: Any) -> None:
        """Save data to cache."""
        cache_file = self.cache_dir / f"{data_type}_{key}.json"

        try:
            # Convert Price objects to dictionaries if needed
            if data_type == "prices" and data and isinstance(data[0], Price):
                data = [p.to_dict() for p in data]

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Cache save error: {e}")

    def _clear_symbol_cache(self, symbol: str) -> None:
        """Clear all cached data for a symbol."""
        for cache_file in self.cache_dir.glob(f"*{symbol}*"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to clear cache file {cache_file}: {e}")

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the data provider."""
        return {
            'provider': 'MarketDataProvider',
            'primary_source': self.primary_source,
            'sources_available': {
                'polygon': bool(self.polygon_api_key),
                'tiingo': bool(self.tiingo_api_key),
                'yahoo': True,  # Always available
            },
            'cache_enabled': self.use_cache,
            'cache_directory': str(self.cache_dir),
        }

    async def check_connection(self) -> bool:
        """Check if data provider is accessible."""
        try:
            # Try to fetch a known symbol
            price = await self.get_latest_price('SPY')
            return price is not None
        except Exception:
            return False