"""Teste pentru numărarea O–D și a pietonilor (fără cameră: detecții sintetice).

Rulare:  set PYTHONPATH=src && python -m unittest discover tests
"""
import tempfile
import unittest
from pathlib import Path

from romana.bridge.od_estimation import estimate, load_counts
from romana.common import load_json
from romana.vision.od_counter import PERSON, ODCounter, is_rider, load_zones

W, H = 3288, 1850
CAR = 2


class ODCounterTest(unittest.TestCase):
    def setUp(self):
        self.t = [1000.0]
        self.tmp = tempfile.TemporaryDirectory()
        self.counter = ODCounter(load_zones(load_json("camera.json")), interval_s=60, lost_after_frames=3,
                                 out_dir=Path(self.tmp.name), clock=lambda: self.t[0])

    def tearDown(self):
        self.tmp.cleanup()

    def step(self, dets, n=1):
        for _ in range(n):
            self.t[0] += 0.2
            self.counter.update(dets, W, H)

    def test_pieton_numarat_o_data_pe_trecere(self):
        # pieton pe trecerea de pe Magheru 5 cadre, apoi dispare
        self.step([(1, PERSON, 0.30 * W, 0.75 * H)], n=5)
        self.step([], n=5)
        self.assertEqual(dict(self.counter.peds), {("magheru", "trecere_magheru"): 1})

    def test_pieton_vazut_un_singur_cadru_nu_conteaza(self):
        self.step([(1, PERSON, 0.30 * W, 0.75 * H)])
        self.step([(1, PERSON, 0.30 * W, 0.55 * H)], n=3)   # pe carosabil, în afara trecerii
        self.step([], n=5)
        self.assertEqual(sum(self.counter.peds.values()), 0)

    def test_persoanele_nu_genereaza_viraje(self):
        # o persoană care trece prin zonele vehiculelor nu este numărată ca vehicul
        self.step([(1, PERSON, 0.10 * W, 0.60 * H)], n=3)
        self.step([(1, PERSON, 0.07 * W, 0.50 * H)], n=3)
        self.step([], n=5)
        self.assertEqual(sum(self.counter.arm_in.values()), 0)
        self.assertEqual(sum(self.counter.od.values()), 0)

    def test_viraj_vehicul(self):
        self.step([(2, CAR, 0.10 * W, 0.60 * H)], n=3)      # magheru_in
        self.step([(2, CAR, 0.20 * W, 0.45 * H)], n=3)      # mendeleev_out
        self.step([], n=5)
        self.assertEqual(dict(self.counter.od), {("magheru", "mendeleev", "passenger"): 1})

    def test_ciclist_nu_este_pieton(self):
        self.assertTrue(is_rider([100, 100, 140, 200], [[95, 150, 145, 215]]))
        self.assertFalse(is_rider([100, 100, 140, 200], [[400, 150, 445, 215]]))

    def test_csv_ajunge_in_cererea_de_pietoni(self):
        self.step([(1, PERSON, 0.30 * W, 0.75 * H)], n=5)
        self.step([], n=5)
        self.t[0] += 60
        self.counter.flush()
        files = sorted(Path(self.tmp.name).glob("numaratori_*.csv"))
        cfg = load_json("demand.json")
        recs = estimate(load_counts(files), cfg)
        ped = sum(r["pietoni_h"] * r["durata_s"] / 3600 for r in recs)
        self.assertAlmostEqual(ped, 1 * cfg["factor_extrapolare_pietoni"], places=0)


if __name__ == "__main__":
    unittest.main()
