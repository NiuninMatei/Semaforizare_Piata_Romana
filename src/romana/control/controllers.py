"""Strategii de control pentru semaforul Piața Romană (folosite la evaluare și în geamănul digital).

  * FixedReference – planul fix de referință al rețelei (fazele N–S / E–V / pietoni, ciclu ≈ 91 s);
  * FixedWebster  – plan fix cu ciclul optim Webster (1958) calculat din debitele observate;
  * Actuated      – programul „actuated” al SUMO (prelungirea verdelui pe goluri între vehicule);
  * MaxPressure   – controlul de presiune maximă (Varaiya, 2013), aceleași 6 faze ca agentul;
  * RLPolicy      – politica PPO antrenată (Stable-Baselines3).
Toate primesc aceeași interfață: reset(traci) la pornire, act(traci, t) la fiecare pas de 5 s.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from romana.common import NET_DIR, load_json
from romana.control.signals import SignalController, all_red_between, romana_green_phases, yellow_between

SAT_FLOW = 1800  # veh/h/bandă verde (valoare uzuală HCM)


def fixed_phase_indices() -> list[int]:
    """Fazele planului fix de referință (cele cu durata_fixa > 0 în config/network.json)."""
    return [i for i, p in enumerate(load_json("network.json")["romana_faze"]) if p["durata_fixa"] > 0]


def webster_plan(od_json: Path, net_file: Path = NET_DIR / "romana.net.xml",
                 lost_per_phase: float = 7.0) -> dict:
    """Ciclul optim Webster: C0 = (1.5 L + 5) / (1 − Y); verdele fazelor de vehicule ∝ y_i.

    Fluxul critic al unei faze = cel mai încărcat braț de intrare cu verde în faza respectivă
    (grupurile `intrare_<braț>`), raportat la debitul de saturație al benzilor de autoturisme
    (benzile dedicate STB nu se numără). Faza de pietoni își păstrează durata din planul fix
    (timp de traversare) și intră integral în timpul pierdut pentru vehicule."""
    import sumolib

    cfg = load_json("network.json")
    arms = load_json("demand.json")["brate"]
    net = sumolib.net.readNet(str(net_file))
    lanes = {a: sum(ln.allows("passenger") for ln in net.getEdge(v["intrare"]).getLanes())
             for a, v in arms.items() if v["intrare"]}
    data = json.loads(Path(od_json).read_text(encoding="utf-8"))["intervale"]
    flow = {a: 0.0 for a in lanes}
    for r in data:
        for i, o in enumerate(r["origini"]):
            flow[o] = max(flow[o], sum(r["od_veh_h"][i]))      # intervalul cel mai încărcat
    phases = [cfg["romana_faze"][i] for i in fixed_phase_indices()]
    crit = [[g[len("intrare_"):] for g in p["verde"] if g.startswith("intrare_")] for p in phases]
    veh = [k for k, c in enumerate(crit) if c]
    y = {k: max(flow[a] / (SAT_FLOW * lanes[a]) for a in crit[k]) for k in veh}
    Y = sum(y.values())
    ped_time = sum(phases[k]["durata_fixa"] for k in range(len(phases)) if k not in veh)
    L = lost_per_phase * len(phases) + ped_time
    C = (1.5 * L + 5) / max(0.05, 1 - Y) if Y < 0.95 else 150.0
    C = float(np.clip(C, 60, 150))
    greens = [max(10.0, (C - L) * y[k] / Y) if k in y else float(phases[k]["durata_fixa"])
              for k in range(len(phases))]
    return {"ciclu_s": round(C, 1), "Y": round(Y, 3), "verde_s": [round(g, 1) for g in greens],
            "debite_veh_h": flow, "benzi": lanes}


class FixedReference:
    """Planul fix de referință din rețea (programul '0': duratele `durata_fixa` din config/network.json)."""

    name = "fix_referinta"

    def reset(self, traci):
        traci.trafficlight.setProgram("romana", "0")

    def act(self, traci, t):
        pass


class FixedWebster:
    name = "fix_webster"

    def __init__(self, od_json: Path):
        self.plan = webster_plan(od_json)

    def reset(self, traci):
        greens, _ = romana_green_phases()
        idx = fixed_phase_indices()
        phases = []
        for k, i in enumerate(idx):
            g, nxt = greens[i], greens[idx[(k + 1) % len(idx)]]
            phases += [traci.trafficlight.Phase(self.plan["verde_s"][k], g),
                       traci.trafficlight.Phase(3, yellow_between(g, nxt)),
                       traci.trafficlight.Phase(2, all_red_between(g, nxt))]
        traci.trafficlight.setProgramLogic("romana", traci.trafficlight.Logic("webster", 0, 0, phases))
        traci.trafficlight.setProgram("romana", "webster")

    def act(self, traci, t):
        pass


class Actuated:
    name = "actuated"

    def reset(self, traci):
        traci.trafficlight.setProgram("romana", "actuated")

    def act(self, traci, t):
        pass


class MaxPressure:
    name = "max_pressure"

    def reset(self, traci):
        greens, names = romana_green_phases()
        self.ctrl = SignalController(traci, "romana", greens, names)

    def act(self, traci, t):
        if self.ctrl.can_switch():
            self.ctrl.request(int(np.argmax(self.ctrl.phase_pressure())))

    def tick(self):
        self.ctrl.tick()


class RLPolicy:
    """Rulează politica PPO pe un mediu deja pornit (aceeași observație ca la antrenare)."""

    name = "rl_ppo"

    def __init__(self, model_path: Path, controlled=("romana",)):
        model_path = Path(model_path)
        npz = model_path.with_suffix(".npz")
        if npz.exists():               # inferență fără PyTorch (vezi policy_numpy.py)
            from romana.control.policy_numpy import NumpyPolicy

            self.np_policy, self.model = NumpyPolicy(npz), None
        else:
            from stable_baselines3 import PPO

            self.np_policy, self.model = None, PPO.load(str(model_path), device="cpu")
        self.controlled = list(controlled)

    def reset(self, traci):
        from romana.control.signals import green_phases_from_program

        self.ctrls = []
        for tid in self.controlled:
            if tid == "romana":
                g, n = romana_green_phases()
            else:
                traci.trafficlight.setProgram(tid, "0")
                g, n = green_phases_from_program(traci, tid), None
            self.ctrls.append(SignalController(traci, tid, g, n))
        self.cap = {ln: max(1.0, traci.lane.getLength(ln) / 7.5) for c in self.ctrls for ln in c.in_lanes}
        self.traci = traci

    def observe(self):
        from romana.control.signals import observation

        return observation(self.traci, self.ctrls, self.cap)

    def act(self, traci, t):
        if self.np_policy is not None:
            a = self.np_policy.predict(self.observe())
        else:
            a, _ = self.model.predict(self.observe(), deterministic=True)
        for c, ai in zip(self.ctrls, np.atleast_1d(a)):
            c.request(int(ai))

    def tick(self):
        for c in self.ctrls:
            c.tick()
