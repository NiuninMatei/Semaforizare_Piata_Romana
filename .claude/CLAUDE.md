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

## Stare curentă (05.11.2026, ~19:55) – pregătirea pentru M2 (08.11, 08:00, online)

- **Direcția nouă, cerută de autor pe 05.11, ≈19:45 (memoriile m2-ce-e-mai-bun, absenta-6-8-11, iot-si-ioc, buget-tokeni):**
  M2 trebuie să arate ce e mai bun și nou, nu „nu trece nimeni”; o schimbare de fond, aleasă de mine, cu mână liberă la
  modificări fundamentale; proiectul e la IOT și IOC. Limita săptămânală, eșalonat până la ≈100% vineri, 23:00, fără blocaj.
  Programul autorului până la M2 și mutarea repetiției lui: doar în memoria locală absenta-6-8-11, nu în depozit.
- **Decizia (05.11, ≈20:55, după wf_21ebd0cc-784: 5 inventare, 3 planuri, un judecător; tot planul, local, în
  `outputs/prezentare/surse_m2/plan_v3/m2_plan_final.md`):** M2 v3 = camera publică, senzor IoT nesupravegheat al traficului și al
  semaforului, plus un om care supraveghează printr-un ecran verificat. Lucrări noi: programul real pe 2–5.11, după criteriile
  publicate înaintea rulării (`docs/rezultate/program_real_criterii.json`, c7d62d3); modulul testat `vision/fisa_senzor.py`; prezentarea
  v3 (demonstrația pe paginile 3–4, cel mult 3 cifre mari pe pagină, negativul într-un rând, finalul „Încercați”). Runda a doua a
  geamănului e respinsă (Dacia vest 821–1 063 veh/h în cameră, față de ≈520 în geamăn). Nimic înghețat nu se atinge; „Oprește
  imaginea” rămâne obligatoriu. Rezerva: prezentarea v2 de pe 5.11, 14:05. Puncte de control: CP1 (1.11 refăcut identic) și CP2
  (2–4.11) joi seara; 5.11 vineri dimineața; fișa la 11:30; v3 completă la 15:00; vineri, la 22:30, consumul la 97–99%.
- **Repornirea completă a laptopului (05.11, seara, cerută de autor):** înainte, `outputs/live/fara_repornire`, Ctrl+C curat în
  consola ascunsă a colectării (`paznic.trimite_ctrl_c`), apoi oprite paznicul, veghea și cele două lanțuri (adormite până la
  00:15 și 03:30). După repornire: se șterge `fara_repornire`, se pornesc paznicul (care pornește singur colectarea), veghea și
  ambele lanțuri cu `--reia`, se cere din nou keep-awake, iar golul colectării se trece în `outputs/logs/reporniri_2026-11-05.csv`.

- **Măsura nouă e înghețată la commitul cffd50e (03.11, 10:13), publică din 03.11, 14:10, înainte de a privi datele din 3.11** (§ 9.11,
  memoria geaman-coliziuni): cererea în `config/factori_v2.json` și `cerere_v2.py`, excluderile în `config/excluderi_cor.json`, pragurile în
  `docs/rezultate/praguri_geaman.json`. Poarta trece pe 8 din 12 ore de antrenare; Dacia vest rămâne sub cameră în zilele lucrătoare.
  Măsurile nu se mai schimbă. Rezultatele pe `zi_*`, `capacitate_*` din 28.10 încoace, inclusiv −7%, nu mai sunt valabile.
- **Lista candidaților e fixată (3.11):** `config/candidati_v2.json` = PLAN_60_40_3, PLAN_45_30_3, models/ppo_e15.zip; raportat
  ACTUATED (§ 9.11). **Validarea din 4.11 s-a încheiat pe 5.11, la 04:16: poarta trece pe 0 din 4 ore, deci validarea e doar descriptivă
  și niciun candidat nu trece.** Decizia, octet cu octet, e în `docs/rezultate/cor_decizie_2026-11-04.json` (commitul 460b947, 05.11,
  04:23). Zilele 5–7.11 se prelucrează noaptea doar până la geamăn și poartă, fără strategii, și nu se desigilează (verificat în cod:
  `pasi_dupa` dă doar „geaman”, chiar desigilat). `--regula-finala` răspunde deja „niciun candidat nu a trecut de validare: runda s-a
  încheiat, rămâne planul observat”; pe 8.11, dimineața, se rulează totuși, cum s-a scris. Lanțul vechi nu se mai desigilează.
