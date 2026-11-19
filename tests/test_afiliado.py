import hashlib
import json
from datetime import date
from pathlib import Path

from afiliado import legenda, pontuacao
from afiliado.historico import Historico
from afiliado.modelos import Produto
from afiliado.shopee.api import ShopeeAfiliados, converter_no


def _produto(**kw):
    base = dict(id="1", nome="Produto Teste", preco=100.0, taxa_comissao=0.1, vendas=1000,
                avaliacao=4.8, imagem_url="x.png", link_afiliado="https://s.shopee.com.br/x")
    base.update(kw)
    return Produto(**base)


def test_assinatura_segue_documentacao():
    c = ShopeeAfiliados("123", "segredo", "https://exemplo")
    payload = '{"query":"{ x }"}'
    esperado = hashlib.sha256(f"1231700000000{payload}segredo".encode()).hexdigest()
    assert c.assinar(payload, 1700000000) == esperado


class _RespostaFalsa:
    def __init__(self, dados): self.dados = dados
    def raise_for_status(self): pass
    def json(self): return self.dados


class _SessaoFalsa:
    def __init__(self, dados): self.dados, self.chamadas = dados, []
    def post(self, url, data, headers, timeout):
        self.chamadas.append((url, data, headers))
        return _RespostaFalsa(self.dados)


def test_buscar_ofertas_envia_cabecalho_assinado_e_converte():
    no = {"itemId": 99, "productName": "Fone", "price": "59.9", "commissionRate": "0.08",
          "sales": 1500, "ratingStar": "4.7", "imageUrl": "http://img", "offerLink": "http://l",
          "priceDiscountRate": 20}
    sessao = _SessaoFalsa({"data": {"productOfferV2": {"nodes": [no]}}})
    c = ShopeeAfiliados("app", "sec", "https://api", pausa_seg=0, sessao=sessao)
    [p] = c.buscar_ofertas("fone")
    url, corpo, cab = sessao.chamadas[0]
    assert cab["Authorization"].startswith("SHA256 Credential=app, Timestamp=")
    assert json.loads(corpo)["variables"]["keyword"] == "fone"
    assert (p.id, p.preco, p.taxa_comissao, p.nicho) == ("99", 59.9, 0.08, "fone")


def test_converter_comissao_em_porcentagem():
    assert converter_no({"commissionRate": "12", "price": "10"}).taxa_comissao == 0.12


def test_ganho_por_venda_e_preco_original():
    p = _produto(preco=70, taxa_comissao=0.1, desconto_pct=30)
    assert p.ganho_por_venda == 7.0
    assert p.preco_original == 100.0
    assert _produto(comissao_valor=5.5).ganho_por_venda == 5.5


def test_filtros_removem_produtos_ruins():
    f = pontuacao.Filtros()
    assert pontuacao.passa_filtros(_produto(), f)
    assert not pontuacao.passa_filtros(_produto(avaliacao=3.9), f)
    assert not pontuacao.passa_filtros(_produto(vendas=3), f)
    assert not pontuacao.passa_filtros(_produto(link_afiliado=""), f)


def test_pontuacao_prefere_mais_ganho_e_mais_vendas():
    bom = _produto(id="a", taxa_comissao=0.15, vendas=50000)
    fraco = _produto(id="b", taxa_comissao=0.03, vendas=60)
    assert [p.id for p in pontuacao.pontuar([fraco, bom])] == ["a", "b"]


def test_historico_evita_repeticao(tmp_path: Path):
    h = Historico(tmp_path / "h.json", dias_sem_repetir=7)
    h.registrar("x", date(2026, 1, 1))
    h.salvar()
    h2 = Historico(tmp_path / "h.json", dias_sem_repetir=7)
    assert h2.recente("x", date(2026, 1, 5))
    assert not h2.recente("x", date(2026, 1, 20))


def test_formatacao_brasileira():
    assert legenda.reais(1234.5) == "R$ 1.234,50"
    assert legenda.formatar_vendas(15400) == "+15 mil"
    texto = legenda.legenda(_produto(desconto_pct=20, nicho="cozinha"))
    assert "Link de afiliado" in texto and "#cozinha" in texto
