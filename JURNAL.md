# Jurnalul proiectului – „Semaforizare Piața Romană”

Povestea construirii proiectului, pe scurt: ce am încercat, ce nu a mers, ce am corectat și de ce. Este scris pentru
oricine vrea să înțeleagă cât efort – tehnic, dar și de răbdare – stă în spatele unui rezultat care, la final,
încape într-un tabel. Detaliile tehnice complete sunt în [`docs/DOCUMENTATIE.md`](docs/DOCUMENTATIE.md), iar istoricul
exact al modificărilor în commit-urile „Borna N: …” de pe GitHub.

**Echipa.** Autor și coordonator: Niunin Matei-Gabriel – a stabilit obiectivele și regulile (rețea fidelă, toți
participanții, date reale, doar programul semaforului se schimbă), a verificat pe teren și în imagini, a corectat
greșelile și a venit cu ideile-cheie. Implementarea: asistentul AI Claude (Anthropic), prin Claude Code, rulând local
pe laptopul autorului (fără placă video dedicată). Ciorna inițială (până la 18.10.2026): modulul AI Google.

---

## Etapa 0 – de la ciornă la un proiect serios (până la 20.10.2026)

* Ciorna inițială avea o rețea „agregată” (piața ca un singur nod), trafic aleatoriu și un agent fără verificare.
  A fost auditată și păstrată în `legacy/`, iar proiectul a fost restructurat pe **borne** (B0–B9).
* Regula de bază, stabilită de autor de la început: **nu se schimbă nimic din infrastructură** – doar felul în care
  semafoarele existente răspund traficului, singura schimbare implementabilă imediat în realitate.

## Etapa 1 – rețeaua fidelă și toți participanții (noaptea de 20–21.10)

* **Replica fidelă din OpenStreetMap**: 16 semafoare fizice grupate într-un singur controler, grupuri de semnal,
  treceri, trotuare, benzi STB. *Provocare:* opțiunea de import al trecerilor din OSM bloca `netconvert` (crash în
  SUMO 1.28) → trecerile reconstruite geometric.
* *Provocare:* **inelul pieței se bloca singur**. Diagnostic: ieșirile din piață primeau roșu; soluția – verde
  permanent pentru ieșiri, pietonii de pe ieșiri într-o fază proprie.
* *Provocare:* liniile de bază „mințeau”: programul actuated avea faze greșite, Webster citea chei vechi,
  Max-Pressure bloca inelul alegând faze fără dozare → toate reparate și restricționate la fazele reale.
* *Provocare – „agentul care trișa”:* agentul pentru coridor ținea vehiculele **în afara rețelei** (nu intrau, deci
  nu apăreau în cozi). Soluția: vehiculele care așteaptă să intre contează în recompensă ca unele oprite.

## Etapa 2 – ochii sistemului: camera live (21.10)

* Căutarea camerelor publice: în zona modelată există doar camera Piața Romană → intersecțiile vecine sunt
  simulate din datele ei.
* *Provocare – viteza:* fără placă NVIDIA, detecția rula cu **0,9 cadre/s** (prea puțin pentru urmărire). Mutată pe
  placa grafică Intel prin OpenVINO → **~5–6 cadre/s**.
* *Provocare – numărări absurde:* mașini numărate „Magheru → Magheru” (întoarceri false) și mașini de pe inel
  numărate ca intrări pe Dacia vest → regula de numărare rescrisă pe traiectoria întreagă (ordinea zonelor, sensul
  de mers, „capăt de traiectorie” pentru brațele îndepărtate); zonele Dacia vest mutate.
* *Provocare – blocaje la intrarea în simulare:* rutele porneau chiar de la linia de oprire → pornesc acum de la
  capătul bulevardelor.
* *Provocare logistică:* git nu avea credențiale în linia de comandă → push-ul se face prin GitHub Desktop, condus
  automat. Laptopul rula la 1,69 GHz (mod de economisire) → autorul a trecut pe „Cea mai bună performanță”.

## Etapa 3 – primele rezultate pe date reale (22.10)

* Două zile de trafic real (21.10 11:45 – 22.10 11:00), 10 scenarii, 300 de simulări: agentul AI **−4,6%** față de
  planul fix – un prim succes.
* Corecturile autorului: strada se numește **Calea Dorobanți**; intersecția Dacia × Polonă e **sens unic de ieșire**,
  deci nu are ce căuta în coridorul controlat.
* Experimente negative, documentate cinstit: agentul care vede cozile din amonte, agentul preantrenat prin imitație,
  orizontul mai lung, coordonarea cu 4 vecini (+35%). Diagnostic important: **68% din întârzierea la vârf** vine din
  coada de pe Bd. Dacia vest, dincolo de piață – un plafon fizic pe care niciun semafor nu-l poate depăși complet.

## Etapa 4 – sistemul rulat live, cap-coadă (seara de 22.10)

* Rulând tot sistemul live (camera, geamănul SUMO, dispeceratul) au ieșit la iveală defecte reale: viziunea se oprea
  când dispeceratul citea imaginea; geamănul revenea pe date de rezervă la fiecare 15 minute; imaginea camerei mergea
  2 s și stătea 4 s (camera trimite bucăți de câte 6 s → tampon de redare de 8 s); dispeceratul arăta 1 cadru/s
  (→ flux video continuu); vehiculele din SUMO „săreau” (→ pași de 0,2 s).
