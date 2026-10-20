"""Borna 1 – Construirea rețelei SUMO a zonei Piața Romană din OpenStreetMap.

Pași:
 1. `netconvert` decupează din extrasul OSM zona Piața Romană + intersecțiile conexe
    (Dacia × Eminescu/Dorobanți, Magheru × Enescu, Lascăr Catargiu × Gh. Manu,
    Dacia × Calea Victoriei, Dacia × Polonă).
 2. Nodurile interne ale pieței (≈30 de noduri OSM, cu segmente de 0,2–17 m) sunt unite
    într-un singur **nod agregat semaforizat** cu 4 brațe de intrare și 6 de ieșire.
    Motivare (verificată experimental, vezi docs/): în modelul OSM brut inelul intră în
    blocaj circular („gridlock”) chiar la cereri mici, deoarece vehiculele se opresc pe
    segmente interne de câțiva metri – artefact de import, nu comportament real.
 3. Semafoarele controlate primesc ID-uri lizibile (romana, dacia_eminescu, ...), găsite
    după coordonatele geografice din config/network.json.
 4. Programul semaforului Piața Romană este rescris cu 6 faze verzi cu semnificație de
    trafic (2 faze principale N–S / E–V + 4 faze exclusive pe braț) + galben automat.
 5. Se generează `tls_actuated.add.xml` (variante „actuated” SUMO, linie de bază).

Rulare:  python -m romana.network.build_network
Date OSM: © OpenStreetMap contributors, licență ODbL 1.0.
"""
from __future__ import annotations

import math
import subprocess
import xml.etree.ElementTree as ET

from romana.common import NET_DIR, ROOT, load_json, save_json, sumo_binary, sumo_home

NET_FILE = NET_DIR / "romana.net.xml"
RAW_FILE = NET_DIR / "_brut.net.xml"


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
        "--tls.default-type", "actuated", "--tls.cycle.time", str(cfg["default_cycle"]),
        "--tls.yellow.time", str(cfg["yellow_time"]),
        "--output.street-names", "--output.original-names",
        "--no-warnings",
        "-o", str(out_file),
    ]
    print("[netconvert] import OSM ...")
    subprocess.run(cmd, check=True)


def join_intersections(cfg: dict) -> dict[str, int]:
    """Unește nodurile interne ale fiecărei intersecții controlate într-un singur nod semaforizat."""
    import sumolib

    net = sumolib.net.readNet(str(RAW_FILE))
    root = ET.Element("nodes")
    used, counts = set(), {}
    for alias, c in cfg["tls"].items():
        if alias.startswith("_") or not c.get("raza_unire_m"):
            continue
        cx, cy = net.convertLonLat2XY(c["lon"], c["lat"])
        nodes = [nd.getID() for nd in net.getNodes()
                 if math.hypot(nd.getCoord()[0] - cx, nd.getCoord()[1] - cy) <= c["raza_unire_m"]
                 and nd.getID() not in used]
        used.update(nodes)
        counts[alias] = len(nodes)
        if len(nodes) > 1:
            ET.SubElement(root, "join", nodes=" ".join(nodes))
    join_file = NET_DIR / "_join.nod.xml"
    ET.ElementTree(root).write(join_file, encoding="UTF-8", xml_declaration=True)
    subprocess.run([sumo_binary("netconvert"), "-s", str(RAW_FILE), "--node-files", str(join_file),
                    "--tls.default-type", "actuated", "--no-warnings", "-o", str(NET_FILE)], check=True)
    join_file.unlink()
    RAW_FILE.unlink()
    return counts


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


def yellow_between(a: str, b: str) -> str:
    return "".join("y" if (x in "Gg" and y == "r") else x for x, y in zip(a, b))


def green_phases_of(tl: ET.Element) -> list[str]:
    out = []
    for p in tl.iter("phase"):
        s = p.get("state")
        if "y" not in s and any(ch in "Gg" for ch in s) and s not in out:
            out.append(s)
    return out


