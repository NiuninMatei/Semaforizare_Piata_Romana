"""Borna 1 / Borna 8 – Replica fidelă a rețelei rutiere reale din zona Piața Romană.

Principiu: **infrastructura rămâne exact cea din realitate** (OpenStreetMap): inelul pieței,
axa centrală N–S, benzile și virajele marcate, sensurile unice, benzile dedicate, trotuarele,
trecerile de pietoni și pozițiile reale ale semafoarelor. Singurul lucru pe care proiectul îl
modifică este *modul în care semafoarele existente răspund traficului* – adică programul lor.

Pași:
 1. `netconvert` importă zona (2,2 × 1,6 km) cu trotuare, treceri de pietoni, acces biciclete,
    benzi de viraj și restricții pe benzi; fiecare semafor OSM devine semafor SUMO.
 2. Semafoarele fizice ale Pieței Romane (≈15 capete de semafor pe intrări, inel, axa
    centrală și trecerile de pietoni) sunt grupate într-un singur controler `romana`, ca un
    automat real de intersecție; vecinii rămân controlere separate.
 3. Programul controlerului `romana` este construit pe **grupuri de semnal** cu semnificație
    de trafic (config/network.json), iar trecerile de pietoni primesc verde automat în fazele
    în care niciun flux de vehicule verde nu le intersectează geometric (siguranță).
 4. Se generează `tls_actuated.add.xml` (variantă „actuated” SUMO pentru linia de bază).

Rulare:  python -m romana.network.build_network
Date OSM: © OpenStreetMap contributors, licență ODbL 1.0.
"""
from __future__ import annotations

import math
import subprocess
import xml.etree.ElementTree as ET

from romana.common import NET_DIR, ROOT, load_json, save_json, sumo_binary, sumo_home

NET_FILE = NET_DIR / "romana.net.xml"
TMP_FILE = NET_DIR / "_pas1.net.xml"


def netconvert_cmd(cfg: dict, out_file, extra: list[str]) -> list[str]:
    typemap = sumo_home() / "data" / "typemap"
    w, s, e, n = cfg["bbox_lon_lat"]
    types = ",".join(str(typemap / t) for t in ("osmNetconvert.typ.xml", "osmNetconvertUrbanDe.typ.xml",
                                                "osmNetconvertPedestrians.typ.xml", "osmNetconvertBicycle.typ.xml"))
    return [
        sumo_binary("netconvert"), "--osm-files", str(ROOT / cfg["osm_file"]), "--type-files", types,
        "--keep-edges.in-geo-boundary", f"{w},{s},{e},{n}",
        "--remove-edges.by-type", "highway.track,highway.raceway,highway.bridleway,railway.tram,"
                                  "railway.subway,railway.rail",
        "--keep-edges.components", "1",
        # participanți: trotuare (din OSM), treceri, acces biciclete, benzi de viraj și dedicate
        # (notă: --osm.crossings provoacă un crash în netconvert 1.28 pe acest extras;
        #  trecerile sunt reconstruite cu --crossings.guess la toate intersecțiile)
        "--osm.sidewalks", "--osm.bike-access", "--osm.turn-lanes", "--osm.lane-access",
        "--crossings.guess", "--walkingareas",
        # curățare standard a importului OSM (nu modifică topologia rutieră)
        "--geometry.remove", "--roundabouts.guess", "--ramps.guess", "--junctions.join",
        "--tls.guess-signals", "--tls.default-type", "actuated", "--tls.ignore-internal-junction-jam",
        "--tls.cycle.time", str(cfg["default_cycle"]), "--tls.yellow.time", str(cfg["yellow_time"]),
        "--output.street-names", "--output.original-names", "--no-warnings",
        "-o", str(out_file), *extra,
    ]


def tls_centroids(net_path) -> dict[str, tuple[float, float, int]]:
    import sumolib

    net = sumolib.net.readNet(str(net_path), withPrograms=True)
    out = {}
    for tl in net.getTrafficLights():
        nodes = {c[0].getEdge().getToNode() for c in tl.getConnections()}
        xs = [n.getCoord()[0] for n in nodes]
        ys = [n.getCoord()[1] for n in nodes]
        lon, lat = net.convertXY2LonLat(sum(xs) / len(xs), sum(ys) / len(ys))
        out[tl.getID()] = (lat, lon, len(tl.getConnections()))
    return out


def dist_m(a, b) -> float:
    return math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 79_500)


