"""Sondarea dispeceratului cu oameni (§ 8): o pagină statică, deschisă cu un link, fără server și fără instalare.

Pagina publicată în docs/sondare (GitHub Pages) are în stânga ghidul, pas cu pas, iar în dreapta dispeceratul, într-una din cele
două versiuni: `m1` (cea prezentată la borna M1, păstrată neschimbată) și `m2` (cea curentă). Datele sunt simulate în browser, ca
toți să aibă aceeași situație și răspunsul corect să se știe: comenzile nu ajung la geamănul digital și nici pe stradă. Imaginea
camerei e fotografia publicată, cu persoanele și plăcuțele estompate; laptopul care colectează nu e implicat deloc.

Pagina nu trimite nimic singură: o regulă de securitate a browserului oprește orice cerere. Răspunsurile stau în fila persoanei.
La final, persoana vede tot ce s-a notat și, dacă vrea, apasă „Trimite”, care deschide un formular Google completat cu acest text.
Formularul apare doar în linkurile date de autor (`?g=grup&o=ordine&f=formular&e=intrare`), deci adresa lui nu e în depozit;
cine găsește singur pagina o poate încerca, dar nu are ce trimite. Grupurile: `a` persoanele apropiate autorului, `c` colegii.

Sondarea e formativă: arată ce nu se înțelege pe ecran, nu cât de bun e ecranul în general. Se raportează doar „x din N” pe grupuri
și ce au spus, fără procente și fără valori p.

Rulare:     python -m romana.dashboard.sondare --pachet    → refac docs/sondare din sursele din static/
            python -m romana.dashboard.sondare --local     → pagina, pe acest calculator: http://127.0.0.1:8060/sondare/
            python -m romana.dashboard.sondare --linkuri   → linkurile pentru invitați (din outputs/sondare/formular.json)
Rezultate:  textele primite, în outputs/sondare/primite/R<n>.txt
            python -m romana.dashboard.sondare --rezumat   → outputs/sondare/rezumat.csv, tabelul pe grupuri și versiuni și ce nu se numără
            python -m romana.dashboard.sondare --publica   → docs/rezultate/sondare_m2.csv (doar totaluri)

Integritatea (pagina v2, din 03.11.2026, seara): textul nu mai arată răspunsurile așteptate, iar la sfârșit are un cod de control.
Un text schimbat după ce l-a scris pagina (codul nu se potrivește sau lipsește ori, la v1, o corectură ca „X (așteptat: X)”) nu se numără.
O a doua trecere în aceeași filă („de la capăt”) se numără doar dacă autorul confirmă că e altă persoană, în
outputs/sondare/confirmari.json: {"R5": "altă persoană"}.
"""
from __future__ import annotations

import argparse
import csv
import functools
import http.server
import json
import re
import shutil
import statistics as st
import sys
import threading
import unicodedata
import webbrowser
from pathlib import Path

from romana.common import OUTPUT_DIR

STATIC = Path(__file__).parent / "static"
DOSAR = OUTPUT_DIR / "sondare"
RADACINA = Path(__file__).resolve().parents[3]
DOCS = RADACINA / "docs"
PACHET = DOCS / "sondare"
PUBLICAT = DOCS / "rezultate" / "sondare_m2.csv"
IMAGINE_PUBLICA = "../imagini/camera_piata_romana.jpg"
ADRESA_PUBLICA = "https://niuninmatei.github.io/Semaforizare_Piata_Romana/sondare/"
URL_PROIECT = "https://github.com/NiuninMatei/Semaforizare_Piata_Romana"
URL_CAMERA = "https://webcamromania.ro/webcam-orase/webcam-piata-romana-bucuresti/"
VERSIUNI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "index.html"}
GRUPURI = {"a": "persoane apropiate", "c": "colegi"}
VERSIUNE_PAGINA = "v2"       # v1, până pe 03.11.2026, seara: răspunsurile așteptate la vedere, fără cod de control
LUNGIME_TEXT = 300

FAZE = ["N–S: Magheru ↔ Lascăr Catargiu prin centru", "E–V: Dacia în jurul insulei",
        "Pietoni: toate trecerile, axa centrală se golește", "N–S, cu intrările Dacia deschise (fără dozare)",
        "E–V, cu intrările Magheru/Catargiu deschise (fără dozare)", "Golirea centrului, fără pietoni"]
PLAN = [(0, 72), (1, 48), (5, 3)]               # planul observat din geamăn (§ 6.5): verde 72/48/3 s, apoi galben 3 s și roșu 2 s
GALBEN, ROSU, VERDE_MIN, PAS_COMANDA = 3, 2, 10, 5    # ca în SignalController și în bucla geamănului (comanda se citește la 5 s)
INTARZIERE_PIETONI, DEGAJARE_PIETONI = 28, 6     # ca în SemaforCuPietoni: pietonii pornesc după vehicule și termină traversarea înaintea galbenului
VERDE_PE_DACIA = (1, 3, 4)                      # schema arată verde pe Dacia în aceste faze
VERDE_PE_MAGHERU = (0, 3, 4)
AUTOMATE = ("ai", "fix", "max_pressure", "program")
# Cozile pe brațe în cele două runde; cea mai lungă e alta, ca răspunsul din prima rundă să nu ajute în a doua.
COZI = [{"dacia_vest": 22, "magheru": 11, "catargiu": 6, "dacia_est": 4, "pietoni": 5},
        {"magheru": 21, "dacia_vest": 9, "catargiu": 12, "dacia_est": 6, "pietoni": 3}]
# Debitele nu dau răspunsul la coadă în nicio rundă: cel mai mare debit e mereu pe alt braț.
INTRARI = [{"magheru": 1180, "catargiu": 410, "dacia_vest": 690, "dacia_est": 520},
           {"magheru": 640, "catargiu": 430, "dacia_vest": 1120, "dacia_est": 560}]
IESIRI = {"magheru": 870, "mendeleev": 240, "dacia_vest": 610, "dacia_est": 480, "caderea_bastiliei": 330, "catargiu": 600}
NUME_BRAT = {"magheru": "Magheru", "catargiu": "Lascăr Catargiu", "dacia_est": "Dacia est", "dacia_vest": "Dacia vest"}
# În prima rundă conduce calculatorul, în a doua un om.
RUNDE = [{"mod": "program"}, {"mod": "manual"}]

