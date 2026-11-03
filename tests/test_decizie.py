"""Regula de decizie cu două referințe (§ 9.11): se bat amândouă, iar semaforul rejucat contează doar pe orele acoperite."""
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from romana.control import decizie

SC = ["cor_zi_2026-11-05_varf", "indisciplinat_cor_zi_2026-11-05_varf", "cor_zi_2026-11-05_linistit", "indisciplinat_cor_zi_2026-11-05_linistit"]


def rulari(pierderi: dict[str, dict[str, float]], seeduri=range(1, 11)) -> list[dict]:
    """Pierderile pe tip de oră, cu un zgomot mic și reproductibil, pe fiecare seed."""
    r, z = [], random.Random(7)
    for model, pe_ora in pierderi.items():
        for sc in SC:
            baza = pe_ora["varf"] if "varf" in sc else pe_ora["linistit"]
            r += [{"model": model, "scenariu": sc, "seed": k, "pierdere_h": baza + z.uniform(-0.5, 0.5)} for k in seeduri]
    return r


class Referinte(unittest.TestCase):
    def ruleaza(self, pierderi, *argumente, acoperire=None):
        with tempfile.TemporaryDirectory() as d:
            csv, out = Path(d) / "r.csv", Path(d) / "d.json"
            pd.DataFrame(rulari(pierderi)).to_csv(csv, index=False)
            acop = acoperire or {"varf": 0.9, "linistit": 0.1}
            with mock.patch.object(decizie, "debite", lambda sc: {s: 5000.0 if "varf" in s else 1000.0 for s in sc}), \
                 mock.patch.object(decizie, "acoperiri", lambda sc: {s: acop["varf" if "varf" in s else "linistit"] for s in sc}):
                decizie.main([str(csv), "--out", str(out), "--program", "X=lejer:PLAN_A,moderat:PLAN_A,greu:PLAN_A", *argumente])
            return json.loads(out.read_text(encoding="utf-8"))

    def test_candidatul_care_bate_una_singura_nu_trece(self):
        p = {"C": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 70, "linistit": 12}}
        d = self.ruleaza(p, "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "C")
        self.assertEqual(d["castigator"], "PLAN_72_48_3")
        self.assertFalse(d["candidati"][0]["eligibil"])

    def test_candidatul_care_le_bate_pe_amandoua_trece(self):
        p = {"C": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 90, "linistit": 12}}
        d = self.ruleaza(p, "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "C")
        self.assertEqual(d["castigator"], "C")
        self.assertEqual(d["referinte"], ["PLAN_72_48_3", "REAL"])

    def test_real_nu_conteaza_pe_orele_neacoperite(self):
        # pe orele liniștite, REAL e mult mai bun; nu contează, fiindcă acolo e în cea mai mare parte presupus
        p = {"C": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 90, "linistit": 1}}
        d = self.ruleaza(p, "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "C")
        self.assertEqual(d["castigator"], "C")
        self.assertEqual(d["candidati"][0]["alte_referinte"]["REAL"]["fata_de_in_vigoare"]["n"], 20)   # doar vârful, cele 2 comportamente × 10 seed-uri

    def test_agentul_se_poate_da_prin_calea_modelului(self):
        # ca în `config/candidati_v2.json`: lista dă calea, iar rezultatele au numele fișierului
        p = {"e15": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 90, "linistit": 12}}
        d = self.ruleaza(p, "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "models/e15.zip")
        self.assertEqual(d["castigator"], "e15")

    def test_fara_nicio_ora_acoperita_se_opreste(self):
        p = {"C": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 90, "linistit": 12}}
        with self.assertRaises(SystemExit):
            self.ruleaza(p, "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "C", acoperire={"varf": 0.5, "linistit": 0.1})

    def test_slab_intr_un_comportament_fata_de_a_doua_referinta(self):
        rand = {"C": {"varf": 80, "linistit": 10}, "PLAN_72_48_3": {"varf": 100, "linistit": 12}, "REAL": {"varf": 90, "linistit": 12}}
        with tempfile.TemporaryDirectory() as d:
            csv, out = Path(d) / "r.csv", Path(d) / "d.json"
            df = pd.DataFrame(rulari(rand))
            df.loc[(df.model == "C") & df.scenariu.str.startswith("indisciplinat_") & df.scenariu.str.contains("varf"), "pierdere_h"] = 95.0
            df.loc[(df.model == "C") & ~df.scenariu.str.startswith("indisciplinat_") & df.scenariu.str.contains("varf"), "pierdere_h"] = 40.0
            df.to_csv(csv, index=False)
            with mock.patch.object(decizie, "debite", lambda sc: {s: 5000.0 if "varf" in s else 1000.0 for s in sc}), \
                 mock.patch.object(decizie, "acoperiri", lambda sc: {s: 0.9 if "varf" in s else 0.1 for s in sc}):
                decizie.main([str(csv), "--out", str(out), "--program", "X=lejer:C,moderat:C,greu:C", "--in-vigoare", "PLAN_72_48_3", "REAL", "--candidati", "C"])
            r = json.loads(out.read_text(encoding="utf-8"))
        self.assertFalse(r["candidati"][0]["eligibil"])

    def test_cu_o_singura_referinta_iesirea_ramane_cea_veche(self):
        p = {"C": {"varf": 80, "linistit": 10}, "PLAN_A": {"varf": 100, "linistit": 12}}
        d = self.ruleaza(p, "--in-vigoare", "PLAN_A", "--candidati", "C")
        self.assertEqual(d["castigator"], "C")
        self.assertNotIn("referinte", d)
        self.assertNotIn("alte_referinte", d["candidati"][0])


class Poarta(unittest.TestCase):
    PIERDERI = {"C": {"varf": 80, "linistit": 11}, "PLAN_A": {"varf": 100, "linistit": 10}}

    def ruleaza(self, trec):
        with tempfile.TemporaryDirectory() as d:
            csv, out, poarta = Path(d) / "r.csv", Path(d) / "d.json", Path(d) / "p.json"
            pd.DataFrame(rulari(self.PIERDERI)).to_csv(csv, index=False)
            poarta.write_text(json.dumps({"commit": "abc", "scenarii": {"cor_zi_2026-11-05_varf": {"trece": "varf" in trec}, "cor_zi_2026-11-05_linistit": {"trece": "linistit" in trec}}}), encoding="utf-8")
            with mock.patch.object(decizie, "debite", lambda sc: {s: 5000.0 if "varf" in s else 1000.0 for s in sc}):
                decizie.main([str(csv), "--out", str(out), "--program", "X=lejer:PLAN_A,moderat:PLAN_A,greu:PLAN_A", "--in-vigoare", "PLAN_A", "--candidati", "C", "--poarta", str(poarta)])
            return json.loads(out.read_text(encoding="utf-8"))

    def test_ora_de_baza(self):
        self.assertEqual(decizie.ora_de_baza("indisciplinat_cor_zi_2026-11-05_varf_x1_2"), "cor_zi_2026-11-05_varf")
        self.assertEqual(decizie.ore_care_trec(["cor_zi_2026-11-05_varf", "cor_zi_2026-11-05_seara"], {"cor_zi_2026-11-05_varf": {"trece": True}}), ({"cor_zi_2026-11-05_varf"}, {"cor_zi_2026-11-05_seara"}))

    def test_orele_care_nu_trec_nu_intra(self):
        d = self.ruleaza({"varf", "linistit"})
        self.assertEqual(d["poarta"]["nu_trec"], [])
        self.assertEqual(d["candidati"][0]["fata_de_in_vigoare"]["n"], 40)
        d = self.ruleaza({"varf"})
        self.assertEqual(d["poarta"]["nu_trec"], ["cor_zi_2026-11-05_linistit"])
        self.assertEqual(d["candidati"][0]["fata_de_in_vigoare"]["n"], 20)
        self.assertEqual(d["castigator"], "C")

    def test_portile_a_doua_zile_de_test_se_unesc(self):
        with tempfile.TemporaryDirectory() as d:
            csv, out, p1, p2 = Path(d) / "r.csv", Path(d) / "d.json", Path(d) / "p1.json", Path(d) / "p2.json"
            pd.DataFrame(rulari(self.PIERDERI)).to_csv(csv, index=False)
            p1.write_text(json.dumps({"commit": "a", "scenarii": {"cor_zi_2026-11-05_varf": {"trece": True}}}), encoding="utf-8")
            p2.write_text(json.dumps({"commit": "b", "scenarii": {"cor_zi_2026-11-05_linistit": {"trece": False}}}), encoding="utf-8")
            with mock.patch.object(decizie, "debite", lambda sc: {s: 5000.0 if "varf" in s else 1000.0 for s in sc}):
                decizie.main([str(csv), "--out", str(out), "--program", "X=lejer:PLAN_A,moderat:PLAN_A,greu:PLAN_A", "--in-vigoare", "PLAN_A",
                              "--candidati", "C", "--poarta", str(p1), str(p2)])
            r = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual((r["poarta"]["trec"], r["poarta"]["nu_trec"]), (["cor_zi_2026-11-05_varf"], ["cor_zi_2026-11-05_linistit"]))
        self.assertEqual(r["poarta"]["commit_validare"], ["a", "b"])

    def test_sub_jumatate_din_ore_ziua_e_descriptiva(self):
        d = self.ruleaza(set())
        self.assertTrue(d["poarta"]["descriptiv"])
        self.assertEqual(d["castigator"], "PLAN_A")
        self.assertIn("descriptivă", d["motiv"])


if __name__ == "__main__":
    unittest.main()
