import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.config import settings
from app.core.logging import logger
from app.models.stock import Stock, StockPrice, StockFeature
from app.models.signal import Signal
from app.services.technical_analysis import TechnicalAnalysisService

class DataIngestionService:
    def __init__(self):
        self.polygon_api_key = settings.POLYGON_API_KEY
        self.tiingo_api_key = settings.TIINGO_API_KEY
        self.ta_service = TechnicalAnalysisService()
        
    async def fetch_stock_list(self) -> List[Dict[str, Any]]:
        """Fetch list of available stocks from Polygon API"""
        url = f"https://api.polygon.io/v3/reference/tickers"
        params = {
            "market": "stocks",
            "active": "true",
            "limit": 1000,
            "apiKey": self.polygon_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        logger.error(f"Failed to fetch stock list: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching stock list: {e}")
                return []
    
    async def fetch_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical stock data from Polygon API"""
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.polygon_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        
                        if not results:
                            return pd.DataFrame()
                        
                        df = pd.DataFrame(results)
                        df["symbol"] = symbol
                        df["date"] = pd.to_datetime(df["t"], unit="ms").dt.date
                        
                        # Rename columns to match our schema
                        df = df.rename(columns={
                            "o": "open",
                            "h": "high",
                            "l": "low",
                            "c": "close",
                            "v": "volume",
                            "vw": "vwap"
                        })
                        
                        return df[["symbol", "date", "open", "high", "low", "close", "volume", "vwap"]]
                    else:
                        logger.error(f"Failed to fetch data for {symbol}: {response.status}")
                        return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                return pd.DataFrame()
    
    async def ingest_stock_data(self, db: AsyncSession, symbols: List[str], 
                              days_back: int = 365) -> int:
        """Ingest stock data for given symbols"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        ingested_count = 0
        
        for symbol in symbols:
            try:
                logger.info(f"Ingesting data for {symbol}")
                
                # Fetch stock data
                df = await self.fetch_stock_data(symbol, start_date.isoformat(), end_date.isoformat())
                
                if df.empty:
                    logger.warning(f"No data found for {symbol}")
                    continue
                
                # Process and store data
                await self._process_stock_data(db, df, symbol)
                ingested_count += 1
                
                # Rate limiting
                await asyncio.sleep(0.1)  # 100ms delay between requests
                
            except Exception as e:
                logger.error(f"Error ingesting data for {symbol}: {e}")
                continue
        
        logger.info(f"Successfully ingested data for {ingested_count} symbols")
        return ingested_count
    
    async def _process_stock_data(self, db: AsyncSession, df: pd.DataFrame, symbol: str):
        """Process and store stock data in database"""
        
        # Check existing data to avoid duplicates
        existing_dates = await self._get_existing_dates(db, symbol)
        
        for _, row in df.iterrows():
            date = row["date"]
            
            if date in existing_dates:
                continue
            
            # Create stock price record
            stock_price = StockPrice(
                symbol=symbol,
                date=date,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=int(row["volume"]),
            )
            
            db.add(stock_price)
        
        await db.commit()
        
        # Calculate technical indicators
        await self._calculate_technical_indicators(db, symbol, df)
    
    async def _get_existing_dates(self, db: AsyncSession, symbol: str) -> set:
        """Get existing dates for a symbol to avoid duplicates"""
        result = await db.execute(
            select(StockPrice.date).where(StockPrice.symbol == symbol)
        )
        return set(result.scalars().all())
    
    async def _calculate_technical_indicators(self, db: AsyncSession, symbol: str, df: pd.DataFrame):
        """Calculate and store technical indicators"""
        
        # Calculate indicators
        indicators_df = self.ta_service.calculate_indicators(df)
        
        # Store features
        for _, row in indicators_df.iterrows():
            feature = StockFeature(
                symbol=symbol,
                date=row["date"],
                sma_20=row.get("sma_20"),
                sma_50=row.get("sma_50"),
                sma_200=row.get("sma_200"),
                ema_12=row.get("ema_12"),
                ema_26=row.get("ema_26"),
                rsi_14=row.get("rsi_14"),
                macd=row.get("macd"),
                macd_signal=row.get("macd_signal"),
                macd_histogram=row.get("macd_histogram"),
                bollinger_upper=row.get("bollinger_upper"),
                bollinger_middle=row.get("bollinger_middle"),
                bollinger_lower=row.get("bollinger_lower"),
                atr_14=row.get("atr_14"),
                stochastic_k=row.get("stochastic_k"),
                stochastic_d=row.get("stochastic_d"),
                williams_r=row.get("williams_r"),
                cci=row.get("cci"),
                obv=row.get("obv"),
                vwap=row.get("vwap"),
                volume_sma_20=row.get("volume_sma_20"),
                volume_ratio=row.get("volume_ratio"),
                price_change_1d=row.get("price_change_1d"),
                price_change_5d=row.get("price_change_5d"),
                price_change_20d=row.get("price_change_20d"),
                price_change_60d=row.get("price_change_60d"),
                volatility_20d=row.get("volatility_20d"),
                volatility_60d=row.get("volatility_60d"),
                market_regime=row.get("market_regime"),
                sector_momentum=row.get("sector_momentum"),
                relative_strength=row.get("relative_strength"),
            )
            
            db.add(feature)
        
        await db.commit()
    
    async def update_stock_info(self, db: AsyncSession) -> int:
        """Update stock information from Polygon API"""
        stocks_data = await self.fetch_stock_list()
        
        updated_count = 0
        
        for stock_data in stocks_data[:1000]:  # Limit to first 1000 stocks
            try:
                symbol = stock_data.get("ticker")
                name = stock_data.get("name", "")
                sector = stock_data.get("sector", "")
                industry = stock_data.get("industry", "")
                market_cap = stock_data.get("market_cap")
                
                # Check if stock exists
                result = await db.execute(
                    select(Stock).where(Stock.symbol == symbol)
                )
                stock = result.scalar_one_or_none()
                
                if stock:
                    # Update existing stock
                    stock.name = name
                    stock.sector = sector
                    stock.industry = industry
                    stock.market_cap = market_cap
                else:
                    # Create new stock
                    stock = Stock(
                        symbol=symbol,
                        name=name,
                        sector=sector,
                        industry=industry,
                        market_cap=market_cap,
                    )
                    db.add(stock)
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    await db.commit()
                
            except Exception as e:
                logger.error(f"Error processing stock {stock_data.get('ticker', 'Unknown')}: {e}")
                continue
        
        await db.commit()
        logger.info(f"Updated information for {updated_count} stocks")
        return updated_count
    
    async def get_symbols_for_ingestion(self, db: AsyncSession, limit: int = 100) -> List[str]:
        """Get symbols that need data ingestion"""
        # Get symbols from database
        result = await db.execute(
            select(Stock.symbol)
            .where(Stock.is_active == True)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def scheduled_ingestion(self, db: AsyncSession):
        """Scheduled data ingestion task"""
        logger.info("Starting scheduled data ingestion")
        
        # Get symbols to ingest
        symbols = await self.get_symbols_for_ingestion(db, limit=50)
        
        if not symbols:
            logger.info("No symbols found for ingestion")
            return
        
        # Ingest data
        count = await self.ingest_stock_data(db, symbols, days_back=30)
        
        logger.info(f"Scheduled ingestion completed for {count} symbols")
        
        # Update model features
        await self.update_model_features(db, symbols)
    
    async def update_model_features(self, db: AsyncSession, symbols: List[str]):
        """Update features for ML model"""
        # This would typically involve calling the ML service
        # For now, we'll just log the update
        logger.info(f"Updating model features for {len(symbols)} symbols")
        
        # Placeholder for ML feature update logic
        pass

# Global instance
data_ingestion_service = DataIngestionService()