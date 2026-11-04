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

## Stare curentă (04.11.2026, ~05:00) – pregătirea pentru M2 (08.11, 08:00, online)

- **Măsura nouă e înghețată la commitul cffd50e (03.11, 10:13), publică din 03.11, 14:10, înainte de a privi datele din 3.11** (§ 9.11,
  memoria geaman-coliziuni): cererea în `config/factori_v2.json` și `cerere_v2.py`, excluderile în `config/excluderi_cor.json`, pragurile în
  `docs/rezultate/praguri_geaman.json`. Poarta trece pe 8 din 12 ore de antrenare; Dacia vest rămâne sub cameră în zilele lucrătoare.
  Măsurile nu se mai schimbă. Rezultatele pe `zi_*`, `capacitate_*` din 28.10 încoace, inclusiv −7%, nu mai sunt valabile.
- **Lista candidaților e fixată (3.11, commitul „Borna M2: lista candidaților…”), nu se mai schimbă:** `config/candidati_v2.json` =
  PLAN_60_40_3, PLAN_45_30_3, models/ppo_e15.zip; raportat ACTUATED (§ 9.11). Pe 4.11 (validare, seed-urile 11–15) un candidat trebuie să
  bată PLAN_72_48_3 și REAL. Decizia validării (`outputs/validare/cor_decizie_2026-11-04.json`, pe 05.11 pe la 04:30) se copiază în
  `docs/rezultate/` și se comite înaintea oricărei desigilări. Fiecare zi de test și de generalizare se desigilează noaptea, după buclă,
  pe 3 procese, cu `bash outputs/unelte/desigileaza_zi.sh <zi> "<termen>"` pornit în fundal (verifică decizia comisă și completitudinea,
  nu citește rezultate). Regula finală: `python -m romana.lant_cor --regula-finala`, abia după toate cele trei zile (pe 8.11, dimineața),
  cu fișierele și ordinea din cod; până atunci nu se citesc rezultatele zilelor de test. Lanțul vechi nu se mai desigilează
  (§ 9.11, precizările din 3.11). Rezultatele zilei de 3.11 se raportează, dar nu schimbă lista.
- **Ziua de 3.11, prelucrată de ambele lanțuri pe 4.11 (lant_cor gata la 04:51) și comisă:** poarta trece pe 0 din 5 ore. La vârf,
  dimineața și la prânz, Dacia vest are 410–510 veh/h în geamăn, față de 820–920 în cameră, și 2,4–5,4% vehicule neintrate; în ora
  liniștită pică la teleportări; seara, la pierderea de detecție pe întuneric. Ziua e doar descriptivă. Raportul e în § 9.11, iar
  fișierele, în `docs/rezultate/*2026-11-03*`. Ziua de validare, 4.11, poate ieși la fel; atunci niciun candidat nu trece, testul nu se
  deschide (lant_cor o face singur), iar pagina 8 a prezentării spune asta. **Alarma pentru 4.11** (`alarma_lant.sh`, termen 05.11,
  09:30) rulează. Când sună: copiez decizia în `docs/rezultate` și o comit; desigilarea o pornesc doar dacă a trecut un candidat.
  Geamănul în timp real rămâne pe planul observat până după M2.
- **Push din linia de comandă, din 03.11:** fără GitHub Desktop și fără computer use, deci fără ferestre de aprobare; comanda, în
  „Reguli operative”. Desktop rămâne rezervă (memoria push-prin-github-desktop).
- Rolurile: 3.11 antrenare, 4.11 validare, 5–6.11 test, 7.11 generalizare. **Invitațiile la sondare au plecat pe 03.11, 21:00–21:02**
  (patru apropiați, cu ordinea ecranelor fixată în link, și colegii de an, cu un link și ordinea la întâmplare); textele și linkurile,
  local, în `outputs/sondare/mesaje_2026-11-03.txt` și `linkuri_2026-11-03.txt`. Sondarea se închide sâmbătă, 7.11, la 18:00; apoi
  `--rezumat`, `--publica` și pagina 5 a prezentării. **Pagina v2 (03.11, seara, cerută de autor, fiindcă textul se putea corecta în formular):**
  fără răspunsurile așteptate la vedere, cu cod de control la final și „de la capăt” cu confirmare; textele modificate nu se numără,
  iar o a doua trecere în aceeași filă doar cu confirmarea autorului în `outputs/sondare/confirmari.json` (§ 8). Răspunsurile se
  copiază exact din foaia formularului în `outputs/sondare/primite/R<n>.txt`; `--rezumat` arată la „de știut” ce nu se numără.
- **Prezentarea M2:** schița „demonstrația întâi” (03.11, 21:17), verificată pe surse la 21:45: ≈3,5 minute de demonstrație pe laptop
  din ≈6 min 10 s, limbaj simplu, 8 pagini care trec `verifica_m2.py`. Totul în `outputs/prezentare/surse_m2` (sablon_m2.html,
  construieste_m2.py, exporta_m2.py, verifica_m2.py; scenariul demonstrației și deciziile, în NOTE_M2.md; prima ciornă, în
  `ciorna_1/`). Locuri goale: pagina 5 (sâmbătă, după 18:00) și pagina 8 (proba pe 5.11, decizia pe 8.11). Pe 8.11 se pornesc doar
  `6_geaman_digital.bat` și `7_dashboard.bat`, niciodată `PORNESTE_TOT.bat`, care ar porni o a doua colectare. **Pe 5.11, după
  validare:** din duratele reale ale lanțului estimez dacă 7.11 se termină pe 8.11 până la ≈06:30; altfel, desigilarea zilei de 7.11
  pe mai multe procese, cu nota în § 9.11.
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
