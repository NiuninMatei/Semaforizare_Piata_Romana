const NUME={magheru:"Magheru",catargiu:"Lascăr Catargiu",dacia_est:"Dacia est",dacia_vest:"Dacia vest",mendeleev:"Mendeleev",caderea_bastiliei:"Căderea Bastiliei"};
const MOD={ai:"Agent AI (PPO)",fix:"Plan fix (N–S / E–V / pietoni)",max_pressure:"Max-Pressure",manual:"Manual",program:"Program pe cazuri de trafic",plan_lung:"plan cu ciclu lung 46/48/12 s",ai_pranz:"agentul E3, trafic mediu și intens",ai_lejer:"agentul E9, trafic lejer",ai_e13:"agentul E13 (oficialul reantrenat)",plan_scurt:"plan fix scurt 12/14/12 s",plan_mediu:"plan fix 16/10/12 s, trafic lejer și mediu"};
// geometrie aproximativă: unghiuri reale ale brațelor (nord sus)
const BRATE={catargiu:[-130,"in"],caderea_bastiliei:[-80,"out"],dacia_est:[0,"in"],magheru:[100,"in"],mendeleev:[140,"out"],dacia_vest:[180,"in"]};
const FAZA_BRATE=[["magheru","catargiu"],["dacia_est","dacia_vest"],[],["magheru","catargiu","dacia_est","dacia_vest"],["magheru","catargiu","dacia_est","dacia_vest"]];
let sim=null, modCerut=null, fazaCeruta=null;
const $=id=>document.getElementById(id);
setInterval(()=>{$("ceas").textContent=new Date().toLocaleTimeString("ro-RO")},1000);

function schema(s){
  const g=$("schema"), cx=150, cy=135; let h=`<circle cx="${cx}" cy="${cy}" r="26" fill="#d9ddd6" stroke="#1f2a33" stroke-width="1.5"/>`;
  const verzi=s?FAZA_BRATE[s.faza]||[]:[]; const etapa=s?s.etapa:"";
  for(const [b,[ang,tip]] of Object.entries(BRATE)){
    const a=ang*Math.PI/180, x1=cx+30*Math.cos(a), y1=cy+30*Math.sin(a), x2=cx+100*Math.cos(a), y2=cy+86*Math.sin(a), xl=cx+112*Math.cos(a), yl=cy+102*Math.sin(a);
    h+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#9aa39b" stroke-width="${tip=="in"?14:8}" stroke-linecap="round"/>`;
    if(tip=="in"){
      const q=s&&s.coada_brate?(s.coada_brate[b]||0):0, L=Math.min(1,q/25);
      const xq=x1+(x2-x1)*L, yq=y1+(y2-y1)*L;
      const col=q>18?"#c8322a":q>8?"#e2a013":"#1d5fa8";
      h+=`<line x1="${x1}" y1="${y1}" x2="${xq}" y2="${yq}" stroke="${col}" stroke-width="9" stroke-linecap="round"/>`;
      const verde=verzi.includes(b), lum=verde?(etapa=="yellow"?"#e2a013":(etapa=="red"?"#c8322a":"#1d9152")):"#c8322a";
      h+=`<circle cx="${x1}" cy="${y1}" r="7" fill="${lum}" stroke="#1f2a33" stroke-width="1.5"><title>${NUME[b]}: ${verde?"verde":"roșu"}</title></circle>`;
      h+=`<text x="${xl}" y="${yl+(Math.sin(a)>0.2?10:Math.sin(a)<-0.2?-2:-12)}" text-anchor="${Math.cos(a)>0.5?"end":Math.cos(a)<-0.5?"start":"middle"}" font-family="Barlow" font-size="12.5" fill="#1f2a33">${NUME[b]} · ${q}</text>`;
    } else {
      h+=`<text x="${xl}" y="${yl+(Math.sin(a)>0?10:-2)}" text-anchor="middle" font-family="Barlow" font-size="11.5" fill="#5d6873">${NUME[b]} (ieșire)</text>`;
    }
  }
  const pw=s&&s.coada_brate?(s.coada_brate.pietoni||0):null;
  if(pw!==null) h+=`<text x="${cx}" y="${cy+4}" text-anchor="middle" font-family="Barlow" font-size="11.5" fill="#1f2a33"><title>Pietoni care așteaptă la trecerile pieței</title>pietoni ${pw}</text>`;
  g.innerHTML=h;
}
function grafic(ist){
  const c=$("grafic"), r=window.devicePixelRatio||1, w=c.clientWidth, hh=150; c.width=w*r; c.height=hh*r;
  const x=c.getContext("2d"); x.scale(r,r); x.clearRect(0,0,w,hh);
  if(!ist||ist.length<2){x.fillStyle="#5d6873";x.font="14px Barlow";x.fillText("Graficul apare după primul minut de simulare.",8,24);return}
  const m=Math.max(10,...ist.map(p=>p[1])); x.strokeStyle="#c9cec7"; x.fillStyle="#5d6873"; x.font="12px Barlow";
  for(let k=0;k<=2;k++){const y=hh-18-(hh-30)*k/2; x.beginPath();x.moveTo(30,y);x.lineTo(w,y);x.stroke(); x.fillText(Math.round(m*k/2),2,y+4)}
  x.strokeStyle="#1d5fa8"; x.lineWidth=2; x.beginPath();
  ist.forEach((p,i)=>{const px=30+(w-34)*i/(ist.length-1), py=hh-18-(hh-30)*p[1]/m; i?x.lineTo(px,py):x.moveTo(px,py)}); x.stroke();
}
function butoane(s){
  const mod=s?s.mod:null;
  document.querySelectorAll("[data-mod]").forEach(b=>{b.setAttribute("aria-pressed",b.dataset.mod==mod);
    if(b.dataset.mod=="ai") b.disabled=!!s&&!s.model_ai, b.title=s&&!s.model_ai?"Nu există model antrenat în models/":""});
  $("manual").classList.toggle("vizibil",mod=="manual");
  if(s&&s.faze&&!$("faze").children.length){
    $("faze").innerHTML=s.faze.map((f,i)=>`<button data-faza="${i}">${f}</button>`).join("");
    document.querySelectorAll("[data-faza]").forEach(b=>b.onclick=()=>cere("manual",+b.dataset.faza));
  }
  document.querySelectorAll("[data-faza]").forEach(b=>b.setAttribute("aria-pressed",s&&mod=="manual"&&+b.dataset.faza==s.faza));
}
function cere(mod,faza){
  modCerut=mod; fazaCeruta=faza;
  const t=mod=="manual"?`Treceți semaforul pe faza „${sim&&sim.faze?sim.faze[faza]:faza}”? Agentul AI nu va mai interveni până alegeți alt mod.`
        :`Predați controlul semaforului către: ${MOD[mod]}?`;
  $("confirm-text").textContent=t; $("confirm").classList.add("vizibil"); $("da").focus();
}
document.querySelectorAll("[data-mod]").forEach(b=>b.onclick=()=>{ if(b.dataset.mod=="manual"){ cere("manual", sim?sim.faza:0) } else cere(b.dataset.mod)});
$("nu").onclick=()=>$("confirm").classList.remove("vizibil");
$("da").onclick=async()=>{
  const r=await fetch("/api/command",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mod:modCerut,faza:fazaCeruta})});
  $("confirm").classList.remove("vizibil");
  if(!r.ok) alert("Comanda nu a fost acceptată: "+(await r.json()).eroare);
};
document.addEventListener("keydown",e=>{if(e.key=="Escape")$("confirm").classList.remove("vizibil")});

async function actualizeaza(){
  let d; try{ d=await (await fetch("/api/state",{cache:"no-store"})).json() }catch(e){ $("s-cam").textContent="serverul dashboard nu răspunde"; $("p-cam").className="punct err"; return }
  const c=d.camera; sim=d.simulare&&d.simulare._varsta_s<10?d.simulare:null;
  // camera
  if(c&&c._varsta_s<15){
    $("p-cam").className="punct "+(c.conectat?"ok":"atent");
    $("s-cam").textContent=c.conectat?"camera: flux live":"camera: reconectare în curs";
    $("s-fps").textContent=`${c.fps} cadre/s analizate`; $("s-urm").textContent=`${c.vehicule_urmarite} vehicule urmărite`;
    // flux MJPEG continuu (pornit o singură dată), nu o imagine reîncărcată la fiecare secundă
    if(!$("cadru").dataset.flux){ $("cadru").dataset.flux="1"; $("cadru").src="../imagini/camera_piata_romana.jpg" }
    $("cadru-gol").style.display="none";
    const ins=c.intrari_veh_h||{}, outs=c.iesiri_veh_h||{}, k=Object.keys(NUME);
    const ped=c.pietoni_h||{};
    $("debite").innerHTML=k.map(b=>`<tr><td>${NUME[b]}</td><td class="n">${ins[b]??"–"}</td><td class="n">${outs[b]??"–"}</td></tr>`).join("")+
      Object.keys(ped).map(b=>`<tr><td>Pietoni pe trecerea ${NUME[b]||b}</td><td class="n" colspan="2">${ped[b]} pers/h</td></tr>`).join("")+
      `<tr><td colspan="3" class="sub">Interval curent: ${Math.round((c.secunde_interval||0)/60)} min. Debitele se stabilizează după ~5 min.</td></tr>`;
  } else {
    // starea veche de cel mult 3 minute = o microînghețare sau o întrerupere scurtă a fluxului (§ 4.6): modulul rulează
    const v=c?Math.round(c._varsta_s):null, scurt=v!==null&&v<180;
    $("p-cam").className="punct "+(scurt?"atent":"err");
    $("s-cam").textContent=scurt?`camera: fără cadre noi de ${v} s (fluxul sau prelucrarea stă)`:"camera: modulul de viziune nu rulează";
    $("s-fps").textContent=""; $("s-urm").textContent="";
    $("cadru-gol").innerHTML=scurt?`Imaginea s-a oprit de ${v} s: fluxul camerei sau prelucrarea stă.<br>De obicei revine singură în mai puțin de un minut.`
      :"Nu primesc imagini de la modulul de viziune.<br>Porniți-l cu <b>scripts\\2_viziune_live.bat</b>; imaginea apare aici în câteva secunde.";
    $("cadru-gol").style.display="grid"
  }
  // simulare
  if(sim){
    $("faza").textContent=sim.faza_nume.split("(")[0].trim();
    const et={green:"verde",yellow:"galben",red:"roșu de degajare"}[sim.etapa];
    $("faza-det").textContent=`${et}, de ${sim.verde_s} s · condus de ${MOD[sim.mod]}${sim.mod_program?` (acum: ${MOD[sim.mod_program]})`:""} · ${sim.vehicule_in_retea} vehicule și ${sim.pietoni_in_retea??0} pietoni în simulare`;
    $("sursa").textContent="Cererea de trafic vine din: "+sim.sursa;
    grafic(sim.istoric_coada);
  } else { $("faza").textContent="—"; $("faza-det").textContent="Geamănul digital nu rulează. Porniți scripts\\6_geaman_digital.bat."; grafic(null) }
  schema(sim); butoane(sim);
}
actualizeaza(); setInterval(actualizeaza,1000);
