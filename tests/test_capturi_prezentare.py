"""Stările de captură ale prezentării (capturi.PREZENTARE) poartă pașii controlerului real al semaforului.

Dacă duratele semaforului se schimbă (verdele minim, degajarea, galbenul, cadența), capturile ar arăta secunde care nu mai sunt
adevărate. Testul rejoacă aceeași comandă pe controler, în ordinea buclei din live_twin, și caută valorile lui în codul stărilor.

Tot aici, drumul --prezentare: ceasul fixat al paginii, scara capturii și starea reală a senzorului, în locul celei scrise de mână.
Stările evaluării din § 8 (STARI, ECRANE) trebuie să rămână cum au fost.
"""
import contextlib
import io
import json
import os
import shutil
import struct
import tempfile
import time
import types
import unittest
from datetime import datetime
from datetime import time as ora_din_zi
from pathlib import Path
from unittest import mock

from romana.control import pasi
from romana.dashboard import capturi, senzor
from test_pasi import manual, semafor_corectat

CEAS = datetime(2026, 6, 10, 8, 30).timestamp()        # miercuri, 10.06.2026, 08:30:00, ora locală
CEAS_TEXT = "2026-06-10 08:30:00"
BS = chr(92)
CALE = f"C:{BS}Users{BS}Cineva{BS}Documents{BS}jurnal.log"     # o cale locală, cum poate apărea într-o notă a paznicului


def sursa(versiune: str = "curent") -> str:
    return capturi.VERSIUNI[versiune].read_text(encoding="utf-8")


def dosare(d: Path, nota: str = "în regulă: 2 procese, o colectare, starea are 0 s", fisa: bool = True) -> dict:
    """Dosarele lui senzor.stare_senzor, temporare: starea camerei scrisă cu 1 s înaintea ceasului, o notă a paznicului de acum 10 min și,
    dacă se cere, o fișă care numără căderile sursei. Numărătorile, veghea și prelucrările de noapte lipsesc: „nu se știe”."""
    live, loguri = d / "live", d / "logs"
    for x in (live, loguri, d / "counts", d / "fise"):
        x.mkdir(parents=True, exist_ok=True)
    (live / "state.json").write_text(json.dumps({"timestamp": CEAS - 1, "fps": 6.0, "conectat": True}), encoding="utf-8")
    os.utime(live / "state.json", (CEAS - 1, CEAS - 1))
    ora = datetime.fromtimestamp(CEAS - 600).isoformat(timespec="seconds")
    (loguri / "paznic_2026-06-10.log").write_text(f"{ora} {nota}" + chr(10), encoding="utf-8")
    if fisa:
        (d / "fise" / "fisa_senzor_2026-06-10_0000.json").write_text(json.dumps({
            "taietura": "2026-06-10T00:00:00", "inceput": "2026-06-01T09:04:46", "durata": {"ore": 206.92}, "minute": {"pondere_cu_cadre": 0.985},
            "cadre_pe_secunda": {"mediana": 5.99}, "pauze": {"numar": 52}, "reconectari": {"episoade": 12}, "caderi_sursa": {"numar": 2},
            "opriri": {"anuntate": 4, "caderi_neprevazute": 0}, "lanturi": {"lant": {"asteptate": 8, "incheiate": 8}},
            "vehicule": {"pe_zile": {"2026-06-01": {"vehicule": 37147}}}}), encoding="utf-8")
    return {"live": live, "loguri": loguri, "numaratori": d / "counts", "fise": (d / "publicate", d / "fise"),
            "lanturi": {"lant": (d / "lant", ora_din_zi(0, 15)), "lant_cor": (d / "lant_cor", ora_din_zi(3, 30))}}


