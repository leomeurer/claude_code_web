"""
Unit tests for risk manager.
"""
import pytest
from crypto_trading.core.risk_manager import RiskManager, RiskParameters
from crypto_trading.core.order_manager import OrderManager, Order, OrderType, OrderStatus
from crypto_trading.strategies.base_strategy import Signal, SignalType


@pytest.fixture
def risk_manager():
    """Create risk manager instance."""
    params = RiskParameters(
        max_position_size_percent=10.0,
        stop_loss_percent=2.0,
        take_profit_percent=5.0,
        max_daily_loss_percent=5.0,
        trailing_stop=True,
        trailing_stop_percent=1.5
    )
    return RiskManager(initial_capital=10000, risk_params=params)


def test_risk_manager_initialization(risk_manager):
    """Test risk manager initialization."""
    assert risk_manager.initial_capital == 10000
    assert risk_manager.current_capital == 10000
    assert risk_manager.daily_pnl == 0.0
    assert risk_manager.stop_trading is False


def test_calculate_position_size(risk_manager):
    """Test position size calculation."""
    signal = Signal(SignalType.BUY, 'BTC/USDT', 40000, strength=1.0)

    position_size = risk_manager.calculate_position_size(
        signal,
        current_balance=10000,
        current_price=40000
    )

    # Should be 10% of portfolio
    expected_value = 10000 * 0.10
    expected_size = expected_value / 40000

    assert abs(position_size - expected_size) < 0.0001


def test_calculate_position_size_with_signal_strength(risk_manager):
    """Test position size with different signal strength."""
    signal = Signal(SignalType.BUY, 'BTC/USDT', 40000, strength=0.5)

    position_size = risk_manager.calculate_position_size(
        signal,
        current_balance=10000,
        current_price=40000
    )

    # Should be adjusted by signal strength
    expected_value = 10000 * 0.10 * 0.5
    expected_size = expected_value / 40000

    assert abs(position_size - expected_size) < 0.0001


def test_calculate_stop_loss_buy(risk_manager):
    """Test stop loss calculation for buy order."""
    entry_price = 40000
    stop_loss = risk_manager.calculate_stop_loss(entry_price, 'buy')

    # Should be 2% below entry price
    expected_stop = entry_price * (1 - 0.02)

    assert abs(stop_loss - expected_stop) < 0.01


def test_calculate_stop_loss_sell(risk_manager):
    """Test stop loss calculation for sell order."""
    entry_price = 40000
    stop_loss = risk_manager.calculate_stop_loss(entry_price, 'sell')

    # Should be 2% above entry price
    expected_stop = entry_price * (1 + 0.02)

    assert abs(stop_loss - expected_stop) < 0.01


def test_calculate_take_profit_buy(risk_manager):
    """Test take profit calculation for buy order."""
    entry_price = 40000
    take_profit = risk_manager.calculate_take_profit(entry_price, 'buy')

    # Should be 5% above entry price
    expected_tp = entry_price * (1 + 0.05)

    assert abs(take_profit - expected_tp) < 0.01


def test_set_stop_loss(risk_manager):
    """Test setting stop loss."""
    order = Order(
        symbol='BTC/USDT',
        side='buy',
        order_type=OrderType.MARKET,
        amount=0.1,
        filled_price=40000
    )

    risk_manager.set_stop_loss('BTC/USDT', order)

    assert 'BTC/USDT' in risk_manager.stop_losses
    assert risk_manager.stop_losses['BTC/USDT'] < 40000


def test_set_take_profit(risk_manager):
    """Test setting take profit."""
    order = Order(
        symbol='BTC/USDT',
        side='buy',
        order_type=OrderType.MARKET,
        amount=0.1,
        filled_price=40000
    )

    risk_manager.set_take_profit('BTC/USDT', order)

    assert 'BTC/USDT' in risk_manager.take_profits
    assert risk_manager.take_profits['BTC/USDT'] > 40000


