# gui/utils/app_logger.py
import logging
from datetime import datetime
import os
from typing import Optional

class AppLogger:
    """
    Custom logger for the application with file and console output.
    """
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('OrthoCFD')
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler
        log_file = os.path.join(
            log_dir,
            f'orthocfd_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_error(self, message: str, error: Optional[Exception] = None):
        """Log error message and exception details."""
        if error:
            self.logger.error(f"{message}: {str(error)}")
        else:
            self.logger.error(message)

    def log_info(self, message: str):
        """Log information message."""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)