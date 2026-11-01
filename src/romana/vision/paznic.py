"""Paznicul colectării (§ 4.6): repornește `run_vision` când procesul moare sau rămâne fără cadre. Veghea
(`romana.vision.veghe`) doar alertează; până acum nimic nu repornea colectarea.

O dată pe minut, paznicul verifică procesul și semnele lui de viață: ora din starea live (outputs/live/state.json, scrisă
de `run_vision` în fiecare secundă în care prelucrează cadre) și datele fișierelor scrise lângă ea (previzualizarea,
rescrisă la fiecare cadru; doar data, imaginea nu se citește). Starea singură poate tăcea și cu colectarea sănătoasă: după
un ceas dat înapoi (o scrie abia când ceasul o ajunge din urmă) sau cât o ține deschisă un cititor. Repornește doar dacă:
  * procesul lipsește, la două verificări la rând; sau
  * ultimul semn de viață e mai vechi de 5 minute, iar playlistul camerei răspunde și avansează de cel puțin 2 minute, în
    același episod (se citește de la 3 minute încolo). Altfel problema e la cameră sau la rețea, iar `run_vision` se
    reconectează singur și mai are nevoie de timp după ce camera revine: paznicul notează și așteaptă.
Nu ia nicio hotărâre:
  * cât timp există outputs/live/fara_repornire (oprire anunțată: fișierul se pune înaintea oricărei opriri voite);
  * 2 minute după o trezire din somn sau un salt mare de ceas;
  * dacă găsește mai multe colectări în același timp (rămân pe seama omului);
  * dacă un proces Python poate fi colectarea, fără să se poată ști (tot pe seama omului): linia de comandă nu se poate
    citi, un `-c` sau un script care pomenește programul, o rulare pe un fișier video (`--source`, cu aceleași fișiere).
Chiar înaintea opririi se mai uită o dată: dacă a apărut fara_repornire sau s-au schimbat procesele, nu oprește nimic.

Repornirea: Ctrl+C în consola ascunsă a colectării (→ `counter.flush()`), forțat abia după 90 s; verificarea jurnalului
zilei cu `romana.vision.repara` (la membri stricați: o copie reparată lângă fișier, verificată, originalul păstrat
sub alt nume, nimic șters); `run_vision` fără fereastră, cu jurnale noi outputs/logs/viziune_<data>_<ora>.log / .err; apoi
se urmărește creșterea jurnalului zilei. Între încercări: 1, 2, apoi 5 minute, pe ceasul monoton, pe care un ceas de sistem
dat înapoi nu le poate lungi. Colectarea are întâietate: o verificare eșuată a jurnalului nu oprește pornirea. Colectarea
pornită nu e copilul paznicului: dacă paznicul moare, ea merge mai departe.

Ce lasă în urmă: outputs/logs/paznic_<zi>.log și outputs/logs/reporniri_<zi>.csv, cu coloanele oprire și repornire, în ora
locală ISO. oprire = ultima dovadă de viață a colectării (`timestamp` din state.json); repornire = prima traiectorie nouă
sau, până se află, momentul pornirii. Lanțul zilnic exclude de acolo sfertul repornirii. Un gol peste miezul nopții apare
în fișierul fiecărei zile atinse.

Procesele se recunosc după programul rulat de interpretor (`-m modul`, cu opțiunile citite ca în interpretor, sau calea
scriptului), nu după numele „python” și nu după un text oarecare din linia de comandă: un PowerShell care doar pomenește
modulul, veghea sau paznicul însuși nu se confundă cu colectarea. Pe Windows, .venv\\Scripts\\python.exe e un lansator: o
colectare apare ca două procese (lansatorul și copilul care lucrează) și se numără ca una. Nu se pornește niciodată a doua.

Se lansează direct (ca mai jos sau din scripts\\2e_paznic.bat), nu dintr-un bash imbricat: oprirea unei sarcini de fundal
a gazdei n-ar ajunge la el (probat). După o oprire voită se verifică, după linia de comandă, că a dispărut.

Toate căile și pragurile se pot înlocui prin parametri, ca să se poată încerca pe un proces de probă (tests/test_paznic.py).
Nu schimbă setări de sistem și nu creează sarcini programate.

Exemple:
  python -m romana.vision.paznic --pana-la "2026-11-08 09:00"
  python -m romana.vision.paznic --proba
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import queue
import re
import shlex
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import zlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import psutil

from romana.common import OUTPUT_DIR, ROOT, TRAJ_RAW_DIR, load_json

LIVE_DIR = OUTPUT_DIR / "live"
LOG_DIR = OUTPUT_DIR / "logs"

CSV_CAP = ["oprire", "repornire"]
REPETARE_NOTA = 300      # s; un mesaj care se repetă se scrie cel mult atât de des
SEMN_DE_VIATA = 3600     # s; cât de des se notează „în regulă”
MARJA_JURNAL = 600       # s; un jurnal mai vechi decât ziua curentă se verifică doar dacă a fost scris în jurul opririi
MARJA_CEAS = 5           # s; o stare scrisă chiar în timpul verificării poate părea puțin „din viitor”
MARIME_PLAYLIST = 1 << 20    # octeți; playlistul real are câțiva KB
COADA_ECRAN = 1000       # rânduri care așteaptă afișarea; peste atât, ecranul rămâne în urmă, nu verificările
PAUZA_NECITITE = 0.2     # s; la pornire, linia de comandă a unui proces poate fi o clipă necitibilă
SEMNE_VECINE = ("frame.jpg", "frame_tmp.jpg", "state_tmp.json")    # scrise de `run_vision` lângă stare
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")

# Ca la oprirea din 29–30.10: Ctrl+C dintr-un proces ajutător atașat la consola țintă; lansatorul din .venv îl ignoră și
# așteaptă procesul real. Ajutorul refuză (cod 4) dacă în consolă mai e cineva în afara proceselor date: semnalul ajunge
# la toată consola și nu trebuie să atingă pe nimeni altcineva.
COD_CTRL_C = """
import ctypes, os, sys, time
k = ctypes.windll.kernel32
k.FreeConsole()
if not k.AttachConsole(int(sys.argv[1])):
    sys.exit(2)
lista = (ctypes.c_ulong * 64)()
n = k.GetConsoleProcessList(lista, 64)
if not 0 < n <= 64 or set(lista[:n]) - {int(x) for x in sys.argv[1:]} - {os.getpid()}:
    k.FreeConsole()
    sys.exit(4)
