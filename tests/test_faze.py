"""Programul pietonilor de pe geamănul corectat (§ 6.5) și semaforul real, rejucat din cameră."""
import unittest

import numpy as np

from romana.bridge.live_twin import turning_ratios
from romana.control.faze import MINIM_PIETONI_S, SCURTA, SemaforCuPietoni, etape_plan, fara_treceri, program_fix, segmente_etapa, tranzitie
from romana.control.rejucat import E_V_MAX_S, ETAPA_SCURTA_S, TRANZITII_S, VERDE_MIN_S, acoperire, cicluri, etape_inceput, valuri

TRECERI = {4, 5}
#        vehicule  treceri
N_S = "GGrr" + "Gr"
E_V = "rrGG" + "rG"
PIETONI = "rrrr" + "GG"
STARI = [N_S, E_V, PIETONI]
CONFIG = {"treceri": [4, 5], "intarziere_s": {"0": 24}, "degajare_s": 6, "stare_scurta": "rrrr" + "rr", "nume_scurta": "scurtă"}


class TrafficLight:
    def __init__(self):
        self.stare = None

    def setRedYellowGreenState(self, _id, s):
        self.stare = s

    def getControlledLanes(self, _id):
        return []

    def getControlledLinks(self, _id):
        return []


class Traci:
    def __init__(self):
        self.trafficlight = TrafficLight()


class TestProgram(unittest.TestCase):
    def test_pietonii_pornesc_dupa_vehicule_si_se_opresc_inaintea_lor(self):
        seg = segmente_etapa(N_S, 72, TRECERI, 24, 6)
        self.assertEqual([d for _, d in seg], [24, 42, 6])
        self.assertEqual([s[4] for s, _ in seg], ["r", "G", "r"])
        self.assertTrue(all(s[:4] == N_S[:4] for s, _ in seg))

    def test_o_etapa_scurta_lasa_pietonilor_macar_un_minim(self):
        lung = segmente_etapa(N_S, 110, TRECERI, 24, 6)
        self.assertEqual([d for _, d in lung], [34.0, 70.0, 6])     # la un val lung, pietonii pornesc mai târziu: +0,5 s pe secunda de peste 90 s
        self.assertEqual([d for _, d in segmente_etapa(N_S, 90, TRECERI, 24, 6)], [24, 60, 6])
        self.assertEqual([d for _, d in segmente_etapa(N_S, 110, TRECERI, 0, 6)], [104, 6])     # etapa fără întârziere rămâne cum era
        seg = segmente_etapa(N_S, 20, TRECERI, 24, 6)
        verde = sum(d for s, d in seg if s[4] == "G")
        self.assertEqual(verde, MINIM_PIETONI_S)
        self.assertEqual(sum(d for _, d in seg), 20)

    def test_programul_fix_are_tranzitii_doar_cand_se_schimba_vehicule(self):
        faze = program_fix(STARI, [(0, 72), (1, 48), (SCURTA, 3)], CONFIG)
        self.assertEqual(sum(d for _, d in faze), 72 + 48 + 3 + 15)
        for (a, _), (b, _) in zip(faze, faze[1:] + faze[:1]):      # între două faze nu dispare niciun verde de vehicul fără galben
            for x, y in zip(a[:4], b[:4]):
                self.assertFalse(x == "G" and y == "r", (a, b))

    def test_trecerile_conflictuale_nu_au_verde_cu_vehiculele_lor(self):
        for s, _ in program_fix(STARI, [(0, 72), (1, 48), (SCURTA, 3)], CONFIG):
            self.assertFalse(s[4] == "G" and s[2] == "G")
            self.assertFalse(s[5] == "G" and s[0] == "G")

    def test_a_treia_etapa_e_scurta_doar_sub_verdele_minim(self):
        self.assertEqual(etape_plan([72, 48, 3], CONFIG)[-1], (SCURTA, 3))
        self.assertEqual(etape_plan([36, 28, 12], CONFIG)[-1], (2, 12))
        self.assertEqual(len(etape_plan([60, 40, 0], CONFIG)), 2)


class TestLiniiInterioare(unittest.TestCase):
    CU = {**CONFIG, "linii_interioare": [1]}

    def test_linia_de_dupa_trecere_se_inchide_dupa_celelalte(self):
        g, r = tranzitie(N_S, E_V, self.CU["linii_interioare"])
        self.assertEqual((g[0], g[1]), ("y", "G"))
        self.assertEqual((r[0], r[1]), ("r", "y"))

    def test_nu_ramane_verde_fara_galben(self):
        for s, _ in program_fix(STARI, [(0, 72), (1, 48), (SCURTA, 3)], self.CU):
            pass
        faze = program_fix(STARI, [(0, 72), (1, 48), (SCURTA, 3)], self.CU)
        for (a, _), (b, _) in zip(faze, faze[1:] + faze[:1]):
            for x, y in zip(a[:4], b[:4]):
                self.assertFalse(x == "G" and y == "r", (a, b))

    def test_controlerul_face_la_fel(self):
        tr = Traci()
        c = SemaforCuPietoni(tr, "x", STARI, list("abc"), self.CU)
        for _ in range(31):
            c.tick()
        c.request(1)
        for _ in range(6):
            c.tick()
        self.assertEqual((tr.trafficlight.stare[0], tr.trafficlight.stare[1]), ("y", "G"))
        for _ in range(3):
            c.tick()
        self.assertEqual((tr.trafficlight.stare[0], tr.trafficlight.stare[1]), ("r", "y"))


