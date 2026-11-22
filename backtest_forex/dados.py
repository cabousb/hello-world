"""Carregamento de dados de preço.

Três fontes possíveis:
- baixar_yahoo: baixa dados reais do Yahoo Finance (precisa de internet).
- carregar_csv: lê um arquivo CSV seu (ex.: exportado do MetaTrader).
- gerar_sinteticos: cria preços aleatórios, útil para testar o código.

Todas devolvem um DataFrame com índice de datas e as colunas
open, high, low, close (em minúsculas).
"""

import numpy as np
import pandas as pd

COLUNAS = ["open", "high", "low", "close"]


def _padronizar(df: pd.DataFrame) -> pd.DataFrame:
    """Deixa os nomes das colunas em minúsculas e mantém só OHLC."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes nos dados: {faltando}")
    df = df[COLUNAS].dropna().sort_index()
    if df.empty:
        raise ValueError("Nenhum dado de preço encontrado.")
    return df


def baixar_yahoo(par: str = "EURUSD", periodo: str = "5y", intervalo: str = "1d") -> pd.DataFrame:
    """Baixa dados do Yahoo Finance. Ex.: par='EURUSD' vira o ticker 'EURUSD=X'."""
    import yfinance as yf  # import aqui para o resto funcionar sem a biblioteca

    ticker = par if par.endswith("=X") else f"{par}=X"
    df = yf.download(ticker, period=periodo, interval=intervalo,
                     progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):  # versões novas do yfinance
        df.columns = df.columns.get_level_values(0)
    return _padronizar(df)


def carregar_csv(caminho: str, coluna_data: str = "date") -> pd.DataFrame:
    """Lê um CSV com colunas date, open, high, low, close."""
    df = pd.read_csv(caminho)
    df.columns = [c.strip().lower() for c in df.columns]
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    return _padronizar(df.set_index(coluna_data))


def gerar_sinteticos(dias: int = 1500, preco_inicial: float = 1.10,
                     volatilidade_anual: float = 0.08, semente: int = 42) -> pd.DataFrame:
    """Gera preços aleatórios (passeio aleatório geométrico).

    Não existe padrão nenhum nesses dados: se uma estratégia "lucra" aqui,
    foi sorte. Ótimo para lembrar que resultado bom em backtest não prova nada.
    """
    rng = np.random.default_rng(semente)
    datas = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=dias)
    vol_diaria = volatilidade_anual / np.sqrt(252)
    retornos = rng.normal(0, vol_diaria, dias)
    close = preco_inicial * np.exp(np.cumsum(retornos))
    open_ = np.concatenate([[preco_inicial], close[:-1]])
    amplitude = np.abs(rng.normal(0, vol_diaria / 2, dias)) * close
    high = np.maximum(open_, close) + amplitude
    low = np.minimum(open_, close) - amplitude
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=datas)
