"""Teste pentru starea senzorului (`romana.dashboard.senzor`, GET /api/senzor): fișiere sintetice mici, scrise într-un dosar
temporar în formatul celor reale, la o oră fixă; plus o probă pe dosarele reale, doar citire, care verifică numai forma
răspunsului. Pragurile copiate din veghe, din paznic și din lanțurile de noapte, și cele ale camerei, din pagină, se verifică
să rămână la fel.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_senzor
"""
import contextlib
import csv
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from datetime import datetime
from datetime import time as ora_din_zi
from pathlib import Path
from unittest import mock

from romana.common import ROOT
from romana.dashboard import senzor as SZ
from romana.vision import fisa_senzor as fs

SRC = Path(SZ.__file__).resolve().parents[2]
PAGINA = Path(SZ.__file__).resolve().parent / "static" / "index.html"
CHEI = ["camera", "colectarea", "veghea", "paznicul", "noaptea"]


def Z(zi: int, h: int, m: int = 0, s: float = 0) -> float:
    """O oră din iunie 2026 (fără schimbare de oră în preajmă), ca marcaj de timp local."""
    return datetime(2026, 6, zi, h, m).timestamp() + s


ACUM = Z(10, 8, 30)            # miercuri, 10.06.2026, 08:30:00


def text_ora(t: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.fromtimestamp(t).strftime(fmt)


def scrie(f: Path, continut, ora: float | None = None) -> Path:
    """Un fișier (textul în UTF-8, cu sfârșiturile de rând lăsate cum sunt), cu data lui pusă la `ora`."""
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(continut if isinstance(continut, bytes) else continut.encode("utf-8"))
    if ora is not None:
        os.utime(f, (ora, ora))
    return f


def csv_text(cap: list[str], randuri: list[list]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)          # ca în colectare: rândurile se încheie cu \r\n
    w.writerow(cap)
    w.writerows(randuri)
    return buf.getvalue()


def json_strict(text: str):
    """JSON citit strict: NaN, Infinity și -Infinity nu sunt JSON valid (pagina nu le-ar putea citi)."""
    def interzis(c):
        raise ValueError(f"nu e JSON valid: {c}")
    return json.loads(text, parse_constant=interzis)


# numărătorile, ca în od_counter.write_csv
CAP_NUMARATORI = ["inceput", "sfarsit", "tip", "origine", "destinatie", "vehicul", "numar"]


def sfert(a: float, intrari=(), iesiri=(), pietoni=(), viraje=()) -> list[list]:
    """Rândurile sfertului care începe la `a`, în ordinea din colectare: viraje, intrări, ieșiri, pietoni."""
    s, e = text_ora(a), text_ora(a + 900)
    return ([[s, e, "viraj", o, d, c, n] for o, d, c, n in viraje] + [[s, e, "intrare", b, "", c, n] for b, c, n in intrari]
            + [[s, e, "iesire", "", b, c, n] for b, c, n in iesiri]
            + [[s, e, "pietoni", b, z, "pieton", n] for b, z, n in pietoni])


# rândul de minut al vegherii
CAP_VEGHE = ["ora", "fps", "varsta_stare_s", "reconectari", "episoade_flux_30min", "pauze_5min", "urmarite", "dif_imagine",
             "pasi", "pasi_lungi_pct", "pas_median_s", "traiectorii", "in_miscare", "oprite", "identice_pct",
             "fara_traiectorii_s", "evenimente"]                  # veghe.CSV_CAP (verificat mai jos)
CAP_VEGHE_VECHI = ["ora", "fps", "varsta_stare_s", "reconectari", "urmarite", "pasi", "pasi_lungi_pct", "pas_median_s",
                   "traiectorii", "in_miscare", "oprite", "identice_pct", "fara_traiectorii_s"]   # ca veghe_2026-10-29_v1.csv


def pauza(t: float, d: int) -> str:
    """O pauză, cum o notează veghea în `evenimente` (cu „; ” și în textul ei)."""
    return (f"{datetime.fromtimestamp(t):%H:%M:%S} fără cadre {d} s (playlist: ultimul segment în urmă -10 s, avansează: "
            "True; rețea: 650 kB/s înainte, 150 kB/s de la −15 s; CPU: 3% în pauză, 118% înainte)")


def randuri_veghe(de_la: float, pana_la: float, schimbari: dict | None = None) -> list[dict]:
    """Câte un rând pe minut; `schimbari` = {"HH:MM": {coloana: valoarea}}."""
    out, t = [], de_la
    while t <= pana_la:
        r = {"ora": text_ora(t, "%Y-%m-%d %H:%M"), "fps": 6.0, "varsta_stare_s": 0.6, "reconectari": 1,
             "episoade_flux_30min": 0, "pauze_5min": 0, "urmarite": 80, "evenimente": ""}
        r.update((schimbari or {}).get(text_ora(t, "%H:%M"), {}))
        out.append(r)
        t += 60
    return out


def scrie_veghe(f: Path, randuri: list[dict], ora: float, cap=CAP_VEGHE) -> Path:
    return scrie(f, csv_text(cap, [[r.get(c, "") for c in cap] for r in randuri]), ora)


# paznicul și lanțurile de noapte
IN_REGULA = "în regulă: 2 procese, o colectare, starea are 0 s"
# paznic_2026-11-08.log, 11:27–12:30: o repornire care a ținut, cu notele ei, mutată pe 10.06.2026
REPORNIRE = [
    ("11:27:34", "calculatorul rămâne treaz cât rulează paznicul"),
    ("11:27:34", "paznic pornit, până la 2026-06-18T09:00:00: program -m romana.vision.run_vision, verificare la 60 s, "
                 "stare veche de la 300 s, așteptări 60/120/300 s"),
    ("11:27:34", "procesul nu se vede (verificarea 1 din 2): mai aștept"),
    ("11:28:34", "repornire, încercarea 1: procesul lipsește"),
    ("11:28:35", "jurnalul traiectorii_2026-06-10.jsonl.gz: întreg (traiectorii_2026-06-10.jsonl.gz: membri=46081, "
                 "stricati=0, in_scriere=0, linii=46081)"),
    ("11:28:35", "run_vision pornit: lansatorul are PID 14552; jurnale viziune_2026-06-10_112835.log, "
                 "viziune_2026-06-10_112835.err; ultima dovadă de viață 2026-06-10T11:12:54"),
    ("11:29:35", "jurnalul zilei crește: prima traiectorie nouă la 2026-06-10T11:28:43"),
    ("11:29:35", IN_REGULA),
    ("11:39:35", "repornirea ține de 600 s: încercările se numără de la capăt"),
    ("12:29:36", IN_REGULA),
]


def nota(t: float, text: str) -> str:
    return f"{datetime.fromtimestamp(t).isoformat(timespec='seconds')} {text}\n"


def stare_lant(zi: str, pornit: str, rezultat: str, pasi: dict, **campuri) -> str:
    """stare.json al unui lanț, ca în lant_zilnic și lant_cor: pașii au și comenzile, cu căi locale."""
    return json.dumps({"zi": zi, "pornit": pornit, "rezultat": rezultat, **campuri,
                       "pasi": {n: {"cod": c, "inceput": a, "sfarsit": b,
                                    "comanda": ["C:\\Users\\Cineva\\.venv\\Scripts\\python.exe", "-m", n]}
                                for n, (c, a, b) in pasi.items()}}, ensure_ascii=False, indent=1)


def fisa_json(taietura: str, ore: float = 110.92) -> str:
    """O fișă a senzorului, cu câmpurile din fisa_senzor.fisa de care are nevoie rezumatul."""
    return json.dumps({
        "taietura": taietura, "inceput": "2026-06-01T09:04:46", "sursa_inceputului": "data creării lui viziune_2026-06-01.log",
        "durata": {"ore": ore, "secunde": 399313}, "minute": {"intregi": 6655, "pondere_cu_cadre": 0.98843},
        "cadre_pe_secunda": {"mediana": 5.98}, "pauze": {"numar": 30, "durata_s": 715}, "reconectari": {"episoade": 10},
        "opriri": {"anuntate": 2, "caderi_neprevazute": 0},
        "lanturi": {"lant": {"ora": "00:15", "asteptate": 4, "incheiate": 4},
                    "lant_cor": {"ora": "03:30", "asteptate": 2, "incheiate": 2}, "total": {"asteptate": 6, "incheiate": 6}},
        "vehicule": {"pe_zile": {"2026-06-01": {"vehicule": 37147, "pietoni": 900}, "2026-06-02": {"vehicule": 56433}},
                     "total": 93580},
        "fisiere_citite": ["outputs/logs/veghe_2026-06-01.csv"]}, ensure_ascii=False)


def fisa_uriasa() -> str:
    """O fișă cu două zile de câte 1e308 vehicule: suma lor ar ieși infinită."""
    d = json.loads(fisa_json("2026-06-06T00:00:00"))
    d["vehicule"]["pe_zile"] = {"2026-06-01": {"vehicule": 1e308}, "2026-06-02": {"vehicule": 1e308}}
    return json.dumps(d)


class Baza(unittest.TestCase):
    """Dosare temporare goale, în locul celor reale; fiecare test scrie doar ce îi trebuie."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        self.live, self.loguri, self.num = self.d / "live", self.d / "logs", self.d / "counts"
        self.lant, self.cor = self.d / "lant", self.d / "lant_cor"
        self.docs, self.fise = self.d / "docs_rezultate", self.d / "fisa_senzor"
        for x in (self.live, self.loguri, self.num):
            x.mkdir()
        self.lanturi = {"lant": (self.lant, ora_din_zi(0, 15)), "lant_cor": (self.cor, ora_din_zi(3, 30))}

    def stare(self, acum: float = ACUM) -> dict:
        return SZ.stare_senzor(acum, live=self.live, loguri=self.loguri, numaratori=self.num, lanturi=self.lanturi,
                               fise=(self.docs, self.fise))

    def veriga(self, cheie: str, acum: float = ACUM) -> dict:
        r = self.stare(acum)
        self.assertEqual([v["cheie"] for v in r["verigi"]], CHEI)
        v = r["verigi"][CHEI.index(cheie)]
        self.assertIn(v["stare"], SZ.STARI)
        self.assertNotIn("eroare", v)
        json_strict(json.dumps(r))
        return v

    def scrie_stare(self, varsta: float, acum: float = ACUM, **campuri) -> None:
        st = {"timestamp": acum - varsta, "fps": 6.0, "conectat": True, "reconectari": 1, "vehicule_urmarite": 82,
              "pietoni_h": {"magheru": 104}, **campuri}
        scrie(self.live / "state.json", json.dumps(st), acum - varsta)


class TestCoada(unittest.TestCase):
    def test_randurile_intregi_din_coada(self):
        with tempfile.TemporaryDirectory() as d:
            # octeții: „cap\r\n” 0–4, „aaaa\r\n” 5–10, „bbbb\r\n” 11–16, „cc” 17–18 (încă în scriere)
            f = scrie(Path(d) / "x.csv", b"cap\r\naaaa\r\nbbbb\r\ncc", ACUM)
            self.assertEqual(SZ._coada(f, 100), ("cap", ["aaaa", "bbbb"], True, ACUM))      # și data fișierului
            self.assertEqual(SZ._coada(f, 14)[:3], ("cap", ["aaaa", "bbbb"], True))
            self.assertEqual(SZ._coada(f, 12)[:3], ("cap", ["bbbb"], False))      # începe în mijlocul lui aaaa
            self.assertEqual(SZ._coada(f, 9)[:3], ("cap", ["bbbb"], False))       # începe pe \n-ul lui aaaa
            self.assertEqual(SZ._coada(f, 8)[:3], ("cap", ["bbbb"], False))       # începe chiar cu bbbb: rândul rămâne
            self.assertEqual(SZ._coada(f, 1)[:3], ("cap", [], False))
            scrie(f, b"\xef\xbb\xbfora,fps\nx\n")                                  # cu BOM, cu \n simplu
            self.assertEqual(SZ._coada(f, 100)[:3], ("ora,fps", ["x"], True))
            scrie(f, b"")
            self.assertEqual(SZ._coada(f, 100)[:3], ("", [], True))


@unittest.skipUnless(os.name == "nt", "doar pe Windows un cititor poate opri ștergerea unui fișier")
class TestDeschiderea(unittest.TestCase):
    """_deschide: cât timp panoul ține un fișier deschis, alt proces îl poate șterge și scrie din nou (BE3), dar nu-l poate
    înlocui (os.replace): de aceea lanțul vechi își reîncearcă scrierea stării."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_stergerea_si_scrierea_din_nou_merg_cat_e_deschis(self):
        f = scrie(self.d / "numaratori_2026-06-09.csv", b"inceput,sfarsit\nvechi\n")
        with SZ._deschide(f) as fo:
            self.assertEqual(fo.readline(), b"inceput,sfarsit\n")
            os.unlink(f)                                   # ca renumărarea de noapte: fără PermissionError
            self.assertFalse(f.exists())
            with open(f, "ab") as nou:                     # și CSV-ul scris din nou, sub același nume (write_csv)
                nou.write(b"nou\n")
            self.assertEqual(fo.read(), b"vechi\n")        # panoul citește până la capăt ce era înainte
        self.assertEqual(f.read_bytes(), b"nou\n")

    def test_adaugarea_merge_cat_e_deschis(self):
        f = scrie(self.d / "paznic_2026-06-10.log", b"a\n")
        with SZ._deschide(f):
            with open(f, "ab") as fo:
                fo.write(b"b\n")
        self.assertEqual(f.read_bytes(), b"a\nb\n")

    def test_un_fisier_lipsa_da_tot_file_not_found(self):
        for f in (self.d / "lipsa.csv", self.d / "nici_dosarul" / "lipsa.csv"):
            with self.subTest(f=f.name), self.assertRaises(FileNotFoundError):
                SZ._deschide(f)

    def test_doar_pentru_citire(self):
        f = scrie(self.d / "x.json", b"{}")
        with SZ._deschide(f) as fo:
            with self.assertRaises(OSError):
                os.write(fo.fileno(), b"x")
        self.assertEqual(f.read_bytes(), b"{}")

    def test_manerul_se_inchide_daca_nu_devine_fisier(self):
        f = scrie(self.d / "x.json", b"{}")
        creeaza, inchide, create, inchise = SZ._winapi.CreateFile, SZ._winapi.CloseHandle, [], []

        def creare(*a):
            create.append(creeaza(*a))
            return create[-1]

        def inchidere(h):
            inchise.append(h)
            return inchide(h)

        with mock.patch.object(SZ._winapi, "CreateFile", creare), mock.patch.object(SZ._winapi, "CloseHandle", inchidere), \
                mock.patch.object(SZ.msvcrt, "open_osfhandle", side_effect=OSError("de probă")):
            with self.assertRaises(OSError):
                SZ._deschide(f)
        self.assertEqual(len(create), 1)
        self.assertIn(create[0], inchise)

    def test_inlocuirea_unui_fisier_tinut_deschis_tot_esueaza(self):
        """Descrierea modulului: partajarea completă lasă ștergerea, dar nu și înlocuirea (os.replace) cât panoul ține
        fișierul deschis; după închidere, înlocuirea merge."""
        f, tmp = scrie(self.d / "stare.json", b"{}"), scrie(self.d / "stare.tmp", b"[]")
        with SZ._deschide(f):
            with self.assertRaises(PermissionError):
                os.replace(tmp, f)
        os.replace(tmp, f)
        self.assertEqual(f.read_bytes(), b"[]")

    def test_lantul_vechi_isi_reincearca_scrierea_starii(self):
        """lant_zilnic.scrie_stare, cât panoul îi ține starea deschisă: reîncearcă înlocuirea de 5 ori, la 0,2 s. Dacă panoul
        o închide între timp, starea se scrie; altfel lanțul notează că n-a putut-o scrie (descrierea modulului)."""
        from romana import lant_zilnic
        f = self.d / "2026-06-09" / "stare.json"
        for inchisa_la, pauze_asteptate, scrisa in ((1, [0.2], True), (None, [0.2] * 4, False)):
            with self.subTest(inchisa_la=inchisa_la):
                scrie(f, b"{}")
                tinut, pauze, note = SZ._deschide(f), [], []
                self.addCleanup(tinut.close)

                def pauza(s, tinut=tinut, pauze=pauze, inchisa_la=inchisa_la):
                    pauze.append(s)
                    if len(pauze) == inchisa_la:
                        tinut.close()                      # panoul a terminat de citit

                with mock.patch.object(lant_zilnic, "DIR_LANT", self.d), mock.patch.object(lant_zilnic.time, "sleep", pauza):
                    lant_zilnic.scrie_stare("2026-06-09", {"rezultat": "in_curs"}, note.append)
                tinut.close()
                self.assertEqual(pauze, pauze_asteptate)
                self.assertEqual(json.loads(f.read_bytes()).get("rezultat"), "in_curs" if scrisa else None)
                self.assertEqual(len(note), 0 if scrisa else 1)
                if note:
                    self.assertIn("nu s-a putut scrie", note[0])
                    self.assertIn("PermissionError", note[0])


class TestCeSeDeschide(Baza):
    """Descrierea modulului: fișierele colectării se deschid toate prin `_deschide`, iar starea unui lanț de noapte o citește
    întâi `fisa_senzor.stare_lant`, neschimbată, cu o deschidere obișnuită; doar citirile ei de aici (atenționarea,
    verificarea lanțului vechi) trec prin `_deschide`."""

    def test_deschiderile_unui_calcul(self):
        acum = Z(10, 3, 45)        # după ora măsurii noi, încă fără starea ei: aceasta citește și starea lanțului vechi
        self.scrie_stare(1, acum)
        scrie(self.num / "numaratori_2026-06-10.csv",
              csv_text(CAP_NUMARATORI, sfert(Z(10, 3, 15), intrari=[("magheru", "autoturism", 10)],
                                             pietoni=[("magheru", "z1", 3)])), acum - 60)
        scrie_veghe(self.loguri / "veghe_2026-06-10.csv", randuri_veghe(Z(10, 3, 30), Z(10, 3, 44)), acum - 30)
        scrie(self.loguri / "veghe_alerta_2026-06-10_031000.json",
              json.dumps({"semne": ["fără cadre: niciun cadru prelucrat de 181 s"], "ora": "2026-06-10T03:10:00"}),
              Z(10, 3, 10))
        scrie(self.loguri / "paznic_2026-06-10.log", nota(Z(10, 3), IN_REGULA), Z(10, 3))
        scrie(self.lant / "2026-06-09" / "stare.json",          # „gata” cu un cod acceptat: se citește și atenționarea
              stare_lant("2026-06-09", "2026-06-10T00:15:00", "gata_fara_simulari",
                         {"repara": (2, "2026-06-10T00:15:01", "2026-06-10T00:15:30"),
                          "recount": (0, "2026-06-10T00:15:30", "2026-06-10T00:17:20")}, atentie="membri stricați"))
        scrie(self.cor / "2026-06-08" / "stare.json",
              stare_lant("2026-06-08", "2026-06-09T03:30:00", "gata_fara_simulari",
                         {"publica": (0, "2026-06-09T03:30:00", "2026-06-09T03:39:59")}))
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_json("2026-06-06T00:00:00"))
        deschide, deschide_io, prin_deschide, obisnuite = SZ._deschide, io.open, [], []

        def nume(f) -> str:
            try:
                return Path(f).relative_to(self.d).as_posix()
            except ValueError:
                return str(f)

        def coduri(cadru):
            while cadru is not None:
                yield cadru.f_code
                cadru = cadru.f_back

        def partajat(f):
            prin_deschide.append(nume(f))
            return deschide(f)

        def obisnuit(fisier, *a, **k):
            if isinstance(fisier, (str, os.PathLike)):
                cine = set(coduri(sys._getframe(1)))
                if deschide.__code__ not in cine:          # în afara lui _deschide (pe Windows, acesta deschide un fd)
                    obisnuite.append((nume(fisier), fs.stare_lant.__code__ in cine))
            return deschide_io(fisier, *a, **k)

        with mock.patch.object(SZ, "_deschide", partajat), mock.patch("builtins.open", obisnuit), \
                mock.patch("io.open", obisnuit):
            r = self.stare(acum)
        self.assertEqual([v.get("eroare") for v in r["verigi"]], [None] * 5)
        self.assertEqual([(x["zi"], x["stare"]) for x in r["verigi"][4]["lanturi"]],
                         [("2026-06-09", "incheiat"), ("2026-06-08", "lipsa")])
        self.assertIsNotNone(r["fisa"])
        colectarea = {"live/state.json", "counts/numaratori_2026-06-10.csv", "logs/veghe_2026-06-10.csv",
                      "logs/veghe_alerta_2026-06-10_031000.json", "logs/paznic_2026-06-10.log",
                      "docs_rezultate/fisa_senzor_2026-06-06_0000.json"}
        self.assertEqual(set(prin_deschide), colectarea | {"lant/2026-06-09/stare.json"})
        self.assertEqual(set(obisnuite), {("lant/2026-06-09/stare.json", True), ("lant_cor/2026-06-08/stare.json", True)})

    def test_colectarea_sare_rescrierea_starii_live(self):
        """run_vision (nu se importă aici: aduce modelul și camera) înlocuiește state.json într-un try care, la
        PermissionError, trece mai departe: sare rescrierea, cum spune descrierea modulului."""
        import ast
        arbore = ast.parse((SRC / "romana" / "vision" / "run_vision.py").read_text(encoding="utf-8"))
        sarituri = [n for n in ast.walk(arbore) if isinstance(n, ast.Try)
                    and any(".replace(" in ast.unparse(x) and "'state.json'" in ast.unparse(x) for x in n.body)
                    and any(h.type is not None and ast.unparse(h.type) == "PermissionError"
                            and all(isinstance(y, ast.Pass) for y in h.body) for h in n.handlers)]
        self.assertEqual(len(sarituri), 1)


