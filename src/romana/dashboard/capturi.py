"""Capturile dispeceratului, în stări fixate, fără server și fără colectare: pentru evaluarea din § 8 și pentru figuri.

Pagina reală (versiunea `m1`, neschimbată, sau cea curentă) se încarcă în Chrome fără fereastră, cu cererile către server simulate, ca stările să se poată
repeta: flux normal, cameră veche, server căzut, confirmare și așa mai departe. Imaginea camerei e fotografia publicată, cu persoanele estompate.

Rulare:  python -m romana.dashboard.capturi --versiune m1 --out outputs/evaluare/m1
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import subprocess
from pathlib import Path

from romana.common import CONFIG_DIR, OUTPUT_DIR

RADACINA = Path(__file__).resolve().parents[3]
STATIC = Path(__file__).resolve().parent / "static"
VERSIUNI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "index.html"}
FOTOGRAFIE = RADACINA / "docs" / "imagini" / "camera_piata_romana.jpg"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
RE_FONTURI = re.compile(r'<link rel="preconnect"[^>]*>\s*<link href="https://fonts\.googleapis\.com[^>]*>|<link href="/static/fonturi/fonturi\.css"[^>]*>')

SIMULARI = r"""
<script>
window.__netOK=true; window.__stare=null;
window.fetch=async(url,opt)=>{
  if(!window.__netOK) throw new TypeError("Failed to fetch");
  if(String(url).includes("/api/state")) return {ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(window.__stare))};
  if(String(url).includes("/api/command")) return {ok:true,status:200,json:async()=>({ok:true})};
  throw new TypeError("necunoscut");
};
const __FAZE=%FAZE%;
const __CAM={_varsta_s:0.9,fps:5.94,conectat:true,reconectari:0,vehicule_urmarite:12,
  intrari_veh_h:{dacia_vest:142,dacia_est:105,magheru:577,catargiu:231},
  iesiri_veh_h:{mendeleev:52,dacia_vest:47,dacia_est:147,catargiu:514,magheru:283,caderea_bastiliei:37},
  pietoni_h:{dacia_est:283,catargiu:5},secunde_interval:687};
const __SIM={_varsta_s:0.5,timp_sim:500,mod:"program",mod_program:"plan_scurt",sursa:"camera live",faza:0,faza_nume:__FAZE[0],etapa:"green",verde_s:9,faze:__FAZE,model_ai:true,
  coada_brate:{magheru:3,catargiu:12,dacia_est:5,dacia_vest:21,pietoni:4},coada_total:41,vehicule_in_retea:123,pietoni_in_retea:8,
  istoric_coada:Array.from({length:40},(_,i)=>[i*5,10+Math.round(8*Math.sin(i/4))])};
