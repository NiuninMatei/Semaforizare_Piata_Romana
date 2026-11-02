"""Măsurarea programului real al semaforului (romana.vision.program_real), pe un semafor inventat, cu programul cunoscut."""
import unittest

import numpy as np

from romana.vision import program_real as P


def valuri(perioada, verde, debit, durata, decalaj=0.0, seed=1):
    """Vehicule care trec cu `debit` pe secundă doar în primele `verde` secunde din fiecare ciclu."""
    r = np.random.default_rng(seed)
    t = np.sort(r.uniform(0, durata, int(durata * debit)))
    return t[((t + decalaj) % perioada) < verde]


class TestProgramReal(unittest.TestCase):
    def test_gaseste_ciclul(self):
        T, z = P.ciclu(valuri(148.0, 75.0, 2.0, 600.0), 0.0, 600.0)
        self.assertAlmostEqual(T, 148.0, delta=4.0)
        self.assertGreater(z, 0.4)

    def test_fara_valuri_tarie_mica(self):
        r = np.random.default_rng(3)
        _, z = P.ciclu(np.sort(r.uniform(0, 600, 800)), 0.0, 600.0)
        self.assertLess(z, 0.15)

    def test_curgerea_se_masoara_chiar_daca_e_taiata_de_capatul_ciclului(self):
        for decalaj in (0.0, 40.0, 120.0):
            t = valuri(130.0, 60.0, 2.0, 7200.0, decalaj)
            c = P.curgere(P.pliaza(t, 0.0, 7200.0, 130.0), 130.0)
            self.assertAlmostEqual(c["curge_s"], 60.0, delta=5.0)
            self.assertAlmostEqual(c["varf_veh_s"], 2.0, delta=0.3)

    def test_intervalul_aliniaza_ferestrele_si_pastreaza_decalajul_dintre_brate(self):
        ev = {"magheru": valuri(150.0, 75.0, 2.0, 7200.0), "dacia_est": valuri(150.0, 40.0, 0.5, 7200.0, -90.0, seed=2)}
        r = P.interval(ev, 0.0, 7200.0)
        self.assertAlmostEqual(r["ciclu_s"], 150.0, delta=5.0)       # pe 10 minute încap doar 4 cicluri
        self.assertEqual(r["ferestre"], 12)
        self.assertAlmostEqual(r["brate"]["magheru"]["curge_s"], 75.0, delta=8.0)
        self.assertAlmostEqual(r["brate"]["dacia_est"]["curge_s"], 40.0, delta=8.0)
        dif = (r["brate"]["dacia_est"]["de_la_s"] - r["brate"]["magheru"]["de_la_s"]) % r["ciclu_s"]
        self.assertAlmostEqual(dif, 90.0, delta=8.0)

    def test_fereastra_cu_prea_putine_vehicule_nu_conteaza(self):
        self.assertEqual(P.interval({"magheru": np.array([1.0, 2.0, 3.0])}, 0.0, 600.0), {})


if __name__ == "__main__":
    unittest.main()
