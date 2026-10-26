"""Calibrarea camerei pe rețeaua SUMO (replica OSM): planul străzii ↔ imagine și zonele derivate din rețea.

Recalibrarea din 26.10.2026 (§ 4.3) a legat imaginea camerei de rețea prin corespondențe de puncte:
  1. `repere`    – reperele geometrice ale rețelei din jurul pieței, în coordonatele rețelei (X spre est, Y spre
                   nord, metri): capetele și lățimea trecerilor de pietoni, liniile de oprire (capătul fiecărei
                   benzi semaforizate), zonele pietonale și benzile auto; opțional o hartă cu grilă de 5 m, din
                   care se citesc coordonatele oricărui punct.
  2. `potrivire` – din corespondențele imagine (x, y normalizate) ↔ rețea (X, Y), potrivește două modele și îl
                   alege pe cel cu eroarea mediană „lasă-unul-afară” (LOO) mai mică, în pixeli ai cadrului de
                   referință (3288 × 1850):
                     H – omografie a planului străzii (fără distorsiune), RANSAC;
                     K – cameră cu distorsiune radială (k1, k2) pe un singur plan (cv2.calibrateCamera, punctul
                         principal fixat în centru, pixeli pătrați).
                   Scrie model.json și erori.csv (eroarea fiecărui punct, la potrivire și LOO); cu --cadru,
                   și suprapunerile rețelei proiectate peste cadru (benzi, treceri, linii de oprire, zone
                   pietonale, corespondențe).
  3. `zone`      – zonele de numărare derivate din rețea, proiectate în imagine cu modelul: intrarea fiecărui braț
                   (ultimii metri ai benzilor înainte de linia de oprire + primii metri după ea), ieșirea (primii
                   metri ai benzilor de ieșire + ultimii metri ai traseelor care o alimentează), trecerile (zebra
                   cu lățimea reală, axa și zonele de așteptare de la borduri). Poligoanele sunt reuniunea benzilor
                   (rasterizare + contur), deci urmăresc curbele reale; zonele mai mult de jumătate în afara
                   cadrului sau deasupra lui `roi_y` sunt eliminate.

Limite (constatate pe 26.10): în fundal eroarea omografiei este ≈14 px (sub ≈1 m); în prim-planul de lângă cameră
niciun model plan unic nu se potrivește (distorsiunea obiectivului, OSM decalat local), de aceea zonele generate
sunt un punct de plecare – în prim-plan zonele din config/camera.json au fost desenate pe marcajele reale, pe un
fundal median fără vehicule. Rezultatul comenzii `zone` se scrie într-un fișier separat; config/camera.json nu se
modifică automat.

Confidențialitate: suprapunerile conțin cadre ale camerei și se salvează DOAR local (implicit
outputs/calibrare_camera/, exclus din Git); nu se publică. Corespondențele și modelul sunt simple coordonate.

Formatul corespondențelor: {"puncte": [{"img_x", "img_y", "world_x", "world_y", "descriere"}, ...]} (sau direct
lista de puncte); img_x, img_y normalizate la cadru.

Exemple:
  python -m romana.vision.calibrare_camera repere outputs/calibrare_camera/repere.json ^
      --harta outputs/calibrare_camera/harta.png --limite 1000 1180 800 960
  python -m romana.vision.calibrare_camera potrivire corespondente.json --cadru cadru.png
  python -m romana.vision.calibrare_camera zone outputs/calibrare_camera/model.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from romana.common import CONFIG_DIR, NET_DIR, OUTPUT_DIR, load_json

CAL_DIR = OUTPUT_DIR / "calibrare_camera"
CENTRU_PIATA = (26.09674, 44.44688)        # lon, lat – centrul Pieței Romane
CAMERA = (26.097428, 44.446773)            # lon, lat – poziția aproximativă a camerei
RAZA_M = 110.0                             # reperele / trecerile luate în calcul în jurul centrului
PARAMETRI_ZONE = {"intrare_inainte": 12.0, "intrare_dupa": 4.0, "iesire_dupa": 12.0, "iesire_inainte": 3.0,
                  "asteptare_adanc": 2.5, "asteptare_lat": 1.0, "doar_brate": None}


def frame_size() -> tuple[int, int]:
    """Dimensiunile cadrului de referință (config/camera.json → referinta_cadru)."""
    w, h = load_json("camera.json").get("referinta_cadru", [3288, 1850])
    return int(w), int(h)


def read_net(net_file: Path = NET_DIR / "romana.net.xml"):
    import sumolib

    return sumolib.net.readNet(str(net_file), withPedestrianConnections=True, withInternal=True)


# ---------------------------------------------------------------- 1. reperele rețelei

def landmarks(net, radius: float = RAZA_M) -> dict:
    """Trecerile, liniile de oprire, zonele pietonale și benzile auto aflate la cel mult `radius` m de centru."""
    cx, cy = net.convertLonLat2XY(*CENTRU_PIATA)

    def near(shape):
        s = np.array(shape)
        return np.min(np.hypot(s[:, 0] - cx, s[:, 1] - cy)) < radius

    out = {"centru_piata": [cx, cy], "camera": list(net.convertLonLat2XY(*CAMERA)),
           "treceri": [], "linii_oprire": [], "zone_pietonale": [], "benzi": []}
    for e in net.getEdges(withInternal=True):
        shp = e.getShape()
        if not near(shp):
            continue
        fn = e.getFunction()
        if fn == "crossing":
            out["treceri"].append({"id": e.getID(), "capete": [list(shp[0]), list(shp[-1])],
                                   "forma": [list(p) for p in shp], "latime_m": e.getLanes()[0].getWidth()})
        elif fn == "walkingarea":
            out["zone_pietonale"].append({"id": e.getID(), "forma": [list(p) for p in shp]})
        elif fn != "internal":
            for ln in e.getLanes():
                if ln.allows("passenger") or ln.allows("bus"):
                    out["benzi"].append({"id": ln.getID(), "strada": e.getName(), "forma": [list(p) for p in ln.getShape()],
                                         "latime_m": ln.getWidth(), "spre": e.getToNode().getID(),
                                         "de_la": e.getFromNode().getID()})
    seen = set()
    for tl in net.getTrafficLights():
        for inl, _, _ in tl.getConnections():
            p = inl.getShape()[-1]
            if inl.getID() in seen or np.hypot(p[0] - cx, p[1] - cy) >= radius or not inl.allows("passenger"):
                continue
            seen.add(inl.getID())
            out["linii_oprire"].append({"banda": inl.getID(), "strada": inl.getEdge().getName(), "punct": list(p),
                                        "latime_m": inl.getWidth()})
    return out


def landmark_map(net, rep: dict, out_png: Path, limits: tuple[float, float, float, float],
                 radius: float = RAZA_M) -> None:
    """Harta reperelor cu grilă la 5 m (pentru citirea coordonatelor punctelor de corespondență)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cx, cy = rep["centru_piata"]
    x0, x1, y0, y1 = limits
    fig, ax = plt.subplots(figsize=(18, 18 * (y1 - y0) / (x1 - x0)))
    for z in rep["zone_pietonale"]:
        s = np.array(z["forma"])
        ax.fill(s[:, 0], s[:, 1], color="#dddddd", zorder=1)
    for e in net.getEdges(withInternal=True):
        s = np.array(e.getShape())
        if e.getFunction() in ("crossing", "walkingarea") or np.min(np.hypot(s[:, 0] - cx, s[:, 1] - cy)) >= radius:
            continue
        internal = e.getFunction() == "internal"
        for ln in e.getLanes():
            if not (ln.allows("passenger") or ln.allows("bus")):
                continue
            s = np.array(ln.getShape())
            ax.plot(s[:, 0], s[:, 1], color="#9ecae1" if internal else "#08519c", lw=1 if internal else 2, zorder=2)
            if not internal and len(s) >= 2:
                a, b = s[-2], s[-1]
                ax.annotate("", xy=b, xytext=a + (b - a) * 0.6, arrowprops=dict(arrowstyle="->", color="#08519c"), zorder=3)
    for t in rep["treceri"]:
        s = np.array(t["forma"])
        ax.plot(s[:, 0], s[:, 1], color="orange", lw=t["latime_m"] * 3, alpha=0.7, zorder=4)
        ax.text(s[0, 0], s[0, 1], t["id"].split("_")[-1], fontsize=7, color="darkorange", zorder=6)
    for st in rep["linii_oprire"]:
        ax.plot(*st["punct"], "s", color="green", ms=5, zorder=5)
    ax.plot(*rep["camera"], "r*", ms=25, zorder=7)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(np.floor(x0 / 5) * 5, x1, 5))
    ax.set_yticks(np.arange(np.floor(y0 / 5) * 5, y1, 5))
    ax.tick_params(labelsize=6)
    plt.xticks(rotation=90)
    ax.grid(True, alpha=0.35)
    ax.set_title("Rețeaua SUMO în jurul pieței – grilă 5 m (X spre est, Y spre nord); portocaliu = treceri, "
                 "verde = linii de oprire, gri = trotuare/zone pietonale, * = camera")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=85, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 2. potrivirea modelului

