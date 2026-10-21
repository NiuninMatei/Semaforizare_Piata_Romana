"""Borna 3 – Transformarea numărătorilor camerei în cerere de trafic SUMO calibrată.

Flux:
  numărători CSV (data/counts) ──► matrice O–D pe intervale (od_estimation, Furness)
     ──► fișier de viraje `edgeRelation` (intrare braț → ieșire braț) pe intervale
     ──► routeSampler.py alege, dintr-un set mare de rute candidate realiste
         (drumuri minime de la marginea rețelei), rutele care reproduc exact virajele
     ──► + trafic de fond pe străzile conexe nemonitorizate (fracțiune explicită, opțională)
     ──► sumo/scenarios/<nume>.sumocfg

Astfel, prin Piața Romană circulă exact vehiculele văzute de cameră (pe brațe și
viraje), iar SUMO NU generează trafic aleator prin intersecția studiată.

Exemple:
  python -m romana.bridge.build_demand --profil referinta --nume referinta_varf
  python -m romana.bridge.build_demand --counts data/counts/numaratori_2026-10-21.csv \
         --de-la "2026-10-21 07:30" --pana-la "2026-10-21 08:30" --nume dimineata_2026-10-21
"""
from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from romana.bridge.od_estimation import estimate, load_counts, reference_profile, summarize
from romana.common import (COUNTS_DIR, DEMAND_DIR, NET_DIR, ROOT, SUMO_DIR, load_json, save_json,
                           sumo_binary, sumo_tools)

NET = NET_DIR / "romana.net.xml"
CANDIDATES = DEMAND_DIR / "candidate.rou.xml"
VTYPES = DEMAND_DIR / "vtypes.add.xml"
SCEN_DIR = SUMO_DIR / "scenarios"

VTYPE_DEFS = {
    "passenger": dict(vClass="passenger", length="4.6", accel="2.6", decel="4.5", sigma="0.5", maxSpeed="16.7", color="200,200,200"),
    "bus": dict(vClass="bus", length="12", accel="1.2", decel="4.0", sigma="0.4", maxSpeed="14", color="0,120,255", guiShape="bus"),
    "truck": dict(vClass="truck", length="9", accel="1.3", decel="4.0", sigma="0.5", maxSpeed="14", color="160,100,40", guiShape="truck"),
    "motorcycle": dict(vClass="motorcycle", length="2.2", accel="3.5", decel="6", sigma="0.5", maxSpeed="16.7", color="255,200,0", guiShape="motorcycle"),
    "bicycle": dict(vClass="bicycle", length="1.8", accel="1.2", decel="3", sigma="0.5", maxSpeed="6", color="0,200,0", guiShape="bicycle"),
    "pieton": dict(vClass="pedestrian", length="0.3", width="0.5", maxSpeed="1.4", speedDev="0.15", color="255,90,90", guiShape="pedestrian"),
}


def run(cmd: list[str], log: Path | None = None) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout + res.stderr
    if log:
        log.write_text(out, encoding="utf-8")
    if res.returncode != 0:
        print(out[-3000:])
        raise SystemExit(f"Comanda a eșuat: {' '.join(cmd[:3])}")
    return out


def write_vtypes() -> None:
    root = ET.Element("additional")
    for vid, attrs in VTYPE_DEFS.items():
        ET.SubElement(root, "vType", id=vid, **attrs)
    ET.indent(root)
    ET.ElementTree(root).write(VTYPES, encoding="UTF-8", xml_declaration=True)


def route_edges(route_file: Path):
    for _, el in ET.iterparse(route_file):
        if el.tag == "vehicle":
            r = el.find("route")
            if r is not None:
                yield el, r.get("edges").split()


