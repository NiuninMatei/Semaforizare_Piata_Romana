// Logica sondării, fără pagină: situația simulată a dispeceratului (Banc) și parcursul unei persoane (Sesiune).
// Totul rulează în browserul persoanei și nu trimite nimic. Datele și pașii vin din date.js, scris de
// `romana.dashboard.sondare --pachet`; „D” de mai jos este obiectul DATE_SONDARE.
"use strict";

const secunde = () => Date.now() / 1000;
const rotunjit = x => Math.round(x * 100) / 100;

// Aceleași câmpuri ca outputs/live/state.json și sim_state.json. Reacția la o comandă e ca în geamăn: faza veche rămâne
// până la pasul de citire a comenzii (5 s), apoi galben 3 s și roșu 2 s, iar faza nouă vine abia după ele. Fiindcă planul
// stă pe faza N–S cu verdele minim deja atins la sarcina de verde, aici reacția durează 5–10 s; în geamănul adevărat
// poate ajunge la ≈24 s (§ 8).
class Banc {
  constructor(D, ceas = secunde, salvat = null) {
    this.D = D;
    this.ceas = ceas;
    const t = ceas();
    this.t0 = this.t_plan = t;
    this.runda = 0;
    this.mod = "program";
    this.faza_manual = 0;
    this.t_manual = t - 30;      // când a început verdele fazei manuale
    this.tranzitie = null;       // [faza veche, verdele ei la cerere, momentul cererii, începutul galbenului]
    this.nemiscat = false;       // planul stă pe N–S: faza Dacia nu vine singură cât se cere verde pe Dacia
    this.t_nemiscat = t;
    if (salvat) Object.assign(this, salvat);
  }

  salvare() {
    const {t0, t_plan, runda, mod, faza_manual, t_manual, tranzitie, nemiscat, t_nemiscat} = this;
    return {t0, t_plan, runda, mod, faza_manual, t_manual, tranzitie, nemiscat, t_nemiscat};
  }

  // Pune direct situația cerută de un pas, fără tranziție.
  seteaza({runda, mod, faza, nemiscat = false} = {}) {
    const acum = this.ceas();
    if (runda !== undefined) this.runda = runda;
    if (mod !== undefined) {
      this.mod = mod;
      this.tranzitie = null;
      this.nemiscat = nemiscat;
      this.t_nemiscat = acum;
      if (mod === "manual") {
        this.faza_manual = faza === undefined || faza === null ? 0 : faza;
        this.t_manual = acum - 30;
      }
    }
  }

  // Comanda unui participant; faza verde curentă rămâne, iar o fază nouă vine după galben și roșu.
  comanda(mod, faza) {
    const D = this.D, acum = this.ceas();
    const [f, etapa, verde] = this.faza();
    if (mod === "manual") {
      const noua = faza === undefined || faza === null ? f : Math.trunc(faza);
      if (this.mod === "manual" && this.tranzitie && acum < this.t_manual) {
        this.faza_manual = noua;            // o tranziție e în curs: doar ținta se schimbă
      } else if (noua === f && etapa === "green") {
        this.faza_manual = f;
        this.t_manual = acum - verde;
        this.tranzitie = null;
      } else if (!(this.mod === "manual" && noua === this.faza_manual)) {
        const citire = acum + Math.max(D.VERDE_MIN - verde, 0);
        const t_g = this.t0 + Math.ceil((citire - this.t0) / D.PAS_COMANDA) * D.PAS_COMANDA;
        this.tranzitie = [f, verde, acum, t_g];
        this.faza_manual = noua;
        this.t_manual = t_g + D.GALBEN + D.ROSU;
      }
    } else {
      if (this.mod === "manual" || this.nemiscat) {   // planul continuă din faza curentă, nu sare
        let decalaj = 0, gasit = false;
        for (const [g, v] of D.PLAN) {
          if (g === f) {
            this.t_plan = acum - decalaj - Math.min(verde, v - 1);
            gasit = true;
            break;
          }
          decalaj += v + D.GALBEN + D.ROSU;
        }
        if (!gasit) this.t_plan = acum;
      }
      this.tranzitie = null;
    }
    this.nemiscat = false;
    this.mod = mod;
    return {ok: true, mod, timestamp: acum, ...(mod === "manual" ? {faza: this.faza_manual} : {})};
  }

  // [faza, etapa, verde_s]: ca în geamăn, verde_s rămâne cât a ținut verdele și în galben și în roșu.
  faza(acum = this.ceas()) {
    const D = this.D;
    if (this.mod === "manual") {
      if (this.tranzitie && acum < this.t_manual) {
        const [f, v, t_cerere, t_g] = this.tranzitie;
        if (acum < t_g) return [f, "green", v + Math.trunc(acum - t_cerere)];
        return [f, acum < t_g + D.GALBEN ? "yellow" : "red", v + Math.trunc(t_g - t_cerere)];
      }
      return [this.faza_manual, "green", Math.trunc(acum - this.t_manual)];
    }
    if (this.nemiscat) return [0, "green", D.VERDE_MIN + Math.trunc(acum - this.t_nemiscat)];
    const ciclu = D.PLAN.reduce((s, [, v]) => s + v + D.GALBEN + D.ROSU, 0);
    let t = (((acum - this.t_plan) % ciclu) + ciclu) % ciclu;
    for (const [f, v] of D.PLAN) {
      if (t < v) return [f, "green", Math.trunc(t)];
      if (t < v + D.GALBEN) return [f, "yellow", v];
      if (t < v + D.GALBEN + D.ROSU) return [f, "red", v];
      t -= v + D.GALBEN + D.ROSU;
    }
    return [0, "green", 0];
  }

