# Semaforizare Piața Romană

**Semaforizare inteligentă, bazată pe inteligență artificială, a intersecției Piața Romană din București:
camera publică live → viziune artificială → geamăn digital SUMO → agent de învățare prin întărire.**

Proiect comun pentru disciplinele *Interfețe om-calculator* și *Internet of Things*,
Universitatea Transilvania din Brașov, Facultatea de Matematică și Informatică, Informatică ID, anul III.
Autor: **Niunin Matei-Gabriel**.

![Dashboard-ul operatorului](docs/img/dashboard.png)

## Ce face sistemul

```
 Camera Webcam România (HLS)        Viziune artificială                 Geamăn digital SUMO              Control AI
 ┌──────────────────────────┐   ┌───────────────────────────┐   ┌──────────────────────────────┐   ┌──────────────────────┐
 │ mono.m3u8, 3288×1850 px  │──►│ YOLO11 + ByteTrack        │──►│ replică fidelă OSM 2,2×1,6 km│◄─►│ PPO (Stable-Baselines3)│
 │ Piața Romană, live       │   │ 10 zone + 2 treceri       │   │ vehicule, bicicliști, pietoni│   │ fazele reale, galben/ │
 └──────────────────────────┘   │ matrice O–D pe 15 min     │   │ (routeSampler, Furness)      │   │ roșu sigure, verde min│
                                └─────────────┬─────────────┘   └──────────────┬───────────────┘   └──────────┬───────────┘
                                              │ MQTT / JSON                    │ TraCI                         │
                                              └──────────────► Dashboard operator (HCI) ◄─────────────────────┘
```

1. **Preluare în timp real** a fluxului video public (`https://s5.webcamromania.ro/piataromanab/tracks-v1/mono.m3u8`),
   detecția și urmărirea vehiculelor, numărarea **pe direcții**: din ce braț vine fiecare vehicul și pe ce braț iese
   (Magheru, Lascăr Catargiu, Dacia est, Dacia vest; ieșiri unidirecționale Mendeleev și Căderea Bastiliei), plus
   pietonii de pe cele două treceri vizibile și bicicliștii.
2. **Transformarea numărătorilor în trafic simulat** fidel, pe **replica fidelă a rețelei reale** (inelul, axa
   centrală, benzile STB, trotuarele, trecerile și cele 16 semafoare fizice ale pieței): prin Piața Romană trec în
   SUMO exact virajele observate, nu trafic aleatoriu; intersecțiile vecine fără cameră primesc doar traficul care
   iese/intră din piață, plus un trafic de fond declarat explicit.
3. **Antrenarea unui agent RL** care decide ordinea și durata fazelor reale ale semaforului (și, în varianta
   „coridor”, ale celor 4 intersecții vecine care o alimentează) – singurul lucru care se schimbă față de realitate – comparat cu planul
   fix de referință, planul Webster, semaforizarea actuated a SUMO și Max-Pressure, pentru toți participanții.
4. **Dashboard de dispecerat** pentru operatorul uman: imaginea analizată, cozile pe brațe, faza curentă și preluarea
   controlului (AI / plan fix / Max-Pressure / manual) cu confirmare.

> **Pentru evaluare:** ghidul pas cu pas de instalare, rulare și verificare este în [GHID_PROFESOR.md](GHID_PROFESOR.md).

## Rezultate pe date reale (pe scurt)

Două zile de trafic real analizat pe cameră (21.10.2026 11:45 – 22.10.2026 11:00), 10 scenarii SUMO, 300 de
simulări. Pierderea totală de timp a tuturor participanților, față de planul fix actual (medie pe 10 scenarii):

| Agent RL piață | Max-Pressure | Webster | Actuated | Agent RL coridor |
|---|---|---|---|---|
| **−4,6%** (până la −13,5%; niciodată mai rău de +0,7%) | −2,0% | +2,4% | +13,1% | +35,4% |

