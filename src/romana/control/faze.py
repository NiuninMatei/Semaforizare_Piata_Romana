"""Fazele semaforului pieței pentru rețeaua încărcată în simulare: geamănul corectat are fișierul lui (§ 6.5)."""
from __future__ import annotations

import json

from romana.common import NET_DIR
from romana.control.signals import romana_green_phases


def faze_romana(tr) -> tuple[list[str], list[str]]:
    if str(tr.simulation.getOption("net-file")).endswith("_v2.net.xml"):
        info = json.loads((NET_DIR / "network_info_v2.json").read_text(encoding="utf-8"))
        return info["green_states"], info["phase_names"]
    return romana_green_phases()
