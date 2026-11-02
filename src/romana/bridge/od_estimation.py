"""Estimarea matricei origine–destinație a Pieței Romane din numărătorile camerei.

Camera nu poate urmări fiecare vehicul de la intrare până la ieșire (ocluzii, distanță,
stâlpi), așa că se combină trei surse de informație:
  1. numărătorile pe brațe de intrare (cele mai fiabile → totaluri pe linii, T_O);
  2. numărătorile pe brațe de ieșire (→ totaluri pe coloane, U_D);
     cele două sume sunt aduse la media lor (`echilibrare: "medie"`), pentru că ambele sunt
     măsurători imperfecte ale aceluiași debit (camera subnumără intrările de la marginea cadrului
     și supranumără ieșirile spre străzile parțial ascunse); cu `echilibrare: "doar_intrari"`
     (implicit din 25.10.2026) ieșirile nu se folosesc: semaforul controlează doar intrările, iar
     ieșirile brute de pe brațele îndepărtate sunt supranumărate (vehicule pierdute de detector);
  3. virajele complete observate (→ „sămânța” matricei, structura relativă).
Sămânța = viraje observate + w · distribuție a priori (config/demand.json).
Echilibrarea se face cu metoda Furness (IPF – iterative proportional fitting), încheiată
pe linii, astfel încât volumele de intrare măsurate să fie respectate exact.

Referință metodă: Furness (1965); Ortúzar & Willumsen, „Modelling Transport”, cap. 5.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

VTYPES = ["passenger", "bus", "truck", "motorcycle", "bicycle"]


def load_counts(paths: list[Path], start: str | None = None, end: str | None = None) -> pd.DataFrame:
    frames = [pd.read_csv(p, parse_dates=["inceput", "sfarsit"]) for p in paths]
    if not frames:
        raise SystemExit("Nu există fișiere de numărători – rulați întâi modulul de viziune.")
    df = pd.concat(frames, ignore_index=True)
    if start:
        df = df[df["inceput"] >= pd.Timestamp(start)]
    if end:
        df = df[df["sfarsit"] <= pd.Timestamp(end)]
    if df.empty:
        raise SystemExit("Nu există numărători în fereastra de timp cerută.")
    return df


def furness(seed: np.ndarray, rows: np.ndarray, cols: np.ndarray | None, iters: int = 60) -> np.ndarray:
    m = seed.astype(float).copy()
    m[m <= 0] = 1e-9
    for _ in range(iters):
        if cols is not None:
            cs = m.sum(axis=0)
            f = np.divide(cols, cs, out=np.ones_like(cs), where=cs > 0)
            m *= f
        rs = m.sum(axis=1)
        f = np.divide(rows, rs, out=np.zeros_like(rs), where=rs > 0)
        m *= f[:, None]
    return m


def inaltime_soare(moment: datetime, latitudine: float = 44.4478, longitudine: float = 26.0979) -> float:
    """Înălțimea Soarelui deasupra orizontului, în grade, la Piața Romană; `moment` e ora locală a Bucureștiului, ca în numărători."""
    an = moment.year
    ultima_duminica = lambda luna: max(d for d in (datetime(an, luna, z) for z in range(25, 32)) if d.weekday() == 6)
    vara = ultima_duminica(3).replace(hour=3) <= moment < ultima_duminica(10).replace(hour=4)
    ore_utc = moment.hour + moment.minute / 60 + moment.second / 3600 - (3 if vara else 2)
    g = 2 * math.pi / 365 * (moment.timetuple().tm_yday - 1 + (ore_utc - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    ecuatia_min = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    unghi_orar = math.radians((ore_utc * 60 + ecuatia_min + 4 * longitudine) / 4 - 180)
    lat = math.radians(latitudine)
    return math.degrees(math.asin(math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(unghi_orar)))


def factor_brat(valoare, moment) -> float:
    """Factorul unui braț: un număr sau, în măsura nouă, {"zi": ..., "intuneric": ...}, după cum e Soarele deasupra orizontului sau nu."""
    if isinstance(valoare, dict):
        return float(valoare["zi" if inaltime_soare(pd.Timestamp(moment).to_pydatetime()) > -0.833 else "intuneric"])
    return float(valoare)


def aplica_cote_fixe(seed: np.ndarray, origins: list[str], arms: list[str], cote: dict) -> np.ndarray:
    """Cote măsurate direct, pe care traiectoriile nu le pot arăta: pentru un braț de intrare, destinația → fracțiunea din intrările lui. Restul
    destinațiilor își păstrează proporțiile dintre ele."""
    seed = seed.copy()
    for o, fixe in cote.items():
        i, rand = origins.index(o), seed[origins.index(o)].copy()
        rest = [j for j, d in enumerate(arms) if d not in fixe]
        total = rand.sum() or 1.0
        rand_rest = rand[rest].sum()
        for j in rest:
            seed[i, j] = (1 - sum(fixe.values())) * total * (rand[j] / rand_rest if rand_rest > 0 else 1 / len(rest))
        for d, c in fixe.items():
            seed[i, arms.index(d)] = c * total
    return seed


def estimate_interval(sub: pd.DataFrame, cfg: dict, hours: float) -> dict:
    """OD (veh/h) pentru un interval de numărare."""
    arms = list(cfg["brate"])
    origins = [a for a in arms if cfg["brate"][a]["intrare"]]
    # factorul de corecție a detecției: un număr pentru toate brațele sau, măsurat pe numărătoarea de referință,
    # câte unul pe fiecare braț de intrare (raportul referință / numărătoarea automată)
    corr_cfg = cfg.get("factor_corectie_detectie", 1.0)
    moment = sub["inceput"].iloc[0] if isinstance(corr_cfg, dict) and len(sub) else None
    corr_in = np.array([factor_brat(corr_cfg.get(o, 1.0), moment) if isinstance(corr_cfg, dict) else corr_cfg for o in origins], dtype=float)
    corr = float(np.mean(corr_in))
    def get(tip, o=None, d=None):
        m = sub["tip"] == tip
        if o:
            m &= sub["origine"] == o
        if d:
            m &= sub["destinatie"] == d
        return float(sub.loc[m, "numar"].sum())

    raw_in = np.array([get("intrare", o) for o in origins], dtype=float)
    rows = raw_in * corr_in / hours
    cols = np.array([get("iesire", "", d) for d in arms], dtype=float) * corr / hours
    obs = np.array([[get("viraj", o, d) for d in arms] for o in origins], dtype=float) / hours
    prior = np.array([[cfg["prior_destinatii"].get(o, {}).get(d, 0.0) for d in arms] for o in origins])
    prior = prior / prior.sum(axis=1, keepdims=True)
    seed = obs + cfg.get("pondere_prior", 2.0) * prior / hours
    cote = dict(cfg.get("cote_fixe") or {})
    # viraje pe care camera le vede aproape pe toate: numărul lor e o măsură directă, iar din proporții ar ieși umflate, fiindcă celelalte
    # destinații, mai îndepărtate, ajung mult mai rar la traiectorii complete (§ 4.3)
    for o, dest in (cfg.get("viraje_numarate") or {}).items():
        total = rows[origins.index(o)]
        if total > 0:
            cote[o] = {**cote.get(o, {}), **{d: min(0.9, get("viraj", o, d) * k / hours / total) for d, k in dest.items()}}
    if cote:
        seed = aplica_cote_fixe(seed, origins, arms, cote)
    use_cols = None
    measured_in, measured_out = rows.sum(), cols.sum()
    if cfg.get("echilibrare") == "doar_intrari":
        # semaforul controlează doar intrările: volumele vin din intrări, proporțiile de viraj din traiectoriile
        # complete + distribuția a priori; ieșirile brute (supranumărate pe brațele îndepărtate) nu se folosesc
        use_cols = None
    elif cols.sum() > 0 and rows.sum() > 0:
        # Intrările și ieșirile sunt două măsurători ale aceluiași debit (stocarea pe inel e neglijabilă
        # la 15 min). „medie”: totalul = media celor două sume, iar fiecare parte își păstrează
        # distribuția pe brațe; „intrari”: se ține de intrări (varianta inițială).
        target = (rows.sum() + cols.sum()) / 2 if cfg.get("echilibrare", "medie") == "medie" else rows.sum()
        rows = rows * target / rows.sum()
        use_cols = cols * target / cols.sum()
        use_cols = np.where(use_cols > 0, use_cols, 1e-6)
    od = furness(seed, rows, use_cols)
    # ponderi pe tipuri de vehicule (din intrări)
    by_cls = sub[sub["tip"] == "intrare"].groupby("vehicul")["numar"].sum()
    by_cls = by_cls[by_cls.index != "pieton"]
    shares = (by_cls / by_cls.sum()).to_dict() if by_cls.sum() > 0 else {"passenger": 1.0}
    complete = obs.sum() * hours
    ped = float(sub.loc[sub["tip"] == "pietoni", "numar"].sum()) * cfg.get("factor_extrapolare_pietoni", 1.0) * cfg.get("factor_pietoni_masurati", 1.0) / hours
    return {"origini": origins, "destinatii": arms, "od_veh_h": od.round(1).tolist(),
            "intrari_veh_h": dict(zip(origins, rows.round(1).tolist())),
            "iesiri_veh_h": dict(zip(arms, cols.round(1).tolist())),
            "pondere_clase": {k: round(v, 3) for k, v in shares.items()},
            "viraje_complete": int(complete), "pietoni_h": round(ped, 1),
            "intrari_masurate_veh_h": round(float(measured_in), 1), "iesiri_masurate_veh_h": round(float(measured_out), 1),
            "intrari_numarate": int(raw_in.sum())}


def estimate(df: pd.DataFrame, cfg: dict) -> list[dict]:
    out = []
    for (s, e), sub in df.groupby(["inceput", "sfarsit"]):
        hours = max((e - s).total_seconds(), 60) / 3600
        rec = estimate_interval(sub, cfg, hours)
        rec.update({"inceput": str(s), "sfarsit": str(e), "durata_s": int(hours * 3600)})
        out.append(rec)
    return out


def reference_profile(cfg: dict, n_intervals: int = 4, interval_s: int = 900) -> list[dict]:
    """Scenariul ipotetic de referință (până la existența datelor reale de zi)."""
    ref = cfg["profil_referinta"]
    arms = list(cfg["brate"])
    origins = [a for a in arms if cfg["brate"][a]["intrare"]]
    rows = np.array([ref["intrari_veh_h"][o] for o in origins], dtype=float)
    prior = np.array([[cfg["prior_destinatii"][o].get(d, 0.0) for d in arms] for o in origins])
    od = prior / prior.sum(axis=1, keepdims=True) * rows[:, None]
    shape = [0.9, 1.05, 1.1, 0.95]  # profil intra-oră (vârf la mijlocul orei)
    recs = []
    for i in range(n_intervals):
        f = shape[i % len(shape)]
        recs.append({"origini": origins, "destinatii": arms, "od_veh_h": (od * f).round(1).tolist(),
                     "intrari_veh_h": dict(zip(origins, (rows * f).round(1).tolist())),
                     "pondere_clase": ref["pondere_clase"], "viraje_complete": 0,
                     "pietoni_h": ref.get("pietoni_h", 0) * f,
                     "inceput": f"ref+{i * interval_s}s", "sfarsit": f"ref+{(i + 1) * interval_s}s",
                     "durata_s": interval_s})
    return recs


def summarize(recs: list[dict]) -> dict:
    tot = defaultdict(float)
    dur = sum(r["durata_s"] for r in recs)
    for r in recs:
        for i, o in enumerate(r["origini"]):
            for j, d in enumerate(r["destinatii"]):
                tot[(o, d)] += r["od_veh_h"][i][j] * r["durata_s"] / 3600
    return {"vehicule_total": round(sum(tot.values())), "durata_s": dur,
            "od_vehicule": {f"{o}>{d}": round(v) for (o, d), v in sorted(tot.items()) if v >= 0.5}}
