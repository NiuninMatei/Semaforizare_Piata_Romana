"""Cererea măsurii noi (§ 9.11): `config/demand_v2.json`, scris din `config/demand.json`, care rămâne neatins, și din factorii din `config/factori_v2.json`.

Ca să se poată reface din depozit: fișierul generat și generatorul se schimbă împreună, iar explicațiile fiecărei valori stau lângă ea.

Rulare:  python -m romana.bridge.cerere_v2
"""
from __future__ import annotations

import json

from romana.common import CONFIG_DIR, load_json


def cerere(baza: dict, factori: dict) -> dict:
    cfg = dict(baza)
    cfg["factor_corectie_detectie"] = factori["factor_corectie_detectie"]
    cfg["_factor_corectie_detectie"] = ("Măsura nouă (§ 9.11): referință / numărătoarea automată pe zonele din camera_v2.json, pe clipuri de zi și de noapte. Referința, pe foi de contact și felii "
                                        "timp-spațiu; la Lascăr Catargiu, fără inelul dinspre est. Un braț poate avea un factor pentru zi și altul pentru întuneric (după înălțimea Soarelui). Sursa valorilor: config/factori_v2.json.")
    cfg["factor_extrapolare_pietoni"] = 3.0
    cfg["_factor_extrapolare_pietoni"] = "Măsura nouă numără pietonii pe persoane, nu pe zone: 2,5 pe zone înseamnă ≈3,0 pe persoane (raport zone/persoane 1,218 pe 29.10). Rămâne o ipoteză (§ 9.11); ≈30% din pierderea de la vârf vine din acești pietoni neobservați."
    cfg["viraje_numarate"] = {"magheru": {"dacia_est": 1.1}}
    cfg["_viraje_numarate"] = ("Viraje pe care camera le vede aproape pe toate, în prim-plan: se iau din numărul lor, cu factorul dat, nu din proporții. Magheru → Dacia est: 348 de traiectorii complete pe 26.10, 14:30–15:30, și ≈370–390 de vehicule "
                               "la ieșirea Dacia est în timpul etapei N–S. Din proporții ar fi ieșit 672 de vehicule pe oră, fiindcă traiectoriile spre Catargiu, îndepărtat, ajung mult mai rar complete (§ 4.3).")
    cfg["factor_pietoni_masurati"] = factori["factor_pietoni_masurati"]
    cfg["_factor_pietoni_masurati"] = factori["_factor_pietoni_masurati"]
    cfg["cote_fixe"] = {"catargiu": {"dacia_vest": 0.20},
                        "dacia_est": {"dacia_vest": 0.57, "magheru": 0.20, "catargiu": 0.03, "mendeleev": 0.08, "caderea_bastiliei": 0.09, "dacia_est": 0.03}}
    cfg["_cote_fixe"] = ("Cote pe care traiectoriile nu le pot arăta. Drumul de sus duce ≈26% din Catargiu, ca flux, pe clipurile din 1.11 (provizoriu: trei clipuri de duminică); pe el merg și Catargiu → Dacia est, Mendeleev și Căderea Bastiliei, "
                         "deci spre Dacia vest rămân ≈20%. Dacia est: vehiculele numărate pe inelul dinspre est, în aval de ieșirea Catargiu, sunt cam tot atâtea câte intră dinspre Dacia est (29,5/28,5; 38/34; 26/24 pe clipuri), "
                         "deci aproape nimeni nu iese spre Catargiu, deși traiectoriile rupte par să arate altceva; restul destinațiilor sunt distribuția a priori, ipoteză declarată. O–D spre Dacia vest și Mendeleev vine deci din Furness și din a priori, nu din cameră.")
    cfg["cote_timp_real"] = {"magheru": {"dacia_est": 0.14}}
    cfg["_cote_timp_real"] = "Doar în geamănul în timp real, unde nu există traiectorii numărate pe viraj: cota Magheru → Dacia est, în scenarii 9–18%. Debitele de acolo rămân cele brute, de pe zonele vechi, deci factorii de mai sus nu li se aplică (§ 5.5)."
    cfg["rute_pe_brate"] = {"fisier": "candidate_brate.rou.xml",
                            "porniri": {"magheru": "119241030#1", "catargiu": "244658427#1", "dacia_est": "232079775#1", "dacia_vest": "-1486385191#0"},
                            "capete": {"magheru": "44499684#3", "catargiu": "4045775#0", "dacia_est": "669156737#0", "dacia_vest": "1486385191#0", "mendeleev": "125445934#2", "caderea_bastiliei": "119238385#2"},
                            "prin": {"magheru>dacia_est": "448266581#1 778823270 119238380#0 119238380#1"}}
    cfg["_rute_pe_brate"] = ("Rutele pornesc de pe bulevardul fiecărui braț și se termină pe bulevardul de ieșire, câte una pe pereche intrare–ieșire, nu de oriunde din rețea: intrările la 148–566 m de linia de oprire, ieșirile la 130–346 m. Camera nu vede ce e dincolo de piață. "
                             "Ruta de pe Magheru trece prin două semafoare reale, cu program presupus (≈8% din pierderea de la vârf); cu rutele vechi, capacitatea lor limita traficul din piață (§ 6.4, § 9.11).")
    cfg["retea"] = "romana_v2.net.xml"
    cfg["tipuri_vehicule"] = "vtypes_v2.add.xml"
    cfg["optiuni_sumo"] = {"pedestrian.striping.stripe-width": 0.3, "pedestrian.striping.jamtime": 60, "pedestrian.striping.jamtime.narrow": 60, "pedestrian.striping.jamtime.crossing": 5, "pedestrian.striping.jamfactor": 1}
    cfg["_optiuni_sumo"] = ("Modelul de pietoni din SUMO îi ține pe zebră și pe insulele înguste mult mai mult decât se vede în cameră, cu vehiculele așteptând la verde; timpul pe zebră respinge opțiunile implicite (zebra 55, mediană/p90: implicite 8/41 s, alese 5/7 s, cameră 4,8/13,1 s). "
                            "Doar lățimea benzii, 0,3 m, stă pe debit: cu 0,64 m, Magheru scade cu 18%. Peste ≈60 s de blocaj, un pieton intră pe roșu fără să aleagă un gol: de aici ≈5–7% intrări pe roșu, care nu sunt o dovadă de realism; tot ele produc frânările de urgență.")
    cfg["_retea"] = "Geamănul corectat (§ 6.5): se construiește cu romana.network.retea_v2, din config/retea_v2.json."
    cfg["pietoni_pe_treceri"] = {"dacia_est": ["232079775#2", "119238380#1"], "magheru": ["668307642#1", "44499684#2"], "catargiu": ["1320256482", "668307633#2"], "dacia_vest": ["-778823268#2", "778823268#2"]}
    cfg["_pietoni_pe_treceri"] = "Trotuarele dintre care traversează pietonii, pe fiecare braț cu trecere comandată de semafor. Fiecare pieton traversează o singură dată; pe Dacia est, o persoană trece ambele zebre (§ 9.11). Programul de pe celelalte treceri e prin analogie."
    return cfg


def main() -> None:
    cfg = cerere(load_json("demand.json"), load_json("factori_v2.json"))
    (CONFIG_DIR / "demand_v2.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("[OK] config/demand_v2.json", cfg["factor_corectie_detectie"], cfg["factor_pietoni_masurati"])


if __name__ == "__main__":
    main()
