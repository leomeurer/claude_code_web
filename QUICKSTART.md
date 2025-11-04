# 🚀 Guia de Início Rápido

Este guia irá te ajudar a começar em **10 minutos**.

---

## ⚡ Instalação Rápida (5 minutos)

### 1. Instale as Dependências

```bash
# Crie o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instale as bibliotecas
pip install -r requirements.txt
```

### 2. Configure suas Credenciais

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas API keys
nano .env
```

**Obter API Keys do Binance Testnet:**

1. Acesse: https://testnet.binance.vision/
2. Faça login com GitHub
3. Gere uma API Key
4. Cole no `.env`:

```env
BINANCE_API_KEY=sua_api_key_do_testnet
BINANCE_API_SECRET=seu_secret_do_testnet
```

---

## ✅ Teste a Conexão (2 minutos)

Execute o script de teste:

```bash
python scripts/test_connection.py
```

Você deve ver:

```
✅ Todos os testes passaram com sucesso!
```

Se vir erros, verifique suas API keys.

---

## 🎮 Execute o Bot (1 minuto)

```bash
python main.py
```

Você verá algo como:

```
2024-11-04 10:30:15 | INFO | Initializing Crypto Trading Bot
2024-11-04 10:30:16 | INFO | Trading pairs: ['BTC/USDT']
2024-11-04 10:30:17 | INFO | Fetching initial historical data...
2024-11-04 10:30:20 | INFO | Starting trading loop...
```

**Para parar:** Pressione `Ctrl+C`

---

## 📊 Monitore (1 minuto)

Em outro terminal, execute o monitor:

```bash
python scripts/monitor.py
```

Você verá em tempo real:
- 💰 Seu saldo
- 📈 Preços atuais
- 📋 Ordens abertas

---

## 🧪 Faça um Backtest (1 minuto)

Teste sua estratégia com dados históricos:

```bash
python scripts/backtest.py
```

Você verá resultados como:

```
📊 RESULTADOS DO BACKTEST
   Capital inicial:  $10,000.00
   Capital final:    $10,523.50
   Retorno total:    $523.50 (+5.23%)
   Win rate: 58.3%
```

---

## ⚙️ Configuração Básica

O arquivo `config/config.yaml` já vem pré-configurado para modo seguro:

- ✅ Testnet ativado
- ✅ Risk management conservador (5% por trade)
- ✅ Stop loss de 2%
- ✅ Take profit de 5%

**Você pode começar imediatamente!**

---

## 📚 Próximos Passos

### Para Iniciantes

1. **Deixe rodar por 1 semana no testnet**
2. **Observe os logs** em `logs/trading.log`
3. **Entenda cada operação** que o bot faz
4. **Não mexa nos parâmetros** ainda

### Quando se Sentir Confortável

1. **Leia o MANUAL.md completo**
2. **Experimente diferentes pares** em `config/config.yaml`
3. **Ajuste a estratégia** gradualmente
4. **Faça backtests** antes de mudar parâmetros

### Antes de Ir para LIVE

⚠️ **IMPORTANTE:** Só use dinheiro real quando:

- ✅ Rodou no testnet por 2+ semanas
- ✅ Win rate consistente > 50%
- ✅ Entende completamente o sistema
- ✅ Não teve erros críticos
- ✅ Testou com capital pequeno primeiro

---

## 🆘 Problemas Comuns

### "Failed to initialize exchange"

**Solução:**
- Verifique se as API keys estão corretas no `.env`
- Certifique-se de usar keys do **testnet**

### "Rate limit exceeded"

**Solução:**
- Em `config/config.yaml`, aumente `update_interval`:
```yaml
data:
  update_interval: 120  # De 60 para 120 segundos
```

### Bot não executa ordens

**Solução:**
- Verifique se tem saldo no testnet
- Execute: `python scripts/test_connection.py`
- Veja os logs: `tail -f logs/trading.log`

---

## 📖 Documentação Completa

- **MANUAL.md** - Manual completo de uso
- **README.md** - Visão geral do projeto
- **config/config.yaml** - Todas as configurações

---

## 🎯 Checklist Rápido

Antes de começar, certifique-se:

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` configurado com API keys do testnet
- [ ] Teste de conexão passou (`python scripts/test_connection.py`)
- [ ] Entende que está em **testnet** (sem risco)

---

## 💡 Dica Final

**Comece devagar!**

- Use apenas 1 par de trading (BTC/USDT)
- Mantenha configuração conservadora
- Monitore diariamente
- Aprenda com cada operação

**Boa sorte! 🚀**

---

**Precisa de ajuda?** Abra uma issue no GitHub ou consulte o MANUAL.md
