import io

import barcode
from barcode.writer import ImageWriter


def gerar_codigo_barras_png(codigo: str) -> bytes:
    """Gera um código de barras CODE128 (aceita letras e números, o formato
    mais flexível para SKU de loja) como PNG em memória."""
    writer = ImageWriter()
    writer.dpi = 200
    code128 = barcode.get("code128", codigo, writer=writer)

    buffer = io.BytesIO()
    code128.write(
        buffer,
        options={
            "module_height": 10.0,
            "font_size": 8,
            "text_distance": 3,
            "quiet_zone": 2,
        },
    )
    return buffer.getvalue()
