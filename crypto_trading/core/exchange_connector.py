"""
Exchange connector for interacting with cryptocurrency exchanges.
"""
import ccxt
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from crypto_trading.utils.logger import get_logger


class ExchangeConnector:
    """Connector for cryptocurrency exchanges using CCXT library."""

    def __init__(self, exchange_name: str = 'binance', testnet: bool = True):
        """
        Initialize exchange connector.

        Args:
            exchange_name: Name of the exchange (binance, coinbase, etc.)
            testnet: Whether to use testnet/sandbox mode
        """
        self.logger = get_logger()
        self.exchange_name = exchange_name.lower()
        self.testnet = testnet
        self.exchange = None
        self._initialize_exchange()

    def _initialize_exchange(self):
        """Initialize the exchange connection."""
        try:
            # Get exchange class
            exchange_class = getattr(ccxt, self.exchange_name)

            # Get API credentials from environment
            api_key = os.getenv(f'{self.exchange_name.upper()}_API_KEY', '')
            api_secret = os.getenv(f'{self.exchange_name.upper()}_API_SECRET', '')

            # Initialize exchange
            config = {
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # spot, future, swap
                }
            }

            self.exchange = exchange_class(config)

            # Enable testnet if specified
            if self.testnet:
                if hasattr(self.exchange, 'set_sandbox_mode'):
                    self.exchange.set_sandbox_mode(True)
                    self.logger.info(f"Connected to {self.exchange_name} in TESTNET mode")
                else:
                    self.logger.warning(f"{self.exchange_name} doesn't support testnet mode")
            else:
                self.logger.info(f"Connected to {self.exchange_name} in LIVE mode")

            # Load markets
            self.exchange.load_markets()
            self.logger.info(f"Loaded {len(self.exchange.markets)} markets from {self.exchange_name}")

        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')

        Returns:
            Dictionary with ticker data
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            self.logger.debug(f"Fetched ticker for {symbol}: {ticker['last']}")
            return ticker
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List]:
        """
        Get OHLCV (candlestick) data.

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch

        Returns:
            List of OHLCV data [timestamp, open, high, low, close, volume]
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            self.logger.debug(f"Fetched {len(ohlcv)} candles for {symbol} ({timeframe})")
            return ohlcv
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise

    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book data.

        Args:
            symbol: Trading pair symbol
            limit: Depth of order book

        Returns:
            Dictionary with bids and asks
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            self.logger.debug(f"Fetched orderbook for {symbol}")
            return orderbook
        except Exception as e:
            self.logger.error(f"Failed to fetch orderbook for {symbol}: {e}")
            raise

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.

        Returns:
            Dictionary with balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            self.logger.info("Fetched account balance")
            return balance
        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            raise

    def create_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """
        Create a market order.

        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount

        Returns:
            Order information
        """
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            self.logger.info(f"Created market {side} order for {amount} {symbol}")
            return order
        except Exception as e:
            self.logger.error(f"Failed to create market order: {e}")
            raise

    def create_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Create a limit order.

        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount
            price: Limit price

        Returns:
            Order information
        """
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            self.logger.info(f"Created limit {side} order for {amount} {symbol} at {price}")
            return order
        except Exception as e:
            self.logger.error(f"Failed to create limit order: {e}")
            raise

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Cancellation result
        """
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Canceled order {order_id} for {symbol}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders.

        Args:
            symbol: Trading pair symbol (optional, get all if None)

        Returns:
            List of open orders
        """
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            self.logger.info(f"Fetched {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Failed to fetch open orders: {e}")
            raise

    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get order status.

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Order status information
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            self.logger.debug(f"Fetched order {order_id} status: {order['status']}")
            return order
        except Exception as e:
            self.logger.error(f"Failed to fetch order status: {e}")
            raise

    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get trading fees.

        Args:
            symbol: Trading pair symbol (optional)

        Returns:
            Fee information
        """
        try:
            if symbol:
                fees = self.exchange.fetch_trading_fee(symbol)
            else:
                fees = self.exchange.fetch_trading_fees()
            self.logger.debug("Fetched trading fees")
            return fees
        except Exception as e:
            self.logger.error(f"Failed to fetch trading fees: {e}")
            raise

    def close(self):
        """Close exchange connection."""
        if self.exchange:
            self.logger.info(f"Closing connection to {self.exchange_name}")
            self.exchange = None
