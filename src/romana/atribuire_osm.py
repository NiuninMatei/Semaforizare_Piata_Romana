"""Notificarea OpenStreetMap / ODbL 1.0 în fișierele generate din rețeaua derivată din OSM.

ODbL 1.0 § 4.2 b) cere licența (sau URI-ul ei) atât în baza de date derivată, cât și în documentație.
Fișierele XML generate (rețeaua, rutele, virajele, scenariile) admit comentarii, deci notificarea se
inserează ca un comentariu XML imediat după declarația XML. Funcția este idempotentă și păstrează
codificarea și terminațiile de rând ale fișierului.
"""
from __future__ import annotations

from pathlib import Path

NOTIFICARE_OSM = ("Conține informații din OpenStreetMap, © OpenStreetMap contributors "
                  "(https://www.openstreetmap.org/copyright), disponibile sub Open Database License 1.0: "
                  "https://opendatacommons.org/licenses/odbl/1-0/")
COMENTARIU_OSM = f"<!-- {NOTIFICARE_OSM} -->"


def adauga_notificare_osm(path) -> bool:
    """Inserează notificarea ODbL ca prim comentariu al fișierului XML. Întoarce True dacă fișierul s-a schimbat."""
    p = Path(path)
    with open(p, encoding="utf-8", newline="") as f:
        text = f.read()
    if "opendatacommons.org/licenses/odbl" in text[:8192]:
        return False
    nl = "\r\n" if "\r\n" in text[:4096] else "\n"
    bom = "﻿" if text.startswith("﻿") else ""
    body = text[len(bom):]
    if body.startswith("<?xml"):
        end = body.index("?>") + 2
        body = body[:end] + nl + COMENTARIU_OSM + body[end:]
    else:
        body = COMENTARIU_OSM + nl + body
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(bom + body)
    return True
