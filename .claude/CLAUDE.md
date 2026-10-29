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

## Stare curentă (29.10.2026, ~08:30) – testul final: câștigă planul fix 12/14/12, confirmarea pe 29.10; pauză pentru repornire

- **Testul pe 28.10 (lanțul scratchpad\test28.py, 29.10 00:15–02:27, toți pașii exit 0):** ziua 28 completă
  (96 de intervale, 58 557 intrări; calitatea 1–6% goluri), publicată în data/; 12 scenarii × seed-urile 1–10 × 7
  strategii = 840 de simulări (`docs/rezultate/test_28_*.csv`). `romana.control.decizie` → **PLAN_12_14_12**
  (`decizie_2026-10-28.json`): toți trei candidații eligibili față de REALIST (12/14/12 −6,9% din total, p = 0,0013;
  TOD_DEBIT −7,2%; E13 −6,0%), TOD_DEBIT = 12/14/12 (p = 0,90) → cel mai simplu. Pe persoană (20/40/70): același.
  Regula inițială: E13 ar fi trecut (p = 0,0001). Raportate: 16/10/12 singur 56 747 h (cel mai mic total, ns față de
  12/14/12, p = 0,51), oficialul singur 57 823 h. **Câștigul vine de la pietoni** (−12% vs fix; vehiculele +1–2%).
- **Aplicat (aprobarea autorului):** `live_twin.py` `VARIANTA_PROGRAM = "plan_scurt"`, outputs/live/command.json
  `{"mod":"program"}`, eticheta din dispecerat; § 9.10 nou, § 9.7 punctul 7, § 1/§ 2/§ 4.6/§ 9.4/§ 10/§ 12.1, Anexa A,
  § 11.8, README; modul nou `romana.control.totaluri` (tabelele § 9.10); `decizie` afișează diferențele în ore.
- **28.10, 03:46–04:28: prelucrarea încetinită, NU imagine înghețată** (corectat pe 29.10, ≈09:30, după întrebarea
  autorului O18 și doi agenți independenți): pozițiile mașinilor parcate fluctuează normal, autobuze traversează la
  04:08 / 04:10, nicio traiectorie repetată; pasul median dintre puncte 0,17 → ≈0,7 s (≈1,4 cadre/s, pauze de ≈6 s),
  deci ByteTrack pierde vehiculele în mișcare (de 4–5 ori mai puține cadre). Cauza probabilă: validarea E14
  (03:04–04:48) rula în paralel (nesigur: pe 29.10 noaptea lanțul testului a încetinit doar ușor, 0,19–0,22 s, fără
  intervale încetinite). Episoade similare: 27.10 01:15–02:45 (sfertul 02:15 sub prag), 26.10 16:45, 25.10
  02:55–03:08 (scurt); 21, 22, 29.10 (până la 09:15) nimic. Fereastra liniștită din 28.10 (56 veh/h) e subestimată;
  decizia fără noapte: aceeași (p = 0,000005). `calitate` caută acum direct rata de cadre (încetinit: ≥ 40% pași >
  0,5 s; exact 9 intervale pe 21.10–29.10 09:15, restul < 30%); `scenarii_zi --fara-incetinite` (implicit oprită; nefolosită la confirmare,
  protocolul de pe 28.10). Calculele grele: doar la prioritate scăzută cât timp camera colectează.
- **29.10, 03:00–04:30:** verificarea independentă (4 agenți) – cifrele confirmate, protocolul respectat, corecturi
  comise (04a6e1f); `romana.control.treceri`: cu 12/14/12 nicio trecere nu are sub 12 s de verde pe ciclu (faza
  de pietoni, ca în planul de referință; trecerile din două faze 29–31 s în loc de 45–53 s); **sensibilitatea pietonală** (`sens_pietoni_28_*.csv`): 12/14/18 vs
  36/28/18 −7,9% din total (92/120, p < 0,000001), 12/14/18 ≈ 12/14/12 (p = 0,96) – ghidurile europene: 1,2 m/s
  (RiLSA, TRL; nicio normă românească publică găsită). Zonele de vehicule pe traiectoriile din 28.10: 94% din
  vehiculele în mișcare ating o zonă; restul = fragmente pe inel + 96 / 489 traiectorii/zi în colțurile de jos (< 1%)
  – partea cu imaginea (fundal median, OSM) rămâne pentru ziua, la lumină (scratchpad\zone_vehicule28.py).
