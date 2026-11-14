# Instrucțiuni pentru Claude – proiectul „Semaforizare Piața Romană”

Acest fișier (`.claude/CLAUDE.md`) este citit automat de Claude Code la deschiderea proiectului; nu face parte din documentație (singura documentație: `docs/DOCUMENTATIE.md`). Conține regulile
autorului și o stare scurtă a lucrului (secțiunea „Stare curentă”, adusă la zi la fiecare bornă); starea amănunțită a
lucrului stă într-un fișier local, neversionat.

## Regulile autorului (Niunin Matei-Gabriel)

- Limba proiectului, a documentației, a comentariilor și a mesajelor de commit: **română**.
- **Commit după fiecare modificare de impact, push grupat, de câteva ori pe zi** (profesorul coordonator urmărește
  istoricul; cum se face push-ul scrie la „Reguli operative”).
  Mesajele încep cu „Borna N: …” pentru pașii de bornă. Încheiați mesajele cu linia
  `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>` (din 10.11.2026, la cererea autorului: modelul nou se notează
  drept contributor; până atunci, cu Opus 5.5, linia a fost `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` pe
  20–26.10, în 96 de commit-uri, apoi `Co-Authored-By: Claude <noreply@anthropic.com>`, în 156).
- Lucrul este organizat pe **borne** (vezi `docs/DOCUMENTATIE.md` § 12); nu se deviază de la ideea principală.
- **Rețeaua rutieră trebuie să fie replica fidelă a realității** (OpenStreetMap): nu se modifică
  geometria, benzile, sensurile, trecerile sau pozițiile semafoarelor. Se schimbă DOAR modul în care
  semafoarele existente răspund traficului (programul/fazele/durata) – singurul lucru implementabil real.
- În simulare intră **toți participanții observabili pe cameră**: autoturisme, autobuze/troleibuze,
  camioane, motociclete, bicicliști, pietoni (și orice altă categorie care apare).
- Cererea de trafic se calibrează pe datele camerei, nu trafic aleatoriu; ipotezele se declară explicit.
- Bibliografia: note de subsol cu licențe. Asistent generativ: modulul AI Google (ciorna, până la
  18.10.2026), apoi Claude (Anthropic) de la 20.10.2026: cu modelul Opus 5.5 până pe 10.11.2026, cu Fable 5.2 de atunci
  (declarat în § 13, § 14 și README).
- **Consumul (cererea autorului din 10.11.2026):** munca se eșalonează, iar limita săptămânală se atinge cel mult vineri,
  la 23:00, niciodată înainte (un blocaj oprește lucrul); cele mai bune rezultate la consumurile cele mai mici, cu consum
  mai mare doar unde aduce rezultate net superioare. Detaliile și măsurătorile: memoria buget-tokeni.
- Lucrați **local, pe calculatorul autorului** cât timp e posibil; cloud doar dacă local nu se poate.
- **Laptopul e al autorului (din 13.11.2026):** cât e folosit, local rulează doar text, git și citire; lucrul greu (teste,
  SUMO, capturi, exporturi, Chrome fără fereastră) rulează doar când calculatorul stă nefolosit, după controlul din
  `outputs/plan_m4/unelte/inactiv.ps1`, și se oprește la prima folosire. Colectarea continuă se încheie duminică, 15.11,
  după „gata” la M3; de atunci, nimic al proiectului nu mai rulează de la sine pe laptop. Hotărârile de după o analiză le
  ia asistentul și le spune scurt.
- **Viața privată a autorului (regulă din 14.11.2026):** în depozit nu intră nimic despre persoana autorului în afara
  numelui și a calității de autor: nici program, nici ocupație, nici absențe, nici obiceiuri, nici mesajele lui redate.
  Regula privește fișierele, mesajele de commit, documentația, prezentările și orice alt loc public. Starea amănunțită a
  lucrului și arhiva ei stau doar local, neversionate, iar un control la commit și la push refuză ce o încalcă.

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

## Stare curentă (14.11.2026)

- Bornele M1 (01.11) și M2 (08.11) s-au ținut. M3: duminică, 15.11.2026, online; prezentarea M3 e gata.
- Colectarea continuă de la cameră se încheie duminică, 15.11, după M3; setul de numărători se închide cu ziua de 14.11.
- Lucrul pentru bornele următoare (M4, 22.11; M5) se pregătește pe ramuri locale și se publică la borna lui.
- Pe 14.11.2026, istoricul public a fost rescris: versiunile mai vechi ale acestui fișier și arhiva stărilor de lucru au
  fost retrase, iar nouă mesaje de commit au fost reformulate. De aceea, codurile commit-urilor făcute din 21.10.2026
  încoace s-au schimbat (primele 16 au rămas aceleași); conținutul celorlalte fișiere a rămas același, la fiecare pas.
- Starea amănunțită a lucrului (procese, sarcini programate, pașii zilei) stă local, în `.claude/stare_locala.md`,
  neversionat, și se citește la începutul fiecărei sesiuni:

@stare_locala.md

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
- **Rămase pentru autor:** după evaluarea academică, ștergerea jurnalului local
  complet (data/trajectories_brute, outputs/referinta, outputs/sondare, outputs/copie_scratchpad_*, copia istoricului original,
  imaginile și textele sondării din jurnalele sesiunilor, copiile de lucru ale sondării din scratchpad; § 4.5), plus formularul și
  foaia de calcul ale sondării, din contul Google (primirea răspunsurilor e oprită din 8.11).
- **Portul dispeceratului:** se verifică cu `curl -s -o /dev/null -m 3 http://127.0.0.1:8050/` (codul 7 = liber) ori
  după procese; `Get-NetTCPConnection -LocalPort 8050 -State Listen` a dat 0 pe 14.11, cât serverul răspundea cu 200.
- **Workflow-uri întrerupte:** se reiau cu `resumeFromRunId` (merge și după repornirea aplicației); înainte de a șterge
  ceva rămas de la ele, citesc `journal.jsonl` din dosarul lor: un agent cu rând „result” nu mai rulează la reluare.
- **Istoricul stărilor de lucru:** `.claude/stare_arhiva.md`, local, neversionat din 14.11.2026; nu se încarcă automat, se
  citește la nevoie.
- **Paza datelor personale (din 14.11.2026):** `.git/hooks/pre-commit`, `commit-msg` și `pre-push` (locale) refuză
  fișierele locale de stare, cuvintele care țin de persoana autorului și orice commit din istoricul vechi; nu se ocolesc
  (`--no-verify` e interzis). Istoricul dinaintea rescrierii din 14.11 stă doar local (`refs/copie/2026-11-14/*`) și nu
  se publică niciodată; se șterge odată cu jurnalul local, după evaluare.

# Compact instructions

La rezumare, păstrează: mesajele autorului cu decizii, cuvânt cu cuvânt; lucrările în curs, cu PID-urile, ID-urile și căile
fișierelor; ce e comis și ce nu; cifrele verificate, cu sursa lor; ce am promis și până când. Deciziile durabile sunt deja în
memorie și în acest fișier, deci nu le repeta pe larg. Renunță la ieșirile lungi de comenzi și la conținutul fișierelor, care
se pot reciti.