k.SetConsoleCtrlHandler(None, True)
ok = k.GenerateConsoleCtrlEvent(0, 0)
time.sleep(0.5)
k.FreeConsole()
sys.exit(0 if ok else 3)
"""

# Pornirea printr-un proces ajutător care iese imediat: colectarea nu rămâne copilul paznicului, deci nu moare cu el nici
# dacă acesta e oprit cu tot arborele lui (`taskkill /T`, ca un proces din fundal la sfârșitul unei sesiuni; probat). Jobul
# lansatorului din .venv îi permite să iasă din el. Ignorarea lui Ctrl+C se moștenește de la părinte (probat), iar un
# proces pornit cu ea nu s-ar mai putea opri curat: de aceea se scoate înaintea pornirii.
COD_PORNIRE = """
import ctypes, json, subprocess, sys
z = json.loads(sys.argv[1])
ctypes.windll.kernel32.SetConsoleCtrlHandler(None, False)
si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
si.wShowWindow = subprocess.SW_HIDE
with open(z["log"], "wb") as fo, open(z["err"], "wb") as fe:
    p = subprocess.Popen(z["comanda"], cwd=z["cwd"], stdin=subprocess.DEVNULL, stdout=fo, stderr=fe, startupinfo=si,
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
print(p.pid)
"""


def comanda_implicita() -> list[str]:
    """Comanda din pașii de reluare: lansatorul din .venv, cu `-m romana.vision.run_vision`."""
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    return [str(py if py.exists() else sys.executable), "-m", "romana.vision.run_vision"]


@dataclass
class Setari:
    """Căile și pragurile; implicit cele ale colectării reale, înlocuite în probe și în teste."""
    comanda: list[str] = field(default_factory=comanda_implicita)
    comanda_repara: list[str] = field(default_factory=lambda: [sys.executable, "-m", "romana.vision.repara"])
    stare: Path = LIVE_DIR / "state.json"
    fara_repornire: Path = LIVE_DIR / "fara_repornire"
    jurnale: Path = TRAJ_RAW_DIR
    loguri: Path = LOG_DIR
    cwd: Path = ROOT
    playlist: str | None = None
    pas: float = 60                 # s între verificări
    prag_stare: float = 300         # s; veghea alertează de la 180 s, cel mai lung gol refăcut singur în 21–29.10: 144 s
    prag_camera: float = 180        # s de la care se citește playlistul (prag_stare − rabdare_camera)
    prag_viu: float = 10            # s; un semn mai nou spune că cineva încă scrie, chiar dacă procesul nu se vede
    verificari_lipsa: int = 2       # verificări la rând la care procesul nu se vede, înaintea unei porniri
    timp_oprire: float = 90         # s de la Ctrl+C până la oprirea forțată (pe 30.10, oprirea curată a durat ≈4 s)
    pauza_trezire: float = 120      # s fără nicio hotărâre după o trezire din somn sau un salt de ceas
    prag_salt: float = 60           # s; abaterea pasului de la care e vorba de somn sau de un salt al ceasului
    asteptari: tuple[float, ...] = (60, 120, 300)      # s între încercări; ultima se repetă
    stabil: float = 600             # s de funcționare neîntreruptă după care încercările se numără de la capăt
    timp_crestere: float = 300      # s fără traiectorii noi după pornire până la avertisment (veghea: tot 300 s)
    timp_verificare: float = 600    # s pentru o rulare a lui `repara`; apoi se pornește oricum
    rabdare_camera: float = 120     # s de cameră bună înaintea unei opriri; întreruperile s-au refăcut în 33–73 s (§ 4.6)
    timeout_playlist: float = 10    # s pentru o citire a playlistului, oricât ar picura răspunsul
    pauza_playlist: float = 8       # s între cele două citiri ale playlistului (segmentele au ≈6 s)


# ---------------------------------------------------------------------------------------------- recunoașterea
def _citeste_interpretorul(argv: list[str]) -> tuple[tuple[str, ...], list[str]] | None:
    """(programul, argumentele lui), cu opțiunile citite ca în interpretor: lipite (-um modul, -mmodul, -Xutf8) sau cu
    valoarea în cuvântul următor (-X utf8). None dacă nu rulează niciun program sau rulează cod dat cu -c."""
    i = 1
    while i < len(argv):
        a = argv[i]
        i += 1
        if a == "--check-hash-based-pycs":
            i += 1
        elif a == "--":
            return ((os.path.normcase(os.path.normpath(argv[i])),), argv[i + 1:]) if i < len(argv) else None
        elif a.startswith("--"):
            pass
        elif a.startswith("-") and a != "-":
            for k, c in enumerate(a[1:], 2):
                if c in "cmWX":                    # primesc o valoare, lipită sau în cuvântul următor
                    valoare = a[k:]
                    if not valoare and i < len(argv):
                        valoare = argv[i]
                        i += 1
                    if c == "c":
                        return None
                    if c == "m":
                        return (("-m", valoare), argv[i:]) if valoare else None
                    break
        else:
            return (os.path.normcase(os.path.normpath(a)),), argv[i:]
    return None


def program(argv: list[str]) -> tuple[str, ...] | None:
    """Ce rulează un interpretor Python: ("-m", modulul) sau (calea scriptului,). None dacă primul cuvânt nu e Python
    (un PowerShell care doar pomenește modulul într-o interogare), dacă rulează cod dat cu -c (un proces ajutător) sau dacă
    rulează pe altă sursă decât camera (`--source clip.mp4`, ori un prefix primit de argparse): nu e colectarea."""
    if not argv or not Path(argv[0]).stem.casefold().startswith("python"):
        return None
    gasit = _citeste_interpretorul(argv)
    if gasit is None:
        return None
    prog, rest = gasit
    for x in rest:
        nume = x.split("=", 1)[0]
        if len(nume) >= 4 and "--source".startswith(nume):
            return None
    return prog


def acelasi_program(al_lui: tuple[str, ...] | None, prog: tuple[str, ...]) -> bool:
    """Procesul rulează exact `prog`? Modulul se recunoaște și după calea scriptului (src\\romana\\vision\\modul.py)."""
    if al_lui is None:
        return False
    if al_lui == prog:
        return True
    if prog[0] == "-m" and len(al_lui) == 1:
        cale = os.path.normcase(os.path.join(*prog[1].split("."))) + ".py"
        return al_lui[0] == cale or al_lui[0].endswith(os.sep + cale)
    return False


def _ar_putea_fi(argv: list[str], al_lui: tuple[str, ...] | None, prog: tuple[str, ...]) -> bool:
    """Un proces Python care nu rulează recunoscut programul, dar ar putea, fiindcă îl pomenește în argumente: un `-c` cu
    `runpy.run_module`, `-m runpy`, un script care îl lansează sau are același nume, o rulare pe un fișier video. Un alt
    modul al proiectului care doar primește numele ca argument (paznicul, cu `--comanda`) nu intră aici: se știe ce rulează."""
    if prog[0] == "-m":
        if al_lui is not None and al_lui[0] == "-m" and al_lui[1].split(".")[0] == prog[1].split(".")[0]:
            return False
        nume = prog[1].rsplit(".", 1)[-1]
        return any(re.search(rf"\b{re.escape(nume)}\b", x) for x in argv[1:])
    return al_lui is None and any(prog[0] in os.path.normcase(x) for x in argv[1:])


def cerceteaza_procese(prog: tuple[str, ...]) -> tuple[list[psutil.Process], list[psutil.Process]]:
    """(procesele care rulează exact programul `prog`, oricare ar fi calea interpretorului: lansatorul și copilul au căi
    diferite; procesele care ar putea să-l ruleze, fără să se poată ști). Lista pozitivă singură ar trece un proces
    nerecunoscut drept „lipsă”, iar paznicul ar porni a doua colectare. Paznicul nu se numără pe sine."""
    proprii, gasite, nestiute, necitite = {os.getpid(), os.getppid()}, [], [], []

    def incadreaza(p: psutil.Process) -> None:
        argv = p.cmdline()
        al_lui = program(argv)
        if acelasi_program(al_lui, prog):
            gasite.append(p)
        elif _ar_putea_fi(argv, al_lui, prog):
            nestiute.append(p)

    for p in psutil.process_iter():
        try:
            if p.pid in proprii or not p.name().casefold().startswith("python"):
                continue
        except (psutil.Error, OSError):            # încheiat între timp; numele nu se poate afla: nu e un proces al nostru
            continue
        try:
            incadreaza(p)
        except psutil.AccessDenied:
            necitite.append(p)
        except (psutil.Error, OSError):
            pass
    if necitite:
        time.sleep(PAUZA_NECITITE)
    for p in necitite:
        try:
            incadreaza(p)
        except psutil.AccessDenied:
            nestiute.append(p)
        except (psutil.Error, OSError):
            pass
    return gasite, nestiute


def gaseste_procese(prog: tuple[str, ...]) -> list[psutil.Process]:
    """Procesele care rulează exact programul `prog` (vezi `cerceteaza_procese`)."""
    return cerceteaza_procese(prog)[0]


def radacini(procese: list[psutil.Process]) -> list[psutil.Process]:
    """Procesele al căror părinte nu e printre ele: câte una pentru fiecare colectare (lansatorul și copilul lui, cu
    aceeași linie de comandă, sunt una singură)."""
    pids, out = {p.pid for p in procese}, []
    for p in procese:
        try:
            if p.ppid() not in pids:
                out.append(p)
        except psutil.Error:                       # încheiat între timp
            pass
    return out


def numara_colectari(procese: list[psutil.Process]) -> int:
    return len(radacini(procese))


def _pornit_la(procese: list[psutil.Process]) -> float:
    t = 0.0
    for p in procese:
        try:
            t = max(t, p.create_time())
        except psutil.Error:
            pass
    return t


def _amprenta(procese: list[psutil.Process]) -> set[tuple[int, float]]:
    """(PID, ora pornirii) pentru fiecare proces: un PID refolosit nu trece drept același proces."""
    out = set()
    for p in procese:
        try:
            out.add((p.pid, p.create_time()))
        except psutil.Error:
            out.add((p.pid, 0.0))
    return out


# ---------------------------------------------------------------------------------------------- oprirea și pornirea
def trimite_ctrl_c(pids: list[int]) -> int | None:
    """Ctrl+C în consola primului proces, prin procesul ajutător: paznicul nu-și părăsește consola. Întoarce codul
    ajutorului: 0 = trimis, 2 = fără consolă, 4 = consola e împărțită cu alte procese (nu s-a trimis nimic)."""
    try:
        return subprocess.run([sys.executable, "-c", COD_CTRL_C, *map(str, pids)], capture_output=True, timeout=30,
                              creationflags=subprocess.CREATE_NO_WINDOW).returncode
    except (OSError, subprocess.SubprocessError):
        return None


def porneste_ascuns(comanda: list[str], cwd: Path, env: dict, log: Path, err: Path) -> int:
    """Pornește o comandă fără fereastră, în consola ei ascunsă, ca `Start-Process -WindowStyle Hidden` din pașii de
    reluare: Ctrl+C trimis acolo nu ajunge la nimeni altcineva, iar procesul nu rămâne copilul paznicului. Întoarce PID-ul
    procesului pornit; un OSError dacă nu pornește."""
    zona = {"comanda": comanda, "cwd": str(cwd), "log": str(log), "err": str(err)}
    try:
        r = subprocess.run([sys.executable, "-c", COD_PORNIRE, json.dumps(zona)], env=env, capture_output=True,
                           encoding="utf-8", errors="replace", timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    except subprocess.SubprocessError as e:
        raise OSError(repr(e)) from e
    if r.returncode != 0:
        raise OSError(f"cod {r.returncode}: {r.stderr.strip()[-300:]}")
    return int(r.stdout.strip())


def _inlocuieste(a: Path, b: Path, incercari: int = 10) -> None:
    """`b` devine dintr-o dată conținutul lui `a`: numele `b` există în orice clipă. Pe Windows, înlocuirea eșuează cât timp
    altcineva citește fișierul (renumărarea): se mai încearcă."""
    for k in range(incercari):
        try:
            os.replace(a, b)
            return
        except PermissionError:
            if k == incercari - 1:
                raise
            time.sleep(1)


# ---------------------------------------------------------------------------------------------- ce se citește
def citeste_stare(path: Path) -> float | None:
    """Ora ultimului cadru prelucrat (`timestamp` din starea live). Dacă fișierul tocmai e înlocuit și nu se poate citi,
    data lui; None dacă nu există sau dacă ora nu e plauzibilă."""
    t = None
    for _ in range(3):
        try:
            t = float(json.loads(path.read_text(encoding="utf-8"))["timestamp"])
            break
        except FileNotFoundError:
            return None
        except (OSError, ValueError, KeyError, TypeError):
            time.sleep(0.2)
    if t is None:
        try:
            t = path.stat().st_mtime
        except OSError:
            return None
    return t if 1e9 < t < 1e10 else None


def semne_vecine(stare: Path) -> list[float]:
    """Datele fișierelor scrise de `run_vision` lângă stare: previzualizarea, la fiecare cadru, și copia stării, dacă a
    rămas neînlocuită. Doar `stat`: imaginea nu se deschide."""
    out = []
    for nume in SEMNE_VECINE:
        try:
            out.append(stare.with_name(nume).stat().st_mtime)
        except OSError:
            pass
    return out


def varsta_semn(acum: float, *momente: float | None) -> float:
    """Vârsta celui mai nou semn de viață. Un moment „din viitor” nu e un semn: ceasul s-a dat înapoi după el, iar un proces
    care lucrează are alt semn, previzualizarea, rescrisă la fiecare cadru; fără niciun semn: infinit."""
    bune = [t for t in momente if t is not None and t <= acum + MARJA_CEAS]
    return acum - max(bune) if bune else float("inf")


def _descarca(url: str, timeout: float) -> bytes:
    """Corpul răspunsului, pe bucăți, cu termen și limită de mărime: `timeout` din urlopen limitează doar fiecare citire din
    rețea, iar un server care picură câte un octet nu s-ar mai termina."""
    capat, corp = time.monotonic() + timeout, bytearray()
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        while bucata := r.read1(65536):
            corp += bucata
            if len(corp) > MARIME_PLAYLIST:
                raise ValueError(f"răspunsul are peste {MARIME_PLAYLIST} octeți: nu e un playlist HLS")
            if time.monotonic() > capat:
                raise TimeoutError(f"răspunsul nu s-a încheiat în {timeout:g} s")
    return bytes(corp)


def secventa_playlist(url: str, timeout: float) -> int | None:
    """Secvența media a playlistului HLS (None dacă nu o declară). O excepție dacă nu răspunde, nu e un playlist sau nu se
    încheie în `timeout` s. Citirea merge într-un fir separat: numele de domeniu și antetele nu au alt termen, iar
    verificările nu trebuie să stea după ele; firul se încheie odată cu răspunsul."""
    rez = []

    def citeste() -> None:
        try:
            rez.append(_descarca(url, timeout))
        except Exception as e:                     # se ridică mai jos, în firul verificărilor
            rez.append(e)

    fir = threading.Thread(target=citeste, daemon=True, name="playlist")
    fir.start()
    fir.join(timeout)
    if not rez:
        raise TimeoutError(f"răspunsul nu s-a încheiat în {timeout:g} s")
    if isinstance(rez[0], Exception):
        raise rez[0]
    txt = rez[0].decode("utf-8", "replace")
    if "#EXTM3U" not in txt:
        raise ValueError("răspunsul nu e un playlist HLS")
    m = re.search(r"#EXT-X-MEDIA-SEQUENCE:(\d+)", txt)
    return int(m.group(1)) if m else None


def camera_raspunde(url: str | None, timeout: float, pauza: float) -> tuple[bool | None, str]:
    """Playlistul camerei, citit de două ori la `pauza` s distanță: răspunde și avansează? Un playlist care stă pe loc sau
    care nu-și declară secvența (fără etichetă, secvența e 0, RFC 8216) spune același lucru ca unul care nu răspunde:
    repornirea colectării nu ar ajuta cu nimic. None dacă URL-ul nu se cunoaște: nu se știe."""
    if not url:
        return None, "URL-ul playlistului nu se cunoaște"
    try:
        a = secventa_playlist(url, timeout)
        time.sleep(pauza)
        b = secventa_playlist(url, timeout)
    except Exception as e:                         # rețeaua sau serverul camerei: și asta e o informație
        return False, f"playlistul nu răspunde ({e!r})"
    if a is None or b is None:
        return False, "playlistul răspunde, dar fără secvență: nu se vede că avansează"
    if b <= a:
        return False, f"playlistul răspunde, dar stă pe loc (secvența {b})"
    return True, f"playlistul răspunde (secvența {a} → {b})"


def url_din_config() -> str | None:
    try:
        return load_json("camera.json")["stream_url"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def marime_fisier(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def prima_traiectorie(path: Path, poz: int) -> float | None:
    """Cel mai mic `t0` dintre traiectoriile întregi adăugate în jurnal de la octetul `poz` (un membru gzip pe traiectorie),
    sau None. Un ultim membru incomplet rămâne pentru citirea următoare; după un membru stricat se caută antetul următor."""
    try:
        with open(path, "rb") as fh:
            fh.seek(poz)
            octeti = fh.read()
    except OSError:
        return None
    gasite, i = [], 0
    while i < len(octeti):
        d = zlib.decompressobj(31)
        try:
            txt = d.decompress(octeti[i:])
        except zlib.error:
            i = octeti.find(b"\x1f\x8b\x08", i + 1)
            if i < 0:
                break
            continue
        if not d.eof:
            break
        i = len(octeti) - len(d.unused_data)
        for line in txt.decode("utf-8", "replace").splitlines():
            try:
                gasite.append(float(json.loads(line)["t0"]))
            except (ValueError, KeyError, TypeError):
                pass
    return min(gasite) if gasite else None


def are_membri_stricati(rand: str) -> bool | None:
    """Din contoarele afișate de `romana.vision.repara`; None dacă rândul nu le are (o eroare a comenzii, care poate ieși
    tot cu codul 2). Cu colectarea oprită, un ultim membru incomplet (`in_scriere`, pentru care `repara` întoarce 0) nu se
    mai încheie niciodată, iar membrii adăugați după el l-ar face stricat: se socotește la fel."""
    m = re.search(r"stricati=(\d+), in_scriere=(\d+)", rand)
    return None if m is None else int(m.group(1)) + int(m.group(2)) > 0


def coada_fisier(path: Path, n: int = 3) -> list[str]:
    """Ultimele `n` rânduri nevide ale unui fișier (se citesc doar ultimii 4 KB)."""
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, os.fstat(fh.fileno()).st_size - 4096))
            text = fh.read().decode("utf-8", "replace")
    except OSError:
        return []
    return [x.strip()[:200] for x in text.splitlines() if x.strip()][-n:]


# ---------------------------------------------------------------------------------------------- ce se scrie
def iso(t: float) -> str:
    return datetime.fromtimestamp(t).isoformat(timespec="seconds")


def zile_intre(t0: float, t1: float) -> list[str]:
    a, b = sorted((date.fromtimestamp(t0), date.fromtimestamp(t1)))
    return [(a + timedelta(days=k)).isoformat() for k in range((b - a).days + 1)]


def scrie_repornire(loguri: Path, oprire: float, repornire: float, vechi: float | None = None) -> None:
    """Rândul (oprire, repornire) în reporniri_<zi>.csv, pentru fiecare zi atinsă de gol. Cu `vechi`, rândul scris la
    pornire primește ora primei traiectorii noi. Fișierul se înlocuiește atomic: lanțul zilnic nu vede niciodată unul pe
    jumătate; un OSError (fișierul e deschis în altă parte) ajunge la apelant."""
    rand, rand_vechi = [iso(oprire), iso(repornire)], None if vechi is None else [iso(oprire), iso(vechi)]
    loguri.mkdir(parents=True, exist_ok=True)
    for zi in zile_intre(oprire, repornire):
        f = loguri / f"reporniri_{zi}.csv"
        randuri = []
        if f.exists():
            with open(f, newline="", encoding="utf-8") as fh:
                randuri = list(csv.reader(fh))[1:]
        if rand_vechi in randuri:
            randuri[randuri.index(rand_vechi)] = rand
        elif rand not in randuri:
            randuri.append(rand)
        tmp = f.with_suffix(".tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as fo:
            w = csv.writer(fo)
            w.writerow(CSV_CAP)
            w.writerows(randuri)
        tmp.replace(f)


# ---------------------------------------------------------------------------------------------- ecranul
_ecran: queue.Queue = queue.Queue(maxsize=COADA_ECRAN)
_fir_ecran: threading.Thread | None = None


def _afiseaza_mereu() -> None:
    while True:
        flux, rand = _ecran.get()
        try:
            print(rand, file=flux, flush=True)
        except Exception:                          # ieșirea standard închisă sau defectă: rândul rămâne în fișier
            pass
        finally:
            _ecran.task_done()


def afiseaza(rand: str) -> None:
    """Un rând pe ecran, dintr-un fir separat: o ieșire standard care nu se golește (o conductă necitită, o selecție în
    consolă) ține pe loc firul acesta, nu verificările. Rândul e deja în fișier; dacă ecranul rămâne prea mult în urmă,
    rândurile noi nu mai ajung pe el."""
    global _fir_ecran
    if _fir_ecran is None:
        _fir_ecran = threading.Thread(target=_afiseaza_mereu, daemon=True, name="ecran")
        _fir_ecran.start()
    try:
        _ecran.put_nowait((sys.stdout, rand))
    except queue.Full:
        pass


def goleste_ecranul(termen: float = 2.0) -> bool:
    """Așteaptă afișarea rândurilor rămase, cel mult `termen` s; False dacă ieșirea standard e blocată."""
    capat = time.monotonic() + termen
    while _ecran.unfinished_tasks and time.monotonic() < capat:
        time.sleep(0.01)
    return not _ecran.unfinished_tasks


# ---------------------------------------------------------------------------------------------- paznicul
class Paznic:
    """O verificare = `pas()`, care întoarce hotărârea: ok (nimic de făcut), trezire, anuntata, mai_multe, viu (semn
    proaspăt fără proces văzut), lipsa (procesul nu se vede, încă o verificare), nestiut (poate fi colectarea, nu se poate
    ști), camera, asteapta, revenit (s-a refăcut chiar înainte de oprire), schimbat (procesele s-au schimbat chiar înainte
    de oprire), pornit, neoprit, nepornit sau exista. `ceas` dă ora de pe semne și din jurnale; `monoton`, așteptările
    interne (un ceas fals ține loc și de ceas monoton, dacă nu se dă altul)."""

    def __init__(self, s: Setari, ceas=time.time, dormi=time.sleep, monoton=None):
        self.s, self.ceas, self.dormi = s, ceas, dormi
        self.monoton = monoton or (time.monotonic if ceas is time.time else ceas)
        self.prog = program(s.comanda)
        if self.prog is None:
            raise ValueError(f"Comanda nu rulează un program Python recunoscut: {s.comanda}")
        self.pauza_pana = 0.0          # după o trezire sau un salt de ceas, nicio hotărâre până atunci
        self.incercari = 0             # repornirile de la ultima perioadă stabilă
        self.urmatoarea = 0.0          # de când e voie la o nouă încercare
        self.sanatos_din = None        # de când e colectarea sănătoasă, fără întrerupere
        self.pornit = None             # ultimul proces pornit de paznic (psutil.Process sau None)
        self.err = None                # jurnalul de erori al ultimei porniri
        self.urmarire = None           # după o pornire: se caută prima traiectorie nouă
        self.lipsa = 0                 # verificările la rând la care procesul nu s-a văzut
        self.camera_buna_din = None    # de când răspunde și avansează playlistul, în episodul curent
        self.note_recente = {}
        self.ultimul_semn = -1e18
        self.restante = []             # rânduri CSV care n-au putut fi scrise încă (fișier deschis în altă parte)

    # ------------------------------------------------------------------ jurnalul propriu
    def nota(self, text: str, cheie: str | None = None) -> None:
        """Un rând în paznic_<zi>.log și pe ecran. Cu `cheie`, un mesaj care se repetă se scrie cel mult o dată la
        5 minute."""
        acum, mono = self.ceas(), self.monoton()
        if cheie is not None:
            if mono - self.note_recente.get(cheie, -1e18) < REPETARE_NOTA:
                return
            self.note_recente[cheie] = mono
        rand = f"{iso(acum)} {text}"
        try:
            self.s.loguri.mkdir(parents=True, exist_ok=True)
            with open(self.s.loguri / f"paznic_{date.fromtimestamp(acum).isoformat()}.log", "a", encoding="utf-8") as fo:
                fo.write(rand + "\n")
        except OSError:
            pass
        afiseaza(rand)

    def _scrie_repornire(self, oprire: float, repornire: float, vechi: float | None = None) -> None:
        try:
            scrie_repornire(self.s.loguri, oprire, repornire, vechi)
        except OSError as e:
            self.restante.append((oprire, repornire, vechi))
            self.nota(f"reporniri: rândul rămâne pentru pasul următor ({e!r})", "reporniri")

    def _scrie_restante(self) -> None:
        restante, self.restante = self.restante, []
        for r in restante:
            self._scrie_repornire(*r)

    # ------------------------------------------------------------------ o verificare
    def pas(self) -> str:
        acum, mono = self.ceas(), self.monoton()
        try:                                       # o eroare aici nu trebuie să împiedice hotărârile de mai jos
            self._scrie_restante()
            self._urmareste_jurnalul(acum)
        except Exception:
            self.nota("eroare la urmărirea jurnalului: " + traceback.format_exc(limit=3), "urmarire")
        if mono < self.pauza_pana:
            self.nota(f"după trezire / salt de ceas: nicio hotărâre încă {self.pauza_pana - mono:.0f} s", "trezire")
            return "trezire"
        if self.s.fara_repornire.exists():
            self.lipsa = 0
            self.nota(f"oprire anunțată ({self.s.fara_repornire.name}): nu repornesc nimic", "anuntata")
            return "anuntata"
        procese = gaseste_procese(self.prog)
        n = numara_colectari(procese)
        if n > 1:
            self.nota(f"ATENȚIE: {n} colectări în același timp (PID {', '.join(str(p.pid) for p in procese)}): "
                      "nu hotărăsc singur", "mai_multe")
            return "mai_multe"
        hotarare, motiv = self._proces_vazut(procese, mono) if n == 1 else self._proces_nevazut(acum)
        if hotarare is not None:
            return hotarare
        mono = self.monoton()
        if mono < self.urmatoarea:
            self.nota(f"{motiv}; următoarea încercare peste {self.urmatoarea - mono:.0f} s", "asteapta")
            return "asteapta"
        # ultima privire: citirea playlistului durează, iar între timp omul poate anunța o oprire sau reporni colectarea
        if self.s.fara_repornire.exists():
            self.nota("oprire anunțată chiar înaintea opririi: nu opresc nimic")
            return "anuntata"
        vazute, nestiute = cerceteaza_procese(self.prog)
        if nestiute:
            self.nota(f"ATENȚIE: {motiv}, dar PID {', '.join(str(p.pid) for p in nestiute)} poate fi colectarea și nu se "
                      "poate ști: nu opresc și nu pornesc nimic", "nestiut")
            return "nestiut"
        if _amprenta(vazute) != _amprenta(procese):
            self.nota("procesele colectării s-au schimbat între hotărâre și oprire: nu opresc nimic")
            return "schimbat"
        return self._reporneste(motiv)

    def _varsta(self, procese: list[psutil.Process]) -> float:
        """Vârsta ultimului semn de viață; procesul abia pornit nu răspunde pentru o stare mai veche decât el."""
        return varsta_semn(self.ceas(), citeste_stare(self.s.stare), *semne_vecine(self.s.stare), _pornit_la(procese))

    def _proces_vazut(self, procese: list[psutil.Process], mono: float) -> tuple[str | None, str]:
        """Procesul se vede. Întoarce hotărârea, dacă se ia acum una, altfel motivul unei opriri."""
        self.lipsa = 0
        varsta = self._varsta(procese)
        if varsta <= min(self.s.prag_camera, self.s.prag_stare):
            self._sanatos(mono, len(procese), varsta)
            return "ok", ""
        self.sanatos_din = None
        ok, text = self._priveste_camera()
        if varsta <= self.s.prag_stare:
            self.nota(f"ultimul semn de viață are {varsta:.0f} s, încă sub prag: {text}", "sub_prag")
            return "ok", ""
        # citirea playlistului durează: poate s-a refăcut între timp
        if self._varsta(procese) <= self.s.prag_stare:
            self.nota("starea s-a refăcut singură înaintea opririi")
            return "revenit", ""
        motiv = f"proces blocat: ultimul semn de viață are {varsta:.0f} s"
        return (None, motiv) if self._camera_permite(motiv, ok, text) else ("camera", "")

    def _proces_nevazut(self, acum: float) -> tuple[str | None, str]:
        """Procesul nu se vede. Întoarce hotărârea, dacă se ia acum una, altfel motivul unei porniri."""
        self.sanatos_din = None
        varsta = max(varsta_semn(acum, citeste_stare(self.s.stare), *semne_vecine(self.s.stare)), 0)
        if varsta < self.s.prag_viu:
            self.lipsa = 0
            self.nota(f"procesul nu se vede, dar ultimul semn de viață are {varsta:.0f} s: nu pornesc al doilea", "viu")
            return "viu", ""
        self.lipsa += 1
        if self.lipsa < self.s.verificari_lipsa:
            self.nota(f"procesul nu se vede (verificarea {self.lipsa} din {self.s.verificari_lipsa}): mai aștept", "lipsa")
            return "lipsa", ""
        erori = coada_fisier(self.err) if self.err else []
        return None, "procesul lipsește" + (f" (ultimele erori: {' | '.join(erori)})" if erori else "")

    def _sanatos(self, mono: float, n_procese: int, varsta: float) -> None:
        self.camera_buna_din = None
        self.note_recente.clear()
        self.sanatos_din = mono if self.sanatos_din is None else self.sanatos_din
        if self.incercari and mono - self.sanatos_din >= self.s.stabil:
            self.nota(f"repornirea ține de {mono - self.sanatos_din:.0f} s: încercările se numără de la capăt")
            self.incercari, self.urmatoarea = 0, 0.0
        if mono - self.ultimul_semn >= SEMN_DE_VIATA:
            self.ultimul_semn = mono
            self.nota(f"în regulă: {n_procese} procese, o colectare, starea are {max(varsta, 0):.0f} s")

    def _priveste_camera(self) -> tuple[bool | None, str]:
        """O citire a playlistului. Camera contează drept bună de la prima citire bună de după ultima rea, în același
        episod: o citire bună singură nu spune de cât timp e bună (camera poate abia să fi revenit)."""
        ok, text = camera_raspunde(self.s.playlist, self.s.timeout_playlist, self.s.pauza_playlist)
        if not ok:
            self.camera_buna_din = None
        elif self.camera_buna_din is None:
            self.camera_buna_din = self.monoton()
        return ok, text

    def _camera_permite(self, motiv: str, ok: bool | None, text: str) -> bool:
        if ok is None:
            self.nota(f"{motiv}; {text}: nu pot deosebi o pană a camerei de un proces blocat, repornesc", "camera")
            return True
        if not ok:
            self.nota(f"{motiv}; {text}: nu repornesc, run_vision se reconectează singur", "camera")
            return False
        buna = self.monoton() - self.camera_buna_din
        if buna < self.s.rabdare_camera:
            self.nota(f"{motiv}; camera răspunde de {buna:.0f} s: îi mai las {self.s.rabdare_camera - buna:.0f} s să se "
                      "refacă singur", "camera_buna")
            return False
        return True

    # ------------------------------------------------------------------ repornirea
    def _reporneste(self, motiv: str) -> str:
        self.incercari += 1
        self.nota(f"repornire, încercarea {self.incercari}: {motiv}")
        self.urmarire = None                       # rândul unei porniri mai vechi rămâne cu momentul pornirii
        try:
            return self._incearca()
        finally:
            k = min(self.incercari, len(self.s.asteptari)) - 1
            self.urmatoarea = self.monoton() + self.s.asteptari[k]

    def _incearca(self) -> str:
        if not self._opreste():
            return "neoprit"
        self.lipsa = self.s.verificari_lipsa       # oprit chiar de noi: o nouă încercare nu mai așteaptă a doua verificare
        acum = self.ceas()
        oprire = citeste_stare(self.s.stare)
        oprire = acum if oprire is None else oprire
        try:                                       # colectarea e oprită acum: orice s-ar întâmpla aici, trebuie repornită
            self._verifica_jurnalele(oprire, acum)
        except Exception:
            self.nota("verificarea jurnalelor a eșuat; pornesc oricum: " + traceback.format_exc(limit=3))
        if self.s.fara_repornire.exists():
            self.nota("oprire anunțată în timpul repornirii: colectarea rămâne oprită")
            return "anuntata"
        # ultima privire, niciodată a doua colectare: și după căutare, și după procesul pornit ultima dată de paznic
        if any(cerceteaza_procese(self.prog)) or (self.pornit is not None and self.pornit.is_running()):
            self.nota("a apărut între timp o colectare: nu pornesc alta")
            return "exista"
        t = self.ceas()
        oprire = min(oprire, t)                    # o stare „din viitor” (ceasul s-a dat înapoi) nu e o dovadă de viață
        f = self._jurnal(date.fromtimestamp(t).isoformat())
        self._avertizeaza_jurnal_lipsa(f)
        self.s.loguri.mkdir(parents=True, exist_ok=True)
        baza = f"viziune_{datetime.fromtimestamp(t):%Y-%m-%d_%H%M%S}"
        log, err = self.s.loguri / f"{baza}.log", self.s.loguri / f"{baza}.err"
        try:
            poz = marime_fisier(f)
            pid = porneste_ascuns(self.s.comanda, self.s.cwd, self._mediu(), log, err)
        except OSError as e:
            self.nota(f"pornirea a eșuat: {e!r}")
            return "nepornit"
        try:
            self.pornit = psutil.Process(pid)
        except psutil.Error:                       # a ieșit deja; se va vedea la pasul următor
            self.pornit = None
        self.err = err
        self.urmarire = {"t": t, "mono": self.monoton(), "poz": {f: poz}, "oprire": oprire, "repornire": t,
                         "avertizat": False}
        self.nota(f"run_vision pornit: lansatorul are PID {pid}; jurnale {log.name}, {err.name}; "
                  f"ultima dovadă de viață {iso(oprire)}")
        self._scrie_repornire(oprire, t)
        return "pornit"

    def _opreste(self) -> bool:
        """Oprirea curată, apoi cea forțată: întâi copilul, apoi lansatorul. Doar procesele colectării, găsite din nou."""
        procese = gaseste_procese(self.prog)
        if not procese:
            return True
        pids = [p.pid for p in radacini(procese)] or [procese[0].pid]
        pids += [p.pid for p in procese if p.pid not in pids]
        cod = trimite_ctrl_c(pids)
        self.nota(f"Ctrl+C către PID {', '.join(map(str, pids))}: " +
                  {0: "trimis", 2: "procesul nu are consolă", 4: "consola e împărțită cu alte procese, nu l-am trimis"}
                  .get(cod, f"netrimis (cod {cod})"))
        t0 = time.monotonic()
        _, vii = psutil.wait_procs(procese, timeout=self.s.timp_oprire)
        if not vii:
            self.nota(f"oprit curat în {time.monotonic() - t0:.0f} s")
            return True
        self.nota(f"nu s-a oprit în {self.s.timp_oprire:.0f} s: oprire forțată (PID "
                  f"{', '.join(str(p.pid) for p in vii)})")
        ramase = {p.pid for p in vii}
        for p in sorted(vii, key=lambda p: p in radacini(vii)):
            try:
                p.kill()
            except psutil.Error:
                pass
        _, vii = psutil.wait_procs(vii, timeout=15)
        if vii:
            self.nota(f"nu pot opri PID {', '.join(str(p.pid) for p in vii)}: nu pornesc altul")
            return False
        self.nota(f"oprit forțat: PID {', '.join(map(str, sorted(ramase)))}")
        return True

    def _mediu(self) -> dict:
        return {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}

    # ------------------------------------------------------------------ jurnalul de traiectorii
    def _jurnal(self, zi: str) -> Path:
        return self.s.jurnale / f"traiectorii_{zi}.jsonl.gz"

    def _urmareste_jurnalul(self, acum: float) -> None:
        """După o pornire: jurnalul zilei crește? Prima traiectorie nouă devine ora repornirii din CSV."""
        u = self.urmarire
        if u is None:
            return
        gasite = []
        for f in {*u["poz"], self._jurnal(date.fromtimestamp(acum).isoformat())}:
            poz = u["poz"].get(f, 0)
            if marime_fisier(f) > poz:
                t0 = prima_traiectorie(f, poz)
                if t0 is not None:
                    gasite.append(t0)
        trecut = self.monoton() - u["mono"]
        if gasite:
            t0 = max(min(gasite), u["oprire"])     # lanțul zilnic respinge un rând cu repornirea înaintea opririi
            self.nota(f"jurnalul zilei crește: prima traiectorie nouă la {iso(t0)}")
            self._scrie_repornire(u["oprire"], t0, u["repornire"])
            self.urmarire = None
        elif trecut >= self.s.timp_crestere and not u["avertizat"]:
            u["avertizat"] = True
            self.nota(f"ATENȚIE: jurnalul zilei nu a crescut în {trecut:.0f} s de la pornire")

    def _ruleaza_repara(self, *argumente) -> tuple[int | None, str]:
        """`romana.vision.repara` ca subproces, la prioritate scăzută: codul și ultimul rând afișat (doar contoare)."""
        try:
            r = subprocess.run([*self.s.comanda_repara, *map(str, argumente)], cwd=self.s.cwd, env=self._mediu(),
                               capture_output=True, encoding="utf-8", errors="replace", timeout=self.s.timp_verificare,
                               creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        except (OSError, subprocess.SubprocessError) as e:
            return None, repr(e)[:300]
        randuri = (r.stdout or "").strip().splitlines() or (r.stderr or "").strip().splitlines() or [""]
        return r.returncode, randuri[-1][:300]

    def _verifica_jurnalele(self, oprire: float, acum: float) -> None:
        """Jurnalul zilei, plus cele mai vechi scrise în jurul opririi (o urmărire începută ieri se scrie în jurnalul de
        ieri, chiar dacă se încheie azi)."""
        fis = [self._jurnal(z) for z in zile_intre(min(oprire, acum) - 86400, acum)]
        for f in fis:
            if f.exists() and (f == fis[-1] or f.stat().st_mtime >= oprire - MARJA_JURNAL):
                self._verifica_jurnal(f)

    def _verifica_jurnal(self, f: Path) -> None:
        cod, rand = self._ruleaza_repara(f)
        stricat = are_membri_stricati(rand)
        if cod not in (0, 2) or stricat is None:
            self.nota(f"jurnalul {f.name}: verificarea a eșuat (cod {cod}: {rand}); pornesc oricum")
        elif not stricat:
            self.nota(f"jurnalul {f.name}: întreg ({rand})")
        else:
            self.nota(f"jurnalul {f.name}: are membri stricați ({rand})")
            self._repara_jurnalul(f)

    def _repara_jurnalul(self, f: Path) -> None:
        """O copie reparată lângă fișier, verificată; originalul rămâne sub al doilea nume, iar copia îi ia locul dintr-o
        dată: jurnalul zilei există în orice clipă, deci o cădere a paznicului nu poate rupe ziua. Dacă un pas eșuează,
        jurnalul rămâne cum e, iar pornirea merge mai departe: `repara` îl poate repara și mai târziu."""
        ora = f"{datetime.fromtimestamp(self.ceas()):%H%M%S}"
        copie, pastrat = f.with_name(f"{f.name}.reparat_{ora}"), f.with_name(f"{f.name}.stricat_{ora}")
        cod, rand = self._ruleaza_repara(f, "--scrie", copie)
        if cod not in (0, 2) or not copie.exists():
            self.nota(f"jurnalul {f.name}: copia reparată n-a ieșit (cod {cod}: {rand}); rămâne cum e")
            return
        cod, rand = self._ruleaza_repara(copie)
        if cod != 0 or are_membri_stricati(rand) is not False:
            self.nota(f"jurnalul {f.name}: copia {copie.name} nu trece verificarea (cod {cod}: {rand}); rămâne cum e")
            return
        try:
            os.link(f, pastrat)                    # ca `rename`, nu suprascrie niciodată un nume existent
        except OSError as e:
            self.nota(f"jurnalul {f.name}: nu pot păstra originalul ({e!r}); rămâne cum e, copia e {copie.name}")
            return
        try:
            _inlocuieste(copie, f)
        except OSError as e:
            self.nota(f"jurnalul {f.name}: copia nu i-a putut lua locul ({e!r}); rămâne cum e, copia e {copie.name}")
            try:
                pastrat.unlink()                   # doar al doilea nume al jurnalului: datele rămân
            except OSError:
                pass
            return
        self.nota(f"jurnalul {f.name}: reparat ({rand}); originalul păstrat ca {pastrat.name}")

    def _avertizeaza_jurnal_lipsa(self, f: Path) -> None:
        """Jurnalul zilei lipsește, dar au rămas copii ale unei reparări: colectarea ar începe unul nou, iar lanțul zilnic,
        care citește doar numele exact, ar vedea doar partea nouă a zilei."""
        if f.exists():
            return
        ramase = sorted(x.name for x in f.parent.glob(f"{f.name}.*") if ".reparat_" in x.name or ".stricat_" in x.name)
        if ramase:
            self.nota(f"ATENȚIE: jurnalul zilei {f.name} lipsește, dar există {', '.join(ramase)}; colectarea începe unul "
                      "nou, iar ziua trebuie reunită de mână")

    # ------------------------------------------------------------------ bucla
    def bucla(self, pana_la: float) -> None:
        """Verificări la fiecare `pas` s, până la `pana_la`. Un somn al calculatorului sau un salt al ceasului se vede în
        durata pasului. La capăt, `run_vision` rămâne cum e. O eroare într-o verificare nu oprește paznicul."""
        self.nota(f"paznic pornit, până la {iso(pana_la)}: program {' '.join(self.prog)}, verificare la {self.s.pas:g} s, "
                  f"stare veche de la {self.s.prag_stare:g} s, așteptări {'/'.join(f'{x:g}' for x in self.s.asteptari)} s")
        while self.ceas() < pana_la:
            try:
                self.pas()
            except Exception:
                self.nota("eroare în verificare (paznicul merge mai departe): " + traceback.format_exc(limit=4))
            inainte = self.ceas()
            self.dormi(self.s.pas)
            durata = self.ceas() - inainte
            if abs(durata - self.s.pas) > self.s.prag_salt:
                self.pauza_pana = self.monoton() + self.s.pauza_trezire
                self.camera_buna_din, self.lipsa = None, 0      # ce s-a văzut înainte nu mai spune nimic
                self.nota(f"trezire din somn sau salt de ceas: pasul a durat {durata:.0f} s în loc de {self.s.pas:g} s; "
                          f"nicio hotărâre {self.s.pauza_trezire:g} s")
        self.nota("paznic încheiat; run_vision rămâne cum e")


def proba(p: Paznic) -> None:
    """Doar arată ce vede paznicul; nu oprește, nu pornește și nu scrie nimic."""
    procese, nestiute = cerceteaza_procese(p.prog)
    ts = citeste_stare(p.s.stare)
    print(f"program: {' '.join(p.prog)}")
    pids = ", ".join(str(x.pid) for x in procese) or "–"
    print(f"procese: {pids} ({len(procese)}); colectări: {numara_colectari(procese)}")
    print(f"procese care ar putea fi colectarea: {', '.join(str(x.pid) for x in nestiute) or '–'}")
    print("starea: " + ("lipsește" if ts is None else f"{iso(ts)}, are {time.time() - ts:.0f} s"))
    print(f"ultimul semn de viață: {varsta_semn(time.time(), ts, *semne_vecine(p.s.stare)):.0f} s")
    print(f"oprire anunțată: {'da' if p.s.fara_repornire.exists() else 'nu'}")
    print(f"camera: {camera_raspunde(p.s.playlist, p.s.timeout_playlist, p.s.pauza_playlist)[1]}")
    jurnal = p._jurnal(date.today().isoformat())
    print(f"jurnalul zilei: {jurnal.name}, {jurnal.stat().st_size if jurnal.exists() else 0} octeți")


def ia_lacatul(loguri: Path):
    """Un singur paznic la un moment dat: doi ar putea reporni colectarea în același timp. Blocarea dispare odată cu
    procesul, oricum s-ar încheia acesta. Întoarce fișierul blocat (de ținut deschis) sau None dacă e blocat deja."""
    import msvcrt
    loguri.mkdir(parents=True, exist_ok=True)
    fh = open(loguri / "paznic.lock", "a+b")
    try:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        fh.close()
        return None
    return fh


def _ora(text: str) -> float:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).timestamp()
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"oră nerecunoscută: {text} (AAAA-LL-ZZ HH:MM)")


def _cuvinte(text: str) -> list[str]:
    """O comandă dată ca text, cu ghilimele în jurul căilor cu spații (backslash-urile rămân cum sunt)."""
    return [c.strip('"') for c in shlex.split(text, posix=False)]


def main(argv=None) -> None:
    for flux in (sys.stdout, sys.stderr):   # diacriticele merg și când ieșirea e redirecționată fără UTF-8 (cp1250)
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    imp = Setari()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pana-la", type=_ora,
                    help="AAAA-LL-ZZ HH:MM (implicit: peste 24 h); la capăt, run_vision rămâne cum e")
    ap.add_argument("--proba", action="store_true", help="doar arată ce vede paznicul și iese; nu atinge nimic")
    ap.add_argument("--comanda", type=_cuvinte, default=imp.comanda, help="comanda care pornește colectarea, ca text; "
                    "după programul ei (-m modul sau calea scriptului) se recunoaște și procesul")
    ap.add_argument("--comanda-repara", type=_cuvinte, default=imp.comanda_repara,
                    help="comanda de verificare a jurnalului, ca text")
    ap.add_argument("--stare", type=Path, default=imp.stare,
                    help="starea live a colectării; semnele de viață vecine se caută în același dosar")
    ap.add_argument("--fara-repornire", type=Path, default=imp.fara_repornire,
                    help="cât timp există acest fișier, paznicul nu repornește nimic")
    ap.add_argument("--jurnale", type=Path, default=imp.jurnale, help="dosarul jurnalelor traiectorii_<zi>.jsonl.gz")
    ap.add_argument("--loguri", type=Path, default=imp.loguri,
                    help="dosarul pentru paznic_<zi>.log, reporniri_<zi>.csv și viziune_<data>_<ora>.log / .err")
    ap.add_argument("--cwd", type=Path, default=imp.cwd, help="dosarul în care pornește colectarea")
    ap.add_argument("--playlist", help="URL-ul playlistului camerei (implicit stream_url din config/camera.json)")
    for camp, text in (("pas", "s între verificări"),
                       ("prag_stare", "s de la care ultimul semn de viață e vechi"),
                       ("prag_camera", "s de la care se citește playlistul, ca la prag camera să fi fost deja văzută"),
                       ("prag_viu", "s sub care un semn proaspăt oprește pornirea, dacă procesul nu se vede"),
                       ("timp_oprire", "s de la Ctrl+C până la oprirea forțată"),
                       ("pauza_trezire", "s fără hotărâri după o trezire sau un salt de ceas"),
                       ("prag_salt", "s de abatere a pasului care înseamnă somn sau salt de ceas"),
                       ("stabil", "s de funcționare după care încercările se numără de la capăt"),
                       ("timp_crestere", "s fără traiectorii noi după pornire până la avertisment"),
                       ("timp_verificare", "s pentru o rulare a verificării jurnalului"),
                       ("rabdare_camera", "s de cameră bună, în același episod, înaintea unei opriri"),
                       ("timeout_playlist", "s pentru o citire a playlistului"),
                       ("pauza_playlist", "s între cele două citiri ale playlistului")):
        ap.add_argument("--" + camp.replace("_", "-"), type=float, default=getattr(imp, camp), help=text)
    ap.add_argument("--verificari-lipsa", type=int, default=imp.verificari_lipsa,
                    help="verificări la rând la care procesul nu se vede, înaintea unei porniri")
    ap.add_argument("--asteptari", type=float, nargs="+", default=list(imp.asteptari),
                    help="s între încercări; ultima se repetă")
    a = ap.parse_args(argv)
    playlist = a.playlist or url_din_config()
    if not playlist:                        # la pornire e cineva de față; fără el, o pană ar arăta ca un proces blocat
        ap.error("URL-ul playlistului nu se cunoaște (stream_url din config/camera.json sau --playlist)")
    s = Setari(comanda=a.comanda, comanda_repara=a.comanda_repara, stare=a.stare, fara_repornire=a.fara_repornire,
               jurnale=a.jurnale, loguri=a.loguri, cwd=a.cwd, playlist=playlist, pas=a.pas, prag_stare=a.prag_stare,
               prag_camera=a.prag_camera, prag_viu=a.prag_viu, verificari_lipsa=a.verificari_lipsa,
               timp_oprire=a.timp_oprire, pauza_trezire=a.pauza_trezire, prag_salt=a.prag_salt,
               asteptari=tuple(a.asteptari), stabil=a.stabil, timp_crestere=a.timp_crestere,
               timp_verificare=a.timp_verificare, rabdare_camera=a.rabdare_camera, timeout_playlist=a.timeout_playlist,
               pauza_playlist=a.pauza_playlist)
    p = Paznic(s)
    if a.proba:
        proba(p)
        return
    lacat = ia_lacatul(s.loguri)
    if lacat is None:
        print(f"[paznic] alt paznic rulează deja (blocat: {s.loguri / 'paznic.lock'}); ies.", flush=True)
        sys.exit(3)
    try:
        p.bucla(a.pana_la if a.pana_la else time.time() + 86400)
    except KeyboardInterrupt:
        p.nota("paznic oprit cu Ctrl+C; run_vision rămâne cum e")
    finally:
        lacat.close()
        if not goleste_ecranul():           # ieșirea standard e blocată: închiderea interpretorului ar rămâne în ea
            os._exit(0)


if __name__ == "__main__":
    main()