- **Zilele de 3.11 și 4.11, prelucrate și comise:** poarta trece pe 0 din 5 ore pe 3.11 și pe 0 din 4 ore pe 4.11 (ora de dimineață
  se suprapune cu vârful și iese). Pe 4.11, la vârf, la prânz și seara, Dacia vest are 396–516 veh/h în geamăn, față de 867–922 în
  cameră, și 2,2–6,6% vehicule neintrate; în ora liniștită, 25 de teleportări pe rulare și Dacia est cu 18% sub cameră. Rapoartele, în
  § 9.11, iar fișierele, în `docs/rezultate/*2026-11-0[34]*`. Rulările strategiilor din zilele descriptive nu se citează ca procente.
  Geamănul în timp real rămâne pe planul observat până după M2. **Diagnoza (4.11, doar citire, verificată în fișiere):** Dacia vest e
  frânată de cutia dintre linia de oprire și inel (keepClear pe nodurile legate prin muchii scurte și cedarea de la îmbinarea 5280746678);
  teleportările de noapte vin din REAL, care ia ciclul din mediana valurilor (358,8 s, față de 124,5 s în spectru). Raportul și dovezile,
  local, în `outputs/diagnoza/dacia_vest_2026-11-04*`. Reparațiile sunt pentru o rundă nouă, după M2; până atunci nu se atinge
  `rejucat.py`, fiindcă lant_cor îl citește în fiecare noapte.
- **Reparațiile, pe ramura locală `reparatii-dupa-m2`** (copia `C:\Users\Matei\Documents\GitHub\Semaforizare_reparatii`, fără push;
  nu se mai atinge până după M2):
  - **3078dc0:** REAL cu ciclul din spectru, rețeaua v3 cu keepClear oprit în cutia Daciei vest, poarta v3 ca propunere și rulatorul
    `probe_geaman`;
  - **755efbd:** rezultatele probelor din 4.11, cu 355 de rulări;
  - **8c01dd7:** amprenta intrărilor în cheia rulărilor.

  Raportul, verificat de trei ori, e local, în `outputs/diagnoza/probe_reparatii_2026-11-04.md`:
  - V0 reproduce exact runda înghețată;
  - V1 scoate teleportările de noapte;
  - V2 ridică ritmul Daciei vest, dar blochează circular inelul în 5 rulări, lasă mai multe vehicule pe zebre și mută întârzierea pe
    Catargiu și Dacia est.

  După M2, doar cu acordul autorului: V1 se poate adopta, V2 nu. Întâi se compară verdele Daciei vest din programul rejucat cu valurile
  camerei, fără date noi; apoi vin clipurile îmbinării.
- **Push din linia de comandă, din 03.11:** fără GitHub Desktop și fără computer use, deci fără ferestre de aprobare; comanda, în
  „Reguli operative”. Desktop rămâne rezervă (memoria push-prin-github-desktop).
- Rolurile: 3.11 antrenare, 4.11 validare, 5–6.11 test, 7.11 generalizare. **Invitațiile la sondare au plecat pe 03.11, 21:00–21:02**
  (patru apropiați, cu ordinea ecranelor fixată în link, și colegii de an, cu un link și ordinea la întâmplare); textele și linkurile,
  local, în `outputs/sondare/mesaje_2026-11-03.txt` și `linkuri_2026-11-03.txt`. Sondarea se închide sâmbătă, 7.11, la 18:00; apoi
  `--rezumat`, `--publica` și pagina 5 a prezentării. **Pagina v2 (03.11, seara, cerută de autor, fiindcă textul se putea corecta în formular):**
  fără răspunsurile așteptate la vedere, cu cod de control la final și „de la capăt” cu confirmare; textele modificate nu se numără,
  iar o a doua trecere în aceeași filă doar cu confirmarea autorului în `outputs/sondare/confirmari.json` (§ 8). Răspunsurile se
  copiază exact din foaia formularului în `outputs/sondare/primite/R<n>.txt`; `--rezumat` arată la „de știut” ce nu se numără.
