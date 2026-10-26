"""Unde se pierde timpul la vârf (§ 9.6): localizarea vehiculelor oprite și a celor neintroduse în rețea.

La fiecare 10 s de simulare (planul fix actual, programul „0”), fiecare vehicul oprit (viteză < 0,1 m/s) se
atribuie uneia dintre zonele:
  * zona pieței        – benzile de intrare ale controlerului `romana` și grupurile din amonte (≈250 m);
  * la alte semafoare  – muchii care se termină la un alt semafor din rețea;
  * alte muchii        – restul;
iar vehiculele care așteaptă să intre în rețea (neintroduse, coada dincolo de marginea rețelei) se atribuie
muchiei lor de plecare, cu numele străzii și capătul față de piață (vest / est, după coordonata x).
Rezultatul se dă în vehicul-ore și ca pondere din total.

Exemplu:
  python -m romana.control.localizare zi_2026-10-21_varf zi_2026-10-22_varf ^
      indisciplinat_zi_2026-10-21_varf indisciplinat_zi_2026-10-22_varf --out outputs/localizare_varf.csv
"""
from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from romana.common import ROOT
from romana.control import controllers as C
from romana.control.env import start_sumo, traci
from romana.control.signals import SignalController, romana_green_phases, upstream_groups

PAS_S = 10


def first_edges(sumocfg: Path) -> dict[str, str]:
    """Vehicul → muchia de plecare, din fișierele de rute ale scenariului."""
    cfg = ET.parse(sumocfg).getroot()
    files = []
    for tag in ("route-files", "additional-files"):
        el = cfg.find(f".//{tag}")
        if el is not None:
            files += [sumocfg.parent / f.strip() for f in el.get("value").split(",")]
    routes, first = {}, {}
    for f in files:
        if not f.exists() or not f.name.endswith(".xml"):
            continue
        for _, el in ET.iterparse(f):
            if el.tag == "route" and el.get("id"):
                routes[el.get("id")] = el.get("edges").split()[0]
            elif el.tag in ("vehicle", "trip", "flow"):
                r = el.find("route")
                if r is not None:
                    first[el.get("id")] = r.get("edges").split()[0]
                elif el.get("route") in routes:
                    first[el.get("id")] = routes[el.get("route")]
                elif el.get("from"):
                    first[el.get("id")] = el.get("from")
    return first


def localize(scenario: str, seed: int = 1, durata_s: int = 4500) -> tuple[Counter, Counter]:
    """(zone → vehicul-secunde, muchia de plecare → vehicul-secunde neintroduse) pentru un scenariu."""
    sc = Path(scenario) if scenario.endswith(".sumocfg") else ROOT / "sumo/scenarios" / f"{scenario}.sumocfg"
    first = first_edges(sc)
    start_sumo(sc, seed)
    C.FixedReference().reset(traci)
    g, n = romana_green_phases()
    ctrl = SignalController(traci, "romana", g, n)
    traci.trafficlight.setProgram("romana", "0")            # SignalController a suprascris starea; revenim la plan
    zone = set(ctrl.in_lanes) | {ln for lanes, _ in upstream_groups(traci, ctrl) for ln in lanes}
    zone_edges = {ln.rsplit("_", 1)[0] for ln in zone}
    tls_edges = {ln.rsplit("_", 1)[0] for tid in traci.trafficlight.getIDList()
                 for ln in traci.trafficlight.getControlledLanes(tid)}
    xs = [traci.lane.getShape(ln)[-1][0] for ln in ctrl.in_lanes]
    cx = sum(xs) / len(xs)
    acc, pend = Counter(), Counter()
    for t in range(durata_s):
        traci.simulationStep()
        if t % PAS_S:
            continue
        for v in traci.vehicle.getIDList():
            if traci.vehicle.getSpeed(v) < 0.1:
                e = traci.vehicle.getRoadID(v)
                acc["zona pietei" if e in zone_edges else "la alte semafoare" if e in tls_edges else "alte muchii"] += PAS_S
        for v in traci.simulation.getPendingVehicles():
            e = first.get(v) or first.get(v.rsplit(".", 1)[0], "?")
            acc["neintroduse"] += PAS_S
            try:
                capat = "vest" if traci.lane.getShape(f"{e}_0")[0][0] < cx else "est"
                pend[(traci.edge.getStreetName(e) or e, capat, e)] += PAS_S
            except Exception:
                pend[("?", "?", e)] += PAS_S
    traci.close()
    return acc, pend


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarii", nargs="+", help="nume de scenarii din sumo/scenarios sau căi .sumocfg")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", help="CSV cu toate valorile (scenariu, categorie, detaliu, veh_h, pondere)")
    a = ap.parse_args()
    rows = []
    for name in a.scenarii:
        acc, pend = localize(name, a.seed)
        tot = sum(acc.values())
        print(f"\n=== {Path(name).stem}: {tot / 3600:.1f} vehicul-ore oprite sau neintroduse")
        for k, v in acc.most_common():
            print(f"{100 * v / tot:5.1f}%  {v / 3600:7.1f} veh-h  {k}")
            rows.append([Path(name).stem, k, "", round(v / 3600, 2), round(v / tot, 4)])
        for (strada, capat, e), v in pend.most_common(6):
            print(f"   neintroduse pe {strada} ({capat}, {e}): {100 * v / tot:5.1f}%")
        for (strada, capat, e), v in pend.most_common():
            rows.append([Path(name).stem, "neintroduse", f"{strada} | {capat} | {e}", round(v / 3600, 2), round(v / tot, 4)])
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["scenariu", "categorie", "detaliu", "veh_h", "pondere"])
            w.writerows(rows)
        print(f"\n→ {a.out}")


if __name__ == "__main__":
    main()
