"""Estratégias de exemplo.

Cada estratégia recebe o DataFrame de preços e devolve uma Série "sinal"
com valores:
    1  = comprado (aposta que o preço sobe)
   -1  = vendido  (aposta que o preço cai)
    0  = fora do mercado

O sinal do dia é calculado com o preço de FECHAMENTO daquele dia.
O motor de backtest só usa esse sinal no dia SEGUINTE, para não "ver o futuro".
"""

import numpy as np
import pandas as pd


def cruzamento_medias(df: pd.DataFrame, curta: int = 20, longa: int = 50,
                      permite_venda: bool = True) -> pd.Series:
    """Compra quando a média curta está acima da longa; vende quando está abaixo."""
    if curta >= longa:
        raise ValueError("A média curta precisa ser menor que a longa.")
    media_curta = df["close"].rolling(curta).mean()
    media_longa = df["close"].rolling(longa).mean()

    sinal = pd.Series(0, index=df.index, dtype=float)
    sinal[media_curta > media_longa] = 1
    sinal[media_curta < media_longa] = -1 if permite_venda else 0
    sinal[media_longa.isna()] = 0  # sem dados suficientes ainda
    return sinal


def calcular_rsi(close: pd.Series, periodo: int = 14) -> pd.Series:
    """Índice de Força Relativa (RSI), com a média de Wilder."""
    variacao = close.diff()
    ganhos = variacao.clip(lower=0)
    perdas = -variacao.clip(upper=0)
    media_ganhos = ganhos.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    media_perdas = perdas.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    rs = media_ganhos / media_perdas.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return rsi.where(media_perdas != 0, 100.0)  # nenhuma perda = RSI 100


def rsi_reversao(df: pd.DataFrame, periodo: int = 14, sobrevendido: float = 30,
                 sobrecomprado: float = 70) -> pd.Series:
    """Compra quando o RSI cai abaixo de 30 e fica comprado até ele passar de 50.
    Vende quando passa de 70 e fica vendido até cair abaixo de 50.
    """
    rsi = calcular_rsi(df["close"], periodo)
    sinal = pd.Series(0.0, index=df.index)
    posicao = 0.0
    for data, valor in rsi.items():  # laço simples: mais fácil de entender
        if np.isnan(valor):
            posicao = 0.0
        elif posicao == 0 and valor < sobrevendido:
            posicao = 1.0
        elif posicao == 0 and valor > sobrecomprado:
            posicao = -1.0
        elif posicao == 1 and valor >= 50:
            posicao = 0.0
        elif posicao == -1 and valor <= 50:
            posicao = 0.0
        sinal[data] = posicao
    return sinal


def comprar_e_segurar(df: pd.DataFrame) -> pd.Series:
    """Referência: fica comprado o tempo todo."""
    return pd.Series(1.0, index=df.index)


def fibonacci(df: pd.DataFrame, janela: int = 50, zona_inicio: float = 0.5,
              zona_fim: float = 0.618, nivel_stop: float = 0.786,
              alvo_extensao: float = 1.0, amplitude_minima_pct: float = 1.0) -> pd.DataFrame:
    """Retração de Fibonacci: compra correções numa alta, vende repiques numa queda.

    A cada candle, olha os últimos `janela` candles:
    1. Acha o topo (máxima) e o fundo (mínima) desse período.
    2. Fundo antes do topo = tendência de ALTA. Topo antes do fundo = BAIXA.
    3. Calcula as retrações a partir do movimento (amplitude = topo - fundo).
       Na alta: nível 50% = topo - 0.5 * amplitude, e assim por diante.
    4. Entrada (na alta): o preço corrigiu até a zona 50%-61,8%, não furou
       os 78,6% e o candle fechou positivo (fechamento > abertura), acima dos 61,8%.
       Esse candle de "rejeição" mostra compradores defendendo a zona.
    5. Stop: no nível 78,6%. Alvo: extensão do movimento a partir do fundo
       (1.0 = volta ao topo; 1.272 e 1.618 são extensões comuns).
    Na baixa é tudo espelhado.

    Devolve um DataFrame com sinal, preco_stop e preco_alvo. O motor usa o
    modo "gatilho": o sinal só abre a operação, que fecha no stop ou no alvo.
    """
    if not 0 < zona_inicio < zona_fim < nivel_stop < 1:
        raise ValueError("Use 0 < zona_inicio < zona_fim < nivel_stop < 1.")
    if alvo_extensao <= 0:
        raise ValueError("alvo_extensao precisa ser maior que zero.")

    abertura = df["open"].to_numpy(dtype=float)
    maxima = df["high"].to_numpy(dtype=float)
    minima = df["low"].to_numpy(dtype=float)
    fechamento = df["close"].to_numpy(dtype=float)
    n = len(df)

    sinal = np.zeros(n)
    preco_stop = np.full(n, np.nan)
    preco_alvo = np.full(n, np.nan)

    for t in range(janela - 1, n):
        inicio = t - janela + 1
        i_topo = inicio + int(np.argmax(maxima[inicio:t + 1]))
        i_fundo = inicio + int(np.argmin(minima[inicio:t + 1]))
        topo, fundo = maxima[i_topo], minima[i_fundo]
        amplitude = topo - fundo
        if amplitude <= 0 or amplitude / fundo * 100 < amplitude_minima_pct:
            continue  # movimento pequeno demais para valer a pena

        if i_fundo < i_topo < t:  # tendência de alta; o topo já ficou para trás
            zona_alta = topo - zona_inicio * amplitude
            zona_baixa = topo - zona_fim * amplitude
            stop = topo - nivel_stop * amplitude
            menor_desde_topo = minima[i_topo + 1:t + 1].min()
            if (minima[t] <= zona_alta and menor_desde_topo > stop
                    and fechamento[t] > abertura[t] and fechamento[t] >= zona_baixa):
                sinal[t] = 1
                preco_stop[t] = stop
                preco_alvo[t] = fundo + alvo_extensao * amplitude

        elif i_topo < i_fundo < t:  # tendência de baixa; o fundo já ficou para trás
            zona_baixa = fundo + zona_inicio * amplitude
            zona_alta = fundo + zona_fim * amplitude
            stop = fundo + nivel_stop * amplitude
            maior_desde_fundo = maxima[i_fundo + 1:t + 1].max()
            if (maxima[t] >= zona_baixa and maior_desde_fundo < stop
                    and fechamento[t] < abertura[t] and fechamento[t] <= zona_alta):
                sinal[t] = -1
                preco_stop[t] = stop
                preco_alvo[t] = topo - alvo_extensao * amplitude

    return pd.DataFrame({"sinal": sinal, "preco_stop": preco_stop,
                         "preco_alvo": preco_alvo}, index=df.index)


ESTRATEGIAS = {
    "medias": cruzamento_medias,
    "rsi": rsi_reversao,
    "fibonacci": fibonacci,
    "comprar_segurar": comprar_e_segurar,
}
