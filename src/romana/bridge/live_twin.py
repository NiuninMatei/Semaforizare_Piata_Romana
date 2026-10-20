"""Geamănul digital live: camera → SUMO în timp real → semafor controlat de AI.

Procesul citește în fiecare secundă starea publicată de modulul de viziune
(outputs/live/state.json – debite pe brațe, viraje observate, pietoni pe treceri) și
injectează în SUMO vehicule pe brațele Pieței Romane, cu aceleași debite și aceleași
proporții de viraj (proces Poisson, rute realiste din setul candidat; bicicliștii pe rute
permise bicicletelor), plus pietoni pe traseele care trec prin piață (debitul de pe trecerile
vizibile × factor_extrapolare_pietoni). Semaforul pieței este condus de strategia aleasă din
dashboard: agentul RL, planul fix de referință (N–S / E–V / pietoni), Max-Pressure sau manual.

Dacă fluxul camerei nu este disponibil (stare mai veche de 60 s), se folosește
profilul de referință și acest lucru este semnalat explicit în dashboard.

Rulare:  python -m romana.bridge.live_twin [--gui] [--model models/ppo_romana.zip]
"""
from __future__ import annotations

import argparse
import json
import random
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import numpy as np

from romana.common import DEMAND_DIR, MODELS_DIR, NET_DIR, OUTPUT_DIR, load_json
from romana.control.signals import SignalController, romana_green_phases

LIVE = OUTPUT_DIR / "live"


def load_route_pool(cfg: dict, vclass: str = "passenger") -> dict[tuple[str, str], list[list[str]]]:
    from romana.bridge.build_demand import build_candidates, candidates_file, write_vtypes

    arms = cfg["brate"]
    cand = candidates_file(vclass)
    if not cand.exists():   # fișier regenerabil, nu e în Git
        write_vtypes()
        build_candidates(cfg, vclass=vclass)
    pool = defaultdict(list)
    for _, el in ET.iterparse(cand):
        if el.tag != "route":
            continue
        edges = el.get("edges").split()
        for o, oi in arms.items():
            if not oi["intrare"] or oi["intrare"] not in edges:
                continue
            i = edges.index(oi["intrare"])
            for d, di in arms.items():
                if di["iesire"] in edges[i:]:
                    pool[(o, d)].append(edges)
    return pool


