"""Duratele de verde folosite de agenții RL pe piață (diagnostic, § 9.9).

Pentru fiecare agent și scenariu se înregistrează secundă cu secundă faza și etapa controlerului pieței
(`SignalController`). Rezultă, pe fază (N–S, E–V, pietoni), mediana duratei verdelui și numărul de verzi, plus
ciclul median: timpul dintre două începuturi succesive de verde N–S. Planurile fixe nu au nevoie de diagnostic:
duratele lor sunt chiar cele din nume (PLAN_a_b_c).

Exemplu:
  python -m romana.control.durate_verde models/ppo_romana_cal.zip models/ppo_romana.zip ^
      --scenarii capacitate_zi_2026-10-26_linistit capacitate_zi_2026-10-26_pranz capacitate_zi_2026-10-26_varf ^
      --seed 11 --out outputs/durate_verde.csv
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from romana.common import ROOT
from romana.control.env import start_sumo, traci
from romana.control.validare import make_controller

FAZE = {0: "ns", 1: "ev", 2: "pietoni"}


def durate(model: str, scenariu: str, seed: int) -> dict:
    cfg = ROOT / "sumo" / "scenarios" / f"{scenariu}.sumocfg"
    ctrl = make_controller(model)
    start_sumo(cfg, seed, extra=[])
    ctrl.reset(traci)
    sc = ctrl.ctrls[0]                                     # controlerul pieței (primul din listă)
    end = int(float(ET.parse(cfg).getroot().find("time/end").get("value")))
    verzi = {f: [] for f in FAZE}
    start_ns, prev, t0 = [], None, 0
    for t in range(end):
        if t % 5 == 0:
            ctrl.act(traci, t)
        traci.simulationStep()
        ctrl.tick()
        cur = (sc.current, sc.stage)
        if cur != prev:
            if prev is not None and prev[1] == "green" and prev[0] in verzi:
                verzi[prev[0]].append(t - t0)
            if cur == (0, "green"):
                start_ns.append(t)
            prev, t0 = cur, t
    traci.close()
    r = {"strategie": ctrl.name, "scenariu": scenariu, "seed": seed}
    for f, nume in FAZE.items():
        r[f"verde_median_{nume}_s"] = float(np.median(verzi[f])) if verzi[f] else np.nan
        r[f"verzi_{nume}"] = len(verzi[f])
    r["ciclu_median_s"] = float(np.median(np.diff(start_ns))) if len(start_ns) > 1 else np.nan
    return r


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modele", nargs="+", help="căi către agenți .zip (cu .json alături)")
    ap.add_argument("--scenarii", nargs="+", required=True, help="numele scenariilor din sumo/scenarios")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="outputs/durate_verde.csv")
    args = ap.parse_args(argv)
    rez = []
    for m in args.modele:
        for s in args.scenarii:
            rez.append(durate(str(ROOT / m) if not Path(m).is_absolute() else m, s, args.seed))
            print(rez[-1], flush=True)
    df = pd.DataFrame(rez)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print(f"[OK] {args.out}")


if __name__ == "__main__":
    main()
