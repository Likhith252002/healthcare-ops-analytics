# Error Handling & Resilience Guide

## Overview

Production-ready error handling ensures the pipeline can recover from transient failures and degrade gracefully when permanent failures occur.

## Retry Patterns

### Exponential Backoff

Retry failed operations with increasing delays between attempts.

**Use when:**
- Network calls might timeout
- Database connections might be temporarily unavailable
- External APIs might rate-limit

**Example:**
```python
from utils.retry import retry_with_backoff
import psycopg2

@retry_with_backoff(
    max_attempts=5,
    base_delay=2.0,
    exceptions=(psycopg2.OperationalError,)
)
def connect_to_database():
    return psycopg2.connect(...)
```

**Backoff schedule:**
- Attempt 1: Immediate
- Attempt 2: 2s delay
- Attempt 3: 4s delay
- Attempt 4: 8s delay
- Attempt 5: 16s delay

### Safe Execution with Defaults

Execute function and return default value on error.

**Use when:**
- Optional data enrichment
- Non-critical calculations
- Graceful degradation acceptable

**Example:**
```python
from utils.retry import safe_execute

# Returns 0 if function fails
avg_score = safe_execute(calculate_score, patient_id, default=0)
```

## Validation Patterns

### Input Validation

Validate data before processing to fail fast.

**Example:**
```python
from utils.validation import (
    validate_date_range,
    validate_positive_integer,
    validate_required_fields,
    ValidationError
)

try:
    validate_date_range(start_date, end_date)
    validate_positive_integer(num_patients, "num_patients")
    validate_required_fields(patient_data, ['first_name', 'last_name', 'dob'])
except ValidationError as e:
    logger.error(f"Validation failed: {str(e)}")
    return None
```

### Data Integrity Checks

Use data quality tests (see DATA_QUALITY.md) to validate output.

## Circuit Breaker Pattern

Prevent cascading failures when a dependency fails repeatedly.

### How It Works

**States:**
1. **CLOSED** (normal): Requests pass through
2. **OPEN** (failure): Requests blocked, fail fast
3. **HALF_OPEN** (testing): Trial request to check recovery

**Transitions:**
- CLOSED → OPEN: After N consecutive failures
- OPEN → HALF_OPEN: After timeout period
- HALF_OPEN → CLOSED: If trial succeeds
- HALF_OPEN → OPEN: If trial fails

**Example:**
```python
from utils.circuit_breaker import CircuitBreaker

db_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)

try:
    result = db_breaker.call(query_database, sql, params)
except Exception as e:
    logger.error(f"Database unavailable: {str(e)}")
    # Use cached data or return error to user
```

## Error Categories

### Transient Errors (Retry)

- Network timeouts
- Database connection pool exhausted
- Temporary API rate limits
- Lock contention

**Strategy:** Retry with exponential backoff

### Permanent Errors (Fail Fast)

- Invalid SQL syntax
- Permission denied
- Table doesn't exist
- Invalid data type

**Strategy:** Log error, raise immediately

### Validation Errors (User Input)

- Invalid date ranges
- Negative counts
- Missing required fields

**Strategy:** Return clear error message to user

## Logging Best Practices

### Log Levels
```python
logger.debug("Variable values for troubleshooting")
logger.info("Normal operation milestones")
logger.warning("Degraded performance or retry attempts")
logger.error("Operation failed but system continues")
logger.critical("System cannot continue")
```

### Structured Logging
```python
logger.info(
    "Patient record created",
    extra={
        'patient_id': patient_id,
        'record_version': version,
        'elapsed_time_ms': elapsed * 1000
    }
)
```

### Sensitive Data

**Never log:**
- Patient names
- Addresses
- Phone numbers
- Medical records

**Safe to log:**
- Patient IDs (anonymized UUIDs)
- Counts and aggregates
- Timestamps
- Error codes

## Production Deployment

### Health Checks
```python
def health_check():
    """Verify system health"""
    checks = {
        'database': check_database_connection(),
        'disk_space': check_disk_space(),
        'recent_errors': count_recent_errors()
    }

    all_healthy = all(checks.values())
    return {'status': 'healthy' if all_healthy else 'degraded', 'checks': checks}
```

### Alerting Thresholds

- **Warning:** >10% error rate
- **Critical:** >50% error rate or circuit breaker open
- **Page:** Database unavailable for >5 minutes

### Graceful Shutdown
```python
import signal
import sys

def signal_handler(sig, frame):
    logger.info("Shutdown signal received, finishing current batch...")
    # Complete current work
    conn.commit()
    conn.close()
    logger.info("Graceful shutdown complete")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```
