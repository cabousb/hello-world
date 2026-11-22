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


ESTRATEGIAS = {
    "medias": cruzamento_medias,
    "rsi": rsi_reversao,
    "comprar_segurar": comprar_e_segurar,
}
