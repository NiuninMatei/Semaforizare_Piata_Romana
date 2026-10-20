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


def green_phases_from_program(traci, tls_id: str) -> list[str]:
    logic = traci.trafficlight.getAllProgramLogics(tls_id)
    prog = next((lg for lg in logic if lg.programID == traci.trafficlight.getProgram(tls_id)), logic[0])
    out = []
    for p in prog.phases:
        s = p.state
        if "y" not in s and any(c in "Gg" for c in s) and s not in out:
            out.append(s)
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
        """Presiunea fiecărei faze (Varaiya 2013): Σ (coadă amonte − coadă aval) pe legăturile verzi."""
        links = self.t.trafficlight.getControlledLinks(self.id)
        q = {}

        def queue(ln):
            if ln not in q:
                q[ln] = self.t.lane.getLastStepHaltingNumber(ln)
            return q[ln]

        out = []
        for g in self.greens:
            p = 0.0
            for i, ch in enumerate(g):
                if ch in "Gg" and links[i]:
                    inc, outl, _ = links[i][0]
                    p += queue(inc) - queue(outl)
            out.append(p)
        return out


def observation(traci, ctrls, cap: dict) -> "np.ndarray":
    """Starea comună pentru antrenare, evaluare și geamănul digital (aceeași ordine a valorilor)."""
    import numpy as np

    parts = []
    for c in ctrls:
        oh = np.zeros(c.n)
        oh[c.current] = 1.0
        parts.append(oh)
        parts.append([1.0 if c.can_switch() else 0.0, min(1.0, c.green_time / c.max_green)])
        parts.append([min(1.0, traci.lane.getLastStepHaltingNumber(ln) / cap[ln]) for ln in c.in_lanes])
        parts.append([min(1.0, traci.lane.getLastStepVehicleNumber(ln) / cap[ln]) for ln in c.in_lanes])
        parts.append([min(1.0, w / 15.0) for w in c.ped_waiting()])
    return np.concatenate([np.asarray(p, dtype=np.float32) for p in parts])


def waiting_total(traci, ctrls) -> float:
    """Vehicule oprite pe benzile de intrare + pietoni care așteaptă la treceri (toți participanții)."""
    return float(sum(traci.lane.getLastStepHaltingNumber(ln) for c in ctrls for ln in c.in_lanes)
                 + sum(sum(c.ped_waiting()) for c in ctrls))
