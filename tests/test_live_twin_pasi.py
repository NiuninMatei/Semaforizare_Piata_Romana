"""Starea geamănului pentru dispecerat (live_twin.py): pașii schimbării de fază și ecoul comenzii citite, fără SUMO; apoi bucla
adevărată, cu SUMO, într-un dosar temporar (sare peste, dacă SUMO sau rutele candidate lipsesc).

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_live_twin_pasi
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from romana.bridge import live_twin as L
from romana.control import pasi
from romana.control.faze import SemaforCuPietoni, info_v2


class _Semafor:
    def setRedYellowGreenState(self, _id, s):
        self.stare = s

    def getControlledLanes(self, _id):
        return []

    def getControlledLinks(self, _id):
        return []


class _Traci:
    def __init__(self):
        self.trafficlight = _Semafor()


def semafor() -> SemaforCuPietoni:
    info = info_v2()
    return SemaforCuPietoni(_Traci(), "romana", info["green_states"], info["phase_names"], info["pietoni"])


class TestComanda(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.f = self.d / "command.json"
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_fara_fisier_ruleaza_programul(self):
        self.assertEqual(L.citeste_comanda(self.f), {"mod": "program"})
        self.assertEqual(L.citeste_comanda(self.f, {"mod": "manual", "faza": 1}), {"mod": "program"})

    def test_comanda_scrisa_de_server(self):
        cmd = {"mod": "manual", "faza": 1, "timestamp": 1762612345.125}
        self.f.write_text(json.dumps(cmd), encoding="utf-8")
        self.assertEqual(L.citeste_comanda(self.f, {"mod": "fix"}), cmd)

    def test_fisierul_rescris_chiar_acum_lasa_comanda_de_dinainte(self):
        # serverul scrie fișierul fără înlocuire atomică: o citire în acel moment vede un text tăiat
        self.f.write_text('{"mod": "man', encoding="utf-8")
        inainte = {"mod": "manual", "faza": 1, "timestamp": 10.0}
        self.assertIs(L.citeste_comanda(self.f, inainte), inainte)
        self.assertEqual(L.citeste_comanda(self.f), {"mod": "program"})      # la prima citire nu e nicio comandă de păstrat
        self.f.write_text("[1, 2]", encoding="utf-8")                          # niciun JSON care nu e un obiect (aici, o listă) nu schimbă comanda
        self.assertIs(L.citeste_comanda(self.f, inainte), inainte)

    def test_o_comanda_pe_care_geamanul_n_o_poate_aplica_lasa_comanda_de_dinainte(self):
        # în ziua prezentării, fișierul se poate scrie și de mână: o greșeală nu schimbă modul și nu oprește geamănul
        inainte = {"mod": "manual", "faza": 1, "timestamp": 10.0}
        for gresita in ({}, {"faza": 1}, {"mod": "Manual"}, {"mod": "altceva"}, {"mod": ["manual"]}, {"mod": "manual", "faza": 5},
                        {"mod": "manual", "faza": -1}, {"mod": "manual", "faza": "1"}, {"mod": "manual", "faza": 1.0},
                        {"mod": "manual", "faza": True}, {"mod": "manual", "faza": None}):
            with self.subTest(gresita=gresita):
                self.f.write_text(json.dumps(gresita), encoding="utf-8")
                self.assertIs(L.citeste_comanda(self.f, inainte), inainte)
                self.assertEqual(L.citeste_comanda(self.f), {"mod": "program"})      # la prima citire, programul

    def test_comenzile_pe_care_geamanul_le_aplica(self):
        bune = [{"mod": m, "timestamp": 1.0} for m in L.MODURI_COMENZII]
        bune += [{"mod": "manual"}, {"mod": "manual", "faza": 0}, {"mod": "manual", "faza": 4}, {"mod": "fix", "faza": 9}]   # fără fază, faza de acum; faza contează doar la manual
        for buna in bune:
            with self.subTest(buna=buna):
                self.f.write_text(json.dumps(buna), encoding="utf-8")
                self.assertEqual(L.citeste_comanda(self.f, {"mod": "ai"}), buna)

    def test_fisierul_salvat_de_mana_in_alta_codificare(self):
        cmd = {"mod": "manual", "faza": 2, "timestamp": 5.0}
        for cod in ("utf-8-sig", "utf-16", "utf-16-le", "utf-32"):            # Notepad: UTF-8 cu BOM sau „Unicode”, adică UTF-16
            with self.subTest(cod=cod):
                self.f.write_bytes(json.dumps(cmd).encode(cod))
                self.assertEqual(L.citeste_comanda(self.f, {"mod": "ai"}), cmd)
        inainte = {"mod": "fix"}
        self.f.write_bytes('{"mod": "manual", "nota": "ă"}'.encode("cp1250"))   # nici UTF-8, nici altă codificare Unicode: ca un fișier tăiat
        self.assertIs(L.citeste_comanda(self.f, inainte), inainte)


class TestStarea(unittest.TestCase):
    def test_in_degajare_tinta_e_faza_urmatoare_si_comanda_are_ecou(self):
        c = semafor()
        for t in range(400):                       # E–V, până se poate schimba
            if t % pasi.CADENTA_S == 0:
                c.request(1)
            c.tick()
            if c.stage == "green" and c.current == 1 and c.can_switch():
                break
        c.request(0)                               # spre N–S: trecerile de pe Dacia se închid, deci întâi degajarea pietonilor
        self.assertTrue(pasi.in_degajare(c))
        st = L.stare_pasi(c, t + 1, {"mod": "manual", "faza": 0, "timestamp": 42.5})
        self.assertEqual(c.current, 1)
        self.assertEqual(st["pas"], "degajare")
        self.assertEqual(st["faza_tinta"], 0)       # formula veche din live_twin dădea aici 1, faza care se încheie
        self.assertEqual(st["pana_la_tinta_s"], 6 + 3 + 2)
        self.assertEqual(st["comanda_citita_ts"], 42.5)
        self.assertEqual(st["cadenta_s"], L.CADENTA_S)
        self.assertEqual(len(st["pana_la_faza_s"]), 5)
        json.dumps(st)                              # starea se scrie în sim_state.json

    def test_fara_timestamp_ecoul_e_gol(self):
        st = L.stare_pasi(semafor(), 0, {"mod": "program"})
        self.assertIsNone(st["comanda_citita_ts"])
        self.assertEqual((st["pas"], st["faza_tinta"]), ("verde", 0))


def lipseste_pentru_geaman() -> str | None:
    """Ce lipsește ca geamănul să pornească fără să genereze nimic în depozit: SUMO, TraCI sau rutele candidate (nu sunt în Git)."""
    from romana.common import DEMAND_DIR, load_json, sumo_binary

    try:
        sumo_binary("sumo")
    except SystemExit:
        return "SUMO nu e instalat aici"
    if importlib.util.find_spec("traci") is None:
        return "lipsește pachetul traci"
    cfg = load_json("demand_v2.json")
    rute = [DEMAND_DIR / "candidate.rou.xml", DEMAND_DIR / "candidate_bicycle.rou.xml", DEMAND_DIR / "candidate_pietoni.rou.xml"]
    if cfg.get("rute_pe_brate"):
        rute.append(DEMAND_DIR / cfg["rute_pe_brate"]["fisier"])
    lipsa = [p.name for p in rute if not p.exists()]
    return f"lipsesc rutele candidate ({', '.join(lipsa)}); se generează cu romana.bridge.build_demand" if lipsa else None


class TestBucla(unittest.TestCase):
    """Bucla adevărată a geamănului, cu SUMO, 250 s simulate cât de repede se poate, într-un dosar temporar (nu în outputs/live, unde
    poate rula geamănul dispeceratului): comenzile trec prin command.json și prin citeste_comanda, o dată cu fișierul tăiat la mijloc,
    iar secunda prezisă a verdelui cerut (pana_la_faza_s) se compară cu secunda reală."""

    # ce se scrie în command.json după starea cu acest timp_sim (bucla îl citește la pasul următor); la 40, un text tăiat la mijloc
    PLAN = {2: {"mod": "manual", "faza": 1, "timestamp": 1.0}, 40: '{"mod": "man', 41: {"mod": "manual", "faza": 1, "timestamp": 1.0},
            100: {"mod": "manual", "faza": 0, "timestamp": 2.0}, 170: {"mod": "manual", "faza": 2, "timestamp": 3.0}}
    FAZA = {1.0: 1, 2.0: 0, 3.0: 2}            # faza cerută de fiecare comandă, după timestamp

    @classmethod
    def setUpClass(cls):
        motiv = lipseste_pentru_geaman()
        if motiv:
            raise unittest.SkipTest(motiv)
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)
        try:                                   # calcul greu: la prioritate scăzută, ca să nu încurce colectarea camerei (SUMO o moștenește)
            import psutil

            proces = psutil.Process()
            cls.addClassCleanup(proces.nice, proces.nice())
            proces.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        except (ImportError, AttributeError):
            pass
        lacat = open(cls.d / "geaman.lock", "a+b")       # lacătul adevărat e în outputs/live; aici, unul în dosarul temporar
        cls.addClassCleanup(lacat.close)
        originala, cls.stari = L.stare_pasi, []

        def inregistreaza(ctrl, t, cmd):
            st = originala(ctrl, t, cmd)
            faza = ctrl.faza_afisata() if hasattr(ctrl, "faza_afisata") else ctrl.current
            cls.stari.append({"t": t, "faza": faza, "mod": cmd.get("mod"), **{k: st[k] for k in ("pas", "pana_la_faza_s", "comanda_citita_ts")}})
            if t in cls.PLAN:
                c = cls.PLAN[t]
                (cls.d / "command.json").write_text(c if isinstance(c, str) else json.dumps(c), encoding="utf-8")
            return st

        for nume, valoare in (("LIVE", cls.d), ("ia_lacatul", lambda dosar=None: lacat), ("stare_pasi", inregistreaza)):
            cls.addClassCleanup(setattr, L, nume, getattr(L, nume))
            setattr(L, nume, valoare)
        with contextlib.redirect_stdout(io.StringIO()):
            L.main(["--durata", "250", "--viteza", "0"])
        cls.final = json.loads((cls.d / "sim_state.json").read_text(encoding="utf-8"))

    def test_fisierul_taiat_lasa_comanda_de_dinainte(self):
        self.assertEqual([s["t"] for s in self.stari], list(range(1, 251)))
        rupt = next(s for s in self.stari if s["t"] == 41)       # starea pasului care a citit textul tăiat
        self.assertEqual((rupt["mod"], rupt["comanda_citita_ts"]), ("manual", 1.0))

    def test_secunda_prezisa_a_verdelui_cerut_e_cea_reala(self):
        verificate, gresite = 0, []
        for k, s in enumerate(self.stari):
            f = self.FAZA.get(s["comanda_citita_ts"])
            if f is None:
                continue
            j = next((m for m in range(k, len(self.stari)) if self.stari[m]["faza"] == f and self.stari[m]["pas"] == "verde"), None)
            if j is None or any(self.stari[m]["comanda_citita_ts"] != s["comanda_citita_ts"] for m in range(k, j + 1)):
                continue                                          # comanda s-a schimbat înainte de verdele cerut
            verificate += 1
            if self.stari[j]["t"] - s["t"] != s["pana_la_faza_s"][f]:
                gresite.append((s["t"], f, s["pana_la_faza_s"][f], self.stari[j]["t"] - s["t"]))
        self.assertEqual(gresite, [])
        self.assertGreater(verificate, 200)                       # toate cele trei comenzi, pe aproape toată durata

    def test_starea_scrisa_are_pasii_si_ecoul(self):
        st = self.final
        self.assertEqual((st["timp_sim"], st["mod"]), (250, "manual"))
        self.assertIn(st["pas"], ("verde", "degajare", "galben", "rosu"))
        self.assertEqual(len(st["pana_la_faza_s"]), 5)
        self.assertEqual(st["comanda_citita_ts"], 3.0)


if __name__ == "__main__":
    unittest.main()
