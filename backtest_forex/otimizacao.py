"""Separação em treino e teste, com otimização de parâmetros.

A ideia:
1. Dividir os dados em ordem cronológica: o começo é o TREINO, o final é o TESTE.
2. Testar várias combinações de parâmetros só no treino e escolher a melhor.
3. Rodar a combinação escolhida no teste, um período que ela "nunca viu".

Se o resultado despenca no teste, a otimização provavelmente só decorou o
passado (overfitting). Nunca embaralhe os dados: em séries de preço, o teste
precisa vir DEPOIS do treino, como acontece na vida real.
"""

from dataclasses import dataclass
from itertools import product

import pandas as pd

from . import backtest, estrategias

# Combinações testadas para cada estratégia.
GRADES = {
    "medias": {"curta": [5, 10, 20, 30, 50], "longa": [30, 50, 100, 150, 200]},
    "rsi": {"periodo": [7, 10, 14, 21, 28]},
    "fibonacci": {"janela": [20, 30, 50, 80, 120], "alvo_extensao": [1.0, 1.272, 1.618]},
    "comprar_segurar": {},
}

CRITERIOS = {"sharpe": "sharpe", "retorno": "retorno_total_%", "fator_lucro": "fator_lucro"}


@dataclass
class ResultadoOtimizacao:
    ranking: pd.DataFrame          # todas as combinações, da melhor para a pior no treino
    melhores_parametros: dict
    treino: backtest.Resultado
    teste: backtest.Resultado
    data_corte: pd.Timestamp


def dividir(df: pd.DataFrame, proporcao_treino: float = 0.7):
    """Divide em ordem cronológica. Ex.: 0.7 = 70% treino, 30% teste."""
    if not 0 < proporcao_treino < 1:
        raise ValueError("proporcao_treino precisa estar entre 0 e 1.")
    corte = int(len(df) * proporcao_treino)
    if corte < 2 or len(df) - corte < 2:
        raise ValueError("Dados insuficientes para dividir em treino e teste.")
    return df.iloc[:corte], df.iloc[corte:]


def combinacoes(estrategia: str) -> list[dict]:
    grade = GRADES[estrategia]
    nomes = list(grade)
    todas = [dict(zip(nomes, valores)) for valores in product(*grade.values())]
    if estrategia == "medias":
        todas = [c for c in todas if c["curta"] < c["longa"]]
    return todas


def formatar_parametros(parametros: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in parametros.items()) or "(sem parâmetros)"


def otimizar(df: pd.DataFrame, estrategia: str, proporcao_treino: float = 0.7,
             criterio: str = "sharpe", min_operacoes: int = 5,
             parametros_fixos: dict | None = None,
             opcoes_backtest: dict | None = None) -> ResultadoOtimizacao:
    """Escolhe os parâmetros no treino e avalia no teste.

    - O sinal é calculado na série inteira e depois recortado. Como as
      estratégias só usam dados passados, o começo do teste pode usar o fim
      do treino para "aquecer" os indicadores, sem olhar o futuro.
    - Combinações com menos de `min_operacoes` no treino ficam no fim do
      ranking: poucas operações = resultado pouco confiável.
    - As colunas de teste do ranking são só para você ver. A escolha usa
      apenas o treino.
    """
    if criterio not in CRITERIOS:
        raise ValueError(f"Critério deve ser um de: {list(CRITERIOS)}")
    chave = CRITERIOS[criterio]
    parametros_fixos = parametros_fixos or {}
    opcoes_backtest = opcoes_backtest or {}
    funcao = estrategias.ESTRATEGIAS[estrategia]

    df_treino, df_teste = dividir(df, proporcao_treino)

    linhas, resultados = [], []
    for parametros in combinacoes(estrategia):
        sinal = funcao(df, **parametros, **parametros_fixos)
        r_treino = backtest.executar(df_treino, sinal.loc[df_treino.index], **opcoes_backtest)
        r_teste = backtest.executar(df_teste, sinal.loc[df_teste.index], **opcoes_backtest)
        resultados.append((parametros, r_treino, r_teste))
        mt, ms = r_treino.metricas, r_teste.metricas
        linhas.append({
            "parametros": formatar_parametros(parametros),
            "valido": mt["operacoes"] >= min_operacoes or not GRADES[estrategia],
            f"{criterio}_treino": mt[chave],
            "retorno_treino_%": mt["retorno_total_%"],
            "operacoes_treino": mt["operacoes"],
            f"{criterio}_teste": ms[chave],
            "retorno_teste_%": ms["retorno_total_%"],
        })

    ranking = pd.DataFrame(linhas)
    ranking["_indice"] = range(len(ranking))
    ranking = ranking.sort_values(["valido", f"{criterio}_treino"], ascending=False)
    melhor = ranking["_indice"].iloc[0]
    ranking = ranking.drop(columns="_indice").reset_index(drop=True)
    ranking.index += 1  # posição 1 = melhor no treino

    parametros, r_treino, r_teste = resultados[melhor]
    return ResultadoOtimizacao(ranking, parametros, r_treino, r_teste, df_teste.index[0])