def build(cfg: dict) -> int:
    """Pasul 1: semafoare individuale; pasul 2: gruparea semafoarelor pieței într-un controler."""
    print("[netconvert] pasul 1: import OSM ...")
    subprocess.run(netconvert_cmd(cfg, TMP_FILE, []), check=True)
    c = cfg["tls"]["romana"]
    cents = tls_centroids(TMP_FILE)
    members = [t for t, v in cents.items() if dist_m(v, (c["lat"], c["lon"])) <= c["raza_grupare_m"]]
    others = [t for t in cents if t not in members]
    print(f"[netconvert] pasul 2: {len(members)} semafoare fizice grupate în controlerul Piața Romană ...")
    subprocess.run(netconvert_cmd(cfg, NET_FILE, ["--tls.join", "--tls.join-dist", "150",
                                                  "--tls.join-exclude", ",".join(others)]), check=True)
    TMP_FILE.unlink()
    return len(members)


def rename_tls(net_path, tls_cfg: dict) -> dict[str, str]:
    """ID-uri lizibile, alese după coordonatele din config (cel mai apropiat controler)."""
    cents = tls_centroids(net_path)
    mapping = {}
    for alias, info in tls_cfg.items():
        if alias.startswith("_"):
            continue
        cand = [(dist_m(v, (info["lat"], info["lon"])), t) for t, v in cents.items()
                if t not in mapping.values() and dist_m(v, (info["lat"], info["lon"])) <= info.get("raza_cautare_m", 60)]
        if not cand:
            raise SystemExit(f"Nu am găsit semaforul {alias} lângă ({info['lat']}, {info['lon']}).")
        mapping[alias] = min(cand)[1]
    text = net_path.read_text(encoding="utf-8")
    for alias, old in mapping.items():
        text = text.replace(f'<tlLogic id="{old}"', f'<tlLogic id="{alias}"')
        text = text.replace(f'tl="{old}"', f'tl="{alias}"')
    net_path.write_text(text, encoding="utf-8")
    return mapping


# ---------------------------------------------------------------- geometrie (conflicte)
def _seg_intersect(p1, p2, p3, p4) -> bool:
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def polylines_cross(a, b) -> bool:
    return any(_seg_intersect(a[i], a[i + 1], b[j], b[j + 1])
               for i in range(len(a) - 1) for j in range(len(b) - 1))


def tls_links(root: ET.Element, tl_id: str) -> dict[int, dict]:
    """Legăturile semaforului: tip (vehicul/pieton), muchia de proveniență și forma traseului."""
    shapes = {}
    for e in root.iter("edge"):
        for ln in e.iter("lane"):
            shapes[ln.get("id")] = [tuple(map(float, p.split(","))) for p in ln.get("shape").split()]
    nxt = {f"{c.get('from')}_{c.get('fromLane')}": c.get("via")
           for c in root.iter("connection") if c.get("from", "").startswith(":") and c.get("via")}
    links = {}
    for c in root.iter("connection"):
        if c.get("tl") != tl_id:
            continue
        i = int(c.get("linkIndex"))
        if c.get("from").startswith(":"):                 # trecere de pietoni
            links[i] = {"tip": "pieton", "from": c.get("to"), "shape": shapes[f"{c.get('to')}_0"]}
        else:
            v = c.get("via")
            sh = list(shapes[v])
            while v in nxt:
                v = nxt[v]
                sh += shapes[v][1:]
            links[i] = {"tip": "vehicul", "from": c.get("from"), "shape": sh}
    return links


def yellow_between(a: str, b: str) -> str:
    return "".join("y" if (x in "Gg" and y == "r") else x for x, y in zip(a, b))


def all_red_between(a: str, b: str) -> str:
    return "".join(x if (x in "Gg" and y in "Gg") else "r" for x, y in zip(a, b))


def design_romana_program(net_path, cfg: dict) -> dict:
    tree = ET.parse(net_path)
    root = tree.getroot()
    links = tls_links(root, "romana")
    n = max(links) + 1
    groups = {g: set(v) for g, v in cfg["romana_grupuri"].items() if not g.startswith("_")}
    link_group = {}
    for i, lk in links.items():
        if lk["tip"] == "pieton":
            link_group[i] = "pietoni"
            continue
        g = [k for k, edges in groups.items() if lk["from"] in edges]
        link_group[i] = g[0] if g else None
    unknown = sorted({links[i]["from"] for i, g in link_group.items() if g is None})
    if unknown:
        raise SystemExit(f"Muchii ale semaforului romana fără grup în config/network.json: {unknown}")
    ped = [i for i, g in link_group.items() if g == "pietoni"]
    greens, names, ped_ok = [], [], set()
    for ph in cfg["romana_faze"]:
        veh = {i for i, g in link_group.items() if g in ph["verde"]}
        st = ["G" if i in veh else "r" for i in range(n)]
        for p in ped:   # trecerea primește verde doar dacă niciun vehicul cu verde nu o traversează
            if not any(polylines_cross(links[p]["shape"], links[v]["shape"]) for v in veh):
                st[p] = "G"
                ped_ok.add(p)
        greens.append("".join(st))
        names.append(ph["nume"])
    never = [links[p]["from"] for p in ped if p not in ped_ok]
    if never:
        raise SystemExit(f"Treceri de pietoni care nu primesc niciodată verde: {never}")
    fixed = [(s, ph["durata_fixa"]) for s, ph in zip(greens, cfg["romana_faze"]) if ph["durata_fixa"] > 0]
    tl = next(t for t in root.iter("tlLogic") if t.get("id") == "romana")
    for p in list(tl):
        tl.remove(p)
    for k, (st, dur) in enumerate(fixed):
        nx = fixed[(k + 1) % len(fixed)][0]
        tl.append(ET.Element("phase", duration=str(dur), state=st))
        tl.append(ET.Element("phase", duration=str(cfg["yellow_time"]), state=yellow_between(st, nx)))
        tl.append(ET.Element("phase", duration="2", state=all_red_between(st, nx)))
    tl.set("type", "static")
    tl.set("offset", "0")
    ET.indent(tree)
    tree.write(net_path, encoding="UTF-8", xml_declaration=True)
    return {"n_links": n, "green_states": greens, "phase_names": names,
            "link_group": [link_group[i] for i in range(n)],
            "link_from": [links[i]["from"] for i in range(n)],
            "treceri_pietoni": len(ped)}


