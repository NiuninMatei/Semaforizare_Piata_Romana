# Instrucțiuni pentru Claude – proiectul „Semaforizare Piața Romană”

Acest fișier (`.claude/CLAUDE.md`) este citit automat de Claude Code la deschiderea proiectului; nu face parte din documentație (singura documentație: `docs/DOCUMENTATIE.md`). Conține regulile
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

## Stare curentă (22.10.2026, 16:10) – Bornele 7 și 9 încheiate

- Date reale: 21.10 11:45 – 22.10 11:00 (traiectorii + numărători în data/), 10 scenarii `zi_2026-10-2*`.
- Agentul oficial = `models/ppo_romana` (v1, antrenat pe 21.10, ales pe seed-uri de validare 11–13 față de doi
  agenți antrenați pe ambele zile). Evaluare finală (300 de simulări): −4,6% în medie față de planul fix, cea mai
  bună strategie, niciodată mai rău de +0,7%; generalizează pe 22.10 (−4,2% la vârf). Max-Pressure −2,0%.
- Coridorul (piața + 4 vecini, fără Dacia × Polonă – sens unic de ieșire) = rezultat negativ (+35% în medie):
  vecinii rămân pe programele actuated. Experimentele v2, v3, E1 (γ=0,99) – negative, documentate.
- Plafonul la vârf: cel mai bun plan fix posibil −5,4%; 68% din întârzierea la vârf = coada Dacia vest dincolo
  de rețea. § 9 din docs/DOCUMENTATIE.md rescris complet; GHID.md pentru evaluare.
- Laptop: modul Windows „Cea mai bună performanță” + Lenovo „Performanță” (~2,8 GHz pe toate firele).

### 25.10.2026 (noaptea, de la 01:12; autorul revine la 18:00) – E4–E7, date de weekend

- E4: `ppo_romana_nou` (1M pași de la zero) – validare +11,6…+12,9%, fără câștig față de oficial (§ 9.8).
- E5/E6: specialiști pentru trafic greu; E6 (`ppo_romana_greu_bc`, imitație 46/48/12 + PPO) −5,8% pe validare,
  dar −5,7% pe test față de planul 46/48/12 −8,4% → programul păstrează planul (−8,5%). Validare cu 5 seed-uri
  (11–15) pentru experimentele următoare.
- E7: `ppo_romana_greu_e7_400k` −9,3% pe validare (5 seed-uri), −7,0% pe test; statistic echivalent cu planul 46/48/12
  (p = 0,32) → programul păstrează planul. Programul vs plan fix: p = 0,002 (41/50); vs actuated: p = 0,02 (§ 9.9).
- E8 (specialist moderat) negativ; E9 (`ppo_romana_lejer`, specialist lejer) −9,5% vs −9,0% (p = 0,001) → banda lejeră.
  Program final (E9 / E3 / plan 46/48/12) pe 10 seed-uri: −6,9% vs plan fix (p = 0,0003, 79/100), −3,2% vs actuated
  (p = 0,04) – § 9.10. `evaluate.py --seed-start`; `live_twin.py`: `MODEL_LEJER`.
- În lucru: colectarea de date de duminică 25.10 (`run_vision` fără fereastră, de la 01:14)
  → `scenarii_zi --zi 2026-10-25` spre seară, test de generalizare.

### 24.10.2026, 12:11–14:20 – evaluarea completă făcută; antrenarea de la zero oprită la 550k (de continuat)


- **Evaluarea completă (§ 9.7):** 350 de simulări (7 strategii × 10 scenarii × 5 seed-uri): programul pe tipuri de
  trafic −8,5% (cea mai bună), actuated −3,2%, E3 −1,4%, Webster −1,3%, plan 46/48/12 −0,9%, oficial +2,8%, MP +9,6%.
- `models/ppo_romana_nou` = punctul intermediar de la 550k pași (antrenarea oprită la cererea autorului; metadatele
  .json copiate de la ppo_romana). **De făcut:** `train --nume romana_nou --continua --pasi 250000 --medii 8` (peste
  noapte), validare pe seed-urile 11–13 față de ppo_romana / ppo_romana_zn3, evaluarea completă `--adauga`.
- `evaluate.py --planuri 46,48,12` evaluează orice plan fix dat prin durate.

- `ppo_romana_nou`: PPO de la zero pe cele 10 scenarii noi, 800k pași, 8 medii (puncte intermediare la 25k în
  `outputs/train/checkpoints`); apoi validare pe seed-urile 11–13 și evaluarea completă (toate strategiile, 5 seed-uri).
- Numărătoarea manuală în teren scoasă din pașii următori (nerealistă pentru un om, observația autorului); înlocuită
  în § 10 cu adnotarea a 2–3 minute de video ca lucrare viitoare opțională.

### 24.10.2026, 09:19–10:55 – observațiile O10–O12, reantrenarea (E2, negativă), programul pe tipuri de trafic

