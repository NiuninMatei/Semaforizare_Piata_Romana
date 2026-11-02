"""Semaforul real, rejucat din cameră (§ 6.5): etapele măsurate ciclu cu ciclu, în locul unui plan fix.

Semaforul real își schimbă durata de la un ciclu la altul, deci un plan fix îl aproximează doar. Aici, începutul și sfârșitul fiecărui val de vehicule de pe
Magheru, din jurnalul public al zilei, dau etapele: verde N–S cât a ținut valul, apoi E–V până la următorul val, minus tranzițiile și etapa scurtă. Unde camera nu vede
un val (trafic slab, o pauză a colectării), se pune ciclul obișnuit al orei. Pe un scenariu al zilei, e referința cea mai apropiată de ce s-a întâmplat acolo.
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
        if urm is None or urm - t > 1.6 * t_med:
            d = t_med                         # niciun val măsurat curând: ciclul obișnuit
            g = min(g, d - TRANZITII_S - ETAPA_SCURTA_S - VERDE_MIN_S)
        else:
            while urm - t < g + TRANZITII_S + ETAPA_SCURTA_S + VERDE_MIN_S:      # val prea apropiat: rămâne în aceeași etapă N–S
                k += 1
                if k >= len(val):
                    break
                cap2 = val[k - 1][1]
                g = float(np.clip(cap2 - t, 25, 110))
                urm = val[k][0]
            d = (urm - t) if k < len(val) else t_med
            if d < g + TRANZITII_S + ETAPA_SCURTA_S + VERDE_MIN_S:
                d = g + TRANZITII_S + ETAPA_SCURTA_S + VERDE_MIN_S
        g = max(g, d - TRANZITII_S - ETAPA_SCURTA_S - E_V_MAX_S)
        out.append((g, d))
        t += d
    return out


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
    faze: list[tuple[str, float]] = []
    if prima > 5:
        # până la primul val, etapa E–V, care se termină cu tranziția spre N–S
        faze += [(stari[1], max(prima - 5, 1)), ("y", 3), ("r", 2)]
    lista = cicluri(val, ORIZONT_S - prima, t_med, g_med)
    for g, d in lista:
        faze += program_fix(stari, [(0, g), (1, d - g - TRANZITII_S - ETAPA_SCURTA_S), (SCURTA, ETAPA_SCURTA_S)], pietoni)
    if faze and faze[1][0] == "y":                      # tranziția de la început, acum că se știe starea care urmează
        from romana.control.signals import all_red_between, yellow_between

        urm = faze[3][0]
        faze[1] = (yellow_between(stari[1], urm), 3)
        faze[2] = (all_red_between(stari[1], urm), 2)
    return faze, {"zi": zi, "de_la": str(a), "pana_la": str(b), "cicluri": len(lista), "ciclu_median_s": round(t_med, 1), "verde_median_s": round(g_med, 1), "valuri_masurate": len(val)}


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
