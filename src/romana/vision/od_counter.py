"""Numărarea origine–destinație (intrare → ieșire) pe brațele Pieței Romane.

Fiecare vehicul urmărit (ID ByteTrack) trece prin zonele poligonale definite în
`config/camera.json`. Zonele sunt de trei tipuri:
  * `intrare` – banda pe care vehiculele se apropie de piață pe un braț;
  * `iesire`  – banda pe care vehiculele părăsesc piața pe un braț;
  * `trecere` – suprafața unei treceri de pietoni vizibile (doar pentru pietoni).

Clasificarea se face pe traiectoria întreagă, la închiderea ei (`classify`), aceeași funcție
fiind folosită live și la renumărarea din jurnalul de traiectorii (`vision/recount.py`):
  * originea = prima zonă de intrare vizitată înaintea oricărei ieșiri;
  * destinația = ultima zonă de ieșire a unui alt braț, vizitată după origine;
  * zonele de pe brațele îndepărtate, parțial ascunse (`capat_traiectorie`), contează doar
    dacă traiectoria **începe** acolo (intrare: vehiculul apare din strada ascunsă) sau
    **se termină** acolo (ieșire: vehiculul dispare în ea), cu o toleranță de `capat_s` secunde –
    altfel un vehicul care doar circulă pe inel prin dreptul străzii ar fi numărat greșit;
  * opțional, fiecare zonă cere un sens de mers în imagine (`sens`, ±60°), măsurat pe primele /
    ultimele `capat_s` secunde ale traiectoriei sau pe porțiunea din zonă;
  * zonele de intrare și de ieșire ale aceluiași braț sunt alăturate, deci întoarcerile pe
    același braț nu se pot distinge de atingerea benzii vecine și nu se numără (în cerere ele
    provin doar din distribuția a priori, ~3%).
O traiectorie completă produce o mișcare de viraj (origine → destinație); traiectoriile
fragmentate (ocluzii, vehicule pierdute) contribuie doar la numărătorile pe braț.
Un pieton este numărat o singură dată pe fiecare trecere pe care a fost văzut în cel puțin
`min_crossing_frames` cadre și pe care s-a deplasat cel puțin `min_crossing_move` (fracțiune
din lățimea cadrului) – cine doar așteaptă la bordură nu este numărat. Persoanele de pe
biciclete/motociclete sunt excluse înainte, în `run_vision`, ca să nu fie numărate de două ori.

Confidențialitate: nu se păstrează imagini. Jurnalul de traiectorii (opțional) conține doar
clasa obiectului și pozițiile punctului de contact cu solul, în coordonate normalizate, cu
timpul relativ – fără imagini, fără numere de înmatriculare, fără identificatori persistenți
(ID-ul de urmărire este temporar și nu se salvează).
"""
from __future__ import annotations

import csv
import gzip
import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

# Clase COCO → categorii SUMO
COCO_TO_VTYPE = {2: "passenger", 3: "motorcycle", 5: "bus", 7: "truck", 1: "bicycle"}
VEHICLE_CLASSES = list(COCO_TO_VTYPE)
PERSON = 0
PEDESTRIAN = "pieton"


@dataclass
class Zone:
    id: str
    arm: str
    role: str                    # "intrare" | "iesire" | "trecere"
    poly_norm: np.ndarray        # Nx2, coordonate normalizate [0..1]
    color: tuple = (0, 255, 0)
    capat: bool = False          # contează doar la începutul (intrare) / sfârșitul (ieșire) traiectoriei
    sens: tuple | None = None    # direcția de mers cerută în imagine (dx, dy); ±60°
    _poly_px: np.ndarray | None = None
    _size: tuple | None = None
    _poly_f: np.ndarray | None = None

    def poly_px(self, w: int, h: int) -> np.ndarray:
        if self._size != (w, h):
            self._poly_px = (self.poly_norm * np.array([w, h])).astype(np.int32)
            self._size = (w, h)
        return self._poly_px

    def contains(self, x: float, y: float, w: int, h: int) -> bool:
        return cv2.pointPolygonTest(self.poly_px(w, h), (float(x), float(y)), False) >= 0

    def contains_norm(self, x: float, y: float) -> bool:
        if self._poly_f is None:
            self._poly_f = self.poly_norm.astype(np.float32)
        return cv2.pointPolygonTest(self._poly_f, (float(x), float(y)), False) >= 0


