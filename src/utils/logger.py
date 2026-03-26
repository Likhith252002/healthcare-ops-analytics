"""
Centralized logging configuration for the project.
"""
import logging
import sys
from pathlib import Path
from config.settings import LOGGING


def setup_logger(name):
    """
    Set up logger with both file and console handlers.

    Args:
        name (str): Logger name (typically __name__ from calling module)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING['log_level'])

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_path = Path(LOGGING['log_file'])
    log_path.parent.mkdir(exist_ok=True)

    # Create formatters
    formatter = logging.Formatter(LOGGING['log_format'])

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (DEBUG and above)
    file_handler = logging.FileHandler(LOGGING['log_file'])
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
