"""Dados FICTÍCIOS para testar o fluxo inteiro sem credenciais da API."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from .modelos import Produto

_EXEMPLOS = [
    ("Organizador de Gaveta Modular Kit 12 Peças", "organizador", 39.90, 0.12, 15400, 4.8, 35),
    ("Mini Processador de Alimentos Elétrico USB", "cozinha", 54.90, 0.10, 32000, 4.7, 45),
    ("Fita LED RGB 5 Metros com Controle e App", "iluminação led", 47.50, 0.14, 21000, 4.6, 50),
    ("Escova Secadora Alisadora 3 em 1", "cabelo", 119.90, 0.09, 8700, 4.7, 40),
    ("Fone Bluetooth Sem Fio com Case Carregador", "fone bluetooth", 69.90, 0.08, 54000, 4.5, 60),
    ("Garrafa Térmica Inox 1 Litro com Display", "garrafa térmica", 44.90, 0.11, 12500, 4.8, 30),
    ("Sérum Facial Vitamina C 30ml", "skincare", 29.90, 0.15, 41000, 4.9, 25),
    ("Comedouro Automático para Pet com Timer", "pet", 159.90, 0.10, 3200, 4.6, 20),
    ("Smartwatch Esportivo Monitor Cardíaco", "smartwatch", 139.90, 0.07, 26000, 4.4, 55),
    ("Mop Giratório com Balde Centrífugo", "limpeza", 89.90, 0.10, 18000, 4.7, 35),
    ("Kit Pincéis de Maquiagem 13 Peças", "maquiagem", 34.90, 0.13, 9800, 4.8, 40),
    ("Carregador Turbo 20W USB-C", "carregador", 24.90, 0.06, 67000, 4.6, 30),
    ("Luminária de Mesa LED Recarregável", "iluminação led", 59.90, 0.12, 7600, 4.7, 25),
    ("Tapete Higiênico Lavável para Cães", "pet", 49.90, 0.11, 5400, 4.5, 15),
    ("Mochila Notebook Antifurto USB", "escritório", 99.90, 0.09, 11200, 4.7, 45),
    ("Produto com nota baixa (deve ser filtrado)", "teste", 30.00, 0.20, 900, 3.6, 0),
]

_CORES = [(255, 138, 101), (129, 199, 132), (100, 181, 246), (255, 213, 79),
          (186, 104, 200), (77, 208, 225), (240, 98, 146), (161, 136, 127)]


def _imagem_ficticia(nome: str, destino: Path, cor: tuple) -> str:
    img = Image.new("RGB", (800, 800), cor)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((150, 150, 650, 650), radius=60, fill=(255, 255, 255))
    d.ellipse((300, 260, 500, 460), fill=cor)
    d.text((400, 560), "PRODUTO EXEMPLO", fill=(60, 60, 60), anchor="mm")
    img.save(destino)
    return str(destino)


def produtos_exemplo(pasta_imagens: Path, semente: int = 7) -> list[Produto]:
    pasta_imagens.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(semente)
    produtos = []
    for i, (nome, nicho, preco, taxa, vendas, nota, desc) in enumerate(_EXEMPLOS):
        img = _imagem_ficticia(nome, pasta_imagens / f"demo{i}.png", _CORES[i % len(_CORES)])
        produtos.append(Produto(
            id=f"demo{i}", nome=nome, preco=preco, taxa_comissao=taxa,
            vendas=vendas + rnd.randint(0, 500), avaliacao=nota, imagem_url=img,
            link_afiliado=f"https://s.shopee.com.br/EXEMPLO{i}", loja="Loja Exemplo",
            desconto_pct=desc, nicho=nicho,
        ))
    return produtos
