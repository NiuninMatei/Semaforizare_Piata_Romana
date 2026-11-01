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


def corp_pas(p, raspuns=None, nu_reuseste=()):
    c = {"id": p["id"]}
    if p["tip"] == "alegere":
        c["valoare"] = (raspuns or {}).get(p["id"], p["optiuni"][0])
    if p["tip"] == "text":
        c["valoare"] = (raspuns or {}).get(p["id"], "")
    if p["id"] in nu_reuseste:
        c["nu_reuseste"] = True
    return c


def parcurge(client, ceas, comenzi=None, nu_reuseste=(), raspuns=None, pana_la="sfarsit"):
    """Un participant până la pasul `pana_la`: alege primul răspuns sau pe cel din `raspuns`; `comenzi` = {id pas: listă de comenzi}."""
    p = client.get("/sondare/pas").get_json()
    while p["id"] != pana_la and p["tip"] != "sfarsit":
        ceas.mergi(5)
        for c in (comenzi or {}).get(p["id"], []):
            client.post("/sondare/clic", json={"eticheta": c["mod"]})
            client.post("/api/command", json=c)
            ceas.mergi(12)
        p = client.post("/sondare/raspuns", json=corp_pas(p, raspuns, nu_reuseste)).get_json()
    return p


class Baza(unittest.TestCase):
    def setUp(self):
        self.dosar = Path(tempfile.mkdtemp())
        self.ceas = Ceas()
        self.app = s.creeaza_app(self.dosar, cadru_public=True, ceas=self.ceas)
        self.c = self.app.test_client()

    def pasi_jurnal(self, cod="P1"):
        return {o["id"]: o for o in s.citeste_participant(self.dosar / f"{cod}.jsonl") if o.get("tip") == "pas"}


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
        self.assertTrue(any("corect" in x for x in s.pasi(("m1", "m2"))))
        pub = self.c.get("/sondare/pas").get_json()
        while pub["tip"] != "sfarsit":
            for k in ("corect", "corect_din_banc", "sit", "verifica", "pregateste"):
                self.assertNotIn(k, pub)
            pub = self.c.post("/sondare/raspuns", json=corp_pas(pub)).get_json()

    def test_raspunsul_pentru_alt_pas_nu_sare(self):
        p = self.c.get("/sondare/pas").get_json()
        p2 = self.c.post("/sondare/raspuns", json={"id": p["id"]}).get_json()
        p3 = self.c.post("/sondare/raspuns", json={"id": p["id"]}).get_json()
        self.assertEqual(p2["id"], p3["id"])

    def test_valoare_din_afara_optiunilor_se_ignora(self):
        p = parcurge(self.c, self.ceas, pana_la="profil_calculator")
        self.assertEqual(self.c.post("/sondare/raspuns", json={"id": p["id"], "valoare": "Un nume, 74 de ani"}).get_json()["id"], p["id"])
        self.assertNotIn("74", (self.dosar / "P1.jsonl").read_text(encoding="utf-8"))

    def test_corpuri_stricate_nu_dau_eroare(self):
        for u in ("/sondare/raspuns", "/sondare/clic", "/api/command"):
            self.assertLess(self.c.post(u, data="[1,2]", content_type="application/json").status_code, 500)

    def test_textul_cu_separatori_ciudati_nu_se_pierde(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_incurcat")
        self.c.post("/sondare/raspuns", json={"id": p["id"], "valoare": "un doi\u0085trei"})
        self.assertEqual(self.pasi_jurnal()["r1_incurcat"]["valoare"], "un doi\u0085trei")

    def test_codul_neatins_nu_consuma_un_loc(self):
        self.c.get("/sondare/pas")
        self.assertEqual(list(self.dosar.glob("P*.jsonl")), [])

    def test_urmatorul_doar_dupa_sfarsit(self):
        p = self.c.get("/sondare/pas").get_json()
        self.assertEqual(self.c.post("/sondare/urmatorul").get_json()["id"], p["id"])

    def test_durata_e_rezonabil_de_scurta(self):
        pasi_persoana = [x for x in s.pasi(("m1", "m2")) if x["id"] not in ("pregatire", "observatii", "moderator", "sfarsit")]
        self.assertLessEqual(len(pasi_persoana), 38)


class TestOprire(Baza):
    def test_cel_care_se_opreste_nu_il_incurca_pe_urmatorul(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_verde")
        self.assertEqual(p["cod"], "P1")
        nou = self.c.post("/sondare/renunta").get_json()
        self.assertEqual((nou["cod"], nou["id"]), ("P2", "pregatire"))
        linii = s.citeste_participant(self.dosar / "P1.jsonl")
        self.assertEqual(linii[-1]["tip"], "renuntat")
        # și după o repornire a serverului
        din_nou = s.creeaza_app(self.dosar, cadru_public=True, ceas=self.ceas).test_client().get("/sondare/pas").get_json()
        self.assertEqual(din_nou["cod"], "P2")

    def test_cine_s_a_oprit_nu_intra_in_totaluri(self):
        parcurge(self.c, self.ceas, pana_la="r1_verde")
        self.c.post("/sondare/renunta")
        randuri = s.rezumat(self.dosar)
        self.assertTrue(randuri)
        self.assertEqual(s.pe_grup(randuri), [])

    def test_situatia_revine_la_inceput_pentru_urmatorul(self):
        parcurge(self.c, self.ceas, pana_la="r2_conduce")
        self.assertEqual(self.c.get("/api/state").get_json()["simulare"]["mod"], "manual")
        self.c.post("/sondare/renunta")
        self.assertEqual(self.c.get("/api/state").get_json()["simulare"]["mod"], "program")


class TestRepornire(Baza):
    def _din_nou(self):
        return s.creeaza_app(self.dosar, cadru_public=True, ceas=self.ceas).test_client()

    def test_continua_de_la_acelasi_pas_si_aceleasi_comenzi(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_verde")
        self.c.post("/sondare/clic", json={"eticheta": "Manual"})
        self.c.post("/api/command", json={"mod": "manual", "faza": 1})
        self.ceas.mergi(20)
        c2 = self._din_nou()
        pagina = c2.get("/sondare/pas").get_json()
        self.assertEqual((pagina["cod"], pagina["id"]), (p["cod"], p["id"]))
        self.assertTrue(c2.application.banc.verde_pe_dacia())
        c2.post("/sondare/raspuns", json={"id": p["id"]})
        rand = self.pasi_jurnal()["r1_verde"]
        self.assertTrue(rand["reusit"])
        self.assertEqual(rand["clicuri"], 1)
        self.assertEqual(rand["comenzi"], [["manual", 1]])

    def test_adevarul_notat_ramane_dupa_repornire(self):
        p = parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 1}]}, pana_la="r1_verde_r")
        c2 = self._din_nou()
        self.ceas.mergi(300)
        c2.post("/sondare/raspuns", json={"id": p["id"], "valoare": "Roșu"})
        self.assertTrue(self.pasi_jurnal()["r1_verde_r"]["corect"])

    def test_nicio_pregatire_falsa_dupa_repornire(self):
        p = parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 1}]}, pana_la="r1_automat")
        self.c.post("/api/command", json={"mod": "program"})
        c2 = self._din_nou()
        self.assertEqual(c2.get("/sondare/pas").get_json()["id"], p["id"])
        self.assertEqual(c2.application.banc.mod, "program")
        self.assertFalse(any(o.get("tip") == "pregatit" for o in s.citeste_participant(self.dosar / "P1.jsonl")))

    def test_linia_intrerupta_nu_strica_raspunsul_urmator(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_conduce_r")
        with open(self.dosar / "P1.jsonl", "ab") as f:
            f.write(b'{"t": 1, "tip": "pas", "ind')
        c2 = self._din_nou()
        self.assertEqual(c2.get("/sondare/pas").get_json()["id"], p["id"])
        c2.post("/sondare/raspuns", json={"id": p["id"], "valoare": p["optiuni"][0]})
        self.assertIn("r1_conduce_r", self.pasi_jurnal())

    def test_fisier_gol(self):
        (self.dosar / "P1.jsonl").write_bytes(b"")
        self.assertEqual(self._din_nou().get("/sondare/pas").status_code, 200)


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

    def test_debitele_nu_dau_raspunsul_la_coada(self):
        for runda in (0, 1):
            cel_mai_mare = max(s.INTRARI[runda], key=s.INTRARI[runda].get)
            self.assertNotEqual(s.NUME_BRAT[cel_mai_mare], s.corect_coada(runda))

    def test_faza_veche_ramane_pana_la_galben_si_rosu_ca_in_geaman(self):
        b = s.Banc(self.ceas)
        b.seteaza(mod="program", nemiscat=True)
        self.ceas.mergi(2)
        b.comanda("manual", 1)
        etape = []
        for _ in range(12):
            etape.append(b.faza()[:2])
            self.ceas.mergi(1)
        self.assertEqual(etape[0], (0, "green"))
        self.assertIn((0, "yellow"), etape)
        self.assertIn((0, "red"), etape)
        self.assertEqual(etape[-1], (1, "green"))
        self.assertLess(etape.index((1, "green")), 11)
        self.assertGreaterEqual(etape.index((1, "green")), 5)

    def test_verdele_minim_se_respecta(self):
        b = s.Banc(self.ceas)
        self.assertEqual(b.faza()[:2], (0, "green"))       # planul tocmai a început: verdele are 0 s
        b.comanda("manual", 1)
        self.ceas.mergi(9.9)
        self.assertEqual(b.faza()[:2], (0, "green"))

    def test_trecerea_pe_manual_pastreaza_faza_verde(self):
        b = s.Banc(self.ceas)
        self.ceas.mergi(2)
        b.comanda("manual", 0)
        self.assertEqual(b.faza()[:2], (0, "green"))
        self.assertEqual(b.mod, "manual")

    def test_planul_continua_din_faza_curenta_la_revenire(self):
        b = s.Banc(self.ceas)
        b.seteaza(mod="manual", faza=1)
        self.ceas.mergi(5)
        b.comanda("program", None)
        self.assertEqual(b.faza()[0], 1)

    def test_nemiscat_dacia_nu_devine_verde_singura(self):
        b = s.Banc(self.ceas)
        b.seteaza(mod="program", nemiscat=True)
        for _ in range(240):
            self.ceas.mergi(1)
            self.assertEqual(b.faza()[0], 0)

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
    def test_verde_reusit_si_inapoi_la_calculator(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 0}, {"mod": "manual", "faza": 1}], "r1_automat": [{"mod": "program"}]})
        p = self.pasi_jurnal()
        self.assertTrue(p["r1_verde"]["reusit"])
        self.assertEqual(len(p["r1_verde"]["comenzi"]), 2)
        self.assertEqual(p["r1_verde"]["clicuri"], 2)
        self.assertTrue(p["r1_automat"]["reusit"])

    def test_fazele_fara_dozare_dau_si_ele_verde_pe_dacia(self):
        for faza, asteptat in ((3, True), (4, True), (2, False), (0, False)):
            c = s.creeaza_app(Path(tempfile.mkdtemp()), cadru_public=True, ceas=self.ceas)
            cl = c.test_client()
            parcurge(cl, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": faza}]}, pana_la="r1_verde_r")
            self.assertEqual(c.banc.verde_pe_dacia(), asteptat, faza)

    def test_nu_reusesc_ramane_nereusit_chiar_daca_starea_ar_fi_buna(self):
        parcurge(self.c, self.ceas, comenzi={"r1_verde": [{"mod": "manual", "faza": 1}]}, nu_reuseste={"r1_verde"})
        p = self.pasi_jurnal()
        self.assertFalse(p["r1_verde"]["reusit"])
        self.assertTrue(p["r1_verde"]["nu_reuseste"])

    def test_sarcina_de_revenire_porneste_din_manual_si_daca_verde_a_esuat(self):
        parcurge(self.c, self.ceas)
        linii = s.citeste_participant(self.dosar / "P1.jsonl")
        self.assertTrue(any(o.get("tip") == "pregatit" and o["pas"] == "r1_automat" for o in linii))
        self.assertFalse(self.pasi_jurnal()["r1_automat"]["reusit"])

    def test_cine_conduce_se_noteaza_dupa_ce_arata_ecranul(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_conduce")
        self.c.post("/api/command", json={"mod": "manual", "faza": 0})
        self.c.post("/sondare/raspuns", json={"id": p["id"]})
        self.c.post("/sondare/raspuns", json={"id": "r1_conduce_r", "valoare": s.ALEGE_CONDUCE["om"]})
        self.assertTrue(self.pasi_jurnal()["r1_conduce_r"]["corect"])

    def test_runda_a_doua_incepe_cu_un_om(self):
        parcurge(self.c, self.ceas, pana_la="r2_conduce")
        self.assertEqual(self.c.get("/api/state").get_json()["simulare"]["mod"], "manual")

    def test_imaginea_se_opreste_doar_in_prima_runda_cat_se_cauta_coada(self):
        parcurge(self.c, self.ceas, pana_la="r1_coada")
        self.assertEqual(self.app.banc.cam, "oprita")
        parcurge(self.c, self.ceas, pana_la="r1_verde")
        self.assertEqual(self.app.banc.cam, "merge")
        parcurge(self.c, self.ceas, pana_la="r2_coada")
        self.assertEqual(self.app.banc.cam, "merge")

    def test_situatia_e_refacuta_la_sarcina_de_verde_oricum_ar_fi_umblat(self):
        p = parcurge(self.c, self.ceas, pana_la="r1_conduce")
        self.c.post("/api/command", json={"mod": "manual", "faza": 1})
        parcurge(self.c, self.ceas, pana_la="r1_verde")
        st = self.c.get("/api/state").get_json()["simulare"]
        self.assertEqual((st["mod"], st["faza"]), ("program", 0))

    def test_intrebarile_de_perceptie_doar_la_prima_vedere(self):
        ids = [x["id"] for x in s.pasi(("m1", "m2"))]
        self.assertIn("r1_real", ids)
        self.assertNotIn("r2_real", ids)
        self.assertIn("r1_culori", ids)
        self.assertNotIn("r2_culori", ids)


class TestSiguranta(Baza):
    def test_comenzile_nu_ating_gemanul_real(self):
        cmd = s.LIVE / "command.json"
        inainte = cmd.read_bytes() if cmd.exists() else None
        moment = cmd.stat().st_mtime if cmd.exists() else None
        parcurge(self.c, self.ceas, pana_la="r1_verde")
        self.assertTrue(self.c.post("/api/command", json={"mod": "manual", "faza": 1}).get_json()["ok"])
        self.assertEqual(cmd.read_bytes() if cmd.exists() else None, inainte)
        self.assertEqual(cmd.stat().st_mtime if cmd.exists() else None, moment)

    def test_comenzi_invalide(self):
        self.assertEqual(self.c.post("/api/command", json={"mod": "x"}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": "a"}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": 99}).status_code, 400)

    def test_comenzile_din_afara_sarcinilor_nu_schimba_nimic(self):
        self.c.get("/sondare/pas")
        self.assertTrue(self.c.post("/api/command", json={"mod": "manual", "faza": 1}).get_json()["ok"])
        self.assertEqual(self.app.banc.mod, "program")
        self.assertEqual(list(self.dosar.glob("P*.jsonl")), [])

    def test_versiunea_m1_e_cea_prezentata(self):
        # conținutul din commit-ul 4bd74f4, borna M1
        continut = s.VERSIUNI["m1"].read_bytes().replace(bytes([13, 10]), bytes([10]))
        self.assertEqual(hashlib.sha256(continut).hexdigest(), HASH_M1)

    def test_paginile_se_servesc(self):
        for u in ("/", "/d/m1/", "/d/m2/"):
            r = self.c.get(u)
            self.assertEqual(r.status_code, 200)
            r.close()
        self.assertEqual(self.c.get("/d/altceva/").status_code, 404)


class TestRezultate(Baza):
    def _doi(self):
        verde = {"r1_verde": [{"mod": "manual", "faza": 1}], "r1_automat": [{"mod": "program"}]}
        for _ in range(4):
            parcurge(self.c, self.ceas, comenzi=verde, raspuns={"r1_real": "Nu", "preferinta": "A doua", "r1_incurcat": "text liber secret",
                                                                 "observatii": "observatie secreta", "profil_calculator": "Rar sau deloc",
                                                                 "r1_usor": "Ușor", "moderator": "Nu"})
            self.c.post("/sondare/urmatorul")

    def test_rezumatul_numara_corect(self):
        self._doi()
        cale, randuri = s.scrie_rezumat(self.dosar)
        self.assertTrue(cale.exists())
        # „A doua” înseamnă altă versiune, după ordine: P1 m2, P2 m1, P3 m1, P4 m2
        self.assertEqual([r["raspuns"] for r in randuri if r["masura"] == "preferinta"], ["m2", "m1", "m1", "m2"])
        verde = [r for r in randuri if r["masura"] == "sarcina 3: verde pe Dacia" and r["runda"] == 1]
        self.assertEqual(len(verde), 4)
        self.assertTrue(all(r["reusit"] for r in verde))
        ajutor = [r for r in randuri if r["masura"] == "moderator"]
        self.assertEqual(len(ajutor), 4)
        self.assertIn("observatie secreta", cale.read_text(encoding="utf-8"))

    def test_totalurile_pe_versiune_si_prima_runda(self):
        self._doi()
        grup = {(r["masura"], r["versiune"]): r for r in s.pe_grup(s.rezumat(self.dosar))}
        r = grup[("sarcina 3: verde pe Dacia", "m1")]
        self.assertEqual((r["persoane"], r["reusite"], r["persoane_prima_runda"]), (4, 2, 2))
        self.assertEqual(r["reusite_prima_runda"], 2)

    def test_fisierul_public_are_doar_totaluri(self):
        self._doi()
        dest = self.dosar / "public.csv"
        s.publica(self.dosar, dest)
        text = dest.read_text(encoding="utf-8")
        for interzis in ("secret", "P1", "P2", "Rar sau deloc", "durata", "clicuri"):
            self.assertNotIn(interzis, text)
        with open(dest, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        verde = [r for r in rows if r["masura"] == "sarcina 3: verde pe Dacia"]
        self.assertEqual({r["versiune"] for r in verde}, {"m1", "m2"})
        self.assertEqual(sum(int(r["persoane"]) for r in verde), 8)

    def test_nu_se_publica_sub_trei_persoane(self):
        parcurge(self.c, self.ceas)
        with self.assertRaises(SystemExit):
            s.publica(self.dosar, self.dosar / "public.csv")
        self.assertFalse((self.dosar / "public.csv").exists())

    def test_jurnalul_are_cate_o_linie_valida_pentru_fiecare_pas(self):
        sf = parcurge(self.c, self.ceas)
        linii = (self.dosar / f"{sf['cod']}.jsonl").read_text(encoding="utf-8").splitlines()
        for l in linii:
            json.loads(l)
        self.assertEqual(sum('"tip": "pas"' in l for l in linii), len(s.pasi(("m1", "m2"))) - 1)


HASH_M1 = "f7986e77a3a7dc04a0319fdb4230629a7f129ad7a02a97824d9fa0056e1c0b84"

if __name__ == "__main__":
    unittest.main()
