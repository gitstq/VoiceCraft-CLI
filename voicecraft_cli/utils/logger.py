"""
Logging utility module.

Provides a centralized logging setup for VoiceCraft-CLI with
configurable log levels, output formats, and file logging support.
Uses only Python's built-in logging module.
"""

import logging
import sys
import os
from typing import Optional

# Global logger name prefix
LOGGER_PREFIX = "voicecraft_cli"

# Default log format
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
SIMPLE_FORMAT = "[%(levelname)s] %(message)s"

# Module-level cache of created loggers
_loggers: dict = {}


def setup_logging(level: str = "WARNING", log_file: Optional[str] = None,
                  simple: bool = False) -> logging.Logger:
    """Set up the root logger for VoiceCraft-CLI.

    Configures the root logger with handlers, formatters, and level.
    Should be called once at application startup.

    Args:
        level: Log level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        log_file: Optional path to a log file. If provided, a FileHandler
                  is added in addition to the console handler.
        simple: If True, use a simpler log format (no timestamps).

    Returns:
        The root VoiceCraft-CLI logger instance.
    """
    # Get or create the root logger
    root_logger = logging.getLogger(LOGGER_PREFIX)

    # Avoid adding duplicate handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Set log level
    log_level = getattr(logging, level.upper(), logging.WARNING)
    root_logger.setLevel(log_level)

    # Choose format
    fmt = SIMPLE_FORMAT if simple else DEFAULT_FORMAT
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_file = os.path.expanduser(log_file)
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance.

    Creates a child logger under the VoiceCraft-CLI root namespace.
    If the root logger has not been configured, it will be set up
    with default settings.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        A logging.Logger instance.
    """
    # Ensure the full logger name is under our namespace
    if not name.startswith(LOGGER_PREFIX):
        full_name = f"{LOGGER_PREFIX}.{name}"
    else:
        full_name = name

    logger = logging.getLogger(full_name)

    # Auto-configure root logger if no handlers exist
    root_logger = logging.getLogger(LOGGER_PREFIX)
    if not root_logger.handlers:
        setup_logging()

    return logger
