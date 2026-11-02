const NUME={magheru:"Magheru",catargiu:"Lascăr Catargiu",dacia_est:"Dacia est",dacia_vest:"Dacia vest",mendeleev:"Mendeleev",caderea_bastiliei:"Căderea Bastiliei"};
const MODURI={program:{nume:"Program în vigoare",cine:"calculatorul",text:"programul ales după testele din simulare"},ai:{nume:"Agent IA",cine:"calculatorul",text:"un program antrenat în simulare, care alege faza după cozi"},
  fix:{nume:"Plan de referință",cine:"calculatorul",text:"verde pe rând, mereu la fel: 36 s Magheru–Catargiu, 28 s Dacia, 12 s pietoni"},max_pressure:{nume:"Presiune maximă",cine:"calculatorul",text:"verde pentru direcția cu cele mai lungi cozi"},
  manual:{nume:"Comandă manuală",cine:"dumneavoastră",text:"alegeți dumneavoastră direcția care primește verde"}};
const ORDINE=["program","ai","fix","max_pressure","manual"];
const SUBPROGRAM={plan_scurt:"verde 12 s Magheru–Catargiu, 14 s Dacia, 12 s pietoni",plan_mediu:"verde 16 s Magheru–Catargiu, 10 s Dacia, 12 s pietoni",plan_lung:"verde 46 s Magheru–Catargiu, 48 s Dacia, 12 s pietoni",
  ai:"agentul IA",ai_pranz:"agentul IA pentru trafic mediu și intens",ai_lejer:"agentul IA pentru trafic lejer",ai_e13:"agentul IA reantrenat",fix:"planul de referință"};
const FAZE_CLARE=["Verde pe Magheru și Lascăr Catargiu","Verde pe Bd. Dacia, est și vest","Verde pentru pietoni, pe toate trecerile","Verde pe Magheru și Catargiu, plus intrările Dacia","Verde pe Dacia, plus intrările Magheru și Catargiu"];
const FAZE_RISC=[3,4];
const LUMINI={verde:["#12713f","V","#fff"],galben:["#e2a013","G","#1f2a33"],"roșu de degajare":["#b3261e","R","#fff"],"roșu":["#b3261e","R","#fff"],necunoscut:["#8a948c","?","#fff"]};
// geometrie aproximativă: unghiuri reale ale brațelor (nord sus); eticheta: x, y, ancora
const BRATE={catargiu:[-130,"in",70,50,"middle"],caderea_bastiliei:[-80,"out",172,30,"middle"],dacia_est:[0,"in",262,121,"end"],magheru:[100,"in",131,246,"middle"],mendeleev:[140,"out",62,212,"middle"],dacia_vest:[180,"in",38,121,"start"]};
const FAZA_BRATE=[["magheru","catargiu"],["dacia_est","dacia_vest"],[],["magheru","catargiu","dacia_est","dacia_vest"],["magheru","catargiu","dacia_est","dacia_vest"]];
const FLUX="../imagini/camera_piata_romana.jpg";
const ASTEPTARE_COMANDA_MS=10000, TIMP_MAXIM_CERERE_MS=4000;
let sim=null, simUltim=null, simUltimLa=0, cam=null, legatura=true, cazutLa=null, ultimaStare=0;
let modCerut=null, fazaCeruta=null, deschisDe=null, cerere=null, modVazut=null, modAnterior=null, imagineOprita=false, fluxPornit=false, reluare=false, cheieAlerte="";
const istoric=[], schimbari=[];
const $=id=>document.getElementById(id);
const ora=ms=>new Date(ms).toLocaleTimeString("ro-RO");
const nr=v=>Number(v).toLocaleString("ro-RO",{maximumFractionDigits:1});
function durata(s){ s=Math.max(0,Math.round(s)); if(s<90) return `${s} s`; if(s<3600) return `${Math.floor(s/60)} min${s%60?` ${s%60} s`:""}`; return `${Math.floor(s/3600)} h ${Math.round(s%3600/60)} min` }
function pune(el,html){ if(el.dataset.ultim!==html){ el.dataset.ultim=html; el.innerHTML=html } }   // rescrie doar când se schimbă, ca să nu mute cititorul de ecran
setInterval(()=>{ $("ceas").textContent=new Date().toLocaleTimeString("ro-RO");
  const v=ultimaStare?(Date.now()-ultimaStare)/1000:null;
  $("proaspat").textContent=v===null?"":legatura?`date primite acum ${durata(v)}`:`date vechi de ${durata(v)}`; $("proaspat").className=legatura&&v<5?"":"intarziat";
},1000);

