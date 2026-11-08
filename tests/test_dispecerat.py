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
try{
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
document.querySelector('[data-faza="1"]').click(); await new Promise(r=>setTimeout(r,10)); await actualizeaza(); rez.faza_in_curs=text("rezultat");
cerere.la-=40000; await actualizeaza(); rez.faza_in_curs_40=text("rezultat"); cerere.la-=30000; await actualizeaza(); await actualizeaza();   // geamăn fără pașii publicați: termenul fix, de 65 s
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
// pașii publicați de geamăn (src/romana/control/pasi.py): termenul pe timp_sim, ținta reală în degajare, comanda înlocuită, simularea repornită
const cuPasi=o=>nou(s=>{ Object.assign(s,{mod:"manual",mod_program:null,pas:"verde",pas_ramas_s:null,faza_tinta:o&&o.faza!==undefined?o.faza:0,pana_la_tinta_s:0,verde_min_s:35,
  verde_max_s:90,cadenta_s:5,citire_peste_s:0,pana_la_faza_s:[0,50,44,50,50],durate_s:{galben:3,rosu:2,degajare:6},comanda_citita_ts:1000},o); s.etapa={verde:"green",degajare:"green",galben:"yellow",rosu:"red"}[s.pas] });   // etapa controlerului, ca în geamăn
const faza=i=>document.querySelector(`[data-faza="${i}"]`), clic=async i=>{ faza(i).click(); await new Promise(r=>setTimeout(r,10)) }, ultima=()=>document.querySelector("#istoric-lista li").textContent;
__st(__CAM,cuPasi({timp_sim:500,verde_s:9})); await actualizeaza(); cerere=null;
await clic(1); const ts1=__ultimTs; rez.pasi_trimis=text("rezultat");
__st(__CAM,cuPasi({timp_sim:501,verde_s:10,citire_peste_s:4,pana_la_faza_s:[0,49,43,49,49],comanda_citita_ts:ts1})); await actualizeaza();
rez.pasi_citit={rezultat:text("rezultat"),termen:cerere&&cerere.termen};
cerere.la-=40000;   // 40 s pe ceasul paginii: termenul e pe timp_sim, deci comanda e încă în termen
__st(__CAM,cuPasi({timp_sim:541,verde_s:44,pas:"degajare",pas_ramas_s:5,faza_tinta:1,pana_la_tinta_s:10,citire_peste_s:4,pana_la_faza_s:[60,10,60,60,60],comanda_citita_ts:ts1})); await actualizeaza();
rez.pasi_40={rezultat:text("rezultat"),faza:text("faza"),det:text("faza-det"),urmeaza:faza(1).className,apasat:faza(0).getAttribute("aria-pressed")};
__st(__CAM,cuPasi({timp_sim:554,verde_s:57,comanda_citita_ts:ts1})); await actualizeaza(); rez.pasi_expirat=Object.assign(instantaneu(),{istoric:ultima()});
await clic(1); const ts2=__ultimTs;
__st(__CAM,cuPasi({timp_sim:560,verde_s:63,comanda_citita_ts:ts2,pana_la_faza_s:[0,11,5,11,11]})); await actualizeaza(); rez.pasi_porneste=text("rezultat");
__st(__CAM,cuPasi({timp_sim:571,faza:1,verde_s:0,verde_min_s:10,comanda_citita_ts:ts2,pana_la_faza_s:[25,0,19,25,25]})); await actualizeaza();
rez.pasi_aplicat={rezultat:text("rezultat"),cls:$("rezultat").className,istoric:ultima()};
// în degajarea pietonilor: ținta e faza următoare, la preluare și pe butoane
__st(__CAM,cuPasi({mod:"program",mod_program:"plan_observat",timp_sim:600,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:4,verde_s:44,pana_la_tinta_s:9})); await actualizeaza();
rez.degajare={faza:text("faza"),det:text("faza-det"),preluare:fazaDePreluat(sim)};
bt("manual").click(); rez.degajare.confirmare=text("confirm-text"); await $("da").onclick(); rez.degajare.corp=__posts[__posts.length-1];
__st(__CAM,cuPasi({timp_sim:601,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:3,verde_s:45,comanda_citita_ts:__ultimTs})); await actualizeaza();
Object.assign(rez.degajare,{preluata:text("rezultat"),urmeaza:faza(0).className,apasat1:faza(1).getAttribute("aria-pressed")});
const n2=__posts.length; await clic(1); rez.degajare.trimise=__posts.length-n2;
const ts4=__ultimTs; window.__ultimTs=ts4+5; __st(__CAM,cuPasi({timp_sim:602,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:2,verde_s:46,comanda_citita_ts:ts4+5})); await actualizeaza();
rez.inlocuita_alt={rezultat:text("rezultat"),ultima:ultima(),urmarita:!!cerere};
__st(__CAM,cuPasi({timp_sim:603,verde_s:0,comanda_citita_ts:ts4+5})); await actualizeaza();
await clic(1); const ts5=__ultimTs;
__st(__CAM,cuPasi({timp_sim:604,verde_s:1,comanda_citita_ts:ts5})); await actualizeaza();
__st(__CAM,cuPasi({timp_sim:3,verde_s:3,comanda_citita_ts:ts5})); await actualizeaza(); rez.repornita={rezultat:text("rezultat"),ultima:ultima()};
__st(__CAM,cuPasi({timp_sim:501,faza:1,verde_s:70,verde_min_s:10})); await actualizeaza(); rez.verde_lung_pasi=text("faza-det");
const cuScurta=o=>Object.assign(cuPasi(o),{faze:[...__FAZE,"Golirea centrului, fără pietoni"]});
__st(__CAM,cuScurta({mod:"program",timp_sim:700,faza:5,faza_nume:"Golirea centrului, fără pietoni",faza_tinta:5,verde_s:1,verde_min_s:3})); await actualizeaza(); rez.preluare_pasi=[fazaDePreluat(sim)]; rez.in_scurta=text("faza");
__st(__CAM,cuScurta({mod:"program",timp_sim:701,faza:1,faza_tinta:5,pas:"galben",pas_ramas_s:2})); await actualizeaza(); rez.preluare_pasi.push(fazaDePreluat(sim)); rez.spre_scurta={faza:text("faza"),det:text("faza-det")};
__st(__CAM,cuScurta({mod:"program",timp_sim:702,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:5})); await actualizeaza(); rez.preluare_pasi.push(fazaDePreluat(sim));
__st(__CAM,cuScurta({mod:"program",timp_sim:703,faza:2,faza_tinta:2})); await actualizeaza(); rez.preluare_pasi.push(fazaDePreluat(sim));
// reîncărcarea, refăcută pe loc: ca la o pagină nouă, fără istoric, fără cerere și fără mod văzut
cerere=null; istoric.length=0; refacut=false; modAnterior=null; modVazut=null;
const acum_s=Date.now()/1000;
__st(__CAM,cuPasi({timp_sim:800,verde_s:20,comanda_citita_ts:acum_s-8}),{comanda:{mod:"manual",faza:1,timestamp:acum_s-8,_varsta_s:8},
  comenzi:[{mod:"program",timestamp:acum_s-200},{mod:"manual",faza:0,timestamp:acum_s-60},{mod:"manual",faza:1,timestamp:acum_s-8},{stricat:true}],ora_server:acum_s});
await actualizeaza();
rez.reincarcare={istoric:[...document.querySelectorAll("#istoric-lista li")].map(l=>l.textContent),vizibil:!$("istoric-parte").hidden,rezultat:text("rezultat"),faza:cerere?cerere.faza:null,revino:$("revino").hidden?null:text("revino")};
cerere=null; istoric.length=0; refacut=false;
__st(__CAM,cuPasi({timp_sim:900,verde_s:20}),{comanda:{mod:"manual",faza:1,timestamp:acum_s-100,_varsta_s:100},comenzi:[{mod:"manual",faza:1,timestamp:acum_s-100}],ora_server:acum_s});
await actualizeaza(); rez.reincarcare_veche={istoric:text("istoric-lista"),urmarita:!!cerere};
cerere=null; istoric.length=0; refacut=false;
__st(__CAM,cuPasi({timp_sim:950,verde_s:20}),{comanda:{mod:"manual",faza:0,timestamp:acum_s-5,_varsta_s:5}}); await actualizeaza(); rez.reincarcare_aplicata={urmarita:!!cerere};
// după revizia din 8.11: blocuri separate, fiecare de la o stare fără cerere și cu timp_sim nou; ecourile „din altă parte” rămân mai vechi decât comenzile de după ele
const urm=()=>({rezultat:text("rezultat"),cls:$("rezultat").className,urmarita:!!cerere,ultima:document.querySelector("#istoric-lista li")?.textContent??null});
window.__ultimTs=Math.max(window.__ultimTs,Date.now()/1000);
// cerută din nou în degajarea din chiar faza ei: nu „Aplicat”, ci „Întâi se încheie schimbarea…”; apoi înlocuită după citire, din altă parte
__st(__CAM,cuPasi({timp_sim:2000,faza:1,faza_tinta:1,verde_s:90,verde_min_s:10,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
__st(__CAM,cuPasi({timp_sim:2001,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:5,verde_s:91,verde_min_s:35,pana_la_tinta_s:10,pana_la_faza_s:[10,60,54,60,60],comanda_citita_ts:__ultimTs})); await actualizeaza();
const nA=__posts.length; await clic(1); const tA=__ultimTs;
__st(__CAM,cuPasi({timp_sim:2002,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:4,verde_s:92,verde_min_s:35,pana_la_tinta_s:9,pana_la_faza_s:[9,59,53,59,59],comanda_citita_ts:tA})); await actualizeaza();
rez.ceruta_in_degajare=Object.assign(urm(),{trimise:__posts.length-nA,citita:!!(cerere&&cerere.citita)});
__st(__CAM,cuPasi({timp_sim:2003,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:3,verde_s:93,verde_min_s:35,pana_la_tinta_s:8,pana_la_faza_s:[8,58,52,58,58],comanda_citita_ts:tA+5})); await actualizeaza();
rez.inlocuita_dupa_citire=urm(); window.__ultimTs=Math.max(window.__ultimTs,tA+5);
// la fel, după o reîncărcare a paginii: comanda de acum 5 s, încă neaplicată, se urmărește mai departe
cerere=null; istoric.length=0; refacut=false; modAnterior=null; modVazut=null;
const aG=Date.now()/1000;
__st(__CAM,cuPasi({timp_sim:2100,faza:1,faza_tinta:0,pas:"degajare",pas_ramas_s:3,verde_s:91,verde_min_s:35,pana_la_tinta_s:8,pana_la_faza_s:[8,58,52,58,58],comanda_citita_ts:aG-5}),
  {comanda:{mod:"manual",faza:1,timestamp:aG-5,_varsta_s:5},comenzi:[{mod:"manual",faza:1,timestamp:aG-5}],ora_server:aG});
await actualizeaza(); rez.reincarcare_degajare=urm();
// simularea nu citește comanda: după 10 s, pe calea cu pași, „n-a citit”
__st(__CAM,cuPasi({timp_sim:2200,faza:0,verde_s:20,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
await clic(1); cerere.la-=11000; await actualizeaza(); rez.necitita=urm();
// anularea: altă fază cerută și citită, încă neaplicată; clicul pe faza de acum se trimite, nu e „deja activă”
__st(__CAM,cuPasi({timp_sim:2300,faza:0,verde_s:20,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
await clic(1); const tC=__ultimTs;
__st(__CAM,cuPasi({timp_sim:2301,faza:0,verde_s:21,citire_peste_s:4,pana_la_faza_s:[0,29,23,29,29],comanda_citita_ts:tC})); await actualizeaza();
const nC=__posts.length; await clic(0); rez.anulare={trimise:__posts.length-nC,corp:__posts[__posts.length-1],rezultat:text("rezultat")};
// textele pașilor, spre o fază fără intrări care rămân pe verde: următoarea decizie, galbenul și roșul
__st(__CAM,cuPasi({timp_sim:2400,faza:0,verde_s:40,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
await clic(1); const tD=__ultimTs;
__st(__CAM,cuPasi({timp_sim:2402,faza:0,verde_s:42,citire_peste_s:3,pana_la_faza_s:[0,14,8,14,14],comanda_citita_ts:tD})); await actualizeaza(); rez.pasi_decizie=text("rezultat");
__st(__CAM,cuPasi({timp_sim:2412,faza:0,faza_tinta:1,pas:"galben",pas_ramas_s:2,verde_s:52,pana_la_tinta_s:4,pana_la_faza_s:[30,4,30,30,30],comanda_citita_ts:tD})); await actualizeaza();
rez.pasi_galben={rezultat:text("rezultat"),det:text("faza-det"),lumini:titluri()};
__st(__CAM,cuPasi({timp_sim:2415,faza:0,faza_tinta:1,pas:"rosu",pas_ramas_s:1,verde_s:52,pana_la_tinta_s:1,pana_la_faza_s:[30,1,30,30,30],comanda_citita_ts:tD})); await actualizeaza();
rez.pasi_rosu={rezultat:text("rezultat"),det:text("faza-det"),lumini:titluri()};
// răspunsul serverului fără `timestamp`: comanda se recunoaște după primul ecou mai nou
__st(__CAM,cuPasi({timp_sim:2500,faza:0,verde_s:40,comanda_citita_ts:777})); await actualizeaza(); cerere=null;
const fE=window.fetch; window.fetch=async(u,o)=>{ const r=await fE(u,o); if(!String(u).includes("/api/command")) return r; const j=await r.json(); delete j.timestamp; return {ok:true,status:200,json:async()=>j} };
await clic(1); window.fetch=fE; rez.fara_ts={ts:cerere?String(cerere.ts):"fără cerere",inainte:cerere?cerere.inainte:null};
__st(__CAM,cuPasi({timp_sim:2501,faza:0,verde_s:41,comanda_citita_ts:888,pana_la_faza_s:[0,14,8,14,14]})); await actualizeaza();
Object.assign(rez.fara_ts,urm(),{citita:!!(cerere&&cerere.citita)});
// B1: o singură stare fără simulare în timpul urmăririi (serverul n-a putut citi fișierul chiar atunci) nu încheie urmărirea
__st(__CAM,cuPasi({timp_sim:2600,verde_s:9,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
await clic(1); const tB1=__ultimTs;
__st(__CAM,cuPasi({timp_sim:2601,verde_s:10,citire_peste_s:4,pana_la_faza_s:[0,49,43,49,49],comanda_citita_ts:tB1})); await actualizeaza();
cerere.la-=15000;   // 15 s pe ceasul paginii de la clic, iar verdele cerut vine abia peste ≈49 s
__st(__CAM,null); await actualizeaza(); rez.o_stare_lipsa={lipsa:urm()};
__st(__CAM,cuPasi({timp_sim:2603,verde_s:12,citire_peste_s:2,pana_la_faza_s:[0,47,41,47,47],comanda_citita_ts:tB1})); await actualizeaza(); rez.o_stare_lipsa.dupa=urm();
// controlul: simularea chiar s-a oprit (ultima ei stare e veche de 12 s), deci urmărirea se încheie
__st(__CAM,Object.assign(cuPasi({timp_sim:2603,verde_s:12,comanda_citita_ts:tB1}),{_varsta_s:12})); await actualizeaza(); rez.o_stare_lipsa.oprita=urm();
// B2: comanda în vigoare cere N–S, dar după verdele maxim semaforul a dat singur verde pe Dacia: clicul pe Dacia se trimite
const aB2=Date.now()/1000;
__st(__CAM,cuPasi({timp_sim:2700,faza:1,faza_tinta:1,verde_s:4,verde_min_s:10,pana_la_faza_s:[17,0,17,17,17],comanda_citita_ts:aB2-100}),{comanda:{mod:"manual",faza:0,timestamp:aB2-100,_varsta_s:100}});
await actualizeaza(); cerere=null; await actualizeaza();
rez.alternanta={urmeaza0:faza(0).className,apasat1:faza(1).getAttribute("aria-pressed")};
let nB2=__posts.length; await clic(1); Object.assign(rez.alternanta,{trimise:__posts.length-nB2,corp:__posts[__posts.length-1],rezultat:text("rezultat")});
// controlul: comanda în vigoare chiar cere Dacia, sau nu se poate citi: „deja activă”, fără trimitere
__st(__CAM,cuPasi({timp_sim:2720,faza:1,faza_tinta:1,verde_s:19,verde_min_s:10,pana_la_faza_s:[11,0,11,11,11],comanda_citita_ts:aB2-5}),{comanda:{mod:"manual",faza:1,timestamp:aB2-5,_varsta_s:5}});
await actualizeaza(); cerere=null; nB2=__posts.length; await clic(1); rez.alternanta.ceruta={rezultat:text("rezultat"),trimise:__posts.length-nB2};
__st(__CAM,cuPasi({timp_sim:2721,faza:1,faza_tinta:1,verde_s:20,verde_min_s:10,pana_la_faza_s:[10,0,10,10,10],comanda_citita_ts:aB2-5})); await actualizeaza(); cerere=null;
nB2=__posts.length; await clic(1); rez.alternanta.necitita={rezultat:text("rezultat"),trimise:__posts.length-nB2};
// B3: un răspuns /api/state mai vechi, sosit după unul mai nou, se ignoră; la fel o eroare veche, sosită după un răspuns bun
let tine=null; const eliberari=[], fB3=window.fetch;
window.fetch=async(u,o)=>{ const fel=String(u).includes("/api/state")?tine:null; if(!fel) return fB3(u,o); tine=null;
  const st=JSON.parse(JSON.stringify(window.__stare)); await new Promise(r=>eliberari.push(r)); if(fel=="eroare") throw new TypeError("Failed to fetch"); return {ok:true,status:200,json:async()=>st} };
__st(__CAM,cuPasi({timp_sim:2800,verde_s:9,comanda_citita_ts:__ultimTs})); await actualizeaza(); cerere=null;
await clic(1); const tB3=__ultimTs;
tine="lent"; const lenta=actualizeaza();          // citirea stării 2800, încă fără ecoul comenzii, rămâne pe drum
__st(__CAM,cuPasi({timp_sim:2801,verde_s:10,citire_peste_s:4,pana_la_faza_s:[0,49,43,49,49],comanda_citita_ts:tB3})); await actualizeaza();
rez.ordine={citita:!!(cerere&&cerere.citita)};
eliberari.shift()(); await lenta; Object.assign(rez.ordine,urm(),{timp_sim:sim&&sim.timp_sim});
tine="eroare"; const lenta2=actualizeaza(); await actualizeaza(); eliberari.shift()(); await lenta2;
rez.ordine.eroare_veche={legatura,alerte:document.querySelectorAll(".alerta").length};
window.fetch=fB3;
// B4: două comenzi repede, iar răspunsul celei de-a doua nu vine (oprit la 4 s): ecoul primeia nu e luat drept al celei de-a doua
__st(__CAM,cuPasi({timp_sim:2900,verde_s:40,verde_min_s:35,comanda_citita_ts:1000})); await actualizeaza(); cerere=null;
await clic(1); const tA4=__ultimTs;
const fB4=window.fetch; window.fetch=async(u,o)=>{ if(!String(u).includes("/api/command")) return fB4(u,o); window.fetch=fB4; window.__posts.push(JSON.parse(o.body));
  window.__ultimTs=Math.max(Date.now()/1000,window.__ultimTs+0.001); throw new DOMException("The user aborted a request.","AbortError") };   // a ajuns la server, dar răspunsul nu
await clic(2); const tB4=__ultimTs; rez.fara_raspuns={inainte:!!cerere&&cerere.inainte===tA4,fara_ts:!!cerere&&cerere.ts===undefined};
__st(__CAM,cuPasi({timp_sim:2901,verde_s:41,citire_peste_s:4,pana_la_faza_s:[0,10,10,10,10],comanda_citita_ts:tA4})); await actualizeaza();
rez.fara_raspuns.ecou_vechi=Object.assign(urm(),{citita:!!(cerere&&cerere.citita)});
__st(__CAM,cuPasi({timp_sim:2902,verde_s:42,citire_peste_s:3,pana_la_faza_s:[0,9,9,9,9],comanda_citita_ts:tB4})); await actualizeaza();
rez.fara_raspuns.ecou_nou=Object.assign(urm(),{pe_al_ei:!!cerere&&cerere.ts_citit===tB4});
// B5: confirmarea preluării, deschisă pe verdele N–S; planul pornește apoi schimbarea spre Dacia: confirmarea se închide, fără trimitere
const plan=o=>cuPasi(Object.assign({mod:"program",mod_program:"plan_observat"},o));
__st(__CAM,plan({timp_sim:3000,faza:0,verde_s:65})); await actualizeaza(); cerere=null;
let nB5=__posts.length; bt("manual").click(); rez.preluare_schimbata={deschisa:text("confirm-text")};
__st(__CAM,plan({timp_sim:3001,faza:0,faza_tinta:1,pas:"degajare",pas_ramas_s:5,verde_s:66,pana_la_tinta_s:10,pana_la_faza_s:[60,10,54,60,60]})); await actualizeaza();
Object.assign(rez.preluare_schimbata,{confirm:$("confirm").classList.contains("vizibil"),rezultat:text("rezultat"),cls:$("rezultat").className,trimise:__posts.length-nB5});
// „Da” trimite faza arătată în confirmare, chiar dacă starea s-a schimbat între două citiri ale paginii
bt("manual").click(); rez.preluare_schimbata.a_doua=text("confirm-text");
sim=Object.assign({},sim,{faza:1,faza_tinta:0,pas:"degajare"});   // fără o citire nouă, deci fără verificarea care închide confirmarea
nB5=__posts.length; await $("da").onclick(); Object.assign(rez.preluare_schimbata,{corp:__posts[__posts.length-1],trimise_da:__posts.length-nB5});
// B6: spre o fază cu risc, intrările verzi în amândouă fazele rămân pe verde, în schemă și în texte
__st(__CAM,cuPasi({timp_sim:3100,faza:0,verde_s:40})); await actualizeaza(); cerere=null;
faza(3).click(); await $("da").onclick(); const t3=__ultimTs;
__st(__CAM,cuPasi({timp_sim:3106,faza:0,faza_tinta:3,pas:"galben",pas_ramas_s:3,verde_s:46,pana_la_tinta_s:5,pana_la_faza_s:[60,60,60,5,60],comanda_citita_ts:t3})); await actualizeaza();
rez.spre_risc={galben:{rezultat:text("rezultat"),det:text("faza-det"),lumini:titluri()}};
__st(__CAM,cuPasi({timp_sim:3109,faza:0,faza_tinta:3,pas:"rosu",pas_ramas_s:2,verde_s:46,pana_la_tinta_s:2,pana_la_faza_s:[60,60,60,2,60],comanda_citita_ts:t3})); await actualizeaza();
rez.spre_risc.rosu={rezultat:text("rezultat"),det:text("faza-det"),lumini:titluri()};
// între cele două faze cu risc rămân pe verde toate intrările
cerere=null; __st(__CAM,cuPasi({timp_sim:3120,faza:3,faza_tinta:4,pas:"rosu",pas_ramas_s:1,verde_s:20,verde_min_s:10,pana_la_tinta_s:1,pana_la_faza_s:[60,60,60,60,1]})); await actualizeaza();
rez.spre_risc.intre={det:text("faza-det"),lumini:titluri()};
// B7: numărătoarea până la schimbarea automată nu se arată cât e cerută de aici altă fază
__st(__CAM,cuPasi({timp_sim:3202,faza:0,verde_s:62,citire_peste_s:3,pana_la_faza_s:[0,14,8,14,14]})); await actualizeaza(); cerere=null; await actualizeaza();
rez.numaratoare={inainte:text("faza-det")};
await clic(1); const t7=__ultimTs;
__st(__CAM,cuPasi({timp_sim:3203,faza:0,verde_s:63,citire_peste_s:2,pana_la_faza_s:[0,13,7,13,13],comanda_citita_ts:t7})); await actualizeaza();
Object.assign(rez.numaratoare,{dupa:text("faza-det"),rezultat:text("rezultat")});
// un geamăn fără câmpurile pașilor, dar cu faza_tinta, spre o fază cu risc: textul de sub butoane spune, ca schema, cine rămâne pe verde
const faraPasi=o=>nou(s=>Object.assign(s,{mod:"manual",mod_program:null},o));
__st(__CAM,faraPasi({timp_sim:3300,faza:0,etapa:"green",verde_s:40})); await actualizeaza(); cerere=null;
faza(3).click(); await $("da").onclick();
__st(__CAM,faraPasi({timp_sim:3306,faza:0,etapa:"yellow",faza_tinta:3,verde_s:46})); await actualizeaza(); rez.fara_pasi_spre_risc={galben:text("rezultat")};
__st(__CAM,faraPasi({timp_sim:3309,faza:0,etapa:"red",faza_tinta:3,verde_s:46})); await actualizeaza(); rez.fara_pasi_spre_risc.rosu={rezultat:text("rezultat"),lumini:titluri()};
__st(__CAM,faraPasi({timp_sim:3310,faza:0,etapa:"red",verde_s:46})); await actualizeaza(); rez.fara_pasi_spre_risc.fara_tinta=text("rezultat");   // fără faza_tinta, textul de până acum
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# reîncărcarea adevărată: starea cu o comandă încă în curs e gata înaintea primei citiri a paginii
INCARCARE = r"""
const __acum=Date.now()/1000;
__st(__CAM,Object.assign(JSON.parse(JSON.stringify(__SIM)),{mod:"manual",mod_program:null,timp_sim:700,faza:0,verde_s:20,pas:"verde",pas_ramas_s:null,faza_tinta:0,
  pana_la_tinta_s:0,verde_min_s:35,verde_max_s:90,cadenta_s:5,citire_peste_s:0,pana_la_faza_s:[0,50,44,50,50],durate_s:{galben:3,rosu:2,degajare:6},comanda_citita_ts:__acum-8}),
  {comanda:{mod:"manual",faza:1,timestamp:__acum-8,_varsta_s:8},comenzi:[{mod:"program",timestamp:__acum-300},{mod:"manual",faza:0,timestamp:__acum-60},{mod:"manual",faza:1,timestamp:__acum-8}],ora_server:__acum});
"""
DUPA_INCARCARE = r"""
const rez={};
try{
const text=id=>$(id).textContent;
rez.dupa={istoric:[...document.querySelectorAll("#istoric-lista li")].map(l=>l.textContent),vizibil:!$("istoric-parte").hidden,rezultat:text("rezultat"),faza:cerere?cerere.faza:null,revino:$("revino").hidden?null:text("revino")};
window.__stare.simulare=Object.assign(JSON.parse(JSON.stringify(window.__stare.simulare)),{timp_sim:751,faza:1,faza_tinta:1,verde_s:0,verde_min_s:10,pana_la_faza_s:[25,0,19,25,25]}); await actualizeaza();
rez.aplicata={rezultat:text("rezultat"),cls:$("rezultat").className,istoric:text("istoric-lista")};
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""


def ruleaza_pagina(d: Path, pagina: str) -> dict:
    """Pagina, în Chrome fără fereastră, cu un profil separat și fără cererile de fundal ale lui Chrome; întoarce rezultatele scenariului
    din `<pre id="rez">`. Dacă scenariul a aruncat o eroare, ea apare aici, cu locul ei, nu ca un scenariu neîncheiat."""
    f = d / "pagina.html"
    f.write_text(pagina, encoding="utf-8")
    cmd = [C.CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={d / 'profil'}", "--no-first-run", "--no-default-browser-check",
           "--disable-background-networking", "--disable-component-update", "--allow-file-access-from-files",
           "--virtual-time-budget=30000", "--window-size=1366,1500", "--dump-dom", f.as_uri()]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    m = re.search(r'<pre id="rez">(.*?)</pre>', r.stdout.decode("utf-8", "replace"), re.S)
    if not m:
        raise AssertionError("Scenariul din pagină nu s-a încheiat: " + r.stderr.decode("utf-8", "replace")[-400:])
    rez = json.loads(html.unescape(m.group(1)))
    if "__eroare" in rez:
        raise AssertionError("Scenariul din pagină a aruncat: " + rez["__eroare"])
    return rez


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestPagina(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        cls.r = ruleaza_pagina(cls.d, C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), SCENARII))

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
        # un geamăn fără pașii publicați: termenul fix, de 65 s, acoperă cazul cel mai lung (60 s simulate), deci la 40 s comanda e încă în curs
        self.assertIn("Se schimbă spre", self.r["faza_in_curs"])
        self.assertIn("Se schimbă spre", self.r["faza_in_curs_40"])
        self.assertIn("35 s pe Magheru și Lascăr Catargiu", self.r["faza_in_curs"])
        s = self.r["faza_expirata"]
        self.assertIn("n-a aplicat", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")
        self.assertIn("neaplicată", s["istoric"])
        self.assertNotIn("urmeaza", s["clasa"])

    def test_termenul_vine_din_pasii_simularii(self):
        self.assertIn("Așteptăm simularea", self.r["pasi_trimis"])
        c = self.r["pasi_citit"]
        self.assertEqual(c["termen"], 501 + 49 + 3)                    # prima stare cu comanda citită + pana_la_faza_s + marja
        self.assertIn("mai ține cel puțin 25 s", c["rezultat"])
        self.assertIn("vine în ≈49 s", c["rezultat"])
        p = self.r["pasi_40"]                                          # 40 s pe ceasul paginii, dar încă în termen pe timp_sim
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", p["rezultat"])
        self.assertIn("pietonii își termină traversarea, încă 5 s", p["rezultat"])
        self.assertIn("vine în ≈10 s", p["rezultat"])
        self.assertTrue(p["faza"].startswith("Se schimbă spre: Verde pe Bd. Dacia"), p["faza"])
        self.assertIn("vehiculele mai au verde", p["det"])
        self.assertIn("urmeaza", p["urmeaza"])
        self.assertEqual(p["apasat"], "false")
        e = self.r["pasi_expirat"]
        self.assertIn("n-a aplicat", e["rezultat"])
        self.assertIn("52 s", e["rezultat"])
        self.assertEqual(e["rez_cls"], "rau")
        self.assertIn("neaplicată", e["istoric"])
        self.assertIn("Schimbarea pornește acum", self.r["pasi_porneste"])
        self.assertIn("vine în ≈11 s", self.r["pasi_porneste"])
        a = self.r["pasi_aplicat"]
        self.assertIn("Aplicat", a["rezultat"])
        self.assertEqual(a["cls"], "bun")
        self.assertIn("aplicată", a["istoric"])

    def test_in_degajare_tinta_e_faza_urmatoare(self):
        d = self.r["degajare"]
        self.assertEqual(d["faza"], "Se schimbă spre: Verde pe Magheru și Lascăr Catargiu")
        self.assertIn("pietonii își termină traversarea, încă 4 s", d["det"])
        self.assertEqual(d["preluare"], 0)
        self.assertIn("Rămâne „Verde pe Magheru și Lascăr Catargiu”, spre care se schimbă acum semaforul", d["confirmare"])
        self.assertEqual(d["corp"], {"mod": "manual", "faza": 0})
        self.assertIn("Aplicat", d["preluata"])
        self.assertIn("urmeaza", d["urmeaza"])
        self.assertEqual(d["apasat1"], "false")
        self.assertEqual(d["trimise"], 1)          # în degajare, faza care se încheie nu mai e „deja activă”

    def test_comanda_inlocuita_si_simularea_repornita(self):
        i = self.r["inlocuita_alt"]
        self.assertIn("înlocuită de o comandă mai nouă", i["rezultat"])
        self.assertIn("înlocuită", i["ultima"])
        self.assertFalse(i["urmarita"])
        r = self.r["repornita"]
        self.assertIn("a pornit din nou", r["rezultat"])
        self.assertIn("neconfirmată", r["ultima"])

    def test_verdele_maxim_si_etapa_scurta_cu_pasi(self):
        self.assertIn("mai sunt 24 s", self.r["verde_lung_pasi"])      # verdele maxim la 521, prima decizie la 525
        self.assertEqual(self.r["preluare_pasi"], [0, 0, 0, 2])
        self.assertEqual(self.r["in_scurta"], "Golirea centrului, fără pietoni")
        self.assertEqual(self.r["spre_scurta"]["faza"], "Se schimbă spre: Golirea centrului, fără pietoni")
        self.assertIn("galben, încă 2 s", self.r["spre_scurta"]["det"])

    def test_reincarcarea_reface_comenzile(self):
        r = self.r["reincarcare"]
        self.assertEqual(len(r["istoric"]), 3)                          # linia stricată din jurnal se sare
        self.assertIn("Verde pe Bd. Dacia, est și vest: se aplică", r["istoric"][0])
        self.assertIn("Verde pe Magheru și Lascăr Catargiu: trimisă", r["istoric"][1])
        self.assertIn("Planul observat: trimisă", r["istoric"][2])
        self.assertTrue(r["vizibil"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", r["rezultat"])
        self.assertEqual(r["faza"], 1)
        self.assertIn("Planul observat", r["revino"])
        self.assertIn("trimisă", self.r["reincarcare_veche"]["istoric"])
        self.assertFalse(self.r["reincarcare_veche"]["urmarita"])     # mai veche de 70 s: doar în istoric
        self.assertFalse(self.r["reincarcare_aplicata"]["urmarita"])  # deja aplicată: nimic de urmărit

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
        for bucata in ("≈20 s pe Dacia", "≈40–45 s", "≈100 s", "6 s", "Magheru și Lascăr Catargiu, cel puțin 35 s", "la fiecare 5 s",
                       "roșu 2 s pentru cine trebuie să oprească"):   # duratele măsurate pe controler, ținând fiecare fază
            self.assertIn(bucata, self.r["manual_text"])
        self.assertNotIn("toate direcțiile", self.r["manual_text"])     # spre fazele cu risc, unele intrări rămân pe verde

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

    # blocurile de după revizia din 8.11
    def test_ceruta_in_degajarea_din_faza_ei_si_inlocuita_dupa_citire(self):
        c = self.r["ceruta_in_degajare"]
        self.assertEqual(c["trimise"], 1)                         # în degajare, faza care se încheie nu mai e „deja activă”
        self.assertTrue(c["urmarita"] and c["citita"])
        self.assertIn("Întâi se încheie schimbarea spre „Verde pe Magheru și Lascăr Catargiu”", c["rezultat"])
        self.assertNotIn("Aplicat", c["rezultat"])
        i = self.r["inlocuita_dupa_citire"]
        self.assertTrue(i["rezultat"].startswith("Comanda „Verde pe Bd. Dacia, est și vest” a fost înlocuită de o comandă mai nouă, dată din altă parte."), i["rezultat"])
        self.assertIn("înlocuită", i["ultima"])
        self.assertFalse(i["urmarita"])
        g = self.r["reincarcare_degajare"]                       # la fel, după o reîncărcare a paginii
        self.assertTrue(g["urmarita"])
        self.assertIn("Întâi se încheie schimbarea spre „Verde pe Magheru și Lascăr Catargiu”", g["rezultat"])
        self.assertNotIn("Aplicat", g["rezultat"])

    def test_necitita_in_10_s_pe_calea_cu_pasi(self):
        n = self.r["necitita"]
        self.assertIn("Simularea n-a citit comanda „Verde pe Bd. Dacia, est și vest” în 10 s", n["rezultat"])
        self.assertEqual(n["cls"], "rau")
        self.assertIn("neaplicată", n["ultima"])
        self.assertFalse(n["urmarita"])

    def test_clicul_pe_faza_de_acum_anuleaza_alta_faza_ceruta(self):
        a = self.r["anulare"]
        self.assertEqual(a["trimise"], 1)
        self.assertEqual(a["corp"], {"mod": "manual", "faza": 0})
        self.assertNotIn("deja activă", a["rezultat"])

    def test_textele_pasilor_cand_nicio_intrare_nu_ramane_pe_verde(self):
        self.assertIn("Semaforul hotărăște la fiecare 5 s: următoarea dată, peste 3 s.", self.r["pasi_decizie"])
        g, r = self.r["pasi_galben"], self.r["pasi_rosu"]
        self.assertIn("Acum: galben, încă 2 s; apoi roșu 2 s pentru toți.", g["rezultat"])
        self.assertIn("Acum: roșu pentru toți, încă 1 s.", r["rezultat"])
        self.assertTrue(g["det"].startswith("galben, încă 2 s · "), g["det"])
        self.assertTrue(r["det"].startswith("roșu pentru toți, încă 1 s, cât se eliberează intersecția · "), r["det"])
        self.assertIn("Magheru: galben", g["lumini"])
        self.assertIn("Magheru: roșu de degajare", r["lumini"])

    def test_raspunsul_serverului_fara_timestamp(self):
        e = self.r["fara_ts"]
        self.assertEqual((e["ts"], e["inainte"]), ("undefined", 777))
        self.assertTrue(e["urmarita"] and e["citita"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", e["rezultat"])

    def test_o_stare_lipsa_nu_incheie_urmarirea(self):
        o = self.r["o_stare_lipsa"]
        self.assertTrue(o["lipsa"]["urmarita"])                 # 15 s de la clic, dar ultima stare bună e de acum o clipă
        self.assertTrue(o["dupa"]["urmarita"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", o["dupa"]["rezultat"])
        self.assertIn("Nu știm dacă „Verde pe Bd. Dacia, est și vest” s-a aplicat: simularea nu trimite date.", o["oprita"]["rezultat"])
        self.assertFalse(o["oprita"]["urmarita"])

    def test_in_alternanta_clicul_pe_faza_verde_se_trimite(self):
        a = self.r["alternanta"]
        self.assertEqual(a["apasat1"], "true")
        self.assertIn("urmeaza", a["urmeaza0"])                  # faza comenzii în vigoare, la care revine semaforul
        self.assertEqual((a["trimise"], a["corp"]), (1, {"mod": "manual", "faza": 1}))
        self.assertNotIn("deja activă", a["rezultat"])
        for k in ("ceruta", "necitita"):                           # comanda în vigoare cere chiar Dacia, sau nu se poate citi
            self.assertEqual(a[k]["rezultat"], "„Verde pe Bd. Dacia, est și vest” e deja activă.")
            self.assertEqual(a[k]["trimise"], 0)

    def test_raspunsurile_vechi_sosite_tarziu_se_ignora(self):
        o = self.r["ordine"]
        self.assertTrue(o["citita"])
        self.assertEqual(o["timp_sim"], 2801)
        self.assertTrue(o["urmarita"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", o["rezultat"])
        self.assertEqual(o["eroare_veche"], {"legatura": True, "alerte": 0})

    def test_ecoul_comenzii_dinainte_nu_e_luat_drept_al_ei(self):
        f = self.r["fara_raspuns"]
        self.assertTrue(f["inainte"] and f["fara_ts"])
        v = f["ecou_vechi"]
        self.assertFalse(v["citita"])
        self.assertTrue(v["urmarita"])
        self.assertIn("Nu știm încă dacă „Verde pentru pietoni, pe toate trecerile” a ajuns", v["rezultat"])
        n = f["ecou_nou"]
        self.assertTrue(n["pe_al_ei"] and n["urmarita"])
        self.assertIn("Se schimbă spre: Verde pentru pietoni", n["rezultat"])

    def test_preluarea_trimite_faza_aratata(self):
        p = self.r["preluare_schimbata"]
        self.assertIn("Rămâne faza de acum", p["deschisa"])
        self.assertFalse(p["confirm"])
        self.assertEqual(p["rezultat"], "Între timp semaforul a pornit schimbarea spre „Verde pe Bd. Dacia, est și vest”. Comanda nu s-a trimis; "
                                        "dacă vreți să preluați, apăsați din nou „Comandă manuală”.")
        self.assertEqual((p["cls"], p["trimise"]), ("rau", 0))
        self.assertIn("Rămâne „Verde pe Bd. Dacia, est și vest”, spre care se schimbă acum semaforul", p["a_doua"])
        self.assertEqual((p["trimise_da"], p["corp"]), (1, {"mod": "manual", "faza": 1}))

    def test_spre_o_faza_cu_risc_unele_intrari_raman_pe_verde(self):
        g, r, i = (self.r["spre_risc"][k] for k in ("galben", "rosu", "intre"))
        self.assertIn("Acum: galben, încă 3 s, apoi roșu 2 s pentru cine trebuie să oprească; Magheru și Lascăr Catargiu rămân pe verde.", g["rezultat"])
        self.assertIn("Acum: roșu pentru cine trebuie să oprească, încă 2 s; Magheru și Lascăr Catargiu rămân pe verde.", r["rezultat"])
        self.assertTrue(g["det"].startswith("galben, încă 3 s; Magheru și Lascăr Catargiu rămân pe verde · "), g["det"])
        self.assertTrue(r["det"].startswith("roșu pentru cine trebuie să oprească, încă 2 s, cât se eliberează intersecția; Magheru și Lascăr Catargiu rămân pe verde · "), r["det"])
        for s in (g, r):
            self.assertNotIn("pentru toți", s["rezultat"] + s["det"])
            for lumina in ("Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: roșu", "Dacia vest: roșu"):
                self.assertIn(lumina, s["lumini"])
        self.assertTrue(i["det"].startswith("roșu pentru cine trebuie să oprească, încă 1 s, cât se eliberează intersecția; toate intrările rămân pe verde · "), i["det"])
        self.assertEqual(sorted(l for l in i["lumini"] if not l.startswith("Pietonii")),
                         sorted(["Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: verde", "Dacia vest: verde"]))

    def test_numaratoarea_se_ascunde_cat_e_ceruta_alta_faza(self):
        n = self.r["numaratoare"]
        self.assertIn("mai sunt 28 s până la schimbarea automată", n["inainte"])
        self.assertNotIn("mai sunt", n["dupa"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", n["rezultat"])

    def test_geamanul_fara_pasi_spune_cine_ramane_pe_verde(self):
        v = self.r["fara_pasi_spre_risc"]
        r = v["rosu"]
        self.assertIn("Acum: galben; Magheru și Lascăr Catargiu rămân pe verde.", v["galben"])
        self.assertIn("Acum: roșu pentru cine trebuie să oprească; Magheru și Lascăr Catargiu rămân pe verde.", r["rezultat"])
        for text in (v["galben"], r["rezultat"]):
            self.assertNotIn("pentru toți", text)
        for lumina in ("Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: roșu", "Dacia vest: roșu"):   # la fel ca schema
            self.assertIn(lumina, r["lumini"])
        self.assertIn("Acum: roșu pentru toți.", v["fara_tinta"])      # un geamăn fără faza_tinta: textul de până acum


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestReincarcare(unittest.TestCase):
    """Pagina deschisă din nou, cu o comandă încă în curs: „Ultimele comenzi” și urmărirea revin, din `/api/state`."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        p = C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), DUPA_INCARCARE)
        p = p.replace("<script>\nconst NUME=", "<script>" + INCARCARE + "</script>\n<script>\nconst NUME=", 1)   # după simulări, înaintea paginii
        cls.r = ruleaza_pagina(cls.d, p)

    def test_comanda_in_curs_se_urmareste_dupa_reincarcare(self):
        r = self.r["dupa"]
        self.assertEqual(len(r["istoric"]), 3)
        self.assertIn("Verde pe Bd. Dacia, est și vest: se aplică", r["istoric"][0])
        self.assertIn("Planul observat: trimisă", r["istoric"][2])
        self.assertTrue(r["vizibil"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", r["rezultat"])
        self.assertEqual(r["faza"], 1)
        self.assertIn("Planul observat", r["revino"])
        a = self.r["aplicata"]
        self.assertIn("Aplicat", a["rezultat"])
        self.assertEqual(a["cls"], "bun")
        self.assertIn("aplicată", a["istoric"])


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

    def test_pagina_si_serverul_folosesc_acelasi_timestamp(self):
        # pagina își recunoaște comanda după `timestamp`: cel din răspuns e cel din fișier, din jurnal și din /api/state
        r = self.c.post("/api/command", json={"mod": "manual", "faza": 1}).get_json()
        f = json.loads((self.d / "command.json").read_text(encoding="utf-8"))
        st = self.c.get("/api/state").get_json()
        self.assertEqual(r["timestamp"], f["timestamp"])
        self.assertEqual(st["comenzi"][-1]["timestamp"], r["timestamp"])
        self.assertEqual(st["comanda"]["timestamp"], r["timestamp"])
        self.assertIsInstance(st["comanda"]["_varsta_s"], (int, float))
        self.assertIsInstance(st["ora_server"], float)

    def test_comanda_salvata_de_mana_in_alta_codificare(self):
        cmd = {"mod": "manual", "faza": 2, "timestamp": 5.0}
        for cod in ("utf-8-sig", "utf-16"):                         # Notepad: UTF-8 cu BOM sau „Unicode”, adică UTF-16
            with self.subTest(cod=cod):
                (self.d / "command.json").write_bytes(json.dumps(cmd).encode(cod))
                r = self.c.get("/api/state")
                self.assertEqual(r.status_code, 200)
                self.assertEqual({k: v for k, v in r.get_json()["comanda"].items() if k != "_varsta_s"}, cmd)

    def test_un_fisier_care_nu_e_o_comanda_nu_strica_starea(self):
        for continut in (b"[1, 2]", b"null", b"7", b'{"mod": "man', '{"mod": "manual", "nota": "ă"}'.encode("cp1250")):
            with self.subTest(continut=continut):
                (self.d / "command.json").write_bytes(continut)
                r = self.c.get("/api/state")
                self.assertEqual(r.status_code, 200)               # o listă sau null dădeau HTTP 500
                self.assertIsNone(r.get_json()["comanda"])


if __name__ == "__main__":
    unittest.main()
