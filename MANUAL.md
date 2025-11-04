# 📚 Manual de Uso - Sistema de Trading de Criptomoedas

## Índice

1. [Instalação](#instalação)
2. [Configuração Inicial](#configuração-inicial)
3. [Configuração das Exchanges](#configuração-das-exchanges)
4. [Configuração de Estratégias](#configuração-de-estratégias)
5. [Executando o Sistema](#executando-o-sistema)
6. [Monitoramento](#monitoramento)
7. [Gerenciamento de Risco](#gerenciamento-de-risco)
8. [Personalização](#personalização)
9. [Troubleshooting](#troubleshooting)
10. [Boas Práticas](#boas-práticas)

---

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Conta em uma exchange de criptomoedas (Binance recomendado)
- API Keys da exchange

### Passo 1: Clone o Repositório

```bash
git clone <repository_url>
cd crypto_trading
```

### Passo 2: Crie um Ambiente Virtual

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Passo 3: Instale as Dependências

```bash
pip install -r requirements.txt
```

**Tempo estimado:** 2-5 minutos

### Passo 4: Verifique a Instalação

```bash
python -c "import ccxt, pandas, pandas_ta; print('Instalação OK!')"
```

Se aparecer "Instalação OK!", está tudo pronto!

---

## Configuração Inicial

### 1. Configure as Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
nano .env  # ou use seu editor preferido
```

**Exemplo de .env configurado:**

```env
# API Keys da Binance
BINANCE_API_KEY=sua_api_key_aqui
BINANCE_API_SECRET=seu_api_secret_aqui

# Modo de operação
TRADING_MODE=testnet  # testnet ou live
EXCHANGE=binance

# Gerenciamento de Risco
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=5.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading.log
```

### 2. Configure o Sistema

Edite o arquivo `config/config.yaml`:

```bash
nano config/config.yaml
```

**Configuração básica recomendada para iniciantes:**

```yaml
# Exchange
exchange:
  name: binance
  testnet: true  # SEMPRE comece no testnet!
  sandbox: true
  rate_limit: true

# Pares de Trading
trading:
  pairs:
    - BTC/USDT    # Comece com apenas 1 ou 2 pares
  timeframe: 1h   # 1h é mais seguro para iniciantes

# Estratégia
strategy:
  name: moving_average_crossover
  parameters:
    fast_period: 10
    slow_period: 30
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30

# Risco (configuração conservadora)
risk:
  max_position_size_percent: 5   # Apenas 5% por operação
  stop_loss_percent: 2.0          # Stop loss de 2%
  take_profit_percent: 5.0        # Take profit de 5%
  max_daily_loss_percent: 5.0     # Para se perder 5% no dia
  trailing_stop: true
  trailing_stop_percent: 1.5

# Capital Inicial
portfolio:
  initial_capital: 1000  # Valor inicial no testnet
  reserve_percent: 10

# Logging
logging:
  level: INFO
  file: logs/trading.log
  console: true
```

---

## Configuração das Exchanges

### Binance (Recomendado)

#### 1. Criar Conta no Binance Testnet

1. Acesse: https://testnet.binance.vision/
2. Faça login com sua conta GitHub
3. Você receberá automaticamente fundos de teste (10.000 USDT)

#### 2. Obter API Keys do Testnet

1. No Binance Testnet, clique em "API Key"
2. Gere uma nova API Key
3. **IMPORTANTE:** Copie a API Key e Secret imediatamente
4. Cole no arquivo `.env`:

```env
BINANCE_API_KEY=sua_testnet_api_key
BINANCE_API_SECRET=sua_testnet_api_secret
```

#### 3. Configurar Permissões

No testnet, as permissões são automáticas. Para LIVE:

1. Acesse Binance.com → API Management
2. Habilite apenas:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ Enable Withdrawals (DESABILITE!)
3. Configure whitelist de IPs (recomendado)

### Outras Exchanges Suportadas

O sistema suporta 100+ exchanges via CCXT:

**Coinbase:**
```yaml
exchange:
  name: coinbase
  testnet: false
```

```env
COINBASE_API_KEY=sua_api_key
COINBASE_API_SECRET=seu_api_secret
```

**Kraken:**
```yaml
exchange:
  name: kraken
```

```env
KRAKEN_API_KEY=sua_api_key
KRAKEN_API_SECRET=seu_api_secret
```

---

## Configuração de Estratégias

### Estratégia 1: Moving Average Crossover (Padrão)

**Como funciona:**
- Compra quando a média móvel rápida cruza acima da lenta
- Vende quando a média móvel rápida cruza abaixo da lenta
- Usa RSI como filtro para evitar zonas de sobrecompra/sobrevenda

**Configuração Conservadora:**
```yaml
strategy:
  name: moving_average_crossover
  parameters:
    fast_period: 20    # Média mais lenta = menos sinais
    slow_period: 50
    rsi_period: 14
    rsi_overbought: 70
    rsi_oversold: 30
```

**Configuração Agressiva:**
```yaml
strategy:
  name: moving_average_crossover
  parameters:
    fast_period: 5     # Média mais rápida = mais sinais
    slow_period: 15
    rsi_period: 14
    rsi_overbought: 75
    rsi_oversold: 25
```

**Configuração para Day Trading:**
```yaml
trading:
  timeframe: 15m  # Timeframe menor

strategy:
  parameters:
    fast_period: 10
    slow_period: 20
```

**Configuração para Swing Trading:**
```yaml
trading:
  timeframe: 4h   # Timeframe maior

strategy:
  parameters:
    fast_period: 20
    slow_period: 50
```

### Entendendo os Parâmetros

**fast_period:**
- Valor pequeno (5-10): Mais sinais, mais ruído
- Valor médio (10-20): Balanceado
- Valor grande (20-50): Menos sinais, mais confiáveis

**slow_period:**
- Deve ser 2-3x maior que fast_period
- Quanto maior, mais conservador

**RSI:**
- Overbought > 70: Mercado sobrecomprado
- Oversold < 30: Mercado sobrevendido
- Valores mais extremos (80/20) = menos operações

---

## Executando o Sistema

### Teste Inicial (Dry Run)

Antes de executar, teste a configuração:

```bash
# Teste 1: Verificar conexão com exchange
python -c "
from crypto_trading.core.exchange_connector import ExchangeConnector
exchange = ExchangeConnector('binance', testnet=True)
print('Conexão OK!')
print(f'Markets disponíveis: {len(exchange.exchange.markets)}')
"

# Teste 2: Verificar coleta de dados
python -c "
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData

exchange = ExchangeConnector('binance', testnet=True)
market_data = MarketData(exchange)
df = market_data.fetch_historical_data('BTC/USDT', '1h', days=1)
print(f'Dados coletados: {len(df)} candles')
print(f'Último preço: {df[\"close\"].iloc[-1]:.2f}')
"
```

### Executar o Bot

**Modo Normal:**
```bash
python main.py
```

**Modo com Log Detalhado:**
```bash
# Edite config.yaml primeiro:
# logging:
#   level: DEBUG

python main.py
```

**Executar em Background (Linux/Mac):**
```bash
nohup python main.py > output.log 2>&1 &

# Ver o processo
ps aux | grep main.py

# Ver logs em tempo real
tail -f logs/trading.log
```

**Executar em Background (Windows):**
```bash
# Use o Windows Task Scheduler ou:
pythonw main.py  # Executa sem janela
```

### Parar o Bot

**Parada Normal:**
- Pressione `Ctrl+C` no terminal
- O bot finalizará a iteração atual e fechará com segurança

**Parada de Emergência:**
```bash
# Linux/Mac
pkill -f main.py

# Windows
taskkill /F /IM python.exe
```

---

## Monitoramento

### Logs em Tempo Real

**Ver logs no console:**
```bash
tail -f logs/trading.log
```

**Filtrar apenas operações importantes:**
```bash
tail -f logs/trading.log | grep -E "BUY|SELL|Stop|Profit"
```

**Ver erros:**
```bash
tail -f logs/trading.log | grep ERROR
```

### Interpretando os Logs

**Exemplo de log de operação:**

```
2024-11-04 10:30:15 | INFO | Moving Average Crossover: BUY signal for BTC/USDT at 42500.00 (RSI: 45.23)
2024-11-04 10:30:16 | INFO | Calculated position size: 0.023529 for BTC/USDT
2024-11-04 10:30:17 | INFO | Market order executed: buy 0.023529 BTC/USDT
2024-11-04 10:30:17 | INFO | Stop loss set for BTC/USDT at 41650.00
2024-11-04 10:30:17 | INFO | Take profit set for BTC/USDT at 44625.00
```

**O que cada linha significa:**

1. **BUY signal**: Estratégia gerou sinal de compra
   - Preço: 42500.00
   - RSI: 45.23 (não está sobrecomprado)

2. **Calculated position size**: Tamanho da posição calculado
   - 0.023529 BTC (~1000 USDT se BTC = 42500)

3. **Market order executed**: Ordem executada com sucesso

4. **Stop loss set**: Stop loss em 41650 (2% abaixo de 42500)

5. **Take profit set**: Take profit em 44625 (5% acima de 42500)

**Log de Stop Loss Acionado:**

```
2024-11-04 11:15:23 | WARNING | Stop loss hit for BTC/USDT at 41600.00
2024-11-04 11:15:24 | INFO | SELL signal for BTC/USDT at 41600.00
2024-11-04 11:15:25 | INFO | Market order executed: sell 0.023529 BTC/USDT
2024-11-04 11:15:25 | INFO | Updated P&L: -21.18, Capital: 9978.82
```

**Resumo Periódico:**

```
------------------------------------------------------------
Running trading iteration...
------------------------------------------------------------
Capital: $10250.50
Daily P&L: $250.50 (2.51%)
Open Positions:
  BTC/USDT: 0.023529 @ $42500.00 (P&L: $235.29)
  ETH/USDT: 0.500000 @ $2250.00 (P&L: $15.50)
------------------------------------------------------------
```

### Verificar Posições Abertas

**Via código Python:**
```python
from crypto_trading.core.exchange_connector import ExchangeConnector

exchange = ExchangeConnector('binance', testnet=True)
balance = exchange.get_balance()

print("Saldo Disponível:")
for currency, amount in balance['free'].items():
    if float(amount) > 0:
        print(f"  {currency}: {amount}")

print("\nSaldo Total:")
for currency, amount in balance['total'].items():
    if float(amount) > 0:
        print(f"  {currency}: {amount}")
```

### Dashboard Simples

Crie um arquivo `monitor.py`:

```python
#!/usr/bin/env python3
"""Monitor simples para o bot de trading."""

import time
from crypto_trading.core.exchange_connector import ExchangeConnector
from crypto_trading.core.market_data import MarketData

def monitor():
    exchange = ExchangeConnector('binance', testnet=True)
    market_data = MarketData(exchange)

    symbols = ['BTC/USDT', 'ETH/USDT']

    while True:
        print("\n" + "="*60)
        print(f"Monitor - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Saldo
        balance = exchange.get_balance()
        print(f"\nUSDT Disponível: {balance['free'].get('USDT', 0)}")

        # Preços atuais
        print("\nPreços Atuais:")
        for symbol in symbols:
            price = market_data.get_current_price(symbol)
            print(f"  {symbol}: ${price:,.2f}")

        # Ordens abertas
        open_orders = exchange.get_open_orders()
        print(f"\nOrdens Abertas: {len(open_orders)}")

        time.sleep(60)  # Atualiza a cada 60 segundos

if __name__ == "__main__":
    monitor()
```

Execute:
```bash
python monitor.py
```

---

## Gerenciamento de Risco

### Configuração de Risco Conservadora (Iniciantes)

```yaml
risk:
  max_position_size_percent: 5    # Apenas 5% do capital por trade
  stop_loss_percent: 2.0          # Stop de 2%
  take_profit_percent: 6.0        # Take profit de 6% (risk/reward 1:3)
  max_daily_loss_percent: 5.0     # Para após perder 5% no dia
  trailing_stop: true
  trailing_stop_percent: 1.0      # Trailing stop conservador
  max_open_positions: 2           # Máximo 2 posições simultâneas
```

**Com $1000:**
- Máximo por trade: $50
- Stop loss: $1 (2% de $50)
- Take profit: $3 (6% de $50)
- Máximo de perda diária: $50

### Configuração Moderada

```yaml
risk:
  max_position_size_percent: 10
  stop_loss_percent: 2.5
  take_profit_percent: 7.5
  max_daily_loss_percent: 7.0
  trailing_stop: true
  trailing_stop_percent: 1.5
  max_open_positions: 3
```

### Configuração Agressiva (Experientes)

```yaml
risk:
  max_position_size_percent: 20
  stop_loss_percent: 3.0
  take_profit_percent: 9.0
  max_daily_loss_percent: 10.0
  trailing_stop: true
  trailing_stop_percent: 2.0
  max_open_positions: 5
```

### Como o Stop Loss Funciona

**Stop Loss Fixo:**
- Define um preço abaixo do qual você vende automaticamente
- Exemplo: Compra a $100, stop loss de 2% = vende a $98

**Trailing Stop:**
- Acompanha o preço quando sobe
- Não desce quando o preço cai
- Exemplo:
  1. Compra a $100, trailing stop de 1.5% = stop em $98.50
  2. Preço sobe para $110 → stop sobe para $108.35
  3. Preço cai para $109 → stop continua em $108.35
  4. Preço cai para $108 → VENDE (stop atingido)

### Cálculo de Position Sizing

O sistema calcula automaticamente:

```
Valor da Posição = Capital × (max_position_size_percent / 100)
Quantidade = Valor da Posição / Preço Atual
```

**Exemplo:**
- Capital: $10,000
- max_position_size_percent: 10%
- Preço BTC: $40,000

```
Valor = $10,000 × 0.10 = $1,000
Quantidade = $1,000 / $40,000 = 0.025 BTC
```

---

## Personalização

### Criar Sua Própria Estratégia

**Passo 1:** Crie um novo arquivo em `crypto_trading/strategies/`:

```python
# crypto_trading/strategies/minha_estrategia.py

from crypto_trading.strategies.base_strategy import BaseStrategy, Signal, SignalType
import pandas as pd
import pandas_ta as ta

class MinhaEstrategia(BaseStrategy):
    """
    Minha estratégia personalizada.
    """

    def __init__(self, parameters=None):
        default_params = {
            'periodo': 14,
            'limite_superior': 80,
            'limite_inferior': 20
        }

        if parameters:
            default_params.update(parameters)

        super().__init__("Minha Estratégia", default_params)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos."""
        df = df.copy()

        # Adicione seus indicadores aqui
        periodo = self.get_parameter('periodo')
        df['rsi'] = ta.rsi(df['close'], length=periodo)
        df['sma'] = ta.sma(df['close'], length=periodo)

        return df

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Signal:
        """Gerar sinal de trading."""

        # Calcular indicadores se necessário
        if 'rsi' not in df.columns:
            df = self.calculate_indicators(df)

        # Obter valores atuais
        current = df.iloc[-1]
        current_price = float(current['close'])

        # Sua lógica de trading aqui
        limite_superior = self.get_parameter('limite_superior')
        limite_inferior = self.get_parameter('limite_inferior')

        # Sinal de COMPRA
        if current['rsi'] < limite_inferior and current['close'] > current['sma']:
            return Signal(SignalType.BUY, symbol, current_price, 1.0)

        # Sinal de VENDA
        elif current['rsi'] > limite_superior and current['close'] < current['sma']:
            return Signal(SignalType.SELL, symbol, current_price, 1.0)

        # HOLD
        return Signal(SignalType.HOLD, symbol, current_price)
```

**Passo 2:** Use sua estratégia no `main.py`:

```python
# Modifique main.py para importar sua estratégia
from crypto_trading.strategies.minha_estrategia import MinhaEstrategia

# No método __init__ da classe TradingBot:
self.strategy = MinhaEstrategia(strategy_params)
```

### Adicionar Notificações Telegram

**Passo 1:** Instale a biblioteca:
```bash
pip install python-telegram-bot
```

**Passo 2:** Crie um bot no Telegram:
1. Fale com @BotFather no Telegram
2. Use /newbot e siga as instruções
3. Copie o token do bot

**Passo 3:** Obtenha seu Chat ID:
```python
# Envie uma mensagem para seu bot, depois execute:
import requests

token = "SEU_TOKEN_AQUI"
url = f"https://api.telegram.org/bot{token}/getUpdates"
response = requests.get(url)
print(response.json())
# Procure por "chat":{"id":12345678}
```

**Passo 4:** Adicione ao `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id
```

**Passo 5:** Crie `crypto_trading/utils/notifier.py`:

```python
import os
import requests
from crypto_trading.utils.logger import get_logger

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.logger = get_logger()
        self.enabled = bool(self.token and self.chat_id)

    def send_message(self, message):
        if not self.enabled:
            return

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(url, data=data)
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")
```

**Passo 6:** Use no bot:

```python
# No main.py
from crypto_trading.utils.notifier import TelegramNotifier

# No __init__
self.notifier = TelegramNotifier()

# Quando executar ordem:
self.notifier.send_message(
    f"🔔 *Nova Operação*\n"
    f"Ação: {signal.signal_type.value.upper()}\n"
    f"Par: {symbol}\n"
    f"Preço: ${current_price:,.2f}\n"
    f"Quantidade: {amount:.6f}"
)
```

---

## Troubleshooting

### Erro: "Failed to initialize exchange"

**Causa:** Credenciais inválidas ou problemas de conexão

**Solução:**
1. Verifique se as API keys estão corretas no `.env`
2. Verifique se está usando testnet mas colocou keys do live (ou vice-versa)
3. Teste a conexão:
```python
import ccxt
exchange = ccxt.binance({
    'apiKey': 'sua_key',
    'secret': 'seu_secret'
})
exchange.set_sandbox_mode(True)  # Para testnet
print(exchange.fetch_balance())
```

### Erro: "Rate limit exceeded"

**Causa:** Muitas requisições em pouco tempo

**Solução:**
1. Aumente `update_interval` no config.yaml:
```yaml
data:
  update_interval: 120  # De 60 para 120 segundos
```

2. Habilite rate limiting:
```yaml
exchange:
  rate_limit: true
```

### Erro: "Insufficient data"

**Causa:** Não há dados históricos suficientes

**Solução:**
```yaml
data:
  historical_days: 60  # Aumente de 30 para 60 dias
```

### Bot não executa ordens

**Checklist:**
1. ✅ Está em modo testnet?
2. ✅ Tem saldo suficiente?
3. ✅ As permissões da API estão corretas?
4. ✅ O sinal está sendo gerado? (verifique logs)
5. ✅ A validação de risco está passando?

**Debug:**
```python
# Adicione logs extras no main.py
self.logger.setLevel('DEBUG')
```

### Preços muito desatualizados

**Causa:** Cache de dados antigos

**Solução:**
```bash
# Limpe o cache
rm -rf data/*.csv

# Reduza o update_interval
```

### Bot para sozinho

**Causa:** Limite de perda diária atingido

**Solução:**
- Verifique os logs para confirmar
- Ajuste `max_daily_loss_percent` se necessário
- Reset diário automático: reinicie o bot a cada dia

---

## Boas Práticas

### 1. Sempre Comece no Testnet

❌ **NUNCA** pule o testnet
✅ Teste por pelo menos 1-2 semanas no testnet
✅ Só vá para live quando tiver resultados consistentes

### 2. Gestão de Capital

✅ Nunca arrisque mais de 1-2% do capital por trade
✅ Mantenha sempre uma reserva (10-20%)
✅ Não coloque todo seu dinheiro na exchange

### 3. Diversificação

✅ Trade múltiplos pares (mas comece com 1-2)
✅ Não concentre mais de 20% em um único ativo
✅ Combine diferentes timeframes

### 4. Monitoramento

✅ Verifique o bot pelo menos 2x por dia
✅ Configure alertas para operações importantes
✅ Mantenha logs de todas as operações
✅ Faça backup dos logs semanalmente

### 5. Segurança

✅ Use autenticação de dois fatores (2FA)
✅ Whitelist de IPs nas API keys
✅ Desabilite saques nas permissões da API
✅ Mantenha as keys em arquivo .env (nunca commite!)
✅ Use senhas fortes e únicas

### 6. Performance

✅ Faça backtesting antes de usar novas estratégias
✅ Ajuste os parâmetros gradualmente
✅ Mantenha registro de todas as mudanças
✅ Compare resultados antes/depois

### 7. Psicologia

✅ Não altere parâmetros por impulso
✅ Aceite que haverá perdas
✅ Siga seu plano de trading
✅ Não aumente o risco após perdas
✅ Tire lucros regularmente

### 8. Manutenção

✅ Atualize as dependências mensalmente:
```bash
pip install --upgrade -r requirements.txt
```

✅ Revise os logs semanalmente
✅ Faça backup da configuração
✅ Documente mudanças importantes

### 9. Limites Diários

**Exemplo de rotina diária:**

```
09:00 - Verificar logs da noite
09:15 - Conferir posições abertas
09:30 - Verificar saldo
12:00 - Check rápido
18:00 - Revisar operações do dia
21:00 - Verificar posições abertas
23:00 - Check final
```

### 10. Quando Parar

⚠️ **PARE IMEDIATAMENTE se:**
- Perdas excederem 10% do capital em uma semana
- Bot apresentar comportamento errático
- Você não entender uma operação executada
- Exchange apresentar problemas
- Você se sentir desconfortável

---

## Checklist de Início

### Antes de Ligar o Bot

- [ ] Instalei todas as dependências
- [ ] Configurei corretamente o .env
- [ ] API keys estão corretas (testnet!)
- [ ] config.yaml está configurado
- [ ] Testei a conexão com a exchange
- [ ] Tenho saldo no testnet
- [ ] Entendo a estratégia que vou usar
- [ ] Configurei o gerenciamento de risco
- [ ] Sei como parar o bot em emergência
- [ ] Testei os logs
- [ ] Li o manual completo

### Após 1 Semana de Testnet

- [ ] Revisei todas as operações
- [ ] Analisei win rate e P&L
- [ ] Ajustei parâmetros se necessário
- [ ] Não tive erros críticos
- [ ] Entendo todos os logs
- [ ] Estou confortável com o sistema

### Antes de Ir para Live

- [ ] 2+ semanas de testnet bem-sucedidas
- [ ] Win rate consistente > 50%
- [ ] Sem erros nos últimos 7 dias
- [ ] Configuração de risco conservadora
- [ ] Capital inicial pequeno (teste com $100-500)
- [ ] 2FA ativado na exchange
- [ ] Whitelist de IP configurado
- [ ] Saques desabilitados na API
- [ ] Plano de emergência pronto

---

## Suporte e Recursos

### Documentação Oficial

- CCXT: https://docs.ccxt.com/
- Pandas-TA: https://github.com/twopirllc/pandas-ta
- Binance API: https://binance-docs.github.io/apidocs/spot/en/

### Comunidades

- Discord de Trading Algorítmico
- Reddit: r/algotrading
- Stack Overflow: tags `algorithmic-trading`, `ccxt`

### Logs de Mudanças

Mantenha um arquivo `CHANGELOG.md` com suas modificações:

```markdown
# Changelog

## 2024-11-04
- Iniciado bot no testnet
- Configuração conservadora (5% position size)
- 1 par (BTC/USDT)

## 2024-11-05
- Ajustado fast_period de 10 para 15
- Melhorou win rate de 45% para 52%

## 2024-11-10
- Adicionado ETH/USDT
- Aumentado position size para 7%
```

---

## Glossário

**API Key**: Chave de acesso à API da exchange

**Backtesting**: Testar estratégia com dados históricos

**Candlestick**: Gráfico de vela japonesa

**Exchange**: Corretora de criptomoedas

**Limit Order**: Ordem com preço limite

**Market Order**: Ordem a mercado (preço atual)

**OHLCV**: Open, High, Low, Close, Volume

**Position Sizing**: Cálculo do tamanho da posição

**Risk/Reward**: Relação risco/retorno

**RSI**: Relative Strength Index (indicador)

**Slippage**: Diferença entre preço esperado e executado

**Stop Loss**: Ordem para limitar perdas

**Take Profit**: Ordem para realizar lucros

**Testnet**: Ambiente de testes da exchange

**Timeframe**: Período do gráfico (1h, 4h, 1d, etc.)

**Trailing Stop**: Stop loss que acompanha o preço

**Win Rate**: Taxa de acerto (trades lucrativos / total)

---

**🎓 Lembre-se:** Trading de criptomoedas envolve riscos. Este sistema é uma ferramenta, não uma garantia de lucros. Sempre opere com capital que pode perder e estude continuamente.

**✨ Boa sorte e bons trades!**
