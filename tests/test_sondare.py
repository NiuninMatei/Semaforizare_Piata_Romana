"""Teste pentru sondarea dispeceratului (`romana.dashboard.sondare`): parcursul complet, pe un dosar temporar, cu ceas fals.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_sondare
"""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from romana.dashboard import sondare as s


class Ceas:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t

    def mergi(self, d):
        self.t += d


def parcurge(client, ceas, comenzi=None, nu_reuseste=(), raspuns=None):
    """Un participant cap-coadă: alege primul răspuns sau pe cel din `raspuns`; `comenzi` = {id pas: listă de comenzi}."""
    p = client.get("/sondare/pas").get_json()
    while p["tip"] != "sfarsit":
        ceas.mergi(5)
        for c in (comenzi or {}).get(p["id"], []):
            client.post("/api/command", json=c)
            client.post("/sondare/clic", json={"eticheta": c["mod"]})
            ceas.mergi(6)
        corp = {"id": p["id"]}
        if p["tip"] in ("alegere", "scara"):
            corp["valoare"] = (raspuns or {}).get(p["id"], p["optiuni"][0])
        if p["id"] in nu_reuseste:
            corp["nu_reuseste"] = True
        p = client.post("/sondare/raspuns", json=corp).get_json()
    return p


class Baza(unittest.TestCase):
    def setUp(self):
        self.dosar = Path(tempfile.mkdtemp())
        self.ceas = Ceas()
        self.app = s.creeaza_app(self.dosar, cadru_public=True, ceas=self.ceas)
        self.c = self.app.test_client()


class TestParcurs(Baza):
    def test_ordinea_alterneaza_abba(self):
        ordini = []
        for _ in range(4):
            sf = parcurge(self.c, self.ceas)
            self.assertEqual(sf["tip"], "sfarsit")
            ordini.append(tuple(s.citeste_participant(self.dosar / f"{sf['cod']}.jsonl")[0]["ordine"]))
            self.c.post("/sondare/urmatorul")
        self.assertEqual(ordini, [("m1", "m2"), ("m2", "m1"), ("m2", "m1"), ("m1", "m2")])

    def test_raspunsul_corect_nu_ajunge_la_pagina(self):
        p = s.pasi(("m1", "m2"))
        self.assertTrue(any("corect" in x for x in p))
        pub = self.c.get("/sondare/pas").get_json()
        while pub["tip"] != "sfarsit":
            for k in ("corect", "sit", "verifica", "pregateste"):
                self.assertNotIn(k, pub)
            pub = self.c.post("/sondare/raspuns", json={"id": pub["id"], "valoare": (pub.get("optiuni") or [None])[0]}).get_json()

    def test_clicul_dublu_nu_sare_un_pas(self):
        p = self.c.get("/sondare/pas").get_json()
        p2 = self.c.post("/sondare/raspuns", json={"id": p["id"]}).get_json()
        p3 = self.c.post("/sondare/raspuns", json={"id": p["id"]}).get_json()
        self.assertEqual(p2["id"], p3["id"])

    def test_reluarea_dupa_repornire(self):
        p = self.c.get("/sondare/pas").get_json()
        for _ in range(9):
            p = self.c.post("/sondare/raspuns", json={"id": p["id"], "valoare": (p.get("optiuni") or [None])[0]}).get_json()
        pagina = s.creeaza_app(self.dosar, cadru_public=True, ceas=self.ceas).test_client().get("/sondare/pas").get_json()
        self.assertEqual((pagina["cod"], pagina["id"]), (p["cod"], p["id"]))

    def test_codul_neatins_nu_consuma_un_loc(self):
        self.c.get("/sondare/pas")
        self.assertEqual(list(self.dosar.glob("P*.jsonl")), [])

    def test_urmatorul_doar_dupa_sfarsit(self):
        self.c.get("/sondare/pas")
        self.assertEqual(self.c.post("/sondare/urmatorul").status_code, 409)


