"""Teste pentru numărarea O–D și a pietonilor (fără cameră: detecții sintetice).

Rulare:  set PYTHONPATH=src && python -m unittest discover tests
"""
import tempfile
import unittest
from pathlib import Path

from romana.bridge.od_estimation import estimate, load_counts
from romana.common import load_json
import cv2
import numpy as np

from romana.vision.od_counter import PERSON, ODCounter, is_rider, load_zones

W, H = 3288, 1850
CAR = 2
ZONES = {z.id: z for z in load_zones(load_json("camera.json"))}


def _puncte(zid):
    """Puncte din interiorul zonei, cu distanța până la margine (grilă fină în chenarul poligonului)."""
    z = ZONES[zid]
    poly = z.poly_norm.astype(np.float32)
    (x0, y0), (x1, y1) = poly.min(axis=0), poly.max(axis=0)
    pts = [(float(x), float(y)) for x in np.linspace(x0, x1, 60) for y in np.linspace(y0, y1, 60)]
    return [(p, cv2.pointPolygonTest(poly, p, True)) for p in pts if cv2.pointPolygonTest(poly, p, True) > 0]


def interior(zid):
    """Cel mai adânc punct al zonei (departe de margini) și distanța lui până la margine."""
    return max(_puncte(zid), key=lambda q: q[1])


def pe_sens(zid):
    """Două puncte din zonă, aliniate cu sensul de mers cerut (testele nu depind de coordonatele zonelor)."""
    (cx, cy), d = interior(zid)
    dx, dy = ZONES[zid].sens
    n = (dx * dx + dy * dy) ** 0.5
    k = 0.8 * d / n
    return (cx - k * dx, cy - k * dy), (cx + k * dx, cy + k * dy)


