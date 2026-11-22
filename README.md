# hello-world

Aprendendo GitHub, e agora também Python aplicado a dados de mercado.

## Backtest de Forex (projeto de estudo)

Um programa que testa estratégias de Forex em **dados históricos**, sem
arriscar dinheiro. Serve para praticar Python, pandas, testes automatizados e
para entender por que a maioria das estratégias não funciona.

> ⚠️ Projeto educacional. Resultado bom em backtest **não** garante lucro
> futuro, e o programa não envia ordens para nenhuma corretora.

### Instalação

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Como usar

```bash
# Dados reais do Yahoo Finance (precisa de internet)
python -m backtest_forex --par EURUSD --estrategia medias --grafico

# Outros pares e parâmetros
python -m backtest_forex --par GBPUSD --estrategia medias --curta 10 --longa 30
python -m backtest_forex --par USDJPY --estrategia rsi --spread 1.5

# Seu próprio CSV (colunas: date, open, high, low, close)
python -m backtest_forex --fonte csv --arquivo meus_dados.csv

# Dados aleatórios, para testar sem internet
python -m backtest_forex --fonte sintetico

# Ver todas as opções
python -m backtest_forex --help
```

Com `--grafico`, o gráfico de patrimônio e quedas é salvo em `resultados/backtest.png`.

### Estratégias incluídas

| Nome              | Ideia                                                                   |
|-------------------|-------------------------------------------------------------------------|
| `medias`          | Compra quando a média curta cruza acima da longa; vende quando cruza abaixo |
| `rsi`             | Compra com RSI < 30, vende com RSI > 70, sai quando volta a 50          |
| `comprar_segurar` | Fica comprado o tempo todo (serve de comparação)                        |

### Stop loss e take profit

```bash
# Stop de 50 pips e alvo de 100 pips (relação risco:retorno de 1:2)
python -m backtest_forex --par EURUSD --estrategia medias --stop 50 --alvo 100
```

- `--stop`: fecha a operação se o preço andar X pips **contra** você.
- `--alvo`: fecha a operação se o preço andar X pips **a seu favor**.
- Dá para usar só um dos dois.

Regras da simulação (conservadoras de propósito):

- **Gap:** se o candle já abre além do stop, a saída é no preço de abertura.
  O stop não garante o preço: num gap você perde mais do que planejou.
- **Stop e alvo no mesmo candle:** com dados diários não dá para saber qual
  aconteceu primeiro, então o programa assume o pior caso, o stop.
- **Sem reentrada automática:** depois de um stop ou alvo, a estratégia só volta
  ao mercado quando o sinal mudar.

Atenção ao tamanho do stop: o EUR/USD costuma variar 50 a 80 pips num dia.
Um stop de 20 pips em gráfico diário é atingido quase sempre.

### O que cada métrica significa

- **Retorno total / anual:** quanto o capital cresceu (ou encolheu).
- **Volatilidade anual:** o quanto o patrimônio oscila. Quanto maior, mais risco.
- **Índice Sharpe:** retorno dividido pelo risco. Acima de 1 já é considerado bom.
- **Queda máxima:** a maior perda a partir de um topo. É o "quanto dói" a estratégia.
- **Saídas no stop loss / take profit:** quantas operações terminaram em cada um.
- **Taxa de acerto:** porcentagem de operações que deram lucro.
- **Fator de lucro:** soma dos ganhos ÷ soma das perdas. Abaixo de 1 significa prejuízo.

### Cuidados que o código já toma

- **Sem olhar o futuro:** o sinal calculado no fechamento de um dia só vira
  posição no dia seguinte.
- **Custos:** cada entrada ou saída paga o spread (`--spread`, em pips).
- **Alavancagem:** `--alavancagem` multiplica ganhos *e* perdas. Experimente
  `--alavancagem 50` e veja a queda máxima.

### Estrutura

```
backtest_forex/
  dados.py        # Yahoo, CSV ou dados sintéticos
  estrategias.py  # geram o sinal: 1 = compra, -1 = venda, 0 = fora
  backtest.py     # simulação e métricas
  __main__.py     # linha de comando
tests/
  test_backtest.py
```

Para rodar os testes: `python -m pytest`

### Ideias para continuar estudando

1. Criar uma estratégia nova em `estrategias.py` (ex.: rompimento de máxima de 20 dias).
2. Testar várias combinações de `--stop` e `--alvo` e comparar a queda máxima.
3. Testar a mesma estratégia em vários pares e períodos: se só funciona em um, desconfie.
4. Separar os dados em "treino" e "teste" para evitar *overfitting*.