- **29.10, ≈08:33 – pauză pentru repornirea calculatorului** (cererea autorului: actualizarea Claude Desktop și o
  repornire completă; oprirea după 08:30, ca fereastra fixă de dimineață 07:30–08:30 a zilei de confirmare să rămână
  întreagă). Colectarea oprită curat (Ctrl+C în consola ascunsă → `counter.flush()`; scratchpad\oprire_curata.py,
  încercat întâi pe un proces de probă), lanțul test29 oprit, jurnalul zilei verificat cap-coadă
  (scratchpad\verifica_jurnal.py; ora opririi și ultima traiectorie în outputs/logs/oprire_2026-10-29.txt);
  scratchpad-ul copiat în outputs/copie_scratchpad_2026-10-29. `scenarii_zi`: grila completă de 15 min (un gol nu mai e
  sărit de fereastra glisantă; înainte putea da o „oră” falsă sau KeyError la `windows["varf"]`) + `--exclude
  HH:MM-HH:MM`; zilele 21–28.10 neschimbate (verificare independentă).
- **Reluat (29.10, 08:46):** `run_vision` repornit la 08:46:12 (PID 10228; prima traiectorie 08:46:21; gol
  08:33:21–08:46:21, 13 min); noaptea 29.10 fără încetiniri (calitate, goluri 1,1–3,0% pe oră); test29.py
  repornit în fundal cu `scenarii_zi --exclude 08:30-09:00` și oprire dacă calitate / recount eșuează; prioritatea
  BelowNormal a lanțului setată din afară (cea din script nu se aplicase); keep-awake activ. Autorul doarme (după
  tura de noapte) și a lăsat restul în grija mea; întrebarea despre excludere retrasă (premisa era greșită); zonele
  de vehicule pe imagine – ziua, la lumină.
- **Pașii de reluare folosiți (pentru o altă repornire):** (1) `run_vision` fără fereastră: `$env:PYTHONPATH="src"; Start-Process
  .venv\Scripts\python.exe -ArgumentList '-m','romana.vision.run_vision' -RedirectStandardOutput
  outputs\logs\viziune_2026-10-29.log -RedirectStandardError outputs\logs\viziune_2026-10-29.err -WindowStyle Hidden
  -PassThru`, apoi verificat că jurnalul brut al zilei crește; (2) keep-awake; (3) în test29.py, la `scenarii_zi`:
  `--exclude 08:30-<sfertul de după cel al repornirii>` (sfertul opririi, golul și sfertul repornirii, căruia `recount`
  îi dă durata întreagă deși are date doar de la repornire) și oprirea lanțului dacă calitate / recount ies cu cod
  nenul (un membru gzip trunchiat face recount să cadă cu zlib.error), apoi test29.py repornit în fundal (prioritate
  BelowNormal); (4) zonele de vehicule pe imagine, la lumină.
- **De făcut:** 30.10 00:15 test29.py (confirmarea: `--confirma PLAN_12_14_12`) → § 9.10 „Confirmarea” (și golul
  din 29.10 în § 4.6); până pe 30.10 09:30 totul oprit, comis, împins, explicația cap-coadă.

## Stare anterioară (28.10.2026, ~13:00) – „cel mai bun câștigă”, cazurile după debit, testul pe 28.10

- **28.10, ~01:00:** Webcam România și-a dat **acordul scris** (e-mail, 27.10, 20:27): analiza automată în scop
  academic, necomercial, cu sursa „Webcam România – https://webcamromania.ro”, și publicarea a 1–2 capturi cu
  persoanele estompate (documentat în § 4.5, § 10, § 12.5, § 14.1, § 14.2, README, NOTICE). PS-ul lor: vor linkul
  proiectului – autorul a aprobat să le trimit eu răspunsul (ziua, „Bună ziua!”, semnătura după un rând liber; memoria
  stil-email), după publicarea capturilor (de luat ziua, la lumină; persoanele + numerele estompate; REUSE.toml are
  șablonul de adnotare). GitHub Support #4909163 (refs/pull/1/head): doar confirmarea automată, fără răspuns.
