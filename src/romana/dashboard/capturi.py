"""Capturile dispeceratului, în stări fixate, fără server și fără colectare: pentru evaluarea din § 8 și pentru figuri.

Pagina reală (versiunile `m1` și `m2`, păstrate neschimbate, sau cea curentă) se încarcă în Chrome fără fereastră, cu cererile către server simulate, ca stările să se poată
repeta: flux normal, cameră veche, server căzut, confirmare și așa mai departe. Imaginea camerei e fotografia publicată, cu persoanele estompate.

Rulare:  python -m romana.dashboard.capturi --versiune m1 --out outputs/evaluare/m1
Prezentarea M3, ecranul de acum (cu --versiune m2, cel de „înainte”), implicit în outputs/prezentare/surse_m3/capturi_<versiune>:
         python -m romana.dashboard.capturi --versiune curent --prezentare
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
VERSIUNI = {"m1": STATIC / "m1" / "index.html", "m2": STATIC / "m2" / "index.html", "curent": STATIC / "index.html"}
FOTOGRAFIE = RADACINA / "docs" / "imagini" / "camera_piata_romana.jpg"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
RE_FONTURI = re.compile(r'<link rel="preconnect"[^>]*>\s*<link href="https://fonts\.googleapis\.com[^>]*>|<link href="/static/fonturi/fonturi\.css"[^>]*>')

SIMULARI = r"""
<script>
window.__netOK=true; window.__stare=null; window.__posts=[]; window.__ultimTs=0; window.__senzorOK=true; window.__cereriSenzor=0;
window.fetch=async(url,opt)=>{
  if(!window.__netOK) throw new TypeError("Failed to fetch");
  if(String(url).includes("/api/state")) return {ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(window.__stare))};
  if(String(url).includes("/api/senzor")){ window.__cereriSenzor++;   // starea senzorului: o copie a lui window.__senzor; __senzorOK=false dă eroarea 500 a serverului
    return window.__senzorOK?{ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(window.__senzor))}:{ok:false,status:500,json:async()=>({})}; }
  if(String(url).includes("/api/command")){   // ca serverul: comanda, cu `timestamp`-ul ei (crescător), după care pagina o recunoaște în starea simulării
    const corp=JSON.parse(opt.body); window.__posts.push(corp); window.__ultimTs=Math.max(Date.now()/1000,window.__ultimTs+0.001);
    return {ok:true,status:200,json:async()=>({ok:true,...corp,timestamp:window.__ultimTs})}; }
  throw new TypeError("necunoscut");
};
const __FAZE=%FAZE%;
const __CAM={_varsta_s:0.9,fps:5.94,conectat:true,reconectari:0,vehicule_urmarite:12,
  intrari_veh_h:{dacia_vest:142,dacia_est:105,magheru:577,catargiu:231},
  iesiri_veh_h:{mendeleev:52,dacia_vest:47,dacia_est:147,catargiu:514,magheru:283,caderea_bastiliei:37},
  pietoni_h:{dacia_est:283,catargiu:5},secunde_interval:687};
const __SIM={_varsta_s:0.5,timp_sim:500,mod:"program",mod_program:"plan_observat",sursa:"camera live",faza:0,faza_nume:__FAZE[0],etapa:"green",verde_s:9,faze:__FAZE,model_ai:true,
  coada_brate:{magheru:3,catargiu:12,dacia_est:5,dacia_vest:21,pietoni:4},coada_total:41,vehicule_in_retea:123,pietoni_in_retea:8,
  istoric_coada:Array.from({length:40},(_,i)=>[i*5,10+Math.round(8*Math.sin(i/4))])};
// geamănul de acum publică și pașii schimbării de fază (src/romana/control/pasi.py): __SIM_PASI e __SIM cu ei, cu valorile controlerului real
// (faze.SemaforCuPietoni) la timp_sim 500, după 9 s de verde pe Magheru–Catargiu. __SIM rămâne fără ei, ca un geamăn mai vechi: așa îl folosesc testele (teste-15)
const __SIM_PASI=Object.assign(JSON.parse(JSON.stringify(__SIM)),{pas:"verde",pas_ramas_s:null,faza_tinta:0,pana_la_tinta_s:0,verde_min_s:35,verde_max_s:90,cadenta_s:5,
  citire_peste_s:0,pana_la_faza_s:[0,41,35,41,41],durate_s:{galben:3,rosu:2,degajare:6},comanda_citita_ts:1000});
