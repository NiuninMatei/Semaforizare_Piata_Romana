"""Unealtă interactivă pentru (re)desenarea zonelor de intrare/ieșire pe imaginea camerei.

Necesară dacă operatorul Webcam România mișcă sau schimbă camera. Se preia un cadru
live, iar pentru fiecare zonă din config/camera.json se desenează un poligon nou.

Comenzi în fereastră:
  clic stânga  – adaugă un vârf          clic dreapta – șterge ultimul vârf
  ENTER/SPACE  – confirmă zona curentă    s – păstrează zona veche și trece mai departe
  ESC          – renunță fără salvare

Rulare:  python -m romana.vision.calibrate_zones [--source fisier.jpg|URL]
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from romana.common import CONFIG_DIR, load_json, save_json
from romana.vision.stream import FrameSource

DISPLAY_W = 1600


def main(argv=None) -> None:
    cam = load_json("camera.json")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=cam["stream_url"])
    args = ap.parse_args(argv)

    if args.source.lower().endswith((".jpg", ".png")):
        frame = cv2.imread(args.source)
    else:
        src = FrameSource(args.source)
        frame = src.snapshot()
        src.close()
    if frame is None:
        raise SystemExit("Nu am putut obține un cadru de la cameră.")
    h, w = frame.shape[:2]
    scale = DISPLAY_W / w
    base = cv2.resize(frame, (DISPLAY_W, int(h * scale)))
    pts: list[tuple[int, int]] = []

    def on_mouse(ev, x, y, *_):
        if ev == cv2.EVENT_LBUTTONDOWN:
            pts.append((x, y))
        elif ev == cv2.EVENT_RBUTTONDOWN and pts:
            pts.pop()

    win = "Calibrare zone - Piata Romana"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)
    new_zones = []
    for z in cam["zones"]:
        pts.clear()
        old = (np.array(z["poligon"]) * [DISPLAY_W, base.shape[0]]).astype(np.int32)
        while True:
            img = base.copy()
            for done in new_zones:
                p = (np.array(done["poligon"]) * [DISPLAY_W, base.shape[0]]).astype(np.int32)
                cv2.polylines(img, [p], True, (120, 120, 120), 1)
            cv2.polylines(img, [old], True, (0, 0, 255), 1)
            if pts:
                cv2.polylines(img, [np.array(pts)], len(pts) > 2, tuple(z.get("culoare", (0, 255, 0))), 2)
            cv2.putText(img, f"Zona: {z['id']} ({z['rol']} {z['arm']}) - ENTER confirma, s pastreaza vechea",
                        (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow(win, img)
            k = cv2.waitKey(20) & 0xFF
            if k == 27:
                cv2.destroyAllWindows()
                print("Renunțat – nu s-a salvat nimic.")
                return
            if k == ord("s"):
                new_zones.append(z)
                break
            if k in (13, 32) and len(pts) >= 3:
                poly = [[round(x / DISPLAY_W, 4), round(y / base.shape[0], 4)] for x, y in pts]
                new_zones.append({**z, "poligon": poly})
                break
    cv2.destroyAllWindows()
    cam["zones"] = new_zones
    cam["referinta_cadru"] = [w, h]
    save_json(cam, CONFIG_DIR / "camera.json")
    print("Zonele au fost salvate în config/camera.json")


if __name__ == "__main__":
    main()
