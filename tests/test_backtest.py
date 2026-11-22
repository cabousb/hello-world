import numpy as np
import pandas as pd
import pytest

from backtest_forex import backtest, dados, estrategias, otimizacao


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


def sinal_alternado(df, periodo=10):
    """Compra 10 candles, vende 10, e assim por diante (só para testar o motor)."""
    valores = [1.0 if (i // periodo) % 2 == 0 else -1.0 for i in range(len(df))]
    return pd.Series(valores, index=df.index)


def test_spread_reduz_resultado():
    df = dados.gerar_sinteticos(dias=300)
    sinal = sinal_alternado(df)
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
    sinal = sinal_alternado(df)
    res = backtest.executar(df, sinal, spread_pips=1)
    assert res.metricas["saidas_stop"] == 0
    assert res.metricas["saidas_alvo"] == 0


def test_stop_invalido():
    df = dados.gerar_sinteticos(dias=50)
    with pytest.raises(ValueError):
        backtest.executar(df, pd.Series(1.0, index=df.index), stop_pips=-5)


def test_dividir_respeita_a_ordem_do_tempo():
    df = dados.gerar_sinteticos(dias=100)
    treino, teste = otimizacao.dividir(df, 0.7)
    assert len(treino) == 70 and len(teste) == 30
    assert treino.index.max() < teste.index.min()


def test_dividir_invalido():
    with pytest.raises(ValueError):
        otimizacao.dividir(dados.gerar_sinteticos(dias=100), 1.5)


def test_escolha_usa_so_o_treino():
    df = dados.gerar_sinteticos(dias=600, semente=3)
    res = otimizacao.otimizar(df, "fimathe", criterio="sharpe")
    validos = res.ranking[res.ranking["valido"]]
    assert res.ranking["sharpe_treino"].iloc[0] == validos["sharpe_treino"].max()
    assert res.treino.metricas["sharpe"] == pytest.approx(res.ranking["sharpe_treino"].iloc[0])
    assert res.teste.dados.index[0] == res.data_corte


def test_teste_nao_depende_de_dados_do_futuro_do_treino():
    # Alterar os preços do período de teste não pode mudar o resultado do treino.
    df = dados.gerar_sinteticos(dias=600, semente=5)
    alterado = df.copy()
    alterado.iloc[420:] *= 1.5
    a = otimizacao.otimizar(df, "fimathe")
    b = otimizacao.otimizar(alterado, "fimathe")
    pd.testing.assert_series_equal(a.ranking["sharpe_treino"], b.ranking["sharpe_treino"])


def test_ajustar_periodo_respeita_limite_do_yahoo():
    assert dados.ajustar_periodo("5y", "1h")[0] == "730d"
    assert dados.ajustar_periodo("1y", "15m")[0] == "60d"
    assert dados.ajustar_periodo("30d", "15m") == ("30d", None)
    assert dados.ajustar_periodo("5y", "1d") == ("5y", None)
    with pytest.raises(ValueError):
        dados.ajustar_periodo("cinco anos", "1h")


def test_reamostrar_1h_para_4h():
    idx = pd.date_range("2024-01-01 00:00", periods=8, freq="h")
    df = pd.DataFrame({"open": range(8), "high": [x + 10 for x in range(8)],
                       "low": [x - 10 for x in range(8)], "close": [x + 0.5 for x in range(8)]},
                      index=idx, dtype=float)
    r = dados.reamostrar(df, "4h")
    assert len(r) == 2
    assert r.iloc[0].to_dict() == {"open": 0, "high": 13, "low": -10, "close": 3.5}


def test_sinteticos_intradiarios_sem_fim_de_semana():
    df = dados.gerar_sinteticos(dias=500, intervalo="1h")
    assert len(df) == 500
    assert (df.index.dayofweek < 5).all()
    assert (df.index.to_series().diff().dropna().min()) == pd.Timedelta(hours=1)


def test_candles_por_ano_se_adapta_ao_intervalo():
    diario = dados.gerar_sinteticos(dias=520, intervalo="1d")
    horario = dados.gerar_sinteticos(dias=520 * 24, intervalo="1h")
    assert 240 < backtest.candles_por_ano(diario.index) < 270
    assert 5800 < backtest.candles_por_ano(horario.index) < 6500


def test_volatilidade_anual_nao_muda_so_por_trocar_o_intervalo():
    # Mesma volatilidade anual nos dois tempos gráficos: a métrica anualizada deve bater.
    for intervalo, n in (("1d", 1000), ("1h", 1000 * 24)):
        df = dados.gerar_sinteticos(dias=n, intervalo=intervalo, semente=1)
        m = backtest.executar(df, pd.Series(1.0, index=df.index), spread_pips=0).metricas
        assert 5 < m["volatilidade_anual_%"] < 11


# ---------- Fimathe ----------

def cenario_fimathe(depois):
    """Canal de 1.1000 a 1.1050 (50 pips) por 20 candles; depois, os candles dados."""
    linhas = [(1.1025, 1.1050, 1.1000, 1.1025)] * 20
    return candles(linhas + depois)


def test_fimathe_entra_apos_50_por_cento():
    df = cenario_fimathe([
        (1.1025, 1.1060, 1.1020, 1.1055),  # rompe o topo: canal congela
        (1.1055, 1.1080, 1.1050, 1.1078),  # fecha acima de 1.1075 (+50%): COMPRA
        (1.1078, 1.1090, 1.1070, 1.1085),
    ])
    tabela = estrategias.fimathe(df, janela=20)
    assert tabela["sinal"].iloc[20] == 0  # só rompeu, ainda na zona neutra
    assert tabela["sinal"].iloc[21] == 1
    assert tabela["preco_stop"].iloc[21] == pytest.approx(1.1025)  # meio do canal
    assert tabela["base_trailing"].iloc[21] == pytest.approx(1.1050)
    assert tabela["passo_trailing"].iloc[21] == pytest.approx(0.0050)


def test_fimathe_venda_espelhada():
    df = cenario_fimathe([
        (1.1025, 1.1030, 1.0990, 1.0995),
        (1.0995, 1.1000, 1.0970, 1.0972),  # abaixo de 1.0975 (-50%): VENDA
    ])
    tabela = estrategias.fimathe(df, janela=20)
    assert tabela["sinal"].iloc[21] == -1
    assert tabela["preco_stop"].iloc[21] == pytest.approx(1.1025)
    assert tabela["base_trailing"].iloc[21] == pytest.approx(1.1000)


def test_fimathe_nao_entra_atrasado():
    # Um candle só leva o preço para além de 100% do canal: entrada atrasada.
    df = cenario_fimathe([(1.1025, 1.1120, 1.1020, 1.1110)])
    assert (estrategias.fimathe(df, janela=20)["sinal"] == 0).all()


def test_fimathe_alvo_em_niveis():
    df = cenario_fimathe([(1.1025, 1.1060, 1.1020, 1.1055), (1.1055, 1.1080, 1.1050, 1.1078)])
    tabela = estrategias.fimathe(df, janela=20, alvo_niveis=2)
    assert tabela["preco_alvo"].iloc[21] == pytest.approx(1.1150)


def test_fimathe_nao_olha_o_futuro():
    df = dados.gerar_sinteticos(dias=400, semente=7)
    completo = estrategias.fimathe(df, janela=15)
    for t in (100, 250, 399):
        parcial = estrategias.fimathe(df.iloc[:t + 1], janela=15)
        pd.testing.assert_frame_equal(parcial, completo.iloc[:t + 1])


def test_fimathe_parametros_invalidos():
    df = dados.gerar_sinteticos(dias=100)
    with pytest.raises(ValueError):
        estrategias.fimathe(df, entrada=1.2, entrada_maxima=1.0)
    with pytest.raises(ValueError):
        estrategias.fimathe(df, stop=0.2)
    with pytest.raises(ValueError):
        estrategias.fimathe(df, alvo_niveis=0.3)


def test_stop_movel_sobe_de_nivel_em_nivel():
    # Compra a 1.1078 (canal 1.1000-1.1050). O preço chega a 1.1150 (nível 2):
    # o stop sobe para o nível 1 (1.1100). Depois cai e sai em 1.1100, com lucro.
    df = cenario_fimathe([
        (1.1025, 1.1060, 1.1020, 1.1055),
        (1.1055, 1.1080, 1.1050, 1.1078),  # sinal
        (1.1078, 1.1110, 1.1075, 1.1105),  # entrada no fechamento anterior; nível 1
        (1.1105, 1.1155, 1.1100, 1.1150),  # nível 2: stop vai para 1.1100
        (1.1150, 1.1150, 1.1090, 1.1095),  # cai e toca 1.1100: sai
    ])
    res = backtest.executar(df, estrategias.fimathe(df, janela=20), spread_pips=0)
    ops = res.operacoes
    assert list(ops["motivo"]) == ["stop móvel"]
    assert ops["retorno_%"].iloc[0] == pytest.approx((1.1100 / 1.1078 - 1) * 100)


def test_stop_movel_nao_anda_para_tras():
    stop, extremo = backtest.mover_stop(1, 1.1025, 1.1050, 0.005, None, 1.1155, 1.11)
    assert stop == pytest.approx(1.1100)
    stop, extremo = backtest.mover_stop(1, stop, 1.1050, 0.005, extremo, 1.1060, 1.10)
    assert stop == pytest.approx(1.1100)


def test_sem_stop_movel_sai_so_no_stop_inicial():
    df = cenario_fimathe([
        (1.1025, 1.1060, 1.1020, 1.1055),
        (1.1055, 1.1080, 1.1050, 1.1078),
        (1.1078, 1.1110, 1.1075, 1.1105),
        (1.1105, 1.1155, 1.1100, 1.1150),
        (1.1150, 1.1150, 1.1090, 1.1095),
    ])
    tabela = estrategias.fimathe(df, janela=20, stop_movel=False)
    res = backtest.executar(df, tabela, spread_pips=0)
    assert list(res.operacoes["motivo"]) == ["em aberto"]
