"""Estimarea matricei origine–destinație a Pieței Romane din numărătorile camerei.

Camera nu poate urmări fiecare vehicul de la intrare până la ieșire (ocluzii, distanță,
stâlpi), așa că se combină trei surse de informație:
  1. numărătorile pe brațe de intrare (cele mai fiabile → totaluri pe linii, T_O);
  2. numărătorile pe brațe de ieșire (→ totaluri pe coloane, U_D, scalate la ΣT);
  3. virajele complete observate (→ „sămânța” matricei, structura relativă).
Sămânța = viraje observate + w · distribuție a priori (config/demand.json).
Echilibrarea se face cu metoda Furness (IPF – iterative proportional fitting), încheiată
pe linii, astfel încât volumele de intrare măsurate să fie respectate exact.

Referință metodă: Furness (1965); Ortúzar & Willumsen, „Modelling Transport”, cap. 5.
"""
from __future__ import annotations

from collections import defaultdict
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


def estimate_interval(sub: pd.DataFrame, cfg: dict, hours: float) -> dict:
    """OD (veh/h) pentru un interval de numărare."""
    arms = list(cfg["brate"])
    origins = [a for a in arms if cfg["brate"][a]["intrare"]]
    corr = cfg.get("factor_corectie_detectie", 1.0)
    def get(tip, o=None, d=None):
        m = sub["tip"] == tip
        if o:
            m &= sub["origine"] == o
        if d:
            m &= sub["destinatie"] == d
        return float(sub.loc[m, "numar"].sum())

    rows = np.array([get("intrare", o) for o in origins], dtype=float) * corr / hours
    cols = np.array([get("iesire", "", d) for d in arms], dtype=float) * corr / hours
    obs = np.array([[get("viraj", o, d) for d in arms] for o in origins], dtype=float) / hours
    prior = np.array([[cfg["prior_destinatii"].get(o, {}).get(d, 0.0) for d in arms] for o in origins])
    prior = prior / prior.sum(axis=1, keepdims=True)
    seed = obs + cfg.get("pondere_prior", 2.0) * prior / hours
    use_cols = None
    if cols.sum() > 0 and rows.sum() > 0:
        use_cols = cols * rows.sum() / cols.sum()
        use_cols = np.where(use_cols > 0, use_cols, 1e-6)
    od = furness(seed, rows, use_cols)
    # ponderi pe tipuri de vehicule (din intrări)
    by_cls = sub[sub["tip"] == "intrare"].groupby("vehicul")["numar"].sum()
    shares = (by_cls / by_cls.sum()).to_dict() if by_cls.sum() > 0 else {"passenger": 1.0}
    complete = obs.sum() * hours
    return {"origini": origins, "destinatii": arms, "od_veh_h": od.round(1).tolist(),
            "intrari_veh_h": dict(zip(origins, rows.round(1).tolist())),
            "iesiri_veh_h": dict(zip(arms, cols.round(1).tolist())),
            "pondere_clase": {k: round(v, 3) for k, v in shares.items()},
            "viraje_complete": int(complete),
            "intrari_numarate": int(rows.sum() * hours / corr)}


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
