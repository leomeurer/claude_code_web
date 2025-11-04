"""
Moving Average Crossover Strategy with RSI filter.
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional, Dict, Any
from crypto_trading.strategies.base_strategy import BaseStrategy, Signal, SignalType
from crypto_trading.utils.logger import get_logger


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy with RSI filter.

    Generates BUY signal when:
    - Fast MA crosses above Slow MA
    - RSI is not overbought (< 70)

    Generates SELL signal when:
    - Fast MA crosses below Slow MA
    - RSI is not oversold (> 30)
    """

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize Moving Average Crossover strategy.

        Args:
            parameters: Strategy parameters
                - fast_period: Fast MA period (default: 10)
                - slow_period: Slow MA period (default: 30)
                - rsi_period: RSI period (default: 14)
                - rsi_overbought: RSI overbought level (default: 70)
                - rsi_oversold: RSI oversold level (default: 30)
        """
        default_params = {
            'fast_period': 10,
            'slow_period': 30,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }

        if parameters:
            default_params.update(parameters)

        super().__init__("Moving Average Crossover", default_params)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages and RSI.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicators
        """
        try:
            if not self.validate_data(df, ['close']):
                raise ValueError("Invalid data for indicator calculation")

            # Make a copy to avoid modifying original
            df = df.copy()

            # Get parameters
            fast_period = self.get_parameter('fast_period')
            slow_period = self.get_parameter('slow_period')
            rsi_period = self.get_parameter('rsi_period')

            # Calculate moving averages
            df['ma_fast'] = ta.sma(df['close'], length=fast_period)
            df['ma_slow'] = ta.sma(df['close'], length=slow_period)

            # Calculate RSI
            df['rsi'] = ta.rsi(df['close'], length=rsi_period)

            # Calculate MACD for additional confirmation
            macd = ta.macd(df['close'])
            if macd is not None:
                df['macd'] = macd['MACD_12_26_9']
                df['macd_signal'] = macd['MACDs_12_26_9']
                df['macd_hist'] = macd['MACDh_12_26_9']

            # Calculate Bollinger Bands
            bbands = ta.bbands(df['close'], length=20)
            if bbands is not None:
                df['bb_upper'] = bbands['BBU_20_2.0']
                df['bb_middle'] = bbands['BBM_20_2.0']
                df['bb_lower'] = bbands['BBL_20_2.0']

            # Calculate volume indicators
            df['volume_sma'] = ta.sma(df['volume'], length=20)

            self.logger.debug(f"Calculated indicators for {len(df)} rows")
            return df

        except Exception as e:
            self.logger.error(f"Failed to calculate indicators: {e}")
            raise

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Signal:
        """
        Generate trading signal based on MA crossover and RSI.

        Args:
            df: DataFrame with OHLCV and indicators
            symbol: Trading pair symbol

        Returns:
            Trading signal
        """
        try:
            # Calculate indicators if not present
            if 'ma_fast' not in df.columns:
                df = self.calculate_indicators(df)

            # Need at least 2 rows to detect crossover
            if len(df) < 2:
                return Signal(SignalType.HOLD, symbol, df['close'].iloc[-1])

            # Get latest and previous values
            current = df.iloc[-1]
            previous = df.iloc[-2]

            # Get parameters
            rsi_overbought = self.get_parameter('rsi_overbought')
            rsi_oversold = self.get_parameter('rsi_oversold')

            # Current price
            current_price = float(current['close'])

            # Check for NaN values
            if pd.isna(current['ma_fast']) or pd.isna(current['ma_slow']) or pd.isna(current['rsi']):
                self.logger.debug("Indicators not ready, returning HOLD")
                return Signal(SignalType.HOLD, symbol, current_price)

            # Detect crossover
            bullish_cross = (
                previous['ma_fast'] <= previous['ma_slow'] and
                current['ma_fast'] > current['ma_slow']
            )

            bearish_cross = (
                previous['ma_fast'] >= previous['ma_slow'] and
                current['ma_fast'] < current['ma_slow']
            )

            # Calculate signal strength
            ma_diff = abs(current['ma_fast'] - current['ma_slow']) / current['close']
            signal_strength = min(ma_diff * 100, 1.0)

            # Metadata
            metadata = {
                'ma_fast': float(current['ma_fast']),
                'ma_slow': float(current['ma_slow']),
                'rsi': float(current['rsi']),
                'volume': float(current['volume']),
                'volume_sma': float(current['volume_sma']) if 'volume_sma' in current else None
            }

            # Add MACD if available
            if 'macd' in current:
                metadata['macd'] = float(current['macd'])
                metadata['macd_signal'] = float(current['macd_signal'])

            # Generate signal
            if bullish_cross and current['rsi'] < rsi_overbought:
                # Additional confirmation: volume above average
                volume_confirmation = current['volume'] > current['volume_sma'] if 'volume_sma' in current else True

                if volume_confirmation:
                    self.logger.info(f"BUY signal for {symbol} at {current_price} (RSI: {current['rsi']:.2f})")
                    return Signal(SignalType.BUY, symbol, current_price, signal_strength, metadata)

            elif bearish_cross and current['rsi'] > rsi_oversold:
                # Additional confirmation: volume above average
                volume_confirmation = current['volume'] > current['volume_sma'] if 'volume_sma' in current else True

                if volume_confirmation:
                    self.logger.info(f"SELL signal for {symbol} at {current_price} (RSI: {current['rsi']:.2f})")
                    return Signal(SignalType.SELL, symbol, current_price, signal_strength, metadata)

            # No signal, hold position
            return Signal(SignalType.HOLD, symbol, current_price, 0.0, metadata)

        except Exception as e:
            self.logger.error(f"Failed to generate signal: {e}")
            # Return HOLD signal on error
            return Signal(SignalType.HOLD, symbol, df['close'].iloc[-1] if len(df) > 0 else 0.0)

    def get_trend(self, df: pd.DataFrame) -> str:
        """
        Determine market trend.

        Args:
            df: DataFrame with indicators

        Returns:
            Trend ('uptrend', 'downtrend', 'sideways')
        """
        if 'ma_fast' not in df.columns:
            df = self.calculate_indicators(df)

        current = df.iloc[-1]

        if pd.isna(current['ma_fast']) or pd.isna(current['ma_slow']):
            return 'unknown'

        if current['ma_fast'] > current['ma_slow']:
            return 'uptrend'
        elif current['ma_fast'] < current['ma_slow']:
            return 'downtrend'
        else:
            return 'sideways'
