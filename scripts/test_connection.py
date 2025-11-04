#!/usr/bin/env python3
"""
Testa a conexão com a exchange e valida a configuração.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData
from crypto_trading.strategies.moving_average import MovingAverageCrossover
from crypto_trading.utils.config_loader import ConfigLoader


def print_section(title):
    """Imprime cabeçalho de seção."""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)


def test_connection():
    """Testa a conexão e configuração."""

    print("\n" + "🚀 TESTE DE CONEXÃO E CONFIGURAÇÃO" + "\n")

    # 1. Testar configuração
    print_section("1. Testando Configuração")

    try:
        config = ConfigLoader("config/config.yaml")
        print("✅ Arquivo config.yaml carregado com sucesso")

        exchange_name = config.get('exchange.name')
        testnet = config.get('exchange.testnet')
        pairs = config.get('trading.pairs')

        print(f"   Exchange: {exchange_name}")
        print(f"   Modo: {'TESTNET' if testnet else 'LIVE'}")
        print(f"   Pares: {', '.join(pairs)}")

    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return False

    # 2. Testar conexão com exchange
    print_section("2. Testando Conexão com Exchange")

    try:
        exchange = ExchangeConnector(exchange_name, testnet)
        print(f"✅ Conectado à {exchange_name}")
        print(f"   Markets disponíveis: {len(exchange.exchange.markets)}")

    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("\n💡 Dicas:")
        print("   1. Verifique se suas API keys estão corretas no arquivo .env")
        print("   2. Se usando testnet, certifique-se de usar keys do testnet")
        print("   3. Verifique sua conexão com a internet")
        return False

    # 3. Testar obtenção de saldo
    print_section("3. Testando Acesso ao Saldo")

    try:
        balance = exchange.get_balance()
        print("✅ Saldo obtido com sucesso")

        # Mostrar principais moedas
        for currency in ['USDT', 'BTC', 'ETH']:
            total = float(balance['total'].get(currency, 0))
            if total > 0:
                print(f"   {currency}: {total:.6f}")

    except Exception as e:
        print(f"❌ Erro ao obter saldo: {e}")
        print("\n💡 Dicas:")
        print("   1. Verifique as permissões da sua API key")
        print("   2. Certifique-se de que 'Enable Reading' está ativado")
        return False

    # 4. Testar coleta de dados
    print_section("4. Testando Coleta de Dados")

    try:
        market_data = MarketData(exchange)
        symbol = pairs[0]

        print(f"   Testando com {symbol}...")

        # Testar ticker
        ticker = exchange.get_ticker(symbol)
        price = float(ticker['last'])
        print(f"   ✅ Ticker: ${price:,.2f}")

        # Testar OHLCV
        df = market_data.fetch_historical_data(symbol, '1h', days=1)
        print(f"   ✅ Dados históricos: {len(df)} candles")

        # Testar orderbook
        orderbook = exchange.get_orderbook(symbol, limit=5)
        print(f"   ✅ Orderbook: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")

    except Exception as e:
        print(f"❌ Erro ao coletar dados: {e}")
        return False

    # 5. Testar estratégia
    print_section("5. Testando Estratégia")

    try:
        strategy_params = config.get('strategy.parameters', {})
        strategy = MovingAverageCrossover(strategy_params)

        print(f"   Estratégia: {strategy.name}")
        print(f"   Parâmetros: {strategy.parameters}")

        # Testar cálculo de indicadores
        df_with_indicators = strategy.calculate_indicators(df)
        print(f"   ✅ Indicadores calculados")

        # Testar geração de sinal
        signal = strategy.generate_signal(df_with_indicators, symbol)
        print(f"   ✅ Sinal gerado: {signal.signal_type.value}")
        print(f"   Preço: ${signal.price:,.2f}")
        print(f"   Força: {signal.strength:.2f}")

    except Exception as e:
        print(f"❌ Erro ao testar estratégia: {e}")
        return False

    # 6. Resumo final
    print_section("RESUMO")

    print("\n✅ Todos os testes passaram com sucesso!")
    print("\n📋 Próximos passos:")
    print("   1. Revise a configuração em config/config.yaml")
    print("   2. Ajuste os parâmetros de risco conforme necessário")
    print("   3. Execute o bot: python main.py")
    print("   4. Monitore os logs em: logs/trading.log")

    print("\n⚠️  IMPORTANTE:")
    if testnet:
        print("   Você está em modo TESTNET - seguro para testes!")
    else:
        print("   ⚠️  VOCÊ ESTÁ EM MODO LIVE - DINHEIRO REAL!")
        print("   Certifique-se de que sabe o que está fazendo!")

    print("\n" + "="*60 + "\n")

    # Fechar conexão
    exchange.close()

    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
