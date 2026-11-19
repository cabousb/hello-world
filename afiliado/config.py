"""Leitura de configuração a partir de variáveis de ambiente ou do arquivo .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENDPOINT_BR = "https://open-api.affiliate.shopee.com.br/graphql"


def _carregar_dotenv(caminho: Path) -> None:
    """Leitor mínimo de .env (evita dependência extra). Não sobrescreve variáveis já definidas."""
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


@dataclass
class Config:
    app_id: str
    secret: str
    endpoint: str

    @property
    def tem_credenciais(self) -> bool:
        return bool(self.app_id and self.secret)


def carregar(raiz: Path | None = None) -> Config:
    _carregar_dotenv((raiz or Path.cwd()) / ".env")
    return Config(
        app_id=os.environ.get("SHOPEE_APP_ID", ""),
        secret=os.environ.get("SHOPEE_SECRET", ""),
        endpoint=os.environ.get("SHOPEE_ENDPOINT", ENDPOINT_BR),
    )
