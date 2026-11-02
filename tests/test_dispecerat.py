"""Dispeceratul: serverul, cu clientul de test Flask, și pagina reală, în Chrome fără fereastră, cu cererile simulate (ca în `capturi`).

Pagina nu are alte teste, iar ea e cea pe care o vede un om, deci aici se verifică ce promite: nu arată ca proaspete date vechi, spune dacă o comandă a mers.

Rulare:  set PYTHONPATH=src && python -m unittest tests.test_dispecerat
"""
import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from romana.dashboard import capturi as C

SCENARII = r"""
const rez={};
const text=id=>$(id).textContent, vizibil=el=>!!(el.offsetWidth||el.offsetHeight||el.getClientRects().length);
const bt=m=>document.querySelector(`[data-mod=${m}]`);
const titluri=()=>[...document.querySelectorAll("#schema title")].map(t=>t.textContent);
function instantaneu(){ return {alerte:[...document.querySelectorAll(".alerta")].map(a=>a.textContent),cine:text("cine-acum"),faza:text("faza"),det:text("faza-det"),cam:text("s-cam"),
  dezactivate:[...document.querySelectorAll("[data-mod]")].filter(b=>b.disabled).map(b=>b.dataset.mod),apasate:[...document.querySelectorAll("[data-mod][aria-pressed=true]")].map(b=>b.dataset.mod),
  schema_veche:document.querySelector(".schema").classList.contains("vechi"),debite_vechi:$("p-deb").classList.contains("vechi"),nota:text("deb-nota"),blocat:$("blocat").hidden?null:text("blocat"),
  lumini:titluri(),sursa:text("sursa"),rezultat:text("rezultat"),rez_cls:$("rezultat").className,grafic:text("grafic-rez"),gol:vizibil($("cadru-gol")),confirm:$("confirm").classList.contains("vizibil"),coada_max:text("max-coada")} }
await actualizeaza(); rez.normal=instantaneu(); rez.text_pagina=document.body.innerText; await new Promise(r=>setTimeout(r,1100)); rez.antet_normal=text("proaspat");
const nou=(f)=>{ const s=JSON.parse(JSON.stringify(__SIM)); f(s); return s };
__st(__CAM,nou(s=>{s.etapa="yellow";s.verde_s=12})); await actualizeaza(); rez.galben=instantaneu();
__st(__CAM,nou(s=>{s.etapa="red";s.verde_s=14;s.faza_tinta=1})); await actualizeaza(); rez.rosu=instantaneu();
__st(__CAM,nou(s=>{s.faza=2})); await actualizeaza(); rez.pietoni=instantaneu();
__st(__CAM,nou(s=>{s.model_ai=false})); await actualizeaza(); rez.fara_ai=instantaneu(); rez.fara_ai.d_ai=text("d-ai");
__st(__CAM,__SIM); await actualizeaza();
__st(Object.assign({},__CAM,{_varsta_s:40}),__SIM); await actualizeaza(); rez.camera_40=instantaneu(); rez.camera_40.gol_text=text("cadru-gol");
__st(Object.assign({},__CAM,{_varsta_s:200}),__SIM); await actualizeaza(); rez.camera_200=instantaneu();
__st(__CAM,Object.assign({},__SIM,{_varsta_s:50})); await actualizeaza(); rez.geaman_50=instantaneu();
__st(__CAM,__SIM); await actualizeaza();
window.__netOK=false; await actualizeaza(); rez.server=instantaneu(); window.__netOK=true; await actualizeaza(); rez.revenit=instantaneu();
// confirmarea: focusul nu cade pe „Confirm” și se întoarce la buton
bt("fix").focus(); bt("fix").click(); rez.dialog={text:text("confirm-text"),focus:document.activeElement.id,labelledby:$("confirm").getAttribute("aria-labelledby"),describedby:$("confirm").getAttribute("aria-describedby")};
$("nu").click(); rez.dialog.dupa_renunt=document.activeElement.dataset.mod; rez.dialog.mesaj=text("rezultat");
bt("fix").focus(); bt("fix").click(); document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"})); rez.dialog.dupa_esc=document.activeElement.dataset.mod; rez.dialog.inchis_esc=!$("confirm").classList.contains("vizibil");
bt("program").click(); rez.modul_activ={mesaj:text("rezultat"),confirm:$("confirm").classList.contains("vizibil")};
document.dispatchEvent(new KeyboardEvent("keydown",{key:"3"})); rez.tasta={confirm:$("confirm").classList.contains("vizibil"),text:text("confirm-text")}; $("nu").click();
// comanda eșuată
bt("fix").click(); window.__netOK=false; await $("da").onclick(); window.__netOK=true; rez.esuata=instantaneu(); rez.esuata.istoric=text("istoric-lista"); await actualizeaza();
// comanda aplicată
const n0=__posts.length; bt("fix").click(); await $("da").onclick(); rez.primita={mesaj:text("rezultat"),trimise:__posts.length-n0,corp:__posts[__posts.length-1]};
__st(__CAM,nou(s=>{s.mod="fix";s.mod_program=null})); await actualizeaza(); rez.aplicata=instantaneu(); rez.aplicata.istoric=text("istoric-lista"); rez.aplicata.revino=$("revino").hidden?null:text("revino");
// comanda primită, dar neaplicată
bt("max_pressure").click(); await $("da").onclick(); cerere.la-=20000; await actualizeaza(); rez.neaplicata=instantaneu();
// manual: intrarea cere confirmare, fazele obișnuite nu, cele cu risc da
bt("manual").click(); rez.manual_intrare=text("confirm-text"); await $("da").onclick(); rez.manual_corp=__posts[__posts.length-1];
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null})); await actualizeaza(); rez.manual=instantaneu();
rez.faze={obisnuite:[...document.querySelectorAll("#faze button")].map(b=>b.textContent),risc:[...document.querySelectorAll("#faze-risc button")].map(b=>b.textContent)};
const n1=__posts.length; document.querySelector('[data-faza="1"]').click(); await new Promise(r=>setTimeout(r,10)); rez.faza_directa={trimise:__posts.length-n1,corp:__posts[__posts.length-1],confirm:$("confirm").classList.contains("vizibil")};
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null;s.etapa="yellow";s.faza_tinta=1})); await actualizeaza(); rez.faza_trece=instantaneu();
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null;s.faza=1;s.etapa="green";s.verde_s=3})); await actualizeaza(); rez.faza_gata=instantaneu();
document.querySelector('[data-faza="3"]').click(); rez.faza_risc={text:text("confirm-text"),confirm:$("confirm").classList.contains("vizibil")}; $("nu").click();
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null;s.faza=1;s.etapa="green";s.verde_s=70})); await actualizeaza(); rez.verde_lung=instantaneu();
// imaginea
$("b-imagine").click(); rez.imagine={oprita:text("b-imagine"),are_src:$("cadru").hasAttribute("src"),stare:text("s-cam"),gol:vizibil($("cadru-gol"))}; await actualizeaza(); rez.imagine.tot_oprita=!$("cadru").hasAttribute("src"); $("b-imagine").click(); rez.imagine.pornita=$("cadru").hasAttribute("src");
// cele găsite la a doua evaluare
bt("fix").click(); rez.buton_da=text("da"); $("nu").click();
__st(null,__SIM); await actualizeaza(); rez.fara_camera={vechi:$("p-deb").classList.contains("vechi"),nota:text("deb-nota")};
__st(Object.assign({},__CAM,{_varsta_s:40}),__SIM); await actualizeaza(); __st(__CAM,__SIM); await actualizeaza(); rez.anunt_revenire=text("anunt");
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null;s.etapa="yellow";s.faza_tinta=2})); await actualizeaza(); rez.faza_urmeaza=document.querySelector('[data-faza="2"]').className;
__st(__CAM,__SIM); await actualizeaza();
$("taste").checked=false; document.dispatchEvent(new KeyboardEvent("keydown",{key:"3"})); rez.taste_oprite=$("confirm").classList.contains("vizibil"); $("taste").checked=true;
// ajutorul
document.dispatchEvent(new KeyboardEvent("keydown",{key:"?"})); rez.ajutor=vizibil($("ajutor"));
// cele găsite la a doua rundă cu evaluatori
__st(__CAM,__SIM); await actualizeaza();
const stilul=(el,p)=>getComputedStyle(el,p||null), alerteCuClasa=()=>[...document.querySelectorAll(".alerta")].map(a=>({cls:a.className,text:a.textContent}));
window.__netOK=false; await actualizeaza(); const inainte=text("deb-nota"); await new Promise(r=>setTimeout(r,3000));
rez.fara_legatura={inainte,dupa:text("deb-nota"),antet:text("proaspat"),blocat:text("blocat"),faza:text("faza"),revino_blocat:$("revino").disabled}; window.__netOK=true; await actualizeaza(); rez.fara_legatura.revino_dupa=$("revino").disabled;
const retea=window.fetch, raspunde=(parte,raspuns)=>{ window.fetch=async(u,o)=>String(u).includes(parte)?raspuns:retea(u,o) };
raspunde("/api/state",{ok:false,status:500,json:async()=>({})}); await actualizeaza(); rez.eroare_500=instantaneu(); rez.eroare_500.tehnic=document.querySelector(".alerta details").textContent; window.fetch=retea; await actualizeaza();
raspunde("/api/command",{ok:false,status:400,json:async()=>({eroare:"mod necunoscut"})}); bt("fix").click(); await $("da").onclick(); window.fetch=retea; rez.refuzata=instantaneu(); rez.refuzata.istoric=text("istoric-lista"); rez.refuzata.urmarita=!!cerere;
bt("fix").click(); __st(__CAM,nou(s=>{s.mod="max_pressure";s.mod_program=null})); await actualizeaza(); rez.confirmare_depasita=instantaneu(); __st(__CAM,__SIM); await actualizeaza();
__st(__CAM,Object.assign({},__SIM,{_varsta_s:50})); await actualizeaza(); rez.simulare_veche=instantaneu();
Object.assign(rez.simulare_veche,{eticheta:$("svg-schema").getAttribute("aria-label"),opacitate:[".schema svg","#grafic","#faza"].map(q=>stilul(document.querySelector(q)).opacity),marcaj:stilul($("t-sem"),"::after").content,semne:$("schema").innerHTML}); __st(__CAM,__SIM); await actualizeaza();
__st(Object.assign({},__CAM,{conectat:false}),__SIM); await actualizeaza(); await new Promise(r=>setTimeout(r,1100));
rez.reconectare=Object.assign(instantaneu(),{antet:text("proaspat"),punct:$("p-cam").className,nesigur:$("p-deb").classList.contains("nesigur")}); __st(__CAM,__SIM); await actualizeaza();
const camera=()=>({alerte:alerteCuClasa(),punct:$("p-cam").className,cam:text("s-cam"),gol:text("cadru-gol"),nota:text("deb-nota")});
__st(Object.assign({},__CAM,{_varsta_s:700}),__SIM); await actualizeaza(); rez.camera_700=camera();
__st(Object.assign({},__CAM,{_varsta_s:200}),__SIM); await actualizeaza(); rez.camera_200_alerta=camera();
__st(__CAM,__SIM); await actualizeaza(); __st(null,__SIM); await actualizeaza(); rez.camera_lipsa=camera();
camUltimLa=0; await actualizeaza(); rez.camera_niciodata=camera();
__st(Object.assign({},__CAM,{_varsta_s:200}),Object.assign({},__SIM,{_varsta_s:50})); await actualizeaza(); rez.ambele=document.body.innerText; __st(__CAM,__SIM); await actualizeaza();
let gata; window.fetch=async(u,o)=>{ if(String(u).includes("/api/command")) await new Promise(r=>gata=r); return retea(u,o) };
bt("fix").click(); const pe_drum=$("da").onclick(); rez.se_trimite={active:[...document.querySelectorAll("[data-mod],[data-faza],#revino")].filter(b=>!b.disabled).length,istoric:text("istoric-lista")}; gata(); await pe_drum; window.fetch=retea;
rez.se_trimite.dezactivate_dupa=[...document.querySelectorAll("[data-mod]")].filter(b=>b.disabled).length;
bt("max_pressure").click(); await $("da").onclick(); rez.inlocuita=text("istoric-lista"); cerere.la-=20000; await actualizeaza();
const man=s=>{s.mod="manual";s.mod_program=null}; __st(__CAM,nou(man)); await actualizeaza();
document.querySelector('[data-faza="1"]').click(); await new Promise(r=>setTimeout(r,10)); await actualizeaza(); rez.faza_in_curs=text("rezultat"); cerere.la-=40000; await actualizeaza(); await actualizeaza();
rez.faza_expirata=Object.assign(instantaneu(),{istoric:text("istoric-lista"),clasa:document.querySelector('[data-faza="1"]').className});
__st(__CAM,nou(s=>{man(s);s.faza=3})); await actualizeaza(); rez.risc_3={lumini:titluri(),legenda:!$("leg-plus").hidden}; document.querySelector('[data-faza="4"]').click(); rez.risc_3.confirmare=text("confirm-text"); $("nu").click();
__st(__CAM,nou(s=>{man(s);s.faza=4})); await actualizeaza(); rez.risc_4={lumini:titluri()};
__st(__CAM,nou(man)); await actualizeaza(); rez.manual_text=$("manual").querySelector("p").textContent; rez.legenda_fara_risc=$("leg-plus").hidden;
__st(__CAM,nou(s=>{s.model_ai=false})); await actualizeaza(); rez.fara_ai_stil={opacitate:stilul(bt("ai")).opacity,culoare:stilul($("d-ai")).color}; __st(__CAM,__SIM); await actualizeaza();
await new Promise(r=>{ $("cadru").addEventListener("error",r,{once:true}); $("cadru").src="data:,nimic" }); await actualizeaza();
rez.imagine_cazuta={stare:text("s-cam"),gol:text("cadru-gol"),vizibil:vizibil($("cadru-gol")),punct:$("p-cam").className};
__st(__CAM,nou(s=>{s.etapa="green";s.faza=5})); await actualizeaza(); rez.preluare=[fazaDePreluat(sim)];
__st(__CAM,nou(s=>{s.etapa="yellow";s.faza=1;s.faza_tinta=5})); await actualizeaza(); rez.preluare.push(fazaDePreluat(sim));
__st(__CAM,nou(s=>{s.etapa="yellow";s.faza=0;s.faza_tinta=1})); await actualizeaza(); rez.preluare.push(fazaDePreluat(sim));
__st(__CAM,nou(s=>{s.etapa="green";s.faza=2})); await actualizeaza(); rez.preluare.push(fazaDePreluat(sim));
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestPagina(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        pagina = C.pagina(C.VERSIUNI["m2"].read_text(encoding="utf-8"), SCENARII)
        f = cls.d / "pagina.html"
        f.write_text(pagina, encoding="utf-8")
        cmd = [C.CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={cls.d / 'profil'}", "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files",
               "--virtual-time-budget=30000", "--window-size=1366,1500", "--dump-dom", f.as_uri()]
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        m = re.search(r'<pre id="rez">(.*?)</pre>', r.stdout.decode("utf-8", "replace"), re.S)
        if not m:
            raise AssertionError("Scenariul din pagină nu s-a încheiat: " + r.stderr.decode("utf-8", "replace")[-400:])
        cls.r = json.loads(html.unescape(m.group(1)))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, ignore_errors=True)

    def test_la_preluare_se_trimite_o_faza_care_se_poate_cere(self):
        self.assertEqual(self.r["preluare"], [0, 0, 1, 2])      # din etapa scurtă și spre ea: N–S; în tranziție, ținta; altfel, faza de acum

    def test_starea_normala_spune_cine_conduce(self):
        n = self.r["normal"]
        self.assertEqual(n["alerte"], [])
        self.assertIn("un calculator", n["cine"])
        self.assertEqual(n["apasate"], ["program"])
        self.assertEqual(n["dezactivate"], [])
        self.assertIn("Magheru: verde", n["lumini"])
        self.assertIn("Dacia vest: roșu", n["lumini"])
        self.assertIn("Acum: 7 vehicule", n["grafic"])

    def test_pagina_nu_mai_are_termenii_vechi(self):
        t = self.r["text_pagina"]
        for vechi in ("live", "dashboard", "Max-Pressure", "PPO", "models/", "5.94", "Debite", "~5"):
            self.assertNotIn(vechi, t, vechi)
        self.assertIn("doar semaforul din simulare", t)

    def test_galbenul_si_rosul_nu_arata_durata_verdelui(self):
        for k, cuvant, lumina in (("galben", "galben", "Magheru: galben"), ("rosu", "roșu pentru toți", "Magheru: roșu de degajare")):
            s = self.r[k]
            self.assertIn(cuvant, s["det"])
            self.assertNotRegex(s["det"], r"de 1[24] s")
            self.assertIn(lumina, s["lumini"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", self.r["rosu"]["faza"])

    def test_faza_de_pietoni_are_explicatie(self):
        self.assertIn("pietoni", self.r["pietoni"]["faza"])

    def test_agentul_indisponibil_spune_de_ce(self):
        s = self.r["fara_ai"]
        self.assertEqual(s["dezactivate"], ["ai"])
        self.assertIn("Indisponibil", s["d_ai"])

    def test_camera_veche_nu_pare_proaspata(self):
        s = self.r["camera_40"]
        self.assertIn("40 s", s["cam"])
        self.assertTrue(s["debite_vechi"])
        self.assertTrue(s["gol"])
        self.assertEqual(s["alerte"], [])         # o oprire scurtă nu ridică alertă
        self.assertNotIn("în mai puțin de un minut", s["gol_text"])
        l = self.r["camera_200"]
        self.assertIn("3 min 20 s", l["cam"])
        self.assertIn("Camera nu mai trimite date", l["alerte"][0])
        self.assertIn("vechi de", l["nota"])
        self.assertNotIn("nu rulează", l["cam"])

    def test_geamanul_oprit_blocheaza_comenzile(self):
        s = self.r["geaman_50"]
        self.assertIn("Simularea nu mai trimite date", s["alerte"][0])
        self.assertTrue(s["schema_veche"])
        self.assertEqual(len(s["dezactivate"]), 5)
        self.assertIn("vechi de", s["det"])
        self.assertIn("Comenzile sunt blocate", s["blocat"])
        self.assertEqual(s["apasate"], [])
        self.assertEqual(s["sursa"], "")

    def test_serverul_cazut_nu_pare_activ_si_revine(self):
        s = self.r["server"]
        self.assertIn("Nu mai e legătură cu calculatorul dispeceratului", s["alerte"][0])
        self.assertTrue(s["schema_veche"])
        self.assertTrue(s["debite_vechi"])
        self.assertEqual(len(s["dezactivate"]), 5)
        self.assertIn("legătură", s["cam"])
        self.assertTrue(s["gol"])
        r = self.r["revenit"]
        self.assertEqual(r["alerte"], [])
        self.assertEqual(r["dezactivate"], [])
        self.assertFalse(r["schema_veche"])

    def test_confirmarea(self):
        d = self.r["dialog"]
        self.assertIn("de la „Planul observat” către „Plan de referință”", d["text"])
        self.assertEqual(d["focus"], "confirm")      # nu „da”: un Enter din reflex nu confirmă
        self.assertTrue(d["labelledby"] and d["describedby"])
        self.assertEqual(d["dupa_renunt"], "fix")
        self.assertEqual(d["dupa_esc"], "fix")
        self.assertTrue(d["inchis_esc"])
        self.assertIn("Nu s-a schimbat nimic", d["mesaj"])

    def test_modul_activ_nu_cere_confirmare_si_tasta_deschide(self):
        self.assertFalse(self.r["modul_activ"]["confirm"])
        self.assertIn("conduce deja", self.r["modul_activ"]["mesaj"])
        self.assertTrue(self.r["tasta"]["confirm"])
        self.assertIn("Plan de referință", self.r["tasta"]["text"])

    def test_comanda_esuata_spune_si_ce_ramane(self):
        s = self.r["esuata"]
        self.assertIn("nu a ajuns la calculatorul dispeceratului", s["rezultat"])
        self.assertIn("Conduce în continuare „Planul observat”", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")
        self.assertFalse(s["confirm"])
        self.assertIn("eșuată", s["istoric"])

    def test_comanda_aplicata_se_confirma_si_se_poate_reveni(self):
        self.assertIn("Așteptăm simularea", self.r["primita"]["mesaj"])
        self.assertEqual(self.r["primita"]["trimise"], 1)
        self.assertEqual(self.r["primita"]["corp"], {"mod": "fix"})
        s = self.r["aplicata"]
        self.assertIn("Aplicat", s["rezultat"])
        self.assertEqual(s["rez_cls"], "bun")
        self.assertIn("aplicată", s["istoric"])
        self.assertIn("Planul observat", s["revino"])

    def test_comanda_neaplicata_nu_trece_neobservata(self):
        s = self.r["neaplicata"]
        self.assertIn("n-a aplicat", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")

    def test_manualul(self):
        self.assertIn("Rămâne faza de acum", self.r["manual_intrare"])
        self.assertNotIn("Agent", self.r["manual_intrare"])
        self.assertEqual(self.r["manual_corp"], {"mod": "manual", "faza": 0})
        self.assertIn("un om", self.r["manual"]["cine"])
        self.assertEqual(len(self.r["faze"]["obisnuite"]), 3)
        self.assertEqual(len(self.r["faze"]["risc"]), 2)
        d = self.r["faza_directa"]
        self.assertEqual(d["trimise"], 1)
        self.assertEqual(d["corp"], {"mod": "manual", "faza": 1})
        self.assertFalse(d["confirm"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", self.r["faza_trece"]["rezultat"])
        self.assertIn("Aplicat", self.r["faza_gata"]["rezultat"])
        self.assertTrue(self.r["faza_risc"]["confirm"])
        self.assertIn("se poate bloca", self.r["faza_risc"]["text"])
        self.assertIn("mai sunt 20 s", self.r["verde_lung"]["det"])

    def test_cele_gasite_la_a_doua_evaluare(self):
        s = self.r["geaman_50"]
        self.assertIn("Ultimul mod cunoscut: „Planul observat”", s["cine"])
        self.assertIn("Ultima valoare primită", s["grafic"])
        self.assertNotIn("Acum:", s["grafic"])
        self.assertIn("Dacă nu revine în 2 minute, anunțați autorul proiectului", s["alerte"][0])
        self.assertIn("123 de vehicule", self.r["normal"]["det"])
        self.assertIn("e verde de 9 s", self.r["normal"]["det"])
        self.assertIn("Pietonii: roșu", " ".join(self.r["normal"]["lumini"]))
        self.assertIn("Pietonii: verde", " ".join(self.r["pietoni"]["lumini"]))
        self.assertIn("Da, trec la „Plan de referință”", self.r["buton_da"])
        self.assertEqual(self.r["fara_camera"]["vechi"], True)
        self.assertIn("Ultimele valori", self.r["fara_camera"]["nota"])
        self.assertIn("a revenit", self.r["anunt_revenire"])
        self.assertIn("urmeaza", self.r["faza_urmeaza"])
        self.assertEqual(self.r["taste_oprite"], False)

    def test_vechimea_creste_fara_legatura_si_revenirea_e_blocata(self):
        s = self.r["fara_legatura"]
        secunde = lambda t: int(re.search(r"(\d+) s", t)[1])
        self.assertGreaterEqual(secunde(s["dupa"]), secunde(s["inainte"]) + 2)
        self.assertGreaterEqual(secunde(s["dupa"]), secunde(s["antet"]))
        self.assertIn("calculatorul dispeceratului", s["blocat"])
        self.assertIn("Ultima fază cunoscută", s["faza"])
        self.assertTrue(s["revino_blocat"])
        self.assertFalse(s["revino_dupa"])

    def test_eroarea_serverului_nu_da_vina_pe_simulare_si_camera(self):
        s = self.r["eroare_500"]
        self.assertEqual(len(s["alerte"]), 1)
        self.assertIn("calculatorul dispeceratului", s["alerte"][0])
        self.assertIn("500", s["tehnic"])
        self.assertIn("7_dashboard", s["tehnic"])
        self.assertEqual(len(s["dezactivate"]), 5)

    def test_comanda_refuzata_spune_motivul(self):
        s = self.r["refuzata"]
        self.assertIn("a refuzat", s["rezultat"])
        self.assertIn("mod necunoscut", s["rezultat"])
        self.assertNotIn("nu a ajuns", s["rezultat"])
        self.assertNotIn("Încercați din nou", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")
        self.assertIn("refuzată", s["istoric"])
        self.assertFalse(s["urmarita"])

    def test_confirmarea_se_inchide_daca_modul_se_schimba(self):
        s = self.r["confirmare_depasita"]
        self.assertFalse(s["confirm"])
        self.assertIn("Între timp a preluat „Presiune maximă”", s["rezultat"])

    def test_simularea_veche_nu_pare_actuala(self):
        s = self.r["simulare_veche"]
        self.assertTrue(s["faza"].startswith("Ultima fază cunoscută (acum 50 s): Verde pe Magheru"), s["faza"])
        self.assertIn("Magheru: necunoscut; ultima culoare primită: verde", s["lumini"])
        self.assertIn("#5d6873", s["semne"])
        self.assertNotIn("#8a948c", s["semne"])
        self.assertTrue(s["eticheta"].startswith("Ultimele valori primite, vechi de 50 s"), s["eticheta"])
        self.assertIn("Magheru verde", s["eticheta"])
        self.assertEqual(s["opacitate"], ["1", "1", "1"])
        self.assertIn("date vechi", s["marcaj"])
        self.assertTrue(s["coada_max"].startswith("La ultima valoare primită"), s["coada_max"])

    def test_camera_care_se_reconecteaza_nu_e_la_zi(self):
        s = self.r["reconectare"]
        self.assertIn("camera se reconectează", s["antet"])
        self.assertIn("atent-p", s["punct"])
        self.assertTrue(s["nesigur"])
        self.assertIn("nesigure", s["nota"])
        self.assertTrue(s["gol"])
        self.assertEqual(self.r["antet_normal"], "date la zi")
        i = self.r["imagine_cazuta"]
        self.assertIn("imaginea nu se încarcă", i["stare"])
        self.assertIn("încercăm din nou", i["gol"])
        self.assertTrue(i["vizibil"])
        self.assertIn("atent-p", i["punct"])

    def test_alerta_camerei_are_trepte_dupa_vechime(self):
        l = self.r["camera_700"]
        self.assertEqual(l["alerte"][0]["cls"].split(), ["alerta"])       # roșie
        self.assertIn("de peste 10 minute", l["alerte"][0]["text"])
        self.assertNotIn("revin singure", l["alerte"][0]["text"])
        self.assertIn("err", l["punct"])
        m = self.r["camera_200_alerta"]
        self.assertIn("atent", m["alerte"][0]["cls"])
        self.assertIn("revin singure", m["alerte"][0]["text"])
        self.assertIn("atent-p", m["punct"])
        self.assertNotIn("anunțați", m["gol"])
        f = self.r["camera_lipsa"]       # starea lipsește, dar ultima măsurătoare e de acum câteva secunde
        self.assertEqual(f["alerte"], [])
        self.assertIn("atent-p", f["punct"])
        self.assertIn("nicio măsurătoare nouă de", f["cam"])
        self.assertIn("s-a oprit de", f["gol"])
        n = self.r["camera_niciodata"]
        self.assertIn("Camera nu trimite date", n["alerte"][0]["text"])
        self.assertIn("atent", n["alerte"][0]["cls"])
        self.assertNotIn("revin singure", n["alerte"][0]["text"])
        self.assertEqual(n["cam"], "camera: nu trimite date")

    def test_ce_aveti_de_facut_se_spune_o_singura_data(self):
        t = self.r["ambele"]
        self.assertEqual(t.count("anunțați autorul proiectului"), 1)
        self.assertIn("în 2 minute", t)
        self.assertNotIn("administrează", t)

    def test_comenzile_nu_se_incurca(self):
        s = self.r["se_trimite"]
        self.assertEqual(s["active"], 0)
        self.assertIn("se trimite", s["istoric"])
        self.assertNotIn("undefined", s["istoric"])
        self.assertEqual(s["dezactivate_dupa"], 0)
        self.assertIn("înlocuită", self.r["inlocuita"])
        self.assertIn("se aplică", self.r["inlocuita"])

    def test_schimbarea_de_faza_expira(self):
        self.assertIn("Se schimbă spre", self.r["faza_in_curs"])
        s = self.r["faza_expirata"]
        self.assertIn("n-a aplicat", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")
        self.assertIn("neaplicată", s["istoric"])
        self.assertNotIn("urmeaza", s["clasa"])

    def test_fazele_cu_risc_se_deosebesc(self):
        a, b = self.r["faze"]["risc"]
        self.assertIn("prin centru", a)
        self.assertIn("în jurul insulei", b)
        self.assertIn("Magheru: verde", self.r["risc_3"]["lumini"])
        self.assertIn("Dacia est: verde, deschisă în plus", self.r["risc_3"]["lumini"])
        self.assertIn("Dacia est: verde", self.r["risc_4"]["lumini"])
        self.assertIn("Magheru: verde, deschisă în plus", self.r["risc_4"]["lumini"])
        self.assertTrue(self.r["risc_3"]["legenda"])
        self.assertTrue(self.r["legenda_fara_risc"])
        self.assertIn("Verdele principal e pe Dacia", self.r["risc_3"]["confirmare"])
        self.assertIn("≈20 s", self.r["manual_text"])

    def test_schema_raspunde_unde_asteapta_cele_mai_multe(self):
        n = self.r["normal"]
        self.assertIn("Cele mai multe vehicule oprite: Dacia vest (21)", n["coada_max"])
        self.assertIn("pe toate străzile", n["grafic"])
        self.assertIn("schema", n["grafic"])
        self.assertIn("intră în piață", self.r["text_pagina"])
        self.assertIn("ies din piață", self.r["text_pagina"])

    def test_motivul_agentului_indisponibil_se_citeste(self):
        self.assertEqual(self.r["fara_ai_stil"]["opacitate"], "1")
        self.assertEqual(self.r["fara_ai_stil"]["culoare"], "rgb(31, 42, 51)")

    def test_imaginea_si_ajutorul(self):
        i = self.r["imagine"]
        self.assertEqual(i["oprita"], "Pornește imaginea")
        self.assertIn("măsoară", i["stare"])
        self.assertTrue(i["gol"])
        self.assertFalse(i["are_src"])
        self.assertTrue(i["tot_oprita"])
        self.assertTrue(i["pornita"])
        self.assertTrue(self.r["ajutor"])


class TestServer(unittest.TestCase):
    def setUp(self):
        from romana.dashboard import server as S
        self.S = S
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d, True)
        self.vechi = S.LIVE
        S.LIVE = self.d
        self.addCleanup(setattr, S, "LIVE", self.vechi)
        self.c = S.app.test_client()

    def test_comanda_se_scrie_si_se_tine_minte(self):
        r = self.c.post("/api/command", json={"mod": "manual", "faza": 1})
        self.assertEqual(r.status_code, 200)
        self.c.post("/api/command", json={"mod": "fix"})
        self.assertEqual(json.loads((self.d / "command.json").read_text(encoding="utf-8"))["mod"], "fix")
        st = self.c.get("/api/state").get_json()
        self.assertEqual([k["mod"] for k in st["comenzi"]], ["manual", "fix"])
        self.assertEqual(st["comenzi"][0]["faza"], 1)

    def test_comenzile_gresite_se_resping(self):
        self.assertEqual(self.c.post("/api/command", json={"mod": "altceva"}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": "x"}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": 5}).status_code, 400)
        self.assertEqual(self.c.post("/api/command", json={"mod": "manual", "faza": -1}).status_code, 400)
        self.assertFalse((self.d / "command.json").exists())
        self.assertFalse((self.d / "comenzi.jsonl").exists())

    def test_starea_fara_fisiere_si_cu_jurnal_stricat(self):
        st = self.c.get("/api/state").get_json()
        self.assertIsNone(st["camera"])
        self.assertIsNone(st["simulare"])
        self.assertEqual(st["comenzi"], [])
        (self.d / "comenzi.jsonl").write_text('{"mod":"fix"}\nstricat\n{"mod":"ai"}\n', encoding="utf-8")
        self.assertEqual([k["mod"] for k in self.c.get("/api/state").get_json()["comenzi"]], ["fix", "ai"])


if __name__ == "__main__":
    unittest.main()
