"""Gera vídeos verticais 9:16 (Shopee Vídeo / Reels / TikTok) a partir da foto do produto.

Fluxo: baixa a imagem -> desenha 5 cenas com Pillow -> ffmpeg aplica zoom suave
em cada cena e junta tudo em um MP4 (H.264, 1080x1920, 30 fps).
"""

from __future__ import annotations

import asyncio
import io
import logging
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .legenda import formatar_vendas, reais
from .modelos import Produto

log = logging.getLogger(__name__)

LARGURA, ALTURA, FPS = 1080, 1920, 30
LARANJA = (238, 77, 45)       # cor de destaque
BRANCO, PRETO = (255, 255, 255), (20, 20, 20)
AMARELO = (255, 214, 0)

_FONTES_NEGRITO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    for caminho in _FONTES_NEGRITO:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default(size=tamanho)


# ---------------------------------------------------------------- imagem do produto
def carregar_imagem(produto: Produto) -> Image.Image:
    origem = produto.imagem_url
    if origem.startswith(("http://", "https://")):
        resp = requests.get(origem, timeout=30)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    return Image.open(origem).convert("RGB")


def _fundo(img: Image.Image) -> Image.Image:
    """Fundo desfocado com a própria foto (visual de vídeo profissional)."""
    fundo = ImageOps.fit(img, (LARGURA, ALTURA), method=Image.LANCZOS)
    fundo = fundo.filter(ImageFilter.GaussianBlur(40))
    escurecer = Image.new("RGB", fundo.size, (0, 0, 0))
    return Image.blend(fundo, escurecer, 0.45)


def _colar_produto(tela: Image.Image, img: Image.Image, centro_y: int, lado: int = 900) -> None:
    foto = ImageOps.contain(img, (lado, lado), method=Image.LANCZOS)
    moldura = Image.new("RGB", (foto.width + 24, foto.height + 24), BRANCO)
    moldura.paste(foto, (12, 12))
    x = (LARGURA - moldura.width) // 2
    y = centro_y - moldura.height // 2
    tela.paste(moldura, (x, y))


def _texto_centralizado(desenho: ImageDraw.ImageDraw, y: int, texto: str, tam: int,
                        cor=BRANCO, faixa: tuple | None = None, largura_max: int = 22) -> int:
    """Escreve texto quebrado em linhas, centralizado. Retorna o y final."""
    for linha in textwrap.wrap(texto, width=largura_max) or [""]:
        t = tam
        while True:  # diminui a fonte até a linha caber na tela (com margem)
            f = fonte(t)
            caixa = desenho.textbbox((0, 0), linha, font=f)
            w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
            if w <= LARGURA - 140 or t <= 24:
                break
            t -= 4
        x = (LARGURA - w) // 2
        if faixa:
            desenho.rounded_rectangle((x - 30, y - 18, x + w + 30, y + h + 30), radius=24, fill=faixa)
        desenho.text((x, y), linha, font=f, fill=cor, stroke_width=0 if faixa else 4,
                     stroke_fill=PRETO)
        y += h + 40
    return y


def _nome_curto(nome: str, limite: int = 60) -> str:
    return nome if len(nome) <= limite else nome[: limite - 1].rsplit(" ", 1)[0] + "…"


def desenhar_cenas(produto: Produto, img: Image.Image, chamada_final: str) -> list[Image.Image]:
    base = _fundo(img)
    cenas = []

    # 1. Gancho (primeiros 2 segundos decidem se a pessoa continua assistindo)
    c = base.copy(); d = ImageDraw.Draw(c)
    _texto_centralizado(d, 180, "ACHADINHO DA SHOPEE", 84, cor=BRANCO, faixa=LARANJA)
    _colar_produto(c, img, 1000)
    _texto_centralizado(d, 1560, "Você precisa ver isso!", 72, cor=AMARELO)
    cenas.append(c)

    # 2. Produto
    c = base.copy(); d = ImageDraw.Draw(c)
    _colar_produto(c, img, 820, lado=960)
    _texto_centralizado(d, 1420, _nome_curto(produto.nome), 60, largura_max=26)
    cenas.append(c)

    # 3. Preço
    c = base.copy(); d = ImageDraw.Draw(c)
    _colar_produto(c, img, 720, lado=760)
    y = 1220
    if produto.preco_original:
        y = _texto_centralizado(d, y, f"De {reais(produto.preco_original)}", 60, cor=(220, 220, 220))
        y = _texto_centralizado(d, y, f"-{produto.desconto_pct:.0f}% OFF", 70, cor=BRANCO, faixa=LARANJA)
        y += 10
    _texto_centralizado(d, y, f"Por {reais(produto.preco)}", 110, cor=AMARELO)
    cenas.append(c)

    # 4. Prova social
    c = base.copy(); d = ImageDraw.Draw(c)
    _colar_produto(c, img, 760, lado=820)
    y = 1300
    if produto.avaliacao:
        y = _texto_centralizado(d, y, f"Nota {produto.avaliacao:.1f} de 5".replace(".", ","), 80, cor=AMARELO)
    _texto_centralizado(d, y, f"{formatar_vendas(produto.vendas)} vendidos", 76)
    cenas.append(c)

    # 5. Chamada para ação
    c = base.copy(); d = ImageDraw.Draw(c)
    _colar_produto(c, img, 760, lado=700)
    y = _texto_centralizado(d, 1260, chamada_final, 76, cor=BRANCO, faixa=LARANJA, largura_max=20)
    _texto_centralizado(d, y + 30, "Corre que acaba!", 70, cor=AMARELO)
    cenas.append(c)
    return cenas


