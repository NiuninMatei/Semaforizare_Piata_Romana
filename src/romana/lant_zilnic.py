"""Lanțul zilnic de prelucrare: dintr-o zi colectată, până la rezultatele strategiilor pe ziua aceea (§ 9.9, § 9.10).

Generalizează lanțul de confirmare din noaptea de 30.10, care a rulat toți pașii cu cod 0 între 00:15 și 03:20. Pașii, cu
aceleași argumente ca atunci (în afară de zi și de numele ieșirilor):
  1. verificarea jurnalului (`romana.vision.repara`): cod 0 = întreg, cod 2 = membri stricați (se notează și se merge mai
     departe), alt cod = oprire;
  2. calitatea înregistrării (`romana.vision.calitate`, § 4.6), renumărarea și publicarea (`romana.vision.recount`);
  3. scenariile zilei (`romana.bridge.scenarii_zi`) și variantele cu participanți indisciplinați
     (`romana.bridge.indisciplinat`);
  4. testul: `romana.control.validare` pe ambele comportamente, seed-urile 1–10, 11–15 pe ziua de validare; zilele de test
     și de generalizare se opresc înaintea acestui pas până la --desigileaza (§ 9.11); aceleași strategii ca pe 28–29.10;
  5. statisticile (`romana.control.analiza`), confirmarea planului ales (`decizie --confirma PLAN_12_14_12`), regula
     aplicată și pe ziua aceasta (informativ), măsura pe persoană (`ocupare`, autobuz cu 20 / 40 / 70 de persoane, cu decizia
     ei) și totalurile (`romana.control.totaluri`, Anexa A).
Lanțul se oprește dacă lipsește jurnalul sau dacă eșuează calitatea, renumărarea sau scenariile: scenariile nu se fac pe
CSV-ul live. Merge mai departe peste membrii stricați fiindcă citirea (`romana.vision.repara`) sare peste ei; în acele zile
verifică și că renumărarea chiar a ajuns la capătul jurnalului (`verifica_capat`). La alte eșecuri se notează și se merge mai
departe, dar pașii care ar folosi rezultatul lipsă se sar, ca să nu lucreze pe un fișier vechi.

Ieșirile: outputs/lant/<zi>/ (jurnal.txt, <pas>.txt, stare.json), outputs/validare/test_<zi>_{indisciplinat,normal}.csv,
confirmare_<zi>.json, decizie_<zi>.json, test_<zi>_persoane_<b>.csv, decizie_<zi>_persoane_<b>.json. Rezultatele nu se
copiază singure în docs/.

Reluarea (--reia): stare.json păstrează pentru fiecare pas codul, începutul, sfârșitul și comanda; se sar pașii încheiați cu
cod 0 și cu aceeași comandă, dacă nu s-a refăcut între timp un pas de care depind. `validare` fără --adauga scrie --out o
singură dată, la sfârșit, și suprascrie fișierul: un pas întrerupt nu lasă rezultate parțiale, deci se reia de la capăt
(≈1,5 h pe comportament); ieșirile unui pas se șterg înainte de rulare, ca un rezultat vechi să nu pară nou. După o
reparare a jurnalului, lanțul se rulează din nou fără --reia. Un pas blocat se oprește după LIMITA_PAS_S, ca bucla să
ajungă și la noaptea următoare. Un lanț oprit din afară, fără repornirea calculatorului, își lasă pasul în curs să ruleze;
de aceea stare.json ține și PID-ul și momentul pornirii pasului, iar lanțul următor al zilei îl oprește înainte de orice
altceva, ca să nu ruleze două validări peste aceleași fișiere.

Scenariile rămase: `scenarii_zi` scrie doar ferestrele alese și nu șterge ce a rămas de la o rulare anterioară, iar tiparele
`zi_<zi>_*` le-ar lua din nou (simulări degeaba, analize amestecate, `decizie` căzută abia după simulări). De aceea, după
`scenarii_zi`, lanțul șterge scenariile și cererea ferestrelor care nu mai sunt în rezumatul zilei. Dacă `scenarii_zi`
eșuează, nu se șterge nimic.

Excluderile din ferestrele scenariilor (`scenarii_zi --exclude`) se unesc din patru surse: --exclude,
outputs/lant/excluderi.json ({"AAAA-LL-ZZ": ["HH:MM-HH:MM", ...]}), outputs/logs/reporniri_<zi>.csv (coloanele oprire,
repornire, ora locală ISO; le scrie paznicul colectării) și grila numărătorilor, citită după `recount`. Pentru o repornire se
exclude de la sfertul opririi până la sfârșitul sfertului repornirii, căruia `recount` îi dă durata întreagă deși are date
parțiale: oprire 08:33, repornire 08:46 → 08:30-09:00 (§ 4.6). Grila prinde și opririle care nu trec prin paznic: sferturile
fără date sau mai scurte de SFERT_INTREG_MIN, primul sfert întreg de după ele și primul sfert al zilei, dacă nu e 00:00. Pe
29.10, grila singură dă exact excluderea din lanțul de atunci. O oprire și o repornire în același sfert nu se văd în grilă,
nici o repornire în sfertul 00:00 după o oprire din ziua precedentă: pe acelea le prind doar reporniri_<zi>.csv și
excluderi.json.

Rândurile dublate: dacă fluxul se oprește peste miezul nopții și revine după renumărare, `run_vision` închide abia atunci
intervalul 23:45 și îl adaugă în CSV-ul zilei trecute, iar `scenarii_zi` ar aduna rândurile. Lanțul așteaptă de aceea cel
mult ASTEPTARE_FLUX_S fluxul oprit, iar înainte de `scenarii_zi` și la sfârșit reface o dată renumărarea dacă găsește chei
dublate. Dacă rămân, se notează și se merge mai departe: ora 03:xx există de două ori la trecerea la ora de iarnă (25.10).

Față de lanțul din 30.10, în afară de zi și de numele ieșirilor: `repara` și `totaluri` sunt în plus; benzile analizelor vin
tot din decizia zilei, dar --uscat arată în locul lor un locțiitor; strategia confirmată e o constantă (acolo se citea din
decizia din 28.10, cu aceeași valoare); copiii primesc PYTHONIOENCODING=utf-8 și stdin gol; la eșec se sar pașii dependenți.

Prioritatea: la pornire, procesul își pune prioritatea BELOW_NORMAL (psutil) și o citește înapoi; procesele copil o moștenesc
(Windows dă copiilor unui proces BELOW_NORMAL aceeași clasă). Moștenirea o verifică testele, pe un copil și pe un
ProcessPoolExecutor ca în `validare`; la rulare, prioritatea citită a proceselor fiecărui pas mai lung de câteva secunde se
notează în jurnal. Lansatorul din .venv rămâne la prioritate normală, dar doar așteaptă interpretorul real. Apelul prin
ctypes din lanțurile vechi nu se aplica (§ 4.6, „ctypes fără tipuri”).

Exemple:
  python -m romana.lant_zilnic --uscat --zi 2026-11-01 --exclude 08:00-09:15      # doar afișează comenzile
  python -m romana.lant_zilnic --zi 2026-11-01 --exclude 08:00-09:15
  python -m romana.lant_zilnic --zi 2026-11-01 --reia                             # după o repornire a calculatorului
  python -m romana.lant_zilnic                                                    # ziua de ieri
  python -m romana.lant_zilnic --bucla --reia --ora 00:15 --pana-la "2026-11-08 12:00"   # noapte de noapte

Bucla ține minte în outputs/lant/bucla.json prima zi de care răspunde (sau --de-la); cu --reia, la pornire reia în ordine
toate zilele de atunci cu jurnal și fără rezultatul „gata”, deci și nopțile în care n-a rulat. Zilele mai vechi nu intră
singure.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import zlib
from collections import Counter, deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from datetime import time as ora_din_zi
from pathlib import Path

from romana.common import COUNTS_DIR, OUTPUT_DIR, ROOT, TRAJ_RAW_DIR

DIR_LANT = OUTPUT_DIR / "lant"
DIR_LOGURI = OUTPUT_DIR / "logs"
DIR_LIVE = OUTPUT_DIR / "live"
FISIER_EXCLUDERI = "excluderi.json"
FISIER_BLOCARE = "proces.pid"
FISIER_BUCLA = "bucla.json"
PY = sys.executable

# strategiile testului, ca în lanțurile din 28–29.10 (programele sunt cele din `romana.control.decizie`, verificat în teste)
REALIST = "REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3"
TOD_DEBIT = "TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12"
STRATEGII = ["ACTUATED", "models/ppo_romana.zip", "models/ppo_romana_zn3.zip", "models/ppo_romana_cal.zip", "PLAN_12_14_12",
             "PLAN_16_10_12"]
RAPORTATE = {"strategii": ["PLAN_12_14_12", "PLAN_16_10_12"],   # strategiile raportate, planurile fixe din grila pe geamănul
             "programe": ["TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12"],   # calibrat (§ 9.9)
             "referinte": ["PLAN_12_14_12", "TOD_FIX"]}
CONFIRMATA = "PLAN_12_14_12"            # strategia aleasă pe 28.10 și confirmată pe 29.10 (§ 9.10)
OCUPARI_AUTOBUZ = (20, 40, 70)
BENZI = "<benzi_analiza din decizie>"   # se află abia după pasul „decizie”; se completează la rulare

# Rolurile zilelor noi, scrise înainte de date (§ 9.11). Ziua de validare merge pe seed-urile ei. Zilele de test și de
# generalizare se prelucrează fără simulări până există un candidat fixat pe validare; atunci, --desigileaza, zi cu zi.
ROLURI = {"2026-11-01": "antrenare", "2026-11-02": "antrenare", "2026-11-03": "antrenare", "2026-11-04": "validare",
          "2026-11-05": "test", "2026-11-06": "test", "2026-11-07": "generalizare"}
SEEDURI_TEST = "1-10"
SEEDURI_ROL = {"validare": "11-15"}
ROLURI_SIGILATE = ("test", "generalizare")
# zilele care nu intră la antrenare când lista scenariilor nu e dată explicit
ZILE_FARA_ANTRENARE = ("2026-10-21", "2026-10-22", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30",
                       *(z for z, r in ROLURI.items() if r != "antrenare"))

COD_MEMBRI_STRICATI = 2                 # `romana.vision.repara`: jurnal citibil, cu membri stricați
COD_CAPAT = 3                           # renumărarea a ieșit cu 0, dar nu ajunge până la capătul jurnalului
COD_REZUMAT = 4                         # `scenarii_zi` a ieșit cu 0, dar rezumatul lipsește sau scenariile rămase nu se șterg
COD_DEPASIT = 124                       # pasul a depășit LIMITA_PAS_S și a fost oprit
BELOW_NORMAL = 0x4000
LIMITA_PAS_S = 12 * 3600.0              # cel mai lung pas, validarea, a durat ≈1,5 h pe 30.10
PROBA_COPIL_S = 5.0                     # după atâtea secunde se citește prioritatea proceselor unui pas
TOLERANTA_CAPAT_S = 3600.0              # ultimul interval din CSV poate rămâne atât în urma ultimei traiectorii din jurnal
COADA_JURNAL = 1 << 18                  # octeți; ajung pentru ultimele sute de traiectorii
ANTET_GZIP = b"\x1f\x8b\x08"
ORA_IMPLICITA = ora_din_zi(0, 15)
SFERT = 15                              # minute
SFERT_INTREG_MIN = 14.5                 # minute; pe 21–30.10, numai sferturile cu o oprire au ieșit mai scurte
ASTEPTARE_FLUX_S = 1800.0               # cât așteaptă lanțul un flux oprit dinaintea miezului nopții
PAS_FLUX_S = 30.0


def jurnal(zi: str) -> Path:
    """Jurnalul complet al zilei, local (data/trajectories_brute)."""
    return TRAJ_RAW_DIR / f"traiectorii_{zi}.jsonl.gz"


# -------------------------------------------------------------------------------------------------------- pașii
@dataclass
class Pas:
    nume: str
    comanda: list[str]
    opreste: bool = False               # la eșec, lanțul se oprește (altfel notează și merge mai departe)
    depinde: tuple[str, ...] = ()       # pașii ale căror rezultate le folosește
    iesiri: tuple[str, ...] = ()        # fișierele scrise (relativ la rădăcină), șterse înainte de rulare
    acceptate: tuple[int, ...] = (0,)   # codurile de ieșire cu care pasul nu e un eșec
    la_esec: str = ""


def _m(modul: str, *arg: str) -> list[str]:
    return [PY, "-m", modul, *arg]


def comanda_scenarii(zi: str, exclude=()) -> list[str]:
    # pe zilele care decid, sferturile încetinite nu intră în alegerea ferestrelor (§ 9.11)
    rol = ["--fara-incetinite"] if ROLURI.get(zi, "antrenare") != "antrenare" else []
    return _m("romana.bridge.scenarii_zi", "--zi", zi, *rol, *[x for e in exclude for x in ("--exclude", e)])


def sigilata(zi: str) -> bool:
    # o zi de după ultimul rol poate primi un rol mutat (§ 9.11): rămâne fără simulări până îl primește
    return ROLURI.get(zi) in ROLURI_SIGILATE or (zi not in ROLURI and zi > max(ROLURI))


def pasi(zi: str, exclude=(), fara_simulari: bool = False, desigilat: bool = False) -> list[Pas]:
    """Pașii lanțului pentru o zi, în ordine (aceleași argumente ca în lanțul din 30.10; repara și totaluri sunt în plus)."""
    raw = str(jurnal(zi))
    scenarii = str(ROOT / "sumo" / "scenarios" / f"zi_{zi}_*.sumocfg")
    lista = [
        Pas("repara", _m("romana.vision.repara", raw), opreste=True, acceptate=(0, COD_MEMBRI_STRICATI),
            la_esec="jurnalul nu s-a putut verifica"),
        Pas("calitate", _m("romana.vision.calitate", raw, "--out", f"outputs/calitate_{zi}.csv",
                           "--out-15min", f"outputs/calitate_15min_{zi}.csv"), opreste=True,
            la_esec="calitatea nu s-a putut calcula (jurnal deteriorat?)"),
        Pas("recount", _m("romana.vision.recount", "--zi", zi), opreste=True,
            la_esec="renumărarea a eșuat (scenariile nu se fac pe CSV-ul live)"),
        Pas("publica", _m("romana.vision.recount", "--zi", zi, "--publica"),
            la_esec="publicarea jurnalului a eșuat; lanțul continuă, publicarea se reface cu --reia"),
        Pas("scenarii", comanda_scenarii(zi, exclude), opreste=True, depinde=("recount",),
            la_esec="scenariile nu s-au generat"),
        Pas("indisciplinat", _m("romana.bridge.indisciplinat", "--scenarii", scenarii), depinde=("scenarii",)),
    ]
    if fara_simulari or (sigilata(zi) and not desigilat):
        return lista

    seeduri = SEEDURI_ROL.get(ROLURI.get(zi), SEEDURI_TEST)
    strategii = STRATEGII + [s for s in RAPORTATE["strategii"] if s not in STRATEGII]
    out = {c: f"outputs/validare/test_{zi}_{c}.csv" for c in ("indisciplinat", "normal")}
    teste = tuple(f"test_{c}" for c in out)
    toate = list(out.values())
    for comp, tip, dep in (("indisciplinat", f"indisciplinat_zi_{zi}_*", "indisciplinat"),
                           ("normal", f"zi_{zi}_*", "scenarii")):
        lista.append(Pas(f"test_{comp}", _m("romana.control.validare", *strategii, "--scenarii", tip, "--seeds", seeduri,
                                            "--fara-alegere", "--procese", "11", "--out", out[comp]),
                         depinde=(dep,), iesiri=(out[comp],)))

    def analiza(nume: str, *arg: str, depinde: tuple[str, ...]) -> None:
        lista.append(Pas(nume, _m("romana.control.analiza", *arg), depinde=depinde))

    prog = ["--program", REALIST] + [x for p in RAPORTATE["programe"] for x in ("--program", p)]
    for comp in out:
        analiza(f"analiza_{comp}", out[comp], *prog, "--referinte", "FIX", "REALIST", "ACTUATED", "--pe-scenarii",
                depinde=(f"test_{comp}",))
    analiza("analiza_reunite", *toate, *prog, "--referinte", "FIX", "REALIST", depinde=teste)
    for comp in out:
        analiza(f"analiza_{comp}_planuri", out[comp], *prog, "--referinte", *RAPORTATE["referinte"], "--pe-scenarii",
                depinde=(f"test_{comp}",))
    analiza("analiza_reunite_planuri", *toate, *prog, "--referinte", *RAPORTATE["referinte"], depinde=teste)

    confirmare, decizie = f"outputs/validare/confirmare_{zi}.json", f"outputs/validare/decizie_{zi}.json"
    lista.append(Pas("confirmare", _m("romana.control.decizie", *toate, "--confirma", CONFIRMATA, "--out", confirmare),
                     depinde=teste, iesiri=(confirmare,)))
    lista.append(Pas("decizie", _m("romana.control.decizie", *toate, "--out", decizie), depinde=teste, iesiri=(decizie,)))
    prog_d = ["--program", REALIST, "--program", TOD_DEBIT]
    for comp in out:
        analiza(f"analiza_{comp}_debit", out[comp], *prog_d, "--benzi", BENZI, "--referinte", "FIX", "REALIST",
                "--pe-scenarii", depinde=(f"test_{comp}", "decizie"))
    analiza("analiza_reunite_debit", *toate, *prog_d, "--benzi", BENZI, "--referinte", "FIX", "REALIST", "TOD_DEBIT",
            "PLAN_12_14_12", depinde=(*teste, "decizie"))

    # măsura pe persoană (raportată, nu schimbă decizia): ocupări declarate, autobuz / troleibuz 20, 40 și 70 de persoane
    for b in OCUPARI_AUTOBUZ:
        pers = f"outputs/validare/test_{zi}_persoane_{b}.csv"
        dec_pers = f"outputs/validare/decizie_{zi}_persoane_{b}.json"
        lista.append(Pas(f"ocupare_{b}", _m("romana.control.ocupare", *toate, "--autobuz", str(b), "--out", pers),
                         depinde=teste, iesiri=(pers,)))
        lista.append(Pas(f"decizie_persoane_{b}", _m("romana.control.decizie", pers, "--out", dec_pers),
                         depinde=(f"ocupare_{b}",), iesiri=(dec_pers,)))
    lista.append(Pas("totaluri", _m("romana.control.totaluri", *toate), depinde=teste))   # tabelele § 9.10 (Anexa A)
    return lista


def rezolva(p: Pas, zi: str) -> list[str]:
    """Comanda de rulat: benzile de trafic ale analizelor pe debit vin din decizia zilei, abia scrisă de pasul „decizie”."""
    if BENZI not in p.comanda:
        return p.comanda
    d = json.loads((ROOT / f"outputs/validare/decizie_{zi}.json").read_text(encoding="utf-8"))
    return [d["benzi_analiza"] if x == BENZI else x for x in p.comanda]


# -------------------------------------------------------------------------------------------------- excluderile
RE_INTERVAL = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")


def minute_interval(text: str) -> tuple[int, int]:
    """„HH:MM-HH:MM”, pe grila de 15 min, cu aceleași reguli ca `scenarii_zi --exclude` → minutele de la începutul zilei."""
    m = RE_INTERVAL.match(str(text))
    if not m:
        raise ValueError(f"{text}: formatul este HH:MM-HH:MM")
    h1, m1, h2, m2 = map(int, m.groups())
    a, b = h1 * 60 + m1, h2 * 60 + m2
    if m1 % SFERT or m2 % SFERT or max(m1, m2) >= 60 or b <= a or b > 24 * 60:
        raise ValueError(f"{text}: capetele trebuie să fie pe grila de 15 min, cu începutul înaintea sfârșitului")
    return a, b


def uneste(intervale) -> list[str]:
    """Intervalele în minute → „HH:MM-HH:MM”, în ordine, fără dubluri: cele suprapuse sau vecine devin unul singur."""
    out: list[list[int]] = []
    for a, b in sorted(intervale):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [f"{a // 60:02d}:{a % 60:02d}-{b // 60:02d}:{b % 60:02d}" for a, b in out]


def _sfert(t: datetime) -> datetime:
    return t.replace(minute=t.minute - t.minute % SFERT, second=0, microsecond=0)


def interval_repornire(zi: date, oprire: datetime | None, repornire: datetime | None) -> tuple[int, int] | None:
    """Sferturile zilei atinse de o oprire, în minute: de la sfertul opririi până la sfârșitul sfertului repornirii, căruia
    `recount` îi dă durata întreagă deși are date parțiale. Se taie la ziua dată (o oprire poate trece peste miezul nopții);
    None dacă ziua nu e atinsă. Fără repornire: până la sfârșitul zilei opririi. Fără oprire: doar sfertul repornirii."""
    z0 = datetime.combine(zi, ora_din_zi.min)
    z1 = z0 + timedelta(days=1)
    if repornire is None and (oprire is None or oprire.date() != zi):
        return None
    a = max(_sfert(oprire if oprire is not None else repornire), z0)
    b = min(_sfert(repornire) + timedelta(minutes=SFERT), z1) if repornire is not None else z1
    if a >= b:
        return None
    return int((a - z0).total_seconds()) // 60, int((b - z0).total_seconds()) // 60


def _moment(text) -> datetime | None:
    text = (text or "").strip()
    return datetime.fromisoformat(text).replace(tzinfo=None) if text else None


def intervale_reporniri(zi: str, note=print) -> list[tuple[int, int]]:
    """Intervalele zilei din outputs/logs/reporniri_*.csv. Se citesc și fișierele zilelor vecine: o oprire peste miezul nopții
    poate fi notată în fișierul oricăreia dintre cele două zile."""
    z = date.fromisoformat(zi)
    out = []
    for k in (-1, 0, 1):
        f = DIR_LOGURI / f"reporniri_{z + timedelta(days=k)}.csv"
        if not f.exists():
            continue
        with open(f, newline="", encoding="utf-8-sig") as fh:
            for rand in csv.DictReader(fh):
                try:
                    o, r = _moment(rand.get("oprire")), _moment(rand.get("repornire"))
                    if (o is None and r is None) or (o and r and r < o):
                        raise ValueError("oprirea și repornirea nu se potrivesc")
                except (ValueError, AttributeError) as e:
                    note(f"[atenție] {f.name}: rând ignorat ({e}): {rand}")
                    continue
                if o is None and r.date() == z:
                    note(f"[atenție] {f.name}: repornire fără oprire ({r:%H:%M}), se exclude doar sfertul repornirii")
                iv = interval_repornire(z, o, r)
                if iv:
                    out.append(iv)
    return out


def excluderi_zi(zi: str, din_linie=(), note=print) -> list[str]:
    """Excluderile zilei, unite din cele trei surse. O valoare de neînțeles din --exclude sau din excluderi.json ridică
    ValueError: lanțul se oprește înainte de orice calcul, în loc să lucreze pe ferestre greșite."""
    surse = {"linia de comandă": [minute_interval(x) for x in din_linie]}
    f = DIR_LANT / FISIER_EXCLUDERI
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8-sig"))     # PowerShell scrie UTF-8 cu BOM
        lista = d.get(zi, []) if isinstance(d, dict) else None
        if not isinstance(lista, list):
            raise ValueError(f"{f.name}: se așteaptă {{\"AAAA-LL-ZZ\": [\"HH:MM-HH:MM\", ...]}}")
        surse[FISIER_EXCLUDERI] = [minute_interval(x) for x in lista]
    surse[f"reporniri_{zi}.csv și zilele vecine"] = intervale_reporniri(zi, note)
    for nume, iv in surse.items():
        if iv:
            note(f"excluderi din {nume}: {', '.join(uneste(iv))}")
    return uneste(x for iv in surse.values() for x in iv)


def goluri_grila(zi: str) -> list[tuple[int, int]]:
    """Sferturile întrerupte din grila numărătorilor zilei, în minute, chiar dacă oprirea n-a trecut prin paznic. Grila e cea
    din `scenarii_zi`: un sfert sub 12 min nu contează, deci rămâne gol. Se scot sferturile goale, cele mai scurte de
    SFERT_INTREG_MIN (aici colectarea s-a oprit, dar sfertul mai trece de filtru), primul sfert întreg de după ele
    (repornirea, căreia `recount` îi dă durata întreagă deși are date parțiale) și, la fel, primul sfert al zilei, dacă nu e
    00:00."""
    import pandas as pd

    from romana.bridge.scenarii_zi import hourly_profile
    df = pd.read_csv(COUNTS_DIR / f"numaratori_{zi}.csv", parse_dates=["inceput", "sfarsit"])
    if df.empty:
        return []
    prof = hourly_profile(df)
    if prof.empty or (prof.index != prof.index.floor(f"{SFERT}min")).any():
        return []
    z0, out = pd.Timestamp(zi), []
    dupa_gol = prof.index[0] != z0
    for t, dur_h in prof["dur_h"].items():
        intrerupt = pd.isna(dur_h) or dur_h * 60 < SFERT_INTREG_MIN
        if intrerupt or dupa_gol:
            m = int((t - z0).total_seconds()) // 60
            out.append((m, m + SFERT))
        dupa_gol = intrerupt
    return out


# ------------------------------------------------------------------------------- prioritatea, starea, rularea
def prioritate_scazuta() -> tuple[bool, str]:
    """Pune procesul curent la prioritatea BELOW_NORMAL și o citește înapoi: (aplicată, textul de notat în jurnal)."""
    try:
        import psutil
    except ImportError:
        return False, "ATENȚIE: psutil lipsește din mediu, prioritatea NU s-a schimbat"
    if os.name != "nt":
        return False, "ATENȚIE: prioritatea se schimbă doar pe Windows; procesul a rămas la prioritatea lui"
    try:
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        citita = int(p.nice())
    except (psutil.Error, OSError) as e:
        return False, f"ATENȚIE: prioritatea NU s-a putut schimba: {e!r}"
    if citita != int(psutil.BELOW_NORMAL_PRIORITY_CLASS):
        return False, f"ATENȚIE: prioritatea NU s-a aplicat: cerută BELOW_NORMAL ({BELOW_NORMAL}), citită {citita}"
    return True, f"prioritatea procesului (PID {os.getpid()}): BELOW_NORMAL, citită înapoi {citita}"


def prioritati_proces(pid: int) -> str:
    """Prioritățile citite ale procesului unui pas și ale copiilor lui (interpretorul real, procesele de lucru)."""
    try:
        import psutil
        p = psutil.Process(pid)
        toate = [p, *p.children(recursive=True)]
        val = sorted({int(x.nice()) for x in toate})
    except Exception as e:   # procesul se poate încheia chiar în clipa citirii
        return f"prioritatea pasului nu s-a putut citi: {e!r}"
    return (f"prioritatea pasului, citită: {val[0]} (BELOW_NORMAL), {len(toate)} procese" if val == [BELOW_NORMAL]
            else f"ATENȚIE: prioritățile pasului, citite ({len(toate)} procese): {val}, nu {BELOW_NORMAL} (BELOW_NORMAL)")


def _iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def noteaza(cale: Path | None, mesaj: str) -> None:
    """Un rând în jurnal și pe ecran; o eroare de scriere nu oprește lanțul."""
    linie = f"{datetime.now():%d.%m %H:%M:%S} {mesaj}"
    try:
        print(linie, flush=True)
    except (OSError, ValueError):       # proces fără consolă
        pass
    if cale is not None:
        try:
            with open(cale, "a", encoding="utf-8") as f:
                f.write(linie + "\n")
        except OSError:
            pass


def citeste_stare(zi: str, note=None) -> dict:
    """Starea zilei; lipsă sau deteriorată = goală: pașii se refac, fiindcă toți pot fi rulați din nou fără pagube."""
    f = DIR_LANT / zi / "stare.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        if note:
            note(f"[atenție] {f.name} nu se poate citi ({e!r}): pașii se refac")
        return {}


def scrie_stare(zi: str, stare: dict, note=None) -> None:
    """Scriere atomică: o pană de curent lasă fișierul vechi sau pe cel nou, niciodată unul pe jumătate. Dacă scrierea nu
    reușește (de ex. fișierul e ținut deschis), se notează: la reluare, pasul respectiv se reface."""
    f = DIR_LANT / zi / "stare.json"
    stare["actualizat"] = _iso()
    try:
        tmp = f.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(stare, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        for incercare in range(5):
            try:
                os.replace(tmp, f)
                return
            except PermissionError:     # alt proces citește chiar acum fișierul
                if incercare == 4:
                    raise
                time.sleep(0.2)
    except OSError as e:
        if note:
            note(f"[atenție] {f.name} nu s-a putut scrie: {e!r}")


def _opreste_arbore(p) -> None:
    """Oprește procesul unui pas (subprocess.Popen sau psutil.Process) și copiii lui (procesele de lucru ale validării), doar
    pe ei."""
    try:
        import psutil
        copii = psutil.Process(p.pid).children(recursive=True)
    except Exception:
        copii = []
    for x in (p, *copii):
        try:
            x.kill()
        except Exception:               # s-a încheiat între timp
            pass
    try:
        p.wait(timeout=30)
    except Exception:                   # cine nu s-a oprit se vede la verificarea de după
        pass


def moment_pornire(pid: int) -> float | None:
    """Momentul pornirii procesului: împreună cu PID-ul îl identifică, fiindcă Windows refolosește PID-urile."""
    try:
        import psutil
        return psutil.Process(pid).create_time()
    except Exception:                   # psutil lipsește sau procesul s-a încheiat deja
        return None


def opreste_pasi_ramasi(pasi_vechi: dict, note) -> str | None:
    """Oprește pasul rămas să ruleze de la un lanț oprit din afară (pe Windows, copiii supraviețuiesc părintelui, oricare
    dintre lansator și interpretor ar fi fost oprit). Altfel, reluarea ar porni încă o validare peste aceleași fișiere, cu
    dublul proceselor. Se atinge doar procesul cu același PID și același moment de pornire. Întoarce motivul de oprire
    dacă procesul nu se poate opri."""
    try:
        import psutil
    except ImportError:
        return None
    for nume, rec in pasi_vechi.items():
        pid, creat = rec.get("pid"), rec.get("creat")
        if rec.get("cod") is not None or not pid or creat is None:
            continue
        try:
            p = psutil.Process(pid)
            if abs(p.create_time() - creat) > 1.0:
                continue                # alt proces, cu un PID refolosit (după o repornire a calculatorului)
        except psutil.Error:
            continue                    # s-a încheiat între timp
        note(f"[atenție] pasul {nume} a rămas să ruleze (PID {pid}) de la un lanț oprit din afară: se oprește și se reface")
        _opreste_arbore(p)
        if p.is_running():
            return f"pasul {nume} (PID {pid}) rulează încă și nu s-a putut opri"
    return None


def ruleaza(cmd: list[str], cale: Path, note=None, la_pornire=None) -> int:
    """Rulează comanda din rădăcina proiectului, cu ieșirea în `cale`; întoarce codul de ieșire. Imediat după pornire,
    apelează la_pornire(pid). Copiii scriu în UTF-8: cu ieșirea redirecționată, Python ar folosi altfel cp1250, iar un „ș” sau
    un „→” din print i-ar opri cu UnicodeEncodeError."""
    mediu = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
    with open(cale, "w", encoding="utf-8") as f:
        p = subprocess.Popen(cmd, cwd=ROOT, env=mediu, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT)
        try:
            if la_pornire:
                la_pornire(p.pid)
            try:
                return p.wait(timeout=PROBA_COPIL_S)
            except subprocess.TimeoutExpired:
                if note:
                    note("   " + prioritati_proces(p.pid))
            try:
                return p.wait(timeout=max(LIMITA_PAS_S - PROBA_COPIL_S, 0))
            except subprocess.TimeoutExpired:
                if note:
                    note(f"   pasul a depășit limita de {LIMITA_PAS_S / 3600:g} h și a fost oprit")
                _opreste_arbore(p)
                return COD_DEPASIT
        except BaseException:           # și Ctrl+C: procesele pasului nu rămân să ruleze singure
            _opreste_arbore(p)
            raise


def capat_jurnal(raw: Path, coada: int = COADA_JURNAL) -> float | None:
    """Cel mai mare început de traiectorie din coada jurnalului, citită membru cu membru, independent de cititorul lui
    `recount`; None dacă nu s-a putut citi nimic."""
    with open(raw, "rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - coada))
        date_brute = f.read()
    capat, i = None, date_brute.find(ANTET_GZIP)
    while i >= 0:
        d = zlib.decompressobj(31)
        try:
            text = d.decompress(date_brute[i:])
            if d.eof:
                t0 = float(json.loads(text.splitlines()[0])["t0"])
                capat = t0 if capat is None else max(capat, t0)
        except (zlib.error, ValueError, KeyError, IndexError, TypeError):   # antet fals sau membru stricat
            pass
        i = date_brute.find(ANTET_GZIP, i + 1)
    return capat


def ultimul_interval(zi: str) -> float | None:
    """Începutul ultimului interval din numărătorile zilei (secunde), None dacă fișierul lipsește sau n-are date."""
    f = COUNTS_DIR / f"numaratori_{zi}.csv"
    try:
        with open(f, newline="", encoding="utf-8") as fh:
            ultim = deque(csv.reader(fh), maxlen=1)
        return datetime.fromisoformat(ultim[0][0]).timestamp()
    except (OSError, IndexError, ValueError):
        return None


def verifica_capat(zi: str) -> str | None:
    """Pe o zi cu membri stricați: motivul de oprire dacă renumărarea n-a ajuns până la capătul jurnalului. Lanțul merge mai
    departe peste membrii stricați doar fiindcă citirea sare peste ei; cititorul vechi se oprea în tăcere la un membru
    stricat și ieșea cu cod 0, deși pierduse restul zilei, iar scenariile ar fi ieșit din jumătate de zi."""
    try:
        capat = capat_jurnal(jurnal(zi))
    except OSError:
        return None
    if capat is None:
        return None                     # coada nu s-a putut citi: nu e o dovadă de eroare
    ultim = ultimul_interval(zi)
    if ultim is None:
        return f"numaratori_{zi}.csv lipsește sau e gol după renumărare"
    if capat - ultim > TOLERANTA_CAPAT_S:
        return (f"renumărarea s-a oprit la {datetime.fromtimestamp(ultim):%H:%M}, dar jurnalul merge până la "
                f"{datetime.fromtimestamp(capat):%H:%M}: citirea n-a trecut de membrii stricați, iar CSV-ul zilei e incomplet")
    return None


def curata_scenarii(zi: str, note) -> str | None:
    """După `scenarii_zi`: șterge scenariile și cererea ferestrelor care nu mai sunt în rezumatul zilei (vezi „Scenariile
    rămase” în antet). Întoarce motivul de oprire dacă rezumatul nu se poate citi sau un scenariu rămas nu se poate
    șterge."""
    f = ROOT / "sumo" / "demand" / f"zi_{zi}_rezumat.json"
    try:
        valabile = set(json.loads(f.read_text(encoding="utf-8"))["scenarii"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        return f"{f.name} nu se poate citi după scenarii_zi: {e!r}"
    sterse = []
    try:
        for prefix in ("", "indisciplinat_"):
            for sc in sorted((ROOT / "sumo" / "scenarios").glob(f"{prefix}zi_{zi}_*.sumocfg")):
                nume = sc.stem.removeprefix(prefix)
                if nume not in valabile:
                    sc.unlink()
                    sterse.append(sc.stem)
                    shutil.rmtree(ROOT / "sumo" / "demand" / nume, ignore_errors=True)
    except OSError as e:
        return f"un scenariu rămas de la o rulare anterioară nu se poate șterge: {e!r}"
    if sterse:
        note(f"[atenție] scenarii rămase de la o rulare anterioară, care nu mai sunt în {f.name}, șterse: "
             + ", ".join(sterse))
    return None


def randuri_dublate(zi: str) -> int:
    """Câte rânduri din numărătorile zilei repetă cheia altui rând."""
    try:
        with open(COUNTS_DIR / f"numaratori_{zi}.csv", newline="", encoding="utf-8") as f:
            n = Counter((r["inceput"], r["tip"], r["origine"], r["destinatie"], r["vehicul"]) for r in csv.DictReader(f))
    except (OSError, ValueError, KeyError):
        return 0                        # fără CSV n-are ce se dubla; lipsa lui o prinde `scenarii_zi`
    return sum(k - 1 for k in n.values())


def reface_dublate(zi: str, note) -> str | None:
    """Rândurile dublate din numărătorile zilei (vezi „Rândurile dublate” în antet) dispar la o nouă renumărare, care rescrie
    CSV-ul; rezultatul pentru datele din jurnal e același. Întoarce motivul, dacă renumărarea eșuează."""
    n = randuri_dublate(zi)
    if not n:
        return None
    note(f"[atenție] numaratori_{zi}.csv are {n} rânduri cu cheie dublată: se reface renumărarea")
    cmd = _m("romana.vision.recount", "--zi", zi)
    note("RUN " + " ".join(cmd))
    try:
        cod = ruleaza(cmd, DIR_LANT / zi / "recount_dublate.txt", note)
    except OSError as e:
        return f"renumărarea pentru rândurile dublate nu s-a putut lansa: {e!r}"
    note(f"   exit {cod}")
    if cod != 0:
        return f"renumărarea pentru rândurile dublate a eșuat (cod {cod})"
    n = randuri_dublate(zi)
    if n:
        note(f"[atenție] rămân {n} rânduri cu cheie dublată (ora care se repetă la trecerea la ora de iarnă?); lanțul "
             "continuă")
    return None


def ultimul_cadru() -> float | None:
    """Momentul ultimului cadru prelucrat de colectare (`timestamp` din starea live), None dacă nu se poate citi."""
    try:
        return float(json.loads((DIR_LIVE / "state.json").read_text(encoding="utf-8"))["timestamp"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def asteapta_fluxul(zi: str, note, ceas=time.time, dormi=time.sleep) -> bool:
    """Colectarea activă n-a mai prelucrat niciun cadru de după miezul nopții de la sfârșitul zilei? Atunci intervalul 23:45
    e încă deschis și va ajunge în CSV după renumărare; se așteaptă cel mult ASTEPTARE_FLUX_S. Întoarce False dacă nu
    revine."""
    miez = datetime.combine(date.fromisoformat(zi) + timedelta(days=1), ora_din_zi.min).timestamp()
    t = ultimul_cadru()
    if t is None or t >= miez:
        return True
    note(f"colectarea n-a mai prelucrat cadre din {datetime.fromtimestamp(t):%d.%m %H:%M}: aștept fluxul cel mult "
         f"{ASTEPTARE_FLUX_S / 60:.0f} min, ca intervalul deschis să nu se adauge după renumărare")
    limita = ceas() + ASTEPTARE_FLUX_S
    while ceas() < limita:
        dormi(PAS_FLUX_S)
        t = ultimul_cadru()
        if t is not None and t >= miez:
            note("fluxul a revenit")
            return True
    note(f"[atenție] fluxul n-a revenit; când revine, numaratori_{zi}.csv poate primi rânduri dublate. Lanțul le verifică "
         f"înainte de scenarii și la sfârșit; dacă apar după el: python -m romana.vision.recount --zi {zi}")
    return False


def colectare_activa() -> bool:
    """Rulează `run_vision`? Atunci CSV-ul zilei curente e scris live, iar `recount` nu trebuie să-l șteargă."""
    try:
        import psutil
    except ImportError:
        return False
    for p in psutil.process_iter(["cmdline"]):
        try:
            if "romana.vision.run_vision" in " ".join(p.info["cmdline"] or []):
                return True
        except psutil.Error:
            pass
    return False


def zi_scrisa_live(zi: str) -> bool:
    return date.fromisoformat(zi) >= date.today() and colectare_activa()


def lant_activ(pid: int) -> bool:
    """Procesul `pid` e un lanț care rulează? (PID-ul rămas după o repornire poate fi al altui program.)"""
    try:
        import psutil
        return "romana.lant_zilnic" in " ".join(psutil.Process(pid).cmdline())
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------- lanțul
def _lant(zi: str, exclude, reia: bool, fara_simulari: bool, note, desigilat: bool = False) -> int:
    aplicata, text = prioritate_scazuta()
    note(f"pornit lanțul zilei {zi}" + (", reluare" if reia else "") + (", fără simulări" if fara_simulari else ""))
    note(text)
    if zi in ROLURI:
        note(f"rolul zilei (§ 9.11): {ROLURI[zi]}" + (", fără simulări până la desigilare" if sigilata(zi) and not desigilat else ""))
    stare_veche = citeste_stare(zi, note)
    pasi_vechi = stare_veche.get("pasi", {})
    vechi = pasi_vechi if reia else {}
    desigilat = desigilat or (reia and bool(stare_veche.get("desigilat")))    # și bucla reia o zi desigilată cu simulări
    stare = {"zi": zi, "pornit": _iso(), "prioritate": text, "prioritate_aplicata": aplicata, "rezultat": "in_curs",
             "pasi": dict(vechi), **({"desigilat": True} if desigilat else {})}

    def opreste(motiv: str) -> int:
        stare["rezultat"] = f"oprit: {motiv}"
        scrie_stare(zi, stare, note)
        note(f"{motiv} – oprire")
        return 1

    def cu_grila(ex: list[str]) -> list[str]:
        """Excluderile, cu golurile din grila renumărării abia încheiate."""
        try:
            grila = goluri_grila(zi)
        except Exception as e:          # `scenarii_zi` citește același CSV și raportează singur dacă e stricat
            note(f"[atenție] grila numărătorilor nu s-a putut citi ({e!r}): se merge doar cu excluderile știute")
            return ex
        stare["excluderi_grila"] = uneste(grila)
        toate = uneste([*map(minute_interval, ex), *grila])
        if toate != ex:
            note("[atenție] goluri în grila numărătorilor, în afara excluderilor știute: "
                 + ", ".join(stare["excluderi_grila"]) + "; se exclud și ele")
            note("excluderi: " + ", ".join(toate))
        stare["excluderi"] = toate
        return toate

    motiv = opreste_pasi_ramasi(pasi_vechi, note)
    if motiv:
        stare["pasi"] = dict(pasi_vechi)
        return opreste(motiv)
    if zi_scrisa_live(zi):
        return opreste("colectarea rulează, iar CSV-ul zilei e scris live")
    raw = jurnal(zi)
    if not raw.exists():
        return opreste(f"LIPSEȘTE {raw}")
    if date.fromisoformat(zi) < date.today() and colectare_activa() and not asteapta_fluxul(zi, note):
        stare["flux_oprit"] = True
    try:
        ex = excluderi_zi(zi, exclude, note)
    except (OSError, ValueError, csv.Error) as e:
        return opreste(f"excluderile nu se pot citi: {e}")
    note("excluderi: " + (", ".join(ex) if ex else "niciuna"))
    stare["excluderi"] = ex

    def pornit(pid: int) -> None:       # pasul curent, chiar după pornire: un pas rămas se recunoaște după aceste două valori
        rec.update(pid=pid, creat=moment_pornire(pid))
        scrie_stare(zi, stare, note)

    esuate: list[str] = []
    refacute: set[str] = set()
    for p in pasi(zi, ex, fara_simulari, desigilat):
        picate = [x for x in p.depinde if x in esuate]
        try:
            if picate:
                raise ValueError(f"depinde de {', '.join(picate)}, care nu s-a încheiat")
            cmd = rezolva(p, zi)
        except (OSError, ValueError, KeyError) as e:     # fără rezultatele de care are nevoie, pasul nu rulează deloc
            note(f"{p.nume}: sărit ({e})")
            stare["pasi"][p.nume] = {"cod": None, "sarit": str(e)}
            esuate.append(p.nume)
            scrie_stare(zi, stare, note)
            continue
        if p.nume == "scenarii":
            motiv = reface_dublate(zi, note)
            if motiv:
                return opreste(motiv)
            ex = cu_grila(ex)
            cmd = comanda_scenarii(zi, ex)
        v = vechi.get(p.nume) or {}
        if (reia and v.get("cod") == 0 and (v.get("comanda") or [])[1:] == cmd[1:] and not refacute.intersection(p.depinde)
                and all((ROOT / f).exists() for f in p.iesiri)):
            note(f"{p.nume}: încheiat la {v.get('sfarsit')}, sărit")
            continue
        rec = {"cod": None, "inceput": _iso(), "sfarsit": None, "comanda": cmd, "jurnal": f"{p.nume}.txt"}
        stare["pasi"][p.nume] = rec
        refacute.add(p.nume)
        scrie_stare(zi, stare, note)
        note("RUN " + " ".join(cmd))
        try:
            for f in p.iesiri:          # un rezultat vechi (rulare întreruptă sau refăcută) nu trebuie să pară nou
                (ROOT / f).unlink(missing_ok=True)
            cod = ruleaza(cmd, DIR_LANT / zi / f"{p.nume}.txt", note, pornit)
        except OSError as e:
            note(f"   {p.nume} nu s-a putut lansa: {e!r}")
            cod = 1
        motiv = None
        if cod == 0 and p.nume == "recount" and "atentie" in stare:
            motiv = verifica_capat(zi)
        elif cod == 0 and p.nume == "scenarii":
            motiv = curata_scenarii(zi, note)
        if motiv:
            cod = COD_CAPAT if p.nume == "recount" else COD_REZUMAT
            rec["motiv"] = motiv
        rec.update(cod=cod, sfarsit=_iso())
        note(f"   exit {cod}")
        if p.nume == "repara" and cod == COD_MEMBRI_STRICATI:
            stare["atentie"] = "jurnalul are membri stricați"
            note(f"ATENȚIE: jurnalul are membri stricați (vezi {p.nume}.txt); citirea sare peste ei, lanțul continuă")
        scrie_stare(zi, stare, note)
        if cod in p.acceptate:
            continue
        if p.opreste:
            return opreste(motiv or p.la_esec or f"{p.nume} a eșuat (cod {cod})")
        note(p.la_esec or f"{p.nume} a eșuat (cod {cod}); lanțul continuă")
        esuate.append(p.nume)

    motiv = reface_dublate(zi, note)    # fluxul poate reveni și în timpul lanțului; scenariile s-au făcut înainte
    if motiv:
        note(f"[atenție] {motiv}; CSV-ul zilei rămâne cu rânduri dublate")
    if esuate:
        stare["rezultat"] = "cu_esecuri: " + ", ".join(esuate)
    else:
        stare["rezultat"] = "gata_fara_simulari" if fara_simulari or (sigilata(zi) and not desigilat) else "gata"
    scrie_stare(zi, stare, note)
    note(f"lanțul zilei {zi}: {stare['rezultat']}")
    return 1 if esuate else 0


def lant(zi: str, exclude=(), reia: bool = False, fara_simulari: bool = False, desigilat: bool = False) -> int:
    """Rulează lanțul unei zile; întoarce 0 dacă toți pașii s-au încheiat. Pe aceeași zi rulează un singur lanț odată: două
    ar scrie în aceleași fișiere și ar încărca de două ori procesorul."""
    d = DIR_LANT / zi
    d.mkdir(parents=True, exist_ok=True)
    jr = d / "jurnal.txt"
    note = lambda mesaj: noteaza(jr, mesaj)
    blocare = d / FISIER_BLOCARE
    try:
        alt = int(blocare.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        alt = None
    if alt and alt != os.getpid() and lant_activ(alt):
        note(f"pe ziua {zi} rulează deja un lanț (PID {alt}) – oprire")
        return 1
    blocare.write_text(str(os.getpid()), encoding="utf-8")
    try:
        return _lant(zi, exclude, reia, fara_simulari, note, desigilat)
    finally:
        try:
            blocare.unlink(missing_ok=True)
        except OSError:
            pass


# ------------------------------------------------------------------------------------------------------ bucla
def zi_implicita(acum: datetime | None = None) -> str:
    """Ziua de ieri."""
    return ((acum or datetime.now()).date() - timedelta(days=1)).isoformat()


def urmatoarea_ora(acum: datetime, ora: ora_din_zi) -> datetime:
    t = datetime.combine(acum.date(), ora)
    return t if t >= acum else t + timedelta(days=1)


def noptile(acum: datetime, ora: ora_din_zi, pana_la: datetime | None, maxim: int = 7) -> list[tuple[datetime, str]]:
    """Rulările următoare: (momentul, ziua prelucrată, adică cea precedentă)."""
    out, t = [], urmatoarea_ora(acum, ora)
    while (pana_la is None and len(out) < maxim) or (pana_la is not None and t <= pana_la):
        out.append((t, zi_implicita(t)))
        t += timedelta(days=1)
    return out


def prima_zi_buclei(note=None) -> str | None:
    """Prima zi de care răspunde bucla, păstrată de la prima ei pornire; None dacă nu s-a scris încă."""
    f = DIR_LANT / FISIER_BUCLA
    try:
        return date.fromisoformat(json.loads(f.read_text(encoding="utf-8"))["prima_zi"]).isoformat()
    except FileNotFoundError:
        return None
    except (OSError, ValueError, KeyError, TypeError) as e:
        if note:
            note(f"[atenție] {f.name} nu se poate citi ({e!r}): se scrie din nou")
        return None


def zile_restante(prima: str, t: datetime, ora: ora_din_zi, pana_la: datetime | None, fara_simulari: bool = False,
                  note=None) -> list[str]:
    """Zilele de la `prima` până la ultima noapte dinaintea momentului `t`, cu jurnal, al căror lanț nu s-a încheiat."""
    out, z = [], date.fromisoformat(prima)
    while (noapte := datetime.combine(z + timedelta(days=1), ora)) < t and (pana_la is None or noapte <= pana_la):
        zi = z.isoformat()
        if not jurnal(zi).exists():
            if note:
                note(f"ziua {zi}: fără jurnal, nu e de prelucrat")
        elif citeste_stare(zi).get("rezultat") not in ({"gata", "gata_fara_simulari"} if fara_simulari or sigilata(zi) else {"gata"}):
            out.append(zi)
        z += timedelta(days=1)
    return out


def bucla(ora: ora_din_zi, pana_la: datetime | None, reia: bool = False, fara_simulari: bool = False,
          acum=datetime.now, dormi=time.sleep, de_la: str | None = None) -> int:
    """Noapte de noapte: doarme până la ora dată și prelucrează ziua precedentă; dacă o noapte eșuează, notează și așteaptă
    noaptea următoare. Următorul moment se socotește din cel precedent, deci un lanț mai lung de 24 h nu sare peste o zi.
    Cu --reia, la pornire se reiau întâi, în ordine, zilele neîncheiate de la prima zi a buclei (o repornire a
    calculatorului, una sau mai multe nopți fără buclă); prima zi e `de_la` sau cea păstrată în bucla.json, altfel ultima
    noapte trecută."""
    DIR_LANT.mkdir(parents=True, exist_ok=True)
    jr = DIR_LANT / "bucla.txt"
    note = lambda mesaj: noteaza(jr, mesaj)
    note(f"bucla pornită: ora {ora:%H:%M}, până la {pana_la:%d.%m.%Y %H:%M}" if pana_la else f"bucla pornită: ora {ora:%H:%M}")
    note(prioritate_scazuta()[1])
    esecuri = 0

    def noapte(zi: str) -> None:
        nonlocal esecuri
        try:
            cod = lant(zi, (), reia, fara_simulari)
        except (Exception, SystemExit):
            note(traceback.format_exc())
            cod = 1
        if cod == 0:
            note(f"ziua {zi}: gata")
        else:
            esecuri += 1
            note(f"ziua {zi}: EȘUATĂ (cod {cod}, vezi outputs/lant/{zi}/jurnal.txt); aștept noaptea următoare; pentru "
                 f"reluare: python -m romana.lant_zilnic --zi {zi} --reia")

    t = urmatoarea_ora(acum(), ora)
    salvata = prima_zi_buclei(note)
    prima = de_la or salvata or zi_implicita(t - timedelta(days=1) if reia else t)
    if prima != salvata:
        try:
            (DIR_LANT / FISIER_BUCLA).write_text(json.dumps({"prima_zi": prima}), encoding="utf-8")
        except OSError as e:
            note(f"[atenție] {FISIER_BUCLA} nu s-a putut scrie: {e!r}")
    restante = zile_restante(prima, t, ora, pana_la, fara_simulari, note)
    if restante and not reia:
        note(f"zile neîncheiate: {', '.join(restante)}; se reiau cu --bucla --reia sau cu --zi <zi> --reia")
    for zi in restante if reia else ():
        note(f"ziua {zi}: lanțul nu s-a încheiat, se reia acum")
        noapte(zi)
    while pana_la is None or t <= pana_la:
        zi = zi_implicita(t)
        note(f"aștept până la {t:%d.%m %H:%M} (ziua {zi})")
        while (ramas := (t - acum()).total_seconds()) > 0:
            dormi(min(60.0, ramas))     # pași scurți: ceasul rămâne corect și după o adormire a calculatorului
        noapte(zi)
        t += timedelta(days=1)
    note(f"bucla încheiată; nopți eșuate: {esecuri}")
    return 1 if esecuri else 0


# ------------------------------------------------------------------------------------------------ linia de comandă
def uscat(zi: str, exclude=(), fara_simulari: bool = False, planificata: bool = False, desigilat: bool = False) -> int:
    """Afișează comenzile, fără să ruleze nimic și fără să scrie vreun fișier. O zi planificată de buclă va fi încheiată când
    îi vine rândul, deci garda zilei curente nu i se aplică."""
    raw = jurnal(zi)
    print(f"[uscat] ziua {zi}: nu se rulează nimic")
    if not planificata and zi_scrisa_live(zi):
        print("colectarea rulează, iar CSV-ul zilei e scris live (lanțul s-ar opri aici)")
    print(f"jurnalul: {raw}" + ("" if raw.exists() else " (LIPSEȘTE: lanțul s-ar opri aici)"))
    try:
        ex = excluderi_zi(zi, exclude)
    except (OSError, ValueError, csv.Error) as e:
        print(f"excluderile nu se pot citi: {e} (lanțul s-ar opri aici)")
        return 1
    print("excluderi: " + (", ".join(ex) if ex else "niciuna"))
    try:
        grila = goluri_grila(zi)
        print("goluri în grila numărătorilor de acum, adăugate la excluderi (lanțul le recalculează după renumărare): "
              + (", ".join(uneste(grila)) or "niciunul"))
        ex = uneste([*map(minute_interval, ex), *grila])
    except Exception as e:              # de obicei, CSV-ul zilei nu există încă
        print(f"grila numărătorilor nu se poate citi acum ({type(e).__name__}); lanțul o citește după renumărare")
    if zi in ROLURI:
        print(f"rolul zilei (§ 9.11): {ROLURI[zi]}" + (", fără simulări până la desigilare" if sigilata(zi) and not desigilat else ""))
    for p in pasi(zi, ex, fara_simulari, desigilat):
        print(f"[{p.nume}] {subprocess.list2cmdline(p.comanda)}")
    return 0


def zi_valida(text: str) -> str:
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text}: formatul este AAAA-LL-ZZ") from None


def interval_valid(text: str) -> str:
    try:
        minute_interval(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None
    return text


def ora_valida(text: str) -> ora_din_zi:
    try:
        return datetime.strptime(text, "%H:%M").time()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text}: formatul este HH:MM") from None


def moment_valid(text: str) -> datetime:
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text}: formatul este „AAAA-LL-ZZ HH:MM”") from None


def main(argv=None) -> int:
    for flux in (sys.stdout, sys.stderr):   # diacriticele merg și când ieșirea e redirecționată fără UTF-8 (cp1250)
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", type=zi_valida, help="AAAA-LL-ZZ (implicit ziua de ieri)")
    ap.add_argument("--exclude", nargs="+", action="extend", default=[], type=interval_valid, metavar="HH:MM-HH:MM",
                    help="sferturile de oră scoase din ferestrele scenariilor, pe lângă excluderi.json și reporniri")
    ap.add_argument("--fara-simulari", action="store_true", help="se oprește după scenarii, fără validare și analize")
    ap.add_argument("--desigileaza", action="store_true", help="cu --zi: rulează simulările unei zile de test sau de generalizare, "
                                                               "după ce un candidat e fixat pe validare (§ 9.11)")
    ap.add_argument("--uscat", action="store_true", help="afișează comenzile, fără să ruleze nimic")
    ap.add_argument("--reia", action="store_true", help="sare peste pașii încheiați cu cod 0 (după o repornire)")
    ap.add_argument("--bucla", action="store_true", help="doarme până la --ora și prelucrează ziua precedentă, noapte de noapte")
    ap.add_argument("--ora", type=ora_valida, help="cu --bucla: ora pornirii, HH:MM (implicit 00:15)")
    ap.add_argument("--pana-la", type=moment_valid, help="cu --bucla: ultimul moment de pornire, „AAAA-LL-ZZ HH:MM”")
    ap.add_argument("--de-la", type=zi_valida, help="cu --bucla: prima zi de care răspunde bucla, păstrată în "
                                                    "outputs/lant/bucla.json (implicit, cea de la prima pornire)")
    args = ap.parse_args(argv)
    if args.bucla and (args.zi or args.exclude):
        ap.error("cu --bucla nu se dau --zi sau --exclude: excluderile fiecărei zile merg în outputs/lant/excluderi.json")
    if not args.bucla and (args.ora or args.pana_la or args.de_la):
        ap.error("--ora, --pana-la și --de-la merg doar cu --bucla")
    if args.desigileaza and not args.zi:
        ap.error("--desigileaza merge doar cu --zi")
    ora = args.ora or ORA_IMPLICITA
    if args.uscat:
        if not args.bucla:
            return uscat(args.zi or zi_implicita(), args.exclude, args.fara_simulari, desigilat=args.desigileaza)
        acum = datetime.now()
        plan = noptile(acum, ora, args.pana_la)
        if args.reia:
            t = urmatoarea_ora(acum, ora)
            prima = args.de_la or prima_zi_buclei() or zi_implicita(t - timedelta(days=1))
            print(f"[uscat] la pornire, bucla ar relua (de la {prima}): "
                  + (", ".join(zile_restante(prima, t, ora, args.pana_la, args.fara_simulari)) or "nicio zi"))
        print("[uscat] bucla ar prelucra: " + ("; ".join(f"{t:%d.%m %H:%M} → ziua {z}" for t, z in plan) or "nicio zi"))
        return uscat(plan[0][1], (), args.fara_simulari, planificata=True) if plan else 0
    try:
        if args.bucla:
            return bucla(ora, args.pana_la, args.reia, args.fara_simulari, de_la=args.de_la)
        return lant(args.zi or zi_implicita(), args.exclude, args.reia, args.fara_simulari, args.desigileaza)
    except KeyboardInterrupt:
        print("oprit cu Ctrl+C; lanțul se reia cu --reia", flush=True)
        return 130


if __name__ == "__main__":
    sys.exit(main())
