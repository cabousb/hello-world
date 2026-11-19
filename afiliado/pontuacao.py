"""Ranking de produtos: equilibra quanto você ganha por venda com a chance de vender."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .modelos import Produto


@dataclass
class Filtros:
    avaliacao_minima: float = 4.3   # evita produto ruim (gera reclamação e devolução)
    vendas_minimas: int = 50        # prova de que o produto vende
    preco_minimo: float = 15.0
    preco_maximo: float = 600.0     # produto muito caro converte pouco em vídeo curto
    comissao_minima: float = 0.03


@dataclass
class Pesos:
    ganho: float = 0.45      # R$ por venda
    demanda: float = 0.35    # quantidade vendida (escala log)
    avaliacao: float = 0.12
    desconto: float = 0.08


def passa_filtros(p: Produto, f: Filtros) -> bool:
    if p.avaliacao and p.avaliacao < f.avaliacao_minima:
        return False
    return (p.vendas >= f.vendas_minimas
            and f.preco_minimo <= p.preco <= f.preco_maximo
            and p.taxa_comissao >= f.comissao_minima
            and bool(p.link_afiliado))


def _normalizar(valores: list[float]) -> list[float]:
    mn, mx = min(valores), max(valores)
    if mx - mn < 1e-9:
        return [1.0 for _ in valores]
    return [(v - mn) / (mx - mn) for v in valores]


def pontuar(produtos: list[Produto], pesos: Pesos | None = None) -> list[Produto]:
    """Atribui `pontuacao` (0 a 100) a cada produto e devolve a lista ordenada."""
    if not produtos:
        return []
    pesos = pesos or Pesos()
    ganho = _normalizar([math.log1p(p.ganho_por_venda) for p in produtos])
    demanda = _normalizar([math.log10(1 + p.vendas) for p in produtos])
    for p, g, d in zip(produtos, ganho, demanda):
        aval = min(max((p.avaliacao - 3.5) / 1.5, 0.0), 1.0) if p.avaliacao else 0.5
        desc = min(p.desconto_pct / 60, 1.0)
        p.pontuacao = round(100 * (pesos.ganho * g + pesos.demanda * d
                                   + pesos.avaliacao * aval + pesos.desconto * desc), 1)
    return sorted(produtos, key=lambda p: p.pontuacao, reverse=True)


def ranking_nichos(produtos: list[Produto], top_por_nicho: int = 5) -> list[tuple[str, float, int]]:
    """Média da pontuação dos melhores produtos de cada nicho -> descobre o nicho mais promissor."""
    grupos: dict[str, list[float]] = {}
    for p in produtos:
        grupos.setdefault(p.nicho or "geral", []).append(p.pontuacao)
    resultado = []
    for nicho, notas in grupos.items():
        melhores = sorted(notas, reverse=True)[:top_por_nicho]
        resultado.append((nicho, round(sum(melhores) / len(melhores), 1), len(notas)))
    return sorted(resultado, key=lambda x: x[1], reverse=True)
