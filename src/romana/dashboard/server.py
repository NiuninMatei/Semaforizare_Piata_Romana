"""Dashboard-ul operatorului (Borna 5) – server web local Flask.

Afișează în timp real: imaginea camerei cu zonele și vehiculele detectate (persoane estompate),
debitele pe brațe, starea semaforului din geamănul digital SUMO, cozile și istoricul lor,
și permite schimbarea modului de control (AI / plan fix / Max-Pressure / manual) cu confirmare.

Rulare:  python -m romana.dashboard.server     → http://localhost:8050
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

from romana.common import OUTPUT_DIR
from romana.dashboard import senzor

LIVE = OUTPUT_DIR / "live"
# ce citește /api/senzor, pe lângă LIVE; variabile ale modulului, ca testele să le poată înlocui
LOGURI, NUMARATORI, LANTURI, FISE = senzor.LOGURI, senzor.NUMARATORI, senzor.LANTURI, senzor.FISE
STATIC = Path(__file__).parent / "static"
app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")
MODES = {"ai", "fix", "max_pressure", "manual", "program"}


def _read(name: str):
    """Un obiect JSON din outputs/live, cu vârsta fișierului; None dacă lipsește, nu se poate citi sau nu e un obiect."""
    p = LIVE / name
    try:
        d = json.loads(p.read_bytes())       # din octeți, json recunoaște singur UTF-8, UTF-8 cu BOM, UTF-16 și UTF-32
        if not isinstance(d, dict):          # o listă sau null în command.json ar fi dat HTTP 500
            return None
        d["_varsta_s"] = round(time.time() - p.stat().st_mtime, 1)
        return d
    except (OSError, ValueError):            # ValueError cuprinde și JSONDecodeError, și UnicodeDecodeError
        return None


@app.get("/")
def index():
    return send_file(STATIC / "index.html")


def _ultimele_comenzi(n: int = 5) -> list[dict]:
    """Ultimele comenzi din jurnal, cea mai nouă la urmă; o linie stricată se sare."""
    p = LIVE / "comenzi.jsonl"
    try:
        linii = p.read_text(encoding="utf-8").splitlines()[-n:]
    except OSError:
        return []
    out = []
    for linie in linii:
        try:
            out.append(json.loads(linie))
        except json.JSONDecodeError:
            pass
    return out


@app.get("/api/state")
def state():
    return jsonify({"camera": _read("state.json"), "simulare": _read("sim_state.json"),
                    "comanda": _read("command.json"), "comenzi": _ultimele_comenzi(), "ora_server": time.time()})


_senzor_lacat = threading.Lock()       # Flask servește cererile în fire paralele: starea se calculează o singură dată
_senzor_memorat: dict | None = None


@app.get("/api/senzor")
def starea_senzorului():
    """Starea senzorului, pentru panoul din pagină: doar citire, refăcută cel mult o dată la senzor.MEMORARE_S s, oricâte
    pagini o cer; între timp se dă aceeași, doar cu `ora_server` de acum. Mereu HTTP 200: o verigă care nu se poate citi
    are starea „necunoscut”."""
    global _senzor_memorat
    with _senzor_lacat:
        acum = time.time()
        m = _senzor_memorat
        if m is None or not 0 <= acum - m["calculat_la"] < senzor.MEMORARE_S:     # și după un ceas dat înapoi
            m = _senzor_memorat = senzor.stare_senzor(acum, live=LIVE, loguri=LOGURI, numaratori=NUMARATORI,
                                                      lanturi=LANTURI, fise=FISE)
    return jsonify({**m, "ora_server": time.time()})


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


FAZE_MANUALE = 5       # etapa scurtă, a șasea afișată, nu se cere: ea vine singură din plan


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
        if not 0 <= cmd["faza"] < FAZE_MANUALE:
            return jsonify({"eroare": "fază invalidă"}), 400
    LIVE.mkdir(parents=True, exist_ok=True)
    (LIVE / "command.json").write_text(json.dumps(cmd), encoding="utf-8")
    with open(LIVE / "comenzi.jsonl", "a", encoding="utf-8") as f:      # istoricul, ca să poată fi citit și după o reîncărcare a paginii
        f.write(json.dumps(cmd) + "\n")
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