class TestCuratarea(unittest.TestCase):
    def test_caile_devin_puncte_de_suspensie(self):
        self.assertEqual(SZ.curata(r"jurnal: C:\Users\Cineva\x.log, gata"), "jurnal: … gata")
        self.assertEqual(SZ.curata("copie în C:/Users/Cineva/y.csv și D:\\date\\z"), "copie în … și …")
        self.assertEqual(SZ.curata(r"vezi /c/Users/Cineva/a.txt, \\server\Users\Cineva\b și ~\c.txt"), "vezi … … și …")
        self.assertEqual(SZ.curata(str(Path.home() / "AppData" / "q.log") + " lipsește"), "… lipsește")
        # dintr-o eroare: repr-ul căii are \\ dublate, între ghilimele care rămân
        text = SZ.curata(r"(PermissionError(13, 'Permission denied', 'C:\\Users\\Cineva\\Documents\\x.csv'))")
        self.assertEqual(text, "(PermissionError(13, 'Permission denied', '…'))")

    def test_cai_cu_spatii_intre_ghilimele_si_de_retea(self):
        for text, curatat in (
                (r'"C:\Program Files (x86)\sumo\bin\sumo.exe" a eșuat', '"…" a eșuat'),
                (r"deschis 'C:\Users\Ana Maria\Documents\x.csv' de altcineva", "deschis '…' de altcineva"),
                (r"jurnal C:\Program Files\Python312\python.exe lipsește", "jurnal … lipsește"),
                (r"D:\date secrete\x.csv lipsește", "… lipsește"),
                (r"C:\x.log, D:\y.log; gata", "… … gata"),
                (r"copie în \\HOST\share\x.log", "copie în …"),
                (r"copie în \\CALCULATOR\c$\Users\Cineva\x.log și gata", "copie în … și gata"),
                (r"\\?\C:\Users\Cineva\x", "…"),
                (r"(OSError(22, 'x', '\\\\HOST\\share\\y'))", "(OSError(22, 'x', '…'))"),
                ("fișierul ..\\..\\Users\\Cineva\\x.log", "fișierul …"),
                (r"Users\Cineva\Documents\x.log", "…"),
                ("file:///C:/Users/Cineva/x.html", "file:///…")):
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), curatat)

    def test_cai_peste_spatii_cu_bara_cu_apostrof_si_de_retea_cu_bara(self):
        """Șirurile revizorului (R1-3): o cale fără ghilimele ține peste spații până la ultima ei parte cu separator, \\ sau
        /; una între ghilimele se închide doar la o ghilimea urmată de un spațiu, de un semn sau de capăt; //calculator/…
        e tot o cale de rețea; parantezele deschise înaintea unei căi rămân."""
        for text, curatat in (
                (r"C:\Program Files (x86)\sumo\bin\sumo.exe a eșuat", "… a eșuat"),
                (r"C:/Program Files/Python312/python.exe", "…"),
                (r"C:/Users/Ana Maria/x.csv", "…"),
                (r"'C:\Users\O'Brien\x.csv'", "'…'"),
                (r"//server/share/x.log", "…"),
                (r"(C:\x) și [D:\y]", "(…) și […]"),
                (r"\\server\share\Ana Maria\x.log nu răspunde", "… nu răspunde"),
                ("/c/Users/Ana Maria/x.csv e folosit", "… e folosit"),
                (r"~\My Documents\x.txt lipsește", "… lipsește"),
                (r"(vezi C:\x(1)), apoi [C:\Program Files (x86)\x] și {~\y}.", "(vezi …), apoi […] și {…}."),
                ("C://Users//Cineva//x", "…"),
                ("https://x.ro/" + Path.home().as_posix() + "/y.html", "https://x.ro/…")):   # dosarul utilizatorului, și aici
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), curatat)

    def test_o_cale_de_disc_dintr_o_adresa_web_se_ascunde(self):
        """O adresă web rămâne, dar se oprește înaintea unei căi de disc nelipite de o literă, care se curăță ca oricare
        alta („fișier:///C:/…” → „fișier:///…”); după „_” sau o literă cu diacritice, o cale de rețea lipită de adresă se
        ascunde și ea (N1). Adresele fără cale rămân întregi (RB-1)."""
        for text, curatat in (
                ("http://localhost:8050/fisier?cale=C:/Users/Ana/x.csv", "http://localhost:8050/fisier?cale=…"),
                ("https://x.ro/?f=D:/proiecte/Ana/x.csv nu merge", "https://x.ro/?f=… nu merge"),
                ("https://x.ro/C:/Users/Ana/x.html", "https://x.ro/…"),
                ("https://x.ro/D:/date secrete/x.csv", "https://x.ro/…"),
                (r"rtsp://u:p@cam/C:\Users\Ana\x", "rtsp://u:p@cam/…"),
                ("fișier:///C:/Users/Ana/x.html", "fișier:///…"),
                ("ăhttps://x.ro/C:/Users/Ana/y", "ăhttps://x.ro/…"),
                # după „_” sau o literă cu diacritice, adresa începe acolo, iar o cale de rețea lipită de ea se ascunde (N1)
                (r"eroare_https://x.ro\\srv\share\Ana Maria\x.log", "eroare_https://x.ro…"),
                (r"ăhttp://x.ro\\srv\Ana\x", "ăhttp://x.ro…"),
                (r"fișier_http://x\\srv\Ana\x", "fișier_http://x…")):
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), curatat)
        for text in ("https://web.archive.org/web/2020/https://x.ro/a", "http://host:8050/a:b/c",
                     "ws://localhost:8050/x și wss://x.ro/y", "https://user:parola@x.ro/a", "mailto:ana@x.ro",
                     "„https://x.ro/a” și «https://x.ro/b»"):
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), text)

    def test_dupa_o_cale_fara_ghilimele_si_unitatea_se_duce(self):
        """O cale fără ghilimele ia cu ea și un cuvânt cu \\ sau / aflat la cel mult două cuvinte după ea (o unitate, o
        fracție, o oră cu /), cu tot ce e între ele: nu se poate deosebi de o parte a căii („…\\Ana Maria/Desktop”), iar mai
        bine prea mult decât o bucată de cale (RB-2). După o cale încheiată cu un semn, sau mai departe, ce urmează rămâne."""
        for text, curatat in ((r"C:\live\state.json are 3,5 cadre/s", "…"),
                              (r"C:\x.log a eșuat 12:30/12:45", "…"),
                              (r"C:\Users\Ana Maria/Desktop", "…"),
                              (r"C:\x.log, are 3,5 cadre/s", "… are 3,5 cadre/s"),
                              (r"C:\x.log are trei cuvinte fără 3,5 cadre/s", "… are trei cuvinte fără 3,5 cadre/s"),
                              ("are 3,5 cadre/s", "are 3,5 cadre/s")):
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), curatat)

    def test_textul_se_taie_inaintea_tiparelor_fara_cuvantul_taiat(self):
        """Se curăță cel mult CITIT_MAXIM × MAX_TEXT caractere. Dacă tăietura cade într-un cuvânt, acesta se lasă deoparte: o
        cale cu spații, tăiată pe la mijloc, nu mai lasă să se vadă bucata dinaintea tăieturii („Ma”)."""
        lung = SZ.CITIT_MAXIM * SZ.MAX_TEXT
        cale = r"C:\Users\Ana Maria\x.csv"
        text = "a" + " " * (lung - 1 - len(r"C:\Users\Ana Ma")) + cale
        self.assertEqual(text[lung - 2:lung + 1], "Mar")                      # tăietura cade între „Ma” și „ria”
        self.assertEqual(SZ.curata(text), "a …")
        self.assertEqual(SZ.curata("a" + " " * lung + cale), "a…")             # între cuvinte: restul nu se mai vede
        self.assertEqual(SZ.curata("b" * (lung + 10)), "b" * (SZ.MAX_TEXT - 1) + "…")   # un singur cuvânt: începutul lui
        self.assertEqual(SZ.curata("b" * lung), "b" * (SZ.MAX_TEXT - 1) + "…")         # chiar la limită: netăiat

    def test_un_cuvant_foarte_lung_se_curata_repede(self):
        """curata rulează sub lacătul serverului, iar pagina renunță după 4 s: un singur cuvânt de 32 000 de caractere, cu
        sau fără „Users\\”, se curăță sub 0,5 s (înainte, ≈10 s). Tiparele merg în timp liniar și fără tăietură (R1-4)."""
        n = 32_000
        for nume, text in (("litere", "a" * n), ("cu Users\\ la capăt", "a" * (n - 9) + "Users\\x1"),
                           ("cu Users\\ la început", "Users\\" + "a" * (n - 6)), ("Users repetat", "Users" * (n // 5)),
                           ("C:\\ repetat", "C:\\" * (n // 3)), ("'C:\\ repetat", "'C:\\" * (n // 4)), ("\\", "\\" * n),
                           ("/", "/" * n), ("a\\ repetat", "a\\" * (n // 2)), ("ab+ repetat", "ab+" * (n // 3)),
                           ("x: repetat", "x:" * (n // 2)), ("~\\ repetat", "~\\" * (n // 2)),
                           ("cuvinte după C:\\x", "C:\\x" + " a" * (n // 2)), ("'C:\\x repetat", "'C:\\x " * (n // 6))):
            with self.subTest(text=nume):
                t0 = time.perf_counter()
                curatat = SZ.curata(text)
                t1 = time.perf_counter()
                SZ._fara_cai(text)                                             # toate tiparele, pe tot textul
                list(SZ.ADRESA_WEB.finditer(text))
                t2 = time.perf_counter()
                self.assertLessEqual(len(curatat), SZ.MAX_TEXT)
                self.assertNotIn("Users\\", curatat)
                self.assertLess(t1 - t0, 0.5)
                self.assertLess(t2 - t1, 0.5)

    def test_ce_nu_e_o_cale_ramane(self):
        for text in ("playlist https://hls.webcamromania.ro/romana/index.m3u8 nu răspunde",
                     "vezi http://127.0.0.1:8050/?imagine=0",
                     "https://example.com/users/5", "(vezi https://example.com/users/5)", "rtsp://camera/users/x nu răspunde",
                     "50 km/h, 1/2 din ore, 09/11, N/S, 08:15/08:30, pe Magheru:\\Dacia",
                     "rata mică: 3.4 cadre/s (mediana ultimelor 3 min)",
                     "ora 12:30:15 fără cadre 12 s (playlist: ultimul segment în urmă -10 s)",
                     "%USERPROFILE%\\Documents\\x.log",
                     *(text for _, text in REPORNIRE)):
            with self.subTest(text=text):
                self.assertEqual(SZ.curata(text), text)

    def test_dosarul_utilizatorului_cu_separatori_dublati(self):
        """Dosarul utilizatorului se ascunde și cu separatorii dublați („C://Users//…”, „C:\\\\Users\\\\…”), chiar
        lipit de un cuvânt, unde textul pare o adresă web cu schema „fisierulC” (N-RB4-1)."""
        with mock.patch.object(Path, "home", return_value=Path("C:/Users/Ana")):
            acasa = SZ._acasa()
        with mock.patch.object(SZ, "ACASA", acasa):
            for text, curatat in (("fisierulC://Users/Ana/x", "fisierul…"),
                                  ("fisierulC://Users//Ana//x.csv e folosit", "fisierul… e folosit"),
                                  ("fisierulC:/Users/Ana/x", "fisierul…"),
                                  (r"eroare: C:\\Users\\Ana\\x.csv", "eroare: …"),
                                  ("https://x.ro/C://Users/Ana/x", "https://x.ro/…"),
                                  ("vezi //c//Users/Ana/x", "vezi …")):
                with self.subTest(text=text):
                    self.assertEqual(SZ.curata(text), curatat)

    def test_dosarul_utilizatorului_nu_ramane_dupa_o_adresa(self):
        """Plasa de siguranță de la capătul lui curata: o „adresă” lipită de dosar se oprește la \\ sau la spațiu,
        deci dosarul de după ea nu mai începe cu C: și scăpa („cuvantC://Users\\\\…”, N-RB4b-1); acum nu rămâne."""
        for acasa_, nume in (("C:/Users/Ana", "Ana"), ("C:/Users/Ana Maria", "Ana Maria")):
            with mock.patch.object(Path, "home", return_value=Path(acasa_)):
                acasa = SZ._acasa()
            with mock.patch.object(SZ, "ACASA", acasa):
                for text, curatat in (("cuvantC://Users\\" + nume, "cuvant…"),
                                      ("eroare://c//Users\\" + nume, "eroare:…"),
                                      ("https://a.ro//c/Users\\" + nume + "/x", "https://a.ro…"),
                                      ("fisierulC://Users//" + nume + "/x gata", "fisierul… gata"),
                                      ("fisierulC://Users\\" + nume + "\\x.log", None)):
                    with self.subTest(text=text):
                        rezultat = SZ.curata(text)
                        self.assertNotIn("ana", rezultat.lower())
                        if curatat is not None:
                            self.assertEqual(rezultat, curatat)

    def test_un_nume_de_utilizator_cu_spatiu(self):
        with mock.patch.object(Path, "home", return_value=Path("C:/Users/Ana Maria")):
            acasa = SZ._acasa()
        self.assertEqual(acasa.sub("…", r"C:\Users\Ana Maria\Documents\x.csv e folosit"), "… e folosit")
        self.assertEqual(acasa.sub("…", "/c/Users/Ana Maria/x și c:/users/ana maria/y"), "… și …")

    def test_spatiile_si_lungimea(self):
        self.assertEqual(SZ.curata("pornit:   lansatorul\tare\nPID 7792 "), "pornit: lansatorul are PID 7792")
        lung = SZ.curata("a" * 300)
        self.assertEqual((len(lung), lung[-1], lung[:5]), (200, "…", "aaaaa"))
        self.assertEqual(SZ.curata("b" * 200), "b" * 200)


class TestCamera(Baza):
    def test_fara_stare_e_o_problema(self):
        v = self.veriga("camera")
        self.assertEqual((v["stare"], v["lipsa"]), ("problema", True))
        self.assertEqual([v[k] for k in ("ultima_dovada", "varsta_s", "conectat", "fps")], [None] * 4)
        self.assertEqual((v["prag_s"], v["alerta_s"], v["rosu_s"], v["prag_fps"]), (15, 180, 600, 3.5))

    def test_pragurile_varstei(self):
        for varsta, stare in ((0.3, "ok"), (14.9, "ok"), (15, "atent"), (180, "atent"), (599.9, "atent"),
                              (600, "problema"), (86400, "problema")):
            with self.subTest(varsta=varsta):
                self.scrie_stare(varsta)
                v = self.veriga("camera")
                self.assertEqual((v["stare"], v["varsta_s"], v["lipsa"]), (stare, varsta, False))
                self.assertAlmostEqual(v["ultima_dovada"], ACUM - varsta, places=3)
                self.assertEqual((v["conectat"], v["fps"]), (True, 6.0))

    def test_o_rata_prea_mare_pentru_float_lipseste(self):
        """O rată de cadre scrisă ca întreg prea mare pentru float (un JSON stricat) lipsește, fără excepție (N2), la fel
        ca un bool, care nu e un număr (N-RB4-2)."""
        for fps in (10 ** 400, True):
            with self.subTest(fps=fps):
                self.scrie_stare(1, fps=fps)
                v = self.veriga("camera")                           # veriga() verifică și că nu e o eroare
                self.assertEqual((v["fps"], v["stare"]), (None, "ok"))

    def test_proaspata_dar_fara_flux_sau_cu_prea_putine_cadre(self):
        for campuri, stare in (({"conectat": False}, "atent"), ({"fps": 3.4}, "atent"), ({"fps": 3.5}, "ok"),
                               ({"fps": None}, "ok")):
            with self.subTest(campuri=campuri):
                self.scrie_stare(1, **campuri)
                self.assertEqual(self.veriga("camera")["stare"], stare)
        self.scrie_stare(20, conectat=False, fps=1.0)
        self.assertEqual(self.veriga("camera")["stare"], "atent")

    def test_starea_care_nu_se_poate_citi_e_necunoscuta(self):
        for continut, incercari in ((b'{"timestamp": 17', 3), (b"", 3), ('{"nota": "ă"}'.encode("cp1250"), 3),
                                    (b"[1, 2]", 1), (b"null", 1)):
            with self.subTest(continut=continut), mock.patch.object(SZ.time, "sleep") as dormi:
                scrie(self.live / "state.json", continut, ACUM - 1)
                v = self.veriga("camera")
                self.assertEqual((v["stare"], v["lipsa"], v["varsta_s"], v["fps"]), ("necunoscut", False, 1.0, None))
                self.assertEqual(dormi.call_count, incercari - 1)

    def test_se_reincearca_cand_starea_tocmai_e_inlocuita(self):
        self.scrie_stare(1)
        citeste = SZ._octeti
        raspunsuri = [PermissionError(13, "fișier folosit"), b'{"timestamp": 17', None]    # None: citirea adevărată

        def citire(f, maxim=None):
            if Path(f).name != "state.json":
                return citeste(f, maxim)
            r = raspunsuri.pop(0)
            if isinstance(r, Exception):
                raise r
            return citeste(f, maxim) if r is None else r

        with mock.patch.object(SZ, "_octeti", citire), mock.patch.object(SZ.time, "sleep") as dormi:
            v = self.veriga("camera")
        self.assertEqual((v["stare"], raspunsuri), ("ok", []))
        self.assertEqual([c.args for c in dormi.call_args_list], [(SZ.PAUZA_STARE_S,)] * 2)

    def test_o_stare_prea_mare_nu_se_citeste(self):
        self.scrie_stare(1, nota="x" * 100)
        with mock.patch.object(SZ, "MARIME_JSON", 50), mock.patch.object(SZ.time, "sleep") as dormi:
            v = self.veriga("camera")
        self.assertEqual((v["stare"], v["varsta_s"], dormi.call_count), ("necunoscut", 1.0, 0))

    def test_starea_scrisa_chiar_in_timpul_calculului_are_varsta_0(self):
        self.scrie_stare(-0.4)                                  # înlocuită după ce s-a luat ora calculului
        v = self.veriga("camera")
        self.assertEqual((v["stare"], v["varsta_s"]), ("ok", 0.0))
        self.assertAlmostEqual(v["ultima_dovada"], ACUM + 0.4, places=3)

    def test_starea_cu_bom(self):
        scrie(self.live / "state.json", b"\xef\xbb\xbf" + json.dumps({"fps": 6.0, "conectat": True}).encode(), ACUM - 1)
        self.assertEqual(self.veriga("camera")["stare"], "ok")


class TestColectarea(Baza):
    def scrie_ziua(self, zi: int, randuri: list[list], final: str = "", ora: float | None = None) -> Path:
        """Fișierul zilei; data lui e `ora` sau încheierea ultimului sfert, când l-a scris colectarea."""
        if ora is None and randuri:
            ora = max(fs.ora(r[1]) for r in randuri)
        return scrie(self.num / f"numaratori_2026-06-{zi:02d}.csv", csv_text(CAP_NUMARATORI, randuri) + final, ora)

    def test_ultimul_sfert_si_vehiculele_urmarite(self):
        self.scrie_ziua(10, sfert(Z(10, 7, 45), [("magheru", "passenger", 400)], pietoni=[("magheru", "trecere_magheru", 50)])
                        + sfert(Z(10, 8), [("magheru", "passenger", 500), ("dacia_est", "bus", 7), ("catargiu", "bicycle", 2)],
                                iesiri=[("catargiu", "passenger", 300)], viraje=[("magheru", "catargiu", "passenger", 250)],
                                pietoni=[("dacia_est", "trecere_dacia_est_iesire", 200), ("magheru", "trecere_magheru", 66)]))
        acum = Z(10, 8, 15) + 365.4
        self.scrie_stare(1, acum)
        v = self.veriga("colectarea", acum)
        self.assertEqual(v["sfert"], {"zi": "2026-06-10", "inceput": "08:00", "sfarsit": "08:15", "vehicule_intrate": 509,
                                      "pietoni": 266})
        self.assertEqual((v["stare"], v["ultima_dovada"], v["varsta_s"], v["vehicule_urmarite"]),
                         ("ok", Z(10, 8, 15), 365.4, 82))
        self.assertEqual((v["prag_s"], v["interval_s"], v["rosu_s"]), (1020, 900, 3600))

    def test_vehiculele_urmarite_doar_cu_camera_proaspata(self):
        self.scrie_ziua(10, sfert(Z(10, 8), [("magheru", "passenger", 5)]))
        self.assertIsNone(self.veriga("colectarea")["vehicule_urmarite"])           # fără stare live
        self.scrie_stare(15)
        self.assertIsNone(self.veriga("colectarea")["vehicule_urmarite"])           # veche
        self.scrie_stare(14.9, conectat=False)
        self.assertEqual(self.veriga("colectarea")["vehicule_urmarite"], 82)

    def test_un_numar_pe_care_pagina_nu_l_ar_citi_exact_lipseste(self):
        """Un rând al numărătorilor cu un număr de peste 2**53 (un CSV stricat) se sare, iar vehiculele urmărite de felul
        acesta lipsesc: pagina (JavaScript) le-ar citi rotunjite sau ca Infinity (RB-3). La fel un întreg prea mare
        pentru float, fără excepție, unul rotunjit de float și un bool, care nu e un număr (N2, N3)."""
        stricat = [text_ora(Z(10, 8)), text_ora(Z(10, 8) + 900), "intrare", "magheru", "", "passenger", "9" * 400]
        self.scrie_ziua(10, sfert(Z(10, 8), [("magheru", "passenger", 500)], pietoni=[("magheru", "trecere_magheru", 66)])
                        + [stricat])
        acum = Z(10, 8, 20)
        self.scrie_stare(1, acum, vehicule_urmarite=2 ** 60)
        v = self.veriga("colectarea", acum)
        self.assertEqual((v["sfert"]["vehicule_intrate"], v["sfert"]["pietoni"], v["vehicule_urmarite"], v["stare"]),
                         (500, 66, None, "ok"))
        json.dumps(v, allow_nan=False)
        self.scrie_stare(1, acum, vehicule_urmarite=2 ** 53)                        # chiar la limită: rămâne
        self.assertEqual(self.veriga("colectarea", acum)["vehicule_urmarite"], 2 ** 53)
        for urmariti in (10 ** 400, 2 ** 53 + 1, True):
            with self.subTest(urmariti=urmariti):
                self.scrie_stare(1, acum, vehicule_urmarite=urmariti)
                v = self.veriga("colectarea", acum)
                self.assertEqual((v["vehicule_urmarite"], v["stare"], v["sfert"]["vehicule_intrate"]), (None, "ok", 500))

    def test_pragurile(self):
        # de la 2 s după scriere: mai devreme, sfertul poate fi încă pe jumătate (testul de mai jos)
        self.scrie_ziua(10, sfert(Z(10, 8), [("magheru", "passenger", 5)]))
        for varsta, stare in ((2, "ok"), (1020, "ok"), (1020.1, "atent"), (3600, "atent"), (3600.1, "problema")):
            with self.subTest(varsta=varsta):
                v = self.veriga("colectarea", Z(10, 8, 15) + varsta)
                self.assertEqual((v["stare"], v["varsta_s"]), (stare, varsta))

    def test_un_sfert_scris_chiar_acum_poate_fi_pe_jumatate(self):
        """Colectarea scrie un sfert de peste 8 KB din mai multe scrieri (od_counter.write_csv, prin zona tampon a
        fișierului): dintr-un fișier scris acum mai puțin de 2 s se ia sfertul dinaintea ultimului."""
        self.scrie_ziua(10, sfert(Z(10, 7, 45), [("magheru", "passenger", 400)])
                        + sfert(Z(10, 8), [("magheru", "passenger", 500)]))           # scris la 08:15
        v = self.veriga("colectarea", Z(10, 8, 15, 1.9))
        self.assertEqual((v["sfert"]["inceput"], v["sfert"]["vehicule_intrate"], v["varsta_s"], v["stare"]),
                         ("07:45", 400, 901.9, "ok"))
        v = self.veriga("colectarea", Z(10, 8, 15, 2))
        self.assertEqual((v["sfert"]["inceput"], v["sfert"]["vehicule_intrate"], v["varsta_s"]), ("08:00", 500, 2))
        self.scrie_ziua(10, sfert(Z(10, 8), [("magheru", "passenger", 500)]), ora=ACUM)    # rescris chiar acum
        self.assertEqual(self.veriga("colectarea")["stare"], "necunoscut")              # niciun sfert sigur întreg

    def test_in_scriere_sfertul_dinainte_se_citeste_intreg(self):
        mare = sfert(Z(10, 7, 45), [("catargiu", "passenger", 11), ("magheru", "passenger", 22)],
                     iesiri=[("magheru", f"clasa_{k}", 1) for k in range(600)])     # ≈ 40 KB după intrări
        self.scrie_ziua(10, sfert(Z(10, 7, 30), [("magheru", "passenger", 1)]) + mare
                        + sfert(Z(10, 8), [("magheru", "passenger", 5)]))
        v = self.veriga("colectarea", Z(10, 8, 15, 1))
        self.assertEqual((v["sfert"]["inceput"], v["sfert"]["vehicule_intrate"]), ("07:45", 33))

    def test_primul_sfert_al_zilei_in_scriere_lasa_sfertul_de_ieri(self):
        self.scrie_ziua(10, sfert(Z(10, 23, 45), [("magheru", "passenger", 30)]))
        self.scrie_ziua(11, sfert(Z(11, 0), [("magheru", "passenger", 12)]))        # fișierul nou, scris la 00:15
        v = self.veriga("colectarea", Z(11, 0, 15, 0.5))
        self.assertEqual((v["sfert"]["zi"], v["sfert"]["inceput"], v["sfert"]["vehicule_intrate"], v["varsta_s"]),
                         ("2026-06-10", "23:45", 30, 900.5))

    def test_fara_fisier_e_necunoscuta(self):
        v = self.veriga("colectarea")
        self.assertEqual((v["stare"], v["sfert"], v["ultima_dovada"], v["varsta_s"]), ("necunoscut", None, None, None))
        self.scrie_ziua(10, [])                                                      # doar antetul
        self.assertEqual(self.veriga("colectarea")["stare"], "necunoscut")

    def test_doar_fisierele_de_azi_si_de_ieri(self):
        self.scrie_ziua(8, sfert(Z(8, 23, 45), [("magheru", "passenger", 5)]))      # alaltăieri
        self.scrie_ziua(11, sfert(Z(11, 0), [("magheru", "passenger", 5)]))         # mâine
        self.assertEqual(self.veriga("colectarea")["stare"], "necunoscut")
        self.scrie_ziua(9, sfert(Z(9, 23, 45), [("magheru", "passenger", 9)]))      # ieri
        v = self.veriga("colectarea")
        self.assertEqual((v["sfert"]["zi"], v["sfert"]["vehicule_intrate"], v["stare"]), ("2026-06-09", 9, "problema"))

    def test_dupa_miezul_noptii_sfertul_de_ieri(self):
        self.scrie_ziua(10, sfert(Z(10, 23, 30), [("magheru", "passenger", 40)])
                        + sfert(Z(10, 23, 45), [("magheru", "passenger", 30)], pietoni=[("magheru", "trecere_magheru", 4)]))
        v = self.veriga("colectarea", Z(11, 0, 5))
        self.assertEqual(v["sfert"], {"zi": "2026-06-10", "inceput": "23:45", "sfarsit": "00:00", "vehicule_intrate": 30,
                                      "pietoni": 4})
        self.assertEqual((v["stare"], v["varsta_s"]), ("ok", 300))
        self.scrie_ziua(11, sfert(Z(11, 0), [("magheru", "passenger", 12)]))        # primul sfert al zilei noi
        v = self.veriga("colectarea", Z(11, 0, 16))
        self.assertEqual((v["sfert"]["zi"], v["sfert"]["inceput"], v["sfert"]["vehicule_intrate"], v["varsta_s"]),
                         ("2026-06-11", "00:00", 12, 60))

    def test_coada_incepe_in_mijlocul_unui_rand_iar_ultimul_e_inca_in_scriere(self):
        randuri = []
        for k in range(34):              # 00:00–08:30, cu multe viraje: fișierul trece de câteva ori de coada citită
            randuri += sfert(Z(10, 0) + 900 * k, [("magheru", "passenger", 100 + k)],
                             viraje=[("magheru", "catargiu", "passenger", n) for n in range(30)])
        final = "2026-06-10 08:30:00,2026-06-10 08:45:00,intrare,magheru,,passenger,5"     # fără sfârșit de rând
        f = self.scrie_ziua(10, randuri, final)
        date = f.read_bytes()
        self.assertGreater(len(date), 3 * SZ.COADA_NUMARATORI)
        self.assertNotEqual(date[len(date) - SZ.COADA_NUMARATORI - 1], ord("\n"))    # coada nu începe cu un rând întreg
        v = self.veriga("colectarea", Z(10, 8, 31))
        self.assertEqual((v["sfert"]["inceput"], v["sfert"]["sfarsit"], v["sfert"]["vehicule_intrate"]),
                         ("08:15", "08:30", 133))

    def test_un_sfert_mai_lung_decat_coada_se_citeste_intreg(self):
        mare = sfert(Z(10, 8), [("catargiu", "passenger", 11), ("magheru", "passenger", 22)],
                     iesiri=[("magheru", f"clasa_{k}", 1) for k in range(600)])     # ≈ 40 KB după intrări
        self.scrie_ziua(10, sfert(Z(10, 7, 45), [("magheru", "passenger", 1)]) + mare)
        self.assertEqual(self.veriga("colectarea", Z(10, 8, 16))["sfert"]["vehicule_intrate"], 33)


class TestVeghea(Baza):
    def csv_(self) -> Path:
        return self.loguri / "veghe_2026-06-01.csv"

    def alerta(self, t: float, semne=("fără cadre: niciun cadru prelucrat de 181 s",), continut=None, nume_la=None):
        nume = f"veghe_alerta_{datetime.fromtimestamp(nume_la or t):%Y-%m-%d_%H%M%S}.json"
        d = {"semne": list(semne), "ora": datetime.fromtimestamp(t).isoformat(timespec="seconds"),
             "stare_live": {"timestamp": t - 181, "fps": 6.0}, "metrici_jurnal": {"pasi": 100},
             "procese": [{"pid": 4321, "nume": "python.exe", "linia": "C:\\Users\\Cineva\\.venv\\Scripts\\python.exe -m x"}],
             "jurnal_erori_viziune": ["[hls] C:\\Users\\Cineva\\x"]}
        scrie(self.loguri / nume, json.dumps(d, ensure_ascii=False) if continut is None else continut, t)

    def fara_alerte(self) -> None:
        for x in self.loguri.glob("veghe_alerta_*.json"):
            x.unlink()

    def test_ultimul_rand_si_ultima_ora(self):
        schimbari = {"07:00": {"evenimente": pauza(Z(10, 6, 59, 40), 12)},                 # de acum mai bine de o oră
                     "08:10": {"evenimente": pauza(Z(10, 8, 9, 30), 25)},
                     "08:20": {"evenimente": "; ".join([pauza(Z(10, 8, 19, 5), 11), pauza(Z(10, 8, 19, 40), 14)])},
                     "08:29": {"fps": 6.01, "pauze_5min": 1, "episoade_flux_30min": 0}}
        scrie_veghe(self.csv_(), randuri_veghe(Z(10, 6), Z(10, 8, 29), schimbari), ACUM - 3.4)
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["varsta_s"], v["ultimul_rand"]), ("ok", 3.4, "2026-06-10 08:29"))
        self.assertAlmostEqual(v["ultima_dovada"], ACUM - 3.4, places=3)
        self.assertEqual((v["fps"], v["pauze_5min"], v["episoade_30min"]), (6.01, 1, 0))
        self.assertEqual((v["randuri_ora"], v["pauze_ora"], v["alerta"]), (60, 3, None))
        self.assertEqual((v["prag_s"], v["rosu_s"], v["prag_fps"], v["prag_pauze"], v["max_episoade"]),
                         (180, 600, 3.5, 10, 4))

    def test_pragurile(self):
        f = scrie_veghe(self.csv_(), randuri_veghe(Z(10, 7), Z(10, 8, 29)), ACUM)
        for varsta, stare in ((179.9, "ok"), (180, "atent"), (599.9, "atent"), (600, "problema")):
            with self.subTest(varsta=varsta):
                os.utime(f, (ACUM - varsta, ACUM - varsta))
                self.assertEqual(self.veriga("veghea")["stare"], stare)
        for ultimul, stare in (({"fps": 3.4}, "atent"), ({"fps": 3.5}, "ok"), ({"fps": ""}, "ok"),
                               ({"pauze_5min": 10}, "atent"), ({"pauze_5min": 9}, "ok"),
                               ({"episoade_flux_30min": 4}, "atent"), ({"episoade_flux_30min": 3}, "ok")):
            with self.subTest(ultimul=ultimul):
                scrie_veghe(f, randuri_veghe(Z(10, 7), Z(10, 8, 29), {"08:29": ultimul}), ACUM - 30)
                self.assertEqual(self.veriga("veghea")["stare"], stare)

    def test_un_numar_pe_care_pagina_nu_l_ar_citi_exact_lipseste_dar_conteaza(self):
        """Pauzele sau reconectările de peste 2**53 (un CSV stricat) lipsesc din răspuns, dar starea tot le socotește: de
        urmărit (RB-3), și când sunt prea mari chiar pentru float („1e400”, infinit; N4)."""
        f = self.csv_()
        for ultimul, camp in (({"pauze_5min": "1e20"}, "pauze_5min"), ({"episoade_flux_30min": "1e300"}, "episoade_30min"),
                              ({"pauze_5min": "1e400"}, "pauze_5min"), ({"pauze_5min": "9" * 400}, "pauze_5min"),
                              ({"pauze_5min": "inf"}, "pauze_5min"), ({"episoade_flux_30min": "1e400"}, "episoade_30min")):
            with self.subTest(ultimul=ultimul):
                scrie_veghe(f, randuri_veghe(Z(10, 7), Z(10, 8, 29), {"08:29": ultimul}), ACUM - 30)
                v = self.veriga("veghea")
                self.assertEqual((v[camp], v["stare"]), (None, "atent"))
                json.dumps(v, allow_nan=False)

    def test_fara_csv_e_necunoscuta(self):
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["ultima_dovada"], v["randuri_ora"], v["alerta"]), ("necunoscut", None, None, None))

    def test_doar_antetul(self):
        scrie_veghe(self.csv_(), [], ACUM - 30)
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["ultimul_rand"], v["fps"], v["randuri_ora"], v["pauze_ora"]), ("ok", None, None, 0, 0))

    def test_csv_cu_antetul_vechi(self):
        scrie_veghe(self.loguri / "veghe_2026-06-10_v1.csv", randuri_veghe(Z(10, 7, 50), Z(10, 8, 29)), ACUM - 20,
                    CAP_VEGHE_VECHI)
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["fps"], v["randuri_ora"], v["ultimul_rand"]), ("ok", 6.0, 40, "2026-06-10 08:29"))
        self.assertEqual((v["pauze_5min"], v["episoade_30min"], v["pauze_ora"]), (None, None, None))

    def test_cel_mai_nou_csv_dupa_data_fisierului(self):
        scrie_veghe(self.loguri / "veghe_2026-06-10.csv", randuri_veghe(Z(10, 6), Z(10, 6, 59)), Z(10, 7))
        scrie_veghe(self.csv_(), randuri_veghe(Z(10, 8), Z(10, 8, 29)), ACUM - 5)
        self.assertEqual(self.veriga("veghea")["ultimul_rand"], "2026-06-10 08:29")

    def test_alerta_din_ultimele_24_h_doar_ora_si_semnele(self):
        scrie_veghe(self.csv_(), randuri_veghe(Z(10, 8), Z(10, 8, 29)), ACUM - 3)
        self.alerta(ACUM - 23 * 3600, semne=["fără cadre: niciun cadru prelucrat de 181 s", "rata mică: în C:\\Users\\Cineva\\x"])
        self.alerta(ACUM - 25 * 3600)
        v = self.veriga("veghea")
        self.assertEqual(v["alerta"], {"ora": ACUM - 23 * 3600, "dupa_ultimul_rand": False,
                                       "semne": ["fără cadre: niciun cadru prelucrat de 181 s", "rata mică: în …"]})
        self.assertEqual(v["stare"], "ok")                                   # veghea a pornit din nou după ea

    def test_granita_de_24_h(self):
        self.alerta(ACUM - 86400 - 1)
        self.assertIsNone(self.veriga("veghea")["alerta"])
        self.alerta(ACUM - 86400)
        self.assertEqual(self.veriga("veghea")["alerta"]["ora"], ACUM - 86400)

    def test_ora_alertei_din_json_altfel_din_nume(self):
        self.alerta(ACUM - 25 * 3600, nume_la=ACUM - 3600)                  # JSON-ul spune 25 h: nu se arată
        self.assertIsNone(self.veriga("veghea")["alerta"])
        self.fara_alerte()
        # fără niciun CSV al vegherii, alerta e după ultimul rând
        self.alerta(ACUM - 3600, continut='{"semne": ["fără ca')            # tocmai se scrie: ora din nume, fără semne
        self.assertEqual(self.veriga("veghea")["alerta"], {"ora": ACUM - 3600, "semne": [], "dupa_ultimul_rand": True})
        self.alerta(ACUM - 1800, continut=json.dumps({"semne": ["pauze: 10 pauze"]}))     # fără `ora`: tot din nume
        self.assertEqual(self.veriga("veghea")["alerta"], {"ora": ACUM - 1800, "semne": ["pauze: 10 pauze"],
                                                           "dupa_ultimul_rand": True})

    def test_alerta_de_dupa_ultimul_rand_cu_veghea_tacuta_e_o_problema(self):
        f = scrie_veghe(self.csv_(), randuri_veghe(Z(10, 7), Z(10, 8, 26)), ACUM)
        for t_alerta, varsta, dupa, stare in ((ACUM - 190, 200, True, "problema"), (ACUM - 320, 200, True, "problema"),
                                              (ACUM - 321, 200, False, "atent"), (ACUM - 150, 100, True, "atent"),
                                              (ACUM - 650, 700, True, "problema")):
            with self.subTest(alerta=ACUM - t_alerta, varsta=varsta):
                self.fara_alerte()
                self.alerta(t_alerta)
                os.utime(f, (ACUM - varsta, ACUM - varsta))
                v = self.veriga("veghea")
                self.assertEqual((v["stare"], v["alerta"]["dupa_ultimul_rand"]), (stare, dupa))

    def test_alerta_pe_care_s_a_oprit_veghea_e_de_urmarit_de_indata(self):
        """O alertă la 10 s după un rând vechi de 40 s: veghea s-a oprit pe ea, dar tăcerea e încă sub 3 min (TM4)."""
        f = scrie_veghe(self.csv_(), randuri_veghe(Z(10, 7), Z(10, 8, 29)), ACUM - 40)
        self.alerta(ACUM - 30)
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["alerta"]["dupa_ultimul_rand"], v["varsta_s"]), ("atent", True, 40))
        self.fara_alerte()
        os.utime(f, (ACUM - 200, ACUM - 200))                               # la fel, cu veghea tăcută de 200 s
        self.alerta(ACUM - 190)
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["alerta"]["dupa_ultimul_rand"]), ("problema", True))

    def test_o_alerta_de_dinaintea_ultimului_rand_a_trecut(self):
        scrie_veghe(self.csv_(), randuri_veghe(Z(10, 7), Z(10, 8, 29)), ACUM - 40)
        self.alerta(ACUM - 40 - 3 * 3600)                                    # cu 3 h înaintea ultimului rând
        v = self.veriga("veghea")
        self.assertEqual((v["stare"], v["alerta"]["dupa_ultimul_rand"]), ("ok", False))


