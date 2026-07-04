import logging
import sys
from config import settings

def setup_logger(name: str = "farmer_assistant") -> logging.Logger:
    """
    Sets up a configured logger with standard formatting, log levels from settings,
    and stdout streaming.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If unable to write to log file, fall back silently to stdout
        pass
        
    return logger

# Shared global logger
logger = setup_logger()