- **Prezentarea M2:** schița „demonstrația întâi” (03.11, 21:17), cu revizia din 3.11, 23:20, aplicată pe 4.11 dimineața: ≈3,5 minute
  de demonstrație pe laptop din ≈6 min, limbaj simplu, 8 pagini; pe pagina 8, lângă fiecare verdict, potrivirea cu camera („X din Y
  ore”). Totul în `outputs/prezentare/surse_m2` (sablon_m2.html, construieste_m2.py, exporta_m2.py, verifica_m2.py; scenariul
  demonstrației, întrebările probabile și deciziile, în NOTE_M2.md; prima ciornă, în `ciorna_1/`). Loc gol: doar pagina 5 (sâmbătă,
  după 18:00). Pagina 8 e completă din 5.11: „Proba: nu trece nimeni: simularea s-a potrivit cu camera pe 0 din 4 ore. Decizia: nu a
  mai avut loc; rămâne programul de azi.” A doua revizie, pe 5.11, după validare (wf_224f8d89-b21, 8 agenți, doar citire; 21 de
  constatări confirmate din 51): benzile paginilor 3 și 6 și rândul pietonilor de pe pagina 6, aduse la surse; textul paginii 8 și
  răspunsurile din NOTE_M2.md, aduse la rezultat, plus două întrebări noi; README-ul și § 9.11, aduse la zi. Rezultatul întreg, local,
  în `surse_m2/revizie_m2_0511.json`, iar rezumatul, la sfârșitul NOTE_M2.md. Pe 8.11 se pornesc doar geamănul și serverul dispeceratului, direct cu Python, după
  `scripts\_mediu.bat`, în două file de Windows Terminal (NOTE_M2.md, pasul de la 07:35), niciodată `PORNESTE_TOT.bat`, care ar porni
  o a doua colectare. Fără desigilări, ziua de 7.11 e gata pe 8.11 pe la 03:45 (doar geamănul), deci dimineața nu mai rulează simulări.
  **Proba tehnică a demonstrației (5.11, 19:20–19:28, fără autor):** pornirea ca pe 8.11 și părțile 1 și 2 merg ca în note (faza
  pe Dacia, aplicată în 16,5 s; alerta, la ≈11 s; revenirea singură, la ≈9 s; camera, 5,9–6,1 cadre/s); clicul pe „Oprește imaginea”
  a fost refuzat de clasificatorul modului automat, deci rămâne, cu zoomul și ferestrele, pentru repetiția autorului. Detaliile, la
  sfârșitul NOTE_M2.md.
- **M1 prezentată pe 01.11.2026** (punctaj maxim, ≈15 min): `docs/prezentari/Prezentare_M1.pdf`; sursele, local, în
  `outputs/prezentare/surse_m1`. Prezentările următoare sunt mult mai scurte.
- **Commit-urile lucrului pentru M2 încep cu „Borna M2: …”** (lista schimbărilor dintre borne, § 12.3).
- **Planul și deciziile autorului:** memoriile borne-curs și laptop-disponibil; planul verificat, cu dovezi:
  `outputs/prezentare/surse_m2/verificare_plan_m2.json`. Bugetul: memoria buget-tokeni. Regulile zilelor noi: § 9.11.
- **Rulează în fundal, pornite pe 01.11 (până după M2):** `run_vision` (de la 09:04; jurnalul brut în
  `data/trajectories_brute`), paznicul (`outputs/logs/paznic_<zi>.log`), veghea (`outputs/logs/veghe_2026-11-01.csv`) și
  prelucrarea de noapte (`romana.lant_zilnic --bucla`, la 00:15; `outputs/lant/<zi>/`), plus, din 03.11, lanțul măsurii noi
  (`romana.lant_cor --bucla`, la 03:30; `outputs/lant_cor/<zi>/`). După o repornire a aplicației se pornesc din nou: paznicul,
  veghea și ambele lanțuri, cu `--reia`.
