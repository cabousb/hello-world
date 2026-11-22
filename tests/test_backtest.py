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


def candles(linhas):
    """linhas = [(open, high, low, close), ...]"""
    idx = pd.bdate_range("2024-01-01", periods=len(linhas))
    return pd.DataFrame(linhas, columns=["open", "high", "low", "close"], index=idx)


def test_stop_loss_limita_a_perda():
    # Entra comprado a 1.1000; o dia seguinte despenca até 1.0500.
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.1, 1.1, 1.05, 1.05)])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, stop_pips=20)
    ops = res.operacoes
    assert list(ops["motivo"]) == ["stop"]
    assert ops["retorno_%"].iloc[0] == pytest.approx((1.098 / 1.1 - 1) * 100)


def test_take_profit_garante_o_ganho():
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.1, 1.12, 1.1, 1.105)])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, alvo_pips=100)
    assert list(res.operacoes["motivo"]) == ["alvo"]
    assert res.metricas["retorno_total_%"] == pytest.approx((1.11 / 1.1 - 1) * 100)


def test_stop_em_operacao_vendida():
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.1, 1.13, 1.1, 1.12)])
    sinal = pd.Series(-1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, stop_pips=50)
    assert list(res.operacoes["motivo"]) == ["stop"]
    assert res.metricas["retorno_total_%"] == pytest.approx(-(1.105 / 1.1 - 1) * 100)


def test_gap_sai_pior_que_o_stop():
    # Abre já 300 pips abaixo: o stop de 20 pips é executado na abertura.
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.07, 1.08, 1.06, 1.075)])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, stop_pips=20)
    assert res.metricas["retorno_total_%"] == pytest.approx((1.07 / 1.1 - 1) * 100)


def test_stop_e_alvo_no_mesmo_candle_assume_stop():
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.1, 1.2, 1.0, 1.1)])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, stop_pips=50, alvo_pips=50)
    assert list(res.operacoes["motivo"]) == ["stop"]


def test_nao_reentra_apos_stop_enquanto_sinal_nao_muda():
    df = candles([(1.1, 1.1, 1.1, 1.1), (1.1, 1.1, 1.09, 1.09),
                  (1.09, 1.1, 1.09, 1.1), (1.1, 1.1, 1.1, 1.1)])
    sinal = pd.Series(1.0, index=df.index)
    res = backtest.executar(df, sinal, spread_pips=0, stop_pips=50)
    assert len(res.operacoes) == 1
    assert (res.dados["posicao"].iloc[2:] == 0).all()


def test_sem_stop_nada_muda():
    df = dados.gerar_sinteticos(dias=300)
    sinal = estrategias.cruzamento_medias(df, 5, 20)
    res = backtest.executar(df, sinal, spread_pips=1)
    assert res.metricas["saidas_stop"] == 0
    assert res.metricas["saidas_alvo"] == 0


def test_stop_invalido():
    df = dados.gerar_sinteticos(dias=50)
    with pytest.raises(ValueError):
        backtest.executar(df, pd.Series(1.0, index=df.index), stop_pips=-5)


def cenario_fibonacci():
    """Alta de 1.00 a 1.10, correção até 1.05 (50%) e candle de rejeição."""
    linhas = [(1.00, 1.00, 1.00, 1.00)]
    for i in range(1, 11):  # sobe 100 pips por dia até 1.10
        p = 1.00 + i * 0.01
        linhas.append((p - 0.01, p, p - 0.01, p))
    linhas += [
        (1.10, 1.10, 1.08, 1.08),
        (1.08, 1.08, 1.06, 1.06),
        (1.06, 1.065, 1.049, 1.062),  # toca 50%, fecha positivo acima de 61,8%
        (1.062, 1.08, 1.06, 1.078),
        (1.078, 1.101, 1.075, 1.09),  # atinge o topo (alvo)
    ]
    return candles(linhas)


def test_fibonacci_gera_compra_na_zona():
    df = cenario_fibonacci()
    tabela = estrategias.fibonacci(df, janela=14)
    t = 13  # candle de rejeição
    assert tabela["sinal"].iloc[t] == 1
    assert (tabela["sinal"].drop(df.index[t]) == 0).all()
    assert tabela["preco_stop"].iloc[t] == pytest.approx(1.10 - 0.786 * 0.10)
    assert tabela["preco_alvo"].iloc[t] == pytest.approx(1.10)


def test_fibonacci_nao_olha_o_futuro():
    df = dados.gerar_sinteticos(dias=400, semente=7)
    completo = estrategias.fibonacci(df, janela=30)
    for t in (100, 200, 399):
        parcial = estrategias.fibonacci(df.iloc[:t + 1], janela=30)
        pd.testing.assert_series_equal(parcial["sinal"], completo["sinal"].iloc[:t + 1])


def test_modo_gatilho_segura_ate_o_alvo():
    df = cenario_fibonacci()
    tabela = estrategias.fibonacci(df, janela=14)
    res = backtest.executar(df, tabela, spread_pips=0)
    ops = res.operacoes
    assert list(ops["motivo"]) == ["alvo"]
    assert ops["dias"].iloc[0] == 2  # segura mesmo com o sinal voltando a 0
    assert res.metricas["retorno_total_%"] == pytest.approx((1.10 / 1.062 - 1) * 100)


def test_fibonacci_parametros_invalidos():
    with pytest.raises(ValueError):
        estrategias.fibonacci(dados.gerar_sinteticos(100), zona_inicio=0.7, zona_fim=0.6)
