"""Renumărarea din jurnalul de traiectorii, cu zonele curente din config/camera.json.

Modulul de viziune salvează, pe lângă numărători, traiectoriile anonime (clasă + punctele de
contact cu solul, normalizate). Astfel zonele pot fi recalibrate după colectare, iar
numărătorile se refac fără a mai avea nevoie de imagini (care nu se păstrează – GDPR).

Exemple:
  python -m romana.vision.recount                                   # toate zilele din data/trajectories
  python -m romana.vision.recount --zi 2026-10-21 --interval 900
  python -m romana.vision.recount --zi 2026-10-21 --directii        # verificarea sensului de mers pe zone
  python -m romana.vision.recount --flux cadru.jpg                   # câmpul de mișcare, pentru calibrarea zonelor
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
            while True:
                try:
                    line = fh.readline()
                except (EOFError, OSError):       # fișier în curs de scriere: ultimul bloc e incomplet
                    break
                if not line:
                    break
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:      # ultima linie poate fi incompletă dacă procesul a fost oprit
                    continue
                yield r["t0"], r["tip"], [(r["t0"] + t, x, y) for t, x, y in r["p"]]


def _velocity(pts: list, end: bool, window: float = 1.0) -> np.ndarray:
    """Viteza medie (unități normalizate / s) pe ultima (end=True) sau prima secundă a traiectoriei."""
    if end:
        seg = [p for p in pts if p[0] >= pts[-1][0] - window]
    else:
        seg = [p for p in pts if p[0] <= pts[0][0] + window]
    if len(seg) < 2 or seg[-1][0] - seg[0][0] < 1e-3:
        return np.zeros(2)
    return np.array([seg[-1][1] - seg[0][1], seg[-1][2] - seg[0][2]]) / (seg[-1][0] - seg[0][0])


def stitch(tracks: list[tuple[str, list]], max_gap: float = 2.0, radius: float = 0.02,
           aspect: float = 1850 / 3288) -> list[tuple[str, list]]:
    """Reunește fragmentele aceleiași traiectorii, întrerupte de ocluzii (stâlpi, autobuze, copaci).

    Un fragment care se termină la momentul t este legat de un fragment care începe în (t, t+max_gap],
    de aceeași categorie (vehicul / pieton), aflat aproape de poziția prezisă din viteza de la capăt
    (rază `radius` + 30% din distanța parcursă în gol) și cu direcție compatibilă. Legăturile se aleg
    lacom, după costul cel mai mic. Fără reunire, o ocluzie face ca un vehicul să fie numărat de două
    ori (două „intrări”) sau deloc (golul cade exact peste o linie de numărare)."""
    if not tracks:
        return []
    tr = sorted(tracks, key=lambda r: r[1][0][0])
    starts = np.array([r[1][0][0] for r in tr])
    cands = []
    for i, (vt, pts) in enumerate(tr):
        te, xe, ye = pts[-1]
        ve = _velocity(pts, end=True)
        ped = vt == PEDESTRIAN
        lo, hi = np.searchsorted(starts, te, "right"), np.searchsorted(starts, te + max_gap, "right")
        for j in range(lo, hi):
            vt2, pts2 = tr[j]
            if (vt2 == PEDESTRIAN) != ped:
                continue
            ts, xs, ys = pts2[0]
            dt = ts - te
            pred = np.array([xe, ye]) + ve * dt
            d = np.hypot(xs - pred[0], (ys - pred[1]) * aspect)
            r = radius * (0.5 if ped else 1.0) + 0.3 * np.hypot(*(ve * dt * [1, aspect]))
            if d > r:
                continue
            vs = _velocity(pts2, end=False)
            if np.hypot(*ve) > 0.01 and np.hypot(*vs) > 0.01 and np.dot(ve, vs) < 0:
                continue                       # direcții opuse
            cands.append((d / r + dt / max_gap, i, j))
    nxt, prev = {}, {}
    for _, i, j in sorted(cands):
        if i not in nxt and j not in prev:
            nxt[i], prev[j] = j, i
    out = []
    for i in range(len(tr)):
        if i in prev:
            continue
        chain, votes = [], defaultdict(int)
        k = i
        while True:
            vt, pts = tr[k]
            votes[vt] += len(pts)
            chain.extend(pts)
            if k not in nxt:
                break
            k = nxt[k]
        out.append((max(votes, key=votes.get), chain))
    return out


def recount(files: list[Path], zones, interval_s: int, out_dir: Path, params: Params,
            do_stitch: bool = True) -> list[dict]:
    """Reconstruiește numărătorile pe intervale; suprascrie CSV-urile zilelor respective."""
    tracks = [(vt, pts) for _, vt, pts in read_trajectories(files)]
    if do_stitch:
        n0 = len(tracks)
        tracks = stitch(tracks)
        print(f"[renumărare] {n0} fragmente → {len(tracks)} traiectorii după reunire")
    buckets = defaultdict(list)
    for vt, pts in tracks:
        t0 = pts[0][0]
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


def flow_image(files: list[Path], zones, background, out_png: Path, cell=(0.015, 0.012)) -> None:
    """Câmpul de mișcare al vehiculelor (direcția medie pe celule) + capetele traiectoriilor.

    Săgeți galbene = mișcare în jos în imagine, mov = în sus; puncte verzi = începuturi de
    traiectorii, roșii = sfârșituri. Servește la plasarea zonelor (sensul benzilor și locurile în
    care vehiculele apar din / dispar în străzile parțial ascunse)."""
    import cv2

    h, w = background.shape[:2]
    acc = defaultdict(lambda: np.zeros(3))
    starts, ends = [], []
    for _, vt, pts in read_trajectories(files):
        if vt == PEDESTRIAN or len(pts) < 5:
            continue
        P = np.array([(x * w, y * h) for _, x, y in pts])
        if np.linalg.norm(P[-1] - P[0]) > 0.03 * w:
            starts.append(P[0])
            ends.append(P[-1])
        for a, b in zip(P[:-1], P[1:]):
            v = b - a
            n = np.linalg.norm(v)
            if 3 < n < 250:
                acc[(int(a[0] / w / cell[0]), int(a[1] / h / cell[1]))] += [v[0] / n, v[1] / n, 1]
    img = (background * 0.55).astype(np.uint8)
    for z in zones:
        cv2.polylines(img, [z.poly_px(w, h)], True, z.color, 3)
        cv2.putText(img, z.id, tuple(z.poly_px(w, h)[0]), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    for p in starts:
        cv2.circle(img, tuple(p.astype(int)), 5, (0, 200, 0), -1)
    for p in ends:
        cv2.circle(img, tuple(p.astype(int)), 5, (0, 0, 230), -1)
    for (i, j), (vx, vy, n) in acc.items():
        if n < 5 or np.hypot(vx, vy) / n < 0.5:
            continue                                      # celule rare sau cu sensuri amestecate
        c = np.array([(i + 0.5) * cell[0] * w, (j + 0.5) * cell[1] * h])
        u = np.array([vx, vy]) / np.hypot(vx, vy)
        cv2.arrowedLine(img, tuple((c - u * 18).astype(int)), tuple((c + u * 18).astype(int)),
                        (0, 255, 255) if u[1] > 0 else (255, 0, 255), 3, tipLength=0.5)
    for v in np.arange(0.05, 1.0, 0.05):                 # gradație normalizată, pentru editarea poligoanelor
        cv2.putText(img, f"{v:.2f}", (int(v * w), int(0.37 * h)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        if v >= 0.4:
            cv2.putText(img, f"{v:.2f}", (5, int(v * h)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.imwrite(str(out_png), img[int(0.35 * h):])
    print(f"[OK] {out_png}  ({len(starts)} traiectorii lungi)")


def main(argv=None) -> None:
    cam = load_json("camera.json")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", nargs="*", help="zile AAAA-LL-ZZ (implicit toate)")
    ap.add_argument("--interval", type=int, default=cam.get("interval_s", 900))
    ap.add_argument("--out", default=str(COUNTS_DIR))
    ap.add_argument("--directii", action="store_true", help="doar verificarea sensului de mers pe zone")
    ap.add_argument("--flux", metavar="IMAGINE.jpg",
                    help="desenează câmpul de mișcare și capetele traiectoriilor peste un cadru (fișier .jpg)")
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
    if args.flux:
        import cv2

        bg = cv2.imread(args.flux)
        flow_image(files, zones, bg, Path(args.flux).with_name(Path(args.flux).stem + "_flux.jpg"))
        return
    p = Params(capat_s=cam.get("capat_s", 1.5))
    recs = recount(files, zones, args.interval, Path(args.out), p)
    n_in = sum(sum(r["in"].values()) for r in recs)
    n_od = sum(sum(r["od"].values()) for r in recs)
    n_p = sum(sum(r["pietoni"].values()) for r in recs)
    print(f"[OK] {len(recs)} intervale: {n_in} intrări, {n_od} viraje complete, {n_p} pietoni → {args.out}")


if __name__ == "__main__":
    main()