- **Înaintea oricărei opriri voite a colectării:** întâi fișierul `outputs/live/fara_repornire`, altfel paznicul o repornește.
- **Sondarea cu oameni:** pagină publică în `docs/sondare` (GitHub Pages), fără laptop; după orice schimbare în `static/` se refac
  fișierele cu `python -m romana.dashboard.sondare --pachet`. Dispeceratul și pagina sondării sunt înghețate din 03.11 seara (commitul
  „Borna M2: înghețul dispeceratului și al paginii de sondare…”); textele ghidului s-au refăcut pe înțelesul oricui pe 03.11, ≈20:45,
  înaintea primei invitații. Linkurile au plecat pe 03.11, deci `static/` nu se mai schimbă până la închiderea sondării. Adresa
  formularului stă doar în `outputs/sondare/formular.json`, niciodată în depozit (§ 4.5, § 8).

## Reguli operative

- **Git:** în Git Bash, `git` (Git for Windows, cu Git Credential Manager, care are deja conectarea contului).
  Mesajul de commit într-un fișier nou, UTF-8 fără BOM, cu `git commit -F`; commit doar pe fișiere numite, fără `git add -A`.
  Push: `GCM_INTERACTIVE=never GIT_TERMINAL_PROMPT=0 git -c credential.username=NiuninMatei push origin main` (fără numele contului,
  git se oprește să întrebe ce cont folosește); grupat, niciodată în timpul simulărilor, fără să cer voie; înainte verific ce ajunge
  public (memoria push-prin-github-desktop).
- **GitHub CLI:** `C:\Users\Matei\AppData\Local\Programs\GitHubCLI\bin\gh.exe` (2.103.3), conectat pe 03.11 ca NiuninMatei, cheia în
  Windows: depozite, issues, versiuni, Actions, Pages, gists, proiecte, discuții, pachete, profil, organizații, webhook-uri, Codespaces;
  fără ștergerea depozitelor sau a pachetelor și fără cheile de securitate ale contului (memoria github-cli-acces).
- **Cât colectează camera:** nu se ating `run_vision.py`, `stream.py`, `od_counter.py`, `config/camera.json`,
  `config/demand.json`, `vtypes*`; `veghe.py` citește `fps` din `state.json`. `signals.py` nu se schimbă. Scenariile
  `zi_2026-10-2[89]_*` nu se regenerează sub același nume. `run_vision` se oprește doar curat (Ctrl+C), altfel jurnalul
  gzip se poate strica. Calculele grele merg la prioritate scăzută.
- **Date și imagini:** pietonii doar agregat; traiectoriile brute rămân local, public doar vehiculele. Imaginile camerei:
  cel mult 1–2 capturi estompate, cu sursa „Webcam România – https://webcamromania.ro”. Clipurile de calibrare rămân doar
  local, nu intră în commit, se șterg după folosire (memoria borne-curs).
- **Rămase pentru autor:** GitHub Support #4909163 (refs/pull/1/head); după evaluarea academică, ștergerea jurnalului local
  complet (data/trajectories_brute, outputs/referinta, outputs/sondare, outputs/copie_scratchpad_*, copia istoricului original,
  imaginile din jurnalele sesiunilor; § 4.5), plus formularul și foaia de calcul ale sondării, din contul Google.
- **Istoricul stărilor de lucru (până pe 01.11):** `.claude/stare_arhiva.md`; nu se încarcă automat, se citește la nevoie.

# Compact instructions

La rezumare, păstrează: mesajele autorului cu decizii, cuvânt cu cuvânt; lucrările în curs, cu PID-urile, ID-urile și căile
fișierelor; ce e comis și ce nu; cifrele verificate, cu sursa lor; ce am promis și până când. Deciziile durabile sunt deja în
memorie și în acest fișier, deci nu le repeta pe larg. Renunță la ieșirile lungi de comenzi și la conținutul fișierelor, care
se pot reciti.
