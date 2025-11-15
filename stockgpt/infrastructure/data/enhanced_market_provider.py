"""
Enhanced Market Data Provider with Multiple API Sources

Intelligently routes requests across multiple APIs based on:
- Rate limits (requests per minute/hour/day)
- API strengths (real-time, historical, fundamentals)
- Caching to minimize API calls
"""

import os
import asyncio
import aiohttp
import time
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict
import pandas as pd
import yfinance as yf

from stockgpt.core.interfaces.data import IDataProvider
from stockgpt.core.entities.stock import Stock, Price

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls with per-minute/hour/day limits."""

    def __init__(self, per_minute: int, per_hour: int = None, per_day: int = None):
        self.per_minute = per_minute
        self.per_hour = per_hour or (per_minute * 60 if per_minute else 60)
        self.per_day = per_day or (self.per_hour * 24 if self.per_hour else float('inf'))

        self.minute_calls = []
        self.hour_calls = []
        self.day_calls = []

    def can_call(self) -> bool:
        """Check if we can make an API call."""
        now = time.time()

        # Clean old timestamps
        self.minute_calls = [t for t in self.minute_calls if now - t < 60]
        self.hour_calls = [t for t in self.hour_calls if now - t < 3600]
        self.day_calls = [t for t in self.day_calls if now - t < 86400]

        # Check limits
        if len(self.minute_calls) >= self.per_minute:
            return False
        if len(self.hour_calls) >= self.per_hour:
            return False
        if len(self.day_calls) >= self.per_day:
            return False

        return True

    def record_call(self):
        """Record an API call."""
        now = time.time()
        self.minute_calls.append(now)
        self.hour_calls.append(now)
        self.day_calls.append(now)

    def wait_time(self) -> float:
        """Get seconds to wait before next call is allowed."""
        if self.can_call():
            return 0

        now = time.time()

        # Check minute limit
        if len(self.minute_calls) >= self.per_minute:
            oldest = min(self.minute_calls)
            return max(0, 60 - (now - oldest))

        return 1  # Default wait


class EnhancedMarketProvider(IDataProvider):
    """
    Enhanced provider using multiple professional APIs efficiently.

    API Limits (Free Tiers):
    - Alpha Vantage: 5 req/min, 500/day
    - Finnhub: 60 req/min
    - Twelve Data: 8 req/min, 800/day
    - FMP: 250 req/day
    - Yahoo Finance: Unlimited (fallback)
    """

    def __init__(
        self,
        cache_dir: str = "./data/cache",
        use_cache: bool = True,
        cache_ttl_minutes: int = 15,
    ):
        """Initialize with API keys and rate limiters."""

        # API Keys
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "FPG7DCR33BFK2HDP")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "d2f75n1r01qj3egrhu7gd2f75n1r01qj3egrhu80")
        self.twelvedata_key = os.getenv("TWELVEDATA_API_KEY", "5361b6392f4941d99f08d14d22551cb2")
        self.fmp_key = os.getenv("FMP_API_KEY", "smkqs1APQJVN2JuJAxSDkEvk7tDdTdZm")

        # Rate Limiters
        self.rate_limiters = {
            "alpha_vantage": RateLimiter(per_minute=5, per_day=500),
            "finnhub": RateLimiter(per_minute=60),
            "twelvedata": RateLimiter(per_minute=8, per_day=800),
            "fmp": RateLimiter(per_minute=5, per_day=250),
        }

        # Cache configuration
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

        # API usage tracking
        self.api_usage = defaultdict(int)

        logger.info("Enhanced Market Provider initialized with 4 professional APIs + Yahoo fallback")

    async def get_stocks(
        self,
        symbols: Optional[List[str]] = None,
        sector: Optional[str] = None,
        market_cap_min: Optional[float] = None,
        market_cap_max: Optional[float] = None,
    ) -> List[Stock]:
        """Get stock metadata using the most appropriate API."""

        stocks = []

        if symbols:
            for symbol in symbols:
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
        Get historical prices using intelligent API routing.

        Strategy:
        1. Check cache first
        2. For recent data (<7 days): Use Finnhub (best for real-time)
        3. For historical data: Use Twelve Data or Alpha Vantage
        4. Fallback: Yahoo Finance
        """

        # Determine date range
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        elif not start_date:
            start_date = date.today() - timedelta(days=365)
        if not end_date:
            end_date = date.today()

        # Check cache
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if self.use_cache:
            cached = self._load_from_cache(cache_key, "prices")
            if cached:
                logger.debug(f"Using cached data for {symbol}")
                return cached

        # Determine best API based on data requirements
        days_requested = (end_date - start_date).days

        prices = None

        # Try APIs in order of preference
        if days_requested <= 7 and self.rate_limiters["finnhub"].can_call():
            prices = await self._fetch_finnhub_prices(symbol, start_date, end_date)

        if not prices and days_requested <= 30 and self.rate_limiters["twelvedata"].can_call():
            prices = await self._fetch_twelvedata_prices(symbol, start_date, end_date)

        if not prices and self.rate_limiters["alpha_vantage"].can_call():
            prices = await self._fetch_alpha_vantage_prices(symbol, start_date, end_date)

        if not prices and self.rate_limiters["fmp"].can_call():
            prices = await self._fetch_fmp_prices(symbol, start_date, end_date)

        # Fallback to Yahoo
        if not prices:
            logger.debug(f"Using Yahoo Finance fallback for {symbol}")
            prices = await self._fetch_yahoo_prices(symbol, start_date, end_date)

        # Cache the results
        if prices and self.use_cache:
            self._save_to_cache(cache_key, "prices", prices)

        return prices or []

    async def _fetch_stock_info(self, symbol: str) -> Optional[Stock]:
        """Fetch stock info, preferring FMP for fundamentals."""

        # Try FMP first (good for fundamentals)
        if self.rate_limiters["fmp"].can_call():
            stock = await self._fetch_fmp_profile(symbol)
            if stock:
                return stock

        # Fallback to Yahoo
        return await self._fetch_yahoo_info(symbol)

    async def _fetch_alpha_vantage_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Price]:
        """Fetch from Alpha Vantage API (good for daily data)."""

        if not self.rate_limiters["alpha_vantage"].can_call():
            return []

        url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_DAILY"
            f"&symbol={symbol}"
            f"&outputsize=full"
            f"&apikey={self.alpha_vantage_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["alpha_vantage"].record_call()
            self.api_usage["alpha_vantage"] += 1

            if "Time Series (Daily)" not in data:
                return []

            prices = []
            for date_str, values in data["Time Series (Daily)"].items():
                price_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                if start_date <= price_date <= end_date:
                    prices.append(Price(
                        symbol=symbol,
                        date=price_date,
                        open=float(values["1. open"]),
                        high=float(values["2. high"]),
                        low=float(values["3. low"]),
                        close=float(values["4. close"]),
                        volume=int(values["5. volume"]),
                    ))

            logger.info(f"Alpha Vantage: Fetched {len(prices)} prices for {symbol}")
            return sorted(prices, key=lambda p: p.date)

        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return []

    async def _fetch_finnhub_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Price]:
        """Fetch from Finnhub (excellent for real-time and recent data)."""

        if not self.rate_limiters["finnhub"].can_call():
            return []

        # Convert dates to timestamps
        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        url = (
            f"https://finnhub.io/api/v1/stock/candle"
            f"?symbol={symbol}"
            f"&resolution=D"
            f"&from={start_ts}"
            f"&to={end_ts}"
            f"&token={self.finnhub_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["finnhub"].record_call()
            self.api_usage["finnhub"] += 1

            if data.get("s") != "ok":
                return []

            prices = []
            for i in range(len(data.get("t", []))):
                prices.append(Price(
                    symbol=symbol,
                    date=datetime.fromtimestamp(data["t"][i]).date(),
                    open=data["o"][i],
                    high=data["h"][i],
                    low=data["l"][i],
                    close=data["c"][i],
                    volume=int(data["v"][i]),
                ))

            logger.info(f"Finnhub: Fetched {len(prices)} prices for {symbol}")
            return prices

        except Exception as e:
            logger.error(f"Finnhub error for {symbol}: {e}")
            return []

    async def _fetch_twelvedata_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Price]:
        """Fetch from Twelve Data (good balance of features)."""

        if not self.rate_limiters["twelvedata"].can_call():
            return []

        url = (
            f"https://api.twelvedata.com/time_series"
            f"?symbol={symbol}"
            f"&interval=1day"
            f"&start_date={start_date}"
            f"&end_date={end_date}"
            f"&apikey={self.twelvedata_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["twelvedata"].record_call()
            self.api_usage["twelvedata"] += 1

            if "values" not in data:
                return []

            prices = []
            for bar in data["values"]:
                prices.append(Price(
                    symbol=symbol,
                    date=datetime.strptime(bar["datetime"], "%Y-%m-%d").date(),
                    open=float(bar["open"]),
                    high=float(bar["high"]),
                    low=float(bar["low"]),
                    close=float(bar["close"]),
                    volume=int(bar.get("volume", 0)),
                ))

            logger.info(f"Twelve Data: Fetched {len(prices)} prices for {symbol}")
            return sorted(prices, key=lambda p: p.date)

        except Exception as e:
            logger.error(f"Twelve Data error for {symbol}: {e}")
            return []

    async def _fetch_fmp_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Price]:
        """Fetch from Financial Modeling Prep (good for fundamentals)."""

        if not self.rate_limiters["fmp"].can_call():
            return []

        url = (
            f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
            f"?from={start_date}"
            f"&to={end_date}"
            f"&apikey={self.fmp_key}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["fmp"].record_call()
            self.api_usage["fmp"] += 1

            if "historical" not in data:
                return []

            prices = []
            for bar in data["historical"]:
                prices.append(Price(
                    symbol=symbol,
                    date=datetime.strptime(bar["date"], "%Y-%m-%d").date(),
                    open=bar["open"],
                    high=bar["high"],
                    low=bar["low"],
                    close=bar["close"],
                    volume=int(bar.get("volume", 0)),
                    adjusted_close=bar.get("adjClose"),
                ))

            logger.info(f"FMP: Fetched {len(prices)} prices for {symbol}")
            return sorted(prices, key=lambda p: p.date)

        except Exception as e:
            logger.error(f"FMP error for {symbol}: {e}")
            return []

    async def _fetch_fmp_profile(self, symbol: str) -> Optional[Stock]:
        """Fetch company profile from FMP."""

        if not self.rate_limiters["fmp"].can_call():
            return None

        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.fmp_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["fmp"].record_call()
            self.api_usage["fmp"] += 1

            if not data:
                return None

            profile = data[0]
            return Stock(
                symbol=symbol,
                name=profile.get("companyName", symbol),
                sector=profile.get("sector"),
                industry=profile.get("industry"),
                market_cap=profile.get("mktCap"),
                exchange=profile.get("exchange"),
                is_active=profile.get("isActivelyTrading", True),
                metadata={
                    "country": profile.get("country"),
                    "website": profile.get("website"),
                    "description": profile.get("description"),
                    "ceo": profile.get("ceo"),
                    "employees": profile.get("fullTimeEmployees"),
                }
            )

        except Exception as e:
            logger.error(f"FMP profile error for {symbol}: {e}")
            return None

    async def _fetch_yahoo_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Price]:
        """Fallback to Yahoo Finance (unlimited, but less features)."""

        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)

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
                ))

            logger.info(f"Yahoo: Fetched {len(prices)} prices for {symbol}")
            return prices

        except Exception as e:
            logger.error(f"Yahoo error for {symbol}: {e}")
            return []

    async def _fetch_yahoo_info(self, symbol: str) -> Optional[Stock]:
        """Fallback to Yahoo for stock info."""

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
            )
        except Exception as e:
            logger.error(f"Yahoo info error for {symbol}: {e}")
            return None

    async def get_latest_price(self, symbol: str) -> Optional[Price]:
        """Get latest price, preferring real-time APIs."""

        # Try Finnhub first (best for real-time)
        if self.rate_limiters["finnhub"].can_call():
            price = await self._fetch_finnhub_quote(symbol)
            if price:
                return price

        # Try FMP
        if self.rate_limiters["fmp"].can_call():
            price = await self._fetch_fmp_quote(symbol)
            if price:
                return price

        # Fallback to Yahoo
        return await self._fetch_yahoo_quote(symbol)

    async def _fetch_finnhub_quote(self, symbol: str) -> Optional[Price]:
        """Get real-time quote from Finnhub."""

        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["finnhub"].record_call()

            return Price(
                symbol=symbol,
                date=date.today(),
                open=data["o"],
                high=data["h"],
                low=data["l"],
                close=data["c"],
                volume=0,  # Quote doesn't include volume
            )
        except Exception:
            return None

    async def _fetch_fmp_quote(self, symbol: str) -> Optional[Price]:
        """Get quote from FMP."""

        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={self.fmp_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()

            self.rate_limiters["fmp"].record_call()

            if not data:
                return None

            quote = data[0]
            return Price(
                symbol=symbol,
                date=date.today(),
                open=quote["open"],
                high=quote["dayHigh"],
                low=quote["dayLow"],
                close=quote["price"],
                volume=quote.get("volume", 0),
            )
        except Exception:
            return None

    async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Price]:
        """Get latest from Yahoo."""

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
        except Exception:
            return None

    async def get_technical_features(
        self, symbol: str, date: Optional[date] = None
    ) -> Dict[str, float]:
        """Calculate technical features using best available data."""

        # Get 100 days of data for indicator calculation
        prices = await self.get_prices(symbol, days=100)

        if not prices or len(prices) < 50:
            return {}

        # Convert to DataFrame
        df = pd.DataFrame([p.to_dict() for p in prices])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Calculate indicators
        features = {}

        # Price and volume
        features['price'] = df['close'].iloc[-1]
        features['volume'] = df['volume'].iloc[-1]

        # Moving averages
        features['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
        features['sma_50'] = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else features['sma_20']

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi_14'] = (100 - (100 / (1 + rs))).iloc[-1]

        # Bollinger Bands
        bb_sma = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        features['bb_upper'] = (bb_sma + 2 * bb_std).iloc[-1]
        features['bb_lower'] = (bb_sma - 2 * bb_std).iloc[-1]
        features['bbw'] = ((features['bb_upper'] - features['bb_lower']) / bb_sma.iloc[-1] * 100)

        # Volume ratio (handle None/NaN values)
        volume_mean = df['volume'].rolling(20).mean().iloc[-1]
        if pd.notna(df['volume'].iloc[-1]) and pd.notna(volume_mean) and volume_mean > 0:
            features['volume_ratio'] = df['volume'].iloc[-1] / volume_mean
        else:
            features['volume_ratio'] = 1.0

        # Price changes (handle None/NaN values)
        if len(df) >= 20 and pd.notna(df['close'].iloc[-1]) and pd.notna(df['close'].iloc[-20]) and df['close'].iloc[-20] > 0:
            features['price_change_20d'] = ((df['close'].iloc[-1] - df['close'].iloc[-20]) /
                                            df['close'].iloc[-20] * 100)
        else:
            features['price_change_20d'] = 0.0

        # Volatility (handle None/NaN values)
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        if pd.notna(volatility):
            features['volatility_20d'] = volatility * 100
        else:
            features['volatility_20d'] = 2.0

        return features

    def _load_from_cache(self, key: str, data_type: str) -> Optional[Any]:
        """Load from cache if fresh."""

        cache_file = self.cache_dir / f"{data_type}_{key}.json"

        if not cache_file.exists():
            return None

        # Check cache age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - file_time > self.cache_ttl:
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

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
                    )
                    for p in data
                ]

            return data

        except Exception:
            return None

    def _save_to_cache(self, key: str, data_type: str, data: Any) -> None:
        """Save to cache."""

        cache_file = self.cache_dir / f"{data_type}_{key}.json"

        try:
            if data_type == "prices" and data and isinstance(data[0], Price):
                data = [p.to_dict() for p in data]

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Cache save error: {e}")

    async def refresh_data(
        self, symbols: Optional[List[str]] = None, force: bool = False
    ) -> Dict[str, Any]:
        """Refresh data for symbols."""

        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMD"]

        refreshed = []
        failed = []

        for symbol in symbols:
            try:
                if force:
                    # Clear cache for symbol
                    for cache_file in self.cache_dir.glob(f"*{symbol}*"):
                        cache_file.unlink()

                prices = await self.get_prices(symbol, days=5)

                if prices:
                    refreshed.append(symbol)
                else:
                    failed.append(symbol)

            except Exception as e:
                logger.error(f"Refresh error for {symbol}: {e}")
                failed.append(symbol)

        return {
            "refreshed": refreshed,
            "failed": failed,
            "api_usage": dict(self.api_usage),
        }

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information including API usage."""

        return {
            "provider": "EnhancedMarketProvider",
            "apis_configured": {
                "alpha_vantage": bool(self.alpha_vantage_key),
                "finnhub": bool(self.finnhub_key),
                "twelvedata": bool(self.twelvedata_key),
                "fmp": bool(self.fmp_key),
                "yahoo": True,  # Always available
            },
            "api_usage": dict(self.api_usage),
            "rate_limits": {
                "alpha_vantage": "5/min, 500/day",
                "finnhub": "60/min",
                "twelvedata": "8/min, 800/day",
                "fmp": "250/day",
            },
            "cache_enabled": self.use_cache,
            "cache_ttl_minutes": self.cache_ttl.seconds // 60,
        }

    async def check_connection(self) -> bool:
        """Check if we can connect to at least one API."""

        # Quick check with Yahoo (always works)
        try:
            ticker = yf.Ticker("SPY")
            history = ticker.history(period="1d")
            return not history.empty
        except Exception:
            return False