class TestPaznicul(Baza):
    def jurnal(self, zi: int, *randuri: str) -> Path:
        return scrie(self.loguri / f"paznic_2026-06-{zi:02d}.log", "".join(randuri))

    def test_in_regula_o_data_pe_ora(self):
        self.jurnal(10, nota(Z(10, 6, 29, 47), IN_REGULA), nota(Z(10, 7, 29, 48), IN_REGULA))
        v = self.veriga("paznicul", Z(10, 7, 29, 48) + 3077.4)
        self.assertEqual((v["stare"], v["in_regula"], v["text"], v["varsta_s"]), ("ok", True, IN_REGULA, 3077.4))
        self.assertEqual(v["ultima_dovada"], Z(10, 7, 29, 48))
        self.assertEqual((v["prag_s"], v["semn_de_viata_s"], v["rosu_s"]), (3720, 3600, 7200))

    def test_pragurile(self):
        self.jurnal(10, nota(Z(10, 6), IN_REGULA))
        for varsta, stare in ((3720, "ok"), (3720.5, "atent"), (7200, "atent"), (7200.5, "problema")):
            with self.subTest(varsta=varsta):
                self.assertEqual(self.veriga("paznicul", Z(10, 6) + varsta)["stare"], stare)

    def test_repornirea_care_a_tinut_e_o_nota_buna(self):
        """Ziua de 8.11, mutată pe 10.06: după repornire, paznicul notează „repornirea ține de 600 s”, iar următorul „în
        regulă” vine abia la ora lui, după 50 min; nota de după repornire e una bună (NOTE_BUNE, BE1)."""
        def la(h: str) -> float:
            return Z(10, *map(int, h.split(":")))

        for cand, stare, ultima in (("11:27:40", "atent", "procesul nu se vede"), ("11:28:40", "atent", "run_vision pornit"),
                                    ("11:29:40", "ok", "în regulă"), ("11:39:40", "ok", "repornirea ține de"),
                                    ("11:45:00", "ok", "repornirea ține de"), ("12:00:00", "ok", "repornirea ține de"),
                                    ("12:29:00", "ok", "repornirea ține de"), ("12:29:40", "ok", "în regulă")):
            with self.subTest(ora=cand):
                self.jurnal(10, *(nota(la(h), text) for h, text in REPORNIRE if la(h) <= la(cand)))
                v = self.veriga("paznicul", la(cand))
                self.assertEqual((v["stare"], v["in_regula"]), (stare, stare == "ok"))
                self.assertTrue(v["text"].startswith(ultima), v["text"])

    def test_alta_nota_e_de_urmarit_iar_randurile_fara_ora_se_sar(self):
        self.jurnal(10, nota(Z(10, 7, 29), IN_REGULA), nota(Z(10, 8, 20), "oprire anunțată (fara_repornire): nu repornesc nimic"),
                    "Traceback (most recent call last):\n", '  File "x.py", line 1\n')
        v = self.veriga("paznicul")
        self.assertEqual((v["stare"], v["in_regula"], v["ultima_dovada"]), ("atent", False, Z(10, 8, 20)))
        self.assertEqual(v["text"], "oprire anunțată (fara_repornire): nu repornesc nimic")

    def test_fara_jurnal_e_necunoscut(self):
        v = self.veriga("paznicul")
        self.assertEqual((v["stare"], v["text"], v["in_regula"], v["ultima_dovada"]), ("necunoscut", None, None, None))

    def test_dupa_miezul_noptii_jurnalul_de_ieri(self):
        self.jurnal(9, nota(Z(9, 22, 29, 42), IN_REGULA), nota(Z(9, 23, 29, 43), IN_REGULA))
        v = self.veriga("paznicul", Z(10, 0, 10))
        self.assertEqual((v["stare"], v["ultima_dovada"], v["varsta_s"]), ("ok", Z(9, 23, 29, 43), 2417))

    def test_jurnalul_de_azi_fara_note_cu_ora_si_cel_de_maine(self):
        self.jurnal(9, nota(Z(9, 23, 29, 43), IN_REGULA))
        self.jurnal(10, "Traceback (most recent call last):\n", "OSError: [WinError 5] Acces refuzat\n")
        self.jurnal(11, nota(Z(11, 0, 29), IN_REGULA))                    # din viitor (un ceas dat înapoi): nu se ia
        v = self.veriga("paznicul", Z(10, 0, 20))
        self.assertEqual((v["stare"], v["ultima_dovada"], v["varsta_s"]), ("ok", Z(9, 23, 29, 43), 3017))

    def test_caile_din_nota_se_curata(self):
        mesaj = (r"reporniri: rândul rămâne pentru pasul următor (PermissionError(13, 'Permission denied', "
                 r"'C:\\Users\\Cineva\\Documents\\x\\reporniri_2026-06-10.csv'))   copie" "\t"
                 r" în C:/Users/Cineva/y, /c/Users/Cineva/z și \\server\Users\Cineva\w; " + str(self.d / "q.log"))
        self.jurnal(10, nota(Z(10, 8), mesaj + " " + "x" * 300))
        v = self.veriga("paznicul")
        for interzis in ("Users", "Cineva", ":\\", ":/", self.d.name, "\t", "  "):
            self.assertNotIn(interzis, v["text"])
        self.assertTrue(v["text"].startswith("reporniri: rândul rămâne pentru pasul următor (PermissionError(13, "
                                             "'Permission denied', '…')) copie în … … și … …"), v["text"])
        self.assertEqual((len(v["text"]), v["text"][-1], v["stare"]), (200, "…", "atent"))


