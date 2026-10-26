"""Capacitatea geamănului față de debitul observat (§ 6.4): baleiajul parametrilor de șofer.

Pentru un scenariu, cu planul fix actual și un seed, se măsoară câte vehicule trec pe fiecare intrare a pieței între
900 și 4 500 s (o oră, după încărcarea rețelei), câte au fost introduse și câte au rămas neintroduse la final
(blocaj: coada ajunge la marginea rețelei). Variantele schimbă doar parametrii modelului de șofer Krauss ai
vehiculelor motorizate – timpul de reacție `tau`, distanța minimă `minGap`, imperfecțiunea `sigma` – într-o copie
temporară a tipurilor de vehicule; rețeaua și cererea rămân aceleași.

Variantele se dau ca `nume=tau:minGap:sigma`; „standard” (tipurile din scenariu) se rulează mereu întâi.

Exemplu (tabelul din § 6.4):
  python -m romana.control.capacitate zi_2026-10-26_varf t10s0=1.0:2.5:0 t10g20=1.0:2.0:0.5 t09g25=0.9:2.5:0.5 ^
      t09g20=0.9:2.0:0.5 t08g25=0.8:2.5:0.5 t08g20=0.8:2.0:0.5 t08s3=0.8:2.0:0.3 --out outputs/capacitate.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import tempfile
from pathlib import Path

from romana.common import ROOT, load_json
from romana.control import controllers as C
from romana.control.env import start_sumo, traci

# numărătoarea de referință din 26.10, 16:00 (§ 4.3, § 4.6), vehicule/h pe intrare
REFERINTA = {"magheru": 3070, "catargiu": 1450, "dacia_vest": 1050, "dacia_est": 650}
MOTORIZATE = "passenger|bus|truck|motorcycle"


def variant_cfg(src: Path, spec: str, tmp: Path, name: str) -> Path:
    """Copia scenariului (căi absolute) cu tipurile de vehicule modificate după `tau:minGap:sigma`."""
    tau, mingap, sigma = spec.split(":")
    text = src.read_text(encoding="utf-8")
    add = re.search(r'<additional-files value="([^"]*)"', text).group(1).split(",")
    vt_src = (src.parent / add[0].strip()).resolve()
    vt = re.sub(rf'(<vType id="({MOTORIZATE})"[^/]*?)sigma="[^"]*"(\s+tau="[^"]*")?',
                rf'\1sigma="{sigma}" tau="{tau}" minGap="{mingap}"', vt_src.read_text(encoding="utf-8"))
    (tmp / f"vt_{name}.add.xml").write_text(vt, encoding="utf-8")
    text = text.replace('../', f'{(ROOT / "sumo").as_posix()}/')
    text = re.sub(r'(<additional-files value=")[^"]*"', rf'\1{(tmp / f"vt_{name}.add.xml").as_posix()}"', text)
    cfg = tmp / f"{src.stem}_{name}.sumocfg"
    cfg.write_text(text, encoding="utf-8")
    return cfg


def measure(cfg: Path, seed: int = 1) -> dict:
    arms = {a: b["intrare"] for a, b in load_json(ROOT / "config/demand.json")["brate"].items() if b["intrare"]}
    start_sumo(cfg, seed)
    C.FixedReference().reset(traci)
    seen = {a: set() for a in arms}
    inserted = 0
    for t in range(4500):
        traci.simulationStep()
        inserted += traci.simulation.getDepartedNumber()
        if t >= 900:
            for a, e in arms.items():
                seen[a].update(traci.edge.getLastStepVehicleIDs(e))
    pending = len(traci.simulation.getPendingVehicles())
    traci.close()
    return {"introduse": inserted, "neintroduse_final": pending, **{a: len(s) for a, s in seen.items()}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenariu", help="nume din sumo/scenarios sau cale .sumocfg")
    ap.add_argument("variante", nargs="*", help="nume=tau:minGap:sigma")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", help="CSV cu rezultatele (se adaugă la un fișier existent)")
    a = ap.parse_args()
    src = Path(a.scenariu) if a.scenariu.endswith(".sumocfg") else ROOT / "sumo/scenarios" / f"{a.scenariu}.sumocfg"
    tmp = Path(tempfile.mkdtemp(prefix="capacitate_"))
    rows = []
    for item in ["standard"] + a.variante:
        name, _, spec = item.partition("=")
        r = measure(variant_cfg(src, spec, tmp, name) if spec else src, a.seed)
        tot = sum(r[k] for k in REFERINTA)
        print(f"{src.stem} [{name} {spec}]: intrări {tot}/h (referința {sum(REFERINTA.values())}), introduse {r['introduse']}, "
              f"neintroduse la final {r['neintroduse_final']} | " + ", ".join(f"{k} {r[k]} ({v})" for k, v in REFERINTA.items()),
              flush=True)
        rows.append({"scenariu": src.stem, "varianta": name, "tau_mingap_sigma": spec or "din scenariu", **r})
    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        new = not out.exists()
        with open(out, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"→ {out}")


if __name__ == "__main__":
    main()