- **Geamănul calibrat (tau = 0,8 s) e implicit din 28.10** (decizia autorului): `build_demand.VTYPE_DEFS` →
  `vtypes.add.xml`, plus `vtypes_indisciplinat.add.xml`; `capacitate_*` rămân doar pentru § 9.9 / E14. Rezultatele
  9.1–9.8 = istorice (tipurile din 75592d3; Anexa A „arborele curent, tipurile vechi”).
- **Protocolul:** testul E13 vs programul realist se mută pe **miercuri 28.10** (27.10 incompletă, oprită la 06:04);
  scenariile `zi_2026-10-28_*` / `indisciplinat_zi_2026-10-28_*` (calibrate implicit), seed-urile 1–10, ambele
  comportamente, `romana.vision.calitate` întâi; 29.10 = zi de confirmare. Colectarea live repornită pe 28.10, 00:10
  (PID în outputs/logs/viziune_2026-10-28.*). Laptopul rămâne pornit cât cer, cel mult până pe 30.10, 10:00.
- **28.10, ~05:30 – lanțul de noapte 2 încheiat și publicat:** noaptea zilei 27 (00:00–06:04) publicată în data/;
  seed-urile 6–10 pe luni (§ 9.9, „Verificarea pe 10 seed-uri”: E13 −9,2% / −7,9% vs fix, −3,9% vs realist pe 120 de
  perechi); **E14 negativ** (`ppo_romana_e14`, validare 26.10 seed-urile 11–15: −6,3% vs fix, +2,2% vs E13, p = 0,06 /
  0,09; § 9.5) → **E13 rămâne singurul candidat**, protocolul neschimbat. Aprobarea autorului (28.10) trecută în § 9.9:
  dacă E13 trece regula, `live_twin.py` trece automat pe E13 și se documentează (subcapitol nou în cap. 9).
- **28.10, 09:30–10:15 – capturile publicate (8b4579e):** un singur cadru (09:30, ploaie) → `docs/imagini/camera_*.jpg`
  (figurile 4.1 / 4.2, și în README); estompate persoanele, plăcuțele apropiate și reclama „Notar…” suprapusă de cameră;
  verificare pe 9 dale în două runde (19 locuri scăpate + 14 incerte estompate); cadrul brut șters;
  `LicenseRef-Toate-drepturile-rezervate` (LICENSES/, REUSE.toml, NOTICE). **Răspunsul către Webcam România trimis pe
  28.10, 10:11** (firul 1a178a0160eff9ba; linkul proiectului și al PDF-ului). GitHub Support: tot fără răspuns.
- **28.10, ~10:30 – grila de planuri fixe pe geamănul calibrat (§ 9.9, `docs/rezultate/grila_calibrat.csv`):** 23 de
  planuri pe validarea 26.10 (seed-urile 11–15); ciclurile scurte câștigă: 12/14/12 −9,3% vs fix, −0,9% vs E13 (ns);
  `TOD_FIX` (16/10/12 lejer + moderat, 12/14/12 greu) −10,8% / −2,3% (ales pe aceleași date). Intră în test ca
  **strategii raportate** (scratchpad\test28_extra.json, cu `referinte`); regula de decizie neschimbată; dacă un plan
  fix iese mai bun decât E13, alegerea rămâne a autorului (degajarea pietonilor: cea mai lungă trecere 12,8 m, § 10).
