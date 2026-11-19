"""Guarda os produtos já divulgados para não repetir o mesmo vídeo todo dia."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


class Historico:
    def __init__(self, caminho: Path, dias_sem_repetir: int = 14):
        self.caminho = caminho
        self.dias = dias_sem_repetir
        self.dados: dict[str, str] = {}
        if caminho.is_file():
            self.dados = json.loads(caminho.read_text(encoding="utf-8"))

    def recente(self, produto_id: str, hoje: date | None = None) -> bool:
        quando = self.dados.get(produto_id)
        if not quando:
            return False
        hoje = hoje or date.today()
        return date.fromisoformat(quando) > hoje - timedelta(days=self.dias)

    def registrar(self, produto_id: str, hoje: date | None = None) -> None:
        self.dados[produto_id] = (hoje or date.today()).isoformat()

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps(self.dados, indent=2), encoding="utf-8")
