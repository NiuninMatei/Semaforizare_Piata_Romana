"""Funcțiile validării geamănului (§ 6.5), fără simulare: vârful pe 20 s, modelul nul eșantionat, verdictul cu interval, decalajul de aliniere, regresia, atingerile, tăierea urmei, ceasul observatorului, citirea pe zone."""
import hashlib
import os
import tempfile
import types
import unittest
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from romana.control import valideaza_geaman as V
from romana.control.valideaza_geaman import (BINI, abatere_profil, acoperire_virtuala, alege_citiri, asteptare_evitata, atinge_pieton, avertisment_factori, cai_git, cicluri_din, citiri_din_virtuala, decalaj_aliniere, decalaje_fara_cate_unul,
                                             deosebeste, deosebeste_profil, eroare_proiectie_s, esantion_ferestre, ferestre_in, forma, interval_seeduri, intervale_etape, matrice_ferestre, matrice_valuri, momente_traiectorie,
                                             nul_esantionat, pe_axa_si_inel, per_etapa, perechi_suprapuse, pierdere_pe_ramuri, prag_din_zgomot, profil, regresie, rulari_cu_probleme, seed_exceptie, taie_dupa_iesire, tipuri_rapide,
                                             urma_in_imagine, valuri_in_fereastra, varf_pe_cicluri, verdict_interval, verifica_cererea, verifica_valuri, zgomot_decalaj, zgomot_reesantionare, zgomot_seeduri, zgomot_seeduri_scalar,
                                             zgomot_statistica, zone_pe_brate)
from romana.vision.od_counter import Params, Zone


def valuri_sintetice(rng, n_valuri=30, ciclu=130.0, pe_val=40, durata=60.0):
    """Valuri de vehicule cu debit constant, la început de ciclu."""
    s = 300.0 + ciclu * np.arange(n_valuri)
    return s, np.sort(np.concatenate([x + rng.uniform(0, durata, pe_val) for x in s]))


class TestVarf(unittest.TestCase):
    def test_vede_grupul_cel_mai_dens_din_fiecare_ciclu(self):
        grup = np.arange(10, 20)                     # 10 vehicule în 10 s, deci 10 pe fereastra de 20 s
        rar = np.array([50.0, 90.0])
        al_doilea = 100 + np.array([0.0, 30.0])      # două vehicule la 30 s: câte unul pe fereastră
        v = varf_pe_cicluri(np.r_[grup, rar, al_doilea], np.array([0.0, 100.0, 200.0, 300.0]))
        self.assertEqual(v.tolist(), [10 / 20, 1 / 20, 0.0])

    def test_fereastra_nu_trece_peste_marginea_ciclului(self):
        v = varf_pe_cicluri(np.array([95.0, 96.0, 104.0, 105.0]), np.array([0.0, 100.0, 200.0]))
        self.assertEqual(v.tolist(), [2 / 20, 2 / 20])

    def test_aceeasi_metoda_nu_depinde_de_ordinea_momentelor(self):
        m = np.array([3.0, 1.0, 2.0, 40.0])
        self.assertEqual(varf_pe_cicluri(m, np.array([0.0, 100.0])).tolist(), [3 / 20])

    def test_marginile_ciclurilor_au_capatul_la_lungimea_obisnuita(self):
        self.assertEqual(cicluri_din(np.array([0.0, 100.0, 220.0])).tolist(), [0.0, 100.0, 220.0, 330.0])


class TestNul(unittest.TestCase):
    def test_esantionul_sta_in_ferestre_cu_debit_constant(self):
        rng = np.random.default_rng(1)
        f = np.array([[0.0, 10.0], [100.0, 130.0]])
        m = esantion_ferestre(f, 40000, rng)
        self.assertEqual(len(m), 40000)
        self.assertTrue(np.all(((m >= 0) & (m < 10)) | ((m >= 100) & (m < 130))))
        self.assertAlmostEqual(float((m < 50).mean()), 0.25, delta=0.01)    # 10 s din 40 s

    def test_acelasi_numar_de_vehicule_si_reproductibil(self):
        s = np.array([0.0, 200.0])
        f = np.array([[0.0, 60.0], [200.0, 260.0]])
        pc = profil(esantion_ferestre(f, 200, np.random.default_rng(1)), s)
        a = nul_esantionat(pc, f, 200, s, np.random.default_rng(2), repetari=20)
        b = nul_esantionat(pc, f, 200, s, np.random.default_rng(2), repetari=20)
        self.assertTrue(np.array_equal(a, b))
        m = esantion_ferestre(f, 200, np.random.default_rng(3))
        self.assertAlmostEqual(float(profil(m, s).sum() * len(s)), 200.0)

    def test_camera_in_afara_ferestrei_il_face_sa_rateze_tot(self):
        s = np.array([0.0, 200.0])
        pc = profil(np.array([100.0, 105.0, 300.0, 305.0]), s)       # toate în secundele 100–110
        ab = nul_esantionat(pc, np.array([[0.0, 60.0], [200.0, 260.0]]), 4, s, np.random.default_rng(1), repetari=20)
        self.assertTrue(np.allclose(ab, 2.0))

    def test_camera_care_chiar_e_uniforma_are_nul_mic(self):
        rng = np.random.default_rng(4)
        s = 200.0 * np.arange(30)
        f = np.c_[s, s + 60]
        pc = profil(esantion_ferestre(f, 3000, rng), s)
        self.assertLess(float(np.median(nul_esantionat(pc, f, 3000, s, rng, repetari=30))), 0.15)

    def test_media_mai_multor_realizari_are_mai_putin_zgomot(self):
        rng = np.random.default_rng(5)
        s = 200.0 * np.arange(20)
        f = np.c_[s, s + 60]
        pc = forma(np.r_[np.full(6, 1 / 6), np.zeros(BINI - 6)])
        o = np.median(nul_esantionat(pc, f, 300, s, rng, repetari=30, normat=True))
        cinci = np.median(nul_esantionat(pc, f, 300, s, rng, repetari=30, realizari=5, normat=True))
        self.assertLess(cinci, o)

    def test_pe_iesire_cota_imparte_vehiculele_intre_etape(self):
        s = np.array([0.0, 200.0])
        ns, ev = np.array([[0.0, 50.0], [200.0, 250.0]]), np.array([[60.0, 110.0], [260.0, 310.0]])
        pc = forma(np.array([1.0] * 5 + [0.0] * (BINI - 5)))        # numai în secundele 0–50
        toate_ns = nul_esantionat(pc, ns, 400, s, np.random.default_rng(1), repetari=10, normat=True, alte_ferestre=ev, cota=1.0)
        doar_ev = nul_esantionat(pc, ns, 400, s, np.random.default_rng(1), repetari=10, normat=True, alte_ferestre=ev, cota=0.0)
        self.assertLess(float(toate_ns.max()), 0.4)
        self.assertAlmostEqual(float(doar_ev.min()), 2.0, delta=1e-6)


class TestVerdict(unittest.TestCase):
    def test_in_prag_peste_prag_nedecis(self):
        self.assertEqual(verdict_interval([0.02, 0.05], 0.10), "în prag")
        self.assertEqual(verdict_interval([0.15, 0.20], 0.10), "peste prag")
        self.assertEqual(verdict_interval([0.05, 0.15], 0.10), "nedecis")

    def test_abaterile_conteaza_in_valoare_absoluta(self):
        self.assertEqual(verdict_interval([-0.05, 0.05], 0.10), "în prag")
        self.assertEqual(verdict_interval([-0.20, -0.15], 0.10), "peste prag")
        self.assertEqual(verdict_interval([-0.15, 0.05], 0.10), "nedecis")

    def test_un_singur_seed_nu_poate_fi_nedecis(self):
        self.assertEqual(verdict_interval([0.11], 0.10), "peste prag")

    def test_fara_prag_sau_fara_valori_nu_exista_verdict(self):
        self.assertEqual(verdict_interval([0.1], float("nan")), "–")
        self.assertEqual(verdict_interval([float("nan")], 0.1), "–")
        self.assertEqual(verdict_interval([0.05, float("nan")], 0.1), "în prag")

    def test_pragul_aduna_zgomotele_in_cuadratura_si_sare_ce_lipseste(self):
        self.assertAlmostEqual(prag_din_zgomot(0.3, 0.4), 0.5)
        self.assertAlmostEqual(prag_din_zgomot(0.3, float("nan")), 0.3)
        self.assertTrue(np.isnan(prag_din_zgomot(float("nan"))))


