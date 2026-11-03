"""Măsura nouă (§ 9.11): factorii după lumină și cotele fixe de viraj, fără să schimbe nimic pentru măsura veche.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_masura_noua
"""
import json
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from romana.bridge.build_demand import fara_ora_dublata
from romana.bridge.od_estimation import aplica_cote_fixe, estimate_interval, factor_brat, inaltime_soare
from romana.common import CONFIG_DIR


class TestSoare(unittest.TestCase):
    def test_apusul_si_rasaritul_din_noiembrie(self):
        # București, 2.11.2026: răsărit ≈06:55, apus ≈17:05 (ora de iarnă)
        self.assertLess(inaltime_soare(datetime(2026, 11, 2, 6, 40)), -0.8)
        self.assertGreater(inaltime_soare(datetime(2026, 11, 2, 7, 15)), -0.8)
        self.assertGreater(inaltime_soare(datetime(2026, 11, 2, 16, 45)), -0.8)
        self.assertLess(inaltime_soare(datetime(2026, 11, 2, 17, 30)), -0.8)

    def test_ora_de_vara(self):
        # 1.7.2026, ora de vară: la prânzul solar (≈13:20) Soarele e la ≈68–69°, iar la 21:30 e deja apus
        self.assertAlmostEqual(inaltime_soare(datetime(2026, 7, 1, 13, 20)), 68.5, delta=1.5)
        self.assertLess(inaltime_soare(datetime(2026, 7, 1, 21, 30)), -0.8)

    def test_factorul_dupa_lumina(self):
        v = {"zi": 1.2, "intuneric": 1.5}
        self.assertEqual(factor_brat(v, "2026-11-02 12:00"), 1.2)
        self.assertEqual(factor_brat(v, "2026-11-02 18:00"), 1.5)
        self.assertEqual(factor_brat(2.52, None), 2.52)

    def test_pragul_de_lumina_e_sub_orizont(self):
        # sferturile care decid pragul (§ 5.1): detecția se schimbă cu Soarele la ≈3,9° sub orizont, nu la apus
        v = {"zi": 1.2, "intuneric": 1.5}
        self.assertEqual(factor_brat(v, "2026-10-26 17:30"), 1.2)
        self.assertEqual(factor_brat(v, "2026-10-28 17:30"), 1.5)
        self.assertEqual(factor_brat(v, "2026-11-01 17:15"), 1.2)


class TestOraDublata(unittest.TestCase):
    def _rand(self, inceput, sfarsit, tip="intrare"):
        return {"inceput": pd.Timestamp(inceput), "sfarsit": pd.Timestamp(sfarsit), "tip": tip, "origine": "magheru", "destinatie": "", "vehicul": "passenger", "numar": 1}

    def test_randurile_cu_sfarsitul_inaintea_inceputului_ies(self):
        df = pd.DataFrame([self._rand("2026-10-25 02:45", "2026-10-25 03:00"), self._rand("2026-10-25 03:45", "2026-10-25 03:00")])
        self.assertEqual(len(fara_ora_dublata(df, "x")), 1)

    def test_o_fereastra_pe_ora_dublata_se_refuza(self):
        df = pd.DataFrame([self._rand("2026-10-25 03:00", "2026-10-25 03:15"), self._rand("2026-10-25 03:00", "2026-10-25 03:15")])
        with self.assertRaises(SystemExit):
            fara_ora_dublata(df, "x")


class TestCote(unittest.TestCase):
    def test_cota_fixa_pastreaza_proportiile_si_totalul(self):
        seed = np.array([[60.0, 0.0, 20.0, 20.0], [10.0, 10.0, 10.0, 10.0]])
        o = aplica_cote_fixe(seed, ["a", "b"], ["w", "x", "y", "z"], {"a": {"y": 0.25}})
        self.assertAlmostEqual(o[0].sum(), 100)
        self.assertAlmostEqual(o[0, 2], 25)
        self.assertAlmostEqual(o[0, 0] / o[0, 3], 3)
        self.assertEqual(o[0, 1], 0)
        np.testing.assert_array_equal(o[1], seed[1])
        np.testing.assert_array_equal(seed[0], [60, 0, 20, 20])       # intrarea nu se schimbă

    def test_fara_observatii_restul_se_imparte_egal(self):
        o = aplica_cote_fixe(np.zeros((1, 3)), ["a"], ["x", "y", "z"], {"a": {"x": 0.5}})
        self.assertAlmostEqual(o[0, 0], 0.5)
        self.assertAlmostEqual(o[0, 1], 0.25)


class TestMasuraVeche(unittest.TestCase):
    def cereri(self):
        cfg = json.loads((CONFIG_DIR / "demand.json").read_text(encoding="utf-8"))
        t = pd.Timestamp("2026-10-29 18:00")
        randuri = [("intrare", "magheru", "", "passenger", 100), ("intrare", "catargiu", "", "passenger", 10), ("intrare", "dacia_est", "", "passenger", 30), ("intrare", "dacia_vest", "", "passenger", 40),
                   ("iesire", "", "magheru", "passenger", 50), ("viraj", "magheru", "catargiu", "passenger", 40), ("viraj", "dacia_vest", "dacia_est", "passenger", 20), ("pietoni", "dacia_est", "x", "pieton", 7)]
        sub = pd.DataFrame([{"inceput": t, "sfarsit": t + pd.Timedelta(minutes=15), "tip": a, "origine": b, "destinatie": c, "vehicul": d, "numar": e} for a, b, c, d, e in randuri])
        return cfg, sub

    def test_configuratia_veche_nu_are_cote_si_factorii_sunt_numere(self):
        cfg, sub = self.cereri()
        self.assertNotIn("cote_fixe", cfg)
        r = estimate_interval(sub, cfg, 0.25)
        self.assertAlmostEqual(r["intrari_veh_h"]["catargiu"], 10 * 4 * 2.52, places=1)
        self.assertAlmostEqual(r["intrari_veh_h"]["magheru"], 100 * 4 * 1.09, places=1)
        self.assertEqual(r["pietoni_h"], 7 * 4 * 2.5)

    def test_masura_noua_schimba_factorul_noaptea_si_cota(self):
        cfg, sub = self.cereri()
        cfg = {**cfg, "factor_corectie_detectie": {"magheru": {"zi": 1.0, "intuneric": 2.0}, "catargiu": 1.5, "dacia_est": 1.0, "dacia_vest": 1.0}, "cote_fixe": {"catargiu": {"dacia_vest": 0.25}}}
        r = estimate_interval(sub, cfg, 0.25)
        self.assertAlmostEqual(r["intrari_veh_h"]["magheru"], 100 * 4 * 2.0, places=1)
        i, j = r["origini"].index("catargiu"), r["destinatii"].index("dacia_vest")
        self.assertAlmostEqual(r["od_veh_h"][i][j] / sum(r["od_veh_h"][i]), 0.25, places=2)


if __name__ == "__main__":
    unittest.main()
