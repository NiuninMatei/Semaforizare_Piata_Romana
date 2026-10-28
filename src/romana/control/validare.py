"""Validarea și testarea strategiilor pe scenarii × seed-uri: pierderea totală de timp, în paralel.

Pentru fiecare strategie, scenariu și seed se rulează simularea completă (aceeași funcție ca în
`evaluate.run_one`: cererea + 15 min de golire) și se păstrează doar indicatorul principal, pierderea
totală de timp a tuturor participanților (ore). Rezultatul: un CSV cu coloanele
`model, scenariu, seed, pierdere_h` și, opțional, alegerea pe medie (`<nume>_alegere.json`):
pentru fiecare strategie, media pe scenarii a diferenței procentuale față de referință (planul fix),
calculată din media pe seed-uri a fiecărui scenariu; „ales” = strategia cu scorul cel mai mic.

Strategii (argumentele poziționale):
  FIX            – planul fix de referință (programul '0', 36/28/12 s); se adaugă automat (vezi --fara-fix);
  ACTUATED       – programul „actuated” al SUMO;
  PLAN_a_b_c     – plan fix cu duratele de verde a / b / c s (N–S, E–V, pietoni), ex. PLAN_46_48_12;
  cale/model.zip – un agent PPO (numele din CSV = numele fișierului, fără extensie).

Seed-urile: alegerile se fac numai pe seed-urile de validare (11–15; 11–13 la primele validări), iar
rezultatele raportate pe seed-urile de test (1–10), rulate cu --fara-alegere. Câmpul
`seeduri_validare` din JSON este scris din seed-urile efectiv prezente în datele din care s-a calculat
scorul (cu --adauga: și cele din CSV-ul existent).

Reproducerea unui fișier publicat: rularea se scrie în outputs/validare/ și se compară cu fișierul din
docs/rezultate (--compara). Scenariile se regenerează la fiecare recalibrare a cererii, deci un fișier
mai vechi se reproduce doar cu versiunea scenariilor din momentul rulării (Anexa A a documentației).
Un fișier existent din docs/rezultate nu se suprascrie decât cu --suprascrie (sau --adauga).

Exemple:
  python -m romana.control.validare ACTUATED PLAN_46_48_12 models/ppo_romana.zip models/ppo_romana_zn3.zip ^
      --scenarii "indisciplinat_zi_2026-10-21_*" "indisciplinat_zi_2026-10-22_*" --seeds 11-15 ^
      --out outputs/validare/validare_x.csv
  python -m romana.control.validare ACTUATED PLAN_46_48_12 models/ppo_romana.zip models/ppo_romana_zn3.zip ^
      models/ppo_romana_lejer.zip --scenarii "indisciplinat_zi_2026-10-2[12]_*" --seeds 1-5 --fara-alegere ^
      --out outputs/validare/calibrat_indisciplinat.csv --compara docs/rezultate/calibrat_indisciplinat.csv
  python -m romana.control.validare --corecteaza-alegeri docs/rezultate
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from pathlib import Path

import pandas as pd

from romana.common import OUTPUT_DIR, ROOT

SCEN_DIR = ROOT / "sumo" / "scenarios"
DOCS_RES = ROOT / "docs" / "rezultate"
COLOANE = ["model", "scenariu", "seed", "pierdere_h"]
# pierderea pe tip de participant (ore), din aceeași simulare: permite, ulterior, o măsură pe persoană cu ocupări
# declarate (autobuze și troleibuze, autoturisme), fără simulări noi; suma lor este pierdere_h
TIPURI = ("passenger", "bus", "truck", "motorcycle", "bicycle", "pieton")
DETALII = [f"pierdere_h_{t}" for t in TIPURI]
CHEI = ["model", "scenariu", "seed"]
REFERINTA = "FIX"
TOLERANTA_H = 1e-6                  # sub această diferență (ore), două rulări sunt considerate identice


def parse_seeds(text: str) -> list[int]:
    """„11-15” sau „11,12,13” (sau combinat: „1-3,7”) → listă sortată de seed-uri."""
    out = set()
    for part in str(text).replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def resolve_scenarios(items: list[str]) -> list[Path]:
    """Scenariile, în ordinea dată (fără dubluri): căi, tipare glob sau nume din sumo/scenarios.

    Un element poate fi o cale către un .sumocfg, un tipar („zi_2026-10-21_*”, căutat în directorul curent
    și în sumo/scenarios) sau doar numele scenariului (cu sau fără extensia .sumocfg)."""
    out = []
    for it in items:
        if any(c in it for c in "*?["):
            found = sorted(glob.glob(it)) or sorted(glob.glob(str(SCEN_DIR / it)))
            if not found and not it.endswith(".sumocfg"):
                found = sorted(glob.glob(str(SCEN_DIR / (it + ".sumocfg"))))
            cands = [Path(f) for f in found if f.endswith(".sumocfg")]
        else:
            p = Path(it)
            cands = [c for c in (p, SCEN_DIR / it, SCEN_DIR / f"{it}.sumocfg") if c.is_file()][:1]
        if not cands:
            raise SystemExit(f"Scenariul „{it}” nu a fost găsit (nici în {SCEN_DIR}).")
        for c in cands:
            c = c.resolve()
            if c not in out:
                out.append(c)
    return out


def strategy_name(spec: str) -> str:
    """Numele strategiei în CSV: FIX / ACTUATED / PLAN_a_b_c rămân ca atare; un model → numele fișierului."""
    if spec in ("FIX", "ACTUATED") or spec.startswith("PLAN_"):
        return spec
    return Path(spec).stem


def make_controller(spec: str):
    """Controlerul unei strategii (construit în procesul care rulează simularea)."""
    from romana.control import controllers as C

    if spec == "FIX":
        ctrl = C.FixedReference()
    elif spec == "ACTUATED":
        ctrl = C.Actuated()
    elif spec.startswith("PLAN_"):
        ctrl = C.FixedWebster.__new__(C.FixedWebster)       # plan fix dat prin duratele de verde
        ctrl.plan = {"verde_s": [float(v) for v in spec.split("_")[1:]]}
    else:
        path = Path(spec)
        meta = path.with_suffix(".json")
        meta = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        ctrl = C.RLPolicy(path, controlled=meta.get("controlate", ["romana"]))
    ctrl.name = strategy_name(spec)
    return ctrl


def run_task(task: tuple) -> tuple:
    """O simulare (strategie, scenariu, seed) → (model, scenariu, seed, pierdere_h, pierderile pe tipuri)."""
    spec, sumocfg, seed, eval_dir, quiet = task
    if quiet:                       # SUMO scrie multe avertismente; în procesele de lucru nu le afișăm
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
    from romana.control import evaluate as E

    E.EVAL_DIR = Path(eval_dir)      # fișierele tripinfo temporare (șterse după agregare)
    ctrl = make_controller(spec)
    r = E.run_one(Path(sumocfg), ctrl, seed)
    return (ctrl.name, Path(sumocfg).stem, seed, r["pierdere_totala_h"], *(r.get(c, 0.0) for c in DETALII))


def run_all(specs: list[str], scenarios: list[Path], seeds: list[int], procese: int,
            eval_dir: Path, quiet: bool = True) -> pd.DataFrame:
    tasks = [(m, str(s), seed, str(eval_dir), quiet) for m in specs for s in scenarios for seed in seeds]
    print(f"[validare] {len(specs)} strategii × {len(scenarios)} scenarii × {len(seeds)} seed-uri = "
          f"{len(tasks)} simulări, {procese} procese", flush=True)
    if procese > 1:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=procese) as ex:
            res = list(ex.map(run_task, tasks))
    else:
        res = [run_task(t[:4] + (False,)) for t in tasks]
    return pd.DataFrame(res, columns=COLOANE + DETALII)


def relative_table(df: pd.DataFrame, ref: str = REFERINTA) -> pd.DataFrame:
    """Diferența procentuală față de referință, pe scenarii (din media pe seed-uri): model × scenariu."""
    p = df.pivot_table(index="model", columns="scenariu", values="pierdere_h", aggfunc="mean")
    return (p - p.loc[ref]) / p.loc[ref] * 100


def choice(df: pd.DataFrame, scenarios: list[str], ref: str = REFERINTA) -> dict:
    """Alegerea pe medie: scorul fiecărei strategii (media pe scenarii a diferenței %) și cea mai bună."""
    df = df[df["scenariu"].isin(scenarios)]
    score = relative_table(df, ref).mean(axis=1).drop(ref)
    per_model = df.groupby("model")["seed"].apply(lambda s: tuple(sorted(s.unique())))
    if per_model.nunique() > 1:
        print("[atenție] strategiile nu au aceleași seed-uri:", per_model.to_dict())
    return {"scor_mediu_procent": score.round(2).to_dict(), "ales": score.idxmin(),
            "seeduri_validare": sorted(int(s) for s in df["seed"].unique()),
            "scenarii": [s for s in scenarios if s in set(df["scenariu"])]}


def choice_path(csv_path: Path) -> Path:
    return csv_path.with_name(csv_path.stem + "_alegere.json")


def published_files(out: Path, results_dir: Path = DOCS_RES) -> list[Path]:
    """Fișierele publicate existente (CSV-ul și alegerea lui) pe care rularea le-ar suprascrie în docs/rezultate."""
    try:
        out.resolve().relative_to(results_dir.resolve())
    except ValueError:
        return []
    return [p for p in (out, choice_path(out)) if p.exists()]


def compare_with(df: pd.DataFrame, ref_csv: Path, tol: float = TOLERANTA_H) -> dict:
    """Compară rezultatele cu un CSV publicat pe cheile comune (model, scenariu, seed)."""
    ref = pd.read_csv(ref_csv)
    m = df.merge(ref[COLOANE], on=CHEI, suffixes=("", "_ref"))
    d = (m["pierdere_h"] - m["pierdere_h_ref"]).abs()
    return {"comune": len(m), "identice": int((d <= tol).sum()), "dif_max_h": float(d.max()) if len(m) else 0.0,
            "doar_rulare": len(df) - len(m), "doar_publicat": len(ref) - len(m)}


def fix_choice_seeds(results_dir: Path) -> list[str]:
    """Corectează `seeduri_validare` din fiecare `*_alegere.json` după seed-urile din CSV-ul pereche.

    Seed-urile se iau din rândurile scenariilor listate în JSON (cele din care s-a calculat scorul).
    Scorurile nu se modifică. Întoarce lista fișierelor schimbate."""
    changed = []
    for jp in sorted(Path(results_dir).glob("*_alegere.json")):
        cp = jp.with_name(jp.name[: -len("_alegere.json")] + ".csv")
        if not cp.exists():
            print(f"[corectare] {jp.name}: fără CSV pereche ({cp.name}), neschimbat")
            continue
        d = json.loads(jp.read_text(encoding="utf-8"))
        df = pd.read_csv(cp)
        if d.get("scenarii"):
            df = df[df["scenariu"].isin(d["scenarii"])]
        seeds = sorted(int(s) for s in df["seed"].unique())
        if d.get("seeduri_validare") != seeds:
            print(f"[corectare] {jp.name}: seeduri_validare {d.get('seeduri_validare')} → {seeds}")
            d["seeduri_validare"] = seeds
            jp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            changed.append(str(jp))
    return changed


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strategii", nargs="*", help="FIX, ACTUATED, PLAN_a_b_c sau căi către modele .zip")
    ap.add_argument("--scenarii", nargs="+", default=None,
                    help="căi, tipare glob sau nume de scenarii din sumo/scenarios (ordinea se păstrează în JSON)")
    ap.add_argument("--seeds", default="11-15", help="seed-uri: „11-15” sau „11,12,13” (implicit 11-15, validare)")
    ap.add_argument("--procese", type=int, default=4, help="simulări în paralel (implicit 4)")
    ap.add_argument("--out", default=str(OUTPUT_DIR / "validare" / "validare.csv"),
                    help="CSV-ul rezultatelor (alegerea: același nume + _alegere.json)")
    ap.add_argument("--fara-fix", action="store_true", help="nu adăuga planul fix (FIX); fără el nu se face alegerea")
    ap.add_argument("--fara-alegere", action="store_true",
                    help="doar CSV-ul, fără _alegere.json (rulările pe seed-urile de test)")
    ap.add_argument("--adauga", action="store_true",
                    help="unește cu CSV-ul existent (rândurile refăcute le înlocuiesc pe cele vechi), apoi alege pe tot")
    ap.add_argument("--compara", metavar="CSV",
                    help="după rulare, compară rezultatele cu acest fișier publicat (perechile comune, diferența maximă)")
    ap.add_argument("--suprascrie", action="store_true",
                    help="permite suprascrierea unui fișier existent din docs/rezultate (implicit refuzată)")
    ap.add_argument("--verbose", action="store_true", help="afișează mesajele SUMO din procesele de lucru")
    ap.add_argument("--corecteaza-alegeri", metavar="DIR",
                    help="doar corectează seeduri_validare din DIR/*_alegere.json după CSV-urile pereche, fără simulări")
    args = ap.parse_args(argv)
    if args.corecteaza_alegeri:
        changed = fix_choice_seeds(Path(args.corecteaza_alegeri))
        print(f"[OK] {len(changed)} fișiere corectate")
        return
    if not args.scenarii:
        ap.error("lipsește --scenarii")
    specs = list(dict.fromkeys(args.strategii))
    if not args.fara_fix and REFERINTA not in specs:
        specs.append(REFERINTA)
    if not specs:
        ap.error("nicio strategie de rulat")
    for s in specs:
        if s not in ("FIX", "ACTUATED") and not s.startswith("PLAN_") and not Path(s).exists():
            ap.error(f"modelul {s} nu există")
    scenarios = resolve_scenarios(args.scenarii)
    seeds = parse_seeds(args.seeds)
    out = Path(args.out)
    existing = published_files(out)
    if existing and not (args.suprascrie or args.adauga):
        ap.error(f"{', '.join(str(p) for p in existing)} există deja în docs/rezultate: scrieți rularea în "
                 "outputs/validare/ și comparați-o cu --compara (sau dați --suprascrie)")
    if args.compara and not Path(args.compara).exists():
        ap.error(f"fișierul de comparat {args.compara} nu există")
    t0 = time.time()
    df = run_all(specs, scenarios, seeds, args.procese, OUTPUT_DIR / "eval_validare", quiet=not args.verbose)
    if args.adauga and out.exists():
        df = pd.concat([pd.read_csv(out), df]).drop_duplicates(CHEI, keep="last")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"[OK] {out}  ({len(df)} rânduri, {time.time() - t0:.0f} s)")
    if args.compara:
        c = compare_with(df, Path(args.compara))
        print(f"[comparație] {args.compara}: {c['comune']} rulări comune, {c['identice']} identice "
              f"(|Δ| ≤ {TOLERANTA_H:g} h), diferența maximă {c['dif_max_h']:.6f} h; doar în rularea nouă: "
              f"{c['doar_rulare']}, doar în fișierul publicat: {c['doar_publicat']}")
    if REFERINTA not in set(df["model"]):
        print("[validare] fără planul fix în rezultate: tabelul relativ și alegerea sunt omise")
        return
    names = [s.stem for s in scenarios]
    pd.set_option("display.width", 250)
    print(relative_table(df[df["scenariu"].isin(names)]).round(1).to_string())
    if args.fara_alegere or set(df["model"]) == {REFERINTA}:
        return
    ch = choice(df, names)
    print("scor mediu (% față de planul fix):", ch["scor_mediu_procent"], "→ ales:", ch["ales"],
          "; seed-uri:", ch["seeduri_validare"])
    choice_path(out).write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {choice_path(out)}")


if __name__ == "__main__":
    main()