class TestSemafor(unittest.TestCase):
    def setUp(self):
        self.tr = Traci()
        self.c = SemaforCuPietoni(self.tr, "x", STARI, list("abc"), CONFIG)

    def treci(self, n):
        for _ in range(n):
            self.c.tick()

    def test_pornire_fara_pietoni_apoi_cu_ei(self):
        self.assertEqual(self.tr.trafficlight.stare, fara_treceri(N_S, TRECERI))
        self.treci(24)
        self.assertEqual(self.tr.trafficlight.stare, N_S)

    def test_inaintea_galbenului_pietonii_au_timp_sa_termine(self):
        self.treci(31)
        self.c.request(1)
        self.assertEqual(self.tr.trafficlight.stare, fara_treceri(N_S, TRECERI))     # vehiculele au verde, pietonii nu
        self.assertEqual(self.c.stage, "green")
        self.assertFalse(self.c.can_switch())
        self.treci(5)
        self.assertEqual(self.c.stage, "green")
        self.treci(1)
        self.assertEqual(self.c.stage, "yellow")
        self.assertEqual(self.tr.trafficlight.stare[:2], "yy")
        self.treci(3)
        self.assertEqual(self.c.stage, "red")
        self.treci(2)
        self.assertEqual((self.c.stage, self.c.current), ("green", 1))
        self.assertEqual(self.tr.trafficlight.stare, E_V)

    def test_pietonii_primesc_verdele_lor_si_la_o_cerere_timpurie(self):
        self.treci(12)                 # sub cele 24 s, pietonii n-au primit verde: cererea așteaptă, oricine ar face-o
        self.c.request(1)
        self.assertEqual(self.c.stage, "green")
        self.assertIsNone(self.c.ramas_degajare)
        self.treci(24 + MINIM_PIETONI_S - 12 - 1)
        self.c.request(1)
        self.assertIsNone(self.c.ramas_degajare)
        self.treci(1)
        self.c.request(1)
        self.assertEqual(self.c.ramas_degajare, 6)

    def test_din_e_v_nu_exista_intarziere(self):
        self.treci(31)
        self.c.request(1)
        self.treci(6 + 5)
        self.assertEqual((self.c.current, self.c.stage), (1, "green"))
        self.treci(self.c.min_green)
        self.assertTrue(self.c.can_switch())

    def test_verdele_minim_ramane(self):
        self.treci(5)
        self.c.request(1)
        self.assertEqual(self.c.stage, "green")
        self.assertIsNone(self.c.ramas_degajare)

    def test_din_etapa_scurta_se_poate_cere_faza_de_pietoni(self):
        self.treci(31)
        self.c.request(2, scurta=True)
        self.treci(6 + 5 + 3)
        self.assertTrue(self.c.scurta)
        self.c.request(2)
        self.assertEqual(self.c.stage, "yellow")
        self.treci(5)
        self.assertEqual((self.c.current, self.c.scurta), (2, False))
        self.assertTrue(self.c.pietoni_verde())

    def test_etapa_scurta_nu_are_verde_minim(self):
        self.treci(31)
        self.c.request(2, scurta=True)
        self.treci(6 + 5)
        self.assertEqual((self.c.current, self.c.scurta, self.c.faza_afisata()), (2, True, 3))
        self.assertFalse(self.c.pietoni_verde())
        self.treci(3)
        self.c.request(0)
        self.assertEqual(self.c.stage, "yellow")

    def test_dupa_verdele_maxim_nu_merge_la_o_faza_fara_dozare(self):
        self.c.current = 2
        self.c.green_time = self.c.max_green
        self.c.request(2)
        self.assertEqual(self.c.target, 0)

    def test_pe_doua_etape_scurta_vine_singura(self):
        self.c.via_scurta = True
        self.treci(31)
        self.c.request(1)
        self.treci(6 + 5)
        self.assertEqual(self.c.current, 1)
        self.treci(30)
        self.c.request(0)                  # agentul cere N–S; prima oară vine etapa scurtă
        self.treci(6 + 5)
        self.assertEqual((self.c.current, self.c.scurta), (2, True))
        self.c.request(1)                  # nu se poate întoarce din ea și nu o scurtează
        self.assertEqual(self.c.stage, "green")
        self.treci(3)
        self.assertEqual(self.c.stage, "yellow")
        self.treci(5)
        self.assertEqual((self.c.current, self.c.scurta), (0, False))

    def test_lista_de_faze_ramane_aceeasi_pentru_agent(self):
        self.assertEqual(self.c.n, 3)


