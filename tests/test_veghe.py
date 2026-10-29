"""Teste pentru veghea fluxului de cadre (`romana.vision.veghe`, § 4.6): citirea jurnalului pe măsură ce crește, semnele
din traiectorii și semnele din starea live (date sintetice, fără cameră).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import gzip
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from romana.vision.veghe import Fereastra, StareLive, _eveniment, membri_noi, semne_jurnal, urme_pauza

T0 = datetime(2026, 10, 29, 3, 0).timestamp()


def traiectorii(n: int, pas: float, misc: bool = True, tremur: bool = True, tip: str = "passenger") -> list[dict]:
    """n traiectorii de ≈5 s, răspândite pe 9 minute de la T0, cu un punct la `pas` secunde; vehiculele oprite au
    pozițiile ușor variabile (`tremur`, ca pe cadre reale) sau identice (cadre identice)."""
    recs = []
    for i in range(n):
        k = int(5 / pas) + 1
        pts = [[round(j * pas, 2), round(0.1 + (0.02 * j if misc else 0.0002 * (j % 2) * tremur), 4), 0.5]
               for j in range(k)]
        recs.append({"t0": T0 + i * 540 / n, "tip": tip, "p": pts})
    return recs


def metrici(recs: list[dict]) -> dict:
    f = Fereastra()
    for d in recs:
        f.adauga(d, d["t0"] + d["p"][-1][0] + 5)
    return f.evalueaza(T0 + 600)


def chei(semne: list) -> set:
    return {k for k, _ in semne}


def stare_live(cadre: list[float], fps: float = 6.0, reconectari=lambda t: 0) -> set:
    """Trece prin StareLive citiri la fiecare secundă, timp de 10 minute; `cadre` = orele cadrelor prelucrate (relativ la
    T0). Întoarce cheile semnelor apărute."""
    s, cadre, k, ultim, gasite = StareLive(T0), sorted(cadre), 0, T0, set()
    for sec in range(600):
        acum = T0 + sec
        while k < len(cadre) and cadre[k] <= sec:
            ultim = T0 + cadre[k]
            k += 1
        gasite |= chei(s.adauga(acum, {"timestamp": ultim, "fps": fps, "reconectari": reconectari(sec)}))
    return gasite


class TestCitireJurnal(unittest.TestCase):
    def test_ultimul_membru_incomplet_ramane_pentru_citirea_urmatoare(self):
        membri = [gzip.compress((json.dumps({"t0": T0 + i, "tip": "passenger", "p": [[0, 0.1, 0.1]]}) + "\n").encode(),
                                mtime=0) for i in range(4)]
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "traiectorii_2026-10-29.jsonl.gz"
            f.write_bytes(b"".join(membri[:3]) + membri[3][:len(membri[3]) // 2])
            recs, poz = membri_noi(f, 0)
            self.assertEqual([r["t0"] for r in recs], [T0, T0 + 1, T0 + 2])
            self.assertEqual(poz, sum(len(m) for m in membri[:3]))
            with open(f, "ab") as fh:                      # scrierea membrului se încheie
                fh.write(membri[3][len(membri[3]) // 2:])
            recs, poz = membri_noi(f, poz)
            self.assertEqual([r["t0"] for r in recs], [T0 + 3])
            self.assertEqual(poz, f.stat().st_size)
            # pornire la un octet oarecare (în mijlocul unui membru): se caută antetul următor
            recs, _ = membri_noi(f, 5)
            self.assertEqual([r["t0"] for r in recs], [T0 + 1, T0 + 2, T0 + 3])


class TestSemneJurnal(unittest.TestCase):
    def test_rata_normala_fara_semne(self):
        m = metrici(traiectorii(200, 0.17) + traiectorii(50, 0.17, misc=False))
        self.assertLess(m["lungi"], 0.01)
        self.assertEqual(semne_jurnal(m, 30), [])

    def test_prelucrarea_incetinita(self):
        m = metrici(traiectorii(200, 0.7))
        self.assertGreater(m["pasi"], 300)
        self.assertIn("pasi", chei(semne_jurnal(m, 30)))

    def test_pietonii_nu_conteaza_la_pasi(self):
        m = metrici(traiectorii(200, 0.17) + traiectorii(200, 0.7, tip="pieton"))
        self.assertEqual(semne_jurnal(m, 30), [])

    def test_imagine_identica(self):
        self.assertIn("imagine", chei(semne_jurnal(metrici(traiectorii(30, 0.17, misc=False, tremur=False)), 30)))
        self.assertEqual(semne_jurnal(metrici(traiectorii(30, 0.17, misc=False)), 30), [])

    def test_jurnal_oprit(self):
        m = metrici(traiectorii(200, 0.17))
        self.assertIn("jurnal", chei(semne_jurnal(m, 301)))


class TestStareLive(unittest.TestCase):
    NORMAL = [i / 6 for i in range(600 * 6)]          # 6 cadre/s, fără pauze

    def test_flux_normal_fara_semne(self):
        self.assertEqual(stare_live(self.NORMAL), set())

    def test_o_intrerupere_scurta_se_reface_si_doar_se_noteaza(self):
        # 100 s fără cadre (o reconectare, ca pe 28.10), cu 3 încercări eșuate numărate în câteva secunde
        cadre = [t for t in self.NORMAL if not 200 <= t < 300]
        s = StareLive(T0)
        gasite = stare_live(cadre, reconectari=lambda sec: 0 if sec < 230 else 3)
        self.assertEqual(gasite, set())
        for sec in range(400):                         # evenimentul ajunge în CSV
            s.adauga(T0 + sec, {"timestamp": T0 + (199 if 200 <= sec < 300 else sec), "fps": 6.0})
        self.assertEqual(len(s.evenimente), 1)
        playlist = {"citiri": [{"ultimul_segment_in_urma_s": 24.2}, {"ultimul_segment_in_urma_s": 31.0}],
                    "avanseaza": False}                # serverul camerei rămăsese în urmă
        text = _eveniment(s.evenimente[0], playlist)
        self.assertIn("fără cadre 101 s", text)
        self.assertIn("în urmă 24, 31 s", text)
        self.assertIn("necitit", _eveniment(s.evenimente[0], None))

    def test_fara_cadre_trei_minute(self):
        self.assertIn("cadre", stare_live([t for t in self.NORMAL if t < 300]))

    def test_redare_sacadata(self):
        # „merge 2 s și stă 4 s”, ca înainte de tamponul de redare (21–22.10)
        self.assertIn("pauze", stare_live([t for t in self.NORMAL if t % 6 < 2]))

    def test_rata_mica(self):
        self.assertIn("rata", stare_live(self.NORMAL, fps=1.4))
        self.assertEqual(stare_live(self.NORMAL, fps=4.6), set())

    def test_reconectari_grupate_in_episoade(self):
        # episoade de câte 3 încercări eșuate (la 0, 2 și 4 s), la 2,5 minute distanță: patru dau alertă, trei nu
        def rec(n):
            return lambda sec: sum(min(3, (sec - s0) // 2 + 1) for s0 in range(60, 60 + 150 * n, 150) if sec >= s0)
        self.assertIn("reconectari", stare_live(self.NORMAL, reconectari=rec(4)))
        self.assertNotIn("reconectari", stare_live(self.NORMAL, reconectari=rec(3)))


def urme(gol_retea=(), cpu_pauza=1.2, pauza=(200, 212)) -> list[tuple]:
    """Citiri pe secundă: un segment de 3 MB descărcat în 2 s la fiecare 6 s (rețeaua tace ≈4 s între ele) și CPU-ul
    lui run_vision de 1,2 nuclee, cu `cpu_pauza` nuclee în timpul pauzei; în secundele `gol_retea` nu sosește nimic."""
    s, rx, cpu = [], 0.0, 0.0
    for sec in range(400):
        if sec % 6 < 2 and sec not in gol_retea:
            rx += 1.5e6
        cpu += cpu_pauza if pauza[0] < sec <= pauza[1] else 1.2       # consumul din secunda (sec − 1, sec]
        s.append((T0 + sec, rx, cpu))
    return s


class TestUrmePauza(unittest.TestCase):
    def test_descarcarea_oprita(self):
        # rețeaua tace 20 s, de la 8 s înaintea pauzei de 12 s (tamponul de redare), iar CPU-ul scade
        text = urme_pauza(urme(gol_retea=range(192, 212), cpu_pauza=0.05), T0 + 200, T0 + 212)
        self.assertRegex(text, r"cel mai lung gol 2\d s \(de la -1\d s\)")
        self.assertIn("CPU run_vision: 5% în pauză, 120% înainte", text)

    def test_prelucrarea_oprita(self):
        # rețeaua merge normal (golurile dintre segmente, ≈4 s), un nucleu ocupat în pauză
        text = urme_pauza(urme(cpu_pauza=1.0), T0 + 200, T0 + 212)
        self.assertRegex(text, r"cel mai lung gol [45] s")
        self.assertIn("100% în pauză", text)
        self.assertIn("prea puține", urme_pauza(urme()[-20:], T0 + 395, T0 + 399))
        self.assertIn("necitit; rețea:", _eveniment((T0 + 200, 12), None, text))


if __name__ == "__main__":
    unittest.main()
