"""Scenariile cu participanți indisciplinați (testul de robustețe, § 9.4), generate din scenariile zilei.

Fiecare `indisciplinat_<scenariu>.sumocfg` este o copie a lui `<scenariu>.sumocfg` (aceeași rețea, aceeași
cerere, același orizont) în care fișierul cu tipurile de participanți `vtypes.add.xml` din `additional-files`
este înlocuit cu `vtypes_indisciplinat.add.xml` (din același director): vehicule care blochează intersecția,
trec pe roșu în primele secunde sau pe galben târziu și schimbă banda agresiv; pietoni care traversează pe roșu.
Restul fișierului rămâne identic, octet cu octet. Scenariile fără `additional-files` sau fără fișierul
`vtypes.add.xml` în listă sunt sărite (cu mesaj).

Același mecanism dă și variantele cu capacitatea calibrată (§ 6.4): `--vtypes vtypes_capacitate.add.xml --prefix
capacitate_` (timpul de reacție al șoferilor 0,8 s) și `--vtypes vtypes_capacitate_indisciplinat.add.xml --prefix
capacitate_indisciplinat_`.

Exemple:
  python -m romana.bridge.indisciplinat                                  # toate sumo/scenarios/zi_*.sumocfg
  python -m romana.bridge.indisciplinat --scenarii "sumo/scenarios/zi_2026-10-25_*.sumocfg"
  python -m romana.bridge.indisciplinat --verifica                       # doar compară cu fișierele existente
  python -m romana.bridge.indisciplinat --scenarii "sumo/scenarios/zi_2026-10-26_*.sumocfg" ^
      --vtypes vtypes_capacitate.add.xml --prefix capacitate_
"""
from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path

from romana.common import SUMO_DIR

PREFIX = "indisciplinat_"
VTYPES = "vtypes.add.xml"
VTYPES_INDISCIPLINAT = "vtypes_indisciplinat.add.xml"
_ADDITIONAL = re.compile(r'(<additional-files\s+value=")([^"]*)(")')


def undisciplined_text(text: str, old: str = VTYPES, new: str = VTYPES_INDISCIPLINAT) -> str | None:
    """Textul sumocfg cu fișierul de tipuri `old` înlocuit cu `new` (doar numele, directorul se păstrează).

    Întoarce None dacă nu există `additional-files` sau dacă lista nu conține `old`."""
    m = _ADDITIONAL.search(text)
    if not m:
        return None
    files = m.group(2).split(",")
    found = False
    for i, f in enumerate(files):
        head, sep, name = f.strip().rpartition("/")
        if name == old:
            files[i] = f"{head}{sep}{new}"
            found = True
    if not found:
        return None
    return text[:m.start(2)] + ",".join(files) + text[m.end(2):]


def _read(path: Path) -> str:
    """Textul fișierului cu terminațiile de rând neschimbate (CRLF rămâne CRLF)."""
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def generate(sources: list[Path], out_dir: Path | None = None, check: bool = False,
             prefix: str = PREFIX, vtypes: str = VTYPES_INDISCIPLINAT) -> dict[str, list[str]]:
    """Scrie (sau, cu check=True, doar compară) scenariile indisciplinate. Întoarce rapoartele pe categorii."""
    rep = {"scrise": [], "identice": [], "diferite": [], "lipsa": [], "sarite": []}
    for src in sources:
        if src.name.startswith(prefix):
            continue                                    # nu se generează „indisciplinat_indisciplinat_…”
        text = _read(src)
        new = undisciplined_text(text, new=vtypes)
        if new is None:
            print(f"[sărit] {src.name}: fără {VTYPES} în additional-files")
            rep["sarite"].append(src.name)
            continue
        dst = (out_dir or src.parent) / f"{prefix}{src.name}"
        if check:
            if not dst.exists():
                rep["lipsa"].append(dst.name)
            elif _read(dst).replace("\r\n", "\n") == new.replace("\r\n", "\n"):
                rep["identice"].append(dst.name)
            else:
                rep["diferite"].append(dst.name)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="") as f:   # aceleași terminații de rând ca sursa
            f.write(new)
        rep["scrise"].append(dst.name)
    return rep


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarii", nargs="*", default=[str(SUMO_DIR / "scenarios" / "zi_*.sumocfg")],
                    help="fișierele .sumocfg sursă (tipare glob; implicit sumo/scenarios/zi_*.sumocfg)")
    ap.add_argument("--out-dir", default=None, help="directorul de ieșire (implicit lângă sursă)")
    ap.add_argument("--vtypes", default=VTYPES_INDISCIPLINAT,
                    help=f"fișierul cu tipurile de participanți pus în locul lui {VTYPES} (implicit {VTYPES_INDISCIPLINAT})")
    ap.add_argument("--prefix", default=PREFIX, help=f"prefixul scenariilor generate (implicit {PREFIX})")
    ap.add_argument("--verifica", action="store_true",
                    help="nu scrie nimic: verifică dacă fișierele existente sunt exact cele generate")
    args = ap.parse_args(argv)
    sources = sorted({Path(f) for pat in args.scenarii for f in glob.glob(pat)})
    if not sources:
        raise SystemExit("Niciun scenariu sursă găsit.")
    if args.out_dir and Path(args.out_dir).resolve() != sources[0].parent.resolve():
        print("[atenție] căile din sumocfg sunt relative: scenariile generate funcționează doar lângă cele sursă")
    rep = generate(sources, Path(args.out_dir) if args.out_dir else None, check=args.verifica,
                   prefix=args.prefix, vtypes=args.vtypes)
    if args.verifica:
        print(f"identice: {len(rep['identice'])}, diferite: {rep['diferite']}, lipsă: {rep['lipsa']}")
        if rep["diferite"] or rep["lipsa"]:
            raise SystemExit(1)
    else:
        print(f"[OK] {len(rep['scrise'])} scenarii {args.prefix}* (tipurile: {args.vtypes})")


if __name__ == "__main__":
    main()
