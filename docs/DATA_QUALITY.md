# Data Quality Framework

## Overview

Automated data quality tests ensure data integrity throughout the pipeline. Tests run after data generation and validate:
- Schema constraints (NOT NULL, data types)
- Referential integrity (foreign keys)
- Business rules (dates, ranges, logic)
- SCD2 consistency (temporal integrity)
- Data completeness

## Test Categories

### 1. NULL Checks
Ensure critical fields are never NULL:
- Patient names (first_name, last_name)
- Encounter dates (admission_date, discharge_date)

### 2. Referential Integrity
Verify foreign key relationships:
- All encounters reference valid patients
- All encounters reference valid departments
- All bed events reference valid encounters

### 3. Business Rules
Validate business logic:
- Discharge dates are after admission dates
- Bed numbers are within department capacity (1 to bed_capacity)
- Patient ages are reasonable (0-120 years)

### 4. SCD2 Integrity
Ensure temporal consistency:
- Only one current record per patient (is_current = TRUE)
- No gaps in patient history (valid_to of version N = valid_from of version N+1)
- Current records have valid_to in the future

### 5. Completeness Checks
Detect missing data patterns:
- All departments should have assigned physicians (WARNING level)

## Running Tests

### Standalone Execution
```bash
python src/run_data_quality.py
```

### As Part of Pipeline
Data quality checks run automatically during `python src/main.py`

### Exit Codes
- `0`: All tests passed (or only warnings)
- `1`: One or more ERROR-level tests failed

## Test Results

Example output:
```
================================================================================
DATA QUALITY REPORT
================================================================================
Timestamp: 2026-03-26T19:00:00
Total Tests: 12
Passed: 11
Failed: 1 (Errors: 0, Warnings: 1)
================================================================================

✓ PASSED TESTS (11):
  ✓ Patients have no NULL names
  ✓ Encounters have valid dates
  ✓ All encounters reference valid patients
  ✓ All encounters reference valid departments
  ✓ All bed events reference valid encounters
  ✓ Discharge dates after admission dates
  ✓ Bed numbers within capacity
  ✓ Patient ages are reasonable
  ✓ Only one current record per patient
  ✓ No gaps in patient history
  ✓ Current records have valid_to in future

✗ FAILED TESTS (1):
  ⚠️  All departments have physicians
     Severity:    WARNING
     Description: Each department should have at least one physician assigned
     Violations:  1
     Sample failures: [(6,)]

================================================================================
⚠️  DATA QUALITY CHECK PASSED WITH WARNINGS
```

## Adding New Tests

Add tests in `src/utils/data_quality.py`:
```python
def define_tests():
    tests = [
        # Existing tests...

        # New test
        DataQualityTest(
            name="Your test name",
            query="SELECT key FROM table WHERE condition_that_indicates_failure",
            severity='error',  # or 'warning'
            description="What this test validates"
        ),
    ]
    return tests
```

## Best Practices

1. **Write tests that return violations**: Query should return rows only when test fails
2. **Use clear names**: Test names should describe what they validate
3. **Set appropriate severity**:
   - `error`: Data integrity issue, pipeline should fail
   - `warning`: Data quality concern, but not blocking
4. **Include descriptions**: Help future developers understand intent
5. **Sample failures**: Show first 5 violations for debugging

## Integration with CI/CD

In production pipelines:
```bash
# Run data generation
python src/main.py

# Explicit quality gate (if not part of main)
python src/run_data_quality.py || exit 1

# Continue with downstream processes...
```
