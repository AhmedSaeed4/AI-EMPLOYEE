"""
Cloud Logger Utility

Provides logging functionality for cloud agents.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class CloudLogger:
    """
    Logger for cloud agent operations.

    Provides both file and console logging with
    appropriate formatting and log levels.
    """

    def __init__(
        self,
        name: str = "cloud_agent",
        log_dir: Optional[Path] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize the cloud logger.

        Args:
            name: Logger name
            log_dir: Directory for log files (defaults to vault/Logs)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Avoid duplicate handlers
        if self.logger.handlers:
            return

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log_dir provided)
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"cloud_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)


# Global logger instance
_global_logger: Optional[CloudLogger] = None


def get_logger(
    name: str = "cloud_agent",
    log_dir: Optional[Path] = None,
    log_level: str = "INFO"
) -> CloudLogger:
    """
    Get or create global logger instance.

    Args:
        name: Logger name
        log_dir: Directory for log files
        log_level: Logging level

    Returns:
        CloudLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = CloudLogger(name, log_dir, log_level)

    return _global_logger


def log_activity(
    activity_type: str,
    details: str,
    status: str = "success",
    metadata: Optional[dict] = None
) -> dict:
    """
    Log an activity event.

    Args:
        activity_type: Type of activity (e.g., "email_draft", "git_sync")
        details: Activity description
        status: Status (success, failed, partial)
        metadata: Optional additional metadata

    Returns:
        Dictionary with log entry data
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "activity_type": activity_type,
        "details": details,
        "status": status,
        "metadata": metadata or {}
    }

    logger = get_logger()
    if status == "success":
        logger.info(f"[{activity_type}] {details}")
    elif status == "failed":
        logger.error(f"[{activity_type}] {details}")
    else:
        logger.warning(f"[{activity_type}] {details}")

    return entry