class TestFerestrele(Baza):
    """Coada citită crește de 4 ori la fiecare încercare, dar nu trece niciodată de COADA_MAXIMA (BE8)."""
    MAXIM = 100_000

    def ferestre(self, cheie: str, nume: str) -> tuple[list[int], dict]:
        vazute, coada = [], SZ._coada

        def spion(f, octeti):
            if Path(f).name == nume:
                vazute.append(octeti)
            return coada(f, octeti)

        with mock.patch.object(SZ, "_coada", spion), mock.patch.object(SZ, "COADA_MAXIMA", self.MAXIM):
            v = self.veriga(cheie)
        return vazute, v

    def test_paznicul(self):
        scrie(self.loguri / "paznic_2026-06-10.log", '  File "x.py", line 1\n' * 10_000)   # ≈ 230 KB, fără nicio notă
        vazute, v = self.ferestre("paznicul", "paznic_2026-06-10.log")
        self.assertEqual((vazute, v["stare"]), ([8192, 32768, self.MAXIM], "necunoscut"))

    def test_numaratorile(self):
        scrie(self.num / "numaratori_2026-06-10.csv", ",".join(CAP_NUMARATORI) + "\n" + "x,y,intrare,a,,b,1\n" * 12_000,
              Z(10, 8))
        vazute, v = self.ferestre("colectarea", "numaratori_2026-06-10.csv")
        self.assertEqual((vazute, v["stare"]), ([16384, 65536, self.MAXIM], "necunoscut"))

    def test_veghea(self):
        scrie(self.loguri / "veghe_2026-06-10.csv", ",".join(CAP_VEGHE) + "\n" + "nu e o oră,6.0\n" * 15_000, ACUM - 5)
        vazute, v = self.ferestre("veghea", "veghe_2026-06-10.csv")
        self.assertEqual((vazute, v["ultimul_rand"]), ([65536, self.MAXIM], None))


