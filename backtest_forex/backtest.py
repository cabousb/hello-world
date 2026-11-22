"""Motor de backtest e métricas de desempenho."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

DIAS_POR_ANO = 252


@dataclass
class Resultado:
    dados: pd.DataFrame   # preços + posição + retornos + patrimônio
    operacoes: pd.DataFrame  # uma linha por operação fechada
    metricas: dict


def tamanho_pip(par: str) -> float:
    """Pares com iene (JPY) têm pip de 0.01; os demais, 0.0001."""
    return 0.01 if "JPY" in par.upper() else 0.0001


def verificar_saida(posicao: float, entrada: float, abertura: float, maxima: float,
                    minima: float, stop: float | None, alvo: float | None):
    """Confere se o stop loss ou o take profit foi atingido neste candle.

    Devolve (preco_de_saida, motivo) ou (None, None).

    Regras (conservadoras de propósito):
    - Gap: se o candle já abre além do stop/alvo, a saída é no preço de abertura.
      Um stop não garante o preço: num gap, você sai pior do que planejou.
    - Se o mesmo candle tocou o stop E o alvo, não dá para saber qual veio
      primeiro com dados diários. Assumimos o pior: o stop.
    """
    if posicao > 0:  # comprado: stop abaixo, alvo acima
        preco_stop = entrada - stop if stop else None
        preco_alvo = entrada + alvo if alvo else None
        if preco_stop is not None and abertura <= preco_stop:
            return abertura, "stop"
        if preco_alvo is not None and abertura >= preco_alvo:
            return abertura, "alvo"
        if preco_stop is not None and minima <= preco_stop:
            return preco_stop, "stop"
        if preco_alvo is not None and maxima >= preco_alvo:
            return preco_alvo, "alvo"
    elif posicao < 0:  # vendido: stop acima, alvo abaixo
        preco_stop = entrada + stop if stop else None
        preco_alvo = entrada - alvo if alvo else None
        if preco_stop is not None and abertura >= preco_stop:
            return abertura, "stop"
        if preco_alvo is not None and abertura <= preco_alvo:
            return abertura, "alvo"
        if preco_stop is not None and maxima >= preco_stop:
            return preco_stop, "stop"
        if preco_alvo is not None and minima <= preco_alvo:
            return preco_alvo, "alvo"
    return None, None


def executar(df: pd.DataFrame, sinal: pd.Series, spread_pips: float = 1.0,
             par: str = "EURUSD", capital_inicial: float = 10_000.0,
             alavancagem: float = 1.0, stop_pips: float | None = None,
             alvo_pips: float | None = None) -> Resultado:
    """Simula a estratégia, candle a candle.

    - posicao: o sinal de ontem é a posição de hoje, para não usar informação
      que ainda não existia no momento da decisão. A entrada é no fechamento
      do candle do sinal.
    - custo: cada entrada ou saída paga metade do spread (ida + volta = 1 spread).
    - stop_pips / alvo_pips: distância, em pips, do preço de entrada até o
      stop loss e o take profit. None = não usar.
    - Depois de um stop ou alvo, a estratégia só entra de novo quando o sinal
      mudar. Sem isso, ela reabriria a mesma operação no dia seguinte.
    - alavancagem: multiplica ganhos E perdas. Comece com 1.
    """
    for nome, valor in (("stop_pips", stop_pips), ("alvo_pips", alvo_pips)):
        if valor is not None and valor <= 0:
            raise ValueError(f"{nome} precisa ser maior que zero.")

    pip = tamanho_pip(par)
    meio_spread = spread_pips * pip / 2
    stop = stop_pips * pip if stop_pips else None
    alvo = alvo_pips * pip if alvo_pips else None

    sinais = sinal.reindex(df.index).fillna(0).to_numpy(dtype=float)
    abertura = df["open"].to_numpy(dtype=float)
    maxima = df["high"].to_numpy(dtype=float)
    minima = df["low"].to_numpy(dtype=float)
    fechamento = df["close"].to_numpy(dtype=float)
    n = len(df)

    posicoes = np.zeros(n)
    retornos = np.zeros(n)
    custos = np.zeros(n)
    id_operacao = np.zeros(n, dtype=int)  # 0 = fora do mercado
    motivos = np.full(n, "", dtype=object)

    pos = 0.0
    entrada = 0.0
    operacao_atual = 0
    sinal_bloqueado = None  # direção travada após um stop/alvo

    for t in range(1, n):
        desejado = sinais[t - 1]
        if sinal_bloqueado is not None:
            if desejado == sinal_bloqueado:
                desejado = 0.0
            else:
                sinal_bloqueado = None

        anterior = fechamento[t - 1]
        if desejado != pos:  # troca de posição no fechamento de ontem
            custos[t] += abs(desejado - pos) * meio_spread / anterior
            if pos != 0:
                motivos[t - 1] = motivos[t - 1] or "sinal"
            if desejado != 0:
                operacao_atual += 1
                entrada = anterior
            pos = desejado

        if pos == 0:
            continue

        posicoes[t] = pos
        id_operacao[t] = operacao_atual
        saida, motivo = verificar_saida(pos, entrada, abertura[t], maxima[t],
                                        minima[t], stop, alvo)
        if saida is None:
            retornos[t] = pos * (fechamento[t] / anterior - 1)
        else:
            retornos[t] = pos * (saida / anterior - 1)
            custos[t] += abs(pos) * meio_spread / anterior
            motivos[t] = motivo
            sinal_bloqueado = sinais[t - 1]
            pos = 0.0

    res = df.copy()
    res["sinal"] = sinais
    res["posicao"] = posicoes
    res["id_operacao"] = id_operacao
    res["motivo_saida"] = motivos
    res["retorno_mercado"] = res["close"].pct_change().fillna(0)
    res["custo"] = custos
    res["retorno_estrategia"] = alavancagem * (retornos - custos)
    # Com alavancagem alta, um dia ruim pode passar de -100%: a conta zera.
    res["retorno_estrategia"] = res["retorno_estrategia"].clip(lower=-1)
    res["patrimonio"] = capital_inicial * (1 + res["retorno_estrategia"]).cumprod()
    res["patrimonio_mercado"] = capital_inicial * (1 + res["retorno_mercado"]).cumprod()

    operacoes = extrair_operacoes(res)
    metricas = calcular_metricas(res, operacoes, capital_inicial)
    return Resultado(res, operacoes, metricas)


def extrair_operacoes(res: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por operação, a partir da coluna id_operacao."""
    linhas = []
    dentro = res[res["id_operacao"] > 0]
    for _, bloco in dentro.groupby("id_operacao"):
        retorno = (1 + bloco["retorno_estrategia"]).prod() - 1
        motivo = bloco["motivo_saida"].iloc[-1] or "em aberto"
        linhas.append({
            "entrada": bloco.index[0],
            "saida": bloco.index[-1],
            "direcao": "compra" if bloco["posicao"].iloc[0] > 0 else "venda",
            "dias": len(bloco),
            "motivo": motivo,
            "retorno_%": retorno * 100,
        })
    return pd.DataFrame(linhas, columns=["entrada", "saida", "direcao", "dias",
                                         "motivo", "retorno_%"])