class TestIntervalSeeduri(unittest.TestCase):
    def test_de_la_cinci_seeduri_e_p10_p90_sub_atat_min_max(self):
        self.assertEqual(interval_seeduri([1.0, 2.0, 9.0]), (1.0, 9.0))
        self.assertEqual(interval_seeduri([1.0, 2.0, 3.0, 9.0]), (1.0, 9.0))
        lo, hi = interval_seeduri([0.0, 1.0, 2.0, 3.0, 100.0])
        self.assertAlmostEqual(lo, 0.4)
        self.assertAlmostEqual(hi, 3 + 0.6 * 97)
        self.assertTrue(np.isnan(interval_seeduri([])[0]))
        self.assertEqual(interval_seeduri([float("nan"), 2.0]), (2.0, 2.0))

    def test_o_singura_rulare_blocata_nu_face_verdictul(self):
        """Pe 26.10 vârf, debitul Magheru era „nedecis” doar din cauza seed-ului 2 (−0,121 față de −0,020…−0,005)."""
        T = V.Tabel(None, None, [1, 2, 3, 4, 5])
        T.rand("A", "debit", "debit", [990.0, 880.0, 985.0, 995.0, 980.0], 1000.0, mod="relativ", prag=(0.10, "scris", "debit"))
        r = T.randuri[0]
        self.assertEqual(r["verdict"], "în prag")
        self.assertIn("cu toate seed-urile ar fi „nedecis”", r["nota"])
        self.assertIn("seed 2 iese din rând", r["nota"])
        self.assertEqual((r["g_min"], r["g_max"]), (880.0, 995.0))        # coloana „pe seed-uri” îl arată în continuare
        self.assertGreater(r["ab_lo"], -0.12)

    def test_sub_cinci_seeduri_verdictul_e_tot_pe_min_max(self):
        T = V.Tabel(None, None)
        T.rand("A", "debit", "debit", [990.0, 880.0], 1000.0, mod="relativ", prag=(0.10, "scris", "debit"))
        self.assertEqual(T.randuri[0]["verdict"], "nedecis")
        self.assertNotIn("iese din rând", T.randuri[0]["nota"])

    def test_mediana_sta_langa_medie(self):
        T = V.Tabel(None, None)
        T.rand("D", "pierdere", "pierdere", [354.7, 463.7, 362.7, 359.7, 357.7])
        self.assertAlmostEqual(T.randuri[0]["geaman"], 379.7)
        self.assertAlmostEqual(T.randuri[0]["g_mediana"], 359.7)
        self.assertIn("seed 2 iese din rând", T.randuri[0]["nota"])

    def test_seedul_exceptie(self):
        self.assertEqual(seed_exceptie([354.7, 463.7, 362.7, 359.7, 357.7]), 1)
        self.assertEqual(seed_exceptie([float("nan"), 463.7, 362.7, 359.7, 357.7]), 1)
        self.assertIsNone(seed_exceptie([354.7, 363.7, 362.7, 359.7, 357.7]))
        self.assertIsNone(seed_exceptie([100.0, 463.7, 300.0]))                  # sub 4 seed-uri nu se poate spune
        self.assertIsNone(seed_exceptie([2.0, 2.0, 1.8, 2.0, 2.0]))              # în trepte de 0,2 s, cu restul identice: nu spune nimic
        self.assertIsNone(seed_exceptie([100.0, 106.0, 101.0, 100.5, 100.2], 0.20))

    def test_rularile_cu_teleportari_sau_cu_blocaj_presupus(self):
        def rulare(tele, total, magheru, pietoni=36.0):
            return {"r": {"teleportari": tele, "pierdere_totala_h": total}, "pierderi": {"magheru": magheru, "pietoni_extrapolati": pietoni}}
        rez = [rulare(0, 354.7, 73.3), rulare(2, 463.7, 159.4), rulare(0, 362.7, 82.1), rulare(1, 359.7, 79.6), rulare(0, 357.7, 75.0, 38.9)]
        p = rulari_cu_probleme(rez)
        self.assertEqual(list(p), [1, 3])                                        # pietonii nu fac un blocaj de vehicule
        self.assertIn("2 teleportări", p[1])
        self.assertIn("pierdere totală 464 h", p[1])
        self.assertIn("pe ramura magheru 159 h", p[1])
        self.assertEqual(p[3], "1 teleportare")
        self.assertEqual(rulari_cu_probleme(rez[:2]), {1: "2 teleportări"})      # sub 4 seed-uri rămân doar teleportările
        # o rulare mult mai bună decât celelalte nu e un blocaj
        self.assertEqual(rulari_cu_probleme([rulare(0, 100.0, 50.0), rulare(0, 300.0, 80.0), rulare(0, 305.0, 81.0), rulare(0, 310.0, 82.0)]), {})


class TestZgomot(unittest.TestCase):
    def test_valuri_identice_nu_au_zgomot_de_reesantionare(self):
        s = 200.0 * np.arange(10)
        m = np.concatenate([x + np.array([5.0, 25.0]) for x in s])
        self.assertEqual(zgomot_reesantionare(matrice_valuri(m, s), np.random.default_rng(1)), 0.0)
        self.assertEqual(zgomot_reesantionare(matrice_valuri(m, s), np.random.default_rng(1), normat=True), 0.0)

    def test_matricea_valurilor_are_ca_medie_profilul(self):
        rng = np.random.default_rng(2)
        s, m = valuri_sintetice(rng, 8)
        self.assertTrue(np.allclose(matrice_valuri(m, s).mean(0), profil(m, s)))

    def test_valurile_inegale_au_zgomot_mai_mare_decat_cele_egale(self):
        rng = np.random.default_rng(3)
        s = 200.0 * np.arange(40)
        egale = np.concatenate([x + rng.uniform(0, 60, 40) for x in s])
        inegale = np.concatenate([x + rng.uniform(0, 60, 4) for x in s])
        self.assertLess(zgomot_reesantionare(matrice_valuri(egale, s), rng), zgomot_reesantionare(matrice_valuri(inegale, s), rng))

    def test_seedurile_identice_nu_au_zgomot(self):
        p = np.array([1.0, 2.0, 3.0])
        self.assertEqual(zgomot_seeduri([p, p, p]), 0.0)
        self.assertTrue(np.isnan(zgomot_seeduri([p])))
        self.assertEqual(zgomot_seeduri_scalar([2.0, 2.0]), 0.0)
        self.assertEqual(zgomot_seeduri_scalar([1.0, 3.0]), 2.0)
        self.assertTrue(np.isnan(zgomot_seeduri_scalar([1.0])))

    def test_o_rulare_blocata_nu_largeste_singura_pragul(self):
        v = [100.0, 101.0, 99.0, 100.5, 160.0]
        toate = [abs(v[i] - np.delete(v, i).mean()) for i in range(5)]
        self.assertLess(zgomot_seeduri_scalar(v), max(toate))
        self.assertAlmostEqual(zgomot_seeduri_scalar(v), float(np.percentile(toate, 90)))
        self.assertEqual(zgomot_seeduri_scalar(v[:4]), max(abs(np.array(v[:4])[i] - np.delete(v[:4], i).mean()) for i in range(4)))

    def test_zgomotul_unei_statistici(self):
        v = np.r_[np.full(50, 10.0)]
        self.assertEqual(zgomot_statistica(v, np.median, np.random.default_rng(1)), 0.0)
        z = zgomot_statistica(np.random.default_rng(2).normal(100, 10, 200), np.mean, np.random.default_rng(3))
        self.assertGreater(z, 0.005)         # eroarea mediei: 0,7%, deci la p95 ≈1,4%
        self.assertLess(z, 0.03)


class TestDecalaj(unittest.TestCase):
    def test_gaseste_decalajul_mutat_dinadins(self):
        rng = np.random.default_rng(1)
        s, m = valuri_sintetice(rng)
        fereastra = lambda x: x[(x >= 300) & (x < 3600)]         # noqa: E731
        pc = profil(fereastra(m), s)
        for d in (-8, 5, 0):
            dl, l_dl, l_0 = decalaj_aliniere(pc, [(m - d, s)])     # geamănul vine cu d secunde mai devreme decât camera, deci trebuie mutat cu +d
            self.assertEqual(dl, d)
            self.assertLessEqual(l_dl, l_0)
            self.assertAlmostEqual(l_dl, 0.0, delta=0.02)

    def test_semnul_negativ_inseamna_camera_mai_devreme(self):
        rng = np.random.default_rng(2)
        s, m = valuri_sintetice(rng)
        dl, _, _ = decalaj_aliniere(profil(m, s), [(m + 8, s)])
        self.assertEqual(dl, -8)

    def test_aceeasi_serie_nu_are_decalaj(self):
        rng = np.random.default_rng(3)
        s, m = valuri_sintetice(rng)
        self.assertEqual(decalaj_aliniere(profil(m, s), [(m, s)])[0], 0)

    def test_profilul_e_al_mediei_seedurilor_si_merge_pe_forme(self):
        rng = np.random.default_rng(4)
        s, m = valuri_sintetice(rng)
        a, b = m[::2], m[1::2]
        self.assertEqual(decalaj_aliniere(forma(profil(m, s)), [(a + 6, s), (b + 6, s)], normat=True)[0], -6)

    def test_zgomotul_decalajului_e_mic_la_multe_valuri_si_mare_la_putine(self):
        rng = np.random.default_rng(5)
        s, m = valuri_sintetice(rng, n_valuri=25, pe_val=40)
        mult = zgomot_decalaj(m, s, np.random.default_rng(6))
        s2, m2 = valuri_sintetice(rng, n_valuri=25, pe_val=4)
        putin = zgomot_decalaj(m2, s2, np.random.default_rng(7))
        self.assertLessEqual(mult, putin)
        self.assertLessEqual(mult, 5.0)

    @staticmethod
    def seeduri_cu_doua_minime(rng):
        """Camera are două vârfuri, la 30 s unul de altul; geamănul le are cu 15 s mai devreme, dar pe fiecare seed unul e mult mai mare. Pe un seed singur, curba are două minime, deci alinierea sare; pe medie, stă pe loc."""
        s = 300.0 + 130.0 * np.arange(25)
        cu = lambda a, p, q: np.sort(np.concatenate([x + np.r_[rng.normal(a, 1.5, p), rng.normal(a + 30, 1.5, q)] for x in s]))     # noqa: E731
        return forma(profil(cu(50, 30, 20), s)), [(cu(35, p, q), s) for p, q in ((45, 5), (5, 45), (45, 5), (5, 45), (45, 5))]

    def test_fara_cate_unul_e_alinierea_mediei_nu_a_seedului_singur(self):
        pc, seeduri = self.seeduri_cu_doua_minime(np.random.default_rng(8))
        self.assertEqual(decalaje_fara_cate_unul(pc, seeduri[:1], True), [])
        a, b = seeduri[0], seeduri[1]
        self.assertEqual(decalaje_fara_cate_unul(pc, [a, b], True), [decalaj_aliniere(pc, [b], True)[0], decalaj_aliniere(pc, [a], True)[0]])       # la 2 seed-uri, fără unul rămâne celălalt
        singure = [decalaj_aliniere(pc, [u], True)[0] for u in seeduri]
        fara = decalaje_fara_cate_unul(pc, seeduri, True)
        self.assertGreater(max(singure) - min(singure), 20)         # seed-urile singure sar între cele două minime
        self.assertLessEqual(max(fara) - min(fara), 3)              # media fără câte unul, nu
        self.assertAlmostEqual(np.median(fara), 15, delta=2)


