"""Teste pentru sondarea dispeceratului (`romana.dashboard.sondare`): pașii, pachetul static, citirea răspunsurilor, logica din
JavaScript (cu Node.js sau, dacă lipsește, într-un browser) și, într-un browser fără fereastră (Chrome sau Edge), parcursul complet al paginii.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_sondare
"""
import csv
import functools
import hashlib
import html
import http.server
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from romana.dashboard import sondare as s

RADACINA = Path(__file__).resolve().parents[1]
HASH_M1 = "f7986e77a3a7dc04a0319fdb4230629a7f129ad7a02a97824d9fa0056e1c0b84"
BROWSERE = (r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            shutil.which("chromium") or "", shutil.which("google-chrome") or "")
BROWSER = next((b for b in BROWSERE if b and Path(b).exists()), None)
NODE = next((n for n in (shutil.which("node") or "", r"C:\Program Files\nodejs\node.exe") if n and Path(n).exists()), None)

RASPUNS = """Sondare dispecerat Piața Romană, v1
Grup {grup}, ordine {ordine}, ecran 1536x730, {sfarsit}
Folosește calculatorul: Rar sau deloc

Prima variantă
Sarcina 1, cine schimbă culorile: 21 s, apăsări 0, comenzi 0
Cine schimbă culorile: Un om, de la acest ecran (așteptat: Un calculator, singur)
Sarcina 2, cea mai lungă coadă: 24 s, apăsări 1, comenzi 0, altă fereastră 5 s
Cele mai multe mașini: Dacia vest
Sarcina 3, verde pe Dacia: 43 s, apăsări 4, comenzi 2, reușit. Manual > Confirm > E–V > Confirm
Culoarea pe Magheru: Roșu
A văzut schimbarea: Da, clar
Sarcina 4, înapoi la calculator: 11 s, apăsări 2, comenzi 1, reușit. Program pe cazuri de t > Confirm
A văzut cine conduce: Nu
Linia roșie: O coadă lungă de mașini
Semaforul adevărat: Da (așteptat: Nu)
Cât de ușor: Ușor
Ce a încurcat: text liber secret: unde era butonul

A doua variantă
Sarcina 1, cine schimbă culorile: 9 s, apăsări 0, comenzi 0
Cine schimbă culorile: Un om, de la acest ecran
Sarcina 2, cea mai lungă coadă: 12 s, apăsări 0, comenzi 0, nu reușesc
Cele mai multe mașini: Nu pot spune (așteptat: Magheru)
Sarcina 3, verde pe Dacia: 30 s, apăsări 0, comenzi 0, nu reușesc, nereușit
Culoarea pe Magheru: Galben (așteptat: Verde)
A văzut schimbarea: Nu
Sarcina 4, înapoi la calculator: 8 s, apăsări 2, comenzi 1, reușit. Agent AI > Confirm
A văzut cine conduce: Da, clar
Cât de ușor: Foarte greu

Mai ușoară: A doua
Văzut înainte: Nu
A ajutat cineva: Da, la înțelegerea sarcinilor
"""


def text(grup="a", ordine=1, sfarsit="terminat", k=0):
    # `k` schimbă o durată, ca în răspunsurile adevărate: două texte identice ar fi aceeași trimitere, de două ori
    return RASPUNS.format(grup=grup, ordine=ordine, sfarsit=sfarsit).replace(": 21 s", f": {21 + k} s")


class Primite(unittest.TestCase):
    def setUp(self):
        self.dosar = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dosar, True)
        (self.dosar / "primite").mkdir()
        self.n = 0

    def pune(self, t):
        self.n += 1
        (self.dosar / "primite" / f"R{self.n}.txt").write_text(t, encoding="utf-8")


