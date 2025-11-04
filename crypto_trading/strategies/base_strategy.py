"""
Base strategy class for trading strategies.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional
from enum import Enum
from crypto_trading.utils.logger import get_logger


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal:
    """Trading signal with metadata."""

    def __init__(
        self,
        signal_type: SignalType,
        symbol: str,
        price: float,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize trading signal.

        Args:
            signal_type: Type of signal (BUY, SELL, HOLD)
            symbol: Trading pair symbol
            price: Price at signal generation
            strength: Signal strength (0.0 to 1.0)
            metadata: Additional signal information
        """
        self.signal_type = signal_type
        self.symbol = symbol
        self.price = price
        self.strength = strength
        self.metadata = metadata or {}
        self.timestamp = pd.Timestamp.now()

    def __repr__(self):
        return f"Signal({self.signal_type.value}, {self.symbol}, {self.price}, strength={self.strength})"


class BaseStrategy(ABC):
    """Base class for all trading strategies."""

    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            parameters: Strategy parameters
        """
        self.name = name
        self.parameters = parameters or {}
        self.logger = get_logger()
        self.logger.info(f"Initialized strategy: {name}")

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicators
        """
        pass

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Signal:
        """
        Generate trading signal based on indicators.

        Args:
            df: DataFrame with OHLCV and indicators
            symbol: Trading pair symbol

        Returns:
            Trading signal
        """
        pass

    def validate_data(self, df: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate that DataFrame has required columns and data.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names

        Returns:
            True if valid, False otherwise
        """
        if df is None or df.empty:
            self.logger.warning("DataFrame is empty")
            return False

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.warning(f"Missing columns: {missing_columns}")
            return False

        return True

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get strategy parameter.

        Args:
            key: Parameter key
            default: Default value if not found

        Returns:
            Parameter value
        """
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any):
        """
        Set strategy parameter.

        Args:
            key: Parameter key
            value: Parameter value
        """
        self.parameters[key] = value
        self.logger.debug(f"Set parameter {key} = {value}")

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', parameters={self.parameters})"