def calcular_metricas(res: pd.DataFrame, operacoes: pd.DataFrame,
                      capital_inicial: float) -> dict:
    r = res["retorno_estrategia"]
    anos = max(len(res) / DIAS_POR_ANO, 1e-9)
    final = res["patrimonio"].iloc[-1]

    pico = res["patrimonio"].cummax()
    queda = res["patrimonio"] / pico - 1

    vol = r.std() * np.sqrt(DIAS_POR_ANO)
    sharpe = (r.mean() * DIAS_POR_ANO) / vol if vol > 0 else 0.0

    n_ops = len(operacoes)
    vencedoras = operacoes[operacoes["retorno_%"] > 0]
    perdedoras = operacoes[operacoes["retorno_%"] <= 0]
    soma_perdas = -perdedoras["retorno_%"].sum()

    return {
        "capital_final": final,
        "retorno_total_%": (final / capital_inicial - 1) * 100,
        "retorno_anual_%": ((final / capital_inicial) ** (1 / anos) - 1) * 100,
        "volatilidade_anual_%": vol * 100,
        "sharpe": sharpe,
        "queda_maxima_%": queda.min() * 100,
        "operacoes": n_ops,
        "taxa_acerto_%": len(vencedoras) / n_ops * 100 if n_ops else 0.0,
        "fator_lucro": (vencedoras["retorno_%"].sum() / soma_perdas
                        if soma_perdas > 0 else float("inf") if n_ops else 0.0),
        "saidas_stop": int((operacoes["motivo"] == "stop").sum()),
        "saidas_alvo": int((operacoes["motivo"] == "alvo").sum()),
        "retorno_mercado_%": (res["patrimonio_mercado"].iloc[-1] / capital_inicial - 1) * 100,
    }


NOMES_METRICAS = {
    "capital_final": "Capital final",
    "retorno_total_%": "Retorno total (%)",
    "retorno_anual_%": "Retorno anual (%)",
    "volatilidade_anual_%": "Volatilidade anual (%)",
    "sharpe": "Índice Sharpe",
    "queda_maxima_%": "Queda máxima (%)",
    "operacoes": "Nº de operações",
    "taxa_acerto_%": "Taxa de acerto (%)",
    "fator_lucro": "Fator de lucro",
    "saidas_stop": "Saídas no stop loss",
    "saidas_alvo": "Saídas no take profit",
    "retorno_mercado_%": "Retorno comprar e segurar (%)",
}


def formatar_metricas(metricas: dict) -> str:
    largura = max(len(n) for n in NOMES_METRICAS.values())
    linhas = []
    for chave, nome in NOMES_METRICAS.items():
        valor = metricas[chave]
        texto = f"{valor:,.0f}" if isinstance(valor, int) else f"{valor:,.2f}"
        linhas.append(f"  {nome:<{largura}}  {texto:>12}")
    return "\n".join(linhas)
