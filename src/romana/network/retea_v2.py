"""Geamănul corectat (§ 6.5): rețeaua, fazele și tipurile de vehicule ale măsurii noi, construite din cele vechi, care rămân neatinse.

Străzile, benzile, trecerile și semafoarele sunt aceleași. Se schimbă, din `config/retea_v2.json`:
  - câteva legături între benzi, pe care OSM nu le spune și netconvert le-a ghicit;
  - cât de departe văd șoferii la legăturile care cedează trecerea;
  - etapele în care au verde trecerile de pietoni de pe ieșiri, cu vehiculele care virează cedând trecerea;
  - tipurile de vehicule: `tau` egal cu pasul de simulare, ca să nu apară coliziuni, distanța minimă și imperfecțiunea, calibrate pe cameră.

Scrie, lângă cele vechi: sumo/net/romana_v2.net.xml, network_info_v2.json, tls_actuated_v2.add.xml, sumo/demand/vtypes_v2.add.xml, vtypes_indisciplinat_v2.add.xml.

Rulare:  python -m romana.network.retea_v2
"""
from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from romana.atribuire_osm import adauga_notificare_osm
from romana.common import CONFIG_DIR, DEMAND_DIR, NET_DIR, load_json, sumo_binary
from romana.control.signals import all_red_between, yellow_between

NET_VECHI = NET_DIR / "romana.net.xml"
NET_V2 = NET_DIR / "romana_v2.net.xml"
INFO_V2 = NET_DIR / "network_info_v2.json"
ACTUATED_V2 = NET_DIR / "tls_actuated_v2.add.xml"
VEHICULE = ("passenger", "bus", "truck", "motorcycle")


def stari_v2(verzi: list[str], cfg: dict) -> list[str]:
    """Fazele verzi cu trecerile deschise în etapa lor, iar vehiculele care le taie cedând trecerea („g”)."""
    out = list(verzi)
    for faza, e in cfg["treceri_in_etape"].items():
        s = list(out[int(faza)])
        for i in e["treceri"]:
            s[i] = "G"
        for i in e["cedeaza"]:
            s[i] = "g"
        out[int(faza)] = "".join(s)
    return out


def program(stari: list[str], durate: list[int], galben: int, actuated: bool = False) -> list[dict]:
    """Fazele planului, cu tranzițiile sigure: galben, apoi roșu de degajare."""
    faze = []
    for k, (g, d) in enumerate(zip(stari, durate)):
        urm = stari[(k + 1) % len(stari)]
        faze.append({"duration": str(d), **({"minDur": str(min(10, d)), "maxDur": str(max(d, 60))} if actuated else {}), "state": g})
        faze.append({"duration": str(galben), "state": yellow_between(g, urm)})
        faze.append({"duration": "2", "state": all_red_between(g, urm)})
    return faze


