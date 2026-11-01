"""Teste pentru evaluarea dispeceratului și pentru capturi, fără rețea și fără Chrome.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_evaluare
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from romana.dashboard import capturi as C
from romana.dashboard import evaluare as E


class TestPrompturi(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        for n in ("telefon", "normal", "confirmare"):
            (self.d / f"{n}.jpg").write_bytes(b"x")

    def test_capturile_incep_cu_starea_normala(self):
        self.assertEqual([p.stem for p in E.capturi(self.d)], ["normal", "confirmare", "telefon"])
        with self.assertRaises(SystemExit):
            E.capturi(self.d / "lipsa")

    def test_evaluatorii_nu_vad_lista_de_defecte(self):
        cereri = E.cereri_evaluare("m1", self.d)
        self.assertEqual(len(cereri), 7)        # 5 euristici, parcurgerea, accesibilitatea
        self.assertEqual(len({c["custom_id"] for c in cereri}), 7)
        for c in cereri:
            continut = c["params"]["messages"][0]["content"]
            self.assertEqual([b["type"] for b in continut], ["image"] * 3 + ["text"])
            text = continut[-1]["text"]
            self.assertIn("Dispecerat Piața Romană", text)
            self.assertIn("nu raporta valorile sau fotografia", text)
            self.assertNotIn("verificare_plan", text)

    def test_schemele_sunt_inchise(self):
        for s in (E.SCHEMA_EURISTICA, E.SCHEMA_PARCURGERE, E.SCHEMA_WCAG, E.SCHEMA_REUNIRE, E.SCHEMA_VERIFICARE):
            self.assertFalse(s["additionalProperties"])
            items = next(iter(s["properties"].values()))["items"]
            self.assertFalse(items["additionalProperties"])
            self.assertEqual(set(items["required"]), set(items["properties"]))

    def test_grupurile_nu_pierd_probleme(self):
        p = [{"id": str(k)} for k in range(25)]
        g = E.grupuri(p, 12)
        self.assertEqual([len(x) for x in g], [12, 12, 1])
        self.assertEqual([x for y in g for x in y], p)


class TestTabel(unittest.TestCase):
    P = {"titlu": "t", "descriere": "d", "surse": ["E1"], "euristici": ["N1"], "capturi": ["normal"], "dovada": "x", "recomandare": "r"}

    def test_o_infirmare_scoate_problema_din_confirmate(self):
        probleme = [{**self.P, "id": "P01", "severitati": [3, 4]}, {**self.P, "id": "P02", "severitati": [2]}, {**self.P, "id": "P03", "severitati": [4]}]
        verdicte = [{"id": "P01", "verdict": "confirmat", "severitate": 3, "motiv": "a"}, {"id": "P01", "verdict": "confirmat", "severitate": 4, "motiv": "b"},
                    {"id": "P02", "verdict": "confirmat", "severitate": 2, "motiv": "a"}, {"id": "P02", "verdict": "infirmat", "severitate": 0, "motiv": "b"},
                    {"id": "P03", "verdict": "incert", "severitate": 2, "motiv": "a"}]
        t = {r["id"]: r for r in E.tabel_final(probleme, verdicte)}
        self.assertTrue(t["P01"]["confirmat"])
        self.assertEqual(t["P01"]["severitate"], 3.5)
        self.assertFalse(t["P02"]["confirmat"])
        self.assertEqual(t["P02"]["severitate"], 2)       # severitatea infirmatorului nu intră în mediană
        self.assertFalse(t["P03"]["confirmat"])
        self.assertEqual(E.tabel_final(probleme, verdicte)[0]["id"], "P01")


class TestCapturi(unittest.TestCase):
    def test_pagina_are_simularile_si_fotografia(self):
        for v in C.VERSIUNI:
            p = C.pagina(C.VERSIUNI[v].read_text(encoding="utf-8"), 'cere("fix");')
            self.assertIn("window.__netOK", p)
            self.assertLess(p.index("window.__netOK"), p.index("const NUME="))
            self.assertNotIn('"/api/video"', p)
            self.assertNotIn("fonts.googleapis.com/css2", p)
            self.assertIn('cere("fix");', p)
            self.assertIn("fonturi.css", p)

    def test_starile_au_cod_si_ecranele_trimit_la_stari_existente(self):
        self.assertEqual(C.STARI["normal"], "")
        for _, s in C.ECRANE.values():
            self.assertIn(s, C.STARI)
        self.assertGreaterEqual(len(C.fazele()), 3)


if __name__ == "__main__":
    unittest.main()
