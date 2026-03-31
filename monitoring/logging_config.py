"""Structured JSON logging configuration."""
import logging
import sys
from pythonjsonlogger import jsonlogger


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger to emit structured JSON.

    Returns the configured root logger so callers can use it directly:

        from monitoring.logging_config import logger
        logger.info("event", extra={"key": "value"})
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Replace any existing handlers so we don't double-log
    root.handlers = []

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    return root


# Module-level logger — import this wherever you need structured logging
logger = setup_logging()
