"""
Logging configuration for the trading bot.
Outputs to both console and bot.log file.
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "trading_bot", log_file: str = "bot.log") -> logging.Logger:
    """
    Set up and return a logger that writes to both console and a log file.

    Args:
        name: Logger name (default: 'trading_bot')
        log_file: Path to the log file (default: 'bot.log')

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Formatter: timestamp | level | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- File handler ---
    log_path = Path(log_file)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Module-level default logger
logger = setup_logger()
