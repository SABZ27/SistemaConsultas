"""Genera 2 documentos de ia/conocimiento/ en PDF.

Usa reportlab==5.1.0 (version FIJA en ia/requirements.txt). Solo lectura de
los .md y escritura de los .pdf: no toca la base de datos ni servicios.

Uso (desde la raiz del repo):
    python ia/scripts/generar_pdfs.py
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "conocimiento"

# Dos de los documentos de conocimiento, tambien en PDF, para demostrar la
# carga de PDF en la base de conocimiento de Open WebUI.
ORIGENES = (
    "01-que-es-el-sistema.md",
    "08-politica-de-contrasenas.md",
)


def enriquecer(texto: str) -> str:
    """Escapa XML y aplica el formato Markdown en linea que usamos."""
    salida = escape(texto)
    salida = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", salida)
    salida = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', salida)
    return salida


def estilos():
    base = getSampleStyleSheet()
    cuerpo = ParagraphStyle(
        "CuerpoIA",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=4,
    )
    codigo = ParagraphStyle(
        "CodigoIA",
        parent=base["Code"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        backColor=None,
    )
    return {
        "h1": base["Heading1"],
        "h2": base["Heading2"],
        "h3": base["Heading3"],
        "p": cuerpo,
        "code": codigo,
    }


def construir(ruta_md: Path, st: dict) -> list:
    story: list = []
    lineas = ruta_md.read_text(encoding="utf-8").splitlines()
    en_codigo = False
    bloque: list[str] = []

    def volcar_codigo():
        nonlocal bloque
        if bloque:
            story.append(Preformatted("\n".join(bloque), st["code"]))
            story.append(Spacer(1, 4))
            bloque = []

    for linea in lineas:
        texto = linea.rstrip()

        if texto.strip().startswith("```"):
            if en_codigo:
                volcar_codigo()
                en_codigo = False
            else:
                en_codigo = True
            continue

        if en_codigo:
            bloque.append(texto)
            continue

        if not texto.strip():
            story.append(Spacer(1, 4))
            continue

        # Separadores de tabla Markdown: se omiten.
        if re.fullmatch(r"[\s|:\-]+", texto):
            continue

        if texto.startswith("### "):
            story.append(Paragraph(enriquecer(texto[4:]), st["h3"]))
        elif texto.startswith("## "):
            story.append(Paragraph(enriquecer(texto[3:]), st["h2"]))
        elif texto.startswith("# "):
            story.append(Paragraph(enriquecer(texto[2:]), st["h1"]))
        elif texto.lstrip().startswith(("- ", "* ")):
            contenido = texto.lstrip()[2:]
            story.append(Paragraph("• " + enriquecer(contenido), st["p"]))
        else:
            # Las filas de tabla se dejan como texto legible.
            story.append(Paragraph(enriquecer(texto), st["p"]))

    volcar_codigo()
    return story


def main() -> int:
    st = estilos()
    for nombre in ORIGENES:
        origen = CARPETA / nombre
        if not origen.exists():
            print(f"ERROR: no existe {origen}")
            return 1
        destino = CARPETA / (origen.stem + ".pdf")
        doc = SimpleDocTemplate(
            str(destino),
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=origen.stem,
            author="Sistema de Consultas Academicas",
        )
        doc.build(construir(origen, st))
        print(f"Generado: {destino.name} ({destino.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