def follow_street(net, edge_id: str, forward: bool, max_steps: int = 60) -> str:
    """Urmează strada (același nume) în amonte (forward=False) sau în aval, până unde își schimbă
    numele sau până la marginea rețelei; întoarce ultima muchie găsită."""
    e = net.getEdge(edge_id)
    seen = {edge_id}
    for _ in range(max_steps):
        if e.is_fringe() and len(seen) > 1:
            break
        nb = e.getOutgoing() if forward else e.getIncoming()
        nb = [x for x in nb if x.getID() not in seen and x.allows("passenger") and not x.getID().startswith(":")
              and x.getName() == e.getName()]
        if not nb:
            break
        e = max(nb, key=lambda x: (x.getPriority(), x.getLaneNumber()))
        seen.add(e.getID())
    return e.getID()


def candidates_file(vclass: str) -> Path:
    return CANDIDATES if vclass == "passenger" else DEMAND_DIR / f"candidate_{vclass}.rou.xml"


def build_candidates(cfg: dict, force: bool = False, vclass: str = "passenger") -> None:
    """Set de rute candidate: drumuri minime margine→margine + rute garantate pentru fiecare viraj."""
    target = candidates_file(vclass)
    if target.exists() and not force:
        return
    tools = sumo_tools()
    DEMAND_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DEMAND_DIR / "_tmp"
    tmp.mkdir(exist_ok=True)
    print(f"[cerere] generez rutele candidate pentru {vclass} (randomTrips + duarouter)...")
    run([sys.executable, str(tools / "randomTrips.py"), "-n", str(NET), "--fringe-factor", "200",
         "-p", "0.12" if vclass == "passenger" else "0.4", "-b", "0", "-e", "3600", "--min-distance", "300",
         "--validate", "--remove-loops", "--vehicle-class", vclass, "--vclass", vclass, "--seed", str(cfg["seed"]),
         "-o", str(tmp / "rt.trips.xml"), "-r", str(tmp / "rt.rou.xml")])
    import sumolib

    net = sumolib.net.readNet(str(NET))
    # rute garantate pentru fiecare pereche intrare→ieșire: pornesc de unde începe bulevardul brațului
    # de intrare și se termină unde se termină strada de ieșire (în limitele rețelei), trecând prin
    # intersecțiile vecine – nu chiar la linia de oprire a pieței, unde inserarea a sute de vehicule
    # pe o muchie de 30 m bloca intrarea în rețea
    arms = cfg["brate"]
    trips = ET.Element("routes")
    k = 0
    for o, oi in arms.items():
        if not oi["intrare"]:
            continue
        start = follow_street(net, oi["intrare"], forward=False)
        for d, di in arms.items():
            end = follow_street(net, di["iesire"], forward=True)
            for rep in range(3):
                ET.SubElement(trips, "trip", id=f"via_{o}_{d}_{rep}", depart=str(k), type=vclass, **{
                    "from": start, "to": end, "via": f"{oi['intrare']} {di['iesire']}", "departLane": "best"})
                k += 1
    ET.ElementTree(trips).write(tmp / "via.trips.xml", encoding="UTF-8", xml_declaration=True)
    run([sumo_binary("duarouter"), "-n", str(NET), "--route-files", str(tmp / "via.trips.xml"),
         "--additional-files", str(VTYPES),
         "-o", str(tmp / "via.rou.xml"), "--ignore-errors", "--no-warnings", "--repair"])
    # combinare + filtrare: fără rute care traversează piața de două ori
    entries = {a["intrare"] for a in arms.values() if a["intrare"]}
    major = ("highway.primary", "highway.secondary", "highway.tertiary", "highway.trunk")
    arterial = ("highway.primary", "highway.secondary", "highway.trunk")

    def realistic(edges: list[str], via: bool) -> bool:
        """Rute plauzibile: pornesc/se termină pe artere și nu circulă mult pe străzi rezidențiale.

        Rutele care traversează piața trebuie să pornească și să se termine pe bulevarde / străzi
        principale (primary / secondary): altfel routeSampler încărca câteva străzi terțiare de la
        marginea rețelei (Ion Câmpineanu, Occidentului, Alecu Russo) cu peste jumătate din vehicule."""
        if via or vclass != "passenger":   # rute garantate / biciclete: fără filtrul de artere
            return True
        objs = [net.getEdge(e) for e in edges]
        ends = arterial if any(e in entries for e in edges) else major
        if not (objs[0].getType().startswith(ends) and objs[-1].getType().startswith(ends)):
            return False
        tot = sum(o.getLength() for o in objs)
        minor = sum(o.getLength() for o in objs if not o.getType().startswith(major))
        return minor <= 0.15 * tot

    out = ET.Element("routes")
    n = 0
    for f in (tmp / "rt.rou.xml", tmp / "via.rou.xml"):
        for veh, edges in route_edges(f):
            if sum(e in entries for e in edges) > 1 or not realistic(edges, f.name.startswith("via")):
                continue
            v = ET.SubElement(out, "vehicle", id=f"c{n}", depart="0")
            ET.SubElement(v, "route", edges=" ".join(edges))
            n += 1
    ET.indent(out)
    ET.ElementTree(out).write(target, encoding="UTF-8", xml_declaration=True)
    print(f"[cerere] {n} rute candidate în {target.relative_to(ROOT)}")