- **28.10, ≈12:30 – decizia autorului: „cel mai bun câștigă”** (ideea proiectului mutată: cea mai bună combinație
  implementabilă pe cazuri de trafic din date reale, nu un agent AI cu orice preț; § 1, § 2, § 9.9, § 12, README).
  Cazurile după debitul echilibrat: lejer < 2 400, intens > 4 100 veh/h (din 26.10; de reverificat pe fiecare zi nouă,
  cerința autorului, eventual o treaptă intermediară – doar după o nouă validare). Candidați: PLAN_12_14_12, TOD_DEBIT
  (16/10/12 lejer + mediu, 12/14/12 intens), E13; în vigoare: REALIST. Regula: `romana.control.decizie` (cea mai mică
  pierdere totală; semnificativ mai bun decât REALIST; nesemnificativ mai slab în niciun comportament; la egalitate,
  cel mai simplu). 29.10 = confirmare (revenire la REALIST doar dacă câștigătorul e semnificativ mai slab).
  `live_twin.py`: variantele e13 / plan_scurt / tod_debit, pragurile 2 400 / 4 100, planurile fixe urmărite secundă cu
  secundă; implicit tot "realist" până la decizie. Pe validare, regula ar alege PLAN_12_14_12 (egal cu TOD_DEBIT).
- **28.10, ≈13:30 – observațiile autorului (O17):** plăcuțele tuturor vehiculelor estompate în imaginea publicată
  (figura zonelor refăcută); zonele de trecere corectate înainte de test: Mendeleev mutată pe zebra marcată din OSM
  (calea 1104820827, proiectată cu docs/rezultate/referinta/model_camera.json; locul real e acoperit – ≈0 pietoni
  detectați), trecere_dacia_est_intrare prelungită până la zebra de jos (2 786 de traiectorii treceau prin golul
  dintre zone). Efect: pietonii +6% pe 26.10; vehiculele neschimbate. Grija autorului: zonele se verifică pe date
  (harta traiectoriilor, OSM, fundal median) înainte de schimbare; jurnalul nu depinde de zone (recount, fără
  colectare nouă). Zonele de vehicule: de reverificat cu aceeași metodă după test (factorii din referinta factori).
- **28.10, ≈14:30 – măsura pe persoană (întrebarea autorului: câți oameni sunt într-un autobuz?):** nu se poate vedea
  și nu există date publice (doar vehiculele STB noi au numărătoare, TPBI / Google Maps) → ocupări declarate cu
  sensibilitate: autoturism 1,2 (EEA), autobuz 20 / 40 / 70; `validare` păstrează acum pierderea pe tipuri
  (pierdere_h_<tip>, suma = pierdere_h, verificat identic cu rezultatele publicate); `romana.control.ocupare`
  scrie CSV-ul pe persoană; lanțurile 28 / 29 rulează `decizie` și pe el (raportat, nu schimbă decizia).
- **De făcut:** după 29.10 00:15, lanțul scratchpad\test28.py (calitate → recount + --publica → scenarii_zi →
  indisciplinat → test seed-urile 1–10 → analizele → `romana.control.decizie` → decizie_2026-10-28.json) → setez
  `VARIANTA_PROGRAM` = varianta_live din JSON, eticheta din dashboard, § 9.10 nou; 30.10 00:15 test29.py (confirmare).

## Stare anterioară (27.10.2026, ~05:20) – documentație unică, capacitatea geamănului, testul pe ziua de luni (§ 9.9)

- **Singura documentație: `docs/DOCUMENTATIE.md`** (+ `docs/DOCUMENTATIE.pdf`, `python -m romana.doc_pdf`); GHID.md,
  JURNAL.md, OBSERVATII_EVALUARE.md au fost integrate (cap. 11 ghid, cap. 12 jurnal); README = prezentare scurtă;
  acest fișier mutat în `.claude/` (cererea autorului: un singur document mare, cu capitole și subcapitole).
- Cererea: `echilibrare: "doar_intrari"` (implicit, marginea de jos; ideea autorului – semaforul controlează intrările);
  marginea de sus = „medie” (scenariile din istoricul git). Auditul numărării: ieșiri/intrări = 1,6; ieșirile
  îndepărtate nu se pot deosebi de vehiculele pierdute (§ 4.3).
