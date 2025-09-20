"""Common API service functions for the application."""

import logging
import time
from typing import Dict, Any, Optional, Callable, TypeVar, cast
from functools import wraps

from .errors import APIError, RateLimitError, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Type variables for function signatures
T = TypeVar('T')
R = TypeVar('R')


def retry_on_failure(
    max_retries: int = 3, 
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_errors: tuple = (RateLimitError, ServiceUnavailableError)
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for retrying API calls that fail with certain exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor by which to increase the delay after each retry
        retryable_errors: Tuple of exception types that should trigger a retry
        
    Returns:
        Decorated function that will retry on specified exceptions
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            last_exception = None
            delay = retry_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    last_exception = e
                    
                    # Check if we've hit the maximum retries
                    if attempt >= max_retries:
                        logger.warning(
                            f"Maximum retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # For rate limit errors, use the retry-after time if provided
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = e.retry_after
                    
                    # Log the retry
                    logger.info(
                        f"Retrying {func.__name__} in {delay:.2f}s after error: {str(e)}. "
                        f"Attempt {attempt + 1}/{max_retries}."
                    )
                    
                    # Wait before retrying
                    time.sleep(delay)
                    
                    # Increase delay for next retry with backoff
                    delay *= backoff_factor
            
            # This should never happen, but just in case
            if last_exception:
                raise last_exception
            
            # This is to make the type checker happy
            raise RuntimeError("Unexpected error in retry_on_failure")
            
        return wrapper
    
    return decorator


def memoize_with_expiry(ttl_seconds: int = 3600) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for caching API call results with expiration.
    
    Args:
        ttl_seconds: Time to live for cached values in seconds
        
    Returns:
        Decorated function that will cache results
    """
    cache: Dict[str, Any] = {}
    
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Create a cache key from the function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check if we have a cached value that's not expired
            current_time = time.time()
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cast(R, result)
                else:
                    logger.debug(f"Cache expired for {func.__name__}")
                    del cache[cache_key]
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            logger.debug(f"Cached result for {func.__name__}")
            return result
            
        return wrapper
    
    return decorator 