def senzor_din(cod: str):
    """Starea senzorului pusă în codul unei stări a prezentării, citită înapoi din JSON."""
    inceput, sfarsit = "window.__senzor=", "; " + capturi.STARI["senzor"]
    assert cod.startswith(inceput), cod[:60]
    return json.loads(cod[len(inceput):cod.index(sfarsit)])


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

    def test_nimic_scris_de_mana_in_panoul_senzorului(self):
        """Stările pornesc de la starea primită (%SENZOR%), fără alerta și nota puse de mână peste răspunsul de exemplu."""
        for cod in capturi.PREZENTARE.values():
            self.assertTrue(cod.startswith("window.__senzor=%SENZOR%; " + capturi.STARI["senzor"]))
            self.assertEqual(cod.count("%SENZOR%"), 1)
            for urma in ("%FISA%", "Object.assign(v(", "alerta:", "niciun cadru prelucrat", "s-a refăcut singură", "in_regula"):
                self.assertNotIn(urma, cod)

    def test_mutarea_rescrie_istoricul(self):
        """După fiecare mutare a clipei comenzii, „Ultimele comenzi” se scrie din nou: altfel ar rămâne ora de dinaintea mutării.
        Purtarea din pagină o vede doar testul din Chrome, care se sare unde Chrome lipsește; aici, măcar codul."""
        self.assertIn("if(i){ i.la-=d; notaIstoric() }", capturi.PASI_M3)
        self.assertEqual(capturi.PASI_M3.count("const __muta="), 1)
        mutari = 0
        for nume, cod in capturi.PREZENTARE.items():
            if "__muta(" in cod:
                mutari += 1
                self.assertIn("notaIstoric()", cod, nume)
        self.assertEqual(mutari, 4)                                            # toate stările comenzii; panoul senzorului n-are nicio comandă
        for versiune in ("curent", "m2"):                                      # funcția paginii, cu acest nume, în amândouă versiunile
            self.assertIn("function notaIstoric(stare){", sursa(versiune))


class Temporar(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)


class TestCeasulFixat(unittest.TestCase):
    def test_doar_cu_ceasul_dat(self):
        """Fără ceas, pagina e cea de până acum (stările evaluării); cu el, are în plus doar scriptul ceasului, înaintea simulărilor."""
        script = capturi.CEAS_FIX.replace("%CEAS%", str(round(CEAS * 1000)))
        for versiune in capturi.VERSIUNI:
            s = sursa(versiune)
            fara, cu = capturi.pagina(s, 'cere("fix");'), capturi.pagina(s, 'cere("fix");', CEAS)
            self.assertNotIn("window.Date=", fara)
            self.assertEqual(cu.count(script), 1)
            self.assertEqual(cu.replace(script, ""), fara)
            self.assertLess(cu.index(script), cu.index("window.__netOK"))       # înaintea oricărui Date.now() al paginii
            self.assertLess(cu.index(script), cu.index("DESCHIS_LA=Date.now()") if "DESCHIS_LA" in cu else len(cu))

    def test_clipa_in_milisecunde_intregi(self):
        self.assertIn(f"const __T0={int(CEAS) * 1000},", capturi.pagina(sursa(), "", CEAS))
        self.assertIn("F.now=()=>__T0;", capturi.CEAS_FIX)
        self.assertIn("return a.length?new __D(...a):new __D(__T0)", capturi.CEAS_FIX)     # doar new Date() fără argumente e schimbat

    def test_ceasul_e_o_functie_nu_o_clasa(self):
        """O clasă chemată fără new, ca Date(), ar arunca TypeError și ar opri scriptul stării; funcția dă textul clipei fixate."""
        self.assertNotIn("class", capturi.CEAS_FIX)
        self.assertIn("if(!new.target) return new __D(__T0).toString();", capturi.CEAS_FIX)
        for urma in ("F.prototype=__D.prototype;", "F.parse=__D.parse;", "F.UTC=__D.UTC;", "window.Date=F;"):
            self.assertIn(urma, capturi.CEAS_FIX)

    def test_ceasul_dat_se_citeste_si_se_scrie_la_fel(self):
        self.assertEqual(capturi.citeste_ceasul(CEAS_TEXT), CEAS)
        self.assertEqual(datetime.fromtimestamp(CEAS).strftime(capturi.FORMAT_CEAS), CEAS_TEXT)
        for stricat in ("", "08:30:00", "2026-06-10", "2026-13-10 08:30:00", "10.06.2026 08:30:00"):
            with self.assertRaises(SystemExit) as e:
                capturi.citeste_ceasul(stricat)
            self.assertIn("AAAA-LL-ZZ HH:MM:SS", str(e.exception))


