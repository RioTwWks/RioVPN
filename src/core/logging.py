"""Logging configuration."""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    log_format_str: Optional[str] = None,
    backup_count: int = 30,
) -> None:
    """
    Setup application logging with console and file handlers.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        log_format_str: Custom log format string (optional)
        backup_count: Number of days of log files to keep (default: 30)
    """
    # Default log format
    if log_format_str is None:
        log_format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    log_format = logging.Formatter(log_format_str, datefmt="%Y-%m-%d %H:%M:%S")

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)

    # File handler with daily rotation (if log_dir is specified)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        log_file = log_path / "riovpn.log"

        # TimedRotatingFileHandler - rotates at midnight
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="D",  # Rotate daily
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(getattr(logging, level.upper()))
        # Filename with date: riovpn.log.2026-03-24
        file_handler.namer = lambda name: name.replace(".log", "") + ".log."
        root_logger.addHandler(file_handler)

    # Set third-party loggers to WARNING
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance by name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