* Privind imaginea analizată, autorul a observat că zonele de pe cameră erau desenate greșit – cea mai memorabilă
  greșeală: **marcajul de staționare interzisă confundat cu trecerea de pietoni de pe Magheru**. Toate zonele au fost
  redesenate, cu 7 treceri în loc de 2.

## Etapa 5 – datele corectate răstoarnă rezultatul (23.10)

* Autorul a desenat el însuși zonele pe capturi ale camerei. Localizarea lor automată a cerut potrivire de imagini
  (SIFT) – *provocare:* decupajele aveau fond transparent, citit inițial greșit; scara corectă (3288/1920) a fost
  dedusă din potrivirile sigure.
* Renumărarea celor două zile cu zonele corecte: virajele urmărite complet au crescut de la 2 800 la 4 995.
* **Momentul de adevăr:** pe scenariile corecte, agentul care dădea −4,6% a ajuns la **+5,2%** (mai slab decât planul
  fix la vârf). Rezultatul frumos de ieri era construit pe date greșite – și l-am raportat ca atare.
* O greșeală a mea, corectată de autor: am „văzut” în Street View o singură bandă pe Dacia est; în realitate sunt
  două pe sens, iar rețeaua era corectă.

## Etapa 6 – căutarea soluției: specialiști în loc de un agent universal (24–25.10)

* Reantrenarea scurtă a agentului (E2) l-a înrăutățit; cu pași de învățare de 10 ori mai mici (E3) a devenit cel mai
  bun la prânz. Ideea care a deblocat proiectul: **un program pe tipuri de trafic** – agentul AI acolo unde e cel mai
  bun, un plan fix bine reglat la vârf.
* Lucrul s-a făcut în condiții reale de viață: într-o cafenea cu prize până la plecarea autobuzului, cu opriri pentru
  masă și cu procesorul limitat la 75% cât autorul avea nevoie de calculator.
* Agentul antrenat de la zero cu 1 milion de pași (E4) nu a fost mai bun decât cel vechi; specialiștii pentru trafic
  greu (E5–E7) au ajuns cel mult la nivelul celui mai bun plan fix; specialistul pentru trafic lejer (E9) a fost puțin,
  dar sigur, mai bun.
* *Lecția zgomotului:* diferențe de 1–2 puncte își schimbau semnul între seed-urile de validare și cele de test →
  validare cu 5 seed-uri stabilită dinainte, teste statistice pe perechi și 10 seed-uri de test.
* **Rezultatul:** programul pe tipuri de trafic, **−6,9%** față de planul fix (p = 0,0003; mai bun în 79 din 100 de
  rulări) și −3,2% față de cea mai bună metodă clasică; pe o **duminică nevăzută**, cu alt tipar de trafic, agenții AI
  au rămas mai buni decât planul fix (−4,9…−6,5%).

## Etapa 7 – „ești sigur că numeri corect?” (25.10)

* Întrebarea autorului a dus la un audit al numărării: camera număra **1,6 ieșiri pentru fiecare intrare**. Cauza,
  văzută pe harta capetelor de traiectorie: pe inelul din fundal vehiculele sunt atât de mici încât detectorul le
  pierde oriunde – iar o mașină pierdută în dreptul ieșirii Catargiu părea „ieșită”.
* Încercarea de a corecta regula pe criteriul conservării (fiecare vehicul care intră trebuie să iasă) a arătat că
  ieșirile spre Dacia vest și Căderea Bastiliei **nu pot fi deosebite** de vehiculele pierdute, oricum s-ar regla
  pragurile.
* **Ideea autorului, adoptată:** semaforul controlează doar intrările, deci **volumele se iau doar din intrări**, iar
  ieșirile servesc doar la proporțiile de viraj (din traiectoriile complete). Tot de aici: comutarea programului live
  se face după debitul real măsurat la intrări.
* Tot la propunerea autorului: un **test cu participanți indisciplinați** (blocarea intersecției, trecerea pe roșu
  proaspăt, schimbări agresive de bandă, pietoni pe roșu) – realitatea străzilor din București.

---

## Ce am învățat

1. **Datele bune contează mai mult decât algoritmul.** Cea mai mare schimbare de rezultat nu a venit din AI, ci din
   corectarea zonelor de pe cameră.
2. **Un rezultat bun trebuie să supraviețuiască verificării.** −4,6% a devenit +5,2% când datele au fost corectate;
   l-am raportat și am căutat o soluție mai bună în loc să-l ascundem.
3. **AI-ul nu e o baghetă magică, dar e util acolo unde e potrivit.** Un singur agent nu bate un plan fix bine reglat
   la vârf; combinat inteligent cu planuri clasice, aduce un câștig semnificativ – și se adaptează la zile noi, lucru
   pe care un plan fix nu-l face.
4. **Rezultatele negative sunt rezultate.** Coridorul, agentul universal, specialiștii nereușiți – fiecare a îngustat
   drumul spre soluția bună și e documentat.
5. **Ochiul omului rămâne indispensabil.** Marcajul confundat cu o trecere, banda „lipsă” de pe Dacia, ideea de a
   număra doar intrările – toate au venit de la autor.