function starea(s,b,etapa,verzi){ if(!s) return "necunoscut"; if(!verzi.includes(b)) return "roșu"; return etapa=="yellow"?"galben":etapa=="red"?"roșu de degajare":"verde" }
function schema(s){
  const cx=150, cy=135, verzi=s?FAZA_BRATE[s.faza]||[]:[], etapa=s?s.etapa:"", pietoniVerde=!!s&&s.faza==2&&etapa=="green";
  let brate="", lumini="", texte="", descriere=[];
  for(const [b,[ang,tip,xl,yl,anc]] of Object.entries(BRATE)){
    const a=ang*Math.PI/180, x1=cx+30*Math.cos(a), y1=cy+30*Math.sin(a), x2=cx+100*Math.cos(a), y2=cy+86*Math.sin(a);
    brate+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#7f897f" stroke-width="${tip=="in"?14:7}" stroke-linecap="round"/>`;
    if(tip=="in"){
      const q=s&&s.coada_brate?(s.coada_brate[b]||0):null, L=Math.min(1,(q||0)/25), xq=x1+(x2-x1)*L, yq=y1+(y2-y1)*L;
      if(q) brate+=`<line x1="${x1}" y1="${y1}" x2="${xq}" y2="${yq}" stroke="#27465f" stroke-width="10" stroke-linecap="round"/>`;
      const st=starea(s,b,etapa,verzi), [col,lit,cl]=LUMINI[st];
      lumini+=`<g><title>${NUME[b]}: ${st}</title><circle cx="${x1}" cy="${y1}" r="9.5" fill="${col}" stroke="#1f2a33" stroke-width="1.5"/><text x="${x1}" y="${y1+4}" text-anchor="middle" font-family="Barlow" font-weight="700" font-size="11.5" fill="${cl}">${lit}</text></g>`;
      texte+=`<text x="${xl}" y="${yl}" text-anchor="${anc}" font-family="Barlow" font-size="12.5" fill="#1f2a33">${NUME[b]}: ${q===null?"—":q}</text>`;
      descriere.push(`${NUME[b]} ${st}, ${q===null?"coadă necunoscută":`${q} vehicule oprite`}`);
    } else {
      texte+=`<text x="${xl}" y="${yl}" text-anchor="${anc}" font-family="Barlow" font-size="11.5" fill="#5d6873">${NUME[b]} (ieșire)</text>`;
    }
  }
  const pw=s&&s.coada_brate?(s.coada_brate.pietoni??0):null;
  const centru=`<circle cx="${cx}" cy="${cy}" r="25" fill="${pietoniVerde?"#cfe8d8":"#dfe3dc"}" stroke="${pietoniVerde?"#12713f":"#1f2a33"}" stroke-width="${pietoniVerde?3:1.5}"/>`+
    `<g><title>Pietoni care așteaptă la trecerile pieței${pietoniVerde?"; acum au verde":""}</title><text x="${cx}" y="${cy-3}" text-anchor="middle" font-family="Barlow" font-size="10" fill="#1f2a33">pietoni</text><text x="${cx}" y="${cy+12}" text-anchor="middle" font-family="Barlow" font-weight="700" font-size="14" fill="#1f2a33">${pw===null?"—":pw}</text></g>`;
  pune($("schema"),brate+centru+lumini+texte);
  $("svg-schema").setAttribute("aria-label",s?`Schema pieței. ${descriere.join("; ")}. Pietoni care așteaptă: ${pw??0}${pietoniVerde?", au verde":""}.`:"Schema pieței: nu sunt date de la simulare");
}
function grafic(ist,viu){
  const c=$("grafic"), r=window.devicePixelRatio||1, w=c.clientWidth, hh=150; c.width=w*r; c.height=hh*r;
  const x=c.getContext("2d"); x.scale(r,r); x.clearRect(0,0,w,hh);
  if(!ist||ist.length<2){
    $("grafic-rez").textContent=viu?"Graficul apare după primul minut de simulare.":"Simularea nu trimite date, deci nu sunt cozi de arătat.";
    $("grafic").setAttribute("aria-label","Evoluția cozii totale: nu sunt date"); return }
  const acum=ist[ist.length-1][0], vedere=ist.filter(p=>acum-p[0]<=600), v=vedere.map(p=>p[1]);
  const m=Math.max(10,Math.ceil(Math.max(...v)/10)*10), X=t=>38+(w-44)*(1-(acum-t)/600), Y=q=>hh-22-(hh-34)*q/m;
  x.font="12px Barlow"; x.textBaseline="middle";
  for(let k=0;k<=2;k++){ const y=Y(m*k/2); x.strokeStyle="#c9cec7"; x.beginPath();x.moveTo(38,y);x.lineTo(w,y);x.stroke(); x.fillStyle="#5d6873"; x.fillText(Math.round(m*k/2),8,y) }
  x.textBaseline="alphabetic";
  [[600,"−10 min","left"],[300,"−5 min","center"],[0,"acum","right"]].forEach(([d,t,al])=>{ x.textAlign=al; x.fillStyle="#5d6873"; x.fillText(t,X(acum-d),hh-5) }); x.textAlign="left";
  schimbari.filter(z=>acum-z.t<=600).forEach(z=>{ const px=X(z.t); x.strokeStyle="#5d6873"; x.setLineDash([3,3]); x.beginPath();x.moveTo(px,10);x.lineTo(px,hh-22);x.stroke(); x.setLineDash([]); x.fillStyle="#1f2a33"; x.textAlign=px>w-110?"right":"left"; x.fillText(MODURI[z.mod]?.nume||z.mod,px+(px>w-110?-4:4),10); x.textAlign="left" });
  x.strokeStyle="#1d5fa8"; x.lineWidth=2; x.beginPath();
  vedere.forEach((p,i)=>{ const px=X(p[0]), py=Y(p[1]); i?x.lineTo(px,py):x.moveTo(px,py) }); x.stroke(); x.lineWidth=1;
  const rez=`Acum: ${v[v.length-1]} vehicule oprite; cel mai mult: ${Math.max(...v)}, cel mai puțin: ${Math.min(...v)}, în ultimele ${durata(Math.min(600,acum-vedere[0][0]))}.`;
  $("grafic-rez").textContent=rez; $("grafic").setAttribute("aria-label","Evoluția cozii totale. "+rez);
}
function faze(s){
  if(!s||!s.faze||$("faze").children.length) return;
  const btn=(i)=>`<button data-faza="${i}"><b>${FAZE_CLARE[i]||s.faze[i]}</b></button>`, toate=s.faze.map((_,i)=>i);
  $("faze").innerHTML=toate.filter(i=>!FAZE_RISC.includes(i)).map(btn).join(""); $("faze-risc").innerHTML=toate.filter(i=>FAZE_RISC.includes(i)).map(btn).join("");
  document.querySelectorAll("[data-faza]").forEach(b=>b.onclick=()=>alegeFaza(+b.dataset.faza,b));
}
function butoane(s){
  const mod=s?s.mod:null, blocat=!legatura?"Comenzile sunt blocate: nu e legătură cu dispeceratul.":!s?"Comenzile sunt blocate: simularea nu trimite date.":"";
  document.querySelectorAll("[data-mod]").forEach(b=>{ b.setAttribute("aria-pressed",b.dataset.mod==mod); b.disabled=!!blocat||(b.dataset.mod=="ai"&&!!s&&!s.model_ai) });
  $("d-ai").textContent=s&&!s.model_ai?"Indisponibil: pe acest calculator nu există un agent antrenat.":"Un program antrenat în simulare alege faza, după cozi.";
  $("d-program").textContent=s&&s.mod_program&&SUBPROGRAM[s.mod_program]?`Planul ales după testele din simulare: ${SUBPROGRAM[s.mod_program]}.`:"Planul ales după testele din simulare.";
  $("blocat").hidden=!blocat; $("blocat").textContent=blocat;
  $("manual").classList.toggle("vizibil",mod=="manual");
  faze(s);
  document.querySelectorAll("[data-faza]").forEach(b=>{ const f=+b.dataset.faza; b.setAttribute("aria-pressed",!!s&&mod=="manual"&&f==(s.etapa=="green"?s.faza:s.faza_tinta??s.faza)); b.disabled=!!blocat });
  if(blocat&&$("confirm").classList.contains("vizibil")) inchide();
  pune($("cine-acum"),s?`Culorile le schimbă acum: <b>${MODURI[mod]?.cine||"necunoscut"}</b>${mod=="manual"?"":`, cu „${MODURI[mod]?.nume||mod}”`}.`:`Nu se știe cine conduce: ${legatura?"simularea nu trimite date":"nu e legătură cu dispeceratul"}.`);
}
function deschide(text,de){
  $("confirm-text").textContent=text; $("confirm").classList.add("vizibil"); $("da").disabled=false; deschisDe=de||document.activeElement; $("confirm").focus();   // focusul nu cade pe „Confirm”, ca să nu se confirme din reflex
}
function inchide(){ const era=$("confirm").classList.contains("vizibil"); $("confirm").classList.remove("vizibil"); if(era&&deschisDe&&document.contains(deschisDe)&&!deschisDe.disabled) deschisDe.focus(); deschisDe=null }
function cere(mod,faza,de){
  modCerut=mod; fazaCeruta=faza;
  const m=MODURI[mod], actual=sim?MODURI[sim.mod]?.nume||sim.mod:null;
  if(mod=="manual"&&faza===undefined) return deschide(`Preluați comanda manuală${actual?` de la „${actual}”`:""}? Rămâne faza de acum, până alegeți alta.`,de);
  if(mod=="manual") return deschide(`Dați „${FAZE_CLARE[faza]||faza}”? Lasă deschise și celelalte intrări, deci piața se poate bloca.`,de);
  deschide(`Predați conducerea${actual?` de la „${actual}”`:""} către „${m.nume}”: ${m.text}?`,de);
}
function alegeFaza(f,b){
  if(FAZE_RISC.includes(f)) return cere("manual",f,b);
  if(sim&&sim.mod=="manual"&&sim.etapa=="green"&&sim.faza==f) return rezultat(`„${FAZE_CLARE[f]}” e deja activă.`);
  trimite("manual",f);
}
function rezultat(text,cls){ $("rezultat").textContent=text; $("rezultat").className=cls||"" }
function notaIstoric(mod,faza,stare){
  const c=istoric.find(i=>i.id==cerere?.id); if(c) c.stare=stare;
  pune($("istoric-lista"),istoric.slice(-5).reverse().map(i=>`<li>${ora(i.la)} · ${i.nume}: ${i.stare}</li>`).join(""));
  $("istoric-parte").hidden=!istoric.length;
}
function numeComanda(mod,faza){ return mod=="manual"&&faza!==undefined?(FAZE_CLARE[faza]||`faza ${faza}`):(MODURI[mod]?.nume||mod) }
async function trimite(mod,faza){
  const id=Date.now(), nume=numeComanda(mod,faza);
  cerere={id,mod,faza,la:id,etapa:"se trimite"}; istoric.push({id,la:id,nume,stare:"se trimite"}); notaIstoric();
  rezultat(`Se trimite: ${nume}…`); $("da").disabled=true;
  const corp={mod}; if(mod=="manual") corp.faza=faza??(sim?sim.faza:0);
  try{
    const ctl=new AbortController(), t=setTimeout(()=>ctl.abort(),TIMP_MAXIM_CERERE_MS);
    const r=await fetch("/api/command",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(corp),signal:ctl.signal}); clearTimeout(t);
    let raspuns={}; try{ raspuns=await r.json() }catch(e){}
    if(!r.ok) throw new Error(raspuns.eroare||`răspuns ${r.status}`);
    cerere.etapa="primita"; notaIstoric(null,null,"se aplică");
    rezultat(`Cerere primită: ${nume}. Așteptăm simularea…`);
  }catch(e){
    notaIstoric(null,null,"eșuată");
    const ramas=sim?` Conduce în continuare „${MODURI[sim.mod]?.nume||sim.mod}”.`:"";
    rezultat(`Comanda nu a ajuns la dispecerat (${e.name=="AbortError"?"nu a răspuns la timp":e.message}).${ramas} Încercați din nou.`,"rau"); cerere=null;
  }
  inchide(); $("da").disabled=false;
}
function urmaresteCererea(){
  if(!cerere||cerere.etapa!="primita"||!sim) return;
  const {mod,faza,la}=cerere, nume=numeComanda(mod,faza);
  const aplicat=sim.mod==mod&&(mod!="manual"||faza===undefined||(sim.faza==faza&&sim.etapa=="green"));
  if(aplicat){ rezultat(`Aplicat la ${ora(Date.now())}: ${nume}.`,"bun"); notaIstoric(null,null,"aplicată"); cerere=null; return }
  if(sim.mod==mod&&mod=="manual"){ rezultat(`Se schimbă spre: ${nume}. ${sim.etapa=="green"?"Verdele de acum trebuie să țină cel puțin 10 s.":sim.etapa=="yellow"?"Acum: galben.":"Acum: roșu pentru toți."}`); return }
  if(Date.now()-la>ASTEPTARE_COMANDA_MS){ rezultat(`Simularea n-a aplicat încă „${nume}”; conduce „${MODURI[sim.mod]?.nume||sim.mod}”. Încercați din nou.`,"rau"); notaIstoric(null,null,"neaplicată"); cerere=null }
}
function alerte(){
  const lista=[], varstaSim=simUltim?(Date.now()-simUltimLa)/1000:null, varstaCam=cam?cam._varsta_s:null;
  if(!legatura) lista.push(["server","",`Legătura cu dispeceratul s-a pierdut la ${ora(cazutLa)}.`,"Datele de mai jos sunt din acel moment și nu se mai actualizează, iar comenzile sunt blocate. Încercăm din nou la fiecare secundă.","Dacă nu revine, pe calculatorul dispeceratului porniți scripts\\7_dashboard.bat."]);
  else{
    if(!sim) lista.push(["sim","",simUltim?"Simularea nu mai trimite date.":"Simularea nu rulează.",simUltim?"Schema și graficul arată ultimele valori, iar comenzile sunt blocate până revine.":"Nu sunt date despre semafor, iar comenzile sunt blocate.","Dacă s-a oprit, pe calculatorul dispeceratului porniți scripts\\6_geaman_digital.bat."]);
    if(!cam||varstaCam>=180) lista.push(["cam","atent","Camera nu mai trimite date.","Imaginea și traficul măsurat lipsesc sau sunt vechi. De obicei, revin singure; dacă rămâne așa, anunțați operatorul.","Dacă modulul de viziune s-a oprit, porniți scripts\\2_viziune_live.bat. Verificați întâi că nu rulează deja."]);
  }
  const cheie=lista.map(a=>a[0]+a[2]).join("|");
  if(cheie!==cheieAlerte){ cheieAlerte=cheie; $("alerte").innerHTML=lista.map(([,cl,tit,txt,teh])=>`<div class="alerta ${cl}"><p><b>${tit}</b> ${txt}</p><details><summary>Pentru cine administrează sistemul</summary>${teh}</details></div>`).join("") }
}
function pornesteFlux(){ if(imagineOprita||fluxPornit) return; $("cadru").src=reluare?FLUX+(FLUX.includes("?")?"&":"?")+"t="+Date.now():FLUX; fluxPornit=true; reluare=true }
$("cadru").onerror=()=>{ fluxPornit=false };
$("b-imagine").onclick=()=>{ imagineOprita=!imagineOprita; $("b-imagine").setAttribute("aria-pressed",imagineOprita); $("b-imagine").textContent=imagineOprita?"Pornește imaginea":"Oprește imaginea"; if(imagineOprita){ $("cadru").removeAttribute("src"); fluxPornit=false } else pornesteFlux() };
$("b-ajutor").onclick=()=>comutaAjutor();
function comutaAjutor(){ const a=$("ajutor"); a.hidden=!a.hidden; $("b-ajutor").setAttribute("aria-expanded",!a.hidden) }
document.querySelectorAll("[data-mod]").forEach(b=>b.onclick=()=>apasaMod(b.dataset.mod,b));
function apasaMod(mod,b){
  if(b.disabled) return;
  if(sim&&sim.mod==mod) return rezultat(`„${MODURI[mod].nume}” conduce deja.`);
  cere(mod,undefined,b);
}
$("nu").onclick=()=>{ inchide(); rezultat("Ați renunțat. Nu s-a schimbat nimic.") };
$("da").onclick=()=>trimite(modCerut,fazaCeruta);
$("revino").onclick=()=>{ if(modAnterior) cere(modAnterior,undefined,$("revino")) };
document.addEventListener("keydown",e=>{
  if(e.key=="Escape"&&$("confirm").classList.contains("vizibil")){ inchide(); rezultat("Ați renunțat. Nu s-a schimbat nimic."); return }
  if(e.ctrlKey||e.altKey||e.metaKey||$("confirm").classList.contains("vizibil")) return;
  if(e.key=="?") return comutaAjutor();
  const k=ORDINE[+e.key-1]; if(k){ const b=document.querySelector(`[data-mod=${k}]`); apasaMod(k,b) }
});

