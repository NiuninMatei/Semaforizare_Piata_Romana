"""Borna 9 – Scenariile SUMO ale unei zile de date reale, generate automat din numărătorile camerei.

Pentru o zi colectată (data/counts/numaratori_AAAA-LL-ZZ.csv):
  1. se calculează, pe ferestre glisante de o oră (pas 15 min), debitul echilibrat prin piață
     (media dintre suma intrărilor și suma ieșirilor, ca în od_estimation);
  2. se aleg ora de vârf (debitul maxim), ora cea mai liniștită și, dacă datele le acoperă și nu se suprapun cu
     vârful, orele fixe de dimineață (07:30–08:30), prânz (12:00–13:00) și seară (17:30–18:30);
  3. pentru fiecare se construiește scenariul cu build_demand (Furness + routeSampler);
  4. se adaugă scenariile de sensibilitate: vârf × 1,2 și liniștit × 0,8 (incertitudinea măsurării).
Ferestrele se aleg pe grila completă de 15 min: un sfert de oră fără date (de exemplu o oprire a colectării) rămâne
gol, iar nicio fereastră nu trece peste el. Cu --fara-inghetate, intervalele de 15 min suspecte de imagine înghețată
(`romana.vision.calitate`, § 4.6) nu intră în nicio fereastră; cu --exclude HH:MM-HH:MM se scot explicit și alte
intervale (de exemplu sferturile de oră atinse de o repornire a colectării). Implicit nu se exclude nimic, ca la
zilele prelucrate până acum.

Exemple:
  python -m romana.bridge.scenarii_zi --zi 2026-10-21
  python -m romana.bridge.scenarii_zi --zi 2026-10-21 --doar-analiza
  python -m romana.bridge.scenarii_zi --zi 2026-10-28 --doar-analiza --fara-inghetate
  python -m romana.bridge.scenarii_zi --zi 2026-10-29 --doar-analiza --exclude 08:30-09:30
"""
from __future__ import annotations

import argparse
import re

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


SPECIFICATIE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$")


def intervale_date(zi: str, specificatii: list[str] | None) -> set[pd.Timestamp]:
    """Începuturile intervalelor de 15 min din specificațiile „HH:MM-HH:MM” (capătul din dreapta nu intră; 24:00 =
    sfârșitul zilei)."""
    out = set()
    for s in specificatii or []:
        m = SPECIFICATIE.match(s)
        if not m:
            raise SystemExit(f"--exclude {s}: formatul este HH:MM-HH:MM")
        h1, m1, h2, m2 = map(int, m.groups())
        a = pd.Timestamp(zi) + pd.Timedelta(hours=h1, minutes=m1)
        b = pd.Timestamp(zi) + pd.Timedelta(hours=h2, minutes=m2)
        if m1 % 15 or m2 % 15 or max(m1, m2) >= 60 or b <= a or b > pd.Timestamp(zi) + pd.Timedelta(days=1):
            raise SystemExit(f"--exclude {s}: capetele trebuie să fie pe grila de 15 min, cu începutul înaintea sfârșitului")
        out |= set(pd.date_range(a, b - pd.Timedelta(minutes=15), freq="15min"))
    return out


