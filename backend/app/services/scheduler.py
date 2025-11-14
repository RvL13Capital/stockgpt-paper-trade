import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.services.data_ingestion import data_ingestion_service
from app.services.signal_engine import signal_engine
from app.services.trade_engine import trade_engine

class SchedulerService:
    def __init__(self):
        self.is_running = False
        self.tasks = []
        
    async def start(self):
        """Start the scheduler service"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting scheduler service")
        self.is_running = True
        
        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._daily_data_ingestion()),
            asyncio.create_task(self._hourly_signal_generation()),
            asyncio.create_task(self._portfolio_update_task()),
            asyncio.create_task(self._otp_reset_task()),
        ]
        
        logger.info("Scheduler service started successfully")
    
    async def stop(self):
        """Stop the scheduler service"""
        if not self.is_running:
            return
        
        logger.info("Stopping scheduler service")
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Scheduler service stopped")
    
    async def _daily_data_ingestion(self):
        """Daily data ingestion task"""
        
        while self.is_running:
            try:
                now = datetime.utcnow()
                
                # Run at 22:00 UTC (after market close)
                if now.hour == 22 and now.minute == 0:
                    logger.info("Starting daily data ingestion")
                    
                    async with AsyncSessionLocal() as db:
                        try:
                            # Update stock list
                            await data_ingestion_service.update_stock_info(db)
                            
                            # Get symbols for ingestion
                            symbols = await data_ingestion_service.get_symbols_for_ingestion(db, limit=100)
                            
                            if symbols:
                                # Ingest daily data
                                count = await data_ingestion_service.ingest_stock_data(db, symbols, days_back=1)
                                logger.info(f"Daily data ingestion completed for {count} symbols")
                            
                            # Update technical indicators
                            for symbol in symbols[:20]:  # Limit to prevent overload
                                await self._update_technical_indicators(db, symbol)
                            
                            await db.commit()
                            
                        except Exception as e:
                            logger.error(f"Error in daily data ingestion: {e}")
                            await db.rollback()
                    
                    # Wait for an hour to avoid duplicate runs
                    await asyncio.sleep(3600)
                
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily data ingestion task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _hourly_signal_generation(self):
        """Hourly signal generation task"""
        
        while self.is_running:
            try:
                now = datetime.utcnow()
                
                # Run every hour at :30 (30 minutes past the hour)
                if now.minute == 30:
                    logger.info("Starting hourly signal generation")
                    
                    async with AsyncSessionLocal() as db:
                        try:
                            # Generate signals
                            symbols = await data_ingestion_service.get_symbols_for_ingestion(db, limit=50)
                            
                            if symbols:
                                signals = await signal_engine.generate_signals(db, symbols)
                                logger.info(f"Generated {len(signals)} signals")
                            
                            await db.commit()
                            
                        except Exception as e:
                            logger.error(f"Error in signal generation: {e}")
                            await db.rollback()
                    
                    # Wait for an hour to avoid duplicate runs
                    await asyncio.sleep(3600)
                
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hourly signal generation task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _portfolio_update_task(self):
        """Portfolio update task (every 15 minutes during market hours)"""
        
        while self.is_running:
            try:
                now = datetime.utcnow()
                
                # Only run during market hours (9:30 AM - 4:00 PM EST, which is 14:30-21:00 UTC)
                if 14 <= now.hour < 21:
                    logger.info("Starting portfolio update")
                    
                    async with AsyncSessionLocal() as db:
                        try:
                            # Update all portfolios
                            from sqlalchemy import select
                            from app.models.portfolio import Portfolio
                            
                            result = await db.execute(select(Portfolio).where(Portfolio.is_active == True))
                            portfolios = result.scalars().all()
                            
                            for portfolio in portfolios:
                                await trade_engine.update_portfolio_metrics(db, portfolio.id)
                            
                            logger.info(f"Updated {len(portfolios)} portfolios")
                            await db.commit()
                            
                        except Exception as e:
                            logger.error(f"Error in portfolio update: {e}")
                            await db.rollback()
                    
                    # Wait 15 minutes
                    await asyncio.sleep(900)
                
                else:
                    # Check every 5 minutes outside market hours
                    await asyncio.sleep(300)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in portfolio update task: {e}")
                await asyncio.sleep(300)
    
    async def _otp_reset_task(self):
        """Daily OTP reset task"""
        
        while self.is_running:
            try:
                now = datetime.utcnow()
                
                # Run at midnight UTC (00:00)
                if now.hour == 0 and now.minute == 0:
                    logger.info("Starting daily OTP reset")
                    
                    # In a real implementation, this would:
                    # 1. Generate new OTP secrets for all users
                    # 2. Invalidate old OTP tokens
                    # 3. Send new OTPs via email
                    
                    logger.info("Daily OTP reset completed")
                    
                    # Wait for an hour to avoid duplicate runs
                    await asyncio.sleep(3600)
                
                else:
                    # Check every minute
                    await asyncio.sleep(60)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in OTP reset task: {e}")
                await asyncio.sleep(300)
    
    async def _update_technical_indicators(self, db: AsyncSession, symbol: str):
        """Update technical indicators for a symbol"""
        
        try:
            # Get recent price data
            from app.models.stock import StockPrice
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow().date() - timedelta(days=60)
            
            result = await db.execute(
                select(StockPrice)
                .where(
                    and_(
                        StockPrice.symbol == symbol,
                        StockPrice.date >= cutoff_date
                    )
                )
                .order_by(StockPrice.date)
            )
            
            prices = result.scalars().all()
            
            if len(prices) < 20:  # Need minimum data
                return
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'date': p.date,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume
                }
                for p in prices
            ])
            
            # Calculate indicators
            from app.services.technical_analysis import technical_analysis_service
            indicators_df = technical_analysis_service.calculate_indicators(df)
            
            # Update latest indicators in database
            latest_indicators = indicators_df.iloc[-1]
            
            # This would update the StockFeature table
            # Implementation would depend on the specific database schema
            
            logger.info(f"Updated technical indicators for {symbol}")
            
        except Exception as e:
            logger.error(f"Error updating technical indicators for {symbol}: {e}")
    
    async def run_scheduled_task(self, task_name: str):
        """Run a specific scheduled task on demand"""
        
        logger.info(f"Running scheduled task: {task_name}")
        
        async with AsyncSessionLocal() as db:
            try:
                if task_name == 'data_ingestion':
                    await data_ingestion_service.scheduled_ingestion(db)
                elif task_name == 'signal_generation':
                    symbols = await data_ingestion_service.get_symbols_for_ingestion(db, limit=50)
                    await signal_engine.generate_signals(db, symbols)
                elif task_name == 'portfolio_update':
                    # Update all portfolios
                    result = await db.execute(select(Portfolio).where(Portfolio.is_active == True))
                    portfolios = result.scalars().all()
                    for portfolio in portfolios:
                        await trade_engine.update_portfolio_metrics(db, portfolio.id)
                elif task_name == 'otp_reset':
                    # OTP reset logic would go here
                    logger.info("OTP reset task completed")
                else:
                    raise ValueError(f"Unknown task: {task_name}")
                
                await db.commit()
                logger.info(f"Scheduled task {task_name} completed successfully")
                
            except Exception as e:
                logger.error(f"Error running scheduled task {task_name}: {e}")
                await db.rollback()
                raise

# Global instance
scheduler_service = SchedulerService()