def _fit_h(wl, img, idx):
    import cv2

    Hm, _ = cv2.findHomography(wl[idx], img[idx], cv2.RANSAC, 25.0, maxIters=5000)
    return Hm


def _proj_h(Hm, w):
    q = np.c_[w, np.ones(len(w))] @ Hm.T
    return q[:, :2] / q[:, 2:3]


def _fit_k(wl, img, idx, size):
    import cv2

    W, H = size
    objp = np.c_[wl[idx], np.zeros(len(idx))].astype(np.float32)
    imgp = img[idx].astype(np.float32)
    f0 = 0.9 * W
    K0 = np.array([[f0, 0, W / 2], [0, f0, H / 2], [0, 0, 1]], np.float64)
    flags = (cv2.CALIB_USE_INTRINSIC_GUESS | cv2.CALIB_FIX_PRINCIPAL_POINT | cv2.CALIB_FIX_ASPECT_RATIO |
             cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K3)
    _, K, d, rv, tv = cv2.calibrateCamera([objp], [imgp], (W, H), K0, np.zeros(5), flags=flags)
    return K, d, rv[0], tv[0]


def _proj_k(m, w):
    import cv2

    K, d, rv, tv = m
    q, _ = cv2.projectPoints(np.c_[w, np.zeros(len(w))].astype(np.float32), rv, tv, K, d)
    return q.reshape(-1, 2)


