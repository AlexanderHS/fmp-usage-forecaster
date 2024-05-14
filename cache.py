import functools
import time


def time_limited_cache(max_age_seconds):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            # Check if the cached value exists and is not expired
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
