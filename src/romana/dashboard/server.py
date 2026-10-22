"""Dashboard-ul operatorului (Borna 5) – server web local Flask.

Afișează în timp real: imaginea camerei cu zonele și vehiculele detectate (persoane estompate),
debitele pe brațe, starea semaforului din geamănul digital SUMO, cozile și istoricul lor,
și permite schimbarea modului de control (AI / plan fix / Max-Pressure / manual) cu confirmare.

Rulare:  python -m romana.dashboard.server     → http://localhost:8050
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

from romana.common import OUTPUT_DIR

LIVE = OUTPUT_DIR / "live"
STATIC = Path(__file__).parent / "static"
app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")
MODES = {"ai", "fix", "max_pressure", "manual"}


def _read(name: str):
    p = LIVE / name
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        d["_varsta_s"] = round(time.time() - p.stat().st_mtime, 1)
        return d
    except (OSError, json.JSONDecodeError):
        return None


@app.get("/")
def index():
    return send_file(STATIC / "index.html")


@app.get("/api/state")
def state():
    return jsonify({"camera": _read("state.json"), "simulare": _read("sim_state.json"),
                    "comanda": _read("command.json"), "ora_server": time.time()})


@app.get("/api/frame.jpg")
def frame():
    p = LIVE / "frame.jpg"
    if not p.exists():
        abort(404)
    resp = send_file(p, mimetype="image/jpeg", max_age=0)
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/api/video")
def video():
    """Flux MJPEG: fiecare cadru nou analizat de modulul de viziune este trimis imediat (~6 cadre/s)."""
    def gen():
        p, last = LIVE / "frame.jpg", 0.0
        while True:
            try:
                m = p.stat().st_mtime
                if m != last:
                    data = p.read_bytes()
                    last = m
                    yield b"--cadru\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
            except OSError:          # fișierul tocmai este înlocuit: încercăm din nou
                pass
            time.sleep(0.04)
    resp = app.response_class(gen(), mimetype="multipart/x-mixed-replace; boundary=cadru")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.post("/api/command")
def command():
    body = request.get_json(force=True, silent=True) or {}
    mode = body.get("mod")
    if mode not in MODES:
        return jsonify({"eroare": "mod necunoscut"}), 400
    cmd = {"mod": mode, "timestamp": time.time()}
    if mode == "manual":
        try:
            cmd["faza"] = int(body.get("faza", 0))
        except (TypeError, ValueError):
            return jsonify({"eroare": "fază invalidă"}), 400
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / "command.json").write_text(json.dumps(cmd), encoding="utf-8")
    return jsonify({"ok": True, **cmd})


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8050)
    args = ap.parse_args()
    print(f"Dashboard: http://localhost:{args.port}")
    app.run(host="127.0.0.1", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
