#!/usr/bin/env python3
"""Genera PDF del anteproyecto FLUORO-HoLEP."""
from pathlib import Path
from markdown_pdf import MarkdownPdf, Section

ROOT = Path(__file__).resolve().parent
DOCS = [
    ("ANTEPROYECTO_FLUORO_HOLEP", "Anteproyecto FLUORO-HoLEP"),
    ("PROYECTO_FLUORO_HOLEP", "Proyecto FLUORO-HoLEP (versión extensa)"),
    ("RESUMEN_EJECUTIVO_ANID", "Resumen ejecutivo — FONIS-ANID"),
    ("CARTA_SCHU", "Carta de presentación — Sociedad Chilena de Urología"),
    ("CONSENTIMIENTO_INFORMADO_DRAFT", "Consentimiento informado (borrador)"),
]

css = """
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.45; color: #222; }
h1 { font-size: 18pt; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 4px; margin-top: 24px; }
h2 { font-size: 14pt; color: #1a3a5c; margin-top: 20px; border-bottom: 1px solid #ccc; padding-bottom: 2px; }
h3 { font-size: 12pt; color: #2c5282; margin-top: 16px; }
h4 { font-size: 11pt; color: #2c5282; margin-top: 12px; }
p { text-align: justify; margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; }
th, td { border: 1px solid #999; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background-color: #e6eef7; font-weight: bold; }
tr:nth-child(even) td { background-color: #f7f9fb; }
code { font-family: 'Courier New', monospace; font-size: 9.5pt; background-color: #f0f0f0; padding: 1px 3px; border-radius: 2px; }
pre { font-family: 'Courier New', monospace; font-size: 9pt; background-color: #f5f5f5; padding: 8px; border-left: 3px solid #1a3a5c; overflow-x: auto; white-space: pre-wrap; }
blockquote { border-left: 3px solid #888; padding-left: 10px; color: #555; font-style: italic; }
hr { border: none; border-top: 1px solid #aaa; margin: 18px 0; }
a { color: #1a3a5c; text-decoration: none; }
ul, ol { margin: 4px 0 8px 20px; }
li { margin: 2px 0; }
"""

for stem, title in DOCS:
    src = ROOT / f"{stem}.md"
    dst = ROOT / f"{stem}.pdf"
    if not src.exists():
        print(f"[saltado] {src.name} no existe")
        continue
    text = src.read_text(encoding="utf-8")
    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = title
    pdf.meta["author"] = "Investigador Principal — FLUORO-HoLEP"
    pdf.meta["subject"] = "Identificación intraoperatoria del plano capsular mediante tinción fluorescente diferencial periprostática"
    pdf.meta["keywords"] = "HoLEP, ICG, NIR, próstata, HPB, cápsula, fluoroguía"
    pdf.add_section(Section(text, paper_size="A4"), user_css=css)
    pdf.save(str(dst))
    print(f"OK  {dst.name}  ({dst.stat().st_size / 1024:.1f} KB)")
