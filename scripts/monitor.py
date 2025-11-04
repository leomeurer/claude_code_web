#!/usr/bin/env python3
"""
Monitor em tempo real para o sistema de trading.
Exibe preços, saldo e ordens abertas.
"""
import time
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData
from crypto_trading.utils.config_loader import ConfigLoader


def clear_screen():
    """Limpa a tela."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def monitor():
    """Executa o monitor."""
    print("Inicializando monitor...")

    # Carregar configuração
    config = ConfigLoader("config/config.yaml")

    # Conectar à exchange
    exchange_name = config.get('exchange.name', 'binance')
    testnet = config.get('exchange.testnet', True)
    exchange = ExchangeConnector(exchange_name, testnet)

    # Inicializar market data
    market_data = MarketData(exchange)

    # Pares para monitorar
    symbols = config.get('trading.pairs', ['BTC/USDT'])

    print(f"Monitorando {len(symbols)} pares...")
    print("Pressione Ctrl+C para sair\n")
    time.sleep(2)

    try:
        while True:
            clear_screen()

            print("="*70)
            print(f"📊 MONITOR DE TRADING - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)

            # Modo
            mode = "🧪 TESTNET" if testnet else "🔴 LIVE"
            print(f"\nModo: {mode}")

            # Saldo
            try:
                balance = exchange.get_balance()
                print("\n💰 SALDO:")
                print("-"*70)

                # Mostrar principais moedas
                for currency in ['USDT', 'BTC', 'ETH', 'BNB']:
                    free = float(balance['free'].get(currency, 0))
                    total = float(balance['total'].get(currency, 0))

                    if total > 0:
                        locked = total - free
                        print(f"  {currency:6s} | Livre: {free:12.6f} | Bloqueado: {locked:12.6f} | Total: {total:12.6f}")

            except Exception as e:
                print(f"  ❌ Erro ao obter saldo: {e}")

            # Preços atuais
            print("\n📈 PREÇOS ATUAIS:")
            print("-"*70)

            for symbol in symbols:
                try:
                    ticker = exchange.get_ticker(symbol)
                    price = float(ticker['last'])
                    change_24h = float(ticker.get('percentage', 0))
                    volume_24h = float(ticker.get('quoteVolume', 0))

                    # Emoji baseado na mudança
                    emoji = "🟢" if change_24h >= 0 else "🔴"

                    print(f"  {emoji} {symbol:12s} | Preço: ${price:12,.2f} | "
                          f"24h: {change_24h:6.2f}% | Volume: ${volume_24h:15,.0f}")

                except Exception as e:
                    print(f"  ❌ {symbol:12s} | Erro: {e}")

            # Ordens abertas
            print("\n📋 ORDENS ABERTAS:")
            print("-"*70)

            try:
                open_orders = exchange.get_open_orders()

                if open_orders:
                    for order in open_orders:
                        symbol = order['symbol']
                        side = order['side']
                        order_type = order['type']
                        amount = float(order['amount'])
                        price = float(order.get('price', 0))

                        emoji = "🟢" if side == 'buy' else "🔴"
                        print(f"  {emoji} {symbol:12s} | {side.upper():4s} {order_type:8s} | "
                              f"Qtd: {amount:10.6f} | Preço: ${price:10,.2f}")
                else:
                    print("  📭 Nenhuma ordem aberta")

            except Exception as e:
                print(f"  ❌ Erro ao obter ordens: {e}")

            # Rodapé
            print("\n" + "="*70)
            print("Atualizando a cada 30 segundos... (Ctrl+C para sair)")

            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n👋 Monitor encerrado.")
        exchange.close()


if __name__ == "__main__":
    monitor()
