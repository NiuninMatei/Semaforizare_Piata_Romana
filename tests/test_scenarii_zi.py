"""Teste pentru alegerea ferestrelor din `romana.bridge.scenarii_zi`: golurile din date și intervalele excluse (date
sintetice, fără SUMO).

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import unittest

import pandas as pd

from romana.bridge.scenarii_zi import alege_ferestre, exclude, hourly_profile, intervale_date

ZI = "2026-10-29"


def t(hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{ZI} {hhmm}")


def numaratori(debit: dict[str, int], lipsa: tuple[str, ...] = ()) -> pd.DataFrame:
    """Numărătorile pe 15 min între 06:00 și 20:00 (intrări = ieșiri = debit / 4 vehicule; implicit 2 000 veh/h),
    fără intervalele din `lipsa`."""
    rows = []
    for s in pd.date_range(t("06:00"), t("20:00"), freq="15min", inclusive="left"):
        if f"{s:%H:%M}" in lipsa:
            continue
        n = debit.get(f"{s:%H:%M}", 2000) // 4
        for tip in ("intrare", "iesire"):
            rows.append({"inceput": s, "sfarsit": s + pd.Timedelta(minutes=15), "tip": tip, "numar": n})
    return pd.DataFrame(rows)


def atinge(fereastra, intervale) -> bool:
    a, b = fereastra
    return any(a <= x < b for x in intervale)


class TestGoluri(unittest.TestCase):
    def test_fereastra_glisanta_nu_sare_golul(self):
        # vârfuri de o parte și de alta a unui gol de o oră: fără grila completă, fereastra 08:30 + 08:45 + 10:00 +
        # 10:15 ar ieși vârful zilei (4 500 veh/h), deși nu e o oră reală
        df = numaratori({"08:30": 5000, "08:45": 5000, "10:00": 4000, "10:15": 4000},
                        lipsa=("09:00", "09:15", "09:30", "09:45"))
        f = alege_ferestre(hourly_profile(df), ZI)
        self.assertEqual(f["varf"], (t("08:00"), t("09:00")))
        gol = [t(x) for x in ("09:00", "09:15", "09:30", "09:45")]
        self.assertFalse(any(atinge(w, gol) for w in f.values()))

    def test_fereastra_fixa_cu_un_sfert_lipsa_iese(self):
        varf = {f"{h}:{m}": 5000 for h in ("15",) for m in ("00", "15", "30", "45")}
        self.assertIn("dimineata", alege_ferestre(hourly_profile(numaratori(varf)), ZI))
        self.assertNotIn("dimineata", alege_ferestre(hourly_profile(numaratori(varf, lipsa=("08:00",))), ZI))

    def test_ziua_fara_goluri_nu_se_schimba(self):
        # fără goluri, grila completă nu adaugă niciun interval
        prof = hourly_profile(numaratori({}))
        self.assertEqual(len(prof), 56)
        self.assertFalse(prof["echilibrat_veh_h"].isna().any())


class TestExcludere(unittest.TestCase):
    def test_specificatia(self):
        self.assertEqual(intervale_date(ZI, ["08:30-09:30"]), {t("08:30"), t("08:45"), t("09:00"), t("09:15")})
        self.assertEqual(intervale_date(ZI, [" 8:30 - 9:00 "]), {t("08:30"), t("08:45")})
        self.assertEqual(intervale_date(ZI, ["23:45-24:00"]), {t("23:45")})
        self.assertEqual(intervale_date(ZI, None), set())
        for gresit in ("08:10-09:00", "09:00-08:30", "08:30-08:30", "08:30:30-09:00", "08:30", "8.30-9.30",
                       "23:45-24:15"):
            with self.assertRaises(SystemExit, msg=gresit):
                intervale_date(ZI, [gresit])

    def test_nicio_ora_completa_da_un_mesaj_clar(self):
        prof = hourly_profile(numaratori({}))
        with self.assertRaises(SystemExit):
            alege_ferestre(exclude(prof, intervale_date(ZI, ["06:00-20:00"])), ZI)

    def test_varful_ocoleste_intervalele_excluse(self):
        df = numaratori({"08:30": 6000, "08:45": 6000, "09:00": 6000, "09:15": 6000, "15:00": 4000, "15:15": 4000,
                         "15:30": 4000, "15:45": 4000})
        excl = intervale_date(ZI, ["08:30-09:30"])
        f = alege_ferestre(exclude(hourly_profile(df), excl), ZI)
        self.assertEqual(f["varf"], (t("15:00"), t("16:00")))
        self.assertFalse(any(atinge(w, excl) for w in f.values()))
        self.assertIn("dimineata", f)          # 07:30–08:30 nu atinge intervalele excluse


if __name__ == "__main__":
    unittest.main()
