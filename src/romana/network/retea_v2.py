"""Geamănul corectat (§ 6.5): rețeaua, fazele și tipurile de vehicule ale măsurii noi, construite din cele vechi, care rămân neatinse.

Străzile, benzile, trecerile și semafoarele sunt aceleași. Se schimbă, din `config/retea_v2.json`:
  - câteva legături între benzi, pe care OSM nu le spune și netconvert le-a ghicit;
  - cât de departe văd șoferii la legăturile care cedează trecerea;
  - momentele în care au verde trecerile de pietoni, măsurate din cameră;
  - tipurile de vehicule: `tau` egal cu pasul de simulare, ca să nu apară coliziuni, și distanța față de pietoni la care un șofer mai poate trece.

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
from romana.control.faze import SCURTA, fara_treceri, program_fix

NET_VECHI = NET_DIR / "romana.net.xml"
NET_V2 = NET_DIR / "romana_v2.net.xml"
INFO_V2 = NET_DIR / "network_info_v2.json"
ACTUATED_V2 = NET_DIR / "tls_actuated_v2.add.xml"
VEHICULE = ("passenger", "bus", "truck", "motorcycle")


def stari_v2(verzi: list[str], cfg: dict) -> list[str]:
    """Fazele verzi cu trecerile deschise și în etapa compatibilă, ca verde care se folosește printre vehiculele care virează („g”)."""
    out = list(verzi)
    for faza, e in cfg["treceri_in_etape"].items():
        s = list(out[int(faza)])
        for i in e["treceri"]:
            s[i] = "g"
        out[int(faza)] = "".join(s)
    return out


def pietoni_cfg(cfg: dict, stari: list[str]) -> dict:
    return {**{k: v for k, v in cfg["pietoni"].items() if k != "nume_faza_scurta"}, "nume_scurta": cfg["pietoni"]["nume_faza_scurta"],
            "stare_scurta": fara_treceri(stari[2], cfg["pietoni"]["treceri"])}     # etapa scurtă: ca etapa de pietoni, dar fără pietoni


def retea(cfg: dict, faze_fix: list[tuple[str, float]]) -> None:
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
    faze = "\n".join(f'    <phase duration="{d:g}" state="{s}"/>' for s, d in faze_fix)
    t, n = re.subn(r'(<tlLogic id="romana" type="static" programID="0" offset="0">\n).*?(\n\s*</tlLogic>)', lambda m: m.group(1) + faze + m.group(2), t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("Nu am găsit programul semaforului romana în rețea.")
    NET_V2.write_text(t, encoding="utf-8", newline="\n")
    adauga_notificare_osm(NET_V2)


def actuated(stari: list[str], pietoni: dict, galben: int) -> None:
    """Programul adaptat la trafic: etapele se lungesc doar în fereastra pietonilor, ca verdele lor să nu se termine pe neașteptate; a treia etapă e cea scurtă, ca la semaforul real."""
    add = ET.Element("additional")
    logic = ET.SubElement(add, "tlLogic", id="romana", type="actuated", programID="actuated", offset="0")
    ET.SubElement(logic, "param", key="max-gap", value="3.0")
    ET.SubElement(logic, "param", key="detector-gap", value="2.0")
    limite = {stari[0]: (10, 64), stari[1]: (10, 54)}        # până la 90 s pe N–S și 60 s pe E–V, cu tot cu fereastra de la capete
    for s, d in program_fix(stari, [(0, 36), (1, 28), (SCURTA, 3)], pietoni, galben):
        ET.SubElement(logic, "phase", duration=f"{d:g}", state=s, **({"minDur": str(limite[s][0]), "maxDur": str(limite[s][1])} if s in limite else {}))
    ET.indent(add)
    ET.ElementTree(add).write(ACTUATED_V2, encoding="UTF-8", xml_declaration=True)


def tipuri(cfg: dict) -> None:
    v = cfg["tipuri_vehicule"]

    def schimba(sursa: Path, tinta: str, nota: str) -> None:
        t = sursa.read_text(encoding="utf-8")

        def vtype(m: re.Match) -> str:
            s = m.group(0)
            if re.search(r'id="([^"]+)"', s).group(1) not in VEHICULE:
                return s
            s = re.sub(r'tau="[0-9.]+"', f'tau="{v["tau"]}"', s)
            return s.replace("<vType ", f'<vType jmCrossingGap="{v["jmCrossingGap"]}" ', 1)

        t = re.sub(r"<!--.*?-->\s*", "", t, flags=re.S)
        t = re.sub(r"<vType [^>]*>", vtype, t)
        t = t.replace("<additional>", f"<!-- {nota} -->\n<additional>", 1)
        (DEMAND_DIR / tinta).write_text(t, encoding="utf-8", newline="\n")

    nota = "Geamănul corectat (§ 6.5): tau egal cu pasul de simulare și jmCrossingGap ales pe cameră; restul, ca în vtypes.add.xml. Generat de romana.network.retea_v2."
    schimba(DEMAND_DIR / "vtypes.add.xml", v["fisier"], nota)
    schimba(DEMAND_DIR / "vtypes_indisciplinat.add.xml", v["fisier_indisciplinat"], nota)


def main() -> None:
    cfg = load_json("retea_v2.json")
    retea_cfg = load_json("network.json")
    info = json.loads((NET_DIR / "network_info.json").read_text(encoding="utf-8"))
    stari = stari_v2(info["green_states"], cfg)
    pietoni = pietoni_cfg(cfg, stari)
    etape = [(i, p["durata_fixa"]) for i, p in enumerate(retea_cfg["romana_faze"]) if p["durata_fixa"] > 0]
    retea(cfg, program_fix(stari, etape, pietoni, retea_cfg["yellow_time"]))
    actuated(stari, pietoni, retea_cfg["yellow_time"])
    tipuri(cfg)
    INFO_V2.write_text(json.dumps({**info, "green_states": stari, "pietoni": pietoni}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] {NET_V2.name}, {INFO_V2.name}, {ACTUATED_V2.name}, tipurile de vehicule; config: {CONFIG_DIR / 'retea_v2.json'}")


if __name__ == "__main__":
    main()
