"""Descoberta automática: varre vários nichos e junta os candidatos sem duplicar."""

from __future__ import annotations

import logging

from ..modelos import Produto
from .api import ORDEM_MAIOR_COMISSAO, ORDEM_MAIS_VENDIDOS, ErroShopee, ShopeeAfiliados

log = logging.getLogger(__name__)

# Palavras-chave amplas: o script testa todas e descobre sozinho quais nichos rendem mais.
NICHOS_PADRAO = [
    "organizador", "cozinha", "decoração", "iluminação led", "limpeza",
    "skincare", "maquiagem", "cabelo", "perfume",
    "fone bluetooth", "carregador", "smartwatch", "acessórios celular",
    "pet", "brinquedo", "bebê",
    "academia", "garrafa térmica", "camping",
    "ferramentas", "carro acessórios",
    "moda feminina", "bolsa", "tênis", "relógio",
    "papelaria", "gamer", "escritório",
]


def descobrir(cliente: ShopeeAfiliados, nichos: list[str] | None = None,
              por_busca: int = 20) -> list[Produto]:
    """Para cada nicho, busca os de maior comissão e os mais vendidos."""
    vistos: dict[str, Produto] = {}
    for nicho in nichos or NICHOS_PADRAO:
        for ordem in (ORDEM_MAIOR_COMISSAO, ORDEM_MAIS_VENDIDOS):
            try:
                produtos = cliente.buscar_ofertas(nicho, ordem=ordem, limite=por_busca)
            except ErroShopee as e:
                log.warning("Erro da API no nicho %r: %s", nicho, e)
                continue
            for p in produtos:
                vistos.setdefault(p.id, p)
        log.info("Nicho %-20s -> %d produtos acumulados", nicho, len(vistos))
    return list(vistos.values())
