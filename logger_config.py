import logging
import os
import sys

def setup_logging(log_level=None):
    """
    Set up logging configuration with configurable log level.
    
    Args:
        log_level (str, optional): Logging level. 
        Defaults to environment variable or INFO.
        Supported levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    # Determine log level from environment variable or default to INFO
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Map log level string to logging module constants
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # Validate and set log level
    level = log_levels.get(log_level, logging.INFO)
    
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    logging.basicConfig(level=level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger

# Optional: Create a module-level logger
logger = logging.getLogger(__name__)

# Automatically set up logging when the module is imported
setup_logging()