function afiseazaCamera(c){
  const proaspat=legatura&&!!c&&c._varsta_s<15, v=c?c._varsta_s:null, scurt=v!==null&&v<180;
  if(proaspat){
    $("p-cam").className="punct "+(c.conectat?"ok":"atent-p");
    $("s-cam").textContent=c.conectat?"camera: flux în timp real":"camera: reconectare în curs";
    $("s-fps").textContent=`${nr(c.fps)} cadre/s analizate`; $("s-urm").textContent=`${c.vehicule_urmarite} vehicule urmărite`;
    pornesteFlux();   // flux MJPEG continuu, nu o imagine reîncărcată la fiecare secundă; repornit după o întrerupere
    $("cadru-gol").style.display="none"; $("cadru").removeAttribute("aria-hidden");
  } else {
    // starea veche de cel mult 3 minute = o microînghețare sau o întrerupere scurtă a fluxului (§ 4.6): modulul rulează, de obicei
    $("p-cam").className="punct "+(legatura&&scurt?"atent-p":"err");
    $("s-cam").textContent=!legatura?"camera: stare necunoscută, nu e legătură cu dispeceratul":c?`camera: nicio stare nouă de ${durata(v)}`:"camera: nu trimite date";
    $("s-fps").textContent=""; $("s-urm").textContent=""; fluxPornit=false;
    pune($("cadru-gol"),`<p>${!legatura?"Nu e legătură cu dispeceratul, deci nici imagine.":scurt?`Imaginea s-a oprit de ${durata(v)}. De obicei revine singură în mai puțin de un minut.`:c?`Nu primim imagini de ${durata(v)}. Dacă rămâne așa, anunțați operatorul.`:"Nu primim imagini de la cameră. Dacă rămâne așa, anunțați operatorul."}</p>`);
    $("cadru-gol").style.display="grid"; $("cadru").setAttribute("aria-hidden","true");
  }
  if(c&&c.intrari_veh_h){
    const ins=c.intrari_veh_h||{}, outs=c.iesiri_veh_h||{}, ped=c.pietoni_h||{}, doarIesiri=b=>b=="mendeleev"||b=="caderea_bastiliei";
    pune($("debite"),Object.keys(NUME).map(b=>`<tr><td>${NUME[b]}</td><td class="n">${doarIesiri(b)?'<span class="doar">doar ieșire</span>':ins[b]??"nu e măsurat"}</td><td class="n">${outs[b]??"nu e măsurat"}</td></tr>`).join(""));
    $("t-pietoni").hidden=!Object.keys(ped).length;
    pune($("pietoni"),Object.keys(ped).map(b=>`<tr><td>${NUME[b]||b}</td><td class="n">${ped[b]}</td></tr>`).join(""));
    $("p-deb").classList.toggle("vechi",!proaspat||!legatura);
    $("deb-nota").textContent=proaspat&&legatura?`Măsurat în ultimele ${Math.round((c.secunde_interval||0)/60)} min. În primele 5 min dintr-un sfert de oră, valorile sunt mai puțin sigure.`:`Ultimele valori, vechi de ${durata(legatura?v:(Date.now()-ultimaStare)/1000+v)}.`;
  } else { $("deb-nota").textContent=""; $("p-deb").classList.remove("vechi") }
}
function afiseazaSimularea(){
  const s=sim||simUltim, viu=!!sim&&legatura;
  document.querySelector(".schema").classList.toggle("vechi",!viu&&!!s); $("p-ist").classList.toggle("vechi",!viu&&!!s);
  if(s){
    const f=FAZE_CLARE[s.faza]||s.faza_nume.split("(")[0].trim(), tinta=s.faza_tinta!==undefined?FAZE_CLARE[s.faza_tinta]:null;
    $("faza").textContent=s.etapa=="green"?f:tinta?`Se schimbă spre: ${tinta}`:`Se încheie: ${f}`;
    const et=s.etapa=="green"?`verde de ${s.verde_s} s`:s.etapa=="yellow"?"galben, câteva secunde":"roșu pentru toți, cât se eliberează intersecția";
    const conduce=s.mod=="manual"?"în comandă manuală":`condus de „${MODURI[s.mod]?.nume||s.mod}”`;
    const aproape=s.mod=="manual"&&s.etapa=="green"&&s.verde_s>=60?` · mai sunt ${Math.max(0,90-s.verde_s)} s până la schimbarea automată`:"";
    const risc=FAZE_RISC.includes(s.faza)?" · fază cu risc de blocare":"";
    $("faza-det").textContent=viu?`${et} · ${conduce}${aproape}${risc} · în simulare: ${s.vehicule_in_retea} vehicule, ${s.pietoni_in_retea??0} pietoni`:`Ultimele valori, vechi de ${durata((Date.now()-simUltimLa)/1000)}.`;
    const de_la=s.sursa&&s.sursa.startsWith("camera")?(s.varsta_debite_s>120?`ultimele măsurători bune ale camerei, vechi de ${durata(s.varsta_debite_s)}`:"măsurătorile camerei"):"un profil de referință, fiindcă nu sunt măsurători bune de la cameră";
    $("sursa").textContent=viu?`Simularea folosește ${de_la}${s.debit_echilibrat_veh_h?`: aprox. ${nr(s.debit_echilibrat_veh_h)} vehicule/oră prin piață`:""}.`:"";
  } else { $("faza").textContent="—"; $("faza-det").textContent=""; $("sursa").textContent="" }
  grafic(s?s.istoric_coada:null,viu); schema(s); butoane(viu?sim:null);
}
function deseneaza(){ alerte(); afiseazaCamera(cam); afiseazaSimularea(); urmaresteCererea() }

