"""
Market data collection and processing.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.utils.logger import get_logger


class MarketData:
    """Collect and process market data from exchanges."""

    def __init__(self, exchange_connector: ExchangeConnector):
        """
        Initialize market data collector.

        Args:
            exchange_connector: Exchange connector instance
        """
        self.exchange = exchange_connector
        self.logger = get_logger()
        self.data_cache: Dict[str, pd.DataFrame] = {}

    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for candles
            days: Number of days to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Calculate the number of candles needed
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }

            minutes = timeframe_minutes.get(timeframe, 60)
            total_candles = (days * 24 * 60) // minutes

            # Fetch data in chunks (most exchanges limit to 1000 candles per request)
            chunk_size = 1000
            all_data = []

            for i in range(0, total_candles, chunk_size):
                limit = min(chunk_size, total_candles - i)
                ohlcv = self.exchange.get_ohlcv(symbol, timeframe, limit)
                all_data.extend(ohlcv)

                if len(ohlcv) < limit:
                    break

            # Convert to DataFrame
            df = pd.DataFrame(
                all_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Cache the data
            cache_key = f"{symbol}_{timeframe}"
            self.data_cache[cache_key] = df

            self.logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df

        except Exception as e:
            self.logger.error(f"Failed to fetch historical data: {e}")
            raise

    def get_latest_candle(self, symbol: str, timeframe: str = '1h') -> pd.Series:
        """
        Get the latest candle data.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for candle

        Returns:
            Series with latest candle data
        """
        try:
            ohlcv = self.exchange.get_ohlcv(symbol, timeframe, limit=1)

            if not ohlcv:
                raise ValueError("No data received")

            latest = ohlcv[-1]
            series = pd.Series({
                'timestamp': pd.to_datetime(latest[0], unit='ms'),
                'open': float(latest[1]),
                'high': float(latest[2]),
                'low': float(latest[3]),
                'close': float(latest[4]),
                'volume': float(latest[5])
            })

            return series

        except Exception as e:
            self.logger.error(f"Failed to fetch latest candle: {e}")
            raise

    def update_data(self, symbol: str, timeframe: str = '1h') -> pd.DataFrame:
        """
        Update cached data with latest candles.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for candles

        Returns:
            Updated DataFrame
        """
        try:
            cache_key = f"{symbol}_{timeframe}"

            # Fetch latest candles
            ohlcv = self.exchange.get_ohlcv(symbol, timeframe, limit=100)

            new_df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms')
            new_df.set_index('timestamp', inplace=True)

            # Merge with cached data
            if cache_key in self.data_cache:
                existing_df = self.data_cache[cache_key]
                # Combine and remove duplicates
                combined_df = pd.concat([existing_df, new_df])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df.sort_index(inplace=True)
                self.data_cache[cache_key] = combined_df
            else:
                self.data_cache[cache_key] = new_df

            self.logger.debug(f"Updated data for {symbol} ({timeframe})")
            return self.data_cache[cache_key]

        except Exception as e:
            self.logger.error(f"Failed to update data: {e}")
            raise

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Current price
        """
        try:
            ticker = self.exchange.get_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            self.logger.error(f"Failed to get current price: {e}")
            raise

    def get_orderbook_data(self, symbol: str, limit: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Get orderbook data as DataFrames.

        Args:
            symbol: Trading pair symbol
            limit: Depth of orderbook

        Returns:
            Dictionary with 'bids' and 'asks' DataFrames
        """
        try:
            orderbook = self.exchange.get_orderbook(symbol, limit)

            bids_df = pd.DataFrame(orderbook['bids'], columns=['price', 'amount'])
            asks_df = pd.DataFrame(orderbook['asks'], columns=['price', 'amount'])

            return {
                'bids': bids_df,
                'asks': asks_df,
                'timestamp': orderbook.get('timestamp')
            }

        except Exception as e:
            self.logger.error(f"Failed to get orderbook data: {e}")
            raise

    def calculate_vwap(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.

        Args:
            df: DataFrame with OHLCV data
            period: Period for calculation

        Returns:
            Series with VWAP values
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).rolling(window=period).sum() / \
               df['volume'].rolling(window=period).sum()

        return vwap

    def get_cached_data(self, symbol: str, timeframe: str = '1h') -> Optional[pd.DataFrame]:
        """
        Get cached data for a symbol.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Cached DataFrame or None
        """
        cache_key = f"{symbol}_{timeframe}"
        return self.data_cache.get(cache_key)

    def save_data(self, symbol: str, timeframe: str, filepath: str):
        """
        Save data to CSV file.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            filepath: Path to save file
        """
        try:
            cache_key = f"{symbol}_{timeframe}"
            if cache_key in self.data_cache:
                df = self.data_cache[cache_key]
                df.to_csv(filepath)
                self.logger.info(f"Saved data to {filepath}")
            else:
                self.logger.warning(f"No cached data found for {symbol} ({timeframe})")

        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            raise

    def load_data(self, filepath: str, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Load data from CSV file.

        Args:
            filepath: Path to CSV file
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            DataFrame with loaded data
        """
        try:
            df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            cache_key = f"{symbol}_{timeframe}"
            self.data_cache[cache_key] = df
            self.logger.info(f"Loaded data from {filepath}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            raise
