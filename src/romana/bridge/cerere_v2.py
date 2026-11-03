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
    cfg["_cote_fixe"] = ('Două cote se numără direct și se fixează, fiindcă traiectoriile rupte le arată greșit (§ 4.3), iar odată cu ele se fixează tot rândul Dacia est. Numărătorile sunt pe felii, de doi adnotatori, pe clipurile din 1.11 și 2.11. Catargiu → Dacia vest: drumul de sus duce ≈31% din Catargiu, ca flux, în etapa N–S (IC90 28–35%), dar cea mai mare parte continuă pe inel. Pe banda ieșirii spre Dacia vest trec, din a 15-a secundă a etapei N–S, 23,5 vehicule pe 8 clipuri, la 478,5 intrări de pe Catargiu fără inel (inelul dinspre est trece prin aceeași linie în afara etapei N–S): 4,9% (IC90 pe clipuri 2,8–8,4%). Un singur clip, 2.11 16:30, are 10 dintre ele; fără el rămân 3,2%, iar mediana pe clipuri e 3,5%. O numărare automată separată, pe 11 clipuri și pe același numitor, a dat 3,2% (2,3–4,4%). Se ia 0,04; rezultatele se dau și cu 0,08. Dacia est → Catargiu: pe 8 etape E–V văzute cap-coadă (1.11: 6, 2.11: 2), cu fereastra ieșirilor legată de fluxul Dacia est (de la prima intrare + 8 s la ultima + 20 s), ieșirile spre Catargiu sunt 0,41 din intrările de pe Dacia est din aceeași etapă (IC90 pe etape 0,32–0,52); după cum se aleg etapele și ferestrele, 0,34–0,48. Între duminică și luni nu se vede o diferență, deci rămâne o singură cotă, 0,40, aceeași cu prima numărare; rezultatele se dau și cu 0,32 și 0,48. Raportul dintre inel și Dacia est nu e o cotă, fiindcă pe inel trece și stocul de pe Magheru. Dacia est → Dacia vest: 0,305, ipoteză declarată. Pe banda ieșirii spre Dacia vest trec, în afara etapei N–S, 0,44 din intrările de pe Dacia est (IC90 0,40–0,49), dar pe aceeași bandă iese și ≈30–50% din stocul de pe inel, deci Dacia est → Dacia vest e ≈0,33–0,42; rezultatele se dau și cu 0,39. Restul rândului e ales, nu numărat: Dacia vest și Căderea Bastiliei, 0,305 și 0,07, sunt distribuția a priori rescalată (0,30 și 0,0675), rotunjită; Mendeleev urcă la 0,085 (a priori, 0,06), fiindcă pe 25.10, la vârf, traiectoriile complete spre el sunt mai multe; diferența se ia din Magheru (0,15 → 0,125) și din întoarcere (0,0225 → 0,015). Pe inel merg astfel 0,53 din Dacia est. Ce nu intră în cerere, limite declarate: Magheru → inel. În cameră, stocul de pe inel e de ≈4–6 vehicule pe ciclu, 90–96% de pe Magheru, adică ≈5–6% din Magheru în zilele lucrătoare și ≈8–10% duminica; în cerere, 1,1–3,0% la orele încărcate, deci inelul din cerere e sub cel din cameră, cel mai mult duminica. Se dă ca variantă, cu 6% în toate zilele (Dacia vest, Mendeleev și întoarcere, câte 2%). Catargiu → Magheru pe drumul de sus nu are rută, fiindcă routeSampler o ignoră, iar forțată, pierderea de timp pe brațul Catargiu crește cu 110–160%.')
    cfg["cote_timp_real"] = {"magheru": {"dacia_est": 0.14}}
    cfg["_cote_timp_real"] = 'Doar în geamănul în timp real, unde vehiculele intră după debitul brut al fiecărui braț, de pe zonele vechi, și se împart pe destinații după proporțiile traiectoriilor complete numărate de la pornirea colectării (§ 5.5). Acolo, virajul Magheru → Dacia est nu se ia din numărul lui, ca în scenarii, ci din această cotă: 0,14, media ponderată cu Magheru pe cele 12 ore observate ale scenariilor (0,10–0,21 de la o oră la alta). Pe clipurile din 2.11, adnotatorii văd în valurile de pe Magheru 0,12 din Magheru, ≈0,14 cu vehiculele pe care le pierd. Factorii de detecție și virajele numărate nu se aplică acolo; cotele fixe se aplică, iar pietonii primesc factorul de extrapolare și cererea efectivă φ, deși sunt numărați pe zone, nu pe persoane.'
    cfg["rute_pe_brate"] = {"fisier": "candidate_brate.rou.xml",
                            "porniri": {"magheru": "119241030#1", "catargiu": "244658427#1", "dacia_est": "232079775#1", "dacia_vest": "-1486385191#0"},
                            "capete": {"magheru": "44499684#3", "catargiu": "4045775#0", "dacia_est": "669156737#0", "dacia_vest": "1486385191#0", "mendeleev": "125445934#2", "caderea_bastiliei": "119238385#2"},
                            "prin": {"magheru>dacia_est": "448266581#1 778823270 119238380#0 119238380#1"}}
    cfg["_rute_pe_brate"] = ("Rutele pornesc de pe bulevardul fiecărui braț și se termină pe bulevardul de ieșire, câte una pe pereche intrare–ieșire, nu de oriunde din rețea: intrările la 148–566 m de linia de oprire, ieșirile la 130–346 m. Camera nu vede ce e dincolo de piață. "
                             "Ruta de pe Magheru trece prin două semafoare reale, cu program presupus (≈8% din pierderea de la vârf); cu rutele vechi, capacitatea lor limita traficul din piață (§ 6.4, § 9.11).")
    cfg["profil_referinta"] = {**baza["profil_referinta"], "_descriere": baza["profil_referinta"]["_descriere"].replace(
        "Calibrat astfel încât planul fix de referință să funcționeze aproape de saturație pe replica fidelă a rețelei (la volume mai mari inelul se suprasaturează).",
        "Ales pe geamănul de dinainte de 2.11, cu teleportări (§ 6.5), și neverificat pe cel corectat: în măsura nouă e doar profilul de rezervă al dispeceratului, când camera lipsește.")}
    cfg["_prior"] = ("Distribuția a priori a destinațiilor pentru fiecare braț de intrare, adăugată mereu, cu ponderea din pondere_prior, peste traiectoriile complete, la echilibrarea Furness. "
                     "Rândul Dacia est și cota Catargiu → Dacia vest nu o folosesc (cote_fixe). Valorile sunt ponderi relative (geometria intersecției: virajele directe dominante, întoarcerile rare).")
    cfg["retea"] = "romana_v2.net.xml"
    cfg["tipuri_vehicule"] = "vtypes_v2.add.xml"
    cfg["optiuni_sumo"] = {"pedestrian.striping.stripe-width": 0.3, "pedestrian.striping.jamtime": 60, "pedestrian.striping.jamtime.narrow": 60, "pedestrian.striping.jamtime.crossing": 5, "pedestrian.striping.jamfactor": 1}
    cfg["_optiuni_sumo"] = ("Modelul de pietoni din SUMO îi ține pe zebră și pe insulele înguste mult mai mult decât se vede în cameră, cu vehiculele așteptând la verde; timpul pe zebră respinge opțiunile implicite (zebra 55, mediană/p90: implicite 8/41 s, alese 5/7 s, cameră 4,8/13,1 s). "
                            "Doar lățimea benzii, 0,3 m, stă pe debit: cu 0,64 m, Magheru scade cu 18%. Peste ≈60 s de blocaj, un pieton intră pe roșu fără să aleagă un gol: de aici ≈5–7% intrări pe roșu, care nu sunt o dovadă de realism; tot ele produc frânările de urgență.")
    cfg["_retea"] = "Geamănul corectat (§ 6.5): se construiește cu romana.network.retea_v2, din config/retea_v2.json."
    cfg["pietoni_pe_treceri"] = {"dacia_est": ["232079775#2", "119238380#1"], "magheru": ["668307642#1", "44499684#2"], "catargiu": ["1320256482", "668307633#2"], "dacia_vest": ["-778823268#2", "778823268#2"]}
    cfg["_pietoni_pe_treceri"] = "Trotuarele dintre care traversează pietonii, pe fiecare braț cu trecere comandată de semafor. Fiecare agent traversează o singură dată, pe un braț; pe Dacia est, Magheru și Catargiu, un agent trece ambele zebre, iar pe Dacia vest, una (§ 9.11). Programul de pe celelalte treceri e prin analogie."
    return cfg


def main() -> None:
    cfg = cerere(load_json("demand.json"), load_json("factori_v2.json"))
    (CONFIG_DIR / "demand_v2.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("[OK] config/demand_v2.json", cfg["factor_corectie_detectie"], cfg["factor_pietoni_masurati"])


if __name__ == "__main__":
    main()
