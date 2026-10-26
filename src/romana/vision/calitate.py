"""Calitatea înregistrării, pe ore, dintr-un jurnal de traiectorii (§ 4.6): cât de continuă a fost urmărirea.

Pentru traiectoriile vehiculelor (fără pietoni), pe ora de început:
  * goluri > 1 s   – ponderea intervalelor dintre puncte consecutive mai lungi de 1 s (cadre pierdute sau
                     redare sacadată a fluxului: vehiculul „sare” peste zonele mici de numărare);
  * densitatea     – puncte pe secundă de traiectorie (un vehicul oprit e detectat în fiecare cadru, deci
                     densitatea nu scade din cauza aglomerației, ci doar a înregistrării);
  * traiectorii    – câte traiectorii au început în acea oră.
Cifrele din § 4.6 sunt pe jurnalele brute (locale); pe jurnalele publicate din data/trajectories (doar vehiculele,
fragmentele reunite) ies practic aceleași (de ex. 21.10, 14:00: 17,3% / 0,98 puncte/s față de 17,2% / 0,98).

Exemplu:
  python -m romana.vision.calitate data/trajectories_brute/traiectorii_2026-10-2*.jsonl.gz --out outputs/calitate.csv
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import defaultdict
from datetime import datetime
from glob import glob
from pathlib import Path

import numpy as np

from romana.vision.od_counter import PEDESTRIAN


def quality(path: Path) -> dict[str, list]:
    """oră → [intervale, intervale > 1 s, durata totală (s), puncte, traiectorii]."""
    per = defaultdict(lambda: [0, 0, 0.0, 0, 0])
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("tip") == PEDESTRIAN or len(d["p"]) < 2:
                continue
            ts = np.array([q[0] for q in d["p"]])
            dt = np.diff(ts)
            r = per[datetime.fromtimestamp(d["t0"]).strftime("%H")]
            r[0] += len(dt)
            r[1] += int((dt > 1.0).sum())
            r[2] += float(ts[-1] - ts[0])
            r[3] += len(ts)
            r[4] += 1
    return per


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jurnale", nargs="+", help="fișiere traiectorii_AAAA-LL-ZZ.jsonl.gz (se acceptă tipare)")
    ap.add_argument("--out", help="CSV: zi, ora, traiectorii, goluri_peste_1s_pct, densitate_puncte_s")
    a = ap.parse_args()
    files = sorted({Path(f) for p in a.jurnale for f in (glob(p) or [p])})
    rows = []
    for f in files:
        day = f.name.split("_")[-1].split(".")[0]
        print(f"\n{day}")
        for h, (n, big, dur, pts, k) in sorted(quality(f).items()):
            g, dens = 100 * big / max(n, 1), pts / max(dur, 1)
            print(f"  {h}: {k:6d} traiectorii  goluri > 1 s {g:5.1f}%  densitate {dens:4.2f} puncte/s")
            rows.append([day, h, k, round(g, 2), round(dens, 3)])
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(["zi", "ora", "traiectorii", "goluri_peste_1s_pct", "densitate_puncte_s"])
            w.writerows(rows)
        print(f"\n→ {a.out}")


if __name__ == "__main__":
    main()
