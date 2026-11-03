"""Validarea geamănului față de cameră (§ 6.5), pe aceeași oră și pe același ceas. Doar pe măsura nouă, `cor_zi_*`; măsura veche nu intră aici.

Semaforul geamănului e semaforul rejucat din jurnalul zilei (`rejucat.py`), deci camera și geamănul se pot pune pe același ceas: secundele de la începutul fiecărui val de pe Magheru.
Rândurile stau pe patru grupuri, fără niciun total, fiindcă un total nu deosebește nimic: un geamăn cu vehicule absurd de rapide și unul fără pietoni au scoruri apropiate de ale celui de bază.
  A. din cerere: debitele pe brațe. Cererea vine din aceleași numărători, deci aici se vede doar dacă geamănul reușește să o ducă, inclusiv supraîncărcarea de pe Dacia vest;
  B. independente de cerere, măsoară fizica: debitul de vârf pe 20 s (el are factorul brațului, deci depinde de el, iar rândul o spune); timpul zonă–zonă, cu același cod de zone pe ambele capete; decalajul de
     cea mai bună aliniere, pe forme, deci fără factori; ieșirea Dacia est în etapa N–S și în secundele 24–60 ale etapei, față de pietoni; pietonii de pe zebra Dacia est, ca număr și ca histogramă; regresia
     vehiculelor pe durata valului (doar diagnostic, corelația nu e o dovadă); cererea pe fiecare pereche O–D, față de traiectoriile complete din cameră, fără factori;
  C. verificarea ceasului și a ferestrelor: profilele pe ciclu. Un model fără nicio fizică, cu debit constant în fereastra de verde, le trece aproape pe toate, deci ele nu arată că geamănul reproduce camera.
     Fiecare are două repere: modelul nul eșantionat și zgomotul camerei; unde nulul e sub p95 din zgomot, rândul e „neinformativ”. Nu există regula „trece doar dacă bate nulul”: ar respinge și un geamăn perfect;
  D. siguranță și limite: teleportări și rulări cu blocaj presupus, ciocnirile văzute de SUMO, atingerile geometrice, intrările pietonilor pe roșu, vehiculele neintrate, pierderea totală și pe ramuri. Pierderea e doar raportată.

Fiecare rând se calculează pe mai multe seed-uri: profilele se compară pe media lor, iar verdictul ține cont de intervalul dintre seed-uri („în prag”, „peste prag” sau „nedecis”, dacă intervalul trece peste prag).
Intervalul e p10–p90 de la 5 seed-uri în sus, ca o singură rulare blocată să nu facă din el verdicte, și min–max sub atât; un seed care iese din rând se scrie în notă. La decalaj, intervalul și zgomotul seed-urilor
vin din media fără câte un seed, fiindcă pe un seed singur curba are adesea două minime aproape egale. Un prag care atinge plaja de căutare face rândul „neinformativ”: rândul n-ar mai putea pica.
Probele `--proba fara_pietoni` și `--proba rapid` sunt gemeni greșiți dinadins, pe aceleași rânduri: o măsură e utilă doar dacă îi deosebește de bază. Pe profile și pe forme, proba se compară direct cu baza, nu prin
distanța lor față de cameră. Lista măsurilor utile se dă doar cu probele pe cel puțin 2 seed-uri.

Geamănul se citește cu același cod de zone ca jurnalul camerei, prin camera virtuală, acolo unde ea prinde aproape toate vehiculele; în rest, pe muchie, iar nota rândului dă diferența pe același vehicul (`LIMITE`).

Pietonii din cameră rămân doar agregat: momentele de intrare pe zebră, în `outputs/validare`, din jurnalul local; nu se afișează și nu se salvează traiectorii.

Exemple:
  python -m romana.control.valideaza_geaman cor_zi_2026-10-26_varf --out docs/rezultate/validare_geaman.csv
  python -m romana.control.valideaza_geaman cor_zi_2026-10-26_varf --proba fara_pietoni --proba rapid --seeds-proba 1,2
  python -m romana.control.valideaza_geaman cor_zi_2026-10-26_varf --scrie-praguri outputs/validare/praguri.json       # cel puțin 5 seed-uri; apoi: --praguri outputs/validare/praguri.json
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from array import array
from pathlib import Path

import numpy as np
import pandas as pd

from romana.bridge.od_estimation import PRAG_INTUNERIC_GRADE, factor_brat, inaltime_soare
from romana.common import CONFIG_DIR, COUNTS_COR_DIR, DEMAND_DIR, OUTPUT_DIR, ROOT, TRAJ_DIR, TRAJ_RAW_DIR
from romana.control.faze import info_v2
from romana.control.rejucat import ORIZONT_S, evenimente_zi, fereastra_scenariu, program_rejucat, valuri
from romana.vision.od_counter import PEDESTRIAN, Params, classify, load_zones
from romana.vision.recount import read_trajectories

BRATE = {"magheru": "668307642#1", "catargiu": "1320256482", "dacia_est": "232079775#2", "dacia_vest": "-778823268#2"}    # muchia dinaintea liniei de oprire
# unde stau zonele camerei în rețea, din proiecție (§ 4.3): zona lui Catargiu e departe de linia de oprire, în mijlocul pieței
PUNCTE_INTRARE = {"catargiu": ("23781788", "122141742#4")}
IESIRI = {"catargiu": ("668307633#0", "668307633#1", "668307633#2"), "magheru": ("44499684#0", "44499684#1", "44499684#2"),
          "dacia_est": ("119238380#0", "119238380#1"), "dacia_vest": ("778823268#0", "778823268#2")}
TRECERE_DACIA_EST = 55
INCALZIRE_S, SFARSIT_S = 300, 3600
BIN_S, BINI = 10, 16
BINE = np.arange(0, (BINI + 1) * BIN_S, BIN_S)
VEHICULE = {"passenger", "truck", "bus", "motorcycle"}
FEREASTRA_VARF_S = 20             # debitul de vârf
PIETONI_DE_LA_S, PIETONI_PANA_LA_S = 24, 60      # fereastra pietonilor de pe Dacia est, de la începutul etapei N–S
PLAJA_DECALAJ_S = 25
MIN_TRAIECTORII = 15              # sub atâtea traiectorii, timpul zonă–zonă nu se judecă
MIN_PARTE_CU_ORIGINE = 0.25       # sub atât, momentele unei ieșiri din cameră sunt mai ales traiectorii pierdute sau apărute pe drum, deci forma lor măsoară detectorul
MIN_SEEDURI_PERCENTILE = 5        # sub atâtea seed-uri, p10–p90 n-are sens: intervalul e min–max
ACOPERIRE_VIRTUALA = 0.90         # de aici în sus, camera virtuală prinde aproape toate vehiculele unei muchii, deci momentele se iau din ea
TOLERANTA_CERERE = 0.03           # pe toate orele privite, cererea din rute stă la cel mult 1,9% de cameră × factor; peste atât, rutele s-au făcut cu alți factori
SAMANTA = 20261102                # reeșantionările și modelul nul sunt reproductibile
# Mișcările timpului zonă–zonă: (origine, destinație, cuantile, departe de cameră). Pe cele îndepărtate, eroarea proiecției e cea mai mare, deci toleranța are un minim („timp_departe”)
MISCARI = (("magheru", "dacia_est", (50, 75), False), ("magheru", "catargiu", (50,), True), ("catargiu", "magheru", (50,), True))
CUTIE_PIATA = (985.0, 1197.0, 775.0, 985.0)       # x0, x1, y0, y1, în coordonatele rețelei: toate zonele de intrare și de ieșire ale camerei încap în ea
# Axa spre nord și inelul se ating în rețea din cauza geometriei din OSM (§ 6.5): se numără separat
AXA, INEL = (":2404247023_2_", "241212606", "23781801"), (":33389729_3_", "448266588#0", ":494777546_0_", "448266588#1")
MODEL_CAMERA = ROOT / "docs" / "rezultate" / "referinta" / "model_camera.json"
PROBE_DIR = OUTPUT_DIR / "validare" / "probe"
RULARI_DIR = OUTPUT_DIR / "validare" / "rulari"
GRUPURI = {"A": "din cerere", "B": "independente de cerere, măsoară fizica", "C": "verificarea ceasului și a ferestrelor", "D": "siguranță și limite"}
CHEI_CAPAT = {"intrare": "brate", "ieșire": "iesiri"}
CITIRE_NS = ("ieșire în N–S", "dacia_est")      # muchia ieșirii e chiar la zebră, deci după așteptare; zona camerei începe mult înainte
# Orele care n-au influențat alegerea măsurilor, ambele de duminică: toate celelalte au fost privite în cele patru runde.
# 1.11 seara: pe 2.11, un revizor a rulat un seed și a văzut rândurile ei; nicio reparație nu stă pe ele. Autorul hotărăște dacă rămâne aici.
ORE_NEATINSE = {"cor_zi_2026-11-01_seara", "cor_zi_2026-10-25_varf"}
# Măsurile s-au stabilit în patru runde pe aceste ore, după ce s-au văzut rezultatele (§ 6.5); de la un commit numit se îngheață, iar prima judecată curată e o zi nouă.
# Aici stau doar pragurile scrise de mână: abatere relativă sau valoare maximă pe rulare. Celelalte se calculează din reeșantionarea camerei și din zgomotul seed-urilor, pe braț,
# iar autorul le fixează într-un fișier (--praguri) înaintea zilei de validare. „pietoni_detectie”: cât de bine prinde camera pietonii, pe zebra din prim-plan.
PRAGURI = {"debit": 0.10, "timp_departe": 0.25, "pietoni_detectie": 0.10, "teleportari": 5, "ciocniri_vehicule": 5, "pieton_in_miscare_fractie": 0.01, "neintrate_fractie": 0.02}
# Poarta din § 9.11: geamănul duce cererea orei, fără teleportări în masă. Dacia vest nu intră, fiindcă se știe că acolo nu trece (§ 6.5), dar lipsa de capacitate se vede la vehiculele neintrate.
POARTA = ("debit, veh/h: magheru", "debit, veh/h: catargiu", "debit, veh/h: dacia_est", "teleportări", "ciocniri între vehicule văzute de SUMO", "vehicule neintrate sau nesosite la final, parte din vehicule", "pierdere de detecție pe întuneric")
# Seara din 2.11, pe întuneric și pe asfalt ud: pe Dacia vest, referința e de ≈3 ori peste detector, deși ziua, pe ploaie, factorii rămân normali, iar debitul real nu scade (ieșirile din prim-plan
# îl confirmă). Doar din cameră, fără simulare: X = ieșirile Dacia est fără virajul Magheru → Dacia est, V = intrările Dacia vest. Pe lumină, X/V e cel mult 1,44, iar pe 26.10 pe întuneric, cel mult 1,40;
# pe 2.11, 17:00–20:00, 2,27–3,67. Pragul stă pe o singură seară dintre zilele permise, deci e o ipoteză declarată (§ 9.11). Ora marcată iese din decizie, cu variantele ei.
PIERDERE_DETECTIE = {"raport": 1.8, "magheru": 600, "x": 100}
# Rândurile la care s-a renunțat și de ce, ca istoria validării să se vadă (§ 6.5)
RENUNTATE = {
    "Total în prag": "nu deosebește nimic: un geamăn greșit dinadins avea aproape același scor cu cel de bază;",
    "drumul Magheru → Catargiu, pe muchii": "măsura alt drum decât camera (linie de oprire → muchie, cu valori întregi); în locul lui, timpul zonă–zonă, cu același cod pe ambele capete;",
    "Magheru, primele 20 s din val": "în locul lui, debitul de vârf pe 20 s, pe toate intrările, și decalajul de aliniere;",
    "Magheru, corelația vehiculelor pe val": "vine din durata valului; rămâne regresia pe durată, ca diagnostic;",
    "pietoni în secundele 20–70": "fereastra largă ascundea nepotrivirea; în locul ei, numărul pe oră și histograma pe 10 s;",
    "ieșirile Mendeleev și Căderea Bastiliei, la decalaj și la formă": "momentele camerei de acolo nu sunt vehicule urmărite până la ieșire: pe 26.10 vârf, pe Mendeleev, 19 din 430 au și origine, iar pe Căderea Bastiliei sunt 85, cam 4 pe val; "
                                                                       "cererea spre ele e 69 și 127 veh/h, din Furness și din distribuția a priori. Un profil de aici ar măsura detectorul, nu semaforul."}
# Ce nu acoperă rândurile, spus la fiecare rulare
LIMITE = {
    "același cod de zone": f"la timpul zonă–zonă e probat doar pe cele trei mișcări din MISCARI. Momentele de pe capete se iau din camera virtuală doar unde ea prinde cel puțin {ACOPERIRE_VIRTUALA:.0%} din vehiculele de pe muchie, pe toate seed-urile "
                           "(pe 26.10 vârf: intrările Magheru, Catargiu, Dacia est și ieșirile Catargiu, Magheru). În rest (intrarea Dacia vest ≈15%, ieșirea Dacia est ≈72%, ieșirea Dacia vest 0%) codul nu se poate generaliza așa cum e, "
                           "deci geamănul se citește pe muchie, iar nota rândului dă diferența pe același vehicul; ea nu e un decalaj de semafor. De ce pierde camera virtuală acele vehicule n-a fost cercetat;",
    "bara din față": "camera virtuală folosește bara din față a vehiculului, camera punctul de contact cu solul. La timpul zonă–zonă, diferența se scade; pe momentele de pe capete rămâne, necorectată și nemăsurată: cam jumătate de vehicul, deci ≈0,5 s la 5 m/s;",
    "ceasul": "`evaluate.run_one` dă observatorului indicele buclei, `t`, iar ceasul SUMO după pas e t + 1. În `Contoare`, ce s-a întâmplat în pas are momentul t + 0,5, cu o eroare de citire de cel mult 0,5 s, pozițiile sunt ale sfârșitului pasului, t + 1, iar starea "
              "semaforului rămâne la t, fiindcă se schimbă la începutul pasului (măsurat: primul vehicul de la linie iese de pe muchie chiar în pasul t);",
    "pietonii": "detectorul pierde persoanele din mulțimi: pe clipurile din 2.11, pe aceleași bucăți, adnotatorii văd mult mai multe. De aceea numărul de comparat e numărătoarea pe persoane × factorul de cerere ales, deci rândul verifică doar că geamănul duce cererea, iar histograma camerei nu e un criteriu;",
    "factorii": "tabelul folosește factorii de acum din demand_v2.json, iar rutele pe cei cu care s-au făcut; generatorul scrie în rezumatul zilei amprenta cererii folosite. Validarea avertizează dacă amprenta diferă sau, pe scenariile mai vechi, dacă fișierul e mai nou decât rutele, și dacă "
                f"cererea din rute se abate cu peste {TOLERANTA_CERERE:.0%} de cameră × factor. Eroarea factorilor nu e măsurată, deci nu intră în pragul vârfului: rândul dă cât s-ar muta abaterea la factor ×0,9 și ×1,1."}
_GOL = float("nan")


# --------------------------------------------------------------------- funcții de calcul, fără simulare

def profil(momente: np.ndarray, starturi: np.ndarray) -> np.ndarray:
    """Câte treceri pe ciclu, pe bucăți de 10 s de la începutul valului de pe Magheru."""
    i = np.searchsorted(starturi, momente, side="right") - 1
    d = momente[i >= 0] - starturi[i[i >= 0]]
    return np.histogram(d, bins=BINE)[0] / max(len(starturi), 1)


def abatere_profil(c: np.ndarray, g: np.ndarray) -> float:
    return float(np.abs(c - g).sum() / max(c.sum(), 1e-9))


def forma(p: np.ndarray) -> np.ndarray:
    """Profilul ca parte din total: ieșirile nu intră în cerere și au alți factori, deci doar forma lor se poate compara."""
    return p / max(p.sum(), 1e-9)


def matrice_valuri(momente: np.ndarray, starturi: np.ndarray) -> np.ndarray:
    """Pe fiecare val, câte treceri pe bucăți de 10 s; media pe rânduri e chiar `profil`."""
    i = np.searchsorted(starturi, momente, side="right") - 1
    return np.array([np.histogram(momente[i == k] - starturi[k], BINE)[0] for k in range(len(starturi))], float).reshape(len(starturi), BINI)


def matrice_ferestre(momente: np.ndarray, ferestre: np.ndarray) -> np.ndarray:
    """Pe fiecare fereastră (o etapă N–S), câte treceri pe bucăți de 10 s de la începutul ei."""
    return np.array([np.histogram(momente[(momente >= a) & (momente < b)] - a, BINE)[0] for a, b in ferestre], float).reshape(len(ferestre), BINI)


def cicluri_din(starturi: np.ndarray) -> np.ndarray:
    """Marginile ciclurilor: începuturile valurilor, plus capătul ultimului, la lungimea obișnuită."""
    if len(starturi) < 2:
        return np.asarray(starturi, float)
    return np.r_[starturi, starturi[-1] + np.median(np.diff(starturi))]


def varf_pe_cicluri(momente: np.ndarray, muchii: np.ndarray, fereastra: float = FEREASTRA_VARF_S) -> np.ndarray:
    """În fiecare ciclu, cel mai mare debit dintr-o fereastră glisantă, în vehicule pe secundă. Aceeași metodă pe cameră și pe geamăn."""
    m = np.sort(np.asarray(momente, float))
    out = []
    for a, b in zip(muchii[:-1], muchii[1:]):
        x = m[(m >= a) & (m < b)]
        out.append((np.searchsorted(x, x + fereastra, side="left") - np.arange(len(x))).max() / fereastra if len(x) else 0.0)
    return np.array(out)


def mediana(x) -> float:
    return float(np.median(x)) if len(x) else _GOL


def per_etapa(momente: np.ndarray, ferestre: np.ndarray, de_la: float, pana_la: float) -> np.ndarray:
    """Câte treceri în fiecare etapă, între secundele date de la începutul ei, fără să treacă de sfârșitul ei: după el, pe ieșire vin alte mișcări."""
    return np.array([((momente >= a + de_la) & (momente < min(a + pana_la, b))).sum() for a, b in np.asarray(ferestre, float).reshape(-1, 2)], float)


def valuri_in_fereastra(momente) -> list[tuple[float, float, int]]:
    """Valurile care încep în fereastră, calculate pe momentele netăiate, ca în `program_rejucat`: tăiat de marginea ferestrei, primul val ar începe la ea, nu la începutul lui."""
    return [v for v in valuri(np.sort(np.asarray(momente, float))) if INCALZIRE_S <= v[0] < SFARSIT_S]


def regresie(x, y) -> dict:
    """y = pantă · x + intercept: panta, eroarea ei standard, interceptul și abaterea standard a restului. Corelația nu apare: pe valuri, vine din durată."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0:
        return {"panta": _GOL, "eroare_panta": _GOL, "intercept": _GOL, "rest": _GOL}
    A = np.c_[np.ones(len(x)), x]
    b = np.linalg.lstsq(A, y, rcond=None)[0]
    e = y - A @ b
    s2 = float(e @ e) / (len(x) - 2)
    return {"panta": float(b[1]), "eroare_panta": float(np.sqrt(s2 * np.linalg.inv(A.T @ A)[1, 1])), "intercept": float(b[0]), "rest": float(np.sqrt(s2))}


