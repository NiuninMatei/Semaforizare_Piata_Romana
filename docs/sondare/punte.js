// Legătura dispeceratului din ramă cu situația simulată din pagina sondării: aceleași adrese ca serverul adevărat,
// ca ecranul să rămână neschimbat, dar nimic nu pleacă în rețea (regula de securitate a paginii oprește oricum orice cerere).
"use strict";
if (window.parent === window) location.replace("./");
window.fetch = async (adresa, optiuni) => {
  const r = window.parent.SONDARE.api(String(adresa), optiuni);
  return {ok: r.status < 400, status: r.status, json: async () => r.corp};
};
