"""Logging configuration for the trading application"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path for logging
        format_string: Optional custom format string
        
    Returns:
        Root logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capability to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


def log_error(logger: logging.Logger, error: Exception, message: str = "An error occurred"):
    """
    Log an error with full traceback
    
    Args:
        logger: Logger instance
        error: Exception to log
        message: Custom error message
    """
    logger.error(f"{message}: {str(error)}", exc_info=True)


def log_api_call(logger: logging.Logger, method: str, endpoint: str, status: str = "success"):
    """
    Log an API call
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint
        status: Call status
    """
    logger.info(f"API {method} {endpoint} - {status}")
