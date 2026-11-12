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
from datetime import datetime, time, timedelta
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
__st(__CAM,nou(man)); await actualizeaza(); rez.manual_text=document.querySelector("#manual > p.sub").textContent; rez.legenda_fara_risc=$("leg-plus").hidden;
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
// runda a doua: nota traficului măsurat la începutul unui sfert de oră, capul tabelului pietonilor și textul rar, cerut în galbenul schimbării spre alta
cerere=null; __st(Object.assign({},__CAM,{secunde_interval:180}),__SIM); await actualizeaza(); rez.nota_devreme=text("deb-nota");
rez.pietoni_antet=[...$("t-pietoni").querySelectorAll("th")].map(x=>x.textContent); rez.titlu_ist=text("t-ist");
__st(__CAM,cuPasi({timp_sim:3400,faza:0,verde_s:44,pas:"galben",pas_ramas_s:2,faza_tinta:1,pana_la_tinta_s:4,pana_la_faza_s:[60,4,60,60,60]})); await actualizeaza(); cerere=null;
await clic(2); const t8=__ultimTs;
__st(__CAM,cuPasi({timp_sim:3401,faza:0,verde_s:44,pas:"galben",pas_ramas_s:1,faza_tinta:1,pana_la_tinta_s:3,pana_la_faza_s:[60,3,50,60,60],comanda_citita_ts:t8})); await actualizeaza();
rez.rar={rezultat:text("rezultat"),urmarita:!!cerere};
const s9=cuPasi({timp_sim:3402,faza:0,verde_s:44,pas:"rosu",pas_ramas_s:2,faza_tinta:1,pana_la_faza_s:[60,2,49,60,60],comanda_citita_ts:t8}); delete s9.pana_la_tinta_s;
__st(__CAM,s9); await actualizeaza(); rez.rar.fara_tinta_s=text("rezultat");   // un geamăn fără pana_la_tinta_s: fără secunde
// runda a treia: întâi se încheie schimbarea spre o fază cu risc; în bandă, doar numele ei scurt (întreg, sub fază)
__st(__CAM,cuPasi({timp_sim:3500,faza:0,verde_s:44,pas:"galben",pas_ramas_s:2,faza_tinta:4,pana_la_tinta_s:4,pana_la_faza_s:[60,60,60,60,4]})); await actualizeaza(); cerere=null;
await clic(2); const t10=__ultimTs;
__st(__CAM,cuPasi({timp_sim:3501,faza:0,verde_s:44,pas:"galben",pas_ramas_s:1,faza_tinta:4,pana_la_tinta_s:3,pana_la_faza_s:[60,60,50,60,3],comanda_citita_ts:t10})); await actualizeaza();
rez.rar.risc=text("rezultat");
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

