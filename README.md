# Sistema de Trading de Criptomoedas

Sistema automatizado de trading de criptomoedas em Python, com suporte para múltiplas exchanges, estratégias customizáveis e gerenciamento avançado de risco.

## 🚀 Características

- **Múltiplas Exchanges**: Suporte para Binance, Coinbase e outras via CCXT
- **Estratégias de Trading**: Implementação de estratégias técnicas (MA Crossover, RSI, MACD)
- **Gerenciamento de Risco**: Stop-loss, take-profit, trailing stop e controle de posição
- **Coleta de Dados**: Dados históricos e em tempo real
- **Logging Avançado**: Sistema completo de logs e monitoramento
- **Backtesting**: Teste suas estratégias com dados históricos
- **Configuração Flexível**: Arquivo YAML para todas as configurações

## 📁 Estrutura do Projeto

```
crypto_trading/
├── crypto_trading/
│   ├── core/
│   │   ├── exchange_connector.py    # Conexão com exchanges
│   │   ├── market_data.py           # Coleta de dados
│   │   ├── order_manager.py         # Gerenciamento de ordens
│   │   └── risk_manager.py          # Gerenciamento de risco
│   ├── strategies/
│   │   ├── base_strategy.py         # Classe base para estratégias
│   │   └── moving_average.py        # Estratégia MA Crossover
│   └── utils/
│       ├── logger.py                # Sistema de logging
│       └── config_loader.py         # Carregador de configuração
├── config/
│   └── config.yaml                  # Arquivo de configuração
├── tests/                           # Testes unitários
├── logs/                            # Arquivos de log
├── data/                            # Dados históricos
├── main.py                          # Ponto de entrada
├── requirements.txt                 # Dependências
├── .env.example                     # Exemplo de variáveis de ambiente
└── README.md                        # Este arquivo
```

## 🛠️ Instalação

### 1. Clone o Repositório

```bash
git clone <repository_url>
cd crypto_trading
```

### 2. Crie um Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
BINANCE_API_KEY=sua_api_key
BINANCE_API_SECRET=seu_api_secret
TRADING_MODE=testnet
```

### 5. Configure o Sistema

Edite `config/config.yaml` conforme suas necessidades:

```yaml
exchange:
  name: binance
  testnet: true

trading:
  pairs:
    - BTC/USDT
    - ETH/USDT
  timeframe: 1h

strategy:
  name: moving_average_crossover
  parameters:
    fast_period: 10
    slow_period: 30
    rsi_period: 14

risk:
  max_position_size_percent: 10
  stop_loss_percent: 2.0
  take_profit_percent: 5.0
```

## 🚦 Como Usar

### Modo Básico

```bash
python main.py
```

### Modo Testnet (Recomendado para Iniciantes)

Certifique-se de que no `config/config.yaml`:

```yaml
exchange:
  testnet: true
```

### Modo Live (Produção)

⚠️ **ATENÇÃO**: Use apenas quando tiver testado completamente no testnet!

```yaml
exchange:
  testnet: false
```

## 📊 Estratégias Disponíveis

### Moving Average Crossover

Estratégia baseada no cruzamento de médias móveis com filtro RSI:

- **Sinal de COMPRA**: MA rápida cruza acima da MA lenta + RSI < 70
- **Sinal de VENDA**: MA rápida cruza abaixo da MA lenta + RSI > 30

Parâmetros configuráveis:
- `fast_period`: Período da média móvel rápida (padrão: 10)
- `slow_period`: Período da média móvel lenta (padrão: 30)
- `rsi_period`: Período do RSI (padrão: 14)

## 🛡️ Gerenciamento de Risco

O sistema inclui múltiplas camadas de proteção:

### Stop Loss
- Stop loss fixo por posição
- Stop loss trailing (acompanha o preço)

### Take Profit
- Níveis automáticos de realização de lucro

### Controle de Posição
- Tamanho máximo por posição
- Número máximo de posições abertas
- Limite de perda diária

### Configuração de Risco

```yaml
risk:
  max_position_size_percent: 10    # Máximo 10% do capital por posição
  stop_loss_percent: 2.0           # Stop loss de 2%
  take_profit_percent: 5.0         # Take profit de 5%
  max_daily_loss_percent: 5.0      # Para trading se perder 5% no dia
  trailing_stop: true              # Ativa trailing stop
  trailing_stop_percent: 1.5       # 1.5% de trailing stop
