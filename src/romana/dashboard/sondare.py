"""Sondarea dispeceratului cu oameni (§ 8): ghid, sarcini și întrebări pe același ecran, pe calculatorul autorului.

Un server local separat de dispecerat. Participantul vede în stânga ghidul, pas cu pas, iar în dreapta dispeceratul,
într-una din cele două versiuni: `m1` (cea prezentată la borna M1, păstrată neschimbată) și `m2` (cea curentă). Datele
sunt simulate, ca toți să aibă aceeași situație și răspunsul corect să se știe: comenzile nu ajung la geamănul digital
și nici pe stradă. Imaginea camerei e previzualizarea estompată a colectării, doar pe ecranul local, sau, cu
`--cadru-public`, figura publicată, nemișcată.

Fiecare participant primește un cod (P1, P2, …), fără nume. Ordinea versiunilor alternează: P1 m1→m2, P2 m2→m1, P3 m2→m1,
P4 m1→m2. Situațiile țin de rundă (prima, a doua), nu de versiune. Fiecare răspuns și clic se scrie pe loc în
outputs/sondare/<cod>.jsonl, iar o pagină reîncărcată continuă de unde a rămas.

Rulare:     python -m romana.dashboard.sondare            → http://localhost:8060
Rezultate:  python -m romana.dashboard.sondare --rezumat   → outputs/sondare/rezumat.csv și tabelul pe versiuni
            python -m romana.dashboard.sondare --publica   → docs/rezultate/sondare_m2.csv (doar rezultate de grup)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

from romana.common import OUTPUT_DIR

STATIC = Path(__file__).parent / "static"
LIVE = OUTPUT_DIR / "live"
DOSAR = OUTPUT_DIR / "sondare"
RADACINA = Path(__file__).resolve().parents[3]
PUBLICAT = RADACINA / "docs" / "rezultate" / "sondare_m2.csv"
CADRU_PUBLIC = RADACINA / "docs" / "imagini" / "camera_piata_romana.jpg"
VERSIUNI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "index.html"}
ORDINI = [("m1", "m2"), ("m2", "m1"), ("m2", "m1"), ("m1", "m2")]

FAZE = ["N–S: Magheru ↔ Lascăr Catargiu prin centru", "E–V: Dacia în jurul insulei",
        "Pietoni: toate trecerile, axa centrală se golește", "N–S, cu intrările Dacia deschise (fără dozare)",
        "E–V, cu intrările Magheru/Catargiu deschise (fără dozare)"]
PLAN = [(0, 12), (1, 14), (2, 12)]              # planul fix din geamăn: verde 12/14/12 s, apoi galben 3 s și roșu 2 s
DACIA = 1
AUTOMATE = {"ai", "fix", "max_pressure", "program"}
# Cozile pe brațe în cele două runde; cea mai lungă e alta, ca răspunsul din prima rundă să nu ajute în a doua.
COZI = [{"dacia_vest": 22, "magheru": 11, "catargiu": 6, "dacia_est": 4, "pietoni": 5},
        {"magheru": 21, "dacia_vest": 9, "catargiu": 12, "dacia_est": 6, "pietoni": 3}]
INTRARI = {"magheru": 1180, "catargiu": 410, "dacia_vest": 690, "dacia_est": 520}
IESIRI = {"magheru": 870, "mendeleev": 240, "dacia_vest": 610, "dacia_est": 480, "caderea_bastiliei": 330, "catargiu": 600}
NUME_BRAT = {"magheru": "Magheru", "catargiu": "Lascăr Catargiu", "dacia_est": "Dacia est", "dacia_vest": "Dacia vest"}
# În prima rundă conduce calculatorul și imaginea se oprește; în a doua conduce un om și imaginea merge.
RUNDE = [{"mod": "program", "conduce": "calculator", "imagine": "oprita"},
         {"mod": "manual", "conduce": "om", "imagine": "merge"}]

NU_POT = "Nu pot spune"
ALEGE_CONDUCE = {"calculator": "Un calculator, singur", "om": "Un om, de la acest ecran"}
ALEGE_IMAGINE = {"oprita": "S-a oprit", "merge": "Merge, se mișcă"}
CUM_ATI_STIUT = ["Am văzut clar pe ecran", "Am văzut, dar nu eram sigur(ă)", "N-am știut", "Nu s-a schimbat nimic"]
SCARA_SUS = ["Deloc de acord", "Mai degrabă nu", "Nici da, nici nu", "Mai degrabă da", "Total de acord"]
# Chestionarul SUS (Brooke, 1996), tradus de autor pentru oameni fără pregătire tehnică; traducerea nu e validată.
SUS = ["Cred că aș folosi des acest ecran, dacă aș avea de supravegheat semafoare.",
       "Mi s-a părut complicat fără rost.",
       "Mi s-a părut ușor de folosit.",
       "Cred că aș avea nevoie de ajutorul cuiva priceput ca să mă descurc cu el.",
       "Părțile ecranului se leagă bine între ele.",
       "Mi s-a părut că multe lucruri nu se potrivesc între ele.",
       "Cred că cei mai mulți oameni ar învăța repede să-l folosească.",
       "Mi s-a părut greoi de folosit.",
       "M-am simțit sigur(ă) pe mine când l-am folosit.",
       "A trebuit să învăț multe lucruri înainte să mă descurc cu el."]


def corect_coada(runda: int) -> str:
    c = COZI[runda]
    return NUME_BRAT[max(NUME_BRAT, key=lambda b: c[b])]


def scor_sus(valori: list[int]) -> float:
    """Scorul SUS, 0–100: itemii impari (1, 3, …) valorează răspuns − 1, cei pari 5 − răspuns, totul × 2,5."""
    return sum((v - 1) if i % 2 == 0 else (5 - v) for i, v in enumerate(valori)) * 2.5


def _runda(runda: int, versiune: str) -> list[dict]:
    """Pașii unei variante: pornirea, cele 5 sarcini cu întrebările lor, închiderea, apoi părerile."""
    r = f"r{runda + 1}"
    v = {"versiune": versiune, "runda": runda}
    ec = {**v, "ecran": True}                     # dispeceratul e deschis și se vede
    ac = {**v, "ecran": True, "acoperit": True}   # dispeceratul e deschis, dar acoperit: se răspunde din ce s-a văzut
    sit = RUNDE[runda]
    p = [
        {"id": f"{r}_deschide", "tip": "deschide", **v, "titlu": "Pornim prima variantă" if runda == 0 else "Pornim a doua variantă",
         "text": ["Apăsați butonul de mai jos. Ecranul de supraveghere se deschide în dreapta."] if runda == 0 else
                 ["Puteți face o pauză, dacă doriți. Urmează aceleași sarcini, pe o altă variantă a ecranului.",
                  "Când sunteți gata, apăsați butonul de mai jos."],
         "buton": "Deschide dispeceratul", "sit": {"runda": runda, "mod": sit["mod"], "cam": "merge"}},
        {"id": f"{r}_conduce", "tip": "sarcina", "sarcina": 1, **ec,
         "text": ["Uitați-vă pe ecranul din dreapta.", "**Cine conduce acum semaforul: un calculator sau un om?**"]},
        {"id": f"{r}_conduce_r", "tip": "alegere", **ac, "titlu": "Cine conduce acum semaforul?",
         "optiuni": [*ALEGE_CONDUCE.values(), NU_POT], "corect": ALEGE_CONDUCE[sit["conduce"]]},
        {"id": f"{r}_coada", "tip": "sarcina", "sarcina": 2, **ec,
         "text": ["**Pe care stradă așteaptă acum cele mai multe mașini la semafor?**"]},
        {"id": f"{r}_coada_r", "tip": "alegere", **ac, "titlu": "Unde așteaptă cele mai multe mașini?",
         "optiuni": [*NUME_BRAT.values(), NU_POT], "corect": corect_coada(runda)},
        {"id": f"{r}_imagine", "tip": "sarcina", "sarcina": 3, **ec, "sit": {"cam": sit["imagine"]},
         "text": ["Uitați-vă la imaginea de la camera din piață.", "**Imaginea merge acum sau s-a oprit?**"]},
        {"id": f"{r}_imagine_r", "tip": "alegere", **ac, "titlu": "Imaginea de la cameră…",
         "optiuni": [ALEGE_IMAGINE["merge"], ALEGE_IMAGINE["oprita"], NU_POT], "corect": ALEGE_IMAGINE[sit["imagine"]]},
        {"id": f"{r}_verde", "tip": "sarcina", "sarcina": 4, **ec, "verifica": "verde", "sit": {"cam": "merge", "mod": "program"},
         "text": ["**Dați verde pe Bulevardul Dacia**, ca și cum ați conduce dumneavoastră semaforul.",
                  "Când credeți că ați reușit, apăsați „Am terminat”."]},
        {"id": f"{r}_verde_r", "tip": "alegere", **ac, "titlu": "Ce culoare are acum semaforul pe Dacia?",
         "optiuni": ["Verde", "Galben", "Roșu", NU_POT], "corect_din_banc": True},
        {"id": f"{r}_verde_vazut", "tip": "alegere", **ac, "titlu": "Cum ați știut că s-a schimbat ce ați vrut?", "optiuni": CUM_ATI_STIUT},
        {"id": f"{r}_automat", "tip": "sarcina", "sarcina": 5, **ec, "verifica": "automat", "pregateste": "manual_dacia",
         "text": ["**Lăsați semaforul să fie condus din nou de calculator**, ca să nu mai fie nevoie de dumneavoastră.",
                  "Când credeți că ați reușit, apăsați „Am terminat”."]},
        {"id": f"{r}_automat_vazut", "tip": "alegere", **ac, "titlu": "Cum ați știut că acum conduce calculatorul?", "optiuni": CUM_ATI_STIUT},
        {"id": f"{r}_inchide", "tip": "inchide", **ec, "titlu": "Închideți dispeceratul",
         "text": ["Ați terminat sarcinile pe această variantă. Apăsați butonul de mai jos: ecranul din dreapta se închide."],
         "buton": "Închide dispeceratul"},
        {"id": f"{r}_real", "tip": "alegere", **v, "titlu": "Dacă apăsați un buton pe acest ecran, se schimbă semaforul adevărat din piață?",
         "optiuni": ["Da", "Nu", NU_POT], "corect": "Nu"},
        {"id": f"{r}_culori", "tip": "alegere", **v, "titlu": "Pe schema pieței, ce credeți că arată o linie roșie groasă pe o stradă?",
         "optiuni": ["Multe mașini care așteaptă", "Un accident", "Strada e închisă", NU_POT], "corect": "Multe mașini care așteaptă"},
        {"id": f"{r}_sus_intro", "tip": "info", **v, "titlu": "Câteva păreri despre această variantă",
         "text": ["Urmează 10 afirmații, pe rând. Spuneți cât de mult sunteți de acord cu fiecare. Nu e nevoie să vă gândiți mult.",
                  "Unele spun de bine, altele de rău, așa că citiți-le pe fiecare."], "buton": "Mai departe"},
    ]
    p += [{"id": f"{r}_sus{i + 1}", "tip": "scara", **v, "titlu": t, "optiuni": SCARA_SUS, "numar": f"Afirmația {i + 1} din 10"}
          for i, t in enumerate(SUS)]
    return p


def pasi(ordine: tuple[str, str]) -> list[dict]:
    """Lista pașilor unui participant. `sit` e situația pe care o arată dispeceratul de la acel pas încolo."""
    return [
        {"id": "pregatire", "tip": "info", "titlu": "Pregătire, pentru cel care invită", "colectare": True, "text": [
            "Puneți fereastra pe tot ecranul, cu tasta F11, și nu închideți nimic altceva de pe calculator.",
            "Stați lângă persoană, dar **nu o ajutați la sarcini**. Dacă vă întreabă ce să facă, spuneți: „Faceți cum credeți”.",
            "Puteți ajuta doar la mouse sau citind textul cu voce tare. La final, ghidul vă întreabă dacă a fost nevoie."],
         "buton": "Predau calculatorul"},
        {"id": "bun_venit", "tip": "info", "titlu": "Bun venit!", "text": [
            "Vă mulțumim că ne ajutați. Verificăm dacă un ecran pentru supravegherea semafoarelor din Piața Romană este ușor de înțeles.",
            "**Testăm ecranul, nu pe dumneavoastră.** Dacă ceva nu merge sau nu se înțelege, vina e a ecranului, iar asta vrem să aflăm.",
            "Durează cam 20 de minute. Vă puteți opri oricând, fără nicio explicație.",
            "**Ce se întâmplă cu răspunsurile:** se salvează pe acest calculator, fără nume, doar cu un cod. Nu se înregistrează imagine sau sunet. "
            "Autorul proiectului le analizează împreună cu asistentul AI Claude (Anthropic), iar în proiect apar doar rezultate de grup."],
         "buton": "Sunt de acord, începem"},
        {"id": "profil_calculator", "tip": "alegere", "titlu": "Cât de des folosiți calculatorul?", "optiuni": ["Rar", "Uneori", "În fiecare zi"]},
        {"id": "profil_vazut", "tip": "alegere", "titlu": "Ați mai văzut până acum ecranul acesta?", "optiuni": ["Nu", "Da"]},
        {"id": "cum_lucram", "tip": "info", "titlu": "Cum lucrăm", "text": [
            "Imaginați-vă că lucrați într-un centru care supraveghează semafoarele din Piața Romană. Nu puteți strica nimic, așa că încercați fără grijă.",
            "Aici, în stânga, primiți pe rând câte o sarcină. O citiți, o faceți pe ecranul din dreapta, apoi apăsați butonul de sub ea. "
            "După aceea, ecranul se acoperă și răspundeți la o întrebare, din ce ați văzut.",
            "Dacă nu reușiți, apăsați „Nu reușesc” și mergem mai departe. Nu e nicio problemă.",
            "Veți vedea două variante ale aceluiași ecran, pe rând."],
         "buton": "Am înțeles"},
        *_runda(0, ordine[0]),
        *_runda(1, ordine[1]),
        {"id": "preferinta", "tip": "alegere", "titlu": "Care variantă v-a fost mai ușoară?", "optiuni": ["Prima", "A doua", "La fel"]},
        {"id": "comentariu", "tip": "text", "titlu": "Ce v-a încurcat cel mai tare?",
         "text": ["Puteți scrie câteva cuvinte sau le puteți spune cuiva care scrie pentru dumneavoastră. Puteți lăsa și gol. Vă rugăm să nu scrieți nume."],
         "buton": "Trimit"},
        {"id": "multumim", "tip": "info", "titlu": "Gata. Vă mulțumim!",
         "text": ["Ați terminat, iar răspunsurile s-au salvat.",
                  "Semafoarele de pe ecran erau simulate pe calculator: nimic din ce ați apăsat nu a schimbat ceva pe stradă.",
                  "Chemați, vă rugăm, persoana care v-a invitat."], "buton": "Mai departe"},
        {"id": "moderator", "tip": "alegere", "titlu": "Pentru cel care a invitat: a fost nevoie de ajutor?",
         "optiuni": ["Nu", "Doar la mouse sau la citit", "La înțeles sarcinile"]},
        {"id": "sfarsit", "tip": "sfarsit", "titlu": "Sesiune încheiată",
         "text": ["Pentru următorul participant, apăsați butonul. Dacă ați terminat, închideți fereastra."], "buton": "Participantul următor"},
    ]


class Banc:
    """Situația simulată a dispeceratului: aceleași câmpuri ca outputs/live/state.json și sim_state.json."""

    def __init__(self, ceas=time.time):
        self.ceas = ceas
        self.t0 = ceas()
        self.runda = 0
        self.mod = "program"
        self.faza_manual = 0
        self.t_manual = self.t0 - 30
        self.cam = "merge"
        self.t_cam = self.t0

    def seteaza(self, runda=None, mod=None, cam=None, faza=None):
        """Pune direct situația cerută de un pas, fără tranziție."""
        if runda is not None:
            self.runda = runda
        if mod is not None:
            self.mod = mod
            if mod == "manual":
                self.faza_manual = 0 if faza is None else faza
                self.t_manual = self.ceas() - 30
        if cam is not None:
            self.cam = cam
            self.t_cam = self.ceas()

    def comanda(self, mod: str, faza) -> dict:
        """Comanda unui participant. La fel ca în geamăn: o fază nouă vine după galben și roșu; faza verde curentă rămâne."""
        if mod == "manual":
            f, etapa, verde = self.faza()
            noua = int(faza) if faza is not None else f
            if noua == f and etapa == "green":
                self.t_manual = self.ceas() - 5 - verde
            elif not (self.mod == "manual" and noua == self.faza_manual):
                self.t_manual = self.ceas()
            self.faza_manual = noua
        self.mod = mod
        return {"ok": True, "mod": mod, "timestamp": self.ceas(), **({"faza": self.faza_manual} if mod == "manual" else {})}

    def faza(self) -> tuple[int, str, int]:
        """(faza, etapa, verde_s): ca în geamăn, verde_s rămâne cât a ținut verdele și în galben și în roșu."""
        acum = self.ceas()
        if self.mod == "manual":
            d = acum - self.t_manual
            if d < 3:
                return self.faza_manual, "yellow", 0
            if d < 5:
                return self.faza_manual, "red", 0
            return self.faza_manual, "green", int(d - 5)
        t = (acum - self.t0) % sum(v + 5 for _, v in PLAN)
        for f, v in PLAN:
            if t < v:
                return f, "green", int(t)
            if t < v + 3:
                return f, "yellow", v
            if t < v + 5:
                return f, "red", v
            t -= v + 5
        return 0, "green", 0

    def cozi(self) -> dict:
        """Cozile rundei, cu o mișcare mică; cea mai lungă rămâne aceeași."""
        faza_timp = (self.ceas() - self.t0) / 6
        return {b: max(0, int(round(q + 1.2 * math.sin(faza_timp + i)))) for i, (b, q) in enumerate(COZI[self.runda].items())}

    def stare(self) -> dict:
        acum = self.ceas()
        faza, etapa, verde = self.faza()
        cozi = self.cozi()
        total = sum(v for k, v in cozi.items() if k != "pietoni")
        t = int(acum - self.t0)
        istoric = [[t - 600 + 5 * i, max(0, int(total + 6 * math.sin(i / 9) + 3 * math.sin(i / 2.3)))] for i in range(120)]
        sim = {"timestamp": acum, "timp_sim": t, "mod": self.mod, "mod_program": "plan_scurt" if self.mod == "program" else None,
               "sursa": "camera live", "faza": faza, "faza_nume": FAZE[faza], "etapa": etapa, "verde_s": verde, "faze": FAZE, "model_ai": True,
               "coada_brate": cozi, "coada_total": total, "vehicule_in_retea": 90 + total, "vehicule_injectate": 412, "pietoni_in_retea": 31,
               "pietoni_injectati": 140, "debite_folosite": INTRARI, "debit_echilibrat_veh_h": 2800, "pietoni_h_folositi": 620,
               "istoric_coada": istoric, "_varsta_s": 0.4}
        cam = {"timestamp": acum, "fps": 5.9, "conectat": True, "reconectari": 0, "vehicule_urmarite": 64,
               "intrari_veh_h": INTRARI, "iesiri_veh_h": IESIRI, "pietoni_h": {"dacia_est": 620}, "secunde_interval": 480,
               "_varsta_s": round(20 + acum - self.t_cam, 1) if self.cam == "oprita" else 0.4}
        return {"camera": cam, "simulare": sim, "comanda": {"mod": self.mod, "timestamp": acum}, "ora_server": acum}

    def verde_pe_dacia(self) -> bool:
        return self.mod == "manual" and self.faza_manual == DACIA

    def culoare_dacia(self) -> str:
        """Ce arată schema pentru Dacia: verde doar în faza ei; în fazele fără dozare, Dacia e la verde și ea, dar acestea nu rulează singure."""
        faza, etapa, _ = self.faza()
        if faza != DACIA and faza not in (3, 4):
            return "Roșu"
        return {"green": "Verde", "yellow": "Galben", "red": "Roșu"}[etapa]

    def e_automat(self) -> bool:
        return self.mod in AUTOMATE


class Sesiune:
    """Un participant: pașii, poziția și jurnalul lui, scris linie cu linie."""

    def __init__(self, cod: str, ordine: tuple[str, str], dosar: Path, banc: Banc, ceas=time.time):
        self.cod, self.ordine, self.dosar, self.banc, self.ceas = cod, ordine, dosar, banc, ceas
        self.pasi = pasi(ordine)
        self.jurnal = dosar / f"{cod}.jsonl"
        self.poz = 0
        self.lacat = threading.Lock()
        if self.jurnal.exists():
            self._reia()
        self._intra()

    def _reia(self) -> None:
        """Continuă de la pasul la care s-a oprit, cu situația pe care o avea atunci."""
        for o in citeste_participant(self.jurnal):
            if o.get("tip") == "pas":
                self.poz = o["index"] + 1
        self.poz = min(self.poz, len(self.pasi) - 1)
        for p in self.pasi[:self.poz]:
            if p.get("sit"):
                self.banc.seteaza(**p["sit"])

    def noteaza(self, o: dict) -> None:
        self.dosar.mkdir(parents=True, exist_ok=True)
        nou = not self.jurnal.exists()
        with open(self.jurnal, "a", encoding="utf-8") as f:
            if nou:                 # fișierul apare abia la primul răspuns: un cod neatins nu consumă un loc
                f.write(json.dumps({"t": round(self.ceas(), 3), "tip": "inceput", "ordine": list(self.ordine)}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"t": round(self.ceas(), 3), **o}, ensure_ascii=False) + "\n")
            f.flush()

    def pas(self) -> dict:
        return self.pasi[self.poz]

    def _intra(self) -> None:
        """Pregătește dispeceratul pentru pasul curent, indiferent ce a făcut participantul înainte."""
        p = self.pas()
        self.t_pas = self.ceas()
        self.clicuri = 0
        self.comenzi = []
        self.defilare = 0
        if p.get("corect_din_banc"):                      # culoarea din clipa în care ecranul s-a acoperit
            self.corect_calculat = self.banc.culoare_dacia()
        if p.get("sit"):
            self.banc.seteaza(**p["sit"])
        if p.get("pregateste") == "manual_dacia" and not self.banc.verde_pe_dacia():
            self.banc.seteaza(mod="manual", faza=DACIA)   # sarcina de dinainte n-a reușit: începem de unde ar fi ajuns
            self.noteaza({"tip": "pregatit", "pas": p["id"]})

    def raspunde(self, valoare=None, nu_reuseste: bool = False, id_pas: str | None = None) -> dict:
        """Înregistrează pasul curent și trece la următorul; un răspuns pentru alt pas (clic dublu) se ignoră."""
        with self.lacat:
            p = self.pas()
            if p["tip"] == "sfarsit" or (id_pas is not None and id_pas != p["id"]):
                return self.pas_public()
            r = {"tip": "pas", "index": self.poz, "id": p["id"], "tip_pas": p["tip"], "durata_s": round(self.ceas() - self.t_pas, 2)}
            for k in ("versiune", "runda", "sarcina"):
                if k in p:
                    r[k] = p[k]
            if valoare is not None:
                r["valoare"] = valoare
            if "corect" in p:
                r["corect"] = valoare == p["corect"]
            if p.get("corect_din_banc"):
                r["corect"] = valoare == self.corect_calculat
            if p["tip"] == "sarcina":
                r.update(clicuri=self.clicuri, comenzi=self.comenzi, defilare=self.defilare, nu_reuseste=nu_reuseste)
                if p.get("verifica") == "verde":
                    r["reusit"] = self.banc.verde_pe_dacia() and not nu_reuseste
                    r["mod_final"] = self.banc.mod
                elif p.get("verifica") == "automat":
                    r["reusit"] = self.banc.e_automat() and not nu_reuseste
                    r["mod_final"] = self.banc.mod
            self.noteaza(r)
            self.poz += 1
            self._intra()
            return self.pas_public()

    def clic(self, eticheta: str) -> None:
        self.clicuri += 1
        self.noteaza({"tip": "clic", "pas": self.pas()["id"], "eticheta": eticheta[:60]})

    def comanda(self, mod: str, faza) -> dict:
        r = self.banc.comanda(mod, faza)
        self.comenzi.append([mod, faza])
        self.noteaza({"tip": "comanda", "pas": self.pas()["id"], "mod": mod, "faza": faza})
        return r

    def pas_public(self) -> dict:
        """Pasul, așa cum îl vede pagina: fără răspunsul corect și fără ce pregătește serverul."""
        p = {k: v for k, v in self.pas().items() if k not in ("corect", "corect_din_banc", "sit", "pregateste", "verifica")}
        p.update(cod=self.cod, index=self.poz, total=len(self.pasi), sarcini=max(x.get("sarcina", 0) for x in self.pasi))
        return p


def urmatorul_cod(dosar: Path) -> tuple[str, tuple[str, str]]:
    n = len(list(dosar.glob("P*.jsonl"))) if dosar.exists() else 0
    return f"P{n + 1}", ORDINI[n % len(ORDINI)]


def _dupa_numar(dosar: Path) -> list[Path]:
    return sorted(dosar.glob("P*.jsonl"), key=lambda p: int(p.stem[1:])) if dosar.exists() else []


def colectarea_merge(prag_s: float = 30, ceas=time.time) -> bool:
    """Imaginea din dispecerat se mișcă doar dacă previzualizarea colectării e proaspătă."""
    try:
        return ceas() - (LIVE / "frame.jpg").stat().st_mtime < prag_s
    except OSError:
        return False


def creeaza_app(dosar: Path = DOSAR, cadru_public: bool = False, ceas=time.time) -> Flask:
    app = Flask(__name__, static_folder=None)
    banc = Banc(ceas)
    stare = {"sesiune": None}

    def sesiune() -> Sesiune:
        if stare["sesiune"] is None:
            neterminat = None
            for j in _dupa_numar(dosar):
                if not any(o.get("id") == "moderator" for o in citeste_participant(j)):
                    neterminat = j
            if neterminat is not None:
                prim = citeste_participant(neterminat)[0]
                stare["sesiune"] = Sesiune(neterminat.stem, tuple(prim["ordine"]), dosar, banc, ceas)
            else:
                cod, ordine = urmatorul_cod(dosar)
                stare["sesiune"] = Sesiune(cod, ordine, dosar, banc, ceas)
        return stare["sesiune"]

    def public(s: Sesiune) -> dict:
        p = s.pas_public()
        if p.get("colectare"):
            p["colectare"] = cadru_public or colectarea_merge()
        return p

    @app.get("/")
    def pagina():
        return send_file(STATIC / "sondare.html", max_age=0)

    @app.get("/d/<versiune>/")
    def dispecerat(versiune):
        if versiune not in VERSIUNI:
            abort(404)
        return send_file(VERSIUNI[versiune], max_age=0)

    @app.get("/sondare/pas")
    def pas_curent():
        return jsonify(public(sesiune()))

    @app.post("/sondare/raspuns")
    def raspuns():
        b = request.get_json(force=True, silent=True) or {}
        s = sesiune()
        s.raspunde(b.get("valoare"), bool(b.get("nu_reuseste")), b.get("id"))
        return jsonify(public(s))

    @app.post("/sondare/clic")
    def clic():
        b = request.get_json(force=True, silent=True) or {}
        sesiune().clic(str(b.get("eticheta", "")))
        return jsonify({"ok": True})

    @app.post("/sondare/defilare")
    def defilare():
        b = request.get_json(force=True, silent=True) or {}
        s = sesiune()
        try:
            s.defilare = max(s.defilare, int(b.get("y", 0)))
        except (TypeError, ValueError):
            pass
        return jsonify({"ok": True})

    @app.post("/sondare/urmatorul")
    def urmatorul():
        s = sesiune()
        if s.pas()["tip"] != "sfarsit":
            return jsonify({"eroare": "sesiunea nu s-a încheiat"}), 409
        stare["sesiune"] = None
        return jsonify(public(sesiune()))

    # Aceleași adrese ca serverul dispeceratului, ca paginile să meargă neschimbate; nimic din outputs/live nu se scrie.
    @app.get("/api/state")
    def api_stare():
        return jsonify(banc.stare())

    @app.post("/api/command")
    def api_comanda():
        b = request.get_json(force=True, silent=True) or {}
        mod = b.get("mod")
        if mod not in AUTOMATE | {"manual"}:
            return jsonify({"eroare": "mod necunoscut"}), 400
        faza = b.get("faza")
        if mod == "manual" and faza is not None:
            try:
                faza = int(faza)
            except (TypeError, ValueError):
                return jsonify({"eroare": "fază invalidă"}), 400
        return jsonify(sesiune().comanda(mod, faza))

    def _cadru() -> bytes | None:
        p = LIVE / "frame.jpg"
        try:
            return (CADRU_PUBLIC if cadru_public or not p.exists() else p).read_bytes()
        except OSError:
            return None

    @app.get("/api/frame.jpg")
    def api_cadru():
        d = _cadru()
        if d is None:
            abort(404)
        return app.response_class(d, mimetype="image/jpeg", headers={"Cache-Control": "no-store"})

    @app.get("/api/video")
    def api_video():
        def gen():
            ultim, moment = None, 0.0
            while True:
                if banc.cam != "oprita":             # imaginea oprită: nu mai trimitem cadre noi
                    d = _cadru()
                    # un cadru neschimbat se retrimite rar: browserul afișează o imagine abia când vine următoarea
                    if d and (d != ultim or time.time() - moment > 2):
                        ultim, moment = d, time.time()
                        yield b"--cadru\r\nContent-Type: image/jpeg\r\n\r\n" + d + b"\r\n"
                time.sleep(0.15)
        return app.response_class(gen(), mimetype="multipart/x-mixed-replace; boundary=cadru", headers={"Cache-Control": "no-store"})

    app.banc = banc
    app.sesiune_curenta = sesiune
    return app


def citeste_participant(cale: Path) -> list[dict]:
    rez = []
    for linie in cale.read_text(encoding="utf-8").splitlines():
        try:
            rez.append(json.loads(linie))
        except json.JSONDecodeError:      # ultima linie, dacă scrierea a fost întreruptă
            pass
    return rez


NUME_SARCINA = {1: "cine conduce", 2: "cea mai lungă coadă", 3: "imaginea merge sau nu", 4: "verde pe Dacia", 5: "înapoi la calculator"}
RASPUNS_SARCINA = {1: "conduce_r", 2: "coada_r", 3: "imagine_r"}
INTREBARI = ("real", "culori", "verde_r", "verde_vazut", "automat_vazut")


def rezumat(dosar: Path = DOSAR) -> list[dict]:
    """Un rând pe participant, versiune și sarcină, plus rânduri pentru SUS, întrebările despre ce au observat și profil."""
    randuri = []
    for cale in _dupa_numar(dosar):
        toate = citeste_participant(cale)
        pasi_p = [o for o in toate if o.get("tip") == "pas"]
        pe_id = {o["id"]: o for o in pasi_p}
        cod = cale.stem
        ordine = next((o["ordine"] for o in toate if o.get("tip") == "inceput"), None)
        for runda in (0, 1):
            r = f"r{runda + 1}"
            for o in pasi_p:
                if o.get("runda") != runda:
                    continue
                if o["tip_pas"] == "sarcina":
                    sarc = o["sarcina"]
                    rasp = pe_id.get(f"{r}_{RASPUNS_SARCINA[sarc]}") if sarc in RASPUNS_SARCINA else None
                    reusit = o.get("reusit") if sarc not in RASPUNS_SARCINA else bool(rasp and rasp.get("corect") and not o.get("nu_reuseste"))
                    randuri.append({"cod": cod, "versiune": o["versiune"], "runda": runda + 1, "masura": f"sarcina {sarc}: {NUME_SARCINA[sarc]}",
                                    "durata_s": o["durata_s"], "reusit": reusit, "clicuri": o.get("clicuri"), "comenzi": len(o.get("comenzi", [])),
                                    "defilare_px": o.get("defilare"), "nu_reuseste": o.get("nu_reuseste"), "raspuns": rasp.get("valoare") if rasp else None})
                elif o["id"][3:] in INTREBARI:
                    randuri.append({"cod": cod, "versiune": o["versiune"], "runda": runda + 1, "masura": o["id"][3:],
                                    "reusit": o.get("corect"), "raspuns": o.get("valoare")})
            valori = [pe_id[f"{r}_sus{i}"] for i in range(1, 11) if f"{r}_sus{i}" in pe_id]
            if len(valori) == 10:
                indici = [SCARA_SUS.index(v["valoare"]) + 1 for v in valori]
                randuri.append({"cod": cod, "versiune": valori[0]["versiune"], "runda": runda + 1, "masura": "SUS", "scor": scor_sus(indici)})
        for k in ("moderator", "profil_calculator", "profil_vazut"):
            if k in pe_id:
                randuri.append({"cod": cod, "masura": k, "raspuns": pe_id[k].get("valoare")})
        if "preferinta" in pe_id and ordine:      # „Prima” / „A doua” înseamnă altă versiune, după ordinea participantului
            v = pe_id["preferinta"].get("valoare")
            randuri.append({"cod": cod, "masura": "preferinta", "raspuns": {"Prima": ordine[0], "A doua": ordine[1]}.get(v, "la fel")})
    return randuri


COLOANE = ["cod", "versiune", "runda", "masura", "durata_s", "reusit", "scor", "clicuri", "comenzi", "defilare_px", "nu_reuseste", "raspuns"]
COLOANE_GRUP = ["masura", "versiune", "persoane", "reusite", "durata_mediana_s", "clicuri_mediana", "sus_medie"]


def scrie_rezumat(dosar: Path = DOSAR) -> tuple[Path, list[dict]]:
    randuri = rezumat(dosar)
    dosar.mkdir(parents=True, exist_ok=True)
    cale = dosar / "rezumat.csv"
    with open(cale, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLOANE)
        w.writeheader()
        w.writerows(randuri)
    return cale, randuri


def pe_grup(randuri: list[dict]) -> list[dict]:
    """Rezultatele de grup, pe versiune și măsură: fără coduri, fără răspunsuri libere, fără profilul participanților."""
    grupe: dict[tuple, list[dict]] = {}
    for r in randuri:
        if r.get("versiune"):
            grupe.setdefault((r["masura"], r["versiune"]), []).append(r)
    rez = []
    for (masura, versiune), lista in sorted(grupe.items()):
        durate = [r["durata_s"] for r in lista if r.get("durata_s") is not None]
        reusite = [r["reusit"] for r in lista if r.get("reusit") is not None]
        scoruri = [r["scor"] for r in lista if r.get("scor") is not None]
        clicuri = [r["clicuri"] for r in lista if r.get("clicuri") is not None]
        rez.append({"masura": masura, "versiune": versiune, "persoane": len(lista),
                    "reusite": sum(bool(x) for x in reusite) if reusite else "",
                    "durata_mediana_s": round(st.median(durate), 1) if durate else "",
                    "clicuri_mediana": st.median(clicuri) if clicuri else "",
                    "sus_medie": round(st.mean(scoruri), 1) if scoruri else ""})
    pref = [r["raspuns"] for r in randuri if r["masura"] == "preferinta"]
    for v in ("m1", "m2", "la fel"):
        if pref:
            rez.append({"masura": "varianta preferată", "versiune": v, "persoane": pref.count(v)})
    ajutor = [r["raspuns"] for r in randuri if r["masura"] == "moderator"]
    if ajutor:
        rez.append({"masura": "a avut nevoie de ajutor", "versiune": "", "persoane": sum(x != "Nu" for x in ajutor)})
    return rez


def publica(dosar: Path = DOSAR, destinatie: Path = PUBLICAT) -> Path:
    _, randuri = scrie_rezumat(dosar)
    destinatie.parent.mkdir(parents=True, exist_ok=True)
    with open(destinatie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLOANE_GRUP)
        w.writeheader()
        w.writerows(pe_grup(randuri))
    return destinatie


def main() -> None:
    ap = argparse.ArgumentParser(description="Sondarea dispeceratului cu oameni")
    ap.add_argument("--port", type=int, default=8060)
    ap.add_argument("--dosar", default=str(DOSAR), help="unde se scriu răspunsurile (implicit outputs/sondare)")
    ap.add_argument("--cadru-public", action="store_true", help="arată figura publicată, nemișcată, în locul previzualizării colectării")
    ap.add_argument("--fara-browser", action="store_true", help="nu deschide singur pagina")
    ap.add_argument("--rezumat", action="store_true", help="scrie rezumat.csv și afișează rezultatele pe versiuni")
    ap.add_argument("--publica", action="store_true", help="scrie docs/rezultate/sondare_m2.csv, doar rezultate de grup")
    a = ap.parse_args()
    dosar = Path(a.dosar)
    if a.rezumat or a.publica:
        cale, randuri = scrie_rezumat(dosar)
        print(f"{cale}: {len(randuri)} rânduri")
        for r in pe_grup(randuri):
            print(r)
        if a.publica:
            print("publicat:", publica(dosar))
        return
    if not a.cadru_public and not colectarea_merge():
        print("ATENȚIE: colectarea nu pare să meargă, deci imaginea din dispecerat nu se va mișca.")
    url = f"http://localhost:{a.port}"
    print(f"Sondare: {url}  (răspunsurile în {dosar})")
    if not a.fara_browser:                 # după ce serverul a apucat să pornească
        threading.Timer(1.5, webbrowser.open, [url]).start()
    creeaza_app(dosar, a.cadru_public).run(host="127.0.0.1", port=a.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