NU_POT = "Nu pot spune"
ALEGE_CONDUCE = {"calculator": "Un calculator, singur", "om": "Un om, de la acest ecran"}
AM_VAZUT = ["Da, clar", "Da, dar nu eram sigur(ă)", "Nu"]
CAT_DE_USOR = ["Foarte greu", "Greu", "Nici greu, nici ușor", "Ușor", "Foarte ușor"]
AJUTOR = ["Nu", "Doar la mouse sau la citit", "Da, la înțelegerea sarcinilor"]
# Pe un ecran îngust, ghidul stă deasupra dispeceratului.
PE_TELEFON = [("în partea din dreapta", "în partea de jos"), ("partea din dreapta", "partea de jos"), ("Partea din dreapta", "Partea de jos"),
              ("aplicația din dreapta", "aplicația de jos"), ("În stânga primiți", "Sus primiți"), ("Răspundeți în stânga", "Răspundeți sus"),
              ("Dacă în dreapta nu se vede tot, folosiți rotița mouse-ului sau două degete pe suprafața tactilă", "Dacă jos nu se vede tot, derulați cu degetul")]
NUME_SARCINA = {1: "cine schimbă culorile", 2: "cea mai lungă coadă", 3: "verde pe Dacia", 4: "înapoi la calculator"}


def corect_coada(runda: int) -> str:
    c = COZI[runda]
    return NUME_BRAT[max(NUME_BRAT, key=lambda b: c[b])]


def _sarcina(n: int) -> dict:
    return {"sarcina": n, "eticheta": f"Sarcina {n}, {NUME_SARCINA[n]}"}


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
         "text": ["Apăsați butonul de mai jos. Aplicația se deschide în partea din dreapta."] if runda == 0 else
                 ["Puteți face o pauză, dacă doriți. Urmează aceleași sarcini, pe o altă variantă a aplicației.",
                  "Situația din piață s-a schimbat, așa că uitați-vă din nou cu atenție.",
                  "Când sunteți gata, apăsați butonul de mai jos."],
         "buton": "Deschide aplicația", "sit": {"runda": runda, "mod": sit["mod"]}},
        {"id": f"{r}_conduce", "tip": "sarcina", **_sarcina(1), **ec,
         "text": ["Uitați-vă la partea din dreapta, fără să apăsați nimic pe ea.",
                  "**Cine schimbă acum culorile semaforului: un calculator sau un om?**", gata]},
        {"id": f"{r}_conduce_r", "tip": "alegere", **ac, "titlu": "Cine schimbă acum culorile semaforului?", "eticheta": "Cine schimbă culorile",
         "optiuni": [*ALEGE_CONDUCE.values(), NU_POT], "corect_din_banc": "conduce"},
        {"id": f"{r}_coada", "tip": "sarcina", **_sarcina(2), **ec,
         "text": ["**Pe care stradă așteaptă acum cele mai multe mașini la semafor?**", gata]},
        {"id": f"{r}_coada_r", "tip": "alegere", **ac, "titlu": "Pe care stradă așteaptă cele mai multe mașini?", "eticheta": "Cele mai multe mașini",
         "optiuni": [*NUME_BRAT.values(), NU_POT], "corect": corect_coada(runda)},
        {"id": f"{r}_verde", "tip": "sarcina", **_sarcina(3), **ec, "verifica": "verde", "sit": {"mod": "program", "nemiscat": True},
         "text": ["**Dați verde pe Bulevardul Dacia**, ca și cum ați schimba dumneavoastră culorile semaforului.", reusit]},
        {"id": f"{r}_verde_r", "tip": "alegere", **ac, "titlu": "Ce culoare avea semaforul pe Bulevardul Magheru când ați apăsat „Am terminat”?",
         "eticheta": "Culoarea pe Magheru", "optiuni": ["Verde", "Galben", "Roșu", NU_POT], "corect_din_banc": "magheru"},
        {"id": f"{r}_verde_vazut", "tip": "alegere", **ac, "titlu": "Ați putut vedea în aplicație dacă s-a schimbat ce ați vrut?",
         "eticheta": "A văzut schimbarea", "optiuni": AM_VAZUT},
        {"id": f"{r}_automat", "tip": "sarcina", **_sarcina(4), **ec, "verifica": "automat", "pregateste": "manual_dacia",
         "text": ["**Lăsați din nou calculatorul să schimbe singur culorile semaforului**, ca să nu mai fie nevoie de dumneavoastră.", reusit]},
        {"id": f"{r}_automat_vazut", "tip": "alegere", **ac, "titlu": "Ați putut vedea în aplicație cine schimbă acum culorile?",
         "eticheta": "A văzut cine conduce", "optiuni": AM_VAZUT},
        {"id": f"{r}_inchide", "tip": "inchide", **ac, "titlu": "Închideți aplicația",
         "text": ["Ați terminat sarcinile pe această variantă. Apăsați butonul de mai jos: aplicația din dreapta se închide."],
         "buton": "Închide aplicația"},
    ]
    if runda == 0:         # doar la prima vedere: a doua oară s-ar repeta ce a răspuns persoana prima dată
        p += [{"id": f"{r}_culori", "tip": "alegere", **v, "titlu": "Pe desenul pieței, ce credeți că arată o linie roșie groasă pe o stradă?",
               "eticheta": "Linia roșie", "optiuni": ["O coadă lungă de mașini", "Semaforul e roșu pe strada aceea", "Strada e închisă", NU_POT],
               "corect": "O coadă lungă de mașini"},
              {"id": f"{r}_real", "tip": "alegere", **v, "titlu": "Dacă apăsați un buton în aplicație, se schimbă semaforul adevărat din piață?",
               "eticheta": "Semaforul adevărat", "optiuni": ["Da", "Nu", NU_POT], "corect": "Nu"}]
    p += [{"id": f"{r}_usor", "tip": "alegere", **v, "titlu": "Cât de ușor v-a fost să folosiți această variantă?", "eticheta": "Cât de ușor", "optiuni": CAT_DE_USOR},
          {"id": f"{r}_incurcat", "tip": "text", **v, "titlu": "Ce v-a încurcat la această variantă?", "eticheta": "Ce a încurcat",
           "text": ["Puteți scrie câteva cuvinte sau puteți lăsa gol. Vă rugăm să nu scrieți nume sau lucruri personale."], "buton": "Mai departe"}]
    return p