class TestRejucat(unittest.TestCase):
    def test_valuri(self):
        m = np.r_[np.arange(0, 20.0, 2), 100 + np.arange(0, 30.0, 3), 200.0, 201.0]
        self.assertEqual([(a, b, n) for a, b, n in valuri(m)], [(0.0, 18.0, 10), (100.0, 127.0, 10)])

    def test_ciclurile_urmeaza_valurile_si_umplu_golurile(self):
        val = [(0.0, 70.0, 80), (140.0, 215.0, 80), (280.0, 350.0, 80), (700.0, 770.0, 80)]
        c = cicluri(val, 900, 140.0, 72.0)
        self.assertEqual(c[0], (70.0, 140.0))
        self.assertEqual(c[1], (75.0, 140.0))
        self.assertGreaterEqual(sum(d for _, d in c), 900)
        for g, d in c:                 # orice ciclu încape: verde N–S, tranziții, etapa scurtă și verdele minim pe E–V
            self.assertGreaterEqual(d - g - TRANZITII_S - ETAPA_SCURTA_S, VERDE_MIN_S)

    def test_la_trafic_slab_verdele_nu_se_termina_odata_cu_valul(self):
        val = [(0.0, 26.0, 9), (130.0, 150.0, 9), (260.0, 290.0, 9)]
        g, d = cicluri(val, 130, 130.0, 40.0)[0]
        self.assertEqual(d, 130.0)
        self.assertEqual(g, 130.0 - TRANZITII_S - ETAPA_SCURTA_S - 60)

    def test_doua_valuri_lipite_urmate_de_o_pauza_nu_dau_un_ciclu_imens(self):
        val = [(0.0, 15.4, 19), (40.2, 53.1, 8), (781.1, 850.0, 50)]
        c = cicluri(val, 900, 120.5, 25.0)
        self.assertLessEqual(max(d for _, d in c), 1.6 * 120.5)
        self.assertLessEqual(max(g for g, _ in c), 110)
        self.assertGreaterEqual(sum(d for _, d in c), 900)

    def test_inceputul_merge_pana_la_primul_val(self):
        for prima in (0.0, 10.0, 40.0, 130.7, 274.4, 500.0):
            etape, rest = etape_inceput(prima, 120.0, 40.0)
            total = sum(v for _, v in etape)
            # fiecare etapă e urmată de o tranziție de 5 s, afară de cea scurtă dintre două tranziții, care are și ea una
            total += 5 * len(etape)
            self.assertAlmostEqual(total + rest, prima, places=6, msg=str(prima))
            self.assertLessEqual(max([v for f, v in etape if f == 1] or [0]), E_V_MAX_S + 30)

    def test_acoperirea_numara_doar_ciclurile_date_de_valuri(self):
        val = [(0.0, 70.0, 80), (140.0, 215.0, 80), (280.0, 350.0, 80)]
        c = [(70.0, 140.0), (75.0, 140.0), (72.0, 140.0)]
        self.assertAlmostEqual(acoperire(val, c, sfarsit=420.0), 280 / 420)
        self.assertEqual(acoperire([], c), 0.0)

    def test_un_val_prea_apropiat_se_lipeste_de_cel_dinainte(self):
        val = [(0.0, 60.0, 80), (70.0, 90.0, 20), (150.0, 220.0, 80)]
        c = cicluri(val, 200, 150.0, 72.0)
        self.assertEqual(c[0], (90.0, 150.0))


class TestCerereTimpReal(unittest.TestCase):
    CFG = {"pondere_prior": 2.0, "prior_destinatii": {"magheru": {"catargiu": 3, "dacia_est": 1}, "catargiu": {"magheru": 1}},
           "cote_fixe": {"catargiu": {"dacia_vest": 0.2}}, "cote_timp_real": {"magheru": {"dacia_est": 0.14}}}

    def test_cotele_declarate_inlocuiesc_proportiile(self):
        r = turning_ratios(self.CFG, {"magheru>dacia_est": 500, "magheru>catargiu": 500})
        self.assertAlmostEqual(r["magheru"]["dacia_est"], 0.14)
        self.assertAlmostEqual(r["magheru"]["catargiu"], 0.86)
        self.assertAlmostEqual(r["catargiu"]["dacia_vest"], 0.2)
        self.assertAlmostEqual(sum(r["catargiu"].values()), 1.0)

    def test_fara_cote_ramane_ca_inainte(self):
        r = turning_ratios({"pondere_prior": 2.0, "prior_destinatii": {"magheru": {"catargiu": 1}}}, {})
        self.assertEqual(r, {"magheru": {"catargiu": 1.0}})


if __name__ == "__main__":
    unittest.main()
