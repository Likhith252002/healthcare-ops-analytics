import time
from enum import Enum
from typing import Callable, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Prevent cascading failures by short-circuiting repeated failures."""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                logger.info("Circuit breaker: Attempting recovery (half-open)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Too many failures. "
                    f"Retry in {self.timeout - (time.time() - self.last_failure_time):.0f}s"
                )

        # Attempt to call function
        try:
            result = func(*args, **kwargs)

            # Success - reset if recovering
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: Recovery successful (closed)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.error(
                f"Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}"
            )

            if self.failure_count >= self.failure_threshold:
                logger.error("Circuit breaker: OPEN (too many failures)")
                self.state = CircuitState.OPEN

            raise

    def reset(self):
        """Manually reset circuit breaker"""
        logger.info("Circuit breaker: Manual reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
