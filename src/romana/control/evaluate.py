"""Evaluarea comparativă a strategiilor de semaforizare pe scenariile calibrate.

Pentru fiecare scenariu × strategie × seed se rulează simularea completă (cererea + 15 min
de golire) și se calculează, din tripinfo SUMO:
  * timpul mediu de așteptare (s/vehicul) și pierderea de timp (timeLoss);
  * durata medie a călătoriei; debitul (vehicule sosite);
  * vehiculele rămase blocate / neintroduse la final (penalizează strategiile care „ascund”
    coada în afara rețelei);
  * emisiile de CO2 (modelul HBEFA din SUMO);
  * coada medie pe brațele Pieței Romane (eșantionată la 5 s).
Rezultatele: outputs/eval/rezultate.csv, docs/rezultate/rezultate.md și grafic PNG.

Exemplu:  python -m romana.control.evaluate --seeds 5 --model models/ppo_romana.zip
"""
from __future__ import annotations

import argparse
import glob
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from romana.common import DEMAND_DIR, OUTPUT_DIR, ROOT
from romana.control import controllers as C
from romana.control.env import start_sumo, traci

EVAL_DIR = OUTPUT_DIR / "eval"
DOCS_RES = ROOT / "docs" / "rezultate"
NAMES_RO = {"fix_webster": "Plan fix (Webster)", "actuated": "Actuated SUMO", "max_pressure": "Max-Pressure",
            "rl_ppo": "Agent RL (PPO)", "rl_ppo_coridor": "Agent RL coridor (PPO)"}


def run_one(sumocfg: Path, ctrl, seed: int, horizon: int | None = None) -> dict:
    tag = f"{sumocfg.stem}_{ctrl.name}_{seed}"
    ti = EVAL_DIR / f"tripinfo_{tag}.xml"
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    start_sumo(sumocfg, seed, extra=["--tripinfo-output", str(ti), "--device.emissions.probability", "1",
                                     "--tripinfo-output.write-unfinished", "true"])
    ctrl.reset(traci)
    end = horizon or int(float(ET.parse(sumocfg).getroot().find("time/end").get("value")))
    from romana.control.signals import SignalController

    lanes = []
    for ln in traci.trafficlight.getControlledLanes("romana"):
        if ln not in lanes:
            lanes.append(ln)
    q_samples = []
    for t in range(end):
        if t % 5 == 0:
            ctrl.act(traci, t)
            q_samples.append(sum(traci.lane.getLastStepHaltingNumber(ln) for ln in lanes))
        traci.simulationStep()
        if hasattr(ctrl, "tick"):
            ctrl.tick()
    pending = traci.simulation.getMinExpectedNumber()
    traci.close()
    _ = SignalController
    return {**parse_tripinfo(ti), "coada_medie_romana": float(np.mean(q_samples)),
            "coada_max_romana": float(np.max(q_samples)), "nefinalizate": int(pending),
            "scenariu": sumocfg.stem, "strategie": ctrl.name, "seed": seed}


def parse_tripinfo(path: Path) -> dict:
    wait, loss, dur, co2, n_arr, n_unf = [], [], [], 0.0, 0, 0
    for _, el in ET.iterparse(path):
        if el.tag != "tripinfo":
            continue
        if el.get("arrival") in (None, "-1", "-1.00") or float(el.get("arrival", -1)) < 0:
            n_unf += 1
        else:
            n_arr += 1
        wait.append(float(el.get("waitingTime")))
        loss.append(float(el.get("timeLoss")))
        dur.append(float(el.get("duration")))
        em = el.find("emissions")
        if em is not None:
            co2 += float(em.get("CO2_abs", 0))
        el.clear()
    path.unlink(missing_ok=True)   # fișierele brute sunt mari; păstrăm doar agregatele
    return {"vehicule_sosite": n_arr, "vehicule_neterminate": n_unf,
            "asteptare_medie_s": float(np.mean(wait)), "pierdere_timp_medie_s": float(np.mean(loss)),
            "durata_medie_s": float(np.mean(dur)), "co2_kg": co2 / 1e6}


def make_controllers(sumocfg: Path, models: list[Path]):
    od = DEMAND_DIR / sumocfg.stem / "od_estimat.json"
    ctrls = [C.FixedWebster(od), C.Actuated(), C.MaxPressure()]
    for m in models:
        meta = json.loads(m.with_suffix(".json").read_text(encoding="utf-8")) if m.with_suffix(".json").exists() else {}
        rl = C.RLPolicy(m, controlled=meta.get("controlate", ["romana"]))
        rl.name = "rl_ppo_coridor" if len(rl.controlled) > 1 else "rl_ppo"
        ctrls.append(rl)
    return ctrls


