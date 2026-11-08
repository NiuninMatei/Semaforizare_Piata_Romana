"""Pașii semaforului pentru dispecerat (src/romana/control/pasi.py), verificați pe controlerele reale, fără SUMO.

Oracolul rulează o copie a controlerului secundă cu secundă, în ordinea din live_twin (decizia la secundele multiple de 5,
apoi pasul de 1 s), cu o comandă manuală care cere mereu aceeași fază, și numără secundele până la verdele ei.
"""
import copy
import random
import unittest

from romana.control import pasi
from romana.control.faze import SemaforCuPietoni, info_v2
from romana.control.signals import SignalController


class TrafficLight:
    def setRedYellowGreenState(self, _id, s):
        self.stare = s

    def getControlledLanes(self, _id):
        return []

    def getControlledLinks(self, _id):
        return []


class Traci:
    def __init__(self):
        self.trafficlight = TrafficLight()


def semafor_corectat() -> SemaforCuPietoni:
    info = info_v2()
    return SemaforCuPietoni(Traci(), "romana", info["green_states"], info["phase_names"], info["pietoni"])


def semafor_vechi() -> SignalController:
    info = info_v2()
    return SignalController(Traci(), "romana", info["green_states"], info["phase_names"])


def ajuns(c, faza: int) -> bool:
    return pasi.pe_verde(c) and c.current == faza and not getattr(c, "scurta", False)


def manual(c):
    """Copia controlerului, ca după citirea unei comenzi manuale: live_twin oprește atunci trecerea singură prin etapa scurtă."""
    c = copy.copy(c)
    if hasattr(c, "via_scurta"):
        c.via_scurta = False
    return c


def oracol_faza(ctrl, timp_sim: int, faza: int, limita: int = 400) -> int:
    c = manual(ctrl)
    if ajuns(c, faza):
        return 0
    for i in range(timp_sim, timp_sim + limita):
        if i % pasi.CADENTA_S == 0:
            c.request(faza)
        c.tick()
        if ajuns(c, faza):
            return i + 1 - timp_sim
    raise AssertionError(f"faza {faza} n-a ajuns pe verde în {limita} s")


def oracol_tinta(ctrl) -> tuple[int, int | None, int]:
    """Fără nicio cerere nouă: secundele până la verdele țintei, secundele până se schimbă pasul și faza afișată la sosire."""
    c = manual(ctrl)
    pas0, pana_pas, s = pasi.pas(c), None, 0
    while not pasi.pe_verde(c):
        c.tick()
        s += 1
        if pana_pas is None and pasi.pas(c) != pas0:
            pana_pas = s
    return s, pana_pas, (len(c.greens) if getattr(c, "scurta", False) else c.current)


def plimbare(ctrl, secunde: int, samanta: int):
    """Stări variate ale controlerului, ca în live_twin: comenzi manuale ținute un timp, planuri fixe care cer în fiecare
    secundă (și spre etapa scurtă) și un agent pe două etape, care trece singur prin etapa scurtă."""
    rnd = random.Random(samanta)
    t, mod, comanda, pana = 0, "manual", 0, 0
    scurta_posibila = hasattr(ctrl, "stare_scurta")
    for _ in range(secunde):
        if t >= pana:
            mod = rnd.choice(["manual", "manual", "plan"] + (["agent"] if scurta_posibila else []))
            comanda, pana = rnd.randrange(ctrl.n), t + rnd.randint(1, 90)
        if scurta_posibila:
            ctrl.via_scurta = mod == "agent"
        if mod == "plan":
            if rnd.random() < 0.25:
                if scurta_posibila and rnd.random() < 0.4:
                    ctrl.request(2, scurta=True)
                else:
                    ctrl.request(rnd.randrange(ctrl.n))
        elif t % pasi.CADENTA_S == 0:
            ctrl.request(rnd.choice([0, 1]) if mod == "agent" else comanda)
        ctrl.tick()
        t += 1
        yield t


def ruleaza(ctrl, t: int, faza: int, pana_la) -> int:
    """Comanda manuală pe `faza`, ca în live_twin, până când `pana_la(ctrl)` e adevărat; întoarce `timp_sim`."""
    for _ in range(400):
        if pana_la(ctrl):
            return t
        if t % pasi.CADENTA_S == 0:
            ctrl.request(faza)
        ctrl.tick()
        t += 1
    raise AssertionError("starea cerută n-a apărut")


class TestOracol(unittest.TestCase):
    def verifica(self, ctrl, secunde: int, samanta: int) -> dict:
        vazute, maxim = set(), 0
        for t in plimbare(ctrl, secunde, samanta):
            p = pasi.pasi_semafor(ctrl, t)
            vazute.add(p["pas"] + ("_scurta" if getattr(ctrl, "scurta", False) or getattr(ctrl, "spre_scurta", False) else ""))
            for f in range(ctrl.n):
                asteptat = oracol_faza(ctrl, t, f)
                self.assertEqual(p["pana_la_faza_s"][f], asteptat, (t, f, p))
                maxim = max(maxim, asteptat)
            pana_tinta, pana_pas, tinta = oracol_tinta(ctrl)
            self.assertEqual(p["pana_la_tinta_s"], pana_tinta, (t, p))
            self.assertEqual(p["pas_ramas_s"], pana_pas, (t, p))
            self.assertEqual(p["faza_tinta"], tinta, (t, p))
            self.assertEqual(p["citire_peste_s"], (-t) % 5)
        return {"vazute": vazute, "maxim": maxim}

    def test_semaforul_corectat_pe_mii_de_stari(self):
        r = self.verifica(semafor_corectat(), 4000, 11)
        # toate pașii, și spre etapa scurtă, au apărut în probă
        for pas in ("verde", "degajare", "galben", "rosu", "verde_scurta", "galben_scurta", "rosu_scurta"):
            self.assertIn(pas, r["vazute"])
        # marginea: 10 s din schimbarea abia pornită (5 s de degajare + 3 + 2), 35 s de verde minim pe N–S,
        # cel mult 4 s până la decizie și 11 s de tranziție
        self.assertLessEqual(r["maxim"], 60)

    def test_semaforul_vechi_pe_mii_de_stari(self):
        r = self.verifica(semafor_vechi(), 2000, 12)
        self.assertNotIn("degajare", r["vazute"])
        # 4 s din galbenul abia pornit + roșul, 10 s de verde minim, cel mult 4 s până la decizie și 5 s de tranziție;
        # 19 s dacă schimbarea a pornit-o tot o comandă manuală, mai mult doar după un plan fix, care decide în orice secundă
        self.assertLessEqual(r["maxim"], 23)


class TestCazuri(unittest.TestCase):
    """Cazurile din harta comenzii: verdele minim pe N–S e 35 s (28 s întârzierea pietonilor + 7 s), degajarea 6 s."""

    def test_n_s_abia_pornit_dintr_o_comanda_manuala(self):
        c = semafor_corectat()
        t = ruleaza(c, 0, 1, lambda k: ajuns(k, 1))                  # întâi E–V
        t = ruleaza(c, t, 0, lambda k: ajuns(k, 0))                  # apoi N–S, tot manual
        self.assertEqual(c.green_time, 0)
        self.assertEqual(t % 5, 1)                                   # schimbarea manuală pornește la t ≡ 0, verdele vine după 11 s
        p = pasi.pasi_semafor(c, t)
        self.assertEqual(p["pana_la_faza_s"][1], 50)                 # 35 s + 4 s până la decizie + 6 + 3 + 2
        self.assertEqual(p["pana_la_faza_s"][2], 44)                 # spre pietoni nu se închide nicio trecere: fără degajare
        self.assertEqual(p["verde_min_s"], 35)
        self.assertEqual(p["pas"], "verde")

    def test_cazul_cel_mai_lung_schimbarea_spre_n_s_deja_pornita(self):
        c = semafor_corectat()
        t = ruleaza(c, 0, 1, lambda k: ajuns(k, 1))
        t = ruleaza(c, t, 0, lambda k: pasi.in_degajare(k))          # schimbarea spre N–S a început cu degajarea
        p = pasi.pasi_semafor(c, t)
        self.assertEqual((p["pas"], p["pas_ramas_s"], p["faza_tinta"], p["pana_la_tinta_s"]), ("degajare", 5, 0, 10))
        self.assertEqual(p["pana_la_faza_s"][1], 60)                 # nu se mai oprește: N–S întâi, 35 s, apoi înapoi pe E–V
        self.assertEqual(p["verde_min_s"], 35)

    def test_din_e_v_spre_n_s_si_spre_pietoni(self):
        c = semafor_corectat()
        t = ruleaza(c, 0, 1, lambda k: ajuns(k, 1))
        p = pasi.pasi_semafor(c, t)
        self.assertEqual(p["verde_min_s"], 10)
        self.assertEqual(p["pana_la_faza_s"][0], 25)                 # 10 s + 4 s + 6 + 3 + 2
        self.assertEqual(p["pana_la_faza_s"][2], 19)                 # 10 s + 4 s + 3 + 2
        self.assertEqual(p["pana_la_faza_s"][1], 0)

    def test_etapa_scurta(self):
        c = semafor_corectat()
        t = ruleaza(c, 0, 1, lambda k: ajuns(k, 1) and k.can_switch())
        c.request(2, scurta=True)                                   # ca planul observat: după E–V, etapa scurtă
        self.assertTrue(pasi.in_degajare(c))                         # trecerile de pe Dacia se închid întâi
        self.assertEqual(pasi.faza_tinta(c), len(c.greens))
        while not pasi.pe_verde(c):
            c.tick()
            t += 1
        p = pasi.pasi_semafor(c, t)
        self.assertEqual((p["faza_tinta"], p["verde_min_s"], p["pas"]), (5, 3, "verde"))
        self.assertNotEqual(p["pana_la_faza_s"][2], 0)               # etapa scurtă nu e faza de pietoni
        self.assertEqual(p["pana_la_faza_s"][2], oracol_faza(c, t, 2))

    def test_campurile(self):
        p = pasi.pasi_semafor(semafor_corectat(), 0)
        self.assertEqual(p["durate_s"], {"galben": 3, "rosu": 2, "degajare": 6})
        self.assertEqual((p["verde_max_s"], p["cadenta_s"], p["citire_peste_s"], p["pas_ramas_s"]), (90, 5, 0, None))
        self.assertEqual(len(p["pana_la_faza_s"]), 5)
        v = pasi.pasi_semafor(semafor_vechi(), 3)
        self.assertEqual((v["durate_s"]["degajare"], v["verde_min_s"], v["citire_peste_s"]), (0, 10, 2))


if __name__ == "__main__":
    unittest.main()
