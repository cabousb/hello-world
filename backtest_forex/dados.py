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


# Intervalos aceitos. O Yahoo não tem 4h: montamos a partir do 1h.
INTERVALOS = ["1d", "4h", "1h", "30m", "15m", "5m"]

# Histórico máximo que o Yahoo entrega em cada intervalo intradiário.
LIMITE_PERIODO_YAHOO = {"4h": "730d", "1h": "730d", "30m": "60d", "15m": "60d", "5m": "60d"}


def _periodo_em_dias(periodo: str) -> float:
    """'5y' -> 1826, '6mo' -> 183, '60d' -> 60, 'max' -> infinito."""
    periodo = periodo.strip().lower()
    if periodo == "max":
        return float("inf")
    for sufixo, dias in (("mo", 30.44), ("y", 365.25), ("d", 1), ("wk", 7)):
        if periodo.endswith(sufixo) and periodo[:-len(sufixo)].isdigit():
            return int(periodo[:-len(sufixo)]) * dias
    raise ValueError(f"Período inválido: {periodo!r}. Use algo como 60d, 6mo, 2y ou max.")


def ajustar_periodo(periodo: str, intervalo: str) -> tuple[str, str | None]:
    """Limita o período ao máximo do Yahoo para o intervalo. Devolve (período, aviso)."""
    limite = LIMITE_PERIODO_YAHOO.get(intervalo)
    if limite and _periodo_em_dias(periodo) > _periodo_em_dias(limite):
        return limite, (f"O Yahoo só tem {limite} de histórico no intervalo {intervalo}; "
                        f"usando {limite} em vez de {periodo}.")
    return periodo, None


def reamostrar(df: pd.DataFrame, intervalo: str) -> pd.DataFrame:
    """Junta candles menores em maiores. Ex.: quatro candles de 1h viram um de 4h."""
    agregado = df.resample(intervalo).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"})
    return agregado.dropna()  # fins de semana e horários sem negociação somem


def baixar_yahoo(par: str = "EURUSD", periodo: str = "5y", intervalo: str = "1d") -> pd.DataFrame:
    """Baixa dados do Yahoo Finance. Ex.: par='EURUSD' vira o ticker 'EURUSD=X'.

    intervalo: 1d, 4h, 1h, 30m, 15m ou 5m. O período é limitado ao que o
    Yahoo oferece (ex.: 730 dias no 1h, 60 dias no 15m).
    """
    import yfinance as yf  # import aqui para o resto funcionar sem a biblioteca

    if intervalo not in INTERVALOS:
        raise ValueError(f"Intervalo inválido: {intervalo}. Use um de {INTERVALOS}.")
    periodo, _ = ajustar_periodo(periodo, intervalo)
    ticker = par if par.endswith("=X") else f"{par}=X"
    intervalo_yahoo = "1h" if intervalo == "4h" else intervalo
    df = yf.download(ticker, period=periodo, interval=intervalo_yahoo,
                     progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):  # versões novas do yfinance
        df.columns = df.columns.get_level_values(0)
    df = _padronizar(df)
    if df.index.tz is not None:  # horários em UTC, sem o "+00:00" nas tabelas
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    if intervalo == "4h":
        df = reamostrar(df, "4h")
    return df


def carregar_csv(caminho: str, coluna_data: str = "date") -> pd.DataFrame:
    """Lê um CSV com colunas date, open, high, low, close."""
    df = pd.read_csv(caminho)
    df.columns = [c.strip().lower() for c in df.columns]
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    return _padronizar(df.set_index(coluna_data))


# Frequência do pandas e candles por ano de cada intervalo, para os dados sintéticos.
FREQUENCIAS = {"1d": ("B", 252), "4h": ("4h", 260 * 6), "1h": ("h", 260 * 24),
               "30m": ("30min", 260 * 48), "15m": ("15min", 260 * 96),
               "5m": ("5min", 260 * 288)}


def gerar_sinteticos(dias: int = 1500, preco_inicial: float = 1.10,
                     volatilidade_anual: float = 0.08, semente: int = 42,
                     intervalo: str = "1d") -> pd.DataFrame:
    """Gera preços aleatórios (passeio aleatório geométrico).

    `dias` é a quantidade de CANDLES gerados. Nos intervalos intradiários,
    sábados e domingos ficam de fora, como no Forex.

    Não existe padrão nenhum nesses dados: se uma estratégia "lucra" aqui,
    foi sorte. Ótimo para lembrar que resultado bom em backtest não prova nada.
    """
    if intervalo not in FREQUENCIAS:
        raise ValueError(f"Intervalo inválido: {intervalo}. Use um de {INTERVALOS}.")
    frequencia, por_ano = FREQUENCIAS[intervalo]
    rng = np.random.default_rng(semente)
    fim = pd.Timestamp.today().normalize()
    if intervalo == "1d":
        datas = pd.bdate_range(end=fim, periods=dias)
    else:
        # gera a mais e descarta o fim de semana
        candidatas = pd.date_range(end=fim, periods=int(dias * 1.5) + 10, freq=frequencia)
        datas = candidatas[candidatas.dayofweek < 5][-dias:]
    vol_candle = volatilidade_anual / np.sqrt(por_ano)
    retornos = rng.normal(0, vol_candle, dias)
    close = preco_inicial * np.exp(np.cumsum(retornos))
    open_ = np.concatenate([[preco_inicial], close[:-1]])
    amplitude = np.abs(rng.normal(0, vol_candle / 2, dias)) * close
    high = np.maximum(open_, close) + amplitude
    low = np.minimum(open_, close) - amplitude
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=datas)
