import functools
import threading
import time


CACHE_SECONDS = 14_400 # 4 hours

def time_limited_cache(max_age_seconds):
    def decorator(func):
        cache = {}
        locks = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            # Check if the cached value exists and is not expired
            if key in cache:
                value, timestamp = cache[key]
                if time.time() - timestamp < max_age_seconds:
                    return value
            # If a lock does not exist for the key, create one
            if key not in locks:
                locks[key] = threading.Lock()
            # Use the lock to ensure only one thread recomputes the value
            with locks[key]:
                # Check the cache again to avoid recomputing if another thread already did it
                if key in cache:
                    value, timestamp = cache[key]
                    if time.time() - timestamp < max_age_seconds:
                        return value
                # Compute and cache the new value
                value = func(*args, **kwargs)
                cache[key] = (value, time.time())
                return value
        return wrapper
    return decorator