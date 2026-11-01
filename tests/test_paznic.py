"""Teste pentru paznicul colectării (`romana.vision.paznic`, § 4.6), pe procese false: scripturi mici lansate de test, cu
căi temporare și praguri de secunde. Procesele reale nu se ating: paznicul caută după programul rulat (calea scriptului),
fiecare paznic din teste primește un program din dosarul temporar al testului, iar la sfârșitul fiecărui test se verifică
faptul că procesele reale, dacă rulează, au același PID și aceeași oră de pornire.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_paznic
"""
import csv
import ctypes
import gzip
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import warnings
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import psutil

from romana.common import ROOT
from romana.vision.paznic import (Paznic, Setari, _cuvinte, _inlocuieste, _pornit_la, acelasi_program, afiseaza,
                                  are_membri_stricati, camera_raspunde, cerceteaza_procese, citeste_stare,
                                  comanda_implicita, gaseste_procese, goleste_ecranul, iso, main, numara_colectari,
                                  porneste_ascuns, prima_traiectorie, program, scrie_repornire, secventa_playlist,
                                  semne_vecine, trimite_ctrl_c, varsta_semn)

# Un run_vision fals: scrie doar în dosarul temporar primit și trăiește cel mult 2 minute, orice s-ar întâmpla cu testul.
# Bucla are aceeași logică a semnelor de viață ca run_vision.py: previzualizarea la fiecare cadru, starea doar dacă
# `now - last_live > 1.0`, deci după un ceas dat înapoi starea tace, iar colectarea lucrează; un `replace` refuzat se sare.
# Ceasul lui se poate muta din test (decalaj.txt), fiindcă cel al sistemului nu se atinge.
FALS = r'''
import argparse, ctypes, gzip, json, os, signal, subprocess, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--mod", default="normal")
ap.add_argument("--source")
a = ap.parse_args()
d = Path(a.dir)
last_live = 0.0


def ceas():
    try:
        return time.time() + float((d / "decalaj.txt").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return time.time()


def stare(now):
    global last_live
    last_live = now
    tmp = d / "state_tmp.json"
    try:
        tmp.write_text(json.dumps({"timestamp": now}), encoding="utf-8")
        os.utime(tmp, (now, now))
        tmp.replace(d / "state.json")
    except OSError:
        pass


def cadru():
    now = ceas()
    tmp = d / "frame_tmp.jpg"
    try:
        tmp.write_bytes(b"x")
        os.utime(tmp, (now, now))
        tmp.replace(d / "frame.jpg")
    except OSError:
        pass
    if now - last_live > 1.0:
        stare(now)


def traiectorie():
    t = time.time()
    (d / "jurnale").mkdir(exist_ok=True)
    nume = f"traiectorii_{time.strftime('%Y-%m-%d', time.localtime(t))}.jsonl.gz"
    with gzip.open(d / "jurnale" / nume, "at", encoding="utf-8") as f:
        f.write(json.dumps({"t0": round(t, 2), "tip": "passenger", "p": [[0, 0.1, 0.1]]}) + "\n")


k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
with open(d / "porniri.txt", "a", encoding="utf-8") as f:
    f.write(json.dumps({"pid": os.getpid(), "mod": a.mod, "t": time.time(),
                        "fereastra": u32.IsWindowVisible(k32.GetConsoleWindow()),
                        "pythonpath": os.environ.get("PYTHONPATH", "")}) + "\n")
print("rând pe stdout", flush=True)
if a.mod == "moare":
    print("eroare de probă", file=sys.stderr, flush=True)
    sys.exit(7)
if a.mod == "surd":
    signal.signal(signal.SIGINT, signal.SIG_IGN)
if a.mod == "cu_strain":             # alt program, în aceeași consolă
    subprocess.Popen([sys.executable, str(d / "strain.py"), str(d)])
capat, n = time.time() + 120, 0
try:
    if a.mod in ("blocat", "surd", "cu_strain"):
        stare(ceas())
    while time.time() < capat:       # „mut” nu scrie nimic: își încarcă modelul
        if a.mod in ("normal", "tace") or (d / "revino").exists():
            cadru()
        if a.mod == "normal" and n % 4 == 3:
            traiectorie()
        n += 1
        time.sleep(0.05)
except KeyboardInterrupt:
    (d / f"flush_{os.getpid()}").write_text("x")
'''

# Alt program, care doar stă: momeală pentru căutarea după cale; în consola colectării false, străinul care nu trebuie atins.
STRAIN = r'''
import os, sys, time
from pathlib import Path
d = Path(sys.argv[1])
(d / f"strain_pornit_{os.getpid()}").write_text("x")
try:
    time.sleep(120)
except KeyboardInterrupt:
    (d / f"strain_ctrlc_{os.getpid()}").write_text("x")
'''

# O verificare a jurnalului care nu se poate baza pe `romana.vision.repara`: scrie o copie, dar spune că aceasta e stricată.
REPARA_RAU = r'''
import sys
from pathlib import Path
a = sys.argv[1:]
if "--scrie" in a:
    Path(a[a.index("--scrie") + 1]).write_bytes(b"copie proasta")
print("x: membri=1, stricati=1, in_scriere=0, linii=1")
sys.exit(2)
'''

REALE: dict[int, float] = {}
MODUL_FALS = "fals_paznic_modul"
PROG_REAL = ("-m", "romana.vision.run_vision")


def procese_reale() -> dict[int, float]:
    """Colectarea și veghea reale, dacă rulează, găsite fără codul paznicului (doar citire)."""
    out = {}
    for p in psutil.process_iter():
        try:
            c = p.cmdline()
            if "romana.vision.run_vision" in c or "romana.vision.veghe" in c:
                out[p.pid] = p.create_time()
        except (psutil.Error, OSError):
            pass
    return out


def schimbate_reale() -> dict:
    acum = procese_reale()
    return {pid: t for pid, t in REALE.items() if acum.get(pid) != t}


def setUpModule():
    REALE.update(procese_reale())
    warnings.simplefilter("ignore", ResourceWarning)      # procesele false rămân pornite după `Popen`, ca în realitate


def tearDownModule():
    if schimbate_reale():
        raise AssertionError(f"Procese reale schimbate în timpul testelor: {schimbate_reale()}")


def membru(t0: float) -> bytes:
    return gzip.compress((json.dumps({"t0": t0, "tip": "passenger", "p": [[0, 0.1, 0.1]]}) + "\n").encode(), mtime=0)


def port_inchis() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Camera:
    """Un server HLS fals, pe 127.0.0.1: playlistul avansează la fiecare citire. Se poate opri (503), poate sta pe loc,
    poate să nu fie un playlist sau să nu-și declare secvența; `lent` = „corp” sau „antet” (picură câte un octet), „urias”
    (nu se mai termină), „bucati” (Transfer-Encoding: chunked)."""

    def __init__(self):
        camera = self
        self.seq, self.pe_loc, self.html, self.oprita, self.fara_secventa = 100, False, False, False, False
        self.lent, self.citiri = None, 0

        class Raspuns(BaseHTTPRequestHandler):
            def do_GET(self):
                camera.citiri += 1
                if camera.oprita:
                    self.send_error(503)
                elif camera.lent == "antet":
                    self.picura(b"HTTP/1.1 200 OK\r\nX-Lung: " + b"a" * 50)
                elif camera.lent == "corp":
                    self.send_response(200)
                    self.send_header("Content-Length", "1000")
                    self.end_headers()
                    self.picura(b"#EXTM3U\n" + b"#" * 50)
                elif camera.lent == "urias":
                    self.send_response(200)
                    self.send_header("Content-Length", str(1 << 30))
                    self.end_headers()
                    self.trimite([b"#" * 65536] * 200)
                elif camera.lent == "bucati":
                    self.protocol_version = "HTTP/1.1"
                    self.send_response(200)
                    self.send_header("Transfer-Encoding", "chunked")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    corp = self.corp()
                    self.trimite([b"%x\r\n%s\r\n" % (len(x), x) for x in (corp[:5], corp[5:])] + [b"0\r\n\r\n"])
                else:
                    corp = self.corp()
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(corp)))
                    self.end_headers()
                    self.wfile.write(corp)

            def corp(self):
                if not camera.pe_loc:
                    camera.seq += 1
                if camera.html:
                    return b"<html>portal</html>"
                if camera.fara_secventa:
                    return b"#EXTM3U\n"
                return f"#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:{camera.seq}\n#EXTINF:6.0,\nseg.ts\n".encode()

            def picura(self, octeti):
                self.trimite([bytes([x]) for x in octeti], 0.2)

            def trimite(self, bucati, pauza=0.0):
                try:
                    for x in bucati:
                        self.wfile.write(x)
                        self.wfile.flush()
                        time.sleep(pauza)
                except OSError:
                    pass

            def log_message(self, *a):
                pass

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Raspuns)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/mono.m3u8"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def inchide(self):
        self.srv.shutdown()
        self.srv.server_close()


