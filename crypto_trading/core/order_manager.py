"""
Order management system for executing and tracking trades.
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.strategies.base_strategy import Signal, SignalType
from crypto_trading.utils.logger import get_logger


class OrderStatus(Enum):
    """Order status types."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELED = "canceled"
    FAILED = "failed"


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass
class Order:
    """Order data structure."""
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    filled_price: Optional[float] = None
    fee: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"Order({self.side} {self.amount} {self.symbol} @ {self.price}, status={self.status.value})"


class OrderManager:
    """Manage order execution and tracking."""

    def __init__(self, exchange_connector: ExchangeConnector):
        """
        Initialize order manager.

        Args:
            exchange_connector: Exchange connector instance
        """
        self.exchange = exchange_connector
        self.logger = get_logger()
        self.orders: List[Order] = []
        self.open_positions: Dict[str, Dict[str, Any]] = {}

    def execute_signal(
        self,
        signal: Signal,
        amount: float,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None
    ) -> Optional[Order]:
        """
        Execute a trading signal.

        Args:
            signal: Trading signal
            amount: Order amount
            order_type: Type of order
            price: Limit price (for limit orders)

        Returns:
            Order object if executed, None if skipped
        """
        try:
            if signal.signal_type == SignalType.HOLD:
                self.logger.debug("HOLD signal, no order executed")
                return None

            side = signal.signal_type.value  # 'buy' or 'sell'

            # Create order object
            order = Order(
                symbol=signal.symbol,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price or signal.price,
                metadata={
                    'signal_strength': signal.strength,
                    'signal_metadata': signal.metadata
                }
            )

            # Execute order on exchange
            if order_type == OrderType.MARKET:
                result = self._execute_market_order(order)
            elif order_type == OrderType.LIMIT:
                result = self._execute_limit_order(order)
            else:
                self.logger.error(f"Unsupported order type: {order_type}")
                return None

            if result:
                self.orders.append(order)
                self._update_position(order)
                return order

            return None

        except Exception as e:
            self.logger.error(f"Failed to execute signal: {e}")
            return None

    def _execute_market_order(self, order: Order) -> bool:
        """
        Execute market order.

        Args:
            order: Order to execute

        Returns:
            True if successful
        """
        try:
            result = self.exchange.create_market_order(
                order.symbol,
                order.side,
                order.amount
            )

            # Update order with result
            order.order_id = result.get('id')
            order.status = OrderStatus.FILLED if result.get('status') == 'closed' else OrderStatus.OPEN
            order.filled_amount = float(result.get('filled', 0))
            order.filled_price = float(result.get('price', 0)) if result.get('price') else None
            order.fee = float(result.get('fee', {}).get('cost', 0))

            self.logger.info(f"Market order executed: {order}")
            return True

        except Exception as e:
            order.status = OrderStatus.FAILED
            self.logger.error(f"Failed to execute market order: {e}")
            return False

    def _execute_limit_order(self, order: Order) -> bool:
        """
        Execute limit order.

        Args:
            order: Order to execute

        Returns:
            True if successful
        """
        try:
            if order.price is None:
                raise ValueError("Limit order requires price")

            result = self.exchange.create_limit_order(
                order.symbol,
                order.side,
                order.amount,
                order.price
            )

            # Update order with result
            order.order_id = result.get('id')
            order.status = OrderStatus.OPEN
            order.filled_amount = float(result.get('filled', 0))

            self.logger.info(f"Limit order placed: {order}")
            return True

        except Exception as e:
            order.status = OrderStatus.FAILED
            self.logger.error(f"Failed to execute limit order: {e}")
            return False

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an open order.

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            True if successful
        """
        try:
            self.exchange.cancel_order(order_id, symbol)

            # Update local order status
            for order in self.orders:
                if order.order_id == order_id:
                    order.status = OrderStatus.CANCELED
                    break

            self.logger.info(f"Order {order_id} canceled")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            return False

    def update_order_status(self, order_id: str, symbol: str) -> Optional[Order]:
        """
        Update order status from exchange.

        Args:
            order_id: Order ID
            symbol: Trading pair symbol

        Returns:
            Updated order object
        """
        try:
            result = self.exchange.get_order_status(order_id, symbol)

            # Find and update local order
            for order in self.orders:
                if order.order_id == order_id:
                    status_map = {
                        'open': OrderStatus.OPEN,
                        'closed': OrderStatus.FILLED,
                        'canceled': OrderStatus.CANCELED,
                        'expired': OrderStatus.CANCELED
                    }

                    order.status = status_map.get(result.get('status', ''), OrderStatus.OPEN)
                    order.filled_amount = float(result.get('filled', 0))
                    order.filled_price = float(result.get('price', 0)) if result.get('price') else None

                    self.logger.debug(f"Updated order {order_id}: {order.status.value}")
                    return order

            return None

        except Exception as e:
            self.logger.error(f"Failed to update order status: {e}")
            return None

    def _update_position(self, order: Order):
        """
        Update position tracking.

        Args:
            order: Executed order
        """
        if order.status != OrderStatus.FILLED:
            return

        symbol = order.symbol

        if symbol not in self.open_positions:
            self.open_positions[symbol] = {
                'amount': 0.0,
                'avg_price': 0.0,
                'total_cost': 0.0,
                'realized_pnl': 0.0
            }

        position = self.open_positions[symbol]

        if order.side == 'buy':
            # Adding to position
            total_cost = position['total_cost'] + (order.filled_amount * order.filled_price)
            total_amount = position['amount'] + order.filled_amount
            position['avg_price'] = total_cost / total_amount if total_amount > 0 else 0
            position['amount'] = total_amount
            position['total_cost'] = total_cost

        elif order.side == 'sell':
            # Reducing position
            pnl = (order.filled_price - position['avg_price']) * order.filled_amount
            position['realized_pnl'] += pnl
            position['amount'] -= order.filled_amount
            position['total_cost'] -= order.filled_amount * position['avg_price']

            # Close position if amount reaches zero
            if position['amount'] <= 0:
                self.logger.info(f"Position closed for {symbol}. Realized P&L: {position['realized_pnl']:.2f}")
                position['amount'] = 0
                position['total_cost'] = 0

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Position information
        """
        return self.open_positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            Dictionary of all positions
        """
        return self.open_positions

    def get_order_history(self, symbol: Optional[str] = None) -> List[Order]:
        """
        Get order history.

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            List of orders
        """
        if symbol:
            return [order for order in self.orders if order.symbol == symbol]
        return self.orders

    def get_open_orders(self) -> List[Order]:
        """
        Get all open orders.

        Returns:
            List of open orders
        """
        return [order for order in self.orders if order.status == OrderStatus.OPEN]

    def calculate_pnl(self, symbol: str, current_price: float) -> Dict[str, float]:
        """
        Calculate profit/loss for a position.

        Args:
            symbol: Trading pair symbol
            current_price: Current market price

        Returns:
            Dictionary with PnL information
        """
        position = self.get_position(symbol)

        if not position or position['amount'] == 0:
            return {
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_pnl': 0.0,
                'pnl_percent': 0.0
            }

        unrealized_pnl = (current_price - position['avg_price']) * position['amount']
        total_pnl = unrealized_pnl + position['realized_pnl']
        pnl_percent = (total_pnl / position['total_cost']) * 100 if position['total_cost'] > 0 else 0

        return {
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': position['realized_pnl'],
            'total_pnl': total_pnl,
            'pnl_percent': pnl_percent
        }

    def get_summary(self) -> pd.DataFrame:
        """
        Get summary of all orders.

        Returns:
            DataFrame with order summary
        """
        if not self.orders:
            return pd.DataFrame()

        data = []
        for order in self.orders:
            data.append({
                'timestamp': order.timestamp,
                'symbol': order.symbol,
                'side': order.side,
                'type': order.order_type.value,
                'amount': order.amount,
                'price': order.price,
                'filled_amount': order.filled_amount,
                'filled_price': order.filled_price,
                'status': order.status.value,
                'fee': order.fee
            })

        return pd.DataFrame(data)
