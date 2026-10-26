"""Statisticile pe perechi din capitolul 9 și programele pe tipuri de trafic.

Fiecare comparație „strategia A față de referința B” se face pe perechi (același scenariu, același
seed), numai pe perechile în care ambele au un rezultat:
  * diferența medie (%)          – media pe perechi a (A − B) / B · 100;
  * media pe scenarii (%)        – media pe scenarii a diferenței medii din fiecare scenariu
                                   (egală cu precedenta când toate scenariile au aceleași seed-uri);
  * „mai bun în k din n”         – perechile în care A are o pierdere totală mai mică decât B;
  * p (testul t pe perechi)      – pe valorile absolute (ore), scipy.stats.ttest_rel;
  * p (Wilcoxon)                 – testul rangurilor cu semn pe perechi, pe perechile care diferă
                                   (scipy.stats.wilcoxon); 1 dacă toate sunt egale.

Programul pe tipuri de trafic alege, pentru fiecare scenariu, strategia benzii lui de trafic. Benzile
se dau prin tipare glob pe numele scenariului, verificate în ordine (prima potrivire câștigă), iar
scenariile nepotrivite cad în ultima bandă dată fără tipar (implicit: lejer = *linistit*,
moderat = *pranz*, greu = restul, ca în § 9.2 și § 9.8).

Intrarea: unul sau mai multe CSV-uri, fie din `control.validare` (model, scenariu, seed, pierdere_h), fie
din `control.evaluate` (strategie, scenariu, seed, pierdere_totala_h); la rânduri dublate se păstrează
ultimul fișier.

Exemple:
  python -m romana.control.analiza docs/rezultate/calibrat_indisciplinat.csv ^
      --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --pe-scenarii
  python -m romana.control.analiza docs/rezultate/robustete_indisciplinat.csv docs/rezultate/robustete_indisciplinat_6_10.csv ^
      --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3
  python -m romana.control.analiza docs/rezultate/rezultate_brute.csv --exclude "*2026-10-25*" ^
      --program JOS=lejer:actuated,moderat:rl_ppo_romana_zn3,greu:fix_referinta --strategii JOS actuated
"""
from __future__ import annotations

import argparse
import fnmatch
import math
from pathlib import Path

import numpy as np
import pandas as pd

BENZI_IMPLICITE = "lejer=*linistit*;moderat=*pranz*;greu"
REFERINTE_POSIBILE = ("FIX", "ACTUATED", "fix_referinta", "actuated")


def load_results(paths: list[str | Path], metric: str | None = None) -> pd.DataFrame:
    """CSV-urile de rezultate, aduse la coloanele model, scenariu, seed, valoare."""
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        model = "model" if "model" in df.columns else "strategie"
        val = metric or ("pierdere_h" if "pierdere_h" in df.columns else "pierdere_totala_h")
        frames.append(df[[model, "scenariu", "seed", val]].set_axis(["model", "scenariu", "seed", "valoare"], axis=1))
    df = pd.concat(frames, ignore_index=True)
    return df.drop_duplicates(["model", "scenariu", "seed"], keep="last")


def parse_bands(text: str) -> list[tuple[str, list[str]]]:
    """„lejer=*linistit*;moderat=*pranz*,*25_dimineata;greu” → [(bandă, [tipare]), ...]; fără tipar = restul."""
    bands = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        name, _, pats = part.partition("=")
        bands.append((name.strip(), [q.strip() for q in pats.split(",") if q.strip()]))
    return bands


def band_of(scenario: str, bands: list[tuple[str, list[str]]]) -> str | None:
    """Banda de trafic a unui scenariu: prima bandă cu un tipar potrivit, altfel banda fără tipare."""
    for name, pats in bands:
        if any(fnmatch.fnmatchcase(scenario, q) for q in pats):
            return name
    rest = [name for name, pats in bands if not pats]
    return rest[-1] if rest else None


def parse_program(text: str) -> tuple[str, dict[str, str]]:
    """„REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3” → (nume, {bandă: strategie})."""
    name, _, spec = text.partition("=")
    if not spec:
        raise ValueError(f"program fără componente: {text}")
    comp = {}
    for item in spec.split(","):
        band, _, strat = item.partition(":")
        comp[band.strip()] = strat.strip()
    return name.strip(), comp


def pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Tabelul perechilor: index (scenariu, seed), o coloană pe strategie."""
    return df.pivot_table(index=["scenariu", "seed"], columns="model", values="valoare")


def add_program(p: pd.DataFrame, name: str, comp: dict[str, str], bands) -> pd.DataFrame:
    """Adaugă coloana programului: pe fiecare rând, valoarea strategiei din banda scenariului."""
    vals = []
    for (sc, _), row in p.iterrows():
        strat = comp.get(band_of(sc, bands))
        vals.append(row[strat] if strat in row.index else np.nan)
    p[name] = vals
    return p


def compare(a: pd.Series, b: pd.Series) -> dict:
    """Statisticile pe perechi pentru A față de B (aceeași indexare scenariu × seed)."""
    from scipy import stats

    m = a.notna() & b.notna()
    a, b = a[m].astype(float), b[m].astype(float)
    n = int(len(a))
    if n == 0:
        return {"n": 0}
    rel = (a - b) / b * 100
    per_sc = rel.groupby(level=0).mean()
    diff = a - b
    nz = diff != 0
    if not nz.any():                              # identice pe toate perechile: nicio diferență de testat
        p_t = p_w = 1.0
    else:
        p_t = float(stats.ttest_rel(a, b).pvalue) if n > 1 else math.nan
        # perechile egale (ex. programul folosește chiar referința pe o bandă) se scot înainte: același test
        # ca zero_method="wilcox", dar scipy poate folosi distribuția exactă (n ≤ 50, fără zerouri)
        p_w = float(stats.wilcoxon(a[nz], b[nz]).pvalue)
    return {"n": n, "diferenta_medie_pct": float(rel.mean()), "medie_pe_scenarii_pct": float(per_sc.mean()),
            "mai_bun": int((diff < 0).sum()), "perechi_diferite": int(nz.sum()), "p_t": p_t, "p_wilcoxon": p_w,
            "pe_scenarii_pct": per_sc.round(1).to_dict()}


def fmt_p(p: float) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "–"
    return "<0,000001" if p < 1e-6 else f"{p:.6f}".rstrip("0").rstrip(".").replace(".", ",")


def analyse(df: pd.DataFrame, strategies: list[str] | None, references: list[str] | None,
            programs: list[str], bands_text: str = BENZI_IMPLICITE) -> list[dict]:
    """Toate comparațiile cerute: fiecare strategie (și program) față de fiecare referință."""
    p = pivot(df)
    bands = parse_bands(bands_text)
    prog_names = []
    for spec in programs:
        name, comp = parse_program(spec)
        missing = [s for s in comp.values() if s not in p.columns]
        if missing:
            raise SystemExit(f"Programul {name}: strategii absente din date: {missing}")
        add_program(p, name, comp, bands)
        prog_names.append(name)
    refs = references or [r for r in REFERINTE_POSIBILE if r in p.columns]
    strats = strategies or prog_names + [c for c in p.columns if c not in prog_names and c not in refs]
    rows = []
    for s in strats:
        if s not in p.columns:
            raise SystemExit(f"Strategia {s} nu există în date (disponibile: {sorted(p.columns)})")
        for r in refs:
            if s == r:
                continue
            if r not in p.columns:
                raise SystemExit(f"Referința {r} nu există în date")
            rows.append({"strategie": s, "referinta": r, **compare(p[s], p[r])})
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+", help="fișierele de rezultate (validare sau evaluate)")
    ap.add_argument("--strategii", nargs="*", default=None,
                    help="strategiile (și programele) de comparat; implicit programele, apoi toate celelalte")
    ap.add_argument("--referinte", nargs="*", default=None,
                    help="referințele; implicit cele prezente dintre FIX, ACTUATED, fix_referinta, actuated")
    ap.add_argument("--program", action="append", default=[],
                    help="program pe tipuri de trafic: NUME=lejer:strategie,moderat:strategie,greu:strategie")
    ap.add_argument("--benzi", default=BENZI_IMPLICITE,
                    help=f"benzile de trafic, „bandă=tipar,tipar;...”, ultima fără tipar = restul (implicit „{BENZI_IMPLICITE}”)")
    ap.add_argument("--scenarii", nargs="*", default=None, help="doar scenariile care se potrivesc cu aceste tipare glob")
    ap.add_argument("--exclude", nargs="*", default=None, help="exclude scenariile care se potrivesc cu aceste tipare")
    ap.add_argument("--seeds", default=None, help="doar aceste seed-uri: „1-5” sau „1,2,3”")
    ap.add_argument("--metrica", default=None, help="coloana analizată (implicit pierdere_h / pierdere_totala_h)")
    ap.add_argument("--pe-scenarii", action="store_true", help="afișează și diferența medie pe fiecare scenariu")
    ap.add_argument("--out", default=None, help="salvează tabelul comparațiilor în acest CSV")
    args = ap.parse_args(argv)
    df = load_results(args.csv, args.metrica)
    if args.scenarii:
        df = df[df["scenariu"].apply(lambda s: any(fnmatch.fnmatchcase(s, q) for q in args.scenarii))]
    if args.exclude:
        df = df[~df["scenariu"].apply(lambda s: any(fnmatch.fnmatchcase(s, q) for q in args.exclude))]
    if args.seeds:
        from romana.control.validare import parse_seeds

        df = df[df["seed"].isin(parse_seeds(args.seeds))]
    if df.empty:
        raise SystemExit("Niciun rând după filtre.")
    bands = parse_bands(args.benzi)
    print(f"{df['scenariu'].nunique()} scenarii, seed-uri {sorted(df['seed'].unique().tolist())}; benzi: "
          + ", ".join(f"{s}→{band_of(s, bands)}" for s in sorted(df["scenariu"].unique())))
    rows = analyse(df, args.strategii, args.referinte, args.program, args.benzi)
    for r in rows:
        if not r["n"]:
            print(f"{r['strategie']:22s} vs {r['referinta']:13s}: fără perechi comune")
            continue
        print(f"{r['strategie']:22s} vs {r['referinta']:13s}: {r['diferenta_medie_pct']:+6.1f}% "
              f"(pe scenarii {r['medie_pe_scenarii_pct']:+6.1f}%)  mai bun în {r['mai_bun']:3d}/{r['n']:<3d} "
              + (f"(diferite: {r['perechi_diferite']})  " if r["perechi_diferite"] < r["n"] else "")
              + f"p t = {fmt_p(r['p_t'])}  p Wilcoxon = {fmt_p(r['p_wilcoxon'])}")
        if args.pe_scenarii:
            print("    " + ", ".join(f"{k}: {v:+.1f}%" for k, v in r["pe_scenarii_pct"].items()))
    if args.out:
        out = pd.DataFrame([{k: v for k, v in r.items() if k != "pe_scenarii_pct"} for r in rows])
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.out, index=False)
        print(f"[OK] {args.out}")


if __name__ == "__main__":
    main()
