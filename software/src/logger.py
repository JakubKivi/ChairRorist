"""Logging configuration for ChairRorist."""
import logging
import os
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up logging for the application.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('chairrorist')
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    try:
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
            log_file = os.path.join(base_path, "..", "logs", "chairrorist.log")
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            log_file = os.path.join(base_path, "..", "..", "logs", "chairrorist.log")

        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        logger.warning(f"Could not set up file logging: {e}")

    return logger


# Global logger instance
logger = setup_logging()