def write_turn_file(recs: list[dict], cfg: dict, vtype: str, path: Path) -> int:
    arms = cfg["brate"]
    root = ET.Element("data")
    t, total = 0, 0
    for r in recs:
        share = r["pondere_clase"].get(vtype, 0.0)
        iv = ET.SubElement(root, "interval", id=f"i{t}", begin=str(t), end=str(t + r["durata_s"]))
        for i, o in enumerate(r["origini"]):
            for j, d in enumerate(r["destinatii"]):
                n = r["od_veh_h"][i][j] * share * r["durata_s"] / 3600
                cnt = int(n) + (1 if random.random() < n - int(n) else 0)  # rotunjire stocastică
                if cnt > 0:
                    ET.SubElement(iv, "edgeRelation", **{"from": arms[o]["intrare"], "to": arms[d]["iesire"],
                                                         "count": str(cnt)})
                    total += cnt
        t += r["durata_s"]
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="UTF-8", xml_declaration=True)
    return total


def background(recs: list[dict], cfg: dict, path: Path) -> int:
    """Trafic pe străzile conexe care nu trece prin piață (nemonitorizat → ipoteză explicită)."""
    frac = cfg.get("fond_fractiune", 0.0)
    dur = sum(r["durata_s"] for r in recs)
    total_obs = sum(sum(map(sum, r["od_veh_h"])) * r["durata_s"] / 3600 for r in recs)
    n = int(round(frac * total_obs))
    entries = {a["intrare"] for a in cfg["brate"].values() if a["intrare"]}
    exits = {a["iesire"] for a in cfg["brate"].values()}
    pool = [e for _, e in route_edges(CANDIDATES) if not (set(e) & (entries | exits))]
    root = ET.Element("routes")
    deps = sorted(random.uniform(0, dur) for _ in range(n)) if pool else []
    for i, t in enumerate(deps):
        v = ET.SubElement(root, "vehicle", id=f"fond_{i}", type="passenger", depart=f"{t:.1f}",
                          departLane="best", departSpeed="max")
        ET.SubElement(v, "route", edges=" ".join(random.choice(pool)))
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="UTF-8", xml_declaration=True)
    return len(deps)


