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


def executar(df: pd.DataFrame, sinal: pd.Series, spread_pips: float = 1.0,
             par: str = "EURUSD", capital_inicial: float = 10_000.0,
             alavancagem: float = 1.0) -> Resultado:
    """Simula a estratégia.

    - posicao: o sinal de ontem é a posição de hoje (shift(1)), para não usar
      informação que ainda não existia no momento da decisão.
    - custo: cada vez que a posição muda, pagamos metade do spread por unidade
      trocada (entrar + sair = 1 spread inteiro).
    - alavancagem: multiplica ganhos E perdas. Comece com 1.
    """
    res = df.copy()
    res["sinal"] = sinal.reindex(df.index).fillna(0)
    res["posicao"] = res["sinal"].shift(1).fillna(0)

    res["retorno_mercado"] = res["close"].pct_change().fillna(0)
    meio_spread = spread_pips * tamanho_pip(par) / 2
    troca = res["posicao"].diff().abs().fillna(res["posicao"].abs())
    res["custo"] = troca * meio_spread / res["close"]

    res["retorno_estrategia"] = alavancagem * (
        res["posicao"] * res["retorno_mercado"] - res["custo"])
    # Com alavancagem alta, um dia ruim pode passar de -100%: a conta zera.
    res["retorno_estrategia"] = res["retorno_estrategia"].clip(lower=-1)
    res["patrimonio"] = capital_inicial * (1 + res["retorno_estrategia"]).cumprod()
    res["patrimonio_mercado"] = capital_inicial * (1 + res["retorno_mercado"]).cumprod()

    operacoes = extrair_operacoes(res)
    metricas = calcular_metricas(res, operacoes, capital_inicial)
    return Resultado(res, operacoes, metricas)


def extrair_operacoes(res: pd.DataFrame) -> pd.DataFrame:
    """Agrupa dias seguidos com a mesma posição (diferente de 0) em uma operação."""
    pos = res["posicao"]
    id_bloco = (pos != pos.shift()).cumsum()
    linhas = []
    for _, bloco in res[pos != 0].groupby(id_bloco[pos != 0]):
        retorno = (1 + bloco["retorno_estrategia"]).prod() - 1
        linhas.append({
            "entrada": bloco.index[0],
            "saida": bloco.index[-1],
            "direcao": "compra" if bloco["posicao"].iloc[0] > 0 else "venda",
            "dias": len(bloco),
            "retorno_%": retorno * 100,
        })
    return pd.DataFrame(linhas, columns=["entrada", "saida", "direcao", "dias", "retorno_%"])


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
    "retorno_mercado_%": "Retorno comprar e segurar (%)",
}


def formatar_metricas(metricas: dict) -> str:
    largura = max(len(n) for n in NOMES_METRICAS.values())
    linhas = []
    for chave, nome in NOMES_METRICAS.items():
        valor = metricas[chave]
        texto = f"{valor:,.0f}" if chave == "operacoes" else f"{valor:,.2f}"
        linhas.append(f"  {nome:<{largura}}  {texto:>12}")
    return "\n".join(linhas)