```

## 📈 Monitoramento

### Logs

Os logs são salvos em `logs/trading.log` e exibidos no console com cores:

```
2024-11-04 10:30:15 | INFO     | Moving Average Crossover: BUY signal for BTC/USDT at 42500.00
2024-11-04 10:30:16 | INFO     | Order executed: buy 0.023529 BTC/USDT
2024-11-04 10:30:16 | INFO     | Stop loss set for BTC/USDT at 41650.00
```

### Níveis de Log

- `DEBUG`: Informações detalhadas para debugging
- `INFO`: Informações gerais sobre operações
- `WARNING`: Avisos importantes
- `ERROR`: Erros que não param a execução
- `CRITICAL`: Erros críticos

Configure em `config/config.yaml`:

```yaml
logging:
  level: INFO
  file: logs/trading.log
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/

# Executar com cobertura
pytest --cov=crypto_trading tests/

# Executar testes específicos
pytest tests/test_strategies.py
```

## 📚 Exemplos de Uso

### Exemplo 1: Bot Simples

```python
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.strategies.moving_average import MovingAverageCrossover
from crypto_trading.core.market_data import MarketData

# Inicializar componentes
exchange = ExchangeConnector('binance', testnet=True)
market_data = MarketData(exchange)
strategy = MovingAverageCrossover()

# Coletar dados
df = market_data.fetch_historical_data('BTC/USDT', '1h', days=30)

# Gerar sinal
signal = strategy.generate_signal(df, 'BTC/USDT')
print(f"Signal: {signal}")
```

### Exemplo 2: Análise de Múltiplos Pares

```python
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

for symbol in symbols:
    df = market_data.fetch_historical_data(symbol, '1h', days=7)
    signal = strategy.generate_signal(df, symbol)
    trend = strategy.get_trend(df)
    print(f"{symbol}: {signal.signal_type.value} (Trend: {trend})")
```

## 🔧 Desenvolvimento

### Criar Nova Estratégia

1. Crie um novo arquivo em `crypto_trading/strategies/`
2. Herde de `BaseStrategy`
3. Implemente os métodos abstratos:

```python
from crypto_trading.strategies.base_strategy import BaseStrategy, Signal, SignalType

class MinhaEstrategia(BaseStrategy):
    def calculate_indicators(self, df):
        # Calcular indicadores técnicos
        return df

    def generate_signal(self, df, symbol):
        # Gerar sinal de trading
        return Signal(SignalType.HOLD, symbol, df['close'].iloc[-1])
```

### Adicionar Nova Exchange

O sistema usa CCXT, que suporta 100+ exchanges. Basta configurar:

```yaml
exchange:
  name: coinbase  # ou kraken, bitfinex, etc.
```

## ⚠️ Avisos Importantes

1. **Testnet Primeiro**: Sempre teste no testnet antes de usar dinheiro real
2. **Gerenciamento de Risco**: Nunca arrisque mais do que pode perder
3. **API Keys**: Mantenha suas chaves seguras, nunca commite no git
4. **Monitoramento**: Monitore o bot regularmente
5. **Responsabilidade**: Use por sua conta e risco

## 🐛 Troubleshooting

### Erro de Conexão

```
Failed to initialize exchange: binance
```

**Solução**: Verifique suas credenciais no arquivo `.env`

### Dados Insuficientes

```
WARNING: Insufficient data for BTC/USDT
```

**Solução**: Aumente `historical_days` em `config/config.yaml`

### Rate Limit

```
ERROR: Rate limit exceeded
```

**Solução**: Aumente `update_interval` ou ative rate limiting:

```yaml
exchange:
  rate_limit: true
```

## 📝 TODO

- [ ] Adicionar mais estratégias (Bollinger Bands, MACD, etc.)
- [ ] Implementar backtesting completo
- [ ] Interface web para monitoramento
- [ ] Notificações (Telegram, Email)
- [ ] Suporte a trading de futuros
- [ ] Machine Learning para otimização

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 💡 Suporte

Para dúvidas, problemas ou sugestões:

- Abra uma issue no GitHub
- Email: seu_email@example.com

## 🙏 Agradecimentos

- [CCXT](https://github.com/ccxt/ccxt) - Biblioteca de exchange
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Indicadores técnicos
- [Loguru](https://github.com/Delgan/loguru) - Sistema de logging

---

**Disclaimer**: Este software é fornecido "como está", sem garantias. Trading de criptomoedas envolve riscos significativos. Nunca invista mais do que pode perder.
