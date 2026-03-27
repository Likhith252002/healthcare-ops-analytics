import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from unittest.mock import patch
from src.utils.retry import retry_with_backoff, safe_execute


class TestRetry(unittest.TestCase):
    """Test retry utilities"""

    def test_retry_succeeds_first_attempt(self):
        """Test function succeeds on first attempt"""
        @retry_with_backoff(max_attempts=3)
        def successful_function():
            return "success"

        result = successful_function()
        self.assertEqual(result, "success")

    def test_retry_succeeds_after_failures(self):
        """Test function succeeds after initial failures"""
        call_count = {'count': 0}

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky_function():
            call_count['count'] += 1
            if call_count['count'] < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count['count'], 3)

    def test_retry_fails_after_max_attempts(self):
        """Test function raises after max attempts"""
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always_fails():
            raise ValueError("Persistent error")

        with self.assertRaises(ValueError):
            always_fails()

    def test_retry_only_catches_specified_exceptions(self):
        """Test retry only catches specified exception types"""
        call_count = {'count': 0}

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            exceptions=(TypeError,)
        )
        def raises_value_error():
            call_count['count'] += 1
            raise ValueError("Wrong exception type")

        with self.assertRaises(ValueError):
            raises_value_error()

        # Should fail immediately without retrying
        self.assertEqual(call_count['count'], 1)

    def test_retry_exponential_backoff_capped(self):
        """Test that delay is capped at max_delay"""
        delays = []

        original_sleep = __import__('time').sleep

        with patch('time.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda d: delays.append(d)

            @retry_with_backoff(max_attempts=5, base_delay=10.0, max_delay=15.0)
            def always_fails():
                raise ValueError("error")

            with self.assertRaises(ValueError):
                always_fails()

        # All recorded delays should be at most max_delay
        for d in delays:
            self.assertLessEqual(d, 15.0)

    def test_safe_execute_success(self):
        """Test safe_execute returns result on success"""
        def successful_function(x, y):
            return x + y

        result = safe_execute(successful_function, 2, 3, default=0)
        self.assertEqual(result, 5)

    def test_safe_execute_failure_returns_default(self):
        """Test safe_execute returns default on error"""
        def failing_function():
            raise ValueError("Error")

        result = safe_execute(failing_function, default="fallback")
        self.assertEqual(result, "fallback")

    def test_safe_execute_default_none(self):
        """Test safe_execute returns None when no default specified"""
        def failing_function():
            raise RuntimeError("Error")

        result = safe_execute(failing_function)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
