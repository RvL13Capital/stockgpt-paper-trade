from typing import Any, Optional, List, Dict
from datetime import timedelta
import json
import hashlib
from app.core.redis import get_redis
from app.core.config import settings

class CacheManager:
    """Advanced cache management with granular invalidation strategies."""
    
    def __init__(self):
        self.redis = get_redis()
        self.default_ttl = timedelta(minutes=15)
        
        # Cache key patterns for different data types
        self.key_patterns = {
            'portfolio': 'portfolio:{portfolio_id}',
            'portfolio_performance': 'portfolio:{portfolio_id}:performance',
            'portfolio_positions': 'portfolio:{portfolio_id}:positions',
            'user_portfolios': 'user:{user_id}:portfolios',
            'signal': 'signal:{symbol}:{strategy}',
            'signal_history': 'signal:history:{symbol}:{timeframe}',
            'market_data': 'market:{symbol}:{data_type}',
            'trade': 'trade:{trade_id}',
            'journal': 'journal:{trade_id}',
            'backtest': 'backtest:{backtest_id}',
            'user_session': 'session:{user_id}',
            'market_summary': 'market:summary:{date}',
        }
    
    def _generate_key(self, pattern: str, **kwargs) -> str:
        """Generate cache key from pattern and parameters."""
        return pattern.format(**kwargs)
    
    def _generate_tag_key(self, tag: str) -> str:
        """Generate cache tag key for invalidation."""
        return f"tag:{tag}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            if settings.DEBUG:
                print(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None, tags: Optional[List[str]] = None) -> bool:
        """Set value in cache with optional tags for invalidation."""
        try:
            # Set the main value
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            self.redis.setex(key, int(ttl.total_seconds()), serialized_value)
            
            # Add to tag sets for invalidation
            if tags:
                for tag in tags:
                    tag_key = self._generate_tag_key(tag)
                    self.redis.sadd(tag_key, key)
                    # Set tag expiration slightly longer than main key
                    self.redis.expire(tag_key, int((ttl + timedelta(minutes=5)).total_seconds()))
            
            return True
        except Exception as e:
            if settings.DEBUG:
                print(f"Cache set error for key {key}: {e}")
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag."""
        try:
            tag_key = self._generate_tag_key(tag)
            keys_to_invalidate = self.redis.smembers(tag_key)
            
            if keys_to_invalidate:
                # Delete all tagged keys
                deleted_count = self.redis.delete(*keys_to_invalidate)
                # Delete the tag set itself
                self.redis.delete(tag_key)
                return deleted_count
            return 0
        except Exception as e:
            if settings.DEBUG:
                print(f"Cache invalidation error for tag {tag}: {e}")
            return 0
    
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries by key pattern."""
        try:
            keys_to_invalidate = self.redis.keys(pattern)
            if keys_to_invalidate:
                return self.redis.delete(*keys_to_invalidate)
            return 0
        except Exception as e:
            if settings.DEBUG:
                print(f"Cache invalidation error for pattern {pattern}: {e}")
            return 0
    
    async def invalidate_portfolio_cache(self, portfolio_id: str) -> None:
        """Invalidate all cache related to a specific portfolio."""
        await self.invalidate_by_tag(f"portfolio:{portfolio_id}")
    
    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache related to a specific user."""
        await self.invalidate_by_tag(f"user:{user_id}")
    
    async def invalidate_symbol_cache(self, symbol: str) -> None:
        """Invalidate all cache related to a specific symbol."""
        await self.invalidate_by_tag(f"symbol:{symbol}")
    
    async def invalidate_market_cache(self) -> None:
        """Invalidate all market data cache."""
        await self.invalidate_by_pattern("market:*")
    
    # Portfolio cache methods
    async def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        key = self._generate_key(self.key_patterns['portfolio'], portfolio_id=portfolio_id)
        return await self.get(key)
    
    async def set_portfolio(self, portfolio_id: str, data: Dict, ttl: Optional[timedelta] = None) -> bool:
        key = self._generate_key(self.key_patterns['portfolio'], portfolio_id=portfolio_id)
        return await self.set(key, data, ttl, tags=[f"portfolio:{portfolio_id}"])
    
    # Performance cache methods
    async def get_portfolio_performance(self, portfolio_id: str) -> Optional[Dict]:
        key = self._generate_key(self.key_patterns['portfolio_performance'], portfolio_id=portfolio_id)
        return await self.get(key)
    
    async def set_portfolio_performance(self, portfolio_id: str, data: Dict, ttl: Optional[timedelta] = None) -> bool:
        key = self._generate_key(self.key_patterns['portfolio_performance'], portfolio_id=portfolio_id)
        return await self.set(key, data, ttl, tags=[f"portfolio:{portfolio_id}", "performance"])
    
    # Signal cache methods
    async def get_signal(self, symbol: str, strategy: str) -> Optional[Dict]:
        key = self._generate_key(self.key_patterns['signal'], symbol=symbol, strategy=strategy)
        return await self.get(key)
    
    async def set_signal(self, symbol: str, strategy: str, data: Dict, ttl: Optional[timedelta] = None) -> bool:
        key = self._generate_key(self.key_patterns['signal'], symbol=symbol, strategy=strategy)
        return await self.set(key, data, ttl, tags=[f"symbol:{symbol}", "signal", strategy])
    
    # Market data cache methods
    async def get_market_data(self, symbol: str, data_type: str) -> Optional[Dict]:
        key = self._generate_key(self.key_patterns['market_data'], symbol=symbol, data_type=data_type)
        return await self.get(key)
    
    async def set_market_data(self, symbol: str, data_type: str, data: Dict, ttl: Optional[timedelta] = None) -> bool:
        key = self._generate_key(self.key_patterns['market_data'], symbol=symbol, data_type=data_type)
        return await self.set(key, data, ttl, tags=[f"symbol:{symbol}", "market_data", data_type])

# Global cache manager instance
cache_manager = CacheManager()