class TestPasi(unittest.TestCase):
    def test_ordinea_da_versiunile(self):
        for p in s.pasi(("m2", "m1")):
            if "runda" in p:
                self.assertEqual(p["versiune"], ("m2", "m1")[p["runda"]])

    def test_intrebarile_de_perceptie_doar_la_prima_vedere(self):
        ids = [x["id"] for x in s.pasi()]
        for k in ("real", "culori"):
            self.assertIn(f"r1_{k}", ids)
            self.assertNotIn(f"r2_{k}", ids)

    def test_fara_pasi_de_moderator_si_fara_intrebarea_imaginii(self):
        ids = {x["id"] for x in s.pasi()}
        self.assertFalse(ids & {"pregatire", "observatii", "moderator", "sfarsit", "r1_imagine_r", "r2_imagine_r"})
        self.assertEqual(s.pasi()[-1]["tip"], "final")

    def test_durata_e_rezonabil_de_scurta(self):
        self.assertLessEqual(len(s.pasi()), 37)

    def test_etichetele_sunt_unice_in_runda(self):
        vazute = set()
        for p in s.pasi():
            if p.get("eticheta"):
                cheie = (p.get("runda"), p["eticheta"])
                self.assertNotIn(cheie, vazute)
                vazute.add(cheie)
                self.assertNotIn(":", p["eticheta"])

    def test_pe_telefon_textele_nu_spun_dreapta_sau_stanga(self):
        def pe_telefon(t):
            for a, b in s.PE_TELEFON:
                t = t.replace(a, b)
            return t
        for p in s.pasi():
            for t in p.get("text", []):
                self.assertNotRegex(pe_telefon(t), "dreapta|stânga", p["id"])
        html = (s.STATIC / "sondare.html").read_text(encoding="utf-8")
        self.assertNotIn("stânga", pe_telefon(re.search(r'<div id="acoperit">(.*?)</div>', html)[1]))

    def test_debitele_nu_dau_raspunsul_la_coada(self):
        for runda in (0, 1):
            cel_mai_mare = max(s.INTRARI[runda], key=s.INTRARI[runda].get)
            self.assertNotEqual(s.NUME_BRAT[cel_mai_mare], s.corect_coada(runda))

    def test_cele_doua_runde_au_alta_coada_si_alt_sofer(self):
        self.assertNotEqual(s.corect_coada(0), s.corect_coada(1))
        self.assertEqual([r["mod"] for r in s.RUNDE], ["program", "manual"])

    def test_acordul_spune_cinstit_cine_vede_raspunsurile(self):
        acord = next(p for p in s.pasi() if p["id"] == "acord")
        invitat = " ".join(acord["text_invitat"])
        for cuvant in ("Google", "GitHub", "Anthropic", "adresa IP", "se șterg"):
            self.assertIn(cuvant, invitat)
        self.assertNotIn("anonim", invitat.lower())
        self.assertIn("nu se trimite", " ".join(acord["text_deschis"]))