def is_rider(person_box, vehicle_boxes, margin: float = 0.25) -> bool:
    """Persoană pe bicicletă/motocicletă (sau în dreptul unui vehicul): punctul ei de contact
    cu solul cade în caseta vehiculului, lărgită cu `margin` din dimensiunile acesteia."""
    px, py = (person_box[0] + person_box[2]) / 2, person_box[3]
    for x1, y1, x2, y2 in vehicle_boxes:
        mw, mh = (x2 - x1) * margin, (y2 - y1) * margin
        if x1 - mw <= px <= x2 + mw and y1 <= py <= y2 + mh:
            return True
    return False


def load_zones(cam_cfg: dict) -> list[Zone]:
    zones = []
    for z in cam_cfg["zones"]:
        zones.append(Zone(z["id"], z["arm"], z["rol"], np.array(z["poligon"], dtype=float),
                          tuple(z.get("culoare", (0, 255, 0))), bool(z.get("capat_traiectorie", False)),
                          tuple(z["sens"]) if z.get("sens") else None))
    return zones


def _heading_ok(pts: list, t0: float, t1: float, sens, aspect: float, min_len: float = 0.004) -> bool:
    """Deplasarea între momentele t0 și t1 are direcția `sens` (±60°). Fără `sens` sau fără
    deplasare măsurabilă (vehicul oprit), condiția se consideră îndeplinită."""
    if sens is None:
        return True
    seg = [(x, y * aspect) for t, x, y in pts if t0 - 1e-6 <= t <= t1 + 1e-6]
    if len(seg) < 2:
        return True
    v = np.subtract(seg[-1], seg[0])
    n = np.hypot(*v)
    if n < min_len:
        return True
    s = np.array([sens[0], sens[1] * aspect])
    return float(np.dot(v, s) / (n * np.hypot(*s))) >= 0.5


@dataclass
class Params:
    min_track_frames: int = 3
    min_crossing_frames: int = 2
    min_crossing_move: float = 0.04     # fracțiune din lățimea cadrului
    capat_s: float = 1.5                # toleranța pentru zonele `capat_traiectorie`
    aspect: float = 1850 / 3288         # înălțime / lățime cadru (distanțe comparabile pe cele două axe)
    # ieșirile pe brațele îndepărtate (`capat_traiectorie`): vehiculele mici se pierd oriunde pe inelul din fundal,
    # deci „a dispărut în zona ieșirii” nu ajunge – se cer și cadre în zonă și o deplasare în sensul străzii
    capat_min_cadre: int = 0
    capat_min_deplasare: float = 0.0    # fracțiune din lățimea cadrului, proiectată pe sensul zonei
    capat_min_fractie: float = 0.0      # fracțiune din lungimea zonei în sensul străzii (independentă de perspectivă)


def classify(vtype: str, pts: list, zones: list[Zone], p: Params) -> dict:
    """Clasificarea unei traiectorii închise.

    pts: [(t, x, y), ...] cu x, y normalizate la cadru și t în secunde, în ordine cronologică.
    Întoarce {"origine", "destinatie"} pentru vehicule sau {"treceri": [(braț, trecere), ...]}
    pentru pietoni."""
    if vtype == PEDESTRIAN:
        out = []
        for z in zones:
            if z.role != "trecere":
                continue
            inside = [(x, y * p.aspect) for _, x, y in pts if z.contains_norm(x, y)]
            if len(inside) >= p.min_crossing_frames:
                (x0, y0), (x1, y1) = inside[0], inside[-1]
                if ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 >= p.min_crossing_move:
                    out.append((z.arm, z.id))
        return {"treceri": out}
    t_first, t_last = pts[0][0], pts[-1][0]
    first, last = {}, {}                       # zonă -> primul / ultimul moment în zonă
    for t, x, y in pts:
        for z in zones:
            if z.role != "trecere" and z.contains_norm(x, y):
                first.setdefault(z.id, t)
                last[z.id] = t
    by_id = {z.id: z for z in zones}
    exits_first = [first[i] for i in first if by_id[i].role == "iesire"]
    origin, t_origin = None, None
    for zid in sorted((i for i in first if by_id[i].role == "intrare"), key=lambda i: first[i]):
        z = by_id[zid]
        if exits_first and min(exits_first) < first[zid]:
            break                              # a atins întâi o ieșire: vehicul care părăsește piața
        if z.capat and first[zid] - t_first > p.capat_s:
            continue                           # nu a apărut din strada ascunsă, doar a trecut prin dreptul ei
        w0, w1 = (t_first, t_first + p.capat_s) if z.capat else (first[zid], max(last[zid], first[zid] + 1.0))
        if not _heading_ok(pts, w0, w1, z.sens, p.aspect):
            continue                           # se mișcă în alt sens decât intrările pe acest braț
        origin, t_origin = z.arm, first[zid]
        break
    dest = None
    for zid in sorted((i for i in last if by_id[i].role == "iesire"), key=lambda i: -last[i]):
        z = by_id[zid]
        if z.arm == origin or (t_origin is not None and last[zid] < t_origin):
            continue
        if z.capat and t_last - last[zid] > p.capat_s:
            continue                           # nu a dispărut în strada ascunsă, a continuat pe inel
        if z.capat and (p.capat_min_cadre or p.capat_min_deplasare or p.capat_min_fractie):
            inside = [(x, y * p.aspect) for _, x, y in pts if z.contains_norm(x, y)]
            if len(inside) < max(p.capat_min_cadre, 1):
                continue                       # prea puțin văzut în zonă: probabil pierdut de detector, nu ieșit
            if (p.capat_min_deplasare or p.capat_min_fractie) and z.sens:
                sx, sy = z.sens[0], z.sens[1] * p.aspect
                n = (sx * sx + sy * sy) ** 0.5
                dx, dy = inside[-1][0] - inside[0][0], inside[-1][1] - inside[0][1]
                avans = (dx * sx + dy * sy) / n
                proiectii = [(x * sx + y * p.aspect * sy) / n for x, y in z.poly_norm]
                lungime = max(proiectii) - min(proiectii)
                if avans < p.capat_min_deplasare or avans < p.capat_min_fractie * lungime:
                    continue                   # nu a înaintat pe stradă

        w0, w1 = (t_last - p.capat_s, t_last) if z.capat else (min(first[zid], last[zid] - 1.0), last[zid])
        if not _heading_ok(pts, w0, w1, z.sens, p.aspect):
            continue
        dest = z.arm
        break
    return {"origine": origin, "destinatie": dest}


