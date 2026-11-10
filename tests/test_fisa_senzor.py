"""Teste pentru fișa senzorului (`romana.vision.fisa_senzor`, § 4.6): jurnale sintetice mici, scrise într-un dosar temporar
cu aceleași funcții ca în colectare (rândul de minut și evenimentele vegherii, golurile paznicului, numărătorile), plus o
probă opțională pe jurnalele reale, la tăietura inventarului pentru M2 (se sare dacă jurnalele lipsesc).

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_fisa_senzor
"""
import contextlib
import csv
import io
import json
import math
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from romana.vision import fisa_senzor as fs
from romana.vision.od_counter import write_csv
from romana.vision.paznic import scrie_repornire
from romana.vision.veghe import CSV_CAP, _eveniment

# Numele programului colectării, din bucăți: paznicul ia drept o colectare posibilă orice proces care îl pomenește întreg.
PROG = "run" + "_vision"


def Z(zi: int, h: int, m: int = 0, s: int = 0) -> float:
    """O oră din iunie 2026 (fără schimbare de oră în preajmă), ca marcaj de timp local."""
    return datetime(2026, 6, zi, h, m, s).timestamp()


START = Z(10, 8, 0, 30)          # pornirea manuală a colectării (viziune_2026-06-10.log)
CUT = Z(12, 5, 0, 30)
G1 = (Z(10, 12, 0, 20), Z(10, 12, 10, 40))     # oprire anunțată
G2 = (Z(11, 3, 0, 10), Z(11, 3, 3, 30))        # cădere neprevăzută
NASTERI = {"viziune_2026-06-01.log": Z(1, 10),                 # o colectare mai veche, încheiată
           "viziune_2026-06-10.log": START,
           "viziune_2026-06-10_121008.log": Z(10, 12, 10, 8),  # pornită de paznic (numită în nota pornirii)
           "viziune_2026-06-11_030213.log": Z(11, 3, 2, 13)}   # pornită de paznic, nenumită: în golul G2
# pauzele, pe rândul în care le scrie veghea: (începutul, durata)
EVENIMENTE = {Z(10, 9, 31): [(Z(10, 9, 30, 5), 25)],
              Z(10, 10, 16): [(Z(10, 10, 14, 50), 40), (Z(10, 10, 15, 30), 35)],   # lipite: un cadru la 10:15:30
              Z(10, 12, 12): [(Z(10, 12, 0, 15), 20)],                              # atinge golul G1: nu se numără
              Z(10, 14, 3): [(Z(10, 14, 0, 50), 75)],                               # acoperă minutul 14:01
              Z(11, 0, 0): [(Z(10, 23, 59, 50), 20)],                               # începută înainte de miezul nopții
              Z(12, 5, 1): [(Z(12, 5, 0, 20), 30)],                                 # peste tăietură: 10 s înaintea ei
              Z(12, 5, 2): [(Z(12, 5, 1, 10), 12)]}                                 # după tăietură
VECHI = {Z(10, 14, 1): 12.0, Z(10, 14, 2): 70.0}    # rânduri scrise în timpul pauzei lungi: starea veche, fps-ul vechi


def contor(t: float) -> int:
    """Contorul de reconectări al colectării la minutul t: fiecare rulare îl ia de la 0."""
    if t < G1[0]:
        return 0 if t < Z(10, 9, 31) else 1 if t == Z(10, 9, 31) else 3 if t < Z(10, 11) else 4
    if t < G2[0]:
        return 0 if t < Z(10, 18) else 2
    return 1


def minute_veghe() -> list[float]:
    """Minutele cu rând: veghea se oprește odată cu colectarea și sare un minut (alunecarea buclei la 16:30)."""
    out, t = [], Z(10, 8, 2)
    while t <= Z(12, 5, 3):
        if not (Z(10, 12) <= t <= Z(10, 12, 11) or Z(11, 3) <= t <= Z(11, 3, 4) or t == Z(10, 16, 30)):
            out.append(t)
        t += 60
    return out


