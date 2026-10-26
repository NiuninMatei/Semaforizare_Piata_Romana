# Semaforizare Piața Romană

Semaforizarea inteligentă a intersecției Piața Romană din București, folosind **doar infrastructura existentă**:
camera publică live → viziune artificială (YOLO11 + ByteTrack) → geamăn digital SUMO, replică fidelă a rețelei →
agenți de învățare prin întărire și planuri clasice, comparați pe date reale de trafic → dispecerat pentru operator.

Proiect pentru disciplinele *Interfețe om-calculator* și *Internet of Things*, Universitatea Transilvania din Brașov,
Facultatea de Matematică și Informatică, Informatică ID, anul III. Autor: **Niunin Matei-Gabriel**.

**Toată documentația – metoda, rezultatele, limitările, ghidul de utilizare, jurnalul proiectului și bibliografia –
este într-un singur document: [docs/DOCUMENTATIE.md](docs/DOCUMENTATIE.md)** (și în PDF, cu pagini numerotate:
[docs/DOCUMENTATIE.pdf](docs/DOCUMENTATIE.pdf)).

Pornire rapidă (Windows): `scripts\0_instalare.bat` (o singură dată), apoi `scripts\PORNESTE_TOT.bat`.

**Licențe** (detalii în fișierul [NOTICE](NOTICE) și în documentație, § 14.1):

* codul și modelele antrenate: [GNU AGPL v3 sau ulterioară](LICENSE) – obligatorie pentru modulul de viziune, care
  folosește Ultralytics YOLO11 (AGPL-3.0), și extinsă la tot codul;
* extrasul OpenStreetMap, rețeaua SUMO, cererea și scenariile (`data/osm/`, `sumo/`): [ODbL 1.0](LICENSES/ODbL-1.0.txt),
  © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright);
* numărătorile și traiectoriile vehiculelor (`data/counts/`, `data/trajectories/`): [ODbL 1.0](LICENSES/ODbL-1.0.txt),
  © 2026 Niunin Matei-Gabriel, în măsura în care asupra lor există drepturi;
* documentația și rezultatele: [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Rezultatele și modelele conțin informații din
  OpenStreetMap, © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0.

Simulatorul folosit este Eclipse SUMO (EPL-2.0 OR GPL-2.0-or-later). Datele de trafic sunt derivate din fluxul public
al camerei Piața Romană difuzat de Webcam România; drepturile asupra imaginilor aparțin operatorului camerei,
neidentificat public (Webcam România declară că nu deține drepturi asupra fluxurilor). Versiunea curentă a depozitului
nu conține imagini din cameră. Asistent generativ: Claude (Anthropic) – documentația, cap. 13.