def write_actuated(cfg: dict, info: dict) -> None:
    """Variantă 'actuated' a controlerului Piața Romană (linie de bază SUMO), pe fazele planului fix.

    Fazele verzi se iau din programul proiectat (nu din tlLogic-ul rețelei, unde stările de roșu
    general păstrează verdele ieșirilor și ar fi confundate cu faze verzi)."""
    add = ET.Element("additional")
    greens = [g for g, ph in zip(info["green_states"], cfg["romana_faze"]) if ph["durata_fixa"] > 0]
    durs = [ph["durata_fixa"] for ph in cfg["romana_faze"] if ph["durata_fixa"] > 0]
    logic = ET.SubElement(add, "tlLogic", id="romana", type="actuated", programID="actuated", offset="0")
    ET.SubElement(logic, "param", key="max-gap", value="3.0")
    ET.SubElement(logic, "param", key="detector-gap", value="2.0")
    for i, (g, d) in enumerate(zip(greens, durs)):
        nx = greens[(i + 1) % len(greens)]
        ET.SubElement(logic, "phase", duration=str(d), minDur=str(min(10, d)), maxDur=str(max(d, 60)), state=g)
        ET.SubElement(logic, "phase", duration=str(cfg["yellow_time"]), state=yellow_between(g, nx))
        ET.SubElement(logic, "phase", duration="2", state=all_red_between(g, nx))
    tree = ET.ElementTree(add)
    ET.indent(tree)
    tree.write(NET_DIR / "tls_actuated.add.xml", encoding="UTF-8", xml_declaration=True)


def summary(net_path, tls_ids) -> dict:
    import sumolib

    net = sumolib.net.readNet(str(net_path), withPrograms=True, withPedestrianConnections=True)
    out = {}
    for t in tls_ids:
        tl = net.getTLS(t)
        prog = list(tl.getPrograms().values())[0]
        out[t] = {"legaturi": len(tl.getConnections()), "faze": len(prog.getPhases())}
    xmin, ymin, xmax, ymax = net.getBoundary()
    edges = net.getEdges()
    out["_retea"] = {"muchii": len(edges), "noduri": len(net.getNodes()),
                     "semafoare": len(net.getTrafficLights()),
                     "muchii_cu_trotuar": sum(1 for e in edges if any(l.allows("pedestrian") for l in e.getLanes())
                                              and e.getLaneNumber() > 1),
                     "muchii_biciclete": sum(1 for e in edges if any(l.allows("bicycle") for l in e.getLanes())),
                     "benzi_dedicate_bus": sum(1 for e in edges for l in e.getLanes()
                                               if l.allows("bus") and not l.allows("passenger")),
                     "dimensiune_m": [round(xmax - xmin), round(ymax - ymin)]}
    return out


def main() -> None:
    cfg = load_json("network.json")
    NET_DIR.mkdir(parents=True, exist_ok=True)
    n_members = build(cfg)
    mapping = rename_tls(NET_FILE, cfg["tls"])
    info = design_romana_program(NET_FILE, cfg)
    tls_ids = [k for k in cfg["tls"] if not k.startswith("_")]
    info["semafoare_fizice_piata"] = n_members
    info["id_original_netconvert"] = mapping
    write_actuated(cfg, info)
    info["rezumat"] = summary(NET_FILE, tls_ids)
    save_json(info, NET_DIR / "network_info.json")
    print(f"[OK] Rețea fidelă scrisă în {NET_FILE}")
    for k, v in info["rezumat"].items():
        print(f"   {k}: {v}")
    for nm, st in zip(info["phase_names"], info["green_states"]):
        print(f"   {st}  {nm}")


if __name__ == "__main__":
    main()
