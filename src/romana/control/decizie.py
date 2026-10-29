"""Regula „cel mai bun câștigă” (§ 9.9): alege, dintr-o listă de candidați fixată dinainte, strategia geamănului live.

Cazurile de trafic se definesc după debitul echilibrat al fiecărui scenariu, adică media dintre intrările și ieșirile
numărate de cameră, ca în `scenarii_zi` și ca în geamănul live: lejer sub 2 400 veh/h, intens peste 4 100 veh/h,
mediu între ele (pragurile vin din ziua de validare, luni 26.10). Programele pe cazuri se evaluează cu aceste benzi.

Câștigă candidatul cu cea mai mică pierdere totală de timp pe toate perechile (scenariu × seed, ambele comportamente),
dacă (a) e semnificativ mai bun decât strategia în vigoare (testul Wilcoxon bilateral pe perechi, p < 0,05, cu
diferența medie negativă) și (b) nu e semnificativ mai slab în niciun comportament luat separat. Dacă primii doi
candidați eligibili nu se deosebesc semnificativ (p ≥ 0,05), câștigă cel mai simplu de pus în practică: ordinea din
listă (planul fix, programul din planuri fixe, agentul). Fără niciun candidat eligibil, rămâne strategia în vigoare.
Cu --confirma X, pe o zi nouă se verifică doar dacă X e semnificativ mai slab decât strategia în vigoare.

Exemple:
  python -m romana.control.decizie outputs/validare/test_28_indisciplinat.csv outputs/validare/test_28_normal.csv
  python -m romana.control.decizie outputs/validare/test_29_*.csv --confirma TOD_DEBIT
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import pandas as pd
from scipy import stats

from romana.common import DEMAND_DIR
from romana.control.analiza import add_program, load_results, parse_program, pivot

PRAGURI = (2400.0, 4100.0)
PROGRAME = ["REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3",
            "TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12"]
CANDIDATI = ["PLAN_12_14_12", "TOD_DEBIT", "ppo_romana_cal"]   # de la cel mai simplu la cel mai complex
IN_VIGOARE = "REALIST"
VARIANTA_LIVE = {"PLAN_12_14_12": "plan_scurt", "TOD_DEBIT": "tod_debit", "ppo_romana_cal": "e13",
                 "REALIST": "realist"}
RE_SC = re.compile(r"zi_(\d{4}-\d{2}-\d{2})_(.+?)(?:_x(\d)_(\d))?$")


def debite(scenarii) -> dict[str, float]:
    """Debitul echilibrat (veh/h) al fiecărui scenariu: media profilului de 15 min pe fereastra lui, din rezumatul
    scris de `scenarii_zi`, înmulțită cu scara scenariilor de sensibilitate (×1,2 / ×0,8)."""
    rezumate, out = {}, {}
    for sc in scenarii:
        m = RE_SC.search(sc)
        if not m:
            raise ValueError(f"scenariu fără zi și fereastră în nume: {sc}")
        zi, fereastra, a, b = m.groups()
        if zi not in rezumate:
            rezumate[zi] = json.loads((DEMAND_DIR / f"zi_{zi}_rezumat.json").read_text(encoding="utf-8"))
        rez = rezumate[zi]
        t0, t1 = (pd.Timestamp(x) for x in rez["ferestre"][fereastra])
        prof = pd.Series({pd.Timestamp(k): float(v) for k, v in rez["profil"].items()})
        out[sc] = float(prof[(prof.index >= t0) & (prof.index < t1)].mean()) * (float(f"{a}.{b}") if a else 1.0)
    return out


def caz(debit: float, praguri=PRAGURI) -> str:
    return "lejer" if debit < praguri[0] else ("greu" if debit > praguri[1] else "moderat")


def benzi_analiza(cazuri: dict[str, str]) -> str:
    """Șirul --benzi pentru `romana.control.analiza`, cu numele exacte ale scenariilor (banda grea = restul)."""
    parti = [f"{b}=" + ",".join(sorted(s for s, c in cazuri.items() if c == b)) for b in ("lejer", "moderat")
             if any(c == b for c in cazuri.values())]
    return ";".join(parti + ["greu"])


def compara(a: pd.Series, b: pd.Series) -> dict:
    m = a.notna() & b.notna()
    a, b = a[m].astype(float), b[m].astype(float)
    d = a - b
    nz = d != 0
    p = float(stats.wilcoxon(a[nz], b[nz]).pvalue) if nz.sum() > 0 else 1.0
    return {"n": int(len(a)), "dif_medie_h": float(d.mean()), "dif_medie_pct": float(((a - b) / b * 100).mean()),
            "mai_bun": int((d < 0).sum()), "p_wilcoxon": p}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fisiere", nargs="+", help="CSV-urile testului (model, scenariu, seed, pierdere_h)")
    ap.add_argument("--praguri", nargs=2, type=float, default=list(PRAGURI), metavar=("LEJER", "INTENS"))
    ap.add_argument("--candidati", nargs="+", default=CANDIDATI)
    ap.add_argument("--in-vigoare", default=IN_VIGOARE)
    ap.add_argument("--program", action="append", default=None, help="implicit: REALIST și TOD_DEBIT")
    ap.add_argument("--confirma", help="pe o zi de confirmare: strategia aleasă înainte")
    ap.add_argument("--out", help="fișierul JSON cu decizia (implicit outputs/validare/decizie_<zi>.json)")
    args = ap.parse_args(argv)

    df = load_results(args.fisiere)
    q = debite(sorted(df["scenariu"].unique()))
    lipsa = [s for s, v in q.items() if not math.isfinite(v)]
    if lipsa:
        raise SystemExit(f"[decizie] fereastră fără debit în profil: {lipsa}")
    cazuri = {s: caz(v, args.praguri) for s, v in q.items()}
    benzi = benzi_analiza(cazuri)
    bands = [(b, [s for s, c in cazuri.items() if c == b]) for b in ("lejer", "moderat")] + [("greu", [])]
    p = pivot(df)
    for spec in args.program or PROGRAME:
        name, comp = parse_program(spec)
        p = add_program(p, name, comp, bands)
    ref = args.in_vigoare
    # toate strategiile comparate trebuie să aibă valori pe toate perechile: altfel totalurile s-ar aduna pe seturi
    # diferite de perechi și n-ar mai fi comparabile (un program primește NaN unde îi lipsește o componentă)
    necesare = [ref, *([args.confirma] if args.confirma else args.candidati)]
    lipsesc = [x for x in necesare if x not in p.columns or not p[x].notna().all()]
    if lipsesc:
        raise SystemExit(f"[decizie] valori lipsă pentru {lipsesc} (strategii sau componente de program nerulate)")
    indisc = p.index.get_level_values(0).str.contains("indisciplinat_")
    print(f"{p.index.get_level_values(0).nunique()} scenarii, {len(p)} perechi; praguri {args.praguri}")
    for s in sorted(q, key=q.get):
        print(f"  {s:48s} {q[s]:7.0f} veh/h → {cazuri[s]}")

    def evaluare(x: str) -> dict:
        r = {"strategie": x, "pierdere_totala_h": float(p[x].sum()), "fata_de_in_vigoare": compara(p[x], p[ref])}
        r["indisciplinati"] = compara(p.loc[indisc, x], p.loc[indisc, ref])
        r["disciplinati"] = compara(p.loc[~indisc, x], p.loc[~indisc, ref])
        return r

    rez = {"zi": sorted({RE_SC.search(s).group(1) for s in q}), "praguri": args.praguri, "in_vigoare": ref,
           "debite": {s: round(v) for s, v in q.items()}, "cazuri": cazuri, "benzi_analiza": benzi}
    if args.confirma:
        e = evaluare(args.confirma)
        g = e["fata_de_in_vigoare"]
        slab = g["p_wilcoxon"] < 0.05 and g["dif_medie_h"] > 0
        rez.update({"confirmare": e, "verdict": "neconfirmat: revenire la " + ref if slab else "confirmat"})
        print(f"\n{args.confirma} față de {ref}: {g['dif_medie_pct']:+.1f}% ({g['dif_medie_h']:+.2f} h/pereche), "
              f"mai bun în {g['mai_bun']}/{g['n']}, p Wilcoxon = {g['p_wilcoxon']:.6f} → {rez['verdict']}")
    else:
        evals = [evaluare(x) for x in args.candidati]
        print(f"\nîn vigoare: {ref}, pierdere totală {p[ref].sum():.1f} h")
        eligibili = []
        for e in evals:
            g, i, d = e["fata_de_in_vigoare"], e["indisciplinati"], e["disciplinati"]
            a_ok = g["dif_medie_h"] < 0 and g["p_wilcoxon"] < 0.05
            b_ok = not any(c["p_wilcoxon"] < 0.05 and c["dif_medie_h"] > 0 for c in (i, d))
            e["eligibil"] = bool(a_ok and b_ok)
            if e["eligibil"]:
                eligibili.append(e)
            # regula se uită la diferențele în ore; media schimbărilor relative pe perechi (în paranteză) dă aceeași
            # greutate scenariilor de noapte, cu pierderi aproape nule, și poate avea alt semn decât totalul
            e["dif_totala_pct"] = (e["pierdere_totala_h"] / p[ref].sum() - 1) * 100
            print(f"  {e['strategie']:16s} total {e['pierdere_totala_h']:8.1f} h ({e['dif_totala_pct']:+.1f}%) | "
                  f"față de {ref}: {g['dif_medie_h']:+.2f} h/pereche (medie relativă {g['dif_medie_pct']:+.1f}%), "
                  f"{g['mai_bun']}/{g['n']}, p = {g['p_wilcoxon']:.6f} | "
                  f"indisc. {i['dif_medie_h']:+.2f} h (p = {i['p_wilcoxon']:.4f}), "
                  f"disc. {d['dif_medie_h']:+.2f} h (p = {d['p_wilcoxon']:.4f}) → {'eligibil' if e['eligibil'] else 'nu'}")
        if not eligibili:
            castig, motiv = ref, "niciun candidat nu e semnificativ mai bun decât strategia în vigoare"
        else:
            eligibili.sort(key=lambda e: e["pierdere_totala_h"])
            castig, motiv = eligibili[0]["strategie"], "cea mai mică pierdere totală dintre candidații eligibili"
            if len(eligibili) > 1:
                a, b = eligibili[0]["strategie"], eligibili[1]["strategie"]
                t = compara(p[a], p[b])
                rez["primii_doi"] = {"a": a, "b": b, **t}
                if t["p_wilcoxon"] >= 0.05:
                    castig = min((a, b), key=args.candidati.index)
                    motiv = (f"{a} și {b} nu se deosebesc semnificativ (p = {t['p_wilcoxon']:.4f}): "
                             "câștigă cel mai simplu de pus în practică")
        rez.update({"candidati": evals, "castigator": castig, "motiv": motiv,
                    "varianta_live": VARIANTA_LIVE.get(castig, castig)})
        print(f"\ncâștigător: {castig} ({motiv}) → VARIANTA_PROGRAM = \"{rez['varianta_live']}\"")
    out = Path(args.out or f"outputs/validare/decizie_{'_'.join(rez['zi'])}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rez, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
