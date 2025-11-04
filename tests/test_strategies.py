"""
Unit tests for trading strategies.
"""
import pytest
import pandas as pd
import numpy as np
from crypto_trading.strategies.moving_average import MovingAverageCrossover
from crypto_trading.strategies.base_strategy import SignalType


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)

    # Generate realistic price data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    base_price = 40000

    # Simulate price movement
    returns = np.random.normal(0, 0.02, 100)
    prices = base_price * (1 + returns).cumprod()

    df = pd.DataFrame({
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 100)
    }, index=dates)

    return df


@pytest.fixture
def strategy():
    """Create strategy instance."""
    return MovingAverageCrossover({
        'fast_period': 5,
        'slow_period': 10,
        'rsi_period': 14
    })


def test_strategy_initialization(strategy):
    """Test strategy initialization."""
    assert strategy.name == "Moving Average Crossover"
    assert strategy.get_parameter('fast_period') == 5
    assert strategy.get_parameter('slow_period') == 10


def test_calculate_indicators(strategy, sample_data):
    """Test indicator calculation."""
    df = strategy.calculate_indicators(sample_data)

    # Check that indicators were added
    assert 'ma_fast' in df.columns
    assert 'ma_slow' in df.columns
    assert 'rsi' in df.columns

    # Check that values are calculated
    assert not df['ma_fast'].iloc[-1:].isna().all()
    assert not df['ma_slow'].iloc[-1:].isna().all()
    assert not df['rsi'].iloc[-1:].isna().all()


def test_generate_signal(strategy, sample_data):
    """Test signal generation."""
    signal = strategy.generate_signal(sample_data, 'BTC/USDT')

    # Check signal properties
    assert signal.symbol == 'BTC/USDT'
    assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
    assert signal.price > 0
    assert 0 <= signal.strength <= 1


def test_signal_with_uptrend():
    """Test signal generation in uptrend."""
    # Create data with clear uptrend
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    prices = np.linspace(40000, 45000, 50)

    df = pd.DataFrame({
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': [1000] * 50
    }, index=dates)

    strategy = MovingAverageCrossover({
        'fast_period': 5,
        'slow_period': 10
    })

    df = strategy.calculate_indicators(df)
    trend = strategy.get_trend(df)

    assert trend == 'uptrend'


def test_signal_with_downtrend():
    """Test signal generation in downtrend."""
    # Create data with clear downtrend
    dates = pd.date_range(start='2024-01-01', periods=50, freq='1H')
    prices = np.linspace(45000, 40000, 50)

    df = pd.DataFrame({
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': [1000] * 50
    }, index=dates)

    strategy = MovingAverageCrossover({
        'fast_period': 5,
        'slow_period': 10
    })

    df = strategy.calculate_indicators(df)
    trend = strategy.get_trend(df)

    assert trend == 'downtrend'


def test_validate_data(strategy):
    """Test data validation."""
    # Valid data
    df = pd.DataFrame({
        'close': [100, 101, 102],
        'volume': [1000, 1100, 1200]
    })

    assert strategy.validate_data(df, ['close', 'volume']) is True

    # Missing columns
    assert strategy.validate_data(df, ['close', 'open']) is False

    # Empty dataframe
    empty_df = pd.DataFrame()
    assert strategy.validate_data(empty_df, ['close']) is False


def test_parameter_management(strategy):
    """Test parameter get/set."""
    # Get existing parameter
    assert strategy.get_parameter('fast_period') == 5

    # Get non-existing parameter with default
    assert strategy.get_parameter('non_existing', 42) == 42

    # Set parameter
    strategy.set_parameter('fast_period', 15)
    assert strategy.get_parameter('fast_period') == 15


def test_signal_metadata(strategy, sample_data):
    """Test that signal includes metadata."""
    signal = strategy.generate_signal(sample_data, 'BTC/USDT')

    assert signal.metadata is not None
    assert 'rsi' in signal.metadata
    assert signal.timestamp is not None


def test_insufficient_data(strategy):
    """Test handling of insufficient data."""
    # Create very small dataset
    df = pd.DataFrame({
        'close': [100],
        'open': [99],
        'high': [101],
        'low': [98],
        'volume': [1000]
    })

    signal = strategy.generate_signal(df, 'BTC/USDT')

    # Should return HOLD signal with insufficient data
    assert signal.signal_type == SignalType.HOLD
