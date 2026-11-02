"""Validarea geamănului față de cameră (§ 6.5), pe aceeași oră, pe același ceas și cu praguri scrise dinainte.

Semaforul geamănului e semaforul real, rejucat ciclu cu ciclu din jurnalul zilei (`rejucat.py`), deci camera și geamănul se pot pune pe același ceas: secundele de la începutul
fiecărui val de pe Magheru. Se compară:
  - debitele pe brațe. Cererea vine din aceleași numărători, deci aici se vede doar dacă geamănul reușește să le ducă;
  - profilul pe ciclu al fiecărei intrări, pe 10 s: cât trece, și când, față de începutul valului. Pe Dacia vest doar se afișează: zona camerei prinde și mașinile care așteaptă la roșu;
  - profilul pe ciclu al fiecărei ieșiri, ca forme, fiindcă ieșirile nu intră în cerere (afară de un viraj) și au alți factori;
  - cât durează drumul Magheru → Catargiu, care nu depinde nici de cerere, nici de factori;
  - valurile de pe Magheru, unul câte unul;
  - când traversează pietonii pe zebrele de pe Dacia est (din jurnalul local; doar agregat);
  - siguranța: teleportări, ciocniri între vehicule, vehicule în mișcare care ating pietoni, vehicule rămase neintrate.

Exemplu:  python -m romana.control.valideaza_geaman cor_zi_2026-10-26_varf cor_zi_2026-10-26_pranz --out docs/rezultate/validare_geaman.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from romana.bridge.od_estimation import factor_brat
from romana.common import CONFIG_DIR, OUTPUT_DIR, ROOT, TRAJ_DIR, TRAJ_RAW_DIR
from romana.control.rejucat import fereastra_scenariu, valuri
from romana.vision.od_counter import PEDESTRIAN, Params, classify, load_zones
from romana.vision.recount import read_trajectories

BRATE = {"magheru": "668307642#1", "catargiu": "1320256482", "dacia_est": "232079775#2", "dacia_vest": "-778823268#2"}    # muchia dinaintea liniei de oprire
# unde stau zonele camerei în rețea, din proiecție (§ 4.3): zona lui Catargiu e departe de linia de oprire, în mijlocul pieței
PUNCTE_INTRARE = {"catargiu": ("23781788", "122141742#4")}
IESIRI = {"catargiu": ("668307633#0", "668307633#1", "668307633#2"), "magheru": ("44499684#0", "44499684#1", "44499684#2"),
          "dacia_est": ("119238380#0", "119238380#1"), "dacia_vest": ("778823268#0", "778823268#2")}
TRECERE_DACIA_EST = 55
INCALZIRE_S, SFARSIT_S = 300, 3600
BIN_S, BINI = 10, 16
VEHICULE = {"passenger", "truck", "bus", "motorcycle"}
# Pragurile, stabilite înaintea rulărilor de validare: abatere relativă sau valoare maximă pe oră (§ 6.5)
PRAGURI = {"debit": 0.10, "profil_intrare": 0.35, "profil_iesire": 0.35, "drum": 0.25, "primele_20": 0.25, "pietoni_fereastra": 0.15,
           "teleportari": 5, "ciocniri_vehicule": 5, "pieton_in_miscare_fractie": 0.01, "neintrate_fractie": 0.02}


class Contoare:
    """În geamăn: când pleacă vehiculele de la liniile de oprire, când ajung pe ieșiri și când intră pietonii pe zebra Dacia est."""

    def __init__(self):
        self.brate = {b: [] for b in BRATE}
        self.iesiri = {b: [] for b in IESIRI}
        self.prec = {m: {} for m in BRATE.values()}
        self.vazute = {b: set() for b in IESIRI}
        self.pe_punct: dict[str, set[str]] = {b: set() for b in PUNCTE_INTRARE}    # au trecut de linia de oprire, încă n-au ajuns în dreptul zonei
        self.ramase: dict[str, dict[str, int]] = {b: {} for b in PUNCTE_INTRARE}
        self.drum: dict[str, float] = {}
        self.drumuri: list[float] = []
        self.pietoni: list[int] = []
        self.pe_zebra: set[str] = set()
        self.zebra = None

    def __call__(self, tr, t: int) -> None:
        if self.zebra is None:
            self.zebra = tr.trafficlight.getControlledLinks("romana")[TRECERE_DACIA_EST][0][1].rsplit("_", 1)[0]
        for b, m in BRATE.items():
            acum = {v: self.prec[m].get(v) or tr.vehicle.getTypeID(v) for v in tr.edge.getLastStepVehicleIDs(m)}
            for v, tip in self.prec[m].items():
                if v not in acum and tip in VEHICULE:
                    if b in PUNCTE_INTRARE:
                        self.ramase[b][v] = t
                    else:
                        self.brate[b].append(t)
                    if b == "magheru":
                        self.drum[v] = t
            self.prec[m] = acum
        for b, muchii in PUNCTE_INTRARE.items():
            for m in muchii:
                for v in tr.edge.getLastStepVehicleIDs(m):
                    if self.ramase[b].pop(v, None) is not None:
                        self.brate[b].append(t)
            for v, t0 in list(self.ramase[b].items()):
                if t - t0 > 40:                      # n-a trecut prin dreptul zonei în timp util: se numără la linia de oprire, cu întârzierea obișnuită
                    self.brate[b].append(t0 + 8)
                    del self.ramase[b][v]
        for b, muchii in IESIRI.items():
            for m in muchii:
                for v in tr.edge.getLastStepVehicleIDs(m):
                    if v not in self.vazute[b] and tr.vehicle.getTypeID(v) in VEHICULE:
                        self.vazute[b].add(v)
                        self.iesiri[b].append(t)
                        if b == "catargiu" and v in self.drum:
                            self.drumuri.append(t - self.drum.pop(v))
        pe = set(tr.edge.getLastStepPersonIDs(self.zebra))
        self.pietoni += [t] * len(pe - self.pe_zebra)
        self.pe_zebra = pe


def rezumat_jurnal(sursa, zone: list) -> dict:
    """Din traiectoriile camerei: momentele pe intrări și pe ieșiri, și drumurile complete."""
    params = Params()
    intrari, iesiri = {}, {}
    for z in zone:
        if z.role == "intrare":
            intrari.setdefault(z.arm, []).append(z)
        elif z.role == "iesire":
            iesiri.setdefault(z.arm, []).append(z)
    ev = {b: [] for b in intrari}
    ies = {b: [] for b in iesiri}
    drumuri = []
    for tip, pts in sursa:
        if tip not in VEHICULE or len(pts) < params.min_track_frames:
            continue
        c = classify(tip, pts, zone, params)
        o, d = c.get("origine"), c.get("destinatie")
        t_o = next((t for t, x, y in pts if any(z.contains_norm(x, y) for z in intrari[o])), None) if o else None
        t_d = next((t for t, x, y in pts if any(z.contains_norm(x, y) for z in iesiri[d])), None) if d else None
        if t_o is not None:
            ev[o].append(t_o)
        if t_d is not None:
            ies[d].append(t_d)
        if o == "magheru" and d == "catargiu" and t_o is not None and t_d is not None and t_d > t_o:
            drumuri.append((t_o, t_d - t_o))
    return {"intrari": {b: sorted(v) for b, v in ev.items()}, "iesiri": {b: sorted(v) for b, v in ies.items()}, "drumuri": drumuri}


def camera_zi(zi: str, zone: list) -> dict:
    """Jurnalul public al zilei, rezumat; se calculează o dată."""
    cale = OUTPUT_DIR / "validare" / f"camera_v2_{zi}.json"
    if not cale.exists():
        r = rezumat_jurnal(((tip, pts) for _, tip, pts in read_trajectories([TRAJ_DIR / f"traiectorii_{zi}.jsonl.gz"])), zone)
        cale.parent.mkdir(parents=True, exist_ok=True)
        cale.write_text(json.dumps(r), encoding="utf-8")
    d = json.loads(cale.read_text(encoding="utf-8"))
    return {"intrari": {b: np.array(v) for b, v in d["intrari"].items()}, "iesiri": {b: np.array(v) for b, v in d["iesiri"].items()}, "drumuri": d["drumuri"]}


def pietoni_camera(zi: str, a: float, b: float, zone: list) -> np.ndarray | None:
    """Momentele de intrare pe zebra de ieșire de pe Dacia est, din jurnalul local. Doar pentru un procent agregat; lipsește de pe alte calculatoare."""
    cale = OUTPUT_DIR / "validare" / f"pietoni_{zi}_{int(a)}.npy"
    if cale.exists():
        return np.load(cale)
    brut = TRAJ_RAW_DIR / f"traiectorii_{zi}.jsonl.gz"
    if not brut.exists():
        return None
    z = next(x for x in zone if x.id == "trecere_dacia_est_iesire")
    params = Params()
    out = []
    for t0, tip, pts in read_trajectories([brut]):
        if t0 > b + 60:
            break
        if tip != PEDESTRIAN or t0 < a - 60:
            continue
        if any(i == z.id for _, i in classify(tip, pts, zone, params)["treceri"]):
            t = next((t for t, x, y in pts if z.contains_norm(x, y)), None)
            if t is not None and a <= t < b:
                out.append(t)
    r = np.array(out)
    cale.parent.mkdir(parents=True, exist_ok=True)
    np.save(cale, r)
    return r


def profil(momente: np.ndarray, starturi: np.ndarray) -> np.ndarray:
    """Câte treceri pe ciclu, pe bucăți de 10 s de la începutul valului de pe Magheru."""
    i = np.searchsorted(starturi, momente, side="right") - 1
    d = momente[i >= 0] - starturi[i[i >= 0]]
    return np.histogram(d, bins=np.arange(0, (BINI + 1) * BIN_S, BIN_S))[0] / max(len(starturi), 1)


def abatere_profil(c: np.ndarray, g: np.ndarray) -> float:
    return float(np.abs(c - g).sum() / max(c.sum(), 1e-9))


def fereastra_pietoni(treceri: np.ndarray, starturi: np.ndarray) -> float:
    """Ce parte din treceri cade în secundele 20–70 de la începutul valului de pe Magheru."""
    if len(treceri) == 0 or len(starturi) == 0:
        return float("nan")
    i = np.searchsorted(starturi, treceri, side="right") - 1
    d = treceri[i >= 0] - starturi[i[i >= 0]]
    return float(((d >= 20) & (d < 70)).mean())


def compara(stem: str, strategie: str, seed: int, cfg: Path | None = None) -> pd.DataFrame:
    from romana.control import evaluate as E
    from romana.control.validare import make_controller

    zone = load_zones(json.loads((CONFIG_DIR / "camera_v2.json").read_text(encoding="utf-8")))
    zi, a_ts, _ = fereastra_scenariu(stem)
    a = pd.Timestamp(a_ts, tz="Europe/Bucharest").timestamp()
    cont = Contoare()
    r = E.run_one(cfg or ROOT / "sumo" / "scenarios" / f"{stem}.sumocfg", make_controller(strategie), seed, observator=cont)
    real = camera_zi(zi, zone)
    fact = json.loads((CONFIG_DIR / "demand_v2.json").read_text(encoding="utf-8"))["factor_corectie_detectie"]
    mij = pd.Timestamp(a_ts) + pd.Timedelta(seconds=(INCALZIRE_S + SFARSIT_S) / 2)
    f = {b: factor_brat(fact[b], mij) for b in BRATE}
    n_s = SFARSIT_S - INCALZIRE_S
    interval = lambda m, z=0.0: m[(m >= z + INCALZIRE_S) & (m < z + SFARSIT_S)]  # noqa: E731
    mc = interval(real["intrari"]["magheru"], a) - a
    sc = np.array([s for s, _, _ in valuri(mc)])
    if strategie == "REAL":
        sg = sc                     # același semafor, același ceas
    else:
        sg = np.array([s for s, _, _ in valuri(interval(np.array(cont.brate["magheru"], float)))])
    rand = []

    def adauga(masura, cheie, c, g, prag, tip="relativ"):
        ab = (g - c) / c if tip == "relativ" and c else (g - c)
        rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": masura, "camera": round(float(c), 2), "geaman": round(float(g), 2),
                     "abatere": round(float(ab), 3), "prag": prag, "ok": bool(abs(ab) <= prag) if np.isfinite(ab) else False, "cheie": cheie})

    profile = {}
    for b in BRATE:
        c = interval(real["intrari"][b], a) - a
        g = interval(np.array(cont.brate[b], float))
        adauga(f"debit, veh/h: {b}", "debit", len(c) * f[b] * 3600 / n_s, len(g) * 3600 / n_s, PRAGURI["debit"])
        pc, pg = profil(c, sc) * f[b], profil(g, sg)
        profile[f"intrare {b}"] = (pc, pg)
        rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": f"profil pe ciclu: {b}", "camera": np.nan, "geaman": np.nan, "abatere": round(abatere_profil(pc, pg), 3), "prag": np.nan if b == "dacia_vest" else PRAGURI["profil_intrare"],
                     "ok": abatere_profil(pc, pg) <= PRAGURI["profil_intrare"], "cheie": "profil_intrare"})
    for b in IESIRI:
        c = interval(real["iesiri"][b], a) - a
        g = interval(np.array(cont.iesiri[b], float))
        pc, pg = profil(c, sc), profil(g, sg)
        pc, pg = pc / max(pc.sum(), 1e-9), pg / max(pg.sum(), 1e-9)
        profile[f"ieșire {b}"] = (pc, pg)
        rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": f"forma pe ciclu, ieșirea: {b}", "camera": np.nan, "geaman": np.nan, "abatere": round(abatere_profil(pc, pg), 3), "prag": PRAGURI["profil_iesire"],
                     "ok": abatere_profil(pc, pg) <= PRAGURI["profil_iesire"], "cheie": "profil_iesire"})
    prim_c = np.mean([((mc >= s) & (mc < s + 20)).sum() for s in sc]) * f["magheru"] / 20
    mg = interval(np.array(cont.brate["magheru"], float))
    prim_g = np.mean([((mg >= s) & (mg < s + 20)).sum() for s in sg]) / 20
    adauga("Magheru, primele 20 s din val, veh/s", "primele_20", prim_c, prim_g, PRAGURI["primele_20"])
    dc = [d for t, d in real["drumuri"] if a + INCALZIRE_S <= t < a + SFARSIT_S]
    if len(dc) >= 15 and len(cont.drumuri) >= 15:
        adauga("drumul Magheru → Catargiu, mediană, s", "drum", np.median(dc), np.median(cont.drumuri), PRAGURI["drum"])
    if strategie == "REAL" and len(sc) >= 8:
        muchii = np.r_[sc, sc[-1] + np.median(np.diff(sc))]
        vc, vg = np.histogram(mc, muchii)[0] * f["magheru"], np.histogram(mg, muchii)[0]
        rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": f"Magheru, vehicule pe val, corelație pe {len(sc)} valuri", "camera": round(float(vc.mean()), 1), "geaman": round(float(vg.mean()), 1),
                     "abatere": round(float(np.corrcoef(vc, vg)[0, 1]), 2), "prag": np.nan, "ok": True, "cheie": "corelatie"})
    pc = pietoni_camera(zi, a + INCALZIRE_S, a + SFARSIT_S, zone)
    if pc is not None:
        tg = interval(np.array(cont.pietoni, float))
        adauga("pietoni pe zebra Dacia est, în secundele 20–70", "pietoni_fereastra", fereastra_pietoni(pc - a, sc), fereastra_pietoni(tg, sg), PRAGURI["pietoni_fereastra"], tip="absolut")
    sositi = max(r["vehicule_sosite"], 1)
    for masura, cheie, val, prag in (("teleportări", "teleportari", r["teleportari"], PRAGURI["teleportari"]), ("ciocniri între vehicule", "ciocniri_vehicule", r["ciocniri_vehicule"], PRAGURI["ciocniri_vehicule"]),
                                     ("vehicule în mișcare care ating pietoni, parte din vehicule", "pieton_in_miscare", r["ciocniri_pieton_in_miscare"] / sositi, PRAGURI["pieton_in_miscare_fractie"]),
                                     ("vehicule neintrate sau nesosite la final, parte din vehicule", "neintrate", r["nefinalizate"] / sositi, PRAGURI["neintrate_fractie"])):
        rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": masura, "camera": np.nan, "geaman": round(float(val), 4), "abatere": np.nan, "prag": prag, "ok": bool(val <= prag), "cheie": cheie})
    rand.append({"scenariu": stem, "strategie": strategie, "seed": seed, "masura": "pierdere totală, ore", "camera": np.nan, "geaman": round(float(r["pierdere_totala_h"]), 1), "abatere": np.nan, "prag": np.nan, "ok": True, "cheie": "pierdere"})
    d = pd.DataFrame(rand)
    d.attrs["profile"] = {k: ([round(float(x), 2) for x in c], [round(float(x), 2) for x in g]) for k, (c, g) in profile.items()}
    return d


def una(sarcina: tuple) -> tuple[pd.DataFrame, dict]:
    stem, strategie, seed = sarcina
    import os

    d = os.open(os.devnull, os.O_WRONLY)
    os.dup2(d, 1)
    os.dup2(d, 2)
    r = compara(stem, strategie, seed)
    return r, {"scenariu": stem, "seed": seed, "profile": r.attrs["profile"]}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarii", nargs="+")
    ap.add_argument("--strategie", default="REAL", help="REAL = semaforul real, rejucat; sau PLAN_a_b_c")
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--procese", type=int, default=4)
    ap.add_argument("--out", default=None)
    ap.add_argument("--profile", action="store_true", help="afișează și profilele pe ciclu")
    a = ap.parse_args(argv)
    sarcini = [(s, a.strategie, int(k)) for s in a.scenarii for k in a.seeds.split(",")]
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=min(a.procese, len(sarcini))) as ex:
        rez = list(ex.map(una, sarcini))
    tot = pd.concat([r for r, _ in rez], ignore_index=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_colwidth", 70)
    print(tot.drop(columns=["strategie", "cheie"]).to_string(index=False))
    if a.profile:
        for _, p in rez:
            print(f"\n{p['scenariu']}, seed {p['seed']}: pe ciclu, pe 10 s de la începutul valului de pe Magheru (camera / geamănul)")
            for k, (c, g) in p["profile"].items():
                print(f"  {k:20s} {c}\n  {'':20s} {g}")
    praguri = tot[tot["prag"].notna()]
    print("\nÎn prag, pe tipuri de măsură:\n", praguri.groupby("cheie")["ok"].agg(["sum", "count"]).to_string())
    print(f"\nTotal în prag: {int(praguri['ok'].sum())} din {len(praguri)}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        tot.to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
