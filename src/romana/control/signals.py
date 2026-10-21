"""Controlul sigur al unui semafor prin TraCI: faze verzi, galben, roșu general, verde minim/maxim.

Orice controler (agent RL, Max-Pressure, operator uman din dashboard) cere doar
„faza verde următoare”; tranzițiile sigure (galben 3 s + roșu general) și
constrângerile de verde minim / maxim sunt impuse aici, nu de algoritm.
"""
from __future__ import annotations

import json

from romana.common import NET_DIR


def yellow_between(a: str, b: str) -> str:
    return "".join("y" if (x in "Gg" and y == "r") else x for x, y in zip(a, b))


def all_red_between(a: str, b: str) -> str:
    """Roșu pe legăturile care se schimbă; legăturile verzi în ambele faze rămân verzi."""
    return "".join(x if (x in "Gg" and y in "Gg") else "r" for x, y in zip(a, b))


def green_phases_from_program(traci, tls_id: str, min_dur: float = 10.0) -> list[str]:
    """Fazele verzi principale ale unui program existent (vecinii pieței).

    Se păstrează doar fazele cu durată reală (≥ `min_dur` s): programele generate de netconvert conțin
    și variante scurte de 5 s (degajarea trecerilor de pietoni, faze doar pentru pietoni), care, oferite
    agentului ca acțiuni separate, încurcau învățarea și puteau lăsa trecerile fără verde."""
    logic = traci.trafficlight.getAllProgramLogics(tls_id)
    prog = next((lg for lg in logic if lg.programID == traci.trafficlight.getProgram(tls_id)), logic[0])
    greens = [p for p in prog.phases if "y" not in p.state and any(c in "Gg" for c in p.state)]
    out = []
    for p in greens:
        if p.duration >= min_dur and p.state not in out:
            out.append(p.state)
    # siguranță: o fază scurtă rămâne dacă este singura care dă verde unei legături (ex. o trecere)
    for p in greens:
        served = {i for s in out for i, c in enumerate(s) if c in "Gg"}
        if any(c in "Gg" and i not in served for i, c in enumerate(p.state)) and p.state not in out:
            out.append(p.state)
    return out


def romana_green_phases() -> tuple[list[str], list[str]]:
    info = json.loads((NET_DIR / "network_info.json").read_text(encoding="utf-8"))
    return info["green_states"], info["phase_names"]


