"""Teste pentru statisticile pe perechi, programele pe tipuri de trafic, alegerea pe validare și comparația cu
fișierele publicate (date sintetice).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from romana.control.analiza import (BENZI_IMPLICITE, add_program, analyse, band_of, compare, load_results,
                                    parse_bands, parse_program, pivot)
from romana.control.validare import choice, compare_with, fix_choice_seeds, parse_seeds, published_files

SCEN = ["zi_X_linistit", "zi_X_pranz", "zi_X_varf"]


def date(factori: dict[str, float], seeds=range(1, 6)) -> pd.DataFrame:
    """Pierderea fiecărei strategii = pierderea planului fix × factorul ei (planul fix variază pe seed)."""
    rows = []
    for k, sc in enumerate(SCEN):
        for s in seeds:
            fix = 100.0 + 10 * k + s
            rows.append(("FIX", sc, s, fix))
            for m, f in factori.items():
                rows.append((m, sc, s, fix * (f[sc] if isinstance(f, dict) else f)))
    return pd.DataFrame(rows, columns=["model", "scenariu", "seed", "valoare"])


class StatisticiTest(unittest.TestCase):
    def test_strategie_mereu_mai_buna(self):
        p = pivot(date({"A": 0.9}))
        r = compare(p["A"], p["FIX"])
        self.assertEqual(r["n"], 15)
        self.assertEqual(r["mai_bun"], 15)
        self.assertAlmostEqual(r["diferenta_medie_pct"], -10.0)
        self.assertAlmostEqual(r["medie_pe_scenarii_pct"], -10.0)
        self.assertLess(r["p_t"], 1e-6)
        self.assertAlmostEqual(r["p_wilcoxon"], 2 / 2 ** 15, places=8)   # test exact: toate semnele negative

    def test_strategii_identice(self):
        p = pivot(date({"A": 1.0}))
        r = compare(p["A"], p["FIX"])
        self.assertEqual((r["mai_bun"], r["perechi_diferite"]), (0, 0))
        self.assertEqual((r["p_t"], r["p_wilcoxon"]), (1.0, 1.0))

    def test_media_pe_scenarii_cu_seeduri_diferite(self):
        df = date({"A": {"zi_X_linistit": 0.8, "zi_X_pranz": 1.0, "zi_X_varf": 1.0}})
        df = df[~((df["scenariu"] == "zi_X_linistit") & (df["seed"] > 1))]      # liniștit: un singur seed
        r = compare(*(pivot(df)[c] for c in ("A", "FIX")))
        self.assertEqual(r["n"], 11)
        self.assertAlmostEqual(r["diferenta_medie_pct"], -20.0 / 11)
        self.assertAlmostEqual(r["medie_pe_scenarii_pct"], -20.0 / 3)
        self.assertEqual(r["pe_scenarii_pct"]["zi_X_linistit"], -20.0)

    def test_perechile_incomplete_se_ignora(self):
        df = date({"A": 0.9})
        df = df[~((df["model"] == "A") & (df["seed"] == 5))]
        r = compare(*(pivot(df)[c] for c in ("A", "FIX")))
        self.assertEqual(r["n"], 12)


class ProgramTest(unittest.TestCase):
    def test_benzile_implicite(self):
        bands = parse_bands(BENZI_IMPLICITE)
        self.assertEqual([band_of(s, bands) for s in SCEN], ["lejer", "moderat", "greu"])
        self.assertEqual(band_of("indisciplinat_zi_2026-10-22_linistit_x0_8", bands), "lejer")

    def test_benzi_configurabile(self):
        bands = parse_bands("lejer=*linistit*,*dimineata;greu")
        self.assertEqual(band_of("zi_2026-10-25_dimineata", bands), "lejer")
        self.assertEqual(band_of("zi_2026-10-25_pranz", bands), "greu")

    def test_programul_ia_strategia_benzii(self):
        df = date({"A": 0.8, "B": 1.1})
        p = add_program(pivot(df), "P", parse_program("P=lejer:A,moderat:B,greu:FIX")[1], parse_bands(BENZI_IMPLICITE))
        for (sc, _), row in p.iterrows():
            self.assertEqual(row["P"], row[{"zi_X_linistit": "A", "zi_X_pranz": "B", "zi_X_varf": "FIX"}[sc]])
        r = compare(p["P"], p["FIX"])
        self.assertEqual((r["mai_bun"], r["perechi_diferite"]), (5, 10))      # vârful = chiar planul fix
        self.assertAlmostEqual(r["diferenta_medie_pct"], (-20 * 5 + 10 * 5) / 15)

    def test_analiza_cu_referinte_implicite(self):
        rows = analyse(date({"A": 0.9, "ACTUATED": 1.0}), None, None, ["P=lejer:A,moderat:A,greu:ACTUATED"])
        got = {(r["strategie"], r["referinta"]): r for r in rows}
        self.assertIn(("P", "FIX"), got)
        self.assertIn(("P", "ACTUATED"), got)
        self.assertEqual(got[("A", "ACTUATED")]["mai_bun"], 15)

    def test_formatul_evaluate(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "r.csv"
            pd.DataFrame({"strategie": ["fix_referinta", "actuated"], "scenariu": ["s", "s"], "seed": [1, 1],
                          "pierdere_totala_h": [10.0, 9.0], "alta": [0, 0]}).to_csv(f, index=False)
            df = load_results([f])
        self.assertEqual(list(df.columns), ["model", "scenariu", "seed", "valoare"])
        self.assertEqual(set(df["model"]), {"fix_referinta", "actuated"})


class ValidareTest(unittest.TestCase):
    def test_seeduri(self):
        self.assertEqual(parse_seeds("11-15"), [11, 12, 13, 14, 15])
        self.assertEqual(parse_seeds("1,3-4, 9"), [1, 3, 4, 9])

    def test_alegerea_scrie_seedurile_rulate(self):
        df = date({"A": 0.9, "B": 1.05}, seeds=range(11, 16)).rename(columns={"valoare": "pierdere_h"})
        ch = choice(df, SCEN)
        self.assertEqual(ch["ales"], "A")
        self.assertEqual(ch["seeduri_validare"], [11, 12, 13, 14, 15])
        self.assertAlmostEqual(ch["scor_mediu_procent"]["A"], -10.0)
        self.assertEqual(ch["scenarii"], SCEN)

    def test_corectarea_alegerilor(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            df = date({"A": 0.9}, seeds=range(11, 16)).rename(columns={"valoare": "pierdere_h"})
            df.to_csv(tmp / "validare_x.csv", index=False)
            (tmp / "validare_x_alegere.json").write_text(json.dumps(
                {"scor_mediu_procent": {"A": -10.0}, "ales": "A", "seeduri_validare": [11, 12, 13], "scenarii": SCEN}),
                encoding="utf-8")
            changed = fix_choice_seeds(tmp)
            d = json.loads((tmp / "validare_x_alegere.json").read_text(encoding="utf-8"))
            self.assertEqual(len(changed), 1)
            self.assertEqual(d["seeduri_validare"], [11, 12, 13, 14, 15])
            self.assertEqual(d["scor_mediu_procent"], {"A": -10.0})
            self.assertEqual(fix_choice_seeds(tmp), [])                     # a doua rulare nu mai schimbă nimic

    def test_comparatia_cu_fisierul_publicat(self):
        cols = ["model", "scenariu", "seed", "pierdere_h"]
        nou = pd.DataFrame([("FIX", "s", 1, 10.0), ("A", "s", 1, 9.0), ("A", "s", 2, 8.0)], columns=cols)
        with tempfile.TemporaryDirectory() as tmp:
            pub = Path(tmp) / "publicat.csv"
            pd.DataFrame([("FIX", "s", 1, 10.0), ("A", "s", 1, 9.5), ("B", "s", 1, 7.0)], columns=cols).to_csv(pub, index=False)
            c = compare_with(nou, pub)
        self.assertEqual((c["comune"], c["identice"], c["doar_rulare"], c["doar_publicat"]), (2, 1, 1, 1))
        self.assertAlmostEqual(c["dif_max_h"], 0.5)

    def test_fisierele_publicate_nu_se_suprascriu(self):
        with tempfile.TemporaryDirectory() as tmp:
            rez, alt = Path(tmp) / "rezultate", Path(tmp) / "outputs"
            rez.mkdir()
            (rez / "validare_x.csv").write_text("model\n", encoding="utf-8")
            (rez / "validare_x_alegere.json").write_text("{}", encoding="utf-8")
            self.assertEqual([p.name for p in published_files(rez / "validare_x.csv", rez)],
                             ["validare_x.csv", "validare_x_alegere.json"])
            self.assertEqual(published_files(rez / "validare_nou.csv", rez), [])        # fișier nou: permis
            self.assertEqual(published_files(alt / "validare_x.csv", rez), [])          # în afara docs/rezultate


if __name__ == "__main__":
    unittest.main()
