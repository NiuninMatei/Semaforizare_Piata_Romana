"""Starea senzorului (§ 4.6), pentru panoul „Starea senzorului” din dispecerat (GET /api/senzor): cât de proaspătă e fiecare
verigă a colectării de la cameră și rezumatul ultimei fișe a senzorului (`romana.vision.fisa_senzor`).

Verigile sunt mereu toate cinci, în ordinea de mai jos. Fiecare are ultima dovadă că lucrează (`ultima_dovada`, ca marcaj de
timp, și vârsta ei în secunde, `varsta_s`), pragurile după care devine „de urmărit” sau o problemă și o stare: ok, atent,
problema sau necunoscut. Necunoscut: datele verigii lipsesc sau nu se pot citi, ori calculul a dat o eroare neprevăzută, al
cărei tip e în `eroare`. Două lipsuri spun însă ceva și sunt o problemă: starea live a camerei și un lanț de noapte.
  * camera     – starea live (outputs/live/state.json), rescrisă de colectare în fiecare secundă în care prelucrează cadre;
                 dovada e data fișierului, ca în /api/state. Pragurile paginii: veche de la 15 s, de urmărit până la 10 min,
                 apoi o problemă; proaspătă, dar fără fluxul camerei sau cu sub 3,5 cadre/s, de urmărit. Fără fișier,
                 colectarea nu rulează: o problemă;
  * colectarea – ultimul sfert de oră încheiat din data/counts/numaratori_<zi>.csv, de azi sau de ieri (după miezul nopții,
                 până se încheie primul sfert al zilei): unul la 15 min, plus 2 min până se scrie; după o oră fără niciunul,
                 o problemă. Dintr-un fișier scris în ultimele 2 s se ia sfertul dinaintea ultimului: acela poate fi încă pe
                 jumătate. Vehiculele intrate și pietonii, doar ca totaluri ale sfertului;
  * veghea     – rândul de minut al vegherii (outputs/logs/veghe_*.csv): de la 3 min fără rând, de urmărit, de la 10 min, o
                 problemă; rata cadrelor, pauzele și reconectările, cu pragurile vegherii; ultima ei alertă din ultimele 24 h
                 (doar ora și semnele: instantaneul ei are și lista proceselor). La prima alertă veghea se oprește: o alertă
                 scrisă după ultimul rând sau cu cel mult 2 min înaintea lui (`alerta.dupa_ultimul_rand`) e de urmărit,
                 iar cu veghea tăcută de 3 min, o problemă;
  * paznicul   – ultima notă din outputs/logs/paznic_<zi>.log. Notele care spun că totul merge (NOTE_BUNE): „în regulă”,
                 o dată pe oră, și „repornirea ține de …”, după o repornire care a ținut. O notă bună mai veche de 1 h 2 min
                 sau altă notă e de urmărit; fără nicio notă de 2 h, o problemă;
  * noaptea    – prelucrarea de noapte, în două lanțuri, fiecare pentru ziua de ieri: măsura veche (lant_zilnic, la 00:15)
                 și măsura nouă (lant_cor, la 03:30). Un lanț fără stare pentru ziua lui e neînceput în primele 10 min de la
                 ora lui, apoi lipsește: o problemă, ca un lanț eșuat. Două așteptări țin însă de program (`asteapta`):
                 lanțul măsurii vechi, pornit (își scrie proces.pid), așteaptă fluxul camerei cel mult 30 min înaintea
                 primei stări („fluxul”: în curs; un proces.pid cu data în viitor nu e o pornire), iar lanțul măsurii noi
                 așteaptă, fără să scrie nimic, lanțul măsurii vechi al aceleiași zile („lant”: neînceput), cât timp starea
                 acestuia lipsește, nu se poate citi sau e „in_curs”, exact ca în lant_cor.lant_vechi_incheiat, dar cel mult
                 5 h. Încheierea lui o vede abia la următoarea verificare: după un lanț vechi încheiat după 03:30, măsura
                 nouă mai are 10 min de la încheiere ca să pornească („pornire”: tot neînceput). Un lanț încheiat cu
                 „gata”, dar cu un cod acceptat diferit de 0 (măsura veche acceptă un jurnal cu membri stricați), e
                 încheiat, cu atenționarea lui (`atentie`). De urmărit: un lanț neînceput, necitibil, cu atenționare sau
                 în curs de peste 2 h (`prea_lunga`). Fără niciun dosar al prelucrării de noapte (`fara_dosare`, de pildă
                 pe alt calculator), veriga rămâne necunoscută.

Doar citire: fiecare fișier se deschide o clipă (la jurnale, doar coada lui) și se închide pe loc; nu se blochează și nu se
scrie nimic. Pe Windows, fișierele colectării (starea live, numărătorile, jurnalele vegherii și ale paznicului, alertele,
fișele) se deschid cu partajarea completă (`_deschide`): renumărarea de noapte poate șterge CSV-ul de ieri chiar în clipa în
care panoul îl citește. Starea unui lanț de noapte o citește întâi `fisa_senzor.stare_lant`, neschimbată, cu o deschidere
obișnuită; doar citirile ei de aici (atenționarea, verificarea lanțului vechi) trec prin `_deschide`. Înlocuirea unui fișier
ținut deschis (os.replace) tot nu merge pe Windows, oricum ar fi deschis: colectarea sare atunci o rescriere a stării live,
iar lanțul măsurii vechi își reîncearcă scrierea stării (de 5 ori, la 0,2 s). Jurnalele cresc prin adăugare, pe care o citire
nu o oprește. În răspuns nu intră căi locale: textele luate din jurnale se curăță (o cale, cu dosarul utilizatorului cu tot,
devine „…”), iar o eroare se dă doar prin tipul ei.

Pragurile vegherii, ale paznicului și ale lanțurilor de noapte, ca și verificarea lanțului vechi din lant_cor, sunt copiate
aici, nu importate: serverul încarcă doar biblioteca standard, `romana.common` și `fisa_senzor`, iar `veghe`, `paznic` și
`lant_cor` aduc după ele numpy, psutil, pandas și numărătoarea, prea grele pentru un server care doar citește
(tests/test_senzor.py verifică să rămână la fel).
"""
from __future__ import annotations

import copy
import csv
import json
import math
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from romana.common import COUNTS_DIR, OUTPUT_DIR, ROOT
from romana.vision import fisa_senzor as fs

try:                                     # Windows: deschiderea care nu-i încurcă pe cei care scriu (vezi _deschide)
    import _winapi
    import msvcrt
except ImportError:                      # alt sistem: acolo un cititor nu oprește oricum ștergerea unui fișier
    _winapi = msvcrt = None