class TestScara(Temporar):
    def comenzi(self, **optiuni) -> list[list[str]]:
        """Comenzile cu care randeaza ar porni Chrome (aici nu pornește nimic)."""
        date = []
        with mock.patch.object(capturi.subprocess, "run", lambda cmd, **k: date.append(cmd) or types.SimpleNamespace(stdout=b"")):
            self.assertFalse(capturi.randeaza(sursa(), "", self.d / "x.png", **optiuni))
        self.assertEqual(list(self.d.iterdir()), [])                           # pagina temporară e ștearsă
        return date

    def test_implicit_comanda_e_cea_veche(self):
        (cmd,) = self.comenzi()
        self.assertFalse([x for x in cmd if "device-scale-factor" in x])
        self.assertIn("--window-size=1366,1500", cmd)

    def test_scara_ajunge_la_chrome_in_amandoua_trecerile(self):
        for scara in (2, 3):
            captura, text = self.comenzi(scara=scara, text=self.d / "x.txt", ceas=CEAS)
            for cmd in (captura, text):
                self.assertIn(f"--force-device-scale-factor={scara}", cmd)
                self.assertIn("--window-size=1366,1500", cmd)                  # același așezat al paginii
            self.assertTrue(captura[-2].startswith("--screenshot="))
            self.assertEqual(text[-2], "--dump-dom")
            self.assertEqual(captura[-1], text[-1])                            # aceeași pagină, cu același ceas, în amândouă

    def test_textul_nu_are_randuri_dublate(self):
        """Pe Windows, ieșirea lui Chrome are CR LF, iar scrierea ar mai pune un CR: cine citește pe rânduri ar vedea un rând gol după fiecare."""
        CR, LF = chr(13), chr(10)
        for sfarsit in (CR + LF, LF):
            dom = f'<html><pre id="__text" hidden="">Dispecerat{sfarsit}08:30:00{sfarsit}{sfarsit}a &lt; b{sfarsit}</pre></html>'.encode("utf-8")
            with mock.patch.object(capturi.subprocess, "run", lambda cmd, **k: types.SimpleNamespace(stdout=dom)):
                capturi.randeaza(sursa(), "", self.d / "x.png", text=self.d / "x.txt")
            self.assertNotIn((CR + CR).encode(), (self.d / "x.txt").read_bytes())
            self.assertEqual((self.d / "x.txt").read_text(encoding="utf-8"), LF.join(["Dispecerat", "08:30:00", "", "a < b", ""]))


