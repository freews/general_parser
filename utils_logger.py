import logging
import sys
from pathlib import Path
from typing import Union, Optional

def setup_advanced_logger(
    name: str, 
    dir: Union[str, Path], 
    log_level: int = logging.INFO,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    
    Args:
        name: Name of the logger
        dir: Directory to save log files
        log_level: Logging level (constant from logging module)
        level: String representation of level (optional, overrides log_level if provided)
    
    Returns:
        Configured logger instance
    """
    # Handle string level input (compatibility with some calls)
    if level:
        level_upper = level.upper()
        if level_upper == "DEBUG":
            log_level = logging.DEBUG
        elif level_upper == "INFO":
            log_level = logging.INFO
        elif level_upper == "WARNING":
            log_level = logging.WARNING
        elif level_upper == "ERROR":
            log_level = logging.ERROR
        elif level_upper == "CRITICAL":
            log_level = logging.CRITICAL
            
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
        
    # Ensure capture of all messages including those before handlers are added?
    # No, just standard setup.
    
    # Create log directory
    if isinstance(dir, str):
        dir = Path(dir)
    
    # If dir is a relative path like "output", make it absolute based on CWD or project root
    # Ideally should be passed absolute, but let's be safe.
    if not dir.is_absolute():
        # Assuming run from project root, or handle it? 
        # Making it absolute from CWD is standard.
        dir = Path.cwd() / dir
        
    try:
        dir.mkdir(parents=True, exist_ok=True)
        log_file = dir / f"{name}.log"
        
        # File Handler
        file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(message)s'  # Simplified for console
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
