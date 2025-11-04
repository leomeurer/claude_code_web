#!/usr/bin/env python3
"""
Script simples de backtesting para testar estratégias com dados históricos.
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData
from crypto_trading.strategies.moving_average import MovingAverageCrossover
from crypto_trading.strategies.base_strategy import SignalType
from crypto_trading.utils.config_loader import ConfigLoader


class SimpleBacktester:
    """Backtester simples para avaliar estratégias."""

    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = None
        self.trades = []

    def run(self, df, strategy, symbol):
        """
        Executa backtest em dados históricos.

        Args:
            df: DataFrame com dados OHLCV
            strategy: Estratégia de trading
            symbol: Par de trading
        """
        print(f"\n🔄 Executando backtest para {symbol}")
        print(f"   Período: {df.index[0]} até {df.index[-1]}")
        print(f"   Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   Total de candles: {len(df)}\n")

        # Calcular indicadores
        df = strategy.calculate_indicators(df)

        # Iterar pelos dados
        for i in range(50, len(df)):  # Começar após período de aquecimento
            current_data = df.iloc[:i+1]
            current_row = df.iloc[i]
            current_price = current_row['close']

            # Gerar sinal
            signal = strategy.generate_signal(current_data, symbol)

            # Executar trades
            if signal.signal_type == SignalType.BUY and self.position is None:
                # Comprar
                position_size = (self.capital * 0.95) / current_price  # 95% do capital
                self.position = {
                    'entry_price': current_price,
                    'size': position_size,
                    'entry_date': current_row.name
                }
                print(f"🟢 COMPRA | {current_row.name.strftime('%Y-%m-%d %H:%M')} | "
                      f"${current_price:,.2f} | Qtd: {position_size:.6f}")

            elif signal.signal_type == SignalType.SELL and self.position is not None:
                # Vender
                exit_price = current_price
                pnl = (exit_price - self.position['entry_price']) * self.position['size']
                pnl_percent = ((exit_price / self.position['entry_price']) - 1) * 100

                self.capital += pnl

                trade = {
                    'entry_date': self.position['entry_date'],
                    'exit_date': current_row.name,
                    'entry_price': self.position['entry_price'],
                    'exit_price': exit_price,
                    'size': self.position['size'],
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                }
                self.trades.append(trade)

                emoji = "✅" if pnl > 0 else "❌"
                print(f"{emoji} VENDA | {current_row.name.strftime('%Y-%m-%d %H:%M')} | "
                      f"${exit_price:,.2f} | P&L: ${pnl:,.2f} ({pnl_percent:+.2f}%)")

                self.position = None

        # Fechar posição aberta (se houver)
        if self.position is not None:
            final_price = df.iloc[-1]['close']
            pnl = (final_price - self.position['entry_price']) * self.position['size']
            self.capital += pnl
            print(f"\n⚠️  Posição fechada ao final do período em ${final_price:,.2f}")

        # Exibir resultados
        self.print_results()

    def print_results(self):
        """Exibe resultados do backtest."""
        print("\n" + "="*70)
        print("📊 RESULTADOS DO BACKTEST")
        print("="*70)

        if not self.trades:
            print("\n❌ Nenhum trade executado no período")
            return

        # Estatísticas gerais
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = len([t for t in self.trades if t['pnl'] <= 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in self.trades)
        total_return = ((self.capital / self.initial_capital) - 1) * 100

        avg_win = sum(t['pnl'] for t in self.trades if t['pnl'] > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t['pnl'] for t in self.trades if t['pnl'] <= 0) / losing_trades if losing_trades > 0 else 0

        # Maior ganho e perda
        best_trade = max(self.trades, key=lambda x: x['pnl'])
        worst_trade = min(self.trades, key=lambda x: x['pnl'])

        print(f"\n💼 PERFORMANCE:")
        print(f"   Capital inicial:  ${self.initial_capital:12,.2f}")
        print(f"   Capital final:    ${self.capital:12,.2f}")
        print(f"   Retorno total:    ${total_pnl:12,.2f} ({total_return:+.2f}%)")

        print(f"\n📈 ESTATÍSTICAS:")
        print(f"   Total de trades:  {total_trades}")
        print(f"   Trades vencedores: {winning_trades} ({win_rate:.1f}%)")
        print(f"   Trades perdedores: {losing_trades} ({100-win_rate:.1f}%)")
        print(f"   Média de ganho:   ${avg_win:,.2f}")
        print(f"   Média de perda:   ${avg_loss:,.2f}")

        if avg_loss != 0:
            profit_factor = abs(avg_win / avg_loss)
            print(f"   Profit Factor:    {profit_factor:.2f}")

        print(f"\n🏆 MELHOR TRADE:")
        print(f"   P&L: ${best_trade['pnl']:,.2f} ({best_trade['pnl_percent']:+.2f}%)")
        print(f"   Entrada: ${best_trade['entry_price']:,.2f} → Saída: ${best_trade['exit_price']:,.2f}")

        print(f"\n📉 PIOR TRADE:")
        print(f"   P&L: ${worst_trade['pnl']:,.2f} ({worst_trade['pnl_percent']:+.2f}%)")
        print(f"   Entrada: ${worst_trade['entry_price']:,.2f} → Saída: ${worst_trade['exit_price']:,.2f}")

        print("\n" + "="*70 + "\n")


def main():
    """Função principal."""
    print("\n" + "="*70)
    print("🔬 BACKTESTING - Sistema de Trading de Criptomoedas")
    print("="*70)

    # Carregar configuração
    config = ConfigLoader("config/config.yaml")

    # Parâmetros
    exchange_name = config.get('exchange.name', 'binance')
    testnet = config.get('exchange.testnet', True)
    symbol = config.get('trading.pairs', ['BTC/USDT'])[0]
    timeframe = config.get('trading.timeframe', '1h')
    days = 90  # 3 meses de dados
    initial_capital = 10000

    print(f"\n⚙️  CONFIGURAÇÃO:")
    print(f"   Par: {symbol}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Período: {days} dias")
    print(f"   Capital: ${initial_capital:,.2f}")

    # Conectar e coletar dados
    print(f"\n📡 Conectando à {exchange_name}...")
    exchange = ExchangeConnector(exchange_name, testnet)
    market_data = MarketData(exchange)

    print(f"📊 Coletando dados históricos...")
    df = market_data.fetch_historical_data(symbol, timeframe, days)

    # Inicializar estratégia
    strategy_params = config.get('strategy.parameters', {})
    strategy = MovingAverageCrossover(strategy_params)

    print(f"🎯 Estratégia: {strategy.name}")
    print(f"   Parâmetros: {strategy.parameters}")

    # Executar backtest
    backtester = SimpleBacktester(initial_capital)
    backtester.run(df, strategy, symbol)

    # Fechar conexão
    exchange.close()


if __name__ == "__main__":
    main()
