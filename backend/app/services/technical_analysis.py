import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.core.logging import logger

try:
    import talib
    TA_LIB_AVAILABLE = True
except ImportError:
    TA_LIB_AVAILABLE = False
    logger.warning("TA-Lib not available. Using pandas-based implementations.")

class TechnicalAnalysisService:
    def __init__(self):
        self.indicators = {
            'sma': self._calculate_sma,
            'ema': self._calculate_ema,
            'rsi': self._calculate_rsi,
            'macd': self._calculate_macd,
            'bollinger': self._calculate_bollinger_bands,
            'atr': self._calculate_atr,
            'stochastic': self._calculate_stochastic,
            'williams_r': self._calculate_williams_r,
            'cci': self._calculate_cci,
            'obv': self._calculate_obv,
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a dataframe"""
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Simple Moving Averages
        df['sma_20'] = self._calculate_sma(df['close'], 20)
        df['sma_50'] = self._calculate_sma(df['close'], 50)
        df['sma_200'] = self._calculate_sma(df['close'], 200)
        
        # Exponential Moving Averages
        df['ema_12'] = self._calculate_ema(df['close'], 12)
        df['ema_26'] = self._calculate_ema(df['close'], 26)
        
        # RSI
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)
        
        # MACD
        macd_line, signal_line, histogram = self._calculate_macd(df['close'])
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram
        
        # Bollinger Bands
        upper, middle, lower = self._calculate_bollinger_bands(df['close'])
        df['bollinger_upper'] = upper
        df['bollinger_middle'] = middle
        df['bollinger_lower'] = lower
        
        # ATR
        df['atr_14'] = self._calculate_atr(df['high'], df['low'], df['close'], 14)
        
        # Stochastic Oscillator
        k, d = self._calculate_stochastic(df['high'], df['low'], df['close'])
        df['stochastic_k'] = k
        df['stochastic_d'] = d
        
        # Williams %R
        df['williams_r'] = self._calculate_williams_r(df['high'], df['low'], df['close'])
        
        # CCI
        df['cci'] = self._calculate_cci(df['high'], df['low'], df['close'])
        
        # OBV
        df['obv'] = self._calculate_obv(df['close'], df['volume'])
        
        # VWAP (if available)
        if 'vwap' in df.columns:
            df['vwap'] = df['vwap']
        else:
            df['vwap'] = self._calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
        
        # Volume indicators
        df['volume_sma_20'] = self._calculate_sma(df['volume'], 20)
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Price momentum
        df['price_change_1d'] = df['close'].pct_change(1) * 100
        df['price_change_5d'] = df['close'].pct_change(5) * 100
        df['price_change_20d'] = df['close'].pct_change(20) * 100
        df['price_change_60d'] = df['close'].pct_change(60) * 100
        
        # Volatility
        df['volatility_20d'] = df['close'].rolling(20).std() / df['close'].rolling(20).mean() * 100
        df['volatility_60d'] = df['close'].rolling(60).std() / df['close'].rolling(60).mean() * 100
        
        # Market regime detection
        df['market_regime'] = self._detect_market_regime(df)
        
        return df
    
    def _calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        if TA_LIB_AVAILABLE:
            return talib.SMA(series, timeperiod=period)
        else:
            return series.rolling(window=period).mean()
    
    def _calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        if TA_LIB_AVAILABLE:
            return talib.EMA(series, timeperiod=period)
        else:
            return series.ewm(span=period).mean()
    
    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        if TA_LIB_AVAILABLE:
            return talib.RSI(series, timeperiod=period)
        else:
            # Manual RSI calculation
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD (Moving Average Convergence Divergence)"""
        if TA_LIB_AVAILABLE:
            macd, signal_line, hist = talib.MACD(series, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return macd, signal_line, hist
        else:
            # Manual MACD calculation
            ema_fast = series.ewm(span=fast).mean()
            ema_slow = series.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            hist = macd - signal_line
            return macd, signal_line, hist
    
    def _calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: float = 2):
        """Bollinger Bands"""
        if TA_LIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(series, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
            return upper, middle, lower
        else:
            # Manual Bollinger Bands calculation
            middle = series.rolling(window=period).mean()
            std = series.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            return upper, middle, lower
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
        """Average True Range"""
        if TA_LIB_AVAILABLE:
            return talib.ATR(high, low, close, timeperiod=period)
        else:
            # Manual ATR calculation
            high_low = high - low
            high_close_prev = np.abs(high - close.shift(1))
            low_close_prev = np.abs(low - close.shift(1))
            true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
            return true_range.rolling(window=period).mean()
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                            k_period: int = 14, d_period: int = 3):
        """Stochastic Oscillator"""
        if TA_LIB_AVAILABLE:
            k, d = talib.STOCH(high, low, close, fastk_period=k_period, slowk_period=d_period)
            return k, d
        else:
            # Manual Stochastic calculation
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            d = k.rolling(window=d_period).mean()
            return k, d
    
    def _calculate_williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
        """Williams %R"""
        if TA_LIB_AVAILABLE:
            return talib.WILLR(high, low, close, timeperiod=period)
        else:
            # Manual Williams %R calculation
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
            return wr
    
    def _calculate_cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20):
        """Commodity Channel Index"""
        if TA_LIB_AVAILABLE:
            return talib.CCI(high, low, close, timeperiod=period)
        else:
            # Manual CCI calculation
            tp = (high + low + close) / 3
            sma_tp = tp.rolling(window=period).mean()
            mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
            cci = (tp - sma_tp) / (0.015 * mad)
            return cci
    
    def _calculate_obv(self, close: pd.Series, volume: pd.Series):
        """On-Balance Volume"""
        if TA_LIB_AVAILABLE:
            return talib.OBV(close, volume)
        else:
            # Manual OBV calculation
            obv = volume.copy()
            obv.iloc[0] = 0
            for i in range(1, len(obv)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            return obv
    
    def _calculate_vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series):
        """Volume Weighted Average Price"""
        tp = (high + low + close) / 3
        return (tp * volume).cumsum() / volume.cumsum()
    
    def _detect_market_regime(self, df: pd.DataFrame, period: int = 50) -> pd.Series:
        """Detect market regime based on price trend"""
        sma = self._calculate_sma(df['close'], period)
        current_price = df['close']
        
        # Calculate distance from SMA
        distance = ((current_price - sma) / sma * 100).rolling(20).mean()
        
        # Classify regime
        regime = pd.Series(index=df.index, dtype='object')
        regime[distance > 2] = 'bull'
        regime[distance < -2] = 'bear'
        regime[(-2 <= distance) & (distance <= 2)] = 'sideways'
        regime = regime.fillna('sideways')
        
        return regime
    
    def get_feature_importance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate feature importance for ML model"""
        # This would typically use SHAP or similar
        # For now, return mock importance scores
        features = [
            'rsi_14', 'macd', 'bollinger_position', 'atr_14',
            'stochastic_k', 'volume_ratio', 'price_change_20d',
            'volatility_20d', 'market_regime'
        ]
        
        # Mock importance scores (would be calculated by SHAP in real implementation)
        importance = {
            'rsi_14': 0.15,
            'macd': 0.12,
            'bollinger_position': 0.10,
            'atr_14': 0.08,
            'stochastic_k': 0.07,
            'volume_ratio': 0.09,
            'price_change_20d': 0.11,
            'volatility_20d': 0.06,
            'market_regime': 0.08,
        }
        
        return importance

# Global instance
technical_analysis_service = TechnicalAnalysisService()