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
python -m backtest_forex --par EURUSD --grafico

# Outros pares, tempos gráficos e parâmetros
python -m backtest_forex --par GBPUSD --intervalo 4h --janela 30 --alvo-niveis 2
python -m backtest_forex --par USDJPY --intervalo 1h --spread 1.5

# Seu próprio CSV (colunas: date, open, high, low, close)
python -m backtest_forex --fonte csv --arquivo meus_dados.csv

# Dados aleatórios, para testar sem internet
python -m backtest_forex --fonte sintetico

# Ver todas as opções
python -m backtest_forex --help
```

Com `--grafico`, o gráfico de patrimônio e quedas é salvo em `resultados/backtest.png`.

### Estratégia: Fimathe (interpretação)

> Esta é uma **interpretação simplificada**, feita a partir dos conceitos
> públicos do método Fimathe. As regras exatas do curso podem ser diferentes;
> por isso cada ponto de decisão é um parâmetro.

Exemplo de **compra**, com canal de referência de 1.1000 a 1.1050 (50 pips):

```
nível 2   1.1150   ao chegar aqui, o stop sobe para o nível 1
nível 1   1.1100   ao chegar aqui, o stop sobe para o nível 0
+50%      1.1075   ENTRADA: fechamento acima daqui
nível 0   1.1050   topo do canal
-50%      1.1025   STOP INICIAL: meio do canal
          1.1000   fundo do canal
```

1. **Canal de referência:** máxima e mínima dos últimos `--janela` candles.
   Quando um candle fecha fora dele, o canal **congela**.
2. **Zona neutra:** dentro do canal e até 50% além dele, não opera
   (filtra rompimentos falsos).
3. **Entrada:** fechamento além de `--entrada` (50%) do canal, mas antes de 100%.
   Se o preço pular direto para além de 100%, a entrada está atrasada e o canal
   é descartado. O canal também expira depois de `--janela` candles sem entrada.
4. **Stop inicial:** `--stop-nivel` (padrão -0.5, o meio do canal).
5. **Stop móvel:** ao alcançar o nível *k*, o stop vai para o nível *k − 1*.
   Desligue com `--sem-stop-movel`.
6. **Alvo (opcional):** `--alvo-niveis 2` fecha a operação no nível 2.
7. **Filtros:** `--tamanho-minimo` e `--tamanho-maximo` ignoram canais menores
   ou maiores que X% do preço.

Na venda é tudo espelhado, a partir do fundo do canal.

A operação só fecha no stop (inicial ou móvel) ou no alvo. A tabela de
operações mostra o motivo de cada saída: `stop`, `stop móvel`, `alvo` ou
`em aberto`.

### Tempo gráfico (`--intervalo`)

```bash
python -m backtest_forex --par EURUSD --intervalo 1h
python -m backtest_forex --par EURUSD --intervalo 4h --otimizar
```

| Intervalo | Histórico máximo no Yahoo | Candles por ano (aprox.) |
|-----------|---------------------------|--------------------------|
| `1d` (padrão) | vários anos           | 260                      |
| `4h`      | 730 dias (montado a partir do 1h) | 1.560            |
| `1h`      | 730 dias                  | 6.200                    |
| `30m`, `15m`, `5m` | 60 dias          | 12.000 a 75.000          |

- Se o `--periodo` passar do limite, o programa avisa e usa o máximo permitido.
- Os horários estão em UTC.
- Os parâmetros contam **candles**, não dias: `--janela 20` no 1h monta o
  canal com as últimas 20 horas.
- Retorno anual, volatilidade e Sharpe são calculados medindo quantos candles
  os dados têm por ano, então as métricas valem em qualquer tempo gráfico.
- Em tempos menores há muito mais operações, e o spread pesa bem mais.
- Com `--fonte csv`, vale o tempo gráfico do arquivo (ex.: exportado do
  MetaTrader em H4 ou M15).

### Regras da simulação (conservadoras de propósito)

- **Gap:** se o candle já abre além do stop, a saída é no preço de abertura.
  O stop não garante o preço: num gap você perde mais do que planejou.
- **Stop e alvo no mesmo candle:** com candles não dá para saber qual
  aconteceu primeiro, então o programa assume o pior caso, o stop.
- **Stop móvel:** só é atualizado depois que o candle fecha e passa a valer
  no candle seguinte.

### Treino e teste (otimização de parâmetros)

```bash
python -m backtest_forex --par EURUSD --otimizar --grafico
python -m backtest_forex --par EURUSD --intervalo 4h --otimizar --treino 0.6 --criterio fator_lucro
```

1. Os dados são divididos **em ordem cronológica**: os primeiros 70% são o
   treino e os últimos 30% são o teste (`--treino` muda a proporção).
2. O programa testa várias combinações de parâmetros **só no treino** e escolhe
   a melhor pelo `--criterio` (`sharpe`, `retorno` ou `fator_lucro`).
3. A combinação escolhida roda no teste, um período que ela nunca viu.
4. O programa mostra as métricas lado a lado e um diagnóstico.

Combinações testadas (em `otimizacao.py`, no dicionário `GRADES`):

| Estratégia | Parâmetros                                                  |
|------------|-------------------------------------------------------------|
| `fimathe`  | janela: 10, 20, 30, 50, 80 / alvo: nenhum, 1, 2 ou 3 níveis |

As demais opções (`--entrada`, `--stop-nivel`, filtros) ficam fixas durante a busca.

Como ler o resultado:

- **Bom no treino e ruim no teste:** *overfitting*. Os parâmetros decoraram o
  passado e não previram nada.
- **Posição no teste:** se a melhor do treino fica entre as piores no teste,
  escolher pelo treino não ajudou em nada.
- **Muitas combinações = mais risco de sorte.** Quanto mais combinações você
  testa, maior a chance de uma parecer ótima por acaso.
- **Use o teste uma vez só.** Se você olhar o teste, mudar a estratégia e testar
  de novo, ele vira treino. O ideal é guardar um período final que você só
  olha no fim.

Com `--grafico`, a curva de patrimônio do treino e do teste é salva em
`resultados/treino_teste.png`.

### O que cada métrica significa

- **Retorno total / anual:** quanto o capital cresceu (ou encolheu).
- **Volatilidade anual:** o quanto o patrimônio oscila. Quanto maior, mais risco.
- **Índice Sharpe:** retorno dividido pelo risco. Acima de 1 já é considerado bom.
- **Queda máxima:** a maior perda a partir de um topo. É o "quanto dói" a estratégia.
- **Saídas no stop inicial / stop móvel / take profit:** quantas operações terminaram em cada um.
- **Taxa de acerto:** porcentagem de operações que deram lucro.
- **Fator de lucro:** soma dos ganhos ÷ soma das perdas. Abaixo de 1 significa prejuízo.

### Cuidados que o código já toma

- **Sem olhar o futuro:** o sinal calculado no fechamento de um candle só vira
  posição no candle seguinte.
- **Custos:** cada entrada ou saída paga o spread (`--spread`, em pips).
- **Alavancagem:** `--alavancagem` multiplica ganhos *e* perdas. Experimente
  `--alavancagem 50` e veja a queda máxima.

### Estrutura

```
backtest_forex/
  dados.py        # Yahoo, CSV ou dados sintéticos
  estrategias.py  # Fimathe: sinal, stop, alvo e níveis do stop móvel
  backtest.py     # simulação e métricas
  otimizacao.py   # divisão treino/teste e busca de parâmetros
  __main__.py     # linha de comando
tests/
  test_backtest.py
```

Para rodar os testes: `python -m pytest`

### Ideias para continuar estudando

1. Ajustar as regras do Fimathe às do curso (entrada, stop, filtros).
2. Usar a tendência de um tempo gráfico maior como filtro (ex.: só comprar no
   1h quando o 4h estiver em alta).
3. Testar a mesma configuração em vários pares e períodos: se só funciona em um, desconfie.
4. Implementar *walk-forward*: repetir o treino/teste em várias janelas que
   avançam no tempo, em vez de um único corte.
