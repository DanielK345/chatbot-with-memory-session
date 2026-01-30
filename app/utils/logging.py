"""Centralized logging configuration and utilities."""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name (defaults to 'app.log')
        log_dir: Directory for log files
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        format_string: Custom format string (optional)
        
    Returns:
        Configured root logger
    """
    # Convert string level to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Full path to log file
        full_log_path = log_path / log_file
        
        # Rotating file handler
        file_handler = RotatingFileHandler(
            full_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def configure_logging_from_env() -> logging.Logger:
    """
    Configure logging from environment variables.
    
    Environment variables:
        LOG_LEVEL: Logging level (default: INFO)
        LOG_FILE: Log file name (default: app.log)
        LOG_DIR: Log directory (default: logs)
        LOG_MAX_BYTES: Max log file size (default: 10485760 = 10MB)
        LOG_BACKUP_COUNT: Number of backup files (default: 5)
        
    Returns:
        Configured root logger
    """
    level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "app.log")
    log_dir = os.getenv("LOG_DIR", "logs")
    
    try:
        max_bytes = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    except ValueError:
        max_bytes = 10 * 1024 * 1024
    
    try:
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    except ValueError:
        backup_count = 5
    
    return setup_logging(
        level=level,
        log_file=log_file,
        log_dir=log_dir,
        max_bytes=max_bytes,
        backup_count=backup_count
    )


class LoggerMixin:
    """Mixin class to add logger to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__name__)


# Initialize logging on module import (can be overridden)
# This ensures logging is set up even if setup_logging() is not called explicitly
_initialized = False


def initialize_logging():
    """Initialize logging with default configuration."""
    global _initialized
    if not _initialized:
        # Check if logging is already configured
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            # Use environment variables if available, otherwise defaults
            configure_logging_from_env()
        _initialized = True


# Auto-initialize on import
initialize_logging()
