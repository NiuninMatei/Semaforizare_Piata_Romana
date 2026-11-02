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

## Stare curentă (02.11.2026, ~05:30) – pregătirea pentru M2 (08.11, 08:00, online)

- **Geamănul a fost corectat pe 02.11 (§ 6.5, memoria geaman-coliziuni):** rezultatele pe `zi_*`, `capacitate_*` din 28.10 încoace, inclusiv −7%, stau pe coliziuni și teleportări și nu mai sunt valabile. Măsura nouă `cor_*` folosește geamănul v2 (`romana.network.retea_v2`, `config/retea_v2.json`, `config/demand_v2.json`). Orice simulare nouă raportează teleportările și ciocnirile. Referința regulilor din § 9.11 e planul observat, 71/40/12.
- **M1 prezentată pe 01.11.2026** (punctaj maxim, ≈15 min): `docs/prezentari/Prezentare_M1.pdf`; sursele, local, în
  `outputs/prezentare/surse_m1`. Prezentările următoare sunt mult mai scurte.
- **Commit-urile lucrului pentru M2 încep cu „Borna M2: …”** (lista schimbărilor dintre borne, § 12.3).
- **Planul și deciziile autorului:** memoriile borne-curs și laptop-disponibil; planul verificat, cu dovezi:
  `outputs/prezentare/surse_m2/verificare_plan_m2.json`. Bugetul: memoria buget-tokeni. Regulile zilelor noi: § 9.11.
- **Rulează în fundal, pornite pe 01.11 (până după M2):** `run_vision` (de la 09:04; jurnalul brut în
  `data/trajectories_brute`), paznicul (`outputs/logs/paznic_<zi>.log`), veghea (`outputs/logs/veghe_2026-11-01.csv`) și
  prelucrarea de noapte (`romana.lant_zilnic --bucla`, la 00:15; `outputs/lant/<zi>/`). După o repornire a aplicației se pornesc
  din nou: paznicul, veghea, lanțul cu `--reia`.
- **Înaintea oricărei opriri voite a colectării:** întâi fișierul `outputs/live/fara_repornire`, altfel paznicul o repornește.
- **Sondarea cu oameni:** pagină publică în `docs/sondare` (GitHub Pages), fără laptop; după orice schimbare în `static/` se refac
  fișierele cu `python -m romana.dashboard.sondare --pachet`. Linkurile de invitație: `--linkuri`, abia după reparațiile din
  `static/index.html`; adresa formularului stă doar în `outputs/sondare/formular.json`, niciodată în depozit (§ 4.5, § 8).

## Reguli operative

- **Git:** `C:\Users\Matei\AppData\Local\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe` (în Git Bash merge `git`).
  Mesajul de commit într-un fișier nou, UTF-8 fără BOM, cu `git commit -F`; commit doar pe fișiere numite, fără `git add -A`.
  Push doar prin GitHub Desktop, grupat, niciodată în timpul simulărilor (memoria push-prin-github-desktop).
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
