"""Teste pentru semnul prelucrării încetinite din `romana.vision.calitate` (§ 4.6) și pentru verdele pe treceri din
`romana.control.treceri` (date sintetice, fără SUMO).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import gzip
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np

from romana.control.treceri import verde_continuu
from romana.vision.calitate import incetinite, pasi, quality


def per15(pas: dict[str, float], miscare: dict[str, tuple[int, int]] | None = None) -> dict[str, list]:
    """interval → [traiectorii, în mișcare, durate, pași]; între 02:00 și 06:00, implicit 100 de traiectorii (45 în
    mișcare), cu pași de 0,17 s (≈6 cadre/s)."""
    out = {}
    for h in range(2, 6):
        for m in (0, 15, 30, 45):
            k = f"{h:02d}:{m:02d}"
            n, mis = (miscare or {}).get(k, (100, 45))
            out[k] = [n, mis, [4.0] * n, [np.full(20, pas.get(k, 0.17))]]
    return out


class TestPrelucrareIncetinita(unittest.TestCase):
    def test_incetinirea_e_gasita(self):
        p = per15({"03:45": 0.69, "04:00": 0.67, "04:15": 0.68})
        self.assertEqual([x[0] for x in incetinite(p)], ["03:45", "04:00", "04:15"])

    def test_strada_goala_la_rata_normala_nu_e_incetinire(self):
        # puține vehicule în mișcare și multe traiectorii fixe, dar cadre la rata normală: trafic real, foarte rar
        self.assertEqual(incetinite(per15({}, {"04:00": (40, 3)})), [])

    def test_pasul_median_si_pasii_lungi(self):
        med, lungi = pasi([1, 1, [4.0], [np.array([0.17, 0.17]), np.array([0.7, 0.7, 0.7])]])
        self.assertAlmostEqual(med, 0.7)
        self.assertAlmostEqual(lungi, 0.6)

    def test_quality_numara_pe_15_minute(self):
        t0 = datetime(2026, 10, 28, 3, 50).timestamp()
        recs = [{"t0": t0, "tip": "passenger", "p": [[0, 0.5, 0.5], [1, 0.5, 0.5]]},          # fix
                {"t0": t0 + 1, "tip": "passenger", "p": [[0, 0.1, 0.5], [1, 0.3, 0.5]]},      # în mișcare
                {"t0": t0 + 2, "tip": "pieton", "p": [[0, 0.1, 0.9], [1, 0.4, 0.9]]}]        # pietonii nu contează
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "traiectorii_2026-10-28.jsonl.gz"
            with gzip.open(f, "wt", encoding="utf-8") as fh:
                fh.write("\n".join(json.dumps(r) for r in recs) + "\n")
            bloc = gzip.compress((json.dumps(recs[1]) + "\n").encode())
            with open(f, "ab") as fh:                       # jurnal în curs de scriere: ultimul bloc e incomplet
                fh.write(bloc[:len(bloc) // 2])
            _, p = quality(f)
        self.assertEqual(p["03:45"][:2], [2, 1])
        self.assertEqual(pasi(p["03:45"]), (1.0, 1.0))      # câte un pas de 1 s pe traiectorie


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