LIVE = OUTPUT_DIR / "live"
LOGURI = fs.LOG_DIR
NUMARATORI = COUNTS_DIR
LANTURI = fs.LANTURI                     # numele → (dosarul, ora pornirii): lant la 00:15, lant_cor la 03:30
FISE = (ROOT / "docs" / "rezultate", OUTPUT_DIR / "fisa_senzor")    # întâi dosarul fișelor publicate
STARI = ("ok", "atent", "problema", "necunoscut")
MEMORARE_S = 5           # s; cât refolosește serverul un răspuns. Pagina îl cere la 10 s (SENZOR_MS din index.html): cu
                         # jumătate, fiecare cerere primește un calcul nou, oricât s-ar abate ceasul paginii, iar oricâte
                         # pagini deschise tot nu fac mai mult de un calcul la 5 s

# camera: pragurile paginii (index.html: `c._varsta_s<15`, CAMERA_ALERTA_S, CAMERA_ROSU_S)
CAMERA_PROASPATA_S = 15
CAMERA_ALERTA_S = 180
CAMERA_ROSU_S = 600
INCERCARI_STARE = 3      # citiri ale stării live, la PAUZA_STARE_S una de alta: fișierul e înlocuit în fiecare secundă
PAUZA_STARE_S = 0.05
# colectarea
INTERVAL_S = 900         # s; numărătorile se scriu pe sferturi de oră, la încheierea fiecăruia
COLECTARE_PRAG_S = INTERVAL_S + 120      # plus 2 min până se scrie sfertul încheiat
COLECTARE_ROSU_S = 3600
SFERT_IN_SCRIERE_S = 2   # s; într-un fișier scris de atât de curând, ultimul sfert poate fi încă pe jumătate (_ultimul_sfert)
# veghea: copii ale pragurilor din romana.vision.veghe
PRAG_FPS = 3.5           # cadre/s; veghe.PRAG_FPS (și pentru cameră)
STARE_VECHE = 180        # s; veghe.STARE_VECHE, la fel ca fisa_senzor.TACERE_VEGHE: veghea scrie un rând pe minut
PRAG_PAUZE = 10          # pauze în 5 min; veghe.PRAG_PAUZE
MAX_EPISOADE = 4         # episoade de reconectare în 30 min; veghe.MAX_EPISOADE
VEGHE_ROSU_S = 600
ULTIMA_ORA_S = 3600      # s; rândurile și pauzele vegherii se numără pe ultima oră
ALERTA_S = 86400         # s; o alertă mai veche nu se mai arată
MARJA_ALERTA_S = 120     # s înaintea ultimului rând de la care o alertă ține de oprirea vegherii
# paznicul: copie a pragului din romana.vision.paznic
SEMN_DE_VIATA = 3600     # s; paznic.SEMN_DE_VIATA: cât de des notează „în regulă”
PAZNIC_PRAG_S = SEMN_DE_VIATA + 120
PAZNIC_ROSU_S = 7200
# notele bune ale paznicului, din paznic.Paznic._sanatos: „în regulă: …”, o dată la SEMN_DE_VIATA, și „repornirea ține de N
# s: …”, după o repornire care a ținut 10 min; următorul „în regulă” vine abia la ora lui, deci până la o oră mai târziu
NOTE_BUNE = ("în regulă", "repornirea ține de")
# noaptea
NOAPTE_S = 86400         # s; câte o rulare pe noapte, a fiecărui lanț
MARJA_LANT_S = 600       # s după ora pornirii în care un lanț fără stare pentru ziua lui e „neînceput”, nu „lipsă”; măsura
                         # nouă verifică lanțul vechi la 60 s (lant_cor.PAS_ASTEPTARE_S), deci după încheierea lui are tot atât
FISIER_BLOCARE = "proces.pid"            # lant_zilnic.FISIER_BLOCARE: lanțul vechi îl scrie la pornire, îl șterge la sfârșit
ASTEPTARE_FLUX_S = 1800  # s; lant_zilnic.ASTEPTARE_FLUX_S: cât așteaptă lanțul vechi, înaintea primei stări, un flux oprit
MARJA_CEAS_S = 60        # s; un proces.pid scris „în viitor” cu mai mult de atât (un ceas dat înapoi) nu e o pornire
ASTEPTARE_LANT_VECHI_S = 5 * 3600        # s; lant_cor.ASTEPTARE_LANT_VECHI_S: cât așteaptă măsura nouă lanțul vechi
ASTEAPTA_DUPA = {"lant_cor": "lant"}     # lant_cor.bucla pornește abia după lanțul vechi al aceleiași zile
LANT_LUNG_S = 7200       # s; fără simulări, o noapte ține ≈5–10 min: o rulare în curs de peste 2 h e de urmărit
PAUZA_LANT_S = 0.1       # s; lant_cor își rescrie starea pe loc: o citire chiar atunci găsește fișierul gol
ATENTIE_IMPLICITA = "un pas a avut o atenționare"

COADA_NUMARATORI = 16 * 1024     # octeți citiți de la capătul fișierelor; când nu ajung, de 4 ori mai mult
COADA_VEGHE = 64 * 1024
COADA_PAZNIC = 8 * 1024
COADA_MAXIMA = 4 * 1024 * 1024   # niciodată mai mult
MARIME_JSON = 1024 * 1024        # octeți; o stare, o alertă sau o fișă mai mare nu se citește
MAX_TEXT = 200                   # caractere dintr-un text luat din jurnale
CITIT_MAXIM = 20                 # dintr-un text din jurnale se curăță cel mult de atâtea ori lungimea lui arătată
MAX_SEMNE = 10
LIMITA_INTREG = 2 ** 53          # pagina (JavaScript) citește exact doar întregii până aici; unul mai mare lipsește
PARTAJARE = 1 | 2 | 4            # FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

NUME_PAZNIC = re.compile(r"paznic_(\d{4}-\d{2}-\d{2})\.log")
NUME_ALERTA = re.compile(r"veghe_alerta_(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})(\d{2})\.json")
# căile din textele jurnalelor, în ordinea în care se curăță (curata). Fiecare tipar merge în timp liniar: cuantificatorii
# posesivi (*+, ++) nu dau înapoi, iar niciun început nu se mai încearcă de la fiecare literă a unui cuvânt lung (testul îi
# cronometrează pe 32 000 de caractere); textul se taie oricum dinainte, la CITIT_MAXIM × lungimea arătată
INCEPUT_CALE = r"(?:[A-Za-z]:[\\/]|\\\\|//[^/\s\"']|/[A-Za-z]/|~[\\/])"   # C:\, C:/, \\calculator, //calculator, /c/, ~\
DUPA_CITAT = r"[\s,;:.!?)\]}>\"']|\Z"     # ce urmează după ghilimeaua care închide o cale: un spațiu, un semn, capătul
# o cale între ghilimele, cu spațiile ei: se închide doar la o ghilimea de același fel urmată de DUPA_CITAT („'C:\O'Brien\x'”),
# iar una urmată de alt început de cale o oprește; ghilimelele rămân
CALE_CITATA = re.compile(r"([\"'])(?=" + INCEPUT_CALE + r")(?:(?!\1(?:" + DUPA_CITAT + "|" + INCEPUT_CALE
                         + r"))[^\r\n])*+\1(?=" + DUPA_CITAT + ")")
