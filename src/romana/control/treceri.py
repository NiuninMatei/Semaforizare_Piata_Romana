"""Verdele pe fiecare trecere de pietoni a semaforului pieței, pentru planuri fixe date (§ 9.10).

Pentru fiecare trecere comandată de controlerul `romana`: lungimea, fazele în care are verde (din
`sumo/net/network_info.json`, aceleași stări ca în simulare) și cel mai lung verde continuu pe ciclu. Fazele verzi
consecutive se leagă: între ele trecerea rămâne verde și pe tranziție (galben 3 s + roșu general 2 s, § 7.2).
Timpul de traversare se dă la 1,2 m/s și la 1,0 m/s (pietoni mai lenți), pentru comparație.

Exemplu:
  python -m romana.control.treceri --plan 12,14,12 --plan 36,28,12
"""
from __future__ import annotations

import argparse

from romana.common import SUMO_DIR
from romana.control.env import _import_libsumo
from romana.control.signals import romana_green_phases

TRANZITIE = 5   # galben 3 s + roșu general 2 s


def verde_continuu(stari: list[str], idx: int, durate: list[int]) -> int:
    """Cel mai lung verde continuu pe ciclu al legăturii `idx`, pentru fazele 0..n-1 rulate în ordine."""
    n = len(durate)
    on = [stari[p][idx] in "Gg" for p in range(n)]
    if all(on):
        return sum(durate) + n * TRANZITIE
    best = 0
    for s in range(n):
        if on[s] and not on[s - 1]:
            t, k = 0, s
            while on[k % n]:
                t += durate[k % n] + (TRANZITIE if on[(k + 1) % n] else 0)
                k += 1
            best = max(best, t)
    return best


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="append", required=True, help="duratele verzilor N–S,E–V,pietoni, ex. 12,14,12")
    ap.add_argument("--scenariu", default="zi_2026-10-28_varf", help="orice scenariu (doar pentru încărcarea rețelei)")
    args = ap.parse_args(argv)
    planuri = [[int(x) for x in p.split(",")] for p in args.plan]
    stari, nume = romana_green_phases()
    traci = _import_libsumo()
    traci.start(["sumo", "-c", str(SUMO_DIR / "scenarios" / f"{args.scenariu}.sumocfg"), "--no-step-log", "true",
                 "--no-warnings", "true", "--end", "1"])
    try:
        treceri = {}
        for idx, legaturi in enumerate(traci.trafficlight.getControlledLinks("romana")):
            for _, spre, _ in legaturi:
                ed = spre.rsplit("_", 1)[0]
                if spre.startswith(":") and "_c" in ed[ed.rfind("_"):] and ed not in treceri:
                    treceri[ed] = (traci.lane.getLength(spre), idx)
    finally:
        traci.close()
    print("fazele:", ", ".join(f"{i} = {n}" for i, n in enumerate(nume[:3])))
    cap = " ".join(f"{'verde ' + '/'.join(map(str, p)):>16s}" for p in planuri)
    print(f"{'trecerea':44s} {'L (m)':>6s} {'faze':>6s} {cap} {'L/1,2':>6s} {'L/1,0':>6s}")
    for ed, (L, idx) in sorted(treceri.items(), key=lambda r: -r[1][0]):
        faze = "+".join(str(p) for p in range(3) if stari[p][idx] in "Gg")
        verzi = " ".join(f"{verde_continuu(stari, idx, p):16d}" for p in planuri)
        print(f"{ed:44s} {L:6.1f} {faze:>6s} {verzi} {L / 1.2:6.1f} {L / 1.0:6.1f}")


if __name__ == "__main__":
    main()
