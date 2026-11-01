"""Teste pentru captura clipurilor temporare (`romana.vision.captura_clip`), fără rețea și fără imagini reale.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_captura_clip
"""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from romana.vision import captura_clip as cc

PLAYLIST = """#EXTM3U
#EXT-X-TARGETDURATION:7
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:{seq}
#EXT-X-PROGRAM-DATE-TIME:2026-11-01T10:57:10.000Z
#EXTINF:6.000,
a{seq}.ts
#EXTINF:6.000,
a{seq2}.ts
"""


class FluxFals:
    """Playlist care avansează la fiecare citire; `sar` lasă afară secvențe, ca o întrerupere."""

    def __init__(self, sar=()):
        self.seq = 100
        self.sar = set(sar)
        self.cerute = []

    def __call__(self, url, timeout=15):
        if url.endswith(".m3u8"):
            self.seq += 1
            while self.seq in self.sar:
                self.seq += 1
            return PLAYLIST.format(seq=self.seq, seq2=self.seq + 1).encode()
        self.cerute.append(url.rsplit("/", 1)[1])
        return b"x" * 10


class TestPlaylist(unittest.TestCase):
    def test_citeste_ore_si_secvente(self):
        sec, seg = cc.citeste_playlist(PLAYLIST.format(seq=5, seq2=6))
        self.assertEqual(sec, 5)
        self.assertEqual([s["seq"] for s in seg], [5, 6])
        self.assertEqual(seg[0]["cale"], "a5.ts")
        self.assertAlmostEqual(seg[1]["ora"] - seg[0]["ora"], 6.0)


class TestCaptura(unittest.TestCase):
    def _ruleaza(self, flux, durata, **kw):
        d = Path(tempfile.mkdtemp())
        ceas = iter(float(i) for i in range(100000))
        m = cc.captura("c", durata, url="https://x/y/mono.m3u8", dosar=d, descarca=flux, previzualizare=d / "nu_exista.jpg",
                       ceas=lambda: next(ceas), doarme=lambda _: None, **kw)
        return d, m

    def test_copiaza_pana_la_durata_fara_dubluri(self):
        flux = FluxFals()
        d, m = self._ruleaza(flux, 18)
        self.assertEqual(m["durata_s"], 18.0)
        self.assertEqual(len(flux.cerute), len(set(flux.cerute)))
        self.assertEqual((d / "c.ts").stat().st_size, 10 * len(flux.cerute))
        self.assertEqual(m["segmente_lipsa"], 0)
        self.assertTrue((d / "c.json").exists())

    def test_noteaza_segmentele_pierdute(self):
        _, m = self._ruleaza(FluxFals(sar=range(104, 110)), 30)
        self.assertGreater(m["segmente_lipsa"], 0)

    def test_nu_suprascrie_un_clip_existent(self):
        d = Path(tempfile.mkdtemp())
        (d / "c.ts").write_bytes(b"vechi")
        with self.assertRaises(SystemExit):
            cc.captura("c", 6, url="https://x/y/mono.m3u8", dosar=d, descarca=FluxFals(), previzualizare=d / "n.jpg")
        self.assertEqual((d / "c.ts").read_bytes(), b"vechi")

    def test_se_opreste_cand_fluxul_lipseste(self):
        def stricat(url, timeout=15):
            raise OSError("fără rețea")
        _, m = self._ruleaza(stricat, 18, maxim_fara_flux=30)
        self.assertEqual(m["segmente"], [])


class TestAliniere(unittest.TestCase):
    def test_gaseste_decalajul_cunoscut(self):
        rng = np.random.default_rng(1)
        n = 240
        imagini = rng.integers(0, 255, (n, 54, 96), dtype=np.uint8)
        timpi = np.arange(n) * 0.5                  # 2 imagini/s
        inceput = 1000.0
        decalaj = 23.5
        ore = inceput + decalaj + timpi[::2]        # colectarea vede aceleași cadre, cu 23,5 s mai târziu, o dată pe secundă
        mini = imagini[::2]
        scoruri = cc.potrivire(ore, mini, inceput, timpi, imagini, np.arange(0, 60.01, 0.5))
        self.assertEqual(min(scoruri, key=lambda x: x[1])[0], decalaj)


class TestSterge(unittest.TestCase):
    def test_sterge_imaginile_si_pastreaza_metadatele(self):
        d = Path(tempfile.mkdtemp())
        (d / "c.ts").write_bytes(b"v")
        (d / "c_mini.npz").write_bytes(b"m")
        (d / "c.json").write_text(json.dumps({"nume": "c"}), encoding="utf-8")
        (d / "c_foi").mkdir()
        (d / "c_foi" / "f.jpg").write_bytes(b"f")
        sterse = cc.sterge("c", d)
        self.assertEqual(sorted(sterse), ["c.ts", "c_foi", "c_mini.npz"])
        self.assertTrue((d / "c.json").exists())
        self.assertFalse((d / "c.ts").exists())


if __name__ == "__main__":
    unittest.main()
