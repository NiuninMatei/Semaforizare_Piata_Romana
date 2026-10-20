"""Utilitare comune: căi în proiect, configurații, localizarea SUMO."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
SUMO_DIR = ROOT / "sumo"
NET_DIR = SUMO_DIR / "net"
DEMAND_DIR = SUMO_DIR / "demand"
OUTPUT_DIR = ROOT / "outputs"
COUNTS_DIR = ROOT / "data" / "counts"
MODELS_DIR = ROOT / "models"


def load_json(name: str | Path) -> dict:
    p = Path(name)
    if not p.is_absolute():
        p = CONFIG_DIR / p
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def sumo_home() -> Path:
    """Găsește instalarea SUMO: variabila SUMO_HOME sau pachetul pip `eclipse-sumo`."""
    env = os.environ.get("SUMO_HOME")
    if env and Path(env).exists():
        return Path(env)
    try:
        import sumo  # pachetul pip eclipse-sumo

        os.environ["SUMO_HOME"] = sumo.SUMO_HOME
        return Path(sumo.SUMO_HOME)
    except ImportError:
        pass
    sys.exit(
        "SUMO nu a fost găsit. Instalați SUMO 1.28 (https://sumo.dlr.de) și setați SUMO_HOME "
        "sau rulați: pip install eclipse-sumo==1.28.0"
    )


def sumo_tools() -> Path:
    tools = sumo_home() / "tools"
    if str(tools) not in sys.path:
        sys.path.append(str(tools))
    return tools


def sumo_binary(name: str) -> str:
    """Calea către un executabil SUMO (sumo, sumo-gui, netconvert, duarouter...)."""
    home = sumo_home()
    for cand in (home / "bin" / name, home / "bin" / f"{name}.exe"):
        if cand.exists():
            return str(cand)
    found = shutil.which(name)
    if found:
        return found
    sys.exit(f"Executabilul SUMO '{name}' nu a fost găsit în {home / 'bin'}")
