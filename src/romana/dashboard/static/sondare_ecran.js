// Ghidul din stânga și rama cu dispeceratul din dreapta. Pagina nu trimite nimic singură: răspunsurile stau în această filă,
// iar persoana le vede la final și decide. Datele din link (`?g=a&o=1&f=…&e=…`) arată grupul, ordinea și formularul;
// fără ele, pagina e o probă deschisă, fără buton de trimitere.
"use strict";

const $ = id => document.getElementById(id);
const PAUZA_CLIC = 700, INDEMN_DUPA = 180000, CHEIE = "sondare_dispecerat", LUNGIME_MAXIMA_LINK = 7500;
const D = DATE_SONDARE;
const q = new URLSearchParams(location.search);
const potrivit = (nume, re) => { const v = q.get(nume); return v && re.test(v) ? v : null; };
const LINK = {grup: potrivit("g", /^[a-z]$/), ordine: potrivit("o", /^[12]$/), formular: potrivit("f", /^[\w-]{20,}$/), intrare: potrivit("e", /^\d{5,}$/)};
const INVITAT = !!(LINK.formular && LINK.intrare);
const TELEFON = window.innerWidth < 900;     // ghidul stă deasupra dispeceratului, nu în stânga lui
const loc = t => (TELEFON ? D.PE_TELEFON.reduce((s, [a, b]) => s.split(a).join(b), t) : t);
let ses = null, blocat = false, indemn = null, ascuns_de_la = null;

function fara(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
function aldin(s) { return fara(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"); }

function salveaza() {
  try { sessionStorage.setItem(CHEIE, JSON.stringify(ses.salvare())); } catch (e) { /* fără stocare, pagina merge până la închiderea filei */ }
}
// De câte ori s-a luat sondajul de la capăt în această filă (pagina v2): textul următor spune că nu e prima trecere. Se numără la
// încărcare, nu la buton, ca să se prindă și butonul paginii v1, rămasă deschisă la cineva în clipa publicării: pagina își salvează
// starea la fiecare încărcare, deci o reîncărcare fără stare vine doar de la „de la capăt”.
const CHEIE_RELUARI = CHEIE + "_reluari", CHEIE_FARA_NUMAR = CHEIE + "_fara_numar";
function reluari() {
  try { return parseInt(sessionStorage.getItem(CHEIE_RELUARI), 10) || 0; } catch (e) { return 0; }
}
function numaraReluarea() {
  try {
    const nav = performance.getEntriesByType("navigation")[0];
    const reincarcata = nav ? nav.type === "reload" : !!(performance.navigation && performance.navigation.type === 1);
    if (sessionStorage.getItem(CHEIE_FARA_NUMAR)) sessionStorage.removeItem(CHEIE_FARA_NUMAR);
    else if (reincarcata && sessionStorage.getItem(CHEIE) === null) sessionStorage.setItem(CHEIE_RELUARI, String(reluari() + 1));
  } catch (e) { /* fără stocare: nu se poate ști */ }
}
function incarca() {
  try {
    const s = JSON.parse(sessionStorage.getItem(CHEIE));
    if (s) return new Sesiune(D, s.ordine, secunde, s);
  } catch (e) { /* o stare stricată: se începe de la capăt */ }
  const ordine = LINK.ordine === "1" ? ["m1", "m2"] : LINK.ordine === "2" ? ["m2", "m1"] : (Math.random() < 0.5 ? ["m1", "m2"] : ["m2", "m1"]);
  return new Sesiune(D, ordine);
}

// Aceleași adrese ca serverul dispeceratului; le cheamă sondare_punte.js din ramă.
window.SONDARE = {
  api(adresa, optiuni) {
    if (adresa.startsWith("/api/state")) return {status: 200, corp: ses.banc.stare()};
    if (adresa.startsWith("/api/command")) {
      let b = {};
      try { b = JSON.parse(optiuni.body); } catch (e) { /* corp stricat */ }
      if (!D.AUTOMATE.includes(b.mod) && b.mod !== "manual") return {status: 400, corp: {eroare: "mod necunoscut"}};
      if (b.mod === "manual" && b.faza !== null && b.faza !== undefined && !(Number.isInteger(b.faza) && b.faza >= 0 && b.faza < D.FAZE.length)) return {status: 400, corp: {eroare: "fază invalidă"}};
      const r = ses.comanda(b.mod, b.faza);
      salveaza();
      return {status: 200, corp: r};
    }
    return {status: 404, corp: {eroare: "adresă necunoscută"}};
  },
};

// Al doilea clic al unui dublu clic nu trebuie să răspundă și la pasul nou, care apare chiar sub cursor.
function apasa(fn) {
  return () => {
    if (blocat) return;
    blocat = true;
    fn();
  };
}
function raspunde(corp = {}) {
  ses.raspunde(corp.valoare, !!corp.nu_reuseste, ses.pas().id);
  salveaza();
  arata();
}
function rama() { return document.querySelector("#scena iframe"); }
function deschide(versiune) {
  if (rama()) return;
  const f = document.createElement("iframe");
  f.title = "Aplicația de supraveghere a semafoarelor";
  f.src = `${versiune}.html`;
  f.addEventListener("load", () => {
    f.contentDocument.addEventListener("click", e => {
      const a = e.target.closest("a");
      if (a) e.preventDefault();             // legăturile din subsol nu scot persoana din ecran
      const b = e.target.closest("button,a,input,select");
      const nume = b && b.querySelector("b");   // butoanele cu descriere: numele, nu toată fraza
      ses.clic(b ? ((nume && nume.textContent) || b.textContent || b.id || b.tagName).trim() : "în afara butoanelor");
      salveaza();
    }, true);
  });
  $("scena").insertBefore(f, $("acoperit"));
  $("gol").style.display = "none";
}
function inchide() {
  const f = rama();
  if (f) f.remove();
  $("gol").style.display = "grid";
  $("gol").textContent = "Aplicația e închisă.";
}
function pregatesteRama(p) {
  const f = rama();
  if (!f) return;
  f.inert = !!p.acoperit;                     // sub acoperire nu se ajunge nici cu tastatura
  try {
    const c = f.contentDocument.getElementById("confirm");
    if (c) c.classList.remove("vizibil");     // o confirmare rămasă nu trece la sarcina următoare
    if (p.tip === "sarcina") f.contentWindow.scrollTo(0, 0);   // fiecare sarcină pornește de sus
  } catch (e) { /* rama încă se încarcă */ }
}
function buton(text, clasa, fn) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = text;
  if (clasa) b.className = clasa;
  b.onclick = apasa(fn);
  return b;
}
function legatura(text, adresa, clasa) {
  const a = document.createElement("a");
  a.textContent = text;
  a.href = adresa;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.className = "buton " + (clasa || "");
  return a;
}
function intrebaOprirea(zona, oprire) {
  oprire.remove();
  const t = document.createElement("p");
  t.textContent = "Sigur vă opriți? Vedeți ce s-a notat până aici și decideți dacă trimiteți ceva.";
  zona.appendChild(t);
  zona.appendChild(buton("Da, mă opresc aici", "secundar", () => { inchide(); ses.renunta(); salveaza(); arata(); }));
  zona.appendChild(buton("Nu, continui", "secundar", arata));
  setTimeout(() => { blocat = false; }, PAUZA_CLIC);
}
// „De la capăt” e pentru o altă persoană, pe același calculator; o a doua trecere a aceleiași persoane nu mai e la prima vedere.
function reiaDeLaCapat(numara) {
  try {
    sessionStorage.removeItem(CHEIE);
    if (!numara) sessionStorage.setItem(CHEIE_FARA_NUMAR, "1");
  } catch (e) { /* fără stocare: pagina pornește oricum de la capăt */ }
  location.reload();
}
function intrebaReluarea(zona, reia) {
  // Fără nimic de trimis (proba deschisă) sau înainte ca aplicația să fi fost deschisă, trecerea următoare e tot la prima vedere.
  if (!INVITAT || !ses.linii.some(r => r.id === "r1_deschide")) { reiaDeLaCapat(false); return; }
  reia.remove();
  const t = document.createElement("p");
  t.textContent = "Butonul este pentru o altă persoană, pe același calculator. Dacă nu ați trimis încă răspunsurile de mai sus, trimiteți-le întâi: după „Da”, ele se șterg din această filă, iar textul următor va spune doar că este a doua încercare din fila aceasta. Dacă ați trimis deja, vă rugăm să nu reluați sondajul.";
  zona.appendChild(t);
  zona.appendChild(buton("Da, este altă persoană", "secundar", () => reiaDeLaCapat(true)));
  zona.appendChild(buton("Înapoi", "secundar", arata));
  setTimeout(() => { blocat = false; }, PAUZA_CLIC);
}
function adresaFormular(text) {
  return `https://docs.google.com/forms/d/e/${LINK.formular}/viewform?usp=pp_url&entry.${LINK.intrare}=${encodeURIComponent(text)}`;
}
function copiaza(text, zona) {
  const spune = mesaj => { $("nota").textContent = mesaj; blocat = false; };
  const gata = () => spune("Textul e copiat. Îl puteți lipi, neschimbat, într-un mesaj către persoana care v-a invitat.");
  const camp = zona.querySelector("textarea");
  const vechi = () => {
    camp.select();
    let reusit = false;
    try { reusit = document.execCommand("copy"); } catch (e) { /* browserul refuză */ }
    if (reusit) gata(); else spune("Textul e selectat: apăsați Ctrl+C, apoi îl puteți lipi într-un mesaj către persoana care v-a invitat.");
  };
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(gata, vechi); else vechi();
}
function arataFinal(g, adauga) {
  const dimensiuni = `${window.innerWidth}x${window.innerHeight}`;
  const text = ses.text_final({grup: LINK.grup || "-", ordine: ses.ordine[0] === "m1" ? 1 : 2, ecran: dimensiuni, incercarea: reluari() + 1});
  adauga("h1", ses.oprit ? "V-ați oprit. Vă mulțumim!" : "Gata. Vă mulțumim!");
  adauga("p", INVITAT ? "Mai jos e tot ce s-a notat. Până acum nu a plecat nimic de pe acest calculator."
    : "Aceasta a fost o probă deschisă: nimic nu se trimite, iar când închideți fila totul dispare. Mai jos e ce s-a notat.");
  const zona = document.createElement("div");
  zona.className = "butoane";
  g.appendChild(zona);
  const camp = document.createElement("textarea");
  camp.readOnly = true;
  camp.id = "text-final";
  camp.className = "text-final";
  camp.value = text;
  camp.setAttribute("aria-label", "Tot ce s-a notat");
  zona.appendChild(camp);
  if (INVITAT) {
    const adresa = adresaFormular(text);
    if (adresa.length <= LUNGIME_MAXIMA_LINK) {
      const t = legatura("Trimite răspunsurile", adresa, "principal");
      t.id = "trimite";
      t.addEventListener("click", () => { $("nota").textContent = "S-a deschis formularul Google, cu textul deja completat. Apăsați acolo „Trimite”, fără să schimbați textul, apoi puteți închide filele."; });
      zona.appendChild(t);
    }
    zona.appendChild(buton("Copiază textul", "secundar", () => copiaza(text, zona)));
  }
  const nota = adauga("p", "");
  nota.id = "nota";
  nota.setAttribute("role", "status");
  if (INVITAT) adauga("p", "Vă rugăm să nu schimbați nimic în text, nici în formular; puteți șterge doar ce ați scris liber, la „Ce a încurcat”. Codul de la sfârșit arată dacă textul a ajuns neschimbat. Tot în el se notează, fără să se scrie pe ecran, care răspunsuri se potriveau cu ce arăta aplicația; altceva nu conține.");
  if (INVITAT) adauga("p", "Dacă închideți fila fără să trimiteți, răspunsurile dispar.");
  adauga("p", "Semafoarele din aplicație erau simulate: nimic din ce ați apăsat nu a schimbat ceva pe stradă.");
  if (INVITAT) adauga("p", "Vă rugăm să nu discutați cu alți participanți la acest sondaj despre răspunsuri, ca rezultatele să fie cât mai apropiate de opinia dumneavoastră reală.");
  const din_nou = document.createElement("div");
  din_nou.className = "butoane";
  const reia = buton("Altă persoană vrea să încerce: de la capăt", "oprire", () => intrebaReluarea(din_nou, reia));
  din_nou.appendChild(reia);
  g.appendChild(din_nou);
  const l = adauga("p", "");
  l.appendChild(legatura("Despre proiect, pe GitHub", D.URL_PROIECT, "simplu"));
}
function arata() {
  const p = ses.pas();
  clearTimeout(indemn);
  const g = $("ghid");
  g.innerHTML = "";
  g.className = p.lung ? "lung" : "";       // textele lungi au literă mai mică, iar butonul rămâne la vedere
  const adauga = (tag, html) => { const e = document.createElement(tag); e.innerHTML = html; g.appendChild(e); return e; };
  if (!INVITAT) adauga("div", "Probă deschisă: nimic nu se trimite.").id = "cod";
  if (p.sarcina) adauga("div", `${p.runda ? "A doua variantă" : "Prima variantă"} · sarcina ${p.sarcina} din 4`).id = "progres";
  if (p.tip === "final") {
    if (rama()) inchide();
    arataFinal(g, adauga);
  } else {
    if (p.titlu) adauga("h1", fara(p.titlu));
    [...(p.text || []), ...((INVITAT ? p.text_invitat : p.text_deschis) || [])].forEach(t => adauga("p", aldin(loc(t))));
    if (p.id === "bun_venit" && TELEFON) adauga("p", aldin("**Pagina e făcută pentru un calculator.** Pe telefon se vede greu, dar puteți încerca."));
    const zona = document.createElement("div");
    zona.className = "butoane";
    g.appendChild(zona);
    if (p.link) zona.appendChild(legatura(p.link.text, p.link.adresa, "secundar"));
    if (p.tip === "info") zona.appendChild(buton(p.buton, "principal", () => raspunde()));
    else if (p.tip === "alegere") p.optiuni.forEach(o => zona.appendChild(buton(o, "", () => raspunde({valoare: o}))));
    else if (p.tip === "deschide") zona.appendChild(buton(p.buton, "principal", () => { deschide(p.versiune); raspunde(); }));
    else if (p.tip === "inchide") zona.appendChild(buton(p.buton, "principal", () => { inchide(); raspunde(); }));
    else if (p.tip === "sarcina") {
      zona.appendChild(buton("Am terminat", "principal", () => raspunde()));
      zona.appendChild(buton("Nu reușesc", "secundar", () => raspunde({nu_reuseste: true})));
      indemn = setTimeout(() => {
        const e = document.createElement("p");
        e.id = "indemn";
        e.textContent = "Dacă vi se pare greu, puteți apăsa „Nu reușesc”.";
        zona.after(e);
      }, INDEMN_DUPA);
    } else if (p.tip === "text") {
      const t = document.createElement("textarea");
      t.setAttribute("aria-label", p.titlu);
      t.maxLength = D.LUNGIME_TEXT;
      zona.appendChild(t);
      zona.appendChild(buton(p.buton, "principal", () => raspunde({valoare: t.value})));
    }
    const oprire = buton("Mă opresc aici", "oprire", () => intrebaOprirea(zona, oprire));
    g.appendChild(oprire);
    // Pagina reîncărcată: ecranul se redeschide dacă pasul îl cere; altfel rămâne închis.
    if (p.ecran) deschide(p.versiune); else if (p.tip !== "deschide" && rama()) inchide();
    pregatesteRama(p);
  }
  $("acoperit").classList.toggle("vizibil", !!p.acoperit);
  g.scrollTop = 0;
  blocat = true;
  setTimeout(() => { blocat = false; }, PAUZA_CLIC);
}

// Timpul în care fila nu se vede (o altă fereastră, un telefon) nu se socotește la sarcină; se notează separat.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    ascuns_de_la = secunde();
  } else if (ascuns_de_la !== null) {
    ses.adauga_timp_ascuns(secunde() - ascuns_de_la);
    ascuns_de_la = null;
    salveaza();
  }
});

$("acoperit").innerHTML = loc($("acoperit").innerHTML);
numaraReluarea();
ses = incarca();
salveaza();
arata();
