"""Logging bootstrap for ChairRorist."""
import logging
import os
import sys

from . import paths

_LOGGER_NAME = "chairrorist"
_logger = None


def get_logger() -> logging.Logger:
    """Return the shared application logger (without configuring handlers).

    Handlers are attached lazily by :func:`setup_logging` so that importing
    the package (e.g. from tests) has no file-system side effects.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(_LOGGER_NAME)
        _logger.addHandler(logging.NullHandler())
        _logger.propagate = False
    return _logger


def _log_file_path() -> str:
    if paths.is_frozen():
        return os.path.join(os.path.dirname(sys.executable), "chairrorist.log")
    return paths.resource_path("logs", "chairrorist.log")


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure console and file handlers and return the shared logger."""
    logger = get_logger()
    logger.setLevel(level)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        log_file = _log_file_path()
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError) as exc:
        logger.warning("Could not set up file logging: %s", exc)

    return logger
