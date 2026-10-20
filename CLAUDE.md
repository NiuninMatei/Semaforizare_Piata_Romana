# Instrucțiuni pentru Claude – proiectul „Semaforizare Piața Romană”

Acest fișier este citit automat de Claude Code la deschiderea proiectului. Conține regulile
autorului și starea de predare a lucrului (actualizați secțiunea „Stare curentă” la fiecare bornă).

## Regulile autorului (Niunin Matei-Gabriel)

- Limba proiectului, a documentației, a comentariilor și a mesajelor de commit: **română**.
- **Commit + push după fiecare modificare de impact** (profesorul coordonator urmărește istoricul).
  Mesajele încep cu „Borna N: …” pentru pașii de bornă. Încheiați mesajele cu linia
  `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Lucrul este organizat pe **borne** (vezi `docs/DOCUMENTATIE.md` § 12); nu se deviază de la ideea principală.
- **Rețeaua rutieră trebuie să fie replica fidelă a realității** (OpenStreetMap): nu se modifică
  geometria, benzile, sensurile, trecerile sau pozițiile semafoarelor. Se schimbă DOAR modul în care
  semafoarele existente răspund traficului (programul/fazele/durata) – singurul lucru implementabil real.
- În simulare intră **toți participanții observabili pe cameră**: autoturisme, autobuze/troleibuze,
  camioane, motociclete, bicicliști, pietoni (și orice altă categorie care apare).
- Cererea de trafic se calibrează pe datele camerei, nu trafic aleatoriu; ipotezele se declară explicit.
- Bibliografia: note de subsol cu licențe. Asistent generativ: modulul AI Google (ciorna, până la
  18.10.2026), apoi Claude (Anthropic) de la 20.10.2026.
- Lucrați **local, pe calculatorul autorului** cât timp e posibil; cloud doar dacă local nu se poate.

## Mediul local (Windows)

- Repository: `C:\Users\Matei\Documents\GitHub\Semaforizare_Piata_Romana` (GitHub Desktop + git).
- Python 3.12 în `.venv` (creat de `scripts\0_instalare.bat`); rulați modulele cu
  `.venv\Scripts\python -m romana.<modul>` și `PYTHONPATH=src` (vezi `scripts\_mediu.bat`).
- SUMO 1.28 instalat și în `C:\Program Files (x86)\sumo`; pachetul pip `eclipse-sumo` e în `.venv`.
- `libsumo` (antrenare rapidă) trebuie instalat în `.venv`: `pip install libsumo==1.28.0`.
- Microsoft Visual C++ Redistributable este instalat (necesar pentru PyTorch / YOLO).

## Arhitectura (pe scurt)

`src/romana/vision` (cameră HLS → YOLO11 + ByteTrack → numărători O–D, CSV în `data/counts`) →
`src/romana/bridge` (Furness + `routeSampler.py` → `sumo/scenarios/*.sumocfg`; `live_twin.py` = SUMO live) →
`src/romana/control` (SignalController sigur, mediu Gymnasium, PPO, Webster/actuated/Max-Pressure, evaluare) →
`src/romana/dashboard` (Flask, http://localhost:8050). Config în `config/*.json`.

## Stare curentă (21.10.2026, 01:20) – Borna 8 în lucru

Făcut în Borna 8 (rețea fidelă + toți participanții), comis în acest commit:
- `network/build_network.py` rescris: geometrie OSM completă, trotuare, treceri (`--crossings.guess`;
  `--osm.crossings` dă crash în netconvert 1.28), acces biciclete, benzi de viraj; cele 16 semafoare
  fizice ale pieței grupate într-un controler `romana` (pasul 2 cu `--tls.join-exclude` pentru restul).
- Programul `romana` pe grupuri de semnal (`config/network.json` → `romana_grupuri`, `romana_faze`);
  trecerile de pietoni primesc verde automat doar dacă niciun flux verde nu le intersectează geometric.
  Ieșirile au verde în toate fazele de vehicule (altfel inelul se bloca – diagnosticat), pietonii de pe
  ieșiri au faza „Pietoni”.
- Cererea: biciclete (rute candidate separate), pietoni (1200/h ipotetic, extrapolare din cameră cu
  `factor_extrapolare_pietoni`), scenarii `referinta_moderat/varf/aglomerat` regenerate (vârf = 2060 veh/h
  prin piață; peste ~1,0× planul fix se suprasaturează – realist pentru Piața Romană).
- Mediu RL: observația include pietonii care așteaptă la fiecare trecere; recompensa = −(vehicule oprite +
  pietoni care așteaptă)/100. Funcții comune `observation()` / `waiting_total()` în `control/signals.py`.
- Modelele vechi (pe rețeaua agregată, incompatibile) au fost scoase din `models/`.

### Pașii următori (în ordine)

1. Viziune: numărarea pietonilor pe trecerile vizibile (zone cu `rol: "trecere"` în `config/camera.json`,
   persoanele intră în `ODCounter` ca tip „pietoni”) și verificarea bicicliștilor; calibrarea zonelor pe
   lumină de zi (`scripts\2b_calibrare_zone.bat`).
2. Verificat `bridge/live_twin.py` și dashboard-ul pe rețeaua nouă (pietoni injectați live, `link_group`).
3. `evaluate.py`: adăugat metrici pentru pietoni (timeLoss din `personinfo`) și bicicliști.
4. Antrenare locală: `scripts\4_antreneaza_ai.bat --pasi 150000` (piață) și `--coridor` (6 controlere);
   apoi `scripts\5_evalueaza.bat`; completat § 9 Rezultate în `docs/DOCUMENTATIE.md` (marcajul
   `<!-- REZULTATE_INCEPUT -->`).
5. Documentația: actualizat § 6 (replica fidelă în locul „nodului agregat”), § 4 (pietoni/biciclete),
   jurnalul bornelor (B8–B10), README.
6. Date reale de zi: `scripts\2_viziune_live.bat` în vârful de dimineață/seară, apoi
   `3_genereaza_cerere.bat --nume <zi> --de-la ... --pana-la ...`, reantrenare, evaluare.
