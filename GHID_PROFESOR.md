# Ghid pentru evaluare – „Semaforizare Piața Romană”

Acest ghid explică, pas cu pas, cum se instalează, se rulează și se verifică proiectul. Documentația completă
(metodă, decizii, rezultate, bibliografie) este în [`docs/DOCUMENTATIE.md`](docs/DOCUMENTATIE.md).

Autor: Niunin Matei-Gabriel. Implementarea a fost realizată în cea mai mare parte cu asistentul AI Claude
(Anthropic), sub coordonarea autorului – declarația completă în
[`docs/DOCUMENTATIE.md` § 13](docs/DOCUMENTATIE.md#13-asistență-generativă).

---

## 1. Ce face proiectul, pe scurt

1. **Camera publică** Webcam România din Piața Romană este analizată în timp real: YOLO11 detectează
   autoturisme, autobuze/troleibuze, camioane, motociclete, biciclete și pietoni; ByteTrack îi urmărește; se
   numără din ce braț intră fiecare vehicul, pe ce braț iese și câți pietoni traversează.
2. **Numărătorile** devin cerere de trafic în SUMO (estimare origine–destinație Furness + `routeSampler`),
   pe o **replică fidelă a rețelei reale** (OpenStreetMap): inelul pieței, axa centrală, benzile STB,
   trotuarele, trecerile și cele 16 semafoare fizice ale pieței, plus intersecțiile semaforizate vecine (4 dintre ele în coridorul controlat).
3. **Un agent de învățare prin întărire (PPO)** învață să conducă semaforul existent al pieței – doar ordinea și
   durata fazelor reale, singurul lucru implementabil pe automatul real – și este comparat cu planul fix, Webster,
   semaforizarea „actuated” și Max-Pressure, pe scenarii construite din date reale.
4. **Un dispecerat web** arată imaginea analizată, starea semaforului din geamănul digital SUMO și permite
   operatorului uman să preia controlul.

## 2. Cerințe

| | |
|---|---|
| Sistem | Windows 10/11 (testat pe Windows 11, laptop Lenovo V15 G4, i5-13420H, 16 GB RAM, fără GPU NVIDIA) |
| Python | 3.11–3.13 (testat 3.12) |
| SUMO | 1.28 – instalarea oficială (https://sumo.dlr.de, cu `SUMO_HOME` setat) **sau** pachetul `eclipse-sumo` din `requirements.txt` |
| Spațiu | ~4 GB (mediul Python + modele) |
| Internet | pentru fluxul camerei și instalare |
| Opțional | placă grafică Intel (OpenVINO, implicit) sau NVIDIA (`--device 0`) pentru viziune |

## 3. Instalare (o singură dată)

```bat
git clone https://github.com/NiuninMatei/Semaforizare_Piata_Romana.git
cd Semaforizare_Piata_Romana
scripts\0_instalare.bat
```

Scriptul creează mediul virtual `.venv` și instalează dependențele. Toate celelalte scripturi din `scripts\`
activează automat acest mediu.

## 4. Verificarea rapidă (fără cameră, ~10 minute)

Rezultatele din documentație se pot reproduce fără a mai colecta date: numărătorile, jurnalul de traiectorii,
scenariile și modelele antrenate sunt incluse în repository.

| Pas | Comandă | Ce trebuie să se vadă |
|---|---|---|
| Teste automate | `set PYTHONPATH=src` apoi `.venv\Scripts\python -m unittest discover tests` | `OK` (10 teste: numărarea O–D, pietoni, sensul de mers, renumărarea) |
| Simulare vizuală | `scripts\8_simulare_gui.bat` | SUMO-GUI cu ora de vârf din 21.10.2026 și agentul AI la semaforul pieței (vehicule, bicicliști, pietoni) |
| Comparație vizuală | `scripts\8_simulare_gui.bat sumo\scenarios\zi_2026-10-21_varf.sumocfg --strategie fix_referinta` | aceeași oră, cu planul fix |
| Evaluare (scurtă) | `.venv\Scripts\python -m romana.control.evaluate --seeds 1 --procese 4 --scenarii sumo\scenarios\zi_2026-10-21_varf.sumocfg` | tabelul din `docs\rezultate\rezultate.md` regenerat |

Evaluarea completă (`scripts\5_evalueaza.bat`, 5 seed-uri × toate scenariile × 6 strategii) durează ~1 oră.

## 5. Rularea completă, pas cu pas

| # | Script (`scripts\`) | Ce face | Durată |
|---|---|---|---|
| 1 | `1_construieste_retea.bat` | regenerează rețeaua SUMO din extrasul OSM (`data\osm`) | ~2 min |
| 2 | `2_viziune_live.bat` | analiza live a camerei (fereastră cu zonele, `q` = oprire); scrie `data\counts` și `data\trajectories` | cât se dorește (o zi întreagă pentru un profil complet) |
| 2b | `2b_calibrare_zone.bat` | redesenarea zonelor dacă operatorul mută camera | ~5 min |
| 2c | `2c_renumarare.bat --zi AAAA-LL-ZZ` | renumără ziua din jurnalul de traiectorii (după o recalibrare a zonelor) | ~5 min |
| 3b | `3b_scenarii_zi.bat --zi AAAA-LL-ZZ` | găsește ora de vârf, prânzul și ora liniștită și construiește scenariile SUMO | ~5 min |
| 3 | `3_genereaza_cerere.bat --nume X --de-la "..." --pana-la "..."` | un scenariu pe o fereastră aleasă manual | ~1 min |
| 4 | `4_antreneaza_ai.bat --pasi 500000 --medii 8 --scenarii sumo\scenarios\zi_*.sumocfg` | antrenarea agentului PPO al pieței (`--coridor` pentru piață + 4 vecini) | ~1,5 h pe laptopul de test |
| 5 | `5_evalueaza.bat` | evaluarea comparativă; actualizează `docs\rezultate\` | ~1 h |
| 6 | `6_geaman_digital.bat` | SUMO-GUI alimentat **live** de cameră, semafor condus de AI | continuu |
| 7 | `7_dashboard.bat` | dispeceratul web la http://localhost:8050 | continuu |
| – | `PORNESTE_TOT.bat` | 2 + 6 + 7 în trei ferestre: sistemul complet în timp real | continuu |

## 5b. Demonstrația live (scenariul de prezentare, ~20 de minute)

Folosit la evaluarea prin demonstrație din 22.10.2026 (observațiile și ce s-a făcut: `docs/OBSERVATII_EVALUARE.md`).
Pornire: `scripts\PORNESTE_TOT.bat` (camera, geamănul SUMO-GUI, dispeceratul în browser), apoi câte o fereastră
pe ecran, în ordinea în care circulă datele:

| Pas | Fereastra | Ce se arată |
|---|---|---|
| 1. Ochii sistemului | „Piata Romana – viziune artificiala” | detecțiile YOLO11 + ByteTrack, zonele de intrare/ieșire/trecere, debitele pe brațe (imaginea e redată cu 8 s întârziere, fluent) |
| 2. Geamănul digital | SUMO-GUI | rețeaua fidelă OSM, cele 16 semafoare ca un controler, traficul generat din debitele camerei, în timp real |
| 3. Omul în buclă | dispeceratul, http://localhost:8050 | camera ca flux video, faza curentă în cuvinte, cozile pe brațe; „Plan fix” → „Confirm” schimbă semaforul din SUMO, „Agent AI” → „Confirm” îl readuce |
| 4. Dovada măsurată | `scripts\9_demo_comparatie.bat` (~2,5 min) | aceeași oră reală cu planul fix, Max-Pressure și agentul AI, pe categorii (vehicule, bicicliști, pietoni, CO₂) |
| 5. Rezultate și limite | `docs/DOCUMENTATIE.md` § 9–10 | evaluarea oficială și limitările declarate |

## 6. Unde se găsesc lucrurile

| Director / fișier | Conținut |
|---|---|
| `src/romana/vision/` | cameră → detecție → urmărire → numărare (`od_counter.py`, `recount.py`) |
| `src/romana/bridge/` | estimarea O–D, cererea SUMO, scenariile zilei, geamănul digital live |
| `src/romana/network/` | construirea replicii fidele a rețelei din OSM |
| `src/romana/control/` | controlerul sigur de semafor, mediul Gymnasium, PPO, liniile de bază, evaluarea |
| `src/romana/dashboard/` | dispeceratul web |
| `config/` | camera și zonele, rețeaua și grupurile de semnal, parametrii cererii |
| `data/counts/`, `data/trajectories/` | datele reale colectate (numărători agregate și traiectorii anonime – fără imagini) |
| `sumo/scenarios/zi_*` | scenariile din date reale; `referinta_*` = scenariile ipotetice inițiale |
| `models/` | agenții antrenați (`.zip` Stable-Baselines3 + `.npz` pentru rulare fără PyTorch) |
| `docs/rezultate/` | rezultatele evaluării (tabele, CSV, grafic) |
| `legacy/google_ai_draft/` | ciorna inițială, păstrată cu raportul de audit |

## 7. Cum se citesc rezultatele

`docs/rezultate/rezultate.md` conține, pentru fiecare scenariu și strategie, media ± abaterea standard pe 5
simulări: așteptarea și pierderea de timp a vehiculelor, întârzierea la intrarea în rețea, bicicliștii,
pietonii și **pierderea totală de timp a tuturor participanților** (indicatorul principal). Procentele sunt față
de planul fix de referință. Interpretarea și limitele sunt discutate în `docs/DOCUMENTATIE.md` § 9 și § 10.

## 8. Probleme frecvente

| Simptom | Cauză / soluție |
|---|---|
| `SUMO nu a fost găsit` | setați `SUMO_HOME` sau rulați `pip install eclipse-sumo==1.28.0` în `.venv` |
| `DLL load failed ... _libsumo` | PYTHONPATH-ul instalatorului SUMO umbrește pachetul pip; proiectul îl ocolește automat (`control/env.py`). Dacă persistă: `set ROMANA_USE_TRACI=1` (mai lent) |
| viziunea are sub 2 cadre/s | fără GPU, verificați `runtime: "openvino"` în `config/camera.json`; cu GPU NVIDIA: `runtime: "pytorch"`, `--device 0` |
| `Cannot use optimization (scipy not installed)` | `pip install scipy` în `.venv` |
| camera nu răspunde | fluxul public poate fi temporar indisponibil; geamănul digital trece automat pe profilul de referință și afișează asta |

## 9. Licențe

Codul folosește Ultralytics YOLO (AGPL-3.0), Eclipse SUMO (EPL-2.0), date OpenStreetMap (ODbL 1.0) și imaginile
Webcam România (prelucrate doar în memorie, în scop academic). Lista completă: `docs/DOCUMENTATIE.md` § 14.
