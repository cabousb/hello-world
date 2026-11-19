"""Rotina diária. Uso:

    python -m afiliado --demo              # testa sem API, com dados fictícios
    python -m afiliado --top 5             # dados reais (precisa do .env)
    python -m afiliado --top 3 --narracao  # vídeos com voz (pip install edge-tts)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import date
from pathlib import Path

from . import config, legenda, pontuacao, video
from .historico import Historico
from .relatorio import salvar_csv, salvar_markdown

log = logging.getLogger("afiliado")


def _pasta_nome(texto: str) -> str:
    return re.sub(r"[^\w-]+", "-", texto.lower()).strip("-")[:40]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Descobre os melhores produtos da Shopee e gera vídeos.")
    ap.add_argument("--demo", action="store_true", help="usa dados fictícios (sem API)")
    ap.add_argument("--top", type=int, default=5, help="quantos vídeos gerar (padrão 5)")
    ap.add_argument("--nichos", help="lista separada por vírgula (padrão: descoberta automática)")
    ap.add_argument("--saida", default="saida", help="pasta de saída")
    ap.add_argument("--sem-video", action="store_true", help="só relatório, sem gerar vídeos")
    ap.add_argument("--narracao", action="store_true", help="adiciona voz (requer edge-tts)")
    ap.add_argument("--musica", type=Path, help="mp3 de fundo (use só música livre de direitos)")
    ap.add_argument("--link-curto", action="store_true",
                    help="gera link curto com sub ID por vídeo (rastreia qual vídeo vendeu)")
    ap.add_argument("--historico", type=Path, default=Path("historico.json"))
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S")
    pasta_dia = Path(args.saida) / date.today().isoformat()
    pasta_dia.mkdir(parents=True, exist_ok=True)

    cliente = None
    if args.demo:
        from .demo import produtos_exemplo
        candidatos = produtos_exemplo(pasta_dia / "_imagens_demo")
    else:
        cfg = config.carregar()
        if not cfg.tem_credenciais:
            log.error("Credenciais ausentes. Copie .env.example para .env e preencha "
                      "SHOPEE_APP_ID e SHOPEE_SECRET, ou rode com --demo.")
            return 2
        from .shopee.api import ShopeeAfiliados
        from .shopee.descoberta import descobrir
        cliente = ShopeeAfiliados(cfg.app_id, cfg.secret, cfg.endpoint)
        nichos = [n.strip() for n in args.nichos.split(",")] if args.nichos else None
        candidatos = descobrir(cliente, nichos)

    aprovados = [p for p in candidatos if pontuacao.passa_filtros(p, pontuacao.Filtros())]
    ranqueados = pontuacao.pontuar(aprovados)
    nichos_rank = pontuacao.ranking_nichos(ranqueados)
    log.info("%d candidatos, %d aprovados nos filtros", len(candidatos), len(aprovados))

    hist = Historico(args.historico)
    escolhidos, nichos_usados = [], {}
    for p in ranqueados:  # variedade: no máximo 2 produtos do mesmo nicho por dia
        if hist.recente(p.id) or nichos_usados.get(p.nicho, 0) >= 2:
            continue
        escolhidos.append(p)
        nichos_usados[p.nicho] = nichos_usados.get(p.nicho, 0) + 1
        if len(escolhidos) >= args.top:
            break

    for i, p in enumerate(escolhidos, 1):
        pasta = pasta_dia / f"{i:02d}-{_pasta_nome(p.nome)}"
        pasta.mkdir(parents=True, exist_ok=True)
        p.extras["pasta"] = str(pasta)
        if cliente and args.link_curto:
            try:
                sub = f"v{date.today():%Y%m%d}n{i}"
                p.link_afiliado = cliente.gerar_link_curto(p.link_afiliado, [sub]) or p.link_afiliado
            except Exception as e:
                log.warning("Não gerou link curto: %s", e)
        (pasta / "legenda.txt").write_text(legenda.legenda(p), encoding="utf-8")
        (pasta / "comentario_fixado.txt").write_text(
            f"🛒 Link do produto: {p.link_afiliado}", encoding="utf-8")
        (pasta / "produto.json").write_text(json.dumps(p.to_dict(), ensure_ascii=False, indent=2),
                                            encoding="utf-8")
        if not args.sem_video:
            try:
                video.gerar_video(p, pasta / "video.mp4",
                                  narracao=legenda.roteiro_narracao(p) if args.narracao else None,
                                  musica=args.musica)
                video.gerar_capa(p, pasta / "capa.jpg")
            except Exception as e:
                log.error("Falha ao gerar vídeo de %r: %s", p.nome, e)
        hist.registrar(p.id)

    salvar_csv(ranqueados, pasta_dia / "candidatos.csv")
    salvar_markdown(escolhidos, nichos_rank, len(candidatos), pasta_dia / "relatorio.md", args.demo)
    if not args.demo:  # demo não deve "gastar" o histórico real
        hist.salvar()
    log.info("Pronto! Veja %s", pasta_dia / "relatorio.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
