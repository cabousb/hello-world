"""Modelo de dados compartilhado entre as plataformas (Shopee hoje, Mercado Livre depois)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Produto:
    id: str
    nome: str
    preco: float
    taxa_comissao: float          # fração: 0.12 = 12%
    vendas: int
    avaliacao: float              # 0 a 5 (0 = sem avaliação)
    imagem_url: str
    link_afiliado: str
    loja: str = ""
    desconto_pct: float = 0.0     # 30 = 30% de desconto
    comissao_valor: float | None = None  # valor em R$ por venda, se a API informar
    nicho: str = ""               # palavra-chave/categoria em que foi encontrado
    plataforma: str = "shopee"
    pontuacao: float = 0.0
    extras: dict = field(default_factory=dict)

    @property
    def ganho_por_venda(self) -> float:
        """Quanto você ganha (estimado) em cada venda."""
        if self.comissao_valor is not None and self.comissao_valor > 0:
            return self.comissao_valor
        return round(self.preco * self.taxa_comissao, 2)

    @property
    def preco_original(self) -> float | None:
        if 0 < self.desconto_pct < 100:
            return round(self.preco / (1 - self.desconto_pct / 100), 2)
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ganho_por_venda"] = self.ganho_por_venda
        return d
