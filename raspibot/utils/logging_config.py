"""Simple logging configuration for the Raspibot project.

This module provides a clean, effective logging setup with correlation IDs
and custom formatting without complex abstractions.
"""

import logging
import os
import contextvars
from typing import Optional, Tuple

# Context variables for correlation tracking
_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('correlation_id', default=None)
_task_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('task_name', default=None)


class RaspibotFormatter(logging.Formatter):
    """Custom formatter for clean, readable log output."""
    
    def format(self, record):
        # Get correlation info
        correlation_id = _correlation_id.get()
        task_name = _task_name.get()
        
        # Format correlation part
        if correlation_id and task_name:
            correlation_part = f" [{correlation_id}:{task_name}]"
        else:
            correlation_part = " [:]"
        
        # Get class and function info
        class_name = record.name.split('.')[-1] if '.' in record.name else record.name
        function_name = record.funcName or "unknown"
        line_number = record.lineno or 0
        
        # Format the message
        formatted = (
            f"{self.formatTime(record, self.datefmt)} "
            f"{record.levelname} "
            f"{class_name}.{function_name}:{line_number}"
            f"{correlation_part} "
            f"{record.getMessage()}"
        )
        
        # Add exception info if present (but no stack trace by default)
        if record.exc_info and os.getenv('RASPIBOT_LOG_STACKTRACE', 'false').lower() == 'true':
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def set_correlation_id(correlation_id: Optional[str], task_name: Optional[str]) -> None:
    """Set correlation ID and task name for current context."""
    _correlation_id.set(correlation_id)
    _task_name.set(task_name)


def get_correlation_id() -> Tuple[Optional[str], Optional[str]]:
    """Get current correlation ID and task name."""
    return _correlation_id.get(), _task_name.get()


def setup_logging(name: str = "raspibot") -> logging.Logger:
    """Setup logging with custom formatter and configuration."""
    from raspibot.config.settings import LOG_LEVEL, LOG_TO_FILE, LOG_FILE_PATH
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = RaspibotFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if LOG_TO_FILE:
        try:
            # Ensure the log directory exists
            log_dir = os.path.dirname(LOG_FILE_PATH)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(LOG_FILE_PATH)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, log the error to console and continue
            logger.warning(f"Failed to setup file logging to '{LOG_FILE_PATH}': {e}")
            logger.warning("Continuing with console logging only")
    
    return logger 