def comparar_metricas(resultado: ResultadoOtimizacao) -> str:
    """Tabela lado a lado: treino x teste."""
    nomes = backtest.NOMES_METRICAS
    largura = max(len(n) for n in nomes.values())
    linhas = [f"  {'':<{largura}}  {'Treino':>12}  {'Teste':>12}"]
    for chave, nome in nomes.items():
        valores = []
        for r in (resultado.treino, resultado.teste):
            v = r.metricas[chave]
            valores.append(f"{v:,.0f}" if isinstance(v, int) else f"{v:,.2f}")
        linhas.append(f"  {nome:<{largura}}  {valores[0]:>12}  {valores[1]:>12}")
    return "\n".join(linhas)


# Abaixo destes valores, nem o treino mostra uma vantagem que valha o risco.
MINIMO_RELEVANTE = {"sharpe": 0.5, "retorno": 0.0, "fator_lucro": 1.2}


def diagnostico(resultado: ResultadoOtimizacao, criterio: str = "sharpe") -> str:
    """Uma leitura simples do que aconteceu entre o treino e o teste."""
    chave = CRITERIOS[criterio]
    treino = resultado.treino.metricas[chave]
    teste = resultado.teste.metricas[chave]
    total = len(resultado.ranking)
    posicao_teste = int(resultado.ranking[f"{criterio}_teste"]
                        .rank(ascending=False, method="min").iloc[0])

    texto = [f"A melhor combinação do treino ficou em {posicao_teste}º de {total} no teste."]
    if total > 2 and posicao_teste > total / 2:
        texto.append("Mais da metade das outras combinações foi melhor no teste: "
                     "escolher pelo treino não ajudou.")

    if resultado.teste.metricas["operacoes"] < 5:
        texto.append("Poucas operações no teste: o resultado diz pouco. Use mais dados.")
    elif treino < MINIMO_RELEVANTE[criterio]:
        texto.append(f"Nem no treino o {criterio} chegou a {MINIMO_RELEVANTE[criterio]}: "
                     "a estratégia não mostrou vantagem clara em nenhum período.")
    elif teste <= 0 or (criterio == "fator_lucro" and teste <= 1):
        texto.append("Funcionou no treino e falhou no teste: sinal clássico de overfitting. "
                     "Não use essa estratégia com dinheiro real.")
    elif teste < treino * 0.5:
        texto.append("O desempenho caiu bastante fora do treino. Trate o resultado do "
                     "treino como otimista demais.")
    else:
        texto.append("O resultado se manteve no teste. Bom sinal, mas confirme em "
                     "outros pares e períodos antes de confiar.")
    return "\n".join(texto)
