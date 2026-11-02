"""Fazele semaforului pieței pentru rețeaua încărcată în simulare: geamănul corectat are fișierul lui și programul pietonilor (§ 6.5).

Programul pietonilor vine din cameră. Pe Dacia est, pietonii pornesc la ≈20 s după vehiculele de pe axa Magheru–Catargiu; pe Magheru, abia după sfârșitul
etapei N–S. În ambele etape, pietonii primesc roșu cu câteva secunde înaintea vehiculelor, ca să termine traversarea până vine etapa următoare.
"""
from __future__ import annotations

import json

from romana.common import NET_DIR
from romana.control.signals import SignalController, all_red_between, romana_green_phases, yellow_between

MINIM_PIETONI_S = 7        # dintr-o etapă scurtă, pietonii primesc totuși măcar atât, ca să nu rămână niciodată fără verde
SCURTA = "scurta"          # a treia etapă, când ține mai puțin decât verdele minim: centrul se golește, fără pietoni; nu e o fază în lista agentului
ETAPA_SCURTA_S = 3         # din cameră: între sfârșitul etapei E–V și începutul etapei N–S trec ≈13 s, cu tot cu cele două tranziții
# după verdele maxim: N–S → E–V, E–V → N–S, orice altceva → N–S; nu faza cu numărul următor, care poate fi una „fără dozare” (§ 6.3)
URMATOAREA = {0: 1, 1: 0}


def info_v2() -> dict:
    return json.loads((NET_DIR / "network_info_v2.json").read_text(encoding="utf-8"))


def pe_v2(tr) -> bool:
    return str(tr.simulation.getOption("net-file")).endswith("_v2.net.xml")


def faze_romana(tr) -> tuple[list[str], list[str]]:
    if pe_v2(tr):
        info = info_v2()
        return info["green_states"], info["phase_names"]
    return romana_green_phases()


def fara_treceri(stare: str, treceri) -> str:
    """Aceeași stare, cu trecerile de pietoni pe roșu."""
    return "".join("r" if i in treceri else c for i, c in enumerate(stare))


def segmente_etapa(stare: str, verde: float, treceri, intarziere: float, degajare: float) -> list[tuple[str, float]]:
    """O etapă de `verde` secunde: vehiculele au verde tot timpul, pietonii doar în fereastra lor."""
    goala = fara_treceri(stare, treceri)
    if goala == stare:
        return [(stare, verde)]
    sfarsit = max(verde - degajare, 0)
    inceput = min(intarziere, max(sfarsit - MINIM_PIETONI_S, 0))
    return [(s, d) for s, d in ((goala, inceput), (stare, sfarsit - inceput), (goala, verde - sfarsit)) if d > 0]


def tranzitie(s: str, urm: str, interioare=()) -> tuple[str, str]:
    """Galbenul și roșul general dintre două stări. O linie de oprire de imediat după o trecere rămâne pe verde în galbenul celorlalte și trece pe galben în roșul general:
    cine a trecut de linia dinaintea trecerii trebuie să poată ieși de pe ea, nu să rămână oprit pe zebră toată etapa următoare."""
    g, r = yellow_between(s, urm), all_red_between(s, urm)
    for i in interioare:
        if s[i] in "Gg" and urm[i] not in "Gg":
            g, r = g[:i] + s[i] + g[i + 1:], r[:i] + "y" + r[i + 1:]
    return g, r


def program_fix(stari: list[str], etape: list[tuple[int, float]], pietoni: dict, galben: float = 3, rosu: float = 2) -> list[tuple[str, float]]:
    """Plan fix: [(faza, verde)] → [(stare, durată)], cu fereastra pietonilor și cu tranzițiile sigure acolo unde se schimbă legături de vehicule."""
    seg = [x for f, v in etape for x in ([(pietoni["stare_scurta"], v)] if f == SCURTA else segmente_etapa(stari[f], v, pietoni["treceri"], pietoni["intarziere_s"].get(str(f), 0), pietoni["degajare_s"]))]
    n = min(pietoni["treceri"])          # legăturile de vehicule stau înaintea trecerilor
    out = []
    for k, (s, d) in enumerate(seg):
        urm = seg[(k + 1) % len(seg)][0]
        out.append((s, d))
        if s[:n] != urm[:n]:
            g, r = tranzitie(s, urm, pietoni.get("linii_interioare", ()))
            out += [(g, galben), (r, rosu)]
    return out


def etape_plan(verde_s: list[float], pietoni: dict) -> list[tuple[int, float]]:
    """Planul „a/b/c”: verde N–S, verde E–V, a treia etapă. Sub verdele minim, a treia e etapa scurtă, fără pietoni; altfel, cea doar pentru pietoni."""
    a, b, c = verde_s
    return [(0, a), (1, b)] + ([(SCURTA if c < 10 else 2, c)] if c > 0 else [])