def read_json(path: Path, max_age: float | None = None):
    try:
        if max_age is not None and time.time() - path.stat().st_mtime > max_age:
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def turning_ratios(cfg: dict, observed: dict[str, int]) -> dict[str, dict[str, float]]:
    """Proporții de viraj: virajele observate de cameră + distribuția a priori ca regularizare."""
    w = cfg.get("pondere_prior", 2.0)
    out = {}
    for o, prior in cfg["prior_destinatii"].items():
        tot = sum(prior.values())
        s = {d: observed.get(f"{o}>{d}", 0) + w * p / tot for d, p in prior.items()}
        z = sum(s.values())
        out[o] = {d: v / z for d, v in s.items()}
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gui", action="store_true", help="deschide sumo-gui")
    ap.add_argument("--model", default=str(MODELS_DIR / "ppo_romana.zip"))
    ap.add_argument("--viteza", type=float, default=1.0, help="1 = timp real; 0 = cât de repede se poate")
    ap.add_argument("--durata", type=int, default=0, help="secunde simulate până la oprire (0 = continuu)")
    args = ap.parse_args(argv)

    from romana.common import sumo_binary, sumo_home

    sumo_home()
    import traci  # TraCI clasic: permite și sumo-gui

    cfg = load_json("demand.json")
    pools = {"passenger": load_route_pool(cfg), "bicycle": load_route_pool(cfg, "bicycle")}
    from romana.bridge.build_demand import pedestrian_pool

    ped_pool = pedestrian_pool(cfg)
    ref = cfg["profil_referinta"]
    shares = {k: v for k, v in ref["pondere_clase"].items() if v > 0}
    traci.start([sumo_binary("sumo-gui" if args.gui else "sumo"), "-n", str(NET_DIR / "romana.net.xml"),
                 "--additional-files", f"{DEMAND_DIR / 'vtypes.add.xml'},{NET_DIR / 'tls_actuated.add.xml'}",
                 "--no-step-log", "--no-warnings", "--time-to-teleport", "300", "--begin", "0",
                 "--gui-settings-file", str(NET_DIR / "view.xml"), "--start", "--quit-on-end"]
                if args.gui else
                [sumo_binary("sumo"), "-n", str(NET_DIR / "romana.net.xml"),
                 "--additional-files", f"{DEMAND_DIR / 'vtypes.add.xml'},{NET_DIR / 'tls_actuated.add.xml'}",
                 "--no-step-log", "--no-warnings", "--time-to-teleport", "300"])
    for tid in traci.trafficlight.getIDList():
        traci.trafficlight.setProgram(tid, "0")

    greens, names = romana_green_phases()
    ctrl = SignalController(traci, "romana", greens, names)
    from romana.control.controllers import RLPolicy

    rl = None
    if Path(args.model).exists():
        rl = RLPolicy(Path(args.model))
        rl.reset(traci)
        rl.ctrls = [ctrl]           # aceeași instanță de controler pentru toate modurile
    from romana.control.controllers import fixed_phase_indices

    plan_cycle = fixed_phase_indices()            # planul fix de referință: N–S, E–V, pietoni
    plan_green = {i: load_json("network.json")["romana_faze"][i]["durata_fixa"] for i in plan_cycle}
    info = json.loads((NET_DIR / "network_info.json").read_text(encoding="utf-8"))
    route_ids: dict[tuple, list[str]] = {}
    n_veh, n_ped, t, last_src = 0, 0, 0, ""
    hist = []
    LIVE.mkdir(parents=True, exist_ok=True)
    print("[geamăn digital] pornit. Moduri: ai / fix / max_pressure / manual (din dashboard)")
    try:
        while not args.durata or t < args.durata:
            t0 = time.time()
            cam = read_json(LIVE / "state.json", max_age=60)
            cmd = read_json(LIVE / "command.json") or {"mod": "ai" if rl else "fix"}
            if cam and cam.get("intrari_veh_h") and cam.get("secunde_interval", 0) >= 60:
                rates = {k: float(v) for k, v in cam["intrari_veh_h"].items()}
                obs_turns = cam.get("total_viraje", {})
                ped_rate = sum(cam.get("pietoni_h", {}).values()) * cfg.get("factor_extrapolare_pietoni", 1.0)
                src = "camera live"
            else:
                rates = {k: float(v) for k, v in ref["intrari_veh_h"].items()}
                obs_turns = {}
                ped_rate = float(ref.get("pietoni_h", 0))
                src = "profil de referință (camera indisponibilă)"
            if src != last_src:
                print(f"[geamăn digital] sursa cererii: {src}")
                last_src = src
            ratios = turning_ratios(cfg, obs_turns)
            # --- injectare vehicule (Poisson), pe tipuri după ponderile profilului ---
            for o, lam in rates.items():
                if o not in ratios or random.random() >= lam / 3600.0:
                    continue
                d = random.choices(list(ratios[o]), weights=list(ratios[o].values()))[0]
                vt = random.choices(list(shares), weights=list(shares.values()))[0]
                vclass = "bicycle" if vt == "bicycle" else "passenger"
                routes = pools[vclass].get((o, d))
                if not routes:
                    continue
                key = (vclass, o, d)
                if key not in route_ids:
                    route_ids[key] = []
                    for k, edges in enumerate(routes[:20]):
                        rid = f"r_{vclass}_{o}_{d}_{k}"
                        traci.route.add(rid, edges)
                        route_ids[key].append(rid)
                traci.vehicle.add(f"live_{n_veh}", random.choice(route_ids[key]), typeID=vt, departLane="best")
                n_veh += 1
            # --- injectare pietoni (Poisson) pe traseele care trec prin piață ---
            if ped_pool and random.random() < ped_rate / 3600.0:
                edges = random.choice(ped_pool).split()
                pid = f"pieton_live_{n_ped}"
                try:
                    traci.person.add(pid, edges[0], 0.0, typeID="pieton")
                    traci.person.appendWalkingStage(pid, edges, traci.lane.getLength(f"{edges[-1]}_0") / 2)
                    n_ped += 1
                except traci.exceptions.TraCIException as e:   # traseu invalid: se sare peste
                    print(f"[geamăn digital] pieton omis: {e}")
                    if pid in traci.person.getIDList():
                        traci.person.remove(pid)
                    n_ped += 1
            # --- control semafor ---
            mode = cmd.get("mod", "ai")
            if t % 5 == 0:
                if mode == "ai" and rl is not None:
                    rl.act(traci, t)
                elif mode == "max_pressure" and ctrl.can_switch():
                    ctrl.request(int(np.argmax(ctrl.phase_pressure())))
                elif mode == "manual":
                    ctrl.request(int(cmd.get("faza", ctrl.current)))
                elif mode == "fix":
                    if ctrl.current not in plan_cycle:
                        ctrl.request(plan_cycle[0])
                    elif ctrl.green_time >= plan_green[ctrl.current]:
                        ctrl.request(plan_cycle[(plan_cycle.index(ctrl.current) + 1) % len(plan_cycle)])
            traci.simulationStep()
            ctrl.tick()
            t += 1
            # --- stare pentru dashboard ---
            if True:
                arms_q, seen = defaultdict(int), set()
                for i, ln in enumerate(traci.trafficlight.getControlledLanes("romana")):
                    g = info["link_group"][i] or ""
                    if g.startswith("intrare_") and ln not in seen:   # o bandă controlează mai multe legături
                        seen.add(ln)
                        arms_q[g[len("intrare_"):]] += traci.lane.getLastStepHaltingNumber(ln)
                arms_q["pietoni"] = sum(ctrl.ped_waiting())
                q_tot = sum(traci.lane.getLastStepHaltingNumber(ln) for ln in ctrl.in_lanes)
                hist.append([t, q_tot])
                hist = hist[-600:]
                state = {"timestamp": time.time(), "timp_sim": t, "mod": mode, "sursa": src,
                         "faza": ctrl.current, "faza_nume": ctrl.names[ctrl.current], "etapa": ctrl.stage,
                         "verde_s": ctrl.green_time, "faze": ctrl.names, "model_ai": bool(rl),
                         "coada_brate": dict(arms_q), "coada_total": q_tot,
                         "vehicule_in_retea": traci.vehicle.getIDCount(), "vehicule_injectate": n_veh,
                         "pietoni_in_retea": traci.person.getIDCount(), "pietoni_injectati": n_ped,
                         "debite_folosite": rates, "pietoni_h_folositi": round(ped_rate),
                         "istoric_coada": hist[::5]}
                tmp = LIVE / "sim_tmp.json"
                tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
                tmp.replace(LIVE / "sim_state.json")
            if args.viteza > 0:
                time.sleep(max(0.0, 1.0 / args.viteza - (time.time() - t0)))
    except (KeyboardInterrupt, traci.exceptions.FatalTraCIError):
        pass
    finally:
        try:
            traci.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
