"""Textos prontos: legenda do post, hashtags e roteiro da narração."""

from __future__ import annotations

import re
import unicodedata

from .modelos import Produto

HASHTAGS_BASE = ["#achadinhosshopee", "#shopee", "#achadinhos", "#promoção", "#comprinhas"]


def reais(valor: float) -> str:
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_vendas(n: int) -> str:
    if n >= 1_000_000:
        return f"+{n / 1_000_000:.1f} mi".replace(".0 ", " ").replace(".", ",")
    if n >= 1_000:
        return f"+{n // 1000} mil"
    return f"+{n}"


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def hashtags(produto: Produto, maximo: int = 8) -> list[str]:
    tags = list(HASHTAGS_BASE)
    if produto.nicho:
        tags.append("#" + _slug(produto.nicho))
    palavras = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", produto.nome)][:3]
    tags += ["#" + _slug(w) for w in palavras]
    vistos, unicas = set(), []
    for t in tags:
        if t not in vistos and len(t) > 2:
            vistos.add(t)
            unicas.append(t)
    return unicas[:maximo]


def legenda(produto: Produto) -> str:
    linhas = [f"{produto.nome[:90]}", ""]
    if produto.preco_original:
        linhas.append(f"De {reais(produto.preco_original)} por {reais(produto.preco)} "
                      f"({produto.desconto_pct:.0f}% OFF)")
    else:
        linhas.append(f"Apenas {reais(produto.preco)}")
    prova = []
    if produto.avaliacao:
        prova.append(f"nota {produto.avaliacao:.1f}".replace(".", ","))
    prova.append(f"{formatar_vendas(produto.vendas)} vendidos")
    linhas.append("⭐ " + " | ".join(prova))
    linhas += ["", f"🛒 Link: {produto.link_afiliado}", "",
               "*Preço pode mudar a qualquer momento. Link de afiliado.",
               "", " ".join(hashtags(produto))]
    return "\n".join(linhas)


def roteiro_narracao(produto: Produto) -> str:
    preco = reais(produto.preco).replace("R$ ", "") + " reais"
    partes = ["Olha esse achadinho da Shopee!", f"{produto.nome[:70]}."]
    if produto.desconto_pct >= 10:
        partes.append(f"Está com {produto.desconto_pct:.0f} por cento de desconto, por apenas {preco}.")
    else:
        partes.append(f"Por apenas {preco}.")
    if produto.avaliacao >= 4.5:
        partes.append(f"Nota {produto.avaliacao:.1f} e muita gente já comprou.".replace(".", ",", 1))
    partes.append("O link está nos comentários. Corre que acaba!")
    return " ".join(partes)