class TestNoaptea(Baza):
    def lant_gata(self, dosar: Path, zi: str, pornit: str, sfarsit: str, rezultat: str = "gata_fara_simulari",
                  cod: int = 0) -> None:
        scrie(dosar / zi / "stare.json", stare_lant(zi, pornit, rezultat, {"recount": (0, pornit, sfarsit),
                                                                          "publica": (cod, sfarsit, sfarsit)}))

    def ambele_pe_9(self) -> None:
        self.lant_gata(self.lant, "2026-06-09", "2026-06-10T00:15:00", "2026-06-10T00:20:18")
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")

    def lant_in_curs(self, pornit: str = "2026-06-11T00:15:00") -> None:
        """Lanțul vechi al zilei de 10.06, pornit la `pornit` și încă în curs."""
        scrie(self.lant / "2026-06-10" / "stare.json",
              stare_lant("2026-06-10", pornit, "in_curs", {"repara": (0, pornit, pornit), "recount": (None, pornit, None)}))

    def test_ambele_lanturi_incheiate(self):
        self.ambele_pe_9()
        scrie(self.lant / "bucla.json", "{}")                                # alte fișiere din dosar nu încurcă
        scrie(self.lant / "2026-06-10" / "stare.json", "{}")                 # o zi de după cea așteptată nu se ia
        v = self.veriga("noaptea")
        self.assertEqual((v["stare"], v["prag_s"], v["lunga_s"], v["ultima_dovada"], v["fara_dosare"]),
                         ("ok", 86400, 7200, fs.ora("2026-06-10T03:39:59"), False))
        self.assertEqual(v["varsta_s"], round(ACUM - fs.ora("2026-06-10T03:39:59"), 1))
        lant, cor = v["lanturi"]
        self.assertEqual(lant, {"cheie": "lant", "ora": "00:15", "zi": "2026-06-09", "zi_asteptata": "2026-06-09",
                                "stare": "incheiat", "rezultat": "gata_fara_simulari", "pornit": "2026-06-10T00:15:00",
                                "incheiat_la": "2026-06-10T00:20:18", "pasi": 2, "coduri_nenule": 0,
                                "urmatoarea": "2026-06-11T00:15:00", "atentie": None, "asteapta": None,
                                "prea_lunga": False})
        self.assertEqual((cor["cheie"], cor["ora"], cor["zi"], cor["stare"], cor["urmatoarea"], cor["asteapta"]),
                         ("lant_cor", "03:30", "2026-06-09", "incheiat", "2026-06-11T03:30:00", None))

    def test_lantul_zilnic_inainte_si_dupa_00_15(self):
        self.ambele_pe_9()
        v = self.veriga("noaptea", Z(11, 0, 10))                            # noaptea zilei de 10.06 n-a sosit încă
        lant = v["lanturi"][0]
        self.assertEqual((lant["zi_asteptata"], lant["zi"], lant["stare"], lant["urmatoarea"], v["stare"]),
                         ("2026-06-09", "2026-06-09", "incheiat", "2026-06-11T00:15:00", "ok"))
        (self.lant / "2026-06-10").mkdir()                                   # dosarul zilei, încă fără stare.json
        for acum, stare, veriga in ((Z(11, 0, 15), "neinceput", "atent"), (Z(11, 0, 25), "neinceput", "atent"),
                                    (Z(11, 0, 25, 1), "lipsa", "problema")):
            with self.subTest(acum=text_ora(acum)):
                v = self.veriga("noaptea", acum)
                lant = v["lanturi"][0]
                self.assertEqual((lant["zi_asteptata"], lant["zi"], lant["stare"], lant["asteapta"], v["stare"]),
                                 ("2026-06-10", "2026-06-09", stare, None, veriga))
                self.assertEqual((lant["rezultat"], lant["incheiat_la"], lant["urmatoarea"]),   # din ziua de dinainte
                                 ("gata_fara_simulari", "2026-06-10T00:20:18", "2026-06-12T00:15:00"))
                self.assertEqual(v["lanturi"][1]["stare"], "incheiat")      # măsura nouă: tot ziua de 9.06
        scrie(self.lant / "2026-06-10" / "stare.json",
              stare_lant("2026-06-10", "2026-06-11T00:15:00", "in_curs", {"repara": (0, "2026-06-11T00:15:00",
                                                                                     "2026-06-11T00:15:03")}))
        v = self.veriga("noaptea", Z(11, 0, 26))
        self.assertEqual((v["lanturi"][0]["zi"], v["lanturi"][0]["stare"], v["stare"]), ("2026-06-10", "in_curs", "ok"))

    def test_lantul_vechi_asteapta_fluxul_camerei(self):
        """Lanțul vechi a pornit la 00:15 (proces.pid) și așteaptă cel mult 30 min fluxul camerei, încă fără stare.json:
        e în curs, nu lipsește (BE2)."""
        self.ambele_pe_9()
        scrie(self.lant / "2026-06-10" / "jurnal.txt", "11.06 00:15:00 pornit lanțul zilei 2026-06-10\n")
        scrie(self.lant / "2026-06-10" / SZ.FISIER_BLOCARE, "4321", Z(11, 0, 15))
        for acum in (Z(11, 0, 15, 1), Z(11, 0, 26), Z(11, 0, 44), Z(11, 0, 55)):
            with self.subTest(acum=text_ora(acum)):
                v = self.veriga("noaptea", acum)
                lant = v["lanturi"][0]
                self.assertEqual({k: lant[k] for k in ("zi", "zi_asteptata", "stare", "asteapta", "pornit", "rezultat",
                                                       "incheiat_la", "pasi", "coduri_nenule", "atentie", "prea_lunga")},
                                 {"zi": "2026-06-10", "zi_asteptata": "2026-06-10", "stare": "in_curs",
                                  "asteapta": "fluxul", "pornit": "2026-06-11T00:15:00", "rezultat": None,
                                  "incheiat_la": None, "pasi": None, "coduri_nenule": None, "atentie": None,
                                  "prea_lunga": False})
                self.assertEqual(v["stare"], "ok")
        v = self.veriga("noaptea", Z(11, 0, 55, 1))         # 30 min de așteptare și 10 min de rezervă au trecut
        lant = v["lanturi"][0]
        self.assertEqual((lant["stare"], lant["asteapta"], lant["zi"], lant["rezultat"], v["stare"]),
                         ("lipsa", None, "2026-06-09", "gata_fara_simulari", "problema"))

    def test_masura_noua_asteapta_masura_veche(self):
        """lant_cor.bucla așteaptă, fără să scrie nimic, cel mult 5 h, să se încheie lanțul vechi al aceleiași zile (BE2)."""
        self.ambele_pe_9()
        self.lant_in_curs("2026-06-11T03:00:00")                            # pornit târziu, de mână
        v = self.veriga("noaptea", Z(11, 3, 45))
        lant, cor = v["lanturi"]
        self.assertEqual((lant["stare"], lant["prea_lunga"], cor["stare"], cor["asteapta"], cor["zi"], cor["zi_asteptata"]),
                         ("in_curs", False, "neinceput", "lant", "2026-06-09", "2026-06-10"))
        self.assertEqual(v["stare"], "atent")
        v = self.veriga("noaptea", Z(11, 8, 40))                            # 5 h și 10 min de rezervă
        self.assertEqual((v["lanturi"][1]["stare"], v["lanturi"][1]["asteapta"]), ("neinceput", "lant"))
        v = self.veriga("noaptea", Z(11, 8, 40, 1))
        self.assertEqual((v["lanturi"][1]["stare"], v["lanturi"][1]["asteapta"], v["stare"]), ("lipsa", None, "problema"))

    def test_masura_noua_asteapta_si_lantul_vechi_care_asteapta_fluxul(self):
        self.ambele_pe_9()
        scrie(self.lant / "2026-06-10" / SZ.FISIER_BLOCARE, "4321", Z(11, 3, 20))     # pornit la 03:20, fără stare încă
        v = self.veriga("noaptea", Z(11, 3, 45))
        lant, cor = v["lanturi"]
        self.assertEqual((lant["stare"], lant["asteapta"], cor["stare"], cor["asteapta"], v["stare"]),
                         ("in_curs", "fluxul", "neinceput", "lant", "atent"))
        v = self.veriga("noaptea", Z(11, 4, 30))      # lanțul vechi a depășit așteptarea, dar proces.pid e tot acolo
        lant, cor = v["lanturi"]
        self.assertEqual((lant["stare"], cor["stare"], cor["asteapta"], v["stare"]), ("lipsa", "neinceput", "lant", "problema"))

    def test_masura_noua_nu_asteapta_un_lant_vechi_incheiat_la_timp(self):
        self.ambele_pe_9()
        self.lant_gata(self.lant, "2026-06-10", "2026-06-11T00:15:00", "2026-06-11T00:20:00", "cu_esecuri: publica", 1)
        v = self.veriga("noaptea", Z(11, 3, 45))      # încheiat, chiar cu un pas eșuat: măsura nouă trebuia să pornească
        self.assertEqual([(x["stare"], x["asteapta"]) for x in v["lanturi"]], [("esuat", None), ("lipsa", None)])

    def test_masura_noua_asteapta_si_un_lant_vechi_necitibil_sau_lipsa(self):
        """lant_cor.lant_vechi_incheiat nu dă drept încheiat un lanț vechi a cărui stare nu se poate citi sau lipsește, nici
        fără proces.pid: măsura nouă îl așteaptă și atunci, tot cel mult 5 h și 10 min (R1-2)."""
        self.ambele_pe_9()
        scrie(self.lant / "2026-06-10" / "stare.json", "{nu e JSON")         # fără proces.pid
        for acum, stare, asteapta, veriga in ((Z(11, 3, 45), "neinceput", "lant", "atent"),
                                              (Z(11, 8, 40), "neinceput", "lant", "atent"),
                                              (Z(11, 8, 40, 1), "lipsa", None, "problema")):
            with self.subTest(acum=text_ora(acum)), mock.patch.object(SZ.time, "sleep"):
                v = self.veriga("noaptea", acum)
                lant, cor = v["lanturi"]
                self.assertEqual((lant["stare"], cor["stare"], cor["asteapta"], cor["zi"], v["stare"]),
                                 ("necitibil", stare, asteapta, "2026-06-09", veriga))
        (self.lant / "2026-06-10" / "stare.json").unlink()                  # lipsește, tot fără proces.pid
        v = self.veriga("noaptea", Z(11, 3, 45))
        self.assertEqual([(x["stare"], x["asteapta"]) for x in v["lanturi"]], [("lipsa", None), ("neinceput", "lant")])
        self.assertEqual(v["stare"], "problema")                             # lanțul vechi lipsește

    def test_lantul_vechi_neincheiat_ca_in_lant_cor(self):
        """Copia lui lant_cor.lant_vechi_incheiat răspunde ca originalul pe toate felurile de stări ale lanțului vechi, iar
        măsura nouă îl așteaptă exact când originalul spune că nu s-a încheiat (R1-2)."""
        from romana import lant_cor
        self.ambele_pe_9()
        f = self.lant / "2026-06-10" / "stare.json"
        pasi = {"recount": (0, "2026-06-11T00:15:00", "2026-06-11T00:20:00")}

        def lant_(rezultat: str, cod: int = 0) -> str:
            return stare_lant("2026-06-10", "2026-06-11T00:15:00", rezultat, {**pasi, "publica": (cod, "2026-06-11T00:20:00",
                                                                                            "2026-06-11T00:20:00")})

        stari = {"lipsă": None, "goală": b"", "pe jumătate": b'{"zi": "2026-06-10", "rezu', "stricată": b"{nu e JSON",
                 "cu BOM": b"\xef\xbb\xbf" + lant_("gata").encode(), "în UTF-16": lant_("gata").encode("utf-16"),
                 "în curs": lant_("in_curs").encode(), "gata": lant_("gata").encode(),
                 "gata, fără simulări": lant_("gata_fara_simulari").encode(),
                 "cu eșecuri": lant_("cu_esecuri: publica", 1).encode(), "oprit": lant_("oprit: LIPSEȘTE x", 2).encode(),
                 "fără rezultat": json.dumps({"zi": "2026-06-10", "pasi": {"recount": {"cod": 0, "inceput": "2026-06-11T00:15",
                                                                                       "sfarsit": "2026-06-11T00:20"}}}).encode()}
        incheiate = set()
        with mock.patch.object(lant_cor, "DIR_LANT", self.lant), mock.patch.object(SZ.time, "sleep"):
            for nume, continut in stari.items():
                with self.subTest(stare=nume):
                    if continut is None:
                        f.unlink(missing_ok=True)
                    else:
                        scrie(f, continut)
                    incheiat = lant_cor.lant_vechi_incheiat("2026-06-10")
                    self.assertEqual(SZ._lant_vechi_incheiat(f), incheiat)
                    cor = self.veriga("noaptea", Z(11, 3, 45))["lanturi"][1]
                    self.assertEqual((cor["stare"], cor["asteapta"]), ("lipsa", None) if incheiat else ("neinceput", "lant"))
                    if incheiat:
                        incheiate.add(nume)
        # încheiat, oricum ar fi ieșit, e doar un lanț a cărui stare se citește și nu mai spune „in_curs”
        self.assertEqual(incheiate, {"gata", "gata, fără simulări", "cu eșecuri", "oprit", "fără rezultat"})

    def test_masura_noua_dupa_un_lant_vechi_incheiat_tarziu(self):
        """Lanțul vechi al zilei de 10.06 se încheie târziu, la 04:00, și își șterge proces.pid: măsura nouă îl vede la
        următoarea ei verificare (la 60 s) și abia apoi pornește, deci are 10 min de la încheierea lui, nu de la 03:30 (R1-1).
        Nu mai așteaptă lanțul vechi, doar pornește („pornire”, nu „lant”: pagina nu spune că așteaptă un lanț încheiat,
        RT-2). Încheiat după cele 5 h de așteptare, ea pornise oricum: 10 min de la 08:30."""
        self.ambele_pe_9()
        self.lant_gata(self.lant, "2026-06-10", "2026-06-11T00:15:00", "2026-06-11T04:00:00")
        for acum, stare, asteapta, veriga in ((Z(11, 4, 0, 30), "neinceput", "pornire", "atent"),
                                              (Z(11, 4, 10), "neinceput", "pornire", "atent"),
                                              (Z(11, 4, 10, 1), "lipsa", None, "problema")):
            with self.subTest(acum=text_ora(acum)):
                v = self.veriga("noaptea", acum)
                lant, cor = v["lanturi"]
                self.assertEqual((lant["stare"], cor["stare"], cor["asteapta"], cor["zi"], v["stare"]),
                                 ("incheiat", stare, asteapta, "2026-06-09", veriga))
        self.lant_gata(self.lant, "2026-06-10", "2026-06-11T00:15:00", "2026-06-11T04:00:00", "oprit: recount a eșuat", 1)
        v = self.veriga("noaptea", Z(11, 4, 0, 30))                         # oprit târziu: măsura nouă pornește tot după el
        self.assertEqual([(x["stare"], x["asteapta"]) for x in v["lanturi"]], [("esuat", None), ("neinceput", "pornire")])
        self.assertEqual(v["stare"], "problema")
        self.lant_gata(self.lant, "2026-06-10", "2026-06-11T00:15:00", "2026-06-11T08:35:00")
        for acum, stare in ((Z(11, 8, 36), "neinceput"), (Z(11, 8, 40), "neinceput"), (Z(11, 8, 40, 1), "lipsa")):
            with self.subTest(acum=text_ora(acum)):
                self.assertEqual(self.veriga("noaptea", acum)["lanturi"][1]["stare"], stare)

    def test_un_proces_pid_din_viitor_nu_e_o_pornire(self):
        """Un proces.pid scris „în viitor” (ceasul dat înapoi după ce l-a scris lanțul vechi) nu ține lanțul „în curs”; cu
        cel mult 60 s înainte, cât pot diferi două ceasuri, încă da (R1-5)."""
        self.ambele_pe_9()
        f = scrie(self.lant / "2026-06-10" / SZ.FISIER_BLOCARE, "4321")
        for blocare, stare, asteapta, veriga in ((Z(11, 5), "lipsa", None, "problema"),
                                                 (Z(11, 0, 31, 1), "lipsa", None, "problema"),
                                                 (Z(11, 0, 31), "in_curs", "fluxul", "ok"),
                                                 (Z(11, 0, 30), "in_curs", "fluxul", "ok")):
            with self.subTest(proces_pid=text_ora(blocare)):
                os.utime(f, (blocare, blocare))
                v = self.veriga("noaptea", Z(11, 0, 30))
                lant = v["lanturi"][0]
                self.assertEqual((lant["stare"], lant["asteapta"], lant["prea_lunga"], v["stare"]),
                                 (stare, asteapta, False, veriga))

    def test_masura_noua_inainte_si_dupa_03_30(self):
        self.lant_gata(self.lant, "2026-06-10", "2026-06-11T00:15:00", "2026-06-11T00:20:00")
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")
        v = self.veriga("noaptea", Z(11, 3, 29))
        self.assertEqual([(x["zi_asteptata"], x["stare"]) for x in v["lanturi"]],
                         [("2026-06-10", "incheiat"), ("2026-06-09", "incheiat")])
        self.assertEqual((v["stare"], v["lanturi"][1]["urmatoarea"]), ("ok", "2026-06-11T03:30:00"))
        self.assertEqual(v["ultima_dovada"], fs.ora("2026-06-11T00:20:00"))     # cea mai nouă încheiere
        v = self.veriga("noaptea", Z(11, 3, 35))
        cor = v["lanturi"][1]
        self.assertEqual((cor["zi_asteptata"], cor["zi"], cor["stare"], cor["asteapta"], v["stare"]),
                         ("2026-06-10", "2026-06-09", "neinceput", None, "atent"))
        v = self.veriga("noaptea", Z(11, 3, 41))
        self.assertEqual((v["lanturi"][1]["stare"], v["stare"], v["lanturi"][1]["urmatoarea"]),
                         ("lipsa", "problema", "2026-06-12T03:30:00"))

    def test_esuat_si_necitibil(self):
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")
        self.lant_gata(self.lant, "2026-06-09", "2026-06-10T00:15:00", "2026-06-10T00:30:00", "cu_esecuri: publica", 1)
        v = self.veriga("noaptea")
        self.assertEqual((v["lanturi"][0]["stare"], v["lanturi"][0]["coduri_nenule"], v["lanturi"][0]["rezultat"],
                          v["lanturi"][0]["atentie"], v["stare"]), ("esuat", 1, "cu_esecuri: publica", None, "problema"))
        scrie(self.lant / "2026-06-09" / "stare.json", "{nu e JSON")
        with mock.patch.object(SZ.time, "sleep") as dormi:
            v = self.veriga("noaptea")
        self.assertEqual((v["lanturi"][0]["stare"], v["lanturi"][0]["rezultat"], v["stare"]), ("necitibil", None, "atent"))
        self.assertEqual([c.args for c in dormi.call_args_list], [(SZ.PAUZA_LANT_S,)])     # încă o citire, tot stricată
        self.assertEqual(v["ultima_dovada"], fs.ora("2026-06-10T03:39:59"))

    def test_o_stare_prinsa_chiar_cand_se_rescrie_se_mai_citeste_o_data(self):
        """lant_cor își rescrie stare.json pe loc: o citire chiar atunci îl găsește gol (BE9)."""
        self.ambele_pe_9()
        stare_lant_, goale = fs.stare_lant, []

        def citire(f, t1):
            if Path(f).parent.parent == self.cor and not goale:
                goale.append(f)
                return {"stare": "necitibil"}
            return stare_lant_(f, t1)

        with mock.patch.object(SZ.fs, "stare_lant", citire), mock.patch.object(SZ.time, "sleep") as dormi:
            v = self.veriga("noaptea")
        self.assertEqual((v["lanturi"][1]["stare"], v["stare"], len(goale)), ("incheiat", "ok", 1))
        self.assertEqual([c.args for c in dormi.call_args_list], [(SZ.PAUZA_LANT_S,)])

    def test_un_cod_acceptat_da_un_lant_incheiat_cu_atentionare(self):
        """lant_zilnic acceptă la `repara` codul 2 (jurnal cu membri stricați), notează `atentie` și ajunge la „gata”:
        lanțul e încheiat, cu atenționarea lui; fișa păstrează definiția strictă (BM1)."""
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")
        pasi = {"repara": (2, "2026-06-10T00:15:01", "2026-06-10T00:15:30"),
                "recount": (0, "2026-06-10T00:15:30", "2026-06-10T00:17:20")}
        f = self.lant / "2026-06-09" / "stare.json"
        for campuri, atentie in (({"atentie": "jurnalul are membri stricați"}, "jurnalul are membri stricați"),
                                 ({}, SZ.ATENTIE_IMPLICITA), ({"atentie": "  "}, SZ.ATENTIE_IMPLICITA),
                                 ({"atentie": "vezi C:\\Users\\Cineva\\x\\repara.txt"}, "vezi …")):
            with self.subTest(campuri=campuri):
                scrie(f, stare_lant("2026-06-09", "2026-06-10T00:15:00", "gata_fara_simulari", pasi, **campuri))
                v = self.veriga("noaptea")
                lant = v["lanturi"][0]
                self.assertEqual((lant["stare"], lant["atentie"], lant["coduri_nenule"], lant["rezultat"], v["stare"]),
                                 ("incheiat", atentie, 1, "gata_fara_simulari", "atent"))
                self.assertEqual(fs.stare_lant(f, ACUM)["stare"], "esuat")

    def test_o_rulare_in_curs_de_peste_2_h_e_de_urmarit(self):
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")
        self.lant_in_curs()
        for acum, lunga, veriga in ((Z(11, 2, 15), False, "ok"), (Z(11, 2, 15, 1), True, "atent")):
            with self.subTest(acum=text_ora(acum)):
                v = self.veriga("noaptea", acum)
                self.assertEqual((v["lanturi"][0]["stare"], v["lanturi"][0]["prea_lunga"], v["stare"], v["lunga_s"]),
                                 ("in_curs", lunga, veriga, SZ.LANT_LUNG_S))

    def test_rezultatul_fara_cai(self):
        self.lant_gata(self.cor, "2026-06-09", "2026-06-10T03:30:00", "2026-06-10T03:39:59")
        scrie(self.lant / "2026-06-09" / "stare.json",
              stare_lant("2026-06-09", "2026-06-10T00:15:00", "oprit: LIPSEȘTE C:\\Users\\Cineva\\Documents\\GitHub\\x\\data\\"
                         "trajectories_brute\\traiectorii_2026-06-09.jsonl.gz", {"repara": (2, "2026-06-10T00:15:00",
                                                                                           "2026-06-10T00:15:01")}))
        v = self.veriga("noaptea")
        self.assertEqual((v["lanturi"][0]["rezultat"], v["lanturi"][0]["stare"]), ("oprit: LIPSEȘTE …", "esuat"))

    def test_fara_dosare_e_necunoscut(self):
        """Fără niciun dosar al prelucrării de noapte (alt calculator, un server de probă), veriga e necunoscută, iar
        `fara_dosare` o spune, ca pagina să nu scrie că rulările lipsesc; nici măsura nouă nu așteaptă nimic aici (R2-N5)."""
        v = self.veriga("noaptea")
        self.assertEqual((v["stare"], v["ultima_dovada"], v["fara_dosare"]), ("necunoscut", None, True))
        self.assertEqual([(x["cheie"], x["zi"], x["stare"], x["asteapta"]) for x in v["lanturi"]],
                         [("lant", None, "lipsa", None), ("lant_cor", None, "lipsa", None)])
        self.lant.mkdir()                                                   # un singur dosar, chiar gol: nu mai e „fără”
        v = self.veriga("noaptea")
        self.assertEqual((v["stare"], v["fara_dosare"]), ("problema", False))
        with mock.patch.object(SZ, "_noaptea", side_effect=RuntimeError("de probă")):
            v = self.stare()["verigi"][4]                                   # o eroare: nu se știe, deci nici „fără dosare”
        self.assertEqual((v["stare"], v["eroare"], v["fara_dosare"]), ("necunoscut", "RuntimeError", False))