- Trecerea Căderea Bastiliei deasupra ieșirii; documentația: Mendeleev + Căderea Bastiliei sens unic, Dacia 2+2 benzi.
- E2: `ppo_romana_zn` (+100k pași pe scenariile noi) mai slab pe validare (+19,8% vs +11,3%) → oficial rămâne `ppo_romana`.
- Grila de planuri fixe pe datele noi (§ 9.6): referința 36/28/12 e practic optimă în medie; 46/48/12 câștigă la vârf.
  Program pe tipuri de trafic (lejer → AI, prânz → referință, vârf/dimineață → 46/48/12), ales pe validare: −6,3%.
- E3: `ppo_romana_zn3` (+60k pași, lr 3e-5) ≈ agentul vechi în medie, dar −17,6% la prânz (test) → programul cu E3 la
  prânz: −8,1%. Modul „program” din `live_twin.py`/dispecerat e implementat (banda de mijloc = agentul E3, `MODEL_PRANZ`). `train.py`: `--lr` se aplică acum și la `--continua`.
- **Pasul următor:** antrenare completă de la zero pe scenariile noi (500k+ pași, ~2–3 h la ~80–130 pași/s),
  selecție pe seed-urile 11–13; implementarea programului pe tipuri de trafic în `live_twin.py` (comutare după debit).

### 23.10.2026, 12:40–13:30 – zonele din decupajele autorului, date renumărate, scenarii regenerate

- `config/camera.json` = decupajele autorului (capturi 1920 px, SIFT cu scara fixă 3288/1920); „Dacia vest in”
  și „Căderea Bastiliei trecere” poziționate manual – de verificat. Teste independente de coordonate.
- data/counts renumărate (4 995 viraje complete față de 2 800), 10 scenarii zi_* regenerate, agentul reevaluat
  (3 strategii × 3 seed-uri; § 9.5). Vechile rezultate: `outputs/eval/rezultate_zone_vechi.csv` + istoricul git.
- **Reevaluare (§ 9.5):** pe scenariile noi agentul vechi dă +5,2% în medie (−7…−17% la trafic lejer/prânz,
  +23…+34% la vârf); Max-Pressure +9,1%. **Primul pas următor: reantrenarea `ppo_romana` pe scenariile noi**
  (`4_antreneaza_ai.bat --pasi 500000 --medii 8`, ~o noapte), selecție pe seed-urile 11–13, evaluarea completă.
- **De făcut:** Dacia est are în Street View o bandă pe sens + parcare, în rețea (OSM) două → corectare OSM,
  regenerarea rețelei, reantrenarea agentului; reantrenarea pe datele renumărate; evaluarea completă (5 strategii ×
  5 seed-uri); numărătoarea manuală de 15 min pe braț (autorul, pe teren).

### Evaluarea prin demonstrație (22.10, 20:48–22:00) – pașii 1–5 prezentați

- Verificarea live de către autor; observațiile O1–O9 și ce s-a făcut: `docs/OBSERVATII_EVALUARE.md`.
- Zonele camerei recalibrate (O1–O7, 7 treceri); fluxul MJPEG în dispecerat și pași de 0,2 s în SUMO (O8);
  demo-ul de comparație cu bicicliști/pietoni (O9).
- **De făcut:** Pasul 5 al demonstrației (rezultate și limite); renumărarea oficială cu zonele noi (`recount`)
  → `scenarii_zi` → reevaluarea agenților (măsurat: intrări −29%, Mendeleev ×10, Catargiu out încă prea mare);
  verificarea pe lumină de zi a celor 5 treceri noi și a zonei Catargiu out; scenariul de demo în GHID.md.

### Demonstrația live (22.10, seara) – pregătire

- Pregătită și reparată: tampon de redare de 8 s pentru camera HLS (fără sacade), fereastra camerei
  redimensionabilă, bucla live robustă (PermissionError, debitele la granița de 15 min), SUMO-GUI centrat
  pe piață, `scripts\9_demo_comparatie.bat` (plan fix / Max-Pressure / AI, prânzul 21.10: −4,8% la AI).
- Formatul convenit cu autorul (rol de profesor): ecranul împărțit – fereastra sistemului în stânga
  (2/3), Claude în dreapta; câte un pas pe mesaj, autorul scrie „mai departe”. Pașii: 1 camera (făcut),
  2 geamănul SUMO, 3 dispeceratul și preluarea controlului, 4 comparația măsurată, 5 rezultate și limite.
- Reluare: `scripts\PORNESTE_TOT.bat`, apoi aranjarea ferestrelor (camera / SUMO / Chrome „Dispecerat”).
  De scris după demo: scenariul de prezentare în GHID.md.

### Pași posibili în continuare

1. O numărătoare manuală de 15 min pe fiecare braț (factorul de corecție, § 10).
2. Mai multe zile de date (weekend, vreme rea) → `scenarii_zi` → reantrenare cu selecție pe validare.
3. Coordonare descentralizată cu vecinii (MPLight / CoLight), cu mult mai mult timp de antrenare.

## Stare anterioară (21.10.2026, 22:30) – Borna 7 făcută, Borna 9 în lucru (date reale)