def hourly_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Debitul (veh/h) pe intervale de 15 min și pe ferestre glisante de o oră."""
    q = df.groupby(["inceput", "tip"])["numar"].sum().unstack(fill_value=0)
    for c in ("intrare", "iesire", "pietoni"):
        if c not in q:
            q[c] = 0
    q["dur_h"] = (df.groupby("inceput")["sfarsit"].max() - q.index).dt.total_seconds() / 3600
    q = q[q["dur_h"] >= 0.2]                                   # intervalele incomplete (pornire/oprire) nu contează
    if len(q) and (q.index == q.index.floor("15min")).all():
        # grila completă: un sfert de oră fără date rămâne gol, iar fereastra glisantă de o oră nu-l mai sare
        # (altfel ar uni sferturi de oră nevecine, de o parte și de alta a golului)
        q = q.reindex(pd.date_range(q.index.min(), q.index.max(), freq="15min", name=q.index.name))
    q["echilibrat_veh_h"] = (q["intrare"] + q["iesire"]) / 2 / q["dur_h"]
    q["pietoni_h"] = q["pietoni"] / q["dur_h"]
    q["ora_glisanta_veh_h"] = q["echilibrat_veh_h"].rolling(4).mean()   # fereastra care se termină aici
    return q


def exclude(prof: pd.DataFrame, intervale: set[pd.Timestamp]) -> pd.DataFrame:
    """Scoate intervalele date din alegerea ferestrelor: o fereastră care atinge unul dintre ele nu poate fi nici vârf,
    nici liniștit, nici fereastră fixă."""
    if not intervale:
        return prof
    prof = prof.copy()
    prof.loc[prof.index.isin(intervale), "echilibrat_veh_h"] = float("nan")
    prof["ora_glisanta_veh_h"] = prof["echilibrat_veh_h"].rolling(4).mean()
    return prof


def alege_ferestre(prof: pd.DataFrame, zi: str) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """Vârful, ora cea mai liniștită și ferestrele fixe; se păstrează doar ferestrele acoperite integral de date și
    care nu se suprapun peste vârful zilei (liniștitul rămâne oricum)."""
    full = prof.dropna(subset=["ora_glisanta_veh_h"])
    if full.empty:
        raise SystemExit("scenarii_zi: nicio oră completă de date după excluderi")
    end_peak = full["ora_glisanta_veh_h"].idxmax()
    end_low = full["ora_glisanta_veh_h"].idxmin()
    h = pd.Timedelta(minutes=15)
    windows = {
        "varf": (end_peak - 3 * h, end_peak + h),
        "linistit": (end_low - 3 * h, end_low + h),
        "dimineata": (pd.Timestamp(f"{zi} 07:30"), pd.Timestamp(f"{zi} 08:30")),
        "pranz": (pd.Timestamp(f"{zi} 12:00"), pd.Timestamp(f"{zi} 13:00")),
        "seara": (pd.Timestamp(f"{zi} 17:30"), pd.Timestamp(f"{zi} 18:30")),
    }
    covered = set(prof.index[prof["echilibrat_veh_h"].notna()])
    windows = {k: (a, b) for k, (a, b) in windows.items()
               if all(t in covered for t in pd.date_range(a, b - h, freq="15min"))}
    if "varf" not in windows:      # posibil doar pe un CSV nealiniat la 15 min, unde grila completă nu se aplică
        raise SystemExit("scenarii_zi: ora de vârf trece peste un gol din date (CSV nealiniat la 15 min?)")
    a0, b0 = windows["varf"]
    return {k: (a, b) for k, (a, b) in windows.items() if k in ("varf", "linistit") or b <= a0 or a >= b0}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", required=True, help="AAAA-LL-ZZ")
    ap.add_argument("--doar-analiza", action="store_true", help="doar profilul orar, fără scenarii")
    ap.add_argument("--fara-inghetate", action="store_true",
                    help="exclude din ferestre intervalele suspecte de imagine înghețată (§ 4.6)")
    ap.add_argument("--exclude", action="append", default=[], metavar="HH:MM-HH:MM",
                    help="exclude din ferestre sferturile de oră dintre cele două ore (de ex. o oprire a colectării); "
                         "se poate repeta")
    args = ap.parse_args(argv)
    path = COUNTS_DIR / f"numaratori_{args.zi}.csv"
    df = pd.read_csv(path, parse_dates=["inceput", "sfarsit"])
    prof = hourly_profile(df)
    profil = prof["echilibrat_veh_h"].dropna()        # profilul complet, pentru rezumat (debitele ferestrelor)
    inghet = intervale_inghetate(args.zi) if args.fara_inghetate else set()
    alese = intervale_date(args.zi, args.exclude)
    if inghet:
        print("Intervale excluse (imagine înghețată):", ", ".join(f"{t:%H:%M}" for t in sorted(inghet)))
    if alese:
        print("Intervale excluse (--exclude):", ", ".join(f"{t:%H:%M}" for t in sorted(alese)))
    prof = exclude(prof, inghet | alese)
    print(prof[["intrare", "iesire", "echilibrat_veh_h", "pietoni_h", "ora_glisanta_veh_h"]].round(0).to_string())
    windows = alege_ferestre(prof, args.zi)
    summary = {"zi": args.zi, "profil": {str(k): round(v, 1) for k, v in profil.items()},
               "ferestre": {k: [str(a), str(b)] for k, (a, b) in windows.items()}}
    if args.fara_inghetate:
        summary["inghetate_excluse"] = [str(t) for t in sorted(inghet)]
    if alese:
        summary["intervale_excluse"] = [str(t) for t in sorted(alese)]
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
