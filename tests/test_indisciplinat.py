"""Teste pentru generarea scenariilor cu participanți indisciplinați (pe fișiere .sumocfg temporare).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import tempfile
import unittest
from pathlib import Path

from romana.bridge.indisciplinat import generate, undisciplined_text

CFG = ('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\r\n<configuration>\r\n  <input>\r\n'
       '    <net-file value="../net/romana.net.xml" />\r\n'
       '    <route-files value="../demand/zi_test/passenger.rou.xml" />\r\n'
       '    <additional-files value="{add}" />\r\n  </input>\r\n'
       '  <time>\r\n    <begin value="0" />\r\n    <end value="4500" />\r\n  </time>\r\n</configuration>\r\n')


class IndisciplinatTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        p = self.dir / name
        p.write_bytes(text.encode("utf-8"))
        return p

    def test_inlocuieste_doar_fisierul_de_tipuri(self):
        src = self.write("zi_test.sumocfg", CFG.format(add="../demand/vtypes.add.xml,../demand/alt.add.xml"))
        rep = generate([src])
        self.assertEqual(rep["scrise"], ["indisciplinat_zi_test.sumocfg"])
        out = (self.dir / "indisciplinat_zi_test.sumocfg").read_bytes()
        expected = CFG.format(add="../demand/vtypes_indisciplinat.add.xml,../demand/alt.add.xml").encode("utf-8")
        self.assertEqual(out, expected)                     # restul identic, inclusiv terminațiile CRLF

    def test_fara_additional_files_sau_fara_vtypes_se_sare(self):
        self.assertIsNone(undisciplined_text("<configuration><input/></configuration>"))
        self.assertIsNone(undisciplined_text(CFG.format(add="../demand/alt.add.xml")))
        src = self.write("zi_fara.sumocfg", CFG.format(add="../demand/alt.add.xml"))
        rep = generate([src])
        self.assertEqual((rep["scrise"], rep["sarite"]), ([], ["zi_fara.sumocfg"]))
        self.assertFalse((self.dir / "indisciplinat_zi_fara.sumocfg").exists())

    def test_verificarea_nu_scrie_si_detecteaza_diferentele(self):
        src = self.write("zi_test.sumocfg", CFG.format(add="../demand/vtypes.add.xml"))
        self.assertEqual(generate([src], check=True)["lipsa"], ["indisciplinat_zi_test.sumocfg"])
        self.assertFalse((self.dir / "indisciplinat_zi_test.sumocfg").exists())
        generate([src])
        self.assertEqual(generate([src], check=True)["identice"], ["indisciplinat_zi_test.sumocfg"])
        self.write("indisciplinat_zi_test.sumocfg", CFG.format(add="../demand/vtypes.add.xml"))
        self.assertEqual(generate([src], check=True)["diferite"], ["indisciplinat_zi_test.sumocfg"])

    def test_scenariile_generate_nu_se_reproceseaza(self):
        src = self.write("zi_test.sumocfg", CFG.format(add="../demand/vtypes.add.xml"))
        generate([src])
        rep = generate(sorted(self.dir.glob("*.sumocfg")))
        self.assertEqual(rep["scrise"], ["indisciplinat_zi_test.sumocfg"])
        self.assertFalse(any(p.name.startswith("indisciplinat_indisciplinat") for p in self.dir.iterdir()))


if __name__ == "__main__":
    unittest.main()