def read_correspondences(path: Path) -> list[dict]:
    corr = json.loads(Path(path).read_text(encoding="utf-8"))
    return corr["puncte"] if isinstance(corr, dict) else corr


def fit_camera(points: list[dict], size: tuple[int, int] | None = None) -> tuple[dict, dict]:
    """Potrivește modelele H și K și îl alege pe cel cu mediana erorii LOO mai mică.

    Întoarce (model – dicționarul din model.json, detalii – erorile pe puncte ale modelului ales)."""
    W, H = size or frame_size()
    img = np.array([[p["img_x"] * W, p["img_y"] * H] for p in points], np.float64)
    wld = np.array([[p["world_x"], p["world_y"]] for p in points], np.float64)
    O = wld.mean(0)                                   # originea locală (numere mici, stabile numeric)
    wl = wld - O
    n = len(points)
    allidx = np.arange(n)
    candidates = {"H": (lambda i: _fit_h(wl, img, i), _proj_h), "K": (lambda i: _fit_k(wl, img, i, (W, H)), _proj_k)}
    res = {}
    for name, (fit, proj) in candidates.items():
        try:
            m = fit(allidx)
            e_fit = np.hypot(*(proj(m, wl) - img).T)
            loo = np.array([float(np.hypot(*(proj(fit(np.delete(allidx, i)), wl[i:i + 1])[0] - img[i])))
                            for i in range(n)])
            res[name] = {"model": m, "e_fit": e_fit, "loo": loo}
            print(f"{name}: eroare medie {e_fit.mean():.1f} px, mediana LOO {np.median(loo):.1f} px, "
                  f"LOO > 40 px: {[i for i, v in enumerate(loo) if v > 40]}")
        except Exception as ex:                      # prea puține puncte / configurație degenerată
            print(name, "eșuat:", ex)
    if not res:
        raise SystemExit("Niciun model nu a putut fi potrivit (prea puține corespondențe?).")
    best = min(res, key=lambda k: np.median(res[k]["loo"]))
    r = res[best]
    model = {"tip": best, "origine_locala": O.tolist(), "cadru": [W, H],
             "eroare_medie_px": float(r["e_fit"].mean()), "loo_median_px": float(np.median(r["loo"]))}
    if best == "H":
        model["H_lume_locala_spre_pixeli"] = r["model"].tolist()
    else:
        K, d, rv, tv = r["model"]
        model.update({"K": K.tolist(), "dist": d.ravel().tolist(), "rvec": rv.ravel().tolist(), "tvec": tv.ravel().tolist()})
    print("ales:", best)
    return model, {"e_fit": r["e_fit"], "loo": r["loo"]}