def scrie_veghe(f: Path) -> None:
    playlist = {"citiri": [{"ultimul_segment_in_urma_s": 2.0}, {"ultimul_segment_in_urma_s": 7.5}], "avanseaza": True}
    with open(f, "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(CSV_CAP)
        for t in minute_veghe():
            r = dict.fromkeys(CSV_CAP, "")
            r.update(ora=datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M"),
                     fps=9.9 if t in VECHI else (5.5 if int(t // 60) % 3 == 0 else 6.0),
                     varsta_stare_s=VECHI.get(t, 0.6), reconectari=contor(t), episoade_flux_30min=0, pauze_5min=0,
                     urmarite=40, pasi=60000, traiectorii=1900, in_miscare=900, oprite=200, fara_traiectorii_s=0,
                     evenimente="; ".join(_eveniment(e, playlist, "rețea: 700 kB/s înainte; CPU: 30%")
                                          for e in EVENIMENTE.get(t, [])))
            w.writerow([r[c] for c in CSV_CAP])


PAZNIC = {
    "paznic_2026-06-10.log": [
        "2026-06-10T08:01:00 paznic pornit, până la 2026-06-20T09:00:00: program -m romana.vision.x",
        "2026-06-10T08:01:00 în regulă: 2 procese, o colectare, starea are 0 s",
        "2026-06-10T11:59:50 oprire anunțată (fara_repornire): nu repornesc nimic",
        "2026-06-10T12:09:05 procesul nu se vede (verificarea 1 din 2): mai aștept",
        "2026-06-10T12:10:05 repornire, încercarea 1: procesul lipsește",
        f"2026-06-10T12:10:08 {PROG} pornit: lansatorul are PID 4321; jurnale viziune_2026-06-10_121008.log, "
        "viziune_2026-06-10_121008.err; ultima dovadă de viață 2026-06-10T12:00:20",
        "2026-06-10T12:11:08 jurnalul zilei crește: prima traiectorie nouă la 2026-06-10T12:10:40"],
    "paznic_2026-06-11.log": [
        "2026-06-11T02:40:00 oprire anunțată (fara_repornire): nu repornesc nimic",      # prea veche pentru G2
        "2026-06-11T03:01:10 procesul nu se vede (verificarea 1 din 2): mai aștept",
        "2026-06-11T03:02:10 repornire, încercarea 1: procesul lipsește (ultimele erori: x)",
        "Traceback (most recent call last):",                                             # rând fără oră: se sare
        "2026-06-11T03:04:10 jurnalul zilei crește: prima traiectorie nouă la 2026-06-11T03:03:30"]}


def stare_lant(zi: str, pornit: str, rezultat: str, pasi: dict) -> dict:
    return {"zi": zi, "pornit": pornit, "rezultat": rezultat,
            "pasi": {n: {"cod": c, "inceput": a, "sfarsit": b, "comanda": ["python", "-m", n]}
                     for n, (c, a, b) in pasi.items()}}


def interval(dosar: Path, a: float, b: float, intrari: dict, pietoni: int = 0) -> None:
    write_csv({"start": a, "end": b, "od": {}, "in": intrari, "out": {},
               "pietoni": {("magheru", "trecere_magheru"): pietoni} if pietoni else {}}, dosar)


def construieste(d: Path) -> dict:
    """Jurnalele scenariului, în dosarul d; întoarce dosarele pentru `fisa`."""
    loguri, lant, cor, num = d / "logs", d / "lant", d / "lant_cor", d / "counts"
    for x in (loguri, lant, cor, num):
        x.mkdir()
    scrie_veghe(loguri / "veghe_2026-06-10.csv")
    for g in (G1, G2):
        scrie_repornire(loguri, *g)
    for nume, randuri in PAZNIC.items():
        (loguri / nume).write_text("\n".join(randuri) + "\n", encoding="utf-8")
    for nume in NASTERI:
        (loguri / nume).write_text("", encoding="utf-8")
    # (dosarul, ziua, rezultatul, pașii: numele → (codul, începutul, sfârșitul)); lant_cor nu are ziua 2026-06-11
    for dosar, zi, rezultat, pasi in (
            (lant, "2026-06-01", "gata", {"a": (0, "2026-06-02T00:15:00", "2026-06-02T01:00:00")}),   # de dinainte
            (lant, "2026-06-10", "gata", {"a": (0, "2026-06-11T00:15:00", "2026-06-11T00:40:00"),
                                          "b": (0, "2026-06-11T00:40:00", "2026-06-11T01:30:00")}),
            (lant, "2026-06-11", "cu_esecuri: b", {"a": (0, "2026-06-12T00:15:00", "2026-06-12T00:30:00"),
                                                   "b": (1, "2026-06-12T00:30:00", "2026-06-12T02:00:00")}),
            (cor, "2026-06-10", "gata", {"a": (0, "2026-06-11T03:30:00", "2026-06-11T04:10:00")})):
        (dosar / zi).mkdir()
        continut = stare_lant(zi, min(a for _, a, _ in pasi.values()), rezultat, pasi)
        (dosar / zi / "stare.json").write_text(json.dumps(continut, ensure_ascii=False), encoding="utf-8")
    interval(num, Z(10, 7), Z(10, 7, 10), {("magheru", "passenger"): 5}, 3)          # proba de dinaintea începutului
    interval(num, Z(10, 8), Z(10, 8, 15), {("magheru", "passenger"): 100, ("dacia_est", "bus"): 5}, 7)
    interval(num, Z(10, 8, 15), Z(10, 8, 30), {("magheru", "passenger"): 120, ("dacia_vest", "truck"): 3,
                                                ("catargiu", "bicycle"): 1}, 10)
    interval(num, Z(10, 12), G1[0], {("magheru", "passenger"): 2})                    # sfertul tăiat de oprire
    interval(num, Z(10, 23, 45), Z(11, 0), {("dacia_est", "motorcycle"): 2})
    interval(num, Z(11, 0), Z(11, 0, 15), {("magheru", "passenger"): 30}, 1)
    interval(num, Z(12, 4, 45), Z(12, 5), {("magheru", "passenger"): 40})
    interval(num, Z(12, 5), Z(12, 5, 15), {("magheru", "passenger"): 50}, 4)          # se încheie după tăietură
    return {"loguri": loguri, "dosar_numaratori": num,
            "lanturi": {"lant": (lant, fs.LANTURI["lant"][1]), "lant_cor": (cor, fs.LANTURI["lant_cor"][1])}}


class TestScenariu(unittest.TestCase):
    """Două zile sintetice: o pornire manuală, o oprire anunțată, o cădere, pauze, reconectări, lanțuri și numărători."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = Path(cls.tmp.name)
        cls.dosare = construieste(cls.d)
        cls.f = fs.fisa(CUT, nastere=lambda p: NASTERI.get(p.name), **cls.dosare)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_inceputul_e_ultima_pornire_care_nu_e_o_repornire(self):
        self.assertEqual(self.f["inceput"], "2026-06-10T08:00:30")
        self.assertIn("viziune_2026-06-10.log", self.f["sursa_inceputului"])
        self.assertEqual(self.f["durata"]["ore"], round((CUT - START) / 3600, 2))

    def test_opririle_anuntate_si_caderile(self):
        o = self.f["opriri"]
        self.assertEqual((o["anuntate"], o["caderi_neprevazute"], o["durata_s"]), (1, 1, 620 + 200))
        self.assertEqual([x["anuntata"] for x in o["lista"]], [True, False])
        self.assertEqual(o["lista"][1]["motivul_repornirii"], "procesul lipsește (ultimele erori: x)")
        self.assertEqual(self.f["reporniri_paznic"]["numar"], 2)

    def test_pauzele(self):
        p = self.f["pauze"]
        self.assertEqual((p["numar"], p["durata_s"], p["cea_mai_lunga_s"]), (6, 25 + 40 + 35 + 75 + 20 + 10, 75))
        inceputuri = [x["inceput"] for x in p["lista"]]
        self.assertIn("2026-06-10T23:59:50", inceputuri)              # ziua de dinaintea rândului
        self.assertNotIn("2026-06-10T12:00:15", inceputuri)           # ține de oprirea G1
        self.assertNotIn("2026-06-12T05:01:10", inceputuri)           # după tăietură

    def test_minutele_fara_cadre(self):
        m = self.f["minute"]
        self.assertEqual(m["intregi"], math.floor(CUT / 60) - math.ceil(START / 60))
        # G1: 12:01–12:09; G2: 03:01–03:02; pauza lungă: 14:01; cele două pauze lipite au un cadru la 10:15:30
        self.assertEqual(m["fara_cadre"], 9 + 2 + 1)
        self.assertEqual(m["cu_cadre"], m["intregi"] - 12)
        self.assertAlmostEqual(self.f["timp"]["pondere_colectare_pornita"], round(1 - 820 / (CUT - START), 5))

    def test_cadrele_pe_secunda_doar_cu_starea_proaspata(self):
        c = self.f["cadre_pe_secunda"]
        in_fereastra = [t for t in minute_veghe() if t >= START and t + 60 <= CUT]
        self.assertEqual(self.f["veghe"]["randuri"], len(in_fereastra))
        self.assertEqual(c["randuri"], len(in_fereastra) - len(VECHI))
        self.assertEqual((c["mediana"], c["maxim"]), (6.0, 6.0))

    def test_reconectarile_pe_toate_rularile(self):
        r = self.f["reconectari"]
        # rularea 1: +1, +2 (un episod), +1; rularea 2: +2; rularea 3: +1 chiar de la primul rând (lângă golul G2)
        self.assertEqual((r["cresteri_contor"], r["episoade"], r["refacute_singure"]), (7, 4, 3))
        self.assertEqual([e["cresteri"] for e in r["lista"]], [3, 1, 2, 1])

    def test_lanturile_de_noapte(self):
        lt = self.f["lanturi"]
        self.assertEqual((lt["lant"]["asteptate"], lt["lant"]["pe_stari"]), (2, {"incheiat": 1, "esuat": 1}))
        self.assertEqual((lt["lant_cor"]["asteptate"], lt["lant_cor"]["pe_stari"]), (2, {"incheiat": 1, "lipsa": 1}))
        self.assertEqual(lt["total"], {"asteptate": 4, "incheiate": 2})
        self.assertNotIn("2026-06-01", lt["lant"]["zile"])           # de dinaintea începutului colectării

    def test_vehiculele_pe_zile_si_pietonii(self):
        v = self.f["vehicule"]
        z10, z11, z12 = (v["pe_zile"][z] for z in ("2026-06-10", "2026-06-11", "2026-06-12"))
        self.assertEqual(z10["pe_clase"], {"passenger": 222, "bus": 5, "truck": 3, "motorcycle": 2, "bicycle": 1})
        self.assertEqual((z10["vehicule"], z10["pietoni"], z10["intervale"]), (233, 17, 4))
        self.assertEqual(z10["de_la"], "2026-06-10T08:00:30")
        self.assertEqual((z11["vehicule"], z11["pietoni"]), (30, 1))
        self.assertEqual((z12["vehicule"], z12["pietoni"]), (40, 0))
        self.assertEqual((v["total"], v["pietoni_total"]), (303, 18))

    def test_main_scrie_json_si_md(self):
        js, md, ecran = self.d / "iesiri" / "fisa.json", self.d / "iesiri" / "fisa.md", io.StringIO()
        with contextlib.redirect_stdout(ecran):
            cod = fs.main(["--pana-la", "2026-06-12 05:00:30", "--de-la", "2026-06-10 08:00:30",
                           "--loguri", str(self.dosare["loguri"]), "--lant", str(self.d / "lant"),
                           "--lant-cor", str(self.d / "lant_cor"), "--numaratori", str(self.d / "counts"),
                           "--out-json", str(js), "--out-md", str(md)])
        self.assertEqual(cod, 0)
        f = json.loads(js.read_text(encoding="utf-8"))
        for cheie in ("inceput", "minute", "timp", "pauze", "reconectari", "opriri", "lanturi", "vehicule"):
            self.assertEqual(f[cheie], self.f[cheie], cheie)
        text = md.read_text(encoding="utf-8")
        self.assertIn("| Minute cu cadre prelucrate | ", text)
        self.assertIn("| mie. 10.06 | 233 | 222 | 5 | 3 | 2 | 1 | 17 |", text)
        self.assertIn("| Total | 303 | 292 | 5 | 3 | 2 | 1 | 18 |", text)
        self.assertIn("Fișa senzorului: colectarea de la cameră, până la 12.06.2026 05:00:30", ecran.getvalue())

    def test_main_fara_inceput_se_opreste(self):
        # datele de creare reale ale fișierelor de probă sunt de azi, după tăietură: începutul nu se poate afla
        ecran = io.StringIO()
        with contextlib.redirect_stderr(ecran):
            cod = fs.main(["--pana-la", "2026-06-12 05:00:30", "--loguri", str(self.dosare["loguri"])])
        self.assertEqual(cod, 2)
        self.assertIn("--de-la", ecran.getvalue())


class TestPiese(unittest.TestCase):
    def test_doua_evenimente_intr_un_rand(self):
        text = "; ".join(_eveniment(e, None, "rețea: 1 kB/s; CPU: 2%") for e in [(Z(10, 9, 0, 1), 11), (Z(10, 9, 0, 40), 13)])
        r = fs.RandVeghe(Z(10, 9, 1), 6.0, 0.5, 0, text)
        self.assertEqual(fs.pauze_din([r]), [(Z(10, 9, 0, 1), 11), (Z(10, 9, 0, 40), 13)])

    def test_aceeasi_pauza_in_doua_randuri_se_numara_o_data(self):
        e = _eveniment((Z(10, 9, 0, 1), 11), None)
        randuri = [fs.RandVeghe(Z(10, 9, 1), 6.0, 0.5, 0, e), fs.RandVeghe(Z(10, 9, 2), 6.0, 0.5, 0, e)]
        self.assertEqual(len(fs.pauze_din(randuri)), 1)

    def test_golul_peste_miezul_noptii_o_singura_data(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            a, b = Z(10, 23, 58), Z(11, 0, 2, 30)
            scrie_repornire(d, a, b - 20)                  # rândul scris la pornire...
            scrie_repornire(d, a, b, vechi=b - 20)         # ...primește ora primei traiectorii, în ambele fișiere
            (d / "reporniri_2026-06-12.csv").write_text("oprire,repornire\n2026-06-12T10:00:00,2026-06-12T09:00:00\n",
                                                        encoding="utf-8")       # repornirea înaintea opririi: se sare
            self.assertEqual(len(list(d.glob("reporniri_*.csv"))), 3)
            goluri = fs.citeste_goluri(d)
        self.assertEqual([(g.oprire, g.repornire) for g in goluri], [(a, b)])

    def test_taietura_la_miezul_noptii_fara_randul_zilei_care_incepe(self):
        # ca fișa de sâmbătă, cu tăietura 14.11, 00:00: ziua care abia începe n-are niciun interval încheiat până la tăietură,
        # deci nu apare cu un rând numai cu zerouri (fișa de la M2, cu tăietura 06.11, 00:00, avea „vin. 06.11”)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            interval(d, Z(10, 23, 45), Z(11, 0), {("magheru", "passenger"): 7}, 2)    # în fișierul zilei de 10.06
            interval(d, Z(11, 0), Z(11, 0, 15), {("magheru", "passenger"): 9}, 1)     # se încheie după tăietură
            v = fs.numaratori(d, Z(10, 8), Z(11, 0))
            self.assertEqual(list(v["pe_zile"]), ["2026-06-10"])
            z10 = v["pe_zile"]["2026-06-10"]
            self.assertEqual((z10["vehicule"], z10["pietoni"], z10["intervale"]), (7, 2, 1))
            self.assertEqual((z10["pana_la"], fs.ore_zi(z10, "2026-06-10")), ("2026-06-11T00:00:00", "23:45–24:00"))
            self.assertEqual((v["total"], v["pietoni_total"]), (7, 2))
            # o secundă după miezul nopții, ziua nouă e în fereastră, fără niciun interval încheiat încă
            v = fs.numaratori(d, Z(10, 8), Z(11, 0, 0, 1))
            self.assertEqual(list(v["pe_zile"]), ["2026-06-10", "2026-06-11"])
            self.assertEqual((v["pe_zile"]["2026-06-11"]["intervale"], v["total"]), (0, 7))
            # la sfertul următor, intervalul de la miezul nopții intră în ziua lui
            v = fs.numaratori(d, Z(10, 8), Z(11, 0, 15))
            self.assertEqual((v["pe_zile"]["2026-06-11"]["vehicule"], v["pe_zile"]["2026-06-11"]["pietoni"]), (9, 1))
            self.assertEqual((v["total"], v["pietoni_total"]), (16, 3))
            # și o fereastră care începe fix la miezul nopții începe cu ziua aceea
            self.assertEqual(list(fs.numaratori(d, Z(11, 0), Z(11, 0, 15))["pe_zile"]), ["2026-06-11"])

    def test_anuntul_poate_veni_dupa_oprire(self):
        # ca pe 05.11: fara_repornire pus înaintea opririi, dar văzut de paznic la verificarea de minut, după ea
        g, vechi = fs.Gol(Z(10, 20, 7, 23), Z(10, 20, 22, 6)), fs.Gol(Z(11, 20), Z(11, 20, 5))
        fs.clasifica_goluri([g, vechi], fs.JurnalPaznic(anunturi=[Z(10, 20, 8, 13), Z(11, 19, 49)]))
        self.assertTrue(g.anuntat)
        self.assertFalse(vechi.anuntat)                    # anunțul are 11 min: nu mai privește golul

    def test_inceputul_sare_peste_reporniri(self):
        porniri = [(Z(1, 10), "a.log"), (Z(10, 8), "b.log"), (Z(10, 12, 10, 8), "c.log"), (Z(11, 3, 2, 13), "d.log")]
        goluri = [fs.Gol(*G1), fs.Gol(*G2)]
        self.assertEqual(fs.inceputul(porniri, goluri, {"c.log": 0.0}, CUT), (Z(10, 8), "b.log"))
        self.assertEqual(fs.inceputul(porniri, goluri, {}, CUT), (Z(10, 8), "b.log"))     # c.log stă și în golul G1
        self.assertEqual(fs.inceputul(porniri, [], {}, CUT), (Z(11, 3, 2, 13), "d.log"))  # fără goluri: o pornire nouă
        self.assertEqual(fs.inceputul(porniri, goluri, {}, Z(5, 0)), (Z(1, 10), "a.log"))
        self.assertIsNone(fs.inceputul(porniri, goluri, {}, Z(1, 9)))

    def test_reconectarile_de_la_mijlocul_rularii(self):
        randuri = [fs.RandVeghe(Z(10, 9, k), 6.0, 0.5, n, "") for k, n in enumerate([0, 2, 2, 3, 3, 0, 1])]
        porniri = [(Z(10, 9, 4, 30), "x.log")]             # rularea nouă: contorul o ia de la 0
        self.assertEqual(fs.reconectari(randuri, porniri, [], Z(10, 9), Z(10, 10)),
                         [(Z(10, 9, 1), 2), (Z(10, 9, 3), 1), (Z(10, 9, 6), 1)])
        # fereastra începe după a doua creștere: valoarea de dinainte e doar punctul de plecare
        self.assertEqual(fs.reconectari(randuri, porniri, [], Z(10, 9, 2), Z(10, 10)),
                         [(Z(10, 9, 3), 1), (Z(10, 9, 6), 1)])
        self.assertEqual(fs.episoade([(Z(10, 9, 1), 2), (Z(10, 9, 3), 1), (Z(10, 9, 6), 1)]),
                         [(Z(10, 9, 1), Z(10, 9, 3), 3), (Z(10, 9, 6), Z(10, 9, 6), 1)])

    def test_minutele_dintr_un_gol(self):
        minute = fs.minute_intregi(Z(10, 8, 0, 30), Z(10, 13))
        self.assertEqual(minute.start, int(Z(10, 8, 1) // 60))
        acoperite = fs.minute_in(*G1, minute)
        self.assertEqual((acoperite.start * 60, acoperite.stop * 60), (Z(10, 12, 1), Z(10, 12, 10)))
        self.assertEqual(len(fs.minute_in(Z(10, 9, 0, 10), Z(10, 9, 0, 59), minute)), 0)

    def test_starea_unui_lant_la_taietura(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "stare.json"
            f.write_text(json.dumps(stare_lant("z", "2026-06-11T00:15:00", "gata",
                                               {"a": (0, "2026-06-11T00:15:00", "2026-06-11T01:30:00")})), encoding="utf-8")
            self.assertEqual(fs.stare_lant(f, Z(11, 2))["stare"], "incheiat")
            self.assertEqual(fs.stare_lant(f, Z(11, 1))["stare"], "in_curs")
            self.assertEqual(fs.stare_lant(f, Z(11, 0))["stare"], "neinceput")
            f.write_text(json.dumps(stare_lant("z", "2026-06-11T00:15:00", "gata_fara_simulari",
                                               {"a": (0, "2026-06-11T00:15:00", "2026-06-11T01:30:00")})), encoding="utf-8")
            self.assertEqual(fs.stare_lant(f, Z(11, 2))["stare"], "incheiat")      # zilele sigilate
            f.write_text(json.dumps(stare_lant("z", "2026-06-11T00:15:00", "oprit: renumărarea a eșuat",
                                               {"a": (3, "2026-06-11T00:15:00", "2026-06-11T00:20:00")})), encoding="utf-8")
            self.assertEqual(fs.stare_lant(f, Z(11, 2))["stare"], "esuat")
            for stricat in ("{nu e JSON", "[1, 2]"):
                f.write_text(stricat, encoding="utf-8")
                self.assertEqual(fs.stare_lant(f, Z(11, 2))["stare"], "necitibil", stricat)
            self.assertEqual(fs.stare_lant(Path(d) / "lipsa.json", Z(11, 2))["stare"], "lipsa")

    def test_scrierea_numerelor(self):
        self.assertEqual((fs.nr(277271), fs.nr(98.804, 2), fs.pct(0.98804)), ("277 271", "98,80", "98,8%"))
        self.assertEqual(fs.durata_text(386444), "4 zile, 11 h 20 min")
        self.assertEqual(fs.durata_text(4730), "1 h 18 min 50 s")
        self.assertEqual(fs.durata_text(715), "11 min 55 s")


def _jurnale_reale() -> bool:
    """Jurnalele colectării de la 01.11, cu datele de creare păstrate (o copie a dosarului le-ar schimba)."""
    pornire = fs.LOG_DIR / "viziune_2026-11-01.log"
    if not all(f.exists() for f in (pornire, fs.LOG_DIR / "veghe_2026-11-01.csv", fs.LOG_DIR / "reporniri_2026-11-05.csv")):
        return False
    t = fs.data_crearii(pornire)
    return t is not None and datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S") == "2026-11-01 09:04:46"


@unittest.skipUnless(_jurnale_reale(), "jurnalele reale ale colectării lipsesc (sau datele lor de creare nu s-au păstrat)")
class TestJurnaleReale(unittest.TestCase):
    """Cifrele inventarului pentru M2 (outputs/prezentare/surse_m2/plan_v3/m2_inv_iot.md), la tăietura lui. Doar citire."""

    def test_cifrele_inventarului_la_taietura(self):
        f = fs.fisa(fs.ora("2026-11-05 20:25:31"))
        self.assertEqual((f["inceput"], f["durata"]["ore"]), ("2026-11-01T09:04:46", 107.35))
        self.assertEqual(round(100 * f["minute"]["pondere_cu_cadre"], 1), 98.8)
        self.assertEqual(round(100 * f["timp"]["pondere_colectare_pornita"], 1), 98.8)
        self.assertEqual(f["cadre_pe_secunda"]["mediana"], 5.98)
        self.assertEqual((f["pauze"]["numar"], f["pauze"]["durata_s"]), (30, 715))
        # inventarul a dat 14: contorul rulării a doua; prima rulare mai are o creștere (01.11, 18:41), deci 15, în 10 episoade
        self.assertEqual((f["reconectari"]["cresteri_contor"], f["reconectari"]["episoade"]), (15, 10))
        self.assertEqual((f["opriri"]["anuntate"], f["opriri"]["caderi_neprevazute"]), (2, 0))
        self.assertEqual(f["lanturi"]["total"], {"asteptate": 6, "incheiate": 6})


if __name__ == "__main__":
    unittest.main()