def report(df: pd.DataFrame) -> None:
    DOCS_RES.mkdir(parents=True, exist_ok=True)
    metrics = ["asteptare_medie_s", "pierdere_timp_medie_s", "durata_medie_s", "coada_medie_romana",
               "vehicule_sosite", "nefinalizate", "co2_kg"]
    g = df.groupby(["scenariu", "strategie"])[metrics].agg(["mean", "std"])
    lines = ["# Rezultate – evaluare comparativă\n",
             f"Medii ± abatere standard pe {df['seed'].nunique()} seed-uri SUMO. Generat automat de "
             "`python -m romana.control.evaluate`.\n"]
    for sc in df["scenariu"].unique():
        lines.append(f"\n## Scenariul `{sc}`\n")
        lines.append("| Strategie | Așteptare medie (s) | Pierdere de timp (s) | Durată călătorie (s) | "
                     "Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |")
        lines.append("|---|---|---|---|---|---|---|---|")
        base = g.loc[(sc, "fix_webster"), ("asteptare_medie_s", "mean")] if (sc, "fix_webster") in g.index else None
        for st in g.loc[sc].index:
            r = g.loc[(sc, st)]
            cell = lambda m, d=1: f"{r[(m, 'mean')]:.{d}f} ± {r[(m, 'std')]:.{d}f}"  # noqa: E731
            delta = ""
            if base and st != "fix_webster":
                delta = f" ({100 * (r[('asteptare_medie_s', 'mean')] - base) / base:+.0f}%)"
            lines.append(f"| {NAMES_RO.get(st, st)} | {cell('asteptare_medie_s')}{delta} | {cell('pierdere_timp_medie_s')} | "
                         f"{cell('durata_medie_s')} | {cell('coada_medie_romana')} | {cell('vehicule_sosite', 0)} | "
                         f"{cell('nefinalizate', 0)} | {cell('co2_kg', 0)} |")
    (DOCS_RES / "rezultate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        scen = list(df["scenariu"].unique())
        strat = [s for s in NAMES_RO if s in df["strategie"].unique()]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        w = 0.8 / len(strat)
        colors = ["#8c8c8c", "#e6a23c", "#5b8ff9", "#2fa36b", "#9254de"]
        for k, m in enumerate(["asteptare_medie_s", "coada_medie_romana"]):
            ax = axes[k]
            for i, st in enumerate(strat):
                vals = [g.loc[(sc, st), (m, "mean")] if (sc, st) in g.index else np.nan for sc in scen]
                errs = [g.loc[(sc, st), (m, "std")] if (sc, st) in g.index else 0 for sc in scen]
                ax.bar(np.arange(len(scen)) + i * w, vals, w, yerr=errs, label=NAMES_RO[st], color=colors[i % 5])
            ax.set_xticks(np.arange(len(scen)) + w * (len(strat) - 1) / 2)
            ax.set_xticklabels(scen, rotation=10)
            ax.set_title("Timp mediu de așteptare (s/vehicul)" if k == 0 else "Coadă medie la Piața Romană (vehicule)")
            ax.grid(axis="y", alpha=0.3)
        axes[0].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(DOCS_RES / "comparatie_strategii.png", dpi=120)
    except Exception as e:  # graficul e opțional
        print("grafic omis:", e)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarii", nargs="*", default=None)
    ap.add_argument("--model", nargs="*", default=None, help="modele PPO (.zip) de evaluat")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--strategii", nargs="*", default=None, help="filtru: fix_webster actuated max_pressure rl_ppo ...")
    args = ap.parse_args(argv)
    scen = [Path(s) for s in (args.scenarii or sorted(glob.glob(str(ROOT / "sumo/scenarios/*.sumocfg"))))]
    models = [Path(m) for m in (args.model if args.model is not None else sorted(glob.glob(str(ROOT / "models/ppo_*.zip"))))]
    rows = []
    for sc in scen:
        for ctrl in make_controllers(sc, models):
            if args.strategii and ctrl.name not in args.strategii:
                continue
            for seed in range(1, args.seeds + 1):
                r = run_one(sc, ctrl, seed)
                rows.append(r)
                print(f"{sc.stem:22s} {ctrl.name:15s} seed={seed}  așteptare={r['asteptare_medie_s']:.1f}s  "
                      f"coadă={r['coada_medie_romana']:.1f}  rămase={r['nefinalizate']}")
    df = pd.DataFrame(rows)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(EVAL_DIR / "rezultate.csv", index=False)
    DOCS_RES.mkdir(parents=True, exist_ok=True)
    df.to_csv(DOCS_RES / "rezultate_brute.csv", index=False)
    report(df)
    print(f"[OK] {DOCS_RES / 'rezultate.md'}")


if __name__ == "__main__":
    main()