class TestFisa(Baza):
    def test_fara_fise(self):
        self.assertIsNone(self.stare()["fisa"])

    def test_rezumatul(self):
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_json("2026-06-06T00:00:00"))
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.md", "# Fișa senzorului")
        f = self.stare()["fisa"]
        self.assertEqual(f, {
            "taietura": "2026-06-06T00:00:00", "inceput": "2026-06-01T09:04:46", "ore": 110.92,
            "pondere_minute_cu_cadre": 0.98843, "fps_mediana": 5.98, "opriri_anuntate": 2, "caderi_neprevazute": 0,
            "pauze": 30, "caderi_sursa": None, "episoade_reconectare": 10, "lanturi_incheiate": 6, "lanturi_asteptate": 6,
            "vehicule": 93580, "publica": True})
        self.assertEqual([type(f[k]) for k in ("vehicule", "lanturi_incheiate", "lanturi_asteptate")], [int] * 3)

    def test_caderile_sursei_din_fisa(self):
        # o fișă calculată din 10.11 are și căderile sursei; una de dinainte (ca fișa publicată la M2) nu le are: None
        d = json.loads(fisa_json("2026-06-07T00:00:00"))
        d["caderi_sursa"] = {"numar": 2, "durata_s": 4303, "lista": []}
        scrie(self.docs / "fisa_senzor_2026-06-07_0000.json", json.dumps(d, ensure_ascii=False))
        self.assertEqual(self.stare()["fisa"]["caderi_sursa"], 2)
        for rau in ({"numar": True}, {"numar": "2"}, ["2"], None):
            d["caderi_sursa"] = rau
            scrie(self.docs / "fisa_senzor_2026-06-07_0000.json", json.dumps(d, ensure_ascii=False))
            self.assertIsNone(self.stare()["fisa"]["caderi_sursa"], rau)

    def test_o_suma_care_ar_iesi_infinita_lipseste(self):
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_uriasa())
        f = self.stare()["fisa"]
        self.assertEqual((f["vehicule"], f["lanturi_incheiate"], f["ore"]), (None, 6, 110.92))
        json.dumps(f, allow_nan=False)
        self.assertEqual((SZ._suma([1.5, None, 2]), SZ._suma([None]), SZ._suma([2, 3])), (3.5, None, 5))

    def test_un_intreg_pe_care_pagina_nu_l_ar_citi_exact_lipseste(self):
        """JavaScript citește exact doar întregii până la 2⁵³, iar unul de peste 1,8·10³⁰⁸ îl citește ca Infinity: o sumă
        întreagă mai mare lipsește, la fel un câmp întreg mai mare; cele infinite lipsesc și ele (R1-6)."""
        L = SZ.LIMITA_INTREG
        self.assertEqual(L, 2 ** 53)
        self.assertEqual((SZ._suma([L]), SZ._suma([L, 1]), SZ._suma([-L, -1]), SZ._suma([10 ** 308, 10 ** 308])),
                         (L, None, None, None))
        self.assertEqual((SZ._suma([float("inf")]), SZ._suma([1e308, 1e308]), SZ._suma([2.5, 1e300])), (None, None, 1e300))
        self.assertEqual((SZ._nr(L), SZ._nr(-L), SZ._nr(L + 1), SZ._nr(10 ** 400), SZ._nr(True), SZ._nr(float("nan"))),
                         (L, -L, None, None, None, None))
        d = json.loads(fisa_json("2026-06-06T00:00:00"))
        d["vehicule"]["pe_zile"] = {"2026-06-01": {"vehicule": 10 ** 308}, "2026-06-02": {"vehicule": 10 ** 308}}
        d["pauze"]["numar"] = 10 ** 400                                      # ar fi oprit tot rezumatul (OverflowError)
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", json.dumps(d))
        f = self.stare()["fisa"]
        self.assertEqual((f["vehicule"], f["pauze"], f["ore"], f["lanturi_incheiate"]), (None, None, 110.92, 6))
        json_strict(json.dumps(f))
        d["vehicule"]["pe_zile"] = {"2026-06-01": {"vehicule": L}, "2026-06-02": {"vehicule": 1}}   # fiecare bun, suma nu
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", json.dumps(d))
        self.assertIsNone(self.stare()["fisa"]["vehicule"])

    def test_cea_mai_noua_taietura_iar_la_egalitate_cea_publicata(self):
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_json("2026-06-06T00:00:00", ore=1))
        scrie(self.fise / "fisa_senzor_2026-06-05_2320.json", fisa_json("2026-06-05T23:20:00", ore=2))
        scrie(self.fise / "fisa_senzor_2026-06-06_0000.json", fisa_json("2026-06-06T00:00:00", ore=3))
        f = self.stare()["fisa"]
        self.assertEqual((f["taietura"], f["ore"], f["publica"]), ("2026-06-06T00:00:00", 1, True))
        scrie(self.fise / "fisa_senzor_2026-06-08_0700.json", fisa_json("2026-06-08T07:00:00", ore=4))
        f = self.stare()["fisa"]
        self.assertEqual((f["taietura"], f["ore"], f["publica"]), ("2026-06-08T07:00:00", 4, False))

    def test_o_fisa_stricata_se_sare(self):
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_json("2026-06-06T00:00:00", ore=1))
        for nume, continut in (("a", "{nu e JSON"), ("b", "[1, 2]"), ("c", json.dumps({"inceput": "2026-06-09T00:00:00"})),
                               ("d", json.dumps({"taietura": "nu e o oră"})), ("e", json.dumps({"taietura": 1781000000}))):
            scrie(self.fise / f"fisa_senzor_{nume}.json", continut)
        self.assertEqual(self.stare()["fisa"]["ore"], 1)
        scrie(self.fise / "fisa_senzor_f.json", json.dumps({"taietura": "2026-06-07T00:00:00", "durata": "?"}))
        f = self.stare()["fisa"]          # se poate citi, dar n-are cifrele: câmpurile lipsă rămân goale
        self.assertEqual((f["taietura"], f["publica"]), ("2026-06-07T00:00:00", False))
        self.assertEqual({k for k, x in f.items() if x is not None}, {"taietura", "publica"})

    def test_o_fisa_prea_mare_se_sare(self):
        mica = fisa_json("2026-06-06T00:00:00", ore=1)
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", mica)
        scrie(self.fise / "fisa_senzor_2026-06-08_0700.json", fisa_json("2026-06-08T07:00:00", ore=4) + " " * 2000)
        with mock.patch.object(SZ, "MARIME_JSON", len(mica.encode("utf-8")) + 1000):
            self.assertEqual(self.stare()["fisa"]["ore"], 1)


