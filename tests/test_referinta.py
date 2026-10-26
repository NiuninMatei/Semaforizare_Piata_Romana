"""Teste pentru numărătoarea de referință și calibrarea camerei (date sintetice, fără imagini ale camerei).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from romana.vision import referinta as R
from romana.vision.calibrare_camera import Proiectie, cut, fit_camera


class ReferintaTest(unittest.TestCase):
    def test_regula_adnotatorilor(self):
        self.assertEqual(R.combine_annotators({"0": 10, "1": 30, "arbitru": 12}), 12)
        self.assertEqual(R.combine_annotators({"0": 10, "1": 12}), 11)           # diferență ≤ 2
        self.assertEqual(R.combine_annotators({"0": 40, "1": 46}), 43)           # diferență ≤ 15%
        self.assertIsNone(R.combine_annotators({"0": 10, "1": 14}))              # nici 2, nici 15%: neadnotată
        self.assertIsNone(R.combine_annotators({"0": 10}))

    def test_referinta_din_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            simplu, adn = Path(tmp) / "a.csv", Path(tmp) / "b.csv"
            simplu.write_text("tinta,bucata,numar\nV_magheru,b0,12\nV_magheru,1,7.5\n", encoding="utf-8")
            adn.write_text("țintă,bucată,adnotator,numar\nV_magheru,b0,0,10\nV_magheru,b0,1,12\n"
                           "V_magheru,b1,0,3\nV_magheru,b1,1,9\n", encoding="utf-8")
            self.assertEqual(R.load_reference(simplu), {("V_magheru", 0): 12.0, ("V_magheru", 1): 7.5})
            self.assertEqual(R.load_reference(adn), {("V_magheru", 0): 11.0})

    def test_factorii_si_intervalul(self):
        pairs = {"V_x": [(10, 8, "c1"), (12, 10, "c1"), (9, 8, "c2"), (11, 9, "c2")]}
        r = R.correction_factors(pairs, n_boot=500, seed=0)["V_x"]
        self.assertEqual(r["factor"], round(42 / 35, 2))
        self.assertLessEqual(r["ic90"][0], r["factor"])
        self.assertGreaterEqual(r["ic90"][1], r["factor"])
        self.assertEqual(r["pe_clipuri"]["c1"]["automat"], 18)
        self.assertEqual(r["pe_clipuri"]["c2"]["procent_prins"], 85.0)

    def test_tinta_fara_numarare_automata(self):
        v = [(10, 8, "c1"), (12, 10, "c1"), (9, 8, "c2")]
        fara = R.correction_factors({"P_x": [(5, 0, "c1"), (3, 0, "c2")], "V_x": v}, n_boot=300, seed=0)
        cu = R.correction_factors({"P_x": [(5, 4, "c1"), (3, 2, "c2")], "V_x": v}, n_boot=300, seed=0)
        self.assertIsNone(fara["P_x"]["factor"])
        self.assertEqual(fara["P_x"]["ic90"], [None, None])
        self.assertEqual(fara["V_x"], cu["V_x"])            # aceeași secvență aleatorie pentru țintele următoare

    def test_jurnalul_publicabil_al_clipului(self):
        import gzip
        import json

        from romana.vision.od_counter import PEDESTRIAN

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "clip" / "traiectorii"
            src.mkdir(parents=True)
            with gzip.open(src / "traiectorii_2026-10-26.jsonl.gz", "wt", encoding="utf-8") as f:
                for tip in ("passenger", PEDESTRIAN):
                    f.write(json.dumps({"t0": 100.0, "tip": tip, "p": [[0, 0.1, 0.5], [0.2, 0.2, 0.5]]}) + "\n")
            out = Path(tmp) / "publicat" / "traiectorii"
            self.assertEqual(R.publish_clip(src, out), 1)
            with gzip.open(out / "traiectorii_2026-10-26.jsonl.gz", "rt", encoding="utf-8") as f:
                self.assertEqual([json.loads(r)["tip"] for r in f], ["passenger"])
            with self.assertRaises(SystemExit):                 # jurnalul complet nu se suprascrie
                R.publish_clip(src, src)

    def test_lantul_offline_nu_scrie_in_data(self):
        import romana.vision.run_vision as rv

        old = rv.TRAJ_RAW_DIR, rv.LIVE_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp, mock.patch.object(rv, "main") as m:
                R.run_offline("clip.mp4", Path(tmp) / "o", 30, ["--minutes", "1"])
                self.assertEqual(rv.TRAJ_RAW_DIR, Path(tmp) / "o" / "traiectorii")
                self.assertEqual(rv.LIVE_DIR, Path(tmp) / "o" / "live")
                args = m.call_args[0][0]
                self.assertEqual(args[:2], ["--source", "clip.mp4"])
                self.assertEqual(args[args.index("--out") + 1], str(Path(tmp) / "o" / "numaratori"))
                self.assertEqual(args[-2:], ["--minutes", "1"])
        finally:
            rv.TRAJ_RAW_DIR, rv.LIVE_DIR = old

    def test_foi_de_contact_pe_un_clip_sintetic(self):
        import cv2

        with tempfile.TemporaryDirectory() as tmp:
            clip = str(Path(tmp) / "sintetic.mp4")
            w = cv2.VideoWriter(clip, cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 180))
            if not w.isOpened():
                self.skipTest("codecul mp4v nu este disponibil")
            for k in range(40):                                    # 4 s, un pătrat care se deplasează
                f = np.full((180, 320, 3), 60, np.uint8)
                cv2.rectangle(f, (5 * k, 80), (5 * k + 20, 100), (255, 255, 255), -1)
                w.write(f)
            w.release()
            tg = [{"id": "T", "tip": "vehicule", "decupaj": [0.0, 0.3, 1.0, 0.7], "linii": [[0.5, 0.3, 0.5, 0.7]]}]
            n = R.contact_sheets(tg, clip, Path(tmp) / "foi", chunk_s=2, dt=0.5, per_sheet=12, width=200)
            self.assertEqual(n, 2)
            self.assertEqual(sorted(p.name for p in (Path(tmp) / "foi" / "T").glob("*.jpg")), ["b0_f0.jpg", "b1_f0.jpg"])


class CalibrareCameraTest(unittest.TestCase):
    def test_omografia_se_recupereaza(self):
        H0 = np.array([[30.0, 5.0, 1600.0], [2.0, -10.0, 1000.0], [0.0005, -0.004, 1.0]])
        world = np.array([[1100 + x, 850 + y] for x in np.linspace(-30, 30, 7) for y in np.linspace(-20, 20, 5)])
        loc = world - world.mean(0)
        q = np.c_[loc, np.ones(len(loc))] @ H0.T
        px = q[:, :2] / q[:, 2:3]
        pts = [{"img_x": u / 3288, "img_y": v / 1850, "world_x": X, "world_y": Y}
               for (u, v), (X, Y) in zip(px, world)]
        model, det = fit_camera(pts, (3288, 1850))
        self.assertEqual(model["tip"], "H")
        self.assertLess(model["loo_median_px"], 0.5)
        pr = Proiectie(model)
        np.testing.assert_allclose(pr.lume_spre_img(world) * [3288, 1850], px, atol=0.5)
        np.testing.assert_allclose(pr.img_spre_lume(pr.lume_spre_img(world)), world, atol=1e-3)

    def test_taierea_unei_polilinii(self):
        seg = cut([[0, 0], [10, 0], [10, 10]], 5, 15)
        np.testing.assert_allclose(seg, [[5, 0], [10, 0], [10, 5]])
        self.assertIsNone(cut([[0, 0], [10, 0]], 12, 20))


if __name__ == "__main__":
    unittest.main()