class TestBanc(Baza):
    def test_cea_mai_lunga_coada_ramane_aceeasi(self):
        b = s.Banc(self.ceas)
        for runda in (0, 1):
            b.seteaza(runda=runda)
            nume = s.corect_coada(runda)
            for _ in range(200):
                self.ceas.mergi(1.7)
                c = b.cozi()
                self.assertEqual(s.NUME_BRAT[max(s.NUME_BRAT, key=lambda x: c[x])], nume)

    def test_faza_noua_vine_dupa_galben_si_rosu(self):
        b = s.Banc(self.ceas)
        b.comanda("manual", 1)
        f = []
        for _ in range(8):
            f.append(b.faza()[1])
            self.ceas.mergi(1)
        self.assertEqual(f, ["yellow"] * 3 + ["red"] * 2 + ["green"] * 3)

    def test_trecerea_pe_manual_pastreaza_faza_verde(self):
        b = s.Banc(self.ceas)
        self.ceas.mergi(2)
        self.assertEqual(b.faza()[:2], (0, "green"))
        b.comanda("manual", 0)
        self.assertEqual(b.faza()[:2], (0, "green"))

    def test_campurile_ca_in_gemanul_real(self):
        st = s.Banc(self.ceas).stare()
        for k in ("mod", "mod_program", "faza", "faza_nume", "etapa", "verde_s", "faze", "model_ai", "coada_brate", "vehicule_in_retea",
                  "pietoni_in_retea", "sursa", "istoric_coada", "_varsta_s"):
            self.assertIn(k, st["simulare"])
        for k in ("conectat", "fps", "vehicule_urmarite", "intrari_veh_h", "iesiri_veh_h", "pietoni_h", "secunde_interval", "_varsta_s"):
            self.assertIn(k, st["camera"])
        self.assertEqual(len(st["simulare"]["faze"]), 5)

    def test_imaginea_oprita_se_vede_in_varsta_starii(self):
        b = s.Banc(self.ceas)
        self.assertLess(b.stare()["camera"]["_varsta_s"], 15)
        b.seteaza(cam="oprita")
        self.assertGreaterEqual(b.stare()["camera"]["_varsta_s"], 15)


class TestSarcini(Baza):
    def _pasi(self, cod="P1"):
        return {o["id"]: o for o in s.citeste_participant(self.dosar / f"{cod}.jsonl") if o.get("tip") == "pas"}

    def test_verde_reusit_si_inapoi_la_calculator(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 0}, {"mod": "manual", "faza": 1}], "r1_automat": [{"mod": "program"}]})
        p = self._pasi()
        self.assertTrue(p["r1_verde"]["reusit"])
        self.assertEqual(len(p["r1_verde"]["comenzi"]), 2)
        self.assertEqual(p["r1_verde"]["clicuri"], 2)
        self.assertTrue(p["r1_automat"]["reusit"])

    def test_culoarea_de_pe_dacia_se_verifica_fata_de_ce_arata_schema(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 1}]}, raspuns={"r1_verde_r": "Verde"})
        self.assertTrue(self._pasi()["r1_verde_r"]["corect"])
        rezumat = [r for r in s.rezumat(self.dosar) if r["masura"] == "verde_r" and r["runda"] == 1]
        self.assertTrue(rezumat[0]["reusit"])

    def test_faza_gresita_nu_e_reusita(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 0}]})
        self.assertFalse(self._pasi()["r1_verde"]["reusit"])

    def test_nu_reusesc_contine_si_cand_starea_ar_fi_buna(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 1}]}, nu_reuseste={"r1_verde"})
        p = self._pasi()
        self.assertFalse(p["r1_verde"]["reusit"])
        self.assertTrue(p["r1_verde"]["nu_reuseste"])

    def test_sarcina_5_porneste_din_manual_si_daca_4_a_esuat(self):
        parcurge(self.c, self.ceas)
        linii = s.citeste_participant(self.dosar / "P1.jsonl")
        self.assertTrue(any(o.get("tip") == "pregatit" and o["pas"] == "r1_automat" for o in linii))
        self.assertFalse(self._pasi()["r1_automat"]["reusit"])

    def test_runda_a_doua_incepe_cu_un_om(self):
        p = self.c.get("/sondare/pas").get_json()
        while p["id"] != "r2_conduce":
            p = self.c.post("/sondare/raspuns", json={"id": p["id"], "valoare": (p.get("optiuni") or [None])[0]}).get_json()
        self.assertEqual(self.c.get("/api/state").get_json()["simulare"]["mod"], "manual")

    def test_situatia_e_refacuta_la_sarcina_4_oricum_ar_fi_umblat(self):
        p = self.c.get("/sondare/pas").get_json()
        while p["id"] != "r1_verde":
            if p["id"] == "r1_conduce":
                self.c.post("/api/command", json={"mod": "manual", "faza": 1})
            p = self.c.post("/sondare/raspuns", json={"id": p["id"], "valoare": (p.get("optiuni") or [None])[0]}).get_json()
        self.assertEqual(self.c.get("/api/state").get_json()["simulare"]["mod"], "program")