class Banc(unittest.TestCase):
    """Dosarul temporar, colectarea falsă, camera falsă și paznicul configurat doar pe ele."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="paznic_")).resolve()
        self.fals = self.d / "fals_run_vision.py"
        self.fals.write_text(FALS, encoding="utf-8")
        (self.d / "strain.py").write_text(STRAIN, encoding="utf-8")
        self.camera = Camera()
        self.n, self.decalaj = 0, 0.0
        ecran = mock.patch("sys.stdout", io.StringIO())       # rândurile paznicului rămân în fișierele lor
        ecran.start()
        self.addCleanup(ecran.stop)
        self.addCleanup(shutil.rmtree, self.d, True)
        self.addCleanup(self.camera.inchide)
        self.addCleanup(self._opreste_falsii)
        self.addCleanup(lambda: self.assertEqual(schimbate_reale(), {}))

    def _opreste_falsii(self):
        """Doar procesele cu un argument din dosarul temporar al acestui test."""
        al_nostru = os.path.normcase(str(self.d))
        gasite = []
        for p in psutil.process_iter():
            try:
                if p.name().casefold().startswith("python") and any(os.path.normcase(x).startswith(al_nostru)
                                                                     for x in p.cmdline()):
                    gasite.append(p)
            except (psutil.Error, OSError):
                pass
        for p in gasite:
            try:
                p.kill()
            except psutil.Error:
                pass
        psutil.wait_procs(gasite, timeout=10)

    def comanda(self, mod: str = "normal", fals: Path | None = None, d: Path | None = None) -> list[str]:
        return [sys.executable, str(fals or self.fals), "--dir", str(d or self.d), "--mod", mod]

    def setari(self, **k) -> Setari:
        v = dict(comanda=self.comanda(), comanda_repara=[sys.executable, "-m", "romana.vision.repara"],
                 stare=self.d / "state.json", fara_repornire=self.d / "fara_repornire", jurnale=self.d / "jurnale",
                 loguri=self.d / "logs", cwd=self.d, playlist=self.camera.url, pas=0.1, prag_stare=0.5, prag_viu=0.0,
                 verificari_lipsa=1, timp_oprire=30, pauza_trezire=120, prag_salt=60, asteptari=(0, 0, 0), stabil=600,
                 timp_crestere=60, timp_verificare=60, rabdare_camera=0, timeout_playlist=2, pauza_playlist=0.05)
        v.update(k)
        s = Setari(**v)
        # nicio cale și niciun program al colectării reale nu ajung într-un paznic din teste
        prog = program(s.comanda)
        self.assertTrue(prog[0].startswith(os.path.normcase(str(self.d))) or prog == ("-m", MODUL_FALS), s.comanda)
        for cale in (s.stare, s.fara_repornire, s.jurnale, s.loguri, s.cwd):
            self.assertTrue(cale.is_relative_to(self.d), cale)
        return s

    def paznic(self, **k) -> Paznic:
        return Paznic(self.setari(**k))

    # ------------------------------------------------------------------ ceasul care se poate muta
    def ceas(self) -> float:
        return time.time() + self.decalaj

    def muta_ceasul(self, dt: float) -> None:
        """Mută ceasul paznicului și pe cel al colectării false; ține loc și de timpul care trece."""
        self.decalaj += dt
        tmp = self.d / "decalaj.tmp"
        tmp.write_text(str(self.decalaj), encoding="utf-8")
        for _ in range(100):                     # colectarea îl citește des: pe Windows, înlocuirea poate fi refuzată o clipă
            try:
                tmp.replace(self.d / "decalaj.txt")
                return
            except PermissionError:
                time.sleep(0.01)
        tmp.replace(self.d / "decalaj.txt")

    def paznic_real(self, **k) -> Paznic:
        """Pragurile reale din `Setari`, pe ceasul care se poate muta; doar căile și comanda sunt de probă."""
        r = Setari()
        v = dict(pas=r.pas, prag_stare=r.prag_stare, prag_camera=r.prag_camera, prag_viu=r.prag_viu,
                 verificari_lipsa=r.verificari_lipsa, pauza_trezire=r.pauza_trezire, prag_salt=r.prag_salt,
                 asteptari=r.asteptari, rabdare_camera=r.rabdare_camera, pauza_playlist=0.01)
        v.update(k)
        return Paznic(self.setari(**v), ceas=self.ceas)

    def colectare_veche(self, mod: str = "normal") -> Paznic:
        """Ca o colectare care rulează de mult: ora pornirii procesului nu mai e un semn de viață."""
        self.muta_ceasul(1000)
        self.porneste_fals(mod)
        self.asteapta(lambda: citeste_stare(self.d / "state.json") is not None, "starea a apărut")
        return self.paznic_real()

    def la_varsta(self, secunde: float, ts: float) -> None:
        """Mută ceasul până când starea scrisă la `ts` are vârsta dată."""
        self.muta_ceasul(secunde - (self.ceas() - ts))

    # ------------------------------------------------------------------ ce se vede
    def porniri(self, d: Path | None = None) -> list[dict]:
        f = (d or self.d) / "porniri.txt"
        return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []

    def asteapta(self, cond, mesaj: str = "", timeout: float = 30.0) -> None:
        t0 = time.time()
        while not cond():
            if time.time() - t0 > timeout:
                self.fail(f"nu s-a întâmplat în {timeout} s: {mesaj}")
            time.sleep(0.02)

    def porneste_fals(self, mod: str = "normal", fals: Path | None = None, d: Path | None = None,
                      comanda: list[str] | None = None) -> dict:
        """O colectare falsă, în consola ei ascunsă; se întoarce după ce interpretorul ei a început să lucreze."""
        n0, self.n = len(self.porniri(d)), self.n + 1
        porneste_ascuns(comanda or self.comanda(mod, fals, d), self.d, dict(os.environ), self.d / f"fals_{self.n}.log",
                        self.d / f"fals_{self.n}.err")
        self.asteapta(lambda: len(self.porniri(d)) > n0, "colectarea falsă a pornit")
        return self.porniri(d)[-1]

    def procese(self, fals: Path | None = None) -> list[psutil.Process]:
        return gaseste_procese(program(self.comanda(fals=fals)))

    def pids(self, fals: Path | None = None) -> set[int]:
        return {p.pid for p in self.procese(fals)}

    def stare_veche(self, p: Paznic) -> None:
        """Așteaptă până când și procesul, și starea sunt mai vechi decât pragul paznicului."""
        def e_veche():
            ts = citeste_stare(p.s.stare) or 0.0
            return time.time() - max(ts, _pornit_la(self.procese())) > p.s.prag_stare + 0.05
        self.asteapta(e_veche, "starea a îmbătrânit")

    def scrie_stare(self, ts: float) -> None:
        (self.d / "state.json").write_text(json.dumps({"timestamp": ts}), encoding="utf-8")

    def text_paznic(self) -> str:
        return "".join(f.read_text(encoding="utf-8") for f in sorted((self.d / "logs").glob("paznic_*.log")))

    def reporniri(self) -> list[dict]:
        rez = []
        for f in sorted((self.d / "logs").glob("reporniri_*.csv")):
            with open(f, newline="", encoding="utf-8") as fh:
                rez += list(csv.DictReader(fh))
        return rez

    def flushuri(self) -> list[str]:
        return sorted(x.name for x in self.d.glob("flush_*"))


class FalsP:
    """Un proces văzut de `cerceteaza_procese`: `argv` e linia de comandă sau excepția pe care o ridică citirea ei; o listă de
    excepții și linii se consumă la citiri succesive."""

    def __init__(self, pid: int, *citiri, nume: str = "python.exe"):
        self.pid, self.citiri, self.nume = pid, list(citiri), nume

    def name(self):
        return self.nume

    def cmdline(self):
        c = self.citiri.pop(0) if len(self.citiri) > 1 else self.citiri[0]
        if isinstance(c, Exception):
            raise c
        return c


class TestRecunoastere(unittest.TestCase):
    PY = r"C:\Proiect\.venv\Scripts\python.exe"
    MOD = "romana.vision.run_vision"

    def test_programul_din_linia_de_comanda(self):
        prog = PROG_REAL
        self.assertEqual(program([self.PY, "-m", "romana.vision.run_vision"]), prog)          # lansatorul
        self.assertEqual(program([r"C:\Python312\python.exe", "-m", "romana.vision.run_vision"]), prog)      # copilul
        self.assertEqual(program([self.PY, "-X", "utf8", "-u", "-m", "romana.vision.run_vision", "--show"]), prog)
        self.assertEqual(program([self.PY, r"C:/Tmp/A/fals.py", "--dir", "x"]), (os.path.normcase(r"C:\Tmp\A\fals.py"),))

    def test_optiunile_se_citesc_ca_in_interpretor(self):
        # toate formele pornesc aceeași colectare: nerecunoscută, ar fi luat-o drept „lipsă” și ar fi pornit a doua
        for opt in (["-um", self.MOD], ["-Bm", self.MOD], ["-m" + self.MOD], ["-uBm" + self.MOD], ["-Xutf8", "-m", self.MOD],
                    ["-Xutf8", "-um", self.MOD], ["-X", "utf8", "-m", self.MOD], ["-Wignore", "-u", "-m", self.MOD],
                    ["-W", "ignore", "-m", self.MOD], ["--check-hash-based-pycs", "default", "-m", self.MOD]):
            self.assertEqual(program([self.PY, *opt]), PROG_REAL, opt)
        self.assertEqual(program([self.PY, "-u", "--", "f.py"]), (os.path.normcase("f.py"),))
        self.assertEqual(program([self.PY, "-X", "utf8", "f.py", "-m", self.MOD]), (os.path.normcase("f.py"),))
        self.assertIsNone(program([self.PY, "-uc", "print(1)"]))
        self.assertIsNone(program([self.PY, "-cprint(1)"]))
        self.assertIsNone(program([self.PY, "-X"]))
        self.assertIsNone(program([self.PY, "-um"]))

    def test_calea_scriptului_e_acelasi_program(self):
        for cale in (r"src\romana\vision\run_vision.py", r"C:/P/src/romana/vision/run_vision.py",
                     r"romana\vision\run_vision.py"):
            self.assertTrue(acelasi_program(program([self.PY, cale]), PROG_REAL), cale)
        for cale in (r"C:\P\alta_romana\vision\run_vision.py", "run_vision.py", r"C:\P\romana\vision\veghe.py"):
            self.assertFalse(acelasi_program(program([self.PY, cale]), PROG_REAL), cale)
        self.assertFalse(acelasi_program(None, PROG_REAL))

    def test_nu_se_confunda_cu_altele(self):
        prog = PROG_REAL
        for argv in (["powershell.exe", "-Command", "Get-Process | Where { $_.CommandLine -match 'romana.vision.run_vision' }"],
                     ["cmd.exe", "/c", "python", "-m", "romana.vision.run_vision"],
                     [self.PY, "-m", "romana.vision.veghe", "--pana-la", "2026-11-02 09:00"],
                     [self.PY, "-m", "romana.vision.paznic", "--comanda", "python -m romana.vision.run_vision"],
                     [self.PY, "-c", "import romana.vision.run_vision"],
                     [self.PY, "-uc", "import romana.vision.run_vision"],
                     [self.PY, "alt_script.py", "-m", "romana.vision.run_vision"],
                     [self.PY, "-m", "unittest", "tests.test_paznic"], [self.PY], [self.PY, "-m"], []):
            self.assertNotEqual(program(argv), prog, argv)

    def test_o_rulare_pe_un_fisier_video_nu_e_colectarea(self):
        # scrie în aceleași fișiere, dar se termină odată cu clipul; `--show` și ceilalți parametri rămân colectare
        for rest in (["--source", "clip.mp4"], ["--source=clip.mp4"], ["--sourc", "clip.mp4"], ["--so", "clip.mp4"],
                     ["--show", "--source", "clip.mp4"]):
            self.assertIsNone(program([self.PY, "-m", self.MOD, *rest]), rest)
        for rest in (["--show"], ["--minutes", "15"], ["--s"], ["--sh"]):
            self.assertEqual(program([self.PY, "-m", self.MOD, *rest]), PROG_REAL, rest)
        with self.assertRaises(ValueError):       # o comandă cu `--source` nu se păzește
            Paznic(Setari(comanda=[self.PY, "-m", self.MOD, "--source", "clip.mp4"]))

    def _incadrare(self, *procese, prog=PROG_REAL) -> tuple[list[int], list[int]]:
        with mock.patch("romana.vision.paznic.psutil.process_iter", return_value=list(procese)):
            gasite, nestiute = cerceteaza_procese(prog)
        return [p.pid for p in gasite], [p.pid for p in nestiute]

    def test_incadrarea_proceselor(self):
        py, mod = self.PY, self.MOD
        colectare = [[py, "-m", mod], [py, "-um", mod], [py, "-m" + mod], [py, "-Bm", mod], [py, "-X", "utf8", "-m", mod],
                     [py, "--check-hash-based-pycs", "default", "-m", mod], [py, r"src\romana\vision\run_vision.py"],
                     [py, "-m", mod, "--show"]]
        nestiut = [[py, "-c", "import runpy; runpy.run_module('romana.vision.run_vision', run_name='__main__')"],
                   [py, "-c", "from romana.vision import run_vision; run_vision.main()"], [py, "-m", "runpy", mod],
                   [py, "lanseaza.py", "-m", mod], [py, "-m", mod, "--source", "clip.mp4"], [py, "run_vision.py"],
                   [py, r"C:\Alt\run_vision.py"]]
        altceva = [[py, "-m", "romana.vision.veghe", "--log", "outputs/logs/veghe.csv"], [py, "-c", "print(1)"],
                   [py, "-m", "romana.vision.paznic", "--comanda", "python -m romana.vision.run_vision"],
                   [py, "-m", "romana.lant_zilnic", "--zi", "2026-11-01"], [py, "-m", "romana.vision.run_vision_vechi"],
                   [py, "alt_script.py", "--dir", "fals_run_vision"], [py, "-m", "unittest", "tests.test_paznic"],
                   [r"C:\run_vision\python.exe", "-c", "print(1)"], [py], []]
        numar = [FalsP(10_000_000 + i, x) for i, x in enumerate(colectare)]
        neclar = [FalsP(20_000_000 + i, x) for i, x in enumerate(nestiut)]
        rest = [FalsP(30_000_000 + i, x) for i, x in enumerate(altceva)]
        self.assertEqual(self._incadrare(*numar, *neclar, *rest), ([p.pid for p in numar], [p.pid for p in neclar]))

    def test_doar_procesele_python_se_cerceteaza(self):
        strain = FalsP(10_000_001, ["powershell.exe", "-c", "python -m romana.vision.run_vision"], nume="powershell.exe")
        necitit = FalsP(10_000_002, psutil.AccessDenied(1), nume="svchost.exe")
        self.assertEqual(self._incadrare(strain, necitit), ([], []))

    def test_linia_de_comanda_necitibila_nu_inseamna_lipsa(self):
        refuzat = FalsP(10_000_001, psutil.AccessDenied(1))
        disparut = FalsP(10_000_002, psutil.NoSuchProcess(1))
        self.assertEqual(self._incadrare(refuzat, disparut), ([], [10_000_001]))
        # la pornire, linia de comandă poate fi o clipă necitibilă: la a doua citire, procesul se încadrează
        self.assertEqual(self._incadrare(FalsP(10_000_003, psutil.AccessDenied(1), [self.PY, "-m", "unittest"])), ([], []))
        self.assertEqual(self._incadrare(FalsP(10_000_004, psutil.AccessDenied(1), [self.PY, "-m", self.MOD])),
                         ([10_000_004], []))

    def test_paznicul_nu_se_numara_pe_sine(self):
        eu = FalsP(os.getpid(), [self.PY, "-c", "from romana.vision.paznic import main  # romana.vision.run_vision"])
        parinte = FalsP(os.getppid(), psutil.AccessDenied(1))
        self.assertEqual(self._incadrare(eu, parinte), ([], []))

    def test_comanda_fara_program_e_refuzata(self):
        with self.assertRaises(ValueError):
            Paznic(Setari(comanda=["cmd.exe", "/c", "start"]))

    def test_lansatorul_si_copilul_sunt_o_colectare(self):
        class P:
            def __init__(self, pid, ppid):
                self.pid, self._ppid = pid, ppid

            def ppid(self):
                return self._ppid
        self.assertEqual(numara_colectari([P(10, 1), P(11, 10)]), 1)
        self.assertEqual(numara_colectari([P(11, 10)]), 1)          # copilul fără lansator
        self.assertEqual(numara_colectari([P(10, 1), P(11, 10), P(20, 1), P(21, 20)]), 2)
        self.assertEqual(numara_colectari([]), 0)

    def test_comanda_ca_text(self):
        self.assertEqual(_cuvinte(r'"C:\Program Files\P\python.exe" -m romana.vision.run_vision'),
                         [r"C:\Program Files\P\python.exe", "-m", "romana.vision.run_vision"])
        self.assertEqual(_cuvinte(r"C:\P\python.exe C:\T\f.py --dir C:\T"),
                         [r"C:\P\python.exe", r"C:\T\f.py", "--dir", r"C:\T"])

    def test_starea_citita(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "state.json"
            self.assertIsNone(citeste_stare(f))
            f.write_text(json.dumps({"timestamp": 1793000000.5}), encoding="utf-8")
            self.assertEqual(citeste_stare(f), 1793000000.5)
            for rau in ({"timestamp": 0}, {"timestamp": -5}, {"timestamp": 1e20}, {"timestamp": float("nan")}):
                f.write_text(json.dumps(rau), encoding="utf-8")
                self.assertIsNone(citeste_stare(f), rau)
            f.write_text("{ pe jumătate", encoding="utf-8")         # data fișierului, dacă nu se poate citi
            self.assertAlmostEqual(citeste_stare(f), f.stat().st_mtime)

    def test_valorile_implicite_sunt_cele_cerute(self):
        s = Setari()
        self.assertEqual(program(s.comanda), ("-m", "romana.vision.run_vision"))
        self.assertEqual(program(comanda_implicita()), ("-m", "romana.vision.run_vision"))
        self.assertEqual((s.pas, s.prag_stare, s.timp_oprire, s.pauza_trezire, s.asteptari),
                         (60, 300, 90, 120, (60, 120, 300)))
        self.assertEqual((s.prag_camera, s.rabdare_camera, s.verificari_lipsa), (180, 120, 2))
        self.assertEqual(s.stare, ROOT / "outputs" / "live" / "state.json")
        self.assertEqual(s.fara_repornire, ROOT / "outputs" / "live" / "fara_repornire")
        self.assertEqual(s.jurnale, ROOT / "data" / "trajectories_brute")
        self.assertEqual(s.loguri, ROOT / "outputs" / "logs")
        self.assertEqual(s.comanda_repara[1:], ["-m", "romana.vision.repara"])

    def test_contoarele_verificarii(self):
        self.assertIs(are_membri_stricati("j.gz: membri=9, stricati=0, in_scriere=0, linii=9"), False)
        self.assertIs(are_membri_stricati("j.gz: membri=9, stricati=2, in_scriere=0, linii=9"), True)
        self.assertIs(are_membri_stricati("j.gz: membri=9, stricati=0, in_scriere=1, linii=9"), True)
        self.assertIsNone(are_membri_stricati("usage: repara.py [-h] fisier"))


class TestProcesele(Banc):
    def test_doua_procese_o_colectare_fara_al_doilea(self):
        self.porneste_fals("normal")
        procese = self.procese()
        self.assertEqual(len(procese), 2 if sys.prefix != sys.base_prefix else 1)   # lansatorul din .venv și copilul
        self.assertEqual(numara_colectari(procese), 1)
        p = self.paznic(prag_stare=30)
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.pids(), {x.pid for x in procese})
        self.assertIn("în regulă: 2 procese" if len(procese) == 2 else "în regulă: 1 procese", self.text_paznic())

    def test_doua_colectari_raman_pe_seama_omului(self):
        self.porneste_fals("blocat")
        self.porneste_fals("blocat")
        vechi = self.pids()
        p = self.paznic()
        self.stare_veche(p)
        self.assertEqual(p.pas(), "mai_multe")
        self.assertEqual(self.pids(), vechi)
        self.assertEqual(len(self.porniri()), 2)
        self.assertEqual(self.flushuri(), [])
        self.assertIn("2 colectări", self.text_paznic())

    def test_fara_al_doilea_daca_apare_intre_timp(self):
        # procesul nu se vede la verificare, dar apare chiar înaintea pornirii
        self.porneste_fals("normal")
        p, viu = self.paznic(), self.procese()
        cautari = [([], []), ([], []), ([], []), (viu, [])]   # verificarea, ultima privire, oprirea, chiar înaintea pornirii
        with mock.patch("romana.vision.paznic.cerceteaza_procese", side_effect=cautari):
            self.assertEqual(p.pas(), "exista")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.reporniri(), [])

    def test_fara_al_doilea_daca_procesul_pornit_nu_se_vede(self):
        # căutarea nu-l mai găsește, dar procesul pornit de paznic trăiește
        p = self.paznic(asteptari=(0,))
        with mock.patch("romana.vision.paznic.cerceteaza_procese", return_value=([], [])):
            self.assertEqual(p.pas(), "pornit")
            self.asteapta(lambda: len(self.porniri()) == 1, "colectarea a pornit")
            self.assertEqual(p.pas(), "exista")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(len(self.reporniri()), 1)

    def test_stare_proaspata_fara_proces_vazut(self):
        # cineva tocmai a scris starea: nu pornim altă colectare peste ea
        self.scrie_stare(time.time())
        p = self.paznic(prag_viu=30)
        self.assertEqual(p.pas(), "viu")
        self.assertEqual(self.porniri(), [])

    def test_previzualizare_proaspata_fara_proces_vazut(self):
        # starea e veche, dar cineva încă scrie cadre
        self.scrie_stare(time.time() - 3600)
        (self.d / "frame.jpg").write_bytes(b"x")
        p = self.paznic(prag_viu=30)
        self.assertEqual(p.pas(), "viu")
        self.assertEqual(self.porniri(), [])

    def test_lipsa_se_accepta_la_a_doua_verificare_la_rand(self):
        p = self.paznic(verificari_lipsa=2)
        self.assertEqual(p.pas(), "lipsa")
        self.assertEqual(self.porniri(), [])
        self.assertIn("verificarea 1 din 2", self.text_paznic())
        self.assertEqual(p.pas(), "pornit")

    def test_procesul_nevazut_o_clipa_nu_primeste_al_doilea(self):
        # o căutare care nu-l vede pe cel viu (o linie de comandă care nu se poate citi o clipă): doar o verificare pierdută
        self.porneste_fals("normal")
        vechi = self.pids()
        p = self.paznic(verificari_lipsa=2, prag_stare=30)
        with mock.patch("romana.vision.paznic.cerceteaza_procese", return_value=([], [])):
            self.assertEqual(p.pas(), "lipsa")
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(p.lipsa, 0)
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.pids(), vechi)
        for x in self.procese():                              # numărătoarea a luat-o de la capăt
            x.kill()
        self.asteapta(lambda: not self.procese(), "procesul a murit")
        self.assertEqual(p.pas(), "lipsa")
        self.assertEqual(p.pas(), "pornit")

    def test_colectare_cu_optiuni_lipite_nu_primeste_a_doua(self):
        (self.d / f"{MODUL_FALS}.py").write_text(FALS, encoding="utf-8")
        self.porneste_fals(comanda=[sys.executable, "-um", MODUL_FALS, "--dir", str(self.d), "--mod", "normal"])
        p = self.paznic(comanda=[sys.executable, "-m", MODUL_FALS, "--dir", str(self.d)], prag_stare=30)
        vechi = {x.pid for x in gaseste_procese(p.prog)}
        self.assertEqual(numara_colectari(gaseste_procese(p.prog)), 1)
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual({x.pid for x in gaseste_procese(p.prog)}, vechi)

    def test_linia_de_comanda_necitibila_nu_primeste_a_doua(self):
        self.porneste_fals("normal")
        vechi = self.pids()
        p = self.paznic()
        with mock.patch.object(psutil.Process, "cmdline", side_effect=psutil.AccessDenied(1)):
            self.assertEqual(p.pas(), "nestiut")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.pids(), vechi)
        self.assertIn("poate fi colectarea", self.text_paznic())
        self.assertIn("ATENȚIE", self.text_paznic())

    def _cod_care_pomeneste(self) -> None:
        cod = f"import sys, time; open(sys.argv[1] + '/c_pornit', 'w').close(); time.sleep(60)  # {self.fals}"
        porneste_ascuns([sys.executable, "-c", cod, str(self.d)], self.d, dict(os.environ), self.d / "c.log",
                        self.d / "c.err")
        self.asteapta(lambda: (self.d / "c_pornit").exists(), "codul a pornit")

    def test_cod_care_pomeneste_programul_nu_primeste_a_doua(self):
        self._cod_care_pomeneste()
        p = self.paznic()
        self.assertEqual(self.procese(), [])
        self.assertEqual(len(cerceteaza_procese(p.prog)[1]), 2 if sys.prefix != sys.base_prefix else 1)
        self.assertEqual(p.pas(), "nestiut")
        self.assertEqual(self.porniri(), [])

    def test_un_nestiut_nu_opreste_o_colectare_blocata(self):
        # dacă l-ar opri, ar rămâne fără nicio colectare: pornirea e și ea refuzată cât timp nu se știe
        self.porneste_fals("blocat")
        self._cod_care_pomeneste()
        p = self.paznic()
        self.stare_veche(p)
        vechi = self.pids()
        self.assertEqual(p.pas(), "nestiut")
        self.assertEqual(self.pids(), vechi)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(self.reporniri(), [])

    def test_un_nestiut_aparut_in_timpul_citirii_playlistului_nu_opreste_nimic(self):
        self.porneste_fals("blocat")
        p = self.paznic()
        self.stare_veche(p)
        vechi = self.pids()

        def camera(*a):
            self._cod_care_pomeneste()
            return True, "playlistul răspunde (probă)"
        with mock.patch("romana.vision.paznic.camera_raspunde", side_effect=camera):
            self.assertEqual(p.pas(), "nestiut")
        self.assertEqual(self.pids(), vechi)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(p.incercari, 0)

    def test_un_nestiut_aparut_dupa_oprire_amana_pornirea(self):
        p = self.paznic()
        cautari = [([], []), ([], []), ([], []), ([], [object()])]
        with mock.patch("romana.vision.paznic.cerceteaza_procese", side_effect=cautari):
            self.assertEqual(p.pas(), "exista")
        self.assertEqual(self.porniri(), [])
        self.assertEqual(p.pas(), "pornit")

    def _rulare_pe_clip(self) -> list[psutil.Process]:
        alta = self.d / "clip"
        alta.mkdir()
        self.porneste_fals(d=alta, comanda=[*self.comanda("mut", d=alta), "--source", "clip.mp4"])
        self.assertEqual(self.procese(), [])
        return cerceteaza_procese(program(self.comanda()))[1]

    def test_rularea_pe_clip_nu_blocheaza_paza_colectarii(self):
        # alături de colectare nu e „a doua colectare”, iar colectarea rămâne păzită
        clip = self._rulare_pe_clip()
        self.assertTrue(clip)
        self.porneste_fals("normal")
        p = self.paznic(prag_stare=30)
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(numara_colectari(self.procese()), 1)
        for x in clip:
            self.assertTrue(x.is_running())

    def test_rularea_pe_clip_nu_e_luata_drept_colectare(self):
        # singură: nu se oprește și nu se pornește nimic peste ea; scrie în aceleași fișiere ca o colectare
        clip = self._rulare_pe_clip()
        p = self.paznic()
        self.assertEqual(p.pas(), "nestiut")
        self.assertEqual(self.porniri(), [])
        for x in clip:
            self.assertTrue(x.is_running())
        self.assertEqual(self.flushuri(), [])
        for x in clip:
            x.kill()
        psutil.wait_procs(clip, timeout=10)
        self.assertEqual(p.pas(), "pornit")

    def test_cauta_dupa_cale_nu_dupa_nume(self):
        # aceeași denumire de fișier, în alt dosar; alt program care primește calea noastră ca argument; niciunul nu e atins
        alta = self.d / "alta"
        alta.mkdir()
        (alta / "fals_run_vision.py").write_text(FALS, encoding="utf-8")
        self.porneste_fals("normal", alta / "fals_run_vision.py", alta)
        strain = self.d / "strain.py"
        n = len(list(self.d.glob("strain_pornit_*")))
        porneste_ascuns([sys.executable, str(strain), str(self.d), str(self.fals)], self.d, dict(os.environ),
                        self.d / "m.log", self.d / "m.err")
        self.asteapta(lambda: len(list(self.d.glob("strain_pornit_*"))) > n, "momeala a pornit")
        momeli = self.procese(alta / "fals_run_vision.py") + self.procese(strain)
        self.assertEqual(self.procese(), [])                  # momelile nu se văd ca „procesul nostru”
        self.porneste_fals("blocat")
        vechi = self.pids()
        p = self.paznic()
        self.stare_veche(p)
        self.assertEqual(self.pids() & {x.pid for x in momeli}, set())
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(self.pids() & vechi, set())
        for m in momeli:
            self.assertTrue(m.is_running(), m)
        self.assertEqual(list(alta.glob("flush_*")), [])
        self.assertEqual(list(self.d.glob("strain_ctrlc_*")), [])
        # nici procesele reale nu se văd ca al nostru
        self.assertEqual(self.pids() & set(procese_reale()), set())

    def test_colectarea_reala_se_numara_ca_una_doar_citire(self):
        procese = gaseste_procese(program(comanda_implicita()))
        if not procese:
            self.skipTest("colectarea reală nu rulează")
        self.assertEqual(numara_colectari(procese), 1)
        self.assertLessEqual({p.pid for p in procese}, set(procese_reale()))


class TestRepornirea(Banc):
    def test_proces_mort(self):
        self.porneste_fals("tace")
        for x in self.procese():
            x.kill()
        self.asteapta(lambda: not self.procese(), "procesul a murit")
        ts = citeste_stare(self.d / "state.json")
        p = self.paznic()
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: len(self.porniri()) == 2, "colectarea repornită")
        self.assertEqual(self.porniri()[-1]["mod"], "normal")
        self.assertEqual(numara_colectari(self.procese()), 1)
        self.assertEqual(self.reporniri()[0]["oprire"], iso(ts))
        self.assertIn("procesul lipsește", self.text_paznic())

    def test_proces_mort_se_reporneste_si_cu_camera_oprita(self):
        # run_vision se reconectează singur, dar numai dacă rulează
        p = self.paznic(playlist=f"http://127.0.0.1:{port_inchis()}/mono.m3u8", timeout_playlist=1)
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: len(self.porniri()) == 1, "colectarea a pornit")

    def test_proces_blocat_oprire_curata(self):
        vechi = self.porneste_fals("blocat")
        p = self.paznic()
        self.stare_veche(p)
        t0 = time.time()
        self.assertEqual(p.pas(), "pornit")
        self.assertLess(time.time() - t0, 25)                 # mult sub timpul de oprire forțată (30 s)
        self.assertTrue((self.d / f"flush_{vechi['pid']}").exists(), "Ctrl+C a ajuns, iar colectarea a făcut flush")
        self.assertFalse(psutil.pid_exists(vechi["pid"]))
        self.asteapta(lambda: self.porniri()[-1]["mod"] == "normal", "colectarea repornită")
        self.assertEqual(numara_colectari(self.procese()), 1)
        self.assertIn("proces blocat", self.text_paznic())
        self.assertIn("oprit curat", self.text_paznic())

    def test_proces_surd_oprit_fortat_abia_dupa_timpul_cerut(self):
        vechi = self.porneste_fals("surd")
        p = self.paznic(timp_oprire=1.5)
        self.stare_veche(p)
        t0 = time.time()
        self.assertEqual(p.pas(), "pornit")
        self.assertGreaterEqual(time.time() - t0, 1.5)
        self.assertFalse((self.d / f"flush_{vechi['pid']}").exists())
        self.assertFalse(psutil.pid_exists(vechi["pid"]))
        self.assertEqual(numara_colectari(self.procese()), 1)
        self.assertIn("oprire forțată", self.text_paznic())

    def test_proces_care_nu_poate_fi_oprit_nu_primeste_un_al_doilea(self):
        self.porneste_fals("surd")
        p = self.paznic(timp_oprire=0.2, asteptari=(60,))
        self.stare_veche(p)
        viu = self.procese()
        with mock.patch("romana.vision.paznic.psutil.wait_procs", return_value=([], viu)):
            self.assertEqual(p.pas(), "neoprit")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.reporniri(), [])
        self.assertGreater(p.urmatoarea, p.monoton())

    def test_ctrl_c_merge_si_daca_parintele_il_ignora(self):
        # ignorarea se moștenește: un paznic pornit dintr-un părinte care o are nu trebuie s-o dea mai departe
        k = ctypes.windll.kernel32
        k.SetConsoleCtrlHandler(None, True)
        self.addCleanup(k.SetConsoleCtrlHandler, None, False)
        vechi = self.porneste_fals("blocat")
        self.assertEqual(trimite_ctrl_c([x.pid for x in self.procese()]), 0)
        self.asteapta(lambda: (self.d / f"flush_{vechi['pid']}").exists(), "colectarea a primit Ctrl+C")

    def test_ctrl_c_nu_ajunge_la_straini(self):
        # în consola colectării mai e alt program: nu se trimite nimic, iar oprirea devine forțată, doar pentru colectare
        vechi = self.porneste_fals("cu_strain")
        self.asteapta(lambda: list(self.d.glob("strain_pornit_*")), "străinul a pornit")
        straini = self.procese(self.d / "strain.py")
        self.assertTrue(straini)
        self.assertEqual(trimite_ctrl_c([x.pid for x in self.procese()]), 4)
        p = self.paznic(timp_oprire=0.5)
        self.stare_veche(p)
        self.assertEqual(p.pas(), "pornit")
        self.assertFalse((self.d / f"flush_{vechi['pid']}").exists())
        self.assertEqual(list(self.d.glob("strain_ctrlc_*")), [])
        for s in straini:
            self.assertTrue(s.is_running())
        self.assertIn("consola e împărțită", self.text_paznic())

    def test_fereastra_ascunsa_mediul_si_jurnalele(self):
        p = self.paznic()
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: self.porniri(), "colectarea a pornit")
        r = self.porniri()[-1]
        self.assertEqual(r["fereastra"], 0)
        self.assertEqual(r["pythonpath"], str(ROOT / "src"))
        log = list((self.d / "logs").glob("viziune_*.log"))
        err = list((self.d / "logs").glob("viziune_*.err"))
        self.assertEqual(len(log), 1)
        self.assertEqual(len(err), 1)
        self.assertRegex(log[0].name, r"^viziune_\d{4}-\d\d-\d\d_\d{6}\.log$")
        self.asteapta(lambda: "rând pe stdout" in log[0].read_text(encoding="utf-8"), "ieșirea ajunge în jurnal")

    def test_a_murit_imediat_se_noteaza_de_ce(self):
        p = self.paznic(comanda=self.comanda("moare"))
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: not self.procese(), "procesul a ieșit")
        self.assertEqual(p.pas(), "pornit")
        self.assertRegex(self.text_paznic(), r"procesul lipsește \(ultimele erori: .*eroare de probă\)")

    def test_comanda_care_nu_se_poate_porni(self):
        p = self.paznic(comanda=[str(self.d / "lipsa" / "python.exe"), str(self.fals)], asteptari=(60,))
        self.assertEqual(p.pas(), "nepornit")
        self.assertEqual(self.reporniri(), [])
        self.assertGreater(p.urmatoarea, p.monoton())
        self.assertIn("pornirea a eșuat", self.text_paznic())

    def test_o_stare_din_viitor_nu_strica_randul(self):
        # ceasul s-a dat înapoi după ultima stare: lanțul zilnic respinge un rând cu repornirea înaintea opririi
        self.scrie_stare(time.time() + 3600)
        p = self.paznic(prag_viu=10)                          # și nu trece drept „stare proaspătă”
        self.assertEqual(p.pas(), "pornit")
        r = self.reporniri()[0]
        self.assertLessEqual(datetime.fromisoformat(r["oprire"]), datetime.fromisoformat(r["repornire"]))

    def test_o_stare_din_viitor_nu_ascunde_un_proces_blocat(self):
        self.porneste_fals("blocat")
        self.scrie_stare(time.time() + 3600)
        p = self.paznic()
        self.asteapta(lambda: varsta_semn(time.time(), _pornit_la(self.procese())) > p.s.prag_stare + 0.05,
                      "procesul e vechi")
        self.assertEqual(p.pas(), "pornit")

    def test_varsta_semnului(self):
        self.assertEqual(varsta_semn(1000.0, 990.0, 500.0), 10.0)
        self.assertEqual(varsta_semn(1000.0, 5000.0, 500.0), 500.0)
        self.assertEqual(varsta_semn(1000.0, 1002.0), -2.0)         # scrisă chiar în timpul verificării
        self.assertEqual(varsta_semn(1000.0, 5000.0, 6000.0), float("inf"))
        self.assertEqual(varsta_semn(1000.0, None), float("inf"))
        self.assertEqual(varsta_semn(1000.0, 5000.0, 999.5), 0.5)   # starea din viitor, previzualizarea proaspătă


class TestSemneleDeViata(Banc):
    """Starea poate tăcea și cu colectarea sănătoasă; pragurile sunt cele reale, pe un ceas mutat."""

    def test_semnele_vecine(self):
        stare = self.d / "state.json"
        self.assertEqual(semne_vecine(stare), [])
        for nume, t in (("frame.jpg", 1793000000), ("frame_tmp.jpg", 1793000001), ("state_tmp.json", 1793000002)):
            (self.d / nume).write_bytes(b"x")
            os.utime(self.d / nume, (t, t))
        self.assertEqual(sorted(semne_vecine(stare)), [1793000000, 1793000001, 1793000002])
        (self.d / "frame_tmp.jpg").unlink()
        self.assertEqual(sorted(semne_vecine(stare)), [1793000000, 1793000002])

    def test_falsul_tace_ca_run_vision_dupa_ceasul_dat_inapoi(self):
        # martorul: fără logica `last_live`, testele de mai jos n-ar dovedi nimic
        self.colectare_veche()
        self.asteapta(lambda: (self.d / "frame.jpg").exists(), "primul cadru")
        self.muta_ceasul(-20)
        time.sleep(0.2)
        ts, cadru = citeste_stare(self.d / "state.json"), (self.d / "frame.jpg").stat().st_mtime_ns
        self.assertGreater(ts, self.ceas() + 5)
        time.sleep(2.5)                          # mai mult decât pauza normală dintre două scrieri ale stării
        self.assertEqual(citeste_stare(self.d / "state.json"), ts)
        self.assertNotEqual((self.d / "frame.jpg").stat().st_mtime_ns, cadru)

    def test_ceasul_dat_inapoi_nu_opreste_o_colectare_sanatoasa(self):
        p = self.colectare_veche()
        self.asteapta(lambda: (self.d / "frame.jpg").exists(), "primul cadru")
        self.assertEqual(p.pas(), "ok")
        vechi = self.pids()
        for x in (15, 30, 59):                   # de la ≈15 s în sus, starea e „din viitor” și nu mai contează
            self.muta_ceasul(-x)
            time.sleep(0.3)
            self.assertGreater(citeste_stare(self.d / "state.json"), self.ceas() + 5, x)
            self.assertEqual(p.pas(), "ok", x)
        self.assertEqual(self.pids(), vechi)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(self.camera.citiri, 0)  # previzualizarea e proaspătă: playlistul nici nu se citește

    def test_stare_tinuta_deschisa_nu_opreste_colectarea(self):
        # `replace` eșuează în tăcere cât timp cineva ține starea deschisă, iar colectarea merge mai departe
        p = self.colectare_veche()
        self.asteapta(lambda: (self.d / "frame.jpg").exists(), "primul cadru")
        self.assertEqual(p.pas(), "ok")
        vechi = self.pids()
        with open(self.d / "state.json", "rb"):
            ts = citeste_stare(self.d / "state.json")
            self.muta_ceasul(301)
            time.sleep(0.5)
            self.assertEqual(citeste_stare(self.d / "state.json"), ts)
            self.assertEqual(p.pas(), "ok")
        self.assertEqual(self.pids(), vechi)
        self.assertEqual(self.flushuri(), [])

    def test_o_previzualizare_veche_nu_ascunde_un_proces_blocat(self):
        self.porneste_fals("blocat")
        (self.d / "frame.jpg").write_bytes(b"x")
        os.utime(self.d / "frame.jpg", (time.time() - 3600, time.time() - 3600))
        p = self.paznic()
        self.stare_veche(p)
        self.assertEqual(p.pas(), "pornit")


class TestCamera(Banc):
    def test_camera_oprita_fara_repornire(self):
        vechi = self.porneste_fals("blocat")
        p = self.paznic(playlist=f"http://127.0.0.1:{port_inchis()}/mono.m3u8", timeout_playlist=1)
        self.stare_veche(p)
        pids = self.pids()
        self.assertEqual(p.pas(), "camera")
        self.assertEqual(self.pids(), pids)
        self.assertEqual(len(self.porniri()), 1)
        self.assertFalse((self.d / f"flush_{vechi['pid']}").exists())
        self.assertEqual(self.reporniri(), [])
        self.assertIn("playlistul nu răspunde", self.text_paznic())

    def test_playlist_pe_loc_fara_repornire(self):
        self.porneste_fals("blocat")
        self.camera.pe_loc = True
        p = self.paznic()
        self.stare_veche(p)
        self.assertEqual(p.pas(), "camera")
        self.assertEqual(len(self.porniri()), 1)
        self.assertIn("stă pe loc", self.text_paznic())

    def test_playlist_fara_secventa_fara_repornire(self):
        # un playlist gol, ca al unui flux oprit: fără secvență, avansul nu se poate vedea
        self.porneste_fals("blocat")
        self.camera.fara_secventa = True
        self.assertIs(camera_raspunde(self.camera.url, 2, 0.01)[0], False)
        p = self.paznic()
        self.stare_veche(p)
        self.assertEqual(p.pas(), "camera")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])
        self.assertIn("fără secvență", self.text_paznic())

    def test_raspuns_care_nu_e_playlist(self):
        self.camera.html = True
        ok, text = camera_raspunde(self.camera.url, 2, 0.01)
        self.assertFalse(ok)
        self.assertIn("nu e un playlist", text)
        self.camera.html = False
        self.assertTrue(camera_raspunde(self.camera.url, 2, 0.01)[0])

    def test_raspuns_pe_bucati(self):
        self.camera.lent = "bucati"
        self.assertTrue(camera_raspunde(self.camera.url, 5, 0.01)[0])

    def _termenul_tine(self, lent: str) -> str:
        self.camera.lent = lent
        t0 = time.monotonic()
        ok, text = camera_raspunde(self.camera.url, 1, 0.01)
        self.assertIs(ok, False)
        self.assertLess(time.monotonic() - t0, 5)
        return text

    def test_un_corp_care_picura_nu_tine_verificarile_pe_loc(self):
        self.assertIn("nu s-a încheiat", self._termenul_tine("corp"))

    def test_niste_antete_care_pica_nu_tin_verificarile_pe_loc(self):
        self.assertIn("nu s-a încheiat", self._termenul_tine("antet"))

    def test_un_raspuns_prea_mare_se_abandoneaza(self):
        self.camera.lent = "urias"
        with self.assertRaisesRegex(ValueError, "nu e un playlist"):
            secventa_playlist(self.camera.url, 20)

    def test_url_necunoscut_nu_lasa_procesul_blocat(self):
        # „nu știu” nu înseamnă „camera nu răspunde”: fără URL, un proces blocat ar rămâne așa până la capătul rulării
        self.assertIsNone(camera_raspunde(None, 2, 0.01)[0])
        vechi = self.porneste_fals("blocat")
        p = self.paznic(playlist=None)
        self.stare_veche(p)
        self.assertEqual(p.pas(), "pornit")
        self.assertTrue((self.d / f"flush_{vechi['pid']}").exists())
        self.assertIn("nu pot deosebi o pană", self.text_paznic())
        self.assertNotIn("se reconectează singur", self.text_paznic())

    def test_camera_revine_iar_procesul_se_reface_singur(self):
        self.porneste_fals("blocat")
        p = self.paznic(playlist=f"http://127.0.0.1:{port_inchis()}/mono.m3u8", timeout_playlist=1, rabdare_camera=60)
        self.stare_veche(p)
        self.assertEqual(p.pas(), "camera")
        p.s.playlist = self.camera.url                # camera revine
        self.assertEqual(p.pas(), "camera")           # are răgaz să se refacă singur
        self.assertIn("îi mai las", self.text_paznic())
        (self.d / "revino").touch()
        ts = citeste_stare(p.s.stare)
        self.asteapta(lambda: citeste_stare(p.s.stare) != ts, "starea a revenit")
        p.s.prag_stare = 5                            # un calculator încărcat poate întârzia un cadru cu mai mult de 0,5 s
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(len(self.porniri()), 1)
        self.assertIsNone(p.camera_buna_din)

    def test_camera_revine_dar_procesul_ramane_blocat(self):
        self.porneste_fals("blocat")
        p = self.paznic(playlist=f"http://127.0.0.1:{port_inchis()}/mono.m3u8", timeout_playlist=1, rabdare_camera=3)
        self.stare_veche(p)
        self.assertEqual(p.pas(), "camera")
        p.s.playlist = self.camera.url
        self.assertEqual(p.pas(), "camera")
        time.sleep(3.1)
        self.assertEqual(p.pas(), "pornit")

    def test_starea_se_reface_chiar_in_timpul_citirii_playlistului(self):
        self.porneste_fals("blocat")
        p = self.paznic()
        self.stare_veche(p)

        def camera_si_starea_revin(*a):
            self.scrie_stare(time.time())
            return True, "playlistul răspunde"
        with mock.patch("romana.vision.paznic.camera_raspunde", side_effect=camera_si_starea_revin):
            self.assertEqual(p.pas(), "revenit")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])

    # ------------------------------------------------------------------ cât timp a fost văzută bună (pragurile reale)
    def test_camera_buna_abia_la_prima_verificare_peste_prag(self):
        # paznicul tocmai a pornit, deci camera n-a fost văzută căzută; colectarea se reface peste 30 s, singură
        p = self.colectare_veche("blocat")
        ts = citeste_stare(p.s.stare)
        self.la_varsta(301, ts)
        self.assertEqual(p.pas(), "camera")
        (self.d / "revino").touch()
        self.asteapta(lambda: citeste_stare(p.s.stare) != ts, "starea a revenit")
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(self.reporniri(), [])

    def test_pana_incheiata_chiar_inaintea_pragului(self):
        # 290 s fără cameră; reconectarea mai cere 33–73 s (§ 4.6), deci prima verificare peste prag o prinde din urmă
        p = self.colectare_veche("blocat")
        ts = citeste_stare(p.s.stare)
        self.camera.oprita = True
        rez = []
        for t in (61, 121):
            self.la_varsta(t, ts)
            rez.append(p.pas())
        self.assertEqual(self.camera.citiri, 0)       # sub 3 minute, playlistul nici nu se citește
        for t in (181, 241):
            self.la_varsta(t, ts)
            rez.append(p.pas())
        self.assertEqual(self.camera.citiri, 2)
        self.camera.oprita = False
        self.la_varsta(302, ts)
        rez.append(p.pas())
        self.assertEqual(rez, ["ok", "ok", "ok", "ok", "camera"])
        (self.d / "revino").touch()
        self.asteapta(lambda: citeste_stare(p.s.stare) != ts, "starea a revenit")
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(self.reporniri(), [])

    def test_camera_cazuta_la_ultima_citire_ia_rabdarea_de_la_capat(self):
        p = self.colectare_veche("blocat")
        ts = citeste_stare(p.s.stare)
        rez = []
        for t, oprita in ((181, False), (241, True), (302, False), (362, False), (423, False)):
            self.camera.oprita = oprita
            self.la_varsta(t, ts)
            rez.append(p.pas())
        self.assertEqual(rez, ["ok", "ok", "camera", "camera", "pornit"])

    def test_proces_blocat_cu_camera_buna_se_reporneste_tot_la_5_minute(self):
        # martorul: playlistul citit de la 3 minute lasă la 5 minute cele 2 minute cerute, deci repornirea nu întârzie
        p = self.colectare_veche("blocat")
        vechi = self.porniri()[0]
        ts = citeste_stare(p.s.stare)
        rez = []
        for t in (61, 121, 181, 241, 302):
            self.la_varsta(t, ts)
            rez.append(p.pas())
        self.assertEqual(rez, ["ok", "ok", "ok", "ok", "pornit"])
        self.assertTrue((self.d / f"flush_{vechi['pid']}").exists())
        self.assertEqual(self.reporniri()[0]["oprire"], iso(ts))


class TestOprireaAnuntata(Banc):
    def test_proces_mort_nu_se_reporneste(self):
        (self.d / "fara_repornire").touch()
        p = self.paznic()
        self.assertEqual(p.pas(), "anuntata")
        self.assertEqual(self.porniri(), [])
        self.assertIn("oprire anunțată", self.text_paznic())
        (self.d / "fara_repornire").unlink()
        self.assertEqual(p.pas(), "pornit")

    def test_stare_veche_nu_se_opreste(self):
        vechi = self.porneste_fals("blocat")
        (self.d / "fara_repornire").touch()
        p = self.paznic()
        self.stare_veche(p)
        pids = self.pids()
        self.assertEqual(p.pas(), "anuntata")
        self.assertEqual(self.pids(), pids)
        self.assertFalse((self.d / f"flush_{vechi['pid']}").exists())

    def test_anuntata_in_timpul_repornirii(self):
        p = self.paznic()
        with mock.patch.object(Paznic, "_verifica_jurnalele", side_effect=lambda *a: (self.d / "fara_repornire").touch()):
            self.assertEqual(p.pas(), "anuntata")
        self.assertEqual(self.porniri(), [])
        self.assertEqual(self.reporniri(), [])

    def test_anuntata_in_timpul_citirii_playlistului(self):
        # hotărârea s-a luat deja, dar citirea durează 8–28 s: oprirea anunțată are ultimul cuvânt
        self.porneste_fals("blocat")
        p = self.paznic()
        self.stare_veche(p)
        pids = self.pids()

        def camera(*a):
            (self.d / "fara_repornire").touch()
            return True, "playlistul răspunde (probă)"
        with mock.patch("romana.vision.paznic.camera_raspunde", side_effect=camera):
            self.assertEqual(p.pas(), "anuntata")
        self.assertEqual(self.pids(), pids)
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(p.incercari, 0)
        self.assertEqual(self.reporniri(), [])

    def test_repornita_de_mana_in_timpul_citirii_playlistului(self):
        # noua colectare, care își încarcă modelul, încă fără nicio stare scrisă, nu primește Ctrl+C-ul celei vechi
        self.porneste_fals("blocat")
        p = self.paznic()
        self.stare_veche(p)
        noua = []

        def camera(*a):
            for x in self.procese():
                x.kill()
            self.asteapta(lambda: not self.procese(), "cea veche a murit")
            noua.append(self.porneste_fals("mut"))
            return True, "playlistul răspunde (probă)"
        with mock.patch("romana.vision.paznic.camera_raspunde", side_effect=camera):
            self.assertEqual(p.pas(), "schimbat")
        self.assertTrue(psutil.pid_exists(noua[0]["pid"]))
        self.assertEqual(self.flushuri(), [])
        self.assertEqual(p.incercari, 0)
        self.assertEqual(self.reporniri(), [])
        self.assertIn("s-au schimbat", self.text_paznic())


class TestAsteptarile(Banc):
    def _1_2_apoi_5_minute(self, verificari: int) -> None:
        acum = [time.time()]
        t0 = acum[0]
        p = Paznic(self.setari(comanda=self.comanda("moare"), asteptari=(60, 120, 300), verificari_lipsa=verificari),
                   ceas=lambda: acum[0])
        porniri = 0
        pasi = ((0, "pornit"), (59, "asteapta"), (60, "pornit"), (179, "asteapta"), (180, "pornit"),
                (479, "asteapta"), (480, "pornit"), (779, "asteapta"), (780, "pornit"))
        for dt, asteptat in (((-60, "lipsa"),) if verificari > 1 else ()) + pasi:
            self.asteapta(lambda: not self.procese(), "procesul fals a ieșit")
            acum[0] = t0 + dt
            self.assertEqual(p.pas(), asteptat, f"la {dt} s")
            if asteptat == "pornit":
                porniri += 1
                self.asteapta(lambda: len(self.porniri()) == porniri, "pornirea s-a făcut")
        self.assertEqual(len(self.porniri()), 5)
        self.assertEqual(p.incercari, 5)

    def test_1_2_apoi_5_minute(self):
        self._1_2_apoi_5_minute(1)

    def test_o_verificare_in_plus_nu_lungeste_asteptarile(self):
        self._1_2_apoi_5_minute(2)

    def test_dupa_o_oprire_pornirea_nu_mai_asteapta_a_doua_verificare(self):
        # procesul blocat l-a oprit chiar paznicul; dacă pornirea eșuează, o nouă încercare vine la 1 minut
        self.porneste_fals("blocat")
        p = self.paznic(verificari_lipsa=2)
        self.stare_veche(p)
        with mock.patch("romana.vision.paznic.porneste_ascuns", side_effect=OSError("de probă")):
            self.assertEqual(p.pas(), "nepornit")
            self.assertEqual(p.pas(), "nepornit")

    def test_o_perioada_stabila_le_ia_de_la_capat(self):
        p = self.paznic(stabil=0.5, asteptari=(60, 120, 300), prag_stare=30)
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(p.incercari, 1)
        self.assertGreater(p.urmatoarea, p.monoton())
        self.asteapta(lambda: citeste_stare(p.s.stare) is not None, "starea a apărut")
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(p.incercari, 1)              # încă nu e stabilă
        time.sleep(0.6)
        self.assertEqual(p.pas(), "ok")
        self.assertEqual((p.incercari, p.urmatoarea), (0, 0.0))

    def test_asteptarea_merge_pe_ceasul_monoton(self):
        # ceasul sistemului dat înapoi cu o oră nu lungește cu o oră așteptarea de 1 minut
        ceas, mono = [time.time()], [1000.0]
        p = Paznic(self.setari(comanda=self.comanda("moare"), asteptari=(60,)), ceas=lambda: ceas[0],
                   monoton=lambda: mono[0])
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: len(self.porniri()) == 1, "pornirea s-a făcut")
        self.asteapta(lambda: not self.procese(), "procesul fals a ieșit")
        ceas[0] -= 3600
        mono[0] += 59
        self.assertEqual(p.pas(), "asteapta")
        mono[0] += 1
        self.assertEqual(p.pas(), "pornit")


class Gata(Exception):
    pass


class TestTrezirea(Banc):
    def _ruleaza(self, salt: float) -> list[str]:
        """Bucla pe un ceas fals: procesul lipsește de la primul somn încolo, somn care include și un salt de ceas."""
        acum = [time.time()]
        rez, flag = [], self.d / "fara_repornire"
        flag.touch()
        salturi = [salt]

        class P(Paznic):
            def pas(self):
                rez.append(super().pas())
                return rez[-1]

        def dormi(s):
            if rez[-1] == "pornit":
                raise Gata
            acum[0] += s
            if salturi:
                acum[0] += salturi.pop()
                flag.unlink()

        p = P(self.setari(comanda=self.comanda("tace"), pas=60, prag_salt=60, pauza_trezire=120), ceas=lambda: acum[0],
              dormi=dormi)
        with self.assertRaises(Gata):
            p.bucla(acum[0] + 10 ** 6)
        return rez

    def test_trezire_din_somn(self):
        self.assertEqual(self._ruleaza(3600), ["anuntata", "trezire", "trezire", "pornit"])
        self.assertIn("trezire din somn sau salt de ceas", self.text_paznic())

    def test_ceasul_dat_inapoi(self):
        self.assertEqual(self._ruleaza(-7200), ["anuntata", "trezire", "trezire", "pornit"])

    def test_o_abatere_mica_nu_e_trezire(self):
        self.assertEqual(self._ruleaza(30), ["anuntata", "pornit"])

    def test_ceasul_dat_inapoi_dupa_o_incercare(self):
        # 2 ore pe ceasul sistemului, cu procesul mort: repornirea vine tot după cele 2 minute de după salt
        ceas, mono = [time.time()], [1000.0]
        rez, salt = [], [-7200]

        class P(Paznic):
            def pas(self):
                rez.append(super().pas())
                return rez[-1]

        def dormi(s):
            if rez.count("pornit") == 2:
                raise Gata
            self.asteapta(lambda: not self.procese(), "procesul fals a ieșit")
            ceas[0] += s + (salt.pop() if salt else 0)
            mono[0] += s

        p = P(self.setari(comanda=self.comanda("moare"), asteptari=(60, 120, 300), pas=60), ceas=lambda: ceas[0],
              monoton=lambda: mono[0], dormi=dormi)
        with self.assertRaises(Gata):
            p.bucla(ceas[0] + 10 ** 7)
        self.assertEqual(rez, ["pornit", "trezire", "trezire", "pornit"])

    def test_trezire_cu_reteaua_inca_jos(self):
        # somn de o oră; rețeaua revine la 2 minute de la trezire, iar colectarea se reface peste încă o verificare
        p0 = self.colectare_veche("blocat")
        rez, n = [], [0]
        ts = citeste_stare(p0.s.stare)

        class P(Paznic):
            def pas(self):
                rez.append(super().pas())
                return rez[-1]

        def dormi(s):
            n[0] += 1
            if n[0] == 1:
                self.camera.oprita = True
                self.muta_ceasul(3600)
            elif n[0] == 3:
                self.camera.oprita = False
            elif n[0] == 4:
                (self.d / "revino").touch()
                self.asteapta(lambda: citeste_stare(p0.s.stare) != ts, "starea a revenit")
            elif n[0] == 5:
                raise Gata
            self.muta_ceasul(s)

        p = P(p0.s, ceas=self.ceas, dormi=dormi)
        with self.assertRaises(Gata):
            p.bucla(self.ceas() + 10 ** 7)
        self.assertEqual(rez, ["ok", "trezire", "trezire", "camera", "ok"])
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])

    def test_camera_buna_de_dinaintea_somnului_nu_se_mai_socoteste(self):
        # nici procesul văzut lipsind înainte: după somn, ce s-a văzut înainte nu mai spune nimic
        p0 = self.colectare_veche("blocat")
        ts = citeste_stare(p0.s.stare)
        self.la_varsta(181, ts)
        rez, salt = [], [3600]

        class P(Paznic):
            def pas(self):
                rez.append(super().pas())
                return rez[-1]

        def dormi(s):
            if len(rez) == 4:
                raise Gata
            self.muta_ceasul(s + (salt.pop() if salt else 0))

        p = P(p0.s, ceas=self.ceas, dormi=dormi)
        with self.assertRaises(Gata):
            p.bucla(self.ceas() + 10 ** 7)
        self.assertEqual(rez, ["ok", "trezire", "trezire", "camera"])
        self.assertEqual(len(self.porniri()), 1)
        self.assertEqual(self.flushuri(), [])

    def test_o_eroare_nu_opreste_bucla(self):
        p = self.paznic(pas=0.01)
        rez = iter([RuntimeError("eroare de probă"), "ok"])

        def pas():
            r = next(rez, "ok")
            if isinstance(r, Exception):
                raise r
            return r
        with mock.patch.object(p, "pas", side_effect=pas) as apeluri:
            p.bucla(time.time() + 0.2)
        self.assertGreater(apeluri.call_count, 1)
        self.assertIn("eroare în verificare", self.text_paznic())
        self.assertIn("paznic încheiat", self.text_paznic())


class TestReporniriCSV(Banc):
    def test_repornirea_e_prima_traiectorie_noua(self):
        self.scrie_stare(time.time() - 60)
        ts = citeste_stare(self.d / "state.json")
        p = self.paznic(prag_stare=30)
        self.assertEqual(p.pas(), "pornit")
        pornit_la = p.urmarire["t"]
        self.assertEqual(self.reporniri(), [{"oprire": iso(ts), "repornire": iso(pornit_la)}])
        f = self.d / "jurnale" / f"traiectorii_{date.today().isoformat()}.jsonl.gz"
        self.asteapta(lambda: p.pas() == "ok" and p.urmarire is None, "prima traiectorie nouă s-a citit")
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            prima = json.loads(fh.readline())["t0"]
        # doar antetul și un singur rând; capul de coloane e citit de lanțul zilnic
        self.assertEqual(self.reporniri(), [{"oprire": iso(ts), "repornire": iso(prima)}])
        rand0 = (self.d / "logs" / f"reporniri_{date.today().isoformat()}.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(rand0, "oprire,repornire")
        self.assertIn("jurnalul zilei crește", self.text_paznic())
        self.assertIsNone(p.urmarire)

    def test_fara_traiectorii_ramane_momentul_pornirii(self):
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"), timp_crestere=0.2, prag_stare=30)
        self.assertEqual(p.pas(), "pornit")
        pornit_la = p.urmarire["t"]
        self.asteapta(lambda: citeste_stare(p.s.stare) > pornit_la, "starea nouă")
        time.sleep(0.25)
        self.assertEqual(p.pas(), "ok")
        self.assertEqual(self.reporniri()[0]["repornire"], iso(pornit_la))
        self.assertIn("ATENȚIE: jurnalul zilei nu a crescut", self.text_paznic())

    def test_gol_peste_miezul_noptii(self):
        lg = self.d / "logs"
        o, r = datetime(2026, 11, 1, 23, 50, 7).timestamp(), datetime(2026, 11, 2, 0, 10, 9).timestamp()
        scrie_repornire(lg, o, r)
        for zi in ("2026-11-01", "2026-11-02"):
            with open(lg / f"reporniri_{zi}.csv", newline="", encoding="utf-8") as fh:
                self.assertEqual(list(csv.DictReader(fh)),
                                 [{"oprire": "2026-11-01T23:50:07", "repornire": "2026-11-02T00:10:09"}])
        scrie_repornire(lg, o, r + 30, vechi=r)
        for zi in ("2026-11-01", "2026-11-02"):
            self.assertIn("2026-11-02T00:10:39", (lg / f"reporniri_{zi}.csv").read_text(encoding="utf-8"))
            self.assertNotIn("2026-11-02T00:10:09", (lg / f"reporniri_{zi}.csv").read_text(encoding="utf-8"))
        self.assertEqual(sorted(x.name for x in lg.iterdir()), ["reporniri_2026-11-01.csv", "reporniri_2026-11-02.csv"])

    def test_o_eroare_la_urmarire_nu_impiedica_hotararile(self):
        p = self.paznic(prag_stare=30)
        self.assertEqual(p.pas(), "pornit")
        self.asteapta(lambda: citeste_stare(p.s.stare) is not None, "starea a apărut")
        with mock.patch.object(p, "_urmareste_jurnalul", side_effect=RuntimeError("eroare de probă")):
            self.assertEqual(p.pas(), "ok")
        self.assertIn("eroare la urmărirea jurnalului", self.text_paznic())

    def test_fisier_deschis_altundeva_se_scrie_la_pasul_urmator(self):
        self.scrie_stare(time.time() - 60)
        p = self.paznic(prag_stare=30)
        with mock.patch("romana.vision.paznic.scrie_repornire", side_effect=PermissionError("deschis în Excel")):
            self.assertEqual(p.pas(), "pornit")
        self.assertEqual(self.reporniri(), [])
        self.assertEqual(len(p.restante), 1)
        p.pas()
        self.assertEqual(len(self.reporniri()), 1)
        self.assertEqual(p.restante, [])

    def test_lantul_zilnic_citeste_randul(self):
        # formatul citit de `romana.lant_zilnic`: oprire 08:33, repornire 08:46 → 08:30-09:00 (§ 4.6)
        try:
            import romana.lant_zilnic as lant
        except ImportError:
            self.skipTest("romana.lant_zilnic nu e disponibil")
        lg = self.d / "logs"
        scrie_repornire(lg, datetime(2026, 10, 29, 8, 33).timestamp(), datetime(2026, 10, 29, 8, 46).timestamp())
        with mock.patch.object(lant, "DIR_LOGURI", lg):
            self.assertEqual(lant.intervale_reporniri("2026-10-29", note=self.fail), [(8 * 60 + 30, 9 * 60)])


class TestPrimaTraiectorie(unittest.TestCase):
    def test_cititorul(self):
        membri = [membru(1000.0 + i) for i in range(4)]
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "j.gz"
            f.write_bytes(b"".join(membri) + membri[0][:10])       # un ultim membru în curs de scriere
            self.assertEqual(prima_traiectorie(f, 0), 1000.0)
            self.assertEqual(prima_traiectorie(f, len(membri[0])), 1001.0)
            self.assertIsNone(prima_traiectorie(f, f.stat().st_size))
            self.assertEqual(prima_traiectorie(f, 5), 1001.0)       # în mijlocul unui membru: se caută antetul următor
            f.write_bytes(membri[0][:15])
            self.assertIsNone(prima_traiectorie(f, 0))
            self.assertIsNone(prima_traiectorie(Path(d) / "lipsa.gz", 0))


class Cadere(BaseException):
    """O cădere a paznicului (curent, kill): nimic din paznic n-o prinde."""


class TestJurnalul(Banc):
    def jurnal(self, zi: date | None = None) -> Path:
        d = self.d / "jurnale"
        d.mkdir(exist_ok=True)
        return d / f"traiectorii_{(zi or date.today()).isoformat()}.jsonl.gz"

    def verifica_real(self, f: Path) -> dict:
        from romana.vision.repara import verifica
        return verifica(f)

    def test_jurnal_intreg_ramane_cum_e(self):
        f = self.jurnal()
        date_vechi = b"".join(membru(1000.0 + i) for i in range(5))
        f.write_bytes(date_vechi)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(f.read_bytes(), date_vechi)
        self.assertEqual([x.name for x in f.parent.iterdir()], [f.name])
        self.assertIn(": întreg (", self.text_paznic())

    def _reparat(self, membri_stricati: bytes, membri_buni: int) -> None:
        f = self.jurnal()
        f.write_bytes(membri_stricati)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        self.assertEqual(p.pas(), "pornit")
        pastrate = list(f.parent.glob(f"{f.name}.stricat_*"))
        self.assertEqual(len(pastrate), 1)
        self.assertEqual(pastrate[0].read_bytes(), membri_stricati)          # originalul, neatins
        self.assertEqual(list(f.parent.glob(f"{f.name}.reparat_*")), [])     # copia i-a luat locul
        r = self.verifica_real(f)
        self.assertEqual((r["membri"], r["stricati"], r["in_scriere"]), (membri_buni, 0, 0))
        self.assertIn("reparat", self.text_paznic())
        self.asteapta(lambda: len(self.porniri()) == 1, "pornirea a mers mai departe")

    def test_membru_stricat_la_mijloc(self):
        m = [membru(1000.0 + i) for i in range(4)]
        self._reparat(m[0] + m[1] + m[2][:len(m[2]) // 2] + m[3], 3)

    def test_ultimul_membru_trunchiat(self):
        # `repara` îl vede ca „în scriere” și iese cu 0; cu colectarea oprită, nu se mai încheie niciodată
        m = [membru(1000.0 + i) for i in range(3)]
        self._reparat(m[0] + m[1] + m[2][:len(m[2]) // 2], 2)

    def test_verificarea_esuata_nu_opreste_pornirea(self):
        f = self.jurnal()
        date_vechi = membru(1000.0)
        f.write_bytes(date_vechi)
        self.scrie_stare(time.time() - 60)
        rau = self.d / "cade.py"
        rau.write_text("import sys\nprint('usage: nu')\nsys.exit(2)\n", encoding="utf-8")
        for comanda in ([sys.executable, str(rau)], [str(self.d / "lipsa" / "python.exe")]):
            p = self.paznic(comanda=self.comanda("moare"), comanda_repara=comanda)
            self.assertEqual(p.pas(), "pornit")
            self.asteapta(lambda: not self.procese(), "procesul fals a ieșit")
        self.assertEqual(f.read_bytes(), date_vechi)
        self.assertEqual([x.name for x in f.parent.iterdir()], [f.name])
        self.assertIn("verificarea a eșuat", self.text_paznic())

    def test_o_eroare_neasteptata_la_verificare_nu_opreste_pornirea(self):
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        with mock.patch.object(Paznic, "_verifica_jurnalele", side_effect=RuntimeError("eroare de probă")):
            self.assertEqual(p.pas(), "pornit")
        self.assertIn("verificarea jurnalelor a eșuat", self.text_paznic())

    def test_copia_care_nu_trece_verificarea_nu_ia_locul_jurnalului(self):
        f = self.jurnal()
        stricat = membru(1000.0) + membru(1001.0)[:10] + membru(1002.0)
        f.write_bytes(stricat)
        self.scrie_stare(time.time() - 60)
        rau = self.d / "repara_rau.py"
        rau.write_text(REPARA_RAU, encoding="utf-8")
        p = self.paznic(comanda=self.comanda("tace"), comanda_repara=[sys.executable, str(rau)])
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(f.read_bytes(), stricat)
        copii = list(f.parent.glob(f"{f.name}.reparat_*"))
        self.assertEqual(len(copii), 1)                                      # nimic șters
        self.assertEqual(copii[0].read_bytes(), b"copie proasta")
        self.assertIn("nu trece verificarea", self.text_paznic())

    def test_originalul_nu_se_poate_pastra(self):
        f = self.jurnal()
        stricat = membru(1000.0) + membru(1001.0)[:10] + membru(1002.0)
        f.write_bytes(stricat)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        with mock.patch("romana.vision.paznic.os.link", side_effect=PermissionError("citit de altcineva")):
            self.assertEqual(p.pas(), "pornit")
        self.assertEqual(f.read_bytes(), stricat)
        self.assertEqual(len(list(f.parent.glob(f"{f.name}.reparat_*"))), 1)
        self.assertIn("nu pot păstra originalul", self.text_paznic())

    def test_copia_nu_poate_lua_locul_jurnalul_ramane_cum_e(self):
        f = self.jurnal()
        stricat = membru(1000.0) + membru(1001.0)[:10] + membru(1002.0)
        f.write_bytes(stricat)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        with mock.patch("romana.vision.paznic._inlocuieste", side_effect=PermissionError("blocat")):
            self.assertEqual(p.pas(), "pornit")
        self.assertEqual(f.read_bytes(), stricat)
        self.assertEqual(list(f.parent.glob(f"{f.name}.stricat_*")), [])     # al doilea nume, retras; datele sunt în jurnal
        self.assertEqual(len(list(f.parent.glob(f"{f.name}.reparat_*"))), 1)
        self.assertIn("nu i-a putut lua locul", self.text_paznic())

    def test_o_cadere_in_timpul_reparatiei_nu_lasa_ziua_fara_jurnal(self):
        # între „originalul păstrat” și „copia îi ia locul”: două redenumiri ar fi lăsat ziua fără jurnal, iar colectarea
        # următoare ar fi început unul nou, în tăcere
        f = self.jurnal()
        stricat = b"".join(membru(1000.0 + i) for i in range(5)) + membru(1005.0)[:10]
        f.write_bytes(stricat)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        with mock.patch("romana.vision.paznic._inlocuieste", side_effect=Cadere), self.assertRaises(Cadere):
            p.pas()
        self.assertEqual(f.read_bytes(), stricat)
        self.assertEqual(self.porniri(), [])
        time.sleep(1.1)                                                      # numele copiilor au ora la secundă
        urmatorul = self.paznic(comanda=self.comanda("tace"))
        self.assertEqual(urmatorul.pas(), "pornit")
        r = self.verifica_real(f)
        self.assertEqual((r["membri"], r["stricati"], r["in_scriere"]), (5, 0, 0))
        self.assertTrue(all(x.read_bytes() == stricat for x in f.parent.glob(f"{f.name}.stricat_*")))
        self.assertNotIn("ATENȚIE", self.text_paznic())

    def test_jurnal_lipsa_cu_copii_ramase_se_semnaleaza(self):
        f = self.jurnal()
        ramas = f.with_name(f"{f.name}.stricat_120000")
        ramas.write_bytes(membru(1000.0))
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        self.assertEqual(p.pas(), "pornit")
        self.assertRegex(self.text_paznic(), rf"ATENȚIE: jurnalul zilei .* lipsește, dar există {re.escape(ramas.name)}")
        self.assertEqual(ramas.read_bytes(), membru(1000.0))

    def test_jurnal_lipsa_fara_copii_nu_se_semnaleaza(self):
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("tace"))
        self.assertEqual(p.pas(), "pornit")
        self.assertNotIn("ATENȚIE", self.text_paznic())

    def test_jurnalul_de_ieri_doar_daca_a_fost_scris_in_jurul_opririi(self):
        ieri = self.jurnal(date.today() - timedelta(days=1))
        stricat = membru(1000.0) + membru(1001.0)[:10]
        ieri.write_bytes(stricat)
        self.scrie_stare(time.time() - 60)
        p = self.paznic(comanda=self.comanda("moare"))
        os.utime(ieri, (time.time() - 7200, time.time() - 7200))            # scris cu mult înaintea opririi: rămâne
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(ieri.read_bytes(), stricat)
        self.asteapta(lambda: not self.procese(), "procesul fals a ieșit")
        os.utime(ieri, None)                                                 # scris chiar atunci: se repară
        self.assertEqual(p.pas(), "pornit")
        self.assertEqual(self.verifica_real(ieri)["in_scriere"], 0)
        self.assertEqual(len(list(ieri.parent.glob(f"{ieri.name}.stricat_*"))), 1)

    def test_inlocuirea_mai_incearca(self):
        a, b = self.d / "a.txt", self.d / "b.txt"
        a.write_text("nou")
        b.write_text("vechi")
        fh = open(b, "rb")                                                   # citit de altcineva
        with self.assertRaises(PermissionError):
            _inlocuieste(a, b, incercari=1)
        self.assertEqual(b.read_text(), "vechi")
        threading.Timer(0.3, fh.close).start()
        _inlocuieste(a, b, incercari=5)
        self.assertEqual(b.read_text(), "nou")
        self.assertFalse(a.exists())


class TestLiniaDeComanda(Banc):
    def argumente(self, comanda: list[str] | None = None) -> list[str]:
        return ["--comanda", subprocess.list2cmdline(comanda or self.comanda()),
                "--comanda-repara", subprocess.list2cmdline([sys.executable, "-m", "romana.vision.repara"]),
                "--stare", str(self.d / "state.json"), "--fara-repornire", str(self.d / "fara_repornire"),
                "--jurnale", str(self.d / "jurnale"), "--loguri", str(self.d / "logs"), "--cwd", str(self.d),
                "--playlist", self.camera.url, "--pas", "0.1", "--prag-stare", "30", "--prag-camera", "20", "--prag-viu", "0",
                "--asteptari", "0.5", "--pauza-playlist", "0.05", "--timeout-playlist", "2"]

    def lanseaza(self, *extra: str, nume: str = "p") -> subprocess.Popen:
        with open(self.d / f"{nume}.txt", "wb") as fo:
            return subprocess.Popen([sys.executable, "-m", "romana.vision.paznic", *self.argumente(), *extra],
                                    env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, cwd=self.d, stdout=fo,
                                    stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

    @staticmethod
    def peste(secunde: float) -> str:
        return datetime.fromtimestamp(time.time() + secunde).strftime("%Y-%m-%d %H:%M:%S")

    def test_capat_la_capat(self):
        unu = self.lanseaza("--pana-la", self.peste(60))
        self.addCleanup(unu.wait)
        self.addCleanup(unu.kill)
        self.asteapta(lambda: len(self.porniri()) == 1, "paznicul a pornit colectarea care lipsea")
        self.asteapta(lambda: self.procese(), "procesele colectării")
        time.sleep(1.1)                                          # rândurile din CSV au ora la secundă: să difere
        for x in self.procese():                                 # colectarea moare
            x.kill()
        self.asteapta(lambda: len(self.porniri()) == 2, "paznicul a repornit-o")
        self.asteapta(lambda: numara_colectari(self.procese()) == 1, "o singură colectare")
        doi = self.lanseaza("--pana-la", self.peste(60), nume="doi")      # al doilea paznic e refuzat
        self.assertEqual(doi.wait(timeout=30), 3)
        self.assertIn("alt paznic", (self.d / "doi.txt").read_text(encoding="utf-8"))
        vii = self.procese()
        # paznicul moare, cu tot arborele lui (ca un proces din fundal la sfârșitul unei sesiuni): colectarea rămâne pornită
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(unu.pid)], capture_output=True, timeout=30)
        unu.wait(timeout=30)
        self.asteapta(lambda: not psutil.pid_exists(unu.pid), "paznicul a ieșit")
        time.sleep(0.3)
        for x in vii:
            self.assertTrue(x.is_running(), "colectarea a murit odată cu paznicul")
        ts = citeste_stare(self.d / "state.json")
        self.asteapta(lambda: citeste_stare(self.d / "state.json") != ts, "colectarea lucrează în continuare")
        trei = self.lanseaza("--pana-la", self.peste(1.5), nume="trei")   # blocarea a dispărut odată cu primul
        self.assertEqual(trei.wait(timeout=30), 0)
        self.assertEqual(len(self.porniri()), 2)                 # colectarea sănătoasă n-a fost atinsă
        self.assertEqual({x.pid for x in self.procese()}, {x.pid for x in vii})
        self.assertIn("paznic încheiat", self.text_paznic())
        self.assertEqual(len(self.reporniri()), 2)

    def test_proba_nu_atinge_nimic(self):
        self.porneste_fals("tace")
        pids = self.pids()
        r = subprocess.run([sys.executable, "-m", "romana.vision.paznic", *self.argumente(), "--proba"], cwd=self.d,
                           env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("colectări: 1", r.stdout)
        self.assertIn("playlistul răspunde", r.stdout)
        self.assertIn("ultimul semn de viață", r.stdout)
        self.assertEqual(self.pids(), pids)
        self.assertEqual(len(self.porniri()), 1)
        self.assertFalse((self.d / "logs").exists())             # nu scrie nimic

    def test_ora_de_sfarsit_nerecunoscuta(self):
        r = subprocess.run([sys.executable, "-m", "romana.vision.paznic", *self.argumente(), "--pana-la", "mâine"],
                           cwd=self.d, env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, capture_output=True,
                           timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.porniri(), [])

    def test_fara_url_iese_cu_eroare(self):
        # la pornire e cineva de față; mai târziu, paznicul n-ar deosebi o pană a camerei de un proces blocat
        args = self.argumente()
        k = args.index("--playlist")
        del args[k:k + 2]
        with mock.patch("romana.vision.paznic.load_json", side_effect=OSError("config necitibil")), \
                mock.patch("sys.stderr", io.StringIO()) as err, self.assertRaises(SystemExit) as iesire:
            main([*args, "--pana-la", self.peste(30)])
        self.assertEqual(iesire.exception.code, 2)
        self.assertIn("URL-ul playlistului", err.getvalue())
        self.assertEqual(self.porniri(), [])
        self.assertFalse((self.d / "logs").exists())

    def test_o_iesire_care_nu_se_goleste_nu_opreste_verificarile(self):
        # o conductă pe care n-o citește nimeni (≈4 KB) sau o selecție în consolă: scrierea rămâne blocată, nu verificările
        comanda = [str(self.d / "lipsa" / "python.exe"), str(self.fals)]
        z = subprocess.Popen([sys.executable, "-m", "romana.vision.paznic", *self.argumente(comanda), "--pas", "0.02",
                              "--asteptari", "0", "--verificari-lipsa", "1", "--pana-la", self.peste(12)], cwd=self.d,
                             env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        self.addCleanup(z.stdout.close)
        self.addCleanup(z.wait)
        self.addCleanup(z.kill)
        self.assertEqual(z.wait(timeout=60), 0)                  # se încheie și singur, cu ecranul încă blocat
        text = self.text_paznic()
        self.assertGreater(len(text.encode("utf-8")), 2 * 4096)  # cu scrierea în firul verificărilor, se oprea la ≈12 încercări
        self.assertIn("paznic încheiat", text)


class TestNote(Banc):
    def test_un_mesaj_repetat_se_scrie_rar(self):
        acum = [time.time()]
        p = Paznic(self.setari(), ceas=lambda: acum[0])
        p.nota("de probă", "cheie")
        p.nota("de probă", "cheie")
        self.assertEqual(self.text_paznic().count("de probă"), 1)
        acum[0] += 301
        p.nota("de probă", "cheie")
        self.assertEqual(self.text_paznic().count("de probă"), 2)
        self.assertTrue(re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d de probă", self.text_paznic()))

    def test_ecranul_primeste_randurile(self):
        p = self.paznic()
        p.nota("de probă")
        self.assertTrue(goleste_ecranul(5))
        self.assertIn("de probă", sys.stdout.getvalue())

    def test_ecranul_blocat_nu_opreste_verificarile(self):
        liber = threading.Event()
        self.addCleanup(liber.set)

        class Blocat(io.StringIO):
            def write(self, s):
                liber.wait(2)
                return len(s)
        p = self.paznic()
        with mock.patch("sys.stdout", Blocat()):
            t0 = time.monotonic()
            for k in range(50):
                p.nota(f"rând {k}")
            for k in range(1100):                # coada ecranului se umple: rândurile în plus nu mai ajung pe el
                afiseaza("rând peste")
            self.assertLess(time.monotonic() - t0, 10)
            self.assertEqual(self.text_paznic().count("rând "), 50)
            self.assertFalse(goleste_ecranul(0.1))
            liber.set()
            self.assertTrue(goleste_ecranul(30))


if __name__ == "__main__":
    unittest.main()
