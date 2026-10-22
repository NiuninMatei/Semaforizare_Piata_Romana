# Observații de la evaluarea prin demonstrație (22.10.2026, seara)

Demonstrație live, cap-coadă, a sistemului, în format de susținere: autorul în rolul profesorului
coordonator, Claude în rolul studentului care prezintă. Fiecare observație este notată aici cu ce s-a
făcut pentru ea (rezolvat / planificat), ca să rămână în istoricul proiectului.

Pașii demonstrației: 1 – camera și viziunea artificială; 2 – geamănul digital SUMO; 3 – dispeceratul și
preluarea controlului; 4 – comparația măsurată (`scripts\9_demo_comparatie.bat`); 5 – rezultate și limite.

## Probleme găsite și rezolvate la pregătirea demonstrației

| # | Problemă | Rezolvare |
|---|---|---|
| P1 | Viziunea se oprea cu `PermissionError` când dashboard-ul citea cadrul live | înlocuirea fișierelor tolerează citirea simultană; `state.json` scris atomic |
| P2 | Geamănul revenea pe profilul de referință în primul minut al fiecărui interval de 15 min | păstrează ultimele debite bune ale camerei (max. 20 min) |
| P3 | Imaginea camerei mergea ~2 s și stătea ~4 s (segmente HLS de 6 s) | tampon de redare cu întârziere fixă de 8 s: cadre la 0,17 s, fără pauze |
| P4 | Fereastra camerei tăia imaginea când era micșorată | fereastră redimensionabilă, imagine scalată |
| P5 | SUMO-GUI pornea cu toată rețeaua, piața greu de găsit | vederea pornește centrată pe piață |

## Observațiile profesorului

| # | Observație | Ce s-a făcut |
|---|---|---|
| O1 | Zona trecerii de pe Magheru era desenată pe marcajul hașurat din fața chioșcului, care înseamnă „staționarea interzisă”; trecerea reală e mai în stânga, suprapusă cu zonele Magheru | **Rezolvat:** `trecere_magheru` mutată pe zebra din marginea stângă a cadrului (x 0–0,07) |
| O2 | `magheru_in` și `magheru_out` prea late, fiecare pătrundea pe sensul celeilalte | **Rezolvat:** despărțite pe axa bulevardului (ieșirea sus, 0,50–0,555; intrarea jos, 0,555–0,63), fără suprapunere |
| O3 | `mendeleev_out` prea sus și prea îngustă (carosabilul e mai jos); lipsea trecerea de pe Mendeleev | **Rezolvat:** zona coborâtă și lățită pe carosabil; `trecere_mendeleev` adăugată |
| O4 | `dacia_vest_in` / `dacia_vest_out` suprapuse fără logică; lipsea trecerea | **Rezolvat:** intrarea pe partea stângă a drumului, ieșirea pe partea dreaptă (circulație pe dreapta); `trecere_dacia_vest` adăugată |
| O5 | `catargiu_in` prea jos și prea în dreapta; `catargiu_out` nu trebuie să prindă vehiculele care continuă pe inel; lipsea trecerea | **Rezolvat:** intrarea mutată mai sus și la stânga; ieșirea îngustată spre gura străzii (plus condiția de capăt de traiectorie și sensul de mers); `trecere_catargiu` adăugată |
| O6 | `caderea_bastiliei_out` prea jos și prea în dreapta; lipsea trecerea | **Rezolvat:** zona mutată pe gura străzii; `trecere_caderea_bastiliei` adăugată |
| O7 | `dacia_est_in` era deasupra intrării reale; `dacia_est_out` nu acoperea toată ieșirea | **Rezolvat:** intrarea pe carosabilul dintre trotuarul de sus și insula cu stâlpișori; ieșirea extinsă pe toată lățimea de sub insulă; trecerea din dreapta sus (`trecere_dacia_est_nord`) separată de cea de jos |
| O8 | Mișcarea din dispecerat și din SUMO este sacadată | **Rezolvat:** dispeceratul primește camera ca flux MJPEG continuu (`/api/video`, fiecare cadru analizat, măsurat 6,4 cadre/s, față de o imagine reîncărcată o dată pe secundă); geamănul SUMO rulează în pași de 0,2 s întinși pe secunda reală (înainte, pași de 1 s: o mașină „sărea” ~14 m), cu logica semaforului neschimbată, pe secunde |
| O1–O7 | Consecință: numărătorile din 21–22.10 au fost făcute cu zonele vechi | **Măsurat (renumărare din traiectorii, aceeași fereastră 21.10 11:45 – 22.10 11:00, într-un folder separat):** intrări 25 827 → 18 402 (Catargiu −48%, Magheru −33%, Dacia vest −21%, Dacia est +5%); ieșiri Mendeleev 420 → 4 178 (zona veche era pe clădire), Căderea Bastiliei −39%, Magheru −27%; pietoni 12 595 → 11 495; cele 4 treceri noi îndepărtate nu au prins pietoni (persoanele de acolo sunt prea mici în imagine pentru detector). Ieșirile rămân de ~2× intrările (Catargiu out 15 313) → zona Catargiu out trebuie încă verificată pe zi. **Planificat:** renumărarea din jurnalul de traiectorii (`recount`) cu zonele noi → regenerarea scenariilor (`scenarii_zi`) → reevaluarea agenților; cele 5 treceri noi se verifică pe lumină de zi |