def traversare(zid):
    """Două puncte ale trecerii, cât mai departe unul de altul (pietonul o traversează)."""
    pts = [p for p, d in _puncte(zid) if d > 0.002]
    a = min(pts, key=lambda p: p[0] + p[1])
    b = max(pts, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
    return a, b


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

    def move(self, tid, cls, a, b, n=6):
        """Obiect care se deplasează de la a la b (coordonate normalizate) în n cadre."""
        for k in range(n):
            f = k / (n - 1)
            self.step([(tid, cls, (a[0] + f * (b[0] - a[0])) * W, (a[1] + f * (b[1] - a[1])) * H)])

    def walk(self, tid, a, b, n=6):
        self.move(tid, PERSON, a, b, n)

    def test_pieton_numarat_o_data_pe_trecere(self):
        # pieton care traversează trecerea de pe Magheru, apoi dispare
        self.walk(1, *traversare("trecere_magheru"))
        self.step([], n=5)
        self.assertEqual(dict(self.counter.peds), {("magheru", "trecere_magheru"): 1})

    def test_pieton_care_asteapta_la_bordura_nu_conteaza(self):
        x, y = interior("trecere_magheru")[0]
        self.step([(1, PERSON, x * W, y * H)], n=8)   # stă pe loc în zona trecerii
        self.step([], n=5)
        self.assertEqual(sum(self.counter.peds.values()), 0)

    def test_pieton_vazut_un_singur_cadru_nu_conteaza(self):
        x, y = interior("trecere_magheru")[0]
        self.step([(1, PERSON, x * W, y * H)])
        self.step([(1, PERSON, 0.5 * W, 0.3 * H)], n=3)   # în afara oricărei treceri
        self.step([], n=5)
        self.assertEqual(sum(self.counter.peds.values()), 0)

    def test_persoanele_nu_genereaza_viraje(self):
        # o persoană care trece prin zonele vehiculelor nu este numărată ca vehicul
        (x1, y1), _ = interior("magheru_in")
        (x2, y2), _ = interior("mendeleev_out")
        self.step([(1, PERSON, x1 * W, y1 * H)], n=3)
        self.step([(1, PERSON, x2 * W, y2 * H)], n=3)
        self.step([], n=5)
        self.assertEqual(sum(self.counter.arm_in.values()), 0)
        self.assertEqual(sum(self.counter.od.values()), 0)

    def test_viraj_vehicul(self):
        self.move(2, CAR, *pe_sens("magheru_in"))          # intră pe Magheru, spre piață
        self.move(2, CAR, *pe_sens("mendeleev_out"), n=11)  # iese pe Mendeleev
        self.step([], n=5)
        self.assertEqual(dict(self.counter.od), {("magheru", "mendeleev", "passenger"): 1})

    def test_sens_gresit_nu_conteaza(self):
        # vehicul care traversează zona de ieșire Mendeleev în sens invers (circulă pe inel) nu iese acolo
        self.move(5, CAR, *pe_sens("magheru_in"))
        a, b = pe_sens("mendeleev_out")
        ux, uy = a[0] - b[0], a[1] - b[1]                     # sensul invers, traversând toată zona
        self.move(5, CAR, (b[0] - 3 * ux, b[1] - 3 * uy), (a[0] + 3 * ux, a[1] + 3 * uy), n=12)
        self.step([], n=5)
        self.assertEqual(sum(self.counter.od.values()), 0)

    def test_banda_alaturata_nu_produce_intoarcere(self):
        # intră pe Magheru, atinge banda de ieșire alăturată, apoi iese pe Mendeleev
        self.move(3, CAR, *pe_sens("magheru_in"))
        a, b = pe_sens("magheru_out")
        self.move(3, CAR, b, a, n=2)                          # atinge magheru_out (în sens invers)
        self.move(3, CAR, *pe_sens("mendeleev_out"), n=11)
        # iese pe Magheru: banda de ieșire în sensul ei, apoi atinge banda de intrare
        self.move(4, CAR, *pe_sens("magheru_out"))
        x, y = interior("magheru_in")[0]
        self.move(4, CAR, (x, y), (x - 0.002, y), n=3)
        self.step([], n=5)
        self.assertEqual(dict(self.counter.od), {("magheru", "mendeleev", "passenger"): 1})
        self.assertEqual(sum(n for (a, _), n in self.counter.arm_in.items() if a == "magheru"), 1)
        self.assertEqual(sum(n for (a, _), n in self.counter.arm_out.items() if a == "magheru"), 1)
    def test_ciclist_nu_este_pieton(self):
        self.assertTrue(is_rider([100, 100, 140, 200], [[95, 150, 145, 215]]))
        self.assertFalse(is_rider([100, 100, 140, 200], [[400, 150, 445, 215]]))

    def test_csv_ajunge_in_cererea_de_pietoni(self):
        self.walk(1, *traversare("trecere_magheru"))
        self.step([], n=5)
        self.t[0] += 60
        self.counter.flush()
        files = sorted(Path(self.tmp.name).glob("numaratori_*.csv"))
        cfg = load_json("demand.json")
        recs = estimate(load_counts(files), cfg)
        ped = sum(r["pietoni_h"] * r["durata_s"] / 3600 for r in recs)
        self.assertAlmostEqual(ped, 1 * cfg["factor_extrapolare_pietoni"], places=0)


class RecountTest(unittest.TestCase):
    def test_renumararea_reproduce_numararea_live(self):
        from romana.vision.od_counter import Params
        from romana.vision.recount import recount

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            t = [1000.0]
            zones = load_zones(load_json("camera.json"))
            live = ODCounter(zones, interval_s=900, lost_after_frames=3, out_dir=tmp / "live",
                             clock=lambda: t[0], traj_dir=tmp / "traj")

            def step(dets, n=1):
                for _ in range(n):
                    t[0] += 0.2
                    live.update(dets, W, H)

            for tid, cls, (a, b), n in ((2, CAR, pe_sens("magheru_in"), 6), (2, CAR, pe_sens("mendeleev_out"), 11),
                                        (1, PERSON, traversare("trecere_magheru"), 6)):
                for k in range(n):
                    f = k / (n - 1)
                    step([(tid, cls, (a[0] + f * (b[0] - a[0])) * W, (a[1] + f * (b[1] - a[1])) * H)])
            step([], n=5)
            recs = recount(sorted((tmp / "traj").glob("*.jsonl.gz")), zones, 900, tmp / "re", Params())
            self.assertEqual(recs[0]["od"], dict(live.od))
            self.assertEqual(recs[0]["pietoni"], dict(live.peds))


if __name__ == "__main__":
    unittest.main()
