"""Stările de captură ale prezentării (capturi.PREZENTARE) poartă pașii controlerului real al semaforului.

Dacă duratele semaforului se schimbă (verdele minim, degajarea, galbenul, cadența), capturile ar arăta secunde care nu mai sunt
adevărate. Testul rejoacă aceeași comandă pe controler, în ordinea buclei din live_twin, și caută valorile lui în codul stărilor.
"""
import unittest

from romana.control import pasi
from romana.dashboard import capturi
from test_pasi import manual, semafor_corectat


def rejucare() -> dict:
    """Bd. Dacia (faza 1), cerut în comandă manuală la 1 s după ce Magheru–Catargiu a primit verde (la 501): pașii, pe secunde."""
    c = manual(semafor_corectat())
    t = 501
    stari = {t: (pasi.pasi_semafor(c, t), c.current)}
    for _ in range(56):
        if t % pasi.CADENTA_S == 0 and t >= 503:      # comanda e citită la 503; cererea ajunge la controler la cadența lui
            c.request(1)
        c.tick()
        t += 1
        stari[t] = (pasi.pasi_semafor(c, t), c.current)
    return stari


def lista(p: dict) -> str:
    return "pana_la_faza_s:[" + ",".join(str(x) for x in p["pana_la_faza_s"]) + "]"


class TestStarilePrezentarii(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stari = rejucare()

    def test_starea_de_baza(self):
        """__SIM_PASI: timp_sim 500, după 9 s de verde pe Magheru–Catargiu, în „Planul observat”."""
        c = semafor_corectat()
        for _ in range(9):
            c.tick()
        p = pasi.pasi_semafor(c, 500)
        d = p["durate_s"]
        self.assertEqual((c.current, p["pas"], p["pas_ramas_s"], p["faza_tinta"], p["pana_la_tinta_s"]), (0, "verde", None, 0, 0))
        self.assertIn(f"verde_min_s:{p['verde_min_s']},verde_max_s:{p['verde_max_s']},cadenta_s:{p['cadenta_s']},", capturi.SIMULARI)
        self.assertIn(f"citire_peste_s:{p['citire_peste_s']},{lista(p)},durate_s:{{galben:{d['galben']},rosu:{d['rosu']},degajare:{d['degajare']}}}",
                      capturi.SIMULARI)

    def test_verdele_cerut_vine_la_551(self):
        prima = min(t for t, (p, faza) in self.stari.items() if faza == 1 and p["pas"] == "verde")
        self.assertEqual(prima, 551)                  # la 48 s de la citirea comenzii (503), cât anunță banda în captură

    def test_inainte_de_cerere(self):
        for t, verde in ((502, 1), (503, 2)):
            p, faza = self.stari[t]
            self.assertEqual((faza, p["pas"], p["faza_tinta"], p["verde_min_s"]), (0, "verde", 0, 35))    # rămân valorile din __SIM_PASI
            self.assertIn(f"timp_sim:{t},verde_s:{verde},citire_peste_s:{p['citire_peste_s']},{lista(p)}", capturi.PASI_M3)

    def test_degajare_si_galben(self):
        for t, verde, bucata in ((541, 40, capturi.DEGAJARE), (546, 45, capturi.GALBEN)):
            p, faza = self.stari[t]
            self.assertEqual(faza, 0)
            self.assertIn(f'timp_sim:{t},verde_s:{verde},pas:"{p["pas"]}",pas_ramas_s:{p["pas_ramas_s"]},faza_tinta:{p["faza_tinta"]},'
                          f'pana_la_tinta_s:{p["pana_la_tinta_s"]},verde_min_s:{p["verde_min_s"]},citire_peste_s:{p["citire_peste_s"]},{lista(p)}', bucata)

    def test_aplicat(self):
        for t, verde in ((551, 0), (552, 1)):
            p, faza = self.stari[t]
            self.assertEqual((faza, p["pas"], p["pas_ramas_s"], p["pana_la_tinta_s"]), (1, "verde", None, 0))
            self.assertIn(f"timp_sim:{t},faza:1,faza_nume:__FAZE[1],verde_s:{verde},faza_tinta:{p['faza_tinta']},verde_min_s:{p['verde_min_s']},"
                          f"citire_peste_s:{p['citire_peste_s']},{lista(p)}", capturi.APLICAT)

    def test_starile_se_inlantuie(self):
        """Fiecare stare a comenzii le cuprinde pe cele dinaintea ei, iar toate pornesc de la panoul senzorului."""
        nume = ["m3_senzor", "m3_comanda_citita", "m3_comanda_degajare", "m3_comanda_galben", "m3_comanda_aplicata"]
        self.assertEqual(list(capturi.PREZENTARE), nume)
        for inainte, dupa in zip(nume, nume[1:]):
            self.assertTrue(capturi.PREZENTARE[dupa].startswith(capturi.PREZENTARE[inainte]))


if __name__ == "__main__":
    unittest.main()
