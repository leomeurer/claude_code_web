"""
Logging utility for the crypto trading system.
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class TradingLogger:
    """Custom logger for trading operations."""

    def __init__(self, log_file: Optional[str] = None, level: str = "INFO"):
        """
        Initialize the trading logger.

        Args:
            log_file: Path to the log file
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Remove default handler
        logger.remove()

        # Add console handler with colors
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=level
        )

        # Add file handler if log_file is provided
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_file,
                rotation="500 MB",
                retention="10 days",
                compression="zip",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
                level=level
            )

        self.logger = logger

    def get_logger(self):
        """Get the logger instance."""
        return self.logger


# Global logger instance
_trading_logger = None


def get_logger(log_file: Optional[str] = None, level: str = "INFO"):
    """
    Get or create the global trading logger.

    Args:
        log_file: Path to the log file
        level: Logging level

    Returns:
        Logger instance
    """
    global _trading_logger

    if _trading_logger is None:
        _trading_logger = TradingLogger(log_file, level)

    return _trading_logger.get_logger()
