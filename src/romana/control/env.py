"""Mediu Gymnasium pentru controlul semafoarelor Pieței Romane (și, opțional, al vecinilor).

Stare (pentru fiecare semafor controlat):
  * faza verde curentă (one-hot) + indicator „verde minim îndeplinit”;
  * pentru fiecare bandă de intrare: coada (vehicule oprite) și densitatea, normalizate
    la capacitatea de stocare a benzii (lungime / 7,5 m);
  * pentru fiecare trecere de pietoni controlată: pietonii care așteaptă (normalizat la 15).
Acțiune: indicele fazei verzi dorite pentru fiecare semafor (MultiDiscrete). La Piața Romană,
  implicit doar fazele planului real (N–S, E–V, pietoni): agentul schimbă ordinea și durata
  lor, adică exact ce se poate programa pe automatul existent.
  Tranzițiile sigure (galben, roșu general, verde minim 10 s, maxim 90 s) sunt impuse de
  SignalController – agentul nu poate genera stări periculoase.
Recompensă: −(vehicule oprite pe benzile de intrare + pietoni care așteaptă la treceri)/100,
  calculată la fiecare pas de decizie (5 s) – echivalentă cu minimizarea întârzierii totale.
  Se adaugă o penalizare mică pentru vehiculele care nu pot intra în rețea (blocaj la margine).

Episoadele aleg aleator unul dintre scenariile de antrenare (date reale + referință), astfel
încât politica să nu se specializeze pe un singur profil de trafic.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import gymnasium as gym
import numpy as np

from romana.common import NET_DIR, sumo_home
from romana.control.signals import (SignalController, action_maps, green_phases_from_program, observation,
                                    romana_green_phases, waiting_total)

def _import_libsumo():
    """libsumo (mult mai rapid pentru antrenare). Pe Windows, PYTHONPATH-ul setat de instalatorul
    SUMO pune `SUMO/tools` înaintea pachetelor pip, iar libsumo din instalare nu găsește toate
    DLL-urile; în acest caz se încarcă pachetul pip `libsumo`, care le conține."""
    try:
        import libsumo
        return libsumo
    except ImportError:
        for m in [m for m in sys.modules if m == "libsumo" or m.startswith("libsumo.")]:
            del sys.modules[m]
        saved = sys.path[:]
        sys.path = [p for p in saved if "site-packages" in p] + [p for p in saved if "site-packages" not in p]
        try:
            import libsumo
            return libsumo
        finally:
            sys.path = saved


sumo_home()
try:
    if os.environ.get("ROMANA_USE_TRACI"):
        raise ImportError
    traci = _import_libsumo()
    LIBSUMO = True
except ImportError:
    import traci
    LIBSUMO = False


def start_sumo(sumocfg: Path, seed: int, gui: bool = False, extra: list[str] | None = None, label=None):
    from romana.common import sumo_binary

    cmd = [sumo_binary("sumo-gui" if gui else "sumo"), "-c", str(sumocfg), "--seed", str(seed),
           "--no-step-log", "true", "--no-warnings", "true", "--duration-log.disable", "true",
           "--time-to-teleport", "300", "--additional-files",
           f"{sumocfg.parent / '../demand/vtypes.add.xml'},{NET_DIR / 'tls_actuated.add.xml'}"]
    if gui:
        cmd += ["--start", "--delay", "50"]
    cmd += extra or []
    if LIBSUMO or label is None:
        traci.start(cmd)
    else:
        traci.start(cmd, label=label)
    # tls_actuated.add.xml adaugă programe 'actuated' alternative; pornim toate semafoarele pe
    # programul implicit '0' din rețea (vecinii: actuated, ca sistemul adaptiv BTMS;
    # Piața Romană: plan fix) – controlerul ales îl înlocuiește apoi pe cel al pieței.
    for tid in traci.trafficlight.getIDList():
        if "0" in [lg.programID for lg in traci.trafficlight.getAllProgramLogics(tid)]:
            traci.trafficlight.setProgram(tid, "0")
    return traci


class RomanaEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, scenarios: list[Path], controlled: list[str] = ("romana",), delta_t: int = 5,
                 episode_s: int = 3600, warmup_s: int = 60, seed: int = 0, gui: bool = False,
                 romana_phases: list[int] | None = None):
        super().__init__()
        self.scenarios = [Path(s) for s in scenarios]
        self.controlled = list(controlled)
        self.romana_phases = romana_phases   # fazele dintre care alege agentul (None = toate)
        self.delta_t, self.episode_s, self.warmup_s = delta_t, episode_s, warmup_s
        self.gui = gui
        self.rng = random.Random(seed)
        self._running = False
        # o pornire „uscată” pentru a afla dimensiunile spațiilor
        self._start(self.scenarios[0], seed)
        self.action_space = gym.spaces.MultiDiscrete([len(m) for m in self.action_maps])
        n_obs = len(self._obs())
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=(n_obs,), dtype=np.float32)

    # ------------------------------------------------------------------ intern
    def _start(self, cfg: Path, seed: int) -> None:
        if self._running:
            traci.close()
        start_sumo(cfg, seed, gui=self.gui)
        self._running = True
        self.ctrls = []
        for tid in self.controlled:
            if tid == "romana":
                greens, names = romana_green_phases()
            else:
                traci.trafficlight.setProgram(tid, "0")
                greens, names = green_phases_from_program(traci, tid), None
            self.ctrls.append(SignalController(traci, tid, greens, names))
        self.action_maps = action_maps(self.controlled, self.ctrls, self.romana_phases)
        self.cap = {ln: max(1.0, traci.lane.getLength(ln) / 7.5) for c in self.ctrls for ln in c.in_lanes}
        self.t = 0

    def _obs(self) -> np.ndarray:
        return observation(traci, self.ctrls, self.cap)

    def _halting(self) -> float:
        return waiting_total(traci, self.ctrls)

    def _sim(self, seconds: int) -> None:
        for _ in range(seconds):
            traci.simulationStep()
            for c in self.ctrls:
                c.tick()
            self.t += 1

    # ------------------------------------------------------------------ API gym
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        cfg = (options or {}).get("scenario") or self.rng.choice(self.scenarios)
        self._start(Path(cfg), seed if seed is not None else self.rng.randint(0, 10_000))
        self._sim(self.warmup_s)
        return self._obs(), {"scenariu": str(cfg)}

    def step(self, action):
        for c, m, a in zip(self.ctrls, self.action_maps, np.atleast_1d(action)):
            c.request(m[int(a)])
        self._sim(self.delta_t)
        halting = self._halting()
        backlog = traci.simulation.getMinExpectedNumber() - traci.vehicle.getIDCount()
        reward = -halting / 100.0 - 0.002 * max(0, backlog)
        truncated = self.t >= self.episode_s
        info = {"oprite": halting, "timp": self.t}
        return self._obs(), float(reward), False, truncated, info

    def close(self):
        if self._running:
            traci.close()
            self._running = False
