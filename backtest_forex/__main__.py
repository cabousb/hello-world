"""Linha de comando do backtest.

Exemplos:
    python -m backtest_forex --par EURUSD
    python -m backtest_forex --par EURUSD --intervalo 1h --janela 30 --alvo-niveis 2
    python -m backtest_forex --par GBPUSD --intervalo 4h --otimizar --grafico
    python -m backtest_forex --fonte sintetico
    python -m backtest_forex --fonte csv --arquivo meus_dados.csv
"""

import argparse
from pathlib import Path

from . import backtest, dados, estrategias, otimizacao


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backtest educacional de estratégias de Forex.")
    p.add_argument("--fonte", choices=["yahoo", "csv", "sintetico"], default="yahoo")
    p.add_argument("--par", default="EURUSD", help="Ex.: EURUSD, GBPUSD, USDJPY")
    p.add_argument("--periodo", default="5y", help="Período no Yahoo (60d, 1y, 5y, max...)")
    p.add_argument("--intervalo", choices=dados.INTERVALOS, default="1d",
                   help="Tempo gráfico: 1d, 4h, 1h, 30m, 15m ou 5m (padrão 1d)")
    p.add_argument("--arquivo", help="Caminho do CSV (com --fonte csv)")
    p.add_argument("--estrategia", choices=list(estrategias.ESTRATEGIAS), default="fimathe")
    p.add_argument("--janela", type=int, default=20,
                   help="Candles usados para montar o canal de referência (padrão 20)")
    p.add_argument("--entrada", type=float, default=0.5,
                   help="Quanto além do canal o preço precisa fechar para entrar (0.5 = 50%%)")
    p.add_argument("--stop-nivel", type=float, default=-0.5,
                   help="Stop inicial, em tamanhos de canal a partir da borda (-0.5 = meio do canal)")
    p.add_argument("--alvo-niveis", type=float,
                   help="Alvo fixo em tamanhos de canal (ex.: 2). Sem ele, sai só pelo stop móvel")
    p.add_argument("--sem-stop-movel", action="store_true",
                   help="Desliga o stop móvel por níveis")
    p.add_argument("--tamanho-minimo", type=float, default=0.0,
                   help="Ignora canais menores que X%% do preço")
    p.add_argument("--tamanho-maximo", type=float,
                   help="Ignora canais maiores que X%% do preço (stop longe demais)")
    p.add_argument("--spread", type=float, default=1.0, help="Spread em pips")
    p.add_argument("--capital", type=float, default=10_000.0)
    p.add_argument("--alavancagem", type=float, default=1.0)
    p.add_argument("--otimizar", action="store_true",
                   help="Escolhe os parâmetros no treino e avalia no teste")
    p.add_argument("--treino", type=float, default=0.7,
                   help="Fração dos dados usada como treino (padrão 0.7 = 70%%)")
    p.add_argument("--criterio", choices=list(otimizacao.CRITERIOS), default="sharpe",
                   help="Métrica usada para escolher a melhor combinação")
    p.add_argument("--grafico", action="store_true", help="Salva gráfico em resultados/")
    return p


def obter_dados(args):
    if args.fonte == "yahoo":
        _, aviso = dados.ajustar_periodo(args.periodo, args.intervalo)
        if aviso:
            print(f"Aviso: {aviso}")
        return dados.baixar_yahoo(args.par, args.periodo, args.intervalo)
    if args.fonte == "csv":
        if not args.arquivo:
            raise SystemExit("Use --arquivo com --fonte csv.")
        if args.intervalo != "1d":
            print("Aviso: com --fonte csv, o tempo gráfico é o do arquivo; --intervalo é ignorado.")
        return dados.carregar_csv(args.arquivo)
    return dados.gerar_sinteticos(intervalo=args.intervalo)


def parametros_estrategia(args) -> dict:
    return {"janela": args.janela, "alvo_niveis": args.alvo_niveis}


def parametros_fixos(args) -> dict:
    """Opções que não entram na otimização, mas valem para a estratégia."""
    return {"entrada": args.entrada, "stop": args.stop_nivel,
            "stop_movel": not args.sem_stop_movel,
            "tamanho_minimo_pct": args.tamanho_minimo,
            "tamanho_maximo_pct": args.tamanho_maximo}


def obter_sinal(args, df):
    funcao = estrategias.ESTRATEGIAS[args.estrategia]
    return funcao(df, **parametros_estrategia(args), **parametros_fixos(args))