class TestRegresie(unittest.TestCase):
    def test_o_dreapta_exacta(self):
        x = np.arange(30.0, 90.0, 3.0)
        r = regresie(x, 1.3 * x + 4.0)
        self.assertAlmostEqual(r["panta"], 1.3)
        self.assertAlmostEqual(r["intercept"], 4.0)
        self.assertAlmostEqual(r["rest"], 0.0, places=6)
        self.assertAlmostEqual(r["eroare_panta"], 0.0, places=6)

    def test_restul_e_abaterea_zgomotului(self):
        rng = np.random.default_rng(1)
        x = rng.uniform(30, 100, 2000)
        r = regresie(x, 1.3 * x + 4.0 + rng.normal(0, 5, 2000))
        self.assertAlmostEqual(r["panta"], 1.3, delta=0.02)
        self.assertAlmostEqual(r["intercept"], 4.0, delta=1.5)
        self.assertAlmostEqual(r["rest"], 5.0, delta=0.3)

    def test_fara_variatie_nu_exista_panta(self):
        self.assertTrue(np.isnan(regresie([1.0, 1.0, 1.0, 1.0], [1.0, 2.0, 3.0, 4.0])["panta"]))
        self.assertTrue(np.isnan(regresie([1.0, 2.0], [1.0, 2.0])["panta"]))

    def test_pe_etapa_numara_doar_fereastra_ceruta(self):
        f = np.array([[0.0, 80.0], [100.0, 180.0]])
        self.assertEqual(per_etapa(np.array([5.0, 30.0, 59.0, 60.0, 130.0]), f, 24, 60).tolist(), [2.0, 1.0])

    def test_pe_etapa_nu_trece_de_sfarsitul_ei(self):
        self.assertEqual(per_etapa(np.array([30.0, 44.0, 45.0, 50.0]), np.array([[0.0, 45.0]]), 24, 60).tolist(), [2.0])
        self.assertEqual(per_etapa(np.array([1.0]), np.empty((0, 2)), 24, 60).tolist(), [])


class TestValuri(unittest.TestCase):
    MOMENTE = np.r_[np.arange(267.0, 360.0, 2.0), np.arange(431.0, 500.0, 2.0), np.arange(3590.0, 3640.0, 2.0)]

    def test_primul_val_nu_incepe_la_marginea_ferestrei(self):
        """Pe 26.10 vârf: etapa N–S e 267,4–359,6 s; tăiate la 300 s, momentele dădeau un val care începe la 300,5 s."""
        tiat = self.MOMENTE[self.MOMENTE >= 300]
        self.assertEqual(V.valuri(tiat)[0][0], 301.0)               # așa era: început fals
        v = valuri_in_fereastra(self.MOMENTE)
        self.assertEqual(v[0][0], 431.0)                            # valul de la 267 s începe în afara ferestrei, deci nu mai e printre începuturi
        self.assertEqual(v[-1][0], 3590.0)

    def test_la_fel_si_daca_momentele_nu_sunt_in_ordine(self):
        self.assertEqual(valuri_in_fereastra(self.MOMENTE[::-1]), valuri_in_fereastra(self.MOMENTE))

    def test_valurile_pe_etape(self):
        sc, ns = np.array([300.0, 450.0, 600.0]), np.array([[300.2, 370.0], [450.4, 520.0], [600.0, 680.0]])
        self.assertEqual(verifica_valuri(sc, ns), [])

    def test_un_val_care_nu_incepe_la_o_etapa_se_semnaleaza(self):
        sc, ns = np.array([300.0, 450.0, 600.0]), np.array([[300.0, 520.0], [600.0, 680.0]])       # programul l-a lipit pe al doilea de primul
        a = verifica_valuri(sc, ns)
        self.assertEqual(len(a), 1)
        self.assertIn("1 din 3 valuri", a[0])

    def test_momentele_programului_trebuie_sa_fie_ale_rezumatului(self):
        sc, ns = np.array([300.0]), np.array([[300.0, 370.0]])
        m = np.array([300.0, 301.0, 302.0])
        self.assertEqual(verifica_valuri(sc, ns, m, m[::-1]), [])
        self.assertIn("ev_<zi>.npz", verifica_valuri(sc, ns, m, m[:2])[0])
        self.assertIn("ev_<zi>.npz", verifica_valuri(sc, ns, m, m + 5)[0])


class TestFactori(unittest.TestCase):
    OD = {"od_vehicule": {"magheru>catargiu": 2000, "magheru>dacia_est": 692, "catargiu>magheru": 100, "dacia_est>catargiu": 3}}

    def test_cererea_care_se_potriveste_nu_avertizeaza(self):
        self.assertEqual(verifica_cererea(self.OD, {"magheru": 2243, "catargiu": 90, "dacia_est": 3}, {"magheru": 1.2, "catargiu": 1.11, "dacia_est": 1.0}), [])

    def test_alti_factori_decat_cei_din_rute_se_vad_in_cerere(self):
        a = verifica_cererea(self.OD, {"magheru": 2243, "catargiu": 90, "dacia_est": 3}, {"magheru": 1.05, "catargiu": 1.11, "dacia_est": 1.0})
        self.assertEqual(len(a), 1)
        self.assertIn("pe magheru", a[0])

    def test_la_trafic_slab_rotunjirile_nu_conteaza(self):
        self.assertEqual(verifica_cererea({"od_vehicule": {"dacia_vest>catargiu": 24}}, {"dacia_vest": 20}, {"dacia_vest": 1.24}), [])

    def test_fisierul_de_factori_mai_nou_decat_rutele(self):
        with tempfile.TemporaryDirectory() as d:
            c, r1, r2 = Path(d) / "demand_v2.json", Path(d) / "a.rou.xml", Path(d) / "b.rou.xml"
            for p in (c, r1, r2):
                p.write_text("x", encoding="utf-8")
            os.utime(r1, (1000, 1000))
            os.utime(r2, (2000, 2000))
            os.utime(c, (500, 500))
            self.assertIsNone(avertisment_factori(c, [r1, r2]))
            os.utime(c, (1500, 1500))               # nou față de una dintre rute: e destul
            self.assertIn("mai nou decât rutele", avertisment_factori(c, [r1, r2]))
            self.assertIsNone(avertisment_factori(c, []))

    def test_avertismentele_unui_scenariu_fara_simulare(self):
        cam, _ = sintetic()
        cam["intrari_ora"] = {"magheru": 18000, "catargiu": 9000, "dacia_est": 1, "dacia_vest": 0}
        vechi = V.evenimente_zi
        V.evenimente_zi = lambda zi: {"magheru": cam["intrari"]["magheru"]}
        try:
            self.assertEqual(V.avertismente_scenariu("cor_zi_care_nu_exista", cam), [])
            alti = dict(cam, f=dict(cam["f"], magheru=1.2))
            self.assertTrue(any("pe magheru" in x for x in V.avertismente_scenariu("cor_zi_care_nu_exista", alti)))
            V.evenimente_zi = lambda zi: {"magheru": cam["intrari"]["magheru"][:-1]}       # programul e făcut din alte momente
            self.assertTrue(any("ev_<zi>.npz" in x for x in V.avertismente_scenariu("cor_zi_care_nu_exista", cam)))
        finally:
            V.evenimente_zi = vechi

    def test_starea_git_acopera_tot_ce_hotaraste_tabelul(self):
        c = cai_git(["cor_zi_2026-10-26_varf", "cor_zi_2026-10-26_seara"])
        for x in ("src/romana", "config/demand_v2.json", "sumo/net", "sumo/demand/vtypes_v2.add.xml", "sumo/scenarios/cor_zi_2026-10-26_varf.sumocfg", "sumo/demand/cor_zi_2026-10-26_seara",
                  "data/counts_cor/numaratori_2026-10-26.csv", "data/trajectories/traiectorii_2026-10-26.jsonl.gz"):
            self.assertIn(x, c)
        self.assertEqual(len(c), len(set(c)))
        self.assertIn("src/romana", cai_git([]))


class TestEtape(unittest.TestCase):
    VERZI = ["GGrr", "rrGG"]

    def test_intervalele_din_lista_de_faze(self):
        faze = [("GGrr" + "r", 24), ("GGrr" + "G", 42), ("yyrr" + "r", 3), ("rrrr" + "r", 2), ("rrGG" + "r", 48), ("rryy" + "r", 3), ("rrrr" + "r", 2)]
        ns, ev = intervale_etape(faze, self.VERZI, 4)
        self.assertEqual(ns.tolist(), [[0, 66]])              # fereastra pietonilor nu rupe etapa
        self.assertEqual(ev.tolist(), [[71, 119]])

    def test_ferestrele_taiate_si_cele_intregi(self):
        f = np.array([[250.0, 350.0], [400.0, 500.0], [3550.0, 3650.0]])
        self.assertEqual(ferestre_in(f, 300, 3600).tolist(), [[300, 350], [400, 500], [3550, 3600]])
        self.assertEqual(ferestre_in(f, 300, 3600, intregi=True).tolist(), [[400, 500]])

    def test_matricea_ferestrelor_masoara_de_la_inceputul_etapei(self):
        m = matrice_ferestre(np.array([105.0, 115.0, 215.0, 150.0]), np.array([[100.0, 130.0], [210.0, 240.0]]))
        self.assertEqual(m[0, :3].tolist(), [1.0, 1.0, 0.0])
        self.assertEqual(m[1, :2].tolist(), [1.0, 0.0])
        self.assertEqual(m.sum(), 3.0)


class TestAtingeri(unittest.TestCase):
    def test_doua_vehicule_suprapuse_cu_adancimea_corecta(self):
        p = perechi_suprapuse(np.array([0.0, 0.0, 10.0]), np.array([0.0, -4.0, 0.0]), np.zeros(3), np.full(3, 4.6), np.full(3, 1.8))
        self.assertEqual([(i, j) for i, j, _ in p], [(0, 1)])
        self.assertAlmostEqual(p[0][2], 0.6, places=6)

    def test_vehicule_care_doar_se_apropie_nu_se_ating(self):
        self.assertEqual(perechi_suprapuse(np.array([0.0, 0.0]), np.array([0.0, -5.0]), np.zeros(2), np.full(2, 4.6), np.full(2, 1.8)), [])
        self.assertEqual(perechi_suprapuse(np.array([0.0, 2.0]), np.array([0.0, 0.0]), np.zeros(2), np.full(2, 4.6), np.full(2, 1.8)), [])

    def test_vehicule_perpendiculare(self):
        p = perechi_suprapuse(np.array([0.0, 2.0]), np.array([-2.0, -2.0]), np.array([0.0, 90.0]), np.full(2, 4.6), np.full(2, 1.8))
        self.assertEqual(len(p), 1)            # al doilea merge spre est, cu botul la x = 2, deci îl prinde pe primul de-a latul

    def test_pietonul_pe_marginea_vehiculului(self):
        px, py = np.array([0.0, 0.0, 0.0, 1.0, 2.0]), np.array([-2.0, 1.0, -4.7, -2.0, -2.0])
        m = atinge_pieton(px, py, np.array([0.0]), np.array([0.0]), np.array([0.0]), np.array([4.6]), np.array([1.8]))
        self.assertEqual(m[:, 0].tolist(), [True, False, True, True, False])    # sub vehicul; în față; în spate, în margine; lateral, în margine; lateral, departe

    def test_axa_si_inelul_se_recunosc_pe_benzi(self):
        self.assertTrue(pe_axa_si_inel({"241212606_1"}, {"448266588#0_0"}))
        self.assertTrue(pe_axa_si_inel({":33389729_3_1"}, {":2404247023_2_0"}))
        self.assertFalse(pe_axa_si_inel({"241212606_1"}, {"241212606_0"}))

    def test_asteptarea_evitata_e_pana_la_urmatorul_verde_al_trecerii(self):
        stari = [(0, "rG"), (50, "GG"), (100, "rr"), (150, "rG")]
        self.assertEqual(asteptare_evitata([(10, 0), (120, 1), (120, 0)], stari), 40.0 + 30.0)     # (120, 0): nu mai urmează niciun verde