def test_check_stop_loss_hit(risk_manager):
    """Test stop loss checking."""
    order = Order(
        symbol='BTC/USDT',
        side='buy',
        order_type=OrderType.MARKET,
        amount=0.1,
        filled_price=40000
    )

    risk_manager.set_stop_loss('BTC/USDT', order)

    # Price below stop loss
    assert risk_manager.check_stop_loss('BTC/USDT', 39000, 'buy') is True

    # Price above stop loss
    assert risk_manager.check_stop_loss('BTC/USDT', 40500, 'buy') is False


def test_check_take_profit_hit(risk_manager):
    """Test take profit checking."""
    order = Order(
        symbol='BTC/USDT',
        side='buy',
        order_type=OrderType.MARKET,
        amount=0.1,
        filled_price=40000
    )

    risk_manager.set_take_profit('BTC/USDT', order)

    # Price above take profit
    assert risk_manager.check_take_profit('BTC/USDT', 42500, 'buy') is True

    # Price below take profit
    assert risk_manager.check_take_profit('BTC/USDT', 40500, 'buy') is False


def test_trailing_stop_update(risk_manager):
    """Test trailing stop updates."""
    # Initialize trailing stop
    risk_manager.update_trailing_stop('BTC/USDT', 40000, 'buy')
    initial_stop = risk_manager.trailing_stops['BTC/USDT']

    # Price moves up, trailing stop should move up
    risk_manager.update_trailing_stop('BTC/USDT', 41000, 'buy')
    new_stop = risk_manager.trailing_stops['BTC/USDT']

    assert new_stop > initial_stop

    # Price moves down, trailing stop should not move
    risk_manager.update_trailing_stop('BTC/USDT', 40500, 'buy')
    assert risk_manager.trailing_stops['BTC/USDT'] == new_stop


def test_update_pnl(risk_manager):
    """Test P&L updates."""
    risk_manager.update_pnl(500)
    assert risk_manager.daily_pnl == 500
    assert risk_manager.current_capital == 10500

    risk_manager.update_pnl(-200)
    assert risk_manager.daily_pnl == 300
    assert risk_manager.current_capital == 10300


def test_daily_loss_limit(risk_manager):
    """Test daily loss limit."""
    # Simulate large loss
    loss = -600  # 6% loss (exceeds 5% limit)
    risk_manager.update_pnl(loss)

    signal = Signal(SignalType.BUY, 'BTC/USDT', 40000)

    # Mock order manager
    class MockOrderManager:
        def get_all_positions(self):
            return {}

    order_manager = MockOrderManager()

    # Validation should fail due to daily loss
    is_valid, reason = risk_manager.validate_trade(signal, order_manager, 10000)

    assert is_valid is False
    assert 'daily loss' in reason.lower()


def test_reset_daily_pnl(risk_manager):
    """Test resetting daily P&L."""
    risk_manager.update_pnl(-500)
    risk_manager.stop_trading = True

    risk_manager.reset_daily_pnl()

    assert risk_manager.daily_pnl == 0
    assert risk_manager.stop_trading is False


def test_clear_position_risk(risk_manager):
    """Test clearing position risk parameters."""
    order = Order(
        symbol='BTC/USDT',
        side='buy',
        order_type=OrderType.MARKET,
        amount=0.1,
        filled_price=40000
    )

    risk_manager.set_stop_loss('BTC/USDT', order)
    risk_manager.set_take_profit('BTC/USDT', order)

    assert 'BTC/USDT' in risk_manager.stop_losses
    assert 'BTC/USDT' in risk_manager.take_profits

    risk_manager.clear_position_risk('BTC/USDT')

    assert 'BTC/USDT' not in risk_manager.stop_losses
    assert 'BTC/USDT' not in risk_manager.take_profits


def test_risk_summary(risk_manager):
    """Test risk summary generation."""
    risk_manager.update_pnl(250)

    summary = risk_manager.get_risk_summary()

    assert summary['initial_capital'] == 10000
    assert summary['current_capital'] == 10250
    assert summary['daily_pnl'] == 250
    assert summary['daily_pnl_percent'] == 2.5
    assert summary['stop_trading'] is False
