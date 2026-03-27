import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Any, List, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass


def validate_date_range(start_date: datetime, end_date: datetime) -> None:
    """Validate that end_date is after start_date"""
    if start_date >= end_date:
        raise ValidationError(
            f"Start date ({start_date}) must be before end date ({end_date})"
        )

    if start_date > datetime.now():
        raise ValidationError(
            f"Start date ({start_date}) cannot be in the future"
        )


def validate_positive_integer(value: int, name: str) -> None:
    """Validate that value is a positive integer"""
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}")


def validate_probability(value: float, name: str) -> None:
    """Validate that value is a valid probability (0-1)"""
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} must be a number, got {type(value).__name__}"
        )

    if not 0 <= value <= 1:
        raise ValidationError(
            f"{name} must be between 0 and 1, got {value}"
        )


def validate_required_fields(data: dict, required_fields: List[str]) -> None:
    """Validate that all required fields are present in data"""
    missing = [field for field in required_fields if field not in data or data[field] is None]

    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )
