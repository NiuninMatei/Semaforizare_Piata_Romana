"""Teste pentru lanțul zilnic de prelucrare (`romana.lant_zilnic`): ordinea pașilor și comenzile, comparate cu lanțul din
30.10, oprirea la eșec, reluarea, excluderile, scenariile rămase, pașii rămași după o oprire din afară, rândurile dublate,
ziua implicită și bucla. Rularea comenzilor e înlocuită: nimic nu atinge datele reale, fișierele se scriu într-un proiect
temporar, iar procesele reale pornite aici sunt doar `python -c`.

Rulare:  set PYTHONPATH=src && python -m unittest discover -s tests
"""
import contextlib
import gzip
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import time as timp
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest import mock

from romana import lant_zilnic as L
from romana.common import COUNTS_DIR, ROOT

ZI = "2026-11-01"
RULEAZA = L.ruleaza
LANT_ACTIV = L.lant_activ
# scriptul lanțului din noaptea de 30.10 (copie locală, neversionată; lipsește pe alte calculatoare)
DOSAR_TEST29 = ROOT / "outputs" / "copie_scratchpad_2026-10-29"

# comenzile lanțului din 30.10, în ordine, luate din test29.py (test_copia_e_fidela_lui_test29 verifică asta când scriptul
# există), cu interpretorul, rădăcina și benzile înlocuite
LANT_30_10 = """
{PY} -m romana.vision.calitate {ROOT}/data/trajectories_brute/traiectorii_2026-10-29.jsonl.gz --out outputs/calitate_2026-10-29.csv --out-15min outputs/calitate_15min_2026-10-29.csv
{PY} -m romana.vision.recount --zi 2026-10-29
{PY} -m romana.vision.recount --zi 2026-10-29 --publica
{PY} -m romana.bridge.scenarii_zi --zi 2026-10-29 --exclude 08:30-09:00
{PY} -m romana.bridge.indisciplinat --scenarii {ROOT}/sumo/scenarios/zi_2026-10-29_*.sumocfg
{PY} -m romana.control.validare ACTUATED models/ppo_romana.zip models/ppo_romana_zn3.zip models/ppo_romana_cal.zip PLAN_12_14_12 PLAN_16_10_12 --scenarii indisciplinat_zi_2026-10-29_* --seeds 1-10 --fara-alegere --procese 11 --out outputs/validare/test_29_indisciplinat.csv
{PY} -m romana.control.validare ACTUATED models/ppo_romana.zip models/ppo_romana_zn3.zip models/ppo_romana_cal.zip PLAN_12_14_12 PLAN_16_10_12 --scenarii zi_2026-10-29_* --seeds 1-10 --fara-alegere --procese 11 --out outputs/validare/test_29_normal.csv
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte FIX REALIST ACTUATED --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte FIX REALIST ACTUATED --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte FIX REALIST
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte PLAN_12_14_12 TOD_FIX --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte PLAN_12_14_12 TOD_FIX --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --referinte PLAN_12_14_12 TOD_FIX
{PY} -m romana.control.decizie outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --confirma PLAN_12_14_12 --out outputs/validare/confirmare_2026-10-29.json
{PY} -m romana.control.decizie outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --out outputs/validare/decizie_2026-10-29.json
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --benzi {BENZI} --referinte FIX REALIST --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --benzi {BENZI} --referinte FIX REALIST --pe-scenarii
{PY} -m romana.control.analiza outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --benzi {BENZI} --referinte FIX REALIST TOD_DEBIT PLAN_12_14_12
{PY} -m romana.control.ocupare outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --autobuz 20 --out outputs/validare/test_29_persoane_20.csv
{PY} -m romana.control.decizie outputs/validare/test_29_persoane_20.csv --out outputs/validare/decizie_2026-10-29_persoane_20.json
{PY} -m romana.control.ocupare outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --autobuz 40 --out outputs/validare/test_29_persoane_40.csv
{PY} -m romana.control.decizie outputs/validare/test_29_persoane_40.csv --out outputs/validare/decizie_2026-10-29_persoane_40.json
{PY} -m romana.control.ocupare outputs/validare/test_29_indisciplinat.csv outputs/validare/test_29_normal.csv --autobuz 70 --out outputs/validare/test_29_persoane_70.csv
{PY} -m romana.control.decizie outputs/validare/test_29_persoane_70.csv --out outputs/validare/decizie_2026-10-29_persoane_70.json
"""
NUME_PASI = ["repara", "calitate", "recount", "publica", "scenarii", "indisciplinat", "test_indisciplinat", "test_normal",
             "analiza_indisciplinat", "analiza_normal", "analiza_reunite", "analiza_indisciplinat_planuri",
             "analiza_normal_planuri", "analiza_reunite_planuri", "confirmare", "decizie", "analiza_indisciplinat_debit",
             "analiza_normal_debit", "analiza_reunite_debit", "ocupare_20", "decizie_persoane_20", "ocupare_40",
             "decizie_persoane_40", "ocupare_70", "decizie_persoane_70", "totaluri"]
BENZI_PROBA = "lejer=zi_a,zi_b;moderat=zi_c;greu"
ANTET_CSV = "inceput,sfarsit,tip,origine,destinatie,vehicul,numar\n"


def rand_csv(t: datetime, minute: float = 15.0, numar: int = 3) -> str:
    s = t + timedelta(minutes=minute)
    return f"{t:%Y-%m-%d %H:%M:%S},{s:%Y-%m-%d %H:%M:%S},intrare,magheru,,passenger,{numar}\n"


def normal(cmd: list[str], benzi: str = L.BENZI) -> list[str]:
    """O comandă cu interpretorul, rădăcina și benzile înlocuite, ca în LANT_30_10."""
    out = ["{PY}"]
    for x in cmd[1:]:
        if x == benzi:
            x = "{BENZI}"
        elif x.startswith(str(ROOT)):
            x = "{ROOT}/" + x[len(str(ROOT)) + 1:].replace("\\", "/")
        out.append(x)
    return out


def inghetate() -> list[list[str]]:
    return [r.split() for r in LANT_30_10.strip().splitlines()]


def nume_noi(cmd: list[str]) -> list[str]:
    """Ieșirile lanțului din 30.10 sub numele din lanțul zilnic: test_29_* → test_2026-10-29_*."""
    return [x.replace("outputs/validare/test_29_", "outputs/validare/test_2026-10-29_") for x in cmd]


class TestRoluri(unittest.TestCase):
    """Rolurile zilelor noi (§ 9.11): ziua de validare are seed-urile ei, iar zilele de test rămân fără simulări până la desigilare."""

    @staticmethod
    def _seeduri(zi, **kw):
        cmd = [p.comanda for p in L.pasi(zi, **kw) if p.nume.startswith("test_")]
        return {c[c.index("--seeds") + 1] for c in cmd}

    def test_antrenare_pe_seedurile_de_test(self):
        self.assertEqual(self._seeduri("2026-11-02"), {"1-10"})

    def test_validare_pe_seedurile_ei(self):
        self.assertEqual(self._seeduri("2026-11-04"), {"11-15"})

    def test_zilele_de_test_sunt_sigilate(self):
        for zi in ("2026-11-05", "2026-11-06", "2026-11-07"):
            nume = [p.nume for p in L.pasi(zi)]
            self.assertIn("scenarii", nume)
            self.assertFalse([n for n in nume if n.startswith("test_") or n in ("decizie", "confirmare")], zi)

    def test_desigilarea_ruleaza_simularile(self):
        self.assertEqual(self._seeduri("2026-11-05", desigilat=True), {"1-10"})

    def test_o_zi_fara_rol_ramane_ca_inainte(self):
        self.assertEqual(self._seeduri("2026-10-29"), {"1-10"})

    def test_zilele_care_decid_nu_aleg_ferestre_pe_sferturi_incetinite(self):
        for zi in ("2026-11-04", "2026-11-05", "2026-11-07"):
            self.assertIn("--fara-incetinite", L.comanda_scenarii(zi))
        for zi in ("2026-11-01", "2026-10-29"):
            self.assertNotIn("--fara-incetinite", L.comanda_scenarii(zi))

    def test_o_zi_de_dupa_ultimul_rol_ramane_sigilata(self):
        self.assertTrue(L.sigilata("2026-11-08"))
        self.assertFalse(L.sigilata("2026-11-02"))
        self.assertFalse(L.sigilata("2026-10-29"))

    def test_zilele_fara_antrenare(self):
        for zi in ("2026-10-28", "2026-10-29", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07"):
            self.assertIn(zi, L.ZILE_FARA_ANTRENARE)
        for zi in ("2026-10-25", "2026-10-26", "2026-11-01", "2026-11-02", "2026-11-03"):
            self.assertNotIn(zi, L.ZILE_FARA_ANTRENARE)

    def test_desigilarea_cere_o_zi(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            L.main(["--desigileaza"])


class TestComenzi(unittest.TestCase):
    def test_ordinea_pasilor(self):
        self.assertEqual([p.nume for p in L.pasi(ZI)], NUME_PASI)

    def test_fara_simulari_se_opreste_dupa_scenarii(self):
        self.assertEqual([p.nume for p in L.pasi(ZI, fara_simulari=True)], NUME_PASI[:6])

    def test_comenzile_ca_in_lantul_din_30_10(self):
        # în plus față de 30.10: doar verificarea jurnalului, la început, și totalurile (Anexa A), la sfârșit
        p = L.pasi("2026-10-29", ["08:30-09:00"])
        self.assertEqual((p[0].nume, p[-1].nume), ("repara", "totaluri"))
        self.assertEqual(p[0].comanda[1:], ["-m", "romana.vision.repara", str(L.jurnal("2026-10-29"))])
        self.assertEqual(p[-1].comanda[1:], ["-m", "romana.control.totaluri", "outputs/validare/test_2026-10-29_indisciplinat.csv",
                                             "outputs/validare/test_2026-10-29_normal.csv"])
        generate = [normal(x.comanda) for x in p[1:-1]]
        for gen, vechi in zip(generate, inghetate(), strict=True):
            self.assertEqual(gen, nume_noi(vechi))

    @unittest.skipUnless((DOSAR_TEST29 / "test29.py").exists(), "test29.py nu există pe acest calculator")
    def test_copia_e_fidela_lui_test29(self):
        # test29.py însuși, rulat dintr-un dosar temporar, cu subprocess.run înlocuit: nu rulează nimic și nu scrie lângă el
        comenzi = []

        def fals(cmd, **k):
            comenzi.append(cmd)
            self.assertEqual(Path(k["cwd"]), ROOT)
            return mock.Mock(returncode=0)

        with tempfile.TemporaryDirectory() as d:
            shutil.copy(DOSAR_TEST29 / "test29.py", d)
            shutil.copy(DOSAR_TEST29 / "test28_extra.json", d)
            with (mock.patch("subprocess.run", fals), mock.patch("time.sleep"),
                  mock.patch("ctypes.windll.kernel32.SetPriorityClass")):
                try:
                    runpy.run_path(str(Path(d) / "test29.py"))
                except SystemExit:
                    self.skipTest("lipsește jurnalul din 29.10")
        benzi = next(c[c.index("--benzi") + 1] for c in comenzi if "--benzi" in c)
        self.assertEqual([normal(c, benzi) for c in comenzi], inghetate())

    def test_programele_ca_in_decizie(self):
        from romana.control.decizie import CANDIDATI, PROGRAME
        self.assertEqual([L.REALIST, L.TOD_DEBIT], PROGRAME)
        self.assertIn(L.CONFIRMATA, CANDIDATI)

    def test_strategiile_raportate_ca_in_test28_extra(self):
        self.assertEqual(L.RAPORTATE, {
            "strategii": ["PLAN_12_14_12", "PLAN_16_10_12"],
            "programe": ["TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12"],
            "referinte": ["PLAN_12_14_12", "TOD_FIX"]})
        if (DOSAR_TEST29 / "test28_extra.json").exists():
            extra = json.loads((DOSAR_TEST29 / "test28_extra.json").read_text(encoding="utf-8"))
            self.assertEqual(L.RAPORTATE, extra)

    def test_nimic_nu_se_scrie_in_docs(self):
        for p in L.pasi(ZI):
            self.assertFalse([x for x in p.comanda if x.replace("\\", "/").startswith("docs/")], p.nume)

    def test_iesirile_au_numele_zilei(self):
        c = {p.nume: p.comanda for p in L.pasi(ZI)}
        self.assertEqual(c["test_normal"][-1], f"outputs/validare/test_{ZI}_normal.csv")
        self.assertEqual(c["test_indisciplinat"][-1], f"outputs/validare/test_{ZI}_indisciplinat.csv")
        self.assertEqual(c["confirmare"][-1], f"outputs/validare/confirmare_{ZI}.json")
        self.assertEqual(c["decizie"][-1], f"outputs/validare/decizie_{ZI}.json")
        self.assertEqual(c["ocupare_40"][-1], f"outputs/validare/test_{ZI}_persoane_40.csv")

    def test_excluderile_merg_la_scenarii(self):
        scen = lambda ex: {p.nume: p.comanda for p in L.pasi(ZI, ex)}["scenarii"][3:]
        self.assertEqual(scen([]), ["--zi", ZI])
        self.assertEqual(scen(["08:00-09:15", "14:00-14:15"]),
                         ["--zi", ZI, "--exclude", "08:00-09:15", "--exclude", "14:00-14:15"])


class Cutie(unittest.TestCase):
    """Un proiect temporar (rădăcina, jurnalele, numărătorile, outputs), cu rularea comenzilor înlocuită."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)
        self.rulate, self.comenzi, self.coduri, self.intrerupe = [], {}, {}, {}
        self.ultim_csv = "23:45:00"
        self.durate = {}                # „HH:MM” → durata sfertului în CSV, în minute (0 = fără rând)
        self.dublate_mereu = False      # ora care se repetă la trecerea la ora de iarnă: renumărarea scrie mereu chei dublate
        self.fara_rezumat = False
        self.dupa_pas = {}              # numele pasului → ce se întâmplă în timp ce pasul se încheie (de ex. fluxul revine)
        self.existau = {}
        inlocuite = {"ROOT": self.d, "TRAJ_RAW_DIR": self.d / "brute", "COUNTS_DIR": self.d / "counts",
                     "DIR_LANT": self.d / "outputs" / "lant", "DIR_LOGURI": self.d / "outputs" / "logs",
                     "DIR_LIVE": self.d / "outputs" / "live",
                     "prioritate_scazuta": mock.Mock(return_value=(True, "prioritate de probă")),
                     "colectare_activa": mock.Mock(return_value=False),
                     "lant_activ": mock.Mock(return_value=False),
                     "ruleaza": self.ruleaza_fals}
        for nume, val in inlocuite.items():
            p = mock.patch.object(L, nume, val)
            p.start()
            self.addCleanup(p.stop)
        ecran = contextlib.redirect_stdout(io.StringIO())
        self.ecran = ecran.__enter__()
        self.addCleanup(ecran.__exit__, None, None, None)
        for x in ("brute", "counts", "outputs/logs"):
            (self.d / x).mkdir(parents=True)
        self.jurnal_sintetic(ZI)

    def jurnal_sintetic(self, zi: str) -> None:
        t = datetime.fromisoformat(f"{zi}T00:00:00").timestamp()
        recs = [{"t0": t + h * 3600 + 3590, "tip": "passenger", "p": [[0, 0.1, 0.1], [1, 0.2, 0.2]]} for h in range(24)]
        L.jurnal(zi).write_bytes(b"".join(gzip.compress((json.dumps(r) + "\n").encode()) for r in recs))

    def numaratori(self, zi: str) -> None:
        """CSV-ul zilei, ca după `recount`: sferturile până la `ultim_csv`, cu debitul crescând spre seară."""
        t, randuri = datetime.fromisoformat(f"{zi}T00:00:00"), [ANTET_CSV]
        z0 = t.date()
        while t.date() == z0 and f"{t:%H:%M:%S}" <= self.ultim_csv:
            durata = self.durate.get(f"{t:%H:%M}", 15.0)
            if durata:
                randuri.append(rand_csv(t, durata, 3 + t.hour))
                if self.dublate_mereu and t.hour == 3:
                    randuri.append(rand_csv(t, durata, 3 + t.hour))
            t += timedelta(minutes=15)
        (L.COUNTS_DIR / f"numaratori_{zi}.csv").write_text("".join(randuri), encoding="utf-8")

    def ruleaza_fals(self, cmd, cale, note=None, la_pornire=None):
        nume = cale.stem
        self.rulate.append(nume)
        self.comenzi[nume] = cmd
        self.existau[nume] = "--out" in cmd and (L.ROOT / cmd[cmd.index("--out") + 1]).exists()
        if nume in self.intrerupe:
            raise self.intrerupe.pop(nume)
        cod = self.coduri.get(nume, 0)
        if cod:
            return cod
        if "--out" in cmd:
            f = L.ROOT / cmd[cmd.index("--out") + 1]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({"benzi_analiza": BENZI_PROBA}) if nume == "decizie" else "rezultat", encoding="utf-8")
        if nume in ("recount", "recount_dublate"):
            self.numaratori(cmd[cmd.index("--zi") + 1])
        if nume == "scenarii" and not self.fara_rezumat:
            zi = cmd[cmd.index("--zi") + 1]
            f = L.ROOT / "sumo" / "demand" / f"zi_{zi}_rezumat.json"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({"zi": zi, "scenarii": [f"zi_{zi}_varf"]}), encoding="utf-8")
        if nume in self.dupa_pas:
            self.dupa_pas.pop(nume)()
        return 0

    def stare(self, zi: str = ZI) -> dict:
        return json.loads((L.DIR_LANT / zi / "stare.json").read_text(encoding="utf-8"))

    def jurnal_lant(self, zi: str = ZI) -> str:
        return (L.DIR_LANT / zi / "jurnal.txt").read_text(encoding="utf-8")

    def iesire(self, nume: str) -> Path:
        return self.d / "outputs" / "validare" / nume


class TestLant(Cutie):
    def test_toti_pasii_ruleaza_in_ordine(self):
        self.assertEqual(L.lant(ZI), 0)
        self.assertEqual(self.rulate, NUME_PASI)
        s = self.stare()
        self.assertEqual(s["rezultat"], "gata")
        self.assertEqual(list(s["pasi"]), NUME_PASI)
        for nume, rec in s["pasi"].items():
            self.assertEqual(rec["cod"], 0, nume)
            self.assertLessEqual(rec["inceput"], rec["sfarsit"])
        self.assertFalse((L.DIR_LANT / ZI / L.FISIER_BLOCARE).exists())
        self.assertFalse((L.DIR_LANT / ZI / "stare.tmp").exists())
        self.assertTrue(self.iesire(f"test_{ZI}_normal.csv").exists())
        self.assertIn("prioritate de probă", self.jurnal_lant())

    def test_lipseste_jurnalul(self):
        L.jurnal(ZI).unlink()
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, [])
        self.assertIn("LIPSEȘTE", self.stare()["rezultat"])

    def test_repara_cod_2_noteaza_si_continua(self):
        self.coduri["repara"] = 2
        self.assertEqual(L.lant(ZI), 0)
        self.assertEqual(self.rulate, NUME_PASI)
        self.assertIn("membri stricați", self.stare()["atentie"])
        self.assertIn("membri stricați", self.jurnal_lant())

    def test_repara_alt_cod_opreste(self):
        self.coduri["repara"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, ["repara"])
        self.assertIn("oprit", self.stare()["rezultat"])

    def test_calitate_esuata_opreste(self):
        self.coduri["calitate"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, ["repara", "calitate"])

    def test_recount_esuat_opreste_inainte_de_scenarii(self):
        self.coduri["recount"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, ["repara", "calitate", "recount"])
        self.assertIn("CSV-ul live", self.stare()["rezultat"])

    def test_cu_membri_stricati_renumararea_trebuie_sa_ajunga_la_capat(self):
        # un cititor care s-ar opri la membrul stricat ar ieși cu 0, iar restul zilei ar lipsi din CSV
        self.coduri["repara"] = 2
        self.ultim_csv = "14:00:00"
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, ["repara", "calitate", "recount"])
        rec = self.stare()["pasi"]["recount"]
        self.assertEqual(rec["cod"], L.COD_CAPAT)
        self.assertIn("14:00", rec["motiv"])
        self.assertIn("membrii stricați", self.stare()["rezultat"])

    def test_cu_membri_stricati_si_fara_csv_opreste(self):
        def fals(cmd, cale, note=None, la_pornire=None):
            self.rulate.append(cale.stem)
            return 2 if cale.stem == "repara" else 0
        with mock.patch.object(L, "ruleaza", fals):
            self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate[-1], "recount")

    def test_pe_un_jurnal_intreg_capatul_nu_se_verifica(self):
        # ultimele ore fără nicio numărătoare (de ex. imaginea camerei) nu opresc lanțul: ferestrele se aleg din restul zilei
        self.ultim_csv = "14:00:00"
        self.assertEqual(L.lant(ZI), 0)
        self.assertEqual(self.rulate, NUME_PASI)

    def test_scenarii_esuate_opresc(self):
        self.coduri["scenarii"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, NUME_PASI[:5])

    def test_scenarii_fara_rezumat_opresc(self):
        # fără rezumat nu se știe ce scenarii sunt valabile, iar `decizie` ar cădea abia după simulări
        self.fara_rezumat = True
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, NUME_PASI[:5])
        rec = self.stare()["pasi"]["scenarii"]
        self.assertEqual(rec["cod"], L.COD_REZUMAT)
        self.assertIn("rezumat", rec["motiv"])

    def test_publicarea_esuata_nu_opreste(self):
        self.coduri["publica"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, NUME_PASI)
        self.assertEqual(self.stare()["rezultat"], "cu_esecuri: publica")

    def test_fara_indisciplinat_merge_doar_ce_nu_depinde_de_el(self):
        self.coduri["indisciplinat"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, [*NUME_PASI[:6], "test_normal", "analiza_normal", "analiza_normal_planuri"])
        s = self.stare()["pasi"]
        self.assertIn("depinde", s["test_indisciplinat"]["sarit"])
        self.assertIn("depinde", s["totaluri"]["sarit"])

    def test_validarea_esuata_nu_lasa_un_rezultat_vechi_sa_fie_folosit(self):
        vechi = self.iesire(f"test_{ZI}_normal.csv")
        vechi.parent.mkdir(parents=True)
        vechi.write_text("rezultat vechi", encoding="utf-8")
        self.coduri["test_normal"] = 1
        self.assertEqual(L.lant(ZI), 1)
        self.assertFalse(self.existau["test_normal"])       # șters înainte de rulare
        self.assertFalse(vechi.exists())
        for pas in ("analiza_normal", "analiza_reunite", "confirmare", "decizie", "ocupare_40", "totaluri"):
            self.assertNotIn(pas, self.rulate)
        self.assertIn("analiza_indisciplinat", self.rulate)

    def test_fara_decizie_se_sar_analizele_pe_debit(self):
        self.coduri["decizie"] = 1
        self.assertEqual(L.lant(ZI), 1)
        for pas in ("analiza_normal_debit", "analiza_indisciplinat_debit", "analiza_reunite_debit"):
            self.assertNotIn(pas, self.rulate)
        self.assertIn("ocupare_20", self.rulate)

    def test_decizia_fara_benzi_nu_opreste_lantul(self):
        def fals(cmd, cale, note=None, la_pornire=None):
            cod = self.ruleaza_fals(cmd, cale, note)
            if cale.stem == "decizie":
                self.iesire(f"decizie_{ZI}.json").write_text("{}", encoding="utf-8")
            return cod
        with mock.patch.object(L, "ruleaza", fals):
            self.assertEqual(L.lant(ZI), 1)
        self.assertNotIn("analiza_normal_debit", self.rulate)
        self.assertIn("totaluri", self.rulate)

    def test_benzile_vin_din_decizie(self):
        L.lant(ZI)
        for pas in ("analiza_normal_debit", "analiza_indisciplinat_debit", "analiza_reunite_debit"):
            c = self.comenzi[pas]
            self.assertEqual(c[c.index("--benzi") + 1], BENZI_PROBA)
            self.assertNotIn(L.BENZI, c)

    def test_fara_simulari(self):
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertEqual(self.rulate, NUME_PASI[:6])
        self.assertEqual(self.stare()["rezultat"], "gata_fara_simulari")

    def test_ziua_curenta_nu_se_atinge_cat_ruleaza_colectarea(self):
        azi = date.today().isoformat()
        self.jurnal_sintetic(azi)
        L.colectare_activa.return_value = True
        self.assertEqual(L.lant(azi), 1)
        self.assertEqual(self.rulate, [])
        self.assertIn("live", self.stare(azi)["rezultat"])

    def test_ziua_curenta_cu_colectarea_oprita(self):
        azi = date.today().isoformat()
        self.jurnal_sintetic(azi)
        self.assertEqual(L.lant(azi, fara_simulari=True), 0)

    def test_al_doilea_lant_pe_aceeasi_zi_e_refuzat(self):
        d = L.DIR_LANT / ZI
        d.mkdir(parents=True)
        (d / L.FISIER_BLOCARE).write_text("4242", encoding="utf-8")
        L.lant_activ.return_value = True
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, [])
        self.assertEqual((d / L.FISIER_BLOCARE).read_text(encoding="utf-8"), "4242")
        L.lant_activ.assert_called_with(4242)

    def test_blocarea_ramasa_dupa_o_repornire_nu_opreste(self):
        d = L.DIR_LANT / ZI
        d.mkdir(parents=True)
        (d / L.FISIER_BLOCARE).write_text("4242", encoding="utf-8")
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)

    def test_comanda_care_nu_porneste_e_un_esec(self):
        with mock.patch.object(L, "ruleaza", side_effect=FileNotFoundError("python")):
            self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.stare()["pasi"]["repara"]["cod"], 1)

    def test_iesirea_care_nu_se_poate_sterge_nu_consuma_simularile(self):
        L.lant(ZI)
        self.rulate.clear()
        with mock.patch.object(Path, "unlink", side_effect=PermissionError("deschis în Excel")):
            self.assertEqual(L.lant(ZI), 1)
        self.assertNotIn("test_normal", self.rulate)
        self.assertEqual(self.stare()["pasi"]["test_normal"]["cod"], 1)


class TestReluare(Cutie):
    def test_reia_de_la_pasul_intrerupt(self):
        self.intrerupe["test_normal"] = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            L.lant(ZI)
        s = self.stare()
        self.assertEqual(s["rezultat"], "in_curs")
        self.assertIsNone(s["pasi"]["test_normal"]["cod"])
        self.assertIsNone(s["pasi"]["test_normal"]["sfarsit"])
        self.assertFalse((L.DIR_LANT / ZI / L.FISIER_BLOCARE).exists())
        inceput = s["pasi"]["calitate"]["inceput"]
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, NUME_PASI[NUME_PASI.index("test_normal"):])
        s = self.stare()
        self.assertEqual(s["rezultat"], "gata")
        self.assertEqual(s["pasi"]["calitate"]["inceput"], inceput)    # pasul sărit își păstrează momentele
        self.assertEqual(s["pasi"]["test_normal"]["cod"], 0)

    def test_dupa_o_pana_de_curent_rezultatul_vechi_al_pasului_intrerupt_se_sterge(self):
        L.lant(ZI)
        s = self.stare()
        s["pasi"]["test_normal"].update(cod=None, sfarsit=None)     # ce rămâne după o oprire bruscă în timpul validării
        (L.DIR_LANT / ZI / "stare.json").write_text(json.dumps(s), encoding="utf-8")
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate[0], "test_normal")
        self.assertFalse(self.existau["test_normal"])
        self.assertIn("analiza_normal", self.rulate)        # rezultatele lui se refac
        self.assertNotIn("analiza_indisciplinat", self.rulate)   # cele care nu depind de el, nu

    def test_fara_reia_se_reface_tot(self):
        L.lant(ZI)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI), 0)
        self.assertEqual(self.rulate, NUME_PASI)

    def test_reia_dupa_ce_totul_e_gata_nu_face_nimic(self):
        L.lant(ZI)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, [])
        self.assertEqual(self.stare()["rezultat"], "gata")

    def test_excludere_noua_reface_scenariile_si_ce_iese_din_ele(self):
        L.lant(ZI)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, ["08:00-09:15"], reia=True), 0)
        self.assertEqual(self.rulate, NUME_PASI[4:])
        self.assertIn("08:00-09:15", self.comenzi["scenarii"])

    def test_pas_esuat_fara_dependenti_se_reface_singur(self):
        self.coduri["publica"] = 1
        L.lant(ZI)
        del self.coduri["publica"]
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, ["publica"])
        self.assertEqual(self.stare()["rezultat"], "gata")

    def test_jurnalul_cu_membri_stricati_se_reverifica_fara_sa_refaca_restul(self):
        self.coduri["repara"] = 2
        L.lant(ZI)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, ["repara"])

    def test_pasii_sariti_prin_dependente_ruleaza_la_reluare(self):
        self.coduri["indisciplinat"] = 1
        L.lant(ZI)
        del self.coduri["indisciplinat"]
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate[:2], ["indisciplinat", "test_indisciplinat"])
        self.assertNotIn("test_normal", self.rulate)
        self.assertIn("totaluri", self.rulate)

    def test_stare_deteriorata_reface_tot(self):
        L.lant(ZI)
        (L.DIR_LANT / ZI / "stare.json").write_text('{"pasi": {"calit', encoding="utf-8")
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, NUME_PASI)
        self.assertIn("nu se poate citi", self.jurnal_lant())

    def test_iesire_disparuta_se_reface(self):
        L.lant(ZI)
        self.iesire(f"decizie_{ZI}.json").unlink()
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, ["decizie", "analiza_indisciplinat_debit", "analiza_normal_debit", "analiza_reunite_debit"])

    def test_fara_simulari_apoi_lantul_intreg(self):
        L.lant(ZI, fara_simulari=True)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, NUME_PASI[6:])

    def test_interpretor_scris_altfel_nu_reface_simularile(self):
        L.lant(ZI)
        self.rulate.clear()
        with mock.patch.object(L, "PY", "python"):
            self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertEqual(self.rulate, [])

    def test_excluderi_de_neinteles_opresc_inainte_de_orice_calcul(self):
        (L.DIR_LANT).mkdir(parents=True)
        (L.DIR_LANT / L.FISIER_EXCLUDERI).write_text('{"2026-11-01": ["08:07-09:00"]}', encoding="utf-8")
        self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.rulate, [])
        self.assertIn("grila", self.stare()["rezultat"])


class TestExcluderi(Cutie):
    def reporniri(self, zi: str, *randuri: tuple[str, str]) -> None:
        text = "oprire,repornire\n" + "".join(f"{a},{b}\n" for a, b in randuri)
        (L.DIR_LOGURI / f"reporniri_{zi}.csv").write_text(text, encoding="utf-8")

    def excluderi(self, zi: str = ZI, din_linie=()) -> list[str]:
        self.note = []
        return L.excluderi_zi(zi, din_linie, self.note.append)

    def test_fara_nimic(self):
        self.assertEqual(self.excluderi(), [])

    def test_repornirea_din_29_10_da_intervalul_din_test29(self):
        self.reporniri("2026-10-29", ("2026-10-29T08:33:21", "2026-10-29T08:46:21"))
        self.assertEqual(self.excluderi("2026-10-29"), ["08:30-09:00"])

    def test_repornirea_din_01_11_da_intervalul_cerut(self):
        self.reporniri(ZI, (f"{ZI}T08:02:00", f"{ZI}T09:04:10"))
        self.assertEqual(self.excluderi(), ["08:00-09:15"])

    def test_doua_reporniri(self):
        self.reporniri(ZI, (f"{ZI}T08:33:21", f"{ZI}T08:46:21"), (f"{ZI}T14:01:00", f"{ZI}T14:03:00"))
        self.assertEqual(self.excluderi(), ["08:30-09:00", "14:00-14:15"])

    def test_doua_reporniri_apropiate_se_unesc(self):
        self.reporniri(ZI, (f"{ZI}T08:33:21", f"{ZI}T08:46:21"), (f"{ZI}T09:01:00", f"{ZI}T09:02:00"))
        self.assertEqual(self.excluderi(), ["08:30-09:15"])

    def test_repornire_in_acelasi_sfert(self):
        self.reporniri(ZI, (f"{ZI}T10:16:00", f"{ZI}T10:17:00"))
        self.assertEqual(self.excluderi(), ["10:15-10:30"])

    def test_repornire_fix_la_inceputul_sfertului(self):
        self.reporniri(ZI, (f"{ZI}T10:10:00", f"{ZI}T10:15:00"))
        self.assertEqual(self.excluderi(), ["10:00-10:30"])

    def test_sfertul_de_la_miezul_noptii(self):
        # 23:52 → 00:03: pe prima zi, ultimul sfert (până la 24:00); pe a doua, primul sfert, oricare fișier ar avea rândul
        urm = "2026-11-02"
        self.reporniri(urm, (f"{ZI}T23:52:00", f"{urm}T00:03:00"))
        self.assertEqual(self.excluderi(ZI), ["23:45-24:00"])
        self.assertEqual(self.excluderi(urm), ["00:00-00:15"])
        (L.DIR_LOGURI / f"reporniri_{urm}.csv").unlink()
        self.reporniri(ZI, (f"{ZI}T23:52:00", f"{urm}T00:03:00"))
        self.assertEqual(self.excluderi(ZI), ["23:45-24:00"])
        self.assertEqual(self.excluderi(urm), ["00:00-00:15"])

    def test_repornire_in_ultimul_sfert(self):
        self.reporniri(ZI, (f"{ZI}T23:47:00", f"{ZI}T23:55:00"))
        self.assertEqual(self.excluderi(ZI), ["23:45-24:00"])
        self.assertEqual(self.excluderi("2026-11-02"), [])     # ziua următoare nu e atinsă

    def test_repornire_fix_la_miezul_noptii(self):
        urm = "2026-11-02"
        self.reporniri(ZI, (f"{ZI}T23:58:00", f"{urm}T00:00:00"))
        self.assertEqual(self.excluderi(ZI), ["23:45-24:00"])
        self.assertEqual(self.excluderi(urm), ["00:00-00:15"])

    def test_oprire_peste_o_zi_intreaga(self):
        urm = "2026-11-02"
        poi = "2026-11-03"
        self.reporniri(poi, (f"{ZI}T22:00:00", f"{poi}T01:00:00"))
        self.assertEqual(self.excluderi(urm), ["00:00-24:00"])
        self.assertEqual(self.excluderi(ZI), [])    # fișierul e la două zile distanță: nu se mai citește

    def test_oprire_fara_repornire(self):
        self.reporniri(ZI, (f"{ZI}T08:33:00", ""))
        self.assertEqual(self.excluderi(ZI), ["08:30-24:00"])
        self.assertEqual(self.excluderi("2026-11-02"), [])     # ziua următoare are jurnal, deci colectarea a repornit

    def test_repornire_fara_oprire(self):
        self.reporniri(ZI, ("", f"{ZI}T09:04:00"))
        self.assertEqual(self.excluderi(ZI), ["09:00-09:15"])
        self.assertTrue(any("fără oprire" in n for n in self.note))

    def test_randurile_de_neinteles_se_noteaza(self):
        self.reporniri(ZI, ("ieri", f"{ZI}T09:04:00"), (f"{ZI}T10:00:00", f"{ZI}T09:00:00"), ("", ""),
                       (f"{ZI}T11:01:00", f"{ZI}T11:02:00"))
        self.assertEqual(self.excluderi(), ["11:00-11:15"])
        self.assertEqual(sum("rând ignorat" in n for n in self.note), 3)

    def test_ora_cu_fractiuni_si_decalaj(self):
        self.reporniri(ZI, (f"{ZI}T08:33:21.250000+02:00", f"{ZI}T08:46:21.5+02:00"))
        self.assertEqual(self.excluderi(), ["08:30-09:00"])

    def test_cele_trei_surse_se_unesc_fara_dubluri(self):
        self.reporniri(ZI, (f"{ZI}T08:33:21", f"{ZI}T08:46:21"), (f"{ZI}T08:33:21", f"{ZI}T08:46:21"))
        L.DIR_LANT.mkdir(parents=True)
        (L.DIR_LANT / L.FISIER_EXCLUDERI).write_text(
            json.dumps({ZI: ["08:30-09:00", "20:00-20:30"], "2026-11-02": ["03:00-04:00"]}), encoding="utf-8")
        self.assertEqual(self.excluderi(din_linie=["8:30-9:00", "20:15-21:00", "12:00-12:15"]),
                         ["08:30-09:00", "12:00-12:15", "20:00-21:00"])

    def test_excluderi_json_cu_bom(self):
        L.DIR_LANT.mkdir(parents=True)
        (L.DIR_LANT / L.FISIER_EXCLUDERI).write_bytes(b"\xef\xbb\xbf" + json.dumps({ZI: ["08:00-09:15"]}).encode())
        self.assertEqual(self.excluderi(), ["08:00-09:15"])

    def test_valorile_gresite_ridica_eroare(self):
        for gresit in ("08:07-09:00", "09:00-08:00", "09:00", "08:00-24:15", "08:60-09:00", "08:00-08:00"):
            with self.assertRaises(ValueError, msg=gresit):
                L.minute_interval(gresit)

    def test_excluderi_json_stricat_ridica_eroare(self):
        L.DIR_LANT.mkdir(parents=True)
        for text in ('{"2026-11-01": ', '["08:00-09:15"]', '{"2026-11-01": "08:00-09:15"}'):
            (L.DIR_LANT / L.FISIER_EXCLUDERI).write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError, msg=text):
                self.excluderi()

    def test_rezultatul_e_acceptat_de_scenarii_zi(self):
        import pandas as pd

        from romana.bridge.scenarii_zi import intervale_date
        for text, n in (("23:45-24:00", 1), ("00:00-00:15", 1), ("08:30-09:00", 2), ("00:00-24:00", 96)):
            set_ = intervale_date(ZI, [text])
            self.assertEqual(len(set_), n)
            a, b = L.minute_interval(text)
            self.assertEqual(L.uneste([(a, b)]), [text])
            self.assertEqual(min(set_), pd.Timestamp(ZI) + pd.Timedelta(minutes=a))

    def test_excluderile_ajung_in_comanda_scenariilor(self):
        self.reporniri(ZI, (f"{ZI}T14:01:00", f"{ZI}T14:03:00"))
        self.assertEqual(L.lant(ZI, ["08:00-09:15"], fara_simulari=True), 0)
        c = self.comenzi["scenarii"]
        self.assertEqual(c[3:], ["--zi", ZI, "--exclude", "08:00-09:15", "--exclude", "14:00-14:15"])
        self.assertEqual(self.stare()["excluderi"], ["08:00-09:15", "14:00-14:15"])


class TestGrila(Cutie):
    """Golurile pe care le arată singură grila numărătorilor, fără rând în reporniri și fără excluderi.json."""

    def csv(self, randuri: dict[str, float]) -> None:
        text = ANTET_CSV + "".join(rand_csv(datetime.fromisoformat(f"{ZI}T{o}:00"), m) for o, m in randuri.items())
        (L.COUNTS_DIR / f"numaratori_{ZI}.csv").write_text(text, encoding="utf-8")

    @staticmethod
    def sferturi(de_la: str, pana_la: str) -> dict[str, float]:
        z0 = datetime.fromisoformat(f"{ZI}T00:00:00")
        a, b = (int(x[:2]) * 60 + int(x[3:]) for x in (de_la, pana_la))
        return {f"{z0 + timedelta(minutes=m):%H:%M}": 15.0 for m in range(a, b, 15)}

    def goluri(self) -> list[str]:
        return L.uneste(L.goluri_grila(ZI))

    def test_zi_intreaga(self):
        self.csv(self.sferturi("00:00", "24:00"))
        self.assertEqual(self.goluri(), [])

    def test_forma_din_29_10_da_excluderea_din_lantul_de_atunci(self):
        # oprire 08:33, repornire 08:46: 08:15 e întreg, 08:30 are 3,4 min, 08:45 are durata întreagă, dar date parțiale
        self.csv({**self.sferturi("00:00", "08:30"), "08:30": 3.4, **self.sferturi("08:45", "24:00")})
        self.assertEqual(self.goluri(), ["08:30-09:00"])

    def test_forma_din_01_11(self):
        # jurnalul începe în sfertul 08:15 (până la 08:27:39), oprire până la 09:04; 08:15 încă trece de filtrul de 12 min
        self.csv({"08:15": 12.65, **self.sferturi("09:00", "13:00")})
        self.assertEqual(self.goluri(), ["08:15-09:15"])

    def test_primul_sfert_al_zilei_are_date_partiale(self):
        self.csv(self.sferturi("09:00", "24:00"))
        self.assertEqual(self.goluri(), ["09:00-09:15"])

    def test_oprire_si_repornire_in_sferturi_vecine(self):
        # niciun sfert gol: se vede doar după durata sfertului opririi
        self.csv({**self.sferturi("00:00", "08:15"), "08:15": 13.0, **self.sferturi("08:30", "24:00")})
        self.assertEqual(self.goluri(), ["08:15-08:45"])

    def test_oprire_definitiva(self):
        self.csv({**self.sferturi("00:00", "18:00"), "18:00": 13.0})
        self.assertEqual(self.goluri(), ["18:00-18:15"])
        self.csv({**self.sferturi("00:00", "18:00"), "18:00": 3.0})      # sub filtrul de 12 min: nu intră în grilă
        self.assertEqual(self.goluri(), [])

    def test_doua_goluri(self):
        self.csv({**self.sferturi("00:00", "08:30"), "08:30": 3.0, **self.sferturi("08:45", "14:00"), "14:00": 5.0,
                  **self.sferturi("14:30", "24:00")})
        self.assertEqual(self.goluri(), ["08:30-09:00", "14:00-14:45"])

    def test_sfertul_de_la_miezul_noptii(self):
        self.csv({**self.sferturi("00:00", "23:45"), "23:45": 13.0})
        self.assertEqual(self.goluri(), ["23:45-24:00"])

    def test_oprire_si_repornire_in_acelasi_sfert_nu_se_vad(self):
        # limita declarată: pe acestea le prinde doar reporniri_<zi>.csv sau excluderi.json
        self.csv(self.sferturi("00:00", "24:00"))
        self.assertEqual(self.goluri(), [])

    @unittest.skipUnless((COUNTS_DIR / "numaratori_2026-10-29.csv").exists(), "numărătorile din 29.10 lipsesc")
    def test_zilele_reale(self):
        # doar citire; pe 29.10, exact excluderea din lanțul din 30.10, fără s-o dea cineva de mână
        with mock.patch.object(L, "COUNTS_DIR", COUNTS_DIR):
            self.assertEqual(L.uneste(L.goluri_grila("2026-10-29")), ["08:30-09:00"])
            self.assertEqual(L.goluri_grila("2026-10-28"), [])

    def test_lantul_adauga_golurile_in_comanda_scenariilor(self):
        self.durate["08:30"] = 3.4
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertEqual(self.comenzi["scenarii"][3:], ["--zi", ZI, "--exclude", "08:30-09:00"])
        s = self.stare()
        self.assertEqual((s["excluderi"], s["excluderi_grila"]), (["08:30-09:00"], ["08:30-09:00"]))
        self.assertIn("[atenție] goluri în grila", self.jurnal_lant())

    def test_fara_nicio_excludere_data_comanda_e_cea_din_30_10(self):
        zi = "2026-10-29"
        self.jurnal_sintetic(zi)
        self.durate["08:30"] = 3.4
        self.assertEqual(L.lant(zi, fara_simulari=True), 0)
        self.assertEqual(normal(self.comenzi["scenarii"]), inghetate()[3])

    def test_golurile_se_unesc_cu_celelalte_surse(self):
        self.durate["08:30"] = 3.4
        self.assertEqual(L.lant(ZI, ["08:00-08:30", "20:00-20:15"], fara_simulari=True), 0)
        self.assertEqual(self.comenzi["scenarii"][3:], ["--zi", ZI, "--exclude", "08:00-09:00", "--exclude", "20:00-20:15"])

    def test_gol_deja_exclus_nu_mai_e_o_atentie(self):
        self.durate["08:30"] = 3.4
        self.assertEqual(L.lant(ZI, ["08:30-09:00"], fara_simulari=True), 0)
        self.assertEqual(self.comenzi["scenarii"][3:], ["--zi", ZI, "--exclude", "08:30-09:00"])
        self.assertNotIn("[atenție] goluri în grila", self.jurnal_lant())

    def test_reluarea_nu_reface_scenariile_cu_gol(self):
        self.durate["08:30"] = 3.4
        L.lant(ZI, fara_simulari=True)
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True, fara_simulari=True), 0)
        self.assertEqual(self.rulate, [])

    def test_grila_care_nu_se_citeste_nu_opreste_singura_lantul(self):
        with mock.patch.object(L, "goluri_grila", side_effect=ValueError("stricat")):
            self.assertEqual(L.lant(ZI, ["08:00-09:15"], fara_simulari=True), 0)
        self.assertIn("08:00-09:15", self.comenzi["scenarii"])
        self.assertIn("nu s-a putut citi", self.jurnal_lant())

    def test_csv_fara_randuri(self):
        (L.COUNTS_DIR / f"numaratori_{ZI}.csv").write_text(ANTET_CSV, encoding="utf-8")
        self.assertEqual(L.goluri_grila(ZI), [])

    def test_uscat_arata_golurile(self):
        self.csv({**self.sferturi("00:00", "08:30"), "08:30": 3.4, **self.sferturi("08:45", "24:00")})
        self.assertEqual(L.main(["--uscat", "--zi", ZI]), 0)
        text = self.ecran.getvalue()
        self.assertIn("(lanțul le recalculează după renumărare): 08:30-09:00", text)
        self.assertIn(f"--zi {ZI} --exclude 08:30-09:00", text)


class TestScenariiRamase(Cutie):
    """O excludere nouă care face să dispară o fereastră. `scenarii_zi`, `indisciplinat`, `resolve_scenarios` și `debite` sunt
    cele adevărate, în cutie; doar `build_demand.main` e înlocuit (scrie sumocfg-ul, fără SUMO)."""

    def setUp(self):
        super().setUp()
        from romana.bridge import indisciplinat, scenarii_zi
        from romana.control import decizie, validare
        self.Z, self.I, self.D, self.V = scenarii_zi, indisciplinat, decizie, validare
        self.scen, self.dem = self.d / "sumo" / "scenarios", self.d / "sumo" / "demand"
        self.scen.mkdir(parents=True)
        self.dem.mkdir(parents=True)
        self.simulate = {}
        for obiect, nume, val in ((scenarii_zi, "COUNTS_DIR", L.COUNTS_DIR), (scenarii_zi, "DEMAND_DIR", self.dem),
                                  (scenarii_zi.build_demand, "main", self.build_fals), (decizie, "DEMAND_DIR", self.dem),
                                  (validare, "SCEN_DIR", self.scen), (L, "ruleaza", self.ruleaza_mixt)):
            p = mock.patch.object(obiect, nume, val)
            p.start()
            self.addCleanup(p.stop)

    def build_fals(self, argv):
        nume = argv[argv.index("--nume") + 1]
        (self.scen / f"{nume}.sumocfg").write_text(
            '<configuration><additional-files value="../demand/vtypes.add.xml"/></configuration>', encoding="utf-8")
        (self.dem / nume).mkdir(exist_ok=True)

    def ruleaza_mixt(self, cmd, cale, note=None, la_pornire=None):
        nume = cale.stem
        if nume in ("scenarii", "indisciplinat"):
            self.rulate.append(nume)
            self.comenzi[nume] = cmd
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    (self.Z if nume == "scenarii" else self.I).main(cmd[3:])
            except SystemExit as e:
                return 1 if e.code else 0
            return 0
        if nume.startswith("test_"):
            self.simulate[nume] = sorted(x.stem for x in self.V.resolve_scenarios([cmd[cmd.index("--scenarii") + 1]]))
        return self.ruleaza_fals(cmd, cale, note, la_pornire)

    def pe_disc(self) -> list[str]:
        return sorted(x.stem for x in self.scen.glob("*.sumocfg"))

    def test_fereastra_disparuta_nu_mai_ajunge_la_validare(self):
        self.assertEqual(L.lant(ZI, ["08:30-09:00"]), 0)
        self.assertEqual(len(self.simulate["test_normal"]), 7)
        self.assertIn(f"zi_{ZI}_pranz", self.simulate["test_normal"])
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, ["08:30-09:00", "12:00-12:15"], reia=True), 0)
        self.assertEqual(self.rulate, NUME_PASI[4:])
        self.assertEqual(self.stare()["rezultat"], "gata")
        for pas, prefix in (("test_normal", ""), ("test_indisciplinat", "indisciplinat_")):
            self.assertEqual(len(self.simulate[pas]), 6, pas)
            self.assertNotIn(f"{prefix}zi_{ZI}_pranz", self.simulate[pas])
            self.assertIn(f"{prefix}zi_{ZI}_varf_x1_2", self.simulate[pas])
        self.assertEqual(len(self.pe_disc()), 12)
        self.assertFalse((self.dem / f"zi_{ZI}_pranz").exists())    # nici cererea ferestrei, ca să nu rămână în date
        self.assertTrue((self.dem / f"zi_{ZI}_varf").exists())
        self.assertIn("rămase de la o rulare anterioară", self.jurnal_lant())
        # `decizie` citește fereastra fiecărui scenariu din rezumat: cu scenariul rămas, aici ieșea KeyError, după simulări
        debite = self.D.debite(self.simulate["test_normal"] + self.simulate["test_indisciplinat"])
        self.assertEqual(len(debite), 12)

    def test_cu_aceleasi_ferestre_nu_se_sterge_nimic(self):
        L.lant(ZI, ["08:30-09:00"])
        inainte = self.pe_disc()
        self.assertEqual(L.lant(ZI, ["08:30-09:00", "20:00-20:15"], reia=True), 0)
        self.assertEqual(self.pe_disc(), inainte)
        self.assertNotIn("rămase de la o rulare anterioară", self.jurnal_lant())

    def test_scenarii_esuate_nu_sterg_nimic(self):
        L.lant(ZI, ["08:30-09:00"])
        inainte = self.pe_disc()
        self.assertEqual(L.lant(ZI, ["00:00-24:00"], reia=True), 1)     # nicio oră completă după excluderi
        self.assertEqual(self.pe_disc(), inainte)
        self.assertIn("oprit", self.stare()["rezultat"])

    def test_alte_zile_si_alte_variante_nu_se_ating(self):
        L.lant(ZI, ["08:30-09:00"])
        straine = [self.scen / "zi_2026-10-29_pranz.sumocfg", self.scen / f"capacitate_zi_{ZI}_pranz.sumocfg"]
        for f in straine:
            f.write_text("<configuration/>", encoding="utf-8")
        self.assertEqual(L.lant(ZI, ["08:30-09:00", "12:00-12:15"], reia=True), 0)
        for f in straine:
            self.assertTrue(f.exists(), f.name)
        self.assertFalse((self.scen / f"zi_{ZI}_pranz.sumocfg").exists())

    def test_scenariul_ramas_care_nu_se_poate_sterge_opreste_inainte_de_simulari(self):
        L.lant(ZI, ["08:30-09:00"])
        self.simulate.clear()
        with mock.patch.object(Path, "unlink", side_effect=PermissionError("deschis")):
            self.assertEqual(L.lant(ZI, ["08:30-09:00", "12:00-12:15"], reia=True), 1)
        self.assertEqual(self.simulate, {})
        self.assertEqual(self.stare()["pasi"]["scenarii"]["cod"], L.COD_REZUMAT)


DOARME = "import os, sys, time; open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(120)"
LANT_IN_PROCES = """
import sys
from pathlib import Path
from romana import lant_zilnic as L
d, marca, doarme = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
L.ROOT, L.TRAJ_RAW_DIR, L.COUNTS_DIR = d, d / "brute", d / "counts"
L.DIR_LANT, L.DIR_LOGURI = d / "outputs" / "lant", d / "outputs" / "logs"
L.colectare_activa = lambda: False
L.pasi = lambda zi, ex=(), fs=False, desigilat=False: [L.Pas("test_normal", [sys.executable, "-c", doarme, marca])]
sys.exit(L.lant("2026-11-01"))
"""


class TestPasRamas(Cutie):
    """Lanțul oprit din afară își lasă pasul să ruleze. Procese reale, inofensive (`python -c`, care doarme)."""

    def porneste(self, *cmd, **k) -> subprocess.Popen:
        p = subprocess.Popen(list(cmd), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **k)
        self.addCleanup(self.opreste_tot, p)
        return p

    @staticmethod
    def opreste_tot(p: subprocess.Popen) -> None:
        import psutil
        try:
            copii = psutil.Process(p.pid).children(recursive=True)
        except psutil.Error:
            copii = []
        for x in (p, *copii):
            try:
                x.kill()
            except Exception:
                pass
        p.wait()

    def citeste_cand_apare(self, f: Path, s: float = 60.0) -> str:
        limita = timp.monotonic() + s
        while timp.monotonic() < limita:
            if f.exists() and (text := f.read_text(encoding="utf-8")):
                return text
            timp.sleep(0.05)
        self.fail(f"{f.name} n-a apărut în {s} s")

    def pas_care_doarme(self) -> tuple[subprocess.Popen, int]:
        """Procesul pasului (lansatorul din .venv) și PID-ul interpretorului real, abia după ce acesta a pornit."""
        marca = self.d / "marca.txt"
        p = self.porneste(sys.executable, "-c", DOARME, str(marca))
        return p, int(self.citeste_cand_apare(marca))

    def stare_cu_pas(self, pid: int, cod=None, creat: float | None = None) -> None:
        import psutil
        (L.DIR_LANT / ZI).mkdir(parents=True, exist_ok=True)
        creat = psutil.Process(pid).create_time() if creat is None else creat
        L.scrie_stare(ZI, {"zi": ZI, "rezultat": "in_curs", "pasi": {
            "test_normal": {"cod": cod, "inceput": "2026-11-02T01:00:00", "sfarsit": None, "comanda": ["x"], "pid": pid,
                            "creat": creat}}})

    def mort(self, pid: int, s: float = 10.0) -> bool:
        import psutil
        try:
            psutil.Process(pid).wait(timeout=s)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            return False
        return True

    def test_pasul_ramas_se_opreste_la_reluare(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid)
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertIsNotNone(p.wait(timeout=10))
        self.assertTrue(self.mort(real))            # și interpretorul, nu doar lansatorul
        self.assertIn("a rămas să ruleze", self.jurnal_lant())
        self.assertEqual(self.stare()["rezultat"], "gata")
        self.assertEqual(self.stare()["pasi"]["test_normal"]["cod"], 0)

    def test_pasul_ramas_se_opreste_si_fara_reia(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid)
        self.assertEqual(L.lant(ZI), 0)
        self.assertTrue(self.mort(real))

    def test_pasul_ramas_se_opreste_inainte_de_primul_pas_nou(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid)
        vii = []

        def fals(cmd, cale, note=None, la_pornire=None):
            vii.append(p.poll() is None)
            return self.ruleaza_fals(cmd, cale, note, la_pornire)

        with mock.patch.object(L, "ruleaza", fals):
            L.lant(ZI, fara_simulari=True)
        self.assertEqual(set(vii), {False})

    def test_pid_refolosit_nu_se_atinge(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid, creat=1000.0)      # același PID, alt moment de pornire: alt proces, după o repornire
        self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertIsNone(p.poll())
        self.assertNotIn("a rămas să ruleze", self.jurnal_lant())

    def test_pas_incheiat_nu_se_atinge(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid, cod=0)
        L.lant(ZI, reia=True)
        self.assertIsNone(p.poll())

    def test_fara_momentul_pornirii_nu_se_atinge(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid)
        s = L.citeste_stare(ZI)
        s["pasi"]["test_normal"]["creat"] = None
        L.scrie_stare(ZI, s)
        L.lant(ZI, reia=True)
        self.assertIsNone(p.poll())

    def test_pas_ramas_care_nu_se_poate_opri_opreste_lantul(self):
        p, real = self.pas_care_doarme()
        self.stare_cu_pas(p.pid)
        with mock.patch.object(L, "_opreste_arbore"):
            self.assertEqual(L.lant(ZI, reia=True), 1)
        self.assertEqual(self.rulate, [])
        s = self.stare()
        self.assertIn("nu s-a putut opri", s["rezultat"])
        self.assertEqual(s["pasi"]["test_normal"]["pid"], p.pid)     # data viitoare se încearcă din nou

        with mock.patch.object(L, "_opreste_arbore"):               # și fără --reia: PID-ul nu se pierde
            self.assertEqual(L.lant(ZI), 1)
        self.assertEqual(self.stare()["pasi"]["test_normal"]["pid"], p.pid)

    def test_pidul_ajunge_in_stare_chiar_dupa_pornirea_pasului(self):
        # pasul își citește singur starea cât rulează: lanțul (real, în proces) a scris deja PID-ul și momentul pornirii
        script = ("import json, sys, time\n"
                  "for _ in range(200):\n"
                  "    try:\n"
                  "        r = json.load(open(sys.argv[1], encoding='utf-8'))['pasi']['proba']\n"
                  "        if r.get('pid'):\n"
                  "            break\n"
                  "    except (OSError, ValueError):\n"     # chiar în clipa înlocuirii fișierului
                  "        pass\n"
                  "    time.sleep(0.05)\n"
                  "print(json.dumps(r))\n")
        cmd = [sys.executable, "-c", script, str(L.DIR_LANT / ZI / "stare.json")]
        with mock.patch.object(L, "ruleaza", RULEAZA), mock.patch.object(L, "pasi", lambda *a, **k: [L.Pas("proba", cmd)]):
            self.assertEqual(L.lant(ZI), 0)
        vazut = json.loads((L.DIR_LANT / ZI / "proba.txt").read_text(encoding="utf-8"))
        self.assertIsNone(vazut["cod"])
        self.assertIsNotNone(vazut["creat"])
        self.assertEqual(vazut["pid"], self.stare()["pasi"]["proba"]["pid"])

    def lant_oprit_din_afara(self, tinta: str) -> None:
        # un lanț adevărat, în proces separat, cu un pas care doarme; se oprește doar `tinta`, ca la o oprire din afară
        import psutil
        marca = self.d / f"marca_{tinta}.txt"
        d = L.DIR_LANT / ZI
        d.mkdir(parents=True, exist_ok=True)
        (d / L.FISIER_BLOCARE).unlink(missing_ok=True)
        mediu = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
        p = self.porneste(sys.executable, "-c", LANT_IN_PROCES, str(self.d), str(marca), DOARME, env=mediu)
        pas = int(self.citeste_cand_apare(marca))
        lant_real = int(self.citeste_cand_apare(d / L.FISIER_BLOCARE))
        pas_inregistrat = None
        limita = timp.monotonic() + 30
        while pas_inregistrat is None and timp.monotonic() < limita:    # starea se scrie imediat după pornirea pasului
            pas_inregistrat = L.citeste_stare(ZI).get("pasi", {}).get("test_normal", {}).get("pid")
            timp.sleep(0.05)
        self.assertIsNotNone(pas_inregistrat)
        (psutil.Process(lant_real) if tinta == "interpretorul" else p).kill()
        self.assertTrue(self.mort(lant_real), "lanțul n-a murit odată cu lansatorul lui")
        self.assertFalse(self.mort(pas, 1.0), "premisa: pasul trebuia să rămână să ruleze")
        # reluarea, în acest proces, cu blocarea adevărată și cu rularea comenzilor înlocuită
        self.rulate.clear()
        with mock.patch.object(L, "lant_activ", LANT_ACTIV), \
                mock.patch.object(L, "pasi", lambda *a, **k: [L.Pas("test_normal", ["python", "fals"])]):
            self.assertEqual(L.lant(ZI, reia=True), 0)
        self.assertTrue(self.mort(pas), "pasul rămas trebuia oprit înainte de reluare")
        self.assertEqual(self.rulate, ["test_normal"])
        self.assertIn("a rămas să ruleze", self.jurnal_lant())

    def test_lant_oprit_din_afara_interpretorul(self):
        self.lant_oprit_din_afara("interpretorul")

    def test_lant_oprit_din_afara_lansatorul(self):
        self.lant_oprit_din_afara("lansatorul")


class TestRanduriDublate(Cutie):
    """Fluxul oprit peste miezul nopții care revine după renumărare: `run_vision` adaugă intervalul 23:45 în CSV-ul zilei
    trecute."""

    def rand_dublat(self) -> None:
        with open(L.COUNTS_DIR / f"numaratori_{ZI}.csv", "a", newline="", encoding="utf-8") as f:
            f.write(rand_csv(datetime.fromisoformat(f"{ZI}T23:45:00")))

    def test_randuri_dublate(self):
        self.assertEqual(L.randuri_dublate(ZI), 0)      # fără CSV
        self.numaratori(ZI)
        self.assertEqual(L.randuri_dublate(ZI), 0)
        self.rand_dublat()
        self.assertEqual(L.randuri_dublate(ZI), 1)
        self.rand_dublat()
        self.assertEqual(L.randuri_dublate(ZI), 2)

    @unittest.skipUnless((COUNTS_DIR / "numaratori_2026-10-25.csv").exists(), "numărătorile din 25.10 lipsesc")
    def test_ora_care_se_repeta_la_trecerea_la_ora_de_iarna(self):
        # doar citire: 25.10 are ora 03:xx de două ori, deci chei dublate fără niciun defect
        with mock.patch.object(L, "COUNTS_DIR", COUNTS_DIR):
            self.assertGreater(L.randuri_dublate("2026-10-25"), 0)
            self.assertEqual(L.randuri_dublate("2026-10-28"), 0)

    def test_dublura_aparuta_dupa_renumarare_se_reface_inainte_de_scenarii(self):
        self.dupa_pas["publica"] = self.rand_dublat
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertEqual(self.rulate, [*NUME_PASI[:4], "recount_dublate", *NUME_PASI[4:6]])
        self.assertEqual(L.randuri_dublate(ZI), 0)
        self.assertIn("cheie dublată", self.jurnal_lant())
        self.assertEqual(self.comenzi["recount_dublate"], self.comenzi["recount"])

    def test_dublura_aparuta_dupa_scenarii_se_reface_la_sfarsit(self):
        self.dupa_pas["indisciplinat"] = self.rand_dublat
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertEqual(self.rulate, [*NUME_PASI[:6], "recount_dublate"])
        self.assertEqual(L.randuri_dublate(ZI), 0)

    def test_dublura_care_ramane_se_noteaza_si_lantul_continua(self):
        self.dublate_mereu = True
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertIn("scenarii", self.rulate)
        self.assertIn("rămân", self.jurnal_lant())
        self.assertEqual(self.stare()["rezultat"], "gata_fara_simulari")

    def test_renumararea_esuata_opreste_inainte_de_scenarii(self):
        self.dupa_pas["publica"] = self.rand_dublat
        self.coduri["recount_dublate"] = 1
        self.assertEqual(L.lant(ZI, fara_simulari=True), 1)
        self.assertNotIn("scenarii", self.rulate)
        self.assertIn("rândurile dublate", self.stare()["rezultat"])

    def test_renumararea_esuata_la_sfarsit_doar_se_noteaza(self):
        self.dupa_pas["indisciplinat"] = self.rand_dublat
        self.coduri["recount_dublate"] = 1
        self.assertEqual(L.lant(ZI, fara_simulari=True), 0)
        self.assertIn("rămâne cu rânduri dublate", self.jurnal_lant())

    def test_reluarea_repara_csv_ul_fara_sa_refaca_scenariile(self):
        # scenariile s-au făcut din CSV-ul curat; rândul a apărut abia după, deci rezultatele lor rămân bune
        L.lant(ZI, fara_simulari=True)
        self.rand_dublat()
        self.rulate.clear()
        self.assertEqual(L.lant(ZI, reia=True, fara_simulari=True), 0)
        self.assertEqual(self.rulate, ["recount_dublate"])
        self.assertEqual(L.randuri_dublate(ZI), 0)


class TestFlux(Cutie):
    """Așteptarea fluxului oprit dinaintea miezului nopții (`timestamp` din starea live)."""
    IERI = "2026-10-29"

    def stare_live(self, moment: datetime | None = None, text: str | None = None) -> None:
        L.DIR_LIVE.mkdir(parents=True, exist_ok=True)
        (L.DIR_LIVE / "state.json").write_text(
            text if text is not None else json.dumps({"timestamp": moment.timestamp()}), encoding="utf-8")

    def asteapta(self, dupa_somn=None) -> tuple[bool, list[float], list[str]]:
        ceas, note = [1000.0], []
        somn = []

        def dormi(s):
            somn.append(s)
            ceas[0] += s
            if dupa_somn:
                dupa_somn(len(somn))

        return L.asteapta_fluxul(self.IERI, note.append, lambda: ceas[0], dormi), somn, note

    def test_fluxul_merge_dupa_miezul_noptii(self):
        self.stare_live(datetime(2026, 10, 30, 0, 15))
        self.assertEqual(self.asteapta()[:2], (True, []))

    def test_chiar_la_miezul_noptii(self):
        self.stare_live(datetime(2026, 10, 30, 0, 0))
        self.assertEqual(self.asteapta()[:2], (True, []))

    def test_fara_stare_nu_e_o_dovada(self):
        self.assertEqual(self.asteapta()[:2], (True, []))
        self.stare_live(text='{"timest')
        self.assertEqual(self.asteapta()[:2], (True, []))
        self.stare_live(text='{"fps": 5}')
        self.assertEqual(self.asteapta()[:2], (True, []))

    def test_asteapta_pana_revine(self):
        self.stare_live(datetime(2026, 10, 29, 23, 58))

        def revine(n):
            if n == 3:
                self.stare_live(datetime(2026, 10, 30, 0, 20))
            elif n == 2:
                self.stare_live(text="stricat")     # fișierul poate fi citit și în clipa înlocuirii

        ok, somn, note = self.asteapta(revine)
        self.assertTrue(ok)
        self.assertEqual(len(somn), 3)
        self.assertIn("a revenit", note[-1])

    def test_renunta_dupa_limita(self):
        self.stare_live(datetime(2026, 10, 29, 23, 58))
        ok, somn, note = self.asteapta()
        self.assertFalse(ok)
        self.assertEqual(sum(somn), L.ASTEPTARE_FLUX_S)
        self.assertIn("[atenție]", note[-1])

    def test_ziua_trecuta_cu_colectarea_activa_asteapta_inainte_de_primul_pas(self):
        self.jurnal_sintetic(self.IERI)
        L.colectare_activa.return_value = True
        ordine = []

        def asteapta(zi, note):
            ordine.append(("asteapta", zi, list(self.rulate)))
            return False

        with mock.patch.object(L, "asteapta_fluxul", asteapta):
            self.assertEqual(L.lant(self.IERI, fara_simulari=True), 0)
        self.assertEqual(ordine, [("asteapta", self.IERI, [])])
        self.assertEqual(self.rulate, NUME_PASI[:6])
        self.assertTrue(self.stare(self.IERI)["flux_oprit"])

    def test_cu_colectarea_oprita_nu_se_asteapta(self):
        self.jurnal_sintetic(self.IERI)
        with mock.patch.object(L, "asteapta_fluxul") as a:
            self.assertEqual(L.lant(self.IERI, fara_simulari=True), 0)
        a.assert_not_called()
        self.assertNotIn("flux_oprit", self.stare(self.IERI))


class TestLiniaDeComanda(Cutie):
    def lista(self) -> set:
        return {p for p in self.d.rglob("*")}

    def test_uscat_pe_ziua_curenta_spune_ca_lantul_s_ar_opri(self):
        azi = date.today().isoformat()
        L.colectare_activa.return_value = True
        self.assertEqual(L.main(["--uscat", "--zi", azi]), 0)
        text = self.ecran.getvalue()
        self.assertIn("colectarea rulează, iar CSV-ul zilei e scris live (lanțul s-ar opri aici)", text)
        self.assertLess(text.index("s-ar opri"), text.index("[repara]"))   # ca la jurnalul lipsă, comenzile se afișează oricum
        self.assertEqual(self.rulate, [])

    def test_uscat_pe_o_zi_trecuta_nu_vorbeste_de_colectare(self):
        L.colectare_activa.return_value = True
        self.assertEqual(L.main(["--uscat", "--zi", "2026-10-29"]), 0)
        self.assertNotIn("colectarea rulează", self.ecran.getvalue())

    def test_uscat_pe_ziua_curenta_cu_colectarea_oprita(self):
        self.assertEqual(L.main(["--uscat", "--zi", date.today().isoformat()]), 0)
        self.assertNotIn("colectarea rulează", self.ecran.getvalue())

    def test_uscat_bucla_nu_opreste_o_zi_care_va_fi_incheiata(self):
        # ziua de azi, planificată pentru miezul nopții: atunci va fi deja ziua de ieri
        L.colectare_activa.return_value = True
        self.assertEqual(L.main(["--uscat", "--bucla", "--pana-la", "2099-01-02 12:00"]), 0)
        self.assertNotIn("colectarea rulează", self.ecran.getvalue())

    def test_ziua_implicita_e_ieri(self):
        self.assertEqual(L.zi_implicita(datetime(2026, 11, 2, 0, 15)), "2026-11-01")
        self.assertEqual(L.zi_implicita(datetime(2026, 11, 1, 23, 59)), "2026-10-31")
        self.assertEqual(L.zi_implicita(datetime(2027, 1, 1, 0, 0)), "2026-12-31")

    def test_fara_zi_ruleaza_ziua_de_ieri(self):
        ieri = (date.today() - timedelta(days=1)).isoformat()
        self.jurnal_sintetic(ieri)
        self.assertEqual(L.main(["--fara-simulari"]), 0)
        self.assertEqual(self.stare(ieri)["zi"], ieri)
        self.assertEqual(self.rulate, NUME_PASI[:6])

    def test_uscat_nu_ruleaza_si_nu_scrie_nimic(self):
        inainte = self.lista()
        self.assertEqual(L.main(["--uscat", "--zi", ZI, "--exclude", "08:00-09:15"]), 0)
        self.assertEqual(self.rulate, [])
        self.assertEqual(self.lista(), inainte)
        L.prioritate_scazuta.assert_not_called()
        text = self.ecran.getvalue()
        self.assertIn(f"--zi {ZI} --exclude 08:00-09:15", text)
        for nume in NUME_PASI:
            self.assertIn(f"[{nume}] ", text)

    def test_uscat_fara_zi_si_fara_jurnal(self):
        ieri = (date.today() - timedelta(days=1)).isoformat()
        self.assertEqual(L.main(["--uscat"]), 0)
        self.assertIn(f"ziua {ieri}", self.ecran.getvalue())
        self.assertIn("LIPSEȘTE", self.ecran.getvalue())

    def test_uscat_afiseaza_si_excluderile_gasite(self):
        (L.DIR_LOGURI / f"reporniri_{ZI}.csv").write_text(f"oprire,repornire\n{ZI}T14:01:00,{ZI}T14:03:00\n", encoding="utf-8")
        self.assertEqual(L.main(["--uscat", "--zi", ZI, "--exclude", "08:00-09:15", "14:00-14:15"]), 0)
        self.assertIn("--exclude 08:00-09:15 --exclude 14:00-14:15", self.ecran.getvalue())

    def test_uscat_bucla_afiseaza_noptile(self):
        inainte = self.lista()
        self.assertEqual(L.main(["--uscat", "--bucla", "--ora", "00:15", "--pana-la", "2099-01-02 12:00"]), 0)
        self.assertEqual((self.rulate, self.lista()), ([], inainte))
        self.assertIn("[uscat] bucla ar prelucra", self.ecran.getvalue())

    def test_argumente_gresite(self):
        gresite = (["--zi", "2026-11-1"], ["--exclude", "08:07-09:00"], ["--bucla", "--zi", ZI],
                   ["--bucla", "--exclude", "08:00-09:15"], ["--ora", "00:15"], ["--pana-la", "2026-11-08 12:00"],
                   ["--bucla", "--ora", "25:00"], ["--bucla", "--pana-la", "2026-11-08"], ["--de-la", "2026-11-01"],
                   ["--bucla", "--de-la", "2026-11-1"])
        for arg in gresite:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit, msg=arg) as e:
                L.main(arg)
            self.assertEqual(e.exception.code, 2, arg)
        self.assertEqual(self.rulate, [])

    def test_exclude_de_mai_multe_ori(self):
        self.assertEqual(L.main(["--zi", ZI, "--fara-simulari", "--exclude", "08:00-09:15", "10:00-10:15",
                                 "--exclude", "12:00-12:15"]), 0)
        self.assertEqual(self.stare()["excluderi"], ["08:00-09:15", "10:00-10:15", "12:00-12:15"])


class Ceas:
    def __init__(self, t: datetime):
        self.t, self.somn = t, []

    def acum(self) -> datetime:
        return self.t

    def dormi(self, s: float) -> None:
        self.somn.append(s)
        self.t += timedelta(seconds=s)


class TestBucla(Cutie):
    ORA = time(0, 15)

    def ruleaza_bucla(self, start, pana_la, efecte=None, reia=False, de_la=None):
        """Bucla cu ceasul simulat și lanțul înlocuit: lista (ziua, momentul pornirii) și codul întors."""
        ceas, nopti = Ceas(start), []
        efecte = list(efecte or [])

        def lant_fals(zi, exclude, reia_, fara_simulari):
            nopti.append((zi, ceas.t))
            self.assertEqual((exclude, reia_, fara_simulari), ((), reia, False))
            e = efecte.pop(0) if efecte else 0
            if callable(e):
                e = e(ceas)
            if isinstance(e, BaseException):
                raise e
            return e

        with mock.patch.object(L, "lant", lant_fals):
            cod = L.bucla(self.ORA, pana_la, reia, False, ceas.acum, ceas.dormi, de_la)
        self.ceas = ceas
        return nopti, cod

    def text_bucla(self) -> str:
        return (L.DIR_LANT / "bucla.txt").read_text(encoding="utf-8")

    def test_doua_nopti_prima_esueaza_a_doua_merge(self):
        nopti, cod = self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 3, 12, 0), [1, 0])
        self.assertEqual(nopti, [("2026-11-01", datetime(2026, 11, 2, 0, 15)), ("2026-11-02", datetime(2026, 11, 3, 0, 15))])
        self.assertEqual(cod, 1)
        text = self.text_bucla()
        self.assertIn("ziua 2026-11-01: EȘUATĂ", text)
        self.assertIn("--zi 2026-11-01 --reia", text)
        self.assertIn("ziua 2026-11-02: gata", text)
        self.assertLess(text.index("EȘUATĂ"), text.index("ziua 2026-11-02: gata"))
        self.assertLessEqual(max(self.ceas.somn), 60)

    def test_doua_nopti_bune(self):
        nopti, cod = self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 3, 0, 15))
        self.assertEqual([z for z, _ in nopti], ["2026-11-01", "2026-11-02"])     # ora din --pana-la încă se rulează
        self.assertEqual(cod, 0)

    def test_pana_la_8_noiembrie(self):
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 8, 12, 0))
        self.assertEqual([z for z, _ in nopti], [f"2026-11-0{k}" for k in range(1, 8)])
        self.assertEqual(nopti[-1][1], datetime(2026, 11, 8, 0, 15))

    def test_o_exceptie_nu_opreste_bucla(self):
        nopti, cod = self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 4, 12, 0),
                                        [ValueError("defect"), SystemExit("oprit"), 0])
        self.assertEqual(len(nopti), 3)
        self.assertEqual(cod, 1)
        self.assertIn("defect", self.text_bucla())

    def test_ctrl_c_opreste_bucla(self):
        with self.assertRaises(KeyboardInterrupt):
            self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 4, 12, 0), [KeyboardInterrupt()])

    def test_un_lant_mai_lung_de_24_h_nu_sare_peste_o_zi(self):
        def lung(ceas):
            ceas.t += timedelta(hours=25)
            return 0
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 1, 12, 0), datetime(2026, 11, 3, 12, 0), [lung])
        self.assertEqual(nopti, [("2026-11-01", datetime(2026, 11, 2, 0, 15)), ("2026-11-02", datetime(2026, 11, 3, 1, 15))])

    def test_ora_exacta_se_ruleaza_acum(self):
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 0, 15), datetime(2026, 11, 2, 12, 0))
        self.assertEqual(nopti, [("2026-11-01", datetime(2026, 11, 2, 0, 15))])
        self.assertEqual(self.ceas.somn, [])

    def test_pana_la_trecut_nu_face_nimic(self):
        nopti, cod = self.ruleaza_bucla(datetime(2026, 11, 9, 12, 0), datetime(2026, 11, 8, 12, 0))
        self.assertEqual((nopti, cod), ([], 0))

    def test_reia_la_pornire_noaptea_neincheiata(self):
        d = L.DIR_LANT / ZI
        d.mkdir(parents=True)
        L.scrie_stare(ZI, {"zi": ZI, "rezultat": "in_curs", "pasi": {}})
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual(nopti, [(ZI, datetime(2026, 11, 2, 2, 0))])
        self.assertIn("se reia acum", self.text_bucla())

    def test_reia_la_pornire_si_noaptea_care_n_a_inceput(self):
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual([z for z, _ in nopti], [ZI])

    def test_reia_nu_refac_noaptea_incheiata(self):
        (L.DIR_LANT / ZI).mkdir(parents=True)
        L.scrie_stare(ZI, {"zi": ZI, "rezultat": "gata", "pasi": {}})
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual(nopti, [])

    def test_reia_nu_cauta_o_zi_fara_jurnal(self):
        L.jurnal(ZI).unlink()
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual(nopti, [])

    def test_fara_reia_nu_se_reia_la_pornire(self):
        (L.DIR_LANT / ZI).mkdir(parents=True)
        L.scrie_stare(ZI, {"zi": ZI, "rezultat": "in_curs", "pasi": {}})
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0))
        self.assertEqual(nopti, [])

    def test_reia_apoi_noaptea_urmatoare(self):
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 3, 12, 0), reia=True)
        self.assertEqual(nopti, [(ZI, datetime(2026, 11, 2, 2, 0)), ("2026-11-02", datetime(2026, 11, 3, 0, 15))])

    def prima_pornire(self, moment=datetime(2026, 11, 1, 12, 0)) -> None:
        """Prima pornire a buclei, care ține minte prima zi de care răspunde."""
        self.ruleaza_bucla(moment, moment)
        self.assertEqual(L.prima_zi_buclei(), L.zi_implicita(L.urmatoarea_ora(moment, self.ORA)))

    def test_reia_recupereaza_toate_noptile_pierdute(self):
        # bucla moare pe 02.11 și e repornită abia pe 05.11, la 09:00: 03.11 nu trebuie să rămână neprelucrată, în tăcere
        self.prima_pornire()
        (L.DIR_LANT / ZI).mkdir(parents=True)
        L.scrie_stare(ZI, {"zi": ZI, "rezultat": "gata", "pasi": {}})
        for z in ("2026-11-02", "2026-11-03", "2026-11-04"):
            self.jurnal_sintetic(z)
        repornire = datetime(2026, 11, 5, 9, 0)
        nopti, cod = self.ruleaza_bucla(repornire, datetime(2026, 11, 6, 1, 0), reia=True)
        self.assertEqual(nopti, [("2026-11-02", repornire), ("2026-11-03", repornire), ("2026-11-04", repornire),
                                 ("2026-11-05", datetime(2026, 11, 6, 0, 15))])
        self.assertEqual(cod, 0)
        self.assertEqual(self.text_bucla().count("se reia acum"), 3)

    def test_zilele_vechi_fara_stare_nu_intra(self):
        for z in ("2026-10-21", "2026-10-29", "2026-10-30"):        # colectate înainte de lanț, n-au stare
            self.jurnal_sintetic(z)
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual([z for z, _ in nopti], [ZI])

    def test_prima_zi_ramane_de_la_prima_pornire(self):
        self.prima_pornire(datetime(2026, 11, 2, 12, 0))
        self.assertEqual(L.prima_zi_buclei(), "2026-11-02")
        self.ruleaza_bucla(datetime(2026, 11, 5, 12, 0), datetime(2026, 11, 5, 12, 0))
        self.assertEqual(L.prima_zi_buclei(), "2026-11-02")

    def test_de_la_muta_inceputul_si_se_pastreaza(self):
        self.prima_pornire()
        self.jurnal_sintetic("2026-10-30")
        repornire = datetime(2026, 11, 2, 9, 0)
        nopti, _ = self.ruleaza_bucla(repornire, repornire, reia=True, de_la="2026-10-30")
        self.assertEqual([z for z, _ in nopti], ["2026-10-30", ZI])     # 31.10 n-are jurnal
        self.assertIn("ziua 2026-10-31: fără jurnal", self.text_bucla())
        self.assertEqual(L.prima_zi_buclei(), "2026-10-30")

    def test_fara_reia_zilele_neincheiate_se_noteaza(self):
        self.prima_pornire()
        self.jurnal_sintetic("2026-11-02")
        moment = datetime(2026, 11, 3, 9, 0)
        nopti, _ = self.ruleaza_bucla(moment, moment)
        self.assertEqual(nopti, [])
        self.assertIn(f"zile neîncheiate: {ZI}, 2026-11-02", self.text_bucla())

    def test_pana_la_limiteaza_si_reluarea(self):
        self.prima_pornire()
        for z in ("2026-11-02", "2026-11-03", "2026-11-04"):
            self.jurnal_sintetic(z)
        repornire = datetime(2026, 11, 10, 9, 0)
        nopti, _ = self.ruleaza_bucla(repornire, datetime(2026, 11, 3, 12, 0), reia=True)
        self.assertEqual([z for z, _ in nopti], [ZI, "2026-11-02"])

    def test_o_zi_esuata_nu_opreste_reluarea_celorlalte(self):
        self.prima_pornire()
        self.jurnal_sintetic("2026-11-02")
        repornire = datetime(2026, 11, 3, 9, 0)
        nopti, cod = self.ruleaza_bucla(repornire, repornire, [1, 0], reia=True)
        self.assertEqual([z for z, _ in nopti], [ZI, "2026-11-02"])
        self.assertEqual(cod, 1)

    def test_bucla_json_stricat_se_scrie_din_nou(self):
        L.DIR_LANT.mkdir(parents=True)
        (L.DIR_LANT / L.FISIER_BUCLA).write_text("{stricat", encoding="utf-8")
        nopti, _ = self.ruleaza_bucla(datetime(2026, 11, 2, 2, 0), datetime(2026, 11, 2, 12, 0), reia=True)
        self.assertEqual([z for z, _ in nopti], [ZI])
        self.assertIn("nu se poate citi", self.text_bucla())
        self.assertEqual(L.prima_zi_buclei(), ZI)

    def test_de_la_ajunge_din_linia_de_comanda(self):
        with mock.patch.object(L, "bucla", return_value=0) as b:
            self.assertEqual(L.main(["--bucla", "--reia", "--de-la", "2026-11-01"]), 0)
        self.assertEqual(b.call_args.kwargs["de_la"], "2026-11-01")

    def test_uscat_bucla_reia_arata_zilele_si_nu_scrie_nimic(self):
        self.prima_pornire()
        inainte = {p for p in self.d.rglob("*")}
        self.assertEqual(L.main(["--uscat", "--bucla", "--reia", "--pana-la", "2099-01-02 12:00"]), 0)
        self.assertEqual({p for p in self.d.rglob("*")}, inainte)
        self.assertEqual(self.rulate, [])
        text = self.ecran.getvalue()
        self.assertIn(f"[uscat] la pornire, bucla ar relua (de la {ZI}):", text)

    def test_doua_nopti_cu_lantul_adevarat(self):
        # prima noapte n-are jurnal (eșuează), a doua rulează toți pașii; rularea comenzilor rămâne înlocuită
        L.jurnal(ZI).unlink()
        urm = "2026-11-02"
        self.jurnal_sintetic(urm)
        ceas = Ceas(datetime(2026, 11, 1, 23, 0))
        cod = L.bucla(self.ORA, datetime(2026, 11, 3, 12, 0), False, False, ceas.acum, ceas.dormi)
        self.assertEqual(cod, 1)
        self.assertIn("LIPSEȘTE", self.stare(ZI)["rezultat"])
        self.assertEqual(self.stare(urm)["rezultat"], "gata")
        self.assertEqual(self.rulate, NUME_PASI)
        self.assertEqual(self.comenzi["recount"][-1], urm)

    def test_noptile_planificate(self):
        self.assertEqual(L.noptile(datetime(2026, 11, 6, 23, 0), self.ORA, datetime(2026, 11, 8, 12, 0)),
                         [(datetime(2026, 11, 7, 0, 15), "2026-11-06"), (datetime(2026, 11, 8, 0, 15), "2026-11-07")])
        self.assertEqual(len(L.noptile(datetime(2026, 11, 6, 23, 0), self.ORA, None)), 7)


class TestCapatJurnal(Cutie):
    def membru(self, ora: str) -> bytes:
        t = datetime.fromisoformat(f"{ZI}T{ora}").timestamp()
        return gzip.compress((json.dumps({"t0": t, "tip": "passenger", "p": [[0, 0.1, 0.1]]}) + "\n").encode())

    def capat(self, date_brute: bytes):
        L.jurnal(ZI).write_bytes(date_brute)
        return L.capat_jurnal(L.jurnal(ZI))

    def test_ia_cel_mai_mare_inceput_din_coada(self):
        # o mașină parcată urmărită ore întregi se scrie la sfârșit, cu un început vechi
        t = self.capat(self.membru("23:50:00") + self.membru("23:59:00") + self.membru("20:00:00"))
        self.assertEqual(datetime.fromtimestamp(t).strftime("%H:%M"), "23:59")

    def test_sare_peste_membrii_stricati(self):
        rupt = self.membru("23:59:30")
        t = self.capat(self.membru("23:50:00") + rupt[:len(rupt) // 2] + self.membru("23:58:00") + b"\x1f\x8b\x08gunoi")
        self.assertEqual(datetime.fromtimestamp(t).strftime("%H:%M"), "23:58")

    def test_jurnal_fara_niciun_membru_bun(self):
        self.assertIsNone(self.capat(b"gunoi"))
        self.assertIsNone(self.capat(b""))

    def test_verificarea_trece_pentru_o_zi_incheiata_mai_devreme(self):
        L.jurnal(ZI).write_bytes(self.membru("08:29:00"))
        (L.COUNTS_DIR / f"numaratori_{ZI}.csv").write_text(f"inceput\n{ZI} 08:15:00\n", encoding="utf-8")
        self.assertIsNone(L.verifica_capat(ZI))

    def test_verificarea_prinde_o_renumarare_oprita_la_mijlocul_zilei(self):
        L.jurnal(ZI).write_bytes(self.membru("23:59:00"))
        (L.COUNTS_DIR / f"numaratori_{ZI}.csv").write_text(f"inceput\n{ZI} 13:45:00\n", encoding="utf-8")
        self.assertIn("13:45", L.verifica_capat(ZI))

    def test_verificarea_nu_opreste_daca_nu_poate_citi_jurnalul(self):
        L.jurnal(ZI).write_bytes(b"gunoi")
        self.assertIsNone(L.verifica_capat(ZI))

    def test_csv_fara_date(self):
        L.jurnal(ZI).write_bytes(self.membru("23:59:00"))
        (L.COUNTS_DIR / f"numaratori_{ZI}.csv").write_text("inceput,sfarsit\n", encoding="utf-8")
        self.assertIn("gol", L.verifica_capat(ZI))


class TestValidareSuprascrie(unittest.TestCase):
    """Reluarea se sprijină pe felul în care `romana.control.validare` scrie --out (fără simulări: `run_all` e înlocuit)."""

    def test_out_se_scrie_o_data_la_sfarsit_si_se_suprascrie(self):
        import pandas as pd

        from romana.control import validare as V

        def rezultat(model: str) -> pd.DataFrame:
            return pd.DataFrame([[model, "zi_x", 1, 1.0] + [0.0] * len(V.DETALII)], columns=V.COLOANE + V.DETALII)

        with tempfile.TemporaryDirectory() as d:
            out, sc = Path(d) / "test.csv", Path(d) / "zi_x.sumocfg"
            sc.write_text("<configuration/>", encoding="utf-8")
            arg = ["PLAN_12_14_12", "--fara-fix", "--scenarii", str(sc), "--seeds", "1", "--fara-alegere", "--out", str(out)]
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(V, "run_all", return_value=rezultat("A")):
                    V.main(arg)
                self.assertEqual(pd.read_csv(out)["model"].tolist(), ["A"])
                with mock.patch.object(V, "run_all", return_value=rezultat("B")):
                    V.main(arg)
                self.assertEqual(pd.read_csv(out)["model"].tolist(), ["B"])     # nu completează fișierul vechi
                with mock.patch.object(V, "run_all", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                    V.main(arg)
                self.assertEqual(pd.read_csv(out)["model"].tolist(), ["B"])     # o rulare întreruptă nu scrie nimic


class TestProceseReale(unittest.TestCase):
    """Procese reale, dar inofensive (`python -c`), fără date și fără SUMO."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.d = Path(tmp.name)

    def test_copilul_scrie_diacritice_si_codul_ajunge_inapoi(self):
        # cu ieșirea redirecționată, fără PYTHONIOENCODING, print('ș→') ar cădea cu UnicodeEncodeError (cp1250)
        f = self.d / "pas.txt"
        fara = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
        with mock.patch.dict(os.environ, fara, clear=True):
            cod = L.ruleaza([sys.executable, "-c", "import sys; print('ș→'); sys.exit(3)"], f)
        self.assertEqual(cod, 3)
        self.assertEqual(f.read_text(encoding="utf-8").strip(), "ș→")

    def test_copilul_ruleaza_din_radacina_cu_codul_din_src(self):
        f = self.d / "pas.txt"
        cod = L.ruleaza([sys.executable, "-c", "import os; print(os.getcwd()); print(os.environ['PYTHONPATH'])"], f)
        self.assertEqual(cod, 0)
        self.assertEqual(f.read_text(encoding="utf-8").split("\n")[:2], [str(ROOT), str(ROOT / "src")])

    def test_prioritatea_copilului_se_noteaza_la_pasii_lungi(self):
        note = []
        with mock.patch.object(L, "PROBA_COPIL_S", 0.3):
            cod = L.ruleaza([sys.executable, "-c", "import time; time.sleep(1.5)"], self.d / "pas.txt", note.append)
        self.assertEqual(cod, 0)
        self.assertEqual(len(note), 1)
        self.assertIn("priorit", note[0])

    def test_contractul_cu_repara(self):
        # modulul adevărat, pe un jurnal sintetic: 0 = întreg, 2 = membri stricați, alt cod = oprire (fișier inexistent)
        membri = [gzip.compress((json.dumps({"t0": 1000.0 + i, "tip": "passenger", "p": [[0, 0.1, 0.1]]}) + "\n").encode())
                  for i in range(5)]
        f = self.d / "traiectorii_2026-11-01.jsonl.gz"
        pas = L.pasi(ZI)[0]
        cmd = lambda fisier: [*pas.comanda[:-1], str(fisier)]
        f.write_bytes(b"".join(membri))
        self.assertEqual(L.ruleaza(cmd(f), self.d / "pas.txt"), 0)
        rupt = membri[2][:len(membri[2]) // 2]
        f.write_bytes(membri[0] + membri[1] + rupt + membri[3] + membri[4])
        self.assertEqual(L.ruleaza(cmd(f), self.d / "pas.txt"), L.COD_MEMBRI_STRICATI)
        self.assertIn(L.COD_MEMBRI_STRICATI, pas.acceptate)
        self.assertNotIn(L.ruleaza(cmd(self.d / "lipsa.gz"), self.d / "pas.txt"), pas.acceptate)

    def test_pasul_blocat_se_opreste_cu_tot_cu_copiii_lui(self):
        # copilul pornește un nepot care scrie PID-ul lui și așteaptă; amândoi trebuie să dispară la depășirea limitei
        import psutil
        f = self.d / "nepot.txt"
        script = self.d / "blocat.py"
        script.write_text(
            "import os, subprocess, sys, time\n"
            "if len(sys.argv) > 2:\n"
            "    open(sys.argv[1], 'w').write(str(os.getpid()))\n"
            "    time.sleep(120)\n"
            "else:\n"
            "    subprocess.Popen([sys.executable, __file__, sys.argv[1], 'nepot'])\n"
            "    time.sleep(120)\n", encoding="utf-8")
        note = []
        with mock.patch.object(L, "PROBA_COPIL_S", 5.0), mock.patch.object(L, "LIMITA_PAS_S", 6.0):
            cod = L.ruleaza([sys.executable, str(script), str(f)], self.d / "pas.txt", note.append)
        self.assertEqual(cod, L.COD_DEPASIT)
        self.assertIn("limita", note[-1])
        with self.assertRaises(psutil.NoSuchProcess):       # nepotul a apucat să pornească și a fost oprit
            psutil.Process(int(f.read_text())).wait(timeout=5)
            psutil.Process(int(f.read_text()))

    @unittest.skipUnless(os.name == "nt", "prioritățile BELOW_NORMAL există doar pe Windows")
    def test_copiii_mostenesc_prioritatea_scazuta(self):
        # într-un proces separat, ca testele să nu rămână la prioritate scăzută: copil direct și proces de lucru, ca în validare
        script = self.d / "proba.py"
        script.write_text(
            "import psutil, subprocess, sys\n"
            "from concurrent.futures import ProcessPoolExecutor\n"
            "from romana.lant_zilnic import prioritate_scazuta\n"
            "def citeste():\n"
            "    return int(psutil.Process().nice())\n"
            "if __name__ == '__main__':\n"
            "    ok, text = prioritate_scazuta()\n"
            "    copil = subprocess.run([sys.executable, '-c', 'import psutil; print(int(psutil.Process().nice()))'],\n"
            "                           capture_output=True, text=True).stdout.strip()\n"
            "    with ProcessPoolExecutor(max_workers=1) as ex:\n"
            "        lucru = ex.submit(citeste).result()\n"
            "    print(int(ok), citeste(), copil, lucru)\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=self.d,
                           env=dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.split(), ["1", str(L.BELOW_NORMAL), str(L.BELOW_NORMAL), str(L.BELOW_NORMAL)])

    @unittest.skipUnless(os.name == "nt", "prioritățile BELOW_NORMAL există doar pe Windows")
    def test_prioritatea_neaplicata_se_noteaza_deschis(self):
        import psutil
        with mock.patch.object(psutil, "Process") as P:
            P.return_value.nice.return_value = 32   # Normal: cererea n-a avut efect
            ok, text = L.prioritate_scazuta()
        self.assertFalse(ok)
        self.assertIn("ATENȚIE", text)
        self.assertIn("32", text)
        with mock.patch.object(psutil, "Process", side_effect=psutil.AccessDenied(1)):
            ok, text = L.prioritate_scazuta()
        self.assertFalse(ok)
        self.assertIn("ATENȚIE", text)

    def test_starea_se_scrie_atomic_si_se_citeste_inapoi(self):
        with mock.patch.object(L, "DIR_LANT", self.d):
            (self.d / ZI).mkdir()
            L.scrie_stare(ZI, {"zi": ZI, "pasi": {"calitate": {"cod": 0}}})
            s = L.citeste_stare(ZI)
            self.assertEqual(s["pasi"]["calitate"]["cod"], 0)
            self.assertIn("actualizat", s)
            self.assertEqual(sorted(p.name for p in (self.d / ZI).iterdir()), ["stare.json"])
            with mock.patch("os.replace", side_effect=PermissionError("ținut deschis")), mock.patch("time.sleep"):
                note = []
                L.scrie_stare(ZI, {"zi": "altă stare"}, note.append)     # nu oprește lanțul, dar se notează
            self.assertEqual(len(note), 1)
            self.assertEqual(L.citeste_stare(ZI)["zi"], ZI)      # rămâne starea veche, întreagă


if __name__ == "__main__":
    unittest.main()
