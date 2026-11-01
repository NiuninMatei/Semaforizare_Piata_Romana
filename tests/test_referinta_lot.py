"""Teste pentru numărătoarea de referință prin Batch API (`romana.vision.referinta_lot`), fără rețea și fără cheie.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_referinta_lot
"""
import base64
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from romana.vision import referinta_lot as L
from romana.vision.referinta import load_reference

TINTA = {"id": "V_catargiu_seara", "tip": "vehicule", "descriere": "Vehiculele de pe Catargiu."}


class TestCereri(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        for j in (0, 1, 10, 2):
            (self.d / f"b5_f{j}.jpg").write_bytes(bytes([j]) * 10)

    def test_identificatorul_se_citeste_inapoi_si_respecta_api(self):
        c = L.id_cerere("2026-11-01_1830", "V_catargiu_seara", 5, "arbitru")
        self.assertLessEqual(len(c), 64)
        self.assertEqual(L.citeste_id(c), ("2026-11-01_1830", "V_catargiu_seara", 5, "arbitru"))
        with self.assertRaises(ValueError):
            L.id_cerere("clip cu spațiu", "T", 1, "0")

    def test_foile_vin_in_ordinea_timpului(self):
        self.assertEqual([p.name for p in L.foi_bucata(self.d, 5)], ["b5_f0.jpg", "b5_f1.jpg", "b5_f2.jpg", "b5_f10.jpg"])
        with self.assertRaises(SystemExit):
            L.foi_bucata(self.d, 6)

    def test_cererea_are_toate_foile_apoi_regula(self):
        foi = L.foi_bucata(self.d, 5)
        c = L.cerere("x", foi, "regula", "claude-opus-5-5", "high")
        continut = c["params"]["messages"][0]["content"]
        self.assertEqual([b["type"] for b in continut], ["image"] * 4 + ["text"])
        self.assertEqual(base64.b64decode(continut[3]["source"]["data"]), foi[3].read_bytes())
        self.assertEqual(c["params"]["output_config"]["effort"], "high")
        self.assertEqual(c["params"]["output_config"]["format"]["type"], "json_schema")
        self.assertNotIn("thinking", c["params"])       # Opus 5.5 refuză orice altceva decât gândirea implicită

    def test_prompturile_spun_bucata_si_tinta(self):
        p = L.prompt_adnotator(TINTA, 5, L.ROLURI[0])
        self.assertIn("[150, 180) s", p)
        self.assertIn("Vehiculele de pe Catargiu.", p)
        self.assertNotIn("întuneric", p)
        a = L.prompt_arbitru(TINTA, 5, {"numar": 10, "evenimente": [{"t": 1}]}, {"numar": 20, "evenimente": []}, conditii="filmat seara, pe întuneric")
        self.assertIn("Doi adnotatori au dat 10 și 20", a)
        self.assertIn("camerei publice, filmat seara, pe întuneric,", a)

    def test_gandirea_incape_in_iesire(self):
        self.assertEqual(L.EFORT_IMPLICIT, "max")
        self.assertGreater(L.MAX_TOKENI, 63_000)    # cel mai lung adnotator din pilot
        self.assertLessEqual(L.MAX_TOKENI, 128_000)

    def test_loturile_nu_depasesc_limita_si_nu_pierd_cereri(self):
        cereri = [{"custom_id": str(k), "date": "x" * 100} for k in range(10)]
        loturi = L.imparte_pe_loturi(cereri, maxim=350)
        self.assertGreater(len(loturi), 1)
        self.assertEqual([c for lot in loturi for c in lot], cereri)
        self.assertEqual(L.imparte_pe_loturi([]), [])


class TestFelii(unittest.TestCase):
    TINTA = {"id": "T", "benzi": ["sus", "restul"], "descriere_felie": "Vehiculele care intră."}

    def test_feliile_vin_in_ordinea_liniilor(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        for j in (1, 0, 10):
            (d / f"b3_l{j}.jpg").write_bytes(b"x")
        self.assertEqual([p.name for p in L.felii_bucata(d, 3)], ["b3_l0.jpg", "b3_l1.jpg", "b3_l10.jpg"])
        with self.assertRaises(SystemExit):
            L.felii_bucata(d, 4)

    def test_schema_cere_banda_doar_la_felii(self):
        s = L.schema_felie(self.TINTA["benzi"])
        ev = s["properties"]["evenimente"]["items"]
        self.assertEqual(ev["properties"]["banda"]["enum"], ["sus", "restul"])
        self.assertIn("banda", ev["required"])
        self.assertEqual(set(ev["required"]), set(ev["properties"]))
        self.assertNotIn("banda", L.SCHEMA["properties"]["evenimente"]["items"]["properties"])

    def test_cererea_foloseste_schema_data(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / "f.jpg").write_bytes(b"x")
        s = L.schema_felie(self.TINTA["benzi"])
        c = L.cerere("x", [d / "f.jpg"], "regula", "claude-haiku-5-5", "high", s)
        self.assertIs(c["params"]["output_config"]["format"]["schema"], s)

    def test_promptul_explica_imaginea_si_bucata(self):
        p = L.prompt_felie(self.TINTA, 5, L.ROLURI[0], conditii="filmat seara, pe întuneric")
        self.assertIn("Imaginea de mai sus este o FELIE TIMP-SPAȚIU din un clip", p.replace("dintr-un", "din un"))
        self.assertIn("[150, 180) s", p)
        self.assertIn("Vehiculele care intră.", p)
        self.assertIn("filmat seara", p)
        a = L.prompt_felie(self.TINTA, 5, L.rol_arbitru({"numar": 3, "evenimente": []}, {"numar": 9, "evenimente": []}), imagini=2)
        self.assertIn("Cele 2 imagini", a)
        self.assertIn("Doi adnotatori au dat 3 și 9", a)


class TestRezultate(unittest.TestCase):
    def test_toleranta_e_cea_din_referinta(self):
        self.assertTrue(L.adnotatori_de_acord(37, 37))
        self.assertTrue(L.adnotatori_de_acord(3, 5))
        self.assertTrue(L.adnotatori_de_acord(40, 34))     # 15% din 40 = 6
        self.assertFalse(L.adnotatori_de_acord(40, 33))
        self.assertFalse(L.adnotatori_de_acord(3, 6))

    def test_bucatile_de_arbitrat(self):
        i = lambda b, a: L.id_cerere("c", "T", b, a)
        rez = {i(1, "0"): {"numar": 10}, i(1, "1"): {"numar": 10},    # de acord
               i(2, "0"): {"numar": 10}, i(2, "1"): {"numar": 20},    # diferă
               i(3, "0"): {"numar": 10}, i(3, "1"): {"numar": 20}, i(3, "arbitru"): {"numar": 15},    # are deja arbitru
               i(4, "0"): {"numar": 10}}                              # un singur adnotator
        self.assertEqual(L.bucati_de_arbitrat(rez), [("c", "T", 2)])

    def test_csv_se_citeste_de_referinta(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        i = lambda b, a: L.id_cerere("c", "T", b, a)
        L.scrie_csv({i(1, "0"): {"numar": 10}, i(1, "1"): {"numar": 12}, i(2, "0"): {"numar": 5}, i(2, "1"): {"numar": 30}, i(2, "arbitru"): {"numar": 7}}, d / "r.csv")
        self.assertEqual(load_reference(d / "r.csv"), {("T", 1): 11.0, ("T", 2): 7.0})

    def test_costul_e_la_jumatate_de_pret(self):
        self.assertAlmostEqual(L.cost_usd("claude-opus-5-5", 1_000_000, 100_000), (4 + 2) / 2)
        self.assertAlmostEqual(L.cost_usd("claude-haiku-5-5", 1_000_000, 1_000_000), (0.10 + 0.50) / 2)

    def test_schema_e_inchisa_cum_cere_api(self):
        self.assertFalse(L.SCHEMA["additionalProperties"])
        self.assertEqual(set(L.SCHEMA["required"]), set(L.SCHEMA["properties"]))
        ev = L.SCHEMA["properties"]["evenimente"]["items"]
        self.assertFalse(ev["additionalProperties"])
        json.dumps(L.SCHEMA)


class TestCheia(unittest.TestCase):
    def test_cheia_nu_sta_in_depozit(self):
        self.assertNotIn(L.RADACINA, L.CHEIE.parents)

    def test_modulul_nu_cere_biblioteca_la_import(self):
        import sys
        self.assertTrue("romana.vision.referinta_lot" in sys.modules)
        cod = Path(L.__file__).read_text(encoding="utf-8")
        self.assertNotIn("\nimport anthropic", cod)
        self.assertNotIn("ANTHROPIC_API_KEY=", cod)


if __name__ == "__main__":
    unittest.main()