def salvar_grafico(resultado, titulo: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")  # salva em arquivo, sem abrir janela
    import matplotlib.pyplot as plt

    d = resultado.dados
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(d.index, d["patrimonio"], label="Estratégia")
    ax1.plot(d.index, d["patrimonio_mercado"], label="Comprar e segurar", alpha=0.7)
    ax1.set_title(titulo)
    ax1.set_ylabel("Patrimônio")
    ax1.legend()
    ax1.grid(alpha=0.3)

    queda = (d["patrimonio"] / d["patrimonio"].cummax() - 1) * 100
    ax2.fill_between(d.index, queda, 0, color="tab:red", alpha=0.4)
    ax2.set_ylabel("Queda (%)")
    ax2.grid(alpha=0.3)

    pasta = Path("resultados")
    pasta.mkdir(exist_ok=True)
    caminho = pasta / "backtest.png"
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def formatar_data(data) -> str:
    """Mostra a hora só quando ela importa (gráficos intradiários)."""
    if data.hour or data.minute:
        return f"{data:%d/%m/%Y %H:%M}"
    return f"{data:%d/%m/%Y}"


def descrever_periodo(df) -> str:
    return f"{formatar_data(df.index[0])} a {formatar_data(df.index[-1])} ({len(df)} candles)"


def salvar_grafico_treino_teste(resultado, titulo: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    treino, teste = resultado.treino.dados, resultado.teste.dados
    # O teste continua do capital final do treino, para formar uma curva só.
    escala = treino["patrimonio"].iloc[-1] / teste["patrimonio"].iloc[0]
    escala_mercado = treino["patrimonio_mercado"].iloc[-1] / teste["patrimonio_mercado"].iloc[0]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(treino.index, treino["patrimonio"], color="tab:blue", label="Estratégia (treino)")
    ax.plot(teste.index, teste["patrimonio"] * escala, color="tab:green",
            label="Estratégia (teste)")
    ax.plot(treino.index, treino["patrimonio_mercado"], color="gray", alpha=0.5,
            label="Comprar e segurar")
    ax.plot(teste.index, teste["patrimonio_mercado"] * escala_mercado, color="gray", alpha=0.5)
    ax.axvline(resultado.data_corte, color="black", linestyle="--")
    ax.axvspan(resultado.data_corte, teste.index[-1], color="tab:green", alpha=0.06)
    ax.text(resultado.data_corte, ax.get_ylim()[1], "  início do teste", va="top")
    ax.set_title(titulo)
    ax.set_ylabel("Patrimônio")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)

    pasta = Path("resultados")
    pasta.mkdir(exist_ok=True)
    caminho = pasta / "treino_teste.png"
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    return caminho


def executar_otimizacao(args, df, opcoes_backtest):
    resultado = otimizacao.otimizar(
        df, args.estrategia, proporcao_treino=args.treino, criterio=args.criterio,
        parametros_fixos=parametros_fixos(args), opcoes_backtest=opcoes_backtest)
    treino, teste = resultado.treino.dados, resultado.teste.dados

    titulo = f"{args.par} {args.intervalo} | {args.estrategia} | treino x teste | fonte: {args.fonte}"
    print(f"\n{titulo}")
    print(f"Treino: {descrever_periodo(treino)}")
    print(f"Teste:  {descrever_periodo(teste)}")

    ranking = resultado.ranking
    print(f"\nCombinações testadas: {len(ranking)}. As 5 melhores no treino "
          f"(critério: {args.criterio}):")
    print(ranking.drop(columns="valido").head(5).to_string(float_format="%.2f"))
    if not ranking["valido"].all():
        print(f"({(~ranking['valido']).sum()} combinações com menos de 5 operações "
              "no treino foram para o fim da lista)")

    print(f"\nEscolhida: {otimizacao.formatar_parametros(resultado.melhores_parametros)}\n")
    print(otimizacao.comparar_metricas(resultado))
    print("\n" + otimizacao.diagnostico(resultado, args.criterio))

    if args.fonte == "sintetico":
        print("\nAtenção: dados sintéticos são aleatórios. Qualquer lucro aqui é sorte.")
    if args.grafico:
        print(f"\nGráfico salvo em {salvar_grafico_treino_teste(resultado, titulo)}")


def main(argv=None):
    args = criar_parser().parse_args(argv)
    df = obter_dados(args)
    opcoes_backtest = {"spread_pips": args.spread, "par": args.par,
                       "capital_inicial": args.capital, "alavancagem": args.alavancagem}
    if args.otimizar:
        executar_otimizacao(args, df, opcoes_backtest)
        return
    sinal = obter_sinal(args, df)
    resultado = backtest.executar(df, sinal, **opcoes_backtest)

    titulo = f"{args.par} {args.intervalo} | {args.estrategia} | fonte: {args.fonte}"
    titulo += f" | janela {args.janela}"
    if args.alvo_niveis:
        titulo += f" | alvo {args.alvo_niveis:g} níveis"
    print(f"\n{titulo}")
    print(f"Período: {descrever_periodo(df)}\n")
    print(backtest.formatar_metricas(resultado.metricas))

    if not resultado.operacoes.empty:
        print("\nÚltimas operações:")
        print(resultado.operacoes.tail(5).to_string(index=False, float_format="%.2f"))

    if args.fonte == "sintetico":
        print("\nAtenção: dados sintéticos são aleatórios. Qualquer lucro aqui é sorte.")

    if args.grafico:
        print(f"\nGráfico salvo em {salvar_grafico(resultado, titulo)}")


if __name__ == "__main__":
    main()
