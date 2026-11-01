"""Clipuri temporare pentru numărătoarea de referință (§ 4.3, § 4.5), fără să încurce colectarea.

  `captura`  copiază segmentele .ts din playlistul camerei într-un singur fișier, fără să le decodeze, la
             prioritate scăzută. O dată pe secundă notează și o miniatură de 96×54 a previzualizării colectării,
             ca să se poată afla pe urmă cât de târziu vede colectarea aceleași cadre.
  `aliniaza` află acest decalaj: caută momentul în care miniaturile colectării seamănă cel mai bine cu clipul.
  `jurnal`   scoate din jurnalul brut al zilei traiectoriile care încep în timpul clipului, pentru `referinta numara`:
             factorul se calculează direct față de numărarea live, adică exact ce intră în scenarii.
  `sterge`   șterge clipul, miniaturile și foile de contact; rămân doar metadatele și traiectoriile, fără imagini.

Clipurile rămân doar local, în outputs/referinta/clipuri, nu intră în Git și nu se publică (§ 4.5).

Rulare:  python -m romana.vision.captura_clip captura --nume seara_1745 --durata 300 --la 17:45
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from romana.common import OUTPUT_DIR

CLIPURI = OUTPUT_DIR / "referinta" / "clipuri"
PREVIZUALIZARE = OUTPUT_DIR / "live" / "frame.jpg"
URL_IMPLICIT = "https://s5.webcamromania.ro/piataromanab/tracks-v1/mono.m3u8"
JURNAL_BRUT = Path(__file__).resolve().parents[3] / "data" / "trajectories_brute"
MINIATURA = (96, 54)


def citeste_playlist(text: str) -> tuple[int, list[dict]]:
    """Secvența primului segment și segmentele: {"seq", "durata", "cale", "ora"} (ora = secunde, din program date-time)."""
    secventa = 0
    ora = None
    durata = None
    segmente = []
    for linie in (x.strip() for x in text.splitlines()):
        if linie.startswith("#EXT-X-MEDIA-SEQUENCE:"):
            secventa = int(linie.split(":", 1)[1])
        elif linie.startswith("#EXT-X-PROGRAM-DATE-TIME:"):
            ora = datetime.fromisoformat(linie.split(":", 1)[1].replace("Z", "+00:00")).timestamp()
        elif linie.startswith("#EXTINF:"):
            durata = float(linie.split(":", 1)[1].rstrip(","))
        elif linie and not linie.startswith("#"):
            segmente.append({"seq": secventa + len(segmente), "durata": durata or 0.0, "cale": linie, "ora": ora})
            if ora is not None and durata:
                ora += durata
            durata = None
    return secventa, segmente


def _descarca(url: str, timeout: float = 15) -> bytes:
    cerere = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(cerere, timeout=timeout) as r:
        return r.read()


def _prioritate_scazuta() -> None:
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except (ImportError, AttributeError, OSError):
        pass


def _miniatura(cale: Path):
    """Previzualizarea colectării, în tonuri de gri, la 96×54; None dacă nu se poate citi acum."""
    import cv2
    import numpy as np

    try:
        date = np.frombuffer(cale.read_bytes(), dtype=np.uint8)
    except OSError:
        return None
    img = cv2.imdecode(date, cv2.IMREAD_GRAYSCALE) if date.size else None
    return None if img is None else cv2.resize(img, MINIATURA, interpolation=cv2.INTER_AREA)


def captura(nume: str, durata: float, url: str = URL_IMPLICIT, dosar: Path = CLIPURI, descarca=_descarca,
            previzualizare: Path = PREVIZUALIZARE, ceas=time.time, doarme=time.sleep, pauza: float = 1.0,
            maxim_fara_flux: float = 120) -> dict:
    """Copiază segmentele noi până la `durata` secunde de video; întoarce metadatele scrise lângă clip."""
    import numpy as np

    dosar.mkdir(parents=True, exist_ok=True)
    clip = dosar / f"{nume}.ts"
    if clip.exists():
        raise SystemExit(f"Există deja {clip}; alegeți alt nume sau ștergeți-l cu `sterge`.")
    baza = url.rsplit("/", 1)[0] + "/"
    segmente, ore_mini, mini = [], [], []
    ultim = None
    salvat = 0.0
    lipsa = 0
    ultima_reusita = ceas()
    ultima_mini = 0.0
    with open(clip, "wb") as f:
        while salvat < durata:
            acum = ceas()
            if acum - ultima_mini >= 1.0:
                ultima_mini = acum
                m = _miniatura(previzualizare)
                if m is not None:
                    ore_mini.append(acum)
                    mini.append(m)
            try:
                _, lista = citeste_playlist(descarca(url).decode("utf-8", "replace"))
                for s in lista:
                    if ultim is not None and s["seq"] <= ultim:
                        continue
                    if ultim is None:                 # începem cu ultimul segment apărut, ca ora să fie cât mai aproape de acum
                        if s is not lista[-1]:
                            continue
                    elif s["seq"] > ultim + 1:
                        lipsa += s["seq"] - ultim - 1
                    f.write(descarca(baza + s["cale"]))
                    f.flush()
                    ultim = s["seq"]
                    salvat += s["durata"]
                    segmente.append({**s, "sosit": ceas()})
                ultima_reusita = ceas()
            except (urllib.error.URLError, OSError, ValueError) as e:
                if ceas() - ultima_reusita > maxim_fara_flux:
                    print(f"Fluxul nu răspunde de {maxim_fara_flux:.0f} s: {e}")
                    break
            doarme(pauza)
    meta = {"nume": nume, "durata_s": round(salvat, 3), "segmente": segmente, "segmente_lipsa": lipsa,
            "inceput": segmente[0]["ora"] if segmente else None, "url": url,
            "octeti": clip.stat().st_size, "miniaturi": len(mini)}
    (dosar / f"{nume}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    if mini:
        np.savez_compressed(dosar / f"{nume}_mini.npz", ore=np.array(ore_mini), mini=np.stack(mini))
    return meta


def _cadre_clip(clip: Path, pe_secunda: float = 2.0):
    """Cadrele clipului la `pe_secunda` imagini pe secundă, ca miniaturi: (timpi în secunde de la început, imagini)."""
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    pas = max(1, int(round(fps / pe_secunda)))
    timpi, imagini = [], []
    k = 0
    while cap.grab():
        if k % pas == 0:
            ok, cadru = cap.retrieve()
            if ok:
                gri = cv2.cvtColor(cadru, cv2.COLOR_BGR2GRAY)
                imagini.append(cv2.resize(gri, MINIATURA, interpolation=cv2.INTER_AREA))
                timpi.append(k / fps)
        k += 1
    cap.release()
    return np.array(timpi), (np.stack(imagini) if imagini else np.empty((0, MINIATURA[1], MINIATURA[0]), np.uint8))


def potrivire(ore_mini, mini, inceput: float, timpi_clip, imagini_clip, decalaje) -> list[tuple[float, float]]:
    """Pentru fiecare decalaj, diferența medie dintre miniaturile colectării și cadrele clipului de la acel moment.

    Ora dintr-o miniatură = începutul clipului + timpul din clip + decalaj. Cel mai mic scor arată decalajul real."""
    import numpy as np

    def norm(a):
        return a.astype(np.float32) - a.mean(axis=(1, 2), keepdims=True)

    m, c = norm(mini), norm(imagini_clip)
    rez = []
    for d in decalaje:
        t = ore_mini - inceput - d
        bune = (t >= timpi_clip[0]) & (t <= timpi_clip[-1])
        if bune.sum() < 10:
            continue
        j = np.searchsorted(timpi_clip, t[bune]).clip(0, len(timpi_clip) - 1)
        rez.append((float(d), float(np.abs(m[bune] - c[j]).mean())))
    return rez


def aliniaza(nume: str, dosar: Path = CLIPURI) -> dict:
    """Află decalajul colectării față de clip și îl scrie în metadate."""
    import numpy as np

    _prioritate_scazuta()
    meta = json.loads((dosar / f"{nume}.json").read_text(encoding="utf-8"))
    date = np.load(dosar / f"{nume}_mini.npz")
    timpi, imagini = _cadre_clip(dosar / f"{nume}.ts")
    scoruri = potrivire(date["ore"], date["mini"], meta["inceput"], timpi, imagini, np.arange(0, 90.01, 0.5))
    if not scoruri:
        raise SystemExit("Miniaturile nu se suprapun cu clipul.")
    d, cel_mai_bun = min(scoruri, key=lambda x: x[1])
    median = float(np.median([s for _, s in scoruri]))
    meta["decalaj_s"] = d
    meta["scor_decalaj"] = {"minim": round(cel_mai_bun, 2), "median": round(median, 2)}
    (dosar / f"{nume}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"decalaj_s": d, "minim": round(cel_mai_bun, 2), "median": round(median, 2)}


def jurnal(nume: str, dosar: Path = CLIPURI, brut: Path = JURNAL_BRUT) -> tuple[Path, int, float]:
    """Traiectoriile din jurnalul brut care încep în timpul clipului, pentru `referinta numara` (doar local)."""
    meta = json.loads((dosar / f"{nume}.json").read_text(encoding="utf-8"))
    if "decalaj_s" not in meta:
        raise SystemExit("Rulați întâi `aliniaza`.")
    t0 = meta["inceput"] + meta["decalaj_s"]
    t1 = t0 + meta["durata_s"]
    zile = {datetime.fromtimestamp(t).strftime("%Y-%m-%d") for t in (t0, t1)}
    iesire = dosar / f"{nume}_traiectorii"
    iesire.mkdir(exist_ok=True)
    n = 0
    with gzip.open(iesire / "traiectorii_clip.jsonl.gz", "wt", encoding="utf-8") as g:
        for zi in sorted(zile):
            try:
                with gzip.open(brut / f"traiectorii_{zi}.jsonl.gz", "rt", encoding="utf-8", errors="ignore") as f:
                    for linie in f:
                        m = re.match(r'\{"t0":\s*([0-9.]+)', linie)
                        if not m or not t0 - 3600 <= float(m.group(1)) <= t1:
                            continue
                        o = json.loads(linie)
                        p = o.get("p") or []
                        if p and t0 <= float(o["t0"]) + p[0][0] < t1:
                            g.write(linie)
                            n += 1
            except EOFError:                     # jurnalul zilei încă se scrie: ultimul membru poate fi neîncheiat
                pass
    return iesire, n, t0


def sterge(nume: str, dosar: Path = CLIPURI) -> list[str]:
    """Șterge imaginile clipului: fișierul video, miniaturile și foile de contact. Metadatele rămân."""
    sterse = []
    for p in (dosar / f"{nume}.ts", dosar / f"{nume}_mini.npz"):
        if p.exists():
            p.unlink()
            sterse.append(p.name)
    foi = dosar / f"{nume}_foi"
    if foi.is_dir():
        shutil.rmtree(foi)
        sterse.append(foi.name)
    return sterse


def _asteapta(ora: str) -> None:
    h, m = (int(x) for x in ora.split(":"))
    tinta = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
    ramas = (tinta - datetime.now()).total_seconds()
    if ramas < -60:
        raise SystemExit(f"Ora {ora} a trecut deja.")
    if ramas > 0:
        print(f"Aștept până la {ora} ({ramas / 60:.0f} min).", flush=True)
        time.sleep(ramas)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Clipuri temporare pentru numărătoarea de referință")
    sub = ap.add_subparsers(dest="comanda", required=True)
    c = sub.add_parser("captura", help="copiază segmentele fluxului, fără decodare")
    c.add_argument("--nume", required=True)
    c.add_argument("--durata", type=float, default=300, help="secunde de video (implicit 300)")
    c.add_argument("--la", default=None, help="ora locală de început, HH:MM")
    c.add_argument("--url", default=URL_IMPLICIT)
    for cmd, ajutor in (("aliniaza", "decalajul colectării față de clip"), ("jurnal", "traiectoriile din timpul clipului"),
                        ("sterge", "șterge imaginile clipului")):
        s = sub.add_parser(cmd, help=ajutor)
        s.add_argument("--nume", required=True)
    a = ap.parse_args(argv)
    if a.comanda == "captura":
        _prioritate_scazuta()
        if a.la:
            _asteapta(a.la)
        m = captura(a.nume, a.durata, a.url)
        print(f"{a.nume}: {m['durata_s']:.0f} s, {len(m['segmente'])} segmente, {m['segmente_lipsa']} lipsă, "
              f"{m['octeti'] / 1e6:.0f} MB, {m['miniaturi']} miniaturi, început "
              f"{datetime.fromtimestamp(m['inceput'], timezone.utc).astimezone():%H:%M:%S}" if m["inceput"] else a.nume)
    elif a.comanda == "aliniaza":
        print(aliniaza(a.nume))
    elif a.comanda == "jurnal":
        d, n, t0 = jurnal(a.nume)
        print(f"{n} traiectorii în {d} (începutul clipului în colectare: {t0:.2f})")
    elif a.comanda == "sterge":
        print("șterse:", sterge(a.nume))


if __name__ == "__main__":
    main()