class TestPachet(unittest.TestCase):
    def test_e_la_zi_cu_sursele(self):
        for nume, continut in s.continut_pachet().items():
            cale = s.PACHET / nume
            self.assertTrue(cale.exists(), nume)
            self.assertEqual(cale.read_bytes().replace(b"\r\n", b"\n").decode("utf-8"), continut, f"{nume}: rulați --pachet")
        self.assertTrue((s.DOCS / ".nojekyll").exists())
        for f in (s.STATIC / "fonturi").iterdir():
            self.assertEqual((s.PACHET / "fonturi" / f.name).read_bytes().replace(b"\r\n", b"\n"), f.read_bytes().replace(b"\r\n", b"\n"), f.name)

    def test_fonturile_au_diacriticele_romanesti(self):
        css = (s.STATIC / "fonturi" / "fonturi.css").read_text(encoding="utf-8")
        for fam, greutati in (("Barlow", (400, 500, 600)), ("Barlow Semi Condensed", (500, 600, 700))):
            for g in greutati:
                self.assertEqual(css.count(f"font-family:'{fam}';font-style:normal;font-weight:{g};"), 2, (fam, g))
        for nume in re.findall(r"url\(([^)]+)\)", css):
            self.assertTrue((s.STATIC / "fonturi" / nume).exists(), nume)
        self.assertIn("U+0100-02BA", css)         # ă, ș, ț

    def test_de_unde_vin_fonturile_nu_face_versiunile_diferite(self):
        sursa = s.VERSIUNI["m1"].read_text(encoding="utf-8").replace("\r\n", "\n")
        local = s.RE_FONTURI.sub('<link href="/static/fonturi/fonturi.css" rel="stylesheet">\n', sursa)
        self.assertNotEqual(sursa, local)
        self.assertEqual(s.ecran_static(sursa, "x"), s.ecran_static(local, "x"))

    def test_nicio_pagina_nu_cere_ceva_din_afara(self):
        for nume, continut in s.continut_pachet().items():
            self.assertNotIn("fonts.g", continut, nume)
            for adresa in re.findall(r"""(?:src|href)=["'](https?://[^"']+)""", continut):
                self.assertTrue(adresa.startswith(("https://www.openstreetmap.org/", s.URL_PROIECT)), f"{nume}: {adresa}")

    def test_regula_de_securitate_pe_toate_paginile(self):
        for nume, continut in s.continut_pachet().items():
            if nume.endswith(".html"):
                self.assertIn('http-equiv="Content-Security-Policy"', continut, nume)
                for parte in ("default-src 'none'", "connect-src 'none'", "script-src 'self'", "form-action 'none'", "font-src 'self'"):
                    self.assertIn(parte, continut, nume)
                self.assertNotIn("<script>", continut, f"{nume}: script în pagină")

    def test_ecranul_se_schimba_doar_la_camera(self):
        sursa = s.VERSIUNI["m1"].read_text(encoding="utf-8").replace("\r\n", "\n")
        pagina, script = s.ecran_static(sursa, "m1")
        def corp(t):
            t = re.sub(r"<script.*", "", t[t.index("<body>"):], flags=re.S).replace(s.NOTA_CAMERA, "")
            t = re.sub(r'<h2 id="t-(cam|deb)">.*?</h2>', r"<h2 \1>", t)
            return re.sub(r'<img id="cadru" alt="[^"]*">', "<img>", t)
        self.assertEqual(corp(pagina), corp(sursa).replace(s.SUBSOL_CAMERA, s.SUBSOL_PUBLIC))
        for fals in ("analizată live", "Debite măsurate de cameră", "afișată doar local"):
            self.assertNotIn(fals, pagina)
        self.assertIn(s.NOTA_CAMERA, pagina)
        original = re.search(r"<script>(.*?)</script>", sursa, flags=re.S)[1].strip() + "\n"
        original = original.replace("s.faze.map(", "s.faze.slice(0,5).map(")     # etapa scurtă nu are buton în versiunea M1
        # singura linie în plus: planul de azi se numește în versiunea M1 cum îl numea ea pe cel de atunci
        self.assertEqual(script, original.replace('"/api/video"', json.dumps(s.IMAGINE_PUBLICA)) + "MOD.plan_observat = MOD.plan_scurt;\n")

    def test_un_ecran_schimbat_opreste_pachetul(self):
        with self.assertRaises(SystemExit):
            s.ecran_static("<html>altceva</html>", "m2")

    def test_fotografia_publicata_exista(self):
        self.assertTrue((s.PACHET / s.IMAGINE_PUBLICA).resolve().exists())

    def test_formularul_nu_e_in_depozit(self):
        cale = s.DOSAR / "formular.json"
        if not cale.exists():
            self.skipTest("formularul nu e creat")
        f = json.loads(cale.read_text(encoding="utf-8"))["f"]
        for nume, continut in s.continut_pachet().items():
            self.assertNotIn(f, continut, nume)

    def test_versiunea_m1_e_cea_prezentata(self):
        # conținutul din commit-ul 4bd74f4, borna M1
        continut = s.VERSIUNI["m1"].read_bytes().replace(bytes([13, 10]), bytes([10]))
        self.assertEqual(hashlib.sha256(continut).hexdigest(), HASH_M1)

    def test_linkurile_cer_versiuni_diferite(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / "formular.json").write_text(json.dumps({"f": "X" * 30, "e": "123456"}), encoding="utf-8")
        with mock.patch.object(s, "versiuni_identice", return_value=True), self.assertRaises(SystemExit):
            s.linkuri(d)
        with mock.patch.object(s, "versiuni_identice", return_value=False):
            ll = s.linkuri(d, "https://x/")
        self.assertEqual(ll["a"], [f"https://x/?g=a&o={o}&f={'X' * 30}&e=123456" for o in (1, 2)])
        self.assertEqual(set(ll), set(s.GRUPURI))