def pedestrian_pool(cfg: dict) -> list[str]:
    """Trasee pietonale candidate (șiruri de muchii) care trec prin zona pieței (≤ 120 m de centru)."""
    cand = DEMAND_DIR / "candidate_pietoni.rou.xml"
    if not cand.exists():
        tmp = DEMAND_DIR / "_tmp"
        tmp.mkdir(exist_ok=True)
        print("[cerere] generez trasee candidate pentru pietoni ...")
        run([sys.executable, str(sumo_tools() / "randomTrips.py"), "-n", str(NET), "--pedestrians",
             "-p", "0.25", "-b", "0", "-e", "3600", "--min-distance", "150", "--max-distance", "900",
             "--seed", str(cfg["seed"]), "-o", str(tmp / "ped.trips.xml"), "-r", str(tmp / "ped.rou.xml")])
        import sumolib

        net = sumolib.net.readNet(str(NET))
        c = load_json("network.json")["tls"]["romana"]
        cx, cy = net.convertLonLat2XY(c["lon"], c["lat"])
        near = {e.getID() for e in net.getEdges()
                if min(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in e.getShape()) < 120}
        out = ET.Element("routes")
        k = 0
        for _, el in ET.iterparse(tmp / "ped.rou.xml"):
            if el.tag == "person":
                w = el.find("walk")
                if w is not None and set((w.get("edges") or "").split()) & near:
                    p = ET.SubElement(out, "person", id=f"p{k}", depart="0")
                    ET.SubElement(p, "walk", edges=w.get("edges"))
                    k += 1
        ET.indent(out)
        ET.ElementTree(out).write(cand, encoding="UTF-8", xml_declaration=True)
    return [el.find("walk").get("edges") for _, el in ET.iterparse(cand) if el.tag == "person"]


def pedestrians(recs: list[dict], cfg: dict, path: Path) -> int:
    """Pietonii care traversează zona pieței (trotuare + treceri), cu debitul observat pe cameră."""
    pool = pedestrian_pool(cfg)
    root = ET.Element("routes")
    t0, n = 0.0, 0
    for r in recs:
        rate = r.get("pietoni_h", cfg.get("profil_referinta", {}).get("pietoni_h", 0))
        cnt = int(round(rate * r["durata_s"] / 3600))
        for t in sorted(random.uniform(t0, t0 + r["durata_s"]) for _ in range(cnt)):
            p = ET.SubElement(root, "person", id=f"pieton_{n}", depart=f"{t:.1f}", type="pieton")
            ET.SubElement(p, "walk", edges=random.choice(pool))
            n += 1
        t0 += r["durata_s"]
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="UTF-8", xml_declaration=True)
    return n


def write_sumocfg(name: str, route_files: list[Path], dur: int) -> Path:
    SCEN_DIR.mkdir(parents=True, exist_ok=True)
    rel = lambda p: Path("..") / p.relative_to(SUMO_DIR)  # noqa: E731
    cfg = ET.Element("configuration")
    inp = ET.SubElement(cfg, "input")
    ET.SubElement(inp, "net-file", value=str(rel(NET)).replace("\\", "/"))
    ET.SubElement(inp, "route-files", value=",".join(str(rel(p)).replace("\\", "/") for p in route_files))
    ET.SubElement(inp, "additional-files", value=str(rel(VTYPES)).replace("\\", "/"))
    tm = ET.SubElement(cfg, "time")
    ET.SubElement(tm, "begin", value="0")
    ET.SubElement(tm, "end", value=str(dur + 900))
    proc = ET.SubElement(cfg, "processing")
    ET.SubElement(proc, "time-to-teleport", value="300")
    ET.SubElement(proc, "ignore-route-errors", value="true")
    rep = ET.SubElement(cfg, "report")
    ET.SubElement(rep, "no-step-log", value="true")
    ET.SubElement(rep, "duration-log.statistics", value="true")
    gui = ET.SubElement(cfg, "gui_only")
    ET.SubElement(gui, "gui-settings-file", value="../net/view.xml")
    path = SCEN_DIR / f"{name}.sumocfg"
    ET.indent(cfg)
    ET.ElementTree(cfg).write(path, encoding="UTF-8", xml_declaration=True)
    return path