def write_errors(points: list[dict], details: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("i,descriere,img_x,img_y,world_x,world_y,eroare_px,loo_px\n")
        for i, p in enumerate(points):
            f.write(f"{i},\"{p.get('descriere', '')}\",{p['img_x']:.4f},{p['img_y']:.4f},{p['world_x']:.2f},"
                    f"{p['world_y']:.2f},{details['e_fit'][i]:.1f},{details['loo'][i]:.1f}\n")


class Proiectie:
    """Proiecția plan stradă (coordonatele rețelei, m) ↔ imagine (normalizată), din modelul calibrat."""

    def __init__(self, model: dict | str | Path):
        import cv2

        m = model if isinstance(model, dict) else json.loads(Path(model).read_text(encoding="utf-8"))
        self.m = m
        self.O = np.array(m["origine_locala"])
        self.W, self.H = m["cadru"]
        if m["tip"] == "H":
            self.Hm = np.array(m["H_lume_locala_spre_pixeli"])
            self.Hi = np.linalg.inv(self.Hm)
        else:
            self.K, self.d = np.array(m["K"]), np.array(m["dist"])
            self.rv, self.tv = np.array(m["rvec"]), np.array(m["tvec"])
            R, _ = cv2.Rodrigues(self.rv)
            self.Hk = self.K @ np.c_[R[:, 0], R[:, 1], self.tv.reshape(3)]   # planul Z = 0, fără distorsiune
            self.Hki = np.linalg.inv(self.Hk)

    def lume_spre_img(self, w) -> np.ndarray:
        """w: N×2 metri → N×2 normalizat; NaN pentru punctele din spatele camerei."""
        import cv2

        w = np.atleast_2d(np.asarray(w, float)) - self.O
        if self.m["tip"] == "H":
            q = np.c_[w, np.ones(len(w))] @ self.Hm.T
            ok = q[:, 2] > 0
            p = q[:, :2] / q[:, 2:3]
        else:
            q = np.c_[w, np.ones(len(w))] @ self.Hk.T
            ok = q[:, 2] > 0
            p, _ = cv2.projectPoints(np.c_[w, np.zeros(len(w))].astype(np.float32), self.rv, self.tv, self.K, self.d)
            p = p.reshape(-1, 2)
        p = p / [self.W, self.H]
        p[~ok] = np.nan
        return p

    def img_spre_lume(self, p) -> np.ndarray:
        """p: N×2 normalizat → N×2 metri (pe planul străzii)."""
        import cv2

        p = np.atleast_2d(np.asarray(p, float)) * [self.W, self.H]
        if self.m["tip"] == "H":
            q = np.c_[p, np.ones(len(p))] @ self.Hi.T
        else:
            u = cv2.undistortPoints(p.reshape(-1, 1, 2).astype(np.float32), self.K, self.d, P=self.K).reshape(-1, 2)
            q = np.c_[u, np.ones(len(u))] @ self.Hki.T
        return q[:, :2] / q[:, 2:3] + self.O


def draw_overlays(frame_path: Path, pr: Proiectie, rep: dict, points: list[dict], out: Path) -> None:
    """Rețeaua proiectată peste cadru (DOAR local): benzi (albastru, săgeată spre linia de oprire), treceri
    (portocaliu, lățimea reală), linii de oprire (verde), zone pietonale (gri), corespondențe (cerc = imagine,
    cruce = proiecția modelului)."""
    import cv2

    W, H = pr.W, pr.H

    def P(w):
        return pr.lume_spre_img(w) * [W, H]

    fr = cv2.imread(str(frame_path))
    if fr is None:
        raise SystemExit(f"Cadrul {frame_path} nu poate fi citit.")
    if fr.shape[1] != W:
        fr = cv2.resize(fr, (W, H))
    ov = fr.copy()
    for z in rep["zone_pietonale"]:
        q = P(z["forma"])
        if not np.isnan(q).any():
            cv2.fillPoly(ov, [q.astype(np.int32)], (200, 200, 200))
    fr = cv2.addWeighted(ov, 0.35, fr, 0.65, 0)
    for b in rep["benzi"]:
        s = np.array(b["forma"])
        q = P(np.vstack([np.linspace(s[i], s[i + 1], 12) for i in range(len(s) - 1)]))
        ok = ~np.isnan(q).any(axis=1) & (q[:, 0] > -W) & (q[:, 0] < 2 * W) & (q[:, 1] > -H) & (q[:, 1] < 2 * H)
        q = q[ok].astype(np.int32)
        if len(q) >= 2:
            cv2.polylines(fr, [q], False, (255, 120, 0), 3)
            cv2.arrowedLine(fr, tuple(map(int, q[-4] if len(q) > 4 else q[0])), tuple(map(int, q[-1])),
                            (255, 200, 0), 3, tipLength=0.4)
    for t in rep["treceri"]:
        a, b = np.array(t["capete"])
        v = b - a
        nrm = np.array([-v[1], v[0]]) / max(np.hypot(*v), 1e-6) * t["latime_m"] / 2
        quad = P([a + nrm, b + nrm, b - nrm, a - nrm])
        if not np.isnan(quad).any():
            cv2.polylines(fr, [quad.astype(np.int32)], True, (0, 140, 255), 3)
    for st in rep["linii_oprire"]:
        c = P([st["punct"]])[0]
        if not np.isnan(c).any():
            cv2.circle(fr, tuple(c.astype(int)), 7, (0, 255, 0), -1)
    for i, p in enumerate(points):
        a = np.array([p["img_x"] * W, p["img_y"] * H]).astype(int)
        b = P([[p["world_x"], p["world_y"]]])[0]
        cv2.circle(fr, tuple(map(int, a)), 12, (0, 0, 255), 3)
        if not np.isnan(b).any():
            b = b.astype(int)
            cv2.drawMarker(fr, tuple(map(int, b)), (255, 0, 255), cv2.MARKER_CROSS, 24, 3)
            cv2.line(fr, tuple(map(int, a)), tuple(map(int, b)), (0, 0, 255), 2)
        cv2.putText(fr, str(i), tuple(map(int, a + 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
    out.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out / "suprapunere_full.jpg"), fr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    regions = {"stanga_jos": (0.0, 0.5, 0.55, 1.0), "dreapta_jos": (0.5, 0.5, 1.0, 1.0),
               "departe_stanga": (0.0, 0.38, 0.5, 0.58), "departe_dreapta": (0.45, 0.37, 0.95, 0.57),
               "centru": (0.25, 0.42, 0.8, 0.75)}
    for k, (x0, y0, x1, y1) in regions.items():
        c = fr[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
        cv2.imwrite(str(out / f"suprapunere_{k}.jpg"), cv2.resize(c, (1900, int(c.shape[0] * 1900 / c.shape[1]))),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"[suprapuneri] {out} (doar local, nu se publică)")


# ---------------------------------------------------------------- 3. zonele din rețea

def cut(shape, start: float, end: float):
    """Porțiunea [start, end] (m) dintr-o polilinie; None dacă e vidă."""
    s = np.asarray(shape, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(s, axis=0).T))]
    start, end = max(0, start), min(d[-1], end)
    if end <= start:
        return None
    ts = np.r_[start, d[(d > start) & (d < end)], end]
    return np.c_[np.interp(ts, d, s[:, 0]), np.interp(ts, d, s[:, 1])]


def ribbon(line, width: float) -> np.ndarray:
    """Poligonul unei benzi: polilinia lărgită cu width/2 de o parte și de alta, densificată."""
    line = np.asarray(line, float)
    line = np.vstack([np.linspace(line[i], line[i + 1], 6, endpoint=False) for i in range(len(line) - 1)] + [line[-1:]])
    t = np.gradient(line, axis=0)
    t /= np.maximum(np.hypot(*t.T), 1e-9)[:, None]
    nrm = np.c_[-t[:, 1], t[:, 0]] * width / 2
    return np.vstack([line + nrm, (line - nrm)[::-1]])


def union_img(pr: Proiectie, polys_world, roi_top: float, approx: float = 0.002):
    """Reuniunea poligoanelor (în metri), proiectată: rasterizare la 1/2 din rezoluție + conturul exterior.

    Întoarce (poligonul normalizat, fracțiunea vizibilă: aria din cadru și sub roi_top / aria proiectată)."""
    import cv2

    S = 0.5
    Wm, Hm = int(pr.W * S), int(pr.H * S)
    mask = np.zeros((Hm, Wm), np.uint8)
    tot = 0.0
    for pw in polys_world:
        q = pr.lume_spre_img(pw)
        if np.isnan(q).any():
            continue
        cv2.fillPoly(mask, [(q * [Wm, Hm]).astype(np.int32)], 255)
        tot += abs(cv2.contourArea((q * [Wm, Hm]).astype(np.float32)))
    inside = mask[int(roi_top * Hm):, :].sum()
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, 0.0
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, approx * Wm, True).reshape(-1, 2) / [Wm, Hm]
    return np.clip(c, 0, 1), min(1.0, inside / 255 / max(tot, 1))


def _lane_ok(ln) -> bool:
    return ln.allows("passenger") or ln.allows("bus")


def vehicle_zones(pr: Proiectie, net, arms: dict, params: dict, roi_top: float) -> tuple[list, list]:
    """Zonele de intrare și de ieșire ale brațelor (config/demand.json → brate)."""
    colors = {"intrare": [0, 255, 0], "iesire": [0, 140, 255]}
    zones, report = [], []
    for arm, d in arms.items():
        if params["doar_brate"] and arm not in params["doar_brate"]:
            continue
        for role in ("intrare", "iesire"):
            eid = d.get(role)
            if not eid:
                continue
            e = net.getEdge(eid)
            polys, dirs = [], []
            for ln in e.getLanes():
                if not _lane_ok(ln):
                    continue
                L = ln.getLength()
                after = []
                if role == "intrare":
                    seg = cut(ln.getShape(), L - params["intrare_inainte"], L)
                    for c in ln.getOutgoing():
                        via = c.getViaLaneID()
                        if via:
                            vl = net.getLane(via)
                            s2 = cut(vl.getShape(), 0, params["intrare_dupa"])
                            if s2 is not None:
                                after.append((s2, vl.getWidth()))
                else:
                    seg = cut(ln.getShape(), 0, params["iesire_dupa"])
                if seg is None:
                    continue
                polys.append(ribbon(seg, ln.getWidth()))
                dirs.append(seg[-1] - seg[0])
                polys += [ribbon(s2, w2) for s2, w2 in after]
            if role == "iesire" and params["iesire_inainte"] > 0:
                # traseele din intersecție care alimentează ieșirea (ultimii metri înaintea benzii de ieșire)
                for src in e.getIncoming():
                    for conn in e.getIncoming()[src]:
                        via = conn.getViaLaneID()
                        if via:
                            vl = net.getLane(via)
                            s2 = cut(vl.getShape(), vl.getLength() - params["iesire_inainte"], vl.getLength())
                            if s2 is not None:
                                polys.append(ribbon(s2, vl.getWidth()))
            if not polys:
                continue
            poly, vis = union_img(pr, polys, roi_top)
            if poly is None:
                continue
            zid = f"{arm}_{'in' if role == 'intrare' else 'out'}"
            report.append((zid, round(vis, 2)))
            if vis < 0.5:
                continue
            # sensul de mers în imagine: direcția medie a benzilor, proiectată în centrul zonei
            cw = np.mean([p.mean(0) for p in polys], axis=0)
            dw = np.mean(dirs, axis=0)
            dw = dw / max(np.hypot(*dw), 1e-9) * 2.0
            a, b = pr.lume_spre_img([cw - dw / 2, cw + dw / 2])
            sens = (b - a) * [pr.W, pr.H]
            sens = (sens / max(np.hypot(*sens), 1e-9)).round(3).tolist()
            zones.append({"id": zid, "arm": arm, "rol": role, "culoare": colors[role], "sens": sens,
                          "poligon": poly.round(4).tolist(),
                          "_sursa": f"muchia {eid}, {'ultimii' if role == 'intrare' else 'primii'} metri ai benzilor"})
    return zones, report


def crossing_zones(pr: Proiectie, net, arms: dict, params: dict, roi_top: float,
                   radius: float = RAZA_M) -> tuple[list, list]:
    """Zonele trecerilor de pietoni din jurul pieței (zebra, axa și zonele de așteptare de la borduri)."""
    arm_edges = {dd[role]: arm for arm, dd in arms.items() for role in ("intrare", "iesire") if dd.get(role)}
    cx, cy = net.convertLonLat2XY(*CENTRU_PIATA)
    zones, report, n_arm = [], [], {}
    for e in sorted(net.getEdges(withInternal=True), key=lambda x: x.getID()):
        if e.getFunction() != "crossing":
            continue
        shp = np.array(e.getShape())
        if np.min(np.hypot(shp[:, 0] - cx, shp[:, 1] - cy)) > radius:
            continue
        w = e.getLanes()[0].getWidth()
        a, b = shp[0], shp[-1]
        u = (b - a) / max(np.hypot(*(b - a)), 1e-9)
        nrm = np.array([-u[1], u[0]])
        zebra = np.array([a + nrm * w / 2, b + nrm * w / 2, b - nrm * w / 2, a - nrm * w / 2])
        poly, vis = union_img(pr, [zebra], roi_top, approx=0.001)
        crossed = [x.getID() for x in e.getCrossingEdges()] if hasattr(e, "getCrossingEdges") else []
        arm = next((arm_edges[x] for x in crossed if x in arm_edges), None)
        if arm is None:                              # trecere peste o legătură internă: brațul cel mai apropiat
            mid = shp.mean(0)
            arm = min(arm_edges.items(), key=lambda kv: np.min(np.hypot(*(np.array(net.getEdge(kv[0]).getShape())
                                                                          - mid).T)))[1]
        n_arm[arm] = n_arm.get(arm, 0) + 1
        zid = f"trecere_{arm}_{n_arm[arm]}"
        report.append((zid, round(vis, 2)))
        if poly is None or vis < 0.5:
            continue
        waits = []
        for end, sgn in ((a, -1), (b, 1)):
            r0, r1 = end + u * sgn * 0.3, end + u * sgn * (0.3 + params["asteptare_adanc"])
            half = nrm * (w / 2 + params["asteptare_lat"])
            q, v = union_img(pr, [np.array([r0 + half, r1 + half, r1 - half, r0 - half])], roi_top, approx=0.001)
            if q is not None and v > 0.5:
                waits.append(q.round(4).tolist())
        zones.append({"id": zid, "arm": arm, "rol": "trecere", "culoare": [255, 120, 0], "poligon": poly.round(4).tolist(),
                      "axa": pr.lume_spre_img([a, b]).ravel().round(4).tolist(), "asteptare": waits,
                      "_sursa": f"trecerea {e.getID()} (lățime {w:.1f} m) peste {','.join(crossed)}"})
    return zones, report


def generate_zones(pr: Proiectie, params: dict | None = None, net=None) -> tuple[dict, list]:
    """Configurația camerei (copia lui config/camera.json) cu zonele derivate din rețea + raportul vizibilității."""
    p = dict(PARAMETRI_ZONE, **(params or {}))
    cam = load_json("camera.json")
    arms = load_json("demand.json")["brate"]
    net = net or read_net()
    roi_top = cam.get("roi_y", [0, 1])[0]
    vz, rep_v = vehicle_zones(pr, net, arms, p, roi_top)
    cz, rep_c = crossing_zones(pr, net, arms, p, roi_top)
    out = dict(cam)
    out["zones"] = vz + cz
    return out, rep_v + rep_c


# ---------------------------------------------------------------- linia de comandă

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("repere", help="reperele rețelei din jurul pieței (+ harta cu grilă de 5 m)")
    r.add_argument("out", nargs="?", default=str(CAL_DIR / "repere.json"))
    r.add_argument("--harta", default=None, help="harta PNG a reperelor")
    r.add_argument("--limite", nargs=4, type=float, metavar=("XMIN", "XMAX", "YMIN", "YMAX"), default=None,
                   help="fereastra hărții, în coordonatele rețelei (implicit ±110 m în jurul centrului)")
    r.add_argument("--raza", type=float, default=RAZA_M)
    p = sub.add_parser("potrivire", help="modelul cameră ↔ plan stradă din corespondențe")
    p.add_argument("corespondente", help="JSON cu punctele img_x, img_y (normalizate) ↔ world_x, world_y (m)")
    p.add_argument("--out", default=str(CAL_DIR), help="directorul pentru model.json, erori.csv și suprapuneri")
    p.add_argument("--cadru", default=None, help="un cadru al camerei pentru suprapuneri (salvate doar local)")
    p.add_argument("--repere", default=None, help="repere.json pentru suprapuneri (implicit calculate din rețea)")
    z = sub.add_parser("zone", help="zonele de numărare derivate din rețea, proiectate cu modelul")
    z.add_argument("model", help="model.json produs de `potrivire`")
    z.add_argument("out", nargs="?", default=str(CAL_DIR / "camera_din_retea.json"),
                   help="fișierul de ieșire (config/camera.json nu se suprascrie automat)")
    z.add_argument("--parametri", default=None, help=f"JSON cu parametrii zonelor (implicit {PARAMETRI_ZONE})")
    args = ap.parse_args(argv)

    if args.cmd == "repere":
        net = read_net()
        rep = landmarks(net, args.raza)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(rep['treceri'])} treceri, {len(rep['linii_oprire'])} linii de oprire, {len(rep['benzi'])} benzi → {out}")
        if args.harta:
            cx, cy = rep["centru_piata"]
            lim = args.limite or (cx - args.raza, cx + args.raza, cy - args.raza, cy + args.raza)
            landmark_map(net, rep, Path(args.harta), tuple(lim), args.raza)
            print(f"[OK] {args.harta}")
    elif args.cmd == "potrivire":
        pts = read_correspondences(Path(args.corespondente))
        model, details = fit_camera(pts)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "model.json").write_text(json.dumps(model, indent=1), encoding="utf-8")
        write_errors(pts, details, out / "erori.csv")
        print(f"[OK] {out / 'model.json'}, {out / 'erori.csv'}")
        if args.cadru:
            rep = (json.loads(Path(args.repere).read_text(encoding="utf-8")) if args.repere
                   else landmarks(read_net()))
            draw_overlays(Path(args.cadru), Proiectie(model), rep, pts, out)
    else:
        params = json.loads(Path(args.parametri).read_text(encoding="utf-8")) if args.parametri else None
        cam, report = generate_zones(Proiectie(args.model), params)
        for k, v in report:
            print(f"{k:34s} vizibil {v:.2f}{'' if v >= 0.5 else '  → eliminată'}")
        out = Path(args.out)
        if out.resolve() == (CONFIG_DIR / "camera.json").resolve():
            raise SystemExit("Zonele generate nu suprascriu config/camera.json: scrieți-le în alt fișier și "
                             "copiați manual zonele verificate.")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(cam, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(cam['zones'])} zone → {out}")


if __name__ == "__main__":
    main()