Făcut pe 21.10 (ziua):
- Push autonom prin GitHub Desktop (computer use; vezi memoria „push-prin-github-desktop”). Camere publice
  căutate: în zona modelată există doar camera Piața Romană → vecinii sunt simulați din datele ei (§ 4.1).
- Viziune: OpenVINO pe GPU Intel (~5 cadre/s), jurnal anonim de traiectorii (data/trajectories) +
  `vision/recount.py` (renumărare, --directii, --flux, reunirea fragmentelor), regula pe traiectoria întreagă
  (origine înaintea oricărei ieșiri, zone `capat_traiectorie`, sensul de mers `sens`), zone recalibrate pe zi.
- Prima zi reală: 21.10, 11:45–21:01 → data/counts/numaratori_2026-10-21.csv; echilibrarea intrări/ieșiri
  („medie”, diferență măsurată ~30%); zonele Dacia vest mutate (prindeau vehicule de pe inel); rutele pornesc
  pe bulevardele brațelor (`follow_street`) → scenariile `zi_2026-10-21_{pranz,varf,linistit}` + ×1,2 / ×0,8.
- Liniile de bază pe scenariile reale: outputs/eval/rezultate.csv (planul fix e cel mai bun clasic la vârf).
- În curs (pornite 21:50): antrenarea `ppo_romana` 500k pe scenariile zi_* (`--medii 7`), apoi `ppo_coridor`
  500k (fazele vecinilor curățate, [3 3 3 2 3 2]); colectarea de noapte până pe 22.10, 11:00 (vârful de
  dimineață). Opțiune nouă `--obs-amonte` (cozile din amonte + vehiculele neintroduse), încă neantrenată.
- GHID.md scris; Claude trecut explicit în § 13 / § 14 / README.

### Pașii următori

1. Evaluarea `ppo_romana` / `ppo_coridor` pe scenariile zi_* (`--adauga`), comparată cu liniile de bază; dacă
   agentul nu bate planul fix la vârf: reantrenare cu `--obs-amonte` și/sau mai mulți pași.
2. Dimineața 22.10, după 11:00: `recount --zi 2026-10-22`, `scenarii_zi --zi 2026-10-22` (vârful de dimineață),
   reantrenare pe ambele zile, evaluare finală; § 9 Rezultate pe date reale; jurnalul bornelor.
3. Explicația cap-coadă pentru autor (în chat) la final.

## Stare anterioară (21.10.2026, 05:40) – Borna 8: pașii 1–5 făcuți (noaptea 21.10)

Făcut în noaptea de 21.10 (commit-uri „Borna 8: …”):
- Viziune: zone `trecere` (Magheru, Dacia est) desenate pe cadrul de noapte; pietonii numărați o dată pe
  trecere (≥ 2 cadre), bicicliștii/motocicliștii excluși (`is_rider`); teste în `tests/` (unittest).
- Liniile de bază reparate pe rețeaua fidelă: `tls_actuated.add.xml` (avea faze greșite), Webster (chei vechi),
  strategie nouă `fix_referinta` (programul '0'); Max-Pressure și agentul RL aleg doar fazele 0–2 (fazele
  „fără dozare” blocau inelul). `libsumo` pip se încarcă explicit (PYTHONPATH-ul SUMO îl umbrea).
- Geamăn digital: pietoni + bicicliști injectați, modul fix = planul de 3 faze; dashboard cu pietoni.
- Evaluare pe categorii (vehicule, bicicliști, pietoni, întârziere la intrare, total), mediană, `--procese`,
  `--adauga`, `--doar-raport`. Antrenare paralelă (`--medii 8`), `--continua`.
- Recompensa: vehiculele neintroduse contează cât unul oprit (agentul coridor „ascundea” coada la margine).
- Modele: `ppo_romana` (500k pași) – pierdere totală −3% / −31% / −44% față de planul fix; `ppo_coridor`
  (300k) – mai slab decât actuated (rezultat negativ, documentat). § 9 completat. Modelele vechi: local în
  `outputs/train/arhiva_recompensa_veche/` (neversionat).
- **Push-ul nu a mers din linia de comandă** (git fără credențiale în afara GitHub Desktop): commit-urile sunt
  locale – „Push origin” din GitHub Desktop.

### Pașii următori (actualizați)

1. Pe lumină de zi: verificat zonele de vehicule și cele 2 treceri (`scripts\2b_calibrare_zone.bat`) și
   detecția bicicliștilor; o numărătoare manuală de 15 min pentru `factor_corectie_detectie` și pentru
   `factor_extrapolare_pietoni`.
2. Date reale: `2_viziune_live.bat` în vârful de dimineață/seară, `3_genereaza_cerere.bat --nume <zi> ...`,
   reantrenare (`4_antreneaza_ai.bat --pasi 500000 --medii 8`), `5_evalueaza.bat`, actualizat § 9.
3. Opțional: agentul coridor descentralizat (parametri comuni, MPLight) sau pondere mai mare pentru pietoni.

## Stare anterioară (21.10.2026, 01:20) – Borna 8 în lucru

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

### Pașii următori de atunci (istoric; 1–5 făcuți, vezi mai sus)

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
