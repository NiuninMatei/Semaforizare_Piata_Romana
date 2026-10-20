"""Borna 2 – Preluarea în timp real a datelor de trafic de pe camera Piața Romană.

Lanț de procesare:  HLS (.m3u8) → YOLO11 (detecție) → ByteTrack (urmărire) →
zone de intrare/ieșire pe brațe → matrice origine–destinație pe intervale →
  * CSV agregat în data/counts/ (intrare pentru calibrarea SUMO),
  * stare live în outputs/live/state.json (dashboard + geamănul digital SUMO),
  * opțional MQTT (topic romana/...) pentru arhitectura IoT.

Exemple:
  python -m romana.vision.run_vision --show
  python -m romana.vision.run_vision --minutes 15 --interval 300
  python -m romana.vision.run_vision --source inregistrare.mp4 --show

Confidențialitate: cadrele sunt procesate doar în memorie; nu se salvează video.
Previzualizarea pentru dashboard este redusă la 960 px, cu persoanele estompate,
și este suprascrisă continuu (nu se arhivează).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from romana.common import COUNTS_DIR, OUTPUT_DIR, load_json
from romana.vision.od_counter import VEHICLE_CLASSES, ODCounter, load_zones
from romana.vision.stream import FrameSource

LIVE_DIR = OUTPUT_DIR / "live"
PERSON = 0


def draw_overlay(frame, zones, dets, counter: ODCounter, fps: float) -> np.ndarray:
    h, w = frame.shape[:2]
    over = frame.copy()
    for z in zones:
        cv2.fillPoly(over, [z.poly_px(w, h)], z.color)
    frame = cv2.addWeighted(over, 0.25, frame, 0.75, 0)
    for z in zones:
        p = z.poly_px(w, h)
        cv2.polylines(frame, [p], True, z.color, 3)
        cx, cy = p.mean(axis=0).astype(int)
        cv2.putText(frame, z.id, (cx - 60, cy), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
    for tid, cls, box in dets:
        x1, y1, x2, y2 = map(int, box)
        st = counter.tracks.get(tid)
        lbl = f"{tid}"
        if st and st.origin:
            lbl += f" {st.origin[:3]}>{(st.destination or '?')[:3]}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(frame, lbl, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    rates = counter.current_rates()
    y = 60
    cv2.rectangle(frame, (20, 20), (900, 90 + 40 * len(rates["intrari_veh_h"])), (0, 0, 0), -1)
    cv2.putText(frame, f"Piata Romana - debite intrare (veh/h)  {fps:.1f} fps", (35, y),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    for a, v in sorted(rates["intrari_veh_h"].items()):
        y += 40
        cv2.putText(frame, f"{a:<18} {v:>5}", (35, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    return frame


def blur_persons(frame, person_boxes):
    for x1, y1, x2, y2 in person_boxes:
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        roi = frame[y1:int(y2), x1:int(x2)]
        if roi.size:
            frame[y1:int(y2), x1:int(x2)] = cv2.GaussianBlur(roi, (31, 31), 0)
    return frame


class MqttOut:
    def __init__(self, host: str, port: int = 1883, base: str = "romana"):
        import paho.mqtt.client as mqtt

        self.base = base
        self.cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="romana-camera-edge")
        self.cli.connect(host, port, keepalive=30)
        self.cli.loop_start()

    def publish(self, topic: str, payload: dict, retain: bool = False) -> None:
        self.cli.publish(f"{self.base}/{topic}", json.dumps(payload, ensure_ascii=False), qos=1, retain=retain)


def main(argv=None) -> None:
    cam = load_json("camera.json")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=cam["stream_url"], help="URL HLS sau fișier video")
    ap.add_argument("--model", default=cam.get("model", "yolo11s.pt"))
    ap.add_argument("--imgsz", type=int, default=cam.get("imgsz", 1600))
    ap.add_argument("--conf", type=float, default=cam.get("conf", 0.25))
    ap.add_argument("--device", default=None, help="'cpu', '0' (GPU NVIDIA) etc.; implicit automat")
    ap.add_argument("--fps", type=float, default=cam.get("fps", 6.0), help="cadre analizate pe secundă")
    ap.add_argument("--interval", type=int, default=cam.get("interval_s", 900), help="secunde / interval de agregare")
    ap.add_argument("--minutes", type=float, default=0, help="durata rulării (0 = continuu)")
    ap.add_argument("--show", action="store_true", help="fereastră OpenCV cu suprapunerea zonelor")
    ap.add_argument("--mqtt", default=None, help="gazdă broker MQTT (ex. localhost)")
    ap.add_argument("--out", default=str(COUNTS_DIR))
    args = ap.parse_args(argv)

    from ultralytics import YOLO

    model = YOLO(args.model)
    zones = load_zones(cam)
    src = FrameSource(args.source, target_fps=args.fps)
    lost_frames = int(cam.get("lost_after_s", 5) * args.fps)
    # pentru fișiere video se folosește timpul din fișier, decalat față de momentul pornirii
    t0 = time.time()
    sim_time = [t0]
    clock = time.time if src.is_live else (lambda: sim_time[0])
    counter = ODCounter(zones, interval_s=args.interval, lost_after_frames=lost_frames,
                        out_dir=Path(args.out), clock=clock)
    mqtt = MqttOut(args.mqtt) if args.mqtt else None
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    roi = cam.get("roi_y", [0.0, 1.0])
    t_end = time.time() + args.minutes * 60 if args.minutes else None
    t_prev, fps_est, last_live = time.time(), 0.0, 0.0
    n_closed = len(counter.history)
    print(f"[viziune] sursa={args.source}  model={args.model}  imgsz={args.imgsz}  interval={args.interval}s")
    try:
        for ts, frame in src.frames():
            if not src.is_live:
                sim_time[0] = t0 + ts
            h, w = frame.shape[:2]
            y0, y1 = int(roi[0] * h), int(roi[1] * h)
            crop = frame[y0:y1]
            res = model.track(crop, imgsz=args.imgsz, conf=args.conf, classes=VEHICLE_CLASSES + [PERSON],
                              persist=True, tracker=cam.get("tracker", "bytetrack.yaml"),
                              device=args.device, verbose=False)[0]
            dets, persons, feed = [], [], []
            if res.boxes is not None and len(res.boxes):
                xyxy = res.boxes.xyxy.cpu().numpy()
                xyxy[:, [1, 3]] += y0
                cls = res.boxes.cls.cpu().numpy().astype(int)
                ids = res.boxes.id.cpu().numpy().astype(int) if res.boxes.id is not None else [None] * len(cls)
                for b, c, i in zip(xyxy, cls, ids):
                    if c == PERSON:
                        persons.append(b)
                    elif i is not None:
                        dets.append((int(i), int(c), b))
                        feed.append((int(i), int(c), (b[0] + b[2]) / 2, b[3]))  # punctul de contact cu solul
            events = counter.update(feed, w, h)
            now = time.time()
            fps_est = 0.9 * fps_est + 0.1 / max(1e-3, now - t_prev)
            t_prev = now
            if mqtt:
                for ev in events:
                    mqtt.publish("evenimente/viraj", ev)
            if len(counter.history) > n_closed:
                n_closed = len(counter.history)
                rec = counter.history[-1]
                print(f"[interval închis] {time.strftime('%H:%M', time.localtime(rec['start']))}: "
                      f"{sum(rec['od'].values())} viraje complete, {sum(rec['in'].values())} intrări")
                if mqtt:
                    mqtt.publish("numaratori/interval", {k: {str(kk): vv for kk, vv in v.items()}
                                                         if isinstance(v, dict) else v for k, v in rec.items()},
                                 retain=True)
            if now - last_live > 1.0 or args.show:
                vis = draw_overlay(blur_persons(frame.copy(), persons), zones, dets, counter, fps_est)
                if now - last_live > 1.0:
                    last_live = now
                    small = cv2.resize(vis, (960, int(960 * h / w)))
                    cv2.imwrite(str(LIVE_DIR / "frame_tmp.jpg"), small, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    Path(LIVE_DIR / "frame_tmp.jpg").replace(LIVE_DIR / "frame.jpg")
                    state = {"timestamp": now, "fps": round(fps_est, 2), "conectat": src.connected or not src.is_live,
                             "reconectari": src.reconnects, "vehicule_urmarite": len(counter.tracks),
                             **counter.current_rates(),
                             "total_viraje": {f"{k[1]}>{k[2]}": v for k, v in counter.totals.items() if k[0] == "od"},
                             "ultimul_interval": ({"start": counter.history[-1]["start"],
                                                   "od": {f"{o}>{d}>{v}": n for (o, d, v), n in counter.history[-1]["od"].items()}}
                                                  if counter.history else None)}
                    (LIVE_DIR / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
                    if mqtt:
                        mqtt.publish("stare/camera", state, retain=True)
                if args.show:
                    cv2.imshow("Piata Romana - viziune artificiala (q = iesire)", cv2.resize(vis, (1644, 925)))
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
            if t_end and time.time() > t_end:
                break
    except KeyboardInterrupt:
        pass
    finally:
        rec = counter.flush()
        print(f"[final] ultimul interval: {sum(rec['od'].values())} viraje, {sum(rec['in'].values())} intrări; "
              f"CSV în {args.out}")
        src.close()
        if args.show:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