class TestStareaSenzorului(Temporar):
    def test_starea_pusa_in_pagina_e_cea_primita(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d))
        for nume, cod in capturi.PREZENTARE.items():
            gata = capturi.cod_prezentare(cod, stare)
            self.assertNotIn("%SENZOR%", gata)
            self.assertEqual(senzor_din(gata), stare, nume)
            self.assertNotIn("niciun cadru prelucrat", gata)                   # veghea de aici n-are nicio alertă
            self.assertTrue(gata.endswith(cod[cod.index("; " + capturi.STARI["senzor"]):]))     # restul stării, neschimbat

    def test_starea_e_raspunsul_serverului_la_ceasul_dat(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d))
        self.assertEqual(set(stare), {"calculat_la", "memorare_s", "verigi", "fisa", "ora_server"})       # ca ruta /api/senzor
        self.assertEqual((stare["calculat_la"], stare["ora_server"]), (CEAS, CEAS))
        self.assertEqual([(v["cheie"], v["stare"]) for v in stare["verigi"]],
                         [("camera", "ok"), ("colectarea", "necunoscut"), ("veghea", "necunoscut"), ("paznicul", "ok"), ("noaptea", "necunoscut")])
        self.assertEqual((stare["verigi"][0]["varsta_s"], stare["verigi"][3]["varsta_s"]), (1.0, 600.0))  # vârstele, față de ceas
        self.assertIsNone(stare["verigi"][2]["alerta"])
        self.assertEqual((stare["fisa"]["caderi_sursa"], stare["fisa"]["publica"]), (2, False))
        de_la_senzor = senzor.stare_senzor(CEAS, **dosare(self.d))
        self.assertEqual(stare, {**json.loads(json.dumps(de_la_senzor)), "ora_server": CEAS})

    def test_textele_din_jurnale_ajung_curatate(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d, nota=f"repornire, încercarea 1: vezi {CALE}, apoi 3,5 cadre/s"))
        paznic = stare["verigi"][3]
        self.assertEqual((paznic["stare"], paznic["text"]), ("atent", "repornire, încercarea 1: vezi … apoi 3,5 cadre/s"))
        cod = capturi.cod_prezentare(capturi.PREZENTARE["m3_comanda_aplicata"], stare)
        for urma in ("Users", "Cineva", "jurnal.log", BS + BS, str(self.d), self.d.as_posix(), Path.home().name):
            self.assertNotIn(urma, cod)

    def test_un_text_nu_poate_inchide_scriptul(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d, nota="starea </script><b>s-a refăcut"))
        self.assertIn("</script>", stare["verigi"][3]["text"])
        cod = capturi.cod_prezentare(capturi.PREZENTARE["m3_senzor"], stare)
        self.assertNotIn("<", cod[:cod.index("; " + capturi.STARI["senzor"])])
        self.assertEqual(senzor_din(cod), stare)

    def test_fara_stare_ramane_raspunsul_de_exemplu(self):
        """Pagina de la M2 n-are panoul: nu i se calculează nicio stare."""
        self.assertTrue(capturi.cod_prezentare(capturi.PREZENTARE["m3_senzor"], None).startswith("window.__senzor=__SENZOR; "))

    def test_fara_nicio_dovada_unealta_se_opreste(self):
        gol = self.d / "nimic"
        with self.assertRaises(SystemExit) as e:
            capturi.stare_reala(CEAS, live=gol, loguri=gol, numaratori=gol, fise=(gol,), lanturi={"lant": (gol, ora_din_zi(0, 15))})
        self.assertIn("nicio verigă nu are vreo dovadă", str(e.exception))
        self.assertNotIn(str(self.d), str(e.exception))

    def test_un_raspuns_cu_alta_forma_opreste_unealta(self):
        for raspuns in ({}, {"verigi": [{"stare": "ok"}]}, {"verigi": [{"stare": "ok", "ultima_dovada": float("nan")}] * 5}):
            with mock.patch.object(senzor, "stare_senzor", lambda *a, **k: raspuns), self.assertRaises(SystemExit) as e:
                capturi.stare_reala(CEAS)
            self.assertIn("nu s-a putut calcula", str(e.exception))
        with mock.patch.object(senzor, "stare_senzor", mock.Mock(side_effect=OSError(f"nu pot citi {CALE}"))), self.assertRaises(SystemExit) as e:
            capturi.stare_reala(CEAS)
        self.assertIn("OSError", str(e.exception))
        self.assertNotIn("Cineva", str(e.exception))