- Rezultate (cap. 9): programul pe tipuri de trafic – marginea de sus −6,9% (p = 0,0003; E9 / E3 / plan 46/48/12),
  marginea de jos −1,5% pe 10 seed-uri (actuated / E3 / plan fix actual; ales pe validare 11–15; E3 instabil la prânz); duminica 25.10: −5,2% / −4,5%;
  **participanți indisciplinați** (`vtypes_indisciplinat.add.xml`, `indisciplinat_*.sumocfg`): E3 −14,1% (p = 0,00001; 40/50),
  E9 −9,9% (p = 0,003) față de planul fix pe 10 seed-uri, până la −28% la vârf.
- Defect corectat: `control/env.py` ignora tipurile de participanți din scenariu (primul test de indisciplină invalid).
- **Program realist** (ales pe validare cu participanți indisciplinați): lejer → `ppo_romana`, moderat + greu → E3;
  −16,0% vs plan fix (p = 0,00001; 42/50), −18,4% vs actuated – varianta implicită în `live_twin.py`
  (`VARIANTA_PROGRAM = "realist"`; „marginea_sus” = E9 / E3 / plan 46/48/12). Praguri pe debitul echilibrat 1 300 / 2 000.
- Programul realist pe duminică cu participanți indisciplinați, 10 seed-uri: −4,4% (40/50, Wilcoxon p = 0,035);
  agentul oficial singur −7,9% (44/50) (§ 9.4). Colectarea de duminică oprită la ~17:00; datele finale 25.10 comise.
- 26.10: E10 (E3 reantrenat pe participanți indisciplinați) negativ (−6,6% vs −13,4% pe validare). Colectarea de
  luni 26.10 pornită la 09:11 (`run_vision` fără fereastră, jurnal în outputs/logs) → seara `recount` +
  `scenarii_zi --zi 2026-10-26` + test pe ziua nouă (zi lucrătoare nevăzută).
- **26.10, 17:10 – oprit pentru limita de utilizare (reluare după 19:00).** Făcute și publicate: E10/E11 negative;
  licențe (AGPL cod, ODbL date, CC BY doc), capturile camerei scoase; istoricul rescris (filter-repo, copie locală în
  C:\Users\Matei\Documents\Semaforizare_copie_istoric_original, harta în docs/corespondenta_commituri.txt); jurnalul
  publicat doar cu vehicule (brut local în data/trajectories_brute). Autorul: trimite e-mailul Webcam România (ciornă
  în Gmail) și cererea GitHub Support (refs/pull/1/head).
- **Zonele noi – în lucru** (scratchpad\zone_noi): clipuri cadre\, cadre2\, cadre3\ (16:00) + offline_clip*\ (lanțul
  live pe clip); variante S0 (actuale), S1–S4 (prim-plan desenat + fundal proiectat cu model_departe), S3w3/5/8
  (regula pietonilor); numărătoarea de referință (workflow-uri oprite, de reluat cu resumeFromRunId:
  wf_8b88bf65-ea9 clip1, wf_200b60da-663 clip2, wf_23fcd6ad-446 / wf_1545bf0c-1fc Catargiu corectat) – scor cu
  scor_gt.py. Parțial: S0 prinde Magheru 0,84, Dacia est ~1,0, Dacia vest ~0,25 (detecția în fundal); zona hașurată
  din stânga-jos NU e trecere. Test în curs: offline_clip1_2560 (imgsz 2560). Apoi: factori de corecție pe braț,
  renumărare, scenarii, reevaluare, documentație, README (scratchpad\organizare\README_propus.md).
  17:50: rulează local (fără consum de limită) zone_noi\ruleaza_offline.bat: clipurile 1–3 la imgsz 2560 + clipul 3
  la 1600 (jurnale log_c*.txt); 2560 = ~808 s / clip (≈1,3 cadre/s – prea lent pentru live fără alt hardware).
  Atenție: viziune_offline.py trebuie să seteze și rv.TRAJ_RAW_DIR (corectat); fișierul amestecat de reluări a fost
  mutat în zone_noi\reluari_amestecate_2026-10-26.jsonl.gz (nu sunt date live). E-mail Webcam România trimis de autor;
  tichet GitHub Support #4909163 deschis.
