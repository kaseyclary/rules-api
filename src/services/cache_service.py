from functools import wraps
from typing import Any, Callable, Dict
import asyncio
from datetime import datetime
import gc

class CacheManager:
    _caches: Dict[str, Dict[str, Any]] = {}
    _timestamps: Dict[str, Dict[str, datetime]] = {}
    _max_sizes: Dict[str, int] = {}

    @classmethod
    def init_cache(cls, cache_name: str, max_size: int = 1000):
        """Initialize a new cache with given name and max size"""
        cls._caches[cache_name] = {}
        cls._timestamps[cache_name] = {}
        cls._max_sizes[cache_name] = max_size

    @classmethod
    def clear_all(cls):
        """Clear all caches"""
        cls._caches.clear()
        cls._timestamps.clear()
        cls._max_sizes.clear()
        gc.collect()

def timed_cache(expire: int = 3600, cache_name: str = "default", max_size: int = 1000):
    """
    Enhanced cache decorator with memory management
    
    Args:
        expire (int): Cache expiration time in seconds
        cache_name (str): Name of the cache to use
        max_size (int): Maximum number of items in the cache
    """
    def decorator(func: Callable) -> Callable:
        # Initialize cache if it doesn't exist
        if cache_name not in CacheManager._caches:
            CacheManager.init_cache(cache_name, max_size)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = CacheManager._caches[cache_name]
            timestamps = CacheManager._timestamps[cache_name]
            
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            current_time = datetime.now()
            
            # Clean old entries if cache is too large
            if len(cache) > CacheManager._max_sizes[cache_name]:
                old_keys = [k for k, t in timestamps.items() 
                          if (current_time - t).total_seconds() > expire]
                for k in old_keys:
                    cache.pop(k, None)
                    timestamps.pop(k, None)
                gc.collect()
            
            # Check cache
            if cache_key in cache:
                if (current_time - timestamps[cache_key]).total_seconds() < expire:
                    return cache[cache_key]
                else:
                    cache.pop(cache_key, None)
                    timestamps.pop(cache_key, None)
            
            # Get fresh result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)
            
            # Cache result
            cache[cache_key] = result
            timestamps[cache_key] = current_time
            
            return result
            
        return async_wrapper
    return decorator 