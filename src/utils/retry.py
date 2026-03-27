import time
import functools
from typing import Callable, Any, Type, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    exponential: bool = True
):
    """
    Retry decorator with exponential backoff.

    Usage:
        @retry_with_backoff(max_attempts=5, base_delay=2.0)
        def flaky_function():
            # code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    if exponential:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.1f}s... Error: {str(e)}"
                    )

                    time.sleep(delay)
                    attempt += 1

        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default=None, **kwargs) -> Any:
    """
    Execute function and return default value on error.

    Usage:
        result = safe_execute(risky_function, arg1, arg2, default=0)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {str(e)}. Returning default: {default}")
        return default
