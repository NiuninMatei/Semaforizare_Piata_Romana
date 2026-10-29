"""Borna 9 – Scenariile SUMO ale unei zile de date reale, generate automat din numărătorile camerei.

Pentru o zi colectată (data/counts/numaratori_AAAA-LL-ZZ.csv):
  1. se calculează, pe ferestre glisante de o oră (pas 15 min), debitul echilibrat prin piață
     (media dintre suma intrărilor și suma ieșirilor, ca în od_estimation);
  2. se aleg ora de vârf (debitul maxim), ora cea mai liniștită și, dacă datele le acoperă și nu se suprapun cu
     vârful, orele fixe de dimineață (07:30–08:30), prânz (12:00–13:00) și seară (17:30–18:30);
  3. pentru fiecare se construiește scenariul cu build_demand (Furness + routeSampler);
  4. se adaugă scenariile de sensibilitate: vârf × 1,2 și liniștit × 0,8 (incertitudinea măsurării).
Cu --fara-inghetate, intervalele de 15 min suspecte de imagine înghețată (`romana.vision.calitate`, § 4.6) nu intră
în nicio fereastră; implicit nu se exclude nimic, ca la zilele prelucrate până acum.

Exemple:
  python -m romana.bridge.scenarii_zi --zi 2026-10-21
  python -m romana.bridge.scenarii_zi --zi 2026-10-21 --doar-analiza
  python -m romana.bridge.scenarii_zi --zi 2026-10-28 --doar-analiza --fara-inghetate
"""
from __future__ import annotations

import argparse

import pandas as pd

from romana.bridge import build_demand
from romana.common import COUNTS_DIR, DEMAND_DIR, TRAJ_DIR, TRAJ_RAW_DIR, save_json


def intervale_inghetate(zi: str) -> set[pd.Timestamp]:
    """Începuturile intervalelor de 15 min suspecte de imagine înghețată, din jurnalul de traiectorii al zilei."""
    from romana.vision.calitate import inghetate, quality
    for d in (TRAJ_RAW_DIR, TRAJ_DIR):
        f = d / f"traiectorii_{zi}.jsonl.gz"
        if f.exists():
            return {pd.Timestamp(f"{zi} {k}") for k, *_ in inghetate(quality(f)[1])}
    print(f"[scenarii_zi] fără jurnal de traiectorii pentru {zi}: nu se pot exclude intervalele înghețate")
    return set()


def hourly_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Debitul (veh/h) pe intervale de 15 min și pe ferestre glisante de o oră."""
    q = df.groupby(["inceput", "tip"])["numar"].sum().unstack(fill_value=0)
    for c in ("intrare", "iesire", "pietoni"):
        if c not in q:
            q[c] = 0
    q["dur_h"] = (df.groupby("inceput")["sfarsit"].max() - q.index).dt.total_seconds() / 3600
    q = q[q["dur_h"] >= 0.2]                                   # intervalele incomplete (pornire/oprire) nu contează
    q["echilibrat_veh_h"] = (q["intrare"] + q["iesire"]) / 2 / q["dur_h"]
    q["pietoni_h"] = q["pietoni"] / q["dur_h"]
    q["ora_glisanta_veh_h"] = q["echilibrat_veh_h"].rolling(4).mean()   # fereastra care se termină aici
    return q


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", required=True, help="AAAA-LL-ZZ")
    ap.add_argument("--doar-analiza", action="store_true", help="doar profilul orar, fără scenarii")
    ap.add_argument("--fara-inghetate", action="store_true",
                    help="exclude din ferestre intervalele suspecte de imagine înghețată (§ 4.6)")
    args = ap.parse_args(argv)
    path = COUNTS_DIR / f"numaratori_{args.zi}.csv"
    df = pd.read_csv(path, parse_dates=["inceput", "sfarsit"])
    prof = hourly_profile(df)
    profil = prof["echilibrat_veh_h"].copy()          # profilul complet, pentru rezumat (debitele ferestrelor)
    inghet = intervale_inghetate(args.zi) if args.fara_inghetate else set()
    if inghet:
        # o fereastră care atinge un interval înghețat nu poate fi nici vârf, nici liniștit, nici fereastră fixă
        prof.loc[prof.index.isin(inghet), "echilibrat_veh_h"] = float("nan")
        prof["ora_glisanta_veh_h"] = prof["echilibrat_veh_h"].rolling(4).mean()
        print("Intervale excluse (imagine înghețată):", ", ".join(f"{t:%H:%M}" for t in sorted(inghet)))
    print(prof[["intrare", "iesire", "echilibrat_veh_h", "pietoni_h", "ora_glisanta_veh_h"]].round(0).to_string())
    full = prof.dropna(subset=["ora_glisanta_veh_h"])
    end_peak = full["ora_glisanta_veh_h"].idxmax()
    end_low = full["ora_glisanta_veh_h"].idxmin()
    h = pd.Timedelta(minutes=15)
    windows = {
        "varf": (end_peak - 3 * h, end_peak + h),
        "linistit": (end_low - 3 * h, end_low + h),
        "dimineata": (pd.Timestamp(f"{args.zi} 07:30"), pd.Timestamp(f"{args.zi} 08:30")),
        "pranz": (pd.Timestamp(f"{args.zi} 12:00"), pd.Timestamp(f"{args.zi} 13:00")),
        "seara": (pd.Timestamp(f"{args.zi} 17:30"), pd.Timestamp(f"{args.zi} 18:30")),
    }
    # se păstrează doar ferestrele acoperite integral de date și care nu se suprapun peste vârful zilei
    covered = set(prof.index) - inghet
    windows = {k: (a, b) for k, (a, b) in windows.items()
               if all(t in covered for t in pd.date_range(a, b - h, freq="15min"))}
    a0, b0 = windows["varf"]
    windows = {k: (a, b) for k, (a, b) in windows.items()
               if k in ("varf", "linistit") or b <= a0 or a >= b0}
    summary = {"zi": args.zi, "profil": {str(k): round(v, 1) for k, v in profil.items()},
               "ferestre": {k: [str(a), str(b)] for k, (a, b) in windows.items()}}
    if args.fara_inghetate:
        summary["inghetate_excluse"] = [str(t) for t in sorted(inghet)]
    print("\nFerestre alese:", {k: f"{a:%H:%M}–{b:%H:%M}" for k, (a, b) in windows.items()})
    if args.doar_analiza:
        return
    names = []
    for k, (a, b) in windows.items():
        name = f"zi_{args.zi}_{k}"
        build_demand.main(["--counts", str(path), "--de-la", f"{a:%Y-%m-%d %H:%M}", "--pana-la", f"{b:%Y-%m-%d %H:%M}",
                           "--nume", name])
        names.append(name)
    for k, f in (("varf", 1.2), ("linistit", 0.8)):
        a, b = windows[k]
        name = f"zi_{args.zi}_{k}_x{f:.1f}".replace(".", "_")
        build_demand.main(["--counts", str(path), "--de-la", f"{a:%Y-%m-%d %H:%M}", "--pana-la", f"{b:%Y-%m-%d %H:%M}",
                           "--nume", name, "--scala", str(f)])
        names.append(name)
    summary["scenarii"] = names
    save_json(summary, DEMAND_DIR / f"zi_{args.zi}_rezumat.json")
    print(f"[OK] {len(names)} scenarii: {', '.join(names)}")


if __name__ == "__main__":
    main()
