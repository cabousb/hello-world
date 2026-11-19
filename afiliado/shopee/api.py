"""Cliente da Shopee Affiliate Open API (GraphQL).

Autenticação (documentação oficial do painel de afiliados):
    Authorization: SHA256 Credential={AppId}, Timestamp={ts}, Signature={assinatura}
    assinatura = sha256(AppId + Timestamp + Payload + Secret)  (hex)
onde Payload é exatamente o corpo JSON enviado na requisição.
"""

from __future__ import annotations

import hashlib
import json
import time

import requests

from ..modelos import Produto

# Valores aceitos em productOfferV2(sortType: ...)
ORDEM_RELEVANCIA = 1
ORDEM_MAIS_VENDIDOS = 2
ORDEM_MAIOR_PRECO = 3
ORDEM_MENOR_PRECO = 4
ORDEM_MAIOR_COMISSAO = 5

_CAMPOS_PRODUTO = """
    itemId productName shopName price priceMin priceMax
    commissionRate commission sales ratingStar priceDiscountRate
    imageUrl productLink offerLink
"""


class ErroShopee(RuntimeError):
    pass


class ShopeeAfiliados:
    def __init__(self, app_id: str, secret: str, endpoint: str, pausa_seg: float = 0.4,
                 sessao: requests.Session | None = None):
        self.app_id = app_id
        self.secret = secret
        self.endpoint = endpoint
        self.pausa_seg = pausa_seg  # respeita o limite de requisições da API
        self.sessao = sessao or requests.Session()

    # ------------------------------------------------------------------ baixo nível
    def assinar(self, payload: str, timestamp: int) -> str:
        base = f"{self.app_id}{timestamp}{payload}{self.secret}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def consultar(self, query: str, variaveis: dict | None = None) -> dict:
        corpo = {"query": query}
        if variaveis:
            corpo["variables"] = variaveis
        payload = json.dumps(corpo, separators=(",", ":"), ensure_ascii=False)
        ts = int(time.time())
        cabecalhos = {
            "Content-Type": "application/json",
            "Authorization": (
                f"SHA256 Credential={self.app_id}, Timestamp={ts}, "
                f"Signature={self.assinar(payload, ts)}"
            ),
        }
        resp = self.sessao.post(self.endpoint, data=payload.encode("utf-8"),
                                headers=cabecalhos, timeout=30)
        resp.raise_for_status()
        dados = resp.json()
        if dados.get("errors"):
            raise ErroShopee(json.dumps(dados["errors"], ensure_ascii=False))
        time.sleep(self.pausa_seg)
        return dados.get("data") or {}

    # ------------------------------------------------------------------ alto nível
    def buscar_ofertas(self, palavra_chave: str = "", ordem: int = ORDEM_MAIOR_COMISSAO,
                       pagina: int = 1, limite: int = 20) -> list[Produto]:
        query = f"""
        query Busca($keyword: String, $sortType: Int, $page: Int, $limit: Int) {{
          productOfferV2(keyword: $keyword, sortType: $sortType, page: $page, limit: $limit) {{
            nodes {{ {_CAMPOS_PRODUTO} }}
            pageInfo {{ page limit hasNextPage }}
          }}
        }}"""
        variaveis = {"keyword": palavra_chave, "sortType": ordem, "page": pagina, "limit": limite}
        dados = self.consultar(query, variaveis)
        nos = (dados.get("productOfferV2") or {}).get("nodes") or []
        return [converter_no(n, nicho=palavra_chave) for n in nos]

    def gerar_link_curto(self, url_original: str, sub_ids: list[str] | None = None) -> str:
        """Gera um link de afiliado rastreável. Sub IDs ajudam a saber qual vídeo vendeu."""
        query = """
        mutation Link($url: String!, $subIds: [String]) {
          generateShortLink(input: {originUrl: $url, subIds: $subIds}) { shortLink }
        }"""
        dados = self.consultar(query, {"url": url_original, "subIds": sub_ids or []})
        return (dados.get("generateShortLink") or {}).get("shortLink", "")


def _num(valor, padrao: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def converter_no(no: dict, nicho: str = "") -> Produto:
    """Converte um item retornado pela API no nosso modelo Produto."""
    preco = _num(no.get("price")) or _num(no.get("priceMin"))
    taxa = _num(no.get("commissionRate"))
    if taxa > 1:  # algumas respostas vêm em porcentagem (ex.: "12")
        taxa /= 100
    comissao = _num(no.get("commission"), padrao=-1)
    return Produto(
        id=str(no.get("itemId", "")),
        nome=(no.get("productName") or "").strip(),
        preco=preco,
        taxa_comissao=taxa,
        vendas=int(_num(no.get("sales"))),
        avaliacao=_num(no.get("ratingStar")),
        imagem_url=no.get("imageUrl") or "",
        link_afiliado=no.get("offerLink") or no.get("productLink") or "",
        loja=no.get("shopName") or "",
        desconto_pct=_num(no.get("priceDiscountRate")),
        comissao_valor=comissao if comissao >= 0 else None,
        nicho=nicho,
        extras={"link_produto": no.get("productLink") or ""},
    )