# starea senzorului, în locul imaginii (GET /api/senzor, din `capturi`: o copie a lui window.__senzor), banda de sus și eticheta agentului
SENZOR = r"""
const rez={};
try{
const text=id=>$(id).textContent, vizibil=el=>!!(el.offsetWidth||el.offsetHeight||el.getClientRects().length), asteapta=ms=>new Promise(r=>setTimeout(r,ms));
const memorat=()=>{ try{ return localStorage.getItem("dispecerat.imagine") }catch(e){ return "eroare" } };
const randuri=()=>[...document.querySelectorAll("#senzor-verigi li")].map(li=>({cheie:li.dataset.cheie,stare:li.dataset.stare,punct:li.querySelector(".punct").className,
  nume:li.querySelector("b").textContent,cuvant:li.querySelector(".cuv").textContent,text:li.textContent,prag:li.querySelector(".prag").textContent,titlu:li.title}));
const panou=()=>({vizibil:vizibil($("senzor")),vechi:$("senzor").classList.contains("vechi"),eticheta:getComputedStyle($("t-senzor"),"::after").content,antet:text("senzor-antet"),
  rezumat:text("senzor-rezumat"),fisa:text("senzor-fisa"),randuri:randuri(),cereri:window.__cereriSenzor});
const raspuns=f=>{ const s=JSON.parse(JSON.stringify(__SENZOR)); f(s,k=>s.verigi.find(v=>v.cheie==k)); window.__senzor=s };   // ce răspunde serverul de acum încolo
const citeste=async()=>{ $("anunt").textContent=""; await citesteSenzorul(); return Object.assign(panou(),{anunt:text("anunt")}) };
// cu imaginea arătată, panoul e ascuns și nu se cere nimic
await actualizeaza(); await asteapta(50);
rez.inceput=Object.assign(panou(),{buton:text("b-imagine"),src:$("cadru").hasAttribute("src"),imagine:vizibil($("cadru"))});
// „Ascunde imaginea”: panoul stă în locul imaginii și se citește pe loc; focusul trece pe panou
$("b-imagine").focus(); $("b-imagine").click(); const deschidere=[text("senzor-antet"),text("senzor-rezumat")]; await asteapta(20);   // înaintea primului răspuns, apoi după el
const descriere=()=>($("senzor").getAttribute("aria-describedby")||"").split(" ").map(id=>document.getElementById(id)?document.getElementById(id).textContent:null);
rez.ascunsa=Object.assign(panou(),{buton:text("b-imagine"),imagine:vizibil($("cadru")),gol:vizibil($("cadru-gol")),src:$("cadru").hasAttribute("src"),focus:document.activeElement.id,
  memorat:memorat(),rol:$("senzor").getAttribute("role"),live:$("senzor").getAttribute("aria-live"),cam:text("s-cam"),loc:$("senzor").parentElement===$("cadru").parentElement,
  descris:$("senzor").getAttribute("aria-describedby"),descriere:descriere(),deschidere,la:Date.now()});
rez.acum=__SENZOR.ora_server*1000;   // ora răspunsului de exemplu: din ea se socotesc, în test, zilele și orele rulărilor de noapte
const c0=window.__cereriSenzor; await asteapta(10300); rez.dupa_10s=window.__cereriSenzor-c0;   // încă o citire la 10 s
// stările verigilor: cuvântul, punctul și fraza fiecăreia; un singur anunț, doar când o verigă trece în „problemă”
raspuns((s,v)=>{ Object.assign(v("camera"),{stare:"atent",fps:3.1});
  Object.assign(v("colectarea"),{stare:"problema",ultima_dovada:s.calculat_la-7300,varsta_s:7300,vehicule_urmarite:0}); Object.assign(v("colectarea").sfert,{inceput:"06:45",sfarsit:"07:00",vehicule_intrate:1,pietoni:0});
  Object.assign(v("paznicul"),{stare:"atent",in_regula:false,text:"camera: starea are 40 s"}); Object.assign(v("noaptea"),{stare:"necunoscut",eroare:"ValueError"}) });
rez.stari_1=await citeste();
raspuns((s,v)=>{ Object.assign(v("camera"),{stare:"problema",lipsa:true,ultima_dovada:null,varsta_s:null,conectat:null,fps:null});
  Object.assign(v("colectarea"),{stare:"necunoscut",ultima_dovada:null,varsta_s:null,sfert:null,vehicule_urmarite:null});
  Object.assign(v("veghea"),{stare:"problema",ultima_dovada:s.calculat_la-700,varsta_s:700,fps:2.1,pauze_5min:14,episoade_30min:5,randuri_ora:58,pauze_ora:3,
    alerta:{ora:s.calculat_la-750,semne:["rata mică: 2.1 cadre/s (mediana ultimelor 3 min)","pauze: 14 pauze de peste 2.5 s între cadre în ultimele 5 min"],dupa_ultimul_rand:true}});
  Object.assign(v("paznicul"),{stare:"problema",ultima_dovada:s.calculat_la-7300,varsta_s:7300});
  v("noaptea").stare="problema"; Object.assign(v("noaptea").lanturi[1],{stare:"lipsa",zi:null,rezultat:null,pornit:null,incheiat_la:null,pasi:null,coduri_nenule:null}) });
rez.stari_2=await citeste();
raspuns((s,v)=>{ Object.assign(v("camera"),{stare:"necunoscut",conectat:null,fps:null});
  Object.assign(v("colectarea"),{stare:"atent",ultima_dovada:s.calculat_la-1500,varsta_s:1500});
  Object.assign(v("veghea"),{stare:"necunoscut",ultima_dovada:null,varsta_s:null,ultimul_rand:null,fps:null,pauze_5min:null,episoade_30min:null,randuri_ora:null,pauze_ora:null});
  Object.assign(v("paznicul"),{stare:"necunoscut",ultima_dovada:null,varsta_s:null,in_regula:null,text:null});
  const [a,b]=v("noaptea").lanturi; v("noaptea").stare="atent"; Object.assign(a,{stare:"in_curs",incheiat_la:null}); Object.assign(b,{stare:"neinceput",pornit:null,incheiat_la:null}) });
rez.stari_3=await citeste();
raspuns((s,v)=>{ const [a,b]=v("noaptea").lanturi; v("noaptea").stare="problema"; Object.assign(a,{stare:"esuat",rezultat:"oprit: scenarii_zi",coduri_nenule:2}); b.stare="necitibil";
  v("veghea").stare="atent"; v("veghea").alerta={ora:s.calculat_la-60,semne:"nu e o listă",dupa_ultimul_rand:true}; s.fisa.publica=false });   // veghea, oprită pe o alertă de acum un minut
rez.stari_4=await citeste(); rez.stari_4_din_nou=await citeste();   // același răspuns: niciun anunț nou
raspuns(s=>{ s.fisa=null }); rez.fara_fisa=await citeste();
raspuns(s=>{ Object.assign(s.fisa,{caderi_sursa:2,caderi_neprevazute:1}) }); rez.fisa_caderi=await citeste();   // o fișă din 10.11 încoace
raspuns(s=>{ s.fisa.caderi_sursa=0 }); rez.fisa_fara_caderi=await citeste();
raspuns((s,v)=>{ v("veghea").alerta={ora:s.calculat_la-60,semne:["rata mică: jurnal …"]} }); rez.semn_taiat=await citeste();   // un semn tăiat la o cale: fără „….”
raspuns(()=>{}); rez.din_nou_ok=await citeste();
// valorile vechi: o citire reușită, dar de acum 30 s
senzorLa-=30000; afiseazaSenzorul(); rez.veche_30s=panou(); senzorLa=Date.now(); afiseazaSenzorul();
// cererea nu ajunge la server, apoi serverul răspunde cu 500, apoi cu un răspuns fără verigi: rămân valorile de până atunci, arătate ca vechi
const retea=window.fetch;
window.fetch=async(u,o)=>{ if(String(u).includes("/api/senzor")){ window.__cereriSenzor++; throw new TypeError("Failed to fetch") } return retea(u,o) };
rez.eroare_retea=await citeste(); window.fetch=retea;
window.__senzorOK=false; rez.eroare_500=await citeste(); window.__senzorOK=true;
window.__senzor={verigi:"nimic"}; rez.forma=await citeste();
window.fetch=async(u,o)=>{ if(String(u).includes("/api/senzor")){ window.__cereriSenzor++; return {ok:true,status:200,json:async()=>{ throw new SyntaxError("Unexpected token '<'") }} } return retea(u,o) };
rez.json_stricat=await citeste(); window.fetch=retea;   // un corp care nu e JSON: a ajuns la server, dar nu are forma așteptată
raspuns(()=>{}); rez.revenit=await citeste();
// fără nicio valoare citită până atunci
senzor=null; window.__senzorOK=false; rez.fara_valori=await citeste(); window.__senzorOK=true; await citesteSenzorul();
// fără legătură cu calculatorul dispeceratului: ca alerta de sus; la revenire, starea senzorului se citește pe loc
window.__netOK=false; await actualizeaza();
rez.fara_legatura=Object.assign(panou(),{cazut:ora(cazutLa),alerta:[...document.querySelectorAll(".alerta")].map(a=>a.textContent).join(" | ")});
const c1=window.__cereriSenzor; window.__netOK=true; await actualizeaza(); await asteapta(20); rez.legatura_revenita=Object.assign(panou(),{cereri_noi:window.__cereriSenzor-c1});
// un răspuns mai vechi, sosit după unul mai nou, se ignoră
let tine=false; const eliberari=[];
window.fetch=async(u,o)=>{ if(!tine||!String(u).includes("/api/senzor")) return retea(u,o); tine=false; window.__cereriSenzor++;
  const copie=JSON.parse(JSON.stringify(window.__senzor)); await new Promise(r=>eliberari.push(r)); return {ok:true,status:200,json:async()=>copie} };
raspuns((s,v)=>{ v("veghea").stare="problema" }); tine=true; $("anunt").textContent=""; const lenta=citesteSenzorul();
raspuns(()=>{}); await citesteSenzorul(); eliberari.shift()(); await lenta;
rez.tarziu=Object.assign(panou(),{anunt:text("anunt")});
// „Arată imaginea”, cu o cerere încă pe drum: răspunsul ei nu mai schimbă nimic, iar citirile se opresc
raspuns((s,v)=>{ v("camera").stare="problema" }); tine=true; const pe_drum=citesteSenzorul();
$("b-imagine").click(); eliberari.shift()(); await pe_drum; await asteapta(20); window.fetch=retea;
rez.aratata={vizibil:vizibil($("senzor")),buton:text("b-imagine"),focus:document.activeElement.id,memorat:memorat(),src:$("cadru").hasAttribute("src"),imagine:vizibil($("cadru")),
  camera:stariSenzor.camera,anunt:text("anunt"),cam:text("s-cam")};
const c2=window.__cereriSenzor; await asteapta(10500); rez.dupa_aratare=window.__cereriSenzor-c2;
// pornirea: ?imagine=0 sau 1 din adresă, altfel alegerea ținută minte; un depozit care aruncă nu oprește pagina
const dep=x=>({getItem:k=>k=="dispecerat.imagine"?x:null}), blocat={getItem:()=>{ throw new DOMException("blocat","SecurityError") }};
rez.la_pornire=[["?imagine=0",dep(null)],["?imagine=1",dep("0")],["",dep("0")],["",dep("1")],["",null],["",blocat],["?imagine=x",dep("0")],["?a=1&imagine=0",dep("1")],["",dep(null)]]
  .map(([c,d])=>imagineLaPornire(c,d));
// vechimea spusă în cuvinte, cu granițele serverului: colectarea și paznicul de urmărit peste prag, veghea de la prag
rez.tacere=[[1020,1020,false],[1020.1,1020,false],[179.9,180,true],[180,180,true],[3720,3720,false],[3720.5,3720,false],[null,180,true]]
  .map(([a,p,e])=>tacere({varsta_s:a,prag_s:p},e,"Nimic nou"));
// banda de sus, cu o comandă aplicată (deci și „Reveniți la …”)
__st(__CAM,Object.assign(JSON.parse(JSON.stringify(__SIM)),{mod:"fix",mod_program:null})); await actualizeaza(); await asteapta(100);
const banda=$("banda"), sb=getComputedStyle(banda), col=document.querySelector(".col.comanda"), r=el=>el.getBoundingClientRect();
rez.banda={parinte:banda.parentElement.tagName,dupa_alerte:!!($("alerte").compareDocumentPosition(banda)&Node.DOCUMENT_POSITION_FOLLOWING),urmatorul:banda.nextElementSibling.tagName,
  are:["cine-acum","rezultat","revino"].map(id=>$(id).parentElement===banda),pozitie:sb.position,sus:sb.top,z:sb.zIndex,fundal:sb.backgroundColor,fundal_pagina:getComputedStyle(document.body).backgroundColor,
  rol:$("rezultat").getAttribute("role"),revino:$("revino").hidden?null:text("revino"),rezultat:text("rezultat"),cine:text("cine-acum"),latime:innerWidth,inaltime:banda.offsetHeight,
  col_pozitie:getComputedStyle(col).position,col_sus:getComputedStyle(col).top};
const spatiu=document.createElement("div"); spatiu.style.height="4000px"; document.body.appendChild(spatiu); window.scrollTo(0,300); await asteapta(50);
const inEcran=el=>r(el).top>=0&&r(el).bottom<=innerHeight;
Object.assign(rez.banda,{derulat:scrollY,sus_derulat:r(banda).top,rezultat_in_ecran:inEcran($("rezultat")),revino_in_ecran:inEcran($("revino")),cine_in_ecran:inEcran($("cine-acum")),
  col_sus_derulat:r(col).top,banda_jos:r(banda).bottom});
spatiu.remove(); window.scrollTo(0,0);
// agentul IA: antrenat pe simularea veche
rez.agent={d_ai:text("d-ai"),moduri:MODURI.ai.text}; cere("ai"); rez.agent.confirmare=text("confirm-text"); $("nu").click();
rez.ajutor=$("ajutor").textContent;
// frazele unei singure verigi, dintr-o copie a răspunsului de exemplu, schimbată doar cât trebuie
const rand=(k,f)=>{ const s=JSON.parse(JSON.stringify(__SENZOR)), v=s.verigi.find(x=>x.cheie==k); f(v,s); const li=document.createElement("li"); puneRand(li,randVeriga(v));
  return {text:li.textContent,prag:li.querySelector(".prag").textContent,cuvant:li.querySelector(".cuv").textContent,titlu:li.title} };
const lant=(i,x)=>rand("noaptea",v=>Object.assign(v.lanturi[i],x));
rez.alerte={oprita:rand("veghea",v=>{ v.alerta={ora:v.ultima_dovada+20,semne:["rata mică: 3.2 cadre/s (mediana ultimelor 3 min)"],dupa_ultimul_rand:true} }),
  trecuta:rand("veghea",v=>{ v.alerta={ora:v.ultima_dovada-7200,semne:["proces: run_vision nu mai rulează"],dupa_ultimul_rand:false} }),
  fara_semne:rand("veghea",v=>{ v.alerta={ora:v.ultima_dovada,semne:[],dupa_ultimul_rand:true} }),   // fișierul alertei, prins la jumătatea scrierii
  semne_null:rand("veghea",v=>{ v.alerta={ora:v.ultima_dovada-7200,semne:null,dupa_ultimul_rand:false} }),
  fara_rand:rand("veghea",v=>{ Object.assign(v,{ultimul_rand:null,fps:null,ultima_dovada:null,varsta_s:null,alerta:{ora:__SENZOR.calculat_la-30,semne:["proces: run_vision nu mai rulează"],dupa_ultimul_rand:true}}) })};
rez.cadre=[3.47,0,0.5,1.02,3.5].map(fps=>({camera:rand("camera",v=>{ v.fps=fps }).text,veghea:rand("veghea",v=>{ v.fps=fps }).text}));
rez.csv_vechi=rand("veghea",v=>{ v.pauze_5min=null; v.pauze_ora=null });   // un CSV al vegherii mai vechi, fără pauze
rez.csv_foarte_vechi=rand("veghea",v=>{ v.pauze_5min=null; v.episoade_30min=null; v.pauze_ora=null });   // nici pauze, nici reconectări
rez.eroare=rand("noaptea",v=>{ Object.assign(v,{stare:"necunoscut",eroare:"KeyError",ultima_dovada:null,varsta_s:null}) });
const ieri=new Date(Date.now()-864e5), z2=n=>String(n).padStart(2,"0"); ieri.setHours(11,28,43,0); rez.ieri=ziua(ieri.getTime());
rez.note={repornire:rand("paznicul",v=>{ Object.assign(v,{in_regula:true,text:"repornirea ține de 600 s: încercările se numără de la capăt"}) }),
  repornire_veche:rand("paznicul",v=>{ Object.assign(v,{stare:"atent",in_regula:true,text:"repornirea ține de 600 s: încercările se numără de la capăt",varsta_s:4000}) }),
  alta:rand("paznicul",v=>{ Object.assign(v,{stare:"atent",in_regula:false,text:`jurnalul zilei crește: prima traiectorie nouă la ${ieri.getFullYear()}-${z2(ieri.getMonth()+1)}-${z2(ieri.getDate())}T11:28:43`}) })};
rez.la_noapte=Date.now();   // ziua în care se scriu rândurile de mai jos: scenariul poate trece de miezul nopții
rez.noapte={fluxul:lant(0,{stare:"in_curs",asteapta:"fluxul",incheiat_la:null,rezultat:null,pasi:null,coduri_nenule:null}),
  lant:lant(1,{stare:"neinceput",asteapta:"lant",pornit:null,incheiat_la:null,rezultat:null,pasi:null,coduri_nenule:null}),
  pornire:lant(1,{stare:"neinceput",asteapta:"pornire",pornit:null,incheiat_la:null,rezultat:null,pasi:null,coduri_nenule:null}),   // lanțul vechi s-a încheiat după 03:30
  atentie:lant(0,{atentie:"jurnalul are membri stricați",coduri_nenule:1}), atentie_generala:lant(0,{atentie:"un pas a avut o atenționare",coduri_nenule:1}),
  lunga:lant(0,{stare:"in_curs",prea_lunga:true,incheiat_la:null}), esecuri:lant(0,{stare:"esuat",rezultat:"cu_esecuri: rulare_zi",coduri_nenule:1})};
rez.durate=[75,89,90,120,3599,3600,3629,3630,7170,7199,7200,7320].map(durata);
rez.durate_jos=[0.4,59.99,89.6,3659.9,7199.9,-3].map(durata);   // și secundele cu zecimale se rotunjesc în jos
// runda a doua: sfertul de oră în patru forme; rata camerei doar când explică starea; fără câmpul legăturii; fără dosarele prelucrării de noapte
rez.colectare=[[1046,714],[0,0],[0,5],[1,0]].map(([a,b])=>rand("colectarea",v=>{ Object.assign(v.sfert,{inceput:"12:15",sfarsit:"12:30",vehicule_intrate:a,pietoni:b}) }));
rez.camera_rata=[{conectat:true,fps:5.96},{conectat:false,fps:5.9,stare:"atent"},{conectat:false,fps:0,stare:"atent"},{conectat:false,fps:null,stare:"atent"},{conectat:true,fps:3.1,stare:"atent"}].map(x=>rand("camera",v=>Object.assign(v,x)));
rez.camera_nule=[{conectat:null},{conectat:null,fps:3.1,stare:"atent"},{conectat:null,fps:0,stare:"atent"},{conectat:"da",fps:null}].map(x=>rand("camera",v=>Object.assign(v,x)));
rez.fara_dosare=rand("noaptea",v=>{ Object.assign(v,{stare:"necunoscut",fara_dosare:true,ultima_dovada:null,varsta_s:null});
  v.lanturi.forEach(l=>Object.assign(l,{stare:"lipsa",zi:null,rezultat:null,pornit:null,incheiat_la:null,pasi:null,coduri_nenule:null})) });
rez.praguri=[15,600,900,1020,3600,3720,7200].map(pragT);
rez.urmariti=[];   // rândul camerei de sub imagine: urmărirea ține și vehiculele, și pietonii
for(const n of [53,19,1,0]){ __st(Object.assign({},__CAM,{vehicule_urmarite:n}),__SIM); await actualizeaza(); rez.urmariti.push(text("s-urm")) }
// nume din prototip, date imposibile și verigi necunoscute, cu panoul din nou în locul imaginii: nimic nu aruncă și nu ajunge pe ecran „undefined”, „NaN” sau cod
$("b-imagine").click(); await asteapta(20);
raspuns((s,v)=>{ v("camera").stare="constructor"; v("colectarea").sfert.zi="2026-13-45"; v("veghea").prag_pauze=0; v("paznicul").stare="__proto__";
  const [a,b]=v("noaptea").lanturi; Object.assign(a,{cheie:"constructor",stare:"in_curs",pornit:"2026-13-45T25:61:00"}); Object.assign(b,{stare:"toString",urmatoarea:"2026-13-45T00:00:00"});
  s.verigi.push({stare:"problema"},{cheie:"constructor",stare:"toString"}); s.fisa.inceput="2026-13-45T00:00:00" });
rez.prototip={aruncat:null};
try{ await citesteSenzorul(); deseneaza() }catch(e){ rez.prototip.aruncat=String(e&&e.stack||e) }
Object.assign(rez.prototip,panou(),{tot:$("senzor").innerText});
raspuns(()=>{}); await citesteSenzorul();
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# pornirea paginii, în cinci deschideri cu același profil (a cincea, starea „senzor” din capturi): înaintea paginii, un observator numără orice `src` pus pe imagine
SURSE = r"""
window.__surse=0; window.__obs=new MutationObserver(l=>{ window.__surse+=l.length }); window.__obs.observe(document.getElementById("cadru"),{attributes:true,attributeFilter:["src"]});
"""
PORNIRE = r"""
const rez={};
try{
const vizibil=el=>!!(el.offsetWidth||el.offsetHeight||el.getClientRects().length), asteapta=ms=>new Promise(r=>setTimeout(r,ms));
const memorat=()=>{ try{ return localStorage.getItem("dispecerat.imagine") }catch(e){ return "eroare" } };
const stare=()=>({ascunsa:imagineOprita,panou:vizibil($("senzor")),imagine:vizibil($("cadru")),src:$("cadru").hasAttribute("src"),surse:window.__surse+window.__obs.takeRecords().length,
  cereri:window.__cereriSenzor,randuri:document.querySelectorAll("#senzor-verigi li").length,buton:$("b-imagine").textContent,memorat:memorat(),cautare:location.search});
await asteapta(50); rez.pornire=stare();
%DUPA%
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# așezarea pe ecranul unui laptop, 1366×641 (în ramă): panoul senzorului sub bandă, lista rând cu rând, coloana din stânga în comanda
# manuală, banda în timpul unei comenzi urmărite și „Reveniți la …” după o reîncărcare
ASEZARE = r"""
const rez={};
try{
const asteapta=ms=>new Promise(r=>setTimeout(r,ms)), r=el=>el.getBoundingClientRect(), text=id=>$(id).textContent, banda=$("banda"), col=document.querySelector(".col.comanda");
const nou=f=>{ const s=JSON.parse(JSON.stringify(__SIM)); f(s); return s };
const cuPasi=o=>nou(s=>{ Object.assign(s,{mod:"manual",mod_program:null,pas:"verde",pas_ramas_s:null,faza_tinta:0,pana_la_tinta_s:0,verde_min_s:35,verde_max_s:90,cadenta_s:5,citire_peste_s:0,
  pana_la_faza_s:[0,50,44,50,50],durate_s:{galben:3,rosu:2,degajare:6},comanda_citita_ts:1000},o); s.etapa={verde:"green",degajare:"green",galben:"yellow",rosu:"red"}[s.pas] });
await actualizeaza(); await asteapta(50); rez.ecran=[innerWidth,innerHeight];
// panoul, cu imaginea ascunsă și banda pe un rând (nicio comandă încă): de la titlu la linia fișei, încape sub bandă
$("b-imagine").click(); await asteapta(50); window.scrollTo(0,0); await asteapta(20);
const p=$("senzor"), randuri=()=>[...document.querySelectorAll("#senzor-verigi li")];
rez.panou={vizibil:!p.hidden,randuri:randuri().length,rezumat:text("senzor-rezumat"),h:r(p).height,banda:banda.offsetHeight,rand:parseFloat(getComputedStyle($("cine-acum")).lineHeight),
  rezultat:text("rezultat"),vh:innerHeight};
window.scrollTo(0,Math.round(r(p).top+scrollY-banda.offsetHeight-8)); await asteapta(20);   // derulat cât să înceapă chiar sub bandă
Object.assign(rez.panou,{sus:r(p).top,jos:r(p).bottom,fisa_jos:r($("senzor-fisa")).bottom,banda_jos:r(banda).bottom});
window.scrollTo(0,0); await asteapta(20);
// o citire nouă în care s-a schimbat doar camera rescrie doar rândul ei; celelalte rânduri rămân aceleași elemente (cititorul de ecran, o selecție)
const li0=randuri(), text0=li0.map(li=>li.textContent);
const s2=JSON.parse(JSON.stringify(window.__senzor)); s2.calculat_la+=10; s2.verigi[0].ultima_dovada+=10; window.__senzor=s2; await citesteSenzorul();
const li1=randuri();
rez.rand_cu_rand={aceleasi:li0.map((li,i)=>li===li1[i]),legate:li0.map(li=>li.isConnected),schimbate:li1.map((li,i)=>li.textContent!==text0[i]),chei:li1.map(li=>li.dataset.cheie)};
const s3=JSON.parse(JSON.stringify(s2)); s3.verigi.push({cheie:"alta",stare:"ok"}); window.__senzor=s3; await citesteSenzorul();   // altă listă de verigi: lista se refață
rez.rand_cu_rand.refacuta={randuri:randuri().length,aceleasi:randuri().filter((li,i)=>li===li1[i]).length};
window.__senzor=JSON.parse(JSON.stringify(s2)); await citesteSenzorul();
// comanda manuală: coloana din stânga, cu butoanele fazelor, e mai înaltă decât locul de sub bandă, deci se derulează cu pagina
__st(__CAM,nou(s=>{s.mod="manual";s.mod_program=null})); await actualizeaza(); await asteapta(30); window.scrollTo(0,0); await asteapta(20);
const fz=$("faze"), c0=r(col).top;
rez.coloana={lunga:col.classList.contains("lunga"),pozitie:getComputedStyle(col).position,h:col.offsetHeight,loc:innerHeight-banda.offsetHeight-16,butoane:fz.querySelectorAll("button").length,
  jos0:r(fz).bottom,vh:innerHeight};
const y=Math.ceil(r(fz).bottom-innerHeight+16); window.scrollTo(0,y); await asteapta(20);
Object.assign(rez.coloana,{y,derulat:scrollY,mutata:c0-r(col).top,faze_sus:r(fz).top,faze_jos:r(fz).bottom,banda_jos:r(banda).bottom});
window.scrollTo(0,0); await asteapta(20);
// comanda urmărită pas cu pas, cu pagina sus: banda crește o dată, la clic, apoi nu mai sare
const m=[], masura=et=>{ window.scrollTo(0,0); m.push([et,banda.offsetHeight,Math.round(r(document.querySelector("main")).top),text("rezultat")]) };
masura("inainte");
__st(__CAM,cuPasi({timp_sim:500,verde_s:20})); await actualizeaza(); cerere=null;
document.querySelector('[data-faza="1"]').click(); masura("se_trimite"); await asteapta(20); masura("primita"); const ts=__ultimTs;
for(const [o,e] of [[{timp_sim:501,verde_s:21,citire_peste_s:4,pana_la_faza_s:[0,29,23,29,29]},"citit"],[{timp_sim:516,verde_s:36,citire_peste_s:4,pana_la_faza_s:[0,14,8,14,14]},"decizie"],
  [{timp_sim:520,verde_s:40,pas:"degajare",pas_ramas_s:5,faza_tinta:1,pana_la_tinta_s:10,pana_la_faza_s:[60,10,60,60,60]},"degajare"],
  [{timp_sim:526,verde_s:46,pas:"galben",pas_ramas_s:2,faza_tinta:1,pana_la_tinta_s:4,pana_la_faza_s:[60,4,60,60,60]},"galben"],
  [{timp_sim:529,verde_s:46,pas:"rosu",pas_ramas_s:1,faza_tinta:1,pana_la_tinta_s:1,pana_la_faza_s:[60,1,60,60,60]},"rosu"],
  [{timp_sim:531,faza:1,verde_s:0,verde_min_s:10,pana_la_faza_s:[25,0,19,25,25]},"aplicat"]]){ __st(__CAM,cuPasi(Object.assign({comanda_citita_ts:ts},o))); await actualizeaza(); masura(e) }
rez.pasi=m;
// după o reîncărcare: „Reveniți la …” doar pentru comenzile date de când rulează simularea de acum (aici, de 500 s) sau, fără timp_sim, din ultima jumătate de oră
const reincarca=async(o,comenzi)=>{ cerere=null; istoric.length=0; refacut=false; modAnterior=null; modVazut=null; const t=Date.now()/1000;
  __st(__CAM,nou(s=>Object.assign(s,o)),{comenzi:comenzi.map(([mod,varsta])=>Object.assign({mod,timestamp:t-varsta},mod=="manual"?{faza:0}:{})),ora_server:t}); await actualizeaza();
  return {revino:$("revino").hidden?null:text("revino"),istoric:document.querySelectorAll("#istoric-lista li").length} };
rez.revino={ieri:await reincarca({timp_sim:500},[["manual",86460],["program",86430]]),acum_60s:await reincarca({timp_sim:500},[["manual",60],["program",30]]),
  inaintea_simularii:await reincarca({timp_sim:500},[["manual",600],["program",30]]),fara_timp_ieri:await reincarca({timp_sim:null},[["manual",86460],["program",86430]]),
  fara_timp_10min:await reincarca({timp_sim:null},[["manual",600],["program",30]])};
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# un ecran îngust, 700×900 (în ramă): banda rămâne sus, strânsă; după o comandă de la butoane, rezultatul și „Reveniți la …” se văd
INGUST = r"""
const rez={};
try{
const asteapta=ms=>new Promise(r=>setTimeout(r,ms)), r=el=>el.getBoundingClientRect(), text=id=>$(id).textContent, banda=$("banda"), bt=m=>document.querySelector(`[data-mod=${m}]`);
const inEcran=el=>{ const b=r(el); return b.height>0&&b.top>=0&&b.bottom<=innerHeight }, nou=f=>{ const s=JSON.parse(JSON.stringify(__SIM)); f(s); return s };
await actualizeaza(); await asteapta(50);
rez.inainte={ecran:[innerWidth,innerHeight],pozitie:getComputedStyle(banda).position,inaltime:banda.offsetHeight,cine:getComputedStyle($("cine-acum")).display};
bt("fix").scrollIntoView({block:"center"}); await asteapta(20); const y0=scrollY;
bt("fix").focus(); bt("fix").click(); await asteapta(20); await $("da").onclick(); await asteapta(20);
rez.trimisa={y0,rezultat:text("rezultat"),in_ecran:inEcran($("rezultat")),buton_in_ecran:inEcran(bt("fix")),pozitie:getComputedStyle(banda).position,banda_sus:r(banda).top};
__st(__CAM,nou(s=>{s.mod="fix";s.mod_program=null})); await actualizeaza(); await asteapta(30);
rez.aplicata={rezultat:text("rezultat"),in_ecran:inEcran($("rezultat")),revino:$("revino").hidden?null:text("revino"),revino_in_ecran:inEcran($("revino")),
  banda_sus:r(banda).top,buton_in_ecran:inEcran(bt("fix")),buton_sub_banda:r(bt("fix")).top>=r(banda).bottom};
rez.ajutor=[...$("ajutor").querySelectorAll("li")].map(li=>li.textContent).find(t=>t.includes("banda de sus"))||null;
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# un ecran mai înalt, 1536×1030 (în ramă): coloana comenzii manuale încape sub bandă și stă lipită sub ea; deschisă, lista fazelor
# cu risc o face prea înaltă, iar coloana se derulează cu pagina. Aici, în Chrome fără fereastră, observatorul de mărime nu se
# declanșează, deci clasa o pune desenarea de la fiecare secundă: se așteaptă 1,1 s (în pagina adevărată, observatorul o pune îndată)
INALT = r"""
const rez={};
try{
const col=document.querySelector(".col.comanda"), d=document.querySelector(".manual details"), asteapta=ms=>new Promise(r=>setTimeout(r,ms));
const stare=()=>({h:col.offsetHeight,loc:innerHeight-$("banda").offsetHeight-16,lunga:col.classList.contains("lunga"),pozitie:getComputedStyle(col).position});
const m=JSON.parse(JSON.stringify(__SIM)); m.mod="manual"; m.mod_program=null; __st(__CAM,m); await actualizeaza();
await asteapta(50); rez.ecran=[innerWidth,innerHeight]; rez.inchisa=stare();
d.open=true; await asteapta(1100); rez.deschisa=stare();
d.open=false; await asteapta(1100); rez.inchisa_iar=stare();
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# ecranele de laptop (în ramă): ciclul obișnuit al semaforului, în planul observat și în comanda manuală, cu imaginea ascunsă; la fiecare pas,
# coloana din stânga (lipită sau desprinsă); apoi panoul senzorului, sub bandă, și textul rar din bandă
CICLU = r"""
const rez={};
try{
const asteapta=ms=>new Promise(r=>setTimeout(r,ms)), col=document.querySelector(".col.comanda"), banda=$("banda"), r=el=>el.getBoundingClientRect();
const nou=f=>{ const s=JSON.parse(JSON.stringify(__SIM)); f(s); return s };
const cuPasi=o=>nou(s=>{ Object.assign(s,{mod:"manual",mod_program:null,pas:"verde",pas_ramas_s:null,faza:1,faza_tinta:1,pana_la_tinta_s:0,verde_min_s:35,verde_max_s:90,cadenta_s:5,citire_peste_s:0,
  pana_la_faza_s:[0,50,44,50,50],durate_s:{galben:3,rosu:2,degajare:6},comanda_citita_ts:1000,debit_echilibrat_veh_h:1854,varsta_debite_s:1},o);   // debitul, ca geamănul în timp real (live_twin)
  s.etapa={verde:"green",degajare:"green",galben:"yellow",rosu:"red"}[s.pas] });
await actualizeaza(); await asteapta(50); rez.ecran=[innerWidth,innerHeight];
if(!imagineOprita) $("b-imagine").click(); await asteapta(50);
window.scrollTo(0,Math.round(r($("senzor")).top+scrollY-banda.offsetHeight-8)); await asteapta(20);   // panoul, derulat chiar sub bandă
rez.panou={h:r($("senzor")).height,loc:innerHeight-banda.offsetHeight-8,jos:r($("senzor")).bottom,vh:innerHeight,rezumat:$("senzor-rezumat").textContent};
window.scrollTo(0,0); await asteapta(20);
const PASI=[["verde",{timp_sim:701,verde_s:23}],["degajare",{timp_sim:750,verde_s:47,pas:"degajare",pas_ramas_s:5,faza_tinta:0}],
  ["galben",{timp_sim:756,verde_s:47,pas:"galben",pas_ramas_s:2,faza_tinta:0}],["rosu",{timp_sim:759,verde_s:47,pas:"rosu",pas_ramas_s:1,faza_tinta:0}],
  ["verde_nou",{timp_sim:761,verde_s:1,faza:0,faza_tinta:0}],["verde_70",{timp_sim:830,verde_s:70,faza:0,faza_tinta:0}],
  ["degajare_spre_1",{timp_sim:852,verde_s:72,faza:0,pas:"degajare",pas_ramas_s:6}],["galben_spre_1",{timp_sim:858,verde_s:72,faza:0,pas:"galben",pas_ramas_s:3}],
  ["rosu_spre_1",{timp_sim:861,verde_s:72,faza:0,pas:"rosu",pas_ramas_s:2}],["verde_1",{timp_sim:863,verde_s:1}]];
const ciclu=async program=>{ const out=[]; for(const [pas,o] of PASI){ const s=cuPasi(o); if(program) Object.assign(s,{mod:"program",mod_program:"plan_observat"});
  __st(__CAM,s); await actualizeaza();
  out.push({pas,lunga:col.classList.contains("lunga"),pozitie:getComputedStyle(col).position,h:col.offsetHeight,loc:innerHeight-banda.offsetHeight-16,det:$("faza-det").textContent}) }
  return out };
rez.program=await ciclu(true); rez.manual=await ciclu(false); rez.program_iar=await ciclu(true);
// textul rar, cerut în galbenul schimbării spre Dacia, în comanda manuală venită din planul observat (deci și cu „Reveniți la …” în bandă)
cerere=null; __st(__CAM,cuPasi({timp_sim:900,faza:0,verde_s:44,pas:"galben",pas_ramas_s:2,faza_tinta:1,pana_la_tinta_s:4,pana_la_faza_s:[60,4,60,60,60]})); await actualizeaza(); cerere=null;
document.querySelector('[data-faza="2"]').click(); await asteapta(20); const t=__ultimTs;
__st(__CAM,cuPasi({timp_sim:901,faza:0,verde_s:44,pas:"galben",pas_ramas_s:1,faza_tinta:1,pana_la_tinta_s:3,pana_la_faza_s:[60,3,50,60,60],comanda_citita_ts:t})); await actualizeaza();
const g=document.createRange(); g.selectNodeContents($("rezultat"));
rez.rar={text:$("rezultat").textContent,linii:new Set([...g.getClientRects()].map(x=>Math.round(x.top))).size,revino:!$("revino").hidden,banda:banda.offsetHeight};
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# un telefon și un ecran îngust (în ramă): butonul „Plan de referință”, apăsat la 20 px de marginea de sus, cu banda goală, apoi „Confirm”; banda
# crește la „Cerere primită” și la „Aplicat”. Apoi martorii: același buton, derulat de cititor departe în jos și chiar sub bandă, când banda crește din nou
ACOPERIT = r"""
const rez={};
try{
const asteapta=ms=>new Promise(r=>setTimeout(r,ms)), r=el=>el.getBoundingClientRect(), banda=$("banda"), bt=document.querySelector('[data-mod="fix"]');
const nou=f=>{ const s=JSON.parse(JSON.stringify(__SIM)); f(s); return s }, zec=x=>Math.round(x*10)/10;
const stare=()=>({banda:banda.offsetHeight,sus:zec(r(bt).top),acoperit:Math.max(0,zec(r(banda).bottom-r(bt).top)),in_ecran:r(bt).top>=0&&r(bt).bottom<=innerHeight,
  focus:document.activeElement===bt,y:Math.round(scrollY),rezultat:$("rezultat").textContent});
const LUNG="Un text lung, pe mai multe rânduri, ca banda să crească din nou. ".repeat(5);
await actualizeaza(); await asteapta(50); rez.ecran=[innerWidth,innerHeight];
window.scrollBy(0,r(bt).top-20); await asteapta(20); rez.inainte=stare();
bt.focus(); bt.click(); await asteapta(20); rez.confirmare={deschisa:$("confirm").classList.contains("vizibil")};
if(r($("da")).bottom>innerHeight) $("da").scrollIntoView({block:"nearest"});
await $("da").onclick(); await asteapta(1100);   // fără observatorul de mărime (Chrome fără fereastră), banda se măsoară la desenarea de la fiecare secundă
rez.trimisa=stare();
__st(__CAM,nou(s=>{s.mod="fix";s.mod_program=null})); await actualizeaza(); await asteapta(30);
rez.aplicata=Object.assign(stare(),{revino:!$("revino").hidden});
window.scrollBy(0,700); await asteapta(20); const a=stare(); rezultat(LUNG); await asteapta(1100); rez.departe={inainte:a,dupa:stare()};
rezultat(""); await asteapta(1100);
window.scrollBy(0,r(bt).top-r(banda).bottom+10); await asteapta(20); const b=stare(); rezultat(LUNG); await asteapta(1100); rez.sub_banda={inainte:b,dupa:stare()};
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""

# fereastra mărită a lui Chrome pe laptopul prezentării, 1536×730 și 1536×700 (în ramă), cu imaginea ascunsă: drumul din demonstrație, fără nicio
# derulare făcută de scenariu (pagina se derulează doar singură, când mută focusul): tasta 5, „Da, preiau comanda”, „Reveniți la …” din bandă;
# apoi butoanele și confirmarea, ca înainte: o direcție obișnuită dintr-un clic, o fază cu risc cu confirmare, Esc, întoarcerea la program.
# La faza cu risc, scenariul derulează ca omul, până la buton: confirmarea se deschide deasupra butoanelor și le coboară sub cursor, deci se
# apasă din nou în locul clicului (sus, la mijloc și jos pe buton), ca la un dublu clic. La sfârșit, același drum a doua oară, pe aceeași pagină:
# banda ține de la prima comandă loc pentru două rânduri, deci coloana stă cu ≈21 px mai jos (așa a fost măsurată pagina reală pe 11.11.2026)
LAPTOP = r"""
const rez={};
try{
const asteapta=ms=>new Promise(r=>setTimeout(r,ms)), text=id=>$(id).textContent, banda=$("banda"), fz=f=>document.querySelector(`[data-faza="${f}"]`);
const loc=el=>{ const b=el.getBoundingClientRect(); return {sus:b.top,jos:b.bottom} }, inainte=(a,b)=>!!(a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING);
const focus=()=>{ const a=document.activeElement; return a.id||(a.dataset.mod?"mod:"+a.dataset.mod:a.dataset.faza!==undefined?"faza:"+a.dataset.faza:a.tagName) };
const stare=()=>({y:scrollY,vh:innerHeight,banda:loc(banda),rezumat:loc($("senzor-rezumat")),faze:[...document.querySelectorAll("#faze button")].map(loc),
  confirm:loc($("confirm")),da:loc($("da")),deschisa:$("confirm").classList.contains("vizibil"),risc:$("confirm").classList.contains("risc"),focus:focus(),text:text("confirm-text"),buton:text("da")});
const debit={debit_echilibrat_veh_h:1854,varsta_debite_s:1};   // ca geamănul în timp real (live_twin)
__st(__CAM,Object.assign(JSON.parse(JSON.stringify(__SIM_PASI)),debit)); await actualizeaza(); await asteapta(50); rez.ecran=[innerWidth,innerHeight];
if(!imagineOprita) $("b-imagine").click(); await asteapta(1100); window.scrollTo(0,0); await asteapta(20);
const ex=document.querySelector("#manual > p.sub");
rez.ordine={blocat_confirm:inainte($("blocat"),$("confirm")),confirm_manual:inainte($("confirm"),$("manual")),faze_risc:inainte($("faze"),$("faze-risc")),risc_explicatie:inainte($("faze-risc"),ex),
  faze_explicatie:inainte($("faze"),ex),explicatia_incheie:$("manual").lastElementChild===ex,manual_istoric:inainte($("manual"),$("istoric")),explicatie:ex.textContent,
  cartonas:document.querySelector("[data-mod=manual] span").textContent,pagina:document.querySelector("main").textContent.includes("Alegeți direcția")};
document.dispatchEvent(new KeyboardEvent("keydown",{key:"5"})); await asteapta(1100); rez.preluare=stare();
let n=__posts.length; $("da").click(); await asteapta(50); const ts=__ultimTs; rez.preluare.trimise=__posts.slice(n);
__st(__CAM,__pasi(Object.assign({mod:"manual",mod_program:null,timp_sim:503,verde_s:12,comanda_citita_ts:ts},debit)),{comanda:{mod:"manual",faza:0,timestamp:ts,_varsta_s:1}});
await actualizeaza(); await asteapta(1100); rez.manual=Object.assign(stare(),{rezultat:text("rezultat"),revino:$("revino").hidden?null:text("revino")});
$("revino").click(); await asteapta(1100); rez.revenire=stare();
$("nu").click(); await asteapta(50); rez.renuntat={deschisa:$("confirm").classList.contains("vizibil"),focus:focus()};
n=__posts.length; fz(1).click(); await asteapta(50); rez.directa={trimise:__posts.slice(n),deschisa:$("confirm").classList.contains("vizibil")};
document.querySelector("#manual details").open=true; await asteapta(50);   // butoanele fazelor cu risc se pot apăsa doar cu lista deschisă
const rb=fz(3), maus=()=>[fz(0),fz(1),fz(3),document.querySelector("#manual summary")].map(e=>getComputedStyle(e).pointerEvents);
rb.scrollIntoView({block:"end"}); await asteapta(50); const q=rb.getBoundingClientRect(), cx=q.left+q.width/2, puncte=[q.top+4,q.top+q.height/2,q.bottom-4];
n=__posts.length; rb.focus(); rb.click(); await asteapta(50); rez.risc=Object.assign(stare(),{trimise:__posts.length-n,derulat_de_om:scrollY,mutat:rb.getBoundingClientRect().top-q.top,maus:maus()});
// câte dintre punctele clicului cad acum, ca loc, peste un buton al direcțiilor; apoi clicul din nou, pe ce găsește mausul acolo
rez.risc.peste_directii=puncte.filter(y=>[...document.querySelectorAll("#faze button")].some(b=>{ const r=b.getBoundingClientRect(); return y>=r.top&&y<=r.bottom&&cx>=r.left&&cx<=r.right })).length;
rez.risc.sub_cursor=puncte.map(y=>{ const e=document.elementFromPoint(cx,y), b=e&&e.closest("button,summary"); if(e) e.click(); return b?(b.id||(b.dataset.faza!==undefined?"faza:"+b.dataset.faza:b.tagName)):"" });
await asteapta(50); rez.risc.dupa_clicuri={trimise:__posts.length-n,deschisa:$("confirm").classList.contains("vizibil"),risc:$("confirm").classList.contains("risc"),focus:focus()};
document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape"})); await asteapta(50); rez.risc_esc={deschisa:$("confirm").classList.contains("vizibil"),focus:focus(),trimise:__posts.length-n,maus:maus()};
$("revino").click(); await asteapta(50); rez.intoarcere_maus=maus(); n=__posts.length; $("da").click(); await asteapta(50); rez.intoarcere={trimise:__posts.slice(n),deschisa:$("confirm").classList.contains("vizibil")};
// a doua oară, pe aceeași pagină: simularea e din nou pe program, lista fazelor cu risc e închisă, pagina e sus
const ts2=__ultimTs; document.querySelector("#manual details").open=false;
__st(__CAM,Object.assign(JSON.parse(JSON.stringify(__SIM_PASI)),debit,{timp_sim:520,verde_s:29,comanda_citita_ts:ts2}),{comanda:{mod:"program",timestamp:ts2,_varsta_s:1}});
await actualizeaza(); await asteapta(1100); window.scrollTo(0,0); await asteapta(20); rez.program2={banda:loc(banda),loc_de_doua_randuri:banda.classList.contains("urmarire"),rezultat:text("rezultat")};
document.dispatchEvent(new KeyboardEvent("keydown",{key:"5"})); await asteapta(1100); rez.preluare2=stare();
$("da").click(); await asteapta(50); const ts3=__ultimTs;
__st(__CAM,__pasi(Object.assign({mod:"manual",mod_program:null,timp_sim:523,verde_s:32,comanda_citita_ts:ts3},debit)),{comanda:{mod:"manual",faza:0,timestamp:ts3,_varsta_s:1}});
await actualizeaza(); await asteapta(1100); rez.manual2=Object.assign(stare(),{rezultat:text("rezultat")});
$("revino").click(); await asteapta(1100); rez.revenire2=stare(); $("nu").click(); await asteapta(50);
// dublul clic pe „Da” al întoarcerii la program, din comanda manuală (a doua oară pe aceeași pagină): confirmarea se închide, iar butoanele
// direcțiilor urcă în locul lui „Da”. Fiecare clic merge, ca la mausul adevărat, la elementul pe care îl dă `document.elementFromPoint` în
// locul lui (funcția ține seama de pointer-events), nu direct la un buton: primul, la mijlocul lui „Da”; apoi, ca al doilea clic al unui dublu
// clic, în trei locuri ale lui „Da” (sus, la mijloc, jos), la 150 ms și din nou la 450 ms (dublul clic din Windows are 500 ms); la ≈1,5 s, încă
// un clic, în primul dintre locuri care a ajuns peste o direcție: acum clicurile merg din nou
const numeEl=e=>{ const b=e&&e.closest("button,summary"); return b?(b.id||(b.dataset.faza!==undefined?"faza:"+b.dataset.faza:b.dataset.mod?"mod:"+b.dataset.mod:b.tagName)):"" };
const clicIn=(x,y)=>{ const e=document.elementFromPoint(x,y); if(e) e.click(); return numeEl(e) };
const peDirectie=(x,y)=>[...document.querySelectorAll("#faze button")].find(b=>{ const q=b.getBoundingClientRect(); return y>=q.top&&y<=q.bottom&&x>=q.left&&x<=q.right });
$("revino").click(); await asteapta(1100);
const qd=$("da").getBoundingClientRect(), dx=qd.left+qd.width/2, locuri=[qd.top+4,qd.top+qd.height/2,qd.bottom-4];
n=__posts.length; rez.dublu={deschisa:$("confirm").classList.contains("vizibil"),buton:text("da"),primul:clicIn(dx,locuri[1])};
await asteapta(150); const peste=locuri.map(y=>{ const b=peDirectie(dx,y); return b?"faza:"+b.dataset.faza:"" });
Object.assign(rez.dublu,{inchisa:!$("confirm").classList.contains("vizibil"),peste,maus:getComputedStyle($("manual")).pointerEvents,al_doilea:locuri.map(y=>clicIn(dx,y))});
await asteapta(300); rez.dublu.al_treilea=locuri.map(y=>clicIn(dx,y)); await asteapta(50); rez.dublu.trimise=__posts.slice(n);
await asteapta(1000); n=__posts.length; rez.dublu.maus_dupa=getComputedStyle($("manual")).pointerEvents;
const yd=locuri[peste.findIndex(Boolean)]; rez.dublu.dupa=yd===undefined?null:clicIn(dx,yd); await asteapta(50); rez.dublu.trimise_dupa=__posts.slice(n);
}catch(e){ rez.__eroare=String(e&&e.stack||e) }   // o eroare ajunge în rezultat, cu locul ei, iar ruleaza_pagina o arată
const pre=document.createElement("pre"); pre.id="rez"; pre.textContent=JSON.stringify(rez); document.body.appendChild(pre);
"""


def ruleaza_pagina(d: Path, pagina: str, cautare: str = "", buget_ms: int = 30000, ecran: tuple[int, int] | None = None) -> dict:
    """Pagina, în Chrome fără fereastră, cu un profil separat și fără cererile de fundal ale lui Chrome; întoarce rezultatele scenariului
    din `<pre id="rez">`. Dacă scenariul a aruncat o eroare, ea apare aici, cu locul ei, nu ca un scenariu neîncheiat.
    `cautare` se adaugă la adresa paginii (de exemplu ?imagine=0); același `d` înseamnă același profil, deci același localStorage.
    `ecran` (lățime, înălțime): pagina stă într-o ramă de exact atâția pixeli, ca fereastra unui laptop (1366×641). Fără ramă, fereastra
    fără cadru a lui Chrome păstrează sus o margine a ei: la 641 px, pagina ar vedea doar ≈545. În ramă, adresa paginii nu are `cautare`."""
    f = d / "pagina.html"
    latime, inaltime = 1366, 1500
    if ecran:
        if cautare:
            raise ValueError("în ramă, pagina nu are adresa ei: `cautare` nu ajunge la ea")
        latime, inaltime = ecran[0] + 40, ecran[1] + 200     # rama încape toată în fereastră
        pagina = ("<!doctype html><meta charset='utf-8'><style>body{margin:0}iframe{border:0;display:block}</style>"
                  f"<iframe id='rama' width='{ecran[0]}' height='{ecran[1]}' srcdoc=\"{html.escape(pagina, quote=True)}\"></iframe>"
                  # rezultatul scenariului, copiat din ramă în pagina de afară, pe care o scrie --dump-dom
                  "<script>const t=setInterval(()=>{ const p=document.getElementById('rama').contentDocument?.getElementById('rez'); if(!p) return;"
                  " clearInterval(t); const q=document.createElement('pre'); q.id='rez'; q.textContent=p.textContent; document.body.appendChild(q) },100)</script>")
    f.write_text(pagina, encoding="utf-8")
    cmd = [C.CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={d / 'profil'}", "--no-first-run", "--no-default-browser-check",
           "--disable-background-networking", "--disable-component-update", "--allow-file-access-from-files",
           f"--virtual-time-budget={buget_ms}", f"--window-size={latime},{inaltime}", "--dump-dom", f.as_uri() + cautare]
    r = subprocess.run(cmd, capture_output=True, timeout=120, creationflags=getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0))   # ca să nu încurce colectarea
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
            self.assertNotRegex(s["det"], r"de 1[24]\s")
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
        self.assertIn("40\u00a0s", s["cam"])                    # numărul și unitatea, nedespărțite pe rânduri
        self.assertTrue(s["debite_vechi"])
        self.assertTrue(s["gol"])
        self.assertEqual(s["alerte"], [])         # o oprire scurtă nu ridică alertă
        self.assertNotIn("în mai puțin de un minut", s["gol_text"])
        l = self.r["camera_200"]
        self.assertIn("3\u00a0min 20\u00a0s", l["cam"])
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
        self.assertIn("mai sunt 20\u00a0s", self.r["verde_lung"]["det"])

    def test_cele_gasite_la_a_doua_evaluare(self):
        s = self.r["geaman_50"]
        self.assertIn("Ultimul mod cunoscut: „Planul observat”", s["cine"])
        self.assertIn("Ultima valoare primită", s["grafic"])
        self.assertNotIn("Acum:", s["grafic"])
        self.assertIn("Dacă nu revine în 2 minute, anunțați autorul proiectului", s["alerte"][0])
        self.assertIn("123 de vehicule", self.r["normal"]["det"])
        self.assertIn("e verde de 9\u00a0s", self.r["normal"]["det"])
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
        secunde = lambda t: int(re.search(r"(\d+)\u00a0s", t)[1])
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
        self.assertTrue(s["faza"].startswith("Ultima fază cunoscută (acum 50\u00a0s): Verde pe Magheru"), s["faza"])
        self.assertIn("Magheru: necunoscut; ultima culoare primită: verde", s["lumini"])
        self.assertIn("#5d6873", s["semne"])
        self.assertNotIn("#8a948c", s["semne"])
        self.assertTrue(s["eticheta"].startswith("Ultimele valori primite, vechi de 50\u00a0s"), s["eticheta"])
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
        self.assertIn("35\u00a0s pe Magheru și Lascăr Catargiu", self.r["faza_in_curs"])
        s = self.r["faza_expirata"]
        self.assertIn("n-a aplicat", s["rezultat"])
        self.assertEqual(s["rez_cls"], "rau")
        self.assertIn("neaplicată", s["istoric"])
        self.assertNotIn("urmeaza", s["clasa"])

    def test_termenul_vine_din_pasii_simularii(self):
        self.assertIn("Așteptăm simularea", self.r["pasi_trimis"])
        c = self.r["pasi_citit"]
        self.assertEqual(c["termen"], 501 + 49 + 3)                    # prima stare cu comanda citită + pana_la_faza_s + marja
        self.assertIn("mai ține cel puțin 25\u00a0s", c["rezultat"])
        self.assertIn("vine în ≈49\u00a0s", c["rezultat"])
        p = self.r["pasi_40"]                                          # 40 s pe ceasul paginii, dar încă în termen pe timp_sim
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", p["rezultat"])
        self.assertIn("pietonii își termină traversarea, încă 5\u00a0s", p["rezultat"])
        self.assertIn("vine în ≈10\u00a0s", p["rezultat"])
        self.assertTrue(p["faza"].startswith("Se schimbă spre: Verde pe Bd. Dacia"), p["faza"])
        self.assertIn("vehiculele mai au verde", p["det"])
        self.assertIn("urmeaza", p["urmeaza"])
        self.assertEqual(p["apasat"], "false")
        e = self.r["pasi_expirat"]
        self.assertIn("n-a aplicat", e["rezultat"])
        self.assertIn("52\u00a0s cu tot cu marja", e["rezultat"])
        self.assertEqual(e["rez_cls"], "rau")
        self.assertIn("neaplicată", e["istoric"])
        self.assertIn("Schimbarea pornește acum", self.r["pasi_porneste"])
        self.assertIn("vine în ≈11\u00a0s", self.r["pasi_porneste"])
        a = self.r["pasi_aplicat"]
        self.assertIn("Aplicat", a["rezultat"])
        self.assertEqual(a["cls"], "bun")
        self.assertIn("aplicată", a["istoric"])

    def test_in_degajare_tinta_e_faza_urmatoare(self):
        d = self.r["degajare"]
        self.assertEqual(d["faza"], "Se schimbă spre: Verde pe Magheru și Lascăr Catargiu")
        self.assertIn("pietonii își termină traversarea, încă 4\u00a0s", d["det"])
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
        self.assertIn("mai sunt 24\u00a0s", self.r["verde_lung_pasi"])      # verdele maxim la 521, prima decizie la 525
        self.assertEqual(self.r["preluare_pasi"], [0, 0, 0, 2])
        self.assertEqual(self.r["in_scurta"], "Golirea centrului, fără pietoni")
        self.assertEqual(self.r["spre_scurta"]["faza"], "Se schimbă spre: Golirea centrului, fără pietoni")
        self.assertIn("galben, încă 2\u00a0s", self.r["spre_scurta"]["det"])

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
        for bucata in ("≈20\u00a0s pe Dacia", "≈40–45\u00a0s", "≈100\u00a0s", "6\u00a0s", "Magheru și Lascăr Catargiu, cel puțin 35\u00a0s", "la fiecare 5\u00a0s",
                       "roșu 2\u00a0s pentru cine trebuie să oprească"):   # duratele măsurate pe controler, ținând fiecare fază
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
        self.assertEqual(i["oprita"], "Arată imaginea")
        self.assertIn("măsoară", i["stare"])
        self.assertIn("imaginea e ascunsă aici", i["stare"])
        self.assertFalse(i["gol"])                 # în locul imaginii stă starea senzorului, nu mesajul imaginii
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
        self.assertIn("Simularea n-a citit comanda „Verde pe Bd. Dacia, est și vest” în 10\u00a0s", n["rezultat"])
        self.assertEqual(n["cls"], "rau")
        self.assertIn("neaplicată", n["ultima"])
        self.assertFalse(n["urmarita"])

    def test_clicul_pe_faza_de_acum_anuleaza_alta_faza_ceruta(self):
        a = self.r["anulare"]
        self.assertEqual(a["trimise"], 1)
        self.assertEqual(a["corp"], {"mod": "manual", "faza": 0})
        self.assertNotIn("deja activă", a["rezultat"])

    def test_textele_pasilor_cand_nicio_intrare_nu_ramane_pe_verde(self):
        self.assertIn("Semaforul hotărăște la fiecare 5\u00a0s: următoarea dată, peste 3\u00a0s.", self.r["pasi_decizie"])
        g, r = self.r["pasi_galben"], self.r["pasi_rosu"]
        self.assertIn("Acum: galben, încă 2\u00a0s; apoi roșu 2\u00a0s pentru toți.", g["rezultat"])
        self.assertIn("Acum: roșu pentru toți, încă 1\u00a0s.", r["rezultat"])
        self.assertTrue(g["det"].startswith("galben, încă 2\u00a0s · "), g["det"])
        self.assertTrue(r["det"].startswith("roșu pentru toți, încă 1\u00a0s, cât se eliberează intersecția · "), r["det"])
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
        self.assertIn("Acum: galben, încă 3\u00a0s, apoi roșu 2\u00a0s pentru cine trebuie să oprească; Magheru și Lascăr Catargiu rămân pe verde.", g["rezultat"])
        self.assertIn("Acum: roșu pentru cine trebuie să oprească, încă 2\u00a0s; Magheru și Lascăr Catargiu rămân pe verde.", r["rezultat"])
        self.assertTrue(g["det"].startswith("galben, încă 3\u00a0s; Magheru și Lascăr Catargiu rămân pe verde · "), g["det"])
        self.assertTrue(r["det"].startswith("roșu pentru cine trebuie să oprească, încă 2\u00a0s, cât se eliberează intersecția; Magheru și Lascăr Catargiu rămân pe verde · "), r["det"])
        for s in (g, r):
            self.assertNotIn("pentru toți", s["rezultat"] + s["det"])
            self.assertTrue(s["rezultat"].startswith("Se schimbă spre: Verde pe Magheru–Catargiu, prin centru. Acum: "), s["rezultat"])
            self.assertNotIn("rămân deschise", s["rezultat"])          # în bandă, numele scurt: banda spune cine rămâne pe verde
            for lumina in ("Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: roșu", "Dacia vest: roșu"):
                self.assertIn(lumina, s["lumini"])
        self.assertTrue(i["det"].startswith("roșu pentru cine trebuie să oprească, încă 1\u00a0s, cât se eliberează intersecția; toate intrările rămân pe verde · "), i["det"])
        self.assertEqual(sorted(l for l in i["lumini"] if not l.startswith("Pietonii")),
                         sorted(["Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: verde", "Dacia vest: verde"]))

    def test_numaratoarea_se_ascunde_cat_e_ceruta_alta_faza(self):
        n = self.r["numaratoare"]
        self.assertIn("mai sunt 28\u00a0s până la schimbarea automată", n["inainte"])
        self.assertNotIn("mai sunt", n["dupa"])
        self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", n["rezultat"])

    def test_geamanul_fara_pasi_spune_cine_ramane_pe_verde(self):
        v = self.r["fara_pasi_spre_risc"]
        r = v["rosu"]
        self.assertIn("Acum: galben; Magheru și Lascăr Catargiu rămân pe verde.", v["galben"])
        self.assertIn("Acum: roșu pentru cine trebuie să oprească; Magheru și Lascăr Catargiu rămân pe verde.", r["rezultat"])
        for text in (v["galben"], r["rezultat"]):
            self.assertNotIn("pentru toți", text)
            self.assertTrue(text.startswith("Se schimbă spre: Verde pe Magheru–Catargiu, prin centru. Acum: "), text)
            self.assertNotIn("rămân deschise", text)
        for lumina in ("Magheru: verde", "Lascăr Catargiu: verde", "Dacia est: roșu", "Dacia vest: roșu"):   # la fel ca schema
            self.assertIn(lumina, r["lumini"])
        self.assertIn("Acum: roșu pentru toți.", v["fara_tinta"])      # un geamăn fără faza_tinta: textul de până acum

    # runda a doua a reparațiilor (B1, B8, B11)
    def test_numarul_nu_se_desparte_de_unitate(self):
        """Între număr și unitate, un spațiu care nu se rupe pe rânduri: în textul comenzii manuale, în bandă, sub fază și în nota traficului."""
        simplu = r"\d (s|min|h)\b"
        for text in (self.r["manual_text"], self.r["necitita"]["rezultat"], self.r["pasi_expirat"]["rezultat"], self.r["faza_in_curs"], self.r["normal"]["det"],
                     self.r["degajare"]["det"], self.r["verde_lung"]["det"], self.r["pasi_galben"]["det"], self.r["normal"]["nota"], self.r["nota_devreme"]):
            self.assertNotRegex(text, simplu)
        self.assertIn("Verdele de acum ține cel puțin 10\u00a0s, sau 35\u00a0s pe Magheru și Lascăr Catargiu", self.r["faza_in_curs"])
        self.assertEqual(self.r["normal"]["nota"], "Măsurat în ultimele 11\u00a0min.")
        self.assertEqual(self.r["nota_devreme"], "Valori încă nesigure: au trecut doar 3\u00a0min din acest sfert de oră.")

    def test_coloana_pietonilor_spune_numarari(self):
        """Pietonii se numără pe zone, nu ca persoane: capul coloanei spune „numărări/oră”, ca panoul senzorului."""
        self.assertEqual(self.r["pietoni_antet"], ["Pietoni care traversează", "numărări/oră"])
        self.assertNotIn("persoane/oră", self.r["text_pagina"])

    def test_textul_rar_e_scurt_si_adevarat(self):
        """Cerută altă fază în galbenul schimbării spre Dacia: întâi se încheie acea schimbare, în câte secunde, apoi vine verdele cerut;
        fără „care nu se mai poate opri” și fără pașii schimbării, care se văd sub fază (cât loc ocupă în bandă: TestLaptopMic)."""
        r = self.r["rar"]
        self.assertTrue(r["urmarita"])
        self.assertEqual(r["rezultat"], "Se schimbă spre: Verde pentru pietoni, pe toate trecerile. Întâi se încheie schimbarea spre „Verde pe Bd. Dacia, est și vest”, "
                                        "în 3\u00a0s. Verdele cerut vine în ≈50\u00a0s.")
        self.assertEqual(r["fara_tinta_s"], "Se schimbă spre: Verde pentru pietoni, pe toate trecerile. Întâi se încheie schimbarea spre „Verde pe Bd. Dacia, est și vest”. "
                                            "Verdele cerut vine în ≈49\u00a0s.")        # un geamăn fără pana_la_tinta_s: fără secunde
        self.assertIn("Întâi se încheie schimbarea spre „Verde pe Dacia, în jurul insulei”, în 3\u00a0s.", r["risc"])   # o fază cu risc: numele scurt
        self.assertNotIn("rămân deschise", r["risc"])                       # numele întreg stă sub fază, nu în bandă (N-RV-2)

    def test_titlul_graficului_nu_rupe_numarul_de_unitate(self):
        self.assertEqual(self.r["titlu_ist"], "Totalul vehiculelor oprite la semafoarele din simulare, ultimele 10\u00a0minute")   # N-RV-1


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


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestSenzor(unittest.TestCase):
    """Starea senzorului în locul imaginii: se citește doar cât se vede, spune starea fiecărei verigi în cuvinte, iar valorile
    vechi se arată ca vechi; banda de sus, cu comanda și „Reveniți la …”; eticheta agentului IA."""

    CUVINTE = {"ok": "în regulă", "atent": "de urmărit", "problema": "problemă", "necunoscut": "nu se știe"}
    PUNCTE = {"ok": ["punct", "ok"], "atent": ["punct", "atent-p"], "problema": ["punct", "err"], "necunoscut": ["punct"]}   # „nu se știe”: gri
    CHEI = ["camera", "colectarea", "veghea", "paznicul", "noaptea"]

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        cls.r = ruleaza_pagina(cls.d, C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), SENZOR), buget_ms=60000)

    def randuri(self, k):
        return {x["cheie"]: x for x in self.r[k]["randuri"]}

    @staticmethod
    def fraza(x):
        """Rândul unei verigi fără rândul pragurilor de sub el."""
        return x["text"][:len(x["text"]) - len(x["prag"])]

    def noapte(self, la="ascunsa"):
        """Rulările de noapte ale răspunsului de exemplu, socotite aici din ora lui: ultima încheiată (azi după 00:21, respectiv
        03:40, altfel ieri), pentru ziua dinaintea ei, cu data în față dacă nu e azi, și următoarea pornire, cum o spune pagina.
        `la`: pasul din scenariu după a cărui oră se judecă „azi” (pagina scrie data doar pentru altă zi decât cea de atunci)."""
        t = datetime.fromtimestamp(self.r["acum"] / 1000)
        azi = datetime.fromtimestamp((self.r["ascunsa"]["la"] if la == "ascunsa" else self.r[la]) / 1000).date()
        zi = lambda d: f"{d.day}.{d.month:02d}"

        def lant(gata):
            baza = t.date() if t.time() >= gata else t.date() - timedelta(days=1)
            return zi(baza - timedelta(days=1)), "" if baza == azi else zi(baza) + ", "
        urm = min(x for k in (0, 1) for h, m in ((0, 15), (3, 30)) if (x := datetime.combine(t.date() + timedelta(days=k), time(h, m))) > t)
        cand = {0: "azi", 1: "mâine"}.get((urm.date() - azi).days, zi(urm.date()))
        return lant(time(0, 21)), lant(time(3, 40)), f"{cand}, la {urm:%H:%M}"

    def verifica_stari(self, k, stari):
        """Fiecare verigă cu starea dată: cuvântul, punctul și o frază din cifre, nu doar culoarea."""
        r = self.r[k]["randuri"]
        self.assertEqual([x["cheie"] for x in r], self.CHEI)
        for x, stare in zip(r, stari):
            with self.subTest(pas=k, veriga=x["cheie"]):
                self.assertEqual(x["stare"], stare)
                self.assertEqual(x["cuvant"], self.CUVINTE[stare])
                self.assertEqual(x["punct"].split(), self.PUNCTE[stare])
                self.assertGreater(len(x["text"]) - len(x["prag"]), 40)
                self.assertIn("Ultimul semn de viață: ", x["prag"])
                for gresit in ("undefined", "NaN", "null", "[object", "Invalid Date"):
                    self.assertNotIn(gresit, x["text"])

    def test_cu_imaginea_aratata_panoul_e_ascuns_si_nu_se_cere(self):
        i = self.r["inceput"]
        self.assertFalse(i["vizibil"])
        self.assertEqual(i["cereri"], 0)
        self.assertEqual(i["randuri"], [])
        self.assertEqual(i["buton"], "Ascunde imaginea")
        self.assertTrue(i["src"])
        self.assertTrue(i["imagine"])

    def test_imaginea_ascunsa_lasa_locul_starii_senzorului(self):
        a = self.r["ascunsa"]
        self.assertTrue(a["vizibil"])
        self.assertTrue(a["loc"])                       # în rama imaginii, nu pe altă pagină
        self.assertFalse(a["imagine"])
        self.assertFalse(a["gol"])
        self.assertFalse(a["src"])                      # fluxul camerei nu se mai cere
        self.assertEqual(a["cereri"], 1)
        self.assertEqual(a["buton"], "Arată imaginea")
        self.assertEqual(a["focus"], "senzor")          # nu pe buton: Spațiul sau Enter nu-l mai apasă o dată, din greșeală
        self.assertEqual(a["memorat"], "0")
        self.assertEqual(a["rol"], "region")
        self.assertEqual(a["live"], "off")              # reîmprospătarea nu se citește
        self.assertIn("măsoară, iar imaginea e ascunsă aici", a["cam"])
        self.assertEqual([x["nume"] for x in a["randuri"]], ["Camera", "Numărătorile", "Veghea", "Paznicul", "Prelucrarea de noapte"])
        self.verifica_stari("ascunsa", ["ok"] * 5)
        self.assertEqual(a["rezumat"], "Toate cele cinci verigi sunt în regulă.")
        self.assertRegex(a["antet"], r"^Citită la (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d; se reîmprospătează la 10\u00a0s\.$")
        self.assertFalse(a["vechi"])
        self.assertEqual(self.r["dupa_10s"], 1)         # încă o citire la 10 s, cât panoul se vede
        # numele panoului, citit de cititorul de ecran, vine cu antetul și cu rezumatul: de la prima deschidere, și înaintea primului răspuns
        self.assertEqual(a["descris"], "senzor-antet senzor-rezumat")
        self.assertEqual(a["descriere"], [a["antet"], a["rezumat"]])
        self.assertEqual(a["deschidere"], ["Se citește starea senzorului…", ""])

    def test_randurile_spun_cifrele_si_pragurile(self):
        t = self.randuri("ascunsa")
        self.assertEqual(self.fraza(t["camera"]), "Camera: în regulă. Conectată la fluxul camerei.")   # rata de acum e sub imagine; aici, doar când explică starea
        self.assertRegex(t["camera"]["prag"], r"^Ultimul semn de viață: (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d\. Starea se scrie în fiecare secundă; veche de 15\u00a0s, "
                                              r"e de urmărit, iar de 10\u00a0min, o problemă\. Tot de urmărit: fără fluxul camerei sau sub 3,5\u00a0cadre/s\.$")
        self.assertRegex(self.fraza(t["colectarea"]), r"^Numărătorile: în regulă\. Ultimul sfert de oră, \d\d:\d\d–\d\d:\d\d( din \d{1,2}\.\d\d)?, "
                                                      r"are 1\.234 de vehicule intrate și 266 de numărări de pietoni\.$")
        self.assertNotIn("urmărește", t["colectarea"]["text"])       # cei urmăriți acum, doar în rândul camerei, de sub panou
        self.assertIn("Un sfert de oră se încheie la fiecare 15\u00a0min; fără unul nou de 17\u00a0min, e de urmărit, iar de 1\u00a0h, o problemă.", t["colectarea"]["prag"])
        self.assertNotIn("cadre/s", self.fraza(t["veghea"]))     # la sau peste prag, rata nu se spune: cea de acum e chiar deasupra panoului (RT-1)
        self.assertIn("La ultimul rând: nicio pauză de peste 2,5\u00a0s între cadre în 5\u00a0min, niciun episod de reconectare în 30\u00a0min. "
                      "În ultima oră: 60 de rânduri și nicio pauză de cel puțin 10\u00a0s.", t["veghea"]["text"])
        self.assertIn("Scrie un rând pe minut; tăcută de 3\u00a0min, e de urmărit, iar de 10\u00a0min, o problemă. Tot de urmărit: sub 3,5\u00a0cadre/s, "
                      "de la 10 pauze de peste 2,5\u00a0s în 5\u00a0min sau de la 4 episoade de reconectare în 30\u00a0min. "
                      "După o alertă, veghea se oprește: e de urmărit, iar tăcută de 3\u00a0min, o problemă.", t["veghea"]["prag"])     # pragurile din răspuns
        self.assertIn("Ultima notă: totul în regulă, analiza camerei rulează.", t["paznicul"]["text"])
        self.assertIn("Notează „în regulă” în fiecare oră; fără notă de 1\u00a0h 2\u00a0min, e de urmărit, iar de 2\u00a0h, o problemă. "
                      "Altă notă, în afară de „repornirea ține”, e de urmărit până la următorul „în regulă”.", t["paznicul"]["prag"])
        (zv, pv), (zn, pn), cand = self.noapte()                      # zilele și orele, socotite din ora răspunsului, nu doar „azi sau mâine”
        self.assertIn(f"Măsura veche, pentru ziua de {zv}: rularea s-a încheiat la {pv}00:20. "
                      f"Măsura nouă, pentru ziua de {zn}: rularea s-a încheiat la {pn}03:39.", t["noaptea"]["text"])
        self.assertTrue(t["noaptea"]["prag"].endswith("Prelucrarea pentru măsura veche pornește la 00:15, cea pentru măsura nouă la 03:30; "
                                                      f"o rulare mai lungă de 2\u00a0h e de urmărit; următoarea rulare: {cand}."), t["noaptea"]["prag"])

    def test_linia_fisei(self):
        f = self.r["ascunsa"]["fisa"]
        self.assertTrue(f.startswith("Ultima fișă a senzorului acoperă 110,9\u00a0h, de la 1.11, 09:04, până la 6.11, 00:00; cadre în "), f)
        self.assertNotRegex(f, r"\d\d:\d\d: ")                        # fără două puncte după oră
        for bucata in ("cadre în 98,8% din minute", "o mediană de 5,98\u00a0cadre analizate pe secundă", "2 opriri anunțate și nicio cădere neprevăzută",
                       "prelucrări de noapte încheiate: 6 din 6.", "Fișa e publicată în documentație."):
            self.assertIn(bucata, f)
        self.assertIn("Fișa e calculată doar pe acest calculator, nepublicată.", self.r["stari_4"]["fisa"])
        self.assertEqual(self.r["fara_fisa"]["fisa"], "Nu există încă o fișă a senzorului.")
        self.assertEqual(len(self.r["fara_fisa"]["randuri"]), 5)
        # din 10.11, fișa are și căderile sursei: alături de căderile colectării, fiecare cu numele ei
        self.assertIn("2 opriri anunțate, o cădere neprevăzută a colectării și 2 căderi ale sursei camerei; prelucrări de noapte",
                      self.r["fisa_caderi"]["fisa"])
        self.assertIn("2 opriri anunțate, nicio cădere neprevăzută a colectării și nicio cădere a sursei camerei; ",
                      self.r["fisa_fara_caderi"]["fisa"])
        self.assertNotIn("sursei", f)                                  # fișa publicată la M2 nu le socotea

    def test_fiecare_stare_are_cuvantul_si_fraza_ei(self):
        self.verifica_stari("stari_1", ["atent", "problema", "ok", "atent", "necunoscut"])
        t = self.randuri("stari_1")
        self.assertIn("analizează 3,1\u00a0cadre pe secundă, sub pragul de 3,5.", t["camera"]["text"])
        self.assertRegex(self.fraza(t["colectarea"]), r"Ultimul sfert de oră, 06:45–07:00( din \d{1,2}\.\d\d)?, are un vehicul intrat și nu are nicio numărare de pietoni\.$")
        self.assertIn("Ultima notă nu e „în regulă”: „camera: starea are 40\u00a0s”.", t["paznicul"]["text"])   # nota, citată, cu numărul lipit de unitate
        self.assertIn("Prelucrarea de noapte: nu se știe. Nu se poate citi acum: calculul a dat o eroare neprevăzută.", t["noaptea"]["text"])
        self.assertNotIn("ValueError", t["noaptea"]["text"])         # felul erorii, pentru autor, doar în titlul rândului
        self.assertEqual(t["noaptea"]["titlu"], "ValueError")
        self.assertEqual(t["camera"]["titlu"], "")
        self.assertEqual(self.r["stari_1"]["rezumat"], "O problemă: Numărătorile. De urmărit: Camera, Paznicul. Nu se știe: Prelucrarea de noapte. În regulă: Veghea.")

        self.verifica_stari("stari_2", ["problema", "necunoscut", "problema", "problema", "problema"])
        t = self.randuri("stari_2")
        self.assertIn("Starea camerei lipsește: programul care analizează imaginea pare oprit.", t["camera"]["text"])
        self.assertIn("Ultimul semn de viață: niciunul.", t["camera"]["prag"])
        self.assertIn("Nu s-a găsit niciun sfert de oră numărat azi sau ieri.", t["colectarea"]["text"])
        self.assertRegex(self.fraza(t["veghea"]), r"La ultimul rând: 2,1\u00a0cadre/s, sub 3,5, 14 pauze de peste 2,5\u00a0s între cadre în 5\u00a0min, 5 episoade de reconectare în 30\u00a0min\. "
                                                  r"În ultima oră: 58 de rânduri și 3 pauze de cel puțin 10\u00a0s\. Veghea s-a oprit pe alerta de la (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d, "
                                                  r"cu semnele: „rata mică: 2,1\u00a0cadre/s \(mediana ultimelor 3\u00a0min\); pauze: 14 pauze de peste 2,5\u00a0s între cadre în ultimele 5\u00a0min”\.$")
        self.assertIn("Nicio notă nouă de 2\u00a0h 1\u00a0min. Ultima notă: totul era în regulă, analiza camerei rula.", t["paznicul"]["text"])   # o notă veche spune ce era atunci
        self.assertRegex(t["noaptea"]["text"], r"Măsura nouă, pentru ziua de \d{1,2}\.\d\d: rularea lipsește, deși trebuia să pornească la 03:30\.")
        self.assertEqual(self.r["stari_2"]["rezumat"], "4 probleme: Camera, Veghea, Paznicul, Prelucrarea de noapte. Nu se știe: Numărătorile.")

        self.verifica_stari("stari_3", ["necunoscut", "atent", "necunoscut", "necunoscut", "atent"])
        t = self.randuri("stari_3")
        self.assertIn("Starea camerei există, dar nu se poate citi.", t["camera"]["text"])
        self.assertIn("Nu s-a găsit niciun rând al vegherii.", t["veghea"]["text"])
        self.assertIn("Nu s-a găsit nicio notă a paznicului.", t["paznicul"]["text"])
        self.assertIn("Ultimul semn de viață: niciunul.", t["paznicul"]["prag"])
        self.assertRegex(t["noaptea"]["text"], r"Măsura veche, pentru ziua de \d{1,2}\.\d\d: rularea e în curs, de la (\d{1,2}\.\d\d, )?00:15\. "
                                               r"Măsura nouă, pentru ziua de \d{1,2}\.\d\d: rularea n-a pornit încă, deși ora ei, 03:30, a trecut\.")

        t = self.randuri("stari_4")
        self.assertEqual(t["noaptea"]["cuvant"], "problemă")
        self.assertIn("rularea s-a oprit cu eroare; au eșuat 2 pași din 6", t["noaptea"]["text"])
        self.assertIn("starea rulării nu se poate citi", t["noaptea"]["text"])
        self.assertIn("Valorile primite nu au forma așteptată.", t["veghea"]["text"])    # o alertă cu semnele altfel decât o listă
        self.assertEqual(t["veghea"]["cuvant"], "de urmărit")         # veghea, oprită pe alertă de mai puțin de 3 min
        self.assertEqual(self.r["din_nou_ok"]["rezumat"], "Toate cele cinci verigi sunt în regulă.")

    def test_vechimea_trecuta_de_prag_se_spune_in_cuvinte(self):
        """O verigă veche spune de cât timp tace, nu doar ora ultimului semn: altfel „problemă” lângă o notă „în regulă” s-ar contrazice."""
        fraza = self.fraza                                            # fără rândul pragurilor („fără unul nou de 17 min”)
        t = self.randuri("stari_1")
        self.assertIn("Niciun sfert de oră nou de 2\u00a0h 1\u00a0min. Ultimul sfert de oră, 06:45–07:00", t["colectarea"]["text"])
        self.assertNotIn("nou", fraza(t["paznicul"]))                 # de urmărit doar după notă, nu după vechime
        t = self.randuri("stari_2")
        self.assertIn("Niciun rând nou de 11\u00a0min 40\u00a0s. La ultimul rând: 2,1\u00a0cadre/s", t["veghea"]["text"])
        self.assertIn("Nicio notă nouă de 2\u00a0h 1\u00a0min. Ultima notă: totul era în regulă, analiza camerei rula.", t["paznicul"]["text"])
        self.assertIn("Niciun sfert de oră nou de 25\u00a0min. Ultimul sfert de oră", self.randuri("stari_3")["colectarea"]["text"])
        for cheie, x in self.randuri("ascunsa").items():              # proaspete: fără nicio vechime
            self.assertNotIn(" nou de ", fraza(x), cheie)
            self.assertNotIn(" nouă de ", fraza(x), cheie)
        self.assertEqual(self.r["tacere"], ["", "Nimic nou de 17\u00a0min. ", "", "Nimic nou de 3\u00a0min. ", "", "Nimic nou de 1\u00a0h 2\u00a0min. ", ""])
        v = fraza(self.randuri("semn_taiat")["veghea"])
        self.assertRegex(v, r"Ultima alertă, la (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d, cu semnele: „rata mică: jurnal …”\.$")   # semnul tăiat, citat: fără încă un punct lipit de „…”
        self.assertNotIn("….", v)

    def test_un_singur_anunt_cand_o_veriga_trece_in_problema(self):
        self.assertEqual(self.r["stari_1"]["anunt"], "Starea senzorului, problemă nouă: Numărătorile.")
        self.assertEqual(self.r["stari_2"]["anunt"], "Starea senzorului, probleme noi: Camera, Veghea, Paznicul, Prelucrarea de noapte.")
        self.assertEqual(self.r["stari_3"]["anunt"], "")              # nicio problemă
        self.assertEqual(self.r["stari_4"]["anunt"], "Starea senzorului, problemă nouă: Prelucrarea de noapte.")
        self.assertEqual(self.r["stari_4_din_nou"]["anunt"], "")      # aceeași problemă, citită din nou: niciun anunț
        self.assertEqual(self.r["din_nou_ok"]["anunt"], "")
        self.assertEqual(self.r["ascunsa"]["randuri"][0]["stare"], "ok")

    def test_valorile_vechi_se_arata_ca_vechi(self):
        v = self.r["veche_30s"]
        self.assertTrue(v["vechi"])
        self.assertRegex(v["antet"], r"^Se citește din nou; mai jos, starea citită la (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d\.$")
        e = self.r["eroare_retea"]
        self.assertTrue(e["vechi"])
        self.assertEqual(e["eticheta"], '"date vechi"')
        self.assertEqual(len(e["randuri"]), 5)                        # valorile de până atunci rămân
        self.assertRegex(e["antet"], r"^Starea senzorului nu se mai poate citi de la (\d\d:\d\d:\d\d), fiindcă cererea nu a ajuns la server\. Mai jos, cea citită la (\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d\.$")
        self.assertEqual(e["rezumat"], "Toate cele cinci verigi erau în regulă.")
        c = self.r["eroare_500"]
        self.assertTrue(c["vechi"])
        self.assertIn(", fiindcă serverul răspunde cu eroarea 500.", c["antet"])
        de_la = re.search(r"de la (\d\d:\d\d:\d\d)", e["antet"]).group(1)
        self.assertIn(f"de la {de_la},", c["antet"])                  # de la prima eroare, nu de la ultima
        self.assertIn("răspunsul serverului nu are forma așteptată", self.r["forma"]["antet"])
        self.assertTrue(self.r["forma"]["vechi"])
        self.assertIn(", fiindcă răspunsul serverului nu are forma așteptată.", self.r["json_stricat"]["antet"])   # nu „cererea nu a ajuns la server”
        self.assertTrue(self.r["json_stricat"]["vechi"])
        r = self.r["revenit"]
        self.assertFalse(r["vechi"])
        self.assertEqual(r["eticheta"], "none")
        self.assertTrue(r["antet"].startswith("Citită la "))

    def test_fara_nicio_valoare_spune_ca_nu_se_poate_citi(self):
        f = self.r["fara_valori"]
        self.assertTrue(f["vizibil"])
        self.assertEqual(f["randuri"], [])
        self.assertEqual(f["antet"], "Starea senzorului nu se poate citi: serverul răspunde cu eroarea 500. Încercăm din nou la 10\u00a0s.")
        self.assertEqual(f["rezumat"], "")
        self.assertEqual(f["fisa"], "")

    def test_fara_legatura_ca_alerta_de_sus(self):
        f = self.r["fara_legatura"]
        self.assertTrue(f["vechi"])
        self.assertTrue(f["antet"].startswith(f"Nu e legătură cu calculatorul dispeceratului de la {f['cazut']}; mai jos, starea citită la "), f["antet"])
        self.assertIn(f"Nu mai e legătură cu calculatorul dispeceratului, de la {f['cazut']}.", f["alerta"])
        self.assertEqual(f["rezumat"], "Toate cele cinci verigi erau în regulă.")
        r = self.r["legatura_revenita"]
        self.assertFalse(r["vechi"])
        self.assertEqual(r["cereri_noi"], 1)                          # la revenire, starea senzorului se citește pe loc
        self.assertTrue(r["antet"].startswith("Citită la "))

    def test_raspunsul_vechi_sosit_tarziu_se_ignora(self):
        t = self.r["tarziu"]
        self.assertEqual(self.randuri("tarziu")["veghea"]["stare"], "ok")
        self.assertEqual(t["anunt"], "")
        self.assertEqual(self.r["aratata"]["camera"], "ok")          # nici cel sosit după ascunderea panoului
        self.assertEqual(self.r["aratata"]["anunt"], "")

    def test_imaginea_aratata_din_nou_opreste_citirile(self):
        a = self.r["aratata"]
        self.assertFalse(a["vizibil"])
        self.assertEqual(a["buton"], "Ascunde imaginea")
        self.assertEqual(a["focus"], "t-cam")
        self.assertEqual(a["memorat"], "1")
        self.assertTrue(a["src"])
        self.assertTrue(a["imagine"])
        self.assertEqual(self.r["dupa_aratare"], 0)

    def test_pornirea_din_adresa_sau_din_alegerea_tinuta_minte(self):
        self.assertEqual(self.r["la_pornire"], [True, False, True, False, False, False, True, True, False])

    def test_banda_de_sus_ramane_pe_ecran(self):
        b = self.r["banda"]
        self.assertGreaterEqual(b["latime"], 1200)                   # fereastra de 1366 px, fără bara de derulare: coloana din stânga e lipită
        self.assertEqual(b["parinte"], "BODY")
        self.assertTrue(b["dupa_alerte"])
        self.assertEqual(b["urmatorul"], "MAIN")
        self.assertEqual(b["are"], [True, True, True])
        self.assertEqual(b["pozitie"], "sticky")
        self.assertEqual(b["sus"], "0px")
        self.assertGreater(int(b["z"]), 0)
        self.assertEqual(b["fundal"], b["fundal_pagina"])
        self.assertEqual(b["rol"], "status")
        self.assertIn("Planul observat", b["revino"])
        self.assertIn("Plan de referință", b["rezultat"])
        self.assertEqual(b["col_pozitie"], "sticky")
        self.assertEqual(b["col_sus"], f"{b['inaltime'] + 8}px")       # coloana din stânga se lipește sub bandă
        self.assertEqual(b["derulat"], 300)
        self.assertEqual(b["sus_derulat"], 0)
        self.assertTrue(b["rezultat_in_ecran"] and b["revino_in_ecran"] and b["cine_in_ecran"])
        self.assertGreaterEqual(b["col_sus_derulat"], b["banda_jos"] - 0.5)

    def test_agentul_ia_spune_pe_ce_a_fost_antrenat(self):
        a = self.r["agent"]
        for text in (a["d_ai"], a["moduri"], a["confirmare"]):
            self.assertIn("antrenat pe simularea veche, neverificat pe cea corectată", text)

    def test_ajutorul_spune_de_starea_senzorului(self):
        self.assertIn("Starea senzorului:", self.r["ajutor"])
        self.assertIn("„Ascunde imaginea”", self.r["ajutor"])
        self.assertNotIn("sub butoane", self.r["ajutor"])
        for bucata in ("apar camera, numărătorile, veghea, paznicul și prelucrarea de noapte",       # ce sunt veghea și paznicul, ca în § 4.6
                       "Veghea urmărește în fiecare secundă starea prelucrării și se oprește cu o alertă la primul semn de problemă",
                       "paznicul verifică o dată pe minut dacă analiza camerei rulează și o repornește singur dacă s-a oprit"):
            self.assertIn(bucata, self.r["ajutor"])

    def test_alerta_vegherii_spune_daca_veghea_s_a_oprit_pe_ea(self):
        a = {k: self.fraza(x) for k, x in self.r["alerte"].items()}
        ora = r"(\d{1,2}\.\d\d, )?\d\d:\d\d:\d\d"
        self.assertRegex(a["oprita"], rf"\. Veghea s-a oprit pe alerta de la {ora}, cu semnele: „rata mică: 3,2\u00a0cadre/s \(mediana ultimelor 3\u00a0min\)”\.$")   # zecimala cu virgulă, numărul lipit de unitate
        self.assertRegex(a["trecuta"], rf"\. Ultima alertă, la {ora}, a trecut: veghea a pornit din nou după ea; semnele ei: „proces: run_vision nu mai rulează”\.$")
        self.assertRegex(a["fara_semne"], rf"\. Veghea s-a oprit pe alerta de la {ora}; semnele ei nu se pot citi încă\.$")
        self.assertRegex(a["semne_null"], rf"\. Ultima alertă, la {ora}, a trecut: veghea a pornit din nou după ea; semnele ei nu se pot citi încă\.$")
        self.assertRegex(a["fara_rand"], rf"^Veghea: în regulă\. Nu s-a găsit niciun rând al vegherii\. Veghea s-a oprit pe alerta de la {ora}, "
                                         r"cu semnele: „proces: run_vision nu mai rulează”\.$")   # alerta, spusă și fără niciun rând

    def test_cadrele_pe_secunda_spuse_in_cuvinte(self):
        c = self.r["cadre"]                                           # 3,47; 0; 0,5; 1,02 și 3,5 cadre pe secundă
        self.assertIn("Conectată la fluxul camerei, analizează 3,4\u00a0cadre pe secundă, sub pragul de 3,5.", c[0]["camera"])   # sub prag, rotunjit în jos
        self.assertIn("La ultimul rând: 3,4\u00a0cadre/s, sub 3,5, nicio pauză", c[0]["veghea"])
        self.assertIn("Conectată la fluxul camerei, nu analizează niciun cadru.", c[1]["camera"])
        self.assertIn("La ultimul rând: niciun cadru pe secundă, nicio pauză", c[1]["veghea"])
        self.assertIn("Conectată la fluxul camerei, analizează sub un cadru pe secundă.", c[2]["camera"])
        self.assertIn("La ultimul rând: sub un cadru pe secundă, nicio pauză", c[2]["veghea"])
        self.assertIn("Conectată la fluxul camerei, analizează un cadru pe secundă, sub pragul de 3,5.", c[3]["camera"])
        self.assertIn("La ultimul rând: un cadru pe secundă, sub 3,5, nicio pauză", c[3]["veghea"])
        self.assertIn("Conectată la fluxul camerei.", c[4]["camera"])            # la prag, nu sub el: rata nu explică nimic, deci nu se spune
        self.assertNotIn("cadre pe secundă", c[4]["camera"])
        self.assertIn("La ultimul rând: nicio pauză", c[4]["veghea"])           # și în rândul vegherii
        for x in c:
            for gresit in ("0 cadre pe secundă", " 1 cadre", "0\u00a0cadre/s", "1\u00a0cadre/s", "0\u00a0cadre pe secundă", " 1\u00a0cadre"):
                self.assertNotIn(gresit, x["camera"] + x["veghea"])

    def test_un_csv_vechi_al_vegherii_nu_spune_pauze_necunoscute(self):
        self.assertIn("La ultimul rând: cel puțin 3,5\u00a0cadre/s. În ultima oră: 60 de rânduri.", self.fraza(self.r["csv_foarte_vechi"]))   # nici pauze, nici reconectări
        f = self.fraza(self.r["csv_vechi"])
        self.assertIn("La ultimul rând: niciun episod de reconectare în 30\u00a0min. În ultima oră: 60 de rânduri.", f)
        self.assertNotIn("pauz", f)
        self.assertNotIn("—", f)

    def test_eroarea_calculului_ramane_in_titlul_randului(self):
        e = self.r["eroare"]
        self.assertEqual(e["cuvant"], "nu se știe")
        self.assertTrue(self.fraza(e).endswith(": nu se știe. Nu se poate citi acum: calculul a dat o eroare neprevăzută."), e["text"])
        self.assertTrue(e["prag"].startswith("Ultimul semn de viață: nu se știe. "), e["prag"])
        self.assertEqual(e["titlu"], "KeyError")
        self.assertNotIn("KeyError", e["text"])
        self.assertIn("Ultimul semn de viață: niciunul.", self.randuri("stari_3")["paznicul"]["prag"])   # fără eroare și fără semn: „niciunul”

    def test_notele_paznicului_in_cuvinte(self):
        n = {k: self.fraza(x) for k, x in self.r["note"].items()}
        self.assertTrue(n["repornire"].endswith(": în regulă. Ultima notă: repornirea a ținut, analiza camerei rulează."), n["repornire"])
        self.assertTrue(n["repornire_veche"].endswith(": de urmărit. Nicio notă nouă de 1\u00a0h 6\u00a0min. Ultima notă: repornirea a ținut, analiza camerei rula."),
                        n["repornire_veche"])
        self.assertTrue(n["alta"].endswith(f"Ultima notă nu e „în regulă”: „jurnalul zilei crește: prima traiectorie nouă la {self.r['ieri']}, 11:28:43”."), n["alta"])
        self.assertNotRegex(n["alta"], r"\d{4}-\d\d-\d\dT")             # ora din notă, scrisă ca în restul panoului

    def test_rularile_de_noapte_care_asteapta_sau_au_o_atentionare(self):
        n = {k: self.fraza(x) for k, x in self.r["noapte"].items()}
        (zv, pv), (zn, pn), _ = self.noapte("la_noapte")
        self.assertIn(f"Măsura veche, pentru ziua de {zv}: rularea a pornit la {pv}00:15 și așteaptă imaginea camerei, cel mult 30\u00a0min. ", n["fluxul"])
        self.assertTrue(n["lant"].endswith(f"Măsura nouă, pentru ziua de {zn}: rularea așteaptă să se încheie prelucrarea pentru măsura veche."), n["lant"])
        self.assertTrue(n["pornire"].endswith(f"Măsura nouă, pentru ziua de {zn}: rularea pornește în curând, fiindcă prelucrarea pentru măsura veche "
                                              "s-a terminat."), n["pornire"])     # lanțul vechi încheiat după 03:30: nu „așteaptă” un lanț încheiat (RT-2)
        self.assertIn(f"rularea s-a încheiat la {pv}00:20, cu o atenționare: „jurnalul are membri stricați”. ", n["atentie"])
        self.assertIn(f"rularea s-a încheiat la {pv}00:20; un pas a avut o atenționare. ", n["atentie_generala"])   # textul general, necitat
        self.assertIn(f"rulează din {pv}00:15, de peste 2\u00a0h. ", n["lunga"])
        self.assertIn(f"Măsura veche, pentru ziua de {zv}: rularea s-a încheiat, dar a eșuat un pas din 6. ", n["esecuri"])   # „cu_esecuri”: a mers până la capăt

    def test_duratele_rotunjite_in_jos(self):
        nb = "\u00a0"
        self.assertEqual(self.r["durate"], [f"75{nb}s", f"89{nb}s", f"1{nb}min 30{nb}s", f"2{nb}min", f"59{nb}min 59{nb}s", f"1{nb}h", f"1{nb}h",
                                            f"1{nb}h", f"1{nb}h 59{nb}min", f"1{nb}h 59{nb}min", f"2{nb}h", f"2{nb}h 2{nb}min"])   # niciodată „1 h 60 min” sau „1 h 0 min”
        self.assertEqual(self.r["praguri"], [f"15{nb}s", f"10{nb}min", f"15{nb}min", f"17{nb}min", f"1{nb}h", f"1{nb}h 2{nb}min", f"2{nb}h"])

    def test_randul_camerei_spune_participantii_urmariti(self):
        self.assertEqual(self.r["urmariti"], ["53 de participanți urmăriți", "19 participanți urmăriți", "un participant urmărit", "niciun participant urmărit"])

    def test_nume_din_prototip_si_date_imposibile(self):
        p = self.r["prototip"]
        self.assertIsNone(p["aruncat"])
        r = p["randuri"]
        self.assertEqual([x["nume"] for x in r], ["Camera", "Numărătorile", "Veghea", "Paznicul", "Prelucrarea de noapte", "—", "constructor"])
        self.assertEqual([x["cuvant"] for x in r], ["nu se știe", "în regulă", "în regulă", "nu se știe", "în regulă", "problemă", "nu se știe"])
        self.assertIn(": rularea e în curs, de la —. ", r[4]["text"])   # o oră imposibilă: o liniuță
        self.assertIn("constructor, pentru ziua de ", r[4]["text"])
        self.assertIn("starea „toString”", r[4]["text"])
        self.assertIn("de la —, până la 6.11, 00:00", p["fisa"])
        self.assertEqual(p["rezumat"], "O problemă: —. Nu se știe: Camera, Paznicul, constructor. În regulă: Numărătorile, Veghea, Prelucrarea de noapte.")
        self.assertNotRegex(p["tot"], r"undefined|NaN|null|\[object|native code|Invalid Date|function")

    def test_constantele_paginii_ca_ale_colectarii(self):
        """PAUZA_S și ASTEPTARE_FLUX_MIN din pagină copiază veghe.PAUZA și lant_zilnic.ASTEPTARE_FLUX_S: citite ca text, fără import."""
        pagina = C.VERSIUNI["curent"].read_text(encoding="utf-8")
        m = re.search(r"const PAUZA_S=([\d.]+), ASTEPTARE_FLUX_MIN=(\d+);", pagina)
        src = Path(C.__file__).resolve().parents[1]
        pauza = re.search(r"^PAUZA = ([\d.]+)", (src / "vision" / "veghe.py").read_text(encoding="utf-8"), re.M)
        flux = re.search(r"^ASTEPTARE_FLUX_S = ([\d.]+)", (src / "lant_zilnic.py").read_text(encoding="utf-8"), re.M)
        self.assertEqual(float(m[1]), float(pauza[1]))
        self.assertEqual(float(m[2]) * 60, float(flux[1]))

    # runda a doua a reparațiilor (B1–B7)
    def test_in_panou_numarul_nu_se_desparte_de_unitate(self):
        simplu = r"\d (s|min|h|cadre)\b"
        for k in ("ascunsa", "stari_1", "stari_2", "stari_3", "stari_4"):
            for x in self.r[k]["randuri"]:
                self.assertNotRegex(re.sub(r"„[^”]*”", "", x["text"]), simplu, (k, x["cheie"]))   # fără citatele din jurnale, scrise de programe
            self.assertNotRegex(self.r[k]["fisa"], simplu, k)
        self.assertIn("o mediană de 5,98\u00a0cadre analizate pe secundă", self.r["ascunsa"]["fisa"])

    def test_dupa_ora_fara_doua_puncte_si_niciun_cu_nu(self):
        """Sfertul de oră, în cele patru forme: după oră urmează o virgulă, nu două puncte, iar „niciun” vine cu „nu” pe verb; antetul cu
        valorile vechi spune motivul după „fiindcă”."""
        cap = "Numărătorile: în regulă. Ultimul sfert de oră, 12:15–12:30, "
        self.assertEqual([self.fraza(x) for x in self.r["colectare"]], [cap + "are 1.046 de vehicule intrate și 714 numărări de pietoni.",
                                                                       cap + "nu are niciun vehicul intrat și nicio numărare de pietoni.",
                                                                       cap + "nu are niciun vehicul intrat, dar are 5 numărări de pietoni.",
                                                                       cap + "are un vehicul intrat și nu are nicio numărare de pietoni."])
        for k in ("eroare_retea", "eroare_500", "forma", "json_stricat"):
            self.assertRegex(self.r[k]["antet"], r"^Starea senzorului nu se mai poate citi de la \d\d:\d\d:\d\d, fiindcă (serverul răspunde cu eroarea 500|"
                                                 r"răspunsul serverului nu are forma așteptată|cererea nu a ajuns la server)\. Mai jos, cea citită la ", k)
        for k in ("ascunsa", "stari_1", "stari_2", "stari_3", "stari_4"):
            for x in self.r[k]["randuri"]:
                self.assertNotRegex(self.fraza(x), r"\d\d:\d\d: ", (k, x["cheie"]))

    def test_randul_camerei_spune_rata_doar_cand_explica_starea(self):
        """Rata cadrelor, doar sub prag sau la reconectare; în rest, rata de acum se vede sub imagine."""
        self.assertEqual([self.fraza(x) for x in self.r["camera_rata"]], [
            "Camera: în regulă. Conectată la fluxul camerei.",
            "Camera: de urmărit. Se reconectează la fluxul camerei, analizează 5,9\u00a0cadre pe secundă.",
            "Camera: de urmărit. Se reconectează la fluxul camerei, nu analizează niciun cadru.",
            "Camera: de urmărit. Se reconectează la fluxul camerei.",
            "Camera: de urmărit. Conectată la fluxul camerei, analizează 3,1\u00a0cadre pe secundă, sub pragul de 3,5."])

    def test_fara_campul_legaturii_nu_spune_conectata(self):
        """Fără câmpul `conectat` (sau cu altă valoare decât adevărat ori fals), rândul nu spune nici „conectată”, nici „se reconectează”."""
        f = [self.fraza(x) for x in self.r["camera_nule"]]
        self.assertEqual(f, ["Camera: în regulă. Starea camerei e la zi.",
                             "Camera: de urmărit. Analizează 3,1\u00a0cadre pe secundă, sub pragul de 3,5.",
                             "Camera: de urmărit. Nu analizează niciun cadru.",
                             "Camera: în regulă. Starea camerei e la zi."])
        for x in f:
            self.assertNotIn("onecta", x)

    def test_fara_dosarele_noptii_nu_spune_ca_rularile_lipsesc(self):
        x = self.r["fara_dosare"]
        self.assertEqual(self.fraza(x), "Prelucrarea de noapte: nu se știe. Pe acest calculator nu s-a găsit nicio prelucrare de noapte.")
        self.assertEqual(x["cuvant"], "nu se știe")
        self.assertNotIn("lipsește", x["text"])
        self.assertTrue(x["prag"].endswith("Unde rulează, prelucrarea pentru măsura veche pornește la 00:15, cea pentru măsura nouă la 03:30; "
                                           "o rulare mai lungă de 2\u00a0h e de urmărit."), x["prag"])   # pragul, cu orele, rămâne
        self.assertNotIn("următoarea rulare", x["prag"])                      # aici nu rulează nimic (RT-3)

    def test_masura_noua_asteapta_prelucrarea_pentru_masura_veche(self):
        n = self.fraza(self.r["noapte"]["lant"])
        self.assertIn("rularea așteaptă să se încheie prelucrarea pentru măsura veche.", n)
        self.assertNotIn("să se încheie măsura veche", n)

    def test_durata_rotunjita_in_jos_si_cu_zecimale(self):
        nb = "\u00a0"
        self.assertEqual(self.r["durate_jos"], [f"0{nb}s", f"59{nb}s", f"89{nb}s", f"1{nb}h", f"1{nb}h 59{nb}min", f"0{nb}s"])


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestPornire(unittest.TestCase):
    """Pagina deschisă de cinci ori, cu același profil: ?imagine=0 pornește fără imagine și fără să ceară fluxul camerei,
    ?imagine=1 cu imagine; fără parametru, ultima alegere făcută cu butonul, ținută minte în browser. Parametrul nu se ține minte.
    A cincea, starea „senzor” din capturi, ascunde imaginea fără să schimbe alegerea ținută minte."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass

        def deschide(cautare="", dupa=""):
            p = C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), PORNIRE.replace("%DUPA%", dupa))
            p = p.replace("<script>\nconst NUME=", "<script>" + SURSE + "</script>\n<script>\nconst NUME=", 1)   # după simulări, înaintea paginii
            return ruleaza_pagina(cls.d, p, cautare, buget_ms=10000)

        cls.cu_0 = deschide("?imagine=0")
        cls.fara_1 = deschide(dupa='$("b-imagine").click(); await asteapta(50); rez.dupa=stare();')
        cls.fara_2 = deschide()
        cls.cu_1 = deschide("?imagine=1")
        cls.captura = deschide("?imagine=1", C.STARI["senzor"] + " await asteapta(50); rez.dupa=stare(); rez.focus=document.activeElement.id;")   # starea „senzor” din capturi

    def test_cu_imagine_0_porneste_fara_flux(self):
        p = self.cu_0["pornire"]
        self.assertEqual(p["cautare"], "?imagine=0")
        self.assertTrue(p["ascunsa"])
        self.assertTrue(p["panou"])
        self.assertFalse(p["imagine"])
        self.assertFalse(p["src"])
        self.assertEqual(p["surse"], 0)                  # fluxul camerei nu s-a cerut nicio clipă
        self.assertGreaterEqual(p["cereri"], 1)
        self.assertEqual(p["randuri"], 5)
        self.assertEqual(p["buton"], "Arată imaginea")
        self.assertIsNone(p["memorat"])                  # parametrul din adresă nu se ține minte

    def test_alegerea_cu_butonul_se_tine_minte(self):
        p = self.fara_1["pornire"]
        self.assertFalse(p["ascunsa"])
        self.assertTrue(p["src"])
        self.assertEqual(p["cereri"], 0)
        self.assertIsNone(p["memorat"])
        self.assertEqual(self.fara_1["dupa"]["memorat"], "0")
        self.assertTrue(self.fara_1["dupa"]["panou"])
        p = self.fara_2["pornire"]                       # deschisă din nou, fără parametru: tot fără imagine
        self.assertTrue(p["ascunsa"])
        self.assertTrue(p["panou"])
        self.assertEqual(p["surse"], 0)
        self.assertEqual(p["buton"], "Arată imaginea")

    def test_cu_imagine_1_porneste_cu_imaginea_si_nu_schimba_alegerea(self):
        p = self.cu_1["pornire"]
        self.assertFalse(p["ascunsa"])
        self.assertFalse(p["panou"])
        self.assertTrue(p["src"])
        self.assertEqual(p["cereri"], 0)
        self.assertEqual(p["buton"], "Ascunde imaginea")
        self.assertEqual(p["memorat"], "0")

    def test_starea_senzor_din_capturi(self):
        d = self.captura["dupa"]
        self.assertTrue(d["ascunsa"])
        self.assertTrue(d["panou"])
        self.assertFalse(d["src"])
        self.assertEqual(d["randuri"], 5)
        self.assertNotEqual(self.captura["focus"], "senzor")    # fără chenarul focusului în captură
        self.assertIsNone(d["memorat"])                         # capturile de după ea, din același profil, pornesc cu imaginea


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestAsezare(unittest.TestCase):
    """Pe ecranul unui laptop, 1366×641: panoul senzorului încape sub bandă, lista se rescrie rând cu rând, coloana din stânga se
    derulează cu pagina când e mai înaltă decât locul de sub bandă, banda nu sare în timpul unei comenzi urmărite, iar „Reveniți la …”
    apare după o reîncărcare doar pentru comenzile date de când rulează simularea de acum."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        cls.r = ruleaza_pagina(cls.d, C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), ASEZARE), buget_ms=60000, ecran=(1366, 641))

    def test_ecranul_unui_laptop(self):
        self.assertEqual(self.r["ecran"], [1366, 641])

    def test_panoul_incape_sub_banda(self):
        p = self.r["panou"]
        self.assertTrue(p["vizibil"])
        self.assertEqual(p["randuri"], 5)
        self.assertIn("Toate cele cinci verigi sunt în regulă", p["rezumat"])
        self.assertEqual(p["rezultat"], "")                          # nicio comandă încă: banda are un singur rând
        self.assertLess(p["banda"], 2 * p["rand"])
        self.assertLessEqual(p["h"], p["vh"] - p["banda"] - 8)        # de la titlu la linia fișei, tot panoul, sub bandă
        self.assertAlmostEqual(p["sus"], p["banda"] + 8, delta=1)     # derulat chiar sub bandă...
        self.assertGreaterEqual(p["sus"], p["banda_jos"])
        self.assertLessEqual(p["fisa_jos"], p["vh"])                  # ...se vede până la linia fișei
        self.assertLessEqual(p["jos"], p["vh"])

    def test_lista_se_rescrie_rand_cu_rand(self):
        x = self.r["rand_cu_rand"]
        self.assertEqual(x["chei"], TestSenzor.CHEI)
        self.assertEqual(x["aceleasi"], [True] * 5)                   # aceleași elemente, încă în pagină
        self.assertEqual(x["legate"], [True] * 5)
        self.assertEqual(x["schimbate"], [True, False, False, False, False])   # s-a rescris doar rândul camerei
        self.assertEqual(x["refacuta"], {"randuri": 6, "aceleasi": 0})          # altă listă de verigi: rândurile se fac din nou

    def test_in_comanda_manuala_coloana_se_deruleaza_cu_pagina(self):
        c = self.r["coloana"]
        self.assertGreater(c["butoane"], 0)
        self.assertGreater(c["h"], c["loc"])                          # mai înaltă decât locul de sub bandă...
        self.assertTrue(c["lunga"])
        self.assertEqual(c["pozitie"], "static")                      # ...deci nu se lipește sub ea
        self.assertGreater(c["jos0"], c["vh"])                        # cu pagina sus, butoanele fazelor sunt mai jos de ecran
        self.assertEqual(c["derulat"], c["y"])
        self.assertAlmostEqual(c["mutata"], c["y"], delta=1)          # la derulare, coloana urcă odată cu pagina
        self.assertGreaterEqual(c["faze_sus"], c["banda_jos"])        # și butoanele ajung pe ecran, sub bandă
        self.assertLessEqual(c["faze_jos"], c["vh"])

    def test_banda_nu_sare_in_timpul_comenzii_urmarite(self):
        pasi = {et: (h, sus, text) for et, h, sus, text in self.r["pasi"]}
        inainte = pasi.pop("inainte")
        self.assertIn("Se trimite: Verde pe Bd. Dacia", pasi["se_trimite"][2])
        self.assertIn("Cerere primită", pasi["primita"][2])
        for et in ("citit", "decizie", "degajare", "galben", "rosu"):
            self.assertIn("Se schimbă spre: Verde pe Bd. Dacia", pasi[et][2], et)
        self.assertIn("Aplicat", pasi["aplicat"][2])
        self.assertEqual(len({h for h, _, _ in pasi.values()}), 1, pasi)          # aceeași înălțime la fiecare pas...
        self.assertEqual(len({sus for _, sus, _ in pasi.values()}), 1, pasi)      # ...deci pagina de sub bandă nu se mută
        self.assertGreater(pasi["se_trimite"][0], inainte[0])                     # banda a crescut o dată, la clic
        self.assertGreater(pasi["se_trimite"][1], inainte[1])

    def test_revino_dupa_reincarcare_doar_pentru_comenzile_simularii_de_acum(self):
        v = self.r["revino"]
        for k in v:
            self.assertEqual(v[k]["istoric"], 2, k)                   # „Ultimele comenzi” le arată pe toate
        self.assertIsNone(v["ieri"]["revino"])                        # o comandă de ieri nu mai e „modul de dinainte”
        self.assertEqual(v["acum_60s"]["revino"], "Reveniți la „Comandă manuală”")
        self.assertIsNone(v["inaintea_simularii"]["revino"])          # dată înainte de pornirea simulării de acum
        self.assertIsNone(v["fara_timp_ieri"]["revino"])              # fără timp_sim: doar din ultima jumătate de oră
        self.assertEqual(v["fara_timp_10min"]["revino"], "Reveniți la „Comandă manuală”")


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestIngust(unittest.TestCase):
    """Pe un ecran îngust, 700×900: banda rămâne sus, strânsă, fără loc gol înaintea primei comenzi; după o comandă dată de la
    butoanele de mai jos, rezultatul și „Reveniți la …” se văd fără derulare, iar ajutorul spune la fel."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        cls.r = ruleaza_pagina(cls.d, C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), INGUST), ecran=(700, 900))

    def test_banda_ramane_sus_si_stransa(self):
        i = self.r["inainte"]
        self.assertEqual(i["ecran"], [700, 900])
        self.assertEqual(i["pozitie"], "sticky")
        self.assertEqual(i["cine"], "none")                           # cine conduce se vede pe butonul apăsat și sub fază
        self.assertEqual(i["inaltime"], 0)                            # nicio comandă și nimic de revenit: banda nu ocupă loc

    def test_dupa_o_comanda_de_jos_rezultatul_se_vede(self):
        t = self.r["trimisa"]
        self.assertGreater(t["y0"], 0)                                # comanda, dată cu pagina derulată
        self.assertIn("Plan de referință", t["rezultat"])
        self.assertTrue(t["in_ecran"])
        self.assertTrue(t["buton_in_ecran"])                          # pagina nu sare sus ca să arate rezultatul
        self.assertEqual(t["pozitie"], "sticky")
        self.assertEqual(t["banda_sus"], 0)
        a = self.r["aplicata"]
        self.assertIn("Aplicat", a["rezultat"])
        self.assertTrue(a["in_ecran"])
        self.assertEqual(a["revino"], "Reveniți la „Planul observat”")
        self.assertTrue(a["revino_in_ecran"])
        self.assertEqual(a["banda_sus"], 0)
        self.assertTrue(a["buton_in_ecran"])
        self.assertTrue(a["buton_sub_banda"])                         # banda, crescută, nu acoperă butonul

    def test_ajutorul_spune_ce_face_banda(self):
        self.assertIn("în banda de sus, care rămâne pe ecran și când derulați pagina, scrie dacă s-a aplicat", self.r["ajutor"])


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestEcranInalt(unittest.TestCase):
    """Pe un ecran mai înalt, 1536×1030: coloana comenzii manuale încape sub bandă și stă lipită sub ea; cu lista fazelor cu risc
    deschisă, nu mai încape și se derulează cu pagina; închisă, se lipește din nou."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        cls.r = ruleaza_pagina(cls.d, C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), INALT), ecran=(1536, 1030))

    def test_lista_fazelor_cu_risc_deschisa_desprinde_coloana(self):
        self.assertEqual(self.r["ecran"], [1536, 1030])
        a, b = self.r["inchisa"], self.r["deschisa"]
        self.assertLessEqual(a["h"], a["loc"])
        self.assertFalse(a["lunga"])
        self.assertEqual(a["pozitie"], "sticky")
        self.assertGreater(b["h"], b["loc"])
        self.assertTrue(b["lunga"])
        self.assertEqual(b["pozitie"], "static")
        self.assertEqual(self.r["inchisa_iar"], a)


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestLaptopMic(unittest.TestCase):
    """Pe ecranele de laptop, 1280×720, 1366×641 și 1536×730 (în ramă): în ciclul obișnuit al semaforului (verde, degajarea pietonilor, galben,
    roșu), în planul observat și în comanda manuală, coloana din stânga rămâne în aceeași așezare la fiecare pas; la 1280×720, în degajare,
    rândurile de sub fază o fac prea înaltă, deci se derulează cu pagina tot timpul, nu doar în degajare. Panoul senzorului încape sub bandă,
    iar textul rar din bandă are cel mult două rânduri."""

    ECRANE = ((1280, 720), (1366, 641), (1536, 730))

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        pagina = C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), CICLU)
        cls.r = {}
        for w, h in cls.ECRANE:                              # câte un profil pentru fiecare ecran: alegerea imaginii nu trece de la unul la altul
            (cls.d / str(w)).mkdir()
            cls.r[(w, h)] = ruleaza_pagina(cls.d / str(w), pagina, ecran=(w, h))

    def test_coloana_nu_sare_in_ciclul_semaforului(self):
        for ecran, r in self.r.items():
            self.assertEqual(r["ecran"], list(ecran))
            for mod in ("program", "manual", "program_iar"):
                with self.subTest(ecran=ecran, mod=mod):
                    self.assertEqual(len({(x["lunga"], x["pozitie"]) for x in r[mod]}), 1, r[mod])
        p = self.r[(1280, 720)]["program"]                   # aici sărea, la fiecare degajare
        self.assertTrue(all(x["lunga"] and x["pozitie"] == "static" for x in p), p)
        self.assertTrue(any(x["h"] <= x["loc"] for x in p), p)                    # încăpea în pașii cu verde: rezerva o ține desprinsă și în ei
        self.assertTrue(any(x["h"] > x["loc"] and x["pas"].startswith("degajare") for x in p), p)

    def test_panoul_incape_sub_banda(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                p = r["panou"]
                self.assertEqual(p["rezumat"], "Toate cele cinci verigi sunt în regulă.")
                self.assertLessEqual(p["h"], p["loc"])
                self.assertLessEqual(p["jos"], p["vh"])

    def test_textul_rar_pe_cel_mult_doua_randuri(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                x = r["rar"]
                self.assertTrue(x["revino"])
                self.assertTrue(x["text"].startswith("Se schimbă spre: Verde pentru pietoni, pe toate trecerile. Întâi se încheie schimbarea spre „Verde pe Bd. Dacia"), x)
                self.assertLessEqual(x["linii"], 2, x)


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestBandaPesteButon(unittest.TestCase):
    """Pe un telefon, 375×812, și pe un ecran îngust, 700×900 (în ramă): butonul apăsat chiar sub banda goală rămâne pe ecran, sub bandă, și după
    ce banda crește la „Cerere primită” și la „Aplicat”; un buton derulat de cititor departe sau sub bandă nu trage pagina după el."""

    ECRANE = ((375, 812), (700, 900))

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        pagina = C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), ACOPERIT)
        cls.r = {}
        for w, h in cls.ECRANE:
            (cls.d / str(w)).mkdir()
            cls.r[(w, h)] = ruleaza_pagina(cls.d / str(w), pagina, ecran=(w, h))

    def test_butonul_apasat_ramane_sub_banda_care_creste(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                self.assertEqual(r["ecran"], list(ecran))
                self.assertEqual(r["inainte"]["banda"], 0)                  # nicio comandă încă: banda nu ocupă loc
                self.assertAlmostEqual(r["inainte"]["sus"], 20, delta=1)
                self.assertTrue(r["confirmare"]["deschisa"])
                for k in ("trimisa", "aplicata"):
                    s = r[k]
                    self.assertTrue(s["focus"], (k, s))
                    self.assertGreater(s["banda"], 0, (k, s))
                    self.assertEqual(s["acoperit"], 0, (k, s))            # banda, crescută, nu acoperă butonul
                    self.assertTrue(s["in_ecran"], (k, s))
                self.assertIn("Plan de referință", r["trimisa"]["rezultat"])
                self.assertIn("Aplicat", r["aplicata"]["rezultat"])
                self.assertTrue(r["aplicata"]["revino"])
                self.assertGreater(r["aplicata"]["banda"], r["trimisa"]["banda"])

    def test_butonul_derulat_de_cititor_nu_trage_pagina(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                d, s = r["departe"], r["sub_banda"]
                self.assertTrue(d["inainte"]["focus"] and s["inainte"]["focus"])
                self.assertGreater(d["dupa"]["banda"], d["inainte"]["banda"])   # banda a crescut...
                self.assertFalse(d["dupa"]["in_ecran"])                          # ...dar butonul rămâne unde l-a lăsat cititorul
                self.assertLess(d["dupa"]["sus"], 0)
                self.assertGreater(s["dupa"]["banda"], s["inainte"]["banda"])
                self.assertGreater(s["inainte"]["acoperit"], 0)
                self.assertGreater(s["dupa"]["acoperit"], 0)


@unittest.skipUnless(Path(C.CHROME).exists(), "Chrome nu e instalat aici")
class TestComandaPeLaptop(unittest.TestCase):
    """Pe laptopul prezentării, în fereastra mărită a lui Chrome (1536×730 și 1536×700, în ramă), cu imaginea ascunsă: confirmarea stă înaintea
    comenzii manuale, iar butoanele direcțiilor, înaintea explicației. Așa, în comanda manuală, primele două butoane de direcție, banda și
    rândul de rezumat al panoului „Starea senzorului” se văd deodată, iar confirmarea întoarcerii la program se deschide pe ecran, fără să
    scoată panoul din vedere, și la prima comandă, și a doua oară pe aceeași pagină. Butoanele și confirmarea merg ca înainte; cât e deschisă
    confirmarea unei faze cu risc, butoanele coborâte sub cursor nu se apasă cu mausul, iar după „Da”, al doilea clic al unui dublu clic nu
    nimerește o direcție."""

    ECRANE = ((1536, 730), (1536, 700))
    DERULARE = 70            # cât are voie pagina să coboare singură, în px: ținta e ≈60

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.d, True)      # și când scenariul eșuează în setUpClass
        pagina = C.pagina(C.VERSIUNI["curent"].read_text(encoding="utf-8"), LAPTOP)
        cls.r = {}
        for w, h in cls.ECRANE:
            (cls.d / str(h)).mkdir()
            cls.r[(w, h)] = ruleaza_pagina(cls.d / str(h), pagina, ecran=(w, h))

    def pe_ecran(self, s, *locuri):
        """Fiecare loc e întreg în fereastră și sub bandă, iar banda se vede întreagă (cu o toleranță de 1 px, pentru rotunjirile așezării)."""
        self.assertGreaterEqual(s["banda"]["sus"], 0, s)
        for x in locuri:
            self.assertGreater(x["jos"], x["sus"], s)                     # se vede, nu e ascuns
            self.assertGreaterEqual(x["sus"], s["banda"]["jos"] - 1, s)
            self.assertLessEqual(x["jos"], s["vh"] + 1, s)

    def test_ordinea_blocurilor(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                self.assertEqual(r["ecran"], list(ecran))
                o = r["ordine"]
                self.assertTrue(o["blocat_confirm"] and o["confirm_manual"] and o["manual_istoric"], o)      # confirmarea, imediat sub cartonașele modurilor
                self.assertTrue(o["faze_risc"] and o["risc_explicatie"] and o["faze_explicatie"] and o["explicatia_incheie"], o)   # butoanele, apoi fazele cu risc, apoi explicația
                self.assertTrue(o["explicatie"].startswith("Schimbarea se face singură, pe pași, iar banda de sus spune unde a ajuns"), o)
                self.assertFalse(o["pagina"])                # „Alegeți direcția.” ar trimite la butoane aflate acum deasupra; o spune cartonașul
                self.assertEqual(o["cartonas"], "Alegeți ce direcție primește verde.")

    def test_in_comanda_manuala_butoanele_banda_si_panoul_se_vad_deodata(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                p = r["preluare"]                            # tasta 5: confirmarea preluării, pe ecran
                self.assertTrue(p["deschisa"])
                self.assertEqual(p["focus"], "confirm")
                self.assertEqual(p["buton"], "Da, preiau comanda")
                self.assertEqual(p["trimise"], [{"mod": "manual", "faza": 0}])
                self.assertLessEqual(p["y"], self.DERULARE)
                self.pe_ecran(p, p["confirm"], p["da"], p["rezumat"])
                m = r["manual"]
                self.assertFalse(m["deschisa"])
                self.assertEqual(m["focus"], "mod:manual")   # focusul s-a întors la „Comandă manuală”
                self.assertIn("Aplicat", m["rezultat"])
                self.assertEqual(m["revino"], "Reveniți la „Planul observat”")
                self.assertEqual(len(m["faze"]), 3)
                self.assertLessEqual(m["y"], self.DERULARE)
                self.pe_ecran(m, m["faze"][0], m["faze"][1], m["rezumat"])

    def test_a_doua_oara_pe_aceeasi_pagina_tot_incap(self):
        """După prima comandă, banda păstrează loc pentru două rânduri, deci coloana stă cu ≈21 px mai jos, iar la tasta 5 pagina coboară
        cu atât mai mult (pe pagina reală, la 1536×730: 28 px, nu 7). Butoanele, banda și rândul de rezumat se văd tot deodată."""
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                g = r["program2"]
                self.assertTrue(g["loc_de_doua_randuri"], g)
                self.assertGreater(g["banda"]["jos"] - g["banda"]["sus"], r["preluare"]["banda"]["jos"] - r["preluare"]["banda"]["sus"] + 10, g)
                p, m, v = r["preluare2"], r["manual2"], r["revenire2"]
                self.assertTrue(p["deschisa"])
                self.assertEqual(p["buton"], "Da, preiau comanda")
                self.assertGreater(p["y"], r["preluare"]["y"] + 10)          # banda mai înaltă: pagina coboară mai mult decât prima oară
                self.pe_ecran(p, p["confirm"], p["da"], p["rezumat"])
                self.assertFalse(m["deschisa"])
                self.assertIn("Aplicat", m["rezultat"])
                self.pe_ecran(m, m["faze"][0], m["faze"][1], m["rezumat"])
                self.assertTrue(v["deschisa"])
                self.assertIn("către „Planul observat”", v["text"])
                self.pe_ecran(v, v["confirm"], v["da"], v["rezumat"])
                for s in (p, m, v):
                    self.assertLessEqual(s["y"], self.DERULARE, s)

    def test_confirmarea_intoarcerii_se_deschide_pe_ecran(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                v = r["revenire"]
                self.assertTrue(v["deschisa"])
                self.assertEqual(v["focus"], "confirm")
                self.assertIn("către „Planul observat”", v["text"])
                self.assertLessEqual(v["y"], self.DERULARE)
                self.pe_ecran(v, v["confirm"], v["da"], v["rezumat"])       # panoul senzorului nu iese din vedere
                self.assertEqual(r["renuntat"], {"deschisa": False, "focus": "revino"})

    def test_butoanele_si_confirmarea_merg_ca_inainte(self):
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                self.assertEqual(r["directa"], {"trimise": [{"mod": "manual", "faza": 1}], "deschisa": False})   # o direcție obișnuită, dintr-un clic
                k = r["risc"]                                # o fază cu risc cere confirmare și nu trimite nimic până atunci
                self.assertTrue(k["deschisa"] and k["risc"], k)
                self.assertEqual((k["focus"], k["buton"], k["trimise"]), ("confirm", "Da, cu risc de blocare", 0))
                e = r["risc_esc"]                            # Esc: focusul, înapoi pe butonul fazei
                self.assertEqual((e["deschisa"], e["focus"], e["trimise"]), (False, "faza:3", 0))
                self.assertEqual(r["intoarcere"], {"trimise": [{"mod": "program"}], "deschisa": False})

    def test_la_confirmarea_unei_faze_cu_risc_butoanele_coborate_sub_cursor_nu_se_apasa(self):
        """Confirmarea se deschide deasupra butoanelor și le coboară cu înălțimea ei: în locul clicului ajung butoanele direcțiilor, care
        se trimit dintr-un clic. Al doilea clic al unui dublu clic nu trimite nimic, nu închide confirmarea și nu nimerește „Da”."""
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                k = r["risc"]
                self.assertGreater(k["mutat"], 100, k)                       # butonul apăsat a coborât cu înălțimea confirmării
                self.assertEqual(k["maus"], ["none"] * 4, k)                 # direcțiile, fazele cu risc și titlul listei: fără maus
                self.assertEqual(k["sub_cursor"], ["", "", ""], k)           # nici „Da”, nici „Renunț”, nici alt buton
                self.assertEqual(k["dupa_clicuri"], {"trimise": 0, "deschisa": True, "risc": True, "focus": "confirm"})
                self.assertEqual(r["risc_esc"]["maus"], ["auto"] * 4)        # Esc le redă
                self.assertEqual(r["intoarcere_maus"], ["auto"] * 4)         # o confirmare obișnuită nu oprește nimic

    def test_al_doilea_clic_al_unui_dublu_clic_pe_da_nu_trimite_o_directie(self):
        """După „Da, trec la „Planul observat””, confirmarea se închide și butoanele direcțiilor urcă în locul lui „Da”, iar cât simularea e
        încă în comanda manuală, un clic pe o direcție o trimite fără confirmare. Clicurile trec prin `document.elementFromPoint`, ca mausul
        adevărat: al doilea și al treilea clic, la 150 ms și la 450 ms, în trei locuri ale lui „Da”, nu trimit nimic în afara întoarcerii la
        program (700 ms comanda manuală nu primește clicuri de maus), iar după ≈1,5 s un clic în același loc trimite direcția de acolo."""
        for ecran, r in self.r.items():
            with self.subTest(ecran=ecran):
                d = r["dublu"]
                self.assertEqual((d["deschisa"], d["buton"], d["primul"], d["inchisa"]), (True, "Da, trec la „Planul observat”", "da", True), d)
                self.assertTrue(any(d["peste"]), d)            # măcar un loc al lui „Da” a ajuns peste o direcție: fără pază, clicul de acolo o trimite
                self.assertEqual(d["maus"], "none", d)
                for clicuri in (d["al_doilea"], d["al_treilea"]):
                    self.assertFalse([c for c in clicuri if c.startswith("faza:")], d)   # nicio direcție sub cursor
                self.assertEqual(d["trimise"], [{"mod": "program"}], d)                  # doar întoarcerea la program
                self.assertEqual(d["maus_dupa"], "auto", d)
                f = next(p for p in d["peste"] if p)
                self.assertEqual(d["dupa"], f, d)
                self.assertEqual(d["trimise_dupa"], [{"mod": "manual", "faza": int(f.split(":")[1])}], d)


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