# după o parte de cale, încă una peste spații (C:\Program Files (x86)\sumo\…, C:/Users/Ana Maria/x.csv): cel mult două
# cuvinte fără separator, apoi unul cu \ sau /, care nu începe altă cale; nu și după o parte încheiată cu un semn (C:\x, D:\y).
# Și o unitate sau o fracție aflată la cel mult două cuvinte după cale se duce cu ea, cu tot ce e între ele („C:\x.log are
# 3,5 cadre/s” → „…”): un cuvânt cu / nu se poate deosebi de o parte a căii („C:\Users\Ana Maria/Desktop”), iar mai bine
# prea mult decât o bucată de cale. Un cuvânt care începe cu \ sau / nu se ia („C:\x.log are /tmp” → „… are /tmp”)
FARA_SEMN = r"(?<![,;:.)\]}])"
CONTINUARE = (r"(?:(?:" + FARA_SEMN + r"[ \t]+[^\s\\/\"]++){0,2}" + FARA_SEMN
              + r"[ \t]+(?![A-Za-z]:[\\/]|~[\\/])[^\s\\/\"]++[\\/]\S*+)*")
# o cale de rețea: \\calculator\resursa\… (și forma cu \\ dublate a unei erori) sau //calculator/resursa/… (nu după „https:”)
CALE_RETEA = re.compile(r"(?:(?<![\\\w])\\{2,}+[^\\\s\"']++\\|(?<![:\w/])//[^/\s\"']++/)\S*+" + CONTINUARE)
# C:\… sau C:/…, nu în mijlocul unui cuvânt („Magheru:\Dacia”, „PID:/x”)
CALE_DISC = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]\S*+" + CONTINUARE)
# /c/Users/…, ..\Users\…, Users\… (de la începutul cuvântului) și ~\…
CALE_ACASA = re.compile(r"(?:(?<!\S)\S*?(?<![A-Za-z0-9])Users[\\/]|~[\\/])\S*+" + CONTINUARE, re.IGNORECASE)
# o adresă web cu schemă (https://…, rtsp://…) rămâne cum e, în afară de dosarul utilizatorului; se oprește însă înaintea
# unei căi de disc nelipite de o literă, care se curăță apoi ca oricare alta („https://x.ro/?f=C:/date/x.csv” →
# „https://x.ro/?f=…”, „fișier:///C:/…” → „fișier:///…”). Schema începe doar la capătul din stânga al unui șir de litere
# latine, cifre și + . - (ca tiparul să rămână liniar); după „_” sau o literă cu diacritice, deci, textul se rupe la ea, iar
# o cale lipită de adresă ajunge la început de bucată, unde se recunoaște („eroare_https://x.ro\\srv\…” → „eroare_https://x.ro…”). file:///C:/… e o cale
ADRESA_WEB = re.compile(r"(?<![A-Za-z0-9+.-])(?![Ff][Ii][Ll][Ee]:)[A-Za-z][A-Za-z0-9+.-]++://"
                        r"(?:(?!(?<![A-Za-z0-9])[A-Za-z]:[\\/])[^\s\\\"'<>])*+")
PARANTEZE = {")": "(", "]": "[", "}": "{"}

BAZA_CAMERA = {"cheie": "camera", "stare": "necunoscut", "ultima_dovada": None, "varsta_s": None,
               "prag_s": CAMERA_PROASPATA_S, "alerta_s": CAMERA_ALERTA_S, "rosu_s": CAMERA_ROSU_S, "conectat": None,
               "fps": None, "prag_fps": PRAG_FPS, "lipsa": False}
BAZA_COLECTARE = {"cheie": "colectarea", "stare": "necunoscut", "ultima_dovada": None, "varsta_s": None,
                  "prag_s": COLECTARE_PRAG_S, "rosu_s": COLECTARE_ROSU_S, "interval_s": INTERVAL_S, "sfert": None,
                  "vehicule_urmarite": None}
BAZA_VEGHE = {"cheie": "veghea", "stare": "necunoscut", "ultima_dovada": None, "varsta_s": None, "prag_s": STARE_VECHE,
              "rosu_s": VEGHE_ROSU_S, "ultimul_rand": None, "fps": None, "prag_fps": PRAG_FPS, "pauze_5min": None,
              "prag_pauze": PRAG_PAUZE, "episoade_30min": None, "max_episoade": MAX_EPISOADE, "randuri_ora": None,
              "pauze_ora": None, "alerta": None}
BAZA_PAZNIC = {"cheie": "paznicul", "stare": "necunoscut", "ultima_dovada": None, "varsta_s": None,
               "prag_s": PAZNIC_PRAG_S, "semn_de_viata_s": SEMN_DE_VIATA, "rosu_s": PAZNIC_ROSU_S, "in_regula": None,
               "text": None}
BAZA_NOAPTE = {"cheie": "noaptea", "stare": "necunoscut", "ultima_dovada": None, "varsta_s": None, "prag_s": NOAPTE_S,
               "lunga_s": LANT_LUNG_S, "fara_dosare": False, "lanturi": []}


# ---------------------------------------------------------------------------------------------- textele din jurnale
def _acasa() -> re.Pattern | None:
    """Dosarul utilizatorului și tot ce urmează după el până la primul spațiu (și peste spații, ca CONTINUARE), în formele
    în care poate apărea într-un jurnal: cu \\ sau cu /, oricâți între două părți („C://Users//…”, „C:\\\\Users\\\\…” dintr-o
    eroare), ori ca în Git Bash. Prinde și un nume de utilizator cu spațiu."""
    try:
        a = str(Path.home())
    except (RuntimeError, OSError, KeyError):
        return None
    forme = {a, a.replace("\\", "/")}
    if re.match(r"[A-Za-z]:[\\/]", a):
        forme.add("/" + a[0].lower() + a[2:].replace("\\", "/"))
    forme = [f for f in forme if len(f) > 3]          # nu doar „C:\”: s-ar înlocui orice
    if not forme:
        return None
    # între două părți, oricâți separatori, de oricare fel: forma cu \ și cea cu / dau același tipar. Separatorii se iau
    # posesiv, iar forma care începe cu unul (Git Bash) pornește doar de la primul dintr-un șir: tiparul rămâne liniar și pe
    # un cuvânt de 32 000 de \ sau / (testul cuvântului lung)
    tipare = set()
    for f in forme:
        t = r"[\\/]++".join(map(re.escape, re.split(r"[\\/]+", f)))
        tipare.add(r"(?<![\\/])" + t if t.startswith(r"[\\/]") else t)
    return re.compile("(?:" + "|".join(sorted(tipare, key=len, reverse=True)) + r")\S*+" + CONTINUARE, re.IGNORECASE)


ACASA = _acasa()


