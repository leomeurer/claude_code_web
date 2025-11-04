"""
Risk management system for trading operations.
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass
from crypto_trading.strategies.base_strategy import Signal, SignalType
from crypto_trading.core.order_manager import Order, OrderManager
from crypto_trading.utils.logger import get_logger


@dataclass
class RiskParameters:
    """Risk management parameters."""
    max_position_size_percent: float = 10.0  # Max % of portfolio per position
    stop_loss_percent: float = 2.0  # Stop loss %
    take_profit_percent: float = 5.0  # Take profit %
    max_daily_loss_percent: float = 5.0  # Max daily loss %
    trailing_stop: bool = True
    trailing_stop_percent: float = 1.5
    max_open_positions: int = 5
    risk_reward_ratio: float = 2.0  # Minimum risk/reward ratio


class RiskManager:
    """Manage risk for trading operations."""

    def __init__(
        self,
        initial_capital: float,
        risk_params: Optional[RiskParameters] = None
    ):
        """
        Initialize risk manager.

        Args:
            initial_capital: Initial trading capital
            risk_params: Risk parameters
        """
        self.logger = get_logger()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_params = risk_params or RiskParameters()
        self.daily_pnl = 0.0
        self.stop_trading = False
        self.position_sizes: Dict[str, float] = {}
        self.stop_losses: Dict[str, float] = {}
        self.take_profits: Dict[str, float] = {}
        self.trailing_stops: Dict[str, float] = {}

        self.logger.info(f"Risk Manager initialized with capital: {initial_capital}")

    def validate_trade(
        self,
        signal: Signal,
        order_manager: OrderManager,
        current_balance: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a trade should be executed based on risk parameters.

        Args:
            signal: Trading signal
            order_manager: Order manager instance
            current_balance: Current account balance

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Check if trading is stopped due to daily loss
            if self.stop_trading:
                return False, "Trading stopped due to daily loss limit"

            # Check daily loss limit
            daily_loss_limit = self.initial_capital * (self.risk_params.max_daily_loss_percent / 100)
            if self.daily_pnl < -daily_loss_limit:
                self.stop_trading = True
                self.logger.warning(f"Daily loss limit reached: {self.daily_pnl:.2f}")
                return False, "Daily loss limit exceeded"

            # Check maximum open positions
            open_positions = len([p for p in order_manager.get_all_positions().values() if p['amount'] > 0])
            if open_positions >= self.risk_params.max_open_positions:
                return False, f"Maximum open positions reached: {self.risk_params.max_open_positions}"

            # For BUY signals
            if signal.signal_type == SignalType.BUY:
                # Check if already have a position
                position = order_manager.get_position(signal.symbol)
                if position and position['amount'] > 0:
                    return False, f"Already have open position for {signal.symbol}"

                # Validate available capital
                max_position_value = current_balance * (self.risk_params.max_position_size_percent / 100)
                if max_position_value > current_balance:
                    return False, "Insufficient balance for position"

            # For SELL signals
            elif signal.signal_type == SignalType.SELL:
                # Check if have a position to sell
                position = order_manager.get_position(signal.symbol)
                if not position or position['amount'] <= 0:
                    return False, f"No position to sell for {signal.symbol}"

            return True, None

        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False, str(e)

    def calculate_position_size(
        self,
        signal: Signal,
        current_balance: float,
        current_price: float
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Args:
            signal: Trading signal
            current_balance: Current account balance
            current_price: Current asset price

        Returns:
            Position size (amount to buy/sell)
        """
        try:
            # Maximum position value based on portfolio percentage
            max_position_value = current_balance * (self.risk_params.max_position_size_percent / 100)

            # Calculate position size
            position_size = max_position_value / current_price

            # Adjust based on signal strength
            position_size *= signal.strength

            self.logger.debug(f"Calculated position size: {position_size} for {signal.symbol}")
            return position_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price
            side: Order side ('buy' or 'sell')

        Returns:
            Stop loss price
        """
        if side == 'buy':
            stop_loss = entry_price * (1 - self.risk_params.stop_loss_percent / 100)
        else:
            stop_loss = entry_price * (1 + self.risk_params.stop_loss_percent / 100)

        return stop_loss

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Entry price
            side: Order side ('buy' or 'sell')

        Returns:
            Take profit price
        """
        if side == 'buy':
            take_profit = entry_price * (1 + self.risk_params.take_profit_percent / 100)
        else:
            take_profit = entry_price * (1 - self.risk_params.take_profit_percent / 100)

        return take_profit

    def set_stop_loss(self, symbol: str, order: Order):
        """
        Set stop loss for a position.

        Args:
            symbol: Trading pair symbol
            order: Executed order
        """
        if order.filled_price:
            stop_loss = self.calculate_stop_loss(order.filled_price, order.side)
            self.stop_losses[symbol] = stop_loss
            self.logger.info(f"Stop loss set for {symbol} at {stop_loss:.2f}")

    def set_take_profit(self, symbol: str, order: Order):
        """
        Set take profit for a position.

        Args:
            symbol: Trading pair symbol
            order: Executed order
        """
        if order.filled_price:
            take_profit = self.calculate_take_profit(order.filled_price, order.side)
            self.take_profits[symbol] = take_profit
            self.logger.info(f"Take profit set for {symbol} at {take_profit:.2f}")

    def update_trailing_stop(self, symbol: str, current_price: float, side: str):
        """
        Update trailing stop loss.

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            side: Position side ('buy' or 'sell')
        """
        if not self.risk_params.trailing_stop:
            return

        trailing_distance = current_price * (self.risk_params.trailing_stop_percent / 100)

        if symbol not in self.trailing_stops:
            # Initialize trailing stop
            if side == 'buy':
                self.trailing_stops[symbol] = current_price - trailing_distance
            else:
                self.trailing_stops[symbol] = current_price + trailing_distance
        else:
            # Update trailing stop if price moved in favorable direction
            if side == 'buy':
                new_stop = current_price - trailing_distance
                if new_stop > self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = new_stop
                    self.logger.debug(f"Updated trailing stop for {symbol} to {new_stop:.2f}")
            else:
                new_stop = current_price + trailing_distance
                if new_stop < self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = new_stop
                    self.logger.debug(f"Updated trailing stop for {symbol} to {new_stop:.2f}")

    def check_stop_loss(self, symbol: str, current_price: float, side: str) -> bool:
        """
        Check if stop loss is hit.

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            side: Position side ('buy' or 'sell')

        Returns:
            True if stop loss hit
        """
        # Check regular stop loss
        if symbol in self.stop_losses:
            stop_loss = self.stop_losses[symbol]
            if side == 'buy' and current_price <= stop_loss:
                self.logger.warning(f"Stop loss hit for {symbol} at {current_price:.2f}")
                return True
            elif side == 'sell' and current_price >= stop_loss:
                self.logger.warning(f"Stop loss hit for {symbol} at {current_price:.2f}")
                return True

        # Check trailing stop
        if symbol in self.trailing_stops:
            trailing_stop = self.trailing_stops[symbol]
            if side == 'buy' and current_price <= trailing_stop:
                self.logger.warning(f"Trailing stop hit for {symbol} at {current_price:.2f}")
                return True
            elif side == 'sell' and current_price >= trailing_stop:
                self.logger.warning(f"Trailing stop hit for {symbol} at {current_price:.2f}")
                return True

        return False

    def check_take_profit(self, symbol: str, current_price: float, side: str) -> bool:
        """
        Check if take profit is hit.

        Args:
            symbol: Trading pair symbol
            current_price: Current market price
            side: Position side ('buy' or 'sell')

        Returns:
            True if take profit hit
        """
        if symbol not in self.take_profits:
            return False

        take_profit = self.take_profits[symbol]

        if side == 'buy' and current_price >= take_profit:
            self.logger.info(f"Take profit hit for {symbol} at {current_price:.2f}")
            return True
        elif side == 'sell' and current_price <= take_profit:
            self.logger.info(f"Take profit hit for {symbol} at {current_price:.2f}")
            return True

        return False

    def update_pnl(self, pnl: float):
        """
        Update daily P&L.

        Args:
            pnl: Profit/loss amount
        """
        self.daily_pnl += pnl
        self.current_capital = self.initial_capital + self.daily_pnl
        self.logger.debug(f"Updated P&L: {self.daily_pnl:.2f}, Capital: {self.current_capital:.2f}")

    def reset_daily_pnl(self):
        """Reset daily P&L counter."""
        self.daily_pnl = 0.0
        self.stop_trading = False
        self.logger.info("Daily P&L reset")

    def clear_position_risk(self, symbol: str):
        """
        Clear risk parameters for a closed position.

        Args:
            symbol: Trading pair symbol
        """
        if symbol in self.stop_losses:
            del self.stop_losses[symbol]
        if symbol in self.take_profits:
            del self.take_profits[symbol]
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
        if symbol in self.position_sizes:
            del self.position_sizes[symbol]

        self.logger.debug(f"Cleared risk parameters for {symbol}")

    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get risk management summary.

        Returns:
            Dictionary with risk information
        """
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_percent': (self.daily_pnl / self.initial_capital) * 100,
            'stop_trading': self.stop_trading,
            'open_positions': len(self.position_sizes),
            'max_daily_loss': self.initial_capital * (self.risk_params.max_daily_loss_percent / 100),
            'remaining_daily_loss': (self.initial_capital * (self.risk_params.max_daily_loss_percent / 100)) + self.daily_pnl
        }
