"""Lanțul măsurii noi: ce pași rulează, cu ce fișiere, pe ce roluri; măsura veche nu e atinsă."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from romana import lant_cor as L


def comenzi(lista):
    return {p.nume: " ".join(p.comanda[1:]) for p in lista}


class Pasi(unittest.TestCase):
    def test_renumararea_si_scenariile_sunt_pe_masura_noua(self):
        c = comenzi(L.pasi_inainte("2026-11-03", ["08:00-09:00"]))
        self.assertIn("--camera camera_v2.json --pe-persoane --out data/counts_cor", c["recount"])
        self.assertIn("--masura cor --exclude 08:00-09:00", c["scenarii"])
        self.assertIn("cor_zi_2026-11-03_*", c["indisciplinat"])
        self.assertIn("vtypes_indisciplinat_v2.add.xml", c["indisciplinat"])

    def test_antrenarea_ruleaza_referintele_fara_decizie_cat_nu_exista_lista(self):
        lista = L.pasi_dupa("2026-11-03", ["cor_zi_2026-11-03_varf"], [], [], False, Path("nu_exista.json"))
        c = comenzi(lista)
        self.assertEqual(list(c), ["geaman", "test_indisciplinat", "test_normal"])
        self.assertIn("PLAN_72_48_3 REAL", c["test_normal"])
        self.assertIn("--seeds 1-10", c["test_normal"])
        self.assertNotIn("--praguri", c["geaman"])
        self.assertIn("--poarta outputs/validare/poarta_cor_2026-11-03.json", c["geaman"])

    def test_validarea_are_seedurile_ei_si_decide_cu_cele_doua_referinte_si_cu_poarta(self):
        c = comenzi(L.pasi_dupa("2026-11-04", ["cor_zi_2026-11-04_varf"], ["PLAN_60_40_3", "models/e15.zip"], ["ACTUATED"], False, Path("nu_exista.json")))
        self.assertIn("--seeds 11-15", c["test_normal"])
        self.assertIn("PLAN_72_48_3 REAL PLAN_60_40_3 models/e15.zip ACTUATED", c["test_normal"])
        self.assertIn("--in-vigoare PLAN_72_48_3 REAL --candidati PLAN_60_40_3 models/e15.zip --poarta outputs/validare/poarta_cor_2026-11-04.json", c["decizie"])
        self.assertNotIn("ACTUATED", c["decizie"])           # o strategie raportată nu poate câștiga

    def test_zilele_de_test_sunt_sigilate_pana_la_desigilare(self):
        ore = ["cor_zi_2026-11-05_varf"]
        self.assertEqual(list(comenzi(L.pasi_dupa("2026-11-05", ore, ["X"], [], False, Path("nu_exista.json")))), ["geaman"])
        self.assertEqual(list(comenzi(L.pasi_dupa("2026-11-05", ore, ["X"], [], True, Path("nu_exista.json")))), ["geaman", "test_indisciplinat", "test_normal", "decizie"])
        self.assertEqual(list(comenzi(L.pasi_dupa("2026-11-07", ore, ["X"], [], False, Path("nu_exista.json")))), ["geaman"])
        self.assertIn("--seeds 1-10", comenzi(L.pasi_dupa("2026-11-05", ore, ["X"], [], True, Path("nu_exista.json")))["test_normal"])

    def test_pragurile_inghetate_intra_cand_exista(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cale = Path(f.name)
        try:
            self.assertIn(f"--praguri {cale}", comenzi(L.pasi_dupa("2026-11-03", ["o"], [], [], False, cale))["geaman"])
        finally:
            cale.unlink()

    def test_lista_candidatilor_lipseste_pana_la_termen(self):
        self.assertEqual(L.lista_candidati(Path("nu_exista.json")), [])
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "c.json"
            c.write_text(json.dumps({"candidati": ["A", "B"], "raportate": ["C"]}), encoding="utf-8")
            self.assertEqual(L.lista_candidati(c), ["A", "B"])
            self.assertEqual(L.strategii_raportate(c), ["C"])


class Lant(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.t = Path(d.name)
        (self.t / "raw").mkdir()
        (self.t / "raw" / "traiectorii_2026-11-03.jsonl.gz").write_bytes(b"x")
        (self.t / "demand").mkdir()
        (self.t / "scen").mkdir()
        (self.t / "demand" / "cor_zi_2026-11-03_rezumat.json").write_text(json.dumps({"ferestre": {"varf": [1, 2]}, "scenarii": ["cor_zi_2026-11-03_varf"]}), encoding="utf-8")
        self.rulate = []
        for nume, val in (("DIR_COR", self.t / "cor"), ("ROOT", self.t), ("TRAJ_RAW_DIR", self.t / "raw"), ("DEMAND_DIR", self.t / "demand"), ("CANDIDATI", self.t / "nu.json"), ("PRAGURI", self.t / "nu2.json"),
                          ("prioritate_scazuta", lambda: (True, "prioritate")), ("excluderi_zi", lambda zi, ex, note: list(ex)), ("curata_scenarii", lambda zi, note: None)):
            p = mock.patch.object(L, nume, val)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(L.lista_candidati, "__defaults__", (self.t / "nu.json",))
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(L.strategii_raportate, "__defaults__", (self.t / "nu.json",))
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(L.pasi_dupa, "__defaults__", (self.t / "nu2.json",))
        p.start()
        self.addCleanup(p.stop)

    def rulator(self, cod=lambda nume: 0):
        def r(cmd, cale, note):
            nume = Path(cale).stem
            self.rulate.append(nume)
            for k in ("--poarta", "--out"):
                if k in cmd and cod(nume) == 0:
                    g = self.t / cmd[cmd.index(k) + 1]
                    g.parent.mkdir(parents=True, exist_ok=True)
                    g.write_text("x", encoding="utf-8")
            return cod(nume)
        return r

    def test_ruleaza_pasii_in_ordine_si_scrie_starea(self):
        self.assertEqual(L.lant("2026-11-03", rulator=self.rulator()), 0)
        self.assertEqual(self.rulate, ["recount", "scenarii", "indisciplinat", "geaman", "test_indisciplinat", "test_normal"])
        s = json.loads((self.t / "cor" / "2026-11-03" / "stare.json").read_text(encoding="utf-8"))
        self.assertEqual(s["rezultat"], "gata")

    def test_fara_renumarare_se_opreste(self):
        self.assertEqual(L.lant("2026-11-03", rulator=self.rulator(lambda n: 1 if n == "recount" else 0)), 1)
        self.assertEqual(self.rulate, ["recount"])

    def test_un_test_picat_nu_opreste_celalalt_comportament(self):
        self.assertEqual(L.lant("2026-11-03", rulator=self.rulator(lambda n: 1 if n == "test_indisciplinat" else 0)), 1)
        self.assertIn("test_normal", self.rulate)

    def test_reluarea_sare_ce_s_a_incheiat(self):
        L.lant("2026-11-03", rulator=self.rulator(lambda n: 1 if n == "test_normal" else 0))
        self.rulate.clear()
        L.lant("2026-11-03", reia=True, rulator=self.rulator())
        self.assertEqual(self.rulate, ["test_normal"])

    def test_fara_jurnal_se_opreste(self):
        self.assertEqual(L.lant("2026-11-04", rulator=self.rulator()), 1)
        self.assertEqual(self.rulate, [])


class Bucla(unittest.TestCase):
    def test_asteapta_lantul_vechi_si_ia_ziua_de_ieri(self):
        acum = [datetime(2026, 11, 3, 12, 0)]
        rulate = []

        def dormi(s):
            acum[0] += timedelta(seconds=s)

        verificari = iter([False, True])
        with mock.patch.object(L, "lant_vechi_incheiat", lambda zi: next(verificari, True)):
            L.bucla("03:30", datetime(2026, 11, 4, 12, 0), ceas=lambda: acum[0], dormi=dormi, rulare=lambda zi, reia: rulate.append((zi, reia)))
        self.assertEqual(rulate, [("2026-11-03", True)])

    def test_o_noapte_picata_nu_opreste_buclele_urmatoare(self):
        acum = [datetime(2026, 11, 3, 12, 0)]
        rulate = []

        def dormi(s):
            acum[0] += timedelta(seconds=s)

        def rulare(zi, reia):
            rulate.append(zi)
            raise RuntimeError("picat")
        with mock.patch.object(L, "lant_vechi_incheiat", lambda zi: True), mock.patch.object(L, "DIR_COR", Path(tempfile.mkdtemp())):
            L.bucla("03:30", datetime(2026, 11, 5, 12, 0), ceas=lambda: acum[0], dormi=dormi, rulare=rulare)
        self.assertEqual(rulate, ["2026-11-03", "2026-11-04"])


if __name__ == "__main__":
    unittest.main()
