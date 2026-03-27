# Testing Guide

## Overview

Automated tests ensure code quality and catch regressions before deployment.

## Test Structure

```
tests/
├── test_validation.py     # Tests for input validation utilities
├── test_retry.py          # Tests for retry decorator and safe_execute
├── test_incremental.py    # Tests for incremental loading utilities
└── README.md              # This file
```

## Running Tests

### All Tests
```bash
# Run all tests
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Individual Test Files
```bash
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_retry.py -v
python -m pytest tests/test_incremental.py -v
```

### Specific Test
```bash
python -m pytest tests/test_validation.py::TestValidation::test_validate_date_range_valid -v
```

## Test Categories

### Unit Tests

Test individual functions in isolation.

**Characteristics:**
- Fast (milliseconds per test)
- No external dependencies
- Use mocks for database/network calls

**Example:**
```python
@patch('src.utils.incremental.get_connection')
def test_get_last_load_timestamp(self, mock_get_connection):
    # Mock database connection
    mock_conn = MagicMock()
    # Test logic
```

### Integration Tests

Test components working together with real database.

**Characteristics:**
- Slower (seconds per test)
- Use test database
- Verify end-to-end workflows

**Example:**
```python
def test_full_pipeline_integration(self):
    # Setup test database
    # Run full data generation
    # Verify results in database
```

## Continuous Integration

Tests run automatically on:
- Every push to main branch
- Every pull request

See `.github/workflows/ci.yml` for CI/CD configuration.

### CI Pipeline Steps

1. **Setup:** Install Python, PostgreSQL test database
2. **Install:** Install project dependencies
3. **Schema:** Create database tables
4. **Test:** Run all unit tests
5. **Quality:** Run data quality checks
6. **Lint:** Check code style

### Viewing CI Results

- GitHub Actions tab shows all workflow runs
- Green checkmark = all tests passed
- Red X = tests failed (see logs for details)

## Writing New Tests

### Test File Template
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from src.module_to_test import function_to_test

class TestModuleName(unittest.TestCase):
    """Test module_name functionality"""

    def setUp(self):
        """Run before each test"""
        pass

    def tearDown(self):
        """Run after each test"""
        pass

    def test_function_success_case(self):
        """Test successful execution"""
        result = function_to_test(valid_input)
        self.assertEqual(result, expected_output)

    def test_function_error_case(self):
        """Test error handling"""
        with self.assertRaises(ExpectedError):
            function_to_test(invalid_input)

if __name__ == '__main__':
    unittest.main()
```

### Best Practices

1. **One assertion per test:** Tests should be focused
2. **Descriptive names:** `test_validate_date_range_invalid_order` not `test1`
3. **Test both success and failure:** Happy path and error cases
4. **Use mocks for external systems:** Don't hit real APIs in tests
5. **Clean up:** Reset state after each test

## Test Coverage

### Measuring Coverage
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Goals

- **Utilities:** >80% coverage
- **Generators:** >60% coverage (data randomness makes 100% difficult)
- **Critical paths:** 100% coverage (SCD2, validation, retry)

## Mocking Database Connections
```python
from unittest.mock import patch, MagicMock

@patch('src.utils.incremental.get_connection')
def test_database_function(self, mock_get_connection):
    # Create mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Set return values
    mock_cursor.fetchone.return_value = (expected_value,)

    # Run test
    result = function_that_uses_database()

    # Verify
    self.assertEqual(result, expected_value)
    mock_cursor.execute.assert_called_once()
```

## Troubleshooting

### Tests fail locally but pass in CI

**Cause:** Environment differences
**Solution:** Check environment variables, Python version, dependency versions

### Mock not working

**Cause:** Mocking wrong import path
**Solution:** Mock where function is used, not where it's defined
```python
# If src/module_a.py has: from utils.db import get_connection
# Mock here:
@patch('src.module_a.get_connection')  # Correct

# Not here:
@patch('src.utils.db.get_connection')  # Wrong
```

### Database tests fail

**Cause:** Test database not setup
**Solution:** Run schema setup first: `python src/setup_database.py`
