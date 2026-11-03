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
            python -m romana.dashboard.sondare --rezumat   → outputs/sondare/rezumat.csv și tabelul pe grupuri și versiuni
            python -m romana.dashboard.sondare --publica   → docs/rezultate/sondare_m2.csv (doar totaluri)
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
import threading
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
VERSIUNE_PAGINA = "v1"
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
RE_ASTEPTAT = re.compile(r"^(.*) \(așteptat: (.*)\)$")
INTREBARI = {"verde_r": "culoarea pe Magheru", "verde_vazut": "a văzut schimbarea", "automat_vazut": "a văzut cine conduce",
             "culori": "linia roșie", "real": "semaforul adevărat", "usor": "ușor sau foarte ușor"}
RASPUNS_SARCINA = {1: "conduce_r", 2: "coada_r"}
TEXT_LIBER = {"incurcat": "ce a încurcat"}
PROFIL = ("profil_calculator", "vazut_inainte", "ajutor")
COLOANE = ["cod", "grup", "ecran", "terminat", "versiune", "runda", "masura", "durata_s", "reusit", "clicuri", "comenzi", "nu_reuseste", "raspuns"]
COLOANE_GRUP = ["grup", "masura", "versiune", "persoane", "reusite", "persoane_prima_runda", "reusite_prima_runda"]
COLOANE_DURATA = ["durata_mediana_s", "clicuri_mediana"]
# Sub această lățime, pagina pune ghidul deasupra dispeceratului: e alt ecran, deci răspunsurile se numără separat.
LATIME_TELEFON = 900


def citeste_raspuns(text: str) -> dict | None:
    """Textul trimis de o persoană → {"grup", "ordine", "ecran", "terminat", "pasi"}; None dacă nu e un răspuns al sondării."""
    linii = [x.strip() for x in text.replace("\r\n", "\n").split("\n")]
    antet = next((RE_ANTET.fullmatch(x) for x in linii if RE_ANTET.fullmatch(x)), None)
    if antet is None:
        return None
    ordine = {"1": ("m1", "m2"), "2": ("m2", "m1")}.get(antet[2])
    if ordine is None:
        return None
    pasi_p = pasi(ordine)
    dupa_eticheta = {(p.get("runda"), p["eticheta"].split(",")[0] if p.get("sarcina") else p["eticheta"]): p for p in pasi_p if p.get("eticheta")}
    rez = {"grup": antet[1], "ordine": ordine, "ecran": antet[3], "terminat": antet[4] == "terminat", "pasi": []}
    runda = None
    for l in linii:
        if l == "Prima variantă":
            runda = 0
        elif l == "A doua variantă":
            runda = 1
        elif not l:             # un rând gol apare doar la schimbarea rundei
            runda = None
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
            r["valoare"], r["corect"] = (a[1], False) if a else (valoare, True)
        if "runda" in p:
            r["versiune"], r["runda"] = p["versiune"], p["runda"]
        rez["pasi"].append(r)
    return rez


def raspunsuri_primite(dosar: Path = DOSAR) -> list[tuple[str, dict]]:
    """Textele din primite/, în ordinea sosirii: fără cele identice, fără probe și fără ce nu e un răspuns."""
    cale = dosar / "primite"
    rez, vazute = [], set()
    for f in sorted(cale.glob("R*.txt"), key=lambda p: int(p.stem[1:])) if cale.exists() else []:
        text = f.read_text(encoding="utf-8").strip()
        r = citeste_raspuns(text)
        if r is None or r["grup"] not in GRUPURI or text in vazute:
            continue
        vazute.add(text)
        rez.append((f.stem, r))
    return rez


def pe_telefon(ecran: str) -> bool:
    """„390x844” → True: lățimea din antetul răspunsului e sub LATIME_TELEFON."""
    try:
        return 0 < int(str(ecran).lower().split("x")[0]) < LATIME_TELEFON     # 0 = lățime necunoscută
    except ValueError:
        return False


def grup_raportat(r: dict) -> str:
    """Grupul din totaluri: răspunsurile de pe telefon formează un grup al lor, de exemplu „a_telefon”."""
    return r["grup"] + ("_telefon" if pe_telefon(r.get("ecran", "")) else "")


def rezumat(dosar: Path = DOSAR) -> list[dict]:
    """Un rând pe participant, versiune și măsură; plus părerile și profilul (doar local)."""
    randuri = []
    for cod, rasp in raspunsuri_primite(dosar):
        pe_id = {o["id"]: o for o in rasp["pasi"]}
        baza0 = {"cod": cod, "grup": rasp["grup"], "ecran": rasp["ecran"], "terminat": rasp["terminat"]}
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
    au grupul lor (`grup_raportat`), fiindcă acolo pagina arată altfel."""
    terminati = [{**r, "grup": grup_raportat(r)} for r in randuri if r.get("terminat")]
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


def publica(dosar: Path = DOSAR, destinatie: Path = PUBLICAT, minim: int = 3) -> Path:
    """Totalurile publice, pe grupuri; un grup sub `minim` persoane care au terminat rămâne afară, fiindcă un rând ar fi chiar răspunsul cuiva."""
    _, randuri = scrie_rezumat(dosar)
    coduri: dict[str, set] = {}
    for r in randuri:
        if r.get("terminat"):
            coduri.setdefault(grup_raportat(r), set()).add(r["cod"])
    destule = {g for g, c in coduri.items() if len(c) >= minim}
    if not destule:
        raise SystemExit(f"Niciun grup nu are cel puțin {minim} persoane care au terminat.")
    destinatie.parent.mkdir(parents=True, exist_ok=True)
    publice = [r for r in pe_grup(randuri) if r["grup"] in destule]
    coloane = COLOANE_GRUP + (COLOANE_DURATA if any(c in r for r in publice for c in COLOANE_DURATA) else [])
    with open(destinatie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, coloane)
        w.writeheader()
        w.writerows(publice)
    return destinatie


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
    ap.add_argument("--publica", action="store_true", help="scrie docs/rezultate/sondare_m2.csv, doar totaluri")
    a = ap.parse_args()
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
        if a.publica:
            print("publicat:", publica(dosar))
    if a.local:
        serveste_local(a.port, not a.fara_browser)
    elif not (a.pachet or a.linkuri or a.rezumat or a.publica):
        ap.print_help()


if __name__ == "__main__":
    main()
