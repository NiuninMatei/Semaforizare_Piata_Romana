"""Veghea fluxului de cadre cât timp camera colectează (§ 4.6): o problemă se vede în minute, nu a doua zi.

Rulează lângă `run_vision`, fără să-l atingă: citește o dată pe secundă starea live (outputs/live/state.json, scrisă de
`run_vision` în fiecare secundă în care prelucrează cadre), la 15 s previzualizarea (outputs/live/frame.jpg, doar în
memorie) și, la fiecare minut, traiectoriile noi din jurnalul local. Se oprește cu o alertă (cod de ieșire 2) la primul
semn de problemă, după ce scrie un instantaneu de diagnostic (outputs/logs/veghe_alerta_*.json): procesele după CPU
(plus rândul lui `run_vision`, oricare i-ar fi locul), performanța procesorului, placa grafică pe procese, ultimele rânduri
din jurnalul de erori al viziunii și playlistul HLS al camerei, citit de două ori la 8 s distanță (avansează? cât de în
urmă e ultimul segment?). Analiza cauzei pornește de la acest instantaneu: la noi (prelucrarea) sau în teren (fluxul
camerei)?

Semnele (pragurile alese pe jurnalele 21–29.10 cu `--reluare` și pe jurnalele de erori ale viziunii din 26 și 28.10):
  * proces        – `run_vision` nu mai rulează;
  * fără cadre    – niciun cadru prelucrat de STARE_VECHE s. Întreruperile scurte ale fluxului se refac singure: o
                    reconectare durează ≈30–120 s (30 s până expiră citirea, apoi redeschiderea și tamponul de 8 s);
                    pauzele de cel puțin 10 s doar se notează în CSV, cu playlistul citit la începutul lor (un ultim
                    segment mult în urmă arată spre cameră, unul la zi spre noi) și cu urmele din jurul lor: octeții
                    primiți prin rețea (descărcarea oprită = rețeaua tace, de la ≈8 s – tamponul de redare – înaintea
                    pauzei) și CPU-ul lui `run_vision` (prelucrarea oprită, cu rețeaua mergând);
  * pauze         – cel puțin PRAG_PAUZE pauze de peste PAUZA s între cadre în FEREASTRA_PAUZE s: redare sacadată, ca în
                    21–22.10, când imaginea „mergea 2 s și stătea 4 s”;
  * rata mică     – în ultimele DURATA_FPS s, cel puțin 75% din citiri au rata cadrelor prelucrate (media glisantă din
                    `run_vision`, normal ≈6/s) sub PRAG_FPS. Media glisantă a lui 1/dt supraestimează rata când pașii sunt
                    amestecați, de aceea o dublează semnul din jurnal (pașii lungi); pe 28.10, 03:46–04:28, rata a fost
                    ≈1,4/s;
  * reconectări   – cel puțin MAX_EPISOADE episoade de reconectare în 30 de minute (contorul din `run_vision` crește la
                    fiecare încercare eșuată, deci creșterile la mai puțin de EPISOD s una de alta formează un episod);
                    pe 28.10 au fost 3 episoade în 25 de minute, refăcute singure;
  * jurnal oprit  – nicio traiectorie nouă de STAGNARE s (o imagine înghețată ține urmăririle pe loc: nu se încheie nimic);
  * pași lungi    – în ultimele FEREASTRA s, cel puțin PRAG_LUNGI din pașii dintre punctele vehiculelor peste PAS_LUNG
                    (semnul din `calitate`, văzut pe traiectoriile încheiate);
  * imagine identică – cât timp se prelucrează cadre, previzualizarea nu se schimbă deloc (partea de jos, fără panoul de
                    text) la CITIRI_IDENTICE citiri la rând, sau vehiculele oprite au, minut cu minut, poziții identice
                    punct cu punct. Al doilea semn se vede abia după ce înghețarea trece, iar pe cadre reale detecția
                    „tremură” cu zecimi de pixel. O imagine înghețată care e totuși recodată (cadre aproape identice) nu
                    are încă un prag: diferența dintre previzualizări se notează în CSV, pentru calibrare.
Metricile se scriu o dată pe minut în outputs/logs/veghe_<zi>.csv. Un semn deja analizat se poate ignora la repornire
cu `--fara`.

Exemple:
  python -m romana.vision.veghe --pana-la "2026-10-30 09:05"
  python -m romana.vision.veghe --reluare data/trajectories_brute/traiectorii_2026-10-28.jsonl.gz
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
import zlib
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from romana.common import OUTPUT_DIR, TRAJ_RAW_DIR, load_json
from romana.vision.calitate import MISCARE_MIN, PAS_LUNG, inregistrari
from romana.vision.od_counter import PEDESTRIAN

LIVE_DIR = OUTPUT_DIR / "live"
LOG_DIR = OUTPUT_DIR / "logs"

FEREASTRA = 600          # s; fereastra metricilor din jurnal
PASTRARE = 960           # s; punctele mai vechi nu mai pot intra în fereastră
CADRE_PIERDERE = 30      # cadre prelucrate fără detecție după care o urmărire se închide și se scrie (5 s la 6 cadre/s)
PRAG_LUNGI = 0.15        # pași lungi: pe 29.10 median 3,4%, max 12,4% (cu lanțul de noapte în paralel); episoadele 60–100%
MIN_PASI = 300           # sub atâția pași în fereastră nu se judecă
PRAG_FPS = 3.5           # cadre/s; normal ≈6, cu lanțul de noapte ≈4,5–5,3, pe 28.10 03:46–04:28 ≈1,4
DURATA_FPS = 180         # s de citiri pentru rata mică
STARE_VECHE = 180        # s fără niciun cadru prelucrat; întreruperile din 26 și 28.10 s-au refăcut în cel mult ≈2 min
PAUZA = 2.5              # s; normal starea are cel mult ≈1,2 s
FEREASTRA_PAUZE = 300    # s
PRAG_PAUZE = 10          # pauze în FEREASTRA_PAUZE; sacadarea din 21–22.10 ar da ≈50
EPISOD = 120             # s; creșterile contorului de reconectări mai apropiate fac parte din același episod
MAX_EPISOADE = 4         # în 30 de minute
STAGNARE = 300           # s fără nicio traiectorie nouă; pe 25–29.10, cel mult 1,9 min (afară de opriri)
MIN_PUNCTE_MINUT = 5     # puncte ale unui vehicul oprit într-un minut, ca să-i judecăm pozițiile
PRAG_IDENTICE = 0.5      # ponderea vehiculelor oprite cu poziții identice; pe 21–29.10 cel mult 3,7%
MIN_OPRITE = 10
CITIRI_IDENTICE = 4      # citiri ale previzualizării (la 15 s) fără nicio diferență
URME = 400               # s de urme (octeții primiți, CPU-ul lui run_vision) păstrate pentru pauzele lungi
SEMNE = {"proces": "proces", "cadre": "fără cadre", "pauze": "pauze", "rata": "rata mică", "reconectari": "reconectări",
         "jurnal": "jurnal oprit", "pasi": "pași lungi", "imagine": "imagine identică"}


def membri_noi(path: Path, poz: int) -> tuple[list[dict], int]:
    """Traiectoriile adăugate în jurnal de la octetul `poz` (un membru gzip pe traiectorie). Un ultim membru incomplet
    (în curs de scriere) rămâne pentru citirea următoare; după un membru stricat se caută antetul următor."""
    try:
        with open(path, "rb") as fh:
            fh.seek(poz)
            date = fh.read()
    except OSError:
        return [], poz
    recs, i = [], 0
    while i < len(date):
        d = zlib.decompressobj(31)
        try:
            txt = d.decompress(date[i:])
        except zlib.error:
            j = date.find(b"\x1f\x8b\x08", i + 1)
            if j < 0:
                break
            i = j
            continue
        if not d.eof:
            break
        i = len(date) - len(d.unused_data)
        for line in txt.decode("utf-8", "replace").splitlines():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return recs, poz + i


class Fereastra:
    """Metricile pe minute ale traiectoriilor încheiate (cele scrise deja în jurnal)."""

    def __init__(self):
        self.min = defaultdict(lambda: {"dt": [], "gata": 0, "misc": 0, "st": 0, "st_id": 0})

    def adauga(self, d: dict, sosire: float) -> None:
        p = d.get("p") or []
        if not p:
            return
        t = d["t0"] + np.array([q[0] for q in p])
        m_end = int(t[-1] // 60)
        self.min[m_end]["gata"] += 1
        if d.get("tip") == PEDESTRIAN or len(p) < 2:
            return
        xy = np.array([[q[1], q[2]] for q in p])
        misc = bool(np.hypot(*(xy[-1] - xy[0])) >= MISCARE_MIN)
        self.min[m_end]["misc"] += misc
        k = t >= sosire - PASTRARE
        if k.sum() < 2:
            return
        t, xy = t[k], xy[k]
        mins = (t // 60).astype(int)
        dt, md = np.diff(t), mins[1:]
        for m in np.unique(md):
            self.min[int(m)]["dt"].append(dt[md == m])
        if not misc:
            ms, idx = np.unique(mins, return_index=True)
            for a, b, m in zip(idx, list(idx[1:]) + [len(mins)], ms):
                if b - a >= MIN_PUNCTE_MINUT:
                    r = self.min[int(m)]
                    r["st"] += 1
                    r["st_id"] += int(np.ptp(xy[a:b, 0]) == 0 and np.ptp(xy[a:b, 1]) == 0)

    def evalueaza(self, acum: float) -> dict:
        m1 = int(acum // 60)
        ms = range(m1 - FEREASTRA // 60, m1)
        dt = [a for m in ms if m in self.min for a in self.min[m]["dt"]]
        dt = np.concatenate(dt) if dt else np.zeros(0)
        tot = {c: sum(self.min[m][c] for m in ms if m in self.min) for c in ("gata", "misc", "st", "st_id")}
        for m in [m for m in self.min if m < m1 - PASTRARE // 60]:
            del self.min[m]
        return {"pasi": len(dt), "lungi": float((dt > PAS_LUNG).mean()) if len(dt) else float("nan"),
                "pas_median": float(np.median(dt)) if len(dt) else float("nan"), **tot,
                "identice": tot["st_id"] / tot["st"] if tot["st"] else float("nan")}


def semne_jurnal(m: dict, stagnare: float) -> list[tuple[str, str]]:
    """Semnele de problemă din metricile jurnalului (comune vegherii live și reluării): (cheie, text)."""
    out = []
    if stagnare >= STAGNARE:
        out.append(("jurnal", f"jurnal oprit: nicio traiectorie nouă de {stagnare / 60:.0f} min"))
    if m["pasi"] >= MIN_PASI and m["lungi"] >= PRAG_LUNGI:
        out.append(("pasi", f"pași lungi: {100 * m['lungi']:.0f}% peste {PAS_LUNG} s (pas median {m['pas_median']:.2f} s)"))
    if m["st"] >= MIN_OPRITE and m["identice"] >= PRAG_IDENTICE:
        out.append(("imagine", f"imagine identică: {m['st_id']} / {m['st']} vehicule oprite fără nicio variație a poziției"))
    return out


class StareLive:
    """Semnele din starea live a viziunii (state.json), citită o dată pe secundă."""

    def __init__(self, acum: float):
        self.start = acum
        self.citiri = deque()          # (ora, vârsta stării, rata cadrelor) din ultimele FEREASTRA_PAUZE s
        self.pauze = deque()           # începuturile pauzelor
        self.pauza_din = None          # începutul pauzei în curs
        self.episoade = deque()        # începuturile episoadelor de reconectare
        self.rec0, self.ultima_rec = None, -1e9
        self.evenimente = []           # pauzele lungi încheiate (începutul, durata), pentru CSV

    def adauga(self, acum: float, stare: dict) -> list[tuple[str, str]]:
        varsta = acum - stare["timestamp"]
        self.citiri.append((acum, varsta, stare.get("fps", 6.0)))
        while self.citiri and self.citiri[0][0] < acum - FEREASTRA_PAUZE:
            self.citiri.popleft()
        if varsta >= PAUZA and self.pauza_din is None:
            self.pauza_din = stare["timestamp"]
            self.pauze.append(acum)
        elif varsta < PAUZA and self.pauza_din is not None:
            if stare["timestamp"] - self.pauza_din >= 10:
                self.evenimente.append((self.pauza_din, stare["timestamp"] - self.pauza_din))
            self.pauza_din = None
        while self.pauze and self.pauze[0] < acum - FEREASTRA_PAUZE:
            self.pauze.popleft()
        r = stare.get("reconectari", 0)
        if self.rec0 is not None and r > self.rec0:
            if acum - self.ultima_rec > EPISOD:
                self.episoade.append(acum)
            self.ultima_rec = acum
        self.rec0 = r
        while self.episoade and self.episoade[0] < acum - 1800:
            self.episoade.popleft()
        out = []
        if varsta >= STARE_VECHE:
            out.append(("cadre", f"fără cadre: niciun cadru prelucrat de {varsta:.0f} s"))
        if len(self.pauze) >= PRAG_PAUZE:
            out.append(("pauze", f"pauze: {len(self.pauze)} pauze de peste {PAUZA} s între cadre în ultimele "
                                 f"{FEREASTRA_PAUZE // 60} min"))
        rate = [f for t, v, f in self.citiri if t >= acum - DURATA_FPS and v < PAUZA]
        if acum - self.start >= DURATA_FPS and len(rate) >= DURATA_FPS / 3 and np.mean(np.array(rate) < PRAG_FPS) >= 0.75:
            out.append(("rata", f"rata mică: {np.median(rate):.1f} cadre/s (mediana ultimelor {DURATA_FPS // 60} min)"))
        if len(self.episoade) >= MAX_EPISOADE:
            out.append(("reconectari", f"reconectări: {len(self.episoade)} episoade în ultimele 30 min"))
        return out


def zona_imagine(path: Path):
    """Partea de jos a previzualizării (fără panoul de text din stânga sus), în tonuri de gri, sau None."""
    import cv2
    a = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return None if a is None else a[int(0.4 * a.shape[0]):].astype(np.int16)


# ---------------------------------------------------------------------------------------------- diagnostic
def _playlist(url: str) -> dict:
    """Playlistul HLS citit de două ori, la 8 s distanță: secvența media avansează? (segmentele au ≈6 s)"""
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/130.0 Safari/537.36"}
    out = []
    for k in range(2):
        t = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=10) as r:
                txt = r.read().decode("utf-8", "replace")
            seq = re.search(r"#EXT-X-MEDIA-SEQUENCE:(\d+)", txt)
            seg = [x for x in txt.splitlines() if x and not x.startswith("#")][-3:]
            # numele segmentelor poartă ora lor (UTC), de ex. 2026/10/29/13/10/44-06055.ts: cât de în urmă e fluxul?
            ora = re.search(r"(\d{4})/(\d\d)/(\d\d)/(\d\d)/(\d\d)/(\d\d)", seg[-1]) if seg else None
            urma = (time.time() - datetime(*map(int, ora.groups()), tzinfo=timezone.utc).timestamp()) if ora else None
            out.append({"ora": datetime.now().strftime("%H:%M:%S"), "durata_s": round(time.time() - t, 2),
                        "secventa": int(seq.group(1)) if seq else None, "segmente": seg,
                        "durate": re.findall(r"#EXTINF:([\d.]+)", txt)[-3:],
                        "ultimul_segment_in_urma_s": round(urma, 1) if urma is not None else None})
        except Exception as e:        # rețeaua sau serverul camerei: și asta e o informație
            out.append({"ora": datetime.now().strftime("%H:%M:%S"), "eroare": repr(e)})
        if k == 0:
            time.sleep(8)
    a, b = out[0].get("secventa"), out[1].get("secventa")
    return {"citiri": out, "avanseaza": None if a is None or b is None else b > a}


def _contoare() -> dict:
    """Contoarele Windows: performanța procesorului (% din frecvența nominală; psutil arată doar frecvența de bază) și
    utilizarea plăcii grafice pe procese."""
    cmd = ("$c = Get-Counter '\\Processor Information(_Total)\\% Processor Performance', "
           "'\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue; "
           "$c.CounterSamples | Where-Object { $_.Path -like '*processor*' -or $_.CookedValue -gt 0.5 } | "
           "ForEach-Object { $_.Path + '=' + [math]::Round($_.CookedValue,1) }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=40)
    out, gpu = {}, defaultdict(float)
    for line in r.stdout.splitlines():
        if "=" not in line:
            continue
        cale, v = line.rsplit("=", 1)
        v = float(v.replace(",", "."))
        if "processor performance" in cale.lower():
            out["performanta_cpu_pct"] = v
        else:
            pid, eng = re.search(r"pid_(\d+)", cale), re.search(r"engtype_(\w+)", cale)
            gpu[f"{pid.group(1) if pid else '?'}:{eng.group(1) if eng else '?'}"] += v
    out["gpu"] = dict(sorted(gpu.items(), key=lambda kv: -kv[1])[:10])
    return out


def _procese(proc) -> dict:
    """Procesele după CPU în 3 s (primele 12) și, separat, procesul `run_vision`."""
    import psutil
    procs = list(psutil.process_iter(["pid", "name", "cmdline", "nice"]))
    for p in procs:
        try:
            p.cpu_percent(None)
        except Exception:
            pass
    time.sleep(3)
    rows, viz = [], None
    for p in procs:
        try:
            r = [round(p.cpu_percent(None), 1), p.pid, p.info["name"], str(p.info["nice"]),
                 " ".join(p.info["cmdline"] or [])[:140]]
            rows.append(r)
            if proc is not None and p.pid == proc.pid:
                viz = {"cpu_pct": r[0], "prioritate": r[3], "fire": p.num_threads(),
                       "memorie_mb": round(p.memory_info().rss / 2 ** 20)}
        except Exception:
            pass
    return {"procese_cpu": sorted(rows, key=lambda r: -r[0])[:12], "run_vision": viz}


def _erori_viziune() -> dict:
    """Ultimele 40 de rânduri din cel mai nou jurnal de erori al viziunii (expirări ale fluxului, conexiuni eșuate)."""
    fis = sorted(LOG_DIR.glob("viziune_*.err"), key=lambda f: f.stat().st_mtime)
    if not fis:
        return {}
    f = fis[-1]
    return {"fisier": f.name, "octeti": f.stat().st_size,
            "ultimele": f.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]}


def diagnostic(proc) -> dict:
    """Instantaneul de la momentul alertei: ce rula, cât CPU / GPU lua, cât de tare mergea procesorul, ce a raportat
    fluxul în jurnalul de erori, ce trimitea serverul camerei. Fiecare parte e prinsă separat: o eroare într-una nu le
    pierde pe celelalte."""
    import psutil
    out = {}
    parti = {"procese": lambda: _procese(proc),
             "cpu_pe_nuclee": lambda: psutil.cpu_percent(interval=1, percpu=True),
             "memorie": lambda: {"folosita_pct": psutil.virtual_memory().percent,
                                 "libera_gb": round(psutil.virtual_memory().available / 2 ** 30, 1),
                                 "fisier_paginare_pct": psutil.swap_memory().percent},
             "alimentare": lambda: (lambda b: {"priza": b.power_plugged, "baterie_pct": b.percent} if b else None)(
                 psutil.sensors_battery()),
             "contoare": _contoare,
             "jurnal_erori_viziune": _erori_viziune,
             "playlist": lambda: _playlist(load_json("camera.json")["stream_url"])}
    for k, f in parti.items():
        try:
            out[k] = f()
        except Exception as e:
            out[k] = {"eroare": repr(e)}
    return out


# ---------------------------------------------------------------------------------------------- veghea live
def proces_viziune():
    """Procesul `run_vision` (interpretorul real, nu lansatorul din .venv), dacă rulează (psutil.Process)."""
    import psutil
    gasite = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            if "romana.vision.run_vision" in " ".join(p.info["cmdline"] or []):
                gasite.append(p)
        except psutil.Error:
            pass
    if not gasite:
        return None
    pids = {p.pid for p in gasite}
    try:
        fii = [p for p in gasite if not any(c.pid in pids for c in p.children())]
    except psutil.Error:
        fii = []
    return (fii or gasite)[0]


def jurnale_curente(acum: datetime) -> list[Path]:
    """Jurnalul zilei și al zilei de ieri (o urmărire începută înainte de miezul nopții se scrie în ziua în care a
    început, chiar dacă se încheie după)."""
    return [TRAJ_RAW_DIR / f"traiectorii_{(acum - timedelta(days=k)).strftime('%Y-%m-%d')}.jsonl.gz" for k in (1, 0)]


def _spune(text: str) -> None:
    try:
        print(text, flush=True)
    except (OSError, UnicodeError):    # ieșirea standard închisă sau fără UTF-8: alerta rămâne în fișier
        pass


def _scrie_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


CSV_CAP = ["ora", "fps", "varsta_stare_s", "reconectari", "episoade_flux_30min", "pauze_5min", "urmarite", "dif_imagine",
           "pasi", "pasi_lungi_pct", "pas_median_s", "traiectorii", "in_miscare", "oprite", "identice_pct",
           "fara_traiectorii_s", "evenimente"]


def _eveniment(pauza: tuple[float, float], playlist: dict | None, urme: str | None = None) -> str:
    """O pauză încheiată, cu playlistul citit la începutul ei: un ultim segment mult în urmă (normal 5–9 s) arată spre
    fluxul camerei; unul la zi arată spre noi (descărcarea sau prelucrarea, deosebite de `urme`)."""
    t, d = pauza
    text = f"{datetime.fromtimestamp(t):%H:%M:%S} fără cadre {d:.0f} s"
    if playlist is None:
        text += " (playlist: necitit"
    else:
        urma = [c.get("ultimul_segment_in_urma_s") for c in playlist.get("citiri", [])]
        text += f" (playlist: ultimul segment în urmă {', '.join(f'{u:.0f}' for u in urma if u is not None) or '?'} s, " \
                f"avansează: {playlist.get('avanseaza')}"
    return text + (f"; {urme})" if urme else ")")


class Urme:
    """O dată pe secundă: octeții primiți pe toate plăcile de rețea (fluxul camerei e aproape tot traficul) și timpul de
    procesor al lui `run_vision`, pe ultimele URME s."""

    def __init__(self):
        self.s = deque()                 # (ora, octeți primiți, timp CPU run_vision sau None)

    def adauga(self, acum: float, proc) -> None:
        import psutil
        try:
            rx = psutil.net_io_counters().bytes_recv
        except Exception:
            return
        cpu = None
        if proc is not None:
            try:
                c = proc.cpu_times()
                cpu = c.user + c.system
            except Exception:
                pass
        self.s.append((acum, rx, cpu))
        while self.s and self.s[0][0] < acum - URME:
            self.s.popleft()


def urme_pauza(s, t0: float, t1: float) -> str:
    """Rețeaua și CPU-ul în jurul pauzei [t0, t1]. Descărcarea oprită: cel mai lung gol al rețelei (< 5% din ritmul de
    dinainte) ține cât pauza plus ≈8 s și începe înaintea ei; normal, între două segmente, rețeaua tace ≈4–5 s.
    Prelucrarea oprită: rețeaua merge, iar CPU-ul arată unde (≈100% = un nucleu ocupat în interpretor; puțin = placa
    grafică sau discul)."""
    s = list(s)

    def la(t):                           # ultima citire de dinaintea lui t
        r = [x for x in s if x[0] <= t]
        return r[-1] if r else None

    a, b, d, c = la(t0 - 75), la(t0 - 15), la(t0), la(t1)
    if not (a and b and c and d) or b[0] - a[0] < 30 or c[0] <= b[0]:
        return "urme: prea puține"
    rx0 = (b[1] - a[1]) / (b[0] - a[0])
    rx1 = (c[1] - b[1]) / (c[0] - b[0])
    fer = [x for x in s if t0 - 30 <= x[0] <= t1]
    gol, inceput, cel_mai, inceput_max = 0.0, None, 0.0, None
    for (ta, ra, _), (tb, rb, _) in zip(fer, fer[1:]):
        if (rb - ra) / max(tb - ta, 1e-3) < 0.05 * rx0:
            if inceput is None:
                inceput, gol = ta, 0.0
            gol += tb - ta
            if gol > cel_mai:
                cel_mai, inceput_max = gol, inceput
        else:
            inceput = None
    text = (f"rețea: {rx0 / 1024:.0f} kB/s înainte, {rx1 / 1024:.0f} kB/s de la −15 s, cel mai lung gol {cel_mai:.0f} s"
            + (f" (de la {inceput_max - t0:+.0f} s)" if inceput_max is not None else ""))
    if None not in (a[2], b[2], c[2], d[2]) and c[0] > d[0]:
        text += (f"; CPU run_vision: {100 * (c[2] - d[2]) / (c[0] - d[0]):.0f}% în pauză, "
                 f"{100 * (b[2] - a[2]) / (b[0] - a[0]):.0f}% înainte")
    return text


def veghe(pana_la: datetime, log_csv: Path | None, fara: set[str]) -> int:
    proc = proces_viziune()
    try:
        url = load_json("camera.json")["stream_url"]
    except Exception:
        url = None
    playlist_pauze = {}                # începutul pauzei → playlistul citit atunci (într-un fir separat)
    _spune(f"[veghe] pornită la {datetime.now():%H:%M:%S}, până la {pana_la:%d.%m %H:%M}; run_vision: PID "
           f"{proc.pid if proc else '–'}" + (f"; ignorate: {', '.join(sorted(fara))}" if fara else ""))
    start = time.time()
    fer, live, urme = Fereastra(), StareLive(start), Urme()
    poz = {f: f.stat().st_size if f.exists() else 0 for f in jurnale_curente(datetime.now())}
    ultima_crestere, ultima_eval, ultima_imagine = start, start, 0.0
    stare, m, img0, dif, identice, semne_img = None, None, None, None, 0, []
    while datetime.now() < pana_la:
        acum = time.time()
        semne = []
        if not proc or not proc.is_running():      # is_running compară și ora pornirii (un PID refolosit nu păcălește)
            proc = proces_viziune()
            if not proc:
                semne.append(("proces", "proces: run_vision nu mai rulează"))
        urme.adauga(acum, proc)
        try:
            nou = json.loads((LIVE_DIR / "state.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            nou = None                 # fișierul e înlocuit atomic: o citire ratată nu e o problemă
        if nou:
            stare = nou
            in_pauza = live.pauza_din is not None
            semne += live.adauga(acum, stare)
            if url and not in_pauza and live.pauza_din is not None:
                # la începutul unei pauze: e fluxul camerei în urmă, sau noi? (citirea durează ≈8 s, nu oprește bucla)
                k = live.pauza_din
                threading.Thread(target=lambda: playlist_pauze.__setitem__(k, _playlist(url)), daemon=True).start()
        if acum - ultima_imagine >= 15:
            ultima_imagine = acum
            try:
                img = zona_imagine(LIVE_DIR / "frame.jpg")
            except Exception:
                img = None
            # fără cadre prelucrate, previzualizarea stă pe loc firesc: nu e o imagine înghețată (semnul „fără cadre”)
            proaspat = stare is not None and acum - stare["timestamp"] < PAUZA
            if img is not None and img0 is not None and img.shape == img0.shape and proaspat:
                dif = float(np.abs(img - img0).mean())
                identice = identice + 1 if dif == 0 else 0
            elif not proaspat:
                identice = 0
            if img is not None:
                img0 = img
            semne_img = ([("imagine", f"imagine identică: previzualizarea nu s-a schimbat deloc în "
                                      f"{15 * identice} s")] if identice >= CITIRI_IDENTICE else [])
        semne += semne_img
        if acum - ultima_eval >= 60:
            ultima_eval = acum
            for f in jurnale_curente(datetime.now()):
                poz.setdefault(f, 0)
                if f.exists() and f.stat().st_size < poz[f]:
                    poz[f] = f.stat().st_size          # fișier înlocuit: de la capătul lui
                recs, poz[f] = membri_noi(f, poz[f])
                for d in recs:
                    fer.adauga(d, acum)
                if recs:
                    ultima_crestere = acum
            m = fer.evalueaza(acum)
            # la pornire fereastra e goală: pașii se judecă abia după o fereastră întreagă
            semne += [s for s in semne_jurnal(m, acum - ultima_crestere) if s[0] != "pasi" or acum - start >= FEREASTRA]
            if log_csv:
                rand = [datetime.now().strftime("%Y-%m-%d %H:%M"), stare.get("fps") if stare else "",
                        round(acum - stare["timestamp"], 1) if stare else "", stare.get("reconectari") if stare else "",
                        len(live.episoade), len(live.pauze), stare.get("vehicule_urmarite") if stare else "",
                        round(dif, 2) if dif is not None else "", m["pasi"],
                        round(100 * m["lungi"], 1) if m["pasi"] else "", round(m["pas_median"], 3) if m["pasi"] else "",
                        m["gata"], m["misc"], m["st"], round(100 * m["identice"], 1) if m["st"] else "",
                        round(acum - ultima_crestere),
                        "; ".join(_eveniment(e, playlist_pauze.get(e[0]), urme_pauza(urme.s, e[0], e[0] + e[1]))
                                  for e in live.evenimente)]
                try:
                    nou_csv = not log_csv.exists()
                    with open(log_csv, "a", newline="", encoding="utf-8") as fo:
                        w = csv.writer(fo)
                        if nou_csv:
                            w.writerow(CSV_CAP)
                        w.writerow(rand)
                    live.evenimente.clear()
                except OSError:            # de ex. CSV-ul deschis în Excel: rândul se pierde, veghea continuă
                    pass
        semne = [s for s in semne if s[0] not in fara]
        if semne:
            text = "; ".join(t for _, t in semne)
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            out = LOG_DIR / f"veghe_alerta_{datetime.now():%Y-%m-%d_%H%M%S}.json"
            alerta = {"semne": [t for _, t in semne], "ora": datetime.now().isoformat(timespec="seconds"),
                      "stare_live": stare, "metrici_jurnal": m, "dif_imagine": dif}
            _scrie_json(out, alerta)         # întâi alerta: nicio eroare din diagnostic nu o mai poate pierde
            alerta.update(diagnostic(proc))
            _scrie_json(out, alerta)
            _spune(f"ALERTĂ: {text}")
            _spune(f"[veghe] diagnosticul: {out}")
            return 2
        time.sleep(max(0.0, 1.0 - (time.time() - acum)))
    _spune(f"[veghe] încheiată la {datetime.now():%H:%M:%S}, fără probleme")
    return 0


# ---------------------------------------------------------------------------------------------- reluarea
def reluare(path: Path, csv_out: Path | None) -> None:
    """Trece un jurnal întreg prin regulile din jurnal, în ordinea scrierii: o traiectorie se scrie la CADRE_PIERDERE
    cadre după ultima detecție, adică la sfârșitul ei plus CADRE_PIERDERE pași medii proprii. Servește la alegerea
    pragurilor și la verificarea lor pe episoadele cunoscute (starea live și previzualizarea nu există în trecut)."""
    fer, acum, m_eval, randuri = Fereastra(), None, None, []
    stag_max = defaultdict(float)
    for d in inregistrari(path):
        p = d.get("p")
        if not p:
            continue
        pas = float(np.median(np.diff([q[0] for q in p]))) if len(p) > 1 else 1 / 6
        sos = d["t0"] + p[-1][0] + CADRE_PIERDERE * min(max(pas, 1 / 6), 2.0)
        if acum is not None and sos < acum:
            sos = acum
        if acum is not None:
            h = datetime.fromtimestamp(acum).strftime("%d.%m %H")
            stag_max[h] = max(stag_max[h], sos - acum)
            while m_eval is not None and (m_eval + 1) * 60 <= sos:   # evaluare la fiecare minut încheiat
                m_eval += 1
                t = m_eval * 60
                m = fer.evalueaza(t)
                randuri.append((t, m, t - acum, semne_jurnal(m, t - acum)))
        if m_eval is None:
            m_eval = int(sos // 60)
        acum = sos
        fer.adauga(d, sos)
    print(f"{path.name}: {len(randuri)} minute evaluate")
    episod = None
    for t, m, stag, s in randuri + [(None, None, 0, [])]:
        cheie = ", ".join(sorted({SEMNE[k] for k, _ in s}))
        if episod and (not s or cheie != episod[2]):
            print(f"  {datetime.fromtimestamp(episod[0]):%d.%m %H:%M}–{datetime.fromtimestamp(episod[1]):%H:%M}  "
                  f"{episod[2]}  (prima: {episod[3]})")
            episod = None
        if s and not episod:
            episod = [t, t, cheie, "; ".join(x for _, x in s)]
        elif s:
            episod[1] = t
    ok = [r[1] for r in randuri if r[1]["pasi"] >= MIN_PASI and not r[3]]
    if ok:
        lungi = np.array([m["lungi"] for m in ok])
        ident = np.array([m["identice"] for m in ok if m["st"] >= MIN_OPRITE])
        print(f"  minutele fără semne: pași lungi median {100 * np.median(lungi):.1f}%, p99 {100 * np.quantile(lungi, 0.99):.1f}%,"
              f" max {100 * lungi.max():.1f}%; identice median {100 * np.median(ident) if len(ident) else 0:.1f}%,"
              f" max {100 * ident.max() if len(ident) else 0:.1f}%")
    print("  cel mai lung timp fără traiectorii noi, pe ore (min): " +
          " ".join(f"{h}h:{v / 60:.1f}" for h, v in sorted(stag_max.items(), key=lambda kv: kv[0][3:5] + kv[0])))
    if csv_out:
        with open(csv_out, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(["ora", "pasi", "pasi_lungi_pct", "pas_median_s", "traiectorii", "in_miscare", "oprite",
                        "identice_pct", "fara_traiectorii_s", "semne"])
            for t, m, stag, s in randuri:
                w.writerow([datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M"), m["pasi"],
                            round(100 * m["lungi"], 1) if m["pasi"] else "", round(m["pas_median"], 3) if m["pasi"] else "",
                            m["gata"], m["misc"], m["st"], round(100 * m["identice"], 1) if m["st"] else "",
                            round(stag), "; ".join(x for _, x in s)])


def main() -> None:
    for flux in (sys.stdout, sys.stderr):   # diacriticele merg și când ieșirea e redirecționată fără UTF-8 (cp1250)
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pana-la", help="AAAA-LL-ZZ HH:MM (implicit: peste 24 h)")
    ap.add_argument("--log", help="CSV cu metricile pe minut (implicit outputs/logs/veghe_<zi>.csv)")
    ap.add_argument("--fara", nargs="+", default=[], choices=sorted(SEMNE),
                    help="semne deja analizate, ignorate la această rulare")
    ap.add_argument("--reluare", nargs="+", help="jurnale de traiectorii trecute prin regulile din jurnal (calibrare)")
    ap.add_argument("--out", help="cu --reluare: CSV cu metricile pe minut (doar pentru un singur jurnal)")
    a = ap.parse_args()
    if a.reluare:
        for f in a.reluare:
            reluare(Path(f), Path(a.out) if a.out and len(a.reluare) == 1 else None)
        return
    pana_la = datetime.strptime(a.pana_la, "%Y-%m-%d %H:%M") if a.pana_la else datetime.now() + timedelta(days=1)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = Path(a.log) if a.log else LOG_DIR / f"veghe_{datetime.now():%Y-%m-%d}.csv"
    sys.exit(veghe(pana_la, log, set(a.fara)))


if __name__ == "__main__":
    main()