def pasi(ordine: tuple[str, str] = ("m1", "m2")) -> list[dict]:
    """Lista pașilor unei persoane. `sit` e situația pe care o arată dispeceratul de la acel pas încolo."""
    return [
        {"id": "bun_venit", "tip": "info", "titlu": "Bun venit!", "text": [
            "Vă mulțumim că ne ajutați. Verificăm dacă o aplicație care arată semafoarele din Piața Romană și cozile de mașini, "
            "într-o simulare pe calculator, este ușor de înțeles. Este un proiect universitar.",
            "**Verificăm aplicația, nu pe dumneavoastră: nu există răspunsuri bune sau greșite.** Dacă ceva nu merge sau nu se înțelege, "
            "e o problemă a aplicației, iar asta vrem să aflăm.",
            "Durează între 10 și 20 de minute, pe un calculator. Vă puteți opri oricând, fără nicio explicație, cu butonul „Mă opresc aici”.",
            "**Vă rugăm să nu discutați cu alți participanți la acest sondaj despre răspunsuri**, ca rezultatele să fie cât mai apropiate de opinia dumneavoastră reală."],
         "buton": "Mai departe"},
        {"id": "acord", "tip": "info", "lung": True, "titlu": "Ce se întâmplă cu răspunsurile",
         "text_invitat": [
            "Pagina nu cere nume, cont sau adresă de e-mail. Ce răspundeți, cât durează și ce apăsați se notează doar în această filă a browserului. "
            "Nu se înregistrează imagine sau sunet.",
            "**La final vedeți tot ce s-a notat și decideți dacă trimiteți.** Dacă închideți fila înainte, totul dispare.",
            "Dacă trimiteți, textul ajunge printr-un formular Google la persoana care v-a invitat. Fiindcă sunteți puțini, ea poate bănui al cui e un răspuns. "
            "O ajută Claude, un program de inteligență artificială, deci textul ajunge și la firma care îl face, Anthropic, din SUA.",
            "În proiect apar doar totaluri, nu ce a răspuns fiecare. Răspunsurile se șterg după notarea proiectului și, dacă cereți, mai devreme.",
            "GitHub, care găzduiește pagina, notează adresa IP a vizitatorilor, din motive de securitate. Google o vede dacă deschideți formularul."],
         "text_deschis": [
            "Aceasta e o probă deschisă: nimic din ce faceți aici nu se trimite nicăieri, iar când închideți fila totul dispare.",
            "Pagina nu cere nume, cont sau adresă de e-mail și nu folosește cookie-uri. Nu se înregistrează imagine sau sunet.",
            "GitHub, care găzduiește pagina, notează adresa IP a vizitatorilor, din motive de securitate."],
         "buton": "Sunt de acord, începem"},
        {"id": "profil_calculator", "tip": "alegere", "titlu": "Cât de des folosiți calculatorul?", "eticheta": "Folosește calculatorul",
         "optiuni": ["Rar sau deloc", "Uneori", "În fiecare zi"]},
        {"id": "camera", "tip": "info", "titlu": "Piața, în direct", "text": [
            "Dacă doriți, puteți vedea cum arată acum Piața Romană, pe site-ul Webcam România. Se deschide într-o filă nouă; apoi reveniți aici. Nu e obligatoriu."],
         "link": {"text": "Vedeți camera pe webcamromania.ro", "adresa": URL_CAMERA}, "buton": "Mai departe"},
        {"id": "cum_lucram", "tip": "info", "lung": True, "titlu": "Cum lucrăm", "text": [
            "Imaginați-vă că lucrați într-un centru care supraveghează semafoarele din Piața Romană. Încercați fără grijă: aici nu se dau note.",
            "În stânga primiți, pe rând, câte o sarcină. O faceți în partea din dreapta, apoi apăsați „Am terminat”. "
            "Partea din dreapta se acoperă și răspundeți la o întrebare, din ce ați văzut.",
            "Dacă în dreapta nu se vede tot, folosiți rotița mouse-ului sau două degete pe suprafața tactilă. Imaginea de la cameră e, aici, o fotografie fixă a pieței.",
            "Dacă nu reușiți, apăsați „Nu reușesc”. Nu e nicio problemă.",
            "Veți vedea, pe rând, două variante ale aceleiași aplicații."],
         "buton": "Am înțeles"},
        *_runda(0, ordine[0]),
        *_runda(1, ordine[1]),
        {"id": "preferinta", "tip": "alegere", "titlu": "Care variantă v-a fost mai ușoară?", "eticheta": "Mai ușoară", "optiuni": ["Prima", "A doua", "La fel"]},
        {"id": "vazut_inainte", "tip": "alegere", "titlu": "Ați mai văzut aplicația aceasta înainte de azi?", "eticheta": "Văzut înainte", "optiuni": ["Nu", "Da"]},
        {"id": "ajutor", "tip": "alegere", "titlu": "V-a ajutat cineva la sarcini?", "eticheta": "A ajutat cineva", "optiuni": AJUTOR},
        {"id": "final", "tip": "final"},
    ]


def date_pagina() -> dict:
    """Ce are nevoie pagina: pașii și situația simulată. Versiunea din pași se pune în browser, după ordinea din link."""
    return {"VERSIUNE": VERSIUNE_PAGINA, "FAZE": FAZE, "PLAN": PLAN, "GALBEN": GALBEN, "ROSU": ROSU, "VERDE_MIN": VERDE_MIN, "INTARZIERE_PIETONI": INTARZIERE_PIETONI, "DEGAJARE_PIETONI": DEGAJARE_PIETONI,
            "PAS_COMANDA": PAS_COMANDA, "VERDE_PE_DACIA": VERDE_PE_DACIA, "VERDE_PE_MAGHERU": VERDE_PE_MAGHERU, "AUTOMATE": AUTOMATE,
            "COZI": COZI, "INTRARI": INTRARI, "IESIRI": IESIRI, "ALEGE_CONDUCE": ALEGE_CONDUCE, "LUNGIME_TEXT": LUNGIME_TEXT,
            "URL_PROIECT": URL_PROIECT, "PE_TELEFON": PE_TELEFON, "PASI": pasi()}


# ---------------------------------------------------------------- pachetul static

CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self'; frame-src 'self'; "
       "connect-src 'none'; form-action 'none'; base-uri 'none'")
