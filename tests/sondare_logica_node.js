// Rulează testele logicii sondării cu Node.js, fără browser, pe fișierele adevărate din docs/sondare; scrie rezultatul ca JSON.
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");

const radacina = path.join(__dirname, "..");
let rezultat = "";
const context = vm.createContext({document: {getElementById: () => ({set textContent(t) { rezultat = t; }})}});
for (const f of ["docs/sondare/date.js", "docs/sondare/logica.js", "tests/sondare_logica_teste.js"]) {
  vm.runInContext(fs.readFileSync(path.join(radacina, f), "utf8"), context, {filename: f});
}
process.stdout.write(rezultat);
