"""Linha de comando do backtest.

Exemplos:
    python -m backtest_forex --fonte sintetico
    python -m backtest_forex --fonte yahoo --par EURUSD --estrategia medias --curta 10 --longa 30
    python -m backtest_forex --fonte sintetico --stop 50 --alvo 100
    python -m backtest_forex --fonte csv --arquivo meus_dados.csv --estrategia rsi
"""

import argparse
from pathlib import Path

from . import backtest, dados, estrategias


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backtest educacional de estratégias de Forex.")
    p.add_argument("--fonte", choices=["yahoo", "csv", "sintetico"], default="yahoo")
    p.add_argument("--par", default="EURUSD", help="Ex.: EURUSD, GBPUSD, USDJPY")
    p.add_argument("--periodo", default="5y", help="Período no Yahoo (1y, 5y, max...)")
    p.add_argument("--arquivo", help="Caminho do CSV (com --fonte csv)")
    p.add_argument("--estrategia", choices=list(estrategias.ESTRATEGIAS), default="medias")
    p.add_argument("--curta", type=int, default=20, help="Média curta (estratégia medias)")
    p.add_argument("--longa", type=int, default=50, help="Média longa (estratégia medias)")
    p.add_argument("--so-compra", action="store_true", help="Não abre vendas (medias)")
    p.add_argument("--rsi-periodo", type=int, default=14)
    p.add_argument("--spread", type=float, default=1.0, help="Spread em pips")
    p.add_argument("--capital", type=float, default=10_000.0)
    p.add_argument("--alavancagem", type=float, default=1.0)
    p.add_argument("--stop", type=float, help="Stop loss em pips (ex.: 50)")
    p.add_argument("--alvo", type=float, help="Take profit em pips (ex.: 100)")
    p.add_argument("--grafico", action="store_true", help="Salva gráfico em resultados/")
    return p


def obter_dados(args):
    if args.fonte == "yahoo":
        return dados.baixar_yahoo(args.par, args.periodo)
    if args.fonte == "csv":
        if not args.arquivo:
            raise SystemExit("Use --arquivo com --fonte csv.")
        return dados.carregar_csv(args.arquivo)
    return dados.gerar_sinteticos()


def obter_sinal(args, df):
    if args.estrategia == "medias":
        return estrategias.cruzamento_medias(df, args.curta, args.longa,
                                             permite_venda=not args.so_compra)
    if args.estrategia == "rsi":
        return estrategias.rsi_reversao(df, args.rsi_periodo)
    return estrategias.comprar_e_segurar(df)


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


def main(argv=None):
    args = criar_parser().parse_args(argv)
    df = obter_dados(args)
    sinal = obter_sinal(args, df)
    resultado = backtest.executar(df, sinal, spread_pips=args.spread, par=args.par,
                                  capital_inicial=args.capital,
                                  alavancagem=args.alavancagem,
                                  stop_pips=args.stop, alvo_pips=args.alvo)

    titulo = f"{args.par} | {args.estrategia} | fonte: {args.fonte}"
    if args.stop or args.alvo:
        titulo += f" | stop: {args.stop or '-'} | alvo: {args.alvo or '-'} pips"
    print(f"\n{titulo}")
    print(f"Período: {df.index[0]:%d/%m/%Y} a {df.index[-1]:%d/%m/%Y} ({len(df)} candles)\n")
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