function __st(cam,sim){ window.__stare={camera:cam,simulare:sim,comanda:null,ora_server:0}; }
__st(__CAM,__SIM);
</script>
"""

# starea → codul care o pregătește, după prima încărcare
STARI = {
    "normal": "",
    "confirmare": 'cere("fix");',
    "confirmare_ai": 'cere("ai");',
    "manual": 'const m=JSON.parse(JSON.stringify(__SIM)); m.mod="manual"; m.mod_program=null; __st(__CAM,m); await actualizeaza();',
    "manual_confirmare": 'const m=JSON.parse(JSON.stringify(__SIM)); m.mod="manual"; m.mod_program=null; __st(__CAM,m); await actualizeaza(); cere("manual",1);',
    "galben": 'const m=JSON.parse(JSON.stringify(__SIM)); m.etapa="yellow"; m.verde_s=12; __st(__CAM,m); await actualizeaza();',
    "rosu_degajare": 'const m=JSON.parse(JSON.stringify(__SIM)); m.etapa="red"; m.verde_s=14; __st(__CAM,m); await actualizeaza();',
    "ai_indisponibil": 'const m=JSON.parse(JSON.stringify(__SIM)); m.model_ai=false; __st(__CAM,m); await actualizeaza();',
    "camera_veche_200s": "__st(Object.assign({},__CAM,{_varsta_s:200}),__SIM); await actualizeaza();",
    "geaman_oprit_50s": "__st(__CAM,Object.assign({},__SIM,{_varsta_s:50})); await actualizeaza();",
    "totul_oprit": "__st(null,null); await actualizeaza();",
    "server_cazut": "window.__netOK=false; await actualizeaza();",
}
# numele stării → lățimea ferestrei, dacă nu e cea implicită
ECRANE = {"telefon_normal": (375, "normal"), "telefon_confirmare": (375, "confirmare"), "tableta_normal": (768, "normal")}


def fazele() -> list[str]:
    return [f["nume"] for f in json.loads((CONFIG_DIR / "network.json").read_text(encoding="utf-8"))["romana_faze"]]


def pagina(sursa: str, cod_stare: str) -> str:
    """Pagina reală, cu cererile simulate, fonturile locale, fotografia în locul fluxului și starea pregătită după încărcare."""
    fonturi = (STATIC / "fonturi" / "fonturi.css").as_uri()
    foto = "data:image/jpeg;base64," + base64.b64encode(FOTOGRAFIE.read_bytes()).decode("ascii")
    simulari = SIMULARI.replace("%FAZE%", json.dumps(fazele(), ensure_ascii=False))
    if "<script>\nconst NUME=" not in sursa:
        raise SystemExit("Pagina nu mai are punctul de injectare `const NUME=`: actualizați capturi.py.")
    p = sursa.replace("<script>\nconst NUME=", simulari + "<script>\nconst NUME=", 1)
    p = RE_FONTURI.sub(f'<link href="{fonturi}" rel="stylesheet">', p)
    p = p.replace('"/api/video"', json.dumps(foto))
    final = ("<script>(async()=>{ await document.fonts.ready; await actualizeaza(); " + cod_stare +
             ' await new Promise(r=>setTimeout(r,300)); document.title="gata"; })();</script>')
    return p.replace("</body>", final + "</body>", 1)


def randeaza(sursa: str, cod_stare: str, cale: Path, latime: int = 1366, inaltime: int = 1500, profil: Path | None = None) -> bool:
    """O captură PNG cu Chrome fără fereastră, la prioritate scăzută, ca să nu încurce colectarea."""
    temp = cale.with_suffix(".html")
    temp.write_text(pagina(sursa, cod_stare), encoding="utf-8")
    cmd = [CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={profil or cale.parent / 'profil'}", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--allow-file-access-from-files", "--virtual-time-budget=6000", f"--window-size={latime},{inaltime}", f"--screenshot={cale}", temp.as_uri()]
    subprocess.run(cmd, capture_output=True, timeout=120, creationflags=getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0))
    temp.unlink(missing_ok=True)
    return cale.exists()


def main(argv=None) -> None:
    import shutil

    import cv2

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versiune", choices=sorted(VERSIUNI), default="m1")
    ap.add_argument("--out", default=None, help="implicit outputs/evaluare/<versiune>")
    ap.add_argument("--inaltime", type=int, default=1500)
    a = ap.parse_args(argv)
    dosar = Path(a.out) if a.out else OUTPUT_DIR / "evaluare" / a.versiune
    dosar.mkdir(parents=True, exist_ok=True)
    sursa = VERSIUNI[a.versiune].read_text(encoding="utf-8")
    lista = [(n, 1366, cod, a.inaltime) for n, cod in STARI.items()] + [(n, w, STARI[s], 2400 if w < 500 else 1800) for n, (w, s) in ECRANE.items()]
    for nume, latime, cod, inaltime in lista:
        png = dosar / f"{nume}.png"
        png.unlink(missing_ok=True)
        ok = randeaza(sursa, cod, png, latime, inaltime)
        if ok:                                   # evaluatorii primesc JPEG, mai mic; PNG-ul nu mai trebuie
            cv2.imwrite(str(dosar / f"{nume}.jpg"), cv2.imread(str(png)), [cv2.IMWRITE_JPEG_QUALITY, 88])
            png.unlink()
        print(f"{nume}: {'gata' if ok else 'EȘEC'}")
    shutil.rmtree(dosar / "profil", ignore_errors=True)
    (dosar / "stari.json").write_text(json.dumps({"versiune": a.versiune, "stari": html.escape(", ".join(n for n, *_ in lista))}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