const __pasi=o=>{ const s=Object.assign(JSON.parse(JSON.stringify(__SIM_PASI)),o); s.etapa={verde:"green",degajare:"green",galben:"yellow",rosu:"red"}[s.pas]; return s };   // etapa, din pas, ca în geamăn
function __st(cam,sim,extra){ window.__stare=Object.assign({camera:cam,simulare:sim,comanda:null,ora_server:0},extra||{}); }   // extra: comanda, comenzi, ora_server
__st(__CAM,__SIM);
// răspunsul de exemplu al lui /api/senzor, cu orele mutate la „acum”: ultimul sfert de oră încheiat, rulările de noapte la 00:15 și 03:30, iar fișa publicată din 6.11
const __SENZOR=(()=>{
  const t=Date.now()/1000, calc=t-2.7, z=n=>String(n).padStart(2,"0"), iso=s=>{ const d=new Date(s*1000); return `${d.getFullYear()}-${z(d.getMonth()+1)}-${z(d.getDate())}T${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}` };
  const m=new Date(); m.setHours(0,0,0,0); const azi=m.getTime()/1000, sfert=Math.floor((calc-120)/900)*900;
  // fiecare rulare de noapte, din ora de acum: ultima încheiată (azi, după ce s-a încheiat, altfel ieri), pentru ziua dinaintea ei, și următoarea pornire, ca serverul
  const noapte=(h,mi,durata,gata)=>{ const p=azi+h*3600+mi*60, baza=t>=azi+gata?azi:azi-86400, pornit=baza+h*3600+mi*60;
    return {zi:iso(baza-86400).slice(0,10),pornit,gata:pornit+durata,urmatoarea:p>t?p:p+86400} };
  const a=noapte(0,15,318,21*60), b=noapte(3,30,599,220*60), noaptea=Math.max(a.gata,b.gata);   // 00:15–00:20:18 și 03:30–03:39:59
  return {calculat_la:calc,memorare_s:5,ora_server:t,verigi:[
    {cheie:"camera",stare:"ok",ultima_dovada:calc-0.3,varsta_s:0.3,prag_s:15,alerta_s:180,rosu_s:600,conectat:true,fps:5.96,prag_fps:3.5,lipsa:false},
    {cheie:"colectarea",stare:"ok",ultima_dovada:sfert,varsta_s:Math.round((calc-sfert)*10)/10,prag_s:1020,rosu_s:3600,interval_s:900,
     sfert:{zi:iso(sfert-900).slice(0,10),inceput:iso(sfert-900).slice(11,16),sfarsit:iso(sfert).slice(11,16),vehicule_intrate:1234,pietoni:266},vehicule_urmarite:82},
    {cheie:"veghea",stare:"ok",ultima_dovada:calc-3.4,varsta_s:3.4,prag_s:180,rosu_s:600,ultimul_rand:iso(calc-3.4).slice(0,16).replace("T"," "),fps:6.01,prag_fps:3.5,pauze_5min:0,prag_pauze:10,
     episoade_30min:0,max_episoade:4,randuri_ora:60,pauze_ora:0,alerta:null},   // o alertă din ultimele 24 h: {ora, semne:[…], dupa_ultimul_rand}, adevărat dacă veghea s-a oprit pe ea
    {cheie:"paznicul",stare:"ok",ultima_dovada:calc-3077.4,varsta_s:3077.4,prag_s:3720,semn_de_viata_s:3600,rosu_s:7200,in_regula:true,text:"în regulă: 2 procese, o colectare, starea are 0 s"},
    {cheie:"noaptea",stare:"ok",ultima_dovada:noaptea,varsta_s:Math.round((calc-noaptea)*10)/10,prag_s:86400,lunga_s:7200,fara_dosare:false,lanturi:[   // atentie: textul unui pas acceptat cu o atenționare;
     // asteapta: "fluxul" (lanțul vechi așteaptă imaginea camerei) sau "lant" (măsura nouă așteaptă prelucrarea pentru măsura veche); prea_lunga: în curs de peste lunga_s;
     // fara_dosare: adevărat dacă pe acest calculator nu e niciun dosar al prelucrărilor de noapte (veriga rămâne „necunoscut”)
     {cheie:"lant",ora:"00:15",zi:a.zi,zi_asteptata:a.zi,stare:"incheiat",rezultat:"gata_fara_simulari",pornit:iso(a.pornit),incheiat_la:iso(a.gata),pasi:6,coduri_nenule:0,urmatoarea:iso(a.urmatoarea),
      atentie:null,asteapta:null,prea_lunga:false},
     {cheie:"lant_cor",ora:"03:30",zi:b.zi,zi_asteptata:b.zi,stare:"incheiat",rezultat:"gata_fara_simulari",pornit:iso(b.pornit),incheiat_la:iso(b.gata),pasi:4,coduri_nenule:0,urmatoarea:iso(b.urmatoarea),
      atentie:null,asteapta:null,prea_lunga:false}]}],
   fisa:{taietura:"2026-11-06T00:00:00",inceput:"2026-11-01T09:04:46",ore:110.92,pondere_minute_cu_cadre:0.98843,fps_mediana:5.98,opriri_anuntate:2,caderi_neprevazute:0,
     pauze:30,episoade_reconectare:10,lanturi_incheiate:6,lanturi_asteptate:6,vehicule:284152,publica:true}};
})();
window.__senzor=JSON.parse(JSON.stringify(__SENZOR));
</script>
"""

# starea → codul care o pregătește, după prima încărcare
STARI = {
    "normal": "",
    "confirmare": 'cere("fix");',
    "confirmare_ai": 'cere("ai");',
    "manual": 'const m=JSON.parse(JSON.stringify(__SIM)); m.mod="manual"; m.mod_program=null; __st(__CAM,m); await actualizeaza();',
    "manual_confirmare": 'const m=JSON.parse(JSON.stringify(__SIM)); m.mod="manual"; m.mod_program=null; __st(__CAM,m); await actualizeaza(); cere("manual",3);',
    "galben": 'const m=JSON.parse(JSON.stringify(__SIM)); m.etapa="yellow"; m.verde_s=12; m.faza_tinta=1; __st(__CAM,m); await actualizeaza();',
    "rosu_degajare": 'const m=JSON.parse(JSON.stringify(__SIM)); m.etapa="red"; m.verde_s=14; m.faza_tinta=1; __st(__CAM,m); await actualizeaza();',
    "ai_indisponibil": 'const m=JSON.parse(JSON.stringify(__SIM)); m.model_ai=false; __st(__CAM,m); await actualizeaza();',
    "camera_veche_200s": "__st(Object.assign({},__CAM,{_varsta_s:200}),__SIM); await actualizeaza();",
    "geaman_oprit_50s": "__st(__CAM,Object.assign({},__SIM,{_varsta_s:50})); await actualizeaza();",
    "totul_oprit": "__st(null,null); await actualizeaza();",
    "server_cazut": "window.__netOK=false; await actualizeaza();",
    # imaginea ascunsă, cu starea senzorului în locul ei; alegerea nu rămâne ținută minte pentru capturile următoare, din același profil
    # (versiunile vechi n-au panoul: m2 doar oprește imaginea, iar m1, fără buton, rămâne ca „normal”)
    "senzor": 'if(!(typeof imagineOprita!="undefined"&&imagineOprita)) document.getElementById("b-imagine")?.click(); '
              'if(typeof citesteSenzorul=="function") await citesteSenzorul(); document.activeElement.blur(); '
              'try{ localStorage.removeItem("dispecerat.imagine") }catch(e){}',
}
# Prezentarea M3 (--prezentare), separat de STARI, ca evaluarea din § 8 să rămână pe aceleași stări. Imaginea camerei e ascunsă, cu starea senzorului
# în locul ei: ce face ?imagine=0, care nu ajunge la pagină într-o ramă srcdoc. Senzorul, ca pe 9.11, la ≈19:30, după prima cădere a sursei
# (outputs/logs/paznic_2026-11-09.log, veghe_2026-11-01.csv): veghea a pornit din nou după alertă, iar ultima notă a paznicului nu e „în regulă”,
# deci paznicul e de urmărit; %FISA% e cea mai nouă fișă, aleasă în main.
SENZOR_M3 = ('{ const s=JSON.parse(JSON.stringify(__SENZOR)), c=s.calculat_la, v=k=>s.verigi.find(x=>x.cheie==k); '
             'Object.assign(v("veghea"),{randuri_ora:44,pauze_ora:1,alerta:{ora:c-990,semne:["fără cadre: niciun cadru prelucrat de 181 s"],dupa_ultimul_rand:false}}); '
             'Object.assign(v("paznicul"),{stare:"atent",in_regula:false,text:"starea s-a refăcut singură înaintea opririi",ultima_dovada:c-643,varsta_s:643}); '
             's.fisa=%FISA%; window.__senzor=s; } ' + STARI["senzor"] + "; ")
# Comanda urmărită pas cu pas, într-un caz lung (48 s de la citire până la verde; cel mai lung caz are 60 s: tests/test_pasi.py), cu pașii
# controlerului real (faze.SemaforCuPietoni, în ordinea buclei din live_twin; aceleași valori ies la rejucarea pe controler): Bd. Dacia,
# cerut la 1 s după ce Magheru–Catargiu a primit verde. Clicul vine după starea 502, simularea citește comanda la 503 și dă verde Daciei la 551.
# Pe ceasul paginii, clicul se mută înapoi cu secundele trecute în simulare (__muta): pagina de acum ține termenul pe timp_sim, dar cea de la M2
# (--versiune m2) oprește urmărirea după 30 s pe ceasul ei, deci aceleași stări dau și imaginea de „înainte”.
PASI_M3 = ('const __P=o=>__pasi(Object.assign({mod:"manual",mod_program:null},o)); let __t=502; '
           'const __muta=t=>{ const d=(t-__t)*1000; __t=t; if(cerere) cerere.la-=d; const i=istoric[istoric.length-1]; if(i) i.la-=d }; '
           '__st(__CAM,__P({timp_sim:502,verde_s:1,citire_peste_s:3,pana_la_faza_s:[0,49,43,49,49]})); await actualizeaza(); '
           'document.querySelector(\'[data-faza="1"]\').click(); await new Promise(r=>setTimeout(r,20)); const __ts=__ultimTs; '
           '__muta(503); __st(__CAM,__P({timp_sim:503,verde_s:2,citire_peste_s:2,pana_la_faza_s:[0,48,42,48,48],comanda_citita_ts:__ts})); await actualizeaza(); ')
DEGAJARE = ('__muta(541); __st(__CAM,__P({timp_sim:541,verde_s:40,pas:"degajare",pas_ramas_s:5,faza_tinta:1,pana_la_tinta_s:10,verde_min_s:10,citire_peste_s:4,'
            'pana_la_faza_s:[35,10,29,35,35],comanda_citita_ts:__ts})); await actualizeaza(); ')
GALBEN = ('__muta(546); __st(__CAM,__P({timp_sim:546,verde_s:45,pas:"galben",pas_ramas_s:3,faza_tinta:1,pana_la_tinta_s:5,verde_min_s:10,citire_peste_s:4,'
          'pana_la_faza_s:[30,5,24,30,30],comanda_citita_ts:__ts})); await actualizeaza(); ')
# verdele Daciei se vede la 551; captura arată 552, cu 1 s de verde, ca „e verde de 0 s” să nu apară pe ecran
APLICAT = ('__muta(551); __st(__CAM,__P({timp_sim:551,faza:1,faza_nume:__FAZE[1],verde_s:0,faza_tinta:1,verde_min_s:10,citire_peste_s:4,'
           'pana_la_faza_s:[25,0,19,25,25],comanda_citita_ts:__ts})); await actualizeaza(); '
           '__st(__CAM,__P({timp_sim:552,faza:1,faza_nume:__FAZE[1],verde_s:1,faza_tinta:1,verde_min_s:10,citire_peste_s:3,'
           'pana_la_faza_s:[24,0,18,24,24],comanda_citita_ts:__ts})); await actualizeaza(); ')
PREZENTARE = {"m3_senzor": SENZOR_M3, "m3_comanda_citita": SENZOR_M3 + PASI_M3, "m3_comanda_degajare": SENZOR_M3 + PASI_M3 + DEGAJARE,
              "m3_comanda_galben": SENZOR_M3 + PASI_M3 + DEGAJARE + GALBEN, "m3_comanda_aplicata": SENZOR_M3 + PASI_M3 + DEGAJARE + GALBEN + APLICAT}
# numele stării → lățimea ferestrei, dacă nu e cea implicită
ECRANE = {"telefon_normal": (375, "normal"), "telefon_confirmare": (375, "confirmare"), "tableta_normal": (768, "normal")}
# figura din documentație (§ 8): fără imaginea camerei și fără indicatorii ei, care aici ar fi inventați
FIGURA = ('document.getElementById("cadru").style.visibility="hidden"; const r=document.getElementById("cadru").parentElement; '
          'r.style.cssText+=";background:#d9dcd8;display:flex;align-items:center;justify-content:center;min-height:300px"; '
          'r.insertAdjacentHTML("afterbegin",\'<span style="position:absolute;color:#4a5560">imaginea camerei: nu apare în figură</span>\');')


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


# textul vizibil al paginii, ținut la zi într-un element ascuns al ramei, de unde îl ia a doua trecere a lui Chrome (--dump-dom)
TEXT_VIZIBIL = (' try{ const e=parent.document.createElement("pre"); e.id="__text"; e.hidden=true; parent.document.body.appendChild(e); '
                'const f=()=>{ e.textContent=document.body.innerText }; f(); setInterval(f,200) }catch(_){} ')


def randeaza(sursa: str, cod_stare: str, cale: Path, latime: int = 1366, inaltime: int = 1500, profil: Path | None = None,
             text: Path | None = None) -> bool:
    """O captură PNG cu Chrome fără fereastră, la prioritate scăzută, ca să nu încurce colectarea. Pagina stă într-o ramă de lățimea cerută:
    fereastra fără cadru are cel puțin 500 px, deci sub această lățime pagina s-ar așeza la 500 px, iar captura ar tăia-o.
    Cu `text`, o a doua trecere scrie acolo textul vizibil al aceleiași stări: verificarea frazelor nu poate citi textul din imagini."""
    cale = cale.resolve()            # Chrome se blochează cu un dosar de profil dat relativ
    temp = cale.with_suffix(".html")
    if text is not None:
        cod_stare += TEXT_VIZIBIL
    rama = f"<!doctype html><meta charset='utf-8'><style>body{{margin:0}}iframe{{border:0;display:block}}</style><iframe width='{latime}' height='{inaltime}' srcdoc=\"{html.escape(pagina(sursa, cod_stare), quote=True)}\"></iframe>"
    temp.write_text(rama, encoding="utf-8")
    # fără cererile de fundal ale lui Chrome (actualizări de componente și altele): captura nu iese în rețea și nu se lungește din cauza lor
    cmd = [CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={profil or cale.parent / 'profil'}", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--disable-background-networking", "--disable-component-update", "--allow-file-access-from-files",
           "--virtual-time-budget=6000", f"--window-size={max(latime, 500)},{inaltime}"]
    incet = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    subprocess.run(cmd + [f"--screenshot={cale}", temp.as_uri()], capture_output=True, timeout=120, creationflags=incet)
    if text is not None:
        text.unlink(missing_ok=True)
        dom = subprocess.run(cmd + ["--dump-dom", temp.as_uri()], capture_output=True, timeout=120, creationflags=incet).stdout.decode("utf-8", "replace")
        gasit = re.search(r'<pre id="__text"[^>]*>(.*?)</pre>', dom, re.S)
        if gasit:
            text.write_text(html.unescape(gasit.group(1)), encoding="utf-8")
    temp.unlink(missing_ok=True)
    return cale.exists()


def main(argv=None) -> None:
    import shutil

    import cv2

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versiune", choices=sorted(VERSIUNI), default="m1")
    ap.add_argument("--out", default=None, help="implicit outputs/evaluare/<versiune>; cu --prezentare, outputs/prezentare/surse_m3/capturi_<versiune>")
    ap.add_argument("--inaltime", type=int, default=1500)
    ap.add_argument("--figura", default=None, help="doar figura din documentație, în acest fișier JPEG, și nimic altceva")
    ap.add_argument("--prezentare", action="store_true", help="doar stările prezentării M3 (PREZENTARE), fără ecranele mici")
    ap.add_argument("--fisa", default=None, help="cu --prezentare: dosarul fișelor locale, în locul lui outputs/fisa_senzor; o fișă de aici e „nepublicată”")
    a = ap.parse_args(argv)
    fisa = None
    if a.prezentare:
        if a.versiune == "m1":
            raise SystemExit("Pagina M1 nu urmărește comenzile: --prezentare merge cu --versiune curent sau m2.")
        from romana.dashboard import senzor        # doar citire: cea mai nouă fișă, ca în panoul de pe server
        fisa = senzor.ultima_fisa((senzor.FISE[0], Path(a.fisa)) if a.fisa else senzor.FISE)
        if a.versiune == "curent" and (not fisa or fisa.get("caderi_sursa") is None):
            raise SystemExit("Cea mai nouă fișă a senzorului nu numără căderile sursei camerei (o fișă de dinainte de 10.11): refaceți-o sau dați --fisa.")
    implicit = OUTPUT_DIR / "prezentare" / "surse_m3" / f"capturi_{a.versiune}" if a.prezentare else OUTPUT_DIR / "evaluare" / a.versiune
    dosar = Path(a.out) if a.out else implicit
    dosar.mkdir(parents=True, exist_ok=True)
    sursa = VERSIUNI[a.versiune].read_text(encoding="utf-8")
    if a.figura:
        png = dosar / "figura.png"
        if not randeaza(sursa, FIGURA, png, 1366, a.inaltime):
            raise SystemExit("Captura figurii n-a reușit.")
        imagine = cv2.imread(str(png))
        randuri = (imagine.astype(int) - imagine[-1, -1].astype(int)).any(axis=2).any(axis=1).nonzero()[0]     # taie fundalul gol de jos
        cv2.imwrite(a.figura, imagine[: randuri[-1] + 16], [cv2.IMWRITE_JPEG_QUALITY, 88])
        png.unlink()
        shutil.rmtree(dosar / "profil", ignore_errors=True)
        print(f"figura: {a.figura}")
        return
    if a.prezentare:
        lista = [(n, 1366, cod.replace("%FISA%", json.dumps(fisa, ensure_ascii=False)), a.inaltime) for n, cod in PREZENTARE.items()]
    else:
        lista = [(n, 1366, cod, a.inaltime) for n, cod in STARI.items()] + [(n, w, STARI[s], 2400 if w < 500 else 1800) for n, (w, s) in ECRANE.items()]
    for nume, latime, cod, inaltime in lista:
        png = dosar / f"{nume}.png"
        png.unlink(missing_ok=True)
        ok = randeaza(sursa, cod, png, latime, inaltime, text=dosar / f"{nume}.txt" if a.prezentare else None)
        if ok:                                   # evaluatorii primesc JPEG, mai mic; PNG-ul nu mai trebuie
            cv2.imwrite(str(dosar / f"{nume}.jpg"), cv2.imread(str(png)), [cv2.IMWRITE_JPEG_QUALITY, 88])
            png.unlink()
        print(f"{nume}: {'gata' if ok else 'EȘEC'}")
    shutil.rmtree(dosar / "profil", ignore_errors=True)
    (dosar / "stari.json").write_text(json.dumps({"versiune": a.versiune, "stari": html.escape(", ".join(n for n, *_ in lista))}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
