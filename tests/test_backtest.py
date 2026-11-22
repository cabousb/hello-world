import numpy as np
import pandas as pd
import pytest

from backtest_forex import backtest, dados, estrategias


def precos(valores):
    idx = pd.bdate_range("2024-01-01", periods=len(valores))
    v = np.array(valores, dtype=float)
    return pd.DataFrame({"open": v, "high": v, "low": v, "close": v}, index=idx)


def test_sinal_so_vale_no_dia_seguinte():
    # Preço sobe 10% no dia 2. O sinal de compra do dia 2 não pode capturar essa alta.
    df = precos([1.0, 1.0, 1.1, 1.1])
    sinal = pd.Series([0, 0, 1, 1], index=df.index, dtype=float)
    res = backtest.executar(df, sinal, spread_pips=0)
    assert res.metricas["retorno_total_%"] == pytest.approx(0.0)


def test_comprado_numa_alta_lucra():
    df = precos([1.0, 1.0, 1.1])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0)
    assert res.metricas["retorno_total_%"] == pytest.approx(10.0)


def test_vendido_numa_alta_perde():
    df = precos([1.0, 1.0, 1.1])
    sinal = pd.Series(-1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0)
    assert res.metricas["retorno_total_%"] == pytest.approx(-10.0)


def test_spread_reduz_resultado():
    df = dados.gerar_sinteticos(dias=300)
    sinal = estrategias.cruzamento_medias(df, 5, 20)
    sem = backtest.executar(df, sinal, spread_pips=0).metricas["retorno_total_%"]
    com = backtest.executar(df, sinal, spread_pips=3).metricas["retorno_total_%"]
    assert com < sem


def test_alavancagem_extrema_zera_a_conta():
    df = precos([1.0, 1.0, 0.98])  # queda de 2%
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, alavancagem=100)
    assert res.metricas["capital_final"] == pytest.approx(0.0)


def test_extrair_operacoes():
    df = precos([1.0, 1.0, 1.1, 1.1, 1.0, 1.0])
    sinal = pd.Series([1, 1, 0, -1, -1, 0], index=df.index, dtype=float)
    ops = backtest.executar(df, sinal, spread_pips=0).operacoes
    assert list(ops["direcao"]) == ["compra", "venda"]


def test_rsi_entre_0_e_100():
    df = dados.gerar_sinteticos(dias=500)
    rsi = estrategias.calcular_rsi(df["close"]).dropna()
    assert rsi.between(0, 100).all()


def test_medias_invalidas():
    with pytest.raises(ValueError):
        estrategias.cruzamento_medias(dados.gerar_sinteticos(100), 50, 20)


def test_carregar_csv(tmp_path):
    arquivo = tmp_path / "dados.csv"
    arquivo.write_text("Date,Open,High,Low,Close\n2024-01-02,1.1,1.2,1.0,1.15\n"
                       "2024-01-01,1.0,1.1,0.9,1.05\n")
    df = dados.carregar_csv(str(arquivo))
    assert list(df.columns) == ["open", "high", "low", "close"]
    assert df.index.is_monotonic_increasing
