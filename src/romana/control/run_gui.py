"""Rulează un scenariu calibrat în SUMO-GUI cu strategia aleasă la semaforul Pieței Romane.

Exemple:
  python -m romana.control.run_gui                                   # agent AI, scenariul de referință
  python -m romana.control.run_gui --strategie fix_webster
  python -m romana.control.run_gui --scenariu sumo/scenarios/dimineata_2026-10-21.sumocfg
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from romana.common import DEMAND_DIR, MODELS_DIR, ROOT


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenariu", default=str(ROOT / "sumo/scenarios/referinta_varf.sumocfg"))
    ap.add_argument("--strategie", default="rl_ppo", choices=["rl_ppo", "rl_ppo_coridor", "fix_webster", "actuated", "max_pressure"])
    args = ap.parse_args(argv)
    os.environ["ROMANA_USE_TRACI"] = "1"          # sumo-gui necesită TraCI clasic, nu libsumo
    from romana.control import controllers as C
    from romana.control.env import start_sumo, traci

    sc = Path(args.scenariu)
    if args.strategie == "fix_webster":
        ctrl = C.FixedWebster(DEMAND_DIR / sc.stem / "od_estimat.json")
    elif args.strategie == "actuated":
        ctrl = C.Actuated()
    elif args.strategie == "max_pressure":
        ctrl = C.MaxPressure()
    else:
        name = "coridor" if args.strategie == "rl_ppo_coridor" else "romana"
        from romana.control.train import NEIGHBORS

        ctrl = C.RLPolicy(MODELS_DIR / f"ppo_{name}.zip",
                          controlled=["romana"] + (NEIGHBORS if name == "coridor" else []))
    start_sumo(sc, seed=1, gui=True)
    ctrl.reset(traci)
    t = 0
    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            if t % 5 == 0:
                ctrl.act(traci, t)
            traci.simulationStep()
            if hasattr(ctrl, "tick"):
                ctrl.tick()
            t += 1
    except traci.exceptions.FatalTraCIError:
        pass
    finally:
        try:
            traci.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
