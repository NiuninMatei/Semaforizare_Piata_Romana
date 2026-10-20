# Ciorna inițială (asistent generativ: modulul AI Google din Chrome)

Acest director păstrează **neschimbată** versiunea inițială a proiectului, așa cum a fost generată
până la data de 18.10.2026 cu ajutorul modulului AI de la Google integrat în Chrome. Fișierele au
fost mutate aici (cu `git mv`, deci istoricul lor rămâne vizibil) la începutul Bornei 0, ca reper
pentru evaluarea evoluției proiectului.

## Conținut

| Fișier | Rol în ciornă |
|---|---|
| `traffic_vision.py` | Detecție YOLOv8n + numărare pe 3 linii fixe în cadrul camerei |
| `intelligent_traffic.py` | Mediu Gymnasium + PPO (Stable-Baselines3), 2000 de pași |
| `ai_semafor_romana.zip` | Modelul PPO salvat de ciornă |
| `osm.*`, `osm_*` | Scenariu generat cu `osmWebWizard.py` (SUMO 1.28.0), trafic aleator |
| `build.bat`, `run.bat` | Comenzile `randomTrips.py` / `sumo-gui` folosite |

Fișierele de ieșire ale simulării (`tripinfos.xml`, `edgeData.xml`, `stats.xml` etc.) și greutățile
`yolov8n.pt` au fost scoase din arbore (rămân în istoricul Git), fiind rezultate regenerabile.

## Probleme constatate la audit (Borna 0)

### `traffic_vision.py`
1. **Eroare de sintaxă**: `if cls_id not in:` — scriptul nu poate rula deloc.
2. **`NameError`**: `statistics["Autobuze_STB"]` în loc de `statistici[...]`.
3. Numărarea se face pe 3 linii trasate „din ochi” (procente din lățime/înălțime), fără direcție de
   mers; toate trecerile pe linia Magheru sunt considerate „intrări”.
4. Nu există asociere **origine → destinație** (brațul de intrare cu brațul de ieșire), deci
   virajele reale nu pot fi transmise către SUMO.
5. Setul `id_procesate` este golit la 150 de elemente, ceea ce provoacă numărări duble.
6. Rezultatele nu sunt salvate și nu sunt transmise simulării — legătura cameră → SUMO lipsește.

### `intelligent_traffic.py`
1. Starea este construită cu `hash(lane_id) % 5`: în Python 3 `hash()` pe șiruri este randomizat la
   fiecare pornire (PYTHONHASHSEED), deci benzile sunt repartizate aleatoriu între rulări —
   agentul nu poate învăța o politică stabilă.
2. `setPhase()` sare direct între faze verzi, **fără faze de galben** — comportament nesigur.
3. Nu există timp minim de verde, iar recompensa folosește timpul de așteptare al **tuturor**
   vehiculelor din rețea, nu al intersecției controlate.
4. Antrenarea are doar 2000 de pași de decizie (~5,5 ore simulate, un singur episod) și nu există
   nicio evaluare față de o linie de bază (plan fix, actuated etc.).

### Scenariul SUMO
1. Cererea de trafic este **în întregime aleatorie** (`randomTrips.py`), fără legătură cu datele camerei.
2. Statisticile ciornei (`stats.xml`): 1317 teleportări în 6400 s, timp mediu de așteptare 537 s/vehicul
   — rețeaua intră în blocaj, deci orice antrenare pe ea este nerelevantă.
3. Zona importată (~5,2 × 2,5 km, cu pietoni) este mult prea mare pentru antrenare rapidă.

Toate aceste puncte sunt tratate în noua arhitectură descrisă în `docs/`.
