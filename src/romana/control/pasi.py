"""Pașii semaforului, pentru dispecerat: unde a ajuns o schimbare de fază și în câte secunde ajunge verdele cerut.

Funcțiile doar citesc controlerul (`SignalController`, din signals.py, sau `SemaforCuPietoni`, din faze.py): nu cheamă
TraCI și nu schimbă nimic. Secundele sunt secunde simulate, numărate ca `timp_sim` din starea geamănului. Starea se
scrie după pasul de 1 s, deci `timp_sim` e secunda următoarei decizii, iar verdele de acum (`green_time`) e cel pe care îl
va vedea ea. Comenzile manuale se iau doar la secundele multiple de `CADENTA_S`, ca în live_twin.

O schimbare pornită nu se mai oprește: întâi se ajunge la ținta ei, apoi, după verdele minim al țintei, se poate pleca
spre faza cerută. Pe geamănul corectat, înaintea galbenului vine degajarea pietonilor (6 s), când se închide o trecere
verde; atunci vehiculele au încă verde, deci etapa controlerului rămâne „green”.
"""
from __future__ import annotations

from romana.control.faze import ETAPA_SCURTA_S, MINIM_PIETONI_S

CADENTA_S = 5      # live_twin: agentul, Max-Pressure și comanda manuală decid la fiecare 5 s simulate


def in_degajare(ctrl) -> bool:
    return getattr(ctrl, "ramas_degajare", None) is not None


def pe_verde(ctrl) -> bool:
    """Verde fără nicio schimbare în curs."""
    return ctrl.stage == "green" and not in_degajare(ctrl)


def pas(ctrl) -> str:
    if ctrl.stage == "green":
        return "degajare" if in_degajare(ctrl) else "verde"
    return "galben" if ctrl.stage == "yellow" else "rosu"


def pas_ramas_s(ctrl) -> int | None:
    """Secundele rămase din pasul de acum al schimbării; pe verde, niciuna (verdele ține cât îl cere comanda)."""
    if ctrl.stage == "green":
        return ctrl.ramas_degajare if in_degajare(ctrl) else None
    if ctrl.stage == "yellow":
        return ctrl.yellow - ctrl.stage_time
    return ctrl.all_red - ctrl.stage_time


def pana_la_tinta_s(ctrl) -> int:
    """Secundele până la verdele țintei schimbării în curs: 0 pe verde."""
    if pe_verde(ctrl):
        return 0
    if ctrl.stage == "green":
        return ctrl.ramas_degajare + ctrl.yellow + ctrl.all_red
    return pas_ramas_s(ctrl) + (ctrl.all_red if ctrl.stage == "yellow" else 0)


def faza_tinta(ctrl) -> int:
    """Faza spre care merge semaforul, cu numerotarea dispeceratului (etapa scurtă vine după cele cinci faze); pe verde,
    faza de acum."""
    n = len(ctrl.greens)
    if pe_verde(ctrl):
        return n if getattr(ctrl, "scurta", False) else ctrl.current
    return n if getattr(ctrl, "spre_scurta", False) else ctrl.target


def verde_min_s(ctrl, faza: int, scurta: bool = False) -> int:
    """Verdele minim după care controlerul acceptă o schimbare din faza `faza` (pe N–S, pietonii primesc întâi verdele lor)."""
    if not hasattr(ctrl, "intarziere"):
        return ctrl.min_green
    if scurta:
        return ETAPA_SCURTA_S
    return max(ctrl.min_green, ctrl.intarziere.get(faza, 0) + MINIM_PIETONI_S)


def tranzitie_s(ctrl, din: int, scurta: bool, spre: int) -> int:
    """Secundele de la acceptarea unei schimbări din faza `din` (sau din etapa scurtă) până la verdele fazei `spre`.

    La acceptare, faza `din` are deja verdele întreg, cu pietonii ei: verdele minim de pe N–S trece de întârzierea lor."""
    s = ctrl.yellow + ctrl.all_red
    if hasattr(ctrl, "treceri"):
        acum = ctrl.stare_scurta if scurta else ctrl.greens[din]
        sosire = ctrl._inceput(spre)
        if any(acum[i] in "Gg" and sosire[i] not in "Gg" for i in ctrl.treceri):
            s += ctrl.degajare
    return s


def pana_la_faza_s(ctrl, timp_sim: int, faza: int, cadenta_s: int = CADENTA_S) -> int:
    """Secundele simulate până la verdele fazei `faza`, dacă de acum încolo comanda cere mereu faza asta, la fiecare
    `cadenta_s` secunde (ca o comandă manuală)."""
    if pe_verde(ctrl):
        din, scurta, verde, start = ctrl.current, getattr(ctrl, "scurta", False), ctrl.green_time, timp_sim
        if din == faza and not scurta:
            return 0
    else:
        rest = pana_la_tinta_s(ctrl)
        din, scurta = ctrl.target, getattr(ctrl, "spre_scurta", False)
        if din == faza and not scurta:
            return rest
        verde, start = 0, timp_sim + rest
    gata = start + max(0, verde_min_s(ctrl, din, scurta) - verde)
    acceptare = -(-gata // cadenta_s) * cadenta_s       # prima decizie de după verdele minim
    return acceptare - timp_sim + tranzitie_s(ctrl, din, scurta, faza)


def pasi_semafor(ctrl, timp_sim: int, cadenta_s: int = CADENTA_S) -> dict:
    """Câmpurile pentru starea geamănului: pasul schimbării, ținta ei și, pentru fiecare fază, în cât timp ar ajunge verdele."""
    tinta = faza_tinta(ctrl)
    din = ctrl.current if pe_verde(ctrl) else ctrl.target
    return {
        "pas": pas(ctrl),
        "pas_ramas_s": pas_ramas_s(ctrl),
        "faza_tinta": tinta,
        "pana_la_tinta_s": pana_la_tinta_s(ctrl),
        "verde_min_s": verde_min_s(ctrl, din, tinta == len(ctrl.greens)),
        "verde_max_s": ctrl.max_green,
        "cadenta_s": cadenta_s,
        "citire_peste_s": (-timp_sim) % cadenta_s,
        "pana_la_faza_s": [pana_la_faza_s(ctrl, timp_sim, f, cadenta_s) for f in range(ctrl.n)],
        "durate_s": {"galben": ctrl.yellow, "rosu": ctrl.all_red, "degajare": getattr(ctrl, "degajare", 0)},
    }