class TestZone(unittest.TestCase):
    INTRARE = Zone("a_in", "a", "intrare", np.array([[0.0, 0.5], [0.2, 0.5], [0.2, 0.7], [0.0, 0.7]]))
    IESIRE = Zone("b_out", "b", "iesire", np.array([[0.6, 0.5], [0.8, 0.5], [0.8, 0.7], [0.6, 0.7]]), capat=True)
    ZONE = [INTRARE, IESIRE]

    def urma(self, x_final=0.99):
        return [(float(t), float(x), 0.6) for t, x in zip(np.arange(0, 100) * 0.2, np.linspace(0.01, x_final, 100))]

    def test_fara_taiere_regula_capatului_respinge_vehiculul_care_merge_mai_departe(self):
        intrari, iesiri = zone_pe_brate(self.ZONE)
        self.assertEqual(momente_traiectorie("passenger", self.urma(), self.ZONE, intrari, iesiri, Params())[:2], ("a", None))

    def test_dupa_taiere_acelasi_cod_ii_da_mersul_si_momentele(self):
        intrari, iesiri = zone_pe_brate(self.ZONE)
        u = taie_dupa_iesire(self.urma(), [self.IESIRE])
        self.assertTrue(self.IESIRE.contains_norm(u[-1][1], u[-1][2]))
        self.assertFalse(any(x > 0.8 for _, x, _ in u))
        o, d, t_o, t_d = momente_traiectorie("passenger", u, self.ZONE, intrari, iesiri, Params())
        self.assertEqual((o, d), ("a", "b"))
        self.assertEqual(t_o, 0.0)
        self.assertAlmostEqual(t_d, next(t for t, x, _ in u if x >= 0.6))

    def test_urma_fara_iesire_ramane_intreaga(self):
        u = [(0.0, 0.1, 0.6), (1.0, 0.15, 0.6)]
        self.assertEqual(taie_dupa_iesire(u, [self.IESIRE]), u)