class TestRuta(Baza):
    """GET /api/senzor, cu clientul de test Flask, pe dosarele temporare și cu un ceas al serverului dat de test."""

    def setUp(self):
        super().setUp()
        from romana.dashboard import server as S
        self.S = S
        for nume, valoare in (("LIVE", self.live), ("LOGURI", self.loguri), ("NUMARATORI", self.num),
                              ("LANTURI", self.lanturi), ("FISE", (self.docs, self.fise))):
            self.addCleanup(setattr, S, nume, getattr(S, nume))
            setattr(S, nume, valoare)
        S._senzor_memorat = None
        self.addCleanup(setattr, S, "_senzor_memorat", None)
        self.ceas = [ACUM]
        ceas = mock.patch.object(S, "time", types.SimpleNamespace(time=lambda: self.ceas[0]))
        ceas.start()
        self.addCleanup(ceas.stop)
        self.c = S.app.test_client()

    def json(self, r) -> dict:
        """Răspunsul: HTTP 200, cu corpul citit strict (fără NaN sau Infinity, pe care pagina nu le-ar putea citi)."""
        self.assertEqual(r.status_code, 200)
        return json_strict(r.get_data(as_text=True))

    def cere(self) -> dict:
        return self.json(self.c.get("/api/senzor"))

    def test_http_200_cinci_verigi_fara_cai(self):
        self.scrie_stare(0.3)
        scrie(self.loguri / "paznic_2026-06-10.log",
              nota(Z(10, 8), f"eroare: {self.d / 'x.log'} și C:\\Users\\Cineva\\y.txt"))
        r = self.c.get("/api/senzor")
        j = self.json(r)
        self.assertEqual([v["cheie"] for v in j["verigi"]], CHEI)
        self.assertEqual((j["calculat_la"], j["memorare_s"], j["ora_server"]), (ACUM, 5, ACUM))
        self.assertEqual([v["stare"] for v in j["verigi"]], ["ok", "necunoscut", "necunoscut", "atent", "necunoscut"])
        self.assertEqual(j["verigi"][3]["text"], "eroare: … și …")
        text = r.get_data(as_text=True)
        for interzis in ("C:\\", "C:/", "Users", "Cineva", self.d.name):
            self.assertNotIn(interzis, text)

    def test_memorarea_5_s(self):
        r1 = self.cere()
        self.assertEqual(r1["verigi"][0]["stare"], "problema")             # fără stare live
        self.scrie_stare(1)                                                 # apare între timp: răspunsul memorat rămâne
        self.ceas[0] = ACUM + 4.9
        r2 = self.cere()
        self.assertEqual((r2["calculat_la"], r2["ora_server"], r2["verigi"]), (ACUM, ACUM + 4.9, r1["verigi"]))
        self.ceas[0] = ACUM + 5
        r3 = self.cere()
        self.assertEqual((r3["calculat_la"], r3["ora_server"], r3["verigi"][0]["stare"]), (ACUM + 5, ACUM + 5, "ok"))
        self.ceas[0] = ACUM + 1                                             # ceasul dat înapoi: se calculează din nou
        self.assertEqual(self.cere()["calculat_la"], ACUM + 1)

    def test_fiecare_citire_a_paginii_primeste_un_calcul_nou(self):
        """Pagina cere starea la 10 s, cu abateri de câteva ms în ambele sensuri: fiecare cerere primește un calcul nou (P2)."""
        for t in (ACUM + 0.003, ACUM + 9.995, ACUM + 20.003, ACUM + 29.99, ACUM + 40.002):
            self.ceas[0] = t
            self.assertEqual(self.cere()["calculat_la"], t)

    def test_cererile_deodata_calculeaza_o_singura_data(self):
        apeluri, original, coduri = [], self.S.senzor.stare_senzor, []

        def incet(*a, **k):
            apeluri.append(1)
            time.sleep(0.2)
            return original(*a, **k)

        def cere():
            coduri.append(self.S.app.test_client().get("/api/senzor").status_code)

        with mock.patch.object(self.S.senzor, "stare_senzor", incet):
            fire = [threading.Thread(target=cere) for _ in range(4)]
            for f in fire:
                f.start()
            for f in fire:
                f.join(10)
        self.assertEqual((len(apeluri), coduri), (1, [200] * 4))

    def test_o_eroare_neprevazuta_strica_doar_veriga_ei(self):
        with mock.patch.object(SZ, "_paznicul", side_effect=RuntimeError("C:\\Users\\Cineva\\secret.log")), \
                mock.patch.object(SZ, "ultima_fisa", side_effect=OSError("C:\\Users\\Cineva\\fisa.json")):
            r = self.c.get("/api/senzor")
        j = self.json(r)
        self.assertEqual([v["cheie"] for v in j["verigi"]], CHEI)
        p = j["verigi"][3]
        self.assertEqual((p["stare"], p["eroare"], p["prag_s"], p["text"]), ("necunoscut", "RuntimeError", 3720, None))
        self.assertIsNone(j["fisa"])
        self.assertNotIn("eroare", j["verigi"][2])
        self.assertNotIn("secret", r.get_data(as_text=True))

    def test_o_fisa_cu_sume_uriase_da_tot_json_valid(self):
        scrie(self.docs / "fisa_senzor_2026-06-06_0000.json", fisa_uriasa())
        j = self.cere()
        self.assertEqual((j["fisa"]["taietura"], j["fisa"]["vehicule"]), ("2026-06-06T00:00:00", None))


