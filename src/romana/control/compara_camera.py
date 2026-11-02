"""Geamănul pus lângă cameră (§ 6.5): cu planul observat, trec tot atâtea vehicule pe ciclu, în aceleași momente ale ciclului?

Profilul din cameră vine din `romana.vision.program_real --profile`, înmulțit cu factorii de corecție ai măsurii noi. În geamăn se
numără, secundă cu secundă, vehiculele care părăsesc muchia dinaintea semaforului, pe fiecare intrare. Se folosește scenariul cu
aceeași oră, iar cele două cicluri se aliniază pe cea mai bună suprapunere.

Exemplu:
  python -m romana.control.compara_camera --zi 2026-10-26 --interval 15:00-16:00 --scenariu cor_zi_2026-10-26_varf --plan PLAN_71_40_12 \
      --out docs/rezultate/geaman_camera_2026-10-26.csv --figura docs/imagini/geaman_camera.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from romana.common import CONFIG_DIR, OUTPUT_DIR, ROOT
from romana.vision.program_real import BUCATI, CULORI, NUME

LINII = {"magheru": "668307642#1", "catargiu": "1320256482", "dacia_est": "232079775#2", "dacia_vest": "-778823268#2"}


def treceri_geaman(scenariu: str, plan: str, seed: int, sf: int = 3600, incalzire: int = 300) -> tuple[dict[str, np.ndarray], int, dict]:
    """Câte vehicule pleacă de la fiecare linie de oprire, pe secunde, și câte teleportări și ciocniri au fost."""
    from romana.control import evaluate as E
    from romana.control.validare import make_controller

    E.start_sumo(ROOT / "sumo" / "scenarios" / f"{scenariu}.sumocfg", seed)
    tr = E.traci
    ctrl = make_controller(plan)
    ctrl.reset(tr)
    prec = {b: set() for b in LINII}
    ev = {b: np.zeros(sf) for b in LINII}
    tele = cioc = 0
    for t in range(sf):
        if t % 5 == 0:
            ctrl.act(tr, t)
        tr.simulationStep()
        tele += tr.simulation.getStartingTeleportNumber()
        cioc += tr.simulation.getCollidingVehiclesNumber()
        if hasattr(ctrl, "tick"):
            ctrl.tick()
        for b, m in LINII.items():
            acum = set(tr.edge.getLastStepVehicleIDs(m))
            ev[b][t] = len(prec[b] - acum)
            prec[b] = acum
    tr.close()
    verde = [float(v) for v in plan.split("_")[1:]]
    return {b: v[incalzire:] for b, v in ev.items()}, int(sum(verde) + 5 * len(verde)), {"teleportari": tele, "ciocniri": cioc}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", required=True)
    ap.add_argument("--interval", required=True, help="un interval din fișierul de profile")
    ap.add_argument("--scenariu", required=True)
    ap.add_argument("--plan", required=True, help="PLAN_a_b_c, planul observat la acea oră")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--profile", default=None, help=f"implicit {OUTPUT_DIR / 'program_real'}/profile_<zi>.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--figura", default=None)
    a = ap.parse_args(argv)
    cale = Path(a.profile) if a.profile else OUTPUT_DIR / "program_real" / f"profile_{a.zi}.json"
    real = json.loads(cale.read_text(encoding="utf-8"))[a.interval]
    factori = json.loads((CONFIG_DIR / "demand_v2.json").read_text(encoding="utf-8"))["factor_corectie_detectie"]
    factor = {b: (v["zi"] if isinstance(v, dict) else v) for b, v in factori.items()}
    ev, T, stare = treceri_geaman(a.scenariu, a.plan, a.seed)
    randuri, curbe = [], {}
    Tr = real["ciclu_s"]
    for b in LINII:
        s = ev[b]
        h = np.bincount(np.arange(len(s)) % T, weights=s, minlength=T) / (len(s) / T)
        h5 = np.convolve(np.r_[h, h, h], np.ones(5) / 5, "same")[T:2 * T]
        r = np.array(real[b]) * factor[b]
        x = np.arange(T) / T * Tr
        rr = np.interp(x, np.arange(BUCATI) / BUCATI * Tr, np.convolve(np.r_[r, r, r], np.ones(3) / 3, "same")[BUCATI:2 * BUCATI])
        dec = int(np.argmax(np.fft.irfft(np.fft.rfft(h5) * np.conj(np.fft.rfft(rr)), T)))
        curbe[b] = (np.roll(rr, dec), h5)
        cam, gem = float(r.sum() * Tr / BUCATI), float(h.sum())
        randuri.append({"brat": b, "camera_veh_ciclu": round(cam, 1), "geaman_veh_ciclu": round(gem, 1), "camera_veh_h": round(cam / Tr * 3600), "geaman_veh_h": round(gem / T * 3600),
                        "camera_varf_veh_s": round(float(np.sort(rr)[-5:].mean()), 2), "geaman_varf_veh_s": round(float(np.sort(h5)[-5:].mean()), 2)})
    d = pd.DataFrame(randuri)
    print(f"{a.zi} {a.interval}, ciclul camerei {Tr:.0f} s; {a.scenariu}, {a.plan}, ciclu {T} s; {stare['teleportari']} teleportări, {stare['ciocniri']} ciocniri")
    print(d.to_string(index=False))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        d.to_csv(a.out, index=False)
    if a.figura:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axe = plt.subplots(2, 2, figsize=(10, 5), sharex=True)
        for ax, b in zip(axe.flat, LINII):
            cam, gem = curbe[b]
            ax.plot(np.arange(T), cam, color="#8a8984", linewidth=2, label="camera")
            ax.plot(np.arange(T), gem, color=CULORI[b], linewidth=2, label="geamănul corectat")
            ax.set_title(NUME[b], fontsize=10, loc="left")
            ax.set_ylim(bottom=0)
            ax.grid(axis="y", color="#e4e3df", linewidth=0.8)
            ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            ax.legend(frameon=False, fontsize=8, loc="upper right")
        for ax in axe[1]:
            ax.set_xlabel("secunde în ciclu")
        for ax in axe[:, 0]:
            ax.set_ylabel("vehicule pe secundă")
        fig.tight_layout()
        fig.savefig(a.figura, dpi=130)


if __name__ == "__main__":
    main()
