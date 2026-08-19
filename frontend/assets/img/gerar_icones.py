"""Gera os ícones do PWA (fundo laranja da marca + chave inglesa estilizada).
Rode uma vez com: venv/Scripts/python.exe frontend/assets/img/gerar_icones.py
(usa o Pillow já instalado no venv do backend)."""

import os

from PIL import Image, ImageDraw

COR_FUNDO = (209, 90, 18, 255)  # #d15a12 — laranja da marca
COR_FRENTE = (255, 255, 255, 255)

PASTA = os.path.dirname(os.path.abspath(__file__))


def _desenhar_chave_inglesa(tamanho, margem_proporcional):
    """Desenha uma chave inglesa estilizada (barra + duas argolas nas
    pontas) numa camada transparente, já rotacionada 45°."""
    camada = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(camada)

    margem = tamanho * margem_proporcional
    espessura = tamanho * 0.09
    cy = tamanho / 2
    x1, x2 = margem, tamanho - margem

    desenho.line([(x1, cy), (x2, cy)], fill=COR_FRENTE, width=int(espessura))

    raio_externo = espessura * 1.3
    raio_interno = espessura * 0.62
    for cx in (x1, x2):
        desenho.ellipse(
            [cx - raio_externo, cy - raio_externo, cx + raio_externo, cy + raio_externo],
            fill=COR_FRENTE,
        )
        desenho.ellipse(
            [cx - raio_interno, cy - raio_interno, cx + raio_interno, cy + raio_interno],
            fill=(0, 0, 0, 0),
        )

    return camada.rotate(-45, resample=Image.BICUBIC, center=(tamanho / 2, tamanho / 2))


def gerar_icone(tamanho, nome_arquivo, maskable=False):
    fundo = Image.new("RGBA", (tamanho, tamanho), COR_FUNDO)

    if not maskable:
        # ícone normal: cantos arredondados (fica bonito na lista de apps)
        mascara = Image.new("L", (tamanho, tamanho), 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [0, 0, tamanho - 1, tamanho - 1], radius=int(tamanho * 0.18), fill=255
        )
        base = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
        base.paste(fundo, (0, 0), mascara)
        fundo = base
        margem_proporcional = 0.24
    else:
        # maskable: fundo precisa ir até a borda (o SO aplica o recorte),
        # e o desenho precisa caber dentro da "safe zone" central de ~80%
        margem_proporcional = 0.32

    chave = _desenhar_chave_inglesa(tamanho, margem_proporcional)
    fundo.alpha_composite(chave)

    caminho = os.path.join(PASTA, nome_arquivo)
    fundo.save(caminho)
    print(f"gerado: {caminho}")


if __name__ == "__main__":
    gerar_icone(192, "icon-192.png")
    gerar_icone(512, "icon-512.png")
    gerar_icone(512, "icon-maskable-512.png", maskable=True)