def intervale_etape(faze, verzi: list[str], n: int, inceput: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Din lista de faze [(stare, durată)]: intervalele în care vehiculele sunt pe N–S și pe E–V (fereastra pietonilor nu le schimbă). `n`: câte legături de vehicule are starea."""
    t, ns, ev = inceput, [], []
    for s, d in faze:
        lista = ns if s[:n] == verzi[0][:n] else ev if s[:n] == verzi[1][:n] else None
        if lista is not None:
            if lista and abs(lista[-1][1] - t) < 1e-6:
                lista[-1][1] = t + d
            else:
                lista.append([t, t + d])
        t += d
    return np.array(ns, float).reshape(-1, 2), np.array(ev, float).reshape(-1, 2)


def ferestre_in(ferestre: np.ndarray, a: float, b: float, intregi: bool = False) -> np.ndarray:
    """Ferestrele, tăiate la intervalul [a, b); cu `intregi`, doar cele care încap întregi."""
    f = np.asarray(ferestre, float).reshape(-1, 2)
    if intregi:
        return f[(f[:, 0] >= a) & (f[:, 1] <= b)]
    f = np.c_[np.maximum(f[:, 0], a), np.minimum(f[:, 1], b)]
    return f[f[:, 1] > f[:, 0]]


def esantion_ferestre(ferestre: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """`n` momente cu debit constant în ferestrele date."""
    f = np.asarray(ferestre, float).reshape(-1, 2)
    if n <= 0 or len(f) == 0:
        return np.empty(0)
    cum = np.r_[0.0, np.cumsum(f[:, 1] - f[:, 0])]
    u = rng.uniform(0, cum[-1], n)
    k = np.minimum(np.searchsorted(cum, u, side="right") - 1, len(f) - 1)
    return f[k, 0] + u - cum[k]


def nul_esantionat(pc: np.ndarray, ferestre: np.ndarray, n: int, starturi: np.ndarray, rng: np.random.Generator, repetari: int = 200, realizari: int = 1,
                   normat: bool = False, alte_ferestre: np.ndarray | None = None, cota: float = 1.0) -> np.ndarray:
    """Modelul nul, fără nicio fizică: `n` vehicule cu debit constant în fereastra de verde rejucată. E eșantionat, ca să aibă zgomotul unei realizări; cu `realizari` > 1, e media lor, ca media seed-urilor.
    Pe o ieșire, partea `cota` vine din `ferestre` (N–S), iar restul din `alte_ferestre` (E–V). Întoarce abaterile de la profilul camerei, câte una pe repetare."""
    ab = np.empty(repetari)
    for r in range(repetari):
        ps = []
        for _ in range(realizari):
            k = n if alte_ferestre is None else int(rng.binomial(n, cota))
            m = esantion_ferestre(ferestre, k, rng)
            if alte_ferestre is not None:
                m = np.r_[m, esantion_ferestre(alte_ferestre, n - k, rng)]
            ps.append(profil(m, starturi))
        p = np.mean(ps, axis=0)
        ab[r] = abatere_profil(pc, forma(p) if normat else p)
    return ab


def zgomot_reesantionare(mat: np.ndarray, rng: np.random.Generator, repetari: int = 300, normat: bool = False) -> float:
    """p95 al abaterii profilului camerei de el însuși, când valurile se reeșantionează: cât se mișcă rândul doar din cauza valurilor prinse în acea oră."""
    if len(mat) < 2 or mat.sum() == 0:
        return _GOL
    p = mat.mean(0)
    q = mat[rng.integers(0, len(mat), (repetari, len(mat)))].mean(1)
    if normat:
        ab = np.abs(q / np.maximum(q.sum(1, keepdims=True), 1e-9) - p / p.sum()).sum(1)
    else:
        ab = np.abs(q - p).sum(1) / p.sum()
    return float(np.percentile(ab, 95))


def zgomot_statistica(valori, statistica, rng: np.random.Generator, repetari: int = 300, relativ: bool = True) -> float:
    """p95 al abaterii unei statistici când unitățile (cicluri, valuri, traiectorii) se reeșantionează."""
    v = np.asarray(valori, float)
    if len(v) < 2:
        return _GOL
    s = statistica(v)
    b = np.array([statistica(v[rng.integers(0, len(v), len(v))]) for _ in range(repetari)])
    ab = np.abs(b - s)
    ab = ab[np.isfinite(ab)]
    if len(ab) == 0:
        return _GOL
    return float(np.percentile(ab / abs(s) if relativ and s else ab, 95))


def _margine_seeduri(abateri: list[float]) -> float:
    """Marginea de sus a abaterilor seed-urilor: p90 de la 5 seed-uri în sus, ca o singură rulare blocată să nu lărgească pragul, și cea mai mare sub atât."""
    return float(np.percentile(abateri, 90)) if len(abateri) >= MIN_SEEDURI_PERCENTILE else float(max(abateri))


def zgomot_seeduri(profile: list[np.ndarray]) -> float:
    """Zgomotul seed-urilor pe un profil: cât se abate un seed de media celorlalte, în aceeași măsură ca rândul. Cu un singur seed, nu se poate ști."""
    if len(profile) < 2:
        return _GOL
    P = np.asarray(profile)
    return _margine_seeduri([abatere_profil(np.delete(P, i, 0).mean(0), P[i]) for i in range(len(P))])


def zgomot_seeduri_scalar(valori) -> float:
    """La fel, pe un rând cu o singură cifră."""
    v = np.asarray(valori, float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        return _GOL
    return _margine_seeduri([abs(v[i] - np.delete(v, i).mean()) for i in range(len(v))])


def prag_din_zgomot(*termeni) -> float:
    """Pragul unui rând: zgomotul camerei, al seed-urilor și, unde e cazul, eroarea proiecției, care sunt independente, se adună în cuadratură."""
    t = [float(x) for x in termeni if x is not None and np.isfinite(x)]
    return float(np.sqrt(np.sum(np.square(t)))) if t else _GOL


def verdict_interval(abateri, prag: float) -> str:
    """„în prag” dacă toate abaterile date sunt sub prag, „peste prag” dacă toate sunt peste, „nedecis” dacă intervalul trece peste prag."""
    v = np.abs(np.asarray(abateri, float))
    v = v[np.isfinite(v)]
    if len(v) == 0 or prag is None or not np.isfinite(prag):
        return "–"
    if v.max() <= prag:
        return "în prag"
    return "peste prag" if v.min() > prag else "nedecis"


def interval_seeduri(valori) -> tuple[float, float]:
    """Intervalul dintre seed-uri: p10–p90, ca o singură rulare blocată să nu facă din el verdicte. Sub 5 seed-uri, percentilele n-au sens și rămâne min–max."""
    v = np.asarray(valori, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return _GOL, _GOL
    if len(v) < MIN_SEEDURI_PERCENTILE:
        return float(v.min()), float(v.max())
    lo, hi = np.percentile(v, [10, 90])
    return float(lo), float(hi)


def seed_exceptie(valori, parte: float = 0.05) -> int | None:
    """Poziția seed-ului care iese vizibil din rândul celorlalte: e mai departe de mediana lor decât de trei ori plaja lor, și mai mult decât `parte` din mediană. De la 4 seed-uri; sub atât, nu se poate spune.
    Dacă toate celelalte sunt identice, plaja lor e 0 și nu spune nimic: la valori rare (teleportări) sau în trepte (timpul, pe 0,2 s), o diferență mică ar părea excepție."""
    v = np.asarray(valori, float)
    poz = np.flatnonzero(np.isfinite(v))
    if len(poz) < 4:
        return None
    x = v[poz]
    i = int(np.argmax(np.abs(x - np.median(x))))
    rest = np.delete(x, i)
    med, plaja = float(np.median(rest)), float(np.ptp(rest))
    return int(poz[i]) if plaja > 0 and abs(x[i] - med) > max(3 * plaja, parte * abs(med)) else None


def decalaj_aliniere(pc: np.ndarray, lista: list[tuple[np.ndarray, np.ndarray]], normat: bool = False, plaja: int = PLAJA_DECALAJ_S, a: float = INCALZIRE_S, b: float = SFARSIT_S) -> tuple[int, float, float]:
    """Cu câte secunde trebuie mutat geamănul ca profilul lui să se așeze cel mai bine peste cel al camerei: negativ, dacă în cameră vehiculele vin mai devreme.
    `lista`: (momentele, începuturile valurilor) pe fiecare seed; profilul e al mediei. Întoarce (decalajul, abaterea la el, abaterea la 0); la egalitate, decalajul cel mai mic."""
    L = {}
    for dl in range(-plaja, plaja + 1):
        ps = []
        for m, s in lista:
            x = m + dl
            ps.append(profil(x[(x >= a) & (x < b)], s))
        p = np.mean(ps, axis=0)
        L[dl] = abatere_profil(pc, forma(p) if normat else p)
    k = min(L, key=lambda d: (round(L[d], 9), abs(d)))
    return k, L[k], L[0]


def decalaje_fara_cate_unul(pc: np.ndarray, lista: list[tuple[np.ndarray, np.ndarray]], normat: bool = False, plaja: int = PLAJA_DECALAJ_S) -> list[int]:
    """Cât se mută alinierea mediei când se scoate câte un seed; de aici vin zgomotul seed-urilor și intervalul rândului. Pe un seed singur, curba are adesea două minime aproape egale, deci alinierea lui sare, deși a mediei stă pe loc."""
    if len(lista) < 2:
        return []
    return [decalaj_aliniere(pc, lista[:i] + lista[i + 1:], normat, plaja)[0] for i in range(len(lista))]


def zgomot_decalaj(momente: np.ndarray, starturi: np.ndarray, rng: np.random.Generator, repetari: int = 200, plaja: int = PLAJA_DECALAJ_S, a: float = INCALZIRE_S, b: float = SFARSIT_S) -> float:
    """p95 al decalajului de aliniere dintre profilul întreg al camerei și unul cu valurile reeșantionate: cât de bine se poate măsura un decalaj pe acea oră."""
    if len(starturi) < 2 or len(momente) == 0:
        return _GOL
    mats = []
    for dl in range(-plaja, plaja + 1):
        x = momente + dl
        mats.append(matrice_valuri(x[(x >= a) & (x < b)], starturi))
    mats = np.array(mats)                                                   # decalaj × val × bucată
    p = mats[plaja].mean(0)
    q = mats[:, rng.integers(0, len(starturi), (repetari, len(starturi))), :].mean(2)     # decalaj × repetare × bucată
    q = q / np.maximum(q.sum(2, keepdims=True), 1e-9)
    return float(np.percentile(np.abs(np.abs(q - p / max(p.sum(), 1e-9)).sum(2).argmin(0) - plaja), 95))


def deosebeste(b: float, b_lo: float, b_hi: float, p: float, p_lo: float, p_hi: float, prag: float, marja: float = 0.10):
    """O probă se deosebește de bază pe un rând dacă intervalele lor nu se ating, iar diferența e peste pragul rândului (la un rând fără prag, peste `marja` din valoarea de bază). None: nu se poate spune."""
    if not (np.isfinite(b) and np.isfinite(p)):
        return None
    if p_lo <= b_hi and b_lo <= p_hi:
        return False
    return bool(abs(p - b) > (prag if prag is not None and np.isfinite(prag) else marja * abs(b)))


def deosebeste_profil(baza: np.ndarray, proba: np.ndarray, prag: float) -> tuple[float, bool | None]:
    """Pe rândurile de profil și de formă, distanța chiar dintre profilul probei și cel al bazei, față de pragul rândului: la aceeași distanță de cameră, proba poate fi în altă parte decât baza. None: nu se poate spune."""
    d = abatere_profil(baza, proba) if baza.sum() > 0 else _GOL
    if not np.isfinite(d) or prag is None or not np.isfinite(prag):
        return d, None
    return d, bool(d > prag)


def perechi_suprapuse(x: np.ndarray, y: np.ndarray, unghi: np.ndarray, L: np.ndarray, W: np.ndarray) -> list[tuple[int, int, float]]:
    """Perechile de vehicule cu dreptunghiurile suprapuse, cu adâncimea pătrunderii (axe separatoare). (x, y) e bara din față; unghiul, ca în SUMO: 0 = nord, în sensul acelor de ceasornic."""
    a = np.radians(unghi)
    hx, hy = np.sin(a), np.cos(a)
    mx, my = x - hx * L / 2, y - hy * L / 2
    r = np.hypot(L, W) / 2
    ii, jj = np.nonzero(np.triu((mx[:, None] - mx) ** 2 + (my[:, None] - my) ** 2 < (r[:, None] + r) ** 2, 1))
    out = []
    for i, j in zip(ii.tolist(), jj.tolist()):
        adanc = 1e9
        for ax, ay in ((hx[i], hy[i]), (hy[i], -hx[i]), (hx[j], hy[j]), (hy[j], -hx[j])):
            ri = abs(hx[i] * ax + hy[i] * ay) * L[i] / 2 + abs(hy[i] * ax - hx[i] * ay) * W[i] / 2
            rj = abs(hx[j] * ax + hy[j] * ay) * L[j] / 2 + abs(hy[j] * ax - hx[j] * ay) * W[j] / 2
            adanc = min(adanc, ri + rj - abs((mx[i] - mx[j]) * ax + (my[i] - my[j]) * ay))
            if adanc <= 0:
                break
        if adanc > 0:
            out.append((i, j, float(adanc)))
    return out


def atinge_pieton(px: np.ndarray, py: np.ndarray, x: np.ndarray, y: np.ndarray, unghi: np.ndarray, L: np.ndarray, W: np.ndarray) -> np.ndarray:
    """Pieton × vehicul: centrul pietonului cade în dreptunghiul vehiculului, cu marginea tipului „pieton” (0,25 m lateral, 0,15 m în lung)."""
    a = np.radians(unghi)
    hx, hy = np.sin(a), np.cos(a)
    dx, dy = px[:, None] - x, py[:, None] - y
    ina, lat = dx * hx + dy * hy, dx * hy - dy * hx
    return (ina <= 0.15) & (ina >= -L - 0.15) & (np.abs(lat) <= W / 2 + 0.25)


def pe_axa_si_inel(benzi_i: set, benzi_j: set) -> bool:
    ax = lambda s: any(b.startswith(AXA) for b in s)    # noqa: E731
    inel = lambda s: any(b.startswith(INEL) for b in s)     # noqa: E731
    return (ax(benzi_i) and inel(benzi_j)) or (ax(benzi_j) and inel(benzi_i))


def asteptare_evitata(intrari_rosu, stari: list[tuple[int, str]]) -> float:
    """Câte secunde ar mai fi așteptat, în total, pietonii intrați pe roșu: până la următorul verde al trecerii lor. intrari_rosu: [(moment, legătura)]; stari: [(moment, starea semaforului)], doar schimbările."""
    T = np.array([t for t, _ in stari])
    tot = 0.0
    for t, i in intrari_rosu:
        for k in range(int(np.searchsorted(T, t, side="right")), len(T)):
            if stari[k][1][i] in "Gg":
                tot += float(T[k] - t)
                break
    return tot


def tipuri_rapide(text: str) -> str:
    """Vehicule absurd de rapide: accelerație 4, decelerație 7, sigma 0, minGap 1, speedFactor 1,3. Viteza maximă și speedDev merg cu speedFactor, altfel plafonul tipului l-ar anula. Pietonii și bicicletele rămân la fel."""
    def schimba(m):
        s = m.group(0)
        if 'vClass="pedestrian"' in s or 'vClass="bicycle"' in s:
            return s
        for k, v in (("accel", "4"), ("decel", "7"), ("sigma", "0"), ("maxSpeed", "30")):
            s = re.sub(rf'\b{k}="[^"]*"', f'{k}="{v}"', s)
        return s.replace("<vType ", '<vType minGap="1" speedFactor="1.3" speedDev="0" ', 1)
    return re.sub(r"<vType [^>]*>", schimba, text)


# --------------------------------------------------------------------- aceleași zone pe cameră și pe geamăn

def zone_pe_brate(zone: list) -> tuple[dict, dict]:
    intrari, iesiri = {}, {}
    for z in zone:
        if z.role == "intrare":
            intrari.setdefault(z.arm, []).append(z)
        elif z.role == "iesire":
            iesiri.setdefault(z.arm, []).append(z)
    return intrari, iesiri


def momente_traiectorie(tip: str, pts: list, zone: list, intrari: dict, iesiri: dict, params: Params) -> tuple:
    """(origine, destinație, primul moment în zona de intrare, primul moment în zona de ieșire): același cod pentru traiectoriile camerei și pentru urmele geamănului."""
    c = classify(tip, pts, zone, params)
    o, d = c.get("origine"), c.get("destinatie")
    t_o = next((t for t, x, y in pts if any(z.contains_norm(x, y) for z in intrari[o])), None) if o else None
    t_d = next((t for t, x, y in pts if any(z.contains_norm(x, y) for z in iesiri[d])), None) if d else None
    return o, d, t_o, t_d


def taie_dupa_iesire(pts: list, zone_iesire: list) -> list:
    """Geamănul își ține vehiculele în cadru și după ce au ieșit din zonă, camera le pierde. Urma se taie explicit la ultimul punct dintr-o zonă de ieșire, altfel regula `capat_traiectorie` le-ar respinge pe toate."""
    for i in range(len(pts) - 1, -1, -1):
        if any(z.contains_norm(pts[i][1], pts[i][2]) for z in zone_iesire):
            return pts[:i + 1]
    return pts


def urma_in_imagine(t: np.ndarray, x: np.ndarray, y: np.ndarray, pr, roi_y: tuple, pas: float = 0.2) -> list:
    """Urma unui vehicul din geamăn, proiectată în imagine: poziția e interpolată la pasul camerei, iar din oprirea lungă rămân doar capetele. Doar ce cade în cadru și în zona de interes a camerei."""
    tt = np.arange(t[0], t[-1] + 1e-6, pas)
    wx, wy = np.interp(tt, t, x), np.interp(tt, t, y)
    im = pr.lume_spre_img(np.c_[wx, wy])
    ok = np.isfinite(im[:, 0]) & (im[:, 0] >= 0) & (im[:, 0] <= 1) & (im[:, 1] >= roi_y[0]) & (im[:, 1] <= roi_y[1])
    if len(tt) > 1:
        merge = np.hypot(np.diff(wx), np.diff(wy)) > 1e-3
        ok &= np.r_[True, merge] | np.r_[merge, True]
    return [(float(a), float(b), float(c)) for a, b, c in zip(tt[ok], im[ok, 0], im[ok, 1])]


def eroare_proiectie_s(pr, tau: float, t: np.ndarray, x: np.ndarray, y: np.ndarray, px: float) -> float:
    """Eroarea proiecției într-un punct al urmei, în secunde: `px` pixeli pe verticală, în metri pe stradă (cu perspectiva, cel mai mult spre fundal), la viteza vehiculului acolo (cel puțin 2 m/s)."""
    w = np.array([np.interp(tau, t, x), np.interp(tau, t, y)])
    v = np.hypot(np.interp(tau + 1, t, x) - np.interp(tau - 1, t, x), np.interp(tau + 1, t, y) - np.interp(tau - 1, t, y)) / 2
    im = pr.lume_spre_img(w)[0]
    alaturi = pr.img_spre_lume(np.array([[im[0], im[1] + px / pr.H], [im[0], im[1] - px / pr.H]]))
    return float(np.hypot(*(alaturi - w).T).max()) / max(float(v), 2.0)


def camera_virtuala(urme: np.ndarray, tipuri: list[str], zone: list, roi_y: tuple) -> dict:
    """Urmele geamănului (moment, vehicul, x, y), trecute prin același cod de zone ca jurnalul camerei. Întoarce traiectoriile complete, cu timpul zonă–zonă, în „complete”: (origine, destinație, t_o, t_d, eroarea proiecției în s);
    și, la „intrare” și „ieșire”, pe fiecare braț, momentul fiecărui vehicul prins acolo, ca în `rezumat_jurnal`: {braț: {vehicul: moment}}."""
    from romana.vision.calibrare_camera import Proiectie

    pr = Proiectie(MODEL_CAMERA)
    px = float(pr.m["loo_median_px"])
    params = Params()
    intrari, iesiri = zone_pe_brate(zone)
    toate = [z for lista in iesiri.values() for z in lista]
    miscari = {(o, d) for o, d, _, _ in MISCARI}
    u = urme[np.lexsort((urme[:, 0], urme[:, 1]))]
    k = np.r_[0, np.nonzero(np.diff(u[:, 1]))[0] + 1, len(u)]
    out: dict = {"complete": [], "intrare": {}, "ieșire": {}}
    for i0, i1 in zip(k[:-1], k[1:]):
        vehicul = int(u[i0, 1])
        tip = tipuri[vehicul]
        if tip not in VEHICULE or i1 - i0 < 2:
            continue
        t, x, y = u[i0:i1, 0].astype(float), u[i0:i1, 2].astype(float), u[i0:i1, 3].astype(float)
        pts = urma_in_imagine(t, x, y, pr, roi_y)
        if len(pts) < params.min_track_frames:
            continue
        o, d, t_o, t_d = momente_traiectorie(tip, taie_dupa_iesire(pts, toate), zone, intrari, iesiri, params)
        if t_o is not None:
            out["intrare"].setdefault(o, {})[vehicul] = t_o
        if t_d is not None:
            out["ieșire"].setdefault(d, {})[vehicul] = t_d
        if t_o is not None and t_d is not None and t_d > t_o:
            err = float(np.hypot(eroare_proiectie_s(pr, t_o, t, x, y, px), eroare_proiectie_s(pr, t_d, t, x, y, px))) if (o, d) in miscari else _GOL
            out["complete"].append((o, d, t_o, t_d, err))
    return out


def citiri_din_virtuala(virtuala: dict, pe_muchie: dict) -> tuple[dict, dict]:
    """Din camera virtuală: momentele pe fiecare capăt, {rol: {braț: momente}}, și diferența pe același vehicul, moment pe muchie − moment în zonă, {„rol braț”: diferențe}."""
    zone = {rol: {b: np.array(sorted(d.values()), float) for b, d in virtuala[rol].items()} for rol in CHEI_CAPAT}
    dif = {}
    for rol, brate in pe_muchie.items():
        for b, muchie in brate.items():
            zona = virtuala[rol].get(b, {})
            dif[f"{rol} {b}"] = np.array([muchie[v] - zona[v] for v in muchie.keys() & zona.keys()], float)
    return zone, dif


def acoperire_virtuala(r: dict, rol: str, b: str) -> float:
    """Câte vehicule prinde camera virtuală pe un capăt, în fereastră, față de câte trec pe muchie."""
    in_fereastra = lambda x: int(((x >= INCALZIRE_S) & (x < SFARSIT_S)).sum())       # noqa: E731
    muchie = in_fereastra(np.asarray(r[CHEI_CAPAT[rol]][b], float))
    return in_fereastra(np.asarray(r.get("zone", {}).get(rol, {}).get(b, ()), float)) / muchie if muchie else 0.0


def ns_din_stari(r: dict) -> np.ndarray:
    """Etapele N–S întregi dintr-o rulare, pe ceasul scenariului."""
    info = info_v2()
    return ferestre_in(intervale_etape([(s, u - t) for (t, s), (u, _) in zip(r["stari"], r["stari"][1:] + [(SFARSIT_S + 900, "")])], info["green_states"], min(info["pietoni"]["treceri"]), r["stari"][0][0])[0],
                       INCALZIRE_S, SFARSIT_S, intregi=True)


def acoperire_ns(r: dict) -> float:
    """În etapele N–S, pe ieșirea Dacia est vin aproape numai vehicule de pe Magheru, pe care camera virtuală le prinde, chiar dacă pe toată ora pierde vehiculele venite de pe Dacia vest."""
    ns = ns_din_stari(r)
    in_ns = lambda m: sum(int(((np.asarray(m, float) >= a) & (np.asarray(m, float) < b)).sum()) for a, b in ns)       # noqa: E731
    muchie = in_ns(r["iesiri"]["dacia_est"])
    return in_ns(r.get("zone", {}).get("ieșire", {}).get("dacia_est", ())) / muchie if muchie else 0.0


def alege_citiri(rez: list[dict]) -> dict[tuple[str, str], str]:
    """De unde se citesc momentele geamănului pe fiecare capăt: din camera virtuală („zonă”), cu același cod ca la cameră, doar unde ea prinde aproape toate vehiculele pe toate seed-urile; altfel, de pe muchie. La o probă, citirea e cea a bazei."""
    out = {}
    for rol, brate in (("intrare", BRATE), ("ieșire", IESIRI)):
        for b in brate:
            out[(rol, b)] = "zonă" if rez and min(acoperire_virtuala(r, rol, b) for r in rez) >= ACOPERIRE_VIRTUALA else "muchie"
    out[CITIRE_NS] = "zonă" if rez and min(acoperire_ns(r) for r in rez) >= ACOPERIRE_VIRTUALA else "muchie"
    return out


def diferenta_muchie_zona(rez: list[dict], rol: str, b: str) -> np.ndarray:
    """Pe toate seed-urile, momentul pe muchie − momentul în zonă, pe același vehicul."""
    return np.concatenate([np.asarray(r.get("muchie_zona", {}).get(f"{rol} {b}", ()), float) for r in rez]) if rez else np.empty(0)


def rezumat_citiri(rez: list[dict], citiri: dict) -> str:
    """Pe fiecare capăt: de unde se citește, cât prinde camera virtuală și cât diferă momentele pe același vehicul."""
    parti = []
    for (rol, b), c in citiri.items():
        if rol not in CHEI_CAPAT:
            parti.append(f"{rol} {b}: {c}, {np.mean([acoperire_ns(r) for r in rez]):.0%}")
            continue
        d = diferenta_muchie_zona(rez, rol, b)
        parti.append(f"{rol} {b}: {c}, {np.mean([acoperire_virtuala(r, rol, b) for r in rez]):.0%}" + (f", muchie − zonă p50 {np.median(d):+.1f} s" if len(d) else ""))
    return "; ".join(parti)


# --------------------------------------------------------------------- simularea

class Contoare:
    """În geamăn, la fiecare pas, o singură dată, aici și nu în `evaluate`: când pleacă vehiculele de la liniile de oprire, când ajung pe ieșiri, cum intră pietonii pe zebre, ciocnirile văzute de SUMO, urmele
    vehiculelor din cutia pieței și atingerile geometrice. Zonele de mers nu se numără: pietonii care așteaptă stau uneori în dreptunghiul vehiculelor late, fără efect pe dinamică. `cost`: secundele petrecute aici.

    Ceasul: `t` e indicele buclei din `evaluate.run_one`, iar ceasul SUMO după pas e t + 1. Vehiculele și pietonii trec în (t, t + 1], deci au momentul t + 0,5; pozițiile sunt ale sfârșitului pasului, t + 1;
    starea semaforului se schimbă la începutul pasului, la partea întreagă a momentului din program, deci rămâne la t."""

    def __init__(self, masurati: set | None = None, ramuri: dict | None = None, geometrie: bool = True):
        self.brate = {b: [] for b in BRATE}
        self.iesiri = {b: [] for b in IESIRI}
        self.pe_muchie = {"intrare": {b: {} for b in BRATE}, "ieșire": {b: {} for b in IESIRI}}      # vehiculul → momentul pe muchie, ca să se poată compara cu momentul lui din zonă
        self.prec = {m: {} for m in BRATE.values()}
        self.vazute = {b: set() for b in IESIRI}
        self.ramase: dict[str, dict[str, float]] = {b: {} for b in PUNCTE_INTRARE}    # au trecut de linia de oprire, încă n-au ajuns în dreptul zonei
        self.pietoni: list[float] = []              # intrările pe zebra Dacia est
        self.masurati = masurati or set()           # pietonii de pe rutele de pe Dacia est; ceilalți sunt extrapolați
        self.geometrie = geometrie
        self.zebre = None
        self.pe_zebra: dict[int, set] = {}
        self.intrari_zebre: list[tuple[float, int, str]] = []     # (moment, legătura, litera semaforului la intrare); nu ține minte persoana
        self.stari: list[tuple[int, str]] = []
        self._stare = None
        self._activ: set = set()
        self.ciocniri = {"vehicule": 0, "mers_masurati": 0, "mers_extrapolati": 0, "oprit_masurati": 0, "oprit_extrapolati": 0}
        self.vidx: dict[str, int] = {}
        self.vtip: list[str] = []
        self.vlung: list[float] = []
        self.vlat: list[float] = []
        self.urme = array("f")                      # moment, vehicul, x, y, în cutia pieței
        self.pp: dict[tuple[int, int], dict] = {}   # perechi vehicul–vehicul care se suprapun
        self.pv: dict[tuple[int, str], list] = {}   # perechi vehicul–pieton pe zebre: [pași, viteza maximă, pași cu vehiculul oprit]
        self.neintrate = {"total": 0, "dacia_vest": 0}
        self.ramuri = ramuri or {}
        self.cost = {"contoare_s": 0.0, "pozitii_s": 0.0, "geometrie_s": 0.0}

    def __call__(self, tr, t: int) -> None:
        c0 = time.perf_counter()
        if self.zebre is None:
            legaturi = tr.trafficlight.getControlledLinks("romana")
            self.zebre = {i: legaturi[i][0][1].rsplit("_", 1)[0] for i in info_v2()["pietoni"]["treceri"]}
            self.pe_zebra = {i: set() for i in self.zebre}
        moment = t + 0.5
        for b, m in BRATE.items():
            acum = {v: self.prec[m].get(v) or tr.vehicle.getTypeID(v) for v in tr.edge.getLastStepVehicleIDs(m)}
            for v, tip in self.prec[m].items():
                if v not in acum and tip in VEHICULE:
                    if b in PUNCTE_INTRARE:
                        self.ramase[b][v] = moment
                    else:
                        self._intrare(b, v, moment)
            self.prec[m] = acum
        for b, muchii in PUNCTE_INTRARE.items():
            for m in muchii:
                for v in tr.edge.getLastStepVehicleIDs(m):
                    if self.ramase[b].pop(v, None) is not None:
                        self._intrare(b, v, moment)
            for v, t0 in list(self.ramase[b].items()):
                if moment - t0 > 40:                 # n-a trecut prin dreptul zonei în timp util: se numără la linia de oprire, cu întârzierea obișnuită
                    self._intrare(b, v, t0 + 8)
                    del self.ramase[b][v]
        for b, muchii in IESIRI.items():
            for m in muchii:
                for v in tr.edge.getLastStepVehicleIDs(m):
                    if v not in self.vazute[b] and tr.vehicle.getTypeID(v) in VEHICULE:
                        self.vazute[b].add(v)
                        self.iesiri[b].append(moment)
                        self.pe_muchie["ieșire"][b][v] = moment
        stare = tr.trafficlight.getRedYellowGreenState("romana")
        if stare != self._stare:
            self.stari.append((t, stare))
            self._stare = stare
        for i, muchie in self.zebre.items():
            pe = set(tr.edge.getLastStepPersonIDs(muchie))
            noi = pe - self.pe_zebra[i]
            if noi:
                self.intrari_zebre += [(moment, i, stare[i])] * len(noi)
                if i == TRECERE_DACIA_EST:
                    self.pietoni += [moment] * len(noi)
            self.pe_zebra[i] = pe
        self._ciocniri(tr)
        if t == SFARSIT_S:
            neintrate = tr.simulation.getPendingVehicles()
            self.neintrate = {"total": len(neintrate), "dacia_vest": sum(self.ramuri.get(v) == "dacia_vest" for v in neintrate)}
        c1 = time.perf_counter()
        self.cost["contoare_s"] += c1 - c0
        self._cutie(tr, t, c1)

    def _intrare(self, b: str, v: str, moment: float) -> None:
        self.brate[b].append(moment)
        self.pe_muchie["intrare"][b][v] = moment

    def _ciocniri(self, tr) -> None:
        """Ciocnirile văzute de SUMO, cu aceeași regulă ca `evaluate.stare_ciocniri`, dar pe pietoni măsurați și extrapolați. O ciocnire care continuă se numără o dată."""
        acum = set()
        for c in tr.simulation.getCollisions():
            k = tuple(sorted((c.collider, c.victim)))
            acum.add(k)
            if k in self._activ:
                continue
            if "pieton" in (c.victimType, c.colliderType):
                p = c.victim if c.victimType == "pieton" else c.collider
                self.ciocniri[("mers_" if c.colliderSpeed > 1 else "oprit_") + ("masurati" if p in self.masurati else "extrapolati")] += 1
            else:
                self.ciocniri["vehicule"] += 1
        self._activ = acum

    def _cutie(self, tr, t: int, c1: float) -> None:
        x0, x1, y0, y1 = CUTIE_PIATA
        nume, idx, xs, ys = [], [], [], []
        for v in tr.vehicle.getIDList():
            x, y = tr.vehicle.getPosition(v)
            if x0 < x < x1 and y0 < y < y1:
                i = self.vidx.get(v)
                if i is None:
                    i = self.vidx[v] = len(self.vtip)
                    self.vtip.append(tr.vehicle.getTypeID(v))
                    self.vlung.append(tr.vehicle.getLength(v))
                    self.vlat.append(tr.vehicle.getWidth(v))
                self.urme.extend((t + 1, i, x, y))
                nume.append(v)
                idx.append(i)
                xs.append(x)
                ys.append(y)
        c2 = time.perf_counter()
        self.cost["pozitii_s"] += c2 - c1
        if self.geometrie and nume:
            self._atingeri(tr, nume, idx, xs, ys)
            self.cost["geometrie_s"] += time.perf_counter() - c2

    def _atingeri(self, tr, nume: list, idx: list, xs: list, ys: list) -> None:
        unghi = np.array([tr.vehicle.getAngle(v) for v in nume])
        I = np.array(idx)
        X, Y = np.array(xs), np.array(ys)
        L, W = np.array([self.vlung[i] for i in idx]), np.array([self.vlat[i] for i in idx])
        for a, b, adanc in perechi_suprapuse(X, Y, unghi, L, W):
            i, j = (a, b) if I[a] < I[b] else (b, a)
            k = (int(I[i]), int(I[j]))
            d = self.pp.get(k)
            if d is None:
                d = self.pp[k] = {"adanc": 0.0, "bi": set(), "bj": set()}
            d["adanc"] = max(d["adanc"], adanc)
            d["bi"].add(tr.vehicle.getLaneID(nume[i]))
            d["bj"].add(tr.vehicle.getLaneID(nume[j]))
        pers = [p for s in self.pe_zebra.values() for p in s]      # doar zebrele pieței, deci zonele de mers rămân afară
        if not pers:
            return
        P = np.array([tr.person.getPosition(p) for p in pers])
        for a, b in zip(*np.nonzero(atinge_pieton(P[:, 0], P[:, 1], X, Y, unghi, L, W))):
            if self.vtip[idx[b]] == "bicycle":
                continue
            v = tr.vehicle.getSpeed(nume[b])
            q = self.pv.setdefault((idx[b], pers[a]), [0, 0.0, 0])
            q[0] += 1
            q[1] = max(q[1], v)
            q[2] += v < 0.1

    def rezultat(self) -> dict:
        """Doar momente și contoare; nicio urmă de pieton."""
        vv = list(self.pp.values())
        vp = [(p in self.masurati, q) for (_, p), q in self.pv.items()]
        return {"brate": {b: np.array(v, float) for b, v in self.brate.items()}, "iesiri": {b: np.array(v, float) for b, v in self.iesiri.items()}, "pietoni": np.array(self.pietoni, float),
                "pe_muchie": {rol: {b: {self.vidx[v]: t for v, t in d.items() if v in self.vidx} for b, d in brate.items()} for rol, brate in self.pe_muchie.items()},
                "intrari_zebre": self.intrari_zebre, "stari": self.stari, "ciocniri": self.ciocniri, "neintrate": self.neintrate, "cost": dict(self.cost),
                "vv": {"axa_inel": sum(pe_axa_si_inel(d["bi"], d["bj"]) for d in vv), "alte": sum(not pe_axa_si_inel(d["bi"], d["bj"]) for d in vv), "adanc_1m": sum(d["adanc"] >= 1 for d in vv)},
                "vp": {"mers_masurati": sum(m and q[1] > 1 for m, q in vp), "mers_extrapolati": sum(not m and q[1] > 1 for m, q in vp),
                       "oprit_masurati": sum(m and q[2] >= q[0] for m, q in vp), "oprit_extrapolati": sum(not m and q[2] >= q[0] for m, q in vp)}}


def fisiere_rute(cfg: Path) -> list[Path]:
    return [(cfg.parent / p).resolve() for p in ET.parse(cfg).getroot().find("input/route-files").get("value").split(",")]


def pietoni_masurati(cfg: Path) -> set:
    """Pietonii de pe rutele de pe Dacia est, singurii măsurați; pe celelalte brațe, numărul e extrapolat (§ 9.11)."""
    capete = set(json.loads((CONFIG_DIR / "demand_v2.json").read_text(encoding="utf-8"))["pietoni_pe_treceri"]["dacia_est"])
    out = set()
    for p in fisiere_rute(cfg):
        if p.name == "pietoni.rou.xml":
            for _, el in ET.iterparse(p):
                if el.tag == "person":
                    w = el.find("walk")
                    if w is not None and {w.get("from"), w.get("to")} & capete:
                        out.add(el.get("id"))
                    el.clear()
    return out


def ramuri_din_rute(cfg: Path) -> dict[str, str]:
    """Pe ce ramură intră fiecare vehicul: brațul a cărui muchie o are în rută; traficul de fond are ramura lui."""
    out = {}
    for p in fisiere_rute(cfg):
        if p.name == "pietoni.rou.xml":
            continue
        for _, el in ET.iterparse(p):
            if el.tag == "vehicle":
                r = el.find("route")
                muchii = set(r.get("edges").split()) if r is not None else set()
                out[el.get("id")] = "fond" if p.name == "fond.rou.xml" else next((b for b, m in BRATE.items() if m in muchii), "alta")
                el.clear()
    return out


def pierdere_pe_ramuri(cale: Path, ramuri: dict[str, str], masurati: set) -> dict[str, float]:
    """Pierderea pe ramuri, în ore, cu aceeași regulă ca `evaluate.parse_tripinfo` (vehiculele, cu întârzierea la intrare), deci suma lor e pierderea totală."""
    tot: dict[str, float] = {}
    for _, el in ET.iterparse(cale):
        if el.tag == "tripinfo":
            k = ramuri.get(el.get("id"), "alta")
            tot[k] = tot.get(k, 0.0) + float(el.get("timeLoss")) + (0.0 if el.get("vType") == "bicycle" else float(el.get("departDelay", 0)))
            el.clear()
        elif el.tag == "personinfo":
            k = "pietoni_masurati" if el.get("id") in masurati else "pietoni_extrapolati"
            for w in el.findall("walk"):
                tot[k] = tot.get(k, 0.0) + float(w.get("timeLoss", 0))
            el.clear()
    return {k: v / 3600 for k, v in tot.items()}


def ruleaza(stem: str, strategie: str, seed: int, cfg: Path | None = None, orizont: int | None = None, geometrie: bool = True) -> dict:
    """O simulare, cu tot ce trebuie rândurilor. Fișierele intermediare stau într-un dosar propriu, ca să nu se calce cu o evaluare care rulează în același timp."""
    from romana.control import evaluate as E
    from romana.control.validare import make_controller

    E.EVAL_DIR = RULARI_DIR
    cale = cfg or ROOT / "sumo" / "scenarios" / f"{stem}.sumocfg"
    config = json.loads((CONFIG_DIR / "camera_v2.json").read_text(encoding="utf-8"))
    zone = load_zones(config)
    masurati = pietoni_masurati(cale)
    cont = Contoare(masurati, ramuri_din_rute(cale), geometrie)
    pierderi: dict[str, float] = {}
    original = E.parse_tripinfo

    def cu_ramuri(c):
        pierderi.update(pierdere_pe_ramuri(c, cont.ramuri, masurati))
        return original(c)

    E.parse_tripinfo = cu_ramuri
    t0 = time.perf_counter()
    try:
        r = E.run_one(cale, make_controller(strategie), seed, horizon=orizont, observator=cont)
    finally:
        E.parse_tripinfo = original
    t1 = time.perf_counter()
    urme = np.frombuffer(cont.urme, dtype=np.float32).reshape(-1, 4)
    virtuala = camera_virtuala(urme, cont.vtip, zone, tuple(config["roi_y"]))
    rez = cont.rezultat()
    rez["cost"].update(simulare_s=t1 - t0, camera_virtuala_s=time.perf_counter() - t1)
    citite, dif = citiri_din_virtuala(virtuala, rez.pop("pe_muchie"))
    rez.update(seed=seed, virtuala=virtuala["complete"], zone=citite, muchie_zona=dif, pierderi=pierderi, r={k: r.get(k) for k in ("teleportari", "ciocniri_vehicule", "ciocniri_pieton_in_miscare", "vehicule_sosite", "nefinalizate", "pierdere_totala_h")})
    return rez


def proba_cfg(stem: str, tip: str) -> Path:
    """Scrie, în outputs/validare/probe, configurația unui geamăn greșit dinadins; sumo/ nu se atinge. Numele păstrează zi_AAAA-LL-ZZ_tip, ca semaforul rejucat să ia aceeași oră."""
    baza = ROOT / "sumo" / "scenarios" / f"{stem}.sumocfg"
    arbore = ET.parse(baza)
    rad, dosar = arbore.getroot(), baza.parent
    inp = rad.find("input")
    rute = [(dosar / p).resolve() for p in inp.find("route-files").get("value").split(",")]
    tipuri = (dosar / inp.find("additional-files").get("value")).resolve()
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    if tip == "fara_pietoni":
        rute = [p for p in rute if p.name != "pietoni.rou.xml"]
    elif tip == "rapid":
        nou = PROBE_DIR / f"{stem}_rapid_vtypes.add.xml"
        nou.write_text(tipuri_rapide(tipuri.read_text(encoding="utf-8")), encoding="utf-8")
        tipuri = nou
    else:
        raise ValueError(f"probă necunoscută: {tip}")
    inp.find("net-file").set("value", str((dosar / inp.find("net-file").get("value")).resolve()))
    inp.find("route-files").set("value", ",".join(str(p) for p in rute))
    inp.find("additional-files").set("value", str(tipuri))
    if rad.find("gui_only") is not None:
        rad.remove(rad.find("gui_only"))
    cale = PROBE_DIR / f"{stem}_{tip}.sumocfg"
    arbore.write(cale, encoding="UTF-8", xml_declaration=True)
    return cale


# --------------------------------------------------------------------- camera

def rezumat_jurnal(sursa, zone: list) -> dict:
    """Din traiectoriile camerei: momentele pe intrări și pe ieșiri și traiectoriile complete (origine, destinație, t_o, t_d)."""
    params = Params()
    intrari, iesiri = zone_pe_brate(zone)
    ev = {b: [] for b in intrari}
    ies = {b: [] for b in iesiri}
    miscari = []
    for tip, pts in sursa:
        if tip not in VEHICULE or len(pts) < params.min_track_frames:
            continue
        o, d, t_o, t_d = momente_traiectorie(tip, pts, zone, intrari, iesiri, params)
        if t_o is not None:
            ev[o].append(t_o)
        if t_d is not None:
            ies[d].append(t_d)
        if t_o is not None and t_d is not None:
            miscari.append((o, d, t_o, t_d))
    return {"intrari": {b: sorted(v) for b, v in ev.items()}, "iesiri": {b: sorted(v) for b, v in ies.items()}, "miscari": miscari}


def amprenta_zone(zone: list) -> str:
    """Rezumatul depinde de zone: dacă ele se schimbă, se refac momentele."""
    return hashlib.sha256(json.dumps([[z.id, z.role, z.capat, z.sens, z.poly_norm.tolist()] for z in zone]).encode()).hexdigest()[:16]


def camera_zi(zi: str, zone: list) -> dict:
    """Jurnalul public al zilei, rezumat; se calculează o dată. Doar vehicule."""
    cale = OUTPUT_DIR / "validare" / f"camera_v2_{zi}.json"
    amprenta = amprenta_zone(zone)
    d = json.loads(cale.read_text(encoding="utf-8")) if cale.exists() else {}
    if d.get("amprenta") != amprenta:
        d = rezumat_jurnal(((tip, pts) for _, tip, pts in read_trajectories([TRAJ_DIR / f"traiectorii_{zi}.jsonl.gz"])), zone)
        d["amprenta"] = amprenta
        cale.parent.mkdir(parents=True, exist_ok=True)
        cale.write_text(json.dumps(d), encoding="utf-8")
    return {"intrari": {b: np.array(v) for b, v in d["intrari"].items()}, "iesiri": {b: np.array(v) for b, v in d["iesiri"].items()}, "miscari": d["miscari"]}


def pietoni_camera(zi: str, a: float, b: float, zone: list) -> np.ndarray | None:
    """Momentele de intrare pe zebra de ieșire de pe Dacia est, din jurnalul local. Doar pentru numere agregate; lipsește de pe alte calculatoare. Rezumatul ține de zone: dacă ele se schimbă, se reface."""
    cale = OUTPUT_DIR / "validare" / f"pietoni_{zi}_{int(a)}_{amprenta_zone(zone)}.npy"
    if cale.exists():
        return np.load(cale)
    brut = TRAJ_RAW_DIR / f"traiectorii_{zi}.jsonl.gz"
    z = next((x for x in zone if x.id == "trecere_dacia_est_iesire"), None)
    if not brut.exists() or z is None:
        return None
    params = Params()
    out = []
    for t0, tip, pts in read_trajectories([brut]):
        if t0 > b + 60:
            break
        if tip != PEDESTRIAN or t0 < a - 60:
            continue
        if any(i == z.id for _, i in classify(tip, pts, zone, params)["treceri"]):
            t = next((t for t, x, y in pts if z.contains_norm(x, y)), None)
            if t is not None and a <= t < b:
                out.append(t)
    r = np.array(out)
    cale.parent.mkdir(parents=True, exist_ok=True)
    np.save(cale, r)
    return r


def pietoni_numarati(zi: str, de_la: pd.Timestamp, pana_la: pd.Timestamp, treceri: tuple = ("trecere_dacia_est_iesire",)) -> float | None:
    """Pietonii de pe trecerile date, pe oră, din numărătorile măsurii noi, pe persoane: și cei care așteaptă la bordură, pe care detectorul îi pierde pe zebră. Doar numere agregate."""
    cale = COUNTS_COR_DIR / f"numaratori_{zi}.csv"
    if not cale.exists():
        return None
    d = pd.read_csv(cale)
    t = pd.to_datetime(d["inceput"])
    return float(d[(d["tip"] == "pietoni") & d["destinatie"].isin(treceri) & (t >= de_la) & (t < pana_la)]["numar"].sum()) * 3600 / (pana_la - de_la).total_seconds()


def factori_folositi() -> dict:
    """Factorii din demand_v2.json, ca în tabel să se vadă cu ce s-a calculat; se schimbă, deci nicio cifră de aici nu stă în cod."""
    text = (CONFIG_DIR / "demand_v2.json").read_text(encoding="utf-8")
    c = json.loads(text)
    return {"sha256": hashlib.sha256(text.encode()).hexdigest()[:16], **{k: c.get(k) for k in ("factor_corectie_detectie", "factor_pietoni_masurati", "factor_extrapolare_pietoni", "viraje_numarate", "cote_fixe")}}


def factor_pe_sferturi(valoare, a: float, a_ts, momente: np.ndarray) -> float:
    """Factorul mediu al brațului pe vehiculele numărate: cererea pune eticheta de zi sau de întuneric pe începutul fiecărui sfert, deci o oră care trece peste prag are factori amestecați."""
    if not isinstance(valoare, dict) or not len(momente):
        return factor_brat(valoare, a_ts)
    k, n = np.unique(((momente - a) // 900).astype(int), return_counts=True)
    return float(sum(c * factor_brat(valoare, pd.Timestamp(a_ts) + pd.Timedelta(seconds=900 * int(i))) for i, c in zip(k, n)) / n.sum())


def pierdere_detectie(intrari: dict, iesiri: dict, miscari: list, a: float, mijloc) -> dict:
    """Doar din cameră, pe toată ora: vezi `PIERDERE_DETECTIE`. Pe trafic mic, raportul nu spune nimic, de aceea cere un minim pe Magheru și pe X."""
    in_ora = lambda v: int(((v >= a) & (v < a + SFARSIT_S)).sum())     # noqa: E731
    viraj = sum(1 for o, d, _, td in miscari if o == "magheru" and d == "dacia_est" and a <= td < a + SFARSIT_S)
    x, v, m = in_ora(iesiri["dacia_est"]) - viraj, in_ora(intrari["dacia_vest"]), in_ora(intrari["magheru"])
    raport = x / max(v, 1)
    intuneric = inaltime_soare(pd.Timestamp(mijloc).to_pydatetime()) <= PRAG_INTUNERIC_GRADE
    return {"x": x, "v": v, "m": m, "raport": raport, "intuneric": bool(intuneric),
            "marcata": bool(intuneric and m >= PIERDERE_DETECTIE["magheru"] and x >= PIERDERE_DETECTIE["x"] and raport >= PIERDERE_DETECTIE["raport"])}


def date_camera(stem: str, zone: list) -> dict:
    """Tot ce trebuie din cameră pe un scenariu, pe ceasul scenariului: fără simulare."""
    zi, a_ts, b_ts = fereastra_scenariu(stem)
    a = pd.Timestamp(a_ts, tz="Europe/Bucharest").timestamp()
    real = camera_zi(zi, zone)
    cerere = json.loads((CONFIG_DIR / "demand_v2.json").read_text(encoding="utf-8"))
    fact = cerere["factor_corectie_detectie"]
    fereastra = lambda m: m[(m >= a + INCALZIRE_S) & (m < a + SFARSIT_S)] - a     # noqa: E731
    m = real["intrari"]["magheru"]
    val = valuri_in_fereastra(m[(m >= a - 200) & (m < a + ORIZONT_S)] - a)
    faze, detalii = program_rejucat(stem)
    info = info_v2()
    ns, ev = intervale_etape(faze, info["green_states"], min(info["pietoni"]["treceri"]))
    pc = pietoni_camera(zi, a + INCALZIRE_S, a + SFARSIT_S, zone)
    od = json.loads((DEMAND_DIR / stem / "od_estimat.json").read_text(encoding="utf-8"))["rezumat"]
    return {"stem": stem, "zi": zi, "a": a, "f": {b: factor_pe_sferturi(fact[b], a, a_ts, real["intrari"][b][(real["intrari"][b] >= a + INCALZIRE_S) & (real["intrari"][b] < a + SFARSIT_S)]) for b in BRATE},
            "f_ora": {b: factor_pe_sferturi(fact[b], a, a_ts, real["intrari"][b][(real["intrari"][b] >= a) & (real["intrari"][b] < a + SFARSIT_S)]) for b in BRATE},
            "pierdere_detectie": pierdere_detectie(real["intrari"], real["iesiri"], real["miscari"], a, pd.Timestamp(a_ts) + pd.Timedelta(seconds=SFARSIT_S / 2)),
            "intrari": {b: fereastra(v) for b, v in real["intrari"].items()}, "iesiri": {b: fereastra(v) for b, v in real["iesiri"].items()},
            "intrari_ora": {b: int(((real["intrari"][b] >= a) & (real["intrari"][b] < a + SFARSIT_S)).sum()) for b in BRATE},
            "val": val, "sc": np.array([v[0] for v in val]), "ns": ns, "ev": ev, "detalii": detalii, "pietoni": None if pc is None else pc - a, "pietoni_pe_ora": pietoni_numarati(zi, a_ts, b_ts), "persoane_pe_ora": pietoni_numarati(zi, a_ts, b_ts, ("trecere_dacia_est_iesire", "trecere_dacia_est_intrare")), "f_pietoni": float(cerere.get("factor_pietoni_masurati", 1.0)),
            "miscari": [(o, d, to - a, td - a) for o, d, to, td in real["miscari"]], "od": od}


def avertisment_factori(demand: Path, rute: list[Path], amprenta: str | None = None) -> str | None:
    """Rutele se fac din factori. Generatorul scrie în rezumatul zilei amprenta cererii folosite; pe scenariile mai vechi decât această regulă se compară doar momentele fișierelor."""
    if not rute or not demand.exists():
        return None
    if amprenta is not None:
        if amprenta != hashlib.sha256(demand.read_text(encoding="utf-8").encode()).hexdigest()[:16]:
            return f"ATENȚIE: rutele scenariului s-au făcut cu altă cerere decât {demand.name} de acum ({amprenta}): tabelul înmulțește camera cu alți factori decât cei din rute; regenerați scenariul."
        return None
    if demand.stat().st_mtime > min(p.stat().st_mtime for p in rute):
        return f"ATENȚIE: {demand.name} e mai nou decât rutele scenariului: dacă factorii s-au schimbat, tabelul înmulțește camera cu alți factori decât cei din rute; regenerați scenariul."
    return None


def verifica_cererea(od: dict, intrari_ora: dict, f: dict, toleranta: float = TOLERANTA_CERERE) -> list[str]:
    """Cererea din rute, pe fiecare braț, față de cât a numărat camera în toată ora, cu factorii de acum: dacă se abate, rutele s-au făcut cu alți factori. Cel puțin 3 vehicule, ca rotunjirile de la trafic slab să nu conteze."""
    out = []
    for b, n in intrari_ora.items():
        asteptat = n * f[b]
        cerere = sum(v for k, v in od.get("od_vehicule", {}).items() if k.split(">")[0] == b)
        if abs(cerere - asteptat) > max(toleranta * asteptat, 3):
            out.append(f"ATENȚIE: pe {b}, cererea are {cerere:.0f} vehicule, iar camera × factorul de acum, {f[b]:g}, dă {asteptat:.0f}: scenariul pare făcut cu alți factori.")
    return out


def verifica_valuri(sc: np.ndarray, ns: np.ndarray, m_rezumat: np.ndarray | None = None, m_program: np.ndarray | None = None, toleranta: float = 1.0) -> list[str]:
    """Fără simulare: `sc` vine din rezumatul camerei, iar programul din `ev_<zi>.npz`, care nu știe de zone. Începuturile valurilor trebuie să cadă pe începuturile etapelor N–S, iar momentele pe Magheru să fie aceleași."""
    out = []
    if len(sc) and len(ns):
        pe_alaturi = int((np.abs(np.asarray(ns, float)[:, 0][:, None] - np.asarray(sc, float)).min(0) > toleranta).sum())
        if pe_alaturi:
            out.append(f"ATENȚIE: {pe_alaturi} din {len(sc)} valuri nu încep la o etapă N–S din program: programul le-a lipit de valul dinainte sau `ev_<zi>.npz` e din alte zone.")
    if m_rezumat is not None and m_program is not None:
        a, b = np.sort(m_rezumat), np.sort(m_program)
        if len(a) != len(b) or not np.allclose(a, b):
            out.append(f"ATENȚIE: pe Magheru, programul stă pe {len(b)} momente, iar rezumatul camerei pe {len(a)}, ori nu sunt aceleași: `ev_<zi>.npz` e din alte zone; ștergeți-l și refaceți.")
    return out


def avertismente_scenariu(stem: str, cam: dict) -> list[str]:
    """Tot ce se poate verifica fără simulare despre un scenariu: rutele față de factori și programul față de cameră."""
    a = cam["a"]
    m = evenimente_zi(cam["zi"])["magheru"]
    m = m[(m >= a + INCALZIRE_S) & (m < a + SFARSIT_S)] - a
    cfg = ROOT / "sumo" / "scenarios" / f"{stem}.sumocfg"
    rez = DEMAND_DIR / f"cor_zi_{cam['zi']}_rezumat.json"
    amprenta = json.loads(rez.read_text(encoding="utf-8")).get("cerere_sha256") if rez.exists() else None
    out = [avertisment_factori(CONFIG_DIR / "demand_v2.json", fisiere_rute(cfg), amprenta)] if cfg.exists() else []
    return [x for x in out if x] + verifica_cererea(cam["od"], cam["intrari_ora"], cam.get("f_ora", cam["f"])) + verifica_valuri(cam["sc"], cam["ns"], cam["intrari"]["magheru"], m)


# --------------------------------------------------------------------- rândurile

def _alatura(*parti) -> str:
    return "; ".join(p for p in parti if p)


def fara_etapa(momente: np.ndarray, etape: np.ndarray, marja: float = 5.0) -> np.ndarray:
    """Momentele din afara etapelor date, cu marja de degajare de la sfârșitul lor."""
    m = np.asarray(momente, float)
    afara = np.ones(len(m), bool)
    for a, b in etape:
        afara &= ~((m >= a) & (m < b + marja))
    return m[afara]


def parte_cu_origine(cam: dict, b: str) -> float:
    """Pe o ieșire, ce parte din momentele camerei sunt vehicule urmărite de la o intrare."""
    n = len(cam["iesiri"].get(b, ()))
    return sum(1 for _, d, _, td in cam["miscari"] if d == b and INCALZIRE_S <= td < SFARSIT_S) / n if n else 0.0


def nota_iesire_camera(cam: dict, b: str) -> str:
    """Pe o ieșire, ce parte din momentele camerei sunt vehicule urmărite de la o intrare; restul sunt traiectorii pierdute sau apărute pe drum, deci un rând de aici măsoară și detectorul."""
    n = len(cam["iesiri"].get(b, ()))
    if not n:
        return "în cameră, nicio trecere pe această ieșire"
    return f"în cameră, {parte_cu_origine(cam, b):.0%} din momentele ieșirii au și origine" + ("; prea puține: rândul ar măsura detectorul" if parte_cu_origine(cam, b) < MIN_PARTE_CU_ORIGINE else "")


def rulari_cu_probleme(rez: list[dict], parte: float = 0.20) -> dict[int, str]:
    """Rulările cu teleportări și cele cu blocaj presupus: pierderea, totală sau pe ramura unui braț, iese vizibil din rândul celorlalte, în sus, cu cel puțin `parte`. Că acolo e un blocaj e o presupunere din cifre; de aceea rândul spune „presupus”."""
    out: dict[int, list[str]] = {}
    for i, r in enumerate(rez):
        n = r["r"]["teleportari"]
        if n:
            out.setdefault(i, []).append("1 teleportare" if n == 1 else f"{n} teleportări")
    serii = [("totală", [r["r"]["pierdere_totala_h"] for r in rez])] + [(f"pe ramura {b}", [r["pierderi"].get(b, 0.0) for r in rez]) for b in BRATE]
    for nume, v in serii:
        i = seed_exceptie(v, parte)
        if i is not None and v[i] > np.median(v):
            out.setdefault(i, []).append(f"pierdere {nume} {v[i]:.0f} h, peste celelalte rulări, {min(np.delete(v, i)):.0f}–{max(np.delete(v, i)):.0f} h")
    return {i: ", ".join(m) for i, m in sorted(out.items())}


class Tabel:
    def __init__(self, fixate: dict | None, din_baza: dict | None, seeds: list | None = None):
        self.fixate = fixate or {}
        self.din_baza = din_baza or {}
        self.seeds = seeds or []
        self.randuri: list[dict] = []

    def prag(self, cheie: str, calculat: float, sursa: str = "calculat") -> tuple[float, str, str]:
        """Pragul fixat în fișier, dacă există; la o probă, cel al bazei; altfel cel calculat acum sau scris în PRAGURI."""
        if cheie in self.fixate:
            return float(self.fixate[cheie]), "fișier", cheie
        if cheie in self.din_baza:
            return self.din_baza[cheie], "din bază", cheie
        return calculat, sursa, cheie

    def rand(self, grup: str, cheie: str, masura: str, pe_seed=(), camera: float = _GOL, geaman: float | None = None, abateri=None, abatere: float | None = None, mod: str = "raport",
             prag: tuple | None = None, nul: float = _GOL, zgomot: float = _GOL, z_seed: float = _GOL, nota: str = "", pieton: bool = False, din_simulare: bool = True, verdict: str | None = None,
             profil_g: np.ndarray | None = None, minmax: bool = False, lipsa: int = 0, citire: str = "") -> None:
        """mod: „relativ” (abatere față de cameră, ca parte), „absolut” (în unitatea rândului), „valoare” (valoarea însăși se judecă), „abatere” (`abateri` vin de-a gata) sau „raport” (fără judecată).
        `pe_seed`: de obicei câte o valoare pe seed. `minmax`: valorile sunt ale mediei fără câte un seed, deci intervalul e chiar min–max al lor, iar un seed nu poate ieși din rând. `lipsa`: câte seed-uri n-au valoare; fără ele, „în prag” devine „nedecis”.
        `profil_g`: profilul mediei, pe rândurile unde o probă se compară direct cu baza."""
        v = np.array(pe_seed, float)
        ok = v[np.isfinite(v)]
        g = geaman if geaman is not None else (float(ok.mean()) if len(ok) else _GOL)
        if mod == "relativ" and camera and np.isfinite(camera):
            abateri, abatere = (v - camera) / camera, (g - camera) / camera
        elif mod == "absolut":
            abateri, abatere = v - camera, g - camera
        elif mod == "valoare":
            abateri, abatere = v, g
        elif mod != "abatere":
            abateri, abatere = np.empty(0), _GOL
        ab = np.array(abateri if abateri is not None else [], float)
        ab = ab[np.isfinite(ab)]
        ab_lo, ab_hi = (float(ab.min()), float(ab.max())) if minmax and len(ab) else interval_seeduri(ab)
        g_lo, g_hi = (float(ok.min()), float(ok.max())) if minmax and len(ok) else interval_seeduri(ok)
        media = _GOL if abatere is None else float(abatere)
        if np.isfinite(media):                       # media face parte din interval, ca verdictul s-o vadă
            ab_lo, ab_hi = media if not np.isfinite(ab_lo) else min(ab_lo, media), media if not np.isfinite(ab_hi) else max(ab_hi, media)
        pr, sursa, cheie_prag = prag if prag is not None else (_GOL, "", "")
        if verdict is None:
            verdict = verdict_interval([ab_lo, ab_hi, media], pr)
            pe_toate = verdict_interval(np.r_[ab, media], pr)
            if pe_toate != verdict:
                nota = _alatura(nota, f"cu toate seed-urile ar fi „{pe_toate}”")
            if lipsa and verdict == "în prag":
                verdict = "nedecis"
        i = None if minmax else seed_exceptie(v)
        if i is not None:
            nota = _alatura(nota, f"seed {self.seeds[i] if i < len(self.seeds) else i + 1} iese din rând: {_n(v[i])}")
        self.randuri.append({"grup": grup, "cheie": cheie, "masura": masura, "camera": camera, "geaman": g, "g_mediana": float(np.median(ok)) if len(ok) else _GOL, "g_min": float(ok.min()) if len(ok) else _GOL, "g_max": float(ok.max()) if len(ok) else _GOL,
                             "g_lo": g_lo, "g_hi": g_hi, "abatere": media, "ab_lo": ab_lo, "ab_hi": ab_hi,
                             "prag": pr, "sursa_prag": sursa, "cheie_prag": cheie_prag, "verdict": verdict, "nul": nul, "zgomot_camera_p95": zgomot, "zgomot_seeduri": z_seed,
                             "reper": "" if not (np.isfinite(nul) and np.isfinite(zgomot)) else ("neinformativ" if nul < zgomot else "informativ"), "nota": nota, "pieton": pieton, "din_simulare": din_simulare, "citire": citire,
                             "profil_g": "" if profil_g is None else json.dumps([round(float(x), 4) for x in profil_g]), "pe_seed": json.dumps([None if not np.isfinite(x) else round(float(x), 4) for x in v])})


def randuri(cam: dict, rez: list[dict], strategie: str = "REAL", fixate: dict | None = None, din_baza: dict | None = None, citiri: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Toate rândurile unui scenariu, pe seed-urile date. Cu `din_baza`, pragurile vin de la geamănul de bază, iar cu `citiri`, punctul de citire: o probă nu-și face pragul ei și nu se citește altundeva."""
    rng = np.random.default_rng(SAMANTA)
    T = Tabel(fixate, din_baza, [r.get("seed", i + 1) for i, r in enumerate(rez)])
    f, sc, n_s = cam["f"], cam["sc"], SFARSIT_S - INCALZIRE_S
    K = len(rez)
    citiri = citiri if citiri is not None else alege_citiri(rez)
    fereastra = lambda m: np.asarray(m, float)[(np.asarray(m, float) >= INCALZIRE_S) & (np.asarray(m, float) < SFARSIT_S)]     # noqa: E731

    def citite(rol: str, b: str) -> list[np.ndarray]:
        """Momentele geamănului pe un capăt, netăiate, de unde spune `citiri`; dacă o probă n-are camera virtuală aici, un rând pe zone nu are de unde citi."""
        return [np.sort(np.asarray(r.get("zone", {}).get(rol, {}).get(b, ()) if citiri[(rol, b)] == "zonă" else r[CHEI_CAPAT[rol]][b], float)) for r in rez]

    def nota_citire(rol: str, b: str) -> str:
        """Pe un capăt citit pe muchie: diferența față de zonă, pe același vehicul, ca să nu fie luată drept decalaj de semafor."""
        if citiri[(rol, b)] == "zonă":
            return ""
        ac = float(np.mean([acoperire_virtuala(r, rol, b) for r in rez])) if rez else 0.0
        d = diferenta_muchie_zona(rez, rol, b)
        if len(d) == 0:
            return f"citit pe muchie, camera virtuală prinde {ac:.0%}: nicio comparație pe același vehicul"
        p10, p50, p90 = np.percentile(d, [10, 50, 90])
        return f"citit pe muchie, camera virtuală prinde {ac:.0%}; muchie − zonă pe același vehicul: p50 {p50:+.1f} s, p10…p90 {p10:+.1f}…{p90:+.1f} s, n {len(d)}"

    MI, ME = {b: citite("intrare", b) for b in BRATE}, {b: citite("ieșire", b) for b in IESIRI}
    B = [{b: fereastra(MI[b][k]) for b in BRATE} for k in range(K)]
    I = [{b: fereastra(ME[b][k]) for b in IESIRI} for k in range(K)]
    P = [fereastra(r["pietoni"]) for r in rez]
    S = [sc if strategie == "REAL" else np.array([v[0] for v in valuri_in_fereastra(MI["magheru"][k])]) for k in range(K)]      # același semafor, același ceas
    info = info_v2()
    NS = [ns_din_stari(r) for r in rez]
    ns_c, ev_c = ferestre_in(cam["ns"], INCALZIRE_S, SFARSIT_S), ferestre_in(cam["ev"], INCALZIRE_S, SFARSIT_S)
    muchii = cicluri_din(sc)
    profile = {}

    # A. Din cerere: numărători, deci pe muchii, unde nu se pierde niciun vehicul
    for b in BRATE:
        c = len(cam["intrari"][b]) * f[b] * 3600 / n_s
        T.rand("A", "debit", f"debit, veh/h: {b}", [len(fereastra(r["brate"][b])) * 3600 / n_s for r in rez], c, mod="relativ", prag=T.prag(f"debit:{b}", PRAGURI["debit"], "scris"))

    # B. Independente de cerere
    for b in BRATE:
        cc = varf_pe_cicluri(cam["intrari"][b], muchii) * f[b]
        c = mediana(cc)
        v = [mediana(varf_pe_cicluri(x[b], cicluri_din(s))) for x, s in zip(B, S)]
        zc = zgomot_statistica(cc, np.median, rng)
        zs, cuanta = (zgomot_seeduri_scalar(v) / c, f[b] / FEREASTRA_VARF_S / c) if c else (_GOL, _GOL)      # cuanta: un vehicul în fereastră
        g = float(np.mean(v)) if K else _GOL
        nota = f"cu factorul brațului, {f[b]:g}: la factor ×0,9 abaterea ar fi {g / (c * 0.9) - 1:+.2f}, la ×1,1 {g / (c * 1.1) - 1:+.2f}; eroarea factorului nu e în prag" if c and np.isfinite(c) else "fără vehicule în cameră"
        T.rand("B", "varf_20s", f"debit de vârf pe {FEREASTRA_VARF_S} s, veh/s: {b}", v, c, mod="relativ", zgomot=zc, z_seed=zs, prag=T.prag(f"varf_20s:{b}", prag_din_zgomot(zc, zs, cuanta)), nota=_alatura(nota, nota_citire("intrare", b)), citire=citiri[("intrare", b)])
    for o, d, cuantile, departe in MISCARI:
        x = np.array([td - to for a, e, to, td in cam["miscari"] if a == o and e == d and td > to and INCALZIRE_S <= to < SFARSIT_S])
        y = [np.array([q[3] - q[2] for q in r["virtuala"] if q[0] == o and q[1] == d and INCALZIRE_S <= q[2] < SFARSIT_S]) for r in rez]
        err = [q[4] for r in rez for q in r["virtuala"] if q[0] == o and q[1] == d and INCALZIRE_S <= q[2] < SFARSIT_S and np.isfinite(q[4])]
        for q in cuantile:
            nota = f"n: cameră {len(x)}, geamăn {'/'.join(str(len(u)) for u in y)}"
            masura = f"timp zonă–zonă, {o} → {d}, p{q}, s"
            if len(x) < MIN_TRAIECTORII:
                T.rand("B", "timp", masura, nota=nota + "; prea puține în cameră")
                continue
            c = float(np.percentile(x, q))
            v = [float(np.percentile(u, q)) if len(u) >= MIN_TRAIECTORII else _GOL for u in y]
            lipsa = sum(len(u) < MIN_TRAIECTORII for u in y)
            zc = zgomot_statistica(x, lambda a: np.percentile(a, q), rng)
            zs, pro = zgomot_seeduri_scalar(v) / c, mediana(err) / c
            calc = prag_din_zgomot(zc, zs, pro)
            prag = T.prag(f"timp:{o}>{d}:p{q}", max(calc, PRAGURI["timp_departe"]) if departe else calc)
            if lipsa == K:          # în cameră sunt destule, deci o cameră virtuală stricată nu poate rămâne fără verdict
                T.rand("B", "timp", masura, v, c, mod="relativ", zgomot=zc, nota=f"{nota}; geamănul nu are traiectorii", prag=prag, verdict="peste prag")
                continue
            T.rand("B", "timp", masura, v, c, mod="relativ", zgomot=zc, z_seed=zs, nota=_alatura(f"{nota}; eroarea proiecției {pro:.0%}", f"{lipsa} din {K} seed-uri fără valoare, sub {MIN_TRAIECTORII} traiectorii" if lipsa else ""), prag=prag, lipsa=lipsa)
    intrari_forma = {**cam["intrari"], "dacia_vest": fara_etapa(cam["intrari"]["dacia_vest"], cam["ns"])}      # pe Dacia vest, în N–S, adnotatorii văd 0–7% din vehicule, detectorul 19–37%: fragmente
    nota_fragmente = "fără momentele camerei din N–S: la adnotatori sunt 0–7% din vehicule, la detector 19–37%, deci fragmente"
    for tip, brate, momente_cam, momente_g, cheie_prag in (("intrare", BRATE, intrari_forma, MI, "decalaj_intrare"), ("ieșire", IESIRI, cam["iesiri"], ME, "decalaj_iesire")):
        for b in brate:
            mc = momente_cam[b]
            pc = forma(profil(mc, sc))       # pe forme și la intrări: fără factor, deci rândul nu depinde de el
            lista = [(m, s) for m, s in zip(momente_g[b], S)]      # netăiate: fereastra se aplică după mutare
            dl, l_dl, l_0 = decalaj_aliniere(pc, lista, True)
            singure = [decalaj_aliniere(pc, [u], True)[0] for u in lista]
            fara = decalaje_fara_cate_unul(pc, lista, True)
            zc, zs = zgomot_decalaj(mc, sc, rng), float(max(abs(x - dl) for x in fara)) if fara else _GOL
            prag = T.prag(f"{cheie_prag}:{b}", max(prag_din_zgomot(zc, zs), 1.0))
            nota = _alatura(f"abaterea formei: {l_0:.3f} la 0 s, {l_dl:.3f} la {dl:+d} s", f"la marginea plajei de ±{PLAJA_DECALAJ_S} s" if abs(dl) >= PLAJA_DECALAJ_S else "",
                            f"prag ≥ plaja de ±{PLAJA_DECALAJ_S} s, deci rândul n-ar putea pica" if prag[0] >= PLAJA_DECALAJ_S else "", f"fiecare seed singur: {singure}" if K > 1 else "",
                            nota_citire(tip, b), nota_iesire_camera(cam, b) if tip == "ieșire" else "", nota_fragmente if (tip, b) == ("intrare", "dacia_vest") else "")
            T.rand("B", "decalaj", f"decalaj de aliniere, s: {tip} {b}", fara or [dl], 0.0, geaman=float(dl), mod="absolut", zgomot=zc, z_seed=zs, nota=nota, prag=prag, minmax=True, citire=citiri[(tip, b)],
                   verdict="neinformativ" if prag[0] >= PLAJA_DECALAJ_S or (tip == "ieșire" and parte_cu_origine(cam, b) < MIN_PARTE_CU_ORIGINE) else None)
    ce = cam["iesiri"]["dacia_est"]
    ns_intregi = ferestre_in(cam["ns"], INCALZIRE_S, SFARSIT_S, intregi=True)
    citire_ns = citiri.get(CITIRE_NS, citiri[("ieșire", "dacia_est")])
    if citire_ns == "zonă":     # în N–S, camera virtuală prinde vehiculele de aici, chiar dacă pe toată ora se citește pe muchie
        nc_iesire = f"în N–S, citit pe zonă, ca în cameră: prinde {np.mean([acoperire_ns(r) for r in rez]):.0%}; muchia e la zebră, deci după așteptare"
        I_ns = [fereastra(np.asarray(r.get("zone", {}).get("ieșire", {}).get("dacia_est", ()), float)) for r in rez]
    else:
        nc_iesire = nota_citire("ieșire", "dacia_est")
        I_ns = [x["dacia_est"] for x in I]
    mat = matrice_ferestre(ce, ns_intregi)
    pc_ns = forma(mat.mean(0))
    pg_ns = [matrice_ferestre(x, n).mean(0) for x, n in zip(I_ns, NS)]
    fg_ns = [forma(p) for p in pg_ns]
    zc, zs = zgomot_reesantionare(mat, rng, normat=True), zgomot_seeduri(fg_ns)
    T.rand("B", "iesire_ns", "ieșirea Dacia est în etapa N–S: forma pe 10 s (camera, geamăn: veh/ciclu)", [p.sum() for p in pg_ns], float(mat.sum(1).mean()), abateri=[abatere_profil(pc_ns, p) for p in fg_ns],
           abatere=abatere_profil(pc_ns, forma(np.mean(pg_ns, axis=0))), mod="abatere", zgomot=zc, z_seed=zs, prag=T.prag("iesire_ns:forma", prag_din_zgomot(zc, zs)), nota=_alatura("nu depinde de urmărirea de la origine; fără factori", nc_iesire),
           profil_g=forma(np.mean(pg_ns, axis=0)), citire=citire_ns)
    profile["ieșire dacia_est, în N–S"] = (pc_ns, forma(np.mean(pg_ns, axis=0)))
    vc = per_etapa(ce, ns_intregi, PIETONI_DE_LA_S, PIETONI_PANA_LA_S)
    vg = [per_etapa(x, n, PIETONI_DE_LA_S, PIETONI_PANA_LA_S) for x, n in zip(I_ns, NS)]
    v = [float(u.mean()) if len(u) else _GOL for u in vg]
    c = float(vc.mean()) if len(vc) else _GOL
    zc, zs = zgomot_statistica(vc, np.mean, rng), zgomot_seeduri_scalar(v) / c if c else _GOL
    T.rand("B", "iesire_24_60", f"ieșirea Dacia est, s {PIETONI_DE_LA_S}–{PIETONI_PANA_LA_S} din N–S: nivel, veh/etapă", v, c, mod="relativ", zgomot=zc, z_seed=zs, prag=T.prag("iesire_24_60:nivel", prag_din_zgomot(zc, zs)), nota=_alatura("fără factori", nc_iesire), citire=citire_ns)
    pc = cam["pietoni"]
    if pc is not None:
        nc = per_etapa(pc, ns_intregi, PIETONI_DE_LA_S, PIETONI_PANA_LA_S)
        ng = [per_etapa(x, n, PIETONI_DE_LA_S, PIETONI_PANA_LA_S) for x, n in zip(P, NS)]
        panta_c = regresie(nc, vc)["panta"]
        v = [regresie(a, u)["panta"] for a, u in zip(ng, vg)]
        ind = np.arange(len(nc))
        zc = zgomot_statistica(ind, lambda i: regresie(nc[i.astype(int)], vc[i.astype(int)])["panta"], rng, relativ=False)
        zs = zgomot_seeduri_scalar(v)
        T.rand("B", "iesire_24_60", f"ieșirea Dacia est, s {PIETONI_DE_LA_S}–{PIETONI_PANA_LA_S} din N–S: pantă față de pietoni, veh/pieton", v, panta_c, mod="absolut", zgomot=zc, z_seed=zs, pieton=True,
               prag=T.prag("iesire_24_60:panta", prag_din_zgomot(zc, zs)), nota=f"pietoni pe etapă: cameră {nc.mean() if len(nc) else _GOL:.1f}, geamăn {np.mean([a.mean() if len(a) else _GOL for a in ng]):.1f}; detectorul pierde mulțimile", citire=citire_ns)
        vazuti = len(pc) * 3600 / n_s
        if cam["pietoni_pe_ora"] is not None:       # numărătoarea e pe sferturi, deci pe toată ora; geamănul, la fel
            n_p, f_p = cam.get("persoane_pe_ora", cam["pietoni_pe_ora"]), cam.get("f_pietoni", 1.0)
            c, v = n_p * f_p, [int(((np.asarray(r["pietoni"], float) >= 0) & (np.asarray(r["pietoni"], float) < SFARSIT_S)).sum()) * 3600 / SFARSIT_S for r in rez]
            sursa = f"camera: persoanele numărate pe Dacia est, {n_p:.0f} pe oră, × factorul de cerere ales, {f_p:g}; ambele pe toată ora; detectorul singur, doar pe zebra de ieșire: {cam['pietoni_pe_ora']:.0f}, iar traversările văzute: {vazuti:.0f} pe oră"
        else:
            c, v = vazuti, [len(x) * 3600 / n_s for x in P]
            sursa = f"fără numărătoarea orei (data/counts_cor): doar traversările văzute, pe {INCALZIRE_S}–{SFARSIT_S} s, la fel la geamăn; fără cei care așteaptă la bordură"
        zc, zs = zgomot_statistica(matrice_valuri(pc, sc).sum(1), np.mean, rng), zgomot_seeduri_scalar(v) / c if c else _GOL
        T.rand("A", "pietoni_zebra", "pietoni pe zebra Dacia est, pe oră", v, c, mod="relativ", zgomot=zc, z_seed=zs, pieton=True, prag=T.prag("pietoni_zebra:numar", prag_din_zgomot(zc, zs, PRAGURI["pietoni_detectie"])), nota=sursa)
        mat = matrice_valuri(pc, sc)
        pc_h = forma(mat.mean(0))
        pg_h = [forma(profil(x, s)) for x, s in zip(P, S)]
        medie_h = forma(np.mean([profil(x, s) for x, s in zip(P, S)], axis=0))
        zc, zs = zgomot_reesantionare(mat, rng, normat=True), zgomot_seeduri(pg_h)
        T.rand("B", "pietoni_zebra", "pietoni pe zebra Dacia est: histograma intrărilor pe 10 s", camera=_GOL, abateri=[abatere_profil(pc_h, p) for p in pg_h], abatere=abatere_profil(pc_h, medie_h),
               mod="abatere", zgomot=zc, z_seed=zs, pieton=True, prag=T.prag("pietoni_zebra:histograma", prag_din_zgomot(zc, zs)), nota="se raportează, chiar dacă pică; detectorul pierde începutul mulțimilor, deci histograma camerei e întârziată și lățită", profil_g=medie_h)
        profile["pietoni zebra dacia_est"] = (pc_h, medie_h)
    else:
        T.rand("B", "pietoni_zebra", "pietoni pe zebra Dacia est, pe oră", nota="fără jurnalul local al pietonilor", pieton=True)
    if strategie == "REAL" and len(sc) >= 8:
        intregi = muchii[1:] <= SFARSIT_S      # un val tăiat de sfârșitul ferestrei și-ar păstra durata, dar nu și vehiculele
        durate = np.array([v_[1] - v_[0] for v_ in cam["val"]])[intregi]
        reg_c = regresie(durate, (np.histogram(cam["intrari"]["magheru"], muchii)[0] * f["magheru"])[intregi])
        reg_g = [regresie(durate, np.histogram(x["magheru"], muchii)[0][intregi]) for x in B]
        for k, nume in (("panta", "pantă, veh/s"), ("intercept", "intercept, veh"), ("rest", "abaterea restului, veh")):
            T.rand("B", "regresie_val", f"Magheru, vehicule pe val după durata valului: {nume}", [u[k] for u in reg_g], reg_c[k], nota="diagnostic; corelația nu e o dovadă" if k != "panta" else f"diagnostic; în cameră ±{1.96 * reg_c['eroare_panta']:.2f}", citire=citiri[("intrare", "magheru")])
    complete: dict[tuple[str, str], int] = {}
    for o, d, _, td in cam["miscari"]:
        if 0 <= td < cam["od"]["durata_s"]:
            complete[(o, d)] = complete.get((o, d), 0) + 1
    for (o, d), n in sorted(complete.items()):
        cerere = cam["od"]["od_vehicule"].get(f"{o}>{d}", 0)
        T.rand("B", "od", f"O–D {o} → {d}: traiectorii complete în cameră / cerere", camera=float(n), geaman=float(cerere), verdict="în prag" if cerere >= n else "peste prag", din_simulare=False, nota="fără factori; verifică cererea, nu dinamica" + ("" if cerere >= n else "; cererea e sub limita de jos"))

    # C. Ceasul și ferestrele
    for tip, brate, normat in (("intrare", BRATE, False), ("ieșire", IESIRI, True)):
        for b in brate:
            mc, ms = (intrari_forma[b], B) if tip == "intrare" else (cam["iesiri"][b], I)
            scala = f[b] * len(cam["intrari"][b]) / max(len(mc), 1) if tip == "intrare" else 1.0      # factorul e pe tot brațul, cu fragmente cu tot
            mat = matrice_valuri(mc, sc) * scala
            pc = forma(mat.mean(0)) if normat else mat.mean(0)
            pg = [profil(x[b], s) for x, s in zip(ms, S)]
            medie = np.mean(pg, axis=0)
            if normat:
                pg = [forma(p) for p in pg]
                medie = forma(medie)
                n = len(mc)
                in_ns = np.zeros(len(mc), bool)
                for a_, b_ in cam["ns"]:
                    in_ns |= (mc >= a_) & (mc < b_)
                nul = nul_esantionat(pc, ns_c, n, sc, rng, realizari=K, normat=True, alte_ferestre=ev_c, cota=float(in_ns.mean()) if n else 0.0)
            else:
                nul = nul_esantionat(pc, ns_c if b in ("magheru", "catargiu") else ev_c, int(round(len(mc) * scala)), sc, rng, realizari=K)
            zc, zs = zgomot_reesantionare(mat, rng, normat=normat), zgomot_seeduri(pg)
            cheie = "forma_iesire" if normat else "profil_intrare"
            T.rand("C", cheie, f"{'forma pe ciclu, ieșirea' if normat else 'profil pe ciclu'}: {b}", abateri=[abatere_profil(pc, p) for p in pg], abatere=abatere_profil(pc, medie), mod="abatere",
                   nul=mediana(nul), zgomot=zc, z_seed=zs, prag=T.prag(f"{cheie}:{b}", prag_din_zgomot(zc, zs)), profil_g=medie, citire=citiri[(tip, b)],
                   nota=_alatura("zona camerei prinde și mașinile care așteaptă la roșu" if tip == "intrare" and b == "dacia_vest" else "", nota_citire(tip, b), nota_iesire_camera(cam, b) if normat else ""))
            profile[f"{tip} {b}"] = (pc, medie)

    # D. Siguranță și limite
    def raport(masura, cheie, v, pieton=False, nota=""):
        T.rand("D", cheie, masura, v, pieton=pieton, nota=nota)

    sositi = [max(r["r"]["vehicule_sosite"], 1) for r in rez]
    T.rand("D", "teleportari", "teleportări", [r["r"]["teleportari"] for r in rez], mod="valoare", prag=T.prag("teleportari", PRAGURI["teleportari"], "scris"))
    rulari = rulari_cu_probleme(rez)
    T.rand("D", "rulari", "rulări cu teleportări sau cu blocaj presupus", geaman=float(len(rulari)), nota=_alatura(f"din {K}", *[f"seed {T.seeds[i]}: {m}" for i, m in rulari.items()], "" if K >= 4 else "sub 4 seed-uri, blocajul nu se poate recunoaște"))
    T.rand("D", "ciocniri_sumo", "ciocniri între vehicule văzute de SUMO", [r["r"]["ciocniri_vehicule"] for r in rez], mod="valoare", prag=T.prag("ciocniri_vehicule", PRAGURI["ciocniri_vehicule"], "scris"))
    raport("atingeri geometrice vehicul–vehicul în cutia pieței: axă–inel", "atingeri_vv", [r["vv"]["axa_inel"] for r in rez], nota="limită a rețelei din OSM; SUMO nu le vede")
    raport("atingeri geometrice vehicul–vehicul în cutia pieței: restul", "atingeri_vv", [r["vv"]["alte"] for r in rez])
    raport("atingeri geometrice vehicul–vehicul: din toate, pătrundere de cel puțin 1 m", "atingeri_vv", [r["vv"]["adanc_1m"] for r in rez])
    aici = [r["ciocniri"]["mers_masurati"] + r["ciocniri"]["mers_extrapolati"] for r in rez]       # contorul de aici și cel din `evaluate` trebuie să coincidă
    T.rand("D", "atingeri_pieton", "vehicule în mișcare care ating pietoni (SUMO, peste 1 m/s), parte din vehicule", [r["r"]["ciocniri_pieton_in_miscare"] / s for r, s in zip(rez, sositi)], mod="valoare", pieton=True,
           prag=T.prag("pieton_in_miscare_fractie", PRAGURI["pieton_in_miscare_fractie"], "scris"), nota="pe seed: " + ", ".join(str(r["r"]["ciocniri_pieton_in_miscare"]) for r in rez) + ("" if aici == [r["r"]["ciocniri_pieton_in_miscare"] for r in rez] else f"; ATENȚIE: Contoare numără {aici}"))
    for g, nume in (("masurati", "măsurați"), ("extrapolati", "extrapolați")):
        raport(f"vehicule în mișcare care ating pietoni (SUMO), pietoni {nume}", "atingeri_pieton", [r["ciocniri"][f"mers_{g}"] for r in rez], pieton=True)
    raport("atingeri cu vehiculul oprit (SUMO, sub 1 m/s; `evaluate` le filtrează)", "atingeri_oprit", [r["ciocniri"]["oprit_masurati"] + r["ciocniri"]["oprit_extrapolati"] for r in rez], pieton=True)
    raport("atingeri geometrice pe zebre, vehiculul oprit toată atingerea", "atingeri_oprit", [r["vp"]["oprit_masurati"] + r["vp"]["oprit_extrapolati"] for r in rez], pieton=True, nota="pietonii din zone de mers nu se numără")
    raport("atingeri geometrice pe zebre, vehiculul în mișcare, pietoni măsurați", "atingeri_pieton", [r["vp"]["mers_masurati"] for r in rez], pieton=True)
    raport("atingeri geometrice pe zebre, vehiculul în mișcare, pietoni extrapolați", "atingeri_pieton", [r["vp"]["mers_extrapolati"] for r in rez], pieton=True)
    parti, evitate = [], []
    for r in rez:
        intr = [(t, i, c) for t, i, c in r["intrari_zebre"] if INCALZIRE_S <= t < SFARSIT_S]
        rosu = [(t, i) for t, i, c in intr if c == "r"]
        parti.append(len(rosu) / len(intr) if intr else _GOL)
        evitate.append(asteptare_evitata(rosu, r["stari"]) / 3600)
    raport("intrări pe zebre pe roșu, parte din intrări", "rosu", parti, pieton=True, nota="din deblocare, la ≈60 s; nu e o dovadă de realism")
    raport("așteptarea evitată de cei intrați pe roșu, ore", "rosu", evitate, pieton=True)
    T.rand("D", "neintrate", "vehicule neintrate sau nesosite la final, parte din vehicule", [r["r"]["nefinalizate"] / s for r, s in zip(rez, sositi)], mod="valoare", prag=T.prag("neintrate_fractie", PRAGURI["neintrate_fractie"], "scris"))
    pd_cam = cam.get("pierdere_detectie") or {}
    T.rand("D", "pierdere_detectie", "pierdere de detecție pe întuneric", camera=pd_cam.get("raport", _GOL), din_simulare=False, verdict="peste prag" if pd_cam.get("marcata") else "în prag",
           nota=f"din cameră: ieșirile Dacia est fără virajul Magheru → Dacia est, {pd_cam.get('x', 0)}, față de intrările Dacia vest, {pd_cam.get('v', 0)}; contează doar pe întuneric, la trafic mare; raport peste {PIERDERE_DETECTIE['raport']:g}: ora iese din decizie")
    raport(f"vehicule neintrate la secunda {SFARSIT_S}: toate", "neintrate", [r["neintrate"]["total"] for r in rez])
    raport(f"vehicule neintrate la secunda {SFARSIT_S}: Dacia vest", "neintrate", [r["neintrate"]["dacia_vest"] for r in rez])
    raport("pierdere totală, ore", "pierdere", [r["r"]["pierdere_totala_h"] for r in rez])
    for k, nume in (("magheru", "Magheru"), ("catargiu", "Lascăr Catargiu"), ("dacia_est", "Dacia est"), ("dacia_vest", "Dacia vest"), ("fond", "traficul de fond")):
        raport(f"pierdere pe ramura {nume}, ore", "pierdere", [r["pierderi"].get(k, 0.0) for r in rez])
    if any(r["pierderi"].get("alta") for r in rez):
        raport("pierdere pe alte rute, ore", "pierdere", [r["pierderi"].get("alta", 0.0) for r in rez])
    raport("pierdere, pietoni măsurați, ore", "pierdere", [r["pierderi"].get("pietoni_masurati", 0.0) for r in rez], pieton=True)
    raport("pierdere, pietoni extrapolați, ore", "pierdere", [r["pierderi"].get("pietoni_extrapolati", 0.0) for r in rez], pieton=True, nota="ipoteză: pe aceste brațe, pietonii nu se văd bine")
    d = pd.DataFrame(T.randuri)
    return d, {k: ([round(float(x), 3) for x in c], [round(float(x), 3) for x in g]) for k, (c, g) in profile.items()}


def marcheaza_deosebiri(baza: pd.DataFrame, proba: pd.DataFrame, tip: str) -> pd.DataFrame:
    """Pe fiecare rând: proba se deosebește de geamănul de bază? „da”, „nu”, „fără obiect” (rândul despre pietoni, la o probă fără pietoni), „–” (rândul nu vine din simulare, nu se poate spune sau e neinformativ).
    Pe profile și pe forme, proba se compară direct cu baza (`dist_baza`, de citit față de prag); pe celelalte, ca distanță față de cameră, cu intervalele lor."""
    b = baza.set_index("masura")
    out, dist = [], []
    for _, r in proba.iterrows():
        d = _GOL
        if r["masura"] not in b.index or not r["din_simulare"] or r["cheie"] == "rulari":
            z = "–"
        elif r["pieton"] and tip == "fara_pietoni":
            z = "fără obiect"
        else:
            q = b.loc[r["masura"]]
            if q["verdict"] == "neinformativ":
                z = None
            elif q["profil_g"] and r["profil_g"]:
                d, z = deosebeste_profil(np.array(json.loads(q["profil_g"])), np.array(json.loads(r["profil_g"])), q["prag"])
            else:
                cu_abatere = np.isfinite(q["abatere"]) and np.isfinite(r["abatere"])
                x = (q["abatere"], q["ab_lo"], q["ab_hi"], r["abatere"], r["ab_lo"], r["ab_hi"]) if cu_abatere else (q["geaman"], q["g_lo"], q["g_hi"], r["geaman"], r["g_lo"], r["g_hi"])
                z = deosebeste(*x, q["prag"])
            z = "–" if z is None else ("da" if z else "nu")
        out.append(z)
        dist.append(d)
    proba = proba.copy()
    proba["deosebeste"] = out
    proba["dist_baza"] = dist
    return proba


# --------------------------------------------------------------------- ieșirea

def _n(x) -> str:
    if x is None or not np.isfinite(x):
        return "–"
    a = abs(x)
    return f"{x:.0f}" if a >= 100 else f"{x:.1f}" if a >= 10 else f"{x:.2f}" if a >= 0.1 or a == 0 else f"{x:.3f}"


def _int(lo, hi) -> str:
    return "–" if not np.isfinite(lo) else _n(lo) if lo == hi else f"{_n(lo)}…{_n(hi)}"


def tabel_text(baza: pd.DataFrame, probe: dict[str, pd.DataFrame]) -> str:
    """Tabelul, pe grupuri. Coloana „abatere” e pe media seed-urilor, cu intervalul dintre ele; la probe, „≠” spune dacă rândul o deosebește de bază."""
    lat = 78
    linii = []
    for g, titlu in GRUPURI.items():
        d = baza[baza["grup"] == g]
        if d.empty:
            continue
        cap = f"{'măsura':{lat}s} {'camera':>8s} {'geamăn':>8s} {'mediană':>8s} {'pe seed-uri':>14s} {'abatere':>8s} {'interval':>15s} {'prag':>7s} {'verdict':>12s}"
        if g == "C":
            cap += f" {'nul':>6s} {'p95':>6s} {'reper':>13s}"
        for tip in probe:
            cap += f" | {tip[:12]:>12s} {'abatere':>8s} {'verdict':>12s} {'≠':>5s}"
        linii += [f"\n{g}. {titlu}", cap]
        for _, r in d.iterrows():
            s = (f"{r['masura'][:lat]:{lat}s} {_n(r['camera']):>8s} {_n(r['geaman']):>8s} {_n(r['g_mediana']):>8s} {_int(r['g_min'], r['g_max']):>14s} {_n(r['abatere']):>8s} {_int(r['ab_lo'], r['ab_hi']):>15s} "
                 f"{_n(r['prag']):>7s} {r['verdict']:>12s}")
            if g == "C":
                s += f" {_n(r['nul']):>6s} {_n(r['zgomot_camera_p95']):>6s} {r['reper']:>13s}"
            for tip, dp in probe.items():
                q = dp[dp["masura"] == r["masura"]]
                if q.empty:
                    s += f" | {'–':>12s} {'–':>8s} {'–':>12s} {'–':>5s}"
                else:
                    q = q.iloc[0]
                    s += f" | {_n(q['geaman']):>12s} {_n(q['abatere']):>8s} {q['verdict']:>12s} {'f.o.' if q['deosebeste'] == 'fără obiect' else q['deosebeste']:>5s}"
            linii.append(s + (f"   ({r['nota']})" if r["nota"] else ""))
    linii.append("\ngeamăn: media seed-urilor; pe seed-uri: min…max; interval: al abaterii, p10–p90 de la 5 seed-uri în sus, min–max sub atât. La decalaj, „pe seed-uri” și „interval” vin din media fără câte un seed.")
    if probe:
        linii.append("≠: proba se deosebește de bază pe acest rând; pe profile și pe forme, direct față de profilul bazei; f.o.: fără obiect, rândul e despre pietoni, iar proba nu are pietoni; –: nu se poate spune, sau rândul nu vine din simulare, sau e neinformativ.")
    return "\n".join(linii)


def rezumat_probe(probe: dict[str, pd.DataFrame], k_proba: int, k_baza: int) -> str:
    """Ce rânduri și ce măsuri deosebesc fiecare probă de bază. O măsură care nu le deosebește nu e utilă, pe această oră. Cu un singur seed pe probă, lista se schimbă de la un seed la altul, deci nu se dă."""
    linii = [f"\nCe rânduri deosebesc probele de bază (probe pe {k_proba} {'seed' if k_proba == 1 else 'seed-uri'}, baza pe {k_baza} {'seed' if k_baza == 1 else 'seed-uri'}):"]
    for tip, d in probe.items():
        linii.append(f"  {tip}: {int((d['deosebeste'] == 'da').sum())} din {int((d['deosebeste'].isin(['da', 'nu'])).sum())}")
        if k_proba >= 2:
            linii += [f"    - {m}" for m in d[d["deosebeste"] == "da"]["masura"]]
    if k_proba < 2:
        linii.append("Lista măsurilor utile nu se dă cu un singur seed pe probă: se schimbă de la un seed la altul; pentru ea, --seeds-proba cu cel puțin 2 seed-uri.")
        return "\n".join(linii)
    t = pd.concat([d.assign(proba=tip) for tip, d in probe.items()])
    vazute = t[t["deosebeste"].isin(["da", "nu"])]
    nu = vazute.groupby("masura", sort=False)["deosebeste"].agg(lambda s: not (s == "da").any())
    linii.append(f"Rânduri care nu deosebesc nicio probă, pe {k_proba} seed-uri, deci nu arată nimic despre aceste defecte:")
    linii += [f"    - {m}" for m in nu[nu].index]
    pe_cheie = vazute.groupby("cheie", sort=False)["deosebeste"].agg(lambda s: (s == "da").any())
    linii.append(f"Măsuri care nu deosebesc nicio probă, pe niciun rând, pe {k_proba} seed-uri: " + (", ".join(pe_cheie[~pe_cheie].index) or "niciuna"))
    od = t[(t["deosebeste"] == "–") & ~t["din_simulare"]]["masura"].nunique()
    alte = t[(t["deosebeste"] == "–") & t["din_simulare"] & (t["cheie"] != "rulari")]["masura"].drop_duplicates().tolist()
    fo = t[t["deosebeste"] == "fără obiect"]["masura"].nunique()
    linii.append(f"Nu se pot judeca așa: {od} rânduri O–D, fiindcă cererea nu se schimbă cu proba, deci ele verifică cererea, nu dinamica; {fo} rânduri despre pietoni, la proba fără pietoni, unde n-au obiect" + (f"; valori lipsă sau rând neinformativ: {alte}" if alte else ""))
    return "\n".join(linii)


def cai_git(scenarii: list[str]) -> list[str]:
    """Tot ce hotărăște un tabel, în afară de cod: configurațiile, rețeaua, tipurile de vehicule și, pe fiecare scenariu, cfg-ul, rutele, numărătoarea și jurnalul public al zilei."""
    cai = ["src/romana", "config/demand_v2.json", "config/camera_v2.json", "config/retea_v2.json", "sumo/net", "sumo/demand/vtypes_v2.add.xml"]
    for s in scenarii:
        zi = re.search(r"zi_(\d{4}-\d\d-\d\d)", s).group(1)
        cai += [f"sumo/scenarios/{s}.sumocfg", f"sumo/demand/{s}", f"sumo/demand/cor_zi_{zi}_rezumat.json", f"data/counts_cor/numaratori_{zi}.csv", f"data/trajectories/traiectorii_{zi}.jsonl.gz"]
    return list(dict.fromkeys(cai))


def stare_git(scenarii: list[str] | None = None) -> dict:
    """Commitul de la care rulează validarea și dacă fișierele care o hotărăsc sunt comise, ca un tabel vechi să nu poată fi confundat cu cel curent. `schimbate`: ce nu e comis."""
    git = shutil.which("git") or next(iter(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe"))), None)
    if git is None:
        return {"commit": "necunoscut", "git_curat": None, "schimbate": []}
    try:
        commit = subprocess.run([git, "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        schimbate = subprocess.run([git, "status", "--porcelain", "--", *cai_git(scenarii or [])], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "necunoscut", "git_curat": None, "schimbate": []}
    lista = [x[3:] for x in schimbate.splitlines() if x.strip()]
    return {"commit": commit, "git_curat": not lista, "schimbate": lista}


def poarta(baza: pd.DataFrame) -> dict:
    """Trece doar dacă toate rândurile porții sunt „în prag”; „nedecis” nu ajunge."""
    d = baza.set_index("masura")
    randuri = {m: str(d.loc[m, "verdict"]) if m in d.index else "lipsă" for m in POARTA}
    return {"trece": all(v == "în prag" for v in randuri.values()), "randuri": randuri}


def figura(p: dict, cale: str) -> None:
    """Patru panouri cu câte două curbe, camera și media seed-urilor geamănului, pe același ceas: intrările mari și ieșirea care le deosebește cel mai greu."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panouri = (("intrare magheru", "Intrarea Magheru"), ("intrare catargiu", "Intrarea Lascăr Catargiu"), ("intrare dacia_est", "Intrarea Dacia est"), ("ieșire dacia_est", "Ieșirea Dacia est, parte din total"))
    fig, axe = plt.subplots(2, 2, figsize=(10, 5.4), sharex=True)
    x = (np.arange(BINI) + 0.5) * BIN_S
    for ax, (k, titlu) in zip(axe.flat, panouri):
        c, g = p["profile"][k]
        ax.plot(x, c, color="#8a8984", linewidth=2, label="camera")
        ax.plot(x, g, color="#1f6f8b", linewidth=2, label="geamănul")
        ax.set_title(titlu, fontsize=10, loc="left")
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color="#e4e3df", linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.legend(frameon=False, fontsize=8, loc="upper right")
    for ax in axe[1]:
        ax.set_xlabel("secunde de la începutul valului de pe Magheru")
    for ax in axe[:, 0]:
        ax.set_ylabel("pe ciclu, la 10 s")
    fig.tight_layout()
    fig.savefig(cale, dpi=130)


def una(sarcina: tuple) -> dict:
    """O simulare, în procesul ei: libsumo ține o singură simulare pe proces, iar avertismentele SUMO nu au ce căuta în tabel."""
    d = os.open(os.devnull, os.O_WRONLY)
    os.dup2(d, 1)
    os.dup2(d, 2)
    stem, _, cfg, strategie, seed, orizont, geometrie = sarcina
    return ruleaza(stem, strategie, seed, Path(cfg) if cfg else None, orizont, geometrie)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarii", nargs="+", help="doar scenarii ale măsurii noi: cor_zi_AAAA-LL-ZZ_tip")
    ap.add_argument("--strategie", default="REAL", help="REAL = semaforul rejucat; sau PLAN_a_b_c")
    ap.add_argument("--seeds", default="1,2,3,4,5")
    ap.add_argument("--proba", action="append", default=[], choices=["fara_pietoni", "rapid"], help="geamăn greșit dinadins, pe aceleași rânduri; cfg-urile merg în outputs/validare/probe")
    ap.add_argument("--seeds-proba", default=None, help="seed-urile probelor; implicit, cele de la --seeds")
    ap.add_argument("--procese", type=int, default=3)
    ap.add_argument("--praguri", default=None, help="fișier JSON cu pragurile fixate de autor; fără el, se calculează și se afișează")
    ap.add_argument("--scrie-praguri", default=None, help="scrie pragurile calculate, media lor pe scenariile date, într-un fișier JSON de fixat")
    ap.add_argument("--out", default=None, help="CSV, cu commitul, factorii și data rulării pe fiecare rând")
    ap.add_argument("--profile", action="store_true", help="afișează și profilele pe ciclu")
    ap.add_argument("--figura", default=None, help="PNG cu profilele primului scenariu")
    ap.add_argument("--poarta", default=None, help="scrie aici, pe fiecare scenariu, verdictul porții din § 9.11, pentru `decizie --poarta`")
    ap.add_argument("--orizont", type=int, default=None, help="doar pentru încercarea codului: oprește simularea mai devreme; rândurile nu se mai pot judeca")
    ap.add_argument("--fara-geometrie", action="store_true", help="doar pentru măsurarea costului: fără atingerile geometrice")
    a = ap.parse_args(argv)
    for s in a.scenarii:
        if not re.fullmatch(r"cor_zi_\d{4}-\d\d-\d\d_[a-z]+", s):
            ap.error(f"{s}: validarea rulează doar pe măsura nouă, pe scenariile cor_zi_AAAA-LL-ZZ_tip; scenariile ×0,8 și ×1,2 au altă cerere decât camera")
    seeds = [int(k) for k in a.seeds.split(",")]
    seeds_proba = [int(k) for k in a.seeds_proba.split(",")] if a.seeds_proba else seeds
    if a.scrie_praguri and len(seeds) < MIN_SEEDURI_PERCENTILE and not a.orizont:
        ap.error(f"--scrie-praguri cere cel puțin {MIN_SEEDURI_PERCENTILE} seed-uri: pe mai puține, zgomotul dintre seed-uri nu se poate măsura")
    fixate = {}
    if a.praguri:
        j = json.loads(Path(a.praguri).read_text(encoding="utf-8"))
        fixate = j.get("praguri", j)
    zone = load_zones(json.loads((CONFIG_DIR / "camera_v2.json").read_text(encoding="utf-8")))
    camere = {s: date_camera(s, zone) for s in a.scenarii}         # înaintea simulărilor: dacă ceva lipsește, se vede imediat
    avertismente = {s: avertismente_scenariu(s, camere[s]) for s in a.scenarii}
    for s, lista in avertismente.items():
        for x in lista:
            print(f"{s}: {x}", flush=True)
    sarcini =[(s, "baza", None, a.strategie, k, a.orizont, not a.fara_geometrie) for s in a.scenarii for k in seeds]
    sarcini += [(s, tip, str(proba_cfg(s, tip)), a.strategie, k, a.orizont, not a.fara_geometrie) for s in a.scenarii for tip in a.proba for k in seeds_proba]
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=min(a.procese, len(sarcini)), max_tasks_per_child=1) as ex:
        rez = list(ex.map(una, sarcini))
    git, factori, acum = stare_git(a.scenarii), factori_folositi(), datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    necomise = "" if git["git_curat"] else f" (necomise sau neurmărite, {len(git['schimbate'])}: {', '.join(git['schimbate'][:8])}{', …' if len(git['schimbate']) > 8 else ''})"
    print(f"Commit {git['commit']}{necomise}; rulat la {acum}; demand_v2.json {factori['sha256']}")
    print(f"Factori: {json.dumps({k: v for k, v in factori.items() if k != 'sha256'}, ensure_ascii=False)}")
    if a.orizont:
        print(f"ATENȚIE: simularea se oprește la secunda {a.orizont}, doar pentru încercarea codului; rândurile nu se pot judeca.")
    if len(seeds) < 5:
        print(f"Doar {len(seeds)} seed-uri: pragurile calculate și intervalele sunt orientative; pentru fixarea lor, cel puțin 5.")
    tot, prima_fig, calculate, porti = [], None, [], {}
    for s in a.scenarii:
        cam = camere[s]
        rb = [r for (st, tip, *_), r in zip(sarcini, rez) if st == s and tip == "baza"]
        citiri = alege_citiri(rb)
        baza, prof = randuri(cam, rb, a.strategie, fixate, citiri=citiri)
        din_baza = dict(zip(baza.loc[baza["cheie_prag"] != "", "cheie_prag"], baza.loc[baza["cheie_prag"] != "", "prag"]))
        probe = {}
        for tip in a.proba:
            rp = [r for (st, ti, *_), r in zip(sarcini, rez) if st == s and ti == tip]
            probe[tip] = marcheaza_deosebiri(baza, randuri(cam, rp, a.strategie, fixate, din_baza, citiri)[0], tip)
        det = cam["detalii"]
        print(f"\n===== {s}, strategia {a.strategie}, seed-uri {seeds}" + (f"; probe {a.proba}, seed-uri {seeds_proba}" if a.proba else ""))
        print(f"factorii orei: {cam['f']}; valuri {len(cam['sc'])}; acoperire {det['acoperire']:.0%}" + ("" if det["acoperire"] >= 0.8 else ": sub 80%, programul e în mare parte presupus și nu i se spune „semaforul real”") + ("; oră care n-a influențat alegerea măsurilor" if s in ORE_NEATINSE else ""))
        print("citirea geamănului, pe seed-urile de bază: " + rezumat_citiri(rb, citiri))
        for x in avertismente[s]:
            print(x)
        print(tabel_text(baza, probe))
        porti[s] = poarta(baza)
        print("Poarta din § 9.11: " + ("trece" if porti[s]["trece"] else "NU trece: " + "; ".join(f"{m}: {v}" for m, v in porti[s]["randuri"].items() if v != "în prag")))
        if probe:
            print(rezumat_probe(probe, len(seeds_proba), len(seeds)))
        if a.profile:
            print("\nProfile pe ciclu, pe 10 s (camera / media seed-urilor):")
            for k, (c, g) in prof.items():
                print(f"  {k:26s} {c}\n  {'':26s} {g}")
        comune = {"scenariu": s, "strategie": a.strategie, "neatinsa": s in ORE_NEATINSE, "acoperire": det["acoperire"], "orizont": a.orizont, "commit": git["commit"], "git_curat": git["git_curat"], "data_rularii": acum,
                  "factori": json.dumps(factori, ensure_ascii=False), "factori_ora": json.dumps(cam["f"]), "avertismente": " | ".join(avertismente[s])}
        tot.append(baza.assign(varianta="baza", seeds=",".join(map(str, seeds)), deosebeste="", **comune))
        tot += [d.assign(varianta=tip, seeds=",".join(map(str, seeds_proba)), **comune) for tip, d in probe.items()]
        calculate.append(baza[baza["sursa_prag"] == "calculat"][["cheie_prag", "prag"]])
        prima_fig = prima_fig or {"profile": prof}
    print("\nCost pe rulare, secunde:")
    for (st, tip, _, _, k, *_), r in zip(sarcini, rez):
        c = r["cost"]
        print(f"  {st} {tip}, seed {k}: simulare {c['simulare_s']:.0f} (contoare {c['contoare_s']:.1f}, poziții {c['pozitii_s']:.1f}, geometrie {c['geometrie_s']:.1f}), camera virtuală {c['camera_virtuala_s']:.1f}")
    print("\nRânduri renunțate, cu motivul lor:")
    for k, v in RENUNTATE.items():
        print(f"  {k}: {v}")
    print("\nLimite declarate:")
    for k, v in LIMITE.items():
        print(f"  {k}: {v}")
    praguri =pd.concat(calculate).groupby("cheie_prag")["prag"].mean().round(4)
    if len(praguri):
        print("\nPraguri calculate acum, de fixat înaintea zilei de validare (--scrie-praguri, apoi --praguri):")
        print("  " + ", ".join(f"{k}={v}" for k, v in praguri.items()))
    if a.scrie_praguri:
        Path(a.scrie_praguri).parent.mkdir(parents=True, exist_ok=True)
        Path(a.scrie_praguri).write_text(json.dumps({"_descriere": "Pragurile din zgomotul camerei și al seed-urilor, media pe scenarii. Se fixează înaintea zilei de validare și se comit.", "commit": git["commit"], "data": acum, "scenarii": a.scenarii, "seeds": seeds,
                                                     "factori": factori, "praguri": {k: float(v) for k, v in praguri.items()}}, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.poarta:
        Path(a.poarta).parent.mkdir(parents=True, exist_ok=True)
        Path(a.poarta).write_text(json.dumps({"commit": git["commit"], "data_rularii": acum, "seeds": seeds, "scenarii": porti}, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pd.concat(tot, ignore_index=True).round(4).to_csv(a.out, index=False)
    if a.figura:
        figura(prima_fig, a.figura)


if __name__ == "__main__":
    main()
