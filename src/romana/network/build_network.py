"""Borna 1 – Construirea rețelei SUMO a zonei Piața Romană din OpenStreetMap.

Pași:
 1. `netconvert` decupează din extrasul OSM zona Piața Romană + intersecțiile conexe
    (Dacia × Eminescu/Dorobanți, Magheru × Enescu, Lascăr Catargiu × Gh. Manu,
    Dacia × Calea Victoriei, Dacia × Polonă) și unește semafoarele pieței într-un singur
    controler (`--tls.join`), exact cum funcționează automatul real al pieței.
 2. Semafoarele controlate primesc ID-uri lizibile (romana, dacia_eminescu, ...).
 3. Programul semaforului Piața Romană este rescris cu 4 faze verzi cu semnificație
    trafic (vezi config/network.json) + faze de galben generate automat.
 4. Se generează `tls_actuated.add.xml` (variante „actuated” SUMO, linie de bază).

Rulare:  python -m romana.network.build_network
Date OSM: © OpenStreetMap contributors, licență ODbL 1.0.
"""
from __future__ import annotations

import math
import subprocess
import xml.etree.ElementTree as ET

from romana.common import NET_DIR, ROOT, load_json, save_json, sumo_binary, sumo_home

NET_FILE = NET_DIR / "romana.net.xml"


def run_netconvert(cfg: dict, out_file) -> None:
    typemap = sumo_home() / "data" / "typemap"
    w, s, e, n = cfg["bbox_lon_lat"]
    cmd = [
        sumo_binary("netconvert"),
        "--osm-files", str(ROOT / cfg["osm_file"]),
        "--type-files", f"{typemap / 'osmNetconvert.typ.xml'},{typemap / 'osmNetconvertUrbanDe.typ.xml'}",
        "--keep-edges.in-geo-boundary", f"{w},{s},{e},{n}",
        "--keep-edges.by-vclass", "passenger,bus",
        "--remove-edges.by-type",
        "highway.service,highway.track,highway.living_street,highway.footway,highway.path,"
        "highway.cycleway,highway.steps,highway.pedestrian",
        "--keep-edges.components", "1",
        "--geometry.remove", "--roundabouts.guess", "--ramps.guess", "--junctions.join",
        "--tls.guess-signals", "--tls.join", "--tls.join-dist", "75",
        "--tls.default-type", "static", "--tls.cycle.time", str(cfg["default_cycle"]),
        "--tls.yellow.time", str(cfg["yellow_time"]),
        "--output.street-names", "--output.original-names",
        "--no-warnings",
        "-o", str(out_file),
    ]
    print("[netconvert]", " ".join(cmd[:3]), "...")
    subprocess.run(cmd, check=True)


def tls_centroids(net_path) -> dict[str, tuple[float, float]]:
    import sumolib

    net = sumolib.net.readNet(str(net_path), withPrograms=True)
    out = {}
    for tl in net.getTrafficLights():
        nodes = {c[0].getEdge().getToNode() for c in tl.getConnections()}
        xs = [n.getCoord()[0] for n in nodes]
        ys = [n.getCoord()[1] for n in nodes]
        lon, lat = net.convertXY2LonLat(sum(xs) / len(xs), sum(ys) / len(ys))
        out[tl.getID()] = (lat, lon)
    return out


def rename_tls(net_path, tls_cfg: dict, max_dist_m: float = 60.0) -> dict[str, str]:
    """Atribuie ID-uri lizibile semafoarelor, alegând controlerul cel mai apropiat de coordonatele din config."""
    cents = tls_centroids(net_path)
    mapping = {}
    for alias, info in tls_cfg.items():
        if alias.startswith("_"):
            continue
        best, dist = None, 1e9
        for tid, (lat, lon) in cents.items():
            d = math.hypot((lat - info["lat"]) * 111_320, (lon - info["lon"]) * 79_500)
            if d < dist and tid not in mapping.values():
                best, dist = tid, d
        if best is None or dist > max_dist_m:
            raise SystemExit(f"Nu am găsit semaforul {alias} lângă ({info['lat']}, {info['lon']}).")
        mapping[alias] = best
    text = net_path.read_text(encoding="utf-8")
    for alias, old in mapping.items():
        # doar referințele la controler (nu și ID-ul nodului, folosit de muchiile interne)
        text = text.replace(f'<tlLogic id="{old}"', f'<tlLogic id="{alias}"')
        text = text.replace(f'tl="{old}"', f'tl="{alias}"')
    net_path.write_text(text, encoding="utf-8")
    return mapping


def link_groups(net_root: ET.Element, groups: dict) -> tuple[int, dict[str, set[int]]]:
    """Returnează nr. de legături ale semaforului romana și indicii pe grupuri."""
    n_links = 0
    idx: dict[str, set[int]] = {g: set() for g in groups if not g.startswith("_")}
    for c in net_root.iter("connection"):
        if c.get("tl") != "romana":
            continue
        li = int(c.get("linkIndex"))
        n_links = max(n_links, li + 1)
        for g, edges in groups.items():
            if g.startswith("_"):
                continue
            if c.get("from") in edges:
                idx[g].add(li)
    for g, s in idx.items():
        if not s:
            raise SystemExit(f"Grupul {g} nu are nicio legătură – ID-urile din config/network.json nu corespund rețelei.")
    return n_links, idx