def rewrite_romana_program(net_path, cfg: dict) -> dict:
    tree = ET.parse(net_path)
    root = tree.getroot()
    appr = {k: v for k, v in cfg["romana_approaches"].items() if not k.startswith("_")}
    edge2arm = {v: k for k, v in appr.items()}
    n_links, link_arm = 0, {}
    for c in root.iter("connection"):
        if c.get("tl") == "romana":
            li = int(c.get("linkIndex"))
            n_links = max(n_links, li + 1)
            link_arm[li] = edge2arm.get(c.get("from"))
    missing = set(appr) - set(link_arm.values())
    if missing or None in link_arm.values():
        raise SystemExit(f"Brațele pieței nu corespund rețelei (lipsă: {missing}). Verificați romana_approaches.")
    tl = next(t for t in root.iter("tlLogic") if t.get("id") == "romana")
    generated = green_phases_of(tl)

    def arms_of(state):
        return frozenset(link_arm[i] for i, ch in enumerate(state) if ch in "Gg")

    greens = []
    for ph in cfg["romana_phases"]:
        want = frozenset(ph["brate"])
        if ph["tip"] == "permisiv":
            match = [g for g in generated if arms_of(g) == want]
            if not match:
                raise SystemExit(f"netconvert nu a generat o fază pentru {sorted(want)}")
            greens.append(match[0])
        else:
            greens.append("".join("G" if link_arm[i] in want else "r" for i in range(n_links)))
    fixed = [(s, ph["durata_fixa"]) for s, ph in zip(greens, cfg["romana_phases"]) if ph["durata_fixa"] > 0]
    for p in list(tl):
        if p.tag in ("phase", "param"):
            tl.remove(p)
    for i, (st, dur) in enumerate(fixed):
        nxt = fixed[(i + 1) % len(fixed)][0]
        tl.append(ET.Element("phase", duration=str(dur), state=st))
        tl.append(ET.Element("phase", duration=str(cfg["yellow_time"]), state=yellow_between(st, nxt)))
        tl.append(ET.Element("phase", duration="2", state="r" * n_links))   # roșu general (degajare)
    tl.set("type", "static")
    tl.set("offset", "0")
    ET.indent(tree)
    tree.write(net_path, encoding="UTF-8", xml_declaration=True)
    return {"n_links": n_links, "green_states": greens,
            "phase_names": [p["nume"] for p in cfg["romana_phases"]],
            "link_arm": [link_arm[i] for i in range(n_links)]}


def write_actuated(net_path, tls_ids, cfg: dict) -> None:
    """Variantă 'actuated' (prelungire verde pe goluri între vehicule) – linie de bază SUMO."""
    root = ET.parse(net_path).getroot()
    add = ET.Element("additional")
    for tl in root.iter("tlLogic"):
        if tl.get("id") not in tls_ids:
            continue
        greens = green_phases_of(tl)
        logic = ET.SubElement(add, "tlLogic", id=tl.get("id"), type="actuated", programID="actuated", offset="0")
        ET.SubElement(logic, "param", key="max-gap", value="3.0")
        ET.SubElement(logic, "param", key="detector-gap", value="2.0")
        for i, g in enumerate(greens):
            nxt = greens[(i + 1) % len(greens)]
            ET.SubElement(logic, "phase", duration="30", minDur="10", maxDur="60", state=g)
            ET.SubElement(logic, "phase", duration=str(cfg["yellow_time"]), state=yellow_between(g, nxt))
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
                     "semafoare": len(net.getTrafficLights()),
                     "dimensiune_m": [round(xmax - xmin), round(ymax - ymin)]}
    return out


def main() -> None:
    cfg = load_json("network.json")
    NET_DIR.mkdir(parents=True, exist_ok=True)
    run_netconvert(cfg, RAW_FILE)
    n_joined = join_intersections(cfg)
    mapping = rename_tls(NET_FILE, cfg["tls"])
    info = rewrite_romana_program(NET_FILE, cfg)
    tls_ids = [k for k in cfg["tls"] if not k.startswith("_")]
    info["noduri_unite"] = n_joined
    info["id_original_netconvert"] = mapping
    write_actuated(NET_FILE, tls_ids, cfg)
    info["rezumat"] = summary(NET_FILE, tls_ids)
    save_json(info, NET_DIR / "network_info.json")
    print(f"[OK] Rețea scrisă în {NET_FILE}; noduri OSM unite: {n_joined}")
    for k, v in info["rezumat"].items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