class SignalController:
    def __init__(self, traci, tls_id: str, greens: list[str], names: list[str] | None = None,
                 yellow: int = 3, all_red: int = 2, min_green: int = 10, max_green: int = 90):
        self.t = traci
        self.id = tls_id
        self.greens = greens
        self.names = names or [f"faza {i}" for i in range(len(greens))]
        self.yellow, self.all_red = yellow, all_red
        self.min_green, self.max_green = min_green, max_green
        self.current = 0
        self.target = 0
        self.stage = "green"      # green | yellow | red
        self.stage_time = 0
        self.green_time = 0
        self.switches = 0
        self.t.trafficlight.setRedYellowGreenState(self.id, self.greens[0])
        lanes = []
        for ln in self.t.trafficlight.getControlledLanes(self.id):
            if ln not in lanes:
                lanes.append(ln)
        # benzile de vehicule vs. zonele de așteptare ale pietonilor (walkingarea ':nod_wN')
        self.in_lanes = [ln for ln in lanes if not ln.startswith(":")]
        self.ped_areas = sorted({ln.rsplit("_", 1)[0] for ln in lanes if ln.startswith(":")})
        out = []
        for links in self.t.trafficlight.getControlledLinks(self.id):
            for lk in links:
                if lk and lk[1] not in out:
                    out.append(lk[1])
        self.out_lanes = out

    @property
    def n(self) -> int:
        return len(self.greens)

    def can_switch(self) -> bool:
        return self.stage == "green" and self.green_time >= self.min_green

    def request(self, phase: int) -> None:
        """Cere faza verde `phase`; ignorată dacă nu e permisă încă."""
        if self.stage != "green":
            return
        if phase == self.current and self.green_time >= self.max_green:
            phase = (self.current + 1) % self.n   # verde maxim atins → se trece mai departe
        if phase != self.current and self.green_time >= self.min_green:
            self.target = phase
            self.stage, self.stage_time = "yellow", 0
            self.t.trafficlight.setRedYellowGreenState(
                self.id, yellow_between(self.greens[self.current], self.greens[phase]))

    def tick(self) -> None:
        """De apelat după fiecare pas de simulare de 1 s."""
        self.stage_time += 1
        if self.stage == "green":
            self.green_time += 1
        elif self.stage == "yellow" and self.stage_time >= self.yellow:
            self.stage, self.stage_time = "red", 0
            self.t.trafficlight.setRedYellowGreenState(
                self.id, all_red_between(self.greens[self.current], self.greens[self.target]))
            if self.all_red == 0:
                self.tick()
        elif self.stage == "red" and self.stage_time >= self.all_red:
            self.current = self.target
            self.stage, self.stage_time, self.green_time = "green", 0, 0
            self.switches += 1
            self.t.trafficlight.setRedYellowGreenState(self.id, self.greens[self.current])

    # ------------------------------------------------------------ măsurători
    def ped_waiting(self) -> list[int]:
        """Pietoni care așteaptă la fiecare trecere controlată (viteză < 0,1 m/s pe zona de așteptare)."""
        out = []
        for e in self.ped_areas:
            out.append(sum(1 for p in self.t.edge.getLastStepPersonIDs(e) if self.t.person.getSpeed(p) < 0.1))
        return out

    def lane_queues(self) -> list[int]:
        return [self.t.lane.getLastStepHaltingNumber(ln) for ln in self.in_lanes]

    def phase_pressure(self) -> list[float]:
        """Presiunea fiecărei faze (Varaiya 2013): Σ (coadă amonte − coadă aval) pe legăturile verzi.

        Pentru trecerile de pietoni (legătură zonă de așteptare → trecere), „coada” amonte este
        numărul de pietoni care așteaptă pe zona de așteptare (aceeași pondere ca un vehicul,
        ca în recompensa agentului RL) – altfel faza de pietoni nu ar fi aleasă niciodată."""
        links = self.t.trafficlight.getControlledLinks(self.id)
        q, wp = {}, {}

        def queue(ln):
            if ln not in q:
                q[ln] = 0 if ln.startswith(":") else self.t.lane.getLastStepHaltingNumber(ln)
            return q[ln]

        def ped_queue(ln):
            e = ln.rsplit("_", 1)[0]
            if e not in wp:
                wp[e] = sum(1 for p in self.t.edge.getLastStepPersonIDs(e) if self.t.person.getSpeed(p) < 0.1)
            return wp[e]

        out = []
        for g in self.greens:
            p = 0.0
            seen_areas = set()
            for i, ch in enumerate(g):
                if ch in "Gg" and links[i]:
                    inc, outl, _ = links[i][0]
                    if inc.startswith(":"):          # trecere de pietoni
                        area = inc.rsplit("_", 1)[0]
                        if area not in seen_areas:   # o zonă de așteptare se numără o singură dată pe fază
                            seen_areas.add(area)
                            p += ped_queue(inc)
                    else:
                        p += queue(inc) - queue(outl)
            out.append(p)
        return out


def action_maps(controlled: list[str], ctrls: list, romana_phases: list[int] | None) -> list[list[int]]:
    """Acțiunea agentului → indicele fazei verzi, pentru fiecare controler (None = toate fazele)."""
    return [list(romana_phases) if (tid == "romana" and romana_phases is not None) else list(range(c.n))
            for tid, c in zip(controlled, ctrls)]


