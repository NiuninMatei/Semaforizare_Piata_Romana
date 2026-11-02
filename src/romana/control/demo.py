"""Demonstrație rapidă: aceeași oră de trafic real, semaforul condus de planul de referință, de planul observat și de agentul IA.

Rulează în paralel (câte un proces pe simulare) scenariul ales cu planul de referință 36/28/12, planul observat,
Presiune maximă și agentul PPO, pe aceleași seed-uri (aceleași vehicule, aceiași pietoni), și afișează comparația pe
categorii de participanți. Nu modifică rezultatele oficiale (outputs/eval, docs/rezultate): fișierele temporare merg
în outputs/demo. Evaluarea completă rămâne `python -m romana.control.evaluate` (vezi § 9).

Exemple:
  python -m romana.control.demo                                           # prânzul din 26.10, 5 seed-uri
  python -m romana.control.demo --scenariu sumo/scenarios/cor_zi_2026-10-26_varf.sumocfg --seeds 5
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from romana.common import MODELS_DIR, OUTPUT_DIR, ROOT

PLAN_OBSERVAT = [72.0, 48.0, 3.0]
STRATEGII = {"fix_referinta": "Plan de referință", "plan_observat": "Planul observat", "max_pressure": "Presiune maximă", "rl_ppo": "Agent IA (PPO)"}
COLOANE = [("pierdere_totala_h", "Pierdere totală, toți participanții (h)", 1),
           ("asteptare_medie_s", "Așteptare medie vehicul (s)", 1),
           ("intarziere_intrare_s", "Întârziere la intrarea în rețea (s/veh)", 1),
           ("biciclisti", "Bicicliști în simulare", 0),
           ("asteptare_biciclete_s", "Așteptare medie biciclist (s)", 1),
           ("pierdere_timp_biciclete_s", "Pierdere de timp biciclist (s)", 1),
           ("pietoni_sositi", "Pietoni care au ajuns la destinație", 0),
           ("pierdere_timp_pietoni_s","Pierdere de timp pieton (s)", 1),
           ("pietoni_asteapta_medie", "Pietoni care așteaptă la trecerile pieței (medie)", 1),
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
    if strategie == "plan_observat":
        ctrl = C.FixedWebster.__new__(C.FixedWebster)       # plan fix dat prin duratele de verde, ca în `validare`
        ctrl.plan = {"verde_s": PLAN_OBSERVAT}
    else:
        ctrl = {"fix_referinta": C.FixedReference, "max_pressure": C.MaxPressure}.get(strategie)
        ctrl = ctrl() if ctrl else C.RLPolicy(Path(model))
    ctrl.name = strategie
    return E.run_one(Path(scen), ctrl, seed)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenariu", default=str(ROOT / "sumo" / "scenarios" / "cor_zi_2026-10-26_varf.sumocfg"))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--model", default=str(MODELS_DIR / "ppo_romana_cal.zip"))
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
        baza = medie["plan_observat"][k]
        celule = []
        for s in STRATEGII:
            v = medie[s][k]
            d = "" if s == "plan_observat" or not baza else f" ({(v - baza) / baza * 100:+.0f}%)"
            celule.append(f"{v:.{zec}f}{d}")
        print(f"{titlu:<{w}}" + "".join(f"{c:>18}" for c in celule))
    baza = medie["plan_observat"]["pierdere_totala_h"]
    for s, cine in (("fix_referinta", "Planul de referință"), ("rl_ppo", "Agentul IA")):
        v = medie[s]["pierdere_totala_h"]
        print(f"\n{cine} față de planul observat: {(v - baza) / baza * 100:+.1f}% timp pierdut de toți participanții "
              f"({abs(baza - v):.1f} ore-om {'câștigate' if v < baza else 'pierdute'} în această oră de trafic).", end="")
    print("\nNotă: cu puține seed-uri rezultatul variază; regulile de alegere și evaluarea completă sunt în § 9.11.")


if __name__ == "__main__":
    main()