- **26.10, 22:40 – făcute și publicate:** zonele refăcute (numărătoarea de referință, § 4.3), factorii de corecție pe braț
  (demand.json), zilele 21/22/25 renumărate, scenariile recalibrate, reevaluarea (§ 9.8: programul realist −6,2% vs fix cu
  indisciplinați, nesemnificativ; −11,7% vs actuated; punct slab: vârfurile ×1,2), README nou. Clipurile și imaginile
  camerei din scratchpad au fost șterse. **Peste noapte:** scratchpad\noapte.py (local) – E12 (E3 continuat) și E13
  (oficial continuat) pe scenariile calibrate, validare 11–15, test 1–5, raport în scratchpad\raport_noapte.md, commit
  local (de împins). Workflow „reproductibilitate” (module validare/analiza/indisciplinat/referinta/calibrare_camera +
  § 11) – de verificat și comis. Colectarea live rulează încă (fișierul zilei 26 în data/trajectories – de mutat în
  trajectories_brute și publicat cu recount --publica după oprire). Buget: limita săptămânală trebuie să ajungă până
  vineri 30.10, 08:00 (memoria buget-tokeni).
- **27.10, ~05:20 – noaptea 26–27.10, făcute:** § 4.6 (21–22.10 subnumărate: urmărire sacadată înainte de tamponul
  HLS de 8 s; `romana.vision.calitate`); § 6.4 capacitatea geamănului (parametrii impliciți se blochează la debitul de
  luni; `tau` = 0,8 s îl servește; `romana.control.capacitate`, `vtypes_capacitate*.add.xml`, scenariile `capacitate_*`);
  § 9.6 localizarea pe cererea calibrată (50–78% coada Dacia vest pe geamănul implicit; cu capacitatea calibrată
  coada dispare, rămâne una la marginea rețelei pe Calea Victoriei, nelămurită – `localizare_varf_capacitate.csv`;
  `romana.control.localizare`); ziua 26 prelucrată
  (scenarii `zi_2026-10-26_*`). E12 (`cand_romana_cal3_100k`) / E13 (`ppo_romana_cal`), reantrenați pe 21–22 calibrate:
  echivalenți cu programul realist pe test (§ 9.5) → nu se adoptă. **§ 9.9, testul pe luni 26.10 cu capacitatea
  calibrată:** E13 −9,5% / −9,7% vs fix (60/60 mai bun decât actuated), oficialul −10,0% / −5,9%, programul realist
  −3,9% (ns) / −6,4%; E3 e veriga slabă (seara, ×1,2). **Protocol fixat:** 26.10 = validare, candidatul E13 singur,
  test pe 27.10 (capacitatea calibrată, seed-urile 1–10, ambele comportamente; vs realist, oficial, fix, actuated);
  E13 înlocuiește programul realist în `live_twin.py` doar dacă Wilcoxon p < 0,05 – decizia finală a autorului.
  Capacitatea calibrată ca implicită (ar schimba toate rezultatele 9.1–9.8) = decizia autorului; deocamdată variantă.
- **De făcut:** oprirea colectării live a zilei 27 (seara) → mutarea fișierului brut în data/trajectories_brute,
  `recount --zi 2026-10-27 --publica`, `scenarii_zi --zi 2026-10-27`, `romana.bridge.indisciplinat` cu `--vtypes
  vtypes_capacitate*.add.xml --prefix capacitate_*` pe `zi_2026-10-27_*`, testul E13 după protocolul din § 9.9;
  reantrenarea pe 26–27 cu capacitatea calibrată; grila de planuri fixe pe geamănul calibrat. Răspunsurile Webcam
  România (e-mail) și GitHub Support (#4909163).
- Pași posibili: reantrenarea agenților pe scenariile „doar intrări” și cu participanți indisciplinați; adnotarea a
  2–3 minute de video pentru a fixa nivelul cererii între cele două margini.
## Stare anterioară (22.10.2026, 16:10) – Bornele 7 și 9 încheiate

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
