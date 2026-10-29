"""Calitatea înregistrării, pe ore și pe 15 minute, dintr-un jurnal de traiectorii (§ 4.6).

Pe ore, pentru traiectoriile vehiculelor (fără pietoni), după ora de început:
  * goluri > 1 s   – ponderea intervalelor dintre puncte consecutive mai lungi de 1 s (cadre pierdute sau
                     redare sacadată a fluxului: vehiculul „sare” peste zonele mici de numărare);
  * densitatea     – puncte pe secundă de traiectorie (un vehicul oprit e detectat în fiecare cadru, deci
                     densitatea nu scade din cauza aglomerației, ci doar a înregistrării);
  * traiectorii    – câte traiectorii au început în acea oră.
Cifrele din § 4.6 sunt pe jurnalele brute (locale); pe jurnalele publicate din data/trajectories (doar vehiculele,
fragmentele reunite) ies practic aceleași (de ex. 21.10, 14:00: 17,3% / 0,98 puncte/s față de 17,2% / 0,98).

Pe 15 minute: rata efectivă de cadre prelucrate, adică pasul median dintre punctele consecutive ale traiectoriilor
(normal ≈0,17–0,2 s, la 5–6 cadre/s), și ponderea pașilor mai lungi de PAS_LUNG. Pe 28.10, între 03:46 și 04:28,
pasul median a urcat la ≈0,7 s. La ≈1,4 cadre/s, ByteTrack nu mai leagă vehiculele în mișcare (se mută prea mult de
la un cadru la altul și se rup în fragmente care nu ating zonele), iar mașinile parcate rămân urmărite: numărătorile
scad de câteva ori, iar traiectoriile par „fixe”. Semnul a fost luat întâi, greșit, drept o imagine înghețată; pozițiile
mașinilor parcate fluctuează însă normal, iar autobuzele traversează piața (§ 4.6). Intervalele cu cel puțin
PRAG_PASI_LUNGI pași lungi se afișează ca încetinite (și, cu --out-15min, se scriu); `scenarii_zi --fara-incetinite`
le poate scoate din alegerea ferestrelor.

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
PAS_LUNG = 0.5          # s; un pas mai lung între două puncte înseamnă cadre pierdute (normal ≈0,17–0,2 s)
PRAG_PASI_LUNGI = 0.4   # încetinit: cel puțin 40% dintre pași mai lungi de PAS_LUNG


def inregistrari(path: Path):
    """Traiectoriile din jurnal, citite ca în `recount`: un ultim bloc sau o ultimă linie incompletă se sare (lanțul de
    noapte citește ziua încheiată cât timp colectarea mai poate adăuga o traiectorie începută înainte de miezul nopții)."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        while True:
            try:
                line = fh.readline()
            except (EOFError, OSError):       # fișier în curs de scriere: ultimul bloc e incomplet
                return
            if not line:
                return
            try:
                d = json.loads(line)
            except json.JSONDecodeError:      # ultima linie poate fi incompletă dacă procesul a fost oprit
                continue
            yield d


def quality(path: Path) -> tuple[dict[str, list], dict[str, list]]:
    """oră → [intervale, intervale > 1 s, durata totală (s), puncte, traiectorii];
    interval de 15 min (HH:MM) → [traiectorii, în mișcare, duratele lor (s), pașii dintre puncte (s)]."""
    per = defaultdict(lambda: [0, 0, 0.0, 0, 0])
    per15 = defaultdict(lambda: [0, 0, [], []])
    for d in inregistrari(path):
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
        q[3].append(dt)
    return per, per15


def pasi(interval: list) -> tuple[float, float]:
    """Pasul median dintre puncte (s) și ponderea pașilor mai lungi de PAS_LUNG, pentru un interval din `quality`."""
    d = np.concatenate(interval[3]) if interval[3] else np.zeros(1)
    return float(np.median(d)), float((d > PAS_LUNG).mean())


def incetinite(per15: dict[str, list]) -> list[tuple]:
    """Intervalele cu prelucrarea încetinită: (HH:MM, traiectorii, în mișcare, pasul median în s, pași lungi %)."""
    out = []
    for k in sorted(per15):
        n, mis = per15[k][:2]
        med, lungi = pasi(per15[k])
        if n and lungi >= PRAG_PASI_LUNGI:
            out.append((k, n, mis, med, 100 * lungi))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jurnale", nargs="+", help="fișiere traiectorii_AAAA-LL-ZZ.jsonl.gz (se acceptă tipare)")
    ap.add_argument("--out", help="CSV: zi, ora, traiectorii, goluri_peste_1s_pct, densitate_puncte_s")
    ap.add_argument("--out-15min", help="CSV: zi, interval, traiectorii, in_miscare, fixe_pct, durata_mediana_s, "
                                        "pas_median_s, pasi_lungi_pct, incetinit")
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
        lente = incetinite(per15)
        if lente:
            print(f"  prelucrare încetinită (cel puțin {PRAG_PASI_LUNGI:.0%} din pași peste {PAS_LUNG} s; "
                  "vehicule în mișcare, pasul median):")
            for k, n, mis, med, lungi in lente:
                print(f"    {k}: {lungi:.0f}% pași lungi, pas median {med:.2f} s, {mis} / {n} vehicule în mișcare")
        else:
            print("  nicio încetinire a prelucrării")
        s = {x[0] for x in lente}
        for k in sorted(per15):
            n, mis, durs = per15[k][:3]
            med, lungi = pasi(per15[k])
            rows15.append([day, k, n, mis, round(100 * (1 - mis / n), 1), round(float(np.median(durs)), 1),
                           round(med, 3), round(100 * lungi, 1), int(k in s)])
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
            w.writerow(["zi", "interval", "traiectorii", "in_miscare", "fixe_pct", "durata_mediana_s", "pas_median_s",
                        "pasi_lungi_pct", "incetinit"])
            w.writerows(rows15)
        print(f"→ {a.out_15min}")


if __name__ == "__main__":
    main()