# ---------------------------------------------------------------- ffmpeg
def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg não encontrado. Instale: https://ffmpeg.org/download.html")
    return exe


def _rodar(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou:\n{r.stderr[-2000:]}")


def _gerar_narracao(texto: str, destino: Path, voz: str = "pt-BR-FranciscaNeural") -> bool:
    """Narração opcional com edge-tts (pip install edge-tts). Sem ele, o vídeo sai sem voz."""
    try:
        import edge_tts  # type: ignore
    except ImportError:
        log.info("edge-tts não instalado: vídeo sem narração.")
        return False
    try:
        asyncio.run(edge_tts.Communicate(texto, voz).save(str(destino)))
        return True
    except Exception as e:  # rede indisponível etc.
        log.warning("Falha na narração (%s): vídeo sem voz.", e)
        return False


def gerar_video(produto: Produto, destino: Path, segundos_por_cena: float = 3.0,
                chamada_final: str = "Link nos comentários", narracao: str | None = None,
                musica: Path | None = None) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    img = carregar_imagem(produto)
    cenas = desenhar_cenas(produto, img, chamada_final)
    ff = _ffmpeg()
    quadros = int(segundos_por_cena * FPS)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clipes = []
        for i, cena in enumerate(cenas):
            png, mp4 = tmp / f"cena{i}.png", tmp / f"cena{i}.mp4"
            cena.save(png)
            # zoom suave (efeito Ken Burns) para o vídeo não parecer "foto parada"
            filtro = (f"scale={LARGURA * 2}:{ALTURA * 2},"
                      f"zoompan=z='min(zoom+0.0007,1.06)':d={quadros}"
                      f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={LARGURA}x{ALTURA}:fps={FPS},"
                      "format=yuv420p")
            _rodar([ff, "-y", "-loop", "1", "-i", str(png), "-vf", filtro,
                    "-frames:v", str(quadros), "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", str(mp4)])
            clipes.append(mp4)

        lista = tmp / "lista.txt"
        lista.write_text("".join(f"file '{c.as_posix()}'\n" for c in clipes), encoding="utf-8")
        mudo = tmp / "mudo.mp4"
        _rodar([ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(mudo)])

        audios = []
        if narracao:
            voz = tmp / "voz.mp3"
            if _gerar_narracao(narracao, voz):
                audios.append(voz)
        if musica and Path(musica).is_file():
            audios.append(Path(musica))

        if not audios:
            shutil.copy(mudo, destino)
        else:
            cmd = [ff, "-y", "-i", str(mudo)]
            for a in audios:
                cmd += ["-i", str(a)]
            if len(audios) == 1:
                cmd += ["-map", "0:v", "-map", "1:a"]
            else:  # voz por cima de música baixinha
                cmd += ["-filter_complex",
                        "[2:a]volume=0.15[m];[1:a][m]amix=inputs=2:duration=first[a]",
                        "-map", "0:v", "-map", "[a]"]
            cmd += ["-c:v", "copy", "-c:a", "aac", "-shortest", str(destino)]
            _rodar(cmd)

    log.info("Vídeo gerado: %s", destino)
    return destino


def gerar_capa(produto: Produto, destino: Path) -> Path:
    """Salva a primeira cena como imagem de capa (thumbnail)."""
    cena = desenhar_cenas(produto, carregar_imagem(produto), "")[0]
    destino.parent.mkdir(parents=True, exist_ok=True)
    cena.convert("RGB").save(destino, quality=90)
    return destino
