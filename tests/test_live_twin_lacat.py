"""Lacătul geamănului în timp real: un al doilea geamăn, pornit dintr-o a doua lansare, nu pornește (M05)."""
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from romana.bridge import live_twin as L


@unittest.skipUnless(sys.platform == "win32", "lacătul folosește msvcrt, doar pe Windows")
class TestLacat(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_al_doilea_geaman_nu_ia_lacatul(self):
        primul = L.ia_lacatul(self.d)
        self.assertIsNotNone(primul)
        try:
            self.assertIsNone(L.ia_lacatul(self.d))
        finally:
            primul.close()

    def test_lacatul_se_elibereaza_la_inchidere(self):
        L.ia_lacatul(self.d).close()
        al_doilea = L.ia_lacatul(self.d)
        self.assertIsNotNone(al_doilea)
        al_doilea.close()

    def test_al_doilea_geaman_iese_cu_codul_3_inainte_de_sumo(self):
        primul = L.ia_lacatul(self.d)
        vechi = L.LIVE
        try:
            L.LIVE = self.d
            with unittest.mock.patch.object(L, "ia_lacatul", lambda dosar=self.d: None):
                with self.assertRaises(SystemExit) as e:
                    L.main(["--durata", "1"])
            self.assertEqual(e.exception.code, 3)
        finally:
            L.LIVE = vechi
            primul.close()


if __name__ == "__main__":
    unittest.main()