def main(argv=None) -> None:
    cfg = load_json("demand.json")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--counts", nargs="*", help="fișiere CSV de numărători (implicit toate din data/counts)")
    ap.add_argument("--de-la", dest="start")
    ap.add_argument("--pana-la", dest="end")
    ap.add_argument("--profil", choices=["camera", "referinta"], default="camera")
    ap.add_argument("--nume", required=True, help="numele scenariului (fișier .sumocfg)")
    ap.add_argument("--fond", type=float, default=None, help="suprascrie fond_fractiune")
    ap.add_argument("--scala", type=float, default=1.0, help="multiplicator al volumelor (analize de sensibilitate)")
    ap.add_argument("--regenerare-candidate", action="store_true")
    args = ap.parse_args(argv)
    if args.fond is not None:
        cfg["fond_fractiune"] = args.fond
    random.seed(cfg["seed"])
    write_vtypes()
    build_candidates(cfg, force=args.regenerare_candidate)

    if args.profil == "referinta":
        recs = reference_profile(cfg)
    else:
        files = [Path(p) for p in args.counts] if args.counts else sorted(COUNTS_DIR.glob("numaratori_*.csv"))
        recs = estimate(load_counts(files, args.start, args.end), cfg)
    if args.scala != 1.0:
        for r in recs:
            r["od_veh_h"] = [[v * args.scala for v in row] for row in r["od_veh_h"]]
            r["intrari_veh_h"] = {k: v * args.scala for k, v in r.get("intrari_veh_h", {}).items()}
    dur = sum(r["durata_s"] for r in recs)
    out_dir = DEMAND_DIR / args.nume
    out_dir.mkdir(parents=True, exist_ok=True)
    save_json({"intervale": recs, "rezumat": summarize(recs)}, out_dir / "od_estimat.json")

    route_files, report = [], {"tipuri": {}}
    vtypes = sorted({k for r in recs for k, v in r["pondere_clase"].items() if v > 0})
    for vt in vtypes:
        tf = out_dir / f"viraje_{vt}.xml"
        n = write_turn_file(recs, cfg, vt, tf)
        if n == 0:
            continue
        rf = out_dir / f"{vt}.rou.xml"
        vclass = "bicycle" if vt == "bicycle" else "passenger"
        build_candidates(cfg, force=False, vclass=vclass)
        log = run([sys.executable, str(sumo_tools() / "routeSampler.py"), "-r", str(candidates_file(vclass)), "-t", str(tf),
                   "--turn-max-gap", "25", "-o", str(rf), "--prefix", f"{vt}_", "-a", f'type="{vt}" departLane="best"',
                   "--seed", str(cfg["seed"]), "--optimize", "full", "--mismatch-output", str(out_dir / f"mismatch_{vt}.xml")],
                  log=out_dir / f"routeSampler_{vt}.log")
        geh = re.findall(r"GEH<5 for ([\d.]+)%", log)
        report["tipuri"][vt] = {"viraje_tinta": n, "GEH<5_%": float(geh[-1]) if geh else None}
        route_files.append(rf)
    bg = out_dir / "fond.rou.xml"
    report["vehicule_fond"] = background(recs, cfg, bg)
    route_files.append(bg)
    pf = out_dir / "pietoni.rou.xml"
    report["pietoni"] = pedestrians(recs, cfg, pf)
    if report["pietoni"]:
        route_files.append(pf)
    sumocfg = write_sumocfg(args.nume, route_files, dur)
    report["sumocfg"] = str(sumocfg.relative_to(ROOT))
    report["rezumat_od"] = summarize(recs)
    save_json(report, out_dir / "raport_cerere.json")
    print(f"[OK] Scenariul '{args.nume}': {report['rezumat_od']['vehicule_total']} vehicule prin piață, "
          f"{report['vehicule_fond']} de fond, {report['pietoni']} pietoni → {sumocfg.relative_to(ROOT)}")
    for vt, r in report["tipuri"].items():
        print(f"   {vt}: {r['viraje_tinta']} viraje țintă, GEH<5 pentru {r['GEH<5_%']}% din relații")


if __name__ == "__main__":
    main()
