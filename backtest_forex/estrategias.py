"""Estratégia baseada no método Fimathe.

Esta é uma INTERPRETAÇÃO simplificada, feita a partir dos conceitos públicos
do método (canal de referência, zona neutra, níveis projetados pelo tamanho
do canal e stop movido de nível em nível). As regras exatas do curso podem
ser diferentes: todos os pontos de decisão são parâmetros, para você ajustar.

Uma estratégia devolve um DataFrame com:
    sinal           1 = compra, -1 = venda, 0 = nada
    preco_stop      stop inicial
    preco_alvo      alvo fixo (NaN = sem alvo, sai só pelo stop móvel)
    base_trailing   nível 0, a partir do qual os níveis são contados
    passo_trailing  distância entre os níveis (o tamanho do canal)

O sinal só ABRE a operação. Quem fecha é o stop (inicial ou móvel) ou o alvo.
O sinal de um candle é calculado no fechamento dele e executado no seguinte.
"""

import numpy as np
import pandas as pd


def fimathe(df: pd.DataFrame, janela: int = 20, entrada: float = 0.5,
            stop: float = -0.5, entrada_maxima: float = 1.0, validade: int | None = None,
            alvo_niveis: float | None = None, tamanho_minimo_pct: float = 0.0,
            tamanho_maximo_pct: float | None = None,
            stop_movel: bool = True) -> pd.DataFrame:
    """Rompimento do canal de referência com projeção de níveis.

    Os níveis são medidos em "tamanhos de canal" a partir da borda rompida.
    Exemplo de COMPRA, com canal de 1.1000 a 1.1050 (tamanho = 50 pips):

        nível 2   1.1150   <- ao chegar aqui, o stop sobe para o nível 1
        nível 1   1.1100   <- ao chegar aqui, o stop sobe para o nível 0
        +50%      1.1075   <- entrada: fechamento acima daqui
        nível 0   1.1050   topo do canal
        -50%      1.1025   <- stop inicial: meio do canal
                  1.1000   fundo do canal

    Regras:
    1. Canal de referência: máxima e mínima dos `janela` candles anteriores.
       Quando um candle FECHA fora do canal, o canal congela: topo e fundo
       ficam fixos e os níveis passam a ser contados a partir dele.
    2. Zona neutra: dentro do canal e até `entrada` (50%) além dele, não opera.
       Isso evita entrar em rompimentos falsos.
    3. Entrada: fechamento além de `entrada` (50%) do canal, mas antes de
       `entrada_maxima` (100%). Pode acontecer vários candles depois do
       rompimento. Se o preço pular direto para além de 100%, a entrada está
       atrasada: o canal é descartado e um novo é montado.
       O canal congelado também é descartado após `validade` candles
       (padrão: igual à janela) sem entrada.
    4. Stop inicial: em `stop` (-0.5 = meio do canal).
    5. Stop móvel: ao alcançar o nível k, o stop vai para o nível k - 1.
    6. Alvo opcional: `alvo_niveis` tamanhos de canal além da borda.
    7. Filtros de tamanho: canais muito pequenos (pouco movimento) ou muito
       grandes (stop longe demais) são ignorados, em % do preço.
    Na venda é tudo espelhado, a partir do fundo do canal.
    """
    if janela < 2:
        raise ValueError("A janela precisa ter pelo menos 2 candles.")
    if not stop < 0 < entrada < entrada_maxima:
        raise ValueError("Use stop < 0 < entrada < entrada_maxima.")
    if alvo_niveis is not None and alvo_niveis <= entrada:
        raise ValueError("O alvo precisa estar além do nível de entrada.")

    maxima = df["high"].to_numpy(dtype=float)
    minima = df["low"].to_numpy(dtype=float)
    fechamento = df["close"].to_numpy(dtype=float)
    n = len(df)

    sinal = np.zeros(n)
    preco_stop = np.full(n, np.nan)
    preco_alvo = np.full(n, np.nan)
    base = np.full(n, np.nan)
    passo = np.full(n, np.nan)

    validade = validade or janela
    congelado = None  # (topo, fundo, candle em que congelou)

    for t in range(janela, n):
        c = fechamento[t]
        if congelado is None:
            topo = maxima[t - janela:t].max()
            fundo = minima[t - janela:t].min()
            if fundo < c < topo:
                continue  # ainda dentro do canal: zona neutra
            congelado = (topo, fundo, t)  # rompeu: o canal fica fixo
        topo, fundo, desde = congelado
        tamanho = topo - fundo

        tamanho_pct = tamanho / fundo * 100 if fundo > 0 else 0
        fora_do_filtro = (tamanho <= 0 or tamanho_pct < tamanho_minimo_pct or
                          (tamanho_maximo_pct is not None and tamanho_pct > tamanho_maximo_pct))
        atrasado = (c >= topo + entrada_maxima * tamanho or
                    c <= fundo - entrada_maxima * tamanho)
        if fora_do_filtro or atrasado or t - desde >= validade:
            congelado = None
            continue

        if c > topo + entrada * tamanho:
            sinal[t] = 1
            base[t] = topo
            preco_stop[t] = topo + stop * tamanho
            if alvo_niveis is not None:
                preco_alvo[t] = topo + alvo_niveis * tamanho
        elif c < fundo - entrada * tamanho:
            sinal[t] = -1
            base[t] = fundo
            preco_stop[t] = fundo - stop * tamanho
            if alvo_niveis is not None:
                preco_alvo[t] = fundo - alvo_niveis * tamanho
        else:
            continue  # entre o canal e os 50%: esperando confirmação
        if stop_movel:
            passo[t] = tamanho
        congelado = None  # canal usado; o próximo será montado do zero

    return pd.DataFrame({"sinal": sinal, "preco_stop": preco_stop, "preco_alvo": preco_alvo,
                         "base_trailing": base, "passo_trailing": passo}, index=df.index)


ESTRATEGIAS = {
    "fimathe": fimathe,
}