class TestRaspuns(Primite):
    def test_antetul(self):
        r = s.citeste_raspuns(text())
        self.assertEqual((r["grup"], r["ordine"], r["ecran"], r["terminat"]), ("a", ("m1", "m2"), "1536x730", True))
        self.assertFalse(s.citeste_raspuns(text(sfarsit="oprit la r1_verde"))["terminat"])
        self.assertIsNone(s.citeste_raspuns("salut"))
        self.assertIsNone(s.citeste_raspuns(text(ordine=7)))

    def test_ordinea_da_versiunea_rundei(self):
        pe_id = {o["id"]: o for o in s.citeste_raspuns(text(ordine=2))["pasi"]}
        self.assertEqual((pe_id["r1_verde"]["versiune"], pe_id["r2_verde"]["versiune"]), ("m2", "m1"))

    def test_sarcina_si_raspunsul(self):
        pe_id = {o["id"]: o for o in s.citeste_raspuns(text())["pasi"]}
        v = pe_id["r1_verde"]
        self.assertEqual((v["durata_s"], v["clicuri"], v["comenzi"], v["reusit"], v["nu_reuseste"]), (43, 4, 2, True, False))
        self.assertEqual(v["traseu"], "Manual > Confirm > E–V > Confirm")
        self.assertEqual((pe_id["r2_verde"]["reusit"], pe_id["r2_verde"]["nu_reuseste"]), (False, True))
        self.assertTrue(pe_id["r2_coada"]["nu_reuseste"])
        self.assertEqual((pe_id["r1_conduce_r"]["valoare"], pe_id["r1_conduce_r"]["corect"]), ("Un om, de la acest ecran", False))
        self.assertTrue(pe_id["r1_coada_r"]["corect"])
        self.assertEqual(pe_id["r1_incurcat"]["valoare"], "text liber secret: unde era butonul")
        self.assertEqual(pe_id["ajutor"]["valoare"], "Da, la înțelegerea sarcinilor")
        self.assertEqual(pe_id["profil_calculator"]["valoare"], "Rar sau deloc")

    def test_toate_masurile_sunt_citite(self):
        ids = {o["id"] for o in s.citeste_raspuns(text())["pasi"]}
        asteptat = {p["id"] for p in s.pasi() if p.get("eticheta")} - {"r2_incurcat"}   # textul liber gol nu apare
        self.assertEqual(ids, asteptat)

    def test_dublurile_probele_si_textele_straine_raman_afara(self):
        self.pune(text())
        self.pune(text())
        self.pune(text(grup="-"))
        self.pune("un mesaj oarecare")
        self.pune(text(grup="c", ordine=2))
        self.assertEqual([c for c, _ in s.raspunsuri_primite(self.dosar)], ["R1", "R5"])

    def test_rezumatul_numara_corect(self):
        self.pune(text())
        self.pune(text(grup="c", ordine=2))
        _, randuri = s.scrie_rezumat(self.dosar)
        self.assertEqual([r["raspuns"] for r in randuri if r["masura"] == "preferinta"], ["m2", "m1"])
        conduce = [r for r in randuri if r["masura"] == "sarcina 1: cine schimbă culorile" and r["runda"] == 1]
        self.assertEqual([r["reusit"] for r in conduce], [False, False])
        coada = [r for r in randuri if r["masura"] == "sarcina 2: cea mai lungă coadă"]
        self.assertEqual([r["reusit"] for r in coada], [True, False, True, False])
        self.assertTrue(all(r["reusit"] for r in randuri if r["masura"] == "sarcina 3: verde pe Dacia" and r["runda"] == 1))
        self.assertEqual(len([r for r in randuri if r["masura"] == "ajutor"]), 2)

    def test_totalurile_pe_grup_versiune_si_prima_runda(self):
        for k, o in enumerate((1, 2, 2, 1)):
            self.pune(text(ordine=o, k=k))
        self.pune(text(grup="c"))
        grup = {(r["grup"], r["masura"], r["versiune"]): r for r in s.pe_grup(s.rezumat(self.dosar))}
        r = grup[("a", "sarcina 3: verde pe Dacia", "m1")]
        self.assertEqual((r["persoane"], r["reusite"], r["persoane_prima_runda"], r["reusite_prima_runda"]), (4, 2, 2, 2))
        self.assertEqual(grup[("c", "sarcina 3: verde pe Dacia", "m1")]["persoane"], 1)
        self.assertEqual(grup[("a", "a avut nevoie de ajutor la sarcini", "")]["persoane"], 4)

    def test_cine_s_a_oprit_nu_intra_in_totaluri(self):
        self.pune(text(sfarsit="oprit la r2_verde"))
        randuri = s.rezumat(self.dosar)
        self.assertTrue(randuri)
        self.assertEqual(s.pe_grup(randuri), [])

    def _trei_si_unul(self):
        for k in range(3):
            self.pune(text(k=k))
        self.pune(text(grup="c"))

    def test_fisierul_public_are_doar_totaluri(self):
        self._trei_si_unul()
        dest = self.dosar / "public.csv"
        s.publica(self.dosar, dest)
        continut = dest.read_text(encoding="utf-8")
        for interzis in ("secret", "R1", "Rar sau deloc", "durata", "clicuri", "1536"):
            self.assertNotIn(interzis, continut)
        with open(dest, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual({r["grup"] for r in rows}, {"a"})      # grupul sub 3 persoane rămâne afară

    def test_la_colegi_se_publica_si_duratele_mediane(self):
        for k in range(3):
            self.pune(text(k=k, grup="c"))
        dest = self.dosar / "public.csv"
        s.publica(self.dosar, dest)
        with open(dest, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cu_durata = [r for r in rows if r["durata_mediana_s"]]
        self.assertTrue(cu_durata)
        self.assertEqual({r["grup"] for r in cu_durata}, {"c"})
        self.assertNotIn("secret", dest.read_text(encoding="utf-8"))

    def test_raspunsurile_de_pe_telefon_se_numara_separat(self):
        for k in range(3):
            self.pune(text(k=k))
        self.pune(text(k=7).replace("ecran 1536x730", "ecran 390x844"))
        grup = {(r["grup"], r["masura"], r["versiune"]): r for r in s.pe_grup(s.rezumat(self.dosar))}
        self.assertEqual(grup[("a", "sarcina 3: verde pe Dacia", "m1")]["persoane"], 3)
        self.assertEqual(grup[("a_telefon", "sarcina 3: verde pe Dacia", "m1")]["persoane"], 1)
        dest = self.dosar / "public.csv"
        s.publica(self.dosar, dest)
        with open(dest, encoding="utf-8") as f:
            self.assertEqual({r["grup"] for r in csv.DictReader(f)}, {"a"})     # o singură persoană pe telefon rămâne afară

    def test_nu_se_publica_sub_trei_persoane(self):
        self.pune(text())
        with self.assertRaises(SystemExit):
            s.publica(self.dosar, self.dosar / "public.csv")
        self.assertFalse((self.dosar / "public.csv").exists())


class VerificaLogica:
    def verifica_logica(self, o):
        self.assertGreaterEqual(o["trecute"], 50)
        for nr, t in enumerate(o["texte"], 1):         # textul scris de JavaScript se citește înapoi în Python
            r = s.citeste_raspuns(t)
            self.assertEqual((r["grup"], r["ordine"]), ("a", {1: ("m1", "m2"), 2: ("m2", "m1")}[nr]))
            self.assertEqual({x["id"] for x in r["pasi"]}, {p["id"] for p in s.pasi() if p.get("eticheta")} - {"r2_incurcat"})
            pe_id = {x["id"]: x for x in r["pasi"]}
            self.assertFalse(pe_id["r1_real"]["corect"])
            self.assertEqual(pe_id["r1_incurcat"]["valoare"], "butonul: unde era?")
            self.assertTrue(pe_id["r2_coada"]["nu_reuseste"])


class Tacut(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@unittest.skipUnless(BROWSER, "nu există Chrome sau Edge pe acest calculator")
class TestInBrowser(VerificaLogica, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Tacut, directory=str(RADACINA)))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def ruleaza(self, pagina, buget_ms):
        url = f"http://127.0.0.1:{self.server.server_address[1]}/tests/{pagina}"
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            r = subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                                f"--user-data-dir={d}", f"--virtual-time-budget={buget_ms}", "--dump-dom", url], capture_output=True, timeout=240)
        m = re.search(r'<pre id="rezultat">(.+?)</pre>', r.stdout.decode("utf-8", "replace"), flags=re.S)
        self.assertIsNotNone(m, f"{pagina}: fără rezultat")
        o = json.loads(html.unescape(m[1]))
        self.assertEqual(o["esuate"], [])
        self.assertGreater(o["trecute"], 0)
        return o

    def test_pagina_cap_coada(self):
        o = self.ruleaza("sondare_cap_coada.html", 240000)
        self.assertLess(o["lungime_link"], 7500)
        r = s.citeste_raspuns(o["text"])
        self.assertTrue(r["terminat"])
        pe_id = {x["id"]: x for x in r["pasi"]}
        self.assertTrue(pe_id["r1_verde"]["reusit"])
        self.assertTrue(pe_id["r1_automat"]["reusit"])
        self.assertTrue(pe_id["r1_conduce_r"]["corect"] and pe_id["r1_coada_r"]["corect"] and pe_id["r1_verde_r"]["corect"])
        self.assertTrue(pe_id["r2_verde"]["nu_reuseste"])
        m2 = {x["id"]: x for x in s.citeste_raspuns(o["text_m2"])["pasi"]}
        self.assertTrue(m2["r1_verde"]["reusit"], "verdele pe Dacia, în versiunea reparată")
        self.assertTrue(m2["r1_automat"]["reusit"], "revenirea la calculator, în versiunea reparată")
        self.assertTrue(m2["r1_conduce_r"]["corect"] and m2["r1_coada_r"]["corect"] and m2["r1_verde_r"]["corect"])
        self.assertEqual(s.citeste_raspuns(o["text_oprit"])["grup"], "c")
        self.assertFalse(s.citeste_raspuns(o["text_oprit"])["terminat"])

    def test_logica_in_browser(self):
        self.verifica_logica(self.ruleaza("sondare_logica.html", 20000))


@unittest.skipUnless(NODE, "Node.js nu e instalat")
class TestCuNode(VerificaLogica, unittest.TestCase):
    def test_logica(self):
        r = subprocess.run([NODE, str(RADACINA / "tests" / "sondare_logica_node.js")], capture_output=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace")[-500:])
        o = json.loads(r.stdout.decode("utf-8"))
        self.assertEqual(o["esuate"], [])
        self.verifica_logica(o)


if __name__ == "__main__":
    unittest.main()