def _ascunde(m: re.Match) -> str:
    """„…” în locul căii prinse. Semnele de la capătul ei se duc odată cu ea („C:\\x.log, gata” → „… gata”), în afară de o
    paranteză deschisă înaintea căii, care rămâne, cu tot ce urmează după ea: „(C:\\x) și [D:\\y]” → „(…) și […]”."""
    cale = m.group()
    i = len(cale)
    while i and cale[i - 1] in ",;:.!?)]}":
        i -= 1
    deschise = {d: cale[:i].count(d) - cale[:i].count(p) for p, d in PARANTEZE.items()}
    for k in range(i, len(cale)):
        d = PARANTEZE.get(cale[k])
        if d is None:
            continue
        if deschise[d] > 0:
            deschise[d] -= 1                       # închide o paranteză a căii: „C:\x(1)”
        else:
            return "…" + cale[k:]
    return "…"


def _fara_cai(text: str) -> str:
    """Căile din `text`, unde nu e nicio adresă web, înlocuite cu „…” (vezi tiparele, în ordinea lor)."""
    text = CALE_CITATA.sub(r"\1…\1", text)
    for cale in (ACASA, CALE_RETEA, CALE_DISC, CALE_ACASA):
        if cale is not None:
            text = cale.sub(_ascunde, text)
    return text


def curata(text, maxim: int = MAX_TEXT) -> str:
    """Un text luat din jurnale, bun de arătat: căile locale și ce stă în dosarul utilizatorului devin „…”. O cale între
    ghilimele ține cu tot cu spațiile ei, iar ghilimelele rămân; una fără ghilimele, peste spații până la ultima ei parte cu
    separator (C:\\Program Files (x86)\\sumo\\…). Spațiile se adună câte unul, iar un text mai lung de `maxim` caractere se
    taie, tot cu „…”. Se curăță cel mult CITIT_MAXIM × `maxim` caractere, fără ultimul cuvânt, dacă tăietura cade în el (o
    cale tăiată pe la mijloc nu s-ar mai recunoaște toată). Adresele web cu schemă (https://…) rămân cum sunt, în afară de o
    cale de disc din ele și de dosarul utilizatorului; la fel unitățile (km/h, cadre/s), fracțiile, datele și orele, dar nu
    și cele aflate la cel mult două cuvinte după o cale fără ghilimele: un cuvânt cu \\ sau / (care nu începe cu ele) se duce
    odată cu calea, cu tot ce e între ele („C:\\x.log are 3,5 cadre/s” → „…”), ca să nu rămână o bucată de cale. După o
    parte de cale încheiată cu un semn dintre , ; : . ) ] }, ce urmează rămâne („C:\\x.log, are 3,5 cadre/s” → „… are 3,5
    cadre/s”)."""
    text, lung = str(text), CITIT_MAXIM * maxim
    taiat = len(text) > lung
    if taiat:
        intreg = text[lung].isspace()              # tăietura cade între două cuvinte
        text = text[:lung]
        if not intreg:
            i = len(text)
            while i and not text[i - 1].isspace():
                i -= 1
            text = text[:i] or text                # un singur cuvânt, uriaș: rămâne începutul lui
    bucati, poz = [], 0
    for m in ADRESA_WEB.finditer(text):
        bucati += [_fara_cai(text[poz:m.start()]), m.group() if ACASA is None else ACASA.sub(_ascunde, m.group())]
        poz = m.end()
    text = " ".join(("".join(bucati) + _fara_cai(text[poz:])).split())
    if ACASA is not None:
        # plasa de siguranță: dosarul utilizatorului nu rămâne nicăieri, nici după o „adresă” care se oprește înaintea lui
        # („cuvantC://Users\…”: adresa se oprește la \, iar restul nu mai începe cu C:). Unde nu a rămas, nu schimbă nimic
        text = ACASA.sub(_ascunde, text)
    if taiat and not text.endswith("…"):
        text += "…"
    return text if len(text) <= maxim else text[:maxim - 1].rstrip() + "…"


