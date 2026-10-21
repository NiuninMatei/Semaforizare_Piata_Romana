"""Renumărarea din jurnalul de traiectorii, cu zonele curente din config/camera.json.

Modulul de viziune salvează, pe lângă numărători, traiectoriile anonime (clasă + punctele de
contact cu solul, normalizate). Astfel zonele pot fi recalibrate după colectare, iar
numărătorile se refac fără a mai avea nevoie de imagini (care nu se păstrează – GDPR).

Exemple:
  python -m romana.vision.recount                                   # toate zilele din data/trajectories
  python -m romana.vision.recount --zi 2026-10-21 --interval 900
  python -m romana.vision.recount --zi 2026-10-21 --directii        # verificarea sensului de mers pe zone
"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from romana.common import COUNTS_DIR, TRAJ_DIR, load_json
from romana.vision.od_counter import PEDESTRIAN, ODCounter, Params, classify, load_zones, write_csv


def read_trajectories(files: list[Path]):
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:      # ultima linie poate fi incompletă dacă procesul a fost oprit
                    continue
                yield r["t0"], r["tip"], [(r["t0"] + t, x, y) for t, x, y in r["p"]]


def recount(files: list[Path], zones, interval_s: int, out_dir: Path, params: Params) -> list[dict]:
    """Reconstruiește numărătorile pe intervale; suprascrie CSV-urile zilelor respective."""
    buckets = defaultdict(list)
    for t0, vt, pts in read_trajectories(files):
        buckets[t0 - t0 % interval_s].append((vt, pts))
    days = {time.strftime("%Y-%m-%d", time.localtime(s)) for s in buckets}
    for d in days:
        (out_dir / f"numaratori_{d}.csv").unlink(missing_ok=True)
    recs = []
    for start in sorted(buckets):
        c = ODCounter(zones, interval_s=interval_s, clock=lambda s=start: s)
        c.p = params
        for vt, pts in buckets[start]:
            if len(pts) >= params.min_track_frames:
                c.add(vt, classify(vt, pts, zones, params))
        last = max(p[-1][0] for _, p in buckets[start])
        rec = {"start": start, "end": min(start + interval_s, last), "od": dict(c.od), "in": dict(c.arm_in),
               "out": dict(c.arm_out), "pietoni": dict(c.peds)}
        write_csv(rec, out_dir)
        recs.append(rec)
    return recs


def directions(files: list[Path], zones, center=(0.55, 0.52)) -> None:
    """Pentru fiecare zonă de vehicule: câte traiectorii se apropie / se îndepărtează de centrul pieței."""
    stats = defaultdict(lambda: [0, 0])
    for _, vt, pts in read_trajectories(files):
        if vt == PEDESTRIAN:
            continue
        for z in zones:
            if z.role == "trecere":
                continue
            inside = np.array([(x, y) for _, x, y in pts if z.contains_norm(x, y)])
            if len(inside) < 2 or np.linalg.norm(inside[-1] - inside[0]) < 0.005:
                continue
            toward = np.dot(inside[-1] - inside[0], np.array(center) - inside[0]) > 0
            stats[z.id][0 if toward else 1] += 1
    for z in zones:
        if z.role != "trecere":
            a, b = stats[z.id]
            ok = (a >= b) == (z.role == "intrare")
            print(f"{z.id:24s} {z.role:8s} spre centru {a:5d}   dinspre centru {b:5d}   {'OK' if ok else 'SENS INVERS?'}")


def main(argv=None) -> None:
    cam = load_json("camera.json")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", nargs="*", help="zile AAAA-LL-ZZ (implicit toate)")
    ap.add_argument("--interval", type=int, default=cam.get("interval_s", 900))
    ap.add_argument("--out", default=str(COUNTS_DIR))
    ap.add_argument("--directii", action="store_true", help="doar verificarea sensului de mers pe zone")
    args = ap.parse_args(argv)
    files = sorted(TRAJ_DIR.glob("traiectorii_*.jsonl.gz"))
    if args.zi:
        files = [f for f in files if any(d in f.name for d in args.zi)]
    if not files:
        raise SystemExit(f"Nu există jurnale de traiectorii în {TRAJ_DIR}.")
    zones = load_zones(cam)
    if args.directii:
        directions(files, zones)
        return
    p = Params(capat_s=cam.get("capat_s", 1.5))
    recs = recount(files, zones, args.interval, Path(args.out), p)
    n_in = sum(sum(r["in"].values()) for r in recs)
    n_od = sum(sum(r["od"].values()) for r in recs)
    n_p = sum(sum(r["pietoni"].values()) for r in recs)
    print(f"[OK] {len(recs)} intervale: {n_in} intrări, {n_od} viraje complete, {n_p} pietoni → {args.out}")


if __name__ == "__main__":
    main()
