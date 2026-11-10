"""Fișa senzorului (§ 4.6): cifrele colectării de la cameră, adică partea IoT a prezentării, refăcute din jurnalele locale
până la o tăietură dată (--pana-la), mereu cu aceleași definiții. Jurnalele rămân pe calculatorul care a rulat colectarea,
deci fișa se poate calcula doar acolo.

Citește doar fișierele de mai jos; nu atinge starea live (outputs/live), imaginile sau jurnalele de traiectorii și nu scrie
decât fișierele cerute (--out-json, --out-md):
  * outputs/logs/veghe_*.csv – rândul de minut al vegherii (`romana.vision.veghe`, coloanele din CSV_CAP): rata cadrelor
    (`fps`), vârsta stării live, contorul de reconectări și, în `evenimente`, pauzele fără cadre;
  * outputs/logs/reporniri_*.csv – golurile colectării, scrise de paznic (`oprire` = ultima dovadă de viață, `repornire` =
    prima traiectorie nouă; un gol peste miezul nopții apare în fișierul fiecărei zile atinse);
  * outputs/logs/paznic_*.log – notele „oprire anunțată” și repornirile paznicului („repornire, încercarea N: motivul”);
  * outputs/logs/veghe_alerta_*.json – alertele vegherii: doar cele „fără cadre”, cu ora alertei și ora stării live;
  * outputs/logs/viziune_*.log – doar data creării fiecăruia, adică pornirea fiecărei rulări a colectării. Conținutul lor nu
    se numără: ieșirea standard rămâne în tamponul procesului, iar mesajele fluxului din .err (ffmpeg, OpenCV) nu au oră.
    De aceea reconectările se numără din contorul colectării, notat de veghe în fiecare minut;
  * outputs/lant/<zi>/stare.json și outputs/lant_cor/<zi>/stare.json – lanțurile de noapte;
  * data/counts/numaratori_<zi>.csv – intrările de vehicule pe clase; pietonii, doar ca total pe zi.

Definițiile (aceleași în JSON, în tabel și pe ecran):
  * începutul colectării – ultima pornire a colectării dinaintea tăieturii (data creării unui viziune_*.log) care
    nu e o repornire peste un gol trecut în reporniri_*.csv (sau numită de paznic în nota pornirii): de atunci, orice
    întrerupere e în reporniri, cu durata ei. Se poate da și de mână, cu --de-la.
  * fereastra – de la început până la tăietură. Un rând al vegherii intră doar dacă minutul lui s-a încheiat până la
    tăietură: rândul se scrie în cursul minutului, deci cel al minutului tăieturii poate fi de după ea. O pauză se află abia
    după ce se încheie, iar un gol abia la repornire: pentru o tăietură de acum, cifrele se așază după câteva minute.
  * oprire – un gol din reporniri_*.csv, numărat o dată, tăiat la fereastră. E anunțată dacă paznicul a notat „oprire
    anunțată” între 10 min înaintea ultimei dovezi de viață și repornire: nota se repetă la 5 min cât timp există
    outputs/live/fara_repornire și se scrie la verificarea de minut, deci poate veni și după oprire. Altfel e o cădere
    neprevăzută, cu motivul repornirii din jurnalul paznicului (procesul lipsește / proces blocat).
  * pauză – un gol de cel puțin 10 s între două cadre prelucrate, cât rulează colectarea, cum îl notează veghea în
    `evenimente` („HH:MM:SS fără cadre N s”): de la ultimul cadru dinaintea golului (ora din starea live, citită o dată pe
    secundă) până la primul cadru de după el, cu N rotunjit la secundă. Golurile de 2,5–10 s nu se notează și nu intră; o
    pauză care atinge o oprire ține de oprire, iar una care începe într-o cădere a sursei, de cădere (o pauză încheiată
    chiar la începutul căderii rămâne pauză, deși, din rotunjire, capătul ei poate trece cu o secundă de el). Fiecare pauză
    se încheie cu un cadru nou, fără repornire: s-a refăcut singură.
  * cădere a sursei – un gol al fluxului care nu s-a încheiat cât a mers veghea: după 180 s fără cadre, veghea scrie
    alerta „fără cadre” și se oprește, deci golul nu ajunge pauză, iar până la repornirea ei nu mai are rânduri. Căderea
    începe la ultimul cadru dinaintea alertei (ora stării live din alertă; fără ea, ora alertei minus secundele din semn) și
    ține până la primul semn de cadre: capătul pauzei aceluiași gol, dacă o veghe pornită cu --fara a notat-o, începutul
    unei pauze de după alertă, repornirea unei opriri începute în cădere (prima traiectorie nouă) sau, dacă vine mai devreme
    cu cel puțin un minut, începutul primului minut de după alertă cu un rând al vegherii cu starea proaspătă; fără niciun
    semn, până la tăietură. Sfârșitul e o margine de sus: veghea se repornește abia după ce fluxul a revenit. Căderile care
    se suprapun se unesc, iar partea unei căderi care atinge o oprire ține de oprire. Golul unei alerte „fără cadre” care
    începe într-o oprire sau cu cel mult 5 s înaintea ei nu e o cădere a sursei: colectarea s-a blocat sau era oprită, iar
    golul e deja oprirea. Altfel, colectarea a rămas pornită și s-a reconectat singură, deci o cădere nu e o oprire. Se
    numără doar căderile cu cel puțin o secundă din fereastră în afara opririlor și a pauzelor.
  * minut cu cadre – un minut întreg din fereastră care nu stă în întregime într-o oprire, într-o pauză sau într-o cădere a
    sursei (două pauze lipite au între ele cel puțin un cadru); ponderea = minute cu cadre / minute întregi. Un minut fără
    rând al vegherii, în afara opririlor și a căderilor, se socotește cu cadre: bucla vegherii alunecă un minut la ≈4,5 h,
    iar după o alertă de alt fel veghea se repornește; câte sunt se arată separat. Pentru comparație: ponderea timpului cu
    colectarea pornită (fără opriri) și cea a timpului cu cadre (fără reuniunea opririlor, pauzelor și căderilor).
  * cadre pe secundă – mediana coloanei `fps` (media glisantă a colectării) pe rândurile din fereastră cu starea proaspătă
    (sub 2,5 s, ca la semnul „rata mică” al vegherii): în timpul unei pauze, `fps` e valoarea de dinaintea ei.
  * reconectări – contorul colectării crește la fiecare pierdere a fluxului și la fiecare încercare eșuată de a-l
    redeschide, iar o rulare nouă îl ia de la 0. Se dau creșterile din fereastră, pe toate rulările, și episoadele: creșteri
    la cel mult 2 min una de alta, ca în veghe. Un episod fără vreun gol în jurul lui (±5 min) s-a refăcut singur.
  * lanțuri de noapte – `lant_zilnic` la 00:15 și `lant_cor` la 03:30 prelucrează ziua precedentă. Fiecare e așteptat
    pentru fiecare zi, de la prima zi cu stare.json (dar nu dinaintea începutului colectării) până la ultima noapte
    programată înaintea tăieturii. Încheiat = rezultatul „gata” (sau „gata_fara_simulari”, la zilele sigilate, § 9.11), toți
    pașii cu codul 0 și ultimul pas încheiat înaintea tăieturii.
  * vehicule – rândurile `intrare` (vehicule intrate pe un braț: autoturisme, autobuze și troleibuze, camioane,
    motociclete, biciclete) din intervalele de 15 min încheiate în fereastră; o probă încheiată înaintea începutului nu
    intră. Sunt numerele detectate, fără factorii de corecție (§ 4.3). Fișierul zilei curente e cel live: noaptea îl
    înlocuiește renumărarea, deci cifrele acelei zile se pot schimba o dată. Pietonii: doar totalul zilei (rândurile
    `pietoni`).

Exemple:
  python -m romana.vision.fisa_senzor --pana-la "2026-11-05 20:25:31"
  python -m romana.vision.fisa_senzor --pana-la "2026-11-08 07:00" --out-json fisa.json --out-md fisa.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from datetime import time as ora_din_zi
from pathlib import Path

from romana.common import COUNTS_DIR, OUTPUT_DIR, ROOT

LOG_DIR = OUTPUT_DIR / "logs"
# lanțurile de noapte: dosarul și ora la care pornesc (lant_zilnic.ORA_IMPLICITA; lant_cor, --ora implicit)
LANTURI = {"lant": (OUTPUT_DIR / "lant", ora_din_zi(0, 15)), "lant_cor": (OUTPUT_DIR / "lant_cor", ora_din_zi(3, 30))}

STARE_PROASPATA = 2.5    # s; ca veghe.PAUZA: o stare mai veche înseamnă o pauză în curs, iar `fps` e cel de dinaintea ei
EPISOD = 120             # s; ca veghe.EPISOD: creșterile contorului mai apropiate fac parte din același episod
MARJA_ANUNT = 600        # s înaintea ultimei dovezi de viață în care o notă „oprire anunțată” încă privește golul
MARJA_PORNIRE = 120      # s după repornire în care o pornire încă ține de gol (ora rândului poate fi cea dinaintea pornirii)
MARJA_REFACUT = 300      # s în jurul unui episod de reconectare în care un gol ar însemna că nu s-a refăcut singur
TACERE_VEGHE = 180       # s fără rând al vegherii înaintea tăieturii de la care se avertizează (veghe.STARE_VECHE)
FARA_CADRE_S = 180       # s fără cadre după care veghea dă alerta „fără cadre” (veghe.STARE_VECHE); doar dacă semnul n-o are
STARE_LIVE_MAX_S = 86400  # s; o oră a stării live mai veche decât atât față de alertă nu se crede (alerta minus semnul)
TRUNCHIERE_PAUZA = 1     # s; ora unei pauze e trunchiată la secundă (veghe._eveniment): pauza aceluiași gol începe atunci
MARJA_OPRIRE = 5         # s; o cădere care începe cu atât înaintea unei opriri ține de ea: amândouă pornesc de la ultima stare
GATA = ("gata", "gata_fara_simulari")    # rezultatele unui lanț încheiat (zilele sigilate: fără simulări, § 9.11)
CLASE = {"passenger": "autoturisme", "bus": "autobuze și troleibuze", "truck": "camioane",
         "motorcycle": "motociclete", "bicycle": "biciclete"}
ZILE_SAPTAMANA = ("lun.", "mar.", "mie.", "joi", "vin.", "sâm.", "dum.")

RAND_PAZNIC = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) (.*)$")
ANUNT = re.compile(r"oprire anun[țţt]at[ăa]")
REPORNIRE = re.compile(r"^repornire, încercarea (\d+): (.*)$")
PORNIRE_PAZNIC = re.compile(r"pornit: lansatorul are PID \d+; jurnale (viziune_[^,;\s]+\.log)")
EVENIMENT = re.compile(r"(\d{2}):(\d{2}):(\d{2}) f[ăa]r[ăa] cadre (\d+) s")
SEMN_FARA_CADRE = re.compile(r"f[ăa]r[ăa] cadre\b")    # la începutul semnului: „fără cadre: niciun cadru prelucrat de N s”
SECUNDE_SEMN = re.compile(r"\bde (\d+) s\b")
NUME_ZI = re.compile(r"\d{4}-\d{2}-\d{2}")

DEFINITII = {
    "inceput": "ultima pornire a colectării dinaintea tăieturii (data creării unui viziune_*.log) care nu e o repornire "
               "peste un gol din reporniri_*.csv",
    "randuri_veghe": "rândurile al căror minut a început după început și s-a încheiat până la tăietură",
    "oprire": "un gol din reporniri_*.csv (ultima dovadă de viață → prima traiectorie nouă), tăiat la fereastră; anunțat "
              "dacă paznicul a notat „oprire anunțată” între 10 min înaintea opririi și repornire",
    "pauza": "un gol de cel puțin 10 s între două cadre prelucrate, din coloana `evenimente` a vegherii, care nu atinge o "
             "oprire și nu începe într-o cădere a sursei",
    "cadere_sursa": "un gol al fluxului care a oprit veghea cu alerta „fără cadre” (veghe_alerta_*.json) cât colectarea "
                    "era pornită: de la ultimul cadru dinaintea alertei până la primul semn de cadre (o pauză, o repornire "
                    "sau începutul primului minut cu un rând al vegherii cu starea proaspătă; o margine de sus) sau până la "
                    "tăietură, în afara opririlor și a pauzelor; doar cu cel puțin o secundă acolo",
    "minut_cu_cadre": "minut întreg din fereastră care nu stă în întregime într-o oprire, într-o pauză sau într-o cădere a "
                      "sursei",
    "cadre_pe_secunda": "mediana coloanei `fps` pe rândurile din fereastră cu vârsta stării sub 2,5 s",
    "reconectari": "creșterile contorului colectării (pierderi ale fluxului și încercări eșuate de redeschidere), pe toate "
                   "rulările; episod = creșteri la cel mult 2 min una de alta",
    "lanturi": "o rulare pe zi, de la prima zi cu stare.json până la ultima noapte programată înaintea tăieturii; încheiată "
               "= rezultat gata / gata_fara_simulari, toți pașii cu codul 0, încheiată înaintea tăieturii",
    "vehicule": "rândurile `intrare` din intervalele încheiate în fereastră, detectate, fără factori de corecție; "
                "pietonii doar ca total pe zi",
}


@dataclass
class RandVeghe:
    t: float                     # începutul minutului din coloana `ora`; rândul se scrie în cursul acestui minut
    fps: float | None
    varsta: float | None         # vârsta stării live la scrierea rândului, s
    reconectari: int | None      # contorul colectării
    evenimente: str


@dataclass
class Gol:
    oprire: float                # ultima dovadă de viață a colectării
    repornire: float             # prima traiectorie nouă (sau, până se află, momentul pornirii)
    anuntat: bool = False
    motiv: str = ""              # motivul repornirii, din jurnalul paznicului


@dataclass
class Cadere:
    inceput: float               # ultimul cadru dinaintea alertei „fără cadre”
    sfarsit: float | None        # începutul primului minut de după alertă cu starea proaspătă; None = niciunul până acum
    alerte: list[float] = field(default_factory=list)       # orele alertelor care țin de ea


@dataclass
class JurnalPaznic:
    anunturi: list[float] = field(default_factory=list)       # orele notelor „oprire anunțată”
    reporniri: list[tuple[float, int, str]] = field(default_factory=list)   # (ora, încercarea, motivul)
    porniri: dict[str, float] = field(default_factory=dict)   # jurnalul viziune_*.log al unei porniri → ora notei


# ---------------------------------------------------------------------------------------------- citirea
def ora(text: str) -> float:
    """O oră locală ISO (AAAA-LL-ZZ HH:MM[:SS], cu spațiu sau T) ca marcaj de timp."""
    return datetime.fromisoformat(text.strip()).timestamp()


def _numar(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _intreg(x) -> int | None:
    v = _numar(x)
    return None if v is None else int(v)


def _citeste_text(f: Path, incercari: int = 3) -> str | None:
    """Conținutul unui fișier, sau None dacă lipsește. Pe Windows, un fișier tocmai înlocuit atomic (reporniri_*.csv) poate
    refuza o clipă deschiderea: se mai încearcă."""
    for k in range(incercari):
        try:
            return f.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None
        except PermissionError:
            if k == incercari - 1:
                raise
            time.sleep(0.2)
    return None


def _citeste_csv(f: Path) -> list[dict]:
    text = _citeste_text(f)
    return [] if text is None else list(csv.DictReader(text.splitlines()))


def citeste_veghe(fisiere) -> tuple[list[RandVeghe], int]:
    """Rândurile CSV-urilor vegherii, în ordinea minutelor, și câte rânduri dublate s-au lăsat deoparte (un minut scris de
    două vegheri deodată se ia o singură dată). Un rând fără `ora` sau scris pe jumătate se sare."""
    pe_minut, dublate = {}, 0
    for f in fisiere:
        for r in _citeste_csv(Path(f)):
            try:
                t = datetime.strptime((r.get("ora") or "").strip(), "%Y-%m-%d %H:%M").timestamp()
            except ValueError:
                continue
            if t in pe_minut:
                dublate += 1
                continue
            pe_minut[t] = RandVeghe(t, _numar(r.get("fps")), _numar(r.get("varsta_stare_s")),
                                    _intreg(r.get("reconectari")), r.get("evenimente") or "")
    return [pe_minut[t] for t in sorted(pe_minut)], dublate


def pauze_din(randuri: list[RandVeghe]) -> list[tuple[float, int]]:
    """(începutul, durata) pauzelor notate de veghe, fiecare o dată. Evenimentul dă doar ora din zi: ziua e a rândului, afară
    de o pauză începută înaintea miezului nopții și scrisă după el. Mai multe evenimente într-un rând se despart cu „; ”,
    dar textul unuia conține și el „; ”: de aceea se caută tiparul fiecăruia, nu despărțitorul."""
    vazute = {}
    for r in randuri:
        zi = date.fromtimestamp(r.t)
        for m in EVENIMENT.finditer(r.evenimente):
            h, mi, s, d = map(int, m.groups())
            try:
                t = datetime.combine(zi, ora_din_zi(h, mi, s)).timestamp()
                if t > r.t + 60:
                    t = datetime.combine(zi - timedelta(days=1), ora_din_zi(h, mi, s)).timestamp()
            except ValueError:
                continue
            vazute.setdefault(t, d)
    return sorted(vazute.items())


def citeste_goluri(loguri: Path) -> list[Gol]:
    """Golurile din reporniri_*.csv, fiecare o dată, în ordine. Rândurile care se suprapun (același gol, cu repornirea
    scrisă întâi la pornire, apoi la prima traiectorie) se unesc; un rând cu repornirea înaintea opririi se sare, ca în
    lanțul zilnic."""
    perechi = set()
    for f in sorted(loguri.glob("reporniri_*.csv")):
        for r in _citeste_csv(f):
            try:
                a, b = ora(r["oprire"]), ora(r["repornire"])
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            if b >= a:
                perechi.add((a, b))
    goluri: list[Gol] = []
    for a, b in sorted(perechi):
        if goluri and a <= goluri[-1].repornire:
            goluri[-1].repornire = max(goluri[-1].repornire, b)
        else:
            goluri.append(Gol(a, b))
    return goluri


def citeste_caderi(loguri: Path, randuri: list[RandVeghe], goluri: list[Gol] = ()) -> list[Cadere]:
    """Căderile sursei, în ordine: una pentru fiecare alertă „fără cadre” din veghe_alerta_*.json, unite cele care se
    suprapun (o veghe pornită din nou cât fluxul încă lipsește dă o alertă nouă pentru același gol). Începutul e ora stării
    live din alertă, dacă nu e după alertă și nici mai veche de STARE_LIVE_MAX_S față de ea, altfel ora alertei minus
    secundele din semn. Sfârșitul e primul semn de cadre de după început (`randuri`, în ordinea minutelor; `goluri`, din
    reporniri): sigur – capătul pauzei aceluiași gol (o veghe care n-a dat alerta, pornită cu --fara, o notează când revin
    cadrele), începutul unei pauze de după alertă sau repornirea unei opriri care începe după început (prima traiectorie
    nouă) – ori, dacă vine mai devreme cu cel puțin un minut, începutul primului minut de după alertă cu un rând al vegherii
    cu starea proaspătă; fără niciunul, None (până la tăietură). O pauză care începe în cădere și se încheie după ea o
    lărgește. O cădere care începe într-o oprire sau cu cel mult MARJA_OPRIRE s înaintea ei ține de oprire (amândouă pornesc
    de la ultima stare): colectarea s-a blocat sau s-a oprit, nu fluxul. Un fișier de altă formă și o alertă de alt fel se
    sar; unul care nu se poate deschide oprește fișa, ca la celelalte jurnale."""
    pauze = pauze_din(randuri)
    caderi: list[Cadere] = []
    for f in sorted(Path(loguri).glob("veghe_alerta_*.json")):
        text = _citeste_text(f)
        try:
            d = json.loads(text or "")
            alerta = ora(d["ora"])
            semn = next(s for s in d["semne"] if isinstance(s, str) and SEMN_FARA_CADRE.match(s))
            live = d.get("stare_live")
            inceput = _numar(live.get("timestamp")) if isinstance(live, dict) else None
            if inceput is None or not alerta - STARE_LIVE_MAX_S <= inceput <= alerta:
                m = SECUNDE_SEMN.search(semn)
                inceput = alerta - (int(m.group(1)) if m else FARA_CADRE_S)
            datetime.fromtimestamp(inceput)          # o oră din afara calendarului: OSError, OverflowError sau ValueError
        except (ValueError, TypeError, KeyError, AttributeError, StopIteration, OSError, OverflowError, RecursionError):
            continue
        if any(g.oprire - MARJA_OPRIRE <= inceput < g.repornire for g in goluri):
            continue
        sigure = [*(max(a, inceput) + d for a, d in pauze if abs(a - inceput) <= TRUNCHIERE_PAUZA),
                  *(a for a, _ in pauze if a >= alerta and abs(a - inceput) > TRUNCHIERE_PAUZA),
                  *(g.repornire for g in goluri if g.oprire > inceput)]
        sigur = min((x for x in sigure if x > inceput), default=None)
        rand = next((max(r.t, alerta) for r in randuri
                     if r.t + 60 > alerta and (r.varsta is None or r.varsta < STARE_PROASPATA)), None)
        sfarsit = rand if sigur is None or (rand is not None and rand + 60 <= sigur) else sigur
        if sfarsit is not None:
            sfarsit = max([sfarsit, *(a + d for a, d in pauze if inceput - TRUNCHIERE_PAUZA <= a < sfarsit)])
        caderi.append(Cadere(inceput, sfarsit, [alerta]))
    unite: list[Cadere] = []
    for c in sorted(caderi, key=lambda x: x.inceput):
        u = unite[-1] if unite else None
        if u is not None and (u.sfarsit is None or c.inceput <= u.sfarsit):
            u.sfarsit = None if u.sfarsit is None or c.sfarsit is None else max(u.sfarsit, c.sfarsit)
            u.alerte += c.alerte
        else:
            unite.append(c)
    return unite


def citeste_paznic(loguri: Path) -> JurnalPaznic:
    """Notele paznicului care contează aici; rândurile unei erori (urma apelurilor) nu încep cu ora și se sar."""
    j = JurnalPaznic()
    for f in sorted(loguri.glob("paznic_*.log")):
        for rand in (_citeste_text(f) or "").splitlines():
            m = RAND_PAZNIC.match(rand)
            if not m:
                continue
            try:
                t = ora(m.group(1))
            except ValueError:
                continue
            text = m.group(2)
            if ANUNT.search(text):
                j.anunturi.append(t)
            elif r := REPORNIRE.match(text):
                j.reporniri.append((t, int(r.group(1)), r.group(2).strip()))
            elif p := PORNIRE_PAZNIC.search(text):
                j.porniri[p.group(1)] = t
    j.anunturi.sort()
    j.reporniri.sort()
    return j


def data_crearii(f: Path) -> float | None:
    """Data creării unui fișier (Windows, Python ≥ 3.12: st_birthtime); None dacă sistemul nu o păstrează."""
    try:
        return getattr(f.stat(), "st_birthtime", None)
    except OSError:
        return None


def porniri_colectare(loguri: Path, nastere=data_crearii) -> list[tuple[float, str]]:
    """(ora, numele) pornirilor colectării: fiecare rulare își deschide jurnalul viziune_<data>[_<ora>].log la pornire."""
    out = []
    for f in loguri.glob("viziune_*.log"):
        t = nastere(f)
        if t is not None:
            out.append((float(t), f.name))
    return sorted(out)


def inceputul(porniri: list[tuple[float, str]], goluri: list[Gol], pornite_de_paznic: dict[str, float],
              taietura: float) -> tuple[float, str] | None:
    """Ultima pornire de dinaintea tăieturii care nu e o repornire: nici numită de paznic în nota pornirii, nici în golul
    unui rând din reporniri_*.csv (până la MARJA_PORNIRE după repornire). None dacă nu se găsește niciuna."""
    for t, nume in reversed(porniri):
        if t > taietura or nume in pornite_de_paznic:
            continue
        if any(g.oprire <= t <= g.repornire + MARJA_PORNIRE for g in goluri):
            continue
        return t, nume
    return None


def clasifica_goluri(goluri: list[Gol], j: JurnalPaznic) -> None:
    """Anunțat sau nu, și motivul repornirii paznicului din golul respectiv."""
    for g in goluri:
        g.anuntat = any(g.oprire - MARJA_ANUNT <= t <= g.repornire for t in j.anunturi)
        motive = [m for t, _, m in j.reporniri if g.oprire <= t <= g.repornire + MARJA_PORNIRE]
        g.motiv = motive[0] if motive else ""


# ---------------------------------------------------------------------------------------------- socotelile
def minute_intregi(t0: float, t1: float) -> range:
    """Minutele întregi din [t0, t1], ca indici m ai intervalelor [60m, 60m + 60)."""
    return range(math.ceil(t0 / 60), max(math.ceil(t0 / 60), math.floor(t1 / 60)))


def minute_in(a: float, b: float, minute: range) -> range:
    """Minutele din `minute` care stau în întregime în intervalul [a, b]."""
    return range(max(minute.start, math.ceil(a / 60)), min(minute.stop, math.floor(b / 60)))


def _taie(a: float, b: float, t0: float, t1: float) -> float:
    return max(0.0, min(b, t1) - max(a, t0))


def _uneste(intervale) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in sorted(intervale):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def secunde_in_afara(intervale, scoase) -> float:
    """Câte secunde acoperă `intervale`, unite, în afara intervalelor `scoase` (amândouă perechi (a, b))."""
    scoase = _uneste(scoase)
    return sum(b - a - sum(_taie(x, y, a, b) for x, y in scoase) for a, b in _uneste(intervale))


def reconectari(randuri: list[RandVeghe], porniri: list[tuple[float, str]], goluri: list[Gol], t0: float,
                t1: float) -> list[tuple[float, int]]:
    """(minutul, creșterea) contorului colectării, pe rândurile din fereastră. Contorul o ia de la 0 la fiecare rulare:
    după o pornire sau o repornire (sau o scădere a contorului), creșterea e chiar valoarea nouă. O pornire ține de
    rândurile de după minutul ei: rândul minutului în care a pornit se scrie, de obicei, înaintea ei (veghea se oprește
    odată cu colectarea, deci în realitate pornirea cade într-un gol al vegherii). Rândurile de dinaintea ferestrei dau doar
    valoarea de la care se pornește."""
    momente = sorted({60 * math.floor(t / 60) for t in [*(t for t, _ in porniri), *(g.repornire for g in goluri)]})
    out, prev = [], None
    for r in randuri:
        if r.reconectari is None:
            continue
        rulare_noua = prev is None or r.reconectari < prev[1] or any(prev[0] <= m < r.t for m in momente)
        n = r.reconectari - (0 if rulare_noua else prev[1])
        if n > 0 and r.t >= t0 and r.t + 60 <= t1:
            out.append((r.t, n))
        prev = (r.t, r.reconectari)
    return out


def episoade(cresteri: list[tuple[float, int]]) -> list[tuple[float, float, int]]:
    """(primul minut, ultimul minut, creșterile) pe episoade: creșteri la cel mult EPISOD s una de alta."""
    out: list[list] = []
    for t, n in cresteri:
        if out and t - out[-1][1] <= EPISOD:
            out[-1][1], out[-1][2] = t, out[-1][2] + n
        else:
            out.append([t, t, n])
    return [tuple(e) for e in out]


def stare_lant(f: Path, t1: float) -> dict:
    """Starea unei rulări de noapte la tăietură: incheiat, in_curs, esuat, neinceput, lipsa sau necitibil."""
    try:
        text = _citeste_text(f)
        s = None if text is None else json.loads(text)
    except (OSError, ValueError):
        return {"stare": "necitibil"}
    if s is None:
        return {"stare": "lipsa"}
    if not isinstance(s, dict):
        return {"stare": "necitibil"}
    pasi = {k: v for k, v in (s.get("pasi") or {}).items() if isinstance(v, dict)}
    ore = [x for v in pasi.values() for x in (v.get("inceput"), v.get("sfarsit")) if x]
    try:
        pornit = ora(s["pornit"]) if s.get("pornit") else (min(map(ora, ore)) if ore else None)
        sfarsit = max(map(ora, [x for x in [*ore, s.get("actualizat")] if x]), default=None)
    except ValueError:
        return {"stare": "necitibil"}
    rezultat, coduri = s.get("rezultat") or "", [v.get("cod") for v in pasi.values()]
    out = {"rezultat": rezultat, "pasi": len(pasi), "coduri_nenule": sum(c != 0 for c in coduri),
           "pornit": datetime.fromtimestamp(pornit).isoformat(timespec="seconds") if pornit else None,
           "incheiat_la": datetime.fromtimestamp(sfarsit).isoformat(timespec="seconds") if sfarsit else None}
    if pornit is not None and pornit > t1:
        out["stare"] = "neinceput"
    elif rezultat == "in_curs" or (sfarsit is not None and sfarsit > t1):
        out["stare"] = "in_curs"
    elif rezultat in GATA and coduri and all(c == 0 for c in coduri):
        out["stare"] = "incheiat"
    else:
        out["stare"] = "esuat"
    return out


def lanturi_noapte(lanturi: dict, t0: float, t1: float) -> dict:
    out = {}
    for nume, (dosar, la_ora) in lanturi.items():
        dosar = Path(dosar)
        zile = sorted(p.name for p in dosar.glob("*") if NUME_ZI.fullmatch(p.name) and (p / "stare.json").exists()) \
            if dosar.exists() else []
        zile = [z for z in zile if z >= date.fromtimestamp(t0).isoformat()]
        asteptate = {}
        if zile:
            z = date.fromisoformat(zile[0])
            while datetime.combine(z + timedelta(days=1), la_ora).timestamp() <= t1:
                asteptate[z.isoformat()] = stare_lant(dosar / z.isoformat() / "stare.json", t1)
                z += timedelta(days=1)
        numar = defaultdict(int)
        for v in asteptate.values():
            numar[v["stare"]] += 1
        out[nume] = {"ora": la_ora.strftime("%H:%M"), "asteptate": len(asteptate),
                     "incheiate": numar.get("incheiat", 0), "pe_stari": dict(numar), "zile": asteptate}
    return out


def numaratori(dosar: Path, t0: float, t1: float) -> dict:
    """Intrările de vehicule pe clase și pietonii, pe zile, din intervalele încheiate în fereastră."""
    zile = {}
    # fișierele sunt pe ziua în care începe intervalul, iar un interval din fereastră începe înaintea tăieturii: ultima zi e
    # cea a clipei de dinaintea ei. La o tăietură fix la miezul nopții, ziua care abia începe n-are niciun interval încheiat
    # până la ea, deci nici rând (fișa de la M2, cu tăietura 06.11, 00:00, avea „vin. 06.11” numai cu zerouri).
    z, z1 = date.fromtimestamp(t0), (datetime.fromtimestamp(t1) - timedelta(microseconds=1)).date()
    while z <= z1:
        f = Path(dosar) / f"numaratori_{z.isoformat()}.csv"
        veh, pietoni, intervale = defaultdict(int), 0, set()
        for r in _citeste_csv(f):
            try:
                a, b, n = ora(r["inceput"]), ora(r["sfarsit"]), int(r["numar"])
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            if not t0 < b <= t1:
                continue
            intervale.add((a, b))
            if r.get("tip") == "intrare":
                veh[r.get("vehicul") or "?"] += n
            elif r.get("tip") == "pietoni":
                pietoni += n
        zile[z.isoformat()] = {
            "fisier": f.name if f.exists() else None, "intervale": len(intervale),
            "de_la": datetime.fromtimestamp(max(t0, min(a for a, _ in intervale))).isoformat(timespec="seconds")
            if intervale else None,
            "pana_la": datetime.fromtimestamp(max(b for _, b in intervale)).isoformat(timespec="seconds")
            if intervale else None,
            "vehicule": sum(veh.values()), "pe_clase": dict(sorted(veh.items(), key=lambda kv: -kv[1])),
            "pietoni": pietoni}
        z += timedelta(days=1)
    clase = defaultdict(int)
    for v in zile.values():
        for k, n in v["pe_clase"].items():
            clase[k] += n
    return {"pe_zile": zile, "total": sum(v["vehicule"] for v in zile.values()),
            "pe_clase": dict(sorted(clase.items(), key=lambda kv: -kv[1])),
            "pietoni_total": sum(v["pietoni"] for v in zile.values())}


def iso(t: float | None) -> str | None:
    return None if t is None else datetime.fromtimestamp(t).isoformat(timespec="seconds")


def _rel(f: Path) -> str:
    try:
        return Path(f).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(f)


def fisa(taietura: float, de_la: float | None = None, loguri: Path = LOG_DIR, veghe: list[Path] | None = None,
         lanturi: dict | None = None, dosar_numaratori: Path = COUNTS_DIR, nastere=data_crearii) -> dict:
    """Toate cifrele fișei, la tăietura dată. `veghe` = CSV-urile vegherii (implicit toate veghe_*.csv din `loguri`);
    `nastere` = cum se află data creării unui jurnal (înlocuită în teste). Un ValueError dacă începutul nu se poate afla
    sau nu e înaintea tăieturii."""
    loguri = Path(loguri)
    fis_veghe = sorted(veghe if veghe is not None else loguri.glob("veghe_*.csv"))
    goluri, paznic = citeste_goluri(loguri), citeste_paznic(loguri)
    clasifica_goluri(goluri, paznic)
    porniri = porniri_colectare(loguri, nastere)
    if de_la is not None:
        t0, sursa = de_la, "dat cu --de-la"
    else:
        gasit = inceputul(porniri, goluri, paznic.porniri, taietura)
        if gasit is None:
            raise ValueError("începutul colectării nu se poate afla din datele de creare ale jurnalelor viziune_*.log; "
                             "dați-l cu --de-la")
        t0, sursa = gasit[0], f"data creării lui {gasit[1]}"
    t1 = taietura
    if t1 <= t0:
        raise ValueError(f"tăietura ({iso(t1)}) nu e după început ({iso(t0)})")

    # opririle, căderile sursei și pauzele din fereastră
    goluri_fer = [g for g in goluri if _taie(g.oprire, g.repornire, t0, t1) > 0]
    toate_randurile, dublate = citeste_veghe(fis_veghe)
    # o cădere fără sfârșit încă ține până la tăietură
    caderi = [(c, c.inceput, math.inf if c.sfarsit is None else c.sfarsit)
              for c in citeste_caderi(loguri, toate_randurile, goluri)]
    opriri_fer = [(max(g.oprire, t0), min(g.repornire, t1)) for g in goluri_fer]
    # o pauză încă în curs la tăietură se numără până la ea, în secunde întregi; una care începe într-o cădere ține de ea
    # (ora pauzei e trunchiată la secundă, iar durata rotunjită: una încheiată chiar la începutul căderii rămâne pauză)
    pauze = [(a, min(d, math.floor(t1 - a))) for a, d in pauze_din(toate_randurile)
             if t0 <= a < t1 and not any(a < g.repornire and a + d > g.oprire for g in goluri)
             and not any(ca - TRUNCHIERE_PAUZA <= a < cb for _, ca, cb in caderi)]
    # timpul fără cadre e reuniunea: o cădere se socotește în afara opririlor și a pauzelor și contează doar cu cel puțin
    # o secundă acolo (partea ei din fereastră poate sta toată într-o oprire)
    alte = opriri_fer + [(a, a + d) for a, d in pauze]
    caderi_fer = [(c, a, b, s) for c, a, b in ((c, max(a, t0), min(b, t1)) for c, a, b in caderi)
                  if b > a and (s := secunde_in_afara([(a, b)], alte)) >= 1]
    minute = minute_intregi(t0, t1)
    fara = set()
    for a, b in alte + [(a, b) for _, a, b, _ in caderi_fer]:
        fara.update(minute_in(a, b, minute))
    oprit_s = sum(b - a for a, b in opriri_fer)
    pauze_s = sum(d for _, d in pauze)
    caderi_s = secunde_in_afara([(a, b) for _, a, b, _ in caderi_fer], alte)
    durata = t1 - t0

    # rândurile vegherii din fereastră: cadrele pe secundă și reconectările
    randuri = [r for r in toate_randurile if r.t >= t0 and r.t + 60 <= t1]
    proaspete = [r.fps for r in randuri if r.fps and (r.varsta is None or r.varsta < STARE_PROASPATA)]
    toate_fps = [r.fps for r in randuri if r.fps]
    etichete = {int(r.t // 60) for r in randuri}
    fara_rand = sum(1 for m in minute if m not in fara and m not in etichete)
    cresteri = reconectari(toate_randurile, porniri, goluri, t0, t1)
    ep = episoade(cresteri)
    refacute = sum(1 for a, b, _ in ep
                   if not any(a - MARJA_REFACUT <= g.oprire <= b + 60 + MARJA_REFACUT for g in goluri))
    tacere = t1 - (randuri[-1].t + 60) if randuri else None

    anuntate = [g for g in goluri_fer if g.anuntat]
    neprevazute = [g for g in goluri_fer if not g.anuntat]
    reporniri_fer = [x for x in paznic.reporniri if t0 <= x[0] <= t1]
    lant = lanturi_noapte(LANTURI if lanturi is None else lanturi, t0, t1)
    num = numaratori(dosar_numaratori, t0, t1)
    citite = [*fis_veghe, *sorted(loguri.glob("reporniri_*.csv")), *sorted(loguri.glob("paznic_*.log")),
              *sorted(loguri.glob("veghe_alerta_*.json")), *[loguri / n for _, n in porniri]]

    return {
        "taietura": iso(t1), "inceput": iso(t0), "sursa_inceputului": sursa,
        "durata": {"ore": round(durata / 3600, 2), "secunde": round(durata)},
        "minute": {"intregi": len(minute), "cu_cadre": len(minute) - len(fara), "fara_cadre": len(fara),
                   "pondere_cu_cadre": round((len(minute) - len(fara)) / len(minute), 5) if len(minute) else None,
                   "fara_rand_veghe": fara_rand},
        "timp": {"oprit_s": round(oprit_s), "pauze_s": round(pauze_s), "caderi_s": round(caderi_s),
                 "pondere_colectare_pornita": round(1 - oprit_s / durata, 5),
                 "pondere_cu_cadre": round(1 - (oprit_s + pauze_s + caderi_s) / durata, 5)},
        "veghe": {"randuri": len(randuri), "randuri_dublate_lasate": dublate,
                  "primul": iso(randuri[0].t) if randuri else None, "ultimul": iso(randuri[-1].t) if randuri else None,
                  "tacere_inainte_de_taietura_s": None if tacere is None else round(tacere)},
        "cadre_pe_secunda": {"mediana": round(statistics.median(proaspete), 2) if proaspete else None,
                             "randuri": len(proaspete),
                             "mediana_toate_randurile": round(statistics.median(toate_fps), 2) if toate_fps else None,
                             "media": round(statistics.fmean(proaspete), 2) if proaspete else None,
                             "minim": min(proaspete, default=None), "maxim": max(proaspete, default=None)},
        "pauze": {"numar": len(pauze), "durata_s": round(pauze_s),
                  "cea_mai_lunga_s": max((d for _, d in pauze), default=None),
                  "mediana_s": statistics.median([d for _, d in pauze]) if pauze else None,
                  "lista": [{"inceput": iso(a), "durata_s": d} for a, d in pauze]},
        "caderi_sursa": {"numar": len(caderi_fer), "durata_s": round(caderi_s),
                         "lista": [{"inceput": iso(a), "sfarsit": iso(b), "durata_s": round(s),
                                    "alerte": [iso(x) for x in c.alerte],
                                    "in_curs_la_taietura": c.sfarsit is None or c.sfarsit > t1}
                                   for c, a, b, s in caderi_fer]},
        "reconectari": {"cresteri_contor": sum(n for _, n in cresteri), "episoade": len(ep), "refacute_singure": refacute,
                        "lista": [{"de_la": iso(a), "pana_la": iso(b), "cresteri": n} for a, b, n in ep]},
        "opriri": {"anuntate": len(anuntate), "caderi_neprevazute": len(neprevazute),
                   "durata_s": round(oprit_s),
                   "lista": [{"oprire": iso(g.oprire), "repornire": iso(g.repornire),
                              "durata_s": round(_taie(g.oprire, g.repornire, t0, t1)), "anuntata": g.anuntat,
                              "motivul_repornirii": g.motiv} for g in goluri_fer]},
        "reporniri_paznic": {"numar": len(reporniri_fer),
                             "lista": [{"ora": iso(t), "incercarea": k, "motiv": m} for t, k, m in reporniri_fer]},
        "lanturi": {**lant, "total": {"asteptate": sum(v["asteptate"] for v in lant.values()),
                                      "incheiate": sum(v["incheiate"] for v in lant.values())}},
        "vehicule": num,
        "definitii": DEFINITII,
        "fisiere_citite": [*sorted({_rel(f) for f in citite}),
                           *(f"{_rel(Path(d))}/<zi>/stare.json" for d, _ in (lanturi or LANTURI).values()),
                           f"{_rel(Path(dosar_numaratori))}/numaratori_<zi>.csv"],
    }


# ---------------------------------------------------------------------------------------------- ce se scrie
def nr(x: float | None, zec: int = 0) -> str:
    """Un număr în scrierea românească: virgulă zecimală, spațiu între mii."""
    if x is None:
        return "–"
    return f"{x:,.{zec}f}".replace(",", " ").replace(".", ",")


def pct(x: float | None, zec: int = 1) -> str:
    return "–" if x is None else nr(100 * x, zec) + "%"


def durata_text(s: float) -> str:
    s = round(s)
    z, h, m, sec = s // 86400, s % 86400 // 3600, s % 3600 // 60, s % 60
    parti = [f"{h} h"] if h else []
    parti += [f"{m} min"] if m else []
    parti += [f"{sec} s"] if sec and not z else []
    if z:
        return f"{z} {'zi' if z == 1 else 'zile'}" + (", " + " ".join(parti) if parti else "")
    return " ".join(parti) or "0 s"


def ora_text(text: str | None) -> str:
    return "–" if not text else datetime.fromisoformat(text).strftime("%d.%m.%Y %H:%M:%S")


def zi_text(zi: str) -> str:
    d = date.fromisoformat(zi)
    return f"{ZILE_SAPTAMANA[d.weekday()]} {d:%d.%m}"


def ore_zi(x: dict, zi: str) -> str:
    """Primul și ultimul moment numărat într-o zi, HH:MM–HH:MM (sfârșitul zilei: 24:00)."""
    a, b = datetime.fromisoformat(x["de_la"]), datetime.fromisoformat(x["pana_la"])
    return f"{a:%H:%M}–" + ("24:00" if b.date() > date.fromisoformat(zi) else f"{b:%H:%M}")


def _clase_text(pe_clase: dict) -> str:
    return ", ".join(f"{CLASE.get(k, k)} {nr(n)}" for k, n in pe_clase.items())


def _caderi_text(cs: dict | None) -> str:
    """Numărul căderilor sursei și durata lor, o margine de sus (§ 4.6); o fișă dinaintea lor n-are câmpul."""
    if not cs:
        return "nesocotite în această fișă"
    if not cs["numar"]:
        return "0"
    in_curs = sum(1 for x in cs["lista"] if x["in_curs_la_taietura"])
    return (f"{nr(cs['numar'])}, în total cel mult {durata_text(cs['durata_s'])}"
            + (f" ({'una' if in_curs == 1 else nr(in_curs)} în curs la tăietură)" if in_curs else ""))


def _lanturi_text(lant: dict) -> str:
    parti = []
    for k, v in lant.items():
        if k == "total":
            continue
        rest = {s: n for s, n in v["pe_stari"].items() if s != "incheiat"}
        parti.append(f"{k} {v['incheiate']}/{v['asteptate']}" + (f" ({', '.join(f'{s}: {n}' for s, n in rest.items())})"
                                                                  if rest else ""))
    return ", ".join(parti)


def rezumat(f: dict) -> str:
    """Rezumatul de un ecran."""
    m, t, c, p, r, o, lt, v = (f["minute"], f["timp"], f["cadre_pe_secunda"], f["pauze"], f["reconectari"], f["opriri"],
                               f["lanturi"], f["vehicule"])
    randuri = [
        f"Fișa senzorului: colectarea de la cameră, până la {ora_text(f['taietura'])}",
        f"  începutul colectării           {ora_text(f['inceput'])} ({f['sursa_inceputului']})",
        f"  timp scurs                     {nr(f['durata']['ore'], 2)} h ({durata_text(f['durata']['secunde'])})",
        f"  minute cu cadre prelucrate     {nr(m['cu_cadre'])} din {nr(m['intregi'])} ({pct(m['pondere_cu_cadre'], 2)}); "
        f"colectarea pornită {pct(t['pondere_colectare_pornita'], 2)} din timp",
        f"  cadre analizate pe secundă     mediana {nr(c['mediana'], 2)} ({nr(c['randuri'])} minute cu starea proaspătă)",
        f"  pauze fără cadre, de ≥ 10 s    {nr(p['numar'])}, în total {durata_text(p['durata_s'])}"
        + (f"; cea mai lungă {nr(p['cea_mai_lunga_s'])} s, mediana {nr(p['mediana_s'])} s" if p["numar"] else ""),
        f"  căderi ale sursei camerei      {_caderi_text(f.get('caderi_sursa'))}",
        f"  reconectări la fluxul camerei  {nr(r['episoade'])} episoade ({nr(r['cresteri_contor'])} creșteri ale "
        f"contorului), refăcute singure: {nr(r['refacute_singure'])}",
        f"  opriri                         {nr(o['anuntate'])} anunțate, {nr(o['caderi_neprevazute'])} căderi neprevăzute"
        f" ({durata_text(o['durata_s'])} oprit); reporniri ale paznicului: {nr(f['reporniri_paznic']['numar'])}",
        f"  lanțuri de noapte              {nr(lt['total']['incheiate'])} din {nr(lt['total']['asteptate'])} încheiate "
        f"cu codul 0 ({_lanturi_text(lt)})",
        f"  vehicule intrate (detectate)   {nr(v['total'])}: {_clase_text(v['pe_clase'])}",
    ]
    for zi, x in v["pe_zile"].items():
        randuri.append(f"    {zi_text(zi):<10} {nr(x['vehicule']):>8} vehicule {nr(x['pietoni']):>8} pietoni  "
                       f"({x['intervale']} intervale" + (f", {ore_zi(x, zi)})" if x["intervale"] else ")"))
    tacere = f["veghe"]["tacere_inainte_de_taietura_s"]
    if tacere is None or tacere > TACERE_VEGHE:
        randuri.append(f"  ATENȚIE: veghea nu are niciun rând în ultimele {durata_text(tacere)} dinaintea tăieturii: un gol "
                       "sau o pauză de atunci nu se vede încă" if tacere is not None else
                       "  ATENȚIE: niciun rând al vegherii în fereastră")
    return "\n".join(randuri)


def tabel_md(f: dict) -> str:
    """Tabelul scurt, în Markdown."""
    m, t, c, p, r, o, lt, v = (f["minute"], f["timp"], f["cadre_pe_secunda"], f["pauze"], f["reconectari"], f["opriri"],
                               f["lanturi"], f["vehicule"])
    out = [f"# Fișa senzorului – până la {ora_text(f['taietura'])}", "",
           "| Mărimea | Valoarea |", "|---|---|",
           f"| Începutul colectării | {ora_text(f['inceput'])} |",
           f"| Timp scurs | {nr(f['durata']['ore'], 2)} h |",
           f"| Minute cu cadre prelucrate | {pct(m['pondere_cu_cadre'])} ({nr(m['cu_cadre'])} din {nr(m['intregi'])}) |",
           f"| Timp cu colectarea pornită | {pct(t['pondere_colectare_pornita'], 2)} (oprită "
           f"{durata_text(o['durata_s'])}) |",
           f"| Cadre analizate pe secundă (mediana) | {nr(c['mediana'], 2)} |",
           f"| Pauze fără cadre, de cel puțin 10 s | {nr(p['numar'])} ({nr(p['durata_s'])} s în total"
           + (f"; cea mai lungă {nr(p['cea_mai_lunga_s'])} s)" if p["numar"] else ")") + " |",
           f"| Căderi ale sursei camerei (veghea oprită de „fără cadre”) | {_caderi_text(f.get('caderi_sursa'))} |",
           f"| Reconectări la fluxul camerei | {nr(r['episoade'])} episoade ({nr(r['cresteri_contor'])} creșteri ale "
           f"contorului) |",
           f"| Opriri anunțate / căderi neprevăzute | {nr(o['anuntate'])} / {nr(o['caderi_neprevazute'])} |",
           f"| Lanțuri de noapte încheiate | {nr(lt['total']['incheiate'])} din {nr(lt['total']['asteptate'])} |",
           "", "| Ziua | Vehicule intrate | " + " | ".join(c_.capitalize() for c_ in CLASE.values()) + " | Pietoni |",
           "|---|" + "---:|" * (len(CLASE) + 2)]
    for zi, x in [*v["pe_zile"].items(), ("Total", {"vehicule": v["total"], "pe_clase": v["pe_clase"],
                                                    "pietoni": v["pietoni_total"]})]:
        eticheta = zi if zi == "Total" else zi_text(zi)
        out.append(f"| {eticheta} | {nr(x['vehicule'])} | " + " | ".join(nr(x["pe_clase"].get(k, 0)) for k in CLASE)
                   + f" | {nr(x['pietoni'])} |")
    out += ["", "Vehicule detectate, fără factorii de corecție (§ 4.3); pietonii, doar ca total. Definițiile: "
                "`python -m romana.vision.fisa_senzor --help`; cifrele întregi, în JSON."]
    return "\n".join(out) + "\n"


def _ora_arg(text: str) -> float:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text.strip(), fmt).timestamp()
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"oră nerecunoscută: {text} (AAAA-LL-ZZ HH:MM[:SS])")


def main(argv=None) -> int:
    for flux in (sys.stdout, sys.stderr):   # diacriticele merg și când ieșirea e redirecționată fără UTF-8 (cp1250)
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pana-la", type=_ora_arg, help="tăietura, AAAA-LL-ZZ HH:MM[:SS] (implicit: acum)")
    ap.add_argument("--de-la", type=_ora_arg, help="începutul ferestrei, în locul celui aflat din jurnale")
    ap.add_argument("--out-json", type=Path, help="fișa întreagă, în JSON")
    ap.add_argument("--out-md", type=Path, help="tabelul scurt, în Markdown")
    ap.add_argument("--loguri", type=Path, default=LOG_DIR,
                    help="dosarul cu veghe_*.csv, veghe_alerta_*.json, reporniri_*.csv, paznic_*.log și viziune_*.log")
    ap.add_argument("--veghe", type=Path, nargs="+", help="CSV-urile vegherii (implicit toate veghe_*.csv din --loguri)")
    ap.add_argument("--lant", type=Path, default=LANTURI["lant"][0], help="dosarul lanțului zilnic (<zi>/stare.json)")
    ap.add_argument("--lant-cor", type=Path, default=LANTURI["lant_cor"][0], help="dosarul lanțului măsurii noi")
    ap.add_argument("--numaratori", type=Path, default=COUNTS_DIR, help="dosarul cu numaratori_<zi>.csv")
    a = ap.parse_args(argv)
    lanturi = {"lant": (a.lant, LANTURI["lant"][1]), "lant_cor": (a.lant_cor, LANTURI["lant_cor"][1])}
    try:
        f = fisa(a.pana_la if a.pana_la is not None else time.time(), a.de_la, a.loguri, a.veghe, lanturi, a.numaratori)
    except ValueError as e:
        print(f"[fisa_senzor] {e}", file=sys.stderr)
        return 2
    print(rezumat(f))
    for cale, text in ((a.out_json, json.dumps(f, ensure_ascii=False, indent=1) + "\n"), (a.out_md, tabel_md(f))):
        if cale is not None:
            cale.parent.mkdir(parents=True, exist_ok=True)
            cale.write_text(text, encoding="utf-8")
            print(f"[fisa_senzor] scris: {cale}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