@dataclass
class TrackState:
    vtype: str
    first_seen: float
    last_seen: float
    last_frame: int
    cls_votes: Counter = field(default_factory=Counter)
    pts: list = field(default_factory=list)          # (t, x_norm, y_norm)
    origin: str | None = None                        # provizorii, pentru afișare
    destination: str | None = None


class ODCounter:
    """Agregă mișcările pe intervale fixe (implicit 15 minute)."""

    def __init__(self, zones: list[Zone], interval_s: int = 900, lost_after_frames: int = 30,
                 min_track_frames: int = 3, out_dir: Path | None = None, clock=time.time,
                 min_crossing_frames: int = 2, min_crossing_move: float = 0.04, capat_s: float = 1.5,
                 traj_dir: Path | None = None):
        self.zones = zones
        self.p = Params(min_track_frames, min_crossing_frames, min_crossing_move, capat_s)
        self.interval_s = interval_s
        self.lost_after = lost_after_frames
        self.out_dir = out_dir
        self.traj_dir = traj_dir
        self.clock = clock
        self.tracks: dict[int, TrackState] = {}
        self.frame_idx = 0
        self._start_interval(clock())
        self.history: list[dict] = []           # intervale închise (pentru dashboard)
        self.totals = Counter()                  # de la pornire

    # ------------------------------------------------------------ intervale
    def _start_interval(self, now: float) -> None:
        self.interval_start = now - (now % self.interval_s) if self.interval_s >= 60 else now
        self.od = Counter()          # (origine, destinatie, vtype) -> n
        self.arm_in = Counter()      # (brat, vtype) -> n   (inclusiv traiectorii incomplete)
        self.arm_out = Counter()
        self.peds = Counter()        # (brat, trecere) -> pietoni

    def _close_interval(self, now: float) -> dict:
        rec = {"start": self.interval_start, "end": min(self.interval_start + self.interval_s, now),
               "od": dict(self.od), "in": dict(self.arm_in), "out": dict(self.arm_out),
               "pietoni": dict(self.peds)}
        self.history.append(rec)
        self.history = self.history[-96:]
        if self.out_dir is not None:
            write_csv(rec, self.out_dir)
        self._start_interval(now)
        return rec

    # ------------------------------------------------------------ actualizare
    def update(self, detections, w: int, h: int, now: float | None = None) -> list[dict]:
        """detections: iterabil de (track_id, coco_cls, x_center, y_bottom). Returnează evenimente închise.

        Persoanele (clasa COCO 0) trebuie să fie deja filtrate de călători/bicicliști/motocicliști."""
        now = self.clock() if now is None else now
        self.frame_idx += 1
        events = []
        for tid, cls, x, y in detections:
            vt = PEDESTRIAN if int(cls) == PERSON else COCO_TO_VTYPE.get(int(cls))
            if vt is None:
                continue
            st = self.tracks.get(tid)
            if st is None:
                st = self.tracks[tid] = TrackState(vt, now, now, self.frame_idx)
            st.last_seen, st.last_frame = now, self.frame_idx
            st.cls_votes[vt] += 1
            st.pts.append((float(now), float(x) / w, float(y) / h))
            if vt != PEDESTRIAN:                 # etichetă provizorie pentru suprapunerea video
                for z in self.zones:
                    if z.role == "intrare" and st.origin is None and z.contains(x, y, w, h):
                        st.origin = z.arm
                    elif z.role == "iesire" and z.arm != st.origin and z.contains(x, y, w, h):
                        st.destination = z.arm
        # închiderea traiectoriilor pierdute
        for tid in [t for t, s in self.tracks.items() if self.frame_idx - s.last_frame > self.lost_after]:
            ev = self._finalize(self.tracks.pop(tid))
            if ev:
                events.append(ev)
        if now - self.interval_start >= self.interval_s:
            self._close_interval(now)
        return events

    def _finalize(self, st: TrackState) -> dict | None:
        if len(st.pts) < self.p.min_track_frames:
            return None
        vt = st.cls_votes.most_common(1)[0][0]
        if self.traj_dir is not None:
            log_trajectory(self.traj_dir, vt, st.pts)
        return self.add(vt, classify(vt, st.pts, self.zones, self.p))

    def add(self, vt: str, res: dict) -> dict | None:
        """Adaugă rezultatul clasificării unei traiectorii la intervalul curent."""
        if vt == PEDESTRIAN:
            for key in res["treceri"]:
                self.peds[key] += 1
                self.totals[("pietoni", key[0])] += 1
            return None
        o, d = res["origine"], res["destinatie"]
        if o:
            self.arm_in[(o, vt)] += 1
            self.totals[("in", o)] += 1
        if d:
            self.arm_out[(d, vt)] += 1
            self.totals[("out", d)] += 1
        if o and d:
            self.od[(o, d, vt)] += 1
            self.totals[("od", o, d)] += 1
            return {"origine": o, "destinatie": d, "vehicul": vt}
        return None

    def flush(self) -> dict:
        for tid in list(self.tracks):
            self._finalize(self.tracks.pop(tid))
        return self._close_interval(self.clock())

    # ------------------------------------------------------------ rezumate
    def current_rates(self) -> dict:
        """Debite estimate (veh/h) pe brațe în intervalul curent."""
        el = max(1.0, self.clock() - self.interval_start)
        ins, outs = defaultdict(int), defaultdict(int)
        for (a, _), n in self.arm_in.items():
            ins[a] += n
        for (a, _), n in self.arm_out.items():
            outs[a] += n
        peds = defaultdict(int)
        for (a, _), n in self.peds.items():
            peds[a] += n
        return {"intrari_veh_h": {a: round(n * 3600 / el) for a, n in ins.items()},
                "iesiri_veh_h": {a: round(n * 3600 / el) for a, n in outs.items()},
                "pietoni_h": {a: round(n * 3600 / el) for a, n in peds.items()},
                "secunde_interval": round(el)}


