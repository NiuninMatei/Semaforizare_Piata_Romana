"""Exportul documentației în PDF, cu pagini numerotate: docs/DOCUMENTATIE.md → docs/DOCUMENTATIE.pdf.

Markdown → HTML (pachetul `markdown`: tabele, note de subsol, cuprins), apoi tipărire cu Google Chrome fără
interfață; numerotarea paginilor vine din regulile CSS `@page`.

Rulare:  python -m romana.doc_pdf
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import markdown

from romana.common import ROOT

DOCS = ROOT / "docs"
CHROME = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
          Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
          Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")]
CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm;
        @bottom-center { content: "Pagina " counter(page) " din " counter(pages); font: 9pt sans-serif; color: #555; } }
body { font: 10.5pt/1.45 "Segoe UI", Arial, sans-serif; color: #111; }
h1 { font-size: 20pt; margin-top: 0; } h2 { font-size: 15pt; border-bottom: 1px solid #999; padding-bottom: 2px;
     break-before: page; margin-top: 0; } h3 { font-size: 12pt; margin-top: 14pt; }
h2:first-of-type { break-before: auto; }
table { border-collapse: collapse; margin: 6pt 0; font-size: 9pt; width: 100%; break-inside: auto; }
th, td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: top; } th { background: #eee; }
tr { break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f3f3f3; padding: 0 2px; }
pre { background: #f3f3f3; padding: 6px; font-size: 8.5pt; white-space: pre-wrap; }
img { max-width: 100%; } blockquote { color: #333; border-left: 3px solid #ccc; margin-left: 0; padding-left: 8px; }
.footnote { font-size: 8.5pt; }
"""


def main() -> None:
    text = (DOCS / "DOCUMENTATIE.md").read_text(encoding="utf-8")
    text = re.sub(r"\$([^$\n]+)\$", r"<i>\1</i>", text)            # formulele inline: italic simplu
    body = markdown.markdown(text, extensions=["tables", "footnotes", "toc", "fenced_code", "sane_lists"])
    html = (f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>Semaforizare Piața Romană – '
            f"documentația proiectului</title><style>{CSS}</style></head><body>{body}</body></html>")
    tmp = DOCS / "_documentatie_tmp.html"
    tmp.write_text(html, encoding="utf-8")
    chrome = next((c for c in CHROME if c.exists()), None)
    if chrome is None:
        raise SystemExit("Nu am găsit Chrome sau Edge pentru tipărirea în PDF.")
    out = DOCS / "DOCUMENTATIE.pdf"
    subprocess.run([str(chrome), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", tmp.resolve().as_uri()], check=True, timeout=180)
    tmp.unlink(missing_ok=True)
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
