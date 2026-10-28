"""Pierderea de timp pe persoană (§ 9.9): ponderează pierderea fiecărui tip de participant cu o ocupare declarată.

Camera nu poate vedea câte persoane sunt într-un vehicul, iar pentru liniile STB din piață nu există date publice de
ocupare: doar vehiculele noi au numărătoare automate de călători (TPBI), iar restul se estimează din sondaje. De aceea
ocupările sunt ipoteze declarate, verificate pe un interval (analiză de sensibilitate):
  autoturism 1,2 persoane (naveta la orele de vârf, Agenția Europeană de Mediu / Comisia Europeană),
  autobuz și troleibuz 20 / 40 / 70 de persoane (aproximativ un sfert, jumătate și trei sferturi din capacitatea unui
  vehicul de 12 m), camion și motocicletă 1, bicicletă 1, pieton 1.
Se citesc coloanele pierdere_h_<tip> scrise de `romana.control.validare`; ieșirea are aceleași coloane (model,
scenariu, seed, pierdere_h), cu pierdere_h în ore-persoană, deci se analizează direct cu `romana.control.analiza`
sau `romana.control.decizie`.

Exemplu:
  python -m romana.control.ocupare outputs/validare/test_28_indisciplinat.csv outputs/validare/test_28_normal.csv ^
      --autobuz 40 --out outputs/validare/test_28_persoane_40.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OCUPARE = {"passenger": 1.2, "bus": 40.0, "truck": 1.0, "motorcycle": 1.0, "bicycle": 1.0, "pieton": 1.0}


def pondereaza(df: pd.DataFrame, ocupare: dict[str, float]) -> pd.DataFrame:
    lipsa = [f"pierdere_h_{t}" for t in ocupare if f"pierdere_h_{t}" not in df.columns]
    if lipsa:
        raise SystemExit(f"[ocupare] lipsesc coloanele {lipsa} (rezultate rulate înainte de defalcarea pe tipuri)")
    out = df[["model", "scenariu", "seed"]].copy()
    out["pierdere_h"] = sum(df[f"pierdere_h_{t}"] * k for t, k in ocupare.items())
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fisiere", nargs="+")
    ap.add_argument("--autobuz", type=float, default=OCUPARE["bus"], help="persoane într-un autobuz / troleibuz")
    ap.add_argument("--autoturism", type=float, default=OCUPARE["passenger"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    occ = {**OCUPARE, "bus": args.autobuz, "passenger": args.autoturism}
    df = pd.concat([pd.read_csv(f) for f in args.fisiere], ignore_index=True)
    out = pondereaza(df, occ)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    parts = {t: float((df[f"pierdere_h_{t}"] * k).sum()) for t, k in occ.items()}
    tot = sum(parts.values())
    print("ore-persoană pe tipuri: " + ", ".join(f"{t} {v / tot:.0%}" for t, v in parts.items()) + f"; ocupări {occ}")
    print(f"[OK] {args.out} ({len(out)} rânduri)")


if __name__ == "__main__":
    main()