class TestMain(Temporar):
    """main, fără Chrome: `randeaza` e înlocuită cu una care doar ține minte cu ce a fost chemată."""

    def ruleaza(self, *argumente, stare="reala") -> tuple[list, dict, str]:
        chemari = []
        if stare == "reala":
            stare = capturi.stare_reala(CEAS, **dosare(self.d / "senzor"))
        self.calcul = mock.Mock(return_value=stare)
        erori = io.StringIO()
        with mock.patch.object(capturi, "randeaza", lambda *a, **k: chemari.append((a, k)) or False), \
                mock.patch.object(capturi, "stare_reala", self.calcul), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(erori):
            capturi.main([*argumente, "--out", str(self.d / "out")])
        return chemari, json.loads((self.d / "out" / "stari.json").read_text(encoding="utf-8")), erori.getvalue()

    def test_starile_evaluarii_raman_cum_au_fost(self):
        chemari, rezumat, _ = self.ruleaza("--versiune", "curent")
        asteptate = [(n, 1366, cod, 1500) for n, cod in capturi.STARI.items()] + \
                    [(n, w, capturi.STARI[s], 2400 if w < 500 else 1800) for n, (w, s) in capturi.ECRANE.items()]
        self.assertEqual([(a[2].stem, a[3], a[1], a[4]) for a, _ in chemari], asteptate)
        self.assertEqual([k for _, k in chemari], [{}] * len(asteptate))       # fără text, fără ceas, fără scară
        self.assertEqual(set(rezumat), {"versiune", "stari"})
        self.calcul.assert_not_called()                                        # starea senzorului nu se citește

    def test_ceasul_si_scara_doar_cu_prezentarea(self):
        for optiuni in (("--ceas", CEAS_TEXT), ("--scara", "2")):
            with self.assertRaises(SystemExit) as e:
                self.ruleaza("--versiune", "curent", *optiuni)
            self.assertIn("doar cu --prezentare", str(e.exception))
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self.ruleaza("--versiune", "curent", "--prezentare", "--scara", "4")

    def test_prezentarea_cu_ceasul_dat(self):
        chemari, rezumat, erori = self.ruleaza("--versiune", "curent", "--prezentare", "--scara", "2", "--ceas", CEAS_TEXT)
        stare = self.calcul.return_value
        self.assertEqual([a[2].stem for a, _ in chemari], list(capturi.PREZENTARE))
        for (a, k), cod in zip(chemari, capturi.PREZENTARE.values()):
            self.assertEqual(k, {"text": self.d / "out" / f"{a[2].stem}.txt", "ceas": CEAS, "scara": 2})
            self.assertEqual(a[1], capturi.cod_prezentare(cod, stare))
            self.assertEqual(senzor_din(a[1]), stare)
        self.assertEqual(self.calcul.call_count, 1)                            # o singură dată, la ceasul rulării
        self.assertEqual(self.calcul.call_args.args, (CEAS,))
        self.assertEqual(self.calcul.call_args.kwargs, {"fise": senzor.FISE})
        self.assertEqual(rezumat, {"versiune": "curent", "stari": ", ".join(capturi.PREZENTARE), "ceas": CEAS_TEXT, "scara": 2})
        self.assertIn("ceasul dat nu e cel de acum", erori)                    # starea e citită din fișierele de acum

    def test_prezentarea_cu_ceasul_pornirii(self):
        inainte = time.time()
        chemari, rezumat, erori = self.ruleaza("--versiune", "curent", "--prezentare", "--fisa", str(self.d / "fise"))
        ceasuri = {k["ceas"] for _, k in chemari}
        self.assertEqual(len(ceasuri), 1)                                      # același pentru toate stările
        (ceas,) = ceasuri
        self.assertEqual(ceas, int(ceas))                                      # la secundă
        self.assertTrue(int(inainte) <= ceas <= time.time())
        self.assertEqual(self.calcul.call_args.args, (ceas,))                  # starea senzorului, la același ceas
        self.assertEqual(self.calcul.call_args.kwargs, {"fise": (senzor.FISE[0], self.d / "fise")})
        self.assertEqual((rezumat["ceas"], rezumat["scara"]), (datetime.fromtimestamp(ceas).strftime(capturi.FORMAT_CEAS), 1))
        self.assertEqual(capturi.citeste_ceasul(rezumat["ceas"]), ceas)        # a doua versiune poate fi rulată cu el
        self.assertEqual({k["scara"] for _, k in chemari}, {1})
        self.assertEqual(erori, "")

    def test_pagina_de_la_m2_are_acelasi_ceas_si_nicio_stare_a_senzorului(self):
        chemari, rezumat, erori = self.ruleaza("--versiune", "m2", "--prezentare", "--ceas", CEAS_TEXT)
        self.calcul.assert_not_called()
        self.assertEqual({k["ceas"] for _, k in chemari}, {CEAS})
        self.assertEqual([a[1] for a, _ in chemari], [capturi.cod_prezentare(cod, None) for cod in capturi.PREZENTARE.values()])
        self.assertEqual((rezumat["ceas"], erori), (CEAS_TEXT, ""))

    def test_o_fisa_fara_caderile_sursei_opreste_unealta(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d / "senzor", fisa=False))
        self.assertIsNone(stare["fisa"])
        with self.assertRaises(SystemExit) as e:
            self.ruleaza("--versiune", "curent", "--prezentare", stare=stare)
        self.assertIn("căderile sursei", str(e.exception))