# Versiunea M1 ia fonturile de la Google, cea curentă din static/fonturi; în pagina publică vin amândouă din pachet.
RE_FONTURI = re.compile(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n<link href="https://fonts\.googleapis\.com/[^"]*" rel="stylesheet">\n'
                        r'|<link href="/static/fonturi/fonturi\.css" rel="stylesheet">\n')
# Panoul camerei, în sondaj: o fotografie fixă nu are flux, cadre pe secundă sau vehicule urmărite, iar debitele din test nu vin de la cameră.
TITLU_CAMERA = "Piața Romană, fotografie fixă"
TITLU_DEBITE = "Debite de trafic"
ALT_CAMERA = "Fotografie a Pieței Romane, cu persoanele și plăcuțele estompate"
NOTA_CAMERA = '<div class="sub" style="margin-top:10px">În acest sondaj, o fotografie fixă în locul camerei în direct.</div>\n'
STIL_CAMERA = "<style>.cam .stare,#sursa{display:none}</style>"
SUBSOL_CAMERA = ("Imaginea camerei: sursa Webcam România; drepturile aparțin operatorului camerei – analizată în memorie, "
                 "persoanele estompate, afișată doar local.")
SUBSOL_PUBLIC = ("Imaginea camerei: Webcam România – https://webcamromania.ro; drepturile aparțin operatorului camerei. "
                 "Fotografie publicată cu acordul scris al Webcam România, cu persoanele și plăcuțele estompate.")


def _inlocuieste(text: str, vechi: str, nou: str) -> str:
    if text.count(vechi) != 1:
        raise SystemExit(f"Dispeceratul s-a schimbat: „{vechi[:60]}” apare de {text.count(vechi)} ori; actualizați `ecran_static`.")
    return text.replace(vechi, nou)


def ecran_static(html: str, versiune: str) -> tuple[str, str]:
    """Dispeceratul, pentru pagina statică: (HTML-ul, scriptul lui). Se schimbă doar de unde vin datele, fonturile și imaginea, plus panoul
    camerei, la fel în ambele versiuni; butoanele, schema, graficul și tabelul rămân cele ale versiunii."""
    html = html.replace("\r\n", "\n")
    html, n = RE_FONTURI.subn('<link href="fonturi/fonturi.css" rel="stylesheet">\n', html)
    if n != 1:
        raise SystemExit("Dispeceratul s-a schimbat: legătura spre fonturi nu mai e aceeași; actualizați `ecran_static`.")
    html = _inlocuieste(html, '<meta charset="utf-8">\n', f'<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="{CSP}">\n{STIL_CAMERA}\n')
    for tipar, nou in ((r'<h2 id="t-cam">.*?</h2>', f'<h2 id="t-cam">{TITLU_CAMERA}</h2>'), (r'<h2 id="t-deb">.*?</h2>', f'<h2 id="t-deb">{TITLU_DEBITE}</h2>'),
                       (r'<img id="cadru" alt="[^"]*">', f'<img id="cadru" alt="{ALT_CAMERA}">')):
        html, n = re.subn(tipar, nou, html)
        if n != 1:
            raise SystemExit(f"Dispeceratul s-a schimbat: „{tipar}” apare de {n} ori; actualizați `ecran_static`.")
    html = _inlocuieste(html, '<div class="stare">', NOTA_CAMERA + '<div class="stare">')
    html = _inlocuieste(html, SUBSOL_CAMERA, SUBSOL_PUBLIC)
    m = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    if len(m) != 1:
        raise SystemExit(f"Dispeceratul s-a schimbat: are {len(m)} scripturi în pagină, nu unul; actualizați `ecran_static`.")
    script = _inlocuieste(m[0], '"/api/video"', json.dumps(IMAGINE_PUBLICA))
    html = html.replace(f"<script>{m[0]}</script>", f'<script src="punte.js"></script>\n<script src="{versiune}.js"></script>')
    if versiune == "m1":      # versiunea M1 rămâne neschimbată: planul de azi se numește cum îl numea ea pe cel de atunci
        script = _inlocuieste(script, "s.faze.map(", "s.faze.slice(0,5).map(")      # ca atunci: etapa scurtă nu are buton
        script = script.strip() + "\nMOD.plan_observat = MOD.plan_scurt;"
    return html, script.strip() + "\n"


def continut_pachet() -> dict[str, str]:
    """Fișierele din docs/sondare, ca text: numele → conținutul, cu sfârșit de rând LF."""
    citeste = lambda n: (STATIC / n).read_text(encoding="utf-8").replace("\r\n", "\n")
    fisiere = {"index.html": citeste("sondare.html"), "logica.js": citeste("sondare_logica.js"), "ecran.js": citeste("sondare_ecran.js"),
               "punte.js": citeste("sondare_punte.js"),
               "date.js": '"use strict";\nconst DATE_SONDARE = ' + json.dumps(date_pagina(), ensure_ascii=False, indent=0) + ";\n"}
    for v, cale in VERSIUNI.items():
        fisiere[f"{v}.html"], fisiere[f"{v}.js"] = ecran_static(cale.read_text(encoding="utf-8"), v)
    return fisiere


