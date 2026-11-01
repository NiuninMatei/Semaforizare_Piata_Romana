"""Sondarea dispeceratului cu oameni (§ 8): ghid, sarcini și întrebări pe același ecran, pe calculatorul autorului.

Un server local separat de dispecerat. Participantul vede în stânga ghidul, pas cu pas, iar în dreapta dispeceratul,
într-una din cele două versiuni: `m1` (cea prezentată la borna M1, păstrată neschimbată) și `m2` (cea curentă). Datele
sunt simulate, ca toți să aibă aceeași situație și răspunsul corect să se știe: comenzile nu ajung la geamănul digital
și nici pe stradă. Imaginea camerei e previzualizarea estompată a colectării, doar pe ecranul local, sau, cu
`--cadru-public`, figura publicată, nemișcată.

Fiecare participant primește un cod (P1, P2, …), fără nume. Ordinea versiunilor alternează: P1 m1→m2, P2 m2→m1, P3 m2→m1,
P4 m1→m2. Situațiile țin de rundă (prima, a doua), nu de versiune. Fiecare răspuns, clic și comandă se scrie pe loc în
outputs/sondare/<cod>.jsonl, iar o pagină reîncărcată sau un server repornit continuă de unde a rămas.

Sondarea e formativă: arată ce nu se înțelege pe ecran, nu cât de bun e ecranul în general. Din 4 persoane apropiate
autorului, cu autorul alături, se raportează doar „x din 4” și ce au spus, fără procente și fără valori p.

Rulare:     python -m romana.dashboard.sondare            → http://127.0.0.1:8060
            python -m romana.dashboard.sondare --proba    → o probă, în outputs/sondare_proba, care nu se amestecă
Rezultate:  python -m romana.dashboard.sondare --rezumat   → outputs/sondare/rezumat.csv și tabelul pe versiuni
            python -m romana.dashboard.sondare --publica   → docs/rezultate/sondare_m2.csv (doar totaluri)
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
DOSAR_PROBA = OUTPUT_DIR / "sondare_proba"
RADACINA = Path(__file__).resolve().parents[3]
PUBLICAT = RADACINA / "docs" / "rezultate" / "sondare_m2.csv"
CADRU_PUBLIC = RADACINA / "docs" / "imagini" / "camera_piata_romana.jpg"
VERSIUNI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "index.html"}
ORDINI = [("m1", "m2"), ("m2", "m1"), ("m2", "m1"), ("m1", "m2")]

FAZE = ["N–S: Magheru ↔ Lascăr Catargiu prin centru", "E–V: Dacia în jurul insulei",
        "Pietoni: toate trecerile, axa centrală se golește", "N–S, cu intrările Dacia deschise (fără dozare)",
        "E–V, cu intrările Magheru/Catargiu deschise (fără dozare)"]
PLAN = [(0, 12), (1, 14), (2, 12)]              # planul fix din geamăn: verde 12/14/12 s, apoi galben 3 s și roșu 2 s
GALBEN, ROSU, VERDE_MIN, PAS_COMANDA = 3, 2, 10, 5    # ca în SignalController și în bucla geamănului (comanda se citește la 5 s)
VERDE_PE_DACIA = (1, 3, 4)                      # schema arată verde pe Dacia în aceste faze
VERDE_PE_MAGHERU = (0, 3, 4)
AUTOMATE = {"ai", "fix", "max_pressure", "program"}
# Cozile pe brațe în cele două runde; cea mai lungă e alta, ca răspunsul din prima rundă să nu ajute în a doua.
COZI = [{"dacia_vest": 22, "magheru": 11, "catargiu": 6, "dacia_est": 4, "pietoni": 5},
        {"magheru": 21, "dacia_vest": 9, "catargiu": 12, "dacia_est": 6, "pietoni": 3}]
# Debitele nu dau răspunsul la coadă în nicio rundă: cel mai mare debit e mereu pe alt braț.
INTRARI = [{"magheru": 1180, "catargiu": 410, "dacia_vest": 690, "dacia_est": 520},
           {"magheru": 640, "catargiu": 430, "dacia_vest": 1120, "dacia_est": 560}]
IESIRI = {"magheru": 870, "mendeleev": 240, "dacia_vest": 610, "dacia_est": 480, "caderea_bastiliei": 330, "catargiu": 600}
NUME_BRAT = {"magheru": "Magheru", "catargiu": "Lascăr Catargiu", "dacia_est": "Dacia est", "dacia_vest": "Dacia vest"}
# În prima rundă conduce calculatorul, iar imaginea se oprește cât se caută coada; în a doua conduce un om, iar imaginea merge.
RUNDE = [{"mod": "program", "imagine": "oprita"}, {"mod": "manual", "imagine": "merge"}]

NU_POT = "Nu pot spune"
ALEGE_CONDUCE = {"calculator": "Un calculator, singur", "om": "Un om, de la acest ecran"}
ALEGE_IMAGINE = {"merge": "S-a mișcat tot timpul", "oprita": "S-a oprit"}
AM_VAZUT = ["Da, clar", "Da, dar nu eram sigur(ă)", "Nu"]
CAT_DE_USOR = ["Foarte greu", "Greu", "Nici greu, nici ușor", "Ușor", "Foarte ușor"]


def corect_coada(runda: int) -> str:
    c = COZI[runda]
    return NUME_BRAT[max(NUME_BRAT, key=lambda b: c[b])]


def _runda(runda: int, versiune: str) -> list[dict]:
    """Pașii unei variante: pornirea, cele 4 sarcini cu întrebările lor, închiderea, apoi părerile."""
    r = f"r{runda + 1}"
    v = {"versiune": versiune, "runda": runda}
    ec = {**v, "ecran": True}                     # dispeceratul e deschis și se vede
    ac = {**v, "ecran": True, "acoperit": True}   # dispeceratul e deschis, dar acoperit: se răspunde din ce s-a văzut
    sit = RUNDE[runda]
    gata = "Când ați aflat, apăsați „Am terminat”."
    reusit = "Când credeți că ați reușit, apăsați „Am terminat”."
    p = [
        {"id": f"{r}_deschide", "tip": "deschide", **v, "titlu": "Pornim prima variantă" if runda == 0 else "Pornim a doua variantă",
         "text": ["Apăsați butonul de mai jos. Ecranul de supraveghere se deschide în partea din dreapta."] if runda == 0 else
                 ["Puteți face o pauză, dacă doriți. Urmează aceleași sarcini, pe o altă variantă a ecranului.",
                  "Situația din piață s-a schimbat, așa că uitați-vă din nou cu atenție.",
                  "Când sunteți gata, apăsați butonul de mai jos."],
         "buton": "Deschide ecranul de supraveghere", "sit": {"runda": runda, "mod": sit["mod"], "cam": "merge"}},
        {"id": f"{r}_conduce", "tip": "sarcina", "sarcina": 1, **ec,
         "text": ["Uitați-vă la partea din dreapta, fără să apăsați nimic pe ea.",
                  "**Cine schimbă acum culorile semaforului: un calculator sau un om?**", gata]},
        {"id": f"{r}_conduce_r", "tip": "alegere", **ac, "titlu": "Cine schimbă acum culorile semaforului?",
         "optiuni": [*ALEGE_CONDUCE.values(), NU_POT], "corect_din_banc": "conduce"},
        {"id": f"{r}_coada", "tip": "sarcina", "sarcina": 2, **ec, "sit": {"cam": sit["imagine"]},
         "text": ["**Pe care stradă așteaptă acum cele mai multe mașini la semafor?**", gata]},
        {"id": f"{r}_coada_r", "tip": "alegere", **ac, "titlu": "Pe care stradă așteaptă cele mai multe mașini?",
         "optiuni": [*NUME_BRAT.values(), NU_POT], "corect": corect_coada(runda)},
        {"id": f"{r}_imagine_r", "tip": "alegere", **ac, "titlu": "Cât timp ați căutat mașinile, imaginea de la cameră s-a mișcat sau s-a oprit?",
         "optiuni": [*ALEGE_IMAGINE.values(), NU_POT], "corect": ALEGE_IMAGINE[sit["imagine"]]},
        {"id": f"{r}_verde", "tip": "sarcina", "sarcina": 3, **ec, "verifica": "verde", "sit": {"cam": "merge", "mod": "program", "nemiscat": True},
         "text": ["**Dați verde pe Bulevardul Dacia**, ca și cum ați schimba dumneavoastră culorile semaforului.", reusit]},
        {"id": f"{r}_verde_r", "tip": "alegere", **ac, "titlu": "Ce culoare avea semaforul pe Bulevardul Magheru când ați apăsat „Am terminat”?",
         "optiuni": ["Verde", "Galben", "Roșu", NU_POT], "corect_din_banc": "magheru"},
        {"id": f"{r}_verde_vazut", "tip": "alegere", **ac, "titlu": "Ați putut vedea pe ecran dacă s-a schimbat ce ați vrut?", "optiuni": AM_VAZUT},
        {"id": f"{r}_automat", "tip": "sarcina", "sarcina": 4, **ec, "verifica": "automat", "pregateste": "manual_dacia",
         "text": ["**Lăsați din nou calculatorul să schimbe singur culorile semaforului**, ca să nu mai fie nevoie de dumneavoastră.", reusit]},
        {"id": f"{r}_automat_vazut", "tip": "alegere", **ac, "titlu": "Ați putut vedea pe ecran cine schimbă acum culorile?", "optiuni": AM_VAZUT},
        {"id": f"{r}_inchide", "tip": "inchide", **ac, "titlu": "Închideți ecranul de supraveghere",
         "text": ["Ați terminat sarcinile pe această variantă. Apăsați butonul de mai jos: ecranul din dreapta se închide."],
         "buton": "Închide ecranul de supraveghere"},
    ]
    if runda == 0:         # doar la prima vedere: a doua oară s-ar repeta ce a răspuns persoana prima dată
        p += [{"id": f"{r}_culori", "tip": "alegere", **v, "titlu": "Pe desenul pieței, ce credeți că arată o linie roșie groasă pe o stradă?",
               "optiuni": ["O coadă lungă de mașini", "Semaforul e roșu pe strada aceea", "Strada e închisă", NU_POT], "corect": "O coadă lungă de mașini"},
              {"id": f"{r}_real", "tip": "alegere", **v, "titlu": "Dacă apăsați un buton pe ecranul de supraveghere, se schimbă semaforul adevărat din piață?",
               "optiuni": ["Da", "Nu", NU_POT], "corect": "Nu"}]
    p += [{"id": f"{r}_usor", "tip": "alegere", **v, "titlu": "Cât de ușor v-a fost să folosiți această variantă?", "optiuni": CAT_DE_USOR},
          {"id": f"{r}_incurcat", "tip": "text", **v, "titlu": "Ce v-a încurcat la această variantă?",
           "text": ["Puteți scrie câteva cuvinte sau le puteți spune persoanei care v-a invitat, ca să le scrie. Puteți lăsa și gol. "
                    "Vă rugăm să nu scrieți nume sau lucruri personale."], "buton": "Mai departe"}]
    return p


def pasi(ordine: tuple[str, str]) -> list[dict]:
    """Lista pașilor unui participant. `sit` e situația pe care o arată dispeceratul de la acel pas încolo."""
    return [
        {"id": "pregatire", "tip": "info", "titlu": "Pregătire pentru cel care invită", "colectare": True, "text": [
            "Puneți fereastra pe tot ecranul, cu tasta F11, și conectați un mouse cu rotiță. Nu închideți nimic altceva de pe calculator.",
            "Ceilalți participanți nu stau în cameră și nu află nimic despre test până nu termină toți.",
            "Dintre cei mai puțin obișnuiți cu calculatorul, unul să fie P1 sau P4, iar celălalt P2 sau P3.",
            "Stați lângă persoană, dar **nu o ajutați la sarcini**. Dacă vă întreabă ce să facă, spuneți: „Faceți cum credeți”. "
            "Puteți ajuta doar la mouse sau citind textul cu voce tare."],
         "buton": "Predau calculatorul"},
        {"id": "bun_venit", "tip": "info", "titlu": "Bun venit!", "text": [
            "Vă mulțumim că ne ajutați. Verificăm dacă un ecran pentru supravegherea semafoarelor din Piața Romană este ușor de înțeles.",
            "**Testăm ecranul, nu pe dumneavoastră.** Dacă ceva nu merge sau nu se înțelege, vina e a ecranului, iar asta vrem să aflăm.",
            "Durează între 15 și 30 de minute. Vă puteți opri oricând, fără nicio explicație, cu butonul „Mă opresc aici”."],
         "buton": "Mai departe"},
        {"id": "acord", "tip": "info", "titlu": "Ce se întâmplă cu răspunsurile", "text": [
            "Se salvează pe acest calculator, fără nume, doar cu un cod. Se notează și ce apăsați și cât durează. Nu se înregistrează imagine sau sunet.",
            "Le analizează persoana care v-a invitat, cu ajutorul lui Claude, un program de inteligență artificială. "
            "Pentru asta, răspunsurile, inclusiv ce scrieți dumneavoastră, ajung și la firma care îl face, Anthropic, din SUA.",
            "În proiect apar doar totaluri, nu ce a răspuns fiecare. Răspunsurile se șterg după notarea proiectului și, dacă cereți, mai devreme."],
         "buton": "Sunt de acord, începem"},
        {"id": "profil_calculator", "tip": "alegere", "titlu": "Cât de des folosiți calculatorul?", "optiuni": ["Rar sau deloc", "Uneori", "În fiecare zi"]},
        {"id": "cum_lucram", "tip": "info", "titlu": "Cum lucrăm", "text": [
            "Imaginați-vă că lucrați într-un centru care supraveghează semafoarele din Piața Romană. Încercați fără grijă: aici nu se dau note.",
            "În stânga primiți, pe rând, câte o sarcină. O faceți în partea din dreapta, apoi apăsați „Am terminat”. "
            "Partea din dreapta se acoperă și răspundeți la o întrebare, din ce ați văzut.",
            "Dacă în dreapta nu se vede tot, folosiți rotița mouse-ului.",
            "Dacă nu reușiți, apăsați „Nu reușesc”. Nu e nicio problemă.",
            "Veți vedea două variante ale aceluiași ecran, pe rând."],
         "buton": "Am înțeles"},
        *_runda(0, ordine[0]),
        *_runda(1, ordine[1]),
        {"id": "preferinta", "tip": "alegere", "titlu": "Care variantă v-a fost mai ușoară?", "optiuni": ["Prima", "A doua", "La fel"]},
        {"id": "vazut_inainte", "tip": "alegere", "titlu": "Ați mai văzut ecranul acesta înainte de azi?", "optiuni": ["Nu", "Da"]},
        {"id": "multumim", "tip": "info", "titlu": "Gata. Vă mulțumim!", "fara_oprire": True,
         "text": ["Ați terminat, iar răspunsurile s-au salvat.",
                  "Semafoarele de pe ecran erau simulate pe calculator: nimic din ce ați apăsat nu a schimbat ceva pe stradă. "
                  "Vă rugăm să nu le povestiți celorlalți despre test până nu termină toți.",
                  "Spuneți-i, vă rugăm, persoanei care v-a invitat că ați terminat. Ea apasă butonul de mai jos."], "buton": "Mai departe"},
        {"id": "observatii", "tip": "text", "titlu": "Pentru cel care a invitat: ce ați observat?", "fara_oprire": True,
         "text": ["Unde s-a blocat persoana, ce a spus, la ce sarcină a avut nevoie de ajutor. Fără nume. Puteți lăsa și gol."], "buton": "Mai departe"},
        {"id": "moderator", "tip": "alegere", "titlu": "A fost nevoie de ajutor?", "fara_oprire": True,
         "optiuni": ["Nu", "Doar la mouse sau la citit", "La înțelegerea sarcinilor"]},
        {"id": "sfarsit", "tip": "sfarsit", "titlu": "Sesiune încheiată", "fara_oprire": True,
         "text": ["Pentru următorul participant, apăsați butonul. Dacă ați terminat, închideți fereastra și, în fereastra neagră, apăsați Ctrl+C."],
         "buton": "Participantul următor"},
    ]


class Banc:
    """Situația simulată a dispeceratului: aceleași câmpuri ca outputs/live/state.json și sim_state.json.

    Reacția la o comandă e ca în geamăn: faza veche rămâne până la pasul de citire a comenzii (5 s), apoi galben 3 s și
    roșu 2 s, iar faza nouă vine abia după ele. Fiindcă planul stă pe faza N–S cu verdele minim deja atins la sarcina de
    verde, aici reacția durează 5–10 s; în geamănul adevărat poate ajunge la ≈24 s (§ 8)."""

    def __init__(self, ceas=time.time):
        self.ceas = ceas
        self.t0 = self.t_plan = ceas()
        self.runda = 0
        self.mod = "program"
        self.faza_manual = 0
        self.t_manual = self.t0 - 30       # când a început verdele fazei manuale
        self.tranzitie = None              # (faza veche, verdele ei la cerere, momentul cererii, începutul galbenului)
        self.nemiscat = False              # planul stă pe N–S: faza Dacia nu vine singură cât se cere verde pe Dacia
        self.t_nemiscat = self.t0
        self.cam = "merge"
        self.t_cam = self.t0

    def seteaza(self, runda=None, mod=None, cam=None, faza=None, nemiscat=False):
        """Pune direct situația cerută de un pas, fără tranziție."""
        acum = self.ceas()
        if runda is not None:
            self.runda = runda
        if mod is not None:
            self.mod = mod
            self.tranzitie = None
            self.nemiscat = nemiscat
            self.t_nemiscat = acum
            if mod == "manual":
                self.faza_manual = 0 if faza is None else faza
                self.t_manual = acum - 30
        if cam is not None and cam != self.cam:
            self.cam = cam
            self.t_cam = acum

    def comanda(self, mod: str, faza) -> dict:
        """Comanda unui participant; faza verde curentă rămâne, iar o fază nouă vine după galben și roșu."""
        acum = self.ceas()
        f, etapa, verde = self.faza()
        if mod == "manual":
            noua = f if faza is None else int(faza)
            if self.mod == "manual" and self.tranzitie and acum < self.t_manual:
                self.faza_manual = noua            # o tranziție e în curs: doar ținta se schimbă
            elif noua == f and etapa == "green":
                self.faza_manual, self.t_manual, self.tranzitie = f, acum - verde, None
            elif not (self.mod == "manual" and noua == self.faza_manual):
                citire = acum + max(VERDE_MIN - verde, 0)
                t_g = self.t0 + math.ceil((citire - self.t0) / PAS_COMANDA) * PAS_COMANDA
                self.tranzitie = (f, verde, acum, t_g)
                self.faza_manual, self.t_manual = noua, t_g + GALBEN + ROSU
        else:
            if self.mod == "manual" or self.nemiscat:        # planul continuă din faza curentă, nu sare
                decalaj = 0
                for g, v in PLAN:
                    if g == f:
                        self.t_plan = acum - decalaj - min(verde, v - 1)
                        break
                    decalaj += v + GALBEN + ROSU
                else:
                    self.t_plan = acum
            self.tranzitie = None
        self.nemiscat = False
        self.mod = mod
        return {"ok": True, "mod": mod, "timestamp": acum, **({"faza": self.faza_manual} if mod == "manual" else {})}

    def incheie_tranzitia(self) -> None:
        """După o repornire a serverului: comenzile din jurnal se consideră îndeplinite."""
        if self.tranzitie:
            self.t_manual = self.ceas() - 1
            self.tranzitie = None

    def faza(self, acum: float | None = None) -> tuple[int, str, int]:
        """(faza, etapa, verde_s): ca în geamăn, verde_s rămâne cât a ținut verdele și în galben și în roșu."""
        acum = self.ceas() if acum is None else acum
        if self.mod == "manual":
            if self.tranzitie and acum < self.t_manual:
                f, v, t_cerere, t_g = self.tranzitie
                if acum < t_g:
                    return f, "green", v + int(acum - t_cerere)
                return f, ("yellow" if acum < t_g + GALBEN else "red"), v + int(t_g - t_cerere)
            return self.faza_manual, "green", int(acum - self.t_manual)
        if self.nemiscat:
            return 0, "green", VERDE_MIN + int(acum - self.t_nemiscat)
        t = (acum - self.t_plan) % sum(v + GALBEN + ROSU for _, v in PLAN)
        for f, v in PLAN:
            if t < v:
                return f, "green", int(t)
            if t < v + GALBEN:
                return f, "yellow", v
            if t < v + GALBEN + ROSU:
                return f, "red", v
            t -= v + GALBEN + ROSU
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
        intrari = INTRARI[self.runda]
        sim = {"timestamp": acum, "timp_sim": t, "mod": self.mod, "mod_program": "plan_scurt" if self.mod == "program" else None,
               "sursa": "camera live", "faza": faza, "faza_nume": FAZE[faza], "etapa": etapa, "verde_s": verde, "faze": FAZE, "model_ai": True,
               "coada_brate": cozi, "coada_total": total, "vehicule_in_retea": 90 + total, "vehicule_injectate": 412, "pietoni_in_retea": 31,
               "pietoni_injectati": 140, "debite_folosite": intrari, "debit_echilibrat_veh_h": 2800, "pietoni_h_folositi": 620,
               "istoric_coada": istoric, "_varsta_s": 0.4}
        cam = {"timestamp": acum, "fps": 5.9, "conectat": True, "reconectari": 0, "vehicule_urmarite": 64,
               "intrari_veh_h": intrari, "iesiri_veh_h": IESIRI, "pietoni_h": {"dacia_est": 620}, "secunde_interval": 480,
               "_varsta_s": round(20 + acum - self.t_cam, 1) if self.cam == "oprita" else 0.4}
        return {"camera": cam, "simulare": sim, "comanda": {"mod": self.mod, "timestamp": acum}, "ora_server": acum}

    def verde_pe_dacia(self) -> bool:
        return self.mod == "manual" and self.faza_manual in VERDE_PE_DACIA

    def e_automat(self) -> bool:
        return self.mod in AUTOMATE

    def _culoare_magheru(self, acum: float) -> str:
        faza, etapa, _ = self.faza(acum)
        if faza not in VERDE_PE_MAGHERU:
            return "Roșu"
        return {"green": "Verde", "yellow": "Galben", "red": "Roșu"}[etapa]

    def adevar(self, ce: str) -> list[str]:
        """Răspunsurile corecte în clipa acoperirii ecranului; pagina se actualizează o dată pe secundă, deci contează și ce era cu puțin înainte."""
        acum = self.ceas()
        if ce == "conduce":
            return [ALEGE_CONDUCE["calculator" if self.e_automat() else "om"]]
        return sorted({self._culoare_magheru(acum), self._culoare_magheru(acum - 1.5)})


def citeste_participant(cale: Path) -> list[dict]:
    rez = []
    for linie in cale.read_text(encoding="utf-8").split("\n"):
        if linie.strip():
            try:
                rez.append(json.loads(linie))
            except json.JSONDecodeError:      # ultima linie, dacă scrierea a fost întreruptă
                pass
    return rez


class Sesiune:
    """Un participant: pașii, poziția și jurnalul lui, scris linie cu linie."""

    def __init__(self, cod: str, ordine: tuple[str, str], dosar: Path, banc: Banc, ceas=time.time):
        self.cod, self.ordine, self.dosar, self.banc, self.ceas = cod, ordine, dosar, banc, ceas
        self.pasi = pasi(ordine)
        self.jurnal = dosar / f"{cod}.jsonl"
        self.poz = 0
        self.lacat = threading.RLock()
        self.corect_calculat = None
        self._intra(self._reia() if self.jurnal.exists() else None)

    def _reia(self) -> dict:
        """Reface din jurnal situația și contoarele pasului la care s-a oprit: comenzile, clicurile, adevărul notat."""
        d = self.jurnal.read_bytes()
        if d and not d.endswith(b"\n"):            # scriere întreruptă: linia următoare nu trebuie să se lipească de ea
            with open(self.jurnal, "ab") as f:
                f.write(b"\n")
        r = {"t_pas": None, "clicuri": 0, "comenzi": [], "corect": None}
        for o in citeste_participant(self.jurnal):
            tip = o.get("tip")
            if tip == "pas":
                self.poz = min(o["index"] + 1, len(self.pasi) - 1)
                r = {"t_pas": o["t"], "clicuri": 0, "comenzi": [], "corect": None}
                if self.pasi[self.poz].get("sit"):
                    self.banc.seteaza(**self.pasi[self.poz]["sit"])
            elif tip == "comanda":
                self.banc.comanda(o["mod"], o.get("faza"))
                r["comenzi"].append([o["mod"], o.get("faza")])
            elif tip == "clic":
                r["clicuri"] += 1
            elif tip == "pregatit":
                self.banc.seteaza(mod="manual", faza=VERDE_PE_DACIA[0])
            elif tip == "corect":
                r["corect"] = o["valoare"]
        self.banc.incheie_tranzitia()
        return r

    def noteaza(self, o: dict) -> None:
        with self.lacat:
            self.dosar.mkdir(parents=True, exist_ok=True)
            nou = not self.jurnal.exists()
            with open(self.jurnal, "a", encoding="utf-8") as f:
                if nou:                 # fișierul apare abia la primul răspuns: un cod neatins nu consumă un loc
                    f.write(json.dumps({"t": round(self.ceas(), 3), "tip": "inceput", "ordine": list(self.ordine)}, ensure_ascii=False) + "\n")
                f.write(json.dumps({"t": round(self.ceas(), 3), **o}, ensure_ascii=False) + "\n")

    def pas(self) -> dict:
        return self.pasi[self.poz]

    def _intra(self, reluare: dict | None = None) -> None:
        """Pregătește dispeceratul pentru pasul curent, indiferent ce a făcut participantul înainte."""
        p = self.pas()
        r = reluare or {}
        self.t_pas = r.get("t_pas") or self.ceas()
        self.clicuri = r.get("clicuri", 0)
        self.comenzi = r.get("comenzi", [])
        self.corect_calculat = r.get("corect")
        if p.get("corect_din_banc") and self.corect_calculat is None:     # adevărul din clipa în care ecranul s-a acoperit
            self.corect_calculat = self.banc.adevar(p["corect_din_banc"])
            self.noteaza({"tip": "corect", "pas": p["id"], "valoare": self.corect_calculat})
        if reluare is not None:
            return
        if p.get("sit"):
            self.banc.seteaza(**p["sit"])
        if p.get("pregateste") == "manual_dacia" and not self.banc.verde_pe_dacia():
            self.banc.seteaza(mod="manual", faza=VERDE_PE_DACIA[0])   # sarcina de dinainte n-a reușit: începem de unde ar fi ajuns
            self.noteaza({"tip": "pregatit", "pas": p["id"]})

    def raspunde(self, valoare=None, nu_reuseste: bool = False, id_pas: str | None = None) -> None:
        """Înregistrează pasul curent și trece la următorul; un răspuns pentru alt pas sau cu altă valoare decât opțiunile se ignoră."""
        with self.lacat:
            p = self.pas()
            if p["tip"] == "sfarsit" or (id_pas is not None and id_pas != p["id"]):
                return
            if p["tip"] == "alegere" and valoare not in p["optiuni"]:
                return
            if p["tip"] == "text":
                valoare = str(valoare or "")[:1000]
            r = {"tip": "pas", "index": self.poz, "id": p["id"], "tip_pas": p["tip"], "durata_s": round(self.ceas() - self.t_pas, 2)}
            for k in ("versiune", "runda", "sarcina"):
                if k in p:
                    r[k] = p[k]
            if p["tip"] in ("alegere", "text"):
                r["valoare"] = valoare
            if "corect" in p:
                r["corect"] = valoare == p["corect"]
            if p.get("corect_din_banc"):
                r["corect"] = valoare in self.corect_calculat
            if p["tip"] == "sarcina":
                r.update(clicuri=self.clicuri, comenzi=self.comenzi, nu_reuseste=nu_reuseste)
                if p.get("verifica") == "verde":
                    r["reusit"] = self.banc.verde_pe_dacia() and not nu_reuseste
                    r["mod_final"], r["faza_finala"] = self.banc.mod, self.banc.faza()[0]
                elif p.get("verifica") == "automat":
                    r["reusit"] = self.banc.e_automat() and not nu_reuseste
                    r["mod_final"] = self.banc.mod
            self.noteaza(r)
            self.poz += 1
            self._intra()

    def clic(self, eticheta: str) -> None:
        with self.lacat:
            self.clicuri += 1
            self.noteaza({"tip": "clic", "pas": self.pas()["id"], "eticheta": eticheta[:60]})

    def comanda(self, mod: str, faza) -> dict:
        """Comenzile contează doar în timpul sarcinilor; în rest, ecranul e acoperit sau închis."""
        with self.lacat:
            if self.pas()["tip"] != "sarcina":
                return {"ok": True, "mod": mod, "timestamp": self.ceas()}
            r = self.banc.comanda(mod, faza)
            self.comenzi.append([mod, faza])
            self.noteaza({"tip": "comanda", "pas": self.pas()["id"], "mod": mod, "faza": faza})
            return r

    def renunta(self) -> None:
        self.noteaza({"tip": "renuntat", "pas": self.pas()["id"]})

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


def _incheiat(linii: list[dict]) -> bool:
    return any(o.get("id") == "moderator" or o.get("tip") == "renuntat" for o in linii)


def colectarea_merge(prag_s: float = 30, ceas=time.time) -> bool:
    """Imaginea din dispecerat se mișcă doar dacă previzualizarea colectării e proaspătă."""
    try:
        return ceas() - (LIVE / "frame.jpg").stat().st_mtime < prag_s
    except OSError:
        return False


def _corp() -> dict:
    b = request.get_json(force=True, silent=True)
    return b if isinstance(b, dict) else {}


def creeaza_app(dosar: Path = DOSAR, cadru_public: bool = False, ceas=time.time, proba: bool = False) -> Flask:
    app = Flask(__name__, static_folder=None)
    banc = Banc(ceas)
    stare = {"sesiune": None}

    def sesiune() -> Sesiune:
        if stare["sesiune"] is None:
            neterminat = None
            for j in _dupa_numar(dosar):
                if not _incheiat(citeste_participant(j)):
                    neterminat = j
            if neterminat is not None:
                linii = citeste_participant(neterminat)
                implicit = ORDINI[(int(neterminat.stem[1:]) - 1) % len(ORDINI)]
                ordine = next((tuple(o["ordine"]) for o in linii if o.get("tip") == "inceput"), implicit)
                stare["sesiune"] = Sesiune(neterminat.stem, ordine, dosar, banc, ceas)
            else:
                banc.seteaza(runda=0, mod="program", cam="merge")     # participant nou: situația de la început
                cod, ordine = urmatorul_cod(dosar)
                stare["sesiune"] = Sesiune(cod, ordine, dosar, banc, ceas)
        return stare["sesiune"]

    def public(s: Sesiune) -> dict:
        p = s.pas_public()
        if p.get("colectare"):
            p["colectare"] = "fixa" if cadru_public else ("merge" if colectarea_merge() else "oprita")
        if proba:
            p["proba"] = True
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
        b = _corp()
        s = sesiune()
        s.raspunde(b.get("valoare"), bool(b.get("nu_reuseste")), b.get("id"))
        return jsonify(public(s))

    @app.post("/sondare/clic")
    def clic():
        sesiune().clic(str(_corp().get("eticheta", "")))
        return jsonify({"ok": True})

    @app.post("/sondare/renunta")
    def renunta():
        """Participantul se oprește: ce a răspuns rămâne, iar următorul om primește un cod nou."""
        sesiune().renunta()
        stare["sesiune"] = None
        return jsonify(public(sesiune()))

    @app.post("/sondare/urmatorul")
    def urmatorul():
        s = sesiune()
        if s.pas()["tip"] == "sfarsit":
            stare["sesiune"] = None
        return jsonify(public(sesiune()))

    # Aceleași adrese ca serverul dispeceratului, ca paginile să meargă neschimbate; nimic din outputs/live nu se scrie.
    @app.get("/api/state")
    def api_stare():
        return jsonify(banc.stare())

    @app.post("/api/command")
    def api_comanda():
        b = _corp()
        mod = b.get("mod")
        if mod not in AUTOMATE | {"manual"}:
            return jsonify({"eroare": "mod necunoscut"}), 400
        faza = b.get("faza")
        if mod == "manual" and faza is not None:
            try:
                faza = int(faza)
            except (TypeError, ValueError):
                return jsonify({"eroare": "fază invalidă"}), 400
            if not 0 <= faza < len(FAZE):
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


NUME_SARCINA = {1: "cine schimbă culorile", 2: "cea mai lungă coadă", 3: "verde pe Dacia", 4: "înapoi la calculator"}
RASPUNS_SARCINA = {1: "conduce_r", 2: "coada_r"}
INTREBARI = {"imagine_r": "imaginea oprită", "verde_r": "culoarea pe Magheru", "verde_vazut": "a văzut schimbarea",
             "automat_vazut": "a văzut cine conduce", "culori": "linia roșie", "real": "semaforul adevărat", "usor": "ușor sau foarte ușor"}
TEXT_LIBER = {"incurcat": "ce a încurcat"}
PROFIL = ("profil_calculator", "vazut_inainte", "moderator", "observatii")
COLOANE = ["cod", "terminat", "versiune", "runda", "masura", "durata_s", "reusit", "clicuri", "comenzi", "nu_reuseste", "raspuns"]
COLOANE_GRUP = ["masura", "versiune", "persoane", "reusite", "persoane_prima_runda", "reusite_prima_runda"]


def rezumat(dosar: Path = DOSAR) -> list[dict]:
    """Un rând pe participant, versiune și măsură; plus părerile, profilul și ce a notat cel care a invitat (doar local)."""
    randuri = []
    for cale in _dupa_numar(dosar):
        toate = citeste_participant(cale)
        pasi_p = [o for o in toate if o.get("tip") == "pas"]
        pe_id = {o["id"]: o for o in pasi_p}
        cod = cale.stem
        terminat = "moderator" in pe_id
        ordine = next((o["ordine"] for o in toate if o.get("tip") == "inceput"), None)
        for runda in (0, 1):
            r = f"r{runda + 1}"
            baza = {"cod": cod, "terminat": terminat, "runda": runda + 1}
            for o in pasi_p:
                if o.get("runda") != runda:
                    continue
                id_scurt = o["id"][3:]
                if o["tip_pas"] == "sarcina":
                    sarc = o["sarcina"]
                    rasp = pe_id.get(f"{r}_{RASPUNS_SARCINA[sarc]}") if sarc in RASPUNS_SARCINA else None
                    reusit = o.get("reusit") if sarc not in RASPUNS_SARCINA else bool(rasp and rasp.get("corect") and not o.get("nu_reuseste"))
                    randuri.append({**baza, "versiune": o["versiune"], "masura": f"sarcina {sarc}: {NUME_SARCINA[sarc]}", "durata_s": o["durata_s"],
                                    "reusit": reusit, "clicuri": o.get("clicuri"), "comenzi": len(o.get("comenzi", [])),
                                    "nu_reuseste": o.get("nu_reuseste"), "raspuns": rasp.get("valoare") if rasp else None})
                elif id_scurt in INTREBARI:
                    v = o.get("valoare")
                    if id_scurt in ("verde_vazut", "automat_vazut"):
                        reusit = v == AM_VAZUT[0]
                    elif id_scurt == "usor":
                        reusit = v in CAT_DE_USOR[3:]
                    else:
                        reusit = o.get("corect")
                    randuri.append({**baza, "versiune": o["versiune"], "masura": INTREBARI[id_scurt], "reusit": reusit, "raspuns": v})
                elif id_scurt in TEXT_LIBER and o.get("valoare"):
                    randuri.append({**baza, "versiune": o["versiune"], "masura": TEXT_LIBER[id_scurt], "raspuns": o["valoare"]})
        for k in PROFIL:
            if pe_id.get(k, {}).get("valoare"):
                randuri.append({"cod": cod, "terminat": terminat, "masura": k, "raspuns": pe_id[k]["valoare"]})
        if "preferinta" in pe_id and ordine:      # „Prima” / „A doua” înseamnă altă versiune, după ordinea participantului
            v = pe_id["preferinta"].get("valoare")
            randuri.append({"cod": cod, "terminat": terminat, "masura": "preferinta", "raspuns": {"Prima": ordine[0], "A doua": ordine[1]}.get(v, "la fel")})
    return randuri


def scrie_rezumat(dosar: Path = DOSAR) -> tuple[Path, list[dict]]:
    randuri = rezumat(dosar)
    dosar.mkdir(parents=True, exist_ok=True)
    cale = dosar / "rezumat.csv"
    with open(cale, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLOANE)
        w.writeheader()
        w.writerows(randuri)
    return cale, randuri


def pe_grup(randuri: list[dict], local: bool = False) -> list[dict]:
    """Totaluri pe versiune și măsură, doar pentru cei care au terminat: fără coduri, fără text liber, fără profil.

    Prima rundă se dă separat: e singura la prima vedere, deci singura fără efectul exercițiului. Duratele, doar `local`:
    între persoane de vârste foarte diferite nu se pot compara."""
    terminati = [r for r in randuri if r.get("terminat")]
    grupe: dict[tuple, list[dict]] = {}
    for r in terminati:
        if r.get("versiune") and r["masura"] not in TEXT_LIBER.values():
            grupe.setdefault((r["masura"], r["versiune"]), []).append(r)
    rez = []
    for (masura, versiune), lista in sorted(grupe.items()):
        prima = [r for r in lista if r.get("runda") == 1]
        rand = {"masura": masura, "versiune": versiune, "persoane": len(lista), "reusite": sum(bool(r.get("reusit")) for r in lista),
                "persoane_prima_runda": len(prima), "reusite_prima_runda": sum(bool(r.get("reusit")) for r in prima)}
        if local:
            durate = [r["durata_s"] for r in lista if r.get("durata_s") is not None]
            clicuri = [r["clicuri"] for r in lista if r.get("clicuri") is not None]
            rand["durata_mediana_s"] = round(st.median(durate), 1) if durate else ""
            rand["clicuri_mediana"] = st.median(clicuri) if clicuri else ""
        rez.append(rand)
    pref = [r["raspuns"] for r in terminati if r["masura"] == "preferinta"]
    for v in ("m1", "m2", "la fel"):
        if pref:
            rez.append({"masura": "varianta preferată", "versiune": v, "persoane": pref.count(v)})
    ajutor = [r["raspuns"] for r in terminati if r["masura"] == "moderator"]
    if ajutor:
        rez.append({"masura": "a avut nevoie de ajutor la sarcini", "versiune": "", "persoane": sum(x == "La înțelegerea sarcinilor" for x in ajutor)})
    return rez


def publica(dosar: Path = DOSAR, destinatie: Path = PUBLICAT, minim: int = 3) -> Path:
    """Totalurile publice; sub `minim` persoane care au terminat, un rând ar fi chiar răspunsul cuiva."""
    _, randuri = scrie_rezumat(dosar)
    terminati = {r["cod"] for r in randuri if r.get("terminat")}
    if len(terminati) < minim:
        raise SystemExit(f"Doar {len(terminati)} persoane au terminat; pentru publicare sunt necesare cel puțin {minim}.")
    destinatie.parent.mkdir(parents=True, exist_ok=True)
    with open(destinatie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLOANE_GRUP)
        w.writeheader()
        w.writerows(pe_grup(randuri))
    return destinatie


def versiuni_identice() -> bool:
    a, b = (VERSIUNI[v].read_bytes().replace(b"\r\n", b"\n") for v in ("m1", "m2"))
    return a == b


def main() -> None:
    ap = argparse.ArgumentParser(description="Sondarea dispeceratului cu oameni")
    ap.add_argument("--port", type=int, default=8060)
    ap.add_argument("--dosar", default=None, help="unde se scriu răspunsurile (implicit outputs/sondare)")
    ap.add_argument("--proba", action="store_true", help="o probă a ghidului, în outputs/sondare_proba, care nu se amestecă cu răspunsurile adevărate")
    ap.add_argument("--cadru-public", action="store_true", help="doar la probe: figura publicată, nemișcată, în locul previzualizării colectării")
    ap.add_argument("--fara-browser", action="store_true", help="nu deschide singur pagina")
    ap.add_argument("--rezumat", action="store_true", help="scrie rezumat.csv și afișează rezultatele pe versiuni")
    ap.add_argument("--publica", action="store_true", help="scrie docs/rezultate/sondare_m2.csv, doar totaluri")
    a = ap.parse_args()
    dosar = Path(a.dosar) if a.dosar else (DOSAR_PROBA if a.proba else DOSAR)
    if a.rezumat or a.publica:
        cale, randuri = scrie_rezumat(dosar)
        print(f"{cale}: {len(randuri)} rânduri")
        for r in pe_grup(randuri, local=True):
            print(r)
        if a.publica:
            print("publicat:", publica(dosar))
        return
    if dosar == DOSAR:                     # sesiunile adevărate consumă oameni care apoi nu mai sunt la prima vedere
        if a.cadru_public:
            raise SystemExit("Figura nemișcată merge doar la probe: --proba.")
        if versiuni_identice():
            raise SystemExit("Versiunile m1 și m2 sunt identice: întâi reparațiile din static/index.html, apoi sondarea. O probă: --proba.")
        if not colectarea_merge():
            raise SystemExit("Colectarea nu merge, deci imaginea din dispecerat nu s-ar mișca. Porniți-o întâi; o probă: --proba.")
    url = f"http://127.0.0.1:{a.port}"
    print(f"Sondare: {url}  (răspunsurile în {dosar})")
    if not a.fara_browser:                 # după ce serverul a apucat să pornească
        threading.Timer(1.5, webbrowser.open, [url]).start()
    creeaza_app(dosar, a.cadru_public, proba=dosar != DOSAR).run(host="127.0.0.1", port=a.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
