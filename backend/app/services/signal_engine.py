import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.core.config import settings
from app.core.logging import logger
from app.models.stock import StockFeature, StockPrice
from app.models.signal import Signal, SignalAction, SignalConfidence
from app.services.technical_analysis import technical_analysis_service
from app.services.model_service import model_service

class SignalEngine:
    def __init__(self):
        self.min_confidence_threshold = 0.65
        self.max_signals_per_day = 50
        self.signal_validity_hours = 24
        
    async def generate_signals(self, db: AsyncSession, symbols: List[str] = None) -> List[Signal]:
        """Generate trading signals for given symbols"""
        
        if not symbols:
            symbols = await self._get_active_symbols(db)
        
        signals = []
        generated_count = 0
        
        for symbol in symbols:
            try:
                # Get latest features for the symbol
                features = await self._get_latest_features(db, symbol)
                
                if not features:
                    logger.warning(f"No features found for {symbol}")
                    continue
                
                # Generate signal using ML model
                signal_data = await self._generate_signal_for_symbol(db, symbol, features)
                
                if signal_data and signal_data['confidence'] >= self.min_confidence_threshold:
                    # Create signal record
                    signal = await self._create_signal(db, symbol, signal_data, features)
                    signals.append(signal)
                    generated_count += 1
                    
                    if generated_count >= self.max_signals_per_day:
                        break
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        logger.info(f"Generated {len(signals)} signals for {len(symbols)} symbols")
        return signals
    
    async def _get_active_symbols(self, db: AsyncSession) -> List[str]:
        """Get list of active symbols for signal generation"""
        # Get symbols with recent data
        cutoff_date = datetime.utcnow().date() - timedelta(days=7)
        
        result = await db.execute(
            select(StockFeature.symbol)
            .where(StockFeature.date >= cutoff_date)
            .distinct()
            .limit(200)  # Limit to prevent overload
        )
        
        return result.scalars().all()
    
    async def _get_latest_features(self, db: AsyncSession, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest technical features for a symbol"""
        
        result = await db.execute(
            select(StockFeature)
            .where(StockFeature.symbol == symbol)
            .order_by(desc(StockFeature.date))
            .limit(1)
        )
        
        feature = result.scalar_one_or_none()
        
        if not feature:
            return None
        
        # Convert to dictionary
        return {
            'symbol': feature.symbol,
            'date': feature.date,
            'sma_20': feature.sma_20,
            'sma_50': feature.sma_50,
            'sma_200': feature.sma_200,
            'ema_12': feature.ema_12,
            'ema_26': feature.ema_26,
            'rsi_14': feature.rsi_14,
            'macd': feature.macd,
            'macd_signal': feature.macd_signal,
            'macd_histogram': feature.macd_histogram,
            'bollinger_upper': feature.bollinger_upper,
            'bollinger_middle': feature.bollinger_middle,
            'bollinger_lower': feature.bollinger_lower,
            'atr_14': feature.atr_14,
            'stochastic_k': feature.stochastic_k,
            'stochastic_d': feature.stochastic_d,
            'williams_r': feature.williams_r,
            'cci': feature.cci,
            'obv': feature.obv,
            'vwap': feature.vwap,
            'volume_ratio': feature.volume_ratio,
            'price_change_20d': feature.price_change_20d,
            'volatility_20d': feature.volatility_20d,
            'market_regime': feature.market_regime,
            'sector_momentum': feature.sector_momentum,
            'relative_strength': feature.relative_strength
        }
    
    async def _generate_signal_for_symbol(self, db: AsyncSession, symbol: str, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal for a single symbol"""
        
        try:
            # Get recent price data for context
            price_data = await self._get_recent_price_data(db, symbol, days=60)
            
            if price_data.empty:
                return None
            
            # Prepare features for ML model
            ml_features = self._prepare_ml_features(features, price_data)
            
            # Get prediction from ML model
            prediction = await model_service.predict(ml_features)
            
            if not prediction:
                return None
            
            # Determine signal action and confidence
            action = self._determine_action(prediction)
            confidence = float(prediction.get('confidence', 0.0))
            
            if confidence < self.min_confidence_threshold:
                return None
            
            # Calculate price levels
            current_price = price_data['close'].iloc[-1]
            target_price, stop_loss = self._calculate_price_levels(
                action, current_price, features
            )
            
            # Generate rationale
            rationale = await self._generate_rationale(
                symbol, action, features, prediction
            )
            
            # Calculate risk metrics
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                current_price, target_price, stop_loss
            )
            
            expected_return = self._calculate_expected_return(
                action, current_price, target_price
            )
            
            return {
                'action': action,
                'confidence': confidence,
                'current_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'rationale': rationale,
                'risk_reward_ratio': risk_reward_ratio,
                'expected_return': expected_return,
                'prediction_data': prediction
            }
        
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    async def _get_recent_price_data(self, db: AsyncSession, symbol: str, days: int = 60) -> pd.DataFrame:
        """Get recent price data for a symbol"""
        
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
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
        
        if not prices:
            return pd.DataFrame()
        
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
        
        return df
    
    def _prepare_ml_features(self, features: Dict[str, Any], price_data: pd.DataFrame) -> Dict[str, float]:
        """Prepare features for ML model"""
        
        ml_features = {}
        
        # Technical indicators
        numeric_features = [
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'atr_14', 'stochastic_k', 'stochastic_d', 'williams_r',
            'cci', 'volume_ratio', 'price_change_20d', 'volatility_20d'
        ]
        
        for feature in numeric_features:
            if features.get(feature) is not None:
                ml_features[feature] = float(features[feature])
        
        # Price-based features
        current_price = price_data['close'].iloc[-1]
        sma_20 = features.get('sma_20', current_price)
        sma_50 = features.get('sma_50', current_price)
        
        ml_features['price_vs_sma20'] = (current_price - sma_20) / sma_20
        ml_features['price_vs_sma50'] = (current_price - sma_50) / sma_50
        ml_features['sma20_vs_sma50'] = (sma_20 - sma_50) / sma_50
        
        # Market regime encoding
        regime_mapping = {'bull': 1, 'bear': -1, 'sideways': 0}
        ml_features['market_regime'] = regime_mapping.get(features.get('market_regime', 'sideways'), 0)
        
        # Recent price momentum
        if len(price_data) >= 5:
            ml_features['momentum_5d'] = (current_price - price_data['close'].iloc[-5]) / price_data['close'].iloc[-5]
        
        if len(price_data) >= 20:
            ml_features['momentum_20d'] = (current_price - price_data['close'].iloc[-20]) / price_data['close'].iloc[-20]
        
        return ml_features
    
    def _determine_action(self, prediction: Dict[str, Any]) -> SignalAction:
        """Determine signal action based on prediction"""
        
        signal_strength = prediction.get('signal_strength', 0.0)
        
        if signal_strength > 0.6:
            return SignalAction.BUY
        elif signal_strength < -0.6:
            return SignalAction.SELL
        else:
            return SignalAction.HOLD
    
    def _calculate_price_levels(self, action: SignalAction, current_price: float, features: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate target price and stop loss levels"""
        
        atr = features.get('atr_14', current_price * 0.02)  # Default 2% ATR
        
        if action == SignalAction.BUY:
            # Target: 2x ATR above current price
            target_price = current_price + (2 * atr)
            # Stop: 1x ATR below current price
            stop_loss = current_price - (1 * atr)
        elif action == SignalAction.SELL:
            # Target: 2x ATR below current price
            target_price = current_price - (2 * atr)
            # Stop: 1x ATR above current price
            stop_loss = current_price + (1 * atr)
        else:
            target_price = current_price
            stop_loss = current_price
        
        return round(target_price, 2), round(stop_loss, 2)
    
    async def _generate_rationale(self, symbol: str, action: SignalAction, features: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """Generate signal rationale"""
        
        rationale_parts = []
        
        # Market regime
        regime = features.get('market_regime', 'sideways')
        if regime == 'bull':
            rationale_parts.append("Bull market conditions favor long positions")
        elif regime == 'bear':
            rationale_parts.append("Bear market conditions favor defensive positioning")
        
        # Technical indicators
        rsi = features.get('rsi_14')
        if rsi:
            if rsi < 30:
                rationale_parts.append("RSI indicates oversold conditions")
            elif rsi > 70:
                rationale_parts.append("RSI indicates overbought conditions")
            else:
                rationale_parts.append(f"RSI at {rsi:.1f} shows neutral momentum")
        
        # Volume
        volume_ratio = features.get('volume_ratio')
        if volume_ratio:
            if volume_ratio > 1.5:
                rationale_parts.append("Above-average volume confirms price movement")
            elif volume_ratio < 0.7:
                rationale_parts.append("Below-average volume suggests weak momentum")
        
        # Combine rationale
        if rationale_parts:
            return "; ".join(rationale_parts)
        else:
            return f"ML model generated {action.value} signal with high confidence"
    
    def _calculate_risk_reward_ratio(self, current_price: float, target_price: float, stop_loss: float) -> float:
        """Calculate risk-reward ratio"""
        
        potential_reward = abs(target_price - current_price)
        potential_risk = abs(current_price - stop_loss)
        
        if potential_risk == 0:
            return 0.0
        
        return round(potential_reward / potential_risk, 2)
    
    def _calculate_expected_return(self, action: SignalAction, current_price: float, target_price: float) -> float:
        """Calculate expected return percentage"""
        
        if action == SignalAction.HOLD:
            return 0.0
        
        expected_return = (target_price - current_price) / current_price * 100
        return round(expected_return, 2)
    
    async def _create_signal(self, db: AsyncSession, symbol: str, signal_data: Dict[str, Any], features: Dict[str, Any]) -> Signal:
        """Create signal record in database"""
        
        # Determine confidence level
        confidence = signal_data['confidence']
        if confidence >= 0.85:
            confidence_level = SignalConfidence.HIGH
        elif confidence >= 0.75:
            confidence_level = SignalConfidence.MEDIUM
        else:
            confidence_level = SignalConfidence.LOW
        
        # Create signal
        signal = Signal(
            symbol=symbol,
            action=signal_data['action'],
            confidence=confidence,
            confidence_level=confidence_level,
            entry_price=signal_data['current_price'],
            target_price=signal_data['target_price'],
            stop_loss=signal_data['stop_loss'],
            model_version=settings.MODEL_VERSION,
            model_confidence=confidence,
            rationale=signal_data['rationale'],
            risk_reward_ratio=signal_data['risk_reward_ratio'],
            expected_return=signal_data['expected_return'],
            valid_until=datetime.utcnow() + timedelta(hours=self.signal_validity_hours)
        )
        
        db.add(signal)
        await db.commit()
        await db.refresh(signal)
        
        return signal
    
    async def evaluate_signal_performance(self, db: AsyncSession, signal_id: int) -> Dict[str, Any]:
        """Evaluate the performance of a signal"""
        
        signal = await db.get(Signal, signal_id)
        
        if not signal:
            return None
        
        # Get price data since signal generation
        price_data = await self._get_price_data_since_signal(db, signal)
        
        if price_data.empty:
            return None
        
        # Calculate performance metrics
        performance = self._calculate_signal_performance(signal, price_data)
        
        # Update signal with performance data
        signal.actual_return = performance.get('actual_return')
        signal.max_drawdown = performance.get('max_drawdown')
        signal.holding_period = performance.get('holding_period')
        
        await db.commit()
        
        return performance
    
    async def _get_price_data_since_signal(self, db: AsyncSession, signal: Signal) -> pd.DataFrame:
        """Get price data since signal was generated"""
        
        result = await db.execute(
            select(StockPrice)
            .where(
                and_(
                    StockPrice.symbol == signal.symbol,
                    StockPrice.date >= signal.generated_at.date()
                )
            )
            .order_by(StockPrice.date)
        )
        
        prices = result.scalars().all()
        
        if not prices:
            return pd.DataFrame()
        
        df = pd.DataFrame([
            {
                'date': p.date,
                'close': p.close,
                'high': p.high,
                'low': p.low
            }
            for p in prices
        ])
        
        return df
    
    def _calculate_signal_performance(self, signal: Signal, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate signal performance metrics"""
        
        if price_data.empty:
            return {}
        
        entry_price = signal.entry_price
        current_price = price_data['close'].iloc[-1]
        
        # Calculate return
        if signal.action == SignalAction.BUY:
            actual_return = (current_price - entry_price) / entry_price * 100
        elif signal.action == SignalAction.SELL:
            actual_return = (entry_price - current_price) / entry_price * 100
        else:
            actual_return = 0.0
        
        # Calculate max drawdown
        if signal.action == SignalAction.BUY:
            running_max = price_data['close'].expanding().max()
            drawdown = (price_data['close'] - running_max) / running_max * 100
        else:
            running_min = price_data['close'].expanding().min()
            drawdown = (running_min - price_data['close']) / price_data['close'].iloc[0] * 100
        
        max_drawdown = drawdown.min()
        
        # Calculate holding period
        holding_period = len(price_data)
        
        return {
            'actual_return': round(actual_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'holding_period': holding_period,
            'is_profitable': actual_return > 0,
            'hit_target': self._check_target_hit(signal, price_data),
            'hit_stop_loss': self._check_stop_loss_hit(signal, price_data)
        }
    
    def _check_target_hit(self, signal: Signal, price_data: pd.DataFrame) -> bool:
        """Check if target price was hit"""
        if signal.action == SignalAction.BUY:
            return (price_data['high'] >= signal.target_price).any()
        elif signal.action == SignalAction.SELL:
            return (price_data['low'] <= signal.target_price).any()
        return False
    
    def _check_stop_loss_hit(self, signal: Signal, price_data: pd.DataFrame) -> bool:
        """Check if stop loss was hit"""
        if signal.action == SignalAction.BUY:
            return (price_data['low'] <= signal.stop_loss).any()
        elif signal.action == SignalAction.SELL:
            return (price_data['high'] >= signal.stop_loss).any()
        return False

# Global instance
signal_engine = SignalEngine()