def write_csv(rec: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    day = time.strftime("%Y-%m-%d", time.localtime(rec["start"]))
    path = out_dir / f"numaratori_{day}.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["inceput", "sfarsit", "tip", "origine", "destinatie", "vehicul", "numar"])
        s = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rec["start"]))
        e = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rec["end"]))
        for (o, d, v), n in sorted(rec["od"].items()):
            w.writerow([s, e, "viraj", o, d, v, n])
        for (a, v), n in sorted(rec["in"].items()):
            w.writerow([s, e, "intrare", a, "", v, n])
        for (a, v), n in sorted(rec["out"].items()):
            w.writerow([s, e, "iesire", "", a, v, n])
        for (a, zid), n in sorted(rec.get("pietoni", {}).items()):
            w.writerow([s, e, "pietoni", a, zid, PEDESTRIAN, n])


def log_trajectory(traj_dir: Path, vtype: str, pts: list) -> None:
    """Jurnal anonim: clasa + punctele de contact cu solul (normalizate) + timpul relativ."""
    traj_dir.mkdir(parents=True, exist_ok=True)
    t0 = pts[0][0]
    day = time.strftime("%Y-%m-%d", time.localtime(t0))
    rec = {"t0": round(t0, 2), "tip": vtype,
           "p": [[round(t - t0, 2), round(x, 4), round(y, 4)] for t, x, y in pts]}
    with gzip.open(traj_dir / f"traiectorii_{day}.jsonl.gz", "at", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")
