"""Semaforul real, rejucat din cameră (§ 6.5): etapele măsurate ciclu cu ciclu, în locul unui plan fix.

Semaforul real își schimbă durata de la un ciclu la altul, deci un plan fix îl aproximează doar. Aici, începutul și sfârșitul fiecărui val de vehicule de pe
Magheru, din jurnalul public al zilei, dau etapele: verde N–S cât a ținut valul, apoi E–V până la următorul val, minus tranzițiile și etapa scurtă. Doar etapa N–S e măsurată;
E–V e restul ciclului, tăiat la 60 s prin ipoteză. Unde camera nu vede un val (trafic slab, o pauză a colectării), se pune ciclul obișnuit al orei, deci la trafic slab programul e
în cea mai mare parte presupus: `detalii["acoperire"]` spune ce parte din oră vine din valuri măsurate. Sub 80%, nu i se spune „semaforul real”.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from romana.common import CONFIG_DIR, DEMAND_DIR, OUTPUT_DIR, TRAJ_DIR
from romana.control.faze import ETAPA_SCURTA_S, SCURTA, info_v2, program_fix
from romana.vision import program_real as P
from romana.vision.od_counter import load_zones

GOL_VAL_S = 15            # un val nou începe după atâtea secunde fără vehicule
MIN_VAL = 8               # un val are cel puțin atâtea vehicule
TRANZITII_S = 15          # trei tranziții de 5 s
VERDE_MIN_S = 12
E_V_MAX_S = 60            # la trafic slab, valul de pe Magheru se termină mult înaintea verdelui; restul ciclului nu e E–V, ci tot N–S
ORIZONT_S = 4500


def evenimente_zi(zi: str) -> dict[str, np.ndarray]:
    """Momentele de intrare pe brațe, din jurnalul public al zilei; se calculează o dată, durează un minut."""
    cale = OUTPUT_DIR / "program_real" / f"ev_{zi}.npz"
    if cale.exists():
        return dict(np.load(cale))
    zone = load_zones(json.loads((CONFIG_DIR / "camera_v2.json").read_text(encoding="utf-8")))
    ev = P.evenimente(TRAJ_DIR / f"traiectorii_{zi}.jsonl.gz", zone)
    cale.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cale, **ev)
    return ev


def valuri(momente: np.ndarray, gol: float = GOL_VAL_S, minim: int = MIN_VAL) -> list[tuple[float, float, int]]:
    """Valurile de vehicule: (început, sfârșit, câte vehicule)."""
    if len(momente) == 0:
        return []
    st = np.r_[0, np.where(np.diff(momente) >= gol)[0] + 1]
    return [(float(momente[a]), float(momente[b - 1]), int(b - a)) for a, b in zip(st, np.r_[st[1:], len(momente)]) if b - a >= minim]


def cicluri(val: list[tuple[float, float, int]], orizont: float, t_med: float, g_med: float) -> list[tuple[float, float]]:
    """Din valuri, ciclurile (verde N–S, durată), de la primul val până la orizont. Un val lipsă se înlocuiește cu ciclul obișnuit; un val prea apropiat de cel
    dinainte se lipește de el, ca să nu rezulte o etapă E–V sub verdele minim."""
    out, k = [], 0
    t = val[0][0] if val else 0.0
    while t < orizont:
        while k < len(val) and val[k][0] < t + 1:
            k += 1
        urm = val[k][0] if k < len(val) else None
        cap = val[k - 1][1] if k > 0 and val[k - 1][0] >= t - 1 else None
        g = float(np.clip(cap - t, 25, 110)) if cap is not None else g_med
        while urm is not None and urm - t < g + TRANZITII_S + ETAPA_SCURTA_S + VERDE_MIN_S:      # val prea apropiat: rămâne în aceeași etapă N–S
            k += 1
            g = float(np.clip(val[k - 1][1] - t, 25, 110))
            urm = val[k][0] if k < len(val) else None
        if urm is None or urm - t > 1.6 * t_med:     # niciun val măsurat curând: ciclul obișnuit; se verifică după lipire, altfel o pauză a jurnalului devine un singur ciclu
            d = t_med
            g = min(g, d - TRANZITII_S - ETAPA_SCURTA_S - VERDE_MIN_S)
        else:
            d = urm - t
        g = max(g, d - TRANZITII_S - ETAPA_SCURTA_S - E_V_MAX_S)
        out.append((g, d))
        t += d
    return out


def acoperire(val: list[tuple[float, float, int]], lista: list[tuple[float, float]], sfarsit: float = 3600.0) -> float:
    """Ce parte din oră vine din valuri măsurate: ciclul începe la un val, următorul la alt val, iar verdele e chiar valul."""
    if not val:
        return 0.0
    st = np.array([v[0] for v in val])
    t, masurat = val[0][0], 0.0
    for g, d in lista:
        i, j = int(np.argmin(np.abs(st - t))), int(np.argmin(np.abs(st - (t + d))))
        if t < sfarsit and abs(st[i] - t) < 1 and abs(st[j] - (t + d)) < 1 and j > i and abs(val[j - 1][1] - t - g) < 1:
            masurat += min(t + d, sfarsit) - t
        t += d
    return masurat / sfarsit


def etape_inceput(prima: float, t_med: float, g_med: float) -> tuple[list[tuple], float]:
    """Până la primul val măsurat, cicluri obișnuite, ca el să înceapă la timp; se termină cu E–V și etapa scurtă, ca orice ciclu."""
    g = max(g_med, t_med - TRANZITII_S - ETAPA_SCURTA_S - E_V_MAX_S)
    n, rest = int(prima // t_med), prima % t_med
    etape: list[tuple] = []
    if rest >= 25:
        e = rest - 2 * TRANZITII_S / 3 - ETAPA_SCURTA_S
        if e > E_V_MAX_S + 30:
            etape.append((0, e - E_V_MAX_S - TRANZITII_S / 3))
            e = E_V_MAX_S
        etape += [(1, e), (SCURTA, ETAPA_SCURTA_S)]
        rest = 0
    etape += [(0, g), (1, t_med - g - TRANZITII_S - ETAPA_SCURTA_S), (SCURTA, ETAPA_SCURTA_S)] * n
    return etape, rest


def fereastra_scenariu(stem: str) -> tuple[str, pd.Timestamp, pd.Timestamp]:
    """Ziua și ora pe care le reproduce un scenariu `cor_zi_AAAA-LL-ZZ_tip`."""
    m = re.search(r"zi_(\d{4}-\d\d-\d\d)_([a-z]+)", stem)
    zi, tip = m.group(1), m.group(2)
    rez = json.loads((DEMAND_DIR / f"cor_zi_{zi}_rezumat.json").read_text(encoding="utf-8"))
    a, b = rez["ferestre"][tip]
    return zi, pd.Timestamp(a), pd.Timestamp(b)


def program_rejucat(stem: str) -> tuple[list[tuple[str, float]], dict]:
    """Programul semaforului pe scenariul dat: [(stare, durată)] și câteva cifre despre el."""
    info = info_v2()
    stari, pietoni = info["green_states"], info["pietoni"]
    zi, a, b = fereastra_scenariu(stem)
    zero = pd.Timestamp(a, tz="Europe/Bucharest").timestamp()
    m = evenimente_zi(zi)["magheru"]
    m = m[(m >= zero - 200) & (m < zero + ORIZONT_S)] - zero
    val = valuri(m)
    dur = np.diff([v[0] for v in val])
    t_med = float(np.median(dur)) if len(dur) else 138.0
    g_med = float(np.median([v[1] - v[0] for v in val])) if val else 72.0
    g_med = min(max(g_med, 25.0), t_med - TRANZITII_S - ETAPA_SCURTA_S - VERDE_MIN_S)
    val = [v for v in val if v[0] >= 0]
    prima = val[0][0] if val else 0.0
    lista = cicluri(val, ORIZONT_S, t_med, g_med)
    etape, rest = etape_inceput(prima, t_med, g_med)
    for g, d in lista:
        etape += [(0, g), (1, d - g - TRANZITII_S - ETAPA_SCURTA_S), (SCURTA, ETAPA_SCURTA_S)]
    if rest:                                            # o bucată prea scurtă pentru o etapă proprie lungește primul verde
        etape[0] = (etape[0][0], etape[0][1] + rest)
    faze = program_fix(stari, etape, pietoni)           # o singură listă: tranzițiile și degajarea ies la fel peste tot
    return faze, {"zi": zi, "de_la": str(a), "pana_la": str(b), "cicluri": len(lista), "ciclu_median_s": round(t_med, 1), "verde_median_s": round(g_med, 1), "valuri_masurate": len(val), "acoperire": round(acoperire(val, lista), 3)}


class SemaforRejucat:
    """Referința de pe un scenariu al zilei: semaforul pieței face ce a făcut semaforul real în acea oră, după cameră."""

    name = "semafor_rejucat"

    def reset(self, traci):
        stem = Path(str(traci.simulation.getOption("configuration-file"))).stem
        faze, self.detalii = program_rejucat(stem)
        traci.trafficlight.setProgramLogic("romana", traci.trafficlight.Logic("rejucat", 0, 0, [traci.trafficlight.Phase(d, s) for s, d in faze]))
        traci.trafficlight.setProgram("romana", "rejucat")

    def act(self, traci, t):
        pass
