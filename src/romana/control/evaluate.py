"""Evaluarea comparativă a strategiilor de semaforizare pe scenariile calibrate.

Pentru fiecare scenariu × strategie × seed se rulează simularea completă (cererea + 15 min
de golire) și se calculează, din tripinfo SUMO, separat pe categorii de participanți:
  * vehicule motorizate: timpul mediu de așteptare (s/vehicul), pierderea de timp (timeLoss),
    durata medie a călătoriei, vehiculele sosite;
  * bicicliști: așteptarea și pierderea de timp medii;
  * pietoni (personinfo/walk): pierderea de timp și durata medie a deplasării;
  * pierderea de timp totală a tuturor participanților (ore);
  * vehiculele rămase blocate / neintroduse la final (penalizează strategiile care „ascund”
    coada în afara rețelei);
  * emisiile de CO2 (modelul HBEFA din SUMO);
  * coada medie de vehicule și pietonii care așteaptă la trecerile Pieței Romane (la 5 s).
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
NAMES_RO = {"fix_referinta": "Plan fix de referință", "fix_webster": "Plan fix (Webster)",
            "actuated": "Actuated SUMO", "max_pressure": "Max-Pressure",
            "rl_ppo": "Agent RL (PPO)", "rl_ppo_coridor": "Agent RL coridor (PPO)"}
BASELINE = "fix_referinta"


def run_one(sumocfg: Path, ctrl, seed: int, horizon: int | None = None) -> dict:
    tag = f"{sumocfg.stem}_{ctrl.name}_{seed}"
    ti = EVAL_DIR / f"tripinfo_{tag}.xml"
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    start_sumo(sumocfg, seed, extra=["--tripinfo-output", str(ti), "--device.emissions.probability", "1",
                                     "--tripinfo-output.write-unfinished", "true"])
    ctrl.reset(traci)
    end = horizon or int(float(ET.parse(sumocfg).getroot().find("time/end").get("value")))
    lanes = []
    for ln in traci.trafficlight.getControlledLanes("romana"):
        if ln not in lanes:
            lanes.append(ln)
    veh_lanes = [ln for ln in lanes if not ln.startswith(":")]
    ped_areas = sorted({ln.rsplit("_", 1)[0] for ln in lanes if ln.startswith(":")})
    q_samples, p_samples = [], []
    for t in range(end):
        if t % 5 == 0:
            ctrl.act(traci, t)
            q_samples.append(sum(traci.lane.getLastStepHaltingNumber(ln) for ln in veh_lanes))
            p_samples.append(sum(1 for e in ped_areas for p in traci.edge.getLastStepPersonIDs(e)
                                 if traci.person.getSpeed(p) < 0.1))
        traci.simulationStep()
        if hasattr(ctrl, "tick"):
            ctrl.tick()
    pending = traci.simulation.getMinExpectedNumber()
    traci.close()
    return {**parse_tripinfo(ti), "coada_medie_romana": float(np.mean(q_samples)),
            "coada_max_romana": float(np.max(q_samples)), "pietoni_asteapta_medie": float(np.mean(p_samples)),
            "nefinalizate": int(pending), "scenariu": sumocfg.stem, "strategie": ctrl.name, "seed": seed}


def _mean(xs: list[float]) -> float:
    return float(np.mean(xs)) if xs else float("nan")


def parse_tripinfo(path: Path) -> dict:
    """Agregate pe categorii: vehicule motorizate, bicicliști (vType bicycle) și pietoni (walk)."""
    veh = {"wait": [], "loss": [], "dur": []}
    bike = {"wait": [], "loss": []}
    ped = {"loss": [], "dur": []}
    co2, n_arr, n_unf, n_ped = 0.0, 0, 0, 0
    for _, el in ET.iterparse(path):
        if el.tag == "tripinfo":
            if float(el.get("arrival", -1)) < 0:
                n_unf += 1
            elif el.get("vType") != "bicycle":
                n_arr += 1
            if el.get("vType") == "bicycle":
                bike["wait"].append(float(el.get("waitingTime")))
                bike["loss"].append(float(el.get("timeLoss")))
            else:
                veh["wait"].append(float(el.get("waitingTime")))
                veh["loss"].append(float(el.get("timeLoss")))
                veh["dur"].append(float(el.get("duration")))
            em = el.find("emissions")
            if em is not None:
                co2 += float(em.get("CO2_abs", 0))
            el.clear()
        elif el.tag == "personinfo":
            for w in el.findall("walk"):
                if float(w.get("arrival", -1)) >= 0:
                    n_ped += 1
                ped["loss"].append(float(w.get("timeLoss", 0)))
                ped["dur"].append(float(w.get("duration", 0)))
            el.clear()
    path.unlink(missing_ok=True)   # fișierele brute sunt mari; păstrăm doar agregatele
    total_h = (sum(veh["loss"]) + sum(bike["loss"]) + sum(ped["loss"])) / 3600
    return {"vehicule_sosite": n_arr, "vehicule_neterminate": n_unf,
            "asteptare_medie_s": _mean(veh["wait"]), "pierdere_timp_medie_s": _mean(veh["loss"]),
            "durata_medie_s": _mean(veh["dur"]), "co2_kg": co2 / 1e6,
            "biciclisti": len(bike["loss"]), "asteptare_biciclete_s": _mean(bike["wait"]),
            "pierdere_timp_biciclete_s": _mean(bike["loss"]),
            "pietoni_sositi": n_ped, "pierdere_timp_pietoni_s": _mean(ped["loss"]),
            "durata_pietoni_s": _mean(ped["dur"]), "pierdere_totala_h": total_h}


def make_controllers(sumocfg: Path, models: list[Path]):
    od = DEMAND_DIR / sumocfg.stem / "od_estimat.json"
    ctrls = [C.FixedReference(), C.FixedWebster(od), C.Actuated(), C.MaxPressure()]
    for m in models:
        meta = json.loads(m.with_suffix(".json").read_text(encoding="utf-8")) if m.with_suffix(".json").exists() else {}
        rl = C.RLPolicy(m, controlled=meta.get("controlate", ["romana"]))
        rl.name = "rl_ppo_coridor" if len(rl.controlled) > 1 else "rl_ppo"
        ctrls.append(rl)
    return ctrls


def report(df: pd.DataFrame) -> None:
    DOCS_RES.mkdir(parents=True, exist_ok=True)
    metrics = ["asteptare_medie_s", "pierdere_timp_medie_s", "durata_medie_s", "coada_medie_romana",
               "vehicule_sosite", "nefinalizate", "co2_kg", "asteptare_biciclete_s", "pierdere_timp_biciclete_s",
               "pierdere_timp_pietoni_s", "pietoni_asteapta_medie", "pierdere_totala_h"]
    metrics = [m for m in metrics if m in df.columns]
    g = df.groupby(["scenariu", "strategie"])[metrics].agg(["mean", "std"])
    med = df.groupby(["scenariu", "strategie"])["asteptare_medie_s"].median()
    order = [s for s in NAMES_RO if s in df["strategie"].unique()]
    lines = ["# Rezultate – evaluare comparativă\n",
             f"Medii ± abatere standard pe {df['seed'].nunique()} seed-uri SUMO. Procentele sunt față de "
             f"{NAMES_RO[BASELINE].lower()}. Mediana pe seed-uri este dată separat pentru așteptarea vehiculelor: "
             "aproape de saturație, rețeaua poate intra sau nu în blocaj în funcție de seed, iar câteva rulări "
             "blocate trag media în sus. Generat automat de `python -m romana.control.evaluate`.\n"]

    def delta(r, base, m):
        if base is None or not np.isfinite(base) or base == 0:
            return ""
        return f" ({100 * (r[(m, 'mean')] - base) / base:+.0f}%)"

    for sc in df["scenariu"].unique():
        sts = [s for s in order if (sc, s) in g.index]
        b = g.loc[(sc, BASELINE)] if (sc, BASELINE) in g.index else None
        base = (lambda m: b[(m, "mean")]) if b is not None else (lambda m: None)  # noqa: E731
        lines.append(f"\n## Scenariul `{sc}`\n")
        lines.append("**Vehicule motorizate**\n")
        lines.append("| Strategie | Așteptare medie (s) | Așteptare mediană (s) | Pierdere de timp (s) | "
                     "Durată călătorie (s) | Coadă medie piață (veh) | Vehicule sosite | Rămase în rețea | CO₂ (kg) |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for st in sts:
            r = g.loc[(sc, st)]
            cell = lambda m, d=1: f"{r[(m, 'mean')]:.{d}f} ± {r[(m, 'std')]:.{d}f}"  # noqa: E731
            dl = "" if st == BASELINE else delta(r, base("asteptare_medie_s"), "asteptare_medie_s")
            mb = med.get((sc, BASELINE))
            dm = "" if st == BASELINE or not mb else f" ({100 * (med[(sc, st)] - mb) / mb:+.0f}%)"
            lines.append(f"| {NAMES_RO.get(st, st)} | {cell('asteptare_medie_s')}{dl} | {med[(sc, st)]:.1f}{dm} | "
                         f"{cell('pierdere_timp_medie_s')} | "
                         f"{cell('durata_medie_s')} | {cell('coada_medie_romana')} | {cell('vehicule_sosite', 0)} | "
                         f"{cell('nefinalizate', 0)} | {cell('co2_kg', 0)} |")
        if "pierdere_timp_pietoni_s" in metrics:
            lines.append("\n**Bicicliști, pietoni și total**\n")
            lines.append("| Strategie | Așteptare bicicliști (s) | Pierdere de timp bicicliști (s) | "
                         "Pierdere de timp pietoni (s) | Pietoni care așteaptă la treceri (medie) | "
                         "Pierdere totală, toți participanții (h) |")
            lines.append("|---|---|---|---|---|---|")
            for st in sts:
                r = g.loc[(sc, st)]
                cell = lambda m, d=1: f"{r[(m, 'mean')]:.{d}f} ± {r[(m, 'std')]:.{d}f}"  # noqa: E731
                dp = "" if st == BASELINE else delta(r, base("pierdere_timp_pietoni_s"), "pierdere_timp_pietoni_s")
                dt = "" if st == BASELINE else delta(r, base("pierdere_totala_h"), "pierdere_totala_h")
                lines.append(f"| {NAMES_RO.get(st, st)} | {cell('asteptare_biciclete_s')} | "
                             f"{cell('pierdere_timp_biciclete_s')} | {cell('pierdere_timp_pietoni_s')}{dp} | "
                             f"{cell('pietoni_asteapta_medie')} | {cell('pierdere_totala_h')}{dt} |")
    (DOCS_RES / "rezultate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        scen = list(df["scenariu"].unique())
        strat = [s for s in NAMES_RO if s in df["strategie"].unique()]
        panels = [("asteptare_medie_s", "Așteptare medie vehicule (s)"),
                  ("pierdere_timp_pietoni_s", "Pierdere de timp pietoni (s)"),
                  ("pierdere_totala_h", "Pierdere totală, toți participanții (h)")]
        panels = [p for p in panels if p[0] in metrics]
        fig, axes = plt.subplots(1, len(panels), figsize=(5.5 * len(panels), 4.5))
        axes = np.atleast_1d(axes)
        w = 0.8 / len(strat)
        colors = ["#5d6873", "#8c8c8c", "#e6a23c", "#5b8ff9", "#2fa36b", "#9254de"]
        for k, (m, title) in enumerate(panels):
            ax = axes[k]
            for i, st in enumerate(strat):
                vals = [g.loc[(sc, st), (m, "mean")] if (sc, st) in g.index else np.nan for sc in scen]
                errs = [g.loc[(sc, st), (m, "std")] if (sc, st) in g.index else 0 for sc in scen]
                ax.bar(np.arange(len(scen)) + i * w, vals, w, yerr=errs, label=NAMES_RO[st], color=colors[i % len(colors)])
            ax.set_xticks(np.arange(len(scen)) + w * (len(strat) - 1) / 2)
            ax.set_xticklabels([s.replace("referinta_", "") for s in scen])
            ax.set_title(title)
            ax.grid(axis="y", alpha=0.3)
        axes[0].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(DOCS_RES / "comparatie_strategii.png", dpi=120)
    except Exception as e:  # graficul e opțional
        print("grafic omis:", e)


def run_task(sc: Path, models: list[Path], name: str, seed: int) -> dict:
    """O rulare, construind controlerul în procesul curent (libsumo: o simulare per proces)."""
    ctrl = next(c for c in make_controllers(sc, models) if c.name == name)
    return run_one(sc, ctrl, seed)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarii", nargs="*", default=None)
    ap.add_argument("--model", nargs="*", default=None, help="modele PPO (.zip) de evaluat")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--strategii", nargs="*", default=None,
                    help="filtru: fix_referinta fix_webster actuated max_pressure rl_ppo rl_ppo_coridor")
    ap.add_argument("--procese", type=int, default=1, help="simulări în paralel (procese separate)")
    ap.add_argument("--adauga", action="store_true",
                    help="păstrează rezultatele existente din outputs/eval/rezultate.csv (înlocuiește doar rulările refăcute)")
    ap.add_argument("--doar-raport", action="store_true",
                    help="regenerează doar raportul și graficul din outputs/eval/rezultate.csv, fără simulări")
    args = ap.parse_args(argv)
    if args.doar_raport:
        report(pd.read_csv(EVAL_DIR / "rezultate.csv"))
        print(f"[OK] {DOCS_RES / 'rezultate.md'}")
        return
    scen = [Path(s) for s in (args.scenarii or sorted(glob.glob(str(ROOT / "sumo/scenarios/*.sumocfg"))))]
    models = [Path(m) for m in (args.model if args.model is not None else sorted(glob.glob(str(ROOT / "models/ppo_*.zip"))))]
    tasks = [(sc, c.name, seed) for sc in scen for c in make_controllers(sc, models)
             if not args.strategii or c.name in args.strategii for seed in range(1, args.seeds + 1)]

    def show(r):
        print(f"{r['scenariu']:22s} {r['strategie']:15s} seed={r['seed']}  așteptare={r['asteptare_medie_s']:.1f}s  "
              f"pietoni={r['pierdere_timp_pietoni_s']:.1f}s  coadă={r['coada_medie_romana']:.1f}  "
              f"rămase={r['nefinalizate']}", flush=True)

    rows = []
    if args.procese > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor(max_workers=args.procese) as ex:
            for f in as_completed([ex.submit(run_task, sc, models, name, seed) for sc, name, seed in tasks]):
                rows.append(f.result())
                show(rows[-1])
    else:
        for sc, name, seed in tasks:
            rows.append(run_task(sc, models, name, seed))
            show(rows[-1])
    df = pd.DataFrame(rows)
    key = ["scenariu", "strategie", "seed"]
    if args.adauga and (EVAL_DIR / "rezultate.csv").exists():
        old = pd.read_csv(EVAL_DIR / "rezultate.csv")
        old = old[~old.set_index(key).index.isin(df.set_index(key).index)]
        df = pd.concat([old, df], ignore_index=True)
    df = df.sort_values(key)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(EVAL_DIR / "rezultate.csv", index=False)
    DOCS_RES.mkdir(parents=True, exist_ok=True)
    df.to_csv(DOCS_RES / "rezultate_brute.csv", index=False)
    report(df)
    print(f"[OK] {DOCS_RES / 'rezultate.md'}")


if __name__ == "__main__":
    main()
