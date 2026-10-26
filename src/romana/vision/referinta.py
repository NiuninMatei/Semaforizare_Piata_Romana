"""Numărătoarea de referință și factorii de corecție a detecției (§ 4.3, recalibrarea din 26.10.2026).

Fluxul de lucru, pe unul sau mai multe clipuri scurte (câteva minute) ale camerei:
  1. `foi`     – foile de contact pentru adnotare: pentru fiecare țintă (o intrare de vehicule, o zebră) și
                 fiecare bucată de timp (implicit 30 s), decupajul țintei la fiecare 0,5 s, cu liniile și
                 poligoanele de numărare desenate; imaginile din afara bucății (1 s înainte și după) au chenar
                 gri și eticheta CONTEXT, cele din bucată chenar verde. Adnotatorii (doi independenți, un al
                 treilea ca arbitru la diferențe peste max(2; 15%)) numără pe foi câte obiecte trec în bucată.
  2. `viziune` – rulează exact lanțul live (`run_vision`: același detector, aceeași rezoluție, aceleași cadre
                 pe secundă, ByteTrack) pe clipul salvat, cu jurnalul de traiectorii, numărătorile și cadrul de
                 previzualizare redirecționate într-un director separat – nu atinge data/ și nici dispeceratul.
  3. `numara`  – numărătorile unui set de zone (un fișier ca config/camera.json) pe traiectoriile clipului,
                 pe bucăți de timp: intrările după începutul traiectoriei, ieșirile după sfârșitul ei, pietonii
                 după începutul traiectoriei; timpul e raportat la prima detecție din clip.
  4. `factori` – factorul de corecție pe țintă = referința / numărarea automată, pe bucățile adnotate ale
                 tuturor clipurilor, cu interval de încredere 90% prin bootstrap pe bucăți, și procentul din
                 referință prins de numărarea automată pe fiecare clip (scorul unei variante de zone).
                 Țintele fără nicio numărare automată (ex. pietonii, absenți din jurnalul publicat) se omit.
  5. `publica` – jurnalul publicabil al unui clip: doar traiectoriile vehiculelor, deja reunite (aceeași
                 funcție ca `recount --publica`); pe el, `factori` dă aceiași factori de vehicule ca pe
                 jurnalul complet.

Formatul țintelor pentru `foi` (TINTE.json, coordonate normalizate ale cadrului întreg):
  [{"id": "V_magheru", "tip": "vehicule", "decupaj": [x0, y0, x1, y1],
    "linii": [[xa, ya, xb, yb], ...], "poligoane": [[[x, y], ...], ...]}, ...]
Referința pentru `factori` (CSV, câte unul pe clip): `tinta,bucata,numar` – numărul final pe bucată – sau,
cu o coloană `adnotator` („0”, „1”, „arbitru”), numărătorile fiecărui adnotator: referința bucății este
atunci numărul arbitrului, altfel media celor doi dacă diferă cu cel mult max(2; 15%); celelalte bucăți nu
sunt adnotate complet și se ignoră. Bucata k acoperă [30·k, 30·(k+1)) s de la începutul clipului.

Confidențialitate: clipurile video și foile de contact conțin imagini ale camerei (persoane, vehicule): se
păstrează DOAR local, numai pe durata adnotării (implicit în outputs/, exclus din Git, ca și fișierele .mp4),
nu se publică și se șterg după adnotare. Jurnalul complet de traiectorii al clipului conține și pietonii, deci
rămâne tot local (outputs/referinta/). În depozit (docs/rezultate/referinta/) ajung numai rezultatele, fără
imagini: numărătorile adnotatorilor pe bucăți, factorii și traiectoriile vehiculelor (`publica`).

Exemple:
  python -m romana.vision.referinta foi tinte.json clip1.mp4 --out outputs/referinta/foi_clip1
  python -m romana.vision.referinta viziune clip1.mp4 --out outputs/referinta/clip1
  python -m romana.vision.referinta numara outputs/referinta/clip1/traiectorii --camera config/camera.json
  python -m romana.vision.referinta publica outputs/referinta/clip1/traiectorii docs/rezultate/referinta/clip1/traiectorii
  python -m romana.vision.referinta factori ^
      --clip docs/rezultate/referinta/clip1/traiectorii docs/rezultate/referinta/referinta_clip1.csv ^
      --clip docs/rezultate/referinta/clip2/traiectorii docs/rezultate/referinta/referinta_clip2.csv
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from romana.common import CONFIG_DIR, OUTPUT_DIR, load_json

REF_DIR = OUTPUT_DIR / "referinta"
# țintele adnotate → cheile numărătorii automate (`numara`); o țintă poate aduna mai multe zone
MAPARE_IMPLICITA = {
    "V_magheru": ["intrare:magheru"], "V_dacia_est": ["intrare:dacia_est"], "V_dacia_vest": ["intrare:dacia_vest"],
    "V_catargiu2": ["intrare:catargiu"], "P_dacia_est_iesire": ["pietoni:trecere_dacia_est_iesire"],
    "P_dacia_est_intrare": ["pietoni:trecere_dacia_est_intrare"], "P_magheru": ["pietoni:trecere_magheru"],
}


# ---------------------------------------------------------------- 1. foile de contact

def _tile(frame, target: dict, width: int):
    """Decupajul unei ținte dintr-un cadru, cu liniile și poligoanele de numărare, la lățimea `width`."""
    import cv2

    g = frame.copy() if (target.get("linii") or target.get("poligoane")) else frame
    H, W = g.shape[:2]
    for poly in target.get("poligoane", []):
        q = (np.array(poly) * [W, H]).astype(np.int32)
        cv2.polylines(g, [q], True, (0, 165, 255), 2)
    for xa, ya, xb, yb in target.get("linii", []):
        cv2.line(g, (int(xa * W), int(ya * H)), (int(xb * W), int(yb * H)), (0, 0, 255), 2)
    x0, y0, x1, y1 = target["decupaj"]
    c = g[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
    s = width / c.shape[1]
    return cv2.resize(c, (width, int(c.shape[0] * s)), interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)


def _sheet(images: list, columns: int):
    """Imaginile așezate pe `columns` coloane (completate cu gri închis)."""
    while len(images) % columns:
        images.append(np.full_like(images[0], 30))
    return np.vstack([np.hstack(images[i:i + columns]) for i in range(0, len(images), columns)])


def contact_sheets(targets: list[dict], clip: str, out: Path, chunk_s: float = 30, dt: float = 0.5,
                   per_sheet: int = 12, columns: int = 3, width: int = 800) -> int:
    """Foile de contact: out/<id>/b<k>_f<j>.jpg pentru fiecare țintă și bucată. Clipul se citește o dată, secvențial."""
    import cv2

    cap = cv2.VideoCapture(clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 18.0
    duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
    step = max(1, int(round(dt * fps)))
    tiles = defaultdict(dict)                         # id -> {t: jpeg}
    k = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if k % step == 0:
            t = round(k / fps, 2)
            for tg in targets:
                tiles[tg["id"]][t] = cv2.imencode(".jpg", _tile(f, tg, width), [cv2.IMWRITE_JPEG_QUALITY, 90])[1]
        k += 1
    cap.release()
    n_chunks = int(np.ceil(duration / chunk_s))
    for tg in targets:
        td = out / tg["id"]
        td.mkdir(parents=True, exist_ok=True)
        ts = sorted(tiles[tg["id"]])
        for b in range(n_chunks):
            lo, hi = b * chunk_s, min((b + 1) * chunk_s, duration)
            sel = [t for t in ts if lo - 1.0 - 1e-6 <= t < hi + 1.0]
            for j in range(0, len(sel), per_sheet):
                imgs = []
                for t in sel[j:j + per_sheet]:
                    im = cv2.imdecode(tiles[tg["id"]][t], cv2.IMREAD_COLOR)
                    inside = lo <= t < hi
                    im = cv2.copyMakeBorder(im, 6, 6, 6, 6, cv2.BORDER_CONSTANT,
                                            value=(0, 200, 0) if inside else (128, 128, 128))
                    lab = f"t={t:6.1f}s" + ("" if inside else "  CONTEXT")
                    cv2.rectangle(im, (6, 6), (6 + 11 * len(lab) + 8, 32), (0, 0, 0), -1)
                    cv2.putText(im, lab, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    imgs.append(im)
                if imgs:
                    cv2.imwrite(str(td / f"b{b}_f{j // per_sheet}.jpg"), _sheet(imgs, columns),
                                [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"[foi] {tg['id']} gata")
    print(f"[foi] durata clipului {duration:.1f} s; {n_chunks} bucăți de {chunk_s:g} s → {out}")
    return n_chunks


# ---------------------------------------------------------------- 2. lanțul live pe un clip salvat

def run_offline(clip: str, out: Path, interval_s: int = 30, extra: list[str] | None = None) -> None:
    """Rulează `run_vision` pe clip cu ieșirile în `out` (traiectorii/, numaratori/, live/), nu în data/."""
    import romana.vision.run_vision as rv

    out.mkdir(parents=True, exist_ok=True)
    rv.TRAJ_RAW_DIR = out / "traiectorii"           # jurnalul complet al clipului (și pietonii) – local
    rv.LIVE_DIR = out / "live"                       # cadrul de previzualizare, separat de cel al dispeceratului
    t0 = time.time()
    rv.main(["--source", clip, "--out", str(out / "numaratori"), "--interval", str(interval_s)] + list(extra or []))
    print(f"[viziune] {time.time() - t0:.0f} s pentru clip; traiectoriile în {rv.TRAJ_RAW_DIR}")


# ---------------------------------------------------------------- 3. numărarea pe bucăți

def count_by_chunk(traj_dir: Path, cam: dict, chunk_s: float = 30, do_stitch: bool = True,
                   min_frames: int = 3) -> dict:
    """{"intrare:<braț>" / "iesire:<braț>" / "pietoni:<zonă>" / "viraj:<o>><d>": {"total", "pe_bucati"}}.

    Bucățile sunt numerotate de la prima detecție din clip (cheile din `pe_bucati` sunt întregi)."""
    from romana.vision.od_counter import PEDESTRIAN, Params, classify, load_zones
    from romana.vision.recount import read_trajectories, stitch

    zones = load_zones(cam)
    p = Params(capat_s=cam.get("capat_s", 1.5))
    for k, v in cam.get("parametri_numarare", {}).items():
        setattr(p, k, v)
    files = sorted(Path(traj_dir).glob("*.jsonl.gz"))
    tracks = [(vt, pts) for _, vt, pts in read_trajectories(files)]
    if not tracks:
        raise SystemExit(f"Nicio traiectorie în {traj_dir}.")
    t0 = min(pts[0][0] for _, pts in tracks)
    if do_stitch:
        tracks = stitch(tracks)
    res = defaultdict(Counter)
    for vt, pts in tracks:
        if len(pts) < min_frames:
            continue
        r = classify(vt, pts, zones, p)
        b_start, b_end = int((pts[0][0] - t0) // chunk_s), int((pts[-1][0] - t0) // chunk_s)
        if vt == PEDESTRIAN:
            for _, zid in r["treceri"]:
                res[("pietoni", zid)][b_start] += 1
            continue
        if r["origine"]:
            res[("intrare", r["origine"])][b_start] += 1
        if r["destinatie"]:
            res[("iesire", r["destinatie"])][b_end] += 1
        if r["origine"] and r["destinatie"]:
            res[("viraj", f"{r['origine']}>{r['destinatie']}")][0] += 1
    return {f"{k[0]}:{k[1]}": {"total": sum(c.values()), "pe_bucati": dict(sorted(c.items()))}
            for k, c in sorted(res.items())}


# ---------------------------------------------------------------- 4. referința și factorii

def _chunk_index(v) -> int:
    return int(str(v).strip().lstrip("bB"))


def combine_annotators(values: dict) -> float | None:
    """Referința unei bucăți din numărătorile adnotatorilor {„0”: n0, „1”: n1, „arbitru”: na}."""
    if "arbitru" in values:
        return float(values["arbitru"])
    if "0" in values and "1" in values:
        a, c = values["0"], values["1"]
        if abs(a - c) <= max(2, round(0.15 * max(a, c))):
            return (a + c) / 2
    return None                                      # bucată neadnotată complet


def load_reference(path: Path) -> dict[tuple[str, int], float]:
    """Referința dintr-un CSV `tinta,bucata,numar[,adnotator]` → {(țintă, bucată): număr de referință}."""
    import pandas as pd

    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns={"țintă": "tinta", "bucată": "bucata", "număr": "numar"})
    missing = {"tinta", "bucata", "numar"} - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: lipsesc coloanele {sorted(missing)}")
    if "adnotator" not in df.columns:
        if df.duplicated(["tinta", "bucata"]).any():
            raise SystemExit(f"{path}: bucăți dublate fără coloana `adnotator`")
        return {(r.tinta, _chunk_index(r.bucata)): float(r.numar) for r in df.itertuples()}
    per = defaultdict(dict)
    for r in df.itertuples():
        per[(r.tinta, _chunk_index(r.bucata))][str(r.adnotator).strip()] = float(r.numar)
    ref = {k: combine_annotators(v) for k, v in per.items()}
    return {k: v for k, v in ref.items() if v is not None}


def _round2(v) -> float | None:
    return None if v is None else round(float(v), 2)


def correction_factors(pairs: dict[str, list[tuple[float, int, str]]], n_boot: int = 2000,
                       seed: int = 0) -> dict:
    """Factorul referință / automat pe țintă, cu IC 90% prin bootstrap pe bucăți (percentilele 5 și 95)."""
    rng = np.random.default_rng(seed)
    out = {}
    for tid, pr in sorted(pairs.items()):
        r = np.array([p[0] for p in pr], float)
        a = np.array([p[1] for p in pr], float)
        bs = []
        for _ in range(n_boot):                       # rulat și pentru țintele omise: aceeași secvență aleatorie
            i = rng.integers(0, len(r), len(r))
            if a[i].sum() > 0:
                bs.append(r[i].sum() / a[i].sum())
        if a.sum() == 0:                              # ținta lipsește din traiectorii: niciun factor de calculat
            f = lo = hi = None
        else:
            f = r.sum() / a.sum()
            lo, hi = np.percentile(bs, [5, 95]) if bs else (np.nan, np.nan)
        clips = {}
        for ref, auto, clip in pr:
            c = clips.setdefault(clip, {"referinta": 0.0, "automat": 0})
            c["referinta"] += ref
            c["automat"] += int(auto)
        for c in clips.values():
            c["procent_prins"] = round(100 * c["automat"] / c["referinta"], 1) if c["referinta"] else None
        out[tid] = {"factor": _round2(f), "ic90": [_round2(lo), _round2(hi)],
                    "bucati": len(pr), "referinta": float(r.sum()), "automat": int(a.sum()), "pe_clipuri": clips}
    return out


def publish_clip(traj_dir: Path, out_dir: Path) -> int:
    """Jurnalul publicabil al unui clip (doar vehiculele, reunite) în out_dir; întoarce numărul de fișiere."""
    from romana.vision.recount import publish

    if Path(out_dir).resolve() == Path(traj_dir).resolve():
        raise SystemExit("Directorul de ieșire trebuie să fie altul decât jurnalul complet (care rămâne local).")
    files = sorted(Path(traj_dir).glob("*.jsonl.gz"))
    if not files:
        raise SystemExit(f"Nicio traiectorie în {traj_dir}.")
    for f in files:
        publish(f, Path(out_dir) / f.name)
    return len(files)


def clip_label(traj_dir: str) -> str:
    p = Path(traj_dir)
    return p.parent.name if p.name == "traiectorii" else p.name


def collect_pairs(clips: list[tuple[str, str]], cam: dict, mapping: dict, chunk_s: float = 30,
                  do_stitch: bool = True) -> dict:
    """Perechile (referință, automat, clip) pe țintă, pe bucățile adnotate ale fiecărui clip."""
    pairs = defaultdict(list)
    for traj_dir, ref_csv in clips:
        auto = count_by_chunk(Path(traj_dir), cam, chunk_s, do_stitch)
        for (tid, b), ref in load_reference(Path(ref_csv)).items():
            if tid not in mapping:
                continue
            a = sum(auto.get(k, {}).get("pe_bucati", {}).get(b, 0) for k in mapping[tid])
            pairs[tid].append((ref, a, clip_label(traj_dir)))
    return pairs


# ---------------------------------------------------------------- linia de comandă

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("foi", help="foile de contact pentru adnotare, pe ținte și bucăți")
    a.add_argument("tinte", help="TINTE.json")
    a.add_argument("clip")
    a.add_argument("--out", default=str(REF_DIR / "foi"))
    a.add_argument("--bucata", type=float, default=30, help="secunde pe bucată (implicit 30)")
    a.add_argument("--dt", type=float, default=0.5, help="secunde între imagini (implicit 0,5)")
    a.add_argument("--pe-foaie", type=int, default=12)
    a.add_argument("--coloane", type=int, default=3)
    a.add_argument("--latime-imagine", type=int, default=800)
    v = sub.add_parser("viziune", allow_abbrev=False,
                       help="lanțul live pe un clip salvat (argumentele în plus merg la run_vision)")
    v.add_argument("clip")
    v.add_argument("--out", default=None, help="implicit outputs/referinta/<numele clipului>")
    v.add_argument("--interval", type=int, default=30, help="intervalul de agregare al numărătorilor (s)")
    n = sub.add_parser("numara", help="numărătorile unui set de zone pe traiectoriile unui clip, pe bucăți")
    n.add_argument("traiectorii", help="directorul cu traiectorii_*.jsonl.gz al clipului")
    n.add_argument("--camera", default=str(CONFIG_DIR / "camera.json"), help="fișierul cu zonele (ca config/camera.json)")
    n.add_argument("--bucata", type=float, default=30)
    n.add_argument("--fara-reunire", action="store_true")
    n.add_argument("--min-cadre", type=int, default=3)
    n.add_argument("--json", default=None, help="salvează numărătorile în acest fișier")
    f = sub.add_parser("factori", help="factorii de corecție referință / automat, cu bootstrap pe bucăți")
    f.add_argument("--clip", nargs=2, action="append", required=True, metavar=("TRAIECTORII", "REFERINTA.csv"),
                   help="directorul de traiectorii al unui clip și referința lui (repetabil)")
    f.add_argument("--camera", default=str(CONFIG_DIR / "camera.json"))
    f.add_argument("--mapare", default=None, help="JSON {țintă: [chei automate]}; implicit cele 7 ținte din 26.10")
    f.add_argument("--bucata", type=float, default=30)
    f.add_argument("--fara-reunire", action="store_true")
    f.add_argument("--bootstrap", type=int, default=2000)
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--json", default=None, help="salvează factorii în acest fișier")
    pb = sub.add_parser("publica", help="jurnalul publicabil al unui clip: doar vehiculele, traiectorii reunite")
    pb.add_argument("traiectorii", help="directorul cu traiectorii_*.jsonl.gz al clipului (jurnalul complet, local)")
    pb.add_argument("out", help="directorul de ieșire, ex. docs/rezultate/referinta/clip1/traiectorii")
    args, extra = ap.parse_known_args(argv)
    if extra and args.cmd != "viziune":
        ap.error(f"argumente necunoscute: {extra}")

    if args.cmd == "foi":
        targets = json.loads(Path(args.tinte).read_text(encoding="utf-8-sig"))
        contact_sheets(targets, args.clip, Path(args.out), args.bucata, args.dt, args.pe_foaie, args.coloane,
                       args.latime_imagine)
    elif args.cmd == "viziune":
        run_offline(args.clip, Path(args.out) if args.out else REF_DIR / Path(args.clip).stem, args.interval, extra)
    elif args.cmd == "numara":
        res = count_by_chunk(Path(args.traiectorii), load_json(Path(args.camera).resolve()), args.bucata,
                             not args.fara_reunire, args.min_cadre)
        for k, val in res.items():
            print(f"{k:40s} {val['total']:5d}   {val['pe_bucati']}")
        if args.json:
            Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    elif args.cmd == "publica":
        n = publish_clip(Path(args.traiectorii), Path(args.out))
        print(f"[publicare] {n} fișiere → {args.out}")
    else:
        mapping = json.loads(Path(args.mapare).read_text(encoding="utf-8")) if args.mapare else MAPARE_IMPLICITA
        pairs = collect_pairs([tuple(c) for c in args.clip], load_json(Path(args.camera).resolve()), mapping,
                              args.bucata, not args.fara_reunire)
        res = correction_factors(pairs, args.bootstrap, args.seed)
        omise = [tid for tid, r in res.items() if r["factor"] is None]
        res = {tid: r for tid, r in res.items() if r["factor"] is not None}
        if omise:
            print(f"fără numărare automată (ținta lipsește din traiectorii, ex. pietonii din jurnalul publicat): "
                  f"{', '.join(omise)}")
        for tid, r in res.items():
            clips = ", ".join(f"{c} {d['procent_prins']}%" for c, d in r["pe_clipuri"].items())
            print(f"{tid:22s} bucăți {r['bucati']:2d}  ref {r['referinta']:6.1f}  auto {r['automat']:5d}  "
                  f"factor {r['factor']:.2f}  IC90 [{r['ic90'][0]:.2f}, {r['ic90'][1]:.2f}]  prins: {clips}")
        if args.json:
            Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