Agentul AI al pieței este cea mai bună strategie și generalizează pe o zi nevăzută la antrenare (−4,2% la vârful
din 22.10). **Actualizare 23.10:** după corectarea zonelor camerei și renumărarea datelor, agentul (antrenat pe
datele vechi) câștigă doar la trafic lejer și moderat (până la −16,8%), iar la vârf planul fix e mai bun (medie
+5,2%): agentul trebuie reantrenat pe scenariile noi – detalii în § 9.5. **24.10:** un program pe tipuri de
trafic (agentul AI la trafic lejer, agentul E3 la prânz, planul cu ciclu lung 46/48/12 s la vârf), ales pe
validare, este cea mai bună strategie pe datele noi: **−8,5%** în evaluarea completă (350 de simulări, 7 strategii,
5 seed-uri, § 9.7), față de actuated −3,2%, agentul E3 −1,4%, Webster −1,3%, agentul oficial +2,8% și
Max-Pressure +9,6%. Diferența e **semnificativă statistic** față de planul fix (p = 0,002; mai bun în 41 din 50 de
rulări) și față de actuated (p = 0,02) – § 9.9. Coordonarea învățată cu vecinii a dat un rezultat negativ – detalii și explicații în [docs/DOCUMENTATIE.md § 9](docs/DOCUMENTATIE.md#9-rezultate).

## Pornire rapidă (Windows)

```bat
scripts\0_instalare.bat          :: o singură dată: mediu virtual + dependențe (Python 3.11–3.13)
scripts\PORNESTE_TOT.bat         :: viziune live + geamăn digital SUMO-GUI + dashboard (http://localhost:8050)
```

Pași individuali: `1_construieste_retea` → `2_viziune_live` → `3_genereaza_cerere` → `4_antreneaza_ai` →
`5_evalueaza` → `6_geaman_digital` / `7_dashboard` / `8_simulare_gui`. Detalii în
[docs/DOCUMENTATIE.md](docs/DOCUMENTATIE.md#11-ghid-de-instalare-și-rulare).

## Structura

| Director | Conținut |
|---|---|
| `src/romana/vision/` | citire HLS, YOLO11 + ByteTrack, numărare origine–destinație, calibrarea zonelor |
| `src/romana/bridge/` | estimarea matricei O–D (Furness), generarea cererii SUMO, geamănul digital live |
| `src/romana/network/` | construirea reproductibilă a rețelei SUMO din OpenStreetMap |
| `src/romana/control/` | controler sigur de semafor, mediu Gymnasium, PPO, linii de bază, evaluare |
| `src/romana/dashboard/` | consola web a operatorului |
| `config/` | camera și zonele, rețeaua și fazele, parametrii cererii |
| `sumo/` | rețea, cerere calibrată, scenarii `.sumocfg` |
| `data/counts/` | numărători agregate (fără imagini – GDPR) |
| `models/` | agenții PPO antrenați |
| `docs/` | documentația completă, rezultate, imagini |
| `legacy/google_ai_draft/` | ciorna inițială (asistent Google AI), păstrată cu raport de audit |

## Borne

| Bornă | Conținut | Stare |
|---|---|---|
| B0 | Audit ciornă, restructurare repository | ✅ |
| B1 | Rețea SUMO a zonei, semafoare identificate, faze cu semnificație | ✅ |
| B2 | Viziune artificială: cameră → numărători O–D | ✅ (zone preliminare, de rafinat pe lumină de zi) |
| B3 | Punte cameră → SUMO, cerere calibrată | ✅ |
| B4 | Agent RL + linii de bază + evaluare | ✅ (refăcut în B8 pe rețeaua fidelă) |
| B5 | Dashboard operator (HCI) + IoT (MQTT) | ✅ |
| B6 | Documentație și bibliografie | ✅ (actualizată la fiecare bornă) |
| B7 | Calibrare pe lumină de zi (zone vehicule și treceri), date reale de vârf | planificat |
| B8 | Replica fidelă a rețelei + toți participanții (pietoni, bicicliști), reantrenare și evaluare | în lucru |
| B9 | Reantrenare și evaluare pe datele reale de zi, verificare finală | planificat |

Jurnalul detaliat: [docs/DOCUMENTATIE.md § 12](docs/DOCUMENTATIE.md#12-jurnalul-bornelor).

## Licențe și atribuiri

Dependența Ultralytics YOLO este licențiată AGPL-3.0, deci codul acestui proiect, fiind public, trebuie
distribuit sub o licență compatibilă (recomandat: AGPL-3.0; alegerea finală aparține autorului). Date rețea: © OpenStreetMap contributors, ODbL 1.0.
Imagini cameră: © WebcamRomania.ro – prelucrate doar în memorie, fără stocare. Simulator: Eclipse SUMO, EPL-2.0.
Asistenți generativi: modulul AI Google din Chrome (ciorna până la 18.10.2026); de la 20.10.2026, **Claude (Anthropic,
model Claude Opus 5.5, prin Claude Code)**, care a scris cea mai mare parte a codului și a documentației, sub coordonarea
autorului – declarația completă în [docs/DOCUMENTATIE.md § 13](docs/DOCUMENTATIE.md#13-asistență-generativă).
