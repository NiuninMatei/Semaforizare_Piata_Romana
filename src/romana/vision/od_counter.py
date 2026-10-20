"""Numărarea origine–destinație (intrare → ieșire) pe brațele Pieței Romane.

Fiecare vehicul urmărit (ID ByteTrack) trece prin zonele poligonale definite în
`config/camera.json`. Zonele sunt de două tipuri:
  * `intrare` – banda pe care vehiculele se apropie de piață pe un braț;
  * `iesire`  – banda pe care vehiculele părăsesc piața pe un braț.
  * `trecere` – suprafața unei treceri de pietoni vizibile (doar pentru pietoni).
Prima zonă de intrare vizitată = brațul de origine; ultima zonă de ieșire = destinația.
O traiectorie completă produce o mișcare de viraj (origine → destinație); traiectoriile
fragmentate (ocluzii, vehicule pierdute) contribuie doar la numărătorile pe braț.
Un pieton este numărat o singură dată pe fiecare trecere pe care a fost văzut în cel puțin
`min_crossing_frames` cadre (persoanele de pe biciclete/motociclete sunt excluse înainte,
în `run_vision`, ca să nu fie numărate de două ori).

Nu se păstrează imagini sau identificatori persistenți: ID-urile de urmărire sunt
temporare și sunt uitate după închiderea traiectoriei (GDPR – minimizarea datelor).
"""
from __future__ import annotations

import csv
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
    _poly_px: np.ndarray | None = None
    _size: tuple | None = None

    def poly_px(self, w: int, h: int) -> np.ndarray:
        if self._size != (w, h):
            self._poly_px = (self.poly_norm * np.array([w, h])).astype(np.int32)
            self._size = (w, h)
        return self._poly_px

    def contains(self, x: float, y: float, w: int, h: int) -> bool:
        return cv2.pointPolygonTest(self.poly_px(w, h), (float(x), float(y)), False) >= 0


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
                          tuple(z.get("culoare", (0, 255, 0)))))
    return zones


@dataclass
class TrackState:
    vtype: str
    first_seen: float
    last_seen: float
    last_frame: int
    origin: str | None = None
    destination: str | None = None
    zones_seen: list = field(default_factory=list)
    cls_votes: Counter = field(default_factory=Counter)
    last_point: tuple | None = None
    crossing_frames: Counter = field(default_factory=Counter)   # trecere -> cadre (pietoni)


class ODCounter:
    """Agregă mișcările pe intervale fixe (implicit 15 minute)."""

    def __init__(self, zones: list[Zone], interval_s: int = 900, lost_after_frames: int = 30,
                 min_track_frames: int = 3, out_dir: Path | None = None, clock=time.time,
                 min_crossing_frames: int = 2):
        self.zones = zones
        self.vehicle_zones = [z for z in zones if z.role != "trecere"]
        self.crossing_zones = [z for z in zones if z.role == "trecere"]
        self.min_crossing = min_crossing_frames
        self.interval_s = interval_s
        self.lost_after = lost_after_frames
        self.min_frames = min_track_frames
        self.out_dir = out_dir
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
            self._write_csv(rec)
        self._start_interval(now)
        return rec

    def _write_csv(self, rec: dict) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        day = time.strftime("%Y-%m-%d", time.localtime(rec["start"]))
        path = self.out_dir / f"numaratori_{day}.csv"
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
            st.last_point = (x, y)
            if vt == PEDESTRIAN:
                for z in self.crossing_zones:
                    if z.contains(x, y, w, h):
                        st.crossing_frames[(z.arm, z.id)] += 1
                continue
            for z in self.vehicle_zones:
                if z.contains(x, y, w, h):
                    if not st.zones_seen or st.zones_seen[-1] != z.id:
                        st.zones_seen.append(z.id)
                    if z.role == "intrare" and st.origin is None:
                        st.origin = z.arm
                    elif z.role == "iesire":
                        st.destination = z.arm  # ultima zonă de ieșire vizitată
        # închiderea traiectoriilor pierdute
        for tid in [t for t, s in self.tracks.items() if self.frame_idx - s.last_frame > self.lost_after]:
            ev = self._finalize(self.tracks.pop(tid))
            if ev:
                events.append(ev)
        if now - self.interval_start >= self.interval_s:
            self._close_interval(now)
        return events

    def _finalize(self, st: TrackState) -> dict | None:
        if sum(st.cls_votes.values()) < self.min_frames:
            return None
        vt = st.cls_votes.most_common(1)[0][0]
        if vt == PEDESTRIAN:
            for key, n in st.crossing_frames.items():
                if n >= self.min_crossing:
                    self.peds[key] += 1
                    self.totals[("pietoni", key[0])] += 1
            return None
        if st.origin:
            self.arm_in[(st.origin, vt)] += 1
            self.totals[("in", st.origin)] += 1
        if st.destination:
            self.arm_out[(st.destination, vt)] += 1
            self.totals[("out", st.destination)] += 1
        if st.origin and st.destination:
            self.od[(st.origin, st.destination, vt)] += 1
            self.totals[("od", st.origin, st.destination)] += 1
            return {"origine": st.origin, "destinatie": st.destination, "vehicul": vt}
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