async function actualizeaza(){
  let d;
  try{
    const ctl=new AbortController(), t=setTimeout(()=>ctl.abort(),TIMP_MAXIM_CERERE_MS);
    const r=await fetch("/api/state",{cache:"no-store",signal:ctl.signal}); clearTimeout(t); d=await r.json();
  }catch(e){ if(legatura){ legatura=false; cazutLa=Date.now(); sim=null } deseneaza(); return }
  legatura=true; cazutLa=null; ultimaStare=Date.now(); cam=d.camera;
  const s=d.simulare; sim=s&&s._varsta_s<10?s:null;
  if(s){ simUltim=s; simUltimLa=Date.now()-s._varsta_s*1000 }
  if(sim&&sim.mod!==modVazut){
    if(modVazut){ modAnterior=modVazut; schimbari.push({t:sim.timp_sim,mod:sim.mod}); if(!cerere) rezultat(`Conducerea a trecut la „${MODURI[sim.mod]?.nume||sim.mod}”.`) }
    modVazut=sim.mod;
  }
  if(modAnterior&&sim&&modAnterior!=sim.mod&&MODURI[modAnterior]){ $("revino").hidden=false; $("revino").textContent=`Reveniți la „${MODURI[modAnterior].nume}”` } else $("revino").hidden=true;
  deseneaza();
}
actualizeaza(); setInterval(actualizeaza,1000);
