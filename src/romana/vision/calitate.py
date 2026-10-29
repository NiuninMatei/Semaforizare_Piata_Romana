"""Calitatea înregistrării, pe ore, dintr-un jurnal de traiectorii (§ 4.6): cât de continuă a fost urmărirea.

Pentru traiectoriile vehiculelor (fără pietoni), pe ora de început:
  * goluri > 1 s   – ponderea intervalelor dintre puncte consecutive mai lungi de 1 s (cadre pierdute sau
                     redare sacadată a fluxului: vehiculul „sare” peste zonele mici de numărare);
  * densitatea     – puncte pe secundă de traiectorie (un vehicul oprit e detectat în fiecare cadru, deci
                     densitatea nu scade din cauza aglomerației, ci doar a înregistrării);
  * traiectorii    – câte traiectorii au început în acea oră.
Cifrele din § 4.6 sunt pe jurnalele brute (locale); pe jurnalele publicate din data/trajectories (doar vehiculele,
fragmentele reunite) ies practic aceleași (de ex. 21.10, 14:00: 17,3% / 0,98 puncte/s față de 17,2% / 0,98).

Imaginea înghețată (28.10, ≈03:40–04:30) nu se vede în goluri și densitate: același cadru, repetat, dă detecții dense
ale vehiculelor parcate. Semnul ei, pe intervale de 15 minute: puține vehicule în mișcare (deplasarea netă de cel
puțin MISCARE_MIN din cadru) față de intervalele din jur (±2 h) și multe traiectorii fixe. Intervalele suspecte se
afișează (și, cu --out-15min, se scriu); alegerea ferestrelor din `scenarii_zi` nu le folosește încă.

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

MISCARE_MIN = 0.02      # deplasarea netă minimă (coordonate normalizate) a unui vehicul „în mișcare”
INGHET_RAPORT = 0.3     # suspect: în mișcare sub 30% din mediana intervalelor din jur (±2 h) ...
INGHET_FIXE = 0.75      # ... și cel puțin 75% dintre traiectorii fixe


def quality(path: Path) -> tuple[dict[str, list], dict[str, list]]:
    """oră → [intervale, intervale > 1 s, durata totală (s), puncte, traiectorii];
    interval de 15 min (HH:MM) → [traiectorii, în mișcare, duratele lor (s)]."""
    per = defaultdict(lambda: [0, 0, 0.0, 0, 0])
    per15 = defaultdict(lambda: [0, 0, []])
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("tip") == PEDESTRIAN or len(d["p"]) < 2:
                continue
            ts = np.array([q[0] for q in d["p"]])
            dt = np.diff(ts)
            t0 = datetime.fromtimestamp(d["t0"])
            r = per[t0.strftime("%H")]
            r[0] += len(dt)
            r[1] += int((dt > 1.0).sum())
            r[2] += float(ts[-1] - ts[0])
            r[3] += len(ts)
            r[4] += 1
            q = per15[f"{t0.hour:02d}:{t0.minute // 15 * 15:02d}"]
            q[0] += 1
            q[1] += int(np.hypot(d["p"][-1][1] - d["p"][0][1], d["p"][-1][2] - d["p"][0][2]) >= MISCARE_MIN)
            q[2].append(float(ts[-1] - ts[0]))
    return per, per15


def inghetate(per15: dict[str, list]) -> list[tuple]:
    """Intervalele suspecte de imagine înghețată: (HH:MM, traiectorii, în mișcare, mediana vecinilor, fixe %, durata
    mediană în s)."""
    chei = sorted(per15)
    out = []
    for i, k in enumerate(chei):
        n, mis, durs = per15[k]
        vecini = [per15[c][1] for c in chei[max(0, i - 8):i] + chei[i + 1:i + 9]]
        if not vecini or n == 0:
            continue
        ref = float(np.median(vecini))
        fixe = 1 - mis / n
        if ref > 0 and mis < INGHET_RAPORT * ref and fixe >= INGHET_FIXE:
            out.append((k, n, mis, ref, 100 * fixe, float(np.median(durs))))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jurnale", nargs="+", help="fișiere traiectorii_AAAA-LL-ZZ.jsonl.gz (se acceptă tipare)")
    ap.add_argument("--out", help="CSV: zi, ora, traiectorii, goluri_peste_1s_pct, densitate_puncte_s")
    ap.add_argument("--out-15min", help="CSV: zi, interval, traiectorii, in_miscare, fixe_pct, durata_mediana_s, "
                                        "suspect_inghet")
    a = ap.parse_args()
    files = sorted({Path(f) for p in a.jurnale for f in (glob(p) or [p])})
    rows, rows15 = [], []
    for f in files:
        day = f.name.split("_")[-1].split(".")[0]
        print(f"\n{day}")
        per, per15 = quality(f)
        for h, (n, big, dur, pts, k) in sorted(per.items()):
            g, dens = 100 * big / max(n, 1), pts / max(dur, 1)
            print(f"  {h}: {k:6d} traiectorii  goluri > 1 s {g:5.1f}%  densitate {dens:4.2f} puncte/s")
            rows.append([day, h, k, round(g, 2), round(dens, 3)])
        susp = inghetate(per15)
        if susp:
            print("  posibilă imagine înghețată (vehicule în mișcare față de mediana vecinilor, traiectorii fixe, "
                  "durata mediană):")
            for k, n, mis, ref, fixe, dmed in susp:
                print(f"    {k}: {mis} / {ref:.0f} în mișcare, {fixe:.0f}% fixe, {dmed:.0f} s ({n} traiectorii)")
        else:
            print("  nicio imagine înghețată suspectă")
        s = {x[0] for x in susp}
        for k in sorted(per15):
            n, mis, durs = per15[k]
            rows15.append([day, k, n, mis, round(100 * (1 - mis / n), 1), round(float(np.median(durs)), 1),
                           int(k in s)])
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(["zi", "ora", "traiectorii", "goluri_peste_1s_pct", "densitate_puncte_s"])
            w.writerows(rows)
        print(f"\n→ {a.out}")
    if a.out_15min:
        Path(a.out_15min).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out_15min, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(["zi", "interval", "traiectorii", "in_miscare", "fixe_pct", "durata_mediana_s", "suspect_inghet"])
            w.writerows(rows15)
        print(f"→ {a.out_15min}")


if __name__ == "__main__":
    main()
