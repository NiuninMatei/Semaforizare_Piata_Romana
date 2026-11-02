// Testele logicii sondării. Le rulează Node (sondare_logica_node.js) sau, dacă lipsește, un browser (sondare_logica.html).
"use strict";
const D = DATE_SONDARE;
class Ceas {
  constructor() { this.t = 1000000; this.f = () => this.t; }
  mergi(d) { this.t += d; }
}
const esuate = [];
let trecute = 0;
function verifica(nume, cond, detaliu) {
  if (cond) trecute += 1; else esuate.push(nume + (detaliu === undefined ? "" : ": " + JSON.stringify(detaliu)));
}
const egal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const NUME_BRAT = {magheru: "Magheru", catargiu: "Lascăr Catargiu", dacia_est: "Dacia est", dacia_vest: "Dacia vest"};

// Un participant până la pasul `pana_la`: alege primul răspuns sau pe cel din `raspuns`; `comenzi` = {id pas: listă de comenzi}.
function parcurge(s, ceas, {comenzi = {}, nu_reuseste = [], raspuns = {}, pana_la = "final"} = {}) {
  while (s.pas().id !== pana_la && s.pas().tip !== "final") {
    const p = s.pas();
    ceas.mergi(5);
    for (const [mod, faza] of comenzi[p.id] || []) {
      s.clic(mod);
      s.comanda(mod, faza);
      ceas.mergi(12);
    }
    const v = p.tip === "alegere" ? (raspuns[p.id] || p.optiuni[0]) : p.tip === "text" ? (raspuns[p.id] || "") : undefined;
    s.raspunde(v, nu_reuseste.includes(p.id), p.id);
  }
  return s.pas();
}
const nou = (ordine = ["m1", "m2"]) => { const c = new Ceas(); return [new Sesiune(D, ordine, c.f), c]; };
const linie = (s, id) => s.linii.find(r => r.id === id);
const VERDE = {r1_verde: [["manual", 1]], r1_automat: [["program"]]};

// ------------------------------------------------------------- situația simulată
{
  const c = new Ceas(), b = new Banc(D, c.f);
  for (const runda of [0, 1]) {
    b.seteaza({runda});
    const nume = Object.keys(NUME_BRAT).reduce((x, y) => (D.COZI[runda][x] >= D.COZI[runda][y] ? x : y));
    let bine = true;
    for (let i = 0; i < 200; i++) {
      c.mergi(1.7);
      const q = b.cozi();
      const lung = Object.keys(NUME_BRAT).reduce((x, y) => (q[x] >= q[y] ? x : y));
      if (lung !== nume) bine = false;
    }
    verifica("cea mai lungă coadă rămâne aceeași, runda " + runda, bine);
  }
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  b.seteaza({mod: "program", nemiscat: true});
  c.mergi(2);
  b.comanda("manual", 1);
  const etape = [];
  for (let i = 0; i < 12; i++) { etape.push(b.faza().slice(0, 2).join()); c.mergi(1); }
  verifica("faza veche rămâne întâi", etape[0] === "0,green", etape);
  verifica("galben, ca în geamăn", etape.includes("0,yellow"), etape);
  verifica("roșu, ca în geamăn", etape.includes("0,red"), etape);
  verifica("apoi faza nouă", etape[11] === "1,green", etape);
  const k = etape.indexOf("1,green");
  verifica("reacția durează 5–10 s", k >= 5 && k < 11, etape);
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  verifica("planul începe pe N–S", egal(b.faza().slice(0, 2), [0, "green"]));
  b.comanda("manual", 1);
  c.mergi(9.9);
  verifica("verdele minim se respectă", egal(b.faza().slice(0, 2), [0, "green"]), b.faza());
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  c.mergi(2);
  b.comanda("manual", 0);
  verifica("trecerea pe manual păstrează faza verde", egal(b.faza().slice(0, 2), [0, "green"]) && b.mod === "manual");
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  b.seteaza({mod: "manual", faza: 1});
  c.mergi(5);
  b.comanda("program", null);
  verifica("planul continuă din faza curentă", b.faza()[0] === 1, b.faza());
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  b.seteaza({mod: "program", nemiscat: true});
  let bine = true;
  for (let i = 0; i < 240; i++) { c.mergi(1); if (b.faza()[0] !== 0) bine = false; }
  verifica("nemișcat, Dacia nu devine verde singură", bine);
}
{
  const c = new Ceas(), b = new Banc(D, c.f);
  c.mergi(40);
  const st = b.stare();
  for (const k of ["mod", "mod_program", "faza", "faza_nume", "etapa", "verde_s", "faze", "model_ai", "coada_brate", "vehicule_in_retea", "pietoni_in_retea", "sursa", "istoric_coada", "_varsta_s"]) verifica("câmpul simulării " + k, k in st.simulare);
  for (const k of ["conectat", "fps", "vehicule_urmarite", "intrari_veh_h", "iesiri_veh_h", "pietoni_h", "secunde_interval", "_varsta_s"]) verifica("câmpul camerei " + k, k in st.camera);
  verifica("șase faze", st.simulare.faze.length === 6);
  verifica("starea e mereu proaspătă", st.camera._varsta_s < 15 && st.simulare._varsta_s < 10);
}

// ------------------------------------------------------------- parcursul unei persoane
{
  const [s, c] = nou();
  const id = s.pas().id;
  s.raspunde(undefined, false, id);
  const al_doilea = s.pas().id;
  s.raspunde(undefined, false, id);
  verifica("răspunsul pentru alt pas nu sare", s.pas().id === al_doilea && al_doilea !== id);
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "profil_calculator"});
  s.raspunde("Un nume, 74 de ani", false, "profil_calculator");
  verifica("valoarea din afara opțiunilor se ignoră", s.pas().id === "profil_calculator" && !JSON.stringify(s.linii).includes("74"));
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_incurcat"});
  s.raspunde("un  doi\n\ntrei " + "x".repeat(2000), false, "r1_incurcat");
  const v = linie(s, "r1_incurcat").valoare;
  verifica("textul stă pe un rând și e tăiat", v.startsWith("un doi trei x") && v.length <= D.LUNGIME_TEXT, v.length);
}
{
  const [s, c] = nou();
  parcurge(s, c, {comenzi: {r1_verde: [["manual", 0], ["manual", 1]], r1_automat: [["program"]]}});
  verifica("verde reușit", linie(s, "r1_verde").reusit === true && linie(s, "r1_verde").comenzi === 2 && linie(s, "r1_verde").clicuri === 2);
  verifica("înapoi la calculator, reușit", linie(s, "r1_automat").reusit === true);
}
for (const [faza, asteptat] of [[3, true], [4, true], [2, false], [0, false]]) {
  const [s, c] = nou();
  parcurge(s, c, {comenzi: {r1_verde: [["manual", faza]]}, pana_la: "r1_verde_r"});
  verifica("verde pe Dacia cu faza " + faza, s.banc.verde_pe_dacia() === asteptat);
}
{
  const [s, c] = nou();
  parcurge(s, c, {comenzi: {r1_verde: [["manual", 1]]}, nu_reuseste: ["r1_verde"]});
  verifica("„Nu reușesc” rămâne nereușit", linie(s, "r1_verde").reusit === false && linie(s, "r1_verde").nu_reuseste === true);
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_automat"});
  verifica("sarcina de revenire pornește din manual și dacă verdele a eșuat", s.banc.mod === "manual" && s.banc.verde_pe_dacia());
  parcurge(s, c, {pana_la: "r1_automat_vazut"});
  verifica("fără comandă, revenirea nu e reușită", linie(s, "r1_automat").reusit === false);
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_conduce"});
  s.comanda("manual", 0);
  s.raspunde(undefined, false, "r1_conduce");
  s.raspunde(D.ALEGE_CONDUCE.om, false, "r1_conduce_r");
  verifica("cine conduce se notează după ce arată ecranul", linie(s, "r1_conduce_r").corect === true);
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r2_conduce"});
  verifica("a doua rundă începe cu un om", s.banc.stare().simulare.mod === "manual");
}
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_conduce"});
  s.comanda("manual", 1);
  parcurge(s, c, {pana_la: "r1_verde"});
  const st = s.banc.stare().simulare;
  verifica("situația e refăcută la sarcina de verde", st.mod === "program" && st.faza === 0, st.faza);
}
{
  const [s, c] = nou();
  verifica("comenzile din afara sarcinilor nu schimbă nimic", s.comanda("manual", 1).ok === true && s.banc.mod === "program");
}
{
  const [s] = nou(["m2", "m1"]);
  const v = {};
  s.pasi.forEach(p => { if (p.runda !== undefined) v[p.runda] = p.versiune; });
  verifica("ordinea din link schimbă versiunile", v[0] === "m2" && v[1] === "m1");
}
// ------------------------------------------------------------- reluarea, după o pagină reîncărcată
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_verde"});
  s.clic("Manual");
  s.comanda("manual", 1);
  c.mergi(20);
  const d = new Sesiune(D, s.ordine, c.f, JSON.parse(JSON.stringify(s.salvare())));
  verifica("reluarea continuă de la același pas", d.pas().id === "r1_verde" && d.banc.verde_pe_dacia());
  d.raspunde(undefined, false, "r1_verde");
  const r = linie(d, "r1_verde");
  verifica("reluarea păstrează apăsările și comenzile", r.reusit === true && r.clicuri === 1 && r.comenzi === 1);
}
{
  const [s, c] = nou();
  parcurge(s, c, {comenzi: {r1_verde: [["manual", 1]]}, pana_la: "r1_verde_r"});
  const d = new Sesiune(D, s.ordine, c.f, JSON.parse(JSON.stringify(s.salvare())));
  c.mergi(300);
  d.raspunde("Roșu", false, "r1_verde_r");
  verifica("adevărul notat rămâne după reluare", linie(d, "r1_verde_r").corect === true);
}
// ------------------------------------------------------------- oprirea și textul de la final
{
  const [s, c] = nou();
  parcurge(s, c, {pana_la: "r1_verde"});
  s.renunta();
  verifica("oprirea duce la final", s.pas().tip === "final");
  const t = s.text_final({grup: "a", ordine: 1, ecran: "1500x900"});
  verifica("textul spune unde s-a oprit", t.includes("oprit la r1_verde"), t);
}
const TIPAR = {comenzi: {...VERDE, r2_verde: [["manual", 3]], r2_automat: [["fix"]]}, nu_reuseste: ["r2_coada"],
  raspuns: {r1_conduce_r: D.ALEGE_CONDUCE.om, r1_coada_r: "Dacia vest", r1_verde_r: "Roșu", r1_real: "Da", r1_usor: "Ușor", r1_incurcat: "butonul: unde era?",
            r2_coada_r: "Dacia est", r2_usor: "Foarte greu", preferinta: "A doua", ajutor: "Da, la înțelegerea sarcinilor", profil_calculator: "Rar sau deloc"}};
const texte = [];
for (const [ordine, nr] of [[["m1", "m2"], 1], [["m2", "m1"], 2]]) {
  const [s, c] = nou(ordine);
  const p = parcurge(s, c, TIPAR);
  verifica("parcursul ajunge la final, ordinea " + nr, p.tip === "final");
  texte.push(s.text_final({grup: "a", ordine: nr, ecran: "1536x730"}));
}
document.getElementById("rezultat").textContent = JSON.stringify({trecute, esuate, texte});