def retea(cfg: dict, stari: list[str], durate: list[int], galben: int) -> None:
    con = ET.Element("connections")
    for d in cfg["legaturi_sterse"]:
        ET.SubElement(con, "delete", **d)
    for c in cfg["legaturi_noi"]:
        ET.SubElement(con, "connection", **c)
    fis = NET_DIR / "_legaturi_v2.con.xml"
    ET.ElementTree(con).write(fis, encoding="UTF-8", xml_declaration=True)
    subprocess.run([sumo_binary("netconvert"), "-s", str(NET_VECHI), "--connection-files", str(fis), "-o", str(NET_V2), "--no-warnings", "true"], check=True, capture_output=True)
    fis.unlink()
    t = NET_V2.read_text(encoding="utf-8")
    viz = cfg["vizibilitate_m"]

    def vizibil(m: re.Match) -> str:
        s = m.group(0)
        if 'via="' not in s or "visibility" in s or not ('state="m"' in s or 'tl="romana"' in s):
            return s                       # la legăturile cu semafor, cele care cedează trecerea se schimbă după fază
        return re.sub(r'state="(\w)"', lambda g: f'{g.group(0)} visibility="{viz}"', s)

    t = re.sub(r"<connection [^>]*/>", vizibil, t)
    faze = "\n".join("    <phase " + " ".join(f'{k}="{v}"' for k, v in f.items()) + "/>" for f in program(stari, durate, galben))
    t, n = re.subn(r'(<tlLogic id="romana" type="static" programID="0" offset="0">\n).*?(\n\s*</tlLogic>)', lambda m: m.group(1) + faze + m.group(2), t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("Nu am găsit programul semaforului romana în rețea.")
    NET_V2.write_text(t, encoding="utf-8", newline="\n")
    adauga_notificare_osm(NET_V2)


def actuated(stari: list[str], durate: list[int], galben: int) -> None:
    add = ET.Element("additional")
    logic = ET.SubElement(add, "tlLogic", id="romana", type="actuated", programID="actuated", offset="0")
    ET.SubElement(logic, "param", key="max-gap", value="3.0")
    ET.SubElement(logic, "param", key="detector-gap", value="2.0")
    for f in program(stari, durate, galben, actuated=True):
        ET.SubElement(logic, "phase", **f)
    ET.indent(add)
    ET.ElementTree(add).write(ACTUATED_V2, encoding="UTF-8", xml_declaration=True)


def tipuri(cfg: dict) -> None:
    v = cfg["tipuri_vehicule"]

    def schimba(sursa: Path, tinta: str, sigma: str, nota: str) -> None:
        t = sursa.read_text(encoding="utf-8")

        def vtype(m: re.Match) -> str:
            s = m.group(0)
            if re.search(r'id="([^"]+)"', s).group(1) not in VEHICULE:
                return s
            s = re.sub(r'tau="[0-9.]+"', f'tau="{v["tau"]}"', s)
            s = re.sub(r'sigma="[0-9.]+"', f'sigma="{sigma}"', s)
            return s.replace("<vType ", f'<vType minGap="{v["minGap"]}" jmCrossingGap="{v["jmCrossingGap"]}" lcKeepRight="{v["lcKeepRight"]}" ', 1)

        t = re.sub(r"<vType [^>]*>", vtype, t)
        t = t.replace("<additional>", f"<!-- {nota} -->\n<additional>", 1)
        (DEMAND_DIR / tinta).write_text(t, encoding="utf-8", newline="\n")

    nota = "Geamănul corectat (§ 6.5): tau egal cu pasul de simulare, distanța minimă și imperfecțiunea calibrate pe debitul de descărcare din cameră. Generat de romana.network.retea_v2."
    schimba(DEMAND_DIR / "vtypes.add.xml", v["fisier"], v["sigma"], nota)
    schimba(DEMAND_DIR / "vtypes_indisciplinat.add.xml", v["fisier_indisciplinat"], v["sigma_indisciplinat"], nota)


def main() -> None:
    cfg = load_json("retea_v2.json")
    retea_cfg = load_json("network.json")
    info = json.loads((NET_DIR / "network_info.json").read_text(encoding="utf-8"))
    stari = stari_v2(info["green_states"], cfg)
    fixe = [i for i, p in enumerate(retea_cfg["romana_faze"]) if p["durata_fixa"] > 0]
    durate = [retea_cfg["romana_faze"][i]["durata_fixa"] for i in fixe]
    plan = [stari[i] for i in fixe]
    retea(cfg, plan, durate, retea_cfg["yellow_time"])
    actuated(plan, durate, retea_cfg["yellow_time"])
    tipuri(cfg)
    INFO_V2.write_text(json.dumps({**info, "green_states": stari}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] {NET_V2.name}, {INFO_V2.name}, {ACTUATED_V2.name}, tipurile de vehicule; config: {CONFIG_DIR / 'retea_v2.json'}")


if __name__ == "__main__":
    main()
