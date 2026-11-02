"""Regula „cel mai bun câștigă” (§ 9.9): alege, dintr-o listă de candidați fixată dinainte, strategia geamănului live.

Cazurile de trafic se definesc după debitul echilibrat al fiecărui scenariu, adică media dintre intrările și ieșirile
numărate de cameră, ca în `scenarii_zi` și ca în geamănul live: lejer sub 2 400 veh/h, intens peste 4 100 veh/h,
mediu între ele (pragurile vin din ziua de validare, luni 26.10). Programele pe cazuri se evaluează cu aceste benzi.

Câștigă candidatul cu cea mai mică pierdere totală de timp pe toate perechile (scenariu × seed, ambele comportamente),
dacă (a) e semnificativ mai bun decât strategia în vigoare (testul Wilcoxon bilateral pe perechi, p < 0,05, cu
diferența medie în ore pe pereche negativă, adică pierderea totală mai mică) și (b) nu e semnificativ mai slab în
niciun comportament luat separat (aceeași măsură, în ore). Media schimbărilor relative pe perechi se afișează doar
informativ: ea dă scenariilor de noapte, cu pierderi aproape nule, aceeași greutate ca vârfului. Dacă primii doi
candidați eligibili nu se deosebesc semnificativ (p ≥ 0,05), câștigă cel mai simplu de pus în practică: ordinea din
listă (planul fix, programul din planuri fixe, agentul). Fără niciun candidat eligibil, rămâne strategia în vigoare.
Cu --confirma X, pe o zi nouă se verifică doar dacă X e semnificativ mai slab decât strategia în vigoare.

Cu mai multe referințe (`--in-vigoare PLAN_72_48_3 REAL`, regula din § 9.11), condițiile (a) și (b) se cer față de fiecare; dacă nu trece
nimeni, rămâne prima. Semaforul rejucat, REAL, se compară doar pe orele unde cel puțin `--acoperire-minima` din oră vine din valuri
măsurate: în rest e în cea mai mare parte presupus și nu i se spune „semaforul real”.

Cu `--poarta F` (scris de `valideaza_geaman --poarta`), orele la care geamănul nu trece poarta din § 9.11 nu intră în decizie, nici variantele lor ×0,8 și ×1,2. Dacă trec sub jumătate din ore, ziua rămâne
descriptivă: nu se poate schimba nimic, oricât de bine ar ieși un candidat.

Exemple:
  python -m romana.control.decizie outputs/validare/test_28_indisciplinat.csv outputs/validare/test_28_normal.csv
  python -m romana.control.decizie outputs/validare/test_29_*.csv --confirma TOD_DEBIT
  python -m romana.control.decizie outputs/validare/test_05_*.csv --in-vigoare PLAN_72_48_3 REAL --candidati PLAN_60_40_3 ACTUATED
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
RE_SC = re.compile(r"(?P<masura>cor_)?zi_(?P<zi>\d{4}-\d{2}-\d{2})_(?P<fereastra>.+?)(?:_x(?P<a>\d)_(?P<b>\d))?$")


def debite(scenarii) -> dict[str, float]:
    """Debitul echilibrat (veh/h) al fiecărui scenariu: media profilului de 15 min pe fereastra lui, din rezumatul
    măsurii lui, scris de `scenarii_zi`, înmulțită cu scara scenariilor de sensibilitate (×1,2 / ×0,8). Scenariile unei
    decizii vin dintr-o singură măsură (§ 9.11)."""
    rezumate, out = {}, {}
    for sc in scenarii:
        m = RE_SC.search(sc)
        if not m:
            raise ValueError(f"scenariu fără zi și fereastră în nume: {sc}")
        nume, a, b = f"{m['masura'] or ''}zi_{m['zi']}", m["a"], m["b"]
        if nume not in rezumate:
            rezumate[nume] = json.loads((DEMAND_DIR / f"{nume}_rezumat.json").read_text(encoding="utf-8"))
        rez = rezumate[nume]
        t0, t1 = (pd.Timestamp(x) for x in rez["ferestre"][m["fereastra"]])
        prof = pd.Series({pd.Timestamp(k): float(v) for k, v in rez["profil"].items()})
        out[sc] = float(prof[(prof.index >= t0) & (prof.index < t1)].mean()) * (float(f"{a}.{b}") if a else 1.0)
    if len({n.startswith("cor_") for n in rezumate}) > 1:
        raise ValueError("scenarii din măsuri diferite: rezultatele nu se adună (§ 9.11)")
    return out


def caz(debit: float, praguri=PRAGURI) -> str:
    return "lejer" if debit < praguri[0] else ("greu" if debit > praguri[1] else "moderat")


def benzi_analiza(cazuri: dict[str, str]) -> str:
    """Șirul --benzi pentru `romana.control.analiza`, cu numele exacte ale scenariilor (banda grea = restul)."""
    parti = [f"{b}=" + ",".join(sorted(s for s, c in cazuri.items() if c == b)) for b in ("lejer", "moderat")
             if any(c == b for c in cazuri.values())]
    return ";".join(parti + ["greu"])


def acoperiri(scenarii) -> dict[str, float]:
    """Pe fiecare scenariu, ce parte din oră vine, la semaforul rejucat, din valuri măsurate."""
    from romana.control.rejucat import program_rejucat      # aduce rețeaua și jurnalul zilei; regula veche nu are nevoie de ele
    return {sc: float(program_rejucat(sc)[1]["acoperire"]) for sc in scenarii}


def mascat_real(p: pd.DataFrame, acoperire: dict[str, float], minima: float) -> pd.Series:
    """Perechile pe care semaforul rejucat poate fi referință."""
    return pd.Series([acoperire[sc] >= minima for sc, _ in p.index], index=p.index)


def ora_de_baza(sc: str) -> str:
    """Scenariul observat din care vine o variantă: fără comportament și fără scară."""
    return re.sub(r"_x\d_\d$", "", sc.replace("indisciplinat_", ""))


def ore_care_trec(scenarii, porti: dict) -> tuple[set, set]:
    """Orele de bază care trec poarta și cele care nu; o oră pe care validarea n-a rulat-o nu trece."""
    ore = {ora_de_baza(s) for s in scenarii}
    trec = {o for o in ore if porti.get(o, {}).get("trece")}
    return trec, ore - trec


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
    ap.add_argument("--in-vigoare", nargs="+", default=[IN_VIGOARE], help="referința; cu mai multe, un candidat trebuie să le bată pe toate, iar dacă nu trece nimeni rămâne prima")
    ap.add_argument("--acoperire-minima", type=float, default=0.8, help="semaforul rejucat, REAL, se compară doar pe orele cu cel puțin atâta din oră din valuri măsurate")
    ap.add_argument("--program", action="append", default=None, help="implicit: REALIST și TOD_DEBIT")
    ap.add_argument("--poarta", help="JSON-ul scris de `valideaza_geaman --poarta`: orele care nu trec nu intră în decizie")
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
    descriptiv, poarta_rez = False, None
    if args.poarta:
        porti = json.loads(Path(args.poarta).read_text(encoding="utf-8"))
        trec, nu_trec = ore_care_trec(p.index.get_level_values(0).unique(), porti["scenarii"])
        descriptiv = len(trec) < len(nu_trec)
        print(f"poarta din § 9.11: trec {len(trec)} din {len(trec) + len(nu_trec)} ore; nu trec: {sorted(nu_trec)}" + (" → ziua e doar descriptivă" if descriptiv else ""))
        poarta_rez = {"trec": sorted(trec), "nu_trec": sorted(nu_trec), "descriptiv": descriptiv, "commit_validare": porti.get("commit")}
        if trec:
            p = p[[ora_de_baza(s) in trec for s, _ in p.index]]
        q = {s: v for s, v in q.items() if ora_de_baza(s) in trec} or q
        cazuri = {s: c for s, c in cazuri.items() if s in q}
        benzi = benzi_analiza(cazuri)
        bands = [(b, [s for s, c in cazuri.items() if c == b]) for b in ("lejer", "moderat")] + [("greu", [])]
    for spec in args.program or PROGRAME:
        name, comp = parse_program(spec)
        p = add_program(p, name, comp, bands)
    ref, alte_ref = args.in_vigoare[0], args.in_vigoare[1:]
    # toate strategiile comparate trebuie să aibă valori pe toate perechile: altfel totalurile s-ar aduna pe seturi
    # diferite de perechi și n-ar mai fi comparabile (un program primește NaN unde îi lipsește o componentă)
    necesare = [*args.in_vigoare, *([args.confirma] if args.confirma else args.candidati)]
    lipsesc = [x for x in necesare if x not in p.columns or not p[x].notna().all()]
    if lipsesc:
        raise SystemExit(f"[decizie] valori lipsă pentru {lipsesc} (strategii sau componente de program nerulate)")
    indisc = p.index.get_level_values(0).str.contains("indisciplinat_")
    print(f"{p.index.get_level_values(0).nunique()} scenarii, {len(p)} perechi; praguri {args.praguri}")
    for s in sorted(q, key=q.get):
        print(f"  {s:48s} {q[s]:7.0f} veh/h → {cazuri[s]}")

    def fata_de(x: str, r: str, masca: pd.Series) -> dict:
        return {"fata_de_in_vigoare": compara(p.loc[masca, x], p.loc[masca, r]), "indisciplinati": compara(p.loc[masca & indisc, x], p.loc[masca & indisc, r]),
                "disciplinati": compara(p.loc[masca & ~indisc, x], p.loc[masca & ~indisc, r])}

    toate = pd.Series(True, index=p.index)
    masti = {r: toate for r in args.in_vigoare}
    if "REAL" in args.in_vigoare:
        acop = acoperiri(sorted(q))
        masti["REAL"] = mascat_real(p, acop, args.acoperire_minima)
        scoase = sorted(s for s, v in acop.items() if v < args.acoperire_minima)
        print(f"REAL, doar unde acoperirea e de cel puțin {args.acoperire_minima:.0%}: {int(masti['REAL'].sum())}/{len(p)} perechi; scoase: {scoase}")
        if not masti["REAL"].any():
            raise SystemExit("[decizie] nicio oră cu acoperire suficientă pentru REAL")

    def evaluare(x: str) -> dict:
        r = {"strategie": x, "pierdere_totala_h": float(p[x].sum()), **fata_de(x, ref, masti[ref])}
        if alte_ref:
            r["alte_referinte"] = {a: fata_de(x, a, masti[a]) for a in alte_ref}
        return r

    rez = {"zi": sorted({RE_SC.search(s)["zi"] for s in q}), "praguri": args.praguri, "in_vigoare": ref,
           "debite": {s: round(v) for s, v in q.items()}, "cazuri": cazuri, "benzi_analiza": benzi}
    if alte_ref or "REAL" in args.in_vigoare:
        rez.update({"referinte": args.in_vigoare, "acoperire_minima": args.acoperire_minima})
    if poarta_rez:
        rez["poarta"] = poarta_rez
    if args.confirma:
        e = evaluare(args.confirma)
        g, i, d = e["fata_de_in_vigoare"], e["indisciplinati"], e["disciplinati"]
        e["dif_totala_pct"] = (e["pierdere_totala_h"] / p[ref].sum() - 1) * 100
        slab = g["p_wilcoxon"] < 0.05 and g["dif_medie_h"] > 0
        rez.update({"confirmare": e, "verdict": "neconfirmat: revenire la " + ref if slab else "confirmat"})
        print(f"\nîn vigoare: {ref}, pierdere totală {p[ref].sum():.1f} h")
        print(f"{args.confirma} total {e['pierdere_totala_h']:.1f} h ({e['dif_totala_pct']:+.1f}%) | față de {ref}: "
              f"{g['dif_medie_h']:+.2f} h/pereche (medie relativă {g['dif_medie_pct']:+.1f}%), mai bun în "
              f"{g['mai_bun']}/{g['n']}, p Wilcoxon = {g['p_wilcoxon']:.6f} | indisc. {i['dif_medie_h']:+.2f} h "
              f"(p = {i['p_wilcoxon']:.4f}), disc. {d['dif_medie_h']:+.2f} h (p = {d['p_wilcoxon']:.4f}) → {rez['verdict']}")
    else:
        evals = [evaluare(x) for x in args.candidati]
        print(f"\nîn vigoare: {ref}, pierdere totală {p[ref].sum():.1f} h")
        eligibili = []
        for e in evals:
            g, i, d = e["fata_de_in_vigoare"], e["indisciplinati"], e["disciplinati"]
            a_ok = g["dif_medie_h"] < 0 and g["p_wilcoxon"] < 0.05
            b_ok = not any(c["p_wilcoxon"] < 0.05 and c["dif_medie_h"] > 0 for c in (i, d))
            for a, c in e.get("alte_referinte", {}).items():
                ga, ia, da = c["fata_de_in_vigoare"], c["indisciplinati"], c["disciplinati"]
                a_ok = a_ok and ga["dif_medie_h"] < 0 and ga["p_wilcoxon"] < 0.05
                b_ok = b_ok and not any(k["p_wilcoxon"] < 0.05 and k["dif_medie_h"] > 0 for k in (ia, da))
                print(f"  {e['strategie']:16s} față de {a}: {ga['dif_medie_h']:+.2f} h/pereche, {ga['mai_bun']}/{ga['n']}, p = {ga['p_wilcoxon']:.6f} | "
                      f"indisc. {ia['dif_medie_h']:+.2f} h (p = {ia['p_wilcoxon']:.4f}), disc. {da['dif_medie_h']:+.2f} h (p = {da['p_wilcoxon']:.4f})")
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
        if descriptiv:
            castig, motiv = ref, "geamănul trece poarta din § 9.11 pe sub jumătate din ore: ziua e doar descriptivă"
        elif not eligibili:
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