class TestProbe(unittest.TestCase):
    def test_tipurile_rapide_lasa_pietonii_si_bicicletele(self):
        x = ('<additional><vType id="passenger" vClass="passenger" length="4.6" accel="2.6" decel="4.5" sigma="0.5" tau="1.0" maxSpeed="16.7" />'
             '<vType id="bicycle" vClass="bicycle" accel="1.2" decel="3" sigma="0.5" maxSpeed="6" /><vType id="pieton" vClass="pedestrian" maxSpeed="1.4" /></additional>')
        y = tipuri_rapide(x)
        for k in ('accel="4"', 'decel="7"', 'sigma="0"', 'minGap="1"', 'speedFactor="1.3"'):
            self.assertIn(k, y.split("<vType")[1])
        self.assertNotIn('accel="2.6"', y)
        self.assertEqual(y.split("<vType", 2)[2], x.split("<vType", 2)[2])

    def test_proba_se_deosebeste_doar_peste_prag_si_cu_intervale_separate(self):
        self.assertTrue(deosebeste(0.0, -0.05, 0.05, 0.5, 0.5, 0.5, 0.3))
        self.assertFalse(deosebeste(0.0, -0.05, 0.05, 0.2, 0.2, 0.2, 0.3))         # peste interval, dar sub prag
        self.assertFalse(deosebeste(0.0, -0.5, 0.5, 0.4, 0.4, 0.4, 0.3))           # în interiorul intervalului dintre seed-uri
        self.assertTrue(deosebeste(100.0, 95.0, 105.0, 80.0, 80.0, 80.0, float("nan")))
        self.assertFalse(deosebeste(100.0, 95.0, 105.0, 94.0, 94.0, 94.0, float("nan")))
        self.assertIsNone(deosebeste(float("nan"), 0, 0, 1.0, 1.0, 1.0, 0.1))

    def test_pe_profile_proba_se_compara_direct_cu_baza(self):
        camera, baza = np.array([1.0, 1.0, 0.0, 0.0]), np.array([1.0, 0.8, 0.2, 0.0])
        alta_parte = np.array([0.8, 1.0, 0.0, 0.2])      # la fel de departe de cameră ca baza, dar în altă parte
        self.assertAlmostEqual(abatere_profil(camera, baza), abatere_profil(camera, alta_parte))
        d, z = deosebeste_profil(baza, alta_parte, 0.25)
        self.assertAlmostEqual(d, 0.4)
        self.assertTrue(z)
        self.assertFalse(deosebeste_profil(baza, baza, 0.25)[1])
        self.assertIsNone(deosebeste_profil(baza, alta_parte, float("nan"))[1])
        self.assertIsNone(deosebeste_profil(np.zeros(4), alta_parte, 0.25)[1])

    def test_pierderea_pe_ramuri_e_chiar_pierderea_totala(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "t.xml"
            c.write_text('<tripinfos><tripinfo id="a" vType="passenger" timeLoss="3600" departDelay="1800" /><tripinfo id="b" vType="bicycle" timeLoss="360" departDelay="99" />'
                         '<personinfo id="p1"><walk timeLoss="360" /></personinfo><personinfo id="p2"><walk timeLoss="720" /></personinfo></tripinfos>', encoding="utf-8")
            r = pierdere_pe_ramuri(c, {"a": "dacia_vest", "b": "fond"}, {"p1"})
        self.assertEqual(r, {"dacia_vest": 1.5, "fond": 0.1, "pietoni_masurati": 0.1, "pietoni_extrapolati": 0.2})

    def test_abaterea_profilului(self):
        self.assertEqual(abatere_profil(np.array([1.0, 1.0]), np.array([1.0, 0.0])), 0.5)
        self.assertEqual(forma(np.array([1.0, 3.0])).tolist(), [0.25, 0.75])


class ProiectieLiniara:
    """1 m = 0,001 din cadru, pe ambele axe; punctele din afara plajei cad în afara cadrului."""
    H = 1000

    def lume_spre_img(self, w):
        return np.atleast_2d(np.asarray(w, float)) * 0.001

    def img_spre_lume(self, p):
        return np.atleast_2d(np.asarray(p, float)) * 1000


class TestUrma(unittest.TestCase):
    def test_pozitia_e_interpolata_la_pasul_camerei(self):
        u = urma_in_imagine(np.array([0.0, 1.0, 2.0]), np.array([100.0, 110.0, 120.0]), np.full(3, 500.0), ProiectieLiniara(), (0.0, 1.0))
        self.assertEqual(len(u), 11)
        self.assertAlmostEqual(u[1][0], 0.2)
        self.assertAlmostEqual(u[1][1], 0.102)

    def test_din_oprirea_lunga_raman_doar_capetele(self):
        t = np.arange(0.0, 61.0)
        x = np.r_[np.zeros(30) + 100, np.full(31, 100.0) + np.arange(31)]
        u = urma_in_imagine(t, x, np.full(61, 500.0), ProiectieLiniara(), (0.0, 1.0))
        opriti = [p[0] for p in u if p[0] <= 30.0 + 1e-6]        # stă pe loc până la secunda 30
        self.assertEqual(len(opriti), 2)
        self.assertAlmostEqual(opriti[1], 30.0)
        self.assertTrue(any(p[0] > 30.1 for p in u))

    def test_ce_cade_in_afara_zonei_de_interes_nu_ramane(self):
        u = urma_in_imagine(np.array([0.0, 1.0]), np.array([100.0, 100.0 + 10]), np.array([300.0, 500.0]), ProiectieLiniara(), (0.4, 1.0))
        self.assertTrue(all(p[2] >= 0.4 for p in u))
        self.assertLess(len(u), 6)

    def test_eroarea_proiectiei_e_in_secunde_la_viteza_vehiculului(self):
        t = np.arange(0.0, 10.0)
        x = 100.0 + 10.0 * t                # 10 m/s
        e = eroare_proiectie_s(ProiectieLiniara(), 5.0, t, x, np.full(10, 500.0), 20.0)     # 20 px / 1 000 px × 1 000 m = 20 m
        self.assertAlmostEqual(e, 2.0)
        self.assertAlmostEqual(eroare_proiectie_s(ProiectieLiniara(), 5.0, t, np.full(10, 100.0), np.full(10, 500.0), 20.0), 10.0)     # oprit: cel puțin 2 m/s


class TestNumaratori(unittest.TestCase):
    def test_pietonii_pe_ora_vin_din_numaratorile_ferestrei(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "numaratori_2026-10-26.csv").write_text(
                "inceput,sfarsit,tip,origine,destinatie,vehicul,numar\n"
                "2026-10-26 14:15:00,2026-10-26 14:30:00,pietoni,dacia_est,trecere_dacia_est_iesire,pieton,1000\n"
                "2026-10-26 14:30:00,2026-10-26 14:45:00,pietoni,dacia_est,trecere_dacia_est_iesire,pieton,200\n"
                "2026-10-26 14:30:00,2026-10-26 14:45:00,pietoni,dacia_est,trecere_dacia_est_intrare,pieton,999\n"
                "2026-10-26 14:45:00,2026-10-26 15:00:00,pietoni,dacia_est,trecere_dacia_est_iesire,pieton,100\n", encoding="utf-8")
            vechi = V.COUNTS_COR_DIR
            V.COUNTS_COR_DIR = Path(d)
            try:
                n = V.pietoni_numarati("2026-10-26", pd.Timestamp("2026-10-26 14:30"), pd.Timestamp("2026-10-26 15:00"))
                lipsa = V.pietoni_numarati("2026-10-27", pd.Timestamp("2026-10-27 14:30"), pd.Timestamp("2026-10-27 15:00"))
            finally:
                V.COUNTS_COR_DIR = vechi
        self.assertEqual(n, 600.0)
        self.assertIsNone(lipsa)

    def test_persoanele_de_pe_ambele_zebre(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "numaratori_2026-10-26.csv").write_text(
                "inceput,sfarsit,tip,origine,destinatie,vehicul,numar\n"
                "2026-10-26 14:30:00,2026-10-26 14:45:00,pietoni,dacia_est,trecere_dacia_est_iesire,pieton,200\n"
                "2026-10-26 14:30:00,2026-10-26 14:45:00,pietoni,dacia_est,trecere_dacia_est_intrare,pieton,100\n"
                "2026-10-26 14:30:00,2026-10-26 14:45:00,pietoni,magheru,trecere_magheru,pieton,999\n", encoding="utf-8")
            vechi = V.COUNTS_COR_DIR
            V.COUNTS_COR_DIR = Path(d)
            try:
                n = V.pietoni_numarati("2026-10-26", pd.Timestamp("2026-10-26 14:30"), pd.Timestamp("2026-10-26 14:45"), ("trecere_dacia_est_iesire", "trecere_dacia_est_intrare"))
            finally:
                V.COUNTS_COR_DIR = vechi
        self.assertEqual(n, 1200.0)


def sintetic(decalaj: float = 0.0, seeds: int = 2) -> tuple[dict, list[dict]]:
    """O oră inventată: cameră cu valuri și un „geamăn” care e chiar camera, cu momentele mutate cu `decalaj` secunde, fără factori."""
    rng = np.random.default_rng(1)
    verzi = V.info_v2()["green_states"]
    sc = 300.0 + 130.0 * np.arange(25)
    val = [(s, s + 60.0, 40) for s in sc]
    def valuri_pe(n, de_la, durata):
        return np.sort(np.concatenate([s + de_la + rng.uniform(0, durata, n) for s in sc]))
    intrari = {"magheru": valuri_pe(40, 0, 60), "catargiu": valuri_pe(25, 0, 60), "dacia_est": valuri_pe(8, 75, 40), "dacia_vest": valuri_pe(10, 75, 40)}
    iesiri = {"catargiu": valuri_pe(40, 0, 70), "magheru": valuri_pe(25, 0, 70), "dacia_est": np.sort(np.r_[valuri_pe(5, 0, 60), valuri_pe(10, 75, 40)]), "dacia_vest": valuri_pe(10, 0, 60), "mendeleev": valuri_pe(3, 0, 60)}
    pietoni = valuri_pe(20, 24, 40)
    miscari = [(o, d, float(t), float(t + u)) for (o, d, u) in (("magheru", "catargiu", 6.0), ("magheru", "dacia_est", 3.0), ("catargiu", "magheru", 2.5)) for t in intrari[o][::2]]
    miscari += [("dacia_est", "catargiu", 80.0 + i, 83.0 + i) for i in range(40)]
    miscari += [("catargiu", "dacia_vest", float(t - 3.0), float(t)) for t in iesiri["dacia_vest"][::2]]      # ieșirea are destule momente cu origine, deci rândurile ei judecă
    od = {"magheru>catargiu": 9000, "magheru>dacia_est": 9000, "catargiu>magheru": 9000, "dacia_est>catargiu": 1, "catargiu>dacia_vest": 0}
    cam = {"stem": "cor_zi_2026-10-26_varf", "zi": "2026-10-26", "a": 0.0, "f": dict.fromkeys(V.BRATE, 1.0), "intrari": intrari, "iesiri": iesiri, "val": val, "sc": sc, "ns": np.c_[sc, sc + 70], "ev": np.c_[sc + 75, sc + 120],
           "detalii": {"acoperire": 1.0}, "pietoni": pietoni, "pietoni_pe_ora": float(len(pietoni)), "miscari": miscari, "od": {"durata_s": 3600, "od_vehicule": od}}
    stari = [(0, verzi[1])]
    for s in sc:
        stari += [(int(s), verzi[0]), (int(s) + 70, "y" * len(verzi[0])), (int(s) + 75, verzi[1]), (int(s) + 120, "r" * len(verzi[0]))]
    rez = [{"brate": {b: intrari[b] + decalaj for b in V.BRATE}, "iesiri": {b: iesiri[b] + decalaj for b in V.IESIRI}, "pietoni": pietoni + decalaj, "stari": stari, "intrari_zebre": [(400, 55, "G"), (500, 55, "r")],
            "virtuala": [(o, d, to, td, 0.1) for o, d, to, td in miscari], "ciocniri": {"vehicule": 0, "mers_masurati": 1, "mers_extrapolati": 1, "oprit_masurati": 0, "oprit_extrapolati": 0}, "neintrate": {"total": 0, "dacia_vest": 0},
            "vv": {"axa_inel": 0, "alte": 0, "adanc_1m": 0}, "vp": {"mers_masurati": 0, "mers_extrapolati": 0, "oprit_masurati": 0, "oprit_extrapolati": 0}, "pierderi": {"dacia_vest": 2.0},
            "r": {"teleportari": 0, "ciocniri_vehicule": 0, "ciocniri_pieton_in_miscare": 2, "vehicule_sosite": 1000, "nefinalizate": 0, "pierdere_totala_h": 2.0}, "cost": {}} for _ in range(seeds)]
    return cam, rez


class TestRanduri(unittest.TestCase):
    def test_un_geaman_care_e_chiar_camera_e_in_prag_pe_tot_ce_vine_din_comparatie(self):
        cam, rez = sintetic()
        d, profile = V.randuri(cam, rez)
        self.assertEqual(set(d["grup"]), {"A", "B", "C", "D"})
        self.assertFalse(d["masura"].str.contains("Total în prag|corelați|drumul|primele 20", case=False).any())
        comparate = d[d["cheie"].isin(["debit", "varf_20s", "timp", "decalaj", "iesire_24_60", "profil_intrare", "forma_iesire"])]
        self.assertTrue((comparate["verdict"] == "în prag").all(), comparate[["masura", "abatere", "prag", "verdict"]])
        self.assertTrue(np.allclose(comparate["abatere"].abs(), 0.0, atol=1e-9))
        self.assertEqual(d[d["masura"].str.startswith("pietoni pe zebra Dacia est: hist")]["verdict"].iloc[0], "în prag")
        self.assertIn("intrare magheru", profile)
        self.assertEqual(len(profile["ieșire dacia_est"][0]), BINI)

    def test_profilele_au_nul_si_zgomot_iar_nulul_sub_zgomot_e_neinformativ(self):
        d = V.randuri(*sintetic())[0]
        c = d[d["grup"] == "C"]
        self.assertEqual(len(c), 8)
        self.assertTrue(c["nul"].notna().all() and c["zgomot_camera_p95"].notna().all())
        self.assertTrue(((c["nul"] < c["zgomot_camera_p95"]) == (c["reper"] == "neinformativ")).all())
        self.assertTrue(c["prag"].notna().all())                  # și Dacia vest: pragurile sunt pe braț, din zgomot
        self.assertTrue((c["sursa_prag"] == "calculat").all())

    def test_cererea_sub_traiectoriile_complete_pica(self):
        d = V.randuri(*sintetic())[0]
        o = d[d["cheie"] == "od"].set_index("masura")
        self.assertEqual(o.loc["O–D dacia_est → catargiu: traiectorii complete în cameră / cerere", "verdict"], "peste prag")
        self.assertEqual(o.loc["O–D magheru → catargiu: traiectorii complete în cameră / cerere", "verdict"], "în prag")
        self.assertFalse(o["din_simulare"].any())

    def test_pierderea_si_contoarele_nu_au_prag(self):
        d = V.randuri(*sintetic())[0]
        self.assertTrue(d[d["cheie"].isin(["pierdere", "atingeri_vv", "atingeri_oprit", "rosu", "regresie_val"])]["prag"].isna().all())
        self.assertEqual(d[d["masura"].str.startswith("pierdere pe ramura Dacia vest")]["geaman"].iloc[0], 2.0)

    def test_pragul_vine_din_fisier_apoi_din_baza_si_abia_apoi_din_calcul(self):
        cam, rez = sintetic()
        d = V.randuri(cam, rez, fixate={"profil_intrare:magheru": 0.5, "debit:magheru": 0.2}, din_baza={"profil_intrare:catargiu": 0.4})[0].set_index("masura")
        self.assertEqual((d.loc["profil pe ciclu: magheru", "prag"], d.loc["profil pe ciclu: magheru", "sursa_prag"]), (0.5, "fișier"))
        self.assertEqual((d.loc["profil pe ciclu: catargiu", "prag"], d.loc["profil pe ciclu: catargiu", "sursa_prag"]), (0.4, "din bază"))
        self.assertEqual(d.loc["profil pe ciclu: dacia_est", "sursa_prag"], "calculat")
        self.assertEqual((d.loc["debit, veh/h: magheru", "prag"], d.loc["debit, veh/h: magheru", "sursa_prag"]), (0.2, "fișier"))
        self.assertEqual((d.loc["debit, veh/h: catargiu", "prag"], d.loc["debit, veh/h: catargiu", "sursa_prag"]), (V.PRAGURI["debit"], "scris"))

    def test_un_ceas_gresit_se_vede_la_decalaj_si_tabelul_il_deosebeste_de_baza(self):
        cam, rez = sintetic()
        baza = V.randuri(cam, rez)[0]
        din_baza = dict(zip(baza["cheie_prag"], baza["prag"]))
        din_baza.pop("", None)
        _, gresit = sintetic(decalaj=15.0, seeds=1)
        proba = V.randuri(cam, gresit, din_baza=din_baza)[0]
        m = V.marcheaza_deosebiri(baza, proba, "rapid").set_index("masura")
        self.assertEqual(m.loc["decalaj de aliniere, s: intrare magheru", "geaman"], -15.0)
        self.assertEqual(m.loc["decalaj de aliniere, s: intrare magheru", "verdict"], "peste prag")
        self.assertEqual(m.loc["decalaj de aliniere, s: intrare magheru", "deosebeste"], "da")
        self.assertEqual(m.loc["debit, veh/h: magheru", "deosebeste"], "nu")          # debitul nu vede un ceas greșit
        self.assertEqual(m.loc["O–D magheru → catargiu: traiectorii complete în cameră / cerere", "deosebeste"], "–")
        self.assertIn("rapid", V.tabel_text(baza, {"rapid": m.reset_index()}))

    def test_lista_masurilor_utile_se_da_doar_cu_probele_pe_cel_putin_doua_seeduri(self):
        cam, rez = sintetic()
        baza = V.randuri(cam, rez)[0]
        din_baza = dict(zip(baza["cheie_prag"], baza["prag"]))
        din_baza.pop("", None)
        _, gresit = sintetic(decalaj=15.0, seeds=1)
        m = V.marcheaza_deosebiri(baza, V.randuri(cam, gresit, din_baza=din_baza)[0], "rapid")
        unu = V.rezumat_probe({"rapid": m}, 1, 2)
        self.assertIn("Lista măsurilor utile nu se dă", unu)
        self.assertNotIn("nu deosebesc nicio probă", unu)
        self.assertNotIn("    - ", unu)
        self.assertIn("probe pe 1 seed, baza pe 2 seed-uri", unu)
        doi = V.rezumat_probe({"rapid": m}, 2, 2)
        self.assertIn("nu deosebesc nicio probă, pe 2 seed-uri", doi)
        self.assertIn("    - decalaj de aliniere, s: intrare magheru", doi)

    def test_randurile_despre_pietoni_n_au_obiect_la_proba_fara_pietoni(self):
        cam, rez = sintetic()
        baza = V.randuri(cam, rez)[0]
        _, fara = sintetic(seeds=1)
        fara[0]["pietoni"] = np.empty(0)
        m = V.marcheaza_deosebiri(baza, V.randuri(cam, fara)[0], "fara_pietoni").set_index("masura")
        self.assertEqual(m.loc["pietoni pe zebra Dacia est, pe oră", "deosebeste"], "fără obiect")

    def test_o_ora_fara_valuri_nu_se_opreste_din_calcul(self):
        cam, rez = sintetic()
        cam.update(val=[], sc=np.empty(0))
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d = V.randuri(cam, rez)[0]
        self.assertEqual(d[d["cheie"] == "profil_intrare"]["verdict"].unique().tolist(), ["–"])

    def test_pe_profile_o_proba_la_fel_de_departe_de_camera_dar_in_alta_parte_se_vede(self):
        """Regula veche compara distanțele față de cameră: la +12 s și la −12 s sunt aproape egale, deși cele două profile nu seamănă deloc."""
        cam, _ = sintetic()
        _, plus = sintetic(decalaj=12.0)
        baza = V.randuri(cam, plus)[0]
        din_baza = dict(zip(baza["cheie_prag"], baza["prag"]))
        din_baza.pop("", None)
        _, minus = sintetic(decalaj=-12.0)
        m = V.marcheaza_deosebiri(baza, V.randuri(cam, minus, din_baza=din_baza)[0], "rapid").set_index("masura")
        r = "profil pe ciclu: magheru"
        self.assertLess(abs(abs(m.loc[r, "abatere"]) - abs(baza.set_index("masura").loc[r, "abatere"])), m.loc[r, "prag"])
        self.assertGreater(m.loc[r, "dist_baza"], m.loc[r, "prag"])
        self.assertEqual(m.loc[r, "deosebeste"], "da")
        self.assertEqual(m.loc["forma pe ciclu, ieșirea: catargiu", "deosebeste"], "da")
        self.assertTrue(np.isnan(m.loc["debit, veh/h: magheru", "dist_baza"]))       # pe celelalte rânduri rămâne regula de până acum

    def test_acelasi_geaman_pe_alt_seed_nu_e_deosebit_pe_profile(self):
        cam, rez = sintetic()
        baza = V.randuri(cam, rez)[0]
        din_baza = dict(zip(baza["cheie_prag"], baza["prag"]))
        din_baza.pop("", None)
        m = V.marcheaza_deosebiri(baza, V.randuri(cam, sintetic(seeds=1)[1], din_baza=din_baza)[0], "rapid")
        c = m[m["cheie"].isin(["profil_intrare", "forma_iesire", "iesire_ns"])]
        self.assertTrue((c["deosebeste"] == "nu").all())
        self.assertTrue(np.allclose(c["dist_baza"], 0.0))

    def test_o_camera_virtuala_stricata_pica_nu_da_liniuta(self):
        cam, rez = sintetic()
        for r in rez:
            r["virtuala"] = []
        t = V.randuri(cam, rez)[0]
        t = t[t["cheie"] == "timp"]
        self.assertEqual(len(t), 4)
        self.assertTrue((t["verdict"] == "peste prag").all())
        self.assertTrue(t["nota"].str.contains("geamănul nu are traiectorii").all())

    def test_seedurile_fara_traiectorii_se_numara_si_nu_lasa_randul_in_prag(self):
        cam, rez = sintetic()
        rez[0]["virtuala"] = []
        t = V.randuri(cam, rez)[0]
        t = t[t["cheie"] == "timp"]
        self.assertTrue((t["verdict"] == "nedecis").all())
        self.assertTrue(t["nota"].str.contains("1 din 2 seed-uri fără valoare").all())

    def test_prea_putine_in_camera_tot_nu_se_judeca(self):
        cam, rez = sintetic()
        cam["miscari"] = []
        for r in rez:
            r["virtuala"] = []
        t = V.randuri(cam, rez)[0]
        self.assertTrue((t[t["cheie"] == "timp"]["verdict"] == "–").all())

    def test_pietonii_au_aceeasi_fereastra_pe_ambele_parti(self):
        cam, rez = sintetic()
        cam["pietoni_pe_ora"] = 900.0
        for r in rez:
            r["pietoni"] = np.r_[np.full(10, 100.0), r["pietoni"]]        # și în încălzire: numărătoarea camerei e pe toată ora
        q = V.randuri(cam, rez)[0].set_index("masura").loc["pietoni pe zebra Dacia est, pe oră"]
        self.assertEqual(q["camera"], 900.0)
        self.assertEqual(q["geaman"], float(len(rez[0]["pietoni"])))
        self.assertIn("ambele pe toată ora", q["nota"])
        self.assertNotIn("fără numărătoarea orei", q["nota"])

    def test_pietonii_se_compara_cu_persoanele_ori_factorul(self):
        cam, rez = sintetic()
        cam.update(pietoni_pe_ora=900.0, persoane_pe_ora=1000.0, f_pietoni=1.5)
        q = V.randuri(cam, rez)[0].set_index("masura").loc["pietoni pe zebra Dacia est, pe oră"]
        self.assertEqual(q["camera"], 1500.0)
        self.assertEqual(q["grup"], "A")
        self.assertIn("× factorul din referință, 1.5", q["nota"])
        self.assertIn("detectorul singur, doar pe zebra de ieșire: 900", q["nota"])

    def test_iesirea_in_ns_se_citeste_pe_zona_chiar_daca_pe_ora_se_citeste_pe_muchie(self):
        cam, rez = sintetic()
        z = []
        for r in rez:
            m = np.asarray(r["iesiri"]["dacia_est"], float)
            ns = V.ns_din_stari(r)
            in_ns = np.array([any(a <= x < b for a, b in ns) for x in m])
            z.append(dict(r, zone={"intrare": {}, "ieșire": {"dacia_est": m[in_ns] - 2.0}}))      # în afara etapei N–S, camera virtuală nu le prinde
        self.assertEqual(V.acoperire_virtuala(z[0], "ieșire", "dacia_est") < V.ACOPERIRE_VIRTUALA, True)
        c = alege_citiri(z)
        self.assertEqual(c[("ieșire", "dacia_est")], "muchie")
        self.assertEqual(c[V.CITIRE_NS], "zonă")
        d = V.randuri(cam, z)[0].set_index("masura")
        self.assertEqual(d.loc["ieșirea Dacia est, s 24–60 din N–S: nivel, veh/etapă", "citire"], "zonă")
        self.assertIn("în N–S, citit pe zonă", d.loc["ieșirea Dacia est, s 24–60 din N–S: nivel, veh/etapă", "nota"])
        self.assertEqual(d.loc["decalaj de aliniere, s: ieșire dacia_est", "citire"], "muchie")
        self.assertIn("ieșire în N–S dacia_est: zonă", V.rezumat_citiri(z, c))

    def test_fara_numaratoare_nota_spune_ce_sursa_s_a_folosit(self):
        cam, rez = sintetic()
        cam["pietoni_pe_ora"] = None
        for r in rez:
            r["pietoni"] = np.r_[np.full(10, 100.0), r["pietoni"]]
        q = V.randuri(cam, rez)[0].set_index("masura").loc["pietoni pe zebra Dacia est, pe oră"]
        self.assertAlmostEqual(q["camera"], len(cam["pietoni"]) * 3600 / 3300)
        self.assertAlmostEqual(q["geaman"], q["camera"])                  # și geamănul, pe 300–3600 s
        self.assertIn("doar traversările văzute", q["nota"])
        self.assertNotIn("numărătoarea orei, cu cei", q["nota"])

    def test_decalajul_nu_depinde_de_factor_iar_varful_o_spune(self):
        cam, rez = sintetic(decalaj=5.0)
        d = V.randuri(cam, rez)[0].set_index("masura")
        cam2 = dict(cam, f={b: 0.9 for b in V.BRATE})
        d2 = V.randuri(cam2, rez)[0].set_index("masura")
        dec = d[d["cheie"] == "decalaj"].index
        self.assertEqual(d.loc[dec, "abatere"].tolist(), d2.loc[dec, "abatere"].tolist())
        self.assertEqual(d.loc[dec, "prag"].tolist(), d2.loc[dec, "prag"].tolist())
        v = "debit de vârf pe 20 s, veh/s: magheru"
        self.assertNotEqual(d.loc[v, "abatere"], d2.loc[v, "abatere"])
        self.assertIn("cu factorul brațului, 1", d.loc[v, "nota"])
        self.assertIn("eroarea factorului nu e în prag", d.loc[v, "nota"])

    def test_randul_rularilor_cu_probleme(self):
        cam, rez = sintetic(seeds=5)
        for r, tele, tot in zip(rez, (0, 2, 0, 1, 0), (354.7, 463.7, 362.7, 359.7, 357.7)):
            r["r"] = dict(r["r"], teleportari=tele, pierdere_totala_h=tot)
            r["seed"] = 10 + tele
        q = V.randuri(cam, rez)[0].set_index("masura").loc["rulări cu teleportări sau cu blocaj presupus"]
        self.assertEqual(q["geaman"], 2.0)
        self.assertIn("din 5", q["nota"])
        self.assertIn("seed 12: 2 teleportări, pierdere totală 464 h", q["nota"])
        self.assertIn("seed 11: 1 teleportare", q["nota"])
        self.assertIn("sub 4 seed-uri", V.randuri(*sintetic())[0].set_index("masura").loc["rulări cu teleportări sau cu blocaj presupus", "nota"])


def cu_doua_minime(cam: dict, rez: list[dict]) -> None:
    """Ieșirea Dacia vest, ca pe 26.10 vârf: media seed-urilor se așază clar la +15 s, dar fiecare seed are curba cu două minime, deci unele se așază singure la −15 s."""
    rng = np.random.default_rng(3)

    def doua_varfuri(de_la, p, q):
        return np.sort(np.concatenate([s + np.r_[rng.normal(de_la, 1.5, p), rng.normal(de_la + 30, 1.5, q)] for s in cam["sc"]]))
    cam["iesiri"]["dacia_vest"] = doua_varfuri(50, 30, 20)
    for r, (p, q) in zip(rez, ((45, 5), (5, 45), (45, 5), (5, 45), (45, 5))):
        r["iesiri"] = dict(r["iesiri"], dacia_vest=doua_varfuri(35, p, q))


def mutat(r: dict, d: float) -> dict:
    return dict(r, brate={k: v + d for k, v in r["brate"].items()}, iesiri={k: v + d for k, v in r["iesiri"].items()}, pietoni=r["pietoni"] + d)


class TestDecalajPeSeeduri(unittest.TestCase):
    RAND = "decalaj de aliniere, s: ieșire dacia_vest"

    @classmethod
    def setUpClass(cls):
        cls.cam, cls.rez = sintetic(seeds=5)
        cu_doua_minime(cls.cam, cls.rez)
        cls.cam["miscari"] = cls.cam["miscari"] + [("catargiu", "dacia_vest", float(t - 3.0), float(t)) for t in cls.cam["iesiri"]["dacia_vest"]]      # momentele noi au și origine, deci rândul judecă
        cls.baza = V.randuri(cls.cam, cls.rez)[0]
        cls.din_baza = dict(zip(cls.baza["cheie_prag"], cls.baza["prag"]))
        cls.din_baza.pop("", None)

    def test_zgomotul_seedurilor_vine_din_media_fara_cate_unul(self):
        q = self.baza.set_index("masura").loc[self.RAND]
        self.assertAlmostEqual(q["geaman"], 15, delta=2)
        self.assertTrue(all(abs(x - q["geaman"]) <= 2 for x in V.json.loads(q["pe_seed"])))       # media fără câte un seed stă pe loc
        self.assertLess(q["zgomot_seeduri"], 5)
        self.assertLess(q["prag"], 10)                                 # pe fiecare seed singur, zgomotul ar fi fost ≈30 s, deci pragul ar fi trecut de plajă
        self.assertEqual(q["verdict"], "peste prag")                   # rândul poate pica
        singure = [int(x) for x in q["nota"].split("fiecare seed singur: [")[1].split("]")[0].split(", ")]
        self.assertLess(min(singure), 0)                               # seed-urile singure chiar sar
        self.assertGreater(max(singure), 0)

    def test_un_decalaj_de_12_s_pe_cinci_seeduri_se_vede_pe_toate_randurile(self):
        m = V.marcheaza_deosebiri(self.baza, V.randuri(self.cam, [mutat(r, 12.0) for r in self.rez], din_baza=self.din_baza)[0], "rapid")
        d = m[m["cheie"] == "decalaj"].set_index("masura")
        self.assertEqual(len(d), 8)
        self.assertTrue((d["deosebeste"] == "da").all(), d[["abatere", "prag", "deosebeste"]])
        self.assertAlmostEqual(d.loc[self.RAND, "geaman"], 3, delta=2)      # +15 − 12
        self.assertEqual(d.loc["decalaj de aliniere, s: intrare magheru", "verdict"], "peste prag")
        self.assertEqual(d.loc["decalaj de aliniere, s: intrare magheru", "geaman"], -12.0)

    def test_un_prag_care_atinge_plaja_nu_lasa_randul_in_prag(self):
        q = V.randuri(self.cam, self.rez[:2])[0].set_index("masura").loc[self.RAND]        # la 2 seed-uri, media fără unul e celălalt seed singur, deci sare
        self.assertGreaterEqual(q["prag"], V.PLAJA_DECALAJ_S)
        self.assertEqual(q["verdict"], "neinformativ")
        self.assertIn("n-ar putea pica", q["nota"])

    def test_un_prag_din_fisier_care_atinge_plaja_e_tot_neinformativ_iar_proba_nu_se_judeca(self):
        baza = V.randuri(self.cam, self.rez, fixate={"decalaj_iesire:dacia_vest": 25.0})[0]
        self.assertEqual(baza.set_index("masura").loc[self.RAND, "verdict"], "neinformativ")
        m = V.marcheaza_deosebiri(baza, V.randuri(self.cam, [mutat(r, 12.0) for r in self.rez], fixate={"decalaj_iesire:dacia_vest": 25.0})[0], "rapid").set_index("masura")
        self.assertEqual(m.loc[self.RAND, "deosebeste"], "–")


class TestCitire(unittest.TestCase):
    @staticmethod
    def cu_zone(r: dict, d: float = 2.0, doar=None) -> dict:
        """Camera virtuală prinde toate vehiculele, cu `d` secunde mai târziu decât pe muchie; `doar`: pe ce capete."""
        return dict(r, zone={rol: {b: v + d for b, v in r[V.CHEI_CAPAT[rol]].items() if doar is None or (rol, b) in doar} for rol in V.CHEI_CAPAT})

    def test_acoperirea_e_pe_fereastra_si_cere_toate_seedurile(self):
        r = {"brate": {"a": np.r_[100.0, 400.0, 500.0, 600.0, 700.0]}, "zone": {"intrare": {"a": np.r_[100.0, 400.0, 500.0, 600.0]}}}
        self.assertEqual(acoperire_virtuala(r, "intrare", "a"), 0.75)
        self.assertEqual(acoperire_virtuala({"brate": {"a": np.empty(0)}}, "intrare", "a"), 0.0)
        cam, rez = sintetic()
        c = alege_citiri([self.cu_zone(x) for x in rez])
        self.assertEqual(set(c.values()), {"zonă"})
        self.assertEqual(alege_citiri(rez)[("intrare", "magheru")], "muchie")
        self.assertEqual(alege_citiri([self.cu_zone(rez[0]), rez[1]])[("intrare", "magheru")], "muchie")      # un seed fără, deci muchie

    def test_unde_prinde_aproape_tot_se_citeste_din_camera_virtuala(self):
        cam, rez = sintetic()
        z = [self.cu_zone(r, 2.0) for r in rez]
        d = V.randuri(cam, z)[0].set_index("masura")
        for rand in ("decalaj de aliniere, s: intrare magheru", "decalaj de aliniere, s: ieșire catargiu"):
            self.assertEqual(d.loc[rand, "geaman"], -2.0)
            self.assertEqual(d.loc[rand, "citire"], "zonă")
            self.assertNotIn("citit pe muchie", d.loc[rand, "nota"])
        self.assertEqual(d.loc["profil pe ciclu: magheru", "citire"], "zonă")
        self.assertEqual(d.loc["debit, veh/h: magheru", "abatere"], 0.0)       # numărătorile rămân pe muchie

    def test_in_rest_se_citeste_pe_muchie_iar_nota_da_diferenta_pe_acelasi_vehicul(self):
        cam, rez = sintetic()
        z = [dict(self.cu_zone(r, 2.0, doar={("intrare", "magheru")}), muchie_zona={"ieșire dacia_vest": np.array([1.0, 2.0, 3.0, 4.0, 5.0])}) for r in rez]
        d = V.randuri(cam, z)[0].set_index("masura")
        self.assertEqual(d.loc["decalaj de aliniere, s: intrare magheru", "citire"], "zonă")
        q = d.loc["decalaj de aliniere, s: ieșire dacia_vest"]
        self.assertEqual(q["citire"], "muchie")
        self.assertEqual(q["geaman"], 0.0)
        self.assertIn("muchie − zonă pe același vehicul: p50 +3.0 s", q["nota"])
        self.assertIn("citit pe muchie", d.loc["forma pe ciclu, ieșirea: dacia_vest", "nota"])
        self.assertIn("nicio comparație pe același vehicul", d.loc["decalaj de aliniere, s: ieșire dacia_est", "nota"])

    def test_o_proba_se_citeste_ca_baza(self):
        cam, rez = sintetic()
        z = [self.cu_zone(r, 2.0) for r in rez]
        c = alege_citiri(z)
        fara = dict(self.cu_zone(rez[0], 2.0), zone={"intrare": {b: v + 2.0 for b, v in rez[0]["brate"].items()}, "ieșire": {b: v[:20] + 2.0 for b, v in rez[0]["iesiri"].items()}})      # pe ieșiri, sub 90%
        self.assertEqual(alege_citiri([fara])[("ieșire", "catargiu")], "muchie")
        self.assertEqual(V.randuri(cam, [fara], citiri=c)[0].set_index("masura").loc["decalaj de aliniere, s: ieșire catargiu", "citire"], "zonă")

    def test_diferenta_e_doar_pe_vehiculele_prinse_in_ambele_locuri(self):
        virtuala = {"complete": [], "intrare": {"a": {1: 10.0, 2: 20.0}}, "ieșire": {"b": {3: 50.0}, "mendeleev": {4: 7.0}}}
        muchie = {"intrare": {"a": {1: 11.5, 9: 30.0}}, "ieșire": {"b": {5: 60.0}}}
        zone, dif = citiri_din_virtuala(virtuala, muchie)
        self.assertEqual(zone["intrare"]["a"].tolist(), [10.0, 20.0])
        self.assertEqual(zone["ieșire"]["mendeleev"].tolist(), [7.0])
        self.assertEqual(dif["intrare a"].tolist(), [1.5])
        self.assertEqual(dif["ieșire b"].tolist(), [])

    def test_rezumatul_citirilor_spune_de_unde_si_cat_difera(self):
        _, rez = sintetic()
        z = [dict(self.cu_zone(r, doar={("intrare", "magheru")}), muchie_zona={"intrare magheru": np.array([-1.0, -1.0, -2.0])}) for r in rez]
        s = V.rezumat_citiri(z, alege_citiri(z))
        self.assertIn("intrare magheru: zonă, 100%, muchie − zonă p50 -1.0 s", s)
        self.assertIn("intrare catargiu: muchie, 0%", s)

    def test_o_iesire_cu_prea_putine_origini_nu_judeca_forma(self):
        cam, rez = sintetic(5.0)
        cam["miscari"] = [m for m in cam["miscari"] if m[1] != "dacia_vest"]
        self.assertEqual(V.parte_cu_origine(cam, "dacia_vest"), 0.0)
        d = V.randuri(cam, rez)[0].set_index("masura")
        q = d.loc["decalaj de aliniere, s: ieșire dacia_vest"]
        self.assertEqual(q["verdict"], "neinformativ")
        self.assertIn("rândul ar măsura detectorul", q["nota"])
        self.assertEqual(d.loc["decalaj de aliniere, s: ieșire magheru", "verdict"], "peste prag")

    def test_fragmentele_din_etapa_n_s_nu_intra_la_forma_de_pe_dacia_vest(self):
        self.assertEqual(V.fara_etapa(np.array([5.0, 12.0, 16.0, 30.0]), np.array([[10.0, 11.0]])).tolist(), [5.0, 16.0, 30.0])       # marja de 5 s
        cam, rez = sintetic()
        curat = cam["intrari"]["dacia_vest"]
        fragmente = np.sort(np.concatenate([s + np.arange(5.0, 55.0, 10.0) for s in cam["sc"]]))
        cam["intrari"] = {**cam["intrari"], "dacia_vest": np.sort(np.r_[curat, fragmente])}
        d = V.randuri(cam, rez)[0].set_index("masura")
        self.assertEqual(d.loc["decalaj de aliniere, s: intrare dacia_vest", "geaman"], 0.0)
        self.assertIn("fragmente", d.loc["decalaj de aliniere, s: intrare dacia_vest", "nota"])
        self.assertLess(d.loc["profil pe ciclu: dacia_vest", "abatere"], 0.40)      # factorul de pe tot brațul rămâne, deci profilul e doar mai sus, nu altă formă

    def test_ce_nu_acopera_randurile_e_spus(self):
        self.assertTrue(any("Mendeleev" in k for k in V.RENUNTATE))
        self.assertIn("același cod de zone", V.LIMITE)
        self.assertIn("trei mișcări", V.LIMITE["același cod de zone"])
        self.assertIn("ceasul", V.LIMITE)


class TraciFals:
    """Cât îi trebuie lui `Contoare` dintr-un pas al simulării: cine e pe ce muchie, unde sunt vehiculele, starea semaforului. Pozițiile sunt în cutia pieței."""

    def __init__(self):
        self.muchii, self.persoane, self.pozitii = {}, {}, {}
        self.stare = "G" * 200
        treceri = V.info_v2()["pietoni"]["treceri"]
        legaturi = {i: [("a", f"zebra{i}_0", "c")] for i in treceri}
        self.trafficlight = types.SimpleNamespace(getControlledLinks=lambda _: legaturi, getRedYellowGreenState=lambda _: self.stare)
        self.edge = types.SimpleNamespace(getLastStepVehicleIDs=lambda m: self.muchii.get(m, []), getLastStepPersonIDs=lambda m: self.persoane.get(m, []))
        self.vehicle = types.SimpleNamespace(getTypeID=lambda v: "passenger", getIDList=lambda: list(self.pozitii), getPosition=lambda v: self.pozitii[v], getLength=lambda v: 4.6, getWidth=lambda v: 1.8,
                                             getAngle=lambda v: 0.0, getLaneID=lambda v: "x_0", getSpeed=lambda v: 5.0)
        self.person = types.SimpleNamespace(getPosition=lambda p: (0.0, 0.0))
        self.simulation = types.SimpleNamespace(getCollisions=lambda: [], getPendingVehicles=lambda: [])


class TestContoare(unittest.TestCase):
    def test_ceasul_observatorului(self):
        """`evaluate.run_one` dă indicele buclei, iar ceasul SUMO după pas e t + 1: ce s-a întâmplat în pas are momentul t + 0,5, pozițiile t + 1, iar starea semaforului rămâne la t."""
        c, tr = V.Contoare(), TraciFals()
        magheru, iesire = V.BRATE["magheru"], V.IESIRI["catargiu"][0]
        zebra = f"zebra{V.TRECERE_DACIA_EST}"
        tr.muchii[magheru] = ["v"]
        tr.pozitii["v"] = (1000.0, 800.0)
        tr.persoane[zebra] = ["p"]
        c(tr, 10)
        tr.muchii[magheru] = []
        tr.muchii[iesire] = ["v"]
        tr.stare = "r" * 200
        c(tr, 11)
        r = c.rezultat()
        self.assertEqual(r["brate"]["magheru"].tolist(), [11.5])
        self.assertEqual(r["iesiri"]["catargiu"].tolist(), [11.5])
        self.assertEqual(r["pietoni"].tolist(), [10.5])
        self.assertEqual(r["intrari_zebre"], [(10.5, V.TRECERE_DACIA_EST, "G")])
        self.assertEqual([t for t, _ in r["stari"]], [10, 11])
        self.assertEqual(c.urme[0], 11.0)        # poziția de după pasul 10
        self.assertEqual(c.urme[4], 12.0)
        self.assertEqual(r["pe_muchie"]["intrare"]["magheru"], {0: 11.5})
        self.assertEqual(r["pe_muchie"]["ieșire"]["catargiu"], {0: 11.5})

    def test_vehiculul_de_pe_catargiu_care_nu_ajunge_in_dreptul_zonei(self):
        c, tr = V.Contoare(), TraciFals()
        linia = V.BRATE["catargiu"]
        tr.muchii[linia] = ["v"]
        c(tr, 20)
        tr.muchii[linia] = []
        c(tr, 21)
        for t in range(22, 61):
            c(tr, t)
        self.assertEqual(c.rezultat()["brate"]["catargiu"].tolist(), [])
        c(tr, 62)                                # a trecut de 40 s de la linia de oprire
        self.assertEqual(c.rezultat()["brate"]["catargiu"].tolist(), [21.5 + 8])

    def test_vehiculul_de_pe_catargiu_prins_in_dreptul_zonei(self):
        c, tr = V.Contoare(), TraciFals()
        linia, zona = V.BRATE["catargiu"], V.PUNCTE_INTRARE["catargiu"][0]
        tr.muchii[linia] = ["v"]
        c(tr, 20)
        tr.muchii[linia] = []
        c(tr, 21)
        tr.muchii[zona] = ["v"]
        c(tr, 25)
        self.assertEqual(c.rezultat()["brate"]["catargiu"].tolist(), [25.5])


class TestCachePietoni(unittest.TestCase):
    ZONA = Zone("trecere_dacia_est_iesire", "dacia_est", "trecere", np.array([[0.0, 0.5], [0.2, 0.5], [0.2, 0.7], [0.0, 0.7]]))
    ALTA = Zone("trecere_dacia_est_iesire", "dacia_est", "trecere", np.array([[0.0, 0.5], [0.3, 0.5], [0.3, 0.7], [0.0, 0.7]]))

    def test_rezumatul_tine_de_zone(self):
        with tempfile.TemporaryDirectory() as d:
            vechi = V.OUTPUT_DIR, V.TRAJ_RAW_DIR
            V.OUTPUT_DIR, V.TRAJ_RAW_DIR = Path(d), Path(d)        # fără jurnal: ce nu e în rezumat, nu se poate reface
            try:
                (Path(d) / "validare").mkdir()
                np.save(Path(d) / "validare" / "pietoni_2026-10-26_1000.npy", np.array([1.0]))                                         # numele vechi, fără amprentă
                self.assertIsNone(V.pietoni_camera("2026-10-26", 1000.0, 2000.0, [self.ZONA]))
                np.save(Path(d) / "validare" / f"pietoni_2026-10-26_1000_{V.amprenta_zone([self.ZONA])}.npy", np.array([2.0]))
                self.assertEqual(V.pietoni_camera("2026-10-26", 1000.0, 2000.0, [self.ZONA]).tolist(), [2.0])
                self.assertIsNone(V.pietoni_camera("2026-10-26", 1000.0, 2000.0, [self.ALTA]))                                         # zonele s-au schimbat
                self.assertIsNone(V.pietoni_camera("2026-10-26", 1000.0, 2000.0, []))
            finally:
                V.OUTPUT_DIR, V.TRAJ_RAW_DIR = vechi


class TestLinieDeComanda(unittest.TestCase):
    def test_pragurile_nu_se_scriu_pe_mai_putin_de_cinci_seeduri(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()) as e, self.assertRaises(SystemExit):
            V.main(["cor_zi_2026-10-26_varf", "--seeds", "1,2", "--scrie-praguri", "x.json"])
        self.assertIn("cel puțin 5 seed-uri", e.getvalue())

    def test_doar_scenariile_masurii_noi(self):
        import contextlib
        import io
        for s in ("zi_2026-10-26_varf", "cor_zi_2026-10-26_varf_x1_2"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                V.main([s])


class AmprentaCererii(unittest.TestCase):
    """Rutele poartă amprenta cererii cu care s-au făcut: o nepotrivire se vede și când datele fișierelor nu spun nimic."""

    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.demand, self.ruta = Path(d.name) / "demand_v2.json", Path(d.name) / "r.rou.xml"
        self.demand.write_text('{"factor": 1}', encoding="utf-8")
        self.ruta.write_text("<routes/>", encoding="utf-8")
        self.amprenta = hashlib.sha256(self.demand.read_text(encoding="utf-8").encode()).hexdigest()[:16]

    def test_aceeasi_amprenta(self):
        self.assertIsNone(V.avertisment_factori(self.demand, [self.ruta], self.amprenta))

    def test_alta_amprenta_chiar_daca_rutele_sunt_mai_noi(self):
        os.utime(self.demand, (1, 1))
        self.assertIn("altă cerere", V.avertisment_factori(self.demand, [self.ruta], "0123456789abcdef"))

    def test_fara_amprenta_se_compara_datele(self):
        os.utime(self.ruta, (1, 1))
        self.assertIn("mai nou", V.avertisment_factori(self.demand, [self.ruta]))
        os.utime(self.ruta, None)
        os.utime(self.demand, (1, 1))
        self.assertIsNone(V.avertisment_factori(self.demand, [self.ruta]))


if __name__ == "__main__":
    unittest.main()
