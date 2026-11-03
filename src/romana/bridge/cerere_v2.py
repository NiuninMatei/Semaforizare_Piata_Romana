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
    cfg["factor_extrapolare_pietoni"] = factori["factor_extrapolare_pietoni"]
    cfg["_factor_extrapolare_pietoni"] = factori["_factor_extrapolare_pietoni"]
    cfg["viraje_numarate"] = factori["viraje_numarate"]
    cfg["_viraje_numarate"] = factori["_viraje_numarate"]
    cfg["factor_pietoni_masurati"] = factori["factor_pietoni_masurati"]
    cfg["_factor_pietoni_masurati"] = factori["_factor_pietoni_masurati"]
    cfg["cote_fixe"] = {"catargiu": {"dacia_vest": 0.04},
                        "dacia_est": {"catargiu": 0.4, "caderea_bastiliei": 0.07, "dacia_vest": 0.305, "magheru": 0.125, "mendeleev": 0.085, "dacia_est": 0.015}}
    cfg["_cote_fixe"] = ('Două cote se fixează, fiindcă traiectoriile rupte le arată greșit (§ 4.3); amândouă sunt numărate direct, pe felii, de doi adnotatori, pe clipurile din 1.11 și 2.11. Catargiu → Dacia vest: drumul de sus duce ≈31% din Catargiu, ca flux, în etapa N–S (IC90 27–35%), dar cea mai mare parte continuă pe inel. Pe banda ieșirii spre Dacia vest trec, în etapa N–S, 23,5 vehicule la 616 intrări de pe Catargiu, pe 8 clipuri: 3,8% (IC90 pe clipuri 2,2–6,0%), sau 5,6% cu primele 15 s ale etapei, când ies și vehiculele rămase pe inel. O numărare separată, pe 11 clipuri, a dat 3,2% (2,3–4,4%). Se ia 0,04, iar rezultatele se dau și cu 0,08. Dacia est → Catargiu: pe 13 valuri complete, ieșirile spre Catargiu din etapa E–V sunt 0,43 din intrările de pe Dacia est din același val (IC90 pe valuri 0,30–0,61; duminică 0,56, luni 0,31). Prima numărare, pe 10 valuri, dăduse 0,39–0,50, deci rămâne 0,40, aceeași în toate zilele: diferența dintre zile e în zgomotul dintre valuri. Raportul dintre inel și Dacia est nu e o cotă, fiindcă pe inel trece și stocul de pe Magheru. Pe banda ieșirii spre Dacia vest, în afara etapei N–S, trec 0,44 din intrările de pe Dacia est (IC90 0,40–0,49), dar acolo ies și vehicule de pe inel, deci e doar o margine de sus pentru Dacia est → Dacia vest, 0,305 în cerere. Căderea Bastiliei, 0,07, și celelalte destinații rămân distribuția a priori, rescalată: ipoteză declarată. Mendeleev are 0,085, fiindcă pe 25.10, la vârf, traiectoriile complete spre el sunt mai multe decât ar da 0,07. Ce nu intră în cerere, limite declarate: Magheru → inel, ≈6–7% în cameră față de 1,0–2,6% în cerere, se dă doar ca variantă, cu 3,5% (§ 6.5); Catargiu → Magheru pe drumul de sus nu are rută, fiindcă routeSampler o ignoră, iar forțată, pierderea de timp pe brațul Catargiu crește cu 110–160%.')
    cfg["cote_timp_real"] = {"magheru": {"dacia_est": 0.14}}
    cfg["_cote_timp_real"] = 'Doar în geamănul în timp real, unde nu există traiectorii numărate pe viraj: cota Magheru → Dacia est, media din scenariile măsurii noi, ponderată cu Magheru, 0,14 (pe ore, 0,10–0,21). Direct, pe clipurile din 2.11, adnotatorii văd 0,18 (IC90 0,14–0,24), deci cota de aici poate fi mică. Debitele de acolo rămân cele brute, de pe zonele vechi, deci factorii de mai sus nu li se aplică (§ 5.5).'
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
    cfg["_pietoni_pe_treceri"] = "Trotuarele dintre care traversează pietonii, pe fiecare braț cu trecere comandată de semafor. Fiecare agent traversează o singură dată, pe un braț; pe Dacia est, Magheru și Catargiu, o persoană trece ambele zebre, iar pe Dacia vest, una (§ 9.11). Programul de pe celelalte treceri e prin analogie."
    return cfg


def main() -> None:
    cfg = cerere(load_json("demand.json"), load_json("factori_v2.json"))
    (CONFIG_DIR / "demand_v2.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("[OK] config/demand_v2.json", cfg["factor_corectie_detectie"], cfg["factor_pietoni_masurati"])


if __name__ == "__main__":
    main()