class TestSiguranta(Baza):
    def test_comenzile_nu_ating_gemanul_real(self):
        cmd = s.LIVE / "command.json"
        inainte = cmd.read_bytes() if cmd.exists() else None
        moment = cmd.stat().st_mtime if cmd.exists() else None
        self.assertTrue(self.c.post("/api/command", json={"mod": "manual", "faza": 1}).get_json()["ok"])
        self.assertEqual(cmd.read_bytes() if cmd.exists() else None, inainte)
        self.assertEqual(cmd.stat().st_mtime if cmd.exists() else None, moment)

    def test_comenzi_invalide(self):
        self.assertEqual(self.c.post("/api/command", json={"mod": "x"}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": "a"}).status_code, 400)

    def test_versiunea_m1_e_cea_prezentata(self):
        # conținutul din commit-ul 4bd74f4, borna M1
        continut = s.VERSIUNI["m1"].read_bytes().replace(bytes([13, 10]), bytes([10]))
        self.assertEqual(hashlib.sha256(continut).hexdigest(), HASH_M1)

    def test_paginile_se_servesc(self):
        for u in ("/", "/d/m1/", "/d/m2/"):
            self.assertEqual(self.c.get(u).status_code, 200)
        self.assertEqual(self.c.get("/d/altceva/").status_code, 404)


class TestRezultate(Baza):
    def test_scorul_sus(self):
        self.assertEqual(s.scor_sus([5, 1] * 5), 100.0)
        self.assertEqual(s.scor_sus([1, 5] * 5), 0.0)
        self.assertEqual(s.scor_sus([3] * 10), 50.0)

    def test_rezumat_si_grup_fara_coduri_si_fara_text_liber(self):
        verde = {"r1_verde": [{"mod": "manual", "faza": 1}], "r1_automat": [{"mod": "program"}]}
        for i in range(2):
            p = self.c.get("/sondare/pas").get_json()
            while p["tip"] != "sfarsit":
                self.ceas.mergi(4)
                for c in verde.get(p["id"], []):
                    self.c.post("/api/command", json=c)
                corp = {"id": p["id"]}
                if p["tip"] in ("alegere", "scara"):
                    corp["valoare"] = {"r1_real": "Nu", "preferinta": "A doua"}.get(p["id"], p["optiuni"][-1])
                if p["tip"] == "text":
                    corp["valoare"] = "text liber secret"
                p = self.c.post("/sondare/raspuns", json=corp).get_json()
            self.c.post("/sondare/urmatorul")
        cale, randuri = s.scrie_rezumat(self.dosar)
        self.assertTrue(cale.exists())
        sus = [r for r in randuri if r["masura"] == "SUS"]
        self.assertEqual(len(sus), 4)
        self.assertEqual({r["scor"] for r in sus}, {50.0})     # toate „Total de acord”: impare 4, pare 0
        pref = [r["raspuns"] for r in randuri if r["masura"] == "preferinta"]
        self.assertEqual(pref, ["m2", "m1"])                   # „A doua” înseamnă altă versiune la P1 și la P2
        dest = self.dosar / "public.csv"
        s.publica(self.dosar, dest)
        text = dest.read_text(encoding="utf-8")
        self.assertNotIn("secret", text)
        self.assertNotIn("P1", text)
        with open(dest, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        verde_m = [r for r in rows if r["masura"] == "sarcina 4: verde pe Dacia"]
        self.assertEqual({r["versiune"] for r in verde_m}, {"m1", "m2"})
        self.assertEqual(sum(int(r["persoane"]) for r in verde_m), 4)

    def test_jurnalul_are_cate_o_linie_valida_pentru_fiecare_pas(self):
        sf = parcurge(self.c, self.ceas)
        linii = (self.dosar / f"{sf['cod']}.jsonl").read_text(encoding="utf-8").splitlines()
        for l in linii:
            json.loads(l)
        self.assertEqual(sum('"tip": "pas"' in l for l in linii), len(s.pasi(("m1", "m2"))) - 1)


HASH_M1 = "f7986e77a3a7dc04a0319fdb4230629a7f129ad7a02a97824d9fa0056e1c0b84"

if __name__ == "__main__":
    unittest.main()