def phase_states(n_links: int, idx: dict[str, set[int]], phases_cfg: list[dict]) -> list[str]:
    states = []
    for ph in phases_cfg:
        st = ["G"] * n_links
        for g in ph["rosu"]:
            for i in idx[g]:
                st[i] = "r"
        for g in ph["verde"]:
            for i in idx[g]:
                st[i] = "G"
        states.append("".join(st))
    return states


def yellow_between(a: str, b: str) -> str:
    return "".join("y" if (x in "Gg" and y == "r") else x for x, y in zip(a, b))


def rewrite_romana_program(net_path, cfg: dict) -> dict:
    tree = ET.parse(net_path)
    root = tree.getroot()
    n_links, idx = link_groups(root, cfg["romana_groups"])
    greens = phase_states(n_links, idx, cfg["romana_phases"])
    fixed = [(s, ph["durata_fixa"]) for s, ph in zip(greens, cfg["romana_phases"]) if ph["durata_fixa"] > 0]
    tl = next(t for t in root.iter("tlLogic") if t.get("id") == "romana")
    for p in list(tl):
        if p.tag == "phase":
            tl.remove(p)
    insert_at = 0
    for i, (st, dur) in enumerate(fixed):
        nxt = fixed[(i + 1) % len(fixed)][0]
        for s, d in ((st, dur), (yellow_between(st, nxt), cfg["yellow_time"])):
            el = ET.Element("phase", duration=str(d), state=s)
            tl.insert(insert_at, el)
            insert_at += 1
    tl.set("type", "static")
    tl.set("offset", "0")
    ET.indent(tree)
    tree.write(net_path, encoding="UTF-8", xml_declaration=True)
    return {"n_links": n_links, "green_states": greens,
            "groups": {g: sorted(v) for g, v in idx.items()}}


def green_phases_of(tl: ET.Element) -> list[str]:
    out = []
    for p in tl.iter("phase"):
        s = p.get("state")
        if "y" not in s and any(ch in "Gg" for ch in s) and s not in out:
            out.append(s)
    return out


def write_actuated(net_path, tls_ids, yellow: int) -> None:
    """Variantă 'actuated' (prelungire verde pe goluri între vehicule) – linie de bază SUMO."""
    root = ET.parse(net_path).getroot()
    add = ET.Element("additional")
    for tl in root.iter("tlLogic"):
        if tl.get("id") not in tls_ids:
            continue
        greens = green_phases_of(tl)
        if tl.get("id") == "romana":
            greens = greens[:2]  # fazele de bază N–S / E–V
        logic = ET.SubElement(add, "tlLogic", id=tl.get("id"), type="actuated", programID="actuated", offset="0")
        ET.SubElement(logic, "param", key="max-gap", value="3.0")
        ET.SubElement(logic, "param", key="detector-gap", value="2.0")
        for i, g in enumerate(greens):
            nxt = greens[(i + 1) % len(greens)]
            ET.SubElement(logic, "phase", duration="30", minDur="10", maxDur="60", state=g)
            ET.SubElement(logic, "phase", duration=str(yellow), state=yellow_between(g, nxt))
    tree = ET.ElementTree(add)
    ET.indent(tree)
    tree.write(NET_DIR / "tls_actuated.add.xml", encoding="UTF-8", xml_declaration=True)


def summary(net_path, tls_ids) -> dict:
    import sumolib

    net = sumolib.net.readNet(str(net_path), withPrograms=True)
    out = {}
    for t in tls_ids:
        tl = net.getTLS(t)
        prog = list(tl.getPrograms().values())[0]
        out[t] = {"legaturi": len(tl.getConnections()), "faze": len(prog.getPhases()),
                  "benzi_intrare": len({c[0].getID() for c in tl.getConnections()})}
    xmin, ymin, xmax, ymax = net.getBoundary()
    out["_retea"] = {"muchii": len(net.getEdges()), "noduri": len(net.getNodes()),
                     "dimensiune_m": [round(xmax - xmin), round(ymax - ymin)]}
    return out


def main() -> None:
    cfg = load_json("network.json")
    NET_DIR.mkdir(parents=True, exist_ok=True)
    run_netconvert(cfg, NET_FILE)
    mapping = rename_tls(NET_FILE, cfg["tls"])
    info = rewrite_romana_program(NET_FILE, cfg)
    tls_ids = [k for k in cfg["tls"] if not k.startswith("_")]
    info["id_original_netconvert"] = mapping
    write_actuated(NET_FILE, tls_ids, cfg["yellow_time"])
    info["rezumat"] = summary(NET_FILE, tls_ids)
    save_json(info, NET_DIR / "network_info.json")
    print("[OK] Rețea scrisă în", NET_FILE)
    for k, v in info["rezumat"].items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
