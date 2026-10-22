"""Demonstrație rapidă: aceeași oră de trafic real, semaforul condus de planul fix actual și de agentul AI.

Rulează în paralel (câte un proces pe simulare) scenariul ales cu planul fix de referință, Max-Pressure și
agentul PPO, pe aceleași seed-uri (aceleași vehicule, aceiași pietoni), și afișează comparația pe categorii
de participanți. Nu modifică rezultatele oficiale (outputs/eval, docs/rezultate): fișierele temporare merg
în outputs/demo. Evaluarea completă rămâne `python -m romana.control.evaluate` (vezi § 9).

Exemple:
  python -m romana.control.demo                                           # prânzul din 21.10, 5 seed-uri
  python -m romana.control.demo --scenariu sumo/scenarios/zi_2026-10-21_varf.sumocfg --seeds 5
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from romana.common import MODELS_DIR, OUTPUT_DIR, ROOT

STRATEGII = {"fix_referinta": "Plan fix actual", "max_pressure": "Max-Pressure", "rl_ppo": "Agent AI (PPO)"}
COLOANE = [("pierdere_totala_h", "Pierdere totală, toți participanții (h)", 1),
           ("asteptare_medie_s", "Așteptare medie vehicul (s)", 1),
           ("intarziere_intrare_s", "Întârziere la intrarea în rețea (s/veh)", 1),
           ("pierdere_timp_biciclete_s", "Pierdere de timp biciclist (s)", 1),
           ("pierdere_timp_pietoni_s", "Pierdere de timp pieton (s)", 1),
           ("coada_medie_romana", "Coada medie la semafoarele pieței (veh)", 1),
           ("vehicule_sosite", "Vehicule care au ajuns la destinație", 0),
           ("co2_kg", "Emisii CO2 (kg)", 0)]


def _run(args):
    scen, strategie, seed, model = args
    # mesajele SUMO (încărcare, statistici) ar acoperi tabelul final: le redirecționăm în procesul lucrător
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    from romana.control import controllers as C
    from romana.control import evaluate as E

    E.EVAL_DIR = OUTPUT_DIR / "demo"
    ctrl = {"fix_referinta": C.FixedReference, "max_pressure": C.MaxPressure}.get(strategie)
    ctrl = ctrl() if ctrl else C.RLPolicy(Path(model))
    ctrl.name = strategie
    return E.run_one(Path(scen), ctrl, seed)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenariu", default=str(ROOT / "sumo" / "scenarios" / "zi_2026-10-21_pranz.sumocfg"))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--model", default=str(MODELS_DIR / "ppo_romana.zip"))
    args = ap.parse_args(argv)

    scen = Path(args.scenariu).resolve()
    tasks = [(str(scen), s, seed, args.model) for seed in range(1, args.seeds + 1) for s in STRATEGII]
    print(f"Scenariul {scen.stem}: {len(tasks)} simulări în paralel "
          f"({len(STRATEGII)} strategii × {args.seeds} seed-uri, aceeași cerere de trafic pentru toate)...", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(len(tasks), 8)) as ex:
        res = list(ex.map(_run, tasks))
    print(f"gata în {time.time() - t0:.0f} s\n")

    medie = {s: {k: sum(r[k] for r in res if r["strategie"] == s) / args.seeds for k, _, _ in COLOANE}
             for s in STRATEGII}
    w = max(len(t) for _, t, _ in COLOANE)
    print(f"{'':<{w}}" + "".join(f"{n:>18}" for n in STRATEGII.values()))
    for k, titlu, zec in COLOANE:
        baza = medie["fix_referinta"][k]
        celule = []
        for s in STRATEGII:
            v = medie[s][k]
            d = "" if s == "fix_referinta" or not baza else f" ({(v - baza) / baza * 100:+.0f}%)"
            celule.append(f"{v:.{zec}f}{d}")
        print(f"{titlu:<{w}}" + "".join(f"{c:>18}" for c in celule))
    rl, fx = medie["rl_ppo"]["pierdere_totala_h"], medie["fix_referinta"]["pierdere_totala_h"]
    print(f"\nAgentul AI față de planul fix actual: {(rl - fx) / fx * 100:+.1f}% timp pierdut de toți participanții "
          f"({abs(fx - rl):.1f} ore-om {'câștigate' if rl < fx else 'pierdute'} în această oră de trafic).")
    print("Notă: cu puține seed-uri rezultatul variază; evaluarea oficială (10 scenarii × 5 seed-uri) e în § 9.")


if __name__ == "__main__":
    main()