def pachet(destinatie: Path = PACHET) -> Path:
    destinatie.mkdir(parents=True, exist_ok=True)
    (destinatie.parent / ".nojekyll").touch()      # GitHub Pages servește fișierele așa cum sunt
    for nume, text in continut_pachet().items():
        with open(destinatie / nume, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    shutil.copytree(STATIC / "fonturi", destinatie / "fonturi", dirs_exist_ok=True)
    return destinatie


def versiuni_identice() -> bool:
    """Dacă persoana ar vedea același ecran în ambele runde; de unde vin fonturile nu contează."""
    a, b = (ecran_static(VERSIUNI[v].read_text(encoding="utf-8"), "x") for v in ("m1", "m2"))
    return a == b


def linkuri(dosar: Path = DOSAR, baza: str = ADRESA_PUBLICA) -> dict[str, list[str]]:
    """Câte două linkuri pe grup, unul pentru fiecare ordine a versiunilor. Formularul stă doar local, în formular.json."""
    if versiuni_identice():
        raise SystemExit("Versiunile m1 și m2 sunt identice: întâi reparațiile din static/index.html, apoi invitațiile.")
    f = json.loads((dosar / "formular.json").read_text(encoding="utf-8"))
    return {g: [f"{baza}?g={g}&o={o}&f={f['f']}&e={f['e']}" for o in (1, 2)] for g in GRUPURI}


# ---------------------------------------------------------------- răspunsurile primite

RE_ANTET = re.compile(r"Grup (\S+), ordine (\S+), ecran (\S+), (terminat|oprit la \S+)")
RE_SARCINA = re.compile(r"Sarcina (\d), [^:]*: (\d+) s, apăsări (\d+), comenzi (\d+)(?:, altă fereastră (\d+) s)?(, nu reușesc)?(, reușit|, nereușit)?(?:\. (.*))?$")
RE_ASTEPTAT = re.compile(r"^(.*) \(așteptat: (.*)\)$")      # doar pagina v1
RE_ADNOTARE = re.compile(r" \(așteptat: [^)]*\)$")
RE_VERSIUNE = re.compile(r"Sondare dispecerat Piața Romană, (v\d+)")      # căutat oriunde în rând: un prefix (WhatsApp, ghilimele) nu-l ascunde
RE_INCERCARE = re.compile(r"Încercarea: (\d+)\b.*")
RE_COD = re.compile(r"Cod de control: ([0-9A-Z]{4}-[0-9A-Z]{3}-[0-9A-Z]{2})\b.*")    # un „.” sau un emoji după cod nu-l ascunde
CONFIRMARI = "confirmari.json"

# Codul de control (pagina v2, § 8): același calcul ca `cod_control` din static/sondare_logica.js. Amprenta FNV-1a pe 32 de biți a
# textului adus la o formă care nu ține de transport, apoi biții răspunsurilor așteptate, amestecați cu amprenta. Nu e o semnătură.
ALFABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
TIPOGRAFIC = str.maketrans({chr(0x2026): "...", chr(0x201E): '"', chr(0x201C): '"', chr(0x201D): '"', chr(0x2018): "'", chr(0x2019): "'",
                            chr(0x2013): "-", chr(0x2014): "-"})
# spațiile, cu numerele lor, ca în sondare_logica.js: obișnuit, tab, neîntrerupt, cele tipografice, cel îngust, cel matematic,
# cel ideografic și BOM
SPATII = "".join(map(chr, [0x20, 0x09, 0xA0, *range(0x2000, 0x200B), 0x202F, 0x205F, 0x3000, 0xFEFF]))
RE_SPATII = re.compile("[" + re.escape(SPATII) + "]+")


def _normalizat(text: str) -> str:
    linii = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(l for l in (RE_SPATII.sub(" ", x.translate(TIPOGRAFIC)).strip(" ") for x in linii) if l)


def _fnv1a(text: str) -> int:
    h = 0x811C9DC5
    for b in text.encode("utf-8", "surrogatepass"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h


def _baza32(n: int, cifre: int) -> str:
    s = ""
    for _ in range(cifre):
        s, n = ALFABET[n % 32] + s, n // 32
    return s


def cod_control(text: str, biti: list[bool]) -> str:
    """`text`: tot ce e deasupra rândului codului; `biti`: pentru fiecare răspuns cu răspuns așteptat, în ordinea din text, dacă a fost cel așteptat.
    Masca biților e amprenta textului fără biți, care nu apare în cod."""
    forma = _normalizat(text)
    h = _fnv1a(forma + "\n" + "".join("1" if b else "0" for b in biti))
    n = sum(1 << i for i, b in enumerate(biti) if b)
    a = _baza32(h, 7)
    return f"{a[:4]}-{a[4:]}-{_baza32(n ^ (_fnv1a(forma) % 1024), 2)}"


def verifica_cod(text: str, cod: str, n_biti: int) -> list[bool] | None:
    """Biții răspunsurilor așteptate, dacă `text` (fără rândul codului) e chiar cel scris de pagină; None dacă a fost schimbat."""
    m = re.fullmatch(r"([0-9A-Z]{4})-([0-9A-Z]{3})-([0-9A-Z]{2})", cod)
    if not m or n_biti > 10 or any(c not in ALFABET for c in cod.replace("-", "")):
        return None
    h = functools.reduce(lambda s, c: s * 32 + ALFABET.index(c), m[1] + m[2], 0)
    n = functools.reduce(lambda s, c: s * 32 + ALFABET.index(c), m[3], 0) ^ (_fnv1a(_normalizat(text)) % 1024)
    if h >= 2 ** 32 or n >> n_biti:        # biți în plus: alt număr de răspunsuri decât în text
        return None
    biti = [bool(n >> i & 1) for i in range(n_biti)]
    return biti if cod_control(text, biti) == cod else None
INTREBARI = {"verde_r": "culoarea pe Magheru", "verde_vazut": "a văzut schimbarea", "automat_vazut": "a văzut cine conduce",
             "culori": "linia roșie", "real": "semaforul adevărat", "usor": "ușor sau foarte ușor"}
RASPUNS_SARCINA = {1: "conduce_r", 2: "coada_r"}
TEXT_LIBER = {"incurcat": "ce a încurcat"}
PROFIL = ("profil_calculator", "vazut_inainte", "ajutor")
COLOANE = ["cod", "grup", "ecran", "terminat", "pagina", "integru", "incercarea", "modificat", "numarat",
           "versiune", "runda", "masura", "durata_s", "reusit", "clicuri", "comenzi", "nu_reuseste", "raspuns"]
COLOANE_GRUP = ["grup", "masura", "versiune", "persoane", "reusite", "persoane_prima_runda", "reusite_prima_runda"]
COLOANE_DURATA = ["durata_mediana_s", "clicuri_mediana"]
# Sub această lățime, pagina pune ghidul deasupra dispeceratului: e alt ecran, deci răspunsurile se numără separat.
LATIME_TELEFON = 900


def _curat(rand: str) -> str:
    """Un rând, citit cum îl vede și codul de control: spațiile neobișnuite sau dublate devin unul singur, capetele se taie."""
    return RE_SPATII.sub(" ", rand).strip(" ")


def citeste_raspuns(text: str) -> dict | None:
    """Textul trimis de o persoană → {"grup", "ordine", "ecran", "terminat", "pasi", "pagina", "incercarea", "integru", "cod",
    "contradictii", "modificat", "in_afara", "cheie"}; None dacă nu e un răspuns al sondării.

    Se citește doar blocul scris de pagină, de la rândul versiunii până la primul rând cu codul; ce e în afară (un salut în același
    mesaj, ghilimelele unei celule copiate din foaie) se ignoră și se numără în `in_afara`. Rândurile goale nu contează, ca la cod.
    `integru`: True dacă codul se potrivește; False dacă nu se potrivește sau lipsește deși textul e de pe pagina v2 (`cod` = "lipsă");
    None la pagina v1, fără cod, unde o corectură se vede doar în `contradictii`: „X (așteptat: X)” sau un răspuns greșit fără adnotare."""
    toate = unicodedata.normalize("NFC", text.lstrip(chr(0xFEFF))).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i0 = next((i for i, x in enumerate(toate) if RE_VERSIUNE.search(x)), 0)
    if i0 < len(toate) and RE_VERSIUNE.search(toate[i0]):
        toate[i0] = toate[i0][RE_VERSIUNE.search(toate[i0]).start():]
    i1 = next((i for i in range(i0, len(toate)) if RE_COD.fullmatch(_curat(toate[i]))), None)
    bloc = toate[i0:len(toate) if i1 is None else i1]
    in_afara = sum(1 for x in toate[:i0] + ([] if i1 is None else toate[i1 + 1:]) if _curat(x))
    linii = [_curat(x) for x in bloc]
    antet = next((RE_ANTET.fullmatch(x) for x in linii if RE_ANTET.fullmatch(x)), None)
    if antet is None:
        return None
    ordine = {"1": ("m1", "m2"), "2": ("m2", "m1")}.get(antet[2])
    if ordine is None:
        return None
    pasi_p = pasi(ordine)
    dupa_eticheta = {(p.get("runda"), p["eticheta"].split(",")[0] if p.get("sarcina") else p["eticheta"]): p for p in pasi_p if p.get("eticheta")}
    versiune = next((RE_VERSIUNE.search(x)[1] for x in linii if RE_VERSIUNE.search(x)), None)
    # formatul, după conținut: „(așteptat: …)” scrie doar logica v1, iar antetul vine din date.js, care poate fi din alt cache
    v2 = i1 is not None or (versiune != "v1" and not any(RE_ADNOTARE.search(x) for x in linii))
    rez = {"grup": antet[1], "ordine": ordine, "ecran": antet[3], "terminat": antet[4] == "terminat", "pasi": [], "pagina": versiune,
           "incercarea": 1, "integru": None, "cod": None, "contradictii": [], "in_afara": in_afara,
           "cheie": "\n".join(RE_ADNOTARE.sub("", l) for l in _normalizat("\n".join(bloc)).split("\n")
                              if not l.startswith(("Sondare dispecerat", "Ce a încurcat:")))}
    runda = None
    for l in linii:
        if RE_INCERCARE.fullmatch(l):
            rez["incercarea"] = int(RE_INCERCARE.fullmatch(l)[1])
            continue
        if l == "Prima variantă":
            runda = 0
        elif l == "A doua variantă":
            runda = 1
        m = RE_SARCINA.match(l)
        if m:
            p = dupa_eticheta.get((runda, f"Sarcina {m[1]}"))
            if p:
                r = {"id": p["id"], "tip_pas": "sarcina", "sarcina": int(m[1]), "versiune": p["versiune"], "runda": p["runda"], "durata_s": int(m[2]),
                     "clicuri": int(m[3]), "comenzi": int(m[4]), "nu_reuseste": bool(m[6]), "traseu": m[8] or ""}
                if m[7]:
                    r["reusit"] = m[7] == ", reușit"
                rez["pasi"].append(r)
            continue
        if ": " not in l:
            continue
        eticheta, valoare = l.split(": ", 1)
        p = dupa_eticheta.get((runda, eticheta)) or dupa_eticheta.get((None, eticheta))
        if not p:
            continue
        r = {"id": p["id"], "tip_pas": p["tip"], "valoare": valoare}
        if "corect" in p or "corect_din_banc" in p:
            a = RE_ASTEPTAT.match(valoare)
            r["valoare"] = a[1] if a else valoare
            if "corect" in p:                         # răspunsul așteptat e fix, se știe din pași
                r["corect"] = r["valoare"] == p["corect"]
                if not v2 and (a is None) != r["corect"]:      # v1 scrie adnotarea exact când răspunsul diferă
                    rez["contradictii"].append(p["id"])
            else:                                     # la v1, din adnotare; la v2, din cod, mai jos
                r["corect"] = a is None
                if a and a[1] in a[2].split(" sau "):          # pagina nu scrie așa ceva: răspunsul a fost corectat de mână
                    rez["contradictii"].append(p["id"])
        if "runda" in p:
            r["versiune"], r["runda"] = p["versiune"], p["runda"]
        rez["pasi"].append(r)
    if v2:                  # pagina v2: răspunsurile așteptate vin din cod, nu din text
        cu_asteptat = [r for r in rez["pasi"] if "corect" in r]
        rez["cod"] = "lipsă" if i1 is None else RE_COD.fullmatch(_curat(toate[i1]))[1]
        libere = tuple(p["eticheta"] + ":" for p in pasi_p if p["tip"] == "text")      # textul liber nu intră în amprentă
        biti = None if i1 is None else verifica_cod("\n".join(x for x in bloc if not _curat(x).startswith(libere)), rez["cod"], len(cu_asteptat))
        rez["integru"] = biti is not None
        for r, b in zip(cu_asteptat, biti or [None] * len(cu_asteptat)):
            r["corect"] = b
    rez["modificat"] = rez["integru"] is False or bool(rez["contradictii"])
    return rez


def _primite(dosar: Path) -> tuple[list[tuple[str, dict]], list[tuple[str, str]]]:
    """(textele care se citesc, perechile (cod lăsat, cod păstrat) ale aceleiași treceri primite de două ori)."""
    cale = dosar / "primite"
    alese: dict[str, tuple[int, str, dict]] = {}
    contopite = []
    for f in sorted(cale.glob("R*.txt"), key=lambda p: int(p.stem[1:])) if cale.exists() else []:
        r = citeste_raspuns(f.read_text(encoding="utf-8-sig").strip())
        if r is None or r["grup"] not in GRUPURI:
            continue
        rang = {True: 2, None: 1, False: 0}[r["integru"]]
        vechi = alese.get(r["cheie"])
        if vechi is None:
            alese[r["cheie"]] = (rang, f.stem, r)
        elif rang > vechi[0]:          # se păstrează copia cea mai bună, ca o copie stricată sosită prima să n-o ascundă pe cea bună
            contopite.append((vechi[1], f.stem))
            alese[r["cheie"]] = (rang, f.stem, r)
        else:
            contopite.append((f.stem, vechi[1]))
    return sorted(((c, r) for _, c, r in alese.values()), key=lambda x: int(x[0][1:])), contopite


def raspunsuri_primite(dosar: Path = DOSAR) -> list[tuple[str, dict]]:
    """Textele din primite/, în ordinea sosirii: fără probe, fără ce nu e un răspuns și cu aceeași trecere o singură dată (aceeași
    `cheie`: textul paginii adus la formă, fără antetul versiunii, adnotări, cod și textul liber), din copia cea mai bună."""
    return _primite(dosar)[0]


def pe_telefon(ecran: str) -> bool:
    """„390x844” → True: lățimea din antetul răspunsului e sub LATIME_TELEFON."""
    try:
        return 0 < int(str(ecran).lower().split("x")[0]) < LATIME_TELEFON     # 0 = lățime necunoscută
    except ValueError:
        return False


def grup_raportat(r: dict) -> str:
    """Grupul din totaluri: răspunsurile de pe telefon formează un grup al lor, de exemplu „a_telefon”."""
    return r["grup"] + ("_telefon" if pe_telefon(r.get("ecran", "")) else "")


def confirmari(dosar: Path = DOSAR) -> dict[str, str]:
    """Trecerile a doua dintr-o filă despre care autorul a confirmat că sunt ale altei persoane: {"R5": "altă persoană"}."""
    cale = dosar / CONFIRMARI
    return json.loads(cale.read_text(encoding="utf-8")) if cale.exists() else {}


def se_numara(cod: str, rasp: dict, confirmate: dict[str, str]) -> bool:
    """Un text schimbat după ce l-a scris pagina nu se numără; nici o a doua trecere în aceeași filă, dacă nu e confirmată."""
    return not rasp["modificat"] and (rasp["incercarea"] == 1 or cod in confirmate)


def rezumat(dosar: Path = DOSAR) -> list[dict]:
    """Un rând pe participant, versiune și măsură; plus părerile și profilul (doar local)."""
    randuri = []
    confirmate = confirmari(dosar)
    for cod, rasp in raspunsuri_primite(dosar):
        pe_id = {o["id"]: o for o in rasp["pasi"]}
        baza0 = {"cod": cod, "grup": rasp["grup"], "ecran": rasp["ecran"], "terminat": rasp["terminat"], "pagina": rasp["pagina"],
                 "integru": rasp["integru"], "incercarea": rasp["incercarea"], "modificat": rasp["modificat"],
                 "numarat": se_numara(cod, rasp, confirmate)}
        for runda in (0, 1):
            r = f"r{runda + 1}"
            baza = {**baza0, "runda": runda + 1}
            for o in rasp["pasi"]:
                if o.get("runda") != runda:
                    continue
                id_scurt = o["id"][3:]
                if o["tip_pas"] == "sarcina":
                    sarc = o["sarcina"]
                    rasp_s = pe_id.get(f"{r}_{RASPUNS_SARCINA[sarc]}") if sarc in RASPUNS_SARCINA else None
                    reusit = o.get("reusit") if sarc not in RASPUNS_SARCINA else bool(rasp_s and rasp_s.get("corect") and not o.get("nu_reuseste"))
                    randuri.append({**baza, "versiune": o["versiune"], "masura": f"sarcina {sarc}: {NUME_SARCINA[sarc]}", "durata_s": o["durata_s"],
                                    "reusit": reusit, "clicuri": o["clicuri"], "comenzi": o["comenzi"],
                                    "nu_reuseste": o["nu_reuseste"], "raspuns": rasp_s.get("valoare") if rasp_s else None})
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
                randuri.append({**baza0, "masura": k, "raspuns": pe_id[k]["valoare"]})
        if "preferinta" in pe_id:      # „Prima” / „A doua” înseamnă altă versiune, după ordinea participantului
            v = pe_id["preferinta"].get("valoare")
            randuri.append({**baza0, "masura": "preferinta", "raspuns": {"Prima": rasp["ordine"][0], "A doua": rasp["ordine"][1]}.get(v, "la fel")})
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
    """Totaluri pe grup, versiune și măsură, doar pentru cei care au terminat: fără coduri, fără text liber, fără profil.

    Prima rundă se dă separat: e singura la prima vedere, deci singura fără efectul exercițiului. Duratele, doar `local` sau la colegi:
    între persoane de vârste foarte diferite nu se pot compara, iar colegii au vârste apropiate. Răspunsurile de pe telefon
    au grupul lor (`grup_raportat`), fiindcă acolo pagina arată altfel. Ce nu se numără (`se_numara`) rămâne afară."""
    terminati = [{**r, "grup": grup_raportat(r)} for r in randuri if r.get("terminat") and r.get("numarat", True)]
    grupe: dict[tuple, list[dict]] = {}
    for r in terminati:
        if r.get("versiune") and r["masura"] not in TEXT_LIBER.values():
            grupe.setdefault((r["grup"], r["masura"], r["versiune"]), []).append(r)
    rez = []
    for (grup, masura, versiune), lista in sorted(grupe.items()):
        prima = [r for r in lista if r.get("runda") == 1]
        rand = {"grup": grup, "masura": masura, "versiune": versiune, "persoane": len(lista), "reusite": sum(bool(r.get("reusit")) for r in lista),
                "persoane_prima_runda": len(prima), "reusite_prima_runda": sum(bool(r.get("reusit")) for r in prima)}
        if local or grup.split("_")[0] == "c":       # colegii, și cei de pe telefon
            durate = [r["durata_s"] for r in lista if r.get("durata_s") is not None]
            clicuri = [r["clicuri"] for r in lista if r.get("clicuri") is not None]
            rand["durata_mediana_s"] = round(st.median(durate), 1) if durate else ""
            rand["clicuri_mediana"] = st.median(clicuri) if clicuri else ""
        rez.append(rand)
    for grup in sorted({r["grup"] for r in terminati}):
        din_grup = [r for r in terminati if r["grup"] == grup]
        pref = [r["raspuns"] for r in din_grup if r["masura"] == "preferinta"]
        for v in ("m1", "m2", "la fel"):
            if pref:
                rez.append({"grup": grup, "masura": "varianta preferată", "versiune": v, "persoane": pref.count(v)})
        ajutor = [r["raspuns"] for r in din_grup if r["masura"] == "ajutor"]
        if ajutor:
            rez.append({"grup": grup, "masura": "a avut nevoie de ajutor la sarcini", "versiune": "", "persoane": sum(x == AJUTOR[2] for x in ajutor)})
    return rez


def publica(dosar: Path = DOSAR, destinatie: Path = PUBLICAT, minim: int = 3, forteaza: bool = False) -> Path:
    """Totalurile publice, pe grupuri; un grup sub `minim` persoane care au terminat rămâne afară, fiindcă un rând ar fi chiar răspunsul cuiva.

    Tot de aceea, un rând „x din N” cu N sub `minim` lipsește, iar prima rundă rămâne goală când ea sau restul au 1–2 persoane. Se publică
    o singură dată: o publicare nouă, care diferă prin câteva persoane, le-ar arăta răspunsurile (`forteaza` doar pentru o greșeală)."""
    if destinatie.exists() and not forteaza:
        raise SystemExit(f"{destinatie} există deja: totalurile se publică o singură dată, după închidere și după confirmări.")
    _, randuri = scrie_rezumat(dosar)
    coduri: dict[str, set] = {}
    for r in randuri:
        if r.get("terminat") and r.get("numarat", True):
            coduri.setdefault(grup_raportat(r), set()).add(r["cod"])
    destule = {g for g, c in coduri.items() if len(c) >= minim}
    if not destule:
        raise SystemExit(f"Niciun grup nu are cel puțin {minim} persoane care au terminat.")
    destinatie.parent.mkdir(parents=True, exist_ok=True)
    publice = []
    for r in pe_grup(randuri):
        if r["grup"] not in destule:
            continue
        if "reusite" in r:                       # rândurile „x din N”
            if r["persoane"] < minim:
                continue
            pp = r["persoane_prima_runda"]
            if 0 < pp < minim or 0 < r["persoane"] - pp < minim:
                r["reusite_prima_runda"] = ""     # altfel prima rundă, sau restul, ar fi răspunsul a 1–2 persoane
        publice.append(r)
    coloane = COLOANE_GRUP + (COLOANE_DURATA if any(c in r for r in publice for c in COLOANE_DURATA) else [])
    with open(destinatie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, coloane)
        w.writeheader()
        w.writerows(publice)
    return destinatie


def probleme(dosar: Path = DOSAR) -> list[str]:
    """Ce nu se numără și de ce, plus dublurile posibile (același grup, aceeași ordine, același ecran); doar local, pentru autor."""
    confirmate, rez, vazute = confirmari(dosar), [], {}
    primite, contopite = _primite(dosar)
    for lasat, pastrat in contopite:
        rez.append(f"{lasat}: aceeași trecere ca {pastrat}; se numără o singură dată, din {pastrat}")
    for cod, r in primite:
        if r["cod"] == "lipsă":
            rez.append(f"{cod}: fără cod de control, deși textul e de pe pagina nouă (rândul codului lipsește); nu se numără")
        elif r["integru"] is False:
            rez.append(f"{cod}: codul de control nu se potrivește cu textul; comparați întâi fișierul cu foaia formularului sau cu mesajul "
                       "primit; până atunci nu se numără")
        if r["contradictii"]:
            rez.append(f"{cod}: corectat de mână la {', '.join(r['contradictii'])} (pagina v1); nu se numără")
        if r["in_afara"]:
            rez.append(f"{cod}: {r['in_afara']} rânduri în afara textului paginii (de exemplu un salut), ignorate")
        if r["incercarea"] > 1:
            rez.append(f"{cod}: încercarea {r['incercarea']} în aceeași filă; " + (f"se numără, confirmat: {confirmate[cod]}" if cod in confirmate
                       else f"nu se numără până nu confirmă autorul, în {CONFIRMARI}, că e altă persoană"))
        cheie = (r["grup"], r["ordine"], r["ecran"])
        if cheie in vazute:
            rez.append(f"{cod}: același grup, aceeași ordine și același ecran ca {vazute[cheie]}; poate fi aceeași persoană, de verificat")
        vazute.setdefault(cheie, cod)
    return rez


def serveste_local(port: int = 8060, deschide: bool = True) -> None:
    """Pagina, pe acest calculator: la fel ca pe GitHub Pages, doar pentru probe."""
    gestiune = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    url = f"http://127.0.0.1:{port}/sondare/"
    print(f"Sondare: {url}")
    if deschide:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    http.server.ThreadingHTTPServer(("127.0.0.1", port), gestiune).serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(description="Sondarea dispeceratului cu oameni")
    ap.add_argument("--pachet", action="store_true", help="reface docs/sondare din sursele din static/")
    ap.add_argument("--local", action="store_true", help="servește pagina pe acest calculator, pentru probe")
    ap.add_argument("--port", type=int, default=8060)
    ap.add_argument("--fara-browser", action="store_true", help="nu deschide singur pagina")
    ap.add_argument("--linkuri", action="store_true", help="afișează linkurile pentru invitați")
    ap.add_argument("--dosar", default=None, help="unde stau răspunsurile primite (implicit outputs/sondare)")
    ap.add_argument("--rezumat", action="store_true", help="scrie rezumat.csv și afișează rezultatele pe grupuri și versiuni")
    ap.add_argument("--publica", action="store_true", help="scrie docs/rezultate/sondare_m2.csv, doar totaluri, o singură dată")
    ap.add_argument("--forteaza", action="store_true", help="cu --publica: rescrie totalurile publice (doar pentru o greșeală)")
    a = ap.parse_args()
    for flux in (sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8", errors="replace")
    dosar = Path(a.dosar) if a.dosar else DOSAR
    if a.pachet:
        print("pachet:", pachet())
    if a.linkuri:
        for g, ll in linkuri(dosar).items():
            print(f"{GRUPURI[g]}:")
            for l in ll:
                print(" ", l)
    if a.rezumat or a.publica:
        cale, randuri = scrie_rezumat(dosar)
        print(f"{cale}: {len(randuri)} rânduri")
        for r in pe_grup(randuri, local=True):
            print(r)
        for p in probleme(dosar):
            print("de știut:", p)
        if a.publica:
            print("publicat:", publica(dosar, forteaza=a.forteaza))
    if a.local:
        serveste_local(a.port, not a.fara_browser)
    elif not (a.pachet or a.linkuri or a.rezumat or a.publica):
        ap.print_help()


if __name__ == "__main__":
    main()