def upstream_groups(traci, ctrl, reach_m: float = 250.0) -> list[tuple[list[str], float]]:
    """Pentru fiecare muchie de intrare a controlerului: benzile din amonte pe cel mult `reach_m` metri
    (muchiile care o alimentează, fără cele interne) și capacitatea lor de stocare (vehicule)."""
    groups = []
    for edge in dict.fromkeys(ln.rsplit("_", 1)[0] for ln in ctrl.in_lanes):
        lanes, frontier, dist, seen = [], [edge], 0.0, {edge}
        while frontier and dist < reach_m:
            nxt = []
            for e in frontier:
                inc = [x for x in _incoming_edges(traci, e) if x not in seen and not x.startswith(":")]
                for p in inc:
                    seen.add(p)
                    nxt.append(p)
                    lanes += [f"{p}_{i}" for i in range(traci.edge.getLaneNumber(p))]
            dist += max((traci.lane.getLength(f"{e}_0") for e in nxt), default=reach_m)
            frontier = nxt
        cap = max(1.0, sum(traci.lane.getLength(ln) for ln in lanes) / 7.5)
        groups.append((lanes, cap))
    return groups


_INCOMING: dict = {}


def _incoming_edges(traci, edge: str) -> list[str]:
    """Muchiile (non-interne) care alimentează `edge` – index construit o singură dată din conexiuni."""
    if not _INCOMING:
        for e in traci.edge.getIDList():
            if e.startswith(":"):
                continue
            for i in range(traci.edge.getLaneNumber(e)):
                for link in traci.lane.getLinks(f"{e}_{i}"):
                    _INCOMING.setdefault(link[0].rsplit("_", 1)[0], set()).add(e)
    return sorted(_INCOMING.get(edge, ()))


def observation(traci, ctrls, cap: dict, upstream: list | None = None) -> "np.ndarray":
    """Starea comună pentru antrenare, evaluare și geamănul digital (aceeași ordine a valorilor).

    `upstream` (opțional, câte o listă de grupuri pentru fiecare controler, din `upstream_groups`) adaugă
    coada din amonte de fiecare intrare (până la ~250 m) și, la final, vehiculele care nu pot intra în
    rețea – agentul vede astfel și cozile care depășesc banda de la linia de oprire."""
    import numpy as np

    parts = []
    for k, c in enumerate(ctrls):
        oh = np.zeros(c.n)
        oh[c.current] = 1.0
        parts.append(oh)
        parts.append([1.0 if c.can_switch() else 0.0, min(1.0, c.green_time / c.max_green)])
        parts.append([min(1.0, traci.lane.getLastStepHaltingNumber(ln) / cap[ln]) for ln in c.in_lanes])
        parts.append([min(1.0, traci.lane.getLastStepVehicleNumber(ln) / cap[ln]) for ln in c.in_lanes])
        parts.append([min(1.0, w / 15.0) for w in c.ped_waiting()])
        if upstream is not None:
            parts.append([min(1.0, sum(traci.lane.getLastStepHaltingNumber(ln) for ln in lanes) / gcap)
                          for lanes, gcap in upstream[k]])
    if upstream is not None:
        parts.append([min(1.0, len(traci.simulation.getPendingVehicles()) / 200.0)])
    return np.concatenate([np.asarray(p, dtype=np.float32) for p in parts])


def upstream_halting(traci, upstream) -> float:
    """Vehiculele oprite pe benzile din amonte de intrări (fiecare bandă numărată o singură dată)."""
    lanes = {ln for groups in upstream for lanes, _ in groups for ln in lanes}
    return float(sum(traci.lane.getLastStepHaltingNumber(ln) for ln in lanes))


def waiting_total(traci, ctrls) -> float:
    """Vehicule oprite pe benzile de intrare + pietoni care așteaptă la treceri (toți participanții)."""
    return float(sum(traci.lane.getLastStepHaltingNumber(ln) for c in ctrls for ln in c.in_lanes)
                 + sum(sum(c.ped_waiting()) for c in ctrls))
