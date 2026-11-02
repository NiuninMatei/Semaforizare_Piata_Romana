"""Programul real al semaforului, măsurat din jurnalul vehiculelor, fără acces la controler (§ 6.3).

Vehiculele trec printr-o zonă de intrare în valuri, după cum au verde. Momentele de trecere se repetă deci cu ciclul semaforului:
  1. din jurnalul publicat al zilei, fiecare vehicul primește brațul de origine, ca la numărare, și momentul în care a intrat în zonă;
  2. pe ferestre de 10 minute, ciclul este perioada cu cea mai mare putere a momentelor de pe Magheru, brațul cel mai încărcat;
  3. momentele din fereastră se pliază pe ciclu: se păstrează doar poziția lor în ciclu, deci valurile se suprapun;
  4. cât curge un braț este cel mai lung șir continuu peste jumătate din debitul lui de vârf.

Durata curgerii e o margine de jos a verdelui: la trafic slab, coada se golește înainte de sfârșitul verdelui. Debitele sunt cele
detectate, fără factorii de corecție. Se lucrează doar cu traiectoriile vehiculelor, deci nu se folosesc pietoni sau imagini.

Exemple:
  python -m romana.vision.program_real --zi 2026-11-01 --interval 12:00-14:00 --interval 19:00-21:00
  python -m romana.vision.program_real --zi 2026-11-01 --pe-zi --out docs/rezultate/program_real_2026-11-01.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from romana.common import CONFIG_DIR, TRAJ_DIR
from romana.vision.od_counter import Params, classify, load_zones
from romana.vision.recount import read_trajectories

FEREASTRA_S = 600
BUCATI = 100                                     # un ciclu se împarte în atâtea bucăți, oricât ar dura
PERIOADE = np.arange(100.0, 200.0, 0.25)         # căutarea ciclului, în secunde
BRAT_REPER = "magheru"
MIN_VEHICULE = 30                                # sub atâtea treceri, o fereastră nu are un ciclu de încredere
VEHICULE = {"passenger", "truck", "bus", "motorcycle"}


def evenimente(fisier: Path, zone: list, params: Params | None = None) -> dict[str, np.ndarray]:
    """Brațul de origine → momentele (timp Unix) la care vehiculele au intrat în zona lui de intrare."""
    params = params or Params()
    intrari: dict[str, list] = {}
    for z in zone:
        if z.role == "intrare":
            intrari.setdefault(z.arm, []).append(z)
    ev: dict[str, list[float]] = {b: [] for b in intrari}
    for _, tip, pts in read_trajectories([fisier]):
        if tip not in VEHICULE or len(pts) < params.min_track_frames:
            continue
        origine = classify(tip, pts, zone, params)["origine"]
        if origine:
            ev[origine].append(next(t for t, x, y in pts if any(z.contains_norm(x, y) for z in intrari[origine])))
    return {b: np.sort(np.array(v)) for b, v in ev.items()}


def ciclu(momente: np.ndarray, de_la: float | None = None, durata: float | None = None) -> tuple[float, float]:
    """(perioada, tăria) dintr-o fereastră: perioada la care momentele se adună cel mai bine; tăria e 0 fără valuri și 1 cu valuri perfecte.
    Din sumă se scade ce ar da un debit constant pe fereastră, altfel marginile ferestrei împing perioada cu câteva secunde."""
    de_la = float(momente[0]) if de_la is None else de_la
    durata = float(momente[-1] - momente[0]) if durata is None else durata
    w = 2 * np.pi / PERIOADE
    s = np.exp(1j * w[:, None] * (momente[None, :] - de_la)).sum(1)
    s -= len(momente) * (np.exp(1j * w * durata) - 1) / (1j * w * durata)
    z = np.abs(s) / len(momente)
    i = int(np.argmax(z))
    return float(PERIOADE[i]), float(z[i])


def pliaza(momente: np.ndarray, inceput: float, durata: float, perioada: float) -> np.ndarray:
    """Debitul mediu (vehicule pe secundă) pe bucățile ciclului."""
    h, _ = np.histogram(((momente - inceput) % perioada) / perioada, bins=BUCATI, range=(0, 1))
    return h / (durata / perioada) / (perioada / BUCATI)


def _neteda(p: np.ndarray, n: int = 3) -> np.ndarray:
    return np.convolve(np.r_[p, p, p], np.ones(n) / n, "same")[len(p):2 * len(p)]


def curgere(profil: np.ndarray, perioada: float) -> dict:
    """Vârful (media celor mai mari 5 bucăți), cel mai lung șir continuu peste jumătate din vârf și unde începe el, în secunde."""
    n = _neteda(profil)
    varf = float(np.sort(n)[-5:].mean())
    peste = n > 0.5 * varf
    if peste.all():
        return {"varf_veh_s": round(varf, 2), "curge_s": round(perioada, 1), "de_la_s": 0.0, "veh_pe_ciclu": round(float(profil.sum() * perioada / BUCATI), 1)}
    start = int(np.argmin(peste))                # un loc unde nu curge, ca șirurile să nu fie tăiate de capătul ciclului
    p = np.roll(peste, -start)
    best, unde, cur = 0, 0, 0
    for i, x in enumerate(p):
        cur = cur + 1 if x else 0
        if cur > best:
            best, unde = cur, i - cur + 1
    return {"varf_veh_s": round(varf, 2), "curge_s": round(best / BUCATI * perioada, 1), "de_la_s": round((unde + start) % BUCATI / BUCATI * perioada, 1),
            "veh_pe_ciclu": round(float(profil.sum() * perioada / BUCATI), 1)}


def interval(ev: dict[str, np.ndarray], de_la: float, pana_la: float) -> dict:
    """Pe un interval: ciclul median pe ferestre, profilul mediu al fiecărui braț, aliniat după brațul de reper, și curgerea lui."""
    profile: dict[str, list] = {b: [] for b in ev}
    cicluri, tarii = [], []
    for a in np.arange(de_la, pana_la, FEREASTRA_S):
        reper = ev[BRAT_REPER][(ev[BRAT_REPER] >= a) & (ev[BRAT_REPER] < a + FEREASTRA_S)]
        if len(reper) < MIN_VEHICULE:
            continue
        T, z = ciclu(reper, a, FEREASTRA_S)
        cicluri.append(T)
        tarii.append(z)
        dec = 0
        for b, m in ev.items():
            p = pliaza(m[(m >= a) & (m < a + FEREASTRA_S)], a, FEREASTRA_S, T)
            if b == BRAT_REPER and profile[b]:            # ferestrele încep în alt punct al ciclului: se aliniază după reper
                ref = np.mean(profile[b], axis=0)
                dec = int(np.argmax(np.fft.irfft(np.fft.rfft(ref) * np.conj(np.fft.rfft(p)), BUCATI)))
            profile[b].append(p)
        for b in profile:
            profile[b][-1] = np.roll(profile[b][-1], dec)
    if not cicluri:
        return {}
    T = float(np.median(cicluri))
    medii = {b: np.mean(v, axis=0) for b, v in profile.items()}
    return {"ciclu_s": round(T, 1), "ciclu_min_s": round(min(cicluri), 1), "ciclu_max_s": round(max(cicluri), 1), "tarie": round(float(np.median(tarii)), 2),
            "ferestre": len(cicluri), "brate": {b: curgere(p, T) for b, p in medii.items()}, "profile": {b: [round(float(x), 3) for x in p] for b, p in medii.items()}}


CULORI = {"magheru": "#2a78d6", "catargiu": "#eb6834", "dacia_est": "#1baf7a", "dacia_vest": "#eda100"}
NUME = {"magheru": "Magheru", "catargiu": "Lascăr Catargiu", "dacia_est": "Dacia est", "dacia_vest": "Dacia vest"}


def figura(r: dict, titlu: str, cale: Path) -> None:
    """Profilul pliat al unui interval: câte vehicule trec pe fiecare intrare, în fiecare moment al ciclului."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    T = r["ciclu_s"]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(BUCATI) / BUCATI * T
    dec = BUCATI // 2 - int(np.argmax(_neteda(np.array(r["profile"]["magheru"]), 25)))     # etapa Magheru–Catargiu la mijlocul figurii
    for b, c in CULORI.items():
        y = np.roll(_neteda(np.array(r["profile"][b]), 3), dec)
        ax.plot(x, y, color=c, linewidth=2, label=NUME[b])
    ax.set_xlim(0, T)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("secunde în ciclu")
    ax.set_ylabel("vehicule pe secundă")
    ax.set_title(titlu, fontsize=11, loc="left")
    ax.grid(axis="y", color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18), fontsize=9)
    fig.tight_layout()
    fig.savefig(cale, dpi=130)
    plt.close(fig)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zi", required=True)
    ap.add_argument("--camera", default=str(CONFIG_DIR / "camera_v2.json"))
    ap.add_argument("--jurnal", default=None, help="implicit jurnalul publicat al zilei")
    ap.add_argument("--interval", action="append", default=[], metavar="HH:MM-HH:MM")
    ap.add_argument("--pe-zi", action="store_true", help="ciclul pe fiecare 20 de minute din zi")
    ap.add_argument("--out", default=None, help="CSV cu rezultatele de pe intervale și de pe zi")
    ap.add_argument("--profile", default=None, help="JSON cu profilele pliate ale intervalelor")
    ap.add_argument("--figura", default=None, help="PNG cu profilul primului interval dat cu --interval")
    a = ap.parse_args(argv)
    zone = load_zones(json.loads(Path(a.camera).read_text(encoding="utf-8")))
    ev = evenimente(Path(a.jurnal) if a.jurnal else TRAJ_DIR / f"traiectorii_{a.zi}.jsonl.gz", zone)
    print(a.zi, {b: len(v) for b, v in ev.items()}, "treceri", flush=True)
    zero = pd.Timestamp(f"{a.zi} 00:00", tz="Europe/Bucharest").timestamp()
    ore = lambda s: zero + sum(int(x) * m for x, m in zip(s.split(":"), (3600, 60)))
    lista = [tuple(i.split("-")) for i in a.interval]
    if a.pe_zi:
        lista += [(f"{m // 60:02d}:{m % 60:02d}", f"{(m + 20) // 60:02d}:{(m + 20) % 60:02d}") for m in range(0, 24 * 60, 20)]
    randuri, profile = [], {}
    for de_la, pana_la in lista:
        r = interval(ev, ore(de_la), ore(pana_la))
        if not r:
            continue
        rand = {"zi": a.zi, "de_la": de_la, "pana_la": pana_la, **{k: r[k] for k in ("ciclu_s", "ciclu_min_s", "ciclu_max_s", "tarie", "ferestre")}}
        for b, c in r["brate"].items():
            rand.update({f"{b}_{k}": v for k, v in c.items()})
        randuri.append(rand)
        profile[f"{de_la}-{pana_la}"] = {"ciclu_s": r["ciclu_s"], **r["profile"]}
        print(f"  {de_la}–{pana_la}: ciclu {r['ciclu_s']} s ({r['ciclu_min_s']}–{r['ciclu_max_s']}), tărie {r['tarie']}; " +
              "; ".join(f"{b}: curge {c['curge_s']:.0f} s, de la {c['de_la_s']:.0f} s, vârf {c['varf_veh_s']} veh/s, {c['veh_pe_ciclu']:.0f} veh/ciclu" for b, c in r["brate"].items()), flush=True)
    if a.figura and a.interval:
        de_la, pana_la = a.interval[0].split("-")
        r = interval(ev, ore(de_la), ore(pana_la))
        figura(r, f"{a.zi}, {de_la}–{pana_la}: ciclu de {r['ciclu_s']:.0f} s", Path(a.figura))
    if a.out and randuri:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in randuri for k in r)))
            w.writeheader()
            w.writerows(randuri)
    if a.profile:
        Path(a.profile).write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