class SemaforCuPietoni(SignalController):
    """Tranzițiile sigure din `SignalController`, plus programul pietonilor: în etapa N–S pietonii pornesc după vehicule, iar înaintea unei schimbări au
    timp să termine traversarea, cu vehiculele încă pe verde; abia apoi urmează galbenul. Comanda se ia la fel, deci orice controler le respectă."""

    def __init__(self, traci, tls_id: str, greens: list[str], names: list[str] | None, pietoni: dict):
        super().__init__(traci, tls_id, greens, names)
        self.treceri = set(pietoni["treceri"])
        self.intarziere = {int(k): v for k, v in pietoni["intarziere_s"].items()}
        self.degajare = pietoni["degajare_s"]
        self.interioare = pietoni.get("linii_interioare", ())
        self.stare_scurta = pietoni["stare_scurta"]
        self.nume_scurta = pietoni["nume_scurta"]
        self.scurta = self.spre_scurta = False     # în etapa scurtă, respectiv spre ea; pentru agent, ea rămâne faza a treia
        self.via_scurta = False               # agentul pe două etape: de la E–V la N–S se trece mereu prin etapa scurtă, ca la semaforul real
        self.ramas_degajare = None            # secundele de degajare rămase, cât timp vehiculele mai au verde
        self.plecare = self.sosire = None     # stările dintre care se face tranziția
        self.afisata = None
        self._arata(self._inceput(0))

    def _arata(self, stare: str) -> None:
        self.afisata = stare
        self.t.trafficlight.setRedYellowGreenState(self.id, stare)

    def _inceput(self, faza: int, scurta: bool = False) -> str:
        if scurta:
            return self.stare_scurta
        return fara_treceri(self.greens[faza], self.treceri) if self.intarziere.get(faza, 0) > 0 else self.greens[faza]

    def can_switch(self) -> bool:
        if self.stage != "green" or self.ramas_degajare is not None:
            return False
        # și la o strategie care schimbă des, pietonii primesc verdele lor: fără asta, un N–S sub 24 s lasă trecerile de pe Dacia fără niciun verde
        return self.scurta or self.green_time >= max(self.min_green, self.intarziere.get(self.current, 0) + MINIM_PIETONI_S)

    def request(self, phase: int, scurta: bool = False) -> None:
        if self.stage != "green" or self.ramas_degajare is not None or (self.scurta and self.green_time < ETAPA_SCURTA_S):
            return
        if self.via_scurta:
            if self.scurta:
                phase = 0
            elif self.current == 1 and phase == 0:
                phase, scurta = 2, True
        if phase == self.current and self.green_time >= self.max_green:
            phase = URMATOAREA.get(self.current, 0)
            if self.via_scurta and self.current == 1:
                phase, scurta = 2, True
        if (phase != self.current or (self.scurta and not scurta)) and self.can_switch():
            self.target = phase
            self.spre_scurta = scurta and phase == 2
            self.sosire = self._inceput(phase, self.spre_scurta)
            if any(self.afisata[i] in "Gg" and self.sosire[i] not in "Gg" for i in self.treceri):
                self.ramas_degajare = self.degajare
                self._arata(fara_treceri(self.afisata, {i for i in self.treceri if self.sosire[i] not in "Gg"}))
            else:
                self._galben()

    def faza_afisata(self) -> int:
        """Pentru dispecerat: etapa scurtă are numele ei, după cele cinci faze."""
        return len(self.greens) if self.scurta else self.current

    def pietoni_verde(self) -> bool:
        return any(self.afisata[i] in "Gg" for i in self.treceri)

    def _galben(self) -> None:
        self.ramas_degajare = None
        self.stage, self.stage_time = "yellow", 0
        self.plecare = self.afisata
        self._arata(tranzitie(self.plecare, self.sosire, self.interioare)[0])

    def tick(self) -> None:
        self.stage_time += 1
        if self.stage == "green":
            self.green_time += 1
            if self.ramas_degajare is not None:
                self.ramas_degajare -= 1
                if self.ramas_degajare <= 0:
                    self._galben()
            elif self.scurta and self.via_scurta and self.green_time >= ETAPA_SCURTA_S:
                self.request(0)
            elif not self.scurta and self.green_time == self.intarziere.get(self.current, -1):
                self._arata(self.greens[self.current])
        elif self.stage == "yellow" and self.stage_time >= self.yellow:
            self.stage, self.stage_time = "red", 0
            self._arata(tranzitie(self.plecare, self.sosire, self.interioare)[1])
            if self.all_red == 0:
                self.tick()
        elif self.stage == "red" and self.stage_time >= self.all_red:
            self.current = self.target
            self.scurta = self.spre_scurta
            self.stage, self.stage_time, self.green_time = "green", 0, 0
            self.switches += 1
            self._arata(self.sosire)


def controler(tr, tid: str, greens: list[str], names: list[str] | None) -> SignalController:
    """Controlerul unui semafor: pe geamănul corectat, cel al pieței respectă și programul pietonilor."""
    if tid == "romana" and pe_v2(tr):
        return SemaforCuPietoni(tr, tid, greens, names, info_v2()["pietoni"])
    return SignalController(tr, tid, greens, names)