# ---------------------------------------------------------------------------------------------- citirea
def _deschide(f) -> BinaryIO:
    """Fișierul, deschis doar pentru citire, în mod binar. Pe Windows, cu partajarea completă (citire, scriere, ștergere):
    open() obișnuit nu împarte ștergerea, deci cât îl ține panoul deschis, un unlink al altui proces ar eșua (renumărarea
    de noapte șterge CSV-ul de ieri și îl scrie din nou). Așa, ștergerea și scrierea din nou merg, iar panoul citește până
    la capăt conținutul de dinainte. Un fișier lipsă dă tot FileNotFoundError."""
    if _winapi is None:
        return open(f, "rb")
    h = _winapi.CreateFile(str(f), _winapi.GENERIC_READ, PARTAJARE, 0, _winapi.OPEN_EXISTING, 0, 0)
    try:
        fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        _winapi.CloseHandle(h)
        raise
    try:
        return open(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _octeti(f, maxim: int | None = None) -> bytes | None:
    """Tot conținutul fișierului, dintr-o singură deschidere (`_deschide`); None dacă are mai mult de `maxim` octeți."""
    with _deschide(f) as fo:
        if maxim is not None and os.fstat(fo.fileno()).st_size > maxim:
            return None
        return fo.read()


def _coada(f: Path, octeti: int) -> tuple[str, list[str], bool, float]:
    """(primul rând, rândurile întregi din ultimii `octeti` octeți, s-a ajuns la primul rând?, data fișierului), dintr-o
    singură deschidere a fișierului, închis pe loc. Rândul început înaintea porțiunii citite se lasă deoparte, la fel unul
    încă în scriere (fără sfârșit de rând). Data se ia după citire: o scriere de până atunci a schimbat-o deja."""
    with _deschide(f) as fo:
        cap = fo.readline(COADA_MAXIMA)
        marime = fo.seek(0, 2)
        start = max(len(cap), marime - octeti)
        tot = start == len(cap)
        fo.seek(start if tot else start - 1)       # cu octetul dinainte: se vede dacă porțiunea începe cu un rând întreg
        bucata = fo.read(marime - fo.tell())
        scris = os.fstat(fo.fileno()).st_mtime
    if not tot:
        i = bucata.find(b"\n")
        bucata = bucata[i + 1:] if i >= 0 else b""
    bucata = bucata[:bucata.rfind(b"\n") + 1]       # fără un ultim rând încă în scriere
    randuri = [r.rstrip("\r") for r in bucata.decode("utf-8", "replace").split("\n")[:-1]]
    return cap.decode("utf-8", "replace").lstrip("\ufeff").rstrip("\r\n"), randuri, tot, scris


def _csv(cap: str, randuri: list[str]) -> tuple[list[str], list[dict]]:
    """Coloanele, din primul rând al fișierului (CSV-urile mai vechi au altele), și rândurile, ca dicționare."""
    coloane = next(csv.reader([cap]), [])
    return coloane, list(csv.DictReader(randuri, fieldnames=coloane))


def _varsta(acum: float, t: float) -> float:
    """Vârsta unei dovezi, în secunde, rotunjită la 0,1 s. Una scrisă chiar în timpul calculului (starea live se rescrie în
    fiecare secundă) ar ieși puțin negativă: are 0."""
    return round(max(0.0, acum - t), 1)


def _calculeaza(baza: dict, calcul, *argumente) -> tuple[dict, object]:
    """Veriga completată de `calcul` pe o copie a bazei, și ce întoarce calculul. O eroare neprevăzută lasă baza, cu starea
    „necunoscut” și doar tipul erorii: mesajul ar putea conține o cale."""
    v = copy.deepcopy(baza)
    try:
        return v, calcul(v, *argumente)
    except Exception as e:
        return {**copy.deepcopy(baza), "eroare": type(e).__name__}, None


# ---------------------------------------------------------------------------------------------- verigile
def _camera(v: dict, live, acum: float) -> dict | None:
    """Starea live: dovada e data fișierului. Întoarce conținutul dacă e proaspăt (pentru colectare), altfel None."""
    f = Path(live) / "state.json"
    continut = None
    for k in range(INCERCARI_STARE):
        try:
            date_ = _octeti(f, MARIME_JSON)
            continut = None if date_ is None else json.loads(date_)   # din octeți: json recunoaște singur UTF-8, cu sau
            break                                                      # fără BOM, și UTF-16
        except FileNotFoundError:
            break
        except (OSError, ValueError):              # tocmai înlocuit (Windows) sau prins pe jumătate: încă o dată
            if k + 1 < INCERCARI_STARE:
                time.sleep(PAUZA_STARE_S)
    try:
        scris = f.stat().st_mtime
    except FileNotFoundError:
        v.update(stare="problema", lipsa=True)
        return None
    v["ultima_dovada"], v["varsta_s"] = scris, _varsta(acum, scris)
    if not isinstance(continut, dict):
        return None                                # există, dar nu se poate citi: necunoscut
    conectat = continut.get("conectat")
    v["conectat"] = conectat if isinstance(conectat, bool) else None
    v["fps"] = _numar(continut.get("fps"))
    varsta = v["varsta_s"]
    if varsta >= CAMERA_ROSU_S:
        v["stare"] = "problema"
    elif varsta >= CAMERA_PROASPATA_S:
        v["stare"] = "atent"
    elif v["conectat"] is False or (v["fps"] is not None and v["fps"] < PRAG_FPS):
        v["stare"] = "atent"
    else:
        v["stare"] = "ok"
    return continut if varsta < CAMERA_PROASPATA_S else None


def _ultimul_sfert(f: Path, acum: float) -> tuple[float, float, int | None, int | None] | None:
    """(începutul, sfârșitul, vehiculele intrate, pietonii) ultimului sfert întreg din CSV-ul numărătorilor, adică al
    rândurilor cu cel mai mare `sfarsit`, din coada fișierului (citită mai lung, până cuprinde tot sfertul). Colectarea
    scrie un sfert dintr-o singură deschidere (od_counter.write_csv), dar printr-o zonă tampon de 8 KB: un sfert mai mare
    ajunge în fișier din mai multe scrieri. De aceea, dintr-un fișier scris în ultimele SFERT_IN_SCRIERE_S se ia sfertul
    dinaintea ultimului. Un rând cu un număr pe care pagina nu l-ar citi exact (_bun) e stricat și se sare, iar un total
    de felul acesta lipsește (None). None fără niciun sfert bun."""
    octeti = COADA_NUMARATORI
    while True:
        cap, randuri, tot, scris = _coada(f, octeti)
        sarite = 1 if scris > acum - SFERT_IN_SCRIERE_S else 0      # ultimul sfert, poate încă în scriere
        bune = []
        for r in _csv(cap, randuri)[1]:
            try:
                rand = (fs.ora(r["inceput"]), fs.ora(r["sfarsit"]), r.get("tip"), int(r["numar"]))
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            if _bun(rand[3]):
                bune.append(rand)
        sfarsituri = sorted({b for _, b, _, _ in bune}, reverse=True)
        # sfertul ales e întreg dacă porțiunea citită are și rânduri dinaintea lui
        if tot or octeti >= COADA_MAXIMA or len(sfarsituri) > sarite + 1:
            break
        octeti = min(octeti * 4, COADA_MAXIMA)
    if len(sfarsituri) <= sarite:
        return None
    ales = sfarsituri[sarite]
    sfert = [x for x in bune if x[1] == ales]
    vehicule, pietoni = (sum(n for _, _, tip, n in sfert if tip == fel) for fel in ("intrare", "pietoni"))
    return (min(a for a, _, _, _ in sfert), ales, vehicule if _bun(vehicule) else None, pietoni if _bun(pietoni) else None)


def _colectarea(v: dict, numaratori, acum: float, live_proaspat: dict | None) -> None:
    """Ultimul sfert încheiat, din fișierul de azi sau, până la primul sfert al zilei, din cel de ieri."""
    if live_proaspat is not None:
        v["vehicule_urmarite"] = _intreg_exact(live_proaspat.get("vehicule_urmarite"))
    azi = date.fromtimestamp(acum)
    for zi in (azi, azi - timedelta(days=1)):
        try:
            gasit = _ultimul_sfert(Path(numaratori) / f"numaratori_{zi.isoformat()}.csv", acum)
        except FileNotFoundError:
            continue
        if gasit is not None:
            break
    else:
        return
    inceput, sfarsit, vehicule, pietoni = gasit
    v["ultima_dovada"], v["varsta_s"] = sfarsit, _varsta(acum, sfarsit)
    v["sfert"] = {"zi": date.fromtimestamp(inceput).isoformat(), "inceput": f"{datetime.fromtimestamp(inceput):%H:%M}",
                  "sfarsit": f"{datetime.fromtimestamp(sfarsit):%H:%M}", "vehicule_intrate": vehicule, "pietoni": pietoni}
    varsta = v["varsta_s"]
    v["stare"] = "ok" if varsta <= COLECTARE_PRAG_S else "atent" if varsta <= COLECTARE_ROSU_S else "problema"


def _alerta(loguri: Path, acum: float) -> dict | None:
    """Cea mai nouă alertă a vegherii din ultimele 24 h: ora ei (din JSON, altfel din nume) și semnele, nimic altceva.
    `dupa_ultimul_rand` se socotește în _veghea; fără niciun rând al vegherii, alerta e după el."""
    aleasa = None
    for f in loguri.glob("veghe_alerta_*.json"):
        m = NUME_ALERTA.fullmatch(f.name)
        try:
            t = datetime.strptime("{} {}:{}:{}".format(*m.groups()), "%Y-%m-%d %H:%M:%S").timestamp() if m else None
        except ValueError:
            t = None
        if t is not None and acum - t > ALERTA_S + 3600:
            continue                               # după nume, mult prea veche: nici nu se deschide
        semne = []
        try:
            date_ = _octeti(f, MARIME_JSON)
            d = None if date_ is None else json.loads(date_)
        except (OSError, ValueError):              # tocmai se scrie (alerta se scrie de două ori) sau e stricată
            d = None
        if isinstance(d, dict):
            try:
                t = fs.ora(d["ora"])
            except (KeyError, TypeError, ValueError, AttributeError):
                pass
            if isinstance(d.get("semne"), list):
                semne = [curata(s) for s in d["semne"] if isinstance(s, str)][:MAX_SEMNE]
        if t is not None and acum - t <= ALERTA_S and (aleasa is None or t > aleasa["ora"]):
            aleasa = {"ora": t, "semne": semne, "dupa_ultimul_rand": True}
    return aleasa


def _veghea(v: dict, loguri, acum: float) -> None:
    """Cel mai nou CSV al vegherii (după data fișierului): ultimul rând, rândurile și pauzele din ultima oră, alerta."""
    loguri = Path(loguri)
    v["alerta"] = _alerta(loguri, acum)
    fisiere = []
    for f in loguri.glob("veghe_*.csv"):
        try:
            fisiere.append((f.stat().st_mtime, f))
        except OSError:
            pass
    if not fisiere:
        return
    scris, f = max(fisiere)
    octeti = COADA_VEGHE
    while True:
        cap, randuri, tot, _ = _coada(f, octeti)
        coloane, toate = _csv(cap, randuri)
        bune = []
        for r in toate:
            try:
                bune.append((datetime.strptime((r.get("ora") or "").strip(), "%Y-%m-%d %H:%M").timestamp(), r))
            except ValueError:
                continue
        if tot or octeti >= COADA_MAXIMA or (bune and bune[0][0] < acum - ULTIMA_ORA_S):
            break
        octeti = min(octeti * 4, COADA_MAXIMA)
    v["ultima_dovada"], v["varsta_s"] = scris, _varsta(acum, scris)
    din_ora = [r for t, r in bune if acum - t <= ULTIMA_ORA_S]
    v["randuri_ora"] = len(din_ora)
    if "evenimente" in coloane:                    # CSV-urile vechi n-au pauzele
        v["pauze_ora"] = sum(len(fs.EVENIMENT.findall(r.get("evenimente") or "")) for r in din_ora)
    peste_prag = False
    if bune:
        ultim = bune[-1][1]
        v["ultimul_rand"] = ultim["ora"].strip()
        v["fps"] = _numar(ultim.get("fps"))
        v["pauze_5min"] = _intreg_exact(ultim.get("pauze_5min"))      # în răspuns, doar ce citește pagina exact
        v["episoade_30min"] = _intreg_exact(ultim.get("episoade_flux_30min"))
        # pentru stare contează orice număr, cât de mare (un CSV stricat): „1e400” e tot peste prag
        peste_prag = (_cel_putin(ultim.get("pauze_5min"), PRAG_PAUZE)
                      or _cel_putin(ultim.get("episoade_flux_30min"), MAX_EPISOADE))
    varsta = v["varsta_s"]
    if varsta >= VEGHE_ROSU_S:
        v["stare"] = "problema"
    elif varsta >= STARE_VECHE:
        v["stare"] = "atent"
    elif (v["fps"] is not None and v["fps"] < PRAG_FPS) or peste_prag:
        v["stare"] = "atent"
    else:
        v["stare"] = "ok"
    if v["alerta"] is not None:
        # veghea se oprește la prima alertă: una de după ultimul rând (sau scrisă odată cu el) e cea pe care s-a oprit;
        # e de urmărit de îndată, iar cu veghea tăcută de 3 min, o problemă (sub 3 min, starea de mai sus e ok sau atent)
        v["alerta"]["dupa_ultimul_rand"] = v["alerta"]["ora"] >= scris - MARJA_ALERTA_S
        if v["alerta"]["dupa_ultimul_rand"]:
            v["stare"] = "problema" if varsta >= STARE_VECHE else "atent"


def _ultima_nota(f: Path) -> tuple[float, str] | None:
    """Ora și textul ultimei note a paznicului dintr-un jurnal; rândurile fără oră (urma unei erori) se sar."""
    octeti = COADA_PAZNIC
    while True:
        cap, randuri, tot, _ = _coada(f, octeti)
        for rand in reversed(([cap] if tot else []) + randuri):
            m = fs.RAND_PAZNIC.match(rand)
            if m:
                try:
                    return fs.ora(m.group(1)), m.group(2)
                except ValueError:
                    continue
        if tot or octeti >= COADA_MAXIMA:
            return None
        octeti = min(octeti * 4, COADA_MAXIMA)


def _paznicul(v: dict, loguri, acum: float) -> None:
    """Ultima notă din cel mai nou jurnal al paznicului de până azi; dacă n-are nicio notă cu oră, din cel dinainte. O notă
    bună (NOTE_BUNE) e în regulă cât e mai nouă de PAZNIC_PRAG_S; altă notă e de urmărit, până la următoarea notă bună."""
    azi = date.fromtimestamp(acum).isoformat()
    jurnale = sorted((m.group(1), f) for f in Path(loguri).glob("paznic_*.log")
                     if (m := NUME_PAZNIC.fullmatch(f.name)) and m.group(1) <= azi)
    nota = None
    for _, f in reversed(jurnale[-2:]):
        try:
            nota = _ultima_nota(f)
        except FileNotFoundError:
            continue
        if nota is not None:
            break
    if nota is None:
        return
    t, text = nota
    text = curata(text)
    v.update(ultima_dovada=t, varsta_s=_varsta(acum, t), text=text, in_regula=text.startswith(NOTE_BUNE))
    varsta = v["varsta_s"]
    if varsta > PAZNIC_ROSU_S:
        v["stare"] = "problema"
    elif varsta > PAZNIC_PRAG_S or not v["in_regula"]:
        v["stare"] = "atent"
    else:
        v["stare"] = "ok"


def _atentia(f: Path) -> str:
    """Atenționarea notată de lanț în stare.json (`atentie`), curățată; altfel una generală."""
    try:
        date_ = _octeti(f, MARIME_JSON)
        d = None if date_ is None else json.loads(date_)
    except (OSError, ValueError):
        d = None
    text = d.get("atentie") if isinstance(d, dict) else None
    return curata(text) if isinstance(text, str) and text.strip() else ATENTIE_IMPLICITA


def _stare_lant(f: Path, acum: float) -> dict:
    """`fisa_senzor.stare_lant`, cu două îndreptări pentru panou; fișa își păstrează definiția strictă din § 4.6:
      * o citire care găsește fișierul gol sau pe jumătate (lant_cor își rescrie starea pe loc) se mai încearcă o dată,
        după PAUZA_LANT_S;
      * un lanț încheiat cu „gata”, dar cu un cod diferit de 0, e încheiat, cu atenționarea lui (`atentie`), nu eșuat:
        lant_zilnic scrie „gata” doar fără vreun pas eșuat, deci codul a fost unul acceptat (COD_MEMBRI_STRICATI la
        `repara`, când jurnalul are membri stricați; lanțul notează atunci `atentie` și merge mai departe)."""
    s = fs.stare_lant(f, acum)
    if s.get("stare") == "necitibil":
        time.sleep(PAUZA_LANT_S)
        s = fs.stare_lant(f, acum)
    s = {**s, "atentie": None}
    if s.get("stare") == "esuat" and s.get("rezultat") in fs.GATA and (s.get("coduri_nenule") or 0) > 0:
        s.update(stare="incheiat", atentie=_atentia(f))
    return s


def _blocare(dosar: Path, zi: str) -> float | None:
    """Data fișierului proces.pid al lanțului pentru ziua `zi`, adică pornirea lui, dacă fișierul există."""
    f = dosar / zi / FISIER_BLOCARE
    try:
        return f.stat().st_mtime if f.is_file() else None
    except OSError:
        return None


def _lant_vechi_incheiat(f: Path) -> bool:
    """Copia lui lant_cor.lant_vechi_incheiat, după care măsura nouă își așteaptă lanțul vechi: acesta și-a încheiat ziua,
    oricum ar fi ieșit, dacă starea lui (`f`) se poate citi și rezultatul nu mai e „in_curs”. O stare care lipsește, e
    goală, pe jumătate sau stricată nu e încheiată: măsura nouă o mai așteaptă (tests/test_senzor.py verifică să răspundă ca
    originalul). Una care nu e un dicționar oprește bucla lui lant_cor cu o excepție: atunci nu mai așteaptă nimic."""
    try:
        d = json.loads(_octeti(f).decode("utf-8"))
    except (OSError, ValueError):                  # lipsește (FileNotFoundError) sau nu se poate citi ori decoda
        return False
    return not isinstance(d, dict) or d.get("rezultat") != "in_curs"


def _noaptea(v: dict, lanturi, acum: float) -> None:
    """Fiecare lanț de noapte, pentru ultima zi a cărei noapte a sosit (`zi_asteptata`), cu `_stare_lant`. Fără stare
    pentru ziua aceea: „neinceput” în primele 10 min de la ora lui, apoi „lipsa”, cu datele zilei de dinainte; în afară de
    cele două așteptări din program (`asteapta`, vezi descrierea modulului)."""
    t = datetime.fromtimestamp(acum)
    vreun_dosar = False
    porniri, dosare = {}, {}
    for cheie, (dosar, la_ora) in (LANTURI if lanturi is None else lanturi).items():
        dosare[cheie] = dosar = Path(dosar)
        vreun_dosar = vreun_dosar or dosar.is_dir()
        azi_la_ora = datetime.combine(t.date(), la_ora)
        asteptata = t.date() - timedelta(days=1 if azi_la_ora <= t else 2)
        porniri[cheie] = pornire = datetime.combine(asteptata + timedelta(days=1), la_ora).timestamp()
        zile = sorted(p.name for p in dosar.iterdir() if fs.NUME_ZI.fullmatch(p.name)
                      and p.name <= asteptata.isoformat() and (p / "stare.json").is_file()) if dosar.is_dir() else []
        zi = zile[-1] if zile else None
        s = _stare_lant(dosar / zi / "stare.json", acum) if zi else {}
        x = {"cheie": cheie, "ora": la_ora.strftime("%H:%M"), "zi": zi, "zi_asteptata": asteptata.isoformat(),
             "stare": s.get("stare") if zi == asteptata.isoformat() else
             ("lipsa" if acum - pornire > MARJA_LANT_S else "neinceput"),
             **{k: s.get(k) for k in ("rezultat", "pornit", "incheiat_la", "pasi", "coduri_nenule")},
             "urmatoarea": (azi_la_ora if azi_la_ora > t else azi_la_ora + timedelta(days=1)).isoformat(timespec="seconds"),
             "atentie": s.get("atentie"), "asteapta": None, "prea_lunga": False}
        blocare = _blocare(dosar, asteptata.isoformat()) if dosar.is_dir() else None
        if (zi != asteptata.isoformat() and blocare is not None
                and -MARJA_CEAS_S <= acum - blocare <= ASTEPTARE_FLUX_S + MARJA_LANT_S):
            # lanțul vechi a pornit (proces.pid) și așteaptă fluxul camerei, înaintea primei stări a zilei; un proces.pid
            # scris „în viitor” (ceasul dat înapoi după el) nu e o pornire de acum
            x.update(stare="in_curs", zi=asteptata.isoformat(), pornit=fs.iso(blocare), asteapta="fluxul", rezultat=None,
                     incheiat_la=None, pasi=None, coduri_nenule=None, atentie=None)
        if x["rezultat"] is not None:
            x["rezultat"] = curata(x["rezultat"])  # „oprit: LIPSEȘTE <calea jurnalului>”
        if x["stare"] == "in_curs" and x["pornit"]:
            try:
                x["prea_lunga"] = acum - fs.ora(x["pornit"]) > LANT_LUNG_S
            except (TypeError, ValueError, AttributeError):
                pass
        v["lanturi"].append(x)
    dupa_cheie = {x["cheie"]: x for x in v["lanturi"]}
    for x in v["lanturi"] if vreun_dosar else ():  # fără niciun dosar, nu rulează nimic aici: nu se așteaptă nimic
        # măsura nouă așteaptă, fără să scrie nimic, lanțul vechi al aceleiași zile (lant_cor.bucla): cât timp
        # lant_cor.lant_vechi_incheiat spune că nu s-a încheiat, dar cel mult ASTEPTARE_LANT_VECHI_S
        vechi = dupa_cheie.get(ASTEAPTA_DUPA.get(x["cheie"]))
        if (vechi is None or x["zi"] == x["zi_asteptata"] or x["stare"] not in ("lipsa", "neinceput")
                or vechi["zi_asteptata"] != x["zi_asteptata"]):
            continue
        pornire = porniri[x["cheie"]]
        if not _lant_vechi_incheiat(dosare[vechi["cheie"]] / x["zi_asteptata"] / "stare.json"):
            asteapta = "lant" if acum - pornire <= ASTEPTARE_LANT_VECHI_S + MARJA_LANT_S else None
        else:
            # încheiat (sau oprit) după ora măsurii noi: aceasta îl vede la următoarea ei verificare și abia apoi pornește,
            # deci cele MARJA_LANT_S se socotesc de la încheiere („pornire”: nu mai așteaptă nimic, doar pornește); după
            # ASTEPTARE_LANT_VECHI_S pornise oricum
            try:
                sfarsit = min(fs.ora(vechi["incheiat_la"]), pornire + ASTEPTARE_LANT_VECHI_S)
            except (TypeError, ValueError, AttributeError):
                sfarsit = pornire                  # fără ora încheierii: ca un lanț încheiat la timp
            asteapta = "pornire" if sfarsit > pornire and acum - sfarsit <= MARJA_LANT_S else None
        if asteapta:
            x.update(stare="neinceput", asteapta=asteapta)
    incheiate = [fs.ora(x["incheiat_la"]) for x in v["lanturi"] if x["incheiat_la"]]
    if incheiate:
        v["ultima_dovada"] = max(incheiate)
        v["varsta_s"] = _varsta(acum, v["ultima_dovada"])
    v["fara_dosare"] = not vreun_dosar
    if not vreun_dosar:
        return                                     # nicio prelucrare de noapte aici: necunoscut
    stari = {x["stare"] for x in v["lanturi"]}
    if stari & {"esuat", "lipsa"}:
        v["stare"] = "problema"
    elif stari <= {"incheiat", "in_curs"} and not any(x["atentie"] or x["prea_lunga"] for x in v["lanturi"]):
        v["stare"] = "ok"
    else:                                          # necitibil, neinceput, o atenționare, o rulare prea lungă sau o stare
        v["stare"] = "atent"                       # nouă, necunoscută aici


# ---------------------------------------------------------------------------------------------- fișa
def _bun(x) -> bool:
    """Un număr pe care pagina îl citește exact: finit și, dacă e întreg, cel mult LIMITA_INTREG (JavaScript ar citi un
    întreg mai mare rotunjit, iar unul de peste 1,8·10³⁰⁸ ca Infinity)."""
    return abs(x) <= LIMITA_INTREG if isinstance(x, int) else math.isfinite(x)


def _nr(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and _bun(x) else None


def _numar(x) -> float | None:
    """fs._numar, fără excepție: un întreg JSON prea mare pentru float (OverflowError) lipsește, ca un număr infinit; un
    bool nu e un număr (ca la _intreg_exact)."""
    if isinstance(x, bool):
        return None
    try:
        return fs._numar(x)
    except OverflowError:
        return None


def _intreg_exact(x) -> int | None:
    """Un întreg dintr-o stare sau dintr-un CSV, pentru răspuns. Un int rămâne el însuși, fără ocolul prin float (care ar
    rotunji 2**53 + 1 la 2**53), un bool nu e un număr, iar restul trece prin fs._intreg, fără excepții. Ce pagina n-ar
    citi exact (_nr) lipsește."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return _nr(x)
    try:
        return _nr(fs._intreg(x))
    except OverflowError:
        return None


def _cel_putin(x, prag: float) -> bool:
    """x (un text din CSV sau un număr) e cel puțin `prag`, oricât de mare: și „1e400” (infinit) sau '9' * 400. Un bool nu
    e un număr, iar un int se compară exact, fără ocolul prin float."""
    if isinstance(x, bool):
        return False
    if isinstance(x, int):
        return x >= prag
    try:
        return float(x) >= prag
    except (TypeError, ValueError, OverflowError):
        return False


def _suma(valori) -> float | None:
    """Suma valorilor care nu lipsesc; o sumă de întregi rămâne întreagă. Una pe care pagina n-ar citi-o exact (_bun:
    infinită sau un întreg de peste LIMITA_INTREG) lipsește: în JSON, Infinity nu e o valoare validă."""
    valori = [x for x in valori if x is not None]
    if not valori:
        return None
    s = sum(valori)
    return s if _bun(s) else None


def ultima_fisa(fise=FISE) -> dict | None:
    """Rezumatul celei mai noi fișe a senzorului, după tăietură; la egalitate, cea din primul dosar, adică cea publicată
    (`publica`). O fișă care nu se poate citi sau n-are o tăietură bună se sare; None dacă nu e niciuna."""
    aleasa = None
    for i, dosar in enumerate(fise):
        try:
            fisiere = sorted(Path(dosar).glob("fisa_senzor_*.json")) if Path(dosar).is_dir() else []
        except OSError:
            continue
        for f in fisiere:
            try:
                date_ = _octeti(f, MARIME_JSON)
                if date_ is None:
                    continue
                d = json.loads(date_)
                t = fs.ora(d["taietura"]) if isinstance(d, dict) else None
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue
            if t is not None and (aleasa is None or t > aleasa[0]):
                aleasa = (t, i, d)
    if aleasa is None:
        return None
    t, i, d = aleasa

    def din(*chei):
        x = d
        for k in chei:
            x = x.get(k) if isinstance(x, dict) else None
        return x

    lanturi = din("lanturi") if isinstance(din("lanturi"), dict) else {}
    lanturi = [x for k, x in lanturi.items() if k != "total" and isinstance(x, dict)]    # „total” le adună deja
    zile = din("vehicule", "pe_zile")
    zile = [x for x in zile.values() if isinstance(x, dict)] if isinstance(zile, dict) else []
    try:
        inceput = fs.iso(fs.ora(din("inceput")))
    except (TypeError, ValueError, AttributeError):
        inceput = None
    return {"taietura": fs.iso(t), "inceput": inceput, "ore": _nr(din("durata", "ore")),
            "pondere_minute_cu_cadre": _nr(din("minute", "pondere_cu_cadre")),
            "fps_mediana": _nr(din("cadre_pe_secunda", "mediana")), "opriri_anuntate": _nr(din("opriri", "anuntate")),
            "caderi_neprevazute": _nr(din("opriri", "caderi_neprevazute")), "pauze": _nr(din("pauze", "numar")),
            "episoade_reconectare": _nr(din("reconectari", "episoade")),
            "lanturi_incheiate": _suma(_nr(x.get("incheiate")) for x in lanturi),
            "lanturi_asteptate": _suma(_nr(x.get("asteptate")) for x in lanturi),
            "vehicule": _suma(_nr(x.get("vehicule")) for x in zile), "publica": i == 0}


# ---------------------------------------------------------------------------------------------- răspunsul
def stare_senzor(acum: float | None = None, live=LIVE, loguri=LOGURI, numaratori=NUMARATORI, lanturi=LANTURI,
                 fise=FISE) -> dict:
    """Răspunsul pentru GET /api/senzor, fără `ora_server` (o pune serverul): cele cinci verigi, în ordine, și rezumatul
    ultimei fișe. Nu ridică excepții: fiecare verigă se calculează separat. Dosarele se dau ca parametri, ca testele să
    lucreze pe dosare temporare."""
    acum = time.time() if acum is None else float(acum)
    camera, live_proaspat = _calculeaza(BAZA_CAMERA, _camera, live, acum)
    verigi = [camera] + [_calculeaza(baza, calcul, *argumente)[0] for baza, calcul, argumente in (
        (BAZA_COLECTARE, _colectarea, (numaratori, acum, live_proaspat)),
        (BAZA_VEGHE, _veghea, (loguri, acum)),
        (BAZA_PAZNIC, _paznicul, (loguri, acum)),
        (BAZA_NOAPTE, _noaptea, (lanturi, acum)))]
    try:
        fisa = ultima_fisa(fise)
    except Exception:                              # nici fișa nu poate strica răspunsul
        fisa = None
    return {"calculat_la": acum, "memorare_s": MEMORARE_S, "verigi": verigi, "fisa": fisa}