class TestPraguri(unittest.TestCase):
    """Pragurile copiate: veghe, paznic și lanțurile de noapte nu se importă în server, iar pagina are pragurile ei."""

    def test_copiile_pragurilor_vegherii_si_paznicului(self):
        from romana.vision import paznic, veghe
        self.assertEqual((SZ.STARE_VECHE, SZ.PRAG_FPS, SZ.PRAG_PAUZE, SZ.MAX_EPISOADE, SZ.SEMN_DE_VIATA),
                         (veghe.STARE_VECHE, veghe.PRAG_FPS, veghe.PRAG_PAUZE, veghe.MAX_EPISOADE, paznic.SEMN_DE_VIATA))
        self.assertEqual(SZ.STARE_VECHE, fs.TACERE_VEGHE)
        self.assertEqual((SZ.STARE_VECHE, SZ.PRAG_FPS, SZ.PRAG_PAUZE, SZ.MAX_EPISOADE, SZ.SEMN_DE_VIATA),
                         (180, 3.5, 10, 4, 3600))
        self.assertEqual(CAP_VEGHE, veghe.CSV_CAP)                          # probele de aici au antetul real

    def test_notele_bune_sunt_cele_ale_paznicului(self):
        from romana.vision import paznic
        sursa = inspect.getsource(paznic.Paznic._sanatos)                   # unde le scrie paznicul
        self.assertEqual(SZ.NOTE_BUNE, ("în regulă", "repornirea ține de"))
        for inceput in SZ.NOTE_BUNE:
            self.assertIn(f'self.nota(f"{inceput}', sursa)

    def test_copiile_lanturilor_de_noapte(self):
        from romana import lant_cor, lant_zilnic
        self.assertEqual((SZ.FISIER_BLOCARE, SZ.ASTEPTARE_FLUX_S, SZ.ASTEPTARE_LANT_VECHI_S),
                         (lant_zilnic.FISIER_BLOCARE, lant_zilnic.ASTEPTARE_FLUX_S, lant_cor.ASTEPTARE_LANT_VECHI_S))
        self.assertEqual((SZ.FISIER_BLOCARE, SZ.ASTEPTARE_FLUX_S, SZ.ASTEPTARE_LANT_VECHI_S), ("proces.pid", 1800, 18000))
        self.assertEqual((SZ.LANTURI["lant"][1], SZ.LANTURI["lant_cor"][1]), (lant_zilnic.ORA_IMPLICITA, ora_din_zi(3, 30)))
        self.assertEqual((SZ.LANTURI["lant"][0], SZ.LANTURI["lant_cor"][0]), (lant_zilnic.DIR_LANT, lant_cor.DIR_COR))
        self.assertEqual(SZ.ASTEAPTA_DUPA, {"lant_cor": "lant"})
        # după încheierea lanțului vechi, măsura nouă îl vede la următoarea ei verificare: marja trebuie s-o cuprindă
        self.assertGreater(SZ.MARJA_LANT_S, lant_cor.PAS_ASTEPTARE_S)   # (copia lui lant_vechi_incheiat: TestNoaptea)

    def test_pragurile_camerei_sunt_cele_din_pagina(self):
        pagina = PAGINA.read_text(encoding="utf-8")
        self.assertRegex(pagina, rf"\bCAMERA_ALERTA_S\s*=\s*{SZ.CAMERA_ALERTA_S}\b")
        self.assertRegex(pagina, rf"\bCAMERA_ROSU_S\s*=\s*{SZ.CAMERA_ROSU_S}\b")
        self.assertRegex(pagina, rf"_varsta_s\s*<\s*{SZ.CAMERA_PROASPATA_S}\b")
        self.assertEqual((SZ.CAMERA_PROASPATA_S, SZ.CAMERA_ALERTA_S, SZ.CAMERA_ROSU_S), (15, 180, 600))

    def test_memorarea_e_mai_scurta_decat_ritmul_paginii(self):
        """Pagina cere starea la SENZOR_MS; cu o memorare la fel de lungă, cam o cerere din trei primea calculul vechi."""
        m = re.search(r"\bSENZOR_MS\s*=\s*(\d+)", PAGINA.read_text(encoding="utf-8"))
        self.assertIsNotNone(m, "SENZOR_MS lipsește din index.html")
        self.assertLess(SZ.MEMORARE_S * 1000, int(m.group(1)))
        self.assertLessEqual(SZ.MEMORARE_S * 1000, int(m.group(1)) - 1000)    # cu rezervă pentru abaterile ceasului
        self.assertEqual(SZ.MEMORARE_S, 5)

    def test_importul_ramane_usor(self):
        cod = ("import sys; import romana.dashboard.senzor; print(sorted(m for m in ('numpy', 'psutil', 'cv2', 'flask', "
               "'pandas', 'romana.vision.veghe', 'romana.vision.paznic', 'romana.vision.od_counter', 'romana.lant_zilnic', "
               "'romana.lant_cor') if m in sys.modules))")
        r = subprocess.run([sys.executable, "-B", "-c", cod], capture_output=True, text=True, timeout=120,
                           env={**os.environ, "PYTHONPATH": str(SRC)}, cwd=str(SRC.parent))
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "[]"), r.stderr)


class TestDosareleReale(unittest.TestCase):
    """Starea calculată pe dosarele reale ale colectării, doar citire: se verifică numai forma răspunsului. Nicio stare
    anume nu se cere: o verigă de urmărit sau cu o problemă, pe dosarele reale, e o stare adevărată, nu o greșeală."""

    def test_forma_raspunsului_fara_nicio_scriere(self):
        deschide = io.open

        def doar_citire(fisier, mode="r", *a, **k):
            if set(str(mode)) & set("wax+"):
                raise AssertionError(f"o scriere: {fisier}")
            return deschide(fisier, mode, *a, **k)

        with contextlib.ExitStack() as stiva:
            stiva.enter_context(mock.patch("builtins.open", doar_citire))
            stiva.enter_context(mock.patch("io.open", doar_citire))
            for nume in ("write_text", "write_bytes", "mkdir", "touch", "unlink", "rename", "replace", "rmdir"):
                stiva.enter_context(mock.patch.object(Path, nume, side_effect=AssertionError(nume)))
            for nume in ("replace", "rename", "remove", "unlink", "mkdir", "makedirs", "rmdir", "utime"):
                stiva.enter_context(mock.patch.object(os, nume, side_effect=AssertionError(nume)))
            if SZ._winapi is not None:
                creeaza = SZ._winapi.CreateFile

                def doar_citire_win(nume, acces, partajare, *rest):
                    if acces != SZ._winapi.GENERIC_READ or rest[1] != SZ._winapi.OPEN_EXISTING:
                        raise AssertionError(f"o deschidere care nu e doar citire: {nume}")
                    return creeaza(nume, acces, partajare, *rest)

                stiva.enter_context(mock.patch.object(SZ._winapi, "CreateFile", doar_citire_win))
            r = SZ.stare_senzor()
        self.assertEqual(set(r), {"calculat_la", "memorare_s", "verigi", "fisa"})
        self.assertEqual(r["memorare_s"], SZ.MEMORARE_S)
        self.assertEqual([v["cheie"] for v in r["verigi"]], CHEI)
        for v in r["verigi"]:
            with self.subTest(cheie=v["cheie"]):
                self.assertIn(v["stare"], SZ.STARI)
                self.assertNotIn("eroare", v)
                self.assertLessEqual({"ultima_dovada", "varsta_s", "prag_s"}, set(v))
        veghea, noaptea = r["verigi"][2], r["verigi"][4]
        if veghea["alerta"] is not None:
            self.assertEqual(set(veghea["alerta"]), {"ora", "semne", "dupa_ultimul_rand"})
            self.assertIsInstance(veghea["alerta"]["dupa_ultimul_rand"], bool)
        self.assertEqual(noaptea["lunga_s"], SZ.LANT_LUNG_S)
        self.assertIsInstance(noaptea["fara_dosare"], bool)
        self.assertEqual([x["cheie"] for x in noaptea["lanturi"]], ["lant", "lant_cor"])
        for x in noaptea["lanturi"]:
            with self.subTest(lant=x["cheie"]):
                self.assertIn(x["asteapta"], (None, "fluxul", "lant", "pornire"))
                self.assertIsInstance(x["prea_lunga"], bool)
                self.assertTrue(x["atentie"] is None or isinstance(x["atentie"], str))
        self.assertTrue(r["fisa"] is None or isinstance(r["fisa"]["publica"], bool))
        text = json.dumps(r, ensure_ascii=False, allow_nan=False)
        for interzis in ("C:\\", "Users"):
            self.assertNotIn(interzis, text)

    @unittest.skipUnless((ROOT / "docs" / "rezultate" / "fisa_senzor_2026-11-06_0000.json").exists(), "fișa publicată lipsește")
    def test_rezumatul_fisei_publicate(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(ROOT / "docs" / "rezultate" / "fisa_senzor_2026-11-06_0000.json", d)
            f = SZ.ultima_fisa((Path(d),))
        self.assertEqual(f, {"taietura": "2026-11-06T00:00:00", "inceput": "2026-11-01T09:04:46", "ore": 110.92,
                             "pondere_minute_cu_cadre": 0.98843, "fps_mediana": 5.98, "opriri_anuntate": 2,
                             "caderi_neprevazute": 0, "pauze": 30, "caderi_sursa": None, "episoade_reconectare": 10,
                             "lanturi_incheiate": 6, "lanturi_asteptate": 6, "vehicule": 284152, "publica": True})


if __name__ == "__main__":
    unittest.main()