def marime_png(f: Path) -> tuple[int, int]:
    return struct.unpack(">II", f.read_bytes()[16:24])


@unittest.skipUnless(Path(capturi.CHROME).exists(), "Chrome nu e instalat aici")
class TestInChrome(Temporar):
    """Starea „aplicată”, o dată pe fiecare versiune a paginii, la scara 2 și cu ceasul fixat: imaginea și textul ei."""
    # la sfârșitul stării, ceasul paginii, scris în pagină: Date() fără new, new Date() fără argumente și cu ele, Date.now()
    PROBA_CEAS = (' document.body.append(" __ceas "+[typeof Date(), Date()===new Date().toString(), new Date().getTime(), new Date(5).getTime(), '
                  'Date.now(), new Date() instanceof Date, Date.UTC(1970,0,1), Date.parse("1970-01-01T00:00:01Z")].join(" ")); ')

    def captura(self, versiune: str, stare: dict | None) -> tuple[tuple[int, int], str]:
        png, text = self.d / f"{versiune}.png", self.d / f"{versiune}.txt"
        cod = capturi.cod_prezentare(capturi.PREZENTARE["m3_comanda_aplicata"], stare) + self.PROBA_CEAS
        self.assertTrue(capturi.randeaza(sursa(versiune), cod, png, 1366, 700, text=text, ceas=CEAS, scara=2))
        self.assertNotIn(bytes([13, 13]), text.read_bytes())                   # fără rânduri dublate
        return marime_png(png), text.read_text(encoding="utf-8")

    def test_ceasul_scara_si_starea_senzorului(self):
        stare = capturi.stare_reala(CEAS, **dosare(self.d / "senzor", nota=f"repornire, încercarea 1: vezi {CALE}, gata"))
        marime, acum = self.captura("curent", stare)
        self.assertEqual(marime, (2732, 1400))                                 # de două ori 1366×700
        self.assertIn("Aplicat la 08:30:00: Verde pe Bd. Dacia, est și vest.", acum)
        self.assertIn("08:29:11 · Verde pe Bd. Dacia, est și vest: aplicată", acum)       # comanda, cu 49 s înaintea ceasului
        self.assertIn("Citită la 08:30:00;", acum)                             # starea senzorului, la același ceas
        self.assertIn("De urmărit: Paznicul.", acum)
        self.assertIn("„repornire, încercarea 1: vezi … gata”", acum)
        for urma in ("1.234", "niciun cadru prelucrat", "Users", "Cineva", "jurnal.log", str(self.d)):
            self.assertNotIn(urma, acum)
        marime, inainte = self.captura("m2", None)
        self.assertEqual(marime, (2732, 1400))
        self.assertIn("08:29:11 · Verde pe Bd. Dacia, est și vest: neaplicată", inainte)  # pagina de la M2 renunță după 30 s
        self.assertNotIn("Aplicat la", inainte)
        ms = int(CEAS) * 1000
        for text in (acum, inainte):
            self.assertIn(chr(10) + "08:30:00" + chr(10), text)                # ceasul din antet
            self.assertIn(f"__ceas string true {ms} 5 {ms} true 0 1000", text) # Date() fără new nu oprește scriptul stării


if __name__ == "__main__":
    unittest.main()
