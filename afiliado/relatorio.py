"""Relatório diário em Markdown + CSV com todos os candidatos."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .legenda import formatar_vendas, reais
from .modelos import Produto


def salvar_csv(produtos: list[Produto], destino: Path) -> None:
    campos = ["pontuacao", "nome", "nicho", "preco", "taxa_comissao", "ganho_por_venda",
              "vendas", "avaliacao", "desconto_pct", "loja", "link_afiliado", "id"]
    with destino.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig abre certo no Excel
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore", delimiter=";")
        w.writeheader()
        for p in produtos:
            w.writerow(p.to_dict())


def salvar_markdown(escolhidos: list[Produto], nichos: list[tuple[str, float, int]],
                    total: int, destino: Path, demo: bool) -> None:
    l = [f"# Relatório de afiliado Shopee: {date.today():%d/%m/%Y}", ""]
    if demo:
        l += ["> **MODO DEMONSTRAÇÃO**: dados fictícios. Configure a API para dados reais.", ""]
    l += [f"Produtos analisados: **{total}**", "", "## Melhores nichos hoje", "",
          "| # | Nicho | Nota média (top 5) | Produtos aprovados |", "|---|---|---|---|"]
    for i, (n, nota, qtd) in enumerate(nichos[:10], 1):
        l.append(f"| {i} | {n} | {nota} | {qtd} |")
    l += ["", "## Produtos escolhidos para postar", ""]
    for i, p in enumerate(escolhidos, 1):
        l += [f"### {i}. {p.nome}", "",
              f"- Pontuação: **{p.pontuacao}** · nicho: {p.nicho}",
              f"- Preço: {reais(p.preco)} · comissão: {p.taxa_comissao * 100:.1f}% "
              f"(**≈ {reais(p.ganho_por_venda)} por venda**)",
              f"- Vendas: {formatar_vendas(p.vendas)} · nota: {p.avaliacao or '-'}",
              f"- Link: {p.link_afiliado}",
              f"- Arquivos: `{p.extras.get('pasta', '')}`", ""]
    destino.write_text("\n".join(l), encoding="utf-8")
