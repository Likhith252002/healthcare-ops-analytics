import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from datetime import datetime, timedelta
from src.utils.validation import (
    ValidationError,
    validate_date_range,
    validate_positive_integer,
    validate_probability,
    validate_required_fields
)


class TestValidation(unittest.TestCase):
    """Test validation utilities"""

    def test_validate_date_range_valid(self):
        """Test valid date range passes"""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 31)

        # Should not raise
        validate_date_range(start, end)

    def test_validate_date_range_invalid_order(self):
        """Test that end before start raises error"""
        start = datetime(2025, 1, 31)
        end = datetime(2025, 1, 1)

        with self.assertRaises(ValidationError):
            validate_date_range(start, end)

    def test_validate_date_range_future_start(self):
        """Test that future start date raises error"""
        start = datetime.now() + timedelta(days=1)
        end = datetime.now() + timedelta(days=2)

        with self.assertRaises(ValidationError):
            validate_date_range(start, end)

    def test_validate_positive_integer_valid(self):
        """Test valid positive integer passes"""
        validate_positive_integer(10, "count")

    def test_validate_positive_integer_zero(self):
        """Test zero raises error"""
        with self.assertRaises(ValidationError):
            validate_positive_integer(0, "count")

    def test_validate_positive_integer_negative(self):
        """Test negative raises error"""
        with self.assertRaises(ValidationError):
            validate_positive_integer(-5, "count")

    def test_validate_positive_integer_wrong_type(self):
        """Test non-integer raises error"""
        with self.assertRaises(ValidationError):
            validate_positive_integer("10", "count")

    def test_validate_probability_valid(self):
        """Test valid probability passes"""
        validate_probability(0.5, "rate")
        validate_probability(0.0, "rate")
        validate_probability(1.0, "rate")

    def test_validate_probability_out_of_range(self):
        """Test out-of-range probability raises error"""
        with self.assertRaises(ValidationError):
            validate_probability(1.5, "rate")

        with self.assertRaises(ValidationError):
            validate_probability(-0.1, "rate")

    def test_validate_required_fields_valid(self):
        """Test all required fields present passes"""
        data = {'name': 'John', 'age': 30, 'email': 'john@example.com'}
        validate_required_fields(data, ['name', 'age', 'email'])

    def test_validate_required_fields_missing(self):
        """Test missing required field raises error"""
        data = {'name': 'John', 'age': 30}

        with self.assertRaises(ValidationError) as context:
            validate_required_fields(data, ['name', 'age', 'email'])

        self.assertIn('email', str(context.exception))

    def test_validate_required_fields_null_value(self):
        """Test None value treated as missing"""
        data = {'name': 'John', 'age': None, 'email': 'john@example.com'}

        with self.assertRaises(ValidationError) as context:
            validate_required_fields(data, ['name', 'age', 'email'])

        self.assertIn('age', str(context.exception))


if __name__ == '__main__':
    unittest.main()
