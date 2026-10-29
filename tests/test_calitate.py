"""Teste pentru semnul imaginii înghețate din `romana.vision.calitate` (§ 4.6) și pentru verdele pe treceri din
`romana.control.treceri` (date sintetice, fără SUMO).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import gzip
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from romana.control.treceri import verde_continuu
from romana.vision.calitate import inghetate, quality


def per15(miscare: dict[str, tuple[int, int]], durata: float = 4.0) -> dict[str, list]:
    """interval → [traiectorii, în mișcare, durate]; restul intervalelor dintre 02:00 și 06:00: 100 / 45."""
    out = {}
    for h in range(2, 6):
        for m in (0, 15, 30, 45):
            k = f"{h:02d}:{m:02d}"
            n, mis = miscare.get(k, (100, 45))
            out[k] = [n, mis, [durata] * n]
    return out


class TestImagineInghetata(unittest.TestCase):
    def test_inghetarea_e_gasita(self):
        p = per15({"03:45": (45, 8), "04:00": (40, 6), "04:15": (48, 9)})
        self.assertEqual([x[0] for x in inghetate(p)], ["03:45", "04:00", "04:15"])

    def test_scaderea_lina_nu_e_inghetare(self):
        # trafic care scade treptat, cu aceeași pondere de vehicule în mișcare: niciun interval suspect
        lin = {f"{h:02d}:{m:02d}": (100 - 5 * i, 45 - 2 * i)
               for i, (h, m) in enumerate((h, m) for h in range(2, 6) for m in (0, 15, 30, 45))}
        self.assertEqual(inghetate(per15(lin)), [])

    def test_putine_in_miscare_dar_putine_fixe_nu_e_inghetare(self):
        # un interval cu puține traiectorii, dar majoritatea în mișcare (trafic real, foarte rar)
        self.assertEqual(inghetate(per15({"04:00": (10, 8)})), [])

    def test_quality_numara_pe_15_minute(self):
        t0 = datetime(2026, 10, 28, 3, 50).timestamp()
        recs = [{"t0": t0, "tip": "passenger", "p": [[0, 0.5, 0.5], [1, 0.5, 0.5]]},          # fix
                {"t0": t0 + 1, "tip": "passenger", "p": [[0, 0.1, 0.5], [1, 0.3, 0.5]]},      # în mișcare
                {"t0": t0 + 2, "tip": "pieton", "p": [[0, 0.1, 0.9], [1, 0.4, 0.9]]}]        # pietonii nu contează
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "traiectorii_2026-10-28.jsonl.gz"
            with gzip.open(f, "wt", encoding="utf-8") as fh:
                fh.write("\n".join(json.dumps(r) for r in recs) + "\n")
            _, p = quality(f)
        self.assertEqual(p["03:45"][:2], [2, 1])


class TestVerdeContinuu(unittest.TestCase):
    STARI = ["Gr", "rr", "GG"]          # legătura 0: verde în fazele 0 și 2; legătura 1: doar în faza 2

    def test_fazele_consecutive_se_leaga_peste_ciclu(self):
        # fazele 2 → 0 sunt consecutive peste capătul ciclului: 12 + 5 (tranziția) + 12
        self.assertEqual(verde_continuu(self.STARI, 0, [12, 14, 12]), 29)

    def test_o_singura_faza(self):
        self.assertEqual(verde_continuu(self.STARI, 1, [12, 14, 12]), 12)

    def test_verde_in_toate_fazele(self):
        self.assertEqual(verde_continuu(["G", "G", "G"], 0, [12, 14, 12]), 12 + 14 + 12 + 3 * 5)


if __name__ == "__main__":
    unittest.main()
