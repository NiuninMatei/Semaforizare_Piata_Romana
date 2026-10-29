"""Pierderea totală pe strategii, pe cazuri de trafic și pe tipuri de participanți (§ 9.10).

Regula „cel mai bun câștigă” (`romana.control.decizie`) judecă după pierderea totală pe toate perechile (scenariu ×
seed, ambele comportamente). Modulul o desface pe comportamente, pe cazuri de trafic (după debitul echilibrat, cu
aceleași praguri ca decizia) și pe tipuri de participanți (coloanele `pierdere_h_<tip>` scrise de
`romana.control.validare`). Dă și media schimbărilor relative pe perechi fără cazul lejer: noaptea pierderile sunt
aproape nule, iar o medie relativă le-ar da aceeași greutate ca vârfului.

Exemplu:
  python -m romana.control.totaluri docs/rezultate/test_28_indisciplinat.csv docs/rezultate/test_28_normal.csv
"""
from __future__ import annotations

import argparse
import math

import pandas as pd

from romana.control.analiza import add_program, load_results, parse_program, pivot
from romana.control.decizie import PRAGURI, PROGRAME, caz, debite

TIPURI = ["passenger", "bus", "truck", "motorcycle", "bicycle", "pieton"]


def perechi(fisiere, metric, programe, bands) -> pd.DataFrame:
    """Tabelul perechilor pentru o metrică, cu programele pe cazuri adăugate; doar strategiile complete."""
    p = pivot(load_results(fisiere, metric))
    for spec in programe:
        name, comp = parse_program(spec)
        p = add_program(p, name, comp, bands)
    return p[[c for c in p.columns if p[c].notna().all()]]


def procent(a: float, b: float) -> str:
    return f"{(a / b - 1) * 100:+.1f}%"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fisiere", nargs="+", help="CSV-urile testului (din romana.control.validare)")
    ap.add_argument("--praguri", nargs=2, type=float, default=list(PRAGURI), metavar=("LEJER", "INTENS"))
    ap.add_argument("--program", action="append", default=None, help="implicit: REALIST și TOD_DEBIT")
    ap.add_argument("--referinte", nargs="+", default=["FIX", "REALIST"])
    args = ap.parse_args(argv)

    scenarii = sorted(load_results(args.fisiere)["scenariu"].unique())
    q = debite(scenarii)
    lipsa = [s for s, v in q.items() if not math.isfinite(v)]
    if lipsa:   # caz(NaN) ar da tăcut „moderat”
        raise SystemExit(f"[totaluri] fereastră fără debit în profil: {lipsa}")
    cazuri = {s: caz(v, args.praguri) for s, v in q.items()}
    bands = [(b, [s for s, c in cazuri.items() if c == b]) for b in ("lejer", "moderat")] + [("greu", [])]
    programe = args.program or PROGRAME
    p = perechi(args.fisiere, None, programe, bands)
    ordine = p.sum().sort_values().index.tolist()
    refs = [r for r in args.referinte if r in p.columns]
    indisc = p.index.get_level_values(0).str.contains("indisciplinat_")
    caz_rand = pd.Series([cazuri[s] for s, _ in p.index], index=p.index)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    print(f"{len(p)} perechi; praguri {args.praguri}")
    print("\nPierderea totală (h):")
    for x in ordine:
        fata = "  ".join(f"față de {r}: {procent(p[x].sum(), p[r].sum())}" for r in refs if r != x)
        print(f"  {x:16s} {p[x].sum():9.1f}  indisc. {p.loc[indisc, x].sum():8.1f}  "
              f"disc. {p.loc[~indisc, x].sum():8.1f}  {fata}")

    print("\nPe cazuri de trafic (h):")
    print(p[ordine].groupby(caz_rand).sum().T.round(1).to_string())

    fara = caz_rand != "lejer"
    print(f"\nFără cazul lejer ({int(fara.sum())} perechi): media schimbărilor relative pe perechi (mai bun în k / n)")
    for r in refs:
        for x in ordine:
            if x != r:
                a, b = p.loc[fara, x], p.loc[fara, r]
                print(f"  {x:16s} față de {r:8s}: {((a - b) / b * 100).mean():+6.1f}%  ({int((a < b).sum())} / {len(a)})"
                      f"  total {procent(a.sum(), b.sum())}")

    try:
        tip = pd.DataFrame({t: perechi(args.fisiere, f"pierdere_h_{t}", programe, bands).sum() for t in TIPURI})
    except KeyError:
        print("\n(fișierele nu au pierderea pe tipuri de participanți)")
        return
    tip["total"] = tip.sum(axis=1)
    print("\nPe tipuri de participanți (h):")
    print(tip.loc[[x for x in ordine if x in tip.index]].round(0).to_string())
    for r in refs:
        print(f"\nPe tipuri, față de {r} (%):")
        print(((tip / tip.loc[r] - 1) * 100).drop(index=r).loc[[x for x in ordine if x != r]].round(1).to_string())


if __name__ == "__main__":
    main()
