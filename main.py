"""
Main trading bot entry point.
"""
import time
import asyncio
from pathlib import Path
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData
from crypto_trading.core.order_manager import OrderManager, OrderType
from crypto_trading.core.risk_manager import RiskManager, RiskParameters
from crypto_trading.strategies.moving_average import MovingAverageCrossover
from crypto_trading.strategies.base_strategy import SignalType
from crypto_trading.utils.config_loader import ConfigLoader
from crypto_trading.utils.logger import get_logger


class TradingBot:
    """Main trading bot class."""

    def __init__(self, config_file: str = "config/config.yaml"):
        """
        Initialize trading bot.

        Args:
            config_file: Path to configuration file
        """
        # Load configuration
        self.config = ConfigLoader(config_file)

        # Initialize logger
        log_file = self.config.get('logging.file', 'logs/trading.log')
        log_level = self.config.get('logging.level', 'INFO')
        self.logger = get_logger(log_file, log_level)

        self.logger.info("=" * 60)
        self.logger.info("Initializing Crypto Trading Bot")
        self.logger.info("=" * 60)

        # Initialize exchange connector
        exchange_name = self.config.get('exchange.name', 'binance')
        testnet = self.config.get('exchange.testnet', True)
        self.exchange = ExchangeConnector(exchange_name, testnet)

        # Initialize market data
        self.market_data = MarketData(self.exchange)

        # Initialize order manager
        self.order_manager = OrderManager(self.exchange)

        # Initialize risk manager
        initial_capital = self.config.get('portfolio.initial_capital', 10000)
        risk_params = RiskParameters(
            max_position_size_percent=self.config.get('risk.max_position_size_percent', 10),
            stop_loss_percent=self.config.get('risk.stop_loss_percent', 2.0),
            take_profit_percent=self.config.get('risk.take_profit_percent', 5.0),
            max_daily_loss_percent=self.config.get('risk.max_daily_loss_percent', 5.0),
            trailing_stop=self.config.get('risk.trailing_stop', True),
            trailing_stop_percent=self.config.get('risk.trailing_stop_percent', 1.5)
        )
        self.risk_manager = RiskManager(initial_capital, risk_params)

        # Initialize strategy
        strategy_params = self.config.get('strategy.parameters', {})
        self.strategy = MovingAverageCrossover(strategy_params)

        # Trading settings
        self.trading_pairs = self.config.get('trading.pairs', ['BTC/USDT'])
        self.timeframe = self.config.get('trading.timeframe', '1h')
        self.update_interval = self.config.get('data.update_interval', 60)

        self.running = False

        self.logger.info(f"Trading pairs: {self.trading_pairs}")
        self.logger.info(f"Timeframe: {self.timeframe}")
        self.logger.info(f"Strategy: {self.strategy.name}")
        self.logger.info(f"Initial capital: ${initial_capital:.2f}")

    def fetch_initial_data(self):
        """Fetch initial historical data for all trading pairs."""
        self.logger.info("Fetching initial historical data...")

        historical_days = self.config.get('data.historical_days', 30)

        for symbol in self.trading_pairs:
            try:
                self.logger.info(f"Fetching data for {symbol}...")
                df = self.market_data.fetch_historical_data(
                    symbol,
                    self.timeframe,
                    historical_days
                )
                self.logger.info(f"Fetched {len(df)} candles for {symbol}")

                # Save to file if configured
                if self.config.get('data.save_to_file', False):
                    data_dir = Path(self.config.get('data.data_directory', 'data'))
                    data_dir.mkdir(exist_ok=True)
                    filepath = data_dir / f"{symbol.replace('/', '_')}_{self.timeframe}.csv"
                    self.market_data.save_data(symbol, self.timeframe, str(filepath))

            except Exception as e:
                self.logger.error(f"Failed to fetch data for {symbol}: {e}")

    def process_symbol(self, symbol: str):
        """
        Process trading logic for a symbol.

        Args:
            symbol: Trading pair symbol
        """
        try:
            # Update market data
            df = self.market_data.update_data(symbol, self.timeframe)

            if df is None or len(df) < 50:
                self.logger.warning(f"Insufficient data for {symbol}")
                return

            # Generate signal
            signal = self.strategy.generate_signal(df, symbol)

            # Get current price
            current_price = self.market_data.get_current_price(symbol)

            # Check existing position
            position = self.order_manager.get_position(symbol)

            # Update trailing stop if position exists
            if position and position['amount'] > 0:
                self.risk_manager.update_trailing_stop(symbol, current_price, 'buy')

                # Check stop loss
                if self.risk_manager.check_stop_loss(symbol, current_price, 'buy'):
                    self.logger.warning(f"Stop loss triggered for {symbol}")
                    amount = position['amount']
                    # Create sell signal
                    from crypto_trading.strategies.base_strategy import Signal
                    sell_signal = Signal(SignalType.SELL, symbol, current_price, 1.0)
                    order = self.order_manager.execute_signal(sell_signal, amount, OrderType.MARKET)

                    if order:
                        pnl_info = self.order_manager.calculate_pnl(symbol, current_price)
                        self.risk_manager.update_pnl(pnl_info['realized_pnl'])
                        self.risk_manager.clear_position_risk(symbol)
                    return

                # Check take profit
                if self.risk_manager.check_take_profit(symbol, current_price, 'buy'):
                    self.logger.info(f"Take profit triggered for {symbol}")
                    amount = position['amount']
                    # Create sell signal
                    from crypto_trading.strategies.base_strategy import Signal
                    sell_signal = Signal(SignalType.SELL, symbol, current_price, 1.0)
                    order = self.order_manager.execute_signal(sell_signal, amount, OrderType.MARKET)

                    if order:
                        pnl_info = self.order_manager.calculate_pnl(symbol, current_price)
                        self.risk_manager.update_pnl(pnl_info['realized_pnl'])
                        self.risk_manager.clear_position_risk(symbol)
                    return

            # Process new signals
            if signal.signal_type != SignalType.HOLD:
                # Get current balance
                balance = self.exchange.get_balance()
                quote_currency = symbol.split('/')[1]
                available_balance = float(balance.get('free', {}).get(quote_currency, 0))

                # Validate trade
                is_valid, reason = self.risk_manager.validate_trade(
                    signal,
                    self.order_manager,
                    available_balance
                )

                if not is_valid:
                    self.logger.debug(f"Trade validation failed for {symbol}: {reason}")
                    return

                # Calculate position size
                if signal.signal_type == SignalType.BUY:
                    amount = self.risk_manager.calculate_position_size(
                        signal,
                        available_balance,
                        current_price
                    )
                else:  # SELL
                    amount = position['amount'] if position else 0

                if amount > 0:
                    # Execute order
                    order = self.order_manager.execute_signal(signal, amount, OrderType.MARKET)

                    if order:
                        # Set stop loss and take profit for buy orders
                        if signal.signal_type == SignalType.BUY:
                            self.risk_manager.set_stop_loss(symbol, order)
                            self.risk_manager.set_take_profit(symbol, order)
                        else:
                            # Update PnL for sell orders
                            pnl_info = self.order_manager.calculate_pnl(symbol, current_price)
                            self.risk_manager.update_pnl(pnl_info['realized_pnl'])
                            self.risk_manager.clear_position_risk(symbol)

        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}")

    def run_iteration(self):
        """Run one iteration of the trading loop."""
        self.logger.info("-" * 60)
        self.logger.info("Running trading iteration...")

        for symbol in self.trading_pairs:
            self.process_symbol(symbol)

        # Log summary
        self.log_summary()

    def log_summary(self):
        """Log trading summary."""
        self.logger.info("-" * 60)

        # Risk summary
        risk_summary = self.risk_manager.get_risk_summary()
        self.logger.info(f"Capital: ${risk_summary['current_capital']:.2f}")
        self.logger.info(f"Daily P&L: ${risk_summary['daily_pnl']:.2f} ({risk_summary['daily_pnl_percent']:.2f}%)")

        # Position summary
        positions = self.order_manager.get_all_positions()
        if positions:
            self.logger.info("Open Positions:")
            for symbol, position in positions.items():
                if position['amount'] > 0:
                    current_price = self.market_data.get_current_price(symbol)
                    pnl_info = self.order_manager.calculate_pnl(symbol, current_price)
                    self.logger.info(
                        f"  {symbol}: {position['amount']:.6f} @ ${position['avg_price']:.2f} "
                        f"(P&L: ${pnl_info['unrealized_pnl']:.2f})"
                    )

    def run(self):
        """Run the trading bot."""
        try:
            self.running = True

            # Fetch initial data
            self.fetch_initial_data()

            self.logger.info("Starting trading loop...")
            self.logger.info(f"Update interval: {self.update_interval} seconds")

            while self.running:
                try:
                    self.run_iteration()

                    # Sleep until next iteration
                    time.sleep(self.update_interval)

                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal, stopping...")
                    self.running = False
                    break

                except Exception as e:
                    self.logger.error(f"Error in trading loop: {e}")
                    time.sleep(self.update_interval)

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise

        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        self.logger.info("=" * 60)
        self.logger.info("Shutting down trading bot...")

        # Log final summary
        self.log_summary()

        # Close exchange connection
        self.exchange.close()

        self.logger.info("Trading bot stopped")
        self.logger.info("=" * 60)


def main():
    """Main entry point."""
    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    main()
