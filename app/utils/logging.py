"""Centralized logging configuration and utilities."""

import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
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


class ConversationLogger:
    """Logger for recording conversation exchanges."""
    
    def __init__(
        self,
        log_file: str = "conversations.log",
        log_dir: str = "logs"
    ):
        """
        Initialize conversation logger.
        
        Args:
            log_file: Conversation log file name
            log_dir: Directory for log files
        """
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        self.log_file = log_path / log_file
    
    def log_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Log a conversation exchange (user message + assistant response).
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata (e.g., query understanding, token count)
        """
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user": user_message,
            "assistant": assistant_response
        }
        
        if metadata:
            exchange["metadata"] = metadata
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                # Pretty-print JSON with indentation for readability; add an extra newline between records
                f.write(json.dumps(exchange, ensure_ascii=False, indent=2) + "\n\n")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log conversation exchange: {e}")
    
    def log_user_message(self, session_id: str, user_message: str) -> None:
        """
        Log only a user message (useful for intermediate logging).
        
        Args:
            session_id: Session identifier
            user_message: User's message
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "type": "user",
            "message": user_message
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n\n")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log user message: {e}")
    
    def log_assistant_response(self, session_id: str, response: str) -> None:
        """
        Log only an assistant response.
        
        Args:
            session_id: Session identifier
            response: Assistant's response
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "type": "assistant",
            "message": response
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, indent=2) + "\n\n")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log assistant response: {e}")


class UserQueryLogger:
    """Logger for recording user queries with understanding details."""
    
    def __init__(
        self,
        log_file: str = "user_queries.log",
        log_dir: str = "logs"
    ):
        """
        Initialize user query logger.
        
        Args:
            log_file: User queries log file name
            log_dir: Directory for log files
        """
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        self.log_file = log_path / log_file
    
    def log_query(
        self,
        session_id: str,
        original_query: str,
        is_ambiguous: bool,
        rewritten_query: Optional[str] = None,
        needed_context_from_memory: Optional[list] = None,
        clarifying_questions: Optional[list] = None,
        final_augmented_context: Optional[str] = None
    ) -> None:
        """
        Log a user query with query understanding details.
        
        Args:
            session_id: Session identifier
            original_query: Original user query
            is_ambiguous: Whether query was detected as ambiguous
            rewritten_query: Rewritten/paraphrased query (if ambiguous)
            needed_context_from_memory: List of memory fields used
            clarifying_questions: List of clarifying questions (if still unclear)
            final_augmented_context: Final context used for response
        """
        query_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "original_query": original_query,
            "is_ambiguous": is_ambiguous,
            "rewritten_query": rewritten_query,
            "needed_context_from_memory": needed_context_from_memory or [],
            "clarifying_questions": clarifying_questions or [],
            "final_augmented_context": final_augmented_context
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(query_record, ensure_ascii=False, indent=2) + "\n\n")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log user query: {e}")


class SessionSummaryLogger:
    """Logger for recording session summaries."""
    
    def __init__(
        self,
        log_file: str = "session_summaries.log",
        log_dir: str = "logs"
    ):
        """
        Initialize session summary logger.
        
        Args:
            log_file: Session summaries log file name
            log_dir: Directory for log files
        """
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        self.log_file = log_path / log_file
    
    def log_summary(
        self,
        session_id: str,
        session_summary: dict,
        message_range_summarized: dict
    ) -> None:
        """
        Log a session summary with structured information.
        
        Args:
            session_id: Session identifier
            session_summary: Dictionary containing:
                - user_profile: dict with 'prefs' and 'constraints'
                - key_facts: list of important facts
                - decisions: list of decisions made
                - open_questions: list of unresolved questions
                - todos: list of action items
            message_range_summarized: dict with 'from' and 'to' indices
        """
        summary_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "session_summary": {
                "user_profile": {
                    "prefs": session_summary.get("user_profile", {}).get("prefs", []),
                    "constraints": session_summary.get("user_profile", {}).get("constraints", [])
                },
                "key_facts": session_summary.get("key_facts", []),
                "decisions": session_summary.get("decisions", []),
                "open_questions": session_summary.get("open_questions", []),
                "todos": session_summary.get("todos", [])
            },
            "message_range_summarized": {
                "from": message_range_summarized.get("from", 0),
                "to": message_range_summarized.get("to", 0)
            }
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary_record, ensure_ascii=False, indent=2) + "\n\n")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log session summary: {e}")


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
