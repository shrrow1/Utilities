import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


class CustomLogger:
    """
    A highly reusable and encapsulated logging class that wraps the standard
    Python logging module. It configures both console and file output with
    sensible defaults, avoiding duplicate handler issues.
    """

    def __init__(
            self,
            name: str,
            log_file: Optional[str] = None,
            level: int = logging.INFO,
            max_bytes: int = 5 * 1024 * 1024,  # 5 MB
            backup_count: int = 5
    ):
        """
        Initializes the custom logger.

        Args:
            name (str): Name of the logger (usually __name__).
            log_file (str, optional): Path to a log file. If provided, logs will be saved here.
            level (int): Default logging level (e.g., logging.DEBUG, logging.INFO).
            max_bytes (int): Maximum size of log file before rotating.
            backup_count (int): Number of rotated log files to keep.
        """
        # Method 1: Automatically resolve "__main__" to the actual running script name
        if name == "__main__":
            if sys.argv and sys.argv[0]:
                script_path = sys.argv[0]
                name = os.path.splitext(os.path.basename(script_path))[0]

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent log messages from propagating to the root logger handlers multiple times
        self.logger.propagate = False

        # Clear existing handlers if the logger was already configured elsewhere
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Define a standard format
        log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # 1. Console Handler (Standard Formatting)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 2. File Handler (Optional, with Rotation)
        if log_file:
            # Ensure target directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, *args, **kwargs):
        """Log a debug level message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log an info level message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a warning level message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log an error level message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log a critical level message."""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log an error level message with exception traceback context."""
        self.logger.exception(msg, *args, **kwargs)