  // Cozile rundei, cu o mișcare mică; cea mai lungă rămâne aceeași.
  cozi() {
    const faza_timp = (this.ceas() - this.t0) / 6, rez = {};
    Object.entries(this.D.COZI[this.runda]).forEach(([b, q], i) => {
      rez[b] = Math.max(0, Math.round(q + 1.2 * Math.sin(faza_timp + i)));
    });
    return rez;
  }

  stare() {
    const D = this.D, acum = this.ceas();
    const [faza, etapa, verde] = this.faza();
    const cozi = this.cozi();
    const total = Object.entries(cozi).reduce((s, [k, v]) => s + (k === "pietoni" ? 0 : v), 0);
    const t = Math.trunc(acum - this.t0);
    const istoric = [];
    for (let i = 0; i < 120; i++) istoric.push([t - 600 + 5 * i, Math.max(0, Math.trunc(total + 6 * Math.sin(i / 9) + 3 * Math.sin(i / 2.3)))]);
    const intrari = D.INTRARI[this.runda];
    const simulare = {timestamp: acum, timp_sim: t, mod: this.mod, mod_program: this.mod === "program" ? "plan_scurt" : null,
      sursa: "camera live", faza, faza_nume: D.FAZE[faza], etapa, verde_s: verde, faze: D.FAZE, model_ai: true,
      coada_brate: cozi, coada_total: total, vehicule_in_retea: 90 + total, vehicule_injectate: 412, pietoni_in_retea: 31,
      pietoni_injectati: 140, debite_folosite: intrari, debit_echilibrat_veh_h: 2800, pietoni_h_folositi: 620,
      istoric_coada: istoric, _varsta_s: 0.4};
    const camera = {timestamp: acum, fps: 5.9, conectat: true, reconectari: 0, vehicule_urmarite: 64,
      intrari_veh_h: intrari, iesiri_veh_h: D.IESIRI, pietoni_h: {dacia_est: 620}, secunde_interval: 480, _varsta_s: 0.4};
    return {camera, simulare, comanda: {mod: this.mod, timestamp: acum}, ora_server: acum};
  }

  verde_pe_dacia() { return this.mod === "manual" && this.D.VERDE_PE_DACIA.includes(this.faza_manual); }

  e_automat() { return this.D.AUTOMATE.includes(this.mod); }

  culoare_magheru(acum) {
    const [faza, etapa] = this.faza(acum);
    if (!this.D.VERDE_PE_MAGHERU.includes(faza)) return "Roșu";
    return {green: "Verde", yellow: "Galben", red: "Roșu"}[etapa];
  }

  // Răspunsurile corecte în clipa acoperirii ecranului; pagina se actualizează o dată pe secundă, deci contează și ce era cu puțin înainte.
  adevar(ce) {
    const acum = this.ceas();
    if (ce === "conduce") return [this.D.ALEGE_CONDUCE[this.e_automat() ? "calculator" : "om"]];
    return [...new Set([this.culoare_magheru(acum), this.culoare_magheru(acum - 1.5)])].sort();
  }
}

// O persoană: pașii, poziția și ce s-a notat. Toate rămân în memorie și în sessionStorage, până când persoana apasă „Trimite”.
class Sesiune {
  constructor(D, ordine, ceas = secunde, salvat = null) {
    this.D = D;
    this.ordine = ordine;
    this.ceas = ceas;
    this.pasi = D.PASI.map(p => (p.runda === undefined ? p : {...p, versiune: ordine[p.runda]}));
    this.banc = new Banc(D, ceas, salvat && salvat.banc);
    this.poz = 0;
    this.linii = [];
    this.oprit = null;
    if (salvat) {
      for (const k of ["poz", "linii", "oprit", "t_pas", "clicuri", "traseu", "comenzi", "ascuns_s", "corect_calculat"]) this[k] = salvat[k];
    } else {
      this.intra();
    }
  }

  salvare() {
    const {ordine, poz, linii, oprit, t_pas, clicuri, traseu, comenzi, ascuns_s, corect_calculat} = this;
    return {ordine, poz, linii, oprit, t_pas, clicuri, traseu, comenzi, ascuns_s, corect_calculat, banc: this.banc.salvare()};
  }

  pas() { return this.pasi[this.poz]; }

  // Pregătește dispeceratul pentru pasul curent, indiferent ce a făcut participantul înainte.
  intra() {
    const p = this.pas();
    this.t_pas = this.ceas();
    this.clicuri = 0;
    this.traseu = [];
    this.comenzi = [];
    this.ascuns_s = 0;
    this.corect_calculat = p.corect_din_banc ? this.banc.adevar(p.corect_din_banc) : null;   // adevărul din clipa în care ecranul s-a acoperit
    if (p.sit) this.banc.seteaza(p.sit);
    if (p.pregateste === "manual_dacia" && !this.banc.verde_pe_dacia()) {
      this.banc.seteaza({mod: "manual", faza: this.D.VERDE_PE_DACIA[0]});   // sarcina de dinainte n-a reușit: începem de unde ar fi ajuns
    }
  }

  // Înregistrează pasul curent și trece la următorul; un răspuns pentru alt pas sau cu altă valoare decât opțiunile se ignoră.
  raspunde(valoare, nu_reuseste = false, id_pas = null) {
    const p = this.pas();
    if (p.tip === "final" || (id_pas !== null && id_pas !== p.id)) return;
    if (p.tip === "alegere" && !p.optiuni.includes(valoare)) return;
    if (p.tip === "text") valoare = String(valoare === undefined || valoare === null ? "" : valoare).slice(0, this.D.LUNGIME_TEXT).replace(/\s+/g, " ").trim();
    const r = {id: p.id, tip_pas: p.tip, durata_s: rotunjit(this.ceas() - this.t_pas)};
    if (p.tip === "alegere" || p.tip === "text") r.valoare = valoare;
    if ("corect" in p) {
      r.corect = valoare === p.corect;
      r.asteptat = p.corect;
    }
    if (p.corect_din_banc) {
      r.corect = this.corect_calculat.includes(valoare);
      r.asteptat = this.corect_calculat.join(" sau ");
    }
    if (p.tip === "sarcina") {
      Object.assign(r, {clicuri: this.clicuri, traseu: this.traseu, comenzi: this.comenzi.length, nu_reuseste: !!nu_reuseste, ascuns_s: Math.round(this.ascuns_s)});
      if (p.verifica === "verde") r.reusit = this.banc.verde_pe_dacia() && !nu_reuseste;
      if (p.verifica === "automat") r.reusit = this.banc.e_automat() && !nu_reuseste;
    }
    this.linii.push(r);
    this.poz += 1;
    this.intra();
  }

  clic(eticheta) {
    this.clicuri += 1;
    this.traseu.push(String(eticheta).trim().split(":")[0].slice(0, 22));
  }

  // Comenzile contează doar în timpul sarcinilor; în rest, ecranul e acoperit sau închis.
  comanda(mod, faza) {
    if (this.pas().tip !== "sarcina") return {ok: true, mod, timestamp: this.ceas()};
    const r = this.banc.comanda(mod, faza);
    this.comenzi.push([mod, faza === undefined ? null : faza]);
    return r;
  }

  // Participantul se oprește: ajunge direct la final, unde vede ce s-a notat și decide singur dacă trimite.
  renunta() {
    if (this.pas().tip === "final") return;
    this.oprit = this.pas().id;
    this.poz = this.pasi.findIndex(p => p.tip === "final");
    this.intra();
  }

  adauga_timp_ascuns(s) { this.ascuns_s += s; }

  // Tot ce s-a notat, ca text pe care persoana îl citește și îl trimite ea, dacă vrea. `citeste_raspuns` din sondare.py îl citește înapoi.
  text_final({grup = "-", ordine = "-", ecran = "-"} = {}) {
    const L = [`Sondare dispecerat Piața Romană, ${this.D.VERSIUNE}`,
      `Grup ${grup}, ordine ${ordine}, ecran ${ecran}, ${this.oprit ? "oprit la " + this.oprit : "terminat"}`];
    let runda = null;
    for (const r of this.linii) {
      const p = this.pasi.find(x => x.id === r.id);
      if (!p.eticheta || (r.tip_pas === "text" && !r.valoare)) continue;
      const a_runda = p.runda === undefined ? null : p.runda;
      if (a_runda !== runda) {
        L.push("");
        if (a_runda !== null) L.push(a_runda ? "A doua variantă" : "Prima variantă");
        runda = a_runda;
      }
      if (r.tip_pas === "sarcina") {
        let l = `${p.eticheta}: ${Math.round(r.durata_s)} s, apăsări ${r.clicuri}, comenzi ${r.comenzi}`;
        if (r.ascuns_s) l += `, altă fereastră ${r.ascuns_s} s`;
        if (r.nu_reuseste) l += ", nu reușesc";
        if ("reusit" in r) l += r.reusit ? ", reușit" : ", nereușit";
        if (p.verifica && r.traseu.length) l += ". " + r.traseu.join(" > ");
        L.push(l);
      } else {
        L.push(`${p.eticheta}: ${r.valoare}` + (r.corect === false ? ` (așteptat: ${r.asteptat})` : ""));
      }
    }
    return L.join("\n");
  }
}
