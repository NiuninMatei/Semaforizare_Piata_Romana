# Semaforizare Piața Romană – documentația proiectului

**Semaforizarea inteligentă, bazată pe inteligență artificială, a intersecției Piața Romană din București,
cu date preluate în timp real de pe camera publică Webcam România și simulare în SUMO**

Autor: Niunin Matei-Gabriel · Universitatea Transilvania din Brașov, Facultatea de Matematică și Informatică,
Informatică ID (învățământ la distanță), anul III, grupa 10LD541 · Discipline: *Interfețe om-calculator* și *Internet of Things* ·
Anul universitar 2026–2027

Documentația: © 2026 Niunin Matei-Gabriel, licența CC BY 4.0 (§ 14.1) · Conține informații din OpenStreetMap,
© OpenStreetMap contributors, ODbL 1.0 – https://www.openstreetmap.org/copyright · Sursa fluxului video:
Webcam România – https://webcamromania.ro, care și-a dat pe 27.10.2026 acordul scris pentru folosirea fluxului
(§ 14.1) · Codul sursă, sub licența GNU AGPL v3, și datele: https://github.com/NiuninMatei/Semaforizare_Piata_Romana

---

> **Corectură importantă, 2.11.2026.** Testul final din § 9.9–9.10 și câștigul de −7% al planului 12/14/12, prezentate și la borna M1,
> **nu mai sunt valabile**: simulările rulau pe un geamăn cu coliziuni și teleportări în masă. Explicația, programul real al semaforului,
> măsurat din cameră, și geamănul corectat sunt în § 6.5. Geamănul corectat nu e validat: § 6.5 spune ce se potrivește cu camera și ce nu.
> Noile reguli sunt în § 9.11. Celelalte capitole descriu proiectul așa cum era la data scrierii lor și se corectează pe rând.
>
> *Completare din 6.11:* măsurile geamănului corectat s-au înghețat pe 3.11, la commitul `cffd50e`, înainte de a privi datele din 3.11.
> Poarta, adică verificarea lui oră cu oră față de cameră, trecea atunci pe 8 din cele 12 ore comparate la îngheț, din 25 și 26.10 și
> din 1 și 2.11. Pe primele zile prelucrate după îngheț n-a mai trecut pe nicio oră: nici pe cele 5 din 3.11, nici pe cele 4 din 4.11,
> mai ales fiindcă, la orele încărcate, geamănul duce pe Dacia vest cam jumătate din traficul măsurat de cameră. Validarea din 4.11
> a fost deci doar descriptivă: niciun candidat nu a trecut, runda s-a încheiat pe 5.11 fără un program nou, iar în geamăn rămâne
> planul observat, 72/48/3 (§ 9.11). Asta nu arată că planul observat e cel mai bun, ci doar că geamănul nu a putut judeca. Direct din
> cameră, după criterii publicate înaintea rulării, ciclul real al semaforului a avut pe 2, 3, 4 și 5.11 mediana zilei de ≈135–137 s,
> iar un ciclu de ≈91 s nu apare (§ 6.5).
>
> *Completare din 8.11:* zilele de test, 5 și 6.11, și sâmbăta de 7.11, ziua de generalizare, s-au prelucrat doar până la geamăn și
> poartă, fără strategii. Poarta a trecut pe 1 din 5 ore pe 5.11, pe 1 din 4 ore pe 6.11 și pe toate cele 5 ore pe 7.11, dar pe
> Dacia vest, care nu e un rând al porții, geamănul tot duce, în orele încărcate, mai puține vehicule decât camera, deci nu e validat. Pe 8.11, regula
> finală a confirmat că runda s-a încheiat fără un program nou. Programul real s-a măsurat, după aceleași criterii, și pe 6 și 7.11:
> pe toate cele șase zile, 2–7.11, mediana zilei e de ≈133–137 s (§ 6.5, § 9.11).

## Cuprins

- [Legendă: notații, termeni și abrevieri](#legendă-notații-termeni-și-abrevieri)

1. [Context și motivație](#1-context-și-motivație)
2. [Obiective și cerințe](#2-obiective-și-cerințe)
3. [Arhitectura sistemului (perspectiva IoT)](#3-arhitectura-sistemului-perspectiva-iot)
4. [Modulul de viziune artificială](#4-modulul-de-viziune-artificială)
5. [Puntea cameră → simulare: cererea de trafic calibrată](#5-puntea-cameră--simulare-cererea-de-trafic-calibrată)
6. [Rețeaua rutieră în SUMO](#6-rețeaua-rutieră-în-sumo)
7. [Controlul inteligent al semafoarelor](#7-controlul-inteligent-al-semafoarelor)
8. [Interfața om-calculator: dispeceratul](#8-interfața-om-calculator-dispeceratul)
9. [Rezultate](#9-rezultate)
10. [Limitări, aspecte etice și lucrări viitoare](#10-limitări-aspecte-etice-și-lucrări-viitoare)
11. [Ghid de utilizare](#11-ghid-de-utilizare)
12. [Jurnalul proiectului](#12-jurnalul-proiectului)
13. [Asistență generativă](#13-asistență-generativă)
14. [Bibliografie și licențe](#14-bibliografie-și-licențe)
- [Anexa A. Fișierele de rezultate](#anexa-a-fișierele-de-rezultate-docsrezultate)

## Legendă: notații, termeni și abrevieri

O trimitere de forma (§ 4.6) arată unde este explicat pe larg un subiect: aici, capitolul 4, subcapitolul 6. Paragrafele
care încep cu „Pentru specialiști” dau detalii tehnice și pot fi sărite fără să se piardă firul. Ce e valabil azi se află în § 6.5 și
§ 9.11, limitele sunt în § 10, iar rezultatele din § 9.1–9.10, afară de rândul lui E15 din § 9.5, rămân ca istoric. Tabelele de mai jos explică notațiile, termenii și abrevierile folosite des, cu
trimitere la locul unde sunt prezentate în detaliu.

**Notațiile**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| 12/14/12, 36/28/12, 16/10/12, 46/48/12 | Un plan fix, scris prin secundele de verde ale celor trei faze, în ordine: nord–sud, est–vest și pietoni. Planul 12/14/12 a câștigat testul final, rezultat retras pe 2.11 (§ 6.5), iar 36/28/12 este planul de referință, o ipoteză infirmată de cameră; cu galbenul și roșul de degajare, ciclul lor durează ≈53 s, respectiv ≈91 s. Planul 16/10/12 este celălalt plan scurt, iar 46/48/12 a fost ales pentru traficul greu în programul marginii de sus. În 12/14/18 și 36/28/18, faza de pietoni e lungită la 18 s. | § 6.3, § 9.9, § 9.10 |
| N–S, E–V | Cele două axe ale pieței și fazele lor: nord–sud, între Bd. Magheru și Bd. Lascăr Catargiu, prin mijlocul pieței, și est–vest, pe Bd. Dacia, în jurul insulei centrale. | § 6.3 |
| O–D | Origine–destinație: brațul pe care intră un vehicul și cel pe care iese. Matricea O–D arată câte vehicule merg de la fiecare intrare la fiecare ieșire. | § 4.3, § 5.1 |
| veh/h | Vehicule pe oră, unitatea debitului; veh/h/bandă înseamnă vehicule pe oră pe o singură bandă. | § 5.4 |
| h | Ore. Pierderea de timp se adună pentru toți participanții: 10 oameni care pierd câte 6 minute însumează 1 h. Orele adunate pe vehicule se mai numesc vehicul-ore, iar cele adunate pe oameni, ore-om. „h pe pereche” este media diferențelor în ore dintre două strategii, calculate pereche cu pereche. | § 7.5, § 9.1 |
| % | Diferența față de strategia de comparație, de obicei planul de referință: un procent negativ înseamnă mai puțin timp pierdut, deci un câștig, iar unul pozitiv, timp pierdut în plus. „Din pierderea totală” compară sumele orelor pierdute. „Media pe perechi” și „media pe scenarii” sunt mediile diferențelor procentuale calculate pereche cu pereche, respectiv scenariu cu scenariu; ele dau unei ore de noapte aceeași greutate ca unei ore de vârf. | § 9.1, § 9.10 |
| p | Rezultatul unui test statistic: cât de probabil ar fi să apară doar din întâmplare o diferență cel puțin la fel de mare, dacă strategiile ar fi de fapt la fel de bune. Sub 0,05, diferența se numește semnificativă. 7·10⁻⁸ înseamnă 0,00000007; „p (t / Wilcoxon)” dă valorile celor două teste, în această ordine. | § 9.1 |
| mai bun în k din n, k / n | În câte dintre cele n perechi de simulări strategia a pierdut mai puțin timp decât cea cu care e comparată. | § 9.1 |
| ×1,2 și ×0,8 | Scenariile de sensibilitate: aceeași oră, cu numărul de vehicule înmulțit cu 1,2 la vârf, respectiv cu 0,8 la ora liniștită; pietonii rămân aceiași. Ele trebuiau să acopere incertitudinea măsurării, dar pe unele brațe ea e mai mare: pe Dacia vest, la vârfurile zilelor lucrătoare, debitul real poate fi de ordinul 750–1 250 de vehicule pe oră (§ 6.5). | § 5.4 |
| intervalele de 15 minute | Unitatea de timp a numărătorilor: camera adună vehiculele și pietonii pe sferturi de oră. Pe aceeași grilă se aleg ferestrele scenariilor. Un program pe cazuri de trafic ar comuta în geamănul în timp real după debitul sfertului de oră în curs, dar din 2.11 geamănul rulează implicit planul observat, un plan fix, care nu comută (§ 5.5). | § 4.3, § 5.4, § 9.9 |
| § | Trimitere la un capitol sau subcapitol al acestui document: § 9.10 înseamnă capitolul 9, subcapitolul 10. După numele unei licențe, de exemplu AGPL § 13, trimite la o secțiune a acelei licențe. | tot documentul |
| ≈, –, … | ≈ înseamnă „aproximativ”; 4–6 sau −6,0…−7,2% arată un interval, de la prima valoare la a doua. | tot documentul |
| ± | „Media ± abaterea standard”: valoarea medie și cât se abat de obicei rezultatele de la ea, de la un seed la altul. | § 7.5 |
| 28.10, AAAA-LL-ZZ | Datele scurte sunt din 2026: 28.10 înseamnă 28 octombrie 2026. În numele fișierelor, data se scrie an-lună-zi, ca în `zi_2026-10-28_varf`; orele sunt în formatul de 24 de ore. | tot documentul |
| s, m, m/s, px | Secunde, metri, metri pe secundă și pixeli, adică punctele din care e formată imaginea. | tot documentul |
| Borna N, B0–B9, M1–M5 | Bornele B0–B9 sunt etapele lucrului; fiecare apare în istoricul GitHub prin commit-uri care încep cu „Borna N: …”. M1–M5 sunt bornele cursului, adică prezentările proiectului, notat la ambele discipline, *Interfețe om-calculator* și *Internet of Things*: M1 s-a prezentat pe 1.11, M2 pe 8.11, iar M3 se prezintă pe 15.11. Commit-urile dintre două prezentări încep cu „Borna M2: …”, „Borna M3: …” și așa mai departe. | § 12.3 |
| R1–R8, O1–O18, P1–P10 | R1–R8 sunt cerințele din tema proiectului; O1–O18, observațiile autorului; P1–P10, problemele găsite la rularea sistemului. | § 2, § 12.2 |

**Traficul și semafoarele**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| braț | Fiecare dintre cele șase străzi care pleacă din piață. Bd. Magheru, Bd. Lascăr Catargiu, Bd. Dacia vest și Bd. Dacia est au dublu sens; Str. Mendeleev și Str. Căderea Bastiliei au sens unic, de ieșire din piață. | § 4.3 |
| inel | Carosabilul din jurul insulei centrale a pieței, pe care se circulă ca într-un sens giratoriu; axa N–S trece prin mijlocul pieței. | § 6.2, § 6.3 |
| fază | Intervalul în care au verde doar anumite mișcări, compatibile între ele. Planul de referință, o ipoteză, folosește trei faze: N–S, E–V și faza de pietoni, cu verde pe toate trecerile. La semaforul real, camera arată două etape lungi, N–S și E–V, și o golire scurtă a centrului, iar pe Dacia est și pe Magheru pietonii traversează în timpul etapelor de vehicule (§ 6.5). Alte două faze, „fără dozare”, deschid deodată toate intrările spre inel; ele blochează piața, de aceea nu se folosesc implicit. | § 6.3, § 7.1 |
| ciclu | Timpul după care fazele se repetă: toate verzile, plus 5 s după fiecare fază, adică 3 s de galben și 2 s de roșu de degajare. Pentru 12/14/12: 12 + 14 + 12 + 3 × 5 = 53 s; pentru planul de referință, 91 s. La un ciclu scurt, fiecare fază și fiecare trecere primesc verde mai des. | § 6.3, § 7.4 |
| verde | Cât timp, în secunde, are verde o fază. Controlerul impune un verde minim de 10 s și un verde maxim de 90 s. Excepție face etapa scurtă de 3 s din planul observat și din planurile candidate din 3.11, 60/40/3 și 45/30/3: în ea doar se golește centrul, fără pietoni (§ 11.5). | § 6.3, § 7.2 |
| galben | Cele 3 s de galben care încheie un verde, pe legăturile care se schimbă. | § 7.2 |
| roșu de degajare | Cele 2 s de după galben, cu roșu pe legăturile care se schimbă, ca intersecția să se golească înaintea fazei următoare; se numește și roșu general. Legăturile care rămân verzi și în faza următoare își păstrează verdele. | § 6.3, § 7.2 |
| legătură, grup de semnal, controler | Legătura este o mișcare comandată de semafor, cu semnalul ei, de exemplu de pe o bandă de intrare spre una de ieșire. Un grup de semnal reunește legăturile care primesc mereu aceeași culoare. Controlerul este automatul care conduce semnalele unei intersecții: cele 16 semafoare fizice ale pieței formează în simulare un singur controler, `romana`, cu 61 de legături. | § 6.2, § 6.3 |
| debit | Câte vehicule sau câți pietoni trec într-o oră, în veh/h sau pietoni/h. Pentru cererea unui braț sau a pieței, textul spune adesea „volum”. | § 5.4 |
| debit echilibrat | Media dintre totalul intrărilor și totalul ieșirilor numărate de cameră, pe oră, fără factorii de corecție. După el se aleg ferestrele zilei și cazurile de trafic. Diferă de volumul calibrat al scenariului: la vârful din 26.10, 4 653 față de 5 009 veh/h. | § 5.4, § 9.9 |
| cerere | Traficul care vrea să treacă prin piață într-un interval: câte vehicule și câți pietoni, pe unde intră și pe unde ies. În simulare, cererea se construiește din numărătorile camerei, nu din trafic aleatoriu. | § 5 |
| coadă | Vehiculele oprite unul în spatele altuia înaintea unui semafor; în model, numărul de vehicule oprite pe o bandă de intrare. | § 7.1, § 9.6 |
| pierderea de timp | Cât durează în plus o deplasare față de una făcută tot timpul cu viteza dorită, fără opriri și fără încetiniri. Pierderea totală de timp, indicatorul principal, adună pierderile tuturor participanților dintr-o simulare: vehicule, bicicliști și pietoni. La vehicule intră și întârzierea la intrare, adică timpul cât așteaptă la marginea rețelei simulate până au loc; cele care nu reușesc să intre până la final se numesc neintroduse. | § 7.5, § 9.1 |
| saturație | O intersecție e saturată când primește cam atâtea vehicule câte poate trece; peste acest punct e suprasaturată, iar cozile cresc continuu. Debitul de saturație al unei benzi este cel mai mare debit care poate trece pe ea la verde; în calculul Webster se ia 1800 veh/h. | § 5.3, § 6.4, § 7.4 |
| plan fix | Program care repetă aceleași faze, cu aceleași durate, oricât trafic ar fi. Se notează prin secundele de verde ale fazelor, de exemplu 12/14/12; planurile scurte, 12/14/12 și 16/10/12, au ciclul de ≈53 s. | § 7.4 |
| planul de referință | Planul fix 36/28/12, cu ciclul de ≈91 s: ipoteza proiectului pentru programul actual al semaforului, care nu este public. Camera a arătat pe 2.11 că ipoteza e greșită: ciclul real are ≈125–155 s (§ 6.5). Măsurat din nou pe 2–7.11, după criterii publicate înaintea rulărilor, ciclul a avut mediana zilei de ≈133–137 s, iar un ciclu de ≈91 s nu apare. În § 6.5 și § 9.11, comparațiile se fac cu planul observat sau cu semaforul rejucat; în rest, procentele se dau față de planul de referință, dacă nu se spune altfel. Apare și ca „planul fix”, „planul fix actual” sau `FIX`. | § 6.3, § 7.4, § 10 |
| actuated | Semaforul acționat de trafic, în varianta din SUMO: pe aceleași 3 faze, verdele se prelungește cât timp detectoarele văd vehicule venind la mai puțin de 3 s unul după altul, între 10 și 60 s. Intersecțiile vecine din simulare au programe de acest fel. În geamănul corectat, folosit din 2.11, actuated are etapele planului observat, N–S, E–V și golirea centrului de 3 s, și lungește verdele doar în fereastra pietonilor: verdele N–S ține între 39 și 93 s, iar cel E–V, între 16 și 60 s (`sumo/net/tls_actuated_v2.add.xml`). | § 6.3, § 7.4 |
| Webster | Plan fix calculat cu formula lui Webster, din 1958: lungimea ciclului și împărțirea verdelui între faze rezultă din debitele intrărilor, iar faza de pietoni își păstrează durata. | § 7.4 |
| Max-Pressure | Algoritm clasic, fără învățare. La fiecare decizie dă verde fazei cu „presiunea” cea mai mare, adică suma, pe legăturile ei verzi, a diferențelor dintre coada din amonte și cea din aval. Amonte înseamnă înaintea semaforului, aval, după el; la treceri, coada din amonte e numărul pietonilor care așteaptă. | § 7.4 |
| programul pe cazuri de trafic | Program care folosește, pentru fiecare caz de trafic, strategia cea mai bună pe validare, iar la rezultate practic egale, pe cea mai simplă. În geamănul în timp real comută singur, după debitul echilibrat măsurat de cameră; varianta se alege din `VARIANTA_PROGRAM`. În § 9.2–9.8 se numește „program pe tipuri de trafic”; acolo apar programul marginii de jos, cel al marginii de sus și programul realist. Varianta implicită, din 2.11, este planul observat, un plan fix, deci nu comută. | § 5.5, § 9.2, § 9.9 |
| cazurile de trafic: lejer, mediu, intens | Din 28.10, cazurile se stabilesc după debitul echilibrat: lejer sub 2 400 veh/h, intens peste 4 100 veh/h, mediu între ele. Înainte, cazurile se numeau lejer, moderat și greu și se stabileau, în comparații, după numele scenariilor: lejer pentru scenariile liniștite, moderat pentru prânz, greu pentru celelalte; pragurile geamănului în timp real erau 1 300 și 2 000 veh/h. În comenzi și în fișierele de rezultate, inclusiv în cele din § 9.11, cazurile își păstrează numele vechi: `lejer`, `moderat` și `greu`. | § 9.2, § 9.8, § 9.9 |
| traficul de fond | Traficul de pe străzile vecine care nu trece prin piață și nu e văzut de cameră. În simulare se adaugă ca o fracțiune declarată, 15% din volumul observat, pe trasee care ocolesc piața. | § 5.2 |
| trecere | Trecere de pietoni semaforizată. Semaforul pieței comandă 7 treceri, de 6,4–12,8 m: în planul de referință, patru au verde doar în faza de pietoni, trei și într-o fază de vehicule; în geamănul corectat, toate au verde și într-o etapă de vehicule. Pe imaginea camerei sunt 10 zone de trecere, dar pietonii se văd doar pe trecerile din prim-plan, iar acolo detectorul pierde mulțimile. | § 4.4, § 6.3, § 9.10 |
| degajarea pietonilor | Timpul de care are nevoie un pieton care pornește la sfârșitul verdelui ca să termine traversarea. Ghidurile europene îl calculează la 1,2 m/s: pe cea mai lungă trecere a pieței, de 12,8 m, rezultă ≈10,7 s. Geamănul vechi nu îl impunea separat, iar verificarea fazei de pietoni de 12 s după normele de proiectare privea planurile lui, ale căror rezultate s-au retras pe 2.11 (§ 9.10). În geamănul corectat, pietonii primesc roșu cu 6 s înaintea vehiculelor din aceeași etapă, ca, împreună cu cele 5 s de tranziție, să aibă cele ≈10,7 s; și acolo, verdele lor rămâne de verificat după normele de proiectare (§ 6.5, § 10). | § 6.5, § 9.10, § 10 |

**Simularea și statistica**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| SUMO | Simulatorul de trafic cu sursă deschisă folosit în proiect, Eclipse SUMO 1.28; numele vine de la *Simulation of Urban MObility*. Simulează fiecare vehicul, biciclist și pieton în parte, pe o rețea construită din OpenStreetMap cu unealta `netconvert`. Programele proiectului îl comandă prin interfața TraCI sau prin biblioteca `libsumo`, mai rapidă. | § 6, § 7.3 |
| geamăn digital | Replica Pieței Romane în SUMO: străzile, benzile, trecerile și semafoarele reale, după OpenStreetMap, cu traficul reconstituit din datele camerei. Geamănul în timp real, numit „live” în titlul § 5.5, rulează continuu și primește debitele măsurate de cameră. | § 5.5, § 6 |
| dispecerat | Consola web a operatorului: arată imaginea camerei sau, în locul ei, starea senzorului, precum și starea simulării și faza curentă. Permite, după o confirmare, schimbarea modului de control, inclusiv trecerea la comanda manuală, iar banda de sus a paginii, care rămâne pe ecran la derulare, spune pas cu pas cum ajunge semaforul la faza cerută. | § 8 |
| pașii schimbării de fază | Drumul semaforului spre faza cerută, arătat de dispecerat în banda de sus a paginii: întâi verdele de acum, cât îl mai cere verdele minim, apoi, pe geamănul corectat, cele 6 s în care pietonii își termină traversarea, dacă li se închide trecerea, galbenul de 3 s și roșul de 2 s. Îi calculează `src/romana/control/pasi.py`. Nu se confundă cu pasul unei traiectorii, din tabelul camerei. | § 7.2, § 8 |
| scenariu | O oră de trafic reconstituită din numărătorile unei zile reale, urmată de 15 minute de golire, în care participanții rămași își termină drumul. Numele arată ziua și fereastra, adică ora aleasă: liniștit, ora cu cel mai puțin trafic; dimineața, 07:30–08:30; prânz, 12:00–13:00; vârf, ora cu cel mai mult trafic; seara, 17:30–18:30. Ferestrele cu oră fixă intră doar dacă datele le acoperă complet și nu se suprapun cu vârful. Prefixul `indisciplinat_` marchează varianta cu participanți indisciplinați, iar `referinta_*` sunt scenariile ipotetice de dinaintea datelor reale. | § 5.3, § 5.4 |
| cererea calibrată, marginea de jos, marginea de sus | Cererea calibrată, folosită din 26.10, pornește de la intrările numărate pe fiecare braț, înmulțite cu factorii de corecție; ieșirile dau doar proporțiile de viraj. Înainte au existat două calibrări: marginea de jos, cu volumele doar din intrări, și marginea de sus, cu media dintre intrări și ieșiri. Se credea că cererea reală e între ele; s-a dovedit că e de circa două ori marginea de sus. | § 5.1, § 9.1 |
| metoda Furness, `routeSampler` | Metoda Furness, numită și IPF, potrivește matricea O–D cu totalurile numărate pe brațe; în varianta implicită, doar cu intrările. Unealta SUMO `routeSampler.py` alege apoi traseele vehiculelor simulate astfel încât să reproducă virajele numărate. Indicatorul GEH arată cât de aproape e un debit simulat de cel numărat: cu cât e mai mic, cu atât potrivirea e mai bună. | § 5.1, § 5.2, § 5.4 |
| lanțul de prelucrare | Șirul de pași executați automat, unul după altul. În timp real, lanțul duce de la imaginea camerei la detecție, urmărire și numărători. La testul final și la confirmare, lanțul a rulat noaptea, fără intervenție: verificarea înregistrării, renumărarea, publicarea jurnalului, scenariile, simulările, analizele și regula de decizie. Pe zilele noi, prelucrarea pornește singură în fiecare noapte, în două lanțuri: `romana.lant_zilnic`, la 00:15, pentru măsura veche, și `romana.lant_cor`, la 03:30, pentru măsura nouă; după o repornire a laptopului, lanțurile se pornesc de mână. | § 4.3, § 9.10, § 9.11 |
| seed | Valoarea care pornește generatorul de numere aleatoare al simulării: de ea depind variațiile din felul în care conduc șoferii. Momentele în care pleacă participanții sunt fixate în scenariu, deci nu se schimbă de la un seed la altul. Aceeași strategie, pe același scenariu și cu același seed, dă exact același rezultat. Alegerile se fac pe seed-urile de validare 11–15, la primele alegeri 11–13, iar rezultatele se raportează pe seed-urile de test 1–10, unele doar pe 1–5. Lista candidaților din 3.11 s-a alcătuit pe zilele de antrenare, cu seed-urile 1–3, iar comparația geamănului cu camera folosește câte 5 seed-uri (§ 6.5, § 9.11). | § 9.1, § 11.8 |
| pereche | Două simulări cu același scenariu și același seed, una cu o strategie, cealaltă cu alta; strategiile sunt judecate astfel în exact aceleași condiții. „Perechile reunite” sunt cele ale ambelor comportamente, luate împreună. | § 9.1, § 9.9 |
| testul Wilcoxon, testul t | Teste statistice pe perechi. Testul Wilcoxon, al rangurilor cu semn, ține seama de semnul diferențelor și de ordinea lor după mărime, așa că o valoare extremă îl influențează puțin; regula de decizie îl folosește bilateral, adică verifică diferențele în ambele sensuri. Testul t pe perechi se uită la media diferențelor și la cât variază ele, deci e mai sensibil la valorile extreme. | § 9.1, § 9.9 |
| semnificativ | Statistic semnificativ: testul dă p sub 0,05, deci diferența e greu de pus pe seama întâmplării, adică a variației de la un seed la altul. „Nesemnificativ”, „la egalitate” sau „echivalent statistic” înseamnă că diferența nu se poate deosebi de întâmplare. | § 9.1 |
| validare, test, confirmare | Validarea înseamnă datele pe care se fac alegerile, iar testul, date nefolosite la alegere, pe care se raportează rezultatele. Ziua de validare, luni 26.10, a servit la alegerea candidaților și a pragurilor. Pe ziua de test, miercuri 28.10, nefolosită la alegere, s-a decis câștigătorul, după o regulă fixată dinainte. Pe ziua de confirmare, joi 29.10, s-a verificat doar că acesta nu e semnificativ mai slab decât strategia în vigoare. Rezultatul acestor zile, obținut pe geamănul cu coliziuni, s-a retras pe 2.11 (§ 6.5). Pentru runda din § 9.11, rolurile s-au scris dinainte, pe 1.11: antrenarea pe 25 și 26.10 și 1–3.11, validarea pe 4.11, testul pe 5 și 6.11 și generalizarea pe 7.11. Validarea a ieșit doar descriptivă, fiindcă geamănul nu s-a potrivit cu camera pe nicio oră: niciun candidat nu a trecut, deci testul nu s-a mai deschis. | § 9.9, § 9.10, § 9.11 |
| participanți disciplinați, indisciplinați | Disciplinații respectă regulile, după modelele obișnuite din SUMO. Indisciplinații reprezintă ipoteza proiectului despre traficul din București, cu parametri aleși, nu măsurați: autoturismele și camioanele trec pe roșu în primele 2 s, intră pe galben târziu, blochează intersecția după 1 s de așteptare și schimbă banda agresiv, iar celelalte vehicule au valori proprii; pietonii traversează pe roșu în primele 5 s și uneori ignoră vehiculele. Cele două variante se numesc în text „comportamente”. | § 9.4, § 10 |
| geamănul corectat | Varianta geamănului din 2.11, fără teleportări în masă. Are fișiere proprii, cu sufixul `_v2`, și e folosită de măsura nouă, `cor_`. Nu e validat: pe unele măsuri se apropie de cameră, pe altele nu. Măsurile lui s-au înghețat pe 3.11, la commitul `cffd50e`. Poarta, adică verificarea lui oră cu oră față de cameră, trecea atunci pe 8 din cele 12 ore comparate la îngheț, din 25 și 26.10 și din 1 și 2.11; pe 3 și 4.11, primele zile prelucrate după îngheț, n-a mai trecut pe nicio oră, mai ales fiindcă, la orele încărcate, geamănul duce pe Dacia vest cam jumătate din traficul măsurat de cameră. Pe 5 și 6.11 a trecut pe câte o oră, iar pe 7.11, sâmbăta, pe toate cele 5 ore, dar pe Dacia vest, care nu e un rând al porții, geamănul rămâne sub cameră în orele încărcate. | § 6.5, § 9.11 |
| planul observat | Planul fix dedus din cameră pentru vârful din luni, 26.10: 72/48/3, cu ciclul de 138 s. Semaforul real își schimbă ciclul în cursul zilei, deci planul doar îl aproximează: pe 2–7.11, medianele ciclului pe ore au mers de la ≈122 la ≈154 s. Din 2.11, planul observat este strategia implicită a geamănului în timp real și una dintre cele două referințe ale regulii din § 9.11. | § 6.5, § 9.11, § 11.5 |
| semaforul rejucat | Programul semaforului, cu etapa N–S refăcută din valurile de vehicule din jurnalul camerei, acolo unde există; restul e presupus. Sub 80% acoperire nu i se spune semaforul real. | § 6.5 |
| cerere efectivă de pietoni | Numărul de pietoni din geamăn, ales ca vehiculele să treacă printre ei ca în cameră. Nu e numărul real de oameni: un pieton simulat oprește mașinile cam cât un grup întreg. | § 6.5 |
| teleportare | Mutarea instantanee a unui vehicul mai departe pe drum. SUMO o folosește după o coliziune sau după o așteptare foarte lungă. Numărul lor arată cât de valabilă e o simulare. | § 6.5 |
| felie timp-spațiu | O singură imagine făcută din aceeași linie de pixeli, luată din fiecare cadru. Un vehicul care trece prin dreptul liniei apare ca o pată, deci se numără ușor și noaptea. | § 4.3 |
| capacitatea calibrată | Capacitatea este numărul de vehicule pe oră pe care le poate trece geamănul. Cu parametrii impliciți ai SUMO, el se bloca la debitul real din 26.10; cu intervalul de timp pe care șoferii simulați îl păstrează față de vehiculul din față, `tau`, redus de la 1,0 s la 0,8 s, trecea practic tot vârful, dar prin coliziuni și teleportări (§ 6.5), deci calibrarea a fost greșită. Între 28.10 și 2.11, capacitatea calibrată a fost varianta folosită implicit, iar rezultatele obținute cu ea s-au retras pe 2.11. Cele mai multe rezultate din § 9.1–9.8 sunt obținute cu parametrii impliciți ai SUMO, deci cu o capacitate mult mai mică decât cea reală. | § 6.4 |
| măsura pe persoană | Variantă a indicatorului principal în care orele pierdute de fiecare vehicul se înmulțesc cu numărul declarat de persoane din el: 1,2 pe autoturism, 20, 40 sau 70 pe autobuz sau troleibuz și câte 1 pentru ceilalți participanți; rezultatul se dă în ore-persoană. E raportată alături de rezultate, dar nu schimbă decizia. | § 9.9, § 9.10 |

**Camera și prelucrarea imaginii**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| HLS | *HTTP Live Streaming*, formatul în care camera își trimite imaginea pe internet: segmente video de câte 6 s, anunțate într-o listă de redare care se actualizează continuu. | § 4.1 |
| cadru | O imagine din fluxul video. Camera transmite 18 cadre pe secundă, la rezoluția de 3288 × 1850 px; programul ia 6 pe secundă și le analizează. | § 4.1 |
| cadre/s, fps | Câte cadre analizează programul într-o secundă, în mod normal ≈5–6. Când rata scade mult, urmărirea pierde vehiculele în mișcare. Prescurtarea fps, din engleză *frames per second*, înseamnă tot cadre pe secundă. | § 4.1, § 4.6 |
| tamponul de redare | Rezerva de 8 s de cadre, introdusă pe 22.10 seara: imaginea se redă uniform, cu o întârziere fixă de 8 s, deși camera trimite segmente de câte 6 s. Înainte, analiza primea cadrele în rafale, cu opriri. | § 4.1, § 4.6 |
| YOLO11 | Detectorul de obiecte Ultralytics YOLO11, antrenat dinainte pe setul de imagini COCO. Găsește în fiecare cadru autoturisme, autobuze și troleibuze, camioane, motociclete, biciclete și persoane. Proiectul folosește varianta `yolo11s`, pe imagini de 1600 px. | § 4.2 |
| ByteTrack | Algoritmul de urmărire: leagă detecțiile din cadre succesive, astfel încât fiecare vehicul sau pieton să aibă o traiectorie. Păstrează și detecțiile mai nesigure, ceea ce ajută când vehiculele se acoperă unele pe altele. | § 4.2 |
| OpenVINO | Setul de unelte Intel cu care detectorul rulează pe placa grafică integrată a laptopului: ≈6 cadre/s, față de ≈0,9 pe procesor; pe 1–5.11, mediana a fost de 5,98 (§ 4.6). | § 4.1 |
| zonă | Poligon desenat pe imaginea camerei. Dintre cele 10 zone de vehicule, cele de intrare dau volumele, iar cele de ieșire doar direcțiile; alte 10 zone acoperă trecerile, cu câte o zonă de așteptare la fiecare bordură, unde sunt numărați și pietonii care așteaptă. Zonele stau în `config/camera.json`; cele ale măsurii noi, cu două zone de intrare pe Lascăr Catargiu, deci cu 11 zone de vehicule, stau în `config/camera_v2.json`. | § 4.3, § 4.4 |
| traiectorie | Drumul unui obiect urmărit pe imagine: pozițiile succesive ale punctului în care atinge solul, cu momentul fiecăreia. La încheierea ei, regula de numărare stabilește originea și destinația; o traiectorie completă dă un viraj, de la brațul de intrare la cel de ieșire. | § 4.3 |
| fragment | Bucată de traiectorie: urmărirea se întrerupe când un stâlp, un autobuz sau un copac acoperă vehiculul. `recount` leagă fragmentele aceluiași vehicul, dar doar ≈25–45% dintre vehicule sunt urmărite de la intrare până la ieșire. | § 4.3 |
| jurnalul de traiectorii | Fișierul zilnic cu toate traiectoriile încheiate: clasa obiectului, momentul de început și pozițiile, fără imagini și fără identificatori. Jurnalul complet, cu pietoni, rămâne pe laptop, în `data/trajectories_brute/`; în depozit se publică, în `data/trajectories/`, doar vehiculele, pentru zilele de până la 7.11; de la 8.11, jurnalul rămâne doar pe laptop. Datele sunt pseudonimizate, nu anonime. | § 4.3, § 4.5 |
| `recount` | Modulul `romana.vision.recount`: reface numărătorile din jurnalul de traiectorii, de exemplu după corectarea zonelor, fără o colectare nouă. Cu `--publica` scrie versiunea publicabilă a jurnalului. | § 4.3, § 11.4 |
| `calitate` | Modulul `romana.vision.calitate`: verifică, după colectare, cât de continuă a fost urmărirea. Măsoară golurile dintre punctele traiectoriilor, densitatea punctelor și pașii lungi, apoi marchează intervalele încetinite. | § 4.6 |
| `veghe` | Modulul `romana.vision.veghe`: rulează alături de analiza camerei și urmărește în fiecare secundă starea prelucrării. La primul semn de problemă se oprește cu o alertă și un diagnostic, ca problema să fie analizată pe loc, nu a doua zi. | § 4.6 |
| `paznic` | Modulul `romana.vision.paznic`, paznicul colectării: o dată pe minut verifică dacă analiza camerei rulează și dă semne de viață. Dacă procesul lipsește la două verificări la rând sau tace de 5 minute, deși camera răspunde, îl repornește singur; dacă problema e la cameră sau la rețea, doar așteaptă. Înaintea unei opriri voite se pune fișierul `outputs/live/fara_repornire`, iar fiecare gol se trece în `outputs/logs/reporniri_<zi>.csv`. | § 4.6 |
| fișa senzorului, `fisa_senzor` | Modulul `romana.vision.fisa_senzor`: reface din jurnalele laptopului, până la o oră aleasă și cu aceleași definiții de fiecare dată, cifrele colectării: de când merge, câte opriri anunțate și câte căderi neprevăzute au fost, câte căderi ale sursei camerei, ce parte din minute au cadre, câte cadre se analizează pe secundă, câte pauze și reconectări au fost, câte prelucrări de noapte s-au încheiat și câte vehicule s-au numărat; pietonii, doar ca total pe zi. | § 4.6 |
| starea senzorului, `?imagine=0` | Panoul din dispecerat, din 9.11, care spune în cuvinte cum merg cele cinci verigi ale colectării: camera, numărătorile, veghea, paznicul și prelucrarea de noapte. Fiecare are una dintre stările „în regulă”, „de urmărit”, „problemă” sau „nu se știe”, cu regula scrisă sub ea. Panoul stă în locul imaginii camerei, când aceasta e ascunsă; adresa paginii terminată în `?imagine=0` o deschide direct așa, de exemplu la o prezentare online. | § 4.6, § 8 |
| microînghețare | Oprire a imaginii de 10–30 s, de câteva ori pe zi, cam 0,1–0,2% din timpul înregistrat, când un segment al fluxului întârzie. Trece singură; efectul asupra numărătorilor e neglijabil, dar nu nul. | § 4.6 |
| pas, pași lungi | Pasul este timpul dintre două puncte consecutive ale unei traiectorii, în mod normal ≈0,17–0,2 s. Un pas lung, de peste 0,5 s, înseamnă cadre pierdute. | § 4.6 |
| încetinire | Prelucrare încetinită: un interval de 15 minute în care cel puțin 40% dintre pașii traiectoriilor de vehicule sunt lungi. În măsura nouă (§ 9.11), un interval e încetinit și când pasul median trece de 0,22 s. Calculatorul analizează atunci prea puține cadre, iar urmărirea pierde vehiculele în mișcare, deși imaginea nu e înghețată. Exemplu: 28.10, 03:46–04:28, ≈1,4 cadre/s, cel mai probabil din cauza calculelor grele rulate în paralel. | § 4.6 |
| urmărirea sacadată | Defectul din 21–22.10: înainte de tamponul de redare, analiza primea cadrele în rafale, cu opriri, iar vehiculele „săreau” peste zonele mici de numărare. De aceea, acele zile sunt subnumărate, cu un factor necunoscut. | § 4.6 |
| numărătoarea de referință | Numărarea de control din 26.10: două clipuri de câte 3 minute, numărate cadru cu cadru de câte doi adnotatori AI independenți, instanțe separate ale asistentului Claude. Din ea au rezultat zonele finale și factorii de corecție. | § 4.3 |
| factorii de corecție | Numerele cu care se înmulțesc intrările numărate de cameră pe fiecare braț ca să ajungă la numărătoarea de referință: Magheru 1,09, Dacia est 0,88, Dacia vest 1,12, Lascăr Catargiu 2,52. Aceștia sunt factorii măsurii vechi. Măsura nouă, `cor_`, după care se decide din 2.11, are factori proprii, calculați din numărătorile ei de referință, pe clipurile din 1 și 2.11, și înghețați pe 3.11 în `config/factori_v2.json`; pe Magheru și pe Lascăr Catargiu, ei diferă ziua și pe întuneric (§ 4.3). | § 4.3, § 5.1, § 9.11 |

**Agenții și strategiile din rezultate**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| strategie | Orice fel de a comanda semaforul: un plan fix, actuated, Webster, Max-Pressure, un agent sau un program care le combină pe cazuri de trafic. | § 7.4, § 9.1 |
| învățare prin întărire | Metodă de inteligență artificială în care un program învață din încercări repetate: alege o acțiune, primește o notă, numită recompensă, și ajunge treptat să prefere acțiunile cu note mai bune. Această învățare se numește antrenare și se face doar în simulare. | § 7 |
| PPO | *Proximal Policy Optimization*, algoritmul de învățare prin întărire folosit, din biblioteca Stable-Baselines3. Își corectează politica, adică regula după care agentul alege fazele, în pași mici, fără salturi bruște de comportament. Un pas de antrenare este o decizie a agentului, adică 5 s de trafic simulat; rata de învățare, notată lr, dă mărimea fiecărei corecții, iar punctele intermediare sunt copii ale agentului salvate în timpul antrenării. | § 7.3, § 9.5 |
| agent | Program antrenat cu PPO care decide, la fiecare 5 s, ce fază primește verde; astfel stabilește ordinea și durata fazelor. Agenții de până acum aleg doar dintre cele 3 faze ale planului de referință, iar E15 doar între N–S și E–V. Galbenul, roșul de degajare și verdele minim și maxim îi sunt impuse, ca să nu poată crea o situație periculoasă. Un specialist este un agent antrenat pentru un singur tip de trafic. | § 7.1, § 7.2 |
| recompensă | Nota primită de agent după fiecare decizie: suma vehiculelor oprite pe benzile de intrare, a pietonilor care așteaptă la treceri și a vehiculelor care nu pot intra în rețea, împărțită la 100 și luată cu semnul minus. Cu cât așteaptă mai puțini, cu atât nota e mai mare. | § 7.1 |
| agentul oficial | `ppo_romana`, agentul antrenat pe scenariile reale din 21.10 și ales pe seed-urile de validare 11–13; în § 9.5 apare și ca v1. În programul realist conduce traficul lejer. | § 9.1, § 9.5 |
| E1–E15 | Experimentele de antrenare a agenților, numerotate în ordinea în care s-au făcut; fiecare agent poartă numele experimentului din care provine. Cele mai multe au dat rezultate negative și rămân documentate ca încercări. E5–E7 sunt specialiști pentru traficul greu, E8 pentru cel moderat și E9 pentru cel lejer; E7 a ieșit echivalent cu planul 46/48/12, păstrat pentru că e mai simplu, iar E12 este E3 antrenat în continuare pe aceleași scenarii ca E13. | § 9.5 |
| E3 | `ppo_romana_zn3`: agentul oficial antrenat în continuare pe datele renumărate din 21–22.10, cu o rată de învățare de 10 ori mai mică. A ieșit cel mai bun la prânz, așa că a condus traficul moderat în programele din § 9.2 și, în programul realist, și traficul greu. Pe 28 și 29.10 a ieșit practic egal cu planul de referință, rezultat retras pe 2.11, odată cu tot testul final (§ 6.5). | § 9.4, § 9.5, § 9.10 |
| E9 | `ppo_romana_lejer`: specialistul pentru trafic lejer, antrenat doar pe scenariile liniștite din 21–22.10. Conduce traficul lejer în programul marginii de sus. | § 9.2, § 9.5 |
| E13 | `ppo_romana_cal`: agentul oficial antrenat încă 300 000 de pași pe scenariile calibrate din 21–22.10, cu participanți disciplinați și indisciplinați. Pe 26.10 a fost cel mai constant agent, așa că a intrat în testul final ca singurul agent candidat. Acolo a fost eligibil, dar al treilea după pierderea totală, și nu s-a deosebit semnificativ de planul 12/14/12 (p = 0,82); pe 29.10 a pierdut cu 3,4% mai mult decât planul. Toate aceste rezultate, din 26, 28 și 29.10, stau pe geamănul cu coliziuni, deci s-au retras pe 2.11 (§ 6.5). | § 9.5, § 9.9, § 9.10 |
| E14 | E13 antrenat încă 300 000 de pași pe scenariile zilei de validare, luni 26.10, cu capacitatea calibrată. Pe validare a ieșit mai slab decât E13, deci nu a devenit candidat; și această comparație stă pe geamănul cu coliziuni, deci s-a retras pe 2.11 (§ 6.5). | § 9.5, § 9.9 |
| E15 | `ppo_e15`: agentul antrenat în ziua de 3.11, pe geamănul înghețat, doar pe orele din 25 și 26.10 și 1.11 care trec poarta, fără date din 3.11. Imită întâi planul observat, apoi învață cu PPO, și alege doar între N–S și E–V. Pe zilele de antrenare pierde cu 1,7% mai mult decât planul observat, dar e pe lista candidaților din 3.11, cum s-a scris pe 1.11. La validarea din 4.11 nu a trecut, la fel ca ceilalți doi candidați: geamănul nu s-a potrivit cu camera pe nicio oră, deci validarea a fost doar descriptivă. | § 9.5, § 9.11 |
| programul realist, `REALIST` | Programul ales pe validarea cu participanți indisciplinați: agentul oficial la trafic lejer și E3 la trafic moderat și greu. A fost varianta implicită a geamănului în timp real până pe 29.10 și strategia în vigoare față de care s-a judecat testul final; `REALIST` e numele lui în comenzi. | § 9.4, § 9.10 |
| `TOD_DEBIT` | Program din planuri fixe, cu cazurile stabilite după debit: 16/10/12 la trafic lejer și mediu, 12/14/12 la trafic intens. Candidat în testul final: pe 28.10 a avut cea mai mică pierdere totală dintre candidați, dar diferența față de 12/14/12, de 0,3%, nu a fost semnificativă, așa că a câștigat planul mai simplu. Rezultatul s-a retras pe 2.11, odată cu tot testul final (§ 6.5). | § 9.9, § 9.10 |
| `TOD_FIX` | Aceleași planuri, cu cazurile stabilite după numele scenariilor: 16/10/12 în scenariile liniștite și la prânz, 12/14/12 în rest. A fost ales chiar pe datele de validare, deci estimarea de acolo e optimistă; în teste a fost doar raportat, nu candidat. | § 9.9, § 9.10 |
| `PLAN_12_14_12`, `PLAN_a_b_c` | Numele de cod ale planurilor fixe: `PLAN_a_b_c` are a, b și c secunde de verde pentru N–S, E–V și pietoni. La planul observat, 72/48/3, c e golirea centrului, fără pietoni. `PLAN_12_14_12` a câștigat testul din 28.10, rezultat retras pe 2.11 (§ 6.5); între 29.10 și 2.11 a fost varianta implicită a geamănului în timp real, `plan_scurt`. | § 9.10, § 11.8 |
| `FIX`, `ACTUATED`, `REAL` | Numele de cod ale planului de referință 36/28/12, ale semaforizării actuated și ale semaforului rejucat, în comenzi și în fișierele de rezultate, de exemplu în `docs/rezultate/cor_decizie_2026-11-04.json`. `REAL` e o reconstrucție în simulare, nu semaforul de pe stradă, și nu se confundă cu programul realist, `REALIST`. | § 6.5, § 11.8 |
| grila de planuri fixe | Încercarea sistematică a mai multor planuri fixe, cu alte durate de verde, ca să se găsească cel mai bun: 10 planuri pe calibrările anterioare, 23 pe geamănul calibrat, pe validarea din 26.10, și 8 pe geamănul înghețat, pe 3.11, pe zilele de antrenare 25 și 26.10 și 1.11, înainte de a privi datele din 3.11. A doua grilă arăta că ciclurile scurte câștigă, dar geamănul ei avea coliziuni și teleportări în masă (§ 6.5). Pe geamănul înghețat, planurile foarte scurte nu duc traficul, iar pierderea cea mai mică iese la un ciclu de ≈93 s. | § 6.5, § 9.5, § 9.9, § 9.11 |
| candidat, strategia în vigoare, strategie raportată | Candidații testului final, fixați dinainte, au fost planul 12/14/12, `TOD_DEBIT` și E13. Strategia în vigoare, cu care au fost comparați, era programul realist. Strategiile raportate, de exemplu planul 16/10/12 singur, agentul oficial sau `TOD_FIX`, au fost rulate și prezentate, dar nu puteau câștiga. Pe zilele noi din § 9.11, candidații au fost planurile 60/40/3 și 45/30/3 și E15, comparați cu planul observat și cu semaforul rejucat; actuated a fost doar raportat. Niciunul nu a trecut de validarea din 4.11, care a ieșit doar descriptivă, deci rămâne planul observat, 72/48/3. | § 9.9, § 9.10, § 9.11 |
| regula „cel mai bun câștigă” | Regula de decizie fixată de autor pe 28.10, înaintea testului final: câștigă candidatul cu cea mai mică pierdere totală, dacă e semnificativ mai bun decât strategia în vigoare și nu e semnificativ mai slab în niciunul dintre cele două comportamente. Dacă primii doi candidați nu se deosebesc semnificativ, câștigă cel mai simplu. | § 9.9 |
| coridorul | Varianta în care un singur agent conduce deodată Piața Romană și cele 4 intersecții vecine care o alimentează. Rezultatul a fost negativ: +35,4% față de planul fix. | § 6.1, § 9.5 |

**Abrevierile și organizațiile**

| Termen sau notație | Ce înseamnă, pe scurt | Unde |
|---|---|---|
| AI, IA | Inteligență artificială: AI vine din engleză, de la *artificial intelligence*, iar IA e prescurtarea românească. Pe butonul dispeceratului, „Agent IA”, numit la M1 „Agent AI”, înseamnă un agent de învățare prin întărire, iar „adnotatorii AI” sunt instanțe ale asistentului Claude. | § 4.3, § 7, § 8 |
| RL | Învățare prin întărire, din engleză *reinforcement learning*. | § 7 |
| IoT | Internetul lucrurilor, din engleză *Internet of Things*: dispozitive conectate la internet, de exemplu senzori, ale căror date sunt folosite de alte programe. Aici, camera publică joacă rolul senzorului: al traficului și, prin valurile de vehicule care pornesc la verde, al semaforului. Colectarea merge pe laptop din 1.11, 09:04, zi și noapte, iar procesul ei n-a căzut niciodată neprevăzut; s-a oprit doar de trei ori, anunțat. Pe 9 și pe 10.11 a lipsit o vreme doar fluxul camerei, iar colectarea s-a reconectat singură. | § 3, § 4.6, § 6.5 |
| MQTT | Protocol de mesaje pentru Internetul lucrurilor. Modulul de viziune îl poate folosi, opțional, ca să publice starea camerei și numărătorile. | § 3 |
| OSM | OpenStreetMap, harta deschisă din care s-a construit replica rețelei de străzi; datele ei se folosesc sub licența ODbL. | § 6.1, § 14.1 |
| CPU, GPU | Procesorul și placa grafică ale calculatorului. Laptopul proiectului nu are placă grafică NVIDIA, așa că detectorul rulează pe placa grafică Intel integrată. | § 4.1 |
| GDPR | Regulamentul general privind protecția datelor, Regulamentul (UE) 2016/679. Se aplică pentru că imaginile camerei pot conține persoane și numere de înmatriculare. | § 4.5 |
| EDPB | Comitetul european pentru protecția datelor, din engleză *European Data Protection Board*; ghidul lui 3/2019 privește prelucrarea datelor personale prin dispozitive video. | § 4.5 |
| ANSPDCP | Autoritatea Națională de Supraveghere a Prelucrării Datelor cu Caracter Personal, la care persoanele vizate pot depune plângere. | § 4.5 |
| art., alin., lit. | Articol, alineat și literă, în trimiterile la legi, de exemplu art. 14 GDPR. | § 4.5, § 14.1 |
| BTMS | Sistemul de management al traficului din București, care coordonează dintr-un singur centru aproximativ 267 de intersecții, cele mai multe cu automate care își ajustează programul după trafic. | § 1, § 10 |
| PMB | Primăria Municipiului București. | § 1, § 10 |
| STB | Societatea de Transport București, operatorul transportului public din oraș. În piață circulă autobuzele și troleibuzele ei, iar rețeaua simulată are benzile lor dedicate. | § 4.2, § 6.2, § 9.9 |
| CC BY 4.0 | Licența Creative Commons Atribuire 4.0, sub care este publicată documentația: oricine o poate folosi și adapta, cu condiția să-i menționeze autorul. | § 14.1 |
| ODbL 1.0 | *Open Database License*, licența datelor OpenStreetMap: orice bază de date derivată din ele, ca rețeaua, rutele și scenariile proiectului, rămâne sub aceeași licență. Proiectul o folosește și pentru numărători și traiectorii. | § 14.1 |
| AGPL v3 | *GNU Affero General Public License*, versiunea 3 sau ulterioară, licența codului și a modelelor. E obligatorie pentru că modulul de viziune folosește YOLO11, distribuit sub AGPL; cine redistribuie codul sau oferă prin rețea o versiune modificată trebuie să pună la dispoziție și codul sursă. | § 10, § 14.1 |

---

## 1. Context și motivație

**Pe scurt.** Proiectul măsoară traficul din Piața Romană cu ajutorul unei camere publice, reproduce intersecția
într-un simulator de trafic și caută cel mai bun program pentru semafoarele ei. Se schimbă doar programul
semafoarelor; străzile și semafoarele rămân aceleași. Un test din 28–29.10 alesese planul fix 12/14/12, un program de
semaforizare care se repetă identic, indiferent de trafic, dar rezultatul s-a retras pe 2.11: simulările rulau cu coliziuni și teleportări în masă (§ 6.5). Pe geamănul corectat, planurile scurte nu duc traficul la orele încărcate. Care plan e cel mai bun nu se poate spune încă. Runda de alegere după regulile din § 9.11 s-a încheiat pe 5.11 fără un program nou: în ziua de validare, 4.11, geamănul nu s-a potrivit cu camera pe nicio oră, deci niciun candidat nu a trecut, iar în geamăn rămâne planul observat, 72/48/3, dedus din cameră. Direct din cameră se poate spune însă că, pe 2–7.11, ciclul real al semaforului a avut mediana zilei de ≈133–137 s și s-a schimbat de la o oră la alta (§ 6.5).

Piața Romană este nodul în care axa nord–sud Lascăr Catargiu – Magheru, paralelă cu magistrala de metrou M2, se
intersectează cu axa est–vest a Bulevardului Dacia[^wiki-romana]. Din piață mai pornesc două străzi cu sens unic,
folosite doar pentru ieșire: Str. D. I. Mendeleev și Str. Căderea Bastiliei. Camera Webcam România este montată pe
clădirea dintre Bd. Magheru și Bd. Dacia est. Ea filmează continuu „sensul giratoriu din mijlocul pieței, trecerile de
pietoni, traficul de pe bulevardele Magheru, Lascăr Catargiu și Dacia”[^webcam].

Bucureștiul este unul dintre cele mai congestionate orașe din lume. În ediția 2025 a clasamentului TomTom Traffic
Index, nivelul mediu de congestie a fost de 62,5%, adică o deplasare a durat în medie cu 62,5% mai mult decât ar fi
durat pe străzi libere. Orașul a ocupat locul 20 în lume și locul 5 în Europa. La orele de vârf, un șofer a pierdut
în medie 171 de ore pe an, iar viteza medie în aceste ore a fost de 14 km/h[^tomtom][^pmb-tomtom].

Primăria Capitalei operează sistemul de management al traficului BTMS, extins la aproximativ 267 de intersecții
coordonate dintr-un singur centru. Cele mai multe dintre ele au automate de semaforizare „cu funcționare în mod
adaptiv”[^btms-267][^buletin-btms], adică automate care își ajustează programul după trafic. În 2026, Primăria a
anunțat un proiect nou de semaforizare cu inteligență artificială (AI), pentru 92 de intersecții și treceri de pietoni în prima etapă:
„Vom monta 305 camere și 1.500 de senzori”. Timpii de semaforizare urmează să se ajusteze după numărul de mașini, iar
transportul public va avea prioritate[^digi24-ai]. Axa Unirii – Universitate – Piața Romană – Piața Victoriei a fost
chiar proiectul-pilot al primului sistem „undă verde”, în 2007[^economedia]. Într-o „undă verde”, semafoarele de pe
un traseu sunt coordonate astfel încât vehiculele să prindă verde la rând.

Infrastructura rămâne însă fragilă. Pe 8 mai 2026, un incendiu la cablurile electrice subterane din Piața Romană a
scos din funcțiune semafoarele pieței[^adevarul-incendiu]. De aceea, sistemul propus are întotdeauna un plan fix de
rezervă.

La scară academică, proiectul parcurge tot lanțul pe care îl presupun sistemele de semaforizare inteligentă:
**senzor video → date de trafic → model digital al intersecției → decizie automată → supraveghere umană**. Senzorul
este camera. Din imaginile ei rezultă datele de trafic: câte vehicule, bicicliști și pietoni trec și pe unde. Modelul
digital, numit geamăn digital, este o replică a pieței în simulatorul de trafic SUMO. Decizia o ia strategia care
comandă semafoarele, iar un operator o supraveghează din dispecerat, interfața web a sistemului.

**Întrebarea proiectului.** Pe măsură ce s-au strâns date reale, s-a văzut că nu există o singură strategie bună
pentru orice trafic (§ 9). De aceea, proiectul nu caută „cu orice preț” un agent de inteligență artificială, adică un
program care învață singur să comande semafoarele. Caută **cea mai bună combinație implementabilă de planuri și
agenți pentru cazurile reale de trafic ale pieței**.

Traficul pieței se împarte în trei cazuri: lejer, mediu și intens. Cazul se stabilește după debitul măsurat de
cameră, adică după numărul de vehicule care trec prin piață într-o oră. Scopul este ca fiecare caz să primească strategia care câștigă
pe datele lui, iar un selector s-o pornească automat, după traficul măsurat. Până acum n-a rezistat niciun câștigător. Rezultatul din
28–29.10 s-a retras pe 2.11 (§ 6.5), iar de atunci geamănul în timp real rulează implicit, la orice trafic, planul observat; runda nouă
s-a încheiat pe 5.11 fără un program nou, deci planul observat, 72/48/3, rămâne (§ 5.5, § 9.11). Singurul lucru care se schimbă este
programul semafoarelor: geometria străzilor și semafoarele rămân cele reale.

Concurează, pe picior de egalitate, trei feluri de candidați:

- planurile fixe clasice;
- programele alcătuite din planuri fixe, câte unul pentru fiecare caz de trafic;
- agenții de învățare prin întărire, care învață, din încercări repetate în simulare, în ce ordine și cât timp să
  dea verde.

Câștigă cel mai bun, după o verificare pe o zi nouă, nefolosită la alegere. Ceilalți rămân documentați ca încercări
(§ 9.9). Pe ziua de test, miercuri 28.10, a câștigat atunci planul fix scurt 12/14/12, cu aceleași faze, dar cu durate mai
scurte; rezultatul s-a retras între timp (§ 6.5). O fază este perioada în care au verde doar anumite direcții de mers. Cele trei numere sunt duratele de verde,
în secunde, ale celor trei faze: cea pentru axa nord–sud, cea pentru axa est–vest și cea pentru pietoni. În calcul intră toți participanții observați pe cameră:
autoturisme, autobuze și troleibuze, camioane, motociclete, bicicliști și pietoni.

## 2. Obiective și cerințe

Cerințele din tema proiectului sunt notate aici R1–R8. Tabelul de mai jos arată cum este îndeplinită fiecare și,
unde este cazul, trimite la secțiunea cu detalii.

| # | Cerința din tema proiectului | Cum este îndeplinită |
|---|---|---|
| R1 | Preluarea în timp real a datelor de pe camera publică | `vision/stream.py` citește fluxul video al camerei, transmis prin internet în format HLS, și se reconectează automat dacă legătura cade. `run_vision.py` analizează ≈5–6 cadre/s: pe 1–5.11, mediana a fost de 5,98, după fișa senzorului (§ 4.6); un cadru este o imagine din fluxul video. |
| R2 | Direcțiile **din care vin** și **spre care se îndreaptă** vehiculele, cât mai aproape de adevăr | Pe imaginea camerei sunt definite 10 zone poligonale de intrare și de ieșire pe brațele pieței, calibrate pe traiectorii reale; măsura nouă, `cor_`, are 11, cu două zone de intrare pe Lascăr Catargiu (§ 4.3). Din ele rezultă, pe intervale de 15 min, matricea origine–destinație (O–D): câte vehicule merg de la fiecare intrare la fiecare ieșire. Alte 10 zone acoperă trecerile de pietoni, în forma corectată pe 28.10 (§ 4.4). |
| R3 | Transformarea datelor în flux de trafic simulat în SUMO, nu trafic aleator | Matricea O–D se estimează cu metoda Furness, care o potrivește cu totalurile de intrare numărate. Apoi unealta SUMO `routeSampler.py` alege rutele vehiculelor simulate astfel încât să reproducă virajele numărate, pe tipuri de vehicule, inclusiv biciclete. Cererea de pietoni vine din numărătorile de pe treceri. Traficul de fond, adică traficul de pe străzile vecine care nu trece prin piață, intră doar ca o fracțiune declarată. |
| R4 | Model AI care recunoaște semafoarele intersecției și le controlează | Cele 16 semafoare fizice ale pieței sunt identificate automat după coordonate și grupate într-un singur controler, așa cum în realitate sunt conduse de un singur automat. Un agent antrenat cu PPO, un algoritm de învățare prin întărire, alege ordinea și durata fazelor reale. Agenții sunt candidați pentru programul pe cazuri de trafic, alături de planurile fixe (§ 9.9). |
| R5 | Antrenare până la fluidizarea optimă a intersecției | Agenții se antrenează pe mai multe scenarii de trafic, în procese paralele. Rezultatele se compară cu 4 strategii de referință pe seed-urile de test 1–10, iar alegerile se fac pe seed-urile de validare 11–15. Un seed este valoarea care pornește generatorul de numere aleatoare al simulării. În evaluare intră toți participanții: vehicule, bicicliști și pietoni. Fluidizarea optimă se caută pe cazuri de trafic: fiecare caz primește strategia care câștigă pe el, plan fix sau agent, aleasă pe validare și verificată pe o zi nouă, nefolosită la alegere (§ 9.9). Pe 28–29.10 a ieșit planul fix 12/14/12, rezultat retras pe 2.11, fiindcă geamănul avea coliziuni și teleportări în masă (§ 6.5). Alegerea reluată după regulile din § 9.11, cu planurile 60/40/3 și 45/30/3 și agentul E15 drept candidați, s-a încheiat pe 5.11 fără un program nou: în ziua de validare, 4.11, geamănul nu s-a potrivit cu camera pe nicio oră, deci niciun candidat nu a trecut și rămâne planul observat, 72/48/3. Fluidizarea optimă nu e, așadar, dovedită; reparațiile geamănului țin de o rundă nouă, după M3, cu zile noi și cu reguli publicate înaintea datelor ei (§ 9.11). |
| R6 | Extindere la intersecțiile principale conexe | Varianta „coridor” controlează simultan Piața Romană și cele 4 intersecții imediat vecine care o alimentează. Rezultatul a fost negativ: într-una dintre primele încercări, un singur agent pentru toate cele cinci intersecții a pierdut cu 35,4% mai mult timp decât planul fix (§ 6.1, § 9.5). |
| R7 | Documentație în limba română, cu surse și licențe | Acest document, cu sursele în note de subsol și cu bibliografia și licențele în § 14. |
| R8 | Evoluție vizibilă pe GitHub, pe borne | La fiecare bornă, adică la fiecare etapă a lucrului, se face commit + push pe GitHub: modificările sunt salvate în istoricul proiectului și publicate (§ 12). |

Pe lângă cele opt cerințe, sistemul respectă patru cerințe nefuncționale. Ele nu descriu ce face sistemul, ci cum
trebuie să funcționeze:

- **Siguranța.** Agentul nu poate aduce semaforul într-o stare periculoasă.
- **Confidențialitatea.** Nu se păstrează înregistrări video pe termen lung, iar din imaginile camerei este publicat doar un
  cadru estompat (§ 4.5). Pe laptop rămân doar previzualizarea estompată, suprascrisă continuu, și, temporar, capturi
  și clipuri scurte folosite la calibrare și la numărătoarea de referință, șterse după folosire. Imaginile citite de asistentul Claude au
  fost trimise spre analiză la Anthropic (§ 4.5).
- **Reproductibilitatea.** Rețeaua, cererea de trafic și rezultatele se pot reface din scripturi.
- **Rularea pe un laptop Windows fără placă grafică dedicată.** Detecția rulează pe placa grafică Intel integrată
  (§ 4.1).

## 3. Arhitectura sistemului (perspectiva IoT)

Sistemul este construit după principiile Internetului lucrurilor (IoT, din engleză *Internet of Things*): un
dispozitiv conectat la internet culege date, iar alte programe le prelucrează și le folosesc. Arhitectura urmează
modelul pe straturi din recomandarea ITU-T Y.2060[^itu-y2060] a Uniunii Internaționale a Telecomunicațiilor.
Diagrama de mai jos prezintă straturile și drumul datelor, de la cameră până la operator; săgețile indică sensul în
care circulă datele și comenzile.

```mermaid
flowchart LR
  subgraph Dispozitiv["Strat dispozitiv (senzor)"]
    CAM["Camera Webcam România<br/>HLS 3288×1850, 18 fps"]
  end
  subgraph Edge["Procesare la margine (edge)"]
    YOLO["YOLO11 + ByteTrack"] --> OD["Numărare O–D<br/>pe zone"]
  end
  subgraph Retea["Strat rețea"]
    MQTT[("Broker MQTT<br/>romana/…")]
    JSON[("outputs/live/*.json")]
  end
  subgraph Servicii["Strat suport servicii"]
    EST["Estimare O–D (Furness)<br/>+ routeSampler"] --> SUMO["Geamăn digital SUMO"]
  end
  subgraph Aplicatie["Strat aplicație"]
    RL["Plan fix / program pe cazuri /<br/>agent PPO / Max-Pressure / manual"]
    UI["Dispecerat (operator)"]
  end
  CAM --> YOLO
  OD --> MQTT & JSON
  JSON --> EST
  JSON --> SUMO
  JSON -->|debite, starea camerei| UI
  SUMO <-->|TraCI| RL
  SUMO --> UI
  UI -->|comenzi| RL
```

**Senzorul virtual.** Camera nu aparține proiectului. Ea este tratată ca un senzor public, care transmite pe internet
un flux video HLS, adică imaginea livrată în segmente scurte. În diagramă apar rezoluția fluxului, în pixeli, și
numărul de cadre pe secundă (fps). Partea „inteligentă” a sistemului rulează local: imaginile se analizează chiar pe
laptop, în punctul în care intră în sistem. Diagrama numește acest pas „Procesare la margine (edge)”, după termenul
din engleză *edge computing*. YOLO11 recunoaște vehiculele și persoanele din fiecare cadru, ByteTrack le urmărește de
la un cadru la altul, iar numărarea O–D pe zone stabilește de unde vine și unde merge fiecare vehicul.

Spre restul sistemului pleacă doar trei lucruri: **numărători agregate**, adică totaluri pe intervale de timp;
traiectorii pseudonimizate, adică fără imagini și fără identificatori; previzualizarea estompată, pentru dispeceratul
local (§ 4.5). Astfel se trimit mai puține date prin rețea și, mai ales, se respectă principiul „reducerii la minimum
a datelor” din Regulamentul general privind protecția datelor (GDPR)[^gdpr].

**Paza colectării.** Colectarea merge pe laptop din 1.11, 09:04, zi și noapte, iar procesul ei n-a căzut niciodată neprevăzut; s-a
oprit doar de trei ori, anunțat: pe 1.11, pe 5.11 și pe 8.11. Pe 9 și pe 10.11 a lipsit o vreme doar fluxul camerei, iar
colectarea s-a reconectat singură (§ 4.6). Două programe o urmăresc. Veghea, `romana.vision.veghe`, introdusă pe 29.10, citește în fiecare secundă
starea prelucrării și, la primul semn de problemă, se oprește cu o alertă și un diagnostic. Paznicul, `romana.vision.paznic`, nou de
la borna M1, repornește colectarea dacă procesul a dispărut sau nu mai dă semne de viață, iar camera răspunde; dacă problema e la
cameră sau la rețea, doar așteaptă. După o repornire a laptopului, paznicul, veghea și prelucrările de noapte se pornesc de mână.
Cifrele colectării, până la o oră aleasă, le reface fișa senzorului, iar starea de acum a fiecărei verigi o arată dispeceratul
(§ 4.6).

**Camera, senzor și pentru semafor.** Programul semaforului nu e public, dar vehiculele trec prin zonele de intrare în valuri, după
cum au verde, iar din aceste valuri se măsoară ciclul semaforului. Pe 2–7.11, după criterii publicate înaintea rulărilor,
mediana zilei a fost de ≈133–137 s, iar un ciclu de ≈91 s, cât presupune planul de referință, nu apare (§ 6.5).

**Rețeaua.** Opțional, modulul de viziune publică datele prin MQTT, un protocol de mesaje pentru Internetul
lucrurilor, standardizat de organizația OASIS în versiunea 5.0[^mqtt]. Mesajele trec printr-un broker, adică un server
care le primește și le transmite programelor abonate la subiectul respectiv; brokerul recomandat este Eclipse
Mosquitto[^mosquitto]. Pe laptop, aceleași date se scriu și în fișierele `outputs/live/*.json`.

**Pentru specialiști.** Subiectele MQTT sunt trei: `romana/stare/camera`, cu mesaje păstrate (*retained*) și QoS 1,
`romana/numaratori/interval`, tot cu mesaje păstrate, și `romana/evenimente/viraj`. Brokerul reține ultimul mesaj
păstrat al fiecărui subiect și îl trimite imediat oricărui abonat nou, iar nivelul de calitate a serviciului QoS 1
garantează că mesajul ajunge cel puțin o dată. Fișierele locale se scriu atomic: fișierul nou îl înlocuiește
dintr-odată pe cel vechi, astfel încât niciun program nu citește un fișier scris pe jumătate.

**Serviciile.** Din numărători se estimează matricea O–D și se generează cererea de trafic, adică vehiculele și
pietonii care intră în simulare. În diagramă apar metoda de estimare, Furness, și unealta SUMO `routeSampler.py`,
care alege rutele vehiculelor. Cererea ajunge în geamănul digital, replica pieței din simulatorul SUMO. Geamănul care
rulează în timp real citește debitele și direct din fișierele scrise de modulul de viziune.

**Aplicația.** Aici se află controlerul semaforului și dispeceratul. Controlerul aplică una dintre următoarele
strategii: un plan fix, adică planul observat, dedus din cameră și implicit din 2.11, sau planul de referință, păstrat pentru
comparație; un agent PPO; algoritmul Max-Pressure; sau comanda manuală a operatorului. Pe ecranul dispeceratului, modurile se numesc
„Planul observat”, „Agent IA”, „Plan de referință”, „Presiune maximă” și „Comandă manuală” (§ 8). Programul pe cazuri de trafic
rămâne în cod, ca variantă a primului mod (§ 5.5). PPO este algoritmul de învățare prin întărire cu care au fost antrenați
agenții. Max-Pressure este un algoritm clasic, fără învățare, care dă verde fazei la care diferența dintre cozile dinaintea
semafoarelor ei și cozile de după ele este cea mai mare. Controlerul comunică cu simularea prin TraCI, interfața prin care un
program din afară citește starea simulării SUMO și comandă semafoarele. Dispeceratul arată starea simulării și, din fișierele
locale, debitele măsurate și starea senzorului, iar operatorul îi trimite de acolo comenzi controlerului; banda de sus a paginii
urmărește fiecare comandă până se aplică, iar o fază aleasă de mână, pas cu pas, până la verdele ei (§ 8).

## 4. Modulul de viziune artificială

Modulul de viziune transformă imaginea camerei publice în date de trafic. El găsește în fiecare cadru vehiculele,
bicicliștii și pietonii, îi urmărește de la un cadru la altul, numără pietonii de pe treceri și află de unde vin și
încotro merg vehiculele. Din aceste numărători se construiește traficul din simulare (cap. 5). Din momentele în care
vehiculele trec prin zonele de intrare, modulul măsoară și programul real al semaforului, cu `romana.vision.program_real`
(§ 6.5).

### 4.1 Sursa video

Imaginea camerei ajunge pe internet prin HLS (HTTP Live Streaming), o metodă de difuzare care împarte fluxul video în
bucăți scurte, numite segmente. Fluxul `mono.m3u8` este lista acestor segmente: fișiere `.ts` de câte 6 s, comprimate
în formatul H.264, cu imagini de 3288 × 1850 px, la 18 cadre/s. Caracteristicile au fost verificate cu `ffprobe` pe
20.10.2026.

Componenta `FrameSource` citește fluxul prin FFmpeg/OpenCV[^opencv][^ffmpeg], pe un fir de execuție separat. Ea pune
6 cadre pe secundă într-un tampon în memorie și le transmite mai departe la intervale egale, cu o întârziere fixă de
8 s (§ 4.6). Dacă fluxul se întrerupe, componenta se reconectează singură, la intervale care cresc exponențial, de la
1 s până la 30 s.

![Vederea camerei publice din Piața Romană, 28.10.2026, 09:30](imagini/camera_piata_romana.jpg)

*Figura 4.1 – Vederea camerei publice din Piața Romană, miercuri 28.10.2026, la 09:30, pe ploaie. Sursa: Webcam
România – https://webcamromania.ro[^webcam]. În prim-plan se văd Bd. Magheru în stânga și Bd. Dacia est în dreapta,
iar în fundal, Bd. Lascăr Catargiu și clădirea Academiei de Studii Economice (ASE). Persoanele, plăcuțele de
înmatriculare ale tuturor vehiculelor și textul publicitar suprapus de cameră sunt estompate (§ 4.5). Imaginea este
publicată cu acordul scris al Webcam România din 27.10.2026 (§ 14.1) și nu intră sub licențele proiectului.*

**Camere pentru intersecțiile conexe.** Pe 21.10.2026 au fost căutate toate camerele publice din zona modelată: în
lista Webcam România pentru București, cu 8 camere[^webcam-buc], pe Windy Webcams[^windy], pe Meteoblue[^meteoblue]
și în listele de intersecții supravegheate. Rezultatul:

| Camera | Ce arată | Folosită în proiect? |
|---|---|---|
| Webcam România – Piața Romană (HLS) | piața, toate cele 6 brațe și trecerile lor de pietoni; pietonii se văd doar pe cele 2 treceri din prim-plan, iar acolo detectorul pierde mulțimile (§ 4.4) | **da** – singura sursă video a proiectului |
| Webcam România – Piața Victoriei (transmisiune în direct pe YouTube)[^youtube] | pasajul Victoriei, în afara zonei modelate, dincolo de intersecția Lascăr Catargiu × Gh. Manu | nu |
| „Calea Victoriei City Cam” (YouTube) | o imagine statică a Ateneului, fără trafic | nu |
| Windy / Meteoblue „Piața Romană” | aceeași cameră Webcam România | – |
| Listele de „intersecții supravegheate”: Dacia × Dorobanți, Magheru × Enescu | camere ale Poliției sau ale Primăriei Municipiului București (PMB), fără imagine publică | nu (indisponibile) |

Pentru intersecțiile conexe (§ 6.1) nu există, așadar, camere publice. Traficul lor este simulat din datele Pieței
Romane, conform principiului proiectului: cererea de trafic se calibrează pe datele camerei, nu se generează la
întâmplare. În măsura veche, rutele candidate, adică drumurile posibile dintre care se aleg traseele vehiculelor
simulate, pornesc de la marginea rețelei și traversează intersecțiile vecine (§ 5.2), deci fiecare vecin primește
traficul observat care intră în piață sau iese din ea pe brațul lui. Alegerea liberă a rutelor trimitea însă traficul prin
semafoare depărtate, pe care camera nu le vede (§ 6.5, cauza 1). De aceea, în măsura nouă (§ 9.11), cu geamănul corectat din
2.11, rutele pornesc de pe bulevardul fiecărui braț, la 148–566 m de piață, și se opresc pe bulevardul de ieșire, la
130–346 m. Ruta de pe Magheru trece totuși prin două semafoare reale, cu program presupus. În ambele măsuri, la
traficul observat se adaugă traficul de fond declarat, care nu trece prin piață și este egal cu 15% din volumul
observat.

**Calculul pe laptop.** Laptopul proiectului nu are placă grafică NVIDIA. Pe procesor, detectorul YOLO11s, la
rezoluția de lucru de 1600 px, analiza doar ≈0,9 cadre/s. Era prea puțin pentru urmărire: traiectoriile se rupeau, iar
pe Magheru se numărau prea puține vehicule, ≈250 veh/h. De aceea, detectorul este convertit automat în formatul Intel
OpenVINO[^openvino], conceput pentru rularea rețelelor neuronale pe procesoarele și plăcile grafice Intel. Opțiunea
corespunzătoare din `config/camera.json` este `runtime: "openvino"`. Astfel, detectorul rulează pe placa grafică
Intel integrată, cu ≈6 cadre/s, adică aproape toate cadrele pe care le primește de la `FrameSource`, și dă pe cadrul
de test exact aceleași detecții ca înainte: 34 de vehicule și 11 persoane. Procesorul rămâne liber pentru simulare și
pentru antrenarea agenților.

### 4.2 Detecție și urmărire

**Detecția** găsește obiectele din fiecare cadru și încadrează fiecare obiect într-un dreptunghi. Detectorul este
Ultralytics YOLO11[^yolo11], o rețea neuronală antrenată în prealabil pe COCO[^coco], o colecție publică de imagini
adnotate. Clasele COCO folosite, fiecare cu numărul ei din COCO, sunt:

| Clasa COCO | Ce reprezintă în proiect |
|---|---|
| car (2) | autoturism, tipul `passenger` din simulare |
| motorcycle (3) | motocicletă |
| bus (5) | autobuz; clasa include și troleibuzele STB (Societatea de Transport București) |
| truck (7) | camion |
| bicycle (1) | bicicletă |
| person (0) | persoană; servește la numărarea pietonilor pe treceri (§ 4.4) și la estomparea din previzualizare |

Implicit se folosește modelul `yolo11s`, la 1600 px, doar pe regiunea de interes: partea de jos a cadrului, fără cer.
Setările se pot schimba în `config/camera.json`. Pe o placă grafică NVIDIA se folosește `--runtime pytorch --device 0`.
În acest caz, în `.venv`, mediul Python al proiectului, trebuie instalat PyTorch cu suport CUDA, adică varianta care
calculează pe plăcile NVIDIA, cum indică `0_instalare.bat` (§ 11.7).

**Urmărirea** leagă dreptunghiurile de la un cadru la altul, astfel încât fiecare participant la trafic să aibă o
traiectorie, adică șirul pozițiilor lui în imagine. Ea se face cu ByteTrack[^bytetrack], care ia în calcul și
detecțiile cu scor mic, adică pe cele de care detectorul este mai puțin sigur. Acest lucru ajută în cazul ocluziilor
din piață, când un vehicul este ascuns parțial de alt vehicul sau de un obstacol. Alternativa este BoT-SORT[^botsort].

**Punctul de referință** al fiecărui vehicul este mijlocul laturii de jos a dreptunghiului, adică punctul de contact cu
solul. Acest punct depinde mai puțin de perspectivă decât centrul dreptunghiului.

### 4.3 Zonele de intrare/ieșire și matricea origine–destinație

Simularea are nevoie nu doar de numărul vehiculelor, ci și de drumul lor: de unde vin și încotro merg. Această
informație formează matricea origine–destinație (O–D), un tabel cu brațele de intrare pe rânduri, brațele de ieșire pe
coloane și numărul de vehicule pentru fiecare pereche. Datele vin din zone desenate pe imaginea camerei: prima zonă de
intrare prin care trece un vehicul arată de unde vine, iar ultima zonă de ieșire, încotro merge.

**Brațele și zonele.** Camera vede cele șase brațe ale pieței, de la stânga la dreapta:

- Bd. Magheru, în extrema stângă;
- Str. Mendeleev, cu sens unic, doar de ieșire;
- Bd. Dacia vest, în centru-stânga;
- Bd. Lascăr Catargiu, în centru-dreapta;
- Str. Căderea Bastiliei, cu sens unic, doar de ieșire, lângă clădirea ASE;
- Bd. Dacia est, în extrema dreaptă.

Pe fiecare braț cu dublu sens s-au definit **două** poligoane: unul pe banda de intrare spre piață și unul pe banda de
ieșire. Străzile cu sens unic au doar zona de ieșire. Rezultă 10 zone de vehicule, la care se adaugă zonele de trecere
pentru pietoni (§ 4.4). Toate sunt definite în `config/camera.json`, în coordonate normalizate 0–1, adică fracțiuni
din lățimea și din înălțimea cadrului, deci nu depind de rezoluție.

Ieșirile servesc la direcții, adică la proporțiile de viraj, nu la volumele cererii (§ 5.1), care se iau din intrări.
Ca volum, ieșirile intră doar în debitul echilibrat, adică media dintre intrări și ieșiri. După acest debit se aleg
ferestrele zilei, adică orele pentru care se construiesc scenariile de simulare, și cazurile de trafic (§ 5.4, § 9.9).

![Zonele de numărare peste captura din figura 4.1](imagini/camera_zone.jpg)

*Figura 4.2 – Zonele de numărare folosite în timp real și de măsura veche, desenate peste captura din figura 4.1,
fără cer. Verde: intrările, din care se iau volumele. Portocaliu: ieșirile, folosite doar pentru direcții. Albastru:
trecerile de pietoni (§ 4.4). Zonele au fost recalibrate pe 26.10, iar trecerile Mendeleev și Dacia est au fost
corectate pe 28.10 (§ 4.4); toate sunt definite în `config/camera.json`. Măsura nouă, din 2.11, renumără traiectoriile
cu alte zone pe Lascăr Catargiu și pe Dacia vest, din `config/camera_v2.json`, descrise mai jos. Sursa imaginii: Webcam
România; persoanele, plăcuțele de înmatriculare și textul publicitar al camerei sunt estompate.*

**Regula de numărare.** Fiecare traiectorie este analizată în întregime, la închiderea ei, adică după ce urmărirea
vehiculului s-a încheiat. Regula este scrisă în funcția `classify()` din `vision/od_counter.py`:

- *Originea și destinația.* Originea este **prima** zonă de intrare prin care trece vehiculul **înaintea oricărei
  ieșiri**. Destinația este **ultima** zonă de ieșire a **altui** braț, atinsă după origine. Ieșirea de pe brațul de
  origine nu contează, pentru că zonele de intrare și de ieșire ale unui braț sunt alăturate. Prima variantă a regulii
  număra 25 de „întoarceri” Magheru → Magheru în 5 minute; în realitate, erau vehicule care atingeau banda vecină.
- *Brațele îndepărtate.* Dacia vest, Lascăr Catargiu, Mendeleev și Căderea Bastiliei sunt departe de cameră și parțial
  ascunse. Zonele lor de ieșire sunt marcate `capat_traiectorie`: o ieșire acolo contează doar dacă traiectoria
  **se termină** în zonă, cu o toleranță de 1,5 s. Până la recalibrarea din 26.10 erau marcate la fel și intrările
  Dacia vest și Catargiu, care contau doar dacă traiectoria **începea** acolo, adică dacă vehiculul apărea din strada
  ascunsă. Pe 21.10, verificarea sensului de mers cu `recount --directii` a arătat că fosta zonă „intrare Dacia vest”
  prindea, de fapt, vehiculele care treceau prin dreptul străzii pe inelul pieței, adică pe carosabilul din jurul
  insulei centrale: 73 din 74 se îndepărtau de centru.
- *Sensul de mers.* Fiecare zonă cere un **sens de mers** în imagine, cu o abatere admisă de ±60°: spre piață în
  zonele de intrare, dinspre piață în cele de ieșire. Sensul se măsoară pe porțiunea de traiectorie din zonă, iar la
  zonele `capat_traiectorie`, pe primele sau pe ultimele 1,5 s ale traiectoriei. Astfel, zonele unui braț se pot
  suprapune fără să fie confundate.
- *Traiectorii complete și fragmente.* O traiectorie completă dă un viraj, adică o pereche origine → destinație. Una
  fragmentată, a unui vehicul pierdut când a fost ascuns de altceva, contează doar la numărătoarea pe braț.

**Reunirea fragmentelor.** La 5 cadre/s, stâlpii, autobuzele și copacii întrerup urmărirea, iar traiectoria unui
vehicul se rupe în bucăți, numite fragmente. De aceea, înainte de numărare, `recount` reunește fragmentele aceleiași
traiectorii. Un fragment care se termină este legat de unul care începe cel mult 2 s mai târziu, dacă acesta pornește
aproape de poziția prezisă din viteza de la capătul primului, are aceeași categorie și o direcție compatibilă. Așa se
reunesc ≈12% dintre fragmente. Chiar și după reunire, doar ≈25–45% dintre vehicule sunt urmărite de la intrare până la
ieșire, după raportul dintre viraje și intrări din `data/counts`: 41% pe 28.10 și 45% pe 29.10. Matricea O–D se sprijină deci în principal pe
totalurile pe brațe (§ 5.1).

Numărătorile se adună pe intervale de 15 minute, separat pe tipuri de vehicule, în
`data/counts/numaratori_AAAA-LL-ZZ.csv`, unde AAAA-LL-ZZ este data zilei. Măsura nouă, descrisă mai jos, își face
numărătorile din jurnalul de traiectorii, cu zonele ei și cu pietonii numărați pe persoane, în `data/counts_cor/`, cu
comanda din § 11.8; pentru zilele noi, le face prelucrarea de noapte a măsurii noi (§ 9.11).

**Jurnalul de traiectorii și renumărarea.** Pe lângă numărători, modulul salvează local fiecare traiectorie închisă
în `data/trajectories_brute/traiectorii_AAAA-LL-ZZ.jsonl.gz`. Fișierul este exclus din Git, deci nu ajunge în
depozitul public. Pentru fiecare traiectorie se păstrează doar:

- clasa obiectului;
- momentul de început `t0`, în timp Unix, adică în secunde de la un moment de referință fix, cu precizie de 0,01 s;
- pozițiile punctului de contact cu solul, în coordonate normalizate, fiecare cu timpul ei față de `t0`.

Jurnalul nu conține imagini, numere de înmatriculare sau identificatorul de urmărire. Datorită lui, zonele pot fi
recalibrate **după** colectare: `python -m romana.vision.recount` reface numărătorile din jurnalul local. La test,
rezultatul a fost identic cu cel al numărării în timp real. Dacă operatorul mută camera, zonele se redesenează cu
`scripts\2b_calibrare_zone.bat`, iar `recount` reface numărătorile din jurnal.

În depozit, `data/trajectories/` conține doar rezultatul comenzii `python -m romana.vision.recount --publica`:
traiectoriile vehiculelor, inclusiv ale bicicletelor și motocicletelor, cu fragmentele deja reunite, fără pietoni, în
același format. Pe acest jurnal publicat, renumărarea vehiculelor reproduce renumărarea din jurnalul complet.
Verificarea s-a făcut pe ziua de 22.10. Cu zonele din 23–24.10, rezultatul a fost exact același: 10 726 de intrări,
2 238 de viraje și 0 din 53 de intervale diferite. Cu zonele actuale, recalibrate pe 26.10, jurnalul publicat dă
13 414 intrări, față de 13 413 din cel complet, adică o singură intrare în plus, pe Dacia vest, la 10:15–10:30, și
aceleași 3 270 de viraje. În depozit, pietonii apar doar în numărătorile agregate din `data/counts/`.

Tot din jurnal, comanda `recount --flux` desenează câmpul de mișcare al vehiculelor și capetele traiectoriilor.
Câmpul de mișcare arată direcția în care se deplasează vehiculele în fiecare loc al imaginii, iar capetele arată unde
încep și unde se termină traiectoriile. Ambele au servit la plasarea zonelor.

Zonele actuale sunt rezultatul mai multor etape, descrise mai jos în ordine cronologică.

**Calibrarea pe datele de zi (21.10.2026).** Pozițiile zonelor au fost stabilite atunci din jurnalul primelor 1,5 ore
de traiectorii, adică din ≈16.000 de fragmente. Câmpul de mișcare arată sensul fiecărei benzi; pe inel, de exemplu, se
circulă în sens trigonometric, adică în sens invers acelor de ceasornic. Hărțile cu începuturile și sfârșiturile
traiectoriilor arată unde apar vehiculele din străzile parțial ascunse și unde dispar în ele: Lascăr Catargiu sus, la
centru; Dacia vest în spatele stației de troleibuz; Căderea Bastiliei sus, în dreapta. Ordinea brațelor în imagine
este confirmată de geometria rețelei din harta liberă OpenStreetMap (OSM): din poziția camerei, fiecare braț are un
anumit azimut, adică o anumită direcție față de nord. Camera privește spre vest, deci în stânga imaginii este sudul,
cu Magheru, iar în dreapta, nordul, cu Căderea Bastiliei. Atunci s-au corectat următoarele greșeli: fosta zonă de
intrare Dacia vest era pe inel; zona Căderea Bastiliei era prea sus și număra 0 vehicule; intrarea Dacia est stătea
parțial peste trecerea de pietoni, pe când vehiculele circulă deasupra ei.

**Zonele desenate de autor (23–24.10.2026).** Autorul a decupat 16 zone pe capturi ale camerei: 10 zone de vehicule și
6 treceri. Capturile erau făcute pe un ecran de 1920 px, iar decupajele au fost regăsite automat în cadrul de 3288 px
prin potrivirea punctelor caracteristice (SIFT), adică a detaliilor care se recunosc în ambele imagini. Scara a fost
fixată la 3288/1920, iar poziția s-a ales prin vot pe translație: s-a păstrat deplasarea propusă de cele mai multe
perechi de puncte potrivite. Două zone cu prea puține repere au fost poziționate manual, cu forma și mărimea
decupajului. Aceste zone au înlocuit calibrările anterioare: cea din traiectoriile primelor ore, descrisă mai sus, și
redesenarea din 22.10 (§ 12.2). Ele au fost folosite până la recalibrarea din 26.10, descrisă mai jos.

**Auditul numărării (25.10.2026).** În realitate, fiecare vehicul care intră în piață iese din ea. Cu zonele de
atunci, cele din 23–24.10, camera număra totuși, în medie, **1,6 ieșiri pentru fiecare intrare**; cu zonele actuale,
≈1,4 pe 21–26.10 și ≈1,2 pe zilele întregi din 28.10 încoace, între 1,17 și 1,26. Harta capetelor de traiectorie arată
cauza. Pe inelul din fundal, vehiculele sunt atât de mici încât detectorul le pierde oriunde, iar un vehicul pierdut în
dreptul unei ieșiri îndepărtate pare „ieșit” pe ea. S-a încercat corectarea regulii după principiul conservării
vehiculelor: câte vehicule intră, atâtea trebuie să iasă. Criteriile
încercate au fost un număr minim de cadre în zonă, o înaintare minimă pe stradă și un prag raportat la lungimea zonei;
în cod, ele sunt pragurile `Params.capat_min_*`, iar rezultatele sunt în `docs/rezultate/calibrare_conservare*.csv`.
Orice prag care aduce raportul ieșiri/intrări la ~1 elimină însă aproape complet și ieșirile reale spre Dacia vest și
Căderea Bastiliei. Cu această cameră, ieșirile de acolo **nu pot fi deosebite** de vehiculele pierdute. Concluzia:
ieșirile de pe brațele îndepărtate nu sunt o măsurătoare de încredere. Regula rămâne neschimbată, iar pragurile noi
sunt dezactivate; consecința pentru cerere este tratată în § 5.1. Pe brațele apropiate, Magheru și Dacia est, precum și
pe trecerea mare de pe Dacia est, numărarea este coerentă.

**Recalibrarea pe o numărătoare de referință (26.10.2026).** La cererea autorului, toate zonele au fost reanalizate de
la zero și alese după măsurători, nu după aspect.

*Numărătoarea de referință.* Pentru a afla cât din trafic prinde camera, era nevoie de o numărătoare independentă, pe
aceleași imagini. S-au folosit două clipuri de câte 3 minute, din 26.10, de la 11:58 și de la 12:19. Ele au fost
adnotate, adică numărate cadru cu cadru, pe foi de contact: planșe cu cadre luate la fiecare 0,5 s. Clipurile au fost
păstrate doar local și au fost șterse după adnotare. **Doi adnotatori AI independenți**, adică două instanțe separate
ale asistentului Claude (§ 13), nu oameni, au numărat separat, pe fiecare țintă și pe fiecare bucată de 30 s. Țintele
au fost intrările de pe cele 4 brațe și zebrele. Când diferența dintre adnotatori depășea max(2; 15%), adică era mai
mare și decât 2, și decât 15%, decidea un al treilea, ca arbitru. Foile de contact citite de adnotatori au fost
trimise spre analiză la Anthropic (§ 4.5). Aceleași clipuri au trecut și prin lanțul de prelucrare folosit în timp
real, cu YOLO11s la 1600 px și 6 cadre/s, deci referința și numărarea automată văd exact aceleași cadre. Clipurile au
mici salturi de câteva secunde, aceleași pentru amândouă. Adnotatorii au corectat și o greșeală de țintă: vehiculele
care intră dinspre Lascăr Catargiu coboară pe carosabilul din stânga spațiului verde și virează pe după monument.

*Calibrarea camerei pe rețea.* Pentru a lega imaginea de rețeaua rutieră, s-au căutat puncte care se recunosc atât în
imagine, cât și în rețeaua OSM: capetele zebrelor și liniile de oprire. Din aceste perechi s-a calculat o omografie a
planului străzii, adică transformarea geometrică care duce planul străzii din hartă în planul imaginii. În fundal,
eroarea este de ≈14 px, adică sub ≈1 m. În prim-planul de lângă cameră nu se potrivește niciun model plan unic, din
cauza distorsiunii obiectivului și a unui decalaj local al hărții OSM. Acolo, zonele s-au desenat pe marcajele reale,
pe un fundal median din 90 de cadre, adică pe o imagine compusă din care vehiculele lipsesc, și au fost verificate pe
câmpul de mișcare. Tot atunci s-a constatat că zona cu dungi din stânga-jos, unde parchează uneori o mașină, este o
**zonă hașurată, nu o trecere de pietoni**, deci acolo nu se numără pietoni.

*Rezultatul.* Tabelul arată ce parte din vehiculele din referință prinde numărarea automată, pe bucățile adnotate ale
fiecărui clip. Procentele sunt valorile „prins” afișate de comanda `referinta factori` (§ 11.8). O valoare de peste
100% înseamnă că numărarea automată a găsit mai multe vehicule decât referința.

| Brațul și zona | Clipul 1 | Clipul 2 | Ce arată |
|---|---|---|---|
| **Dacia vest**, zona veche, din versiunea `e1d0f77` a proiectului | 27% | 37% | zona veche prindea puțin din mașinile care ies din bulevard spre cameră |
| **Dacia vest**, zona nouă | **90%** | **89%** | zona nouă prinde aceste mașini, după linia de oprire |
| **Magheru** | 84% | 96% | zona existentă era deja bună și a rămas |
| **Dacia est** | 98% | 124% | zona existentă era deja bună și a rămas |
| **Lascăr Catargiu** | 44% | 38% | limita este detectorul, nu zona: vehiculele sunt mici și departe |

La 2560 px, pe clipul 1 / clipul 2, detectorul prinde pe Catargiu 83% / 60% și pe Magheru 101% / 91%. Pe placa
grafică integrată a laptopului, el prelucrează însă doar ≈2,3 cadre/s, față de ≈4,4 la 1600 px. Este prea puțin pentru
urmărirea în timp real, așa că rezoluția mai mare rămâne o recomandare pentru un calculator cu placă grafică dedicată.

*Factorii de corecție a detecției.* Factorul unui braț este raportul dintre numărătoarea de referință și cea automată,
pe ambele clipuri; intrările numărate automat pe acel braț se înmulțesc cu el. Pe Lascăr Catargiu, de exemplu, unde
camera prinde mai puțin de jumătate dintre vehicule, factorul este 2,52. Intervalele de încredere de 90% arată cât de
precis este estimat fiecare factor. Ele au fost calculate prin bootstrap pe bucăți, adică prin reeșantionarea repetată
a bucăților adnotate.

| Brațul | Factorul de corecție | Intervalul de încredere de 90% |
|---|---|---|
| Magheru | **1,09** | [1,02; 1,16] |
| Dacia est | **0,88** | [0,57; 1,05] |
| Dacia vest | **1,12** | [0,70; 1,42] |
| Lascăr Catargiu | **2,52** | [2,06; 3,00] |

Factorii sunt trecuți în `config/demand.json`, la `factor_corectie_detectie`. Ei înlocuiesc presupunerea de dinainte
cu o calibrare măsurată. Potrivit acelei presupuneri, cererea se afla între „doar intrări” și „media intrări / ieșiri”
(§ 5.1). Limita lor: se sprijină pe două clipuri de 3 minute, ambele de la prânz, deci trebuie confirmați și la alte
ore. Seara, factorul de la prânz nici nu ajunge: pe Lascăr Catargiu, numărarea aproape dispare după apus, cel mai probabil
din cauza întunericului și a poziției zonei. Pe 29.10 s-au numărat 212 intrări brute între 16:00 și 17:00, 9 în ora
următoare și 0 între 18:00 și 19:00, iar pe 26.10, 240, 55 și 4. De aceea, scenariile de seară au puțin trafic de pe acest
braț (§ 9.10, § 9.11). În `docs/rezultate/referinta/` sunt publicate numărătorile adnotatorilor, factorii, corespondențele folosite la
calibrarea camerei și traiectoriile vehiculelor din clipuri, acestea din urmă fără pietoni și fără imagini. Comenzile
sunt descrise în § 11.8.

**Reverificarea din 29.10.** După testul final, zonele au fost verificate din nou, fără nicio schimbare. Pe
traiectoriile din 28.10, 94% dintre vehiculele în mișcare ating o zonă de vehicule. Restul sunt fragmente scurte pe
inel și ≈100–500 de traiectorii pe zi în colțurile de jos ale cadrului; acestea din urmă reprezintă sub 1%. S-a făcut
și un fundal median nou, din 40 de cadre luate la câte 2 s, pe 29.10, la ≈09:25, pe ploaie; cadrele au fost păstrate
doar local și apoi au fost șterse. Pe noul fundal median, toate zonele de vehicule stau pe carosabil, pe benzile
sensului lor: intrările pe banda spre piață, ieșirile pe banda dinspre piață. În fundal, zonele se suprapun cu benzile
OSM proiectate în imagine. În prim-plan, proiecția OSM se abate, ca la calibrarea camerei, iar zonele urmează
marcajele reale.

**O măsură nouă, verificată pe întuneric (1–2.11.2026).** La verificarea bornei M1 a ieșit la iveală că, seara, Lascăr Catargiu
aproape dispare din numărători, deși mașinile trec mai departe. Pe clipurile de seară din 1.11, zona veche a prins 21, 1 și 0
vehicule în 5 minute, iar numărătoarea atentă a găsit 87,5, 127,5 și 113,5. Am numărat deci din nou, am căutat o zonă pe care
detectorul o vede și pe întuneric și am ținut rezultatul separat, ca măsură nouă, cu prefixul `cor_`. Măsura veche nu s-a schimbat:
renumărarea din 29.10 iese identică, octet cu octet, iar regulile celor două măsuri sunt în § 9.11.

*Felii timp-spațiu.* Foile de contact merg bine, dar costă mult, iar pe un drum îndepărtat, noaptea, se văd doar lumini. De aceea
s-a folosit și o a doua metodă, simplă: din fiecare cadru se ia aceeași linie de pixeli, așezată de-a curmezișul drumului, și
liniile se pun una lângă alta, în ordinea timpului. Rezultă o singură imagine cu 30 de secunde din acel loc, iar un vehicul care
trece apare ca o pată. Două linii alăturate arată și sensul de mers, după ordinea în care le atinge vehiculul. O astfel de felie
costă ≈0,24 USD pe bucata de 30 s, față de ≈0,63 USD pentru foi. Pe Lascăr Catargiu, foile au dat cu 0–9% mai mult decât feliile,
iar pe Magheru cu 13–22% mai mult, așa că referința finală rămâne pe foi, iar feliile sunt folosite acolo unde foile nu pot
deosebi sensurile. Ca și pe 26.10, au numărat doi adnotatori AI independenți, iar la diferențe mari, un arbitru (§ 13).

*Ce trece de fapt pe Lascăr Catargiu.* Numărătoarea a arătat că prin acel loc nu trece un singur flux, ci trei:

- **banda principală**, spre Magheru, adică traficul pe care îl voiam;
- **drumul de sus**, ≈31% din traficul bulevardului, numărat ca flux în etapa Magheru–Catargiu. Cea mai mare parte continuă pe inel;
  spre Dacia vest merg doar ≈4% din vehiculele de pe Catargiu, numărate direct pe banda ieșirii. Detectorul nu le poate urmări până
  la capăt, deci în simulare destinația lor se dă ca o cotă fixă, declarată (§ 5.1);
- **inelul dinspre est**, care circulă exact în fazele în care Catargiu are roșu. El nu e trafic de pe Catargiu și nu trebuie numărat
  acolo. Pe inel trec aproape tot atâtea vehicule câte intră dinspre Dacia est, dar asta nu înseamnă că nimeni din Dacia est nu iese
  spre Catargiu, cum am crezut întâi: pe inel trec și vehiculele de pe Magheru care ocolesc piața. Numărate direct, ≈40% din cele de
  pe Dacia est ies spre Catargiu, cum arătau și traiectoriile.

Numărătorile de referință ale măsurii noi, pe toate cele 11 clipuri din 1.11 și 2.11, factorii de corecție și momentele pietonilor
pe valuri sunt publicate, fără imagini, în `docs/rezultate/referinta_v2/`. Tabelul dă numărătoarea de referință pe cele trei clipuri
din 1.11, vehicule în 5 minute. Primul clip e pe lumină, iar celelalte
două sunt după apus, care a fost la ≈17:05.

| Locul | 16:45 | 17:45 | 18:30 |
|---|---|---|---|
| Lascăr Catargiu, fără inel | 87,5 | 127,5 | 113,5 |
| Inelul dinspre est | 29,5 | 38 | 26 |
| Dacia est, intrări | 28,5 | 34 | 24 |
| Dacia vest, intrări | 48 | 41 | 37 |
| Magheru, intrări | 165 | 172,5 | 156,5 |

*Zona nouă.* Pe traiectoriile din clipuri s-au încercat sistematic multe zone. Pe cea aleasă, numărarea automată prindea atunci 76% din
Catargiu și doar 9% din inel, față de numărarea pe felii, iar pe cele 30 de bucăți de 30 s o urmărea bine: corelația era 0,967.
Prima variantă, cea din plan, prindea 53%, respectiv 29%, cu o corelație de 0,884. Tot atunci s-a îngustat și zona de pe Dacia vest. Față de referința finală din tabel, pe aceleași clipuri, zona nouă prinde 79, 91 și 67 de vehicule: 72% în total și cam două treimi după apus. Zonele au fost
fixate prin două commit-uri, `b6a0adc` și `573217f`, **înaintea** clipurilor de verificare, ca să nu poată fi potrivite după ele.
Ele stau în `config/camera_v2.json`, iar `config/camera.json`, al măsurii vechi, a rămas neatins.

*Pietonii, pe persoane.* Măsura nouă numără un pieton o singură dată, chiar dacă atinge mai multe zone de trecere. Pe 29.10, raportul
dintre numărarea pe zone și cea pe persoane este 1,218.

*Factorii măsurii noi.* Din aceleași clipuri din 1.11 și 2.11, 11 în total, iar pe Dacia vest 8, s-au calculat și factorii de
corecție ai măsurii noi. Pe Magheru și pe Lascăr Catargiu ei sunt diferiți ziua și pe întuneric: Magheru 1,19 ziua și 1,39 pe
întuneric, iar Lascăr Catargiu, pe zona nouă, 1,16 și 1,56. Pe Dacia est și pe Dacia vest se folosește câte un singur factor: 0,99 și
1,26. Factorii de întuneric sunt valabili doar pe orele fără pierdere de detecție; o oră cu pierdere iese din decizie (§ 9.11). Cum se
hotărăște dacă un sfert de oră e de zi sau de întuneric se explică în § 5.1. Factorii sunt în `config/factori_v2.json` și au fost
înghețați pe 3.11, înainte de a privi datele acelei zile (§ 9.11). Factorii din tabelul de mai sus, din 26.10, sunt ai măsurii vechi.

### 4.4 Pietoni și bicicliști

În simulare intră toți participanții la trafic pe care îi vede camera, nu doar vehiculele. Pietonii contează pentru
semafor: cei care așteaptă la bordură formează cererea pentru faza de pietoni, adică pentru verdele lor. Ei sunt
numărați pe trecerile de pietoni din imagine, iar rezultatul se extinde apoi la toată piața. Bicicletele se numără ca
vehicule, iar persoana de pe o bicicletă sau de pe o motocicletă nu este numărată ca pieton.

**Unde se numără pietonii.** Numărarea se face în zonele cu rolul `trecere` din `config/camera.json`, așezate peste
trecerile de pietoni. Aceste zone au fost refăcute pe 26.10.2026 și acoperă:

* zebra de pe Magheru;
* cele două zebre ale trecerii duble de pe Dacia est, una peste ieșire și una peste intrare, cu refugiul dintre ele;
* trecerile din fundal: Mendeleev, Dacia vest, Lascăr Catargiu și Căderea Bastiliei. Zonele lor au fost proiectate în
  imagine, adică transpuse din rețeaua rutieră construită după harta OSM.

În practică, detectorul îi vede pe pietoni doar pe trecerile din prim-plan, iar acolo pierde mulțimile (corectura de mai jos): pe Magheru, unde
trecerea este la marginea cadrului și parțial ascunsă de un chioșc, și mai ales pe Dacia est. Pe trecerile
îndepărtate, persoanele sunt prea mici în imagine pentru detector.

**Cum se numără un pieton.** Persoanele detectate sunt urmărite de la un cadru la altul cu același algoritm ca
vehiculele, ByteTrack. De la 26.10.2026, fiecare trecere are în configurație trei elemente:

* zebra reală, desenată ca poligon;
* axa zebrei, adică linia de la o bordură la cealaltă;
* câte o zonă de așteptare la fiecare bordură.

Zonele de așteptare au fost ideea autorului. Ele sunt restrânse la imediata apropiere a zebrei, ca să nu fie numărați
trecătorii de pe trotuar. Un pieton este numărat o singură dată pe fiecare trecere dacă îndeplinește una dintre
următoarele două condiții:

* a înaintat de-a lungul axei zebrei cel puțin 30% din lungimea ei. Cine doar trece pe lângă zebră nu se numără;
* a așteptat la bordură între 5 și 120 s. Așteptarea arată cererea pentru faza de pietoni, iar regula îi prinde astfel
  și pe cei pe care detectorul îi pierde apoi printre vehicule. Cine stă mai mult pe loc, de exemplu în stația de
  autobuz sau la chioșc, nu se numără. Nu se numără nici obiectele nemișcate pe care detectorul le ia drept persoane.

Pragul de 5 s a fost ales cu ajutorul numărătorii de referință (§ 4.3), cu care se compară numărarea automată. Cu
acest prag, numărarea automată pe trecerile de pe Dacia est ajunge la 95–110% din referință, față de numai 20–60% fără
zonele de așteptare. Eșantionul este însă mic: 2–3 bucăți de 30 s pe fiecare zebră.

**Corectură, 2.11.2026.** Numărătoarea de referință pe clipurile din 2.11 arată că rezultatul de mai sus nu se generalizează. Detectorul
pierde mulțimile: pe aceleași bucăți, adnotatorii găsesc pe o zebră de pe Dacia est, în medie, de 1,86 ori mai multe persoane decât
numără el (intervalul de încredere pe clipuri, 1,38–2,32), iar la prânz, pe ploaie, de ≈3 ori mai multe. În mulțimile dense, numărul
adnotatorilor e doar un ordin de mărime. Urmarea pentru geamăn e în § 6.5, la cauza 8.

În tabelele cu numărători, salvate ca fișiere CSV, pietonii apar pe rânduri de tip `pietoni`, cu brațul și trecerea.
Debitul de pietoni măsurat, adică numărul lor pe oră, se extinde la toată piața prin înmulțire cu
`factor_extrapolare_pietoni` = 2,5, valoare stabilită în `config/demand.json`. Factorul este ales, nu calculat, deci rămâne
o ipoteză declarată, iar 2,5 e valoarea măsurii vechi. Pe 26, 28 și 29.10, 96–98% dintre pietonii numărați sunt pe trecerea dublă
de pe Dacia est. În măsura nouă, înghețată pe 3.11, cererea de pietoni din geamăn e efectivă, nu numărul real: pe Dacia est, geamănul
pune 0,25 agenți la o persoană numărată de detector (§ 6.5, cauza 8), iar pe toată piața, tot prin ipoteză, de 3,27 ori mai mulți
agenți decât pe Dacia est. Restul se împarte în mod egal între celelalte trei brațe cu treceri comandate de semafor.
Valorile sunt în `config/factori_v2.json`.

**Dublurile.** Numărarea se face pe zone, nu pe persoane: cine traversează ambele zebre ale trecerii duble de pe Dacia est
apare în ambele. Dublurile sunt 13–21% din sumă, pe 8 zile, și ≈18% pe Dacia est, pe 29.10. Numărarea pe persoane intră ca
variantă în măsura nouă (§ 9.11).

**Bicicliști și motocicliști.** Bicicleta, clasa 1 din lista detectorului, se numără ca orice alt vehicul, pe zonele
de intrare și de ieșire. În simulatorul SUMO, bicicletele primesc rute pe care au acces. Persoana de pe bicicletă sau
de pe motocicletă **nu** se numără ca pieton. Dacă punctul în care o persoană atinge solul cade în dreptunghiul desenat
de detector în jurul unei biciclete sau al unei motociclete, lărgit cu 25%, persoana este exclusă. Regula este scrisă
în funcția `is_rider` din `vision/od_counter.py`.

**Corecturile din 28.10.** În urma observațiilor autorului, zonele trecerilor Mendeleev și Dacia est au fost corectate
înainte de prelucrarea zilei de test. Zonele pentru vehicule au rămas neschimbate.

* *Mendeleev.* Cele două zone vechi stăteau acolo unde programul netconvert presupune că se află trecerea. Programul
  face parte din pachetul SUMO și construiește rețeaua simulării din harta OSM. Locul presupus cade însă peste banda
  cu mașini parcate și taxiuri de pe Str. Mendeleev. Pe 28.10, zona a fost mutată pe zebra marcată în OpenStreetMap,
  înregistrată acolo ca o cale de 10,3 m, cu numărul 1104820827. Noua zonă stă mai la stânga, lângă colțul clădirii
  BCR. Ea a fost proiectată cu modelul camerei, care leagă punctele de pe hartă de cele din imagine (§ 4.3). Pe locul
  real, camera nu vede trecerea: o ascund un stâlp, niște copaci și mașinile parcate. Pe 28.10, traiectoriile au
  arătat doar 2 traversări ale străzii în tot cadrul. Pietonii de pe Mendeleev intră deci în cererea de trafic doar
  prin factorul de extrapolare.
* *Dacia est.* Trecerea dublă este, de fapt, o singură trecere peste bulevard: în OSM, o singură cale de trecere
  traversează ambele carosabile. Între cele două zone rămăsese neacoperită porțiunea din mijloc a zebrei. Pe 28.10,
  prin această porțiune au trecut 2 786 de traiectorii de pietoni, majoritatea între trotuarul de lângă cameră și cel
  din dreapta-sus. Zona de peste intrare a fost prelungită până la cea de peste ieșire.
* *Celelalte treceri*, adică Magheru, Dacia vest, Lascăr Catargiu și Căderea Bastiliei, se potrivesc cu punctele
  marcate ca treceri în OSM, proiectate în imagine.
* *Efectul.* Ziua de luni a fost renumărată cu regula de numărare a proiectului. Totalul pietonilor numărați a crescut
  cu ≈4%, de la 20 579 la 21 382, mai ales pe zebra de peste intrarea Dacia est, de la 9 235 la 10 185. Cele 147 de
  „traversări” numărate în zona veche de pe Mendeleev erau, cel mai probabil, detecții false.

Jurnalul de traiectorii păstrează drumul fiecărui obiect prin imagine și nu depinde de zone. De aceea, o corectură a
zonelor nu cere o colectare nouă de date: numărătorile se refac din jurnal cu `romana.vision.recount`.

### 4.5 Confidențialitate

Imaginile camerei pot conține persoane și numere de înmatriculare. De aceea, prelucrarea lor intră sub incidența
Regulamentului general privind protecția datelor (GDPR)[^gdpr] și a ghidului 3/2019 al Comitetului european pentru
protecția datelor (EDPB) privind dispozitivele video[^edpb]. Principalele garanții sunt trei: în funcționarea normală
nu se păstrează nicio înregistrare video, numerele de înmatriculare nu se citesc, iar traiectoriile pietonilor nu se
publică. Singurul cadru publicat are persoanele și plăcuțele estompate.

Măsurile luate sunt următoarele.

* **Prelucrare doar în memorie.** Cadrele se prelucrează în memorie, iar modulul de viziune nu salvează nicio
  înregistrare video. În funcționarea normală, singura imagine scrisă pe disc este previzualizarea pentru dispecerat.
  Ea are persoanele estompate, este micșorată la 960 px lățime, se suprascrie continuu și se afișează doar local, pe
  calculatorul care rulează sistemul. Butonul „Ascunde imaginea” din dispecerat o scoate de pe ecran, de exemplu înaintea
  partajării ecranului la o prezentare online, iar în locul ei apare starea senzorului (§ 4.6); măsurarea traficului
  continuă. Cu adresa terminată în `?imagine=0`, cum o deschide demonstrația bornei M3, pagina pornește fără imagine și
  nici n-o cere de la server (§ 8, § 11.5). Alegerea făcută cu butonul se ține minte doar în browserul în care s-a făcut.
* **Imaginile folosite la calibrare.** Pentru calibrarea zonelor s-au folosit, temporar, capturi și scurte clipuri ale
  camerei. Ele au fost păstrate local, nu au fost publicate și au fost șterse după calibrare. Capturile, foile de
  contact ale clipurilor și decupajele lor au fost însă citite, neestompate, de asistentul Claude (§ 13). O foaie de
  contact este o singură imagine cu mai multe cadre micșorate ale unui clip, puse unul lângă altul. Prin citire,
  imaginile au fost trimise spre analiză modelului, la Anthropic. Copii ale lor au rămas, ca imagini, în jurnalele
  locale ale sesiunilor Claude Code.
* **Clipurile din săptămâna 1–7.11.2026.** Ca să se verifice numărarea pe întuneric și pe ploaie, s-au salvat din
  nou, temporar, câteva clipuri de câte 5 minute. Regulile sunt aceleași: rămân doar pe calculatorul autorului, nu
  intră în Git, nu se publică și se șterg după numărătoarea de referință, împreună cu foile de contact și cu feliile
  timp-spațiu făcute din ele (§ 4.3). Foile și feliile citite de adnotatori ajung spre analiză la Anthropic, de data
  aceasta în loturi, prin interfața de programare, cu o cheie păstrată în afara depozitului (`romana.vision.referinta_lot`).
  Acordul din 27.10.2026 (§ 14.1) nu pomenește clipurile: salvarea lor temporară este decizia autorului, ca parte a
  analizei automate, și nu lărgește ce se publică.
* **Sondarea cu oameni.** Pe 3–7.11, persoanele invitate de autor au putut folosi dispeceratul pe propriul calculator, într-o pagină publică (§ 8).
  Temeiul este consimțământul lor, conform art. 6 alin. (1) lit. a) GDPR, dat pe un ecran separat, și se pot opri oricând. Pagina nu
  cere nume, cont sau adresă de e-mail, nu folosește cookie-uri, iar o regulă de securitate a browserului oprește orice cerere pe care
  ar face-o singură. Răspunsurile, apăsările și timpii stau în fila persoanei. La final, persoana vede tot ce s-a notat și, dacă vrea,
  trimite textul printr-un formular Google al autorului, care nu colectează adrese de e-mail; adresa formularului apare doar în
  linkurile de invitație, nu în depozit. Cine găsește singur pagina o poate încerca, dar nu are ce trimite. GitHub, care găzduiește
  pagina, notează adresa IP a vizitatorilor, iar Google o vede la deschiderea formularului. Răspunsurile sunt pseudonimizate, nu
  anonime, fiindcă participanții sunt puțini și autorul poate bănui al cui e un răspuns. Ce citește asistentul Claude ajunge la Anthropic.
  Nu se înregistrează imagine sau sunet. Răspunsurile primite stau în foaia de calcul a formularului și, pe calculatorul autorului,
  în `outputs/sondare`, în copiile de lucru și în jurnalele locale ale sesiunilor asistentului Claude, care le-a citit. S-au publicat
  doar totaluri pe grup, de la cel puțin trei persoane; timpii și apăsările au rămas doar local (§ 8). Datele se șterg după
  evaluarea academică sau mai devreme, la cerere, în afară de copiile ajunse la Anthropic, care se păstrează după regulile
  furnizorului. Din 3.11, seara, textul se încheie cu un cod de control, care arată dacă a ajuns neschimbat și care răspunsuri se
  potriveau cu ce arăta aplicația, fără să le scrie pe ecran; dacă în aceeași filă a mai răspuns cineva, textul următor spune doar
  atât (§ 8).
* **Imaginile publicate.** Singurele imagini publicate sunt figurile 4.1 și 4.2, făcute dintr-un singur cadru, din
  28.10.2026, ora 09:30. Același cadru apare și în prezentarea bornei M1 (`docs/prezentari/`). Pe acest cadru s-au estompat automat persoanele, bicicliștii și motocicliștii, banda
  plăcuțelor de înmatriculare la toate vehiculele și textul publicitar suprapus de cameră. Pe oameni i-a găsit
  detectorul YOLO11, care a analizat imaginea pe bucăți suprapuse parțial. Fiecare persoană găsită a fost estompată
  cu o margine în jur. La cererea autorului, plăcuțele au fost estompate la toate vehiculele, pentru o imagine
  uniformă, deci și la cele îndepărtate, deși acolo nu se pot citi.
* **Verificarea imaginii publicate.** Imaginea a fost apoi împărțită în 9 bucăți și verificată vizual, în două
  runde, de agenți independenți, adică de instanțe separate ale asistentului Claude. Prima rundă a găsit 19 locuri
  pe care detectorul le scăpase, mai ales pietoni mici pe trotuarele din fundal; acestea au fost apoi estompate
  manual. A doua rundă nu a mai găsit nicio persoană sigur neestompată. Ea a semnalat totuși 14 locuri incerte, adică
  forme mici la marginea zonelor deja estompate și posibile siluete îndepărtate, care au fost și ele estompate,
  preventiv. Cadrul brut a fost șters.
* **Numerele de înmatriculare nu se citesc.**
* **Identificatorii de urmărire sunt temporari.** Numărul pe care urmărirea îl dă fiecărui obiect se uită la închiderea
  traiectoriei.
* **Ce se publică.** Se publică doar numărători agregate, adică totaluri pe intervale de timp, și, pentru zilele de
  până la 7.11, jurnalul de traiectorii al vehiculelor, inclusiv al bicicletelor și al motocicletelor. Tot așa se publică și
  traiectoriile vehiculelor din clipurile numărătorii de referință (§ 4.3). De la 8.11 se publică doar numărătorile, iar jurnalul
  zilelor noi rămâne pe laptop. Pentru fiecare traiectorie se publică clasa obiectului,
  momentul de început `t0` și pozițiile punctului în care obiectul atinge solul, în coordonate raportate la mărimea
  imaginii. Nu se publică imagini și nici identificatori, deci datele sunt pseudonimizate: nu arată direct cui
  aparțin, dar nici nu sunt complet anonime. Traiectoriile individuale ale pietonilor rămân doar în jurnalul local,
  `data/trajectories_brute/`, care nu se publică. Versiunile vechi ale jurnalelor publicate, care le conțineau, au
  fost eliminate din tot istoricul depozitului pe 26.10.2026 (§ 12.5).

Riscul de reidentificare, adică riscul ca datele să fie legate de o persoană anume, nu este zero. O traiectorie arată
unde și când s-a aflat un anumit obiect, deci îl deosebește de toate celelalte. În principiu, ea ar putea fi pusă în
legătură cu alte imagini ale aceleiași camere. Riscul este cu atât mai mare cu cât momentul de început `t0` este
păstrat, deocamdată, cu o precizie de 0,01 s. De aceea, traiectoriile nu sunt numite anonime, iar licența deschisă a
datelor (§ 14.1) nu ar face publicabile date personale.

Prin fișierul `.gitignore`, fișierele video `.ts` și `.mp4` sunt excluse din Git, sistemul care păstrează versiunile
proiectului. Depozitul și PDF-urile conțin un singur cadru al camerei, estompat, folosit în figurile 4.1 și 4.2 și în
prezentarea bornei M1. Fluxul
camerei este public, iar utilizarea lui este strict academică. Webcam România, care publică fluxul, și-a dat acordul
scris pe 27.10.2026 pentru două lucruri: analiza automată a fluxului în scop academic și necomercial, cu sursa
indicată, și publicarea a cel mult două capturi cu persoanele estompate (§ 14.1)[^webcam]. Orice altă utilizare cere
un acord nou: de exemplu, o utilizare comercială, publicarea altor imagini sau a unor imagini cu persoane neestompate.

**Informarea persoanelor vizate (art. 14 GDPR).** Persoanele vizate sunt participanții la trafic surprinși de cameră.
Informarea individuală a trecătorilor este imposibilă (art. 14 alin. (5) lit. b) GDPR). De aceea, informarea este
publicată aici.

* **Operatorul:** autorul proiectului, Niunin Matei-Gabriel. Operatorul este persoana care stabilește scopul și
  mijloacele prelucrării. El poate fi contactat pe pagina de *Issues* a depozitului:
  https://github.com/NiuninMatei/Semaforizare_Piata_Romana/issues.
* **Scopul:** cercetarea academică privind semaforizarea adaptivă a Pieței Romane.
* **Temeiul legal:** interesul legitim, conform art. 6 alin. (1) lit. f) GDPR, cu garanțiile pentru cercetarea
  științifică prevăzute de art. 89 GDPR și de art. 8 din Legea nr. 190/2018.
* **Datele:** pozițiile și traiectoriile participanților la trafic, extrase automat din fluxul public al camerei
  Piața Romană. Cadrele video nu se păstrează, în afara clipurilor temporare de verificare, șterse după folosire.
* **Destinatarii:** publicul și Anthropic. Numărătorile agregate și, pentru zilele de până la 7.11, traiectoriile vehiculelor sunt
  publicate deschis în depozitul GitHub. Anthropic, furnizorul asistentului Claude, primește spre analiză capturile, foile de contact și feliile timp-spațiu
  folosite la calibrarea zonelor și la numărătoarea de referință.
* **Stocarea:** jurnalul local complet și copiile acestor imagini din jurnalele locale ale sesiunilor asistentului se
  păstrează pe durata proiectului și a evaluării academice, apoi se șterg. Datele publicate rămân în depozit.
* **Drepturile:** persoanele vizate au drepturile prevăzute de art. 15–18 și 21 GDPR, adică dreptul de acces, dreptul
  la rectificare, dreptul la ștergerea datelor, dreptul la restricționarea prelucrării și dreptul la opoziție.
  Drepturile din art. 15–18 se aplică în limitele art. 11: operatorul nu poate identifica persoanele fără informații
  suplimentare furnizate chiar de ele. Există și dreptul de a depune plângere la Autoritatea Națională de
  Supraveghere a Prelucrării Datelor cu Caracter Personal (ANSPDCP, https://www.dataprotection.ro).

### 4.6 Calitatea înregistrării: urmărirea sacadată din 21–22.10

**Pe scurt.** Numărătorile sunt corecte doar dacă analiza prelucrează cadrele camerei într-un ritm susținut și
regulat, în mod normal de ≈6 cadre pe secundă. Când ritmul scade mult sau devine sacadat, urmărirea pierde vehiculele,
iar numărătorile scad, deși traficul nu a scăzut. Așa s-a întâmplat ziua, pe 21–22.10, când imaginea venea în rafale,
și în câteva intervale, mai ales noaptea, când calculele grele rulate pe același laptop au încetinit, cel mai probabil,
prelucrarea. Subcapitolul arată cum au fost descoperite aceste probleme, ce efect au avut asupra datelor și cum pot fi
depistate: după încheierea zilei, cu `romana.vision.calitate`, și pe loc, cu veghea fluxului de cadre. Din 1.11, un program
de pază, numit paznic, pornește colectarea la loc dacă procesul ei lipsește sau nu mai dă semne de viață. Fișa senzorului, de
la sfârșitul subcapitolului, arată cât de bine a lucrat colectarea de atunci.

Problema a ieșit la iveală pe 27.10.2026. La aceleași ore, ziua de luni 26.10 avea de 2–4 ori mai multe intrări
numărate decât miercuri 21.10. Pe Magheru, de exemplu, între 12:00 și 18:00, intrările au fost de 1 424/h față de
558/h. Camera nu se mișcase: hărțile de ocupare ale traiectoriilor din cele patru zile se suprapun fără nicio
deplasare, cu o corelație de 0,91–0,96. O hartă de ocupare arată pe unde trec vehiculele în imagine. Nici detecția nu
se schimbase: codul și parametrii ei, adică YOLO11s la 1600 px, pe OpenVINO, erau aceiași. Diferența stă în
continuitatea urmăririi, măsurată direct în jurnalele de traiectorii cu `romana.vision.calitate`. Rezultatele sunt în
`docs/rezultate/calitate_inregistrare.csv`, iar pe jurnalele publicate din `data/trajectories/` ies practic aceleași
cifre.

Fiecare traiectorie este un șir de puncte, adică pozițiile vehiculului în cadrele prelucrate. Tabelul folosește două
măsuri ale continuității. Prima este procentul golurilor: din toate intervalele dintre două puncte consecutive, cât la
sută depășesc 1 s. A doua este densitatea, adică numărul de puncte pe secundă de traiectorie. O urmărire continuă are
puține goluri și o densitate mare.

| Perioada | Goluri de peste 1 s între punctele unei traiectorii | Densitatea (puncte pe secundă de traiectorie) |
|---|---|---|
| miercuri 21.10, 11:45–21:00 | 12–17% | 1,0–1,5 |
| noaptea 21–22.10, 21:00–07:00 | 5–10% | 2,1–2,9 |
| joi 22.10, 07:00–20:00 | 11–22% | 0,8–1,4 |
| joi 22.10, de la 20:00 | 2–3% | 3,7–4,5 |
| duminică 25.10 și luni 26.10 | 1–6% | 2,4–5,2 |
| miercuri 28.10 (ziua de test, § 9.10), 00:10–24:00 | 1–6% | 2,1–4,9 |
| joi 29.10 (ziua de confirmare, § 9.10), 00:00–24:00, fără oprirea 08:33–08:46 | 1–3% | 3,2–4,9 |

Densitatea nu scade din cauza aglomerației, fiindcă un vehicul oprit la semafor este detectat în fiecare cadru. Ea
scade doar din cauza înregistrării.

Schimbarea din tabel coincide cu introducerea tamponului de redare de 8 s pentru fluxul HLS, pe 22.10 seara, pentru
demonstrația în timp real. Tamponul ține în memorie câteva secunde de imagine și le redă uniform. El a rezolvat
problema semnalată atunci (§ 12.2, P3): „imaginea camerei mergea 2 s și stătea 4 s”, pentru că fluxul vine în bucăți
de 6 s. Înainte de tampon, și analiza primea cadrele în rafale, cu opriri, iar urmărirea avea goluri în care vehiculele
„săreau” peste zonele mici de numărare. Atunci problema a fost văzută doar ca una de afișare.

**Consecințele** sunt trei:

1. Zilele lucrătoare 21–22.10 sunt subnumărate în orele de zi, cu un factor necunoscut și diferit de la un braț la
   altul. Factorii de corecție din § 4.3, măsurați pe 26.10, corespund înregistrării continue și nu se aplică acelor
   zile.
2. Prima zi lucrătoare înregistrată continuu este **luni 26.10**, chiar ziua numărătorii de referință. Vârful ei
   calibrat are ≈5 000 de vehicule/h prin piață în măsura veche (§ 5.4) și ≈5 600, la 14:30–15:30, în cea nouă
   (§ 6.5). Numărătoarea de referință de la prânz (§ 4.3) dă ≈6 200 de vehicule/h: Magheru ≈3 070, Lascăr Catargiu
   ≈1 450, Dacia vest ≈1 050 și Dacia est ≈650. Diferența față de scenariul calibrat al aceleiași ore e discutată în
   § 5.4. Aceste niveluri sunt de aproximativ două ori mai mari decât vârfurile din 21–22.10, de ≈2 500 de vehicule/h.
3. Duminica 25.10, înregistrată continuu, părea „mai aglomerată” decât zilele lucrătoare, cu 4 683 de vehicule/h la
   vârf. Era un semnal care ar fi trebuit să atragă atenția mai devreme.

De aceea, la orice colectare nouă, jurnalul zilei trece prin `romana.vision.calitate` înainte de orice scenariu.

**Prelucrarea încetinită (28.10, 03:46–04:28), nu o imagine înghețată.** În noaptea zilei de test, numărătorile au
scăzut brusc. Pe intervale de 15 minute, vehiculele urmărite au fost de 4–5 ori mai puține, 80–85% dintre ele stăteau
pe loc, iar durata mediană a urmăririi lor a urcat de la 3–5 s la 20–40 s. Semnul a fost pus întâi, greșit, pe seama
unei imagini înghețate. Verificarea directă, cerută de autor pe 29.10 și refăcută independent de doi agenți, adică de
două instanțe separate ale asistentului Claude, a arătat altceva.

Imaginea nu era înghețată. Pozițiile mașinilor parcate fluctuează ca în orice noapte, pe când un cadru repetat ar da
poziții identice de la un cadru la altul. Autobuze traversează piața la 04:08 și la 04:10, iar nicio traiectorie nu se
repetă. Nici strada nu era goală: scăderea numărătorilor începe și se termină în aceleași minute ca scăderea ratei
cadrelor prelucrate. Între 03:46 și 04:28, pasul median dintre punctele unei traiectorii a urcat de la ≈0,17 s la
≈0,7 s. Pasul este timpul dintre două puncte consecutive, iar pasul median este valoarea din mijloc a pașilor, așezați
în ordine crescătoare. Analiza a prelucrat deci ≈1,4 cadre/s în loc de 5–6, cu câte o pauză de ≈6 s în fiecare minut.
La această rată, algoritmul de urmărire ByteTrack nu mai leagă vehiculele în mișcare: ele se mută prea mult de la un
cadru la altul și se rup în fragmente care nu ating zonele de numărare. Mașinile parcate rămân urmărite. De aici vin
traiectoriile „fixe” și cele 1–7 intrări pe sfert de oră din jurnalul colectării, față de 22–52 înainte.

Cauza cea mai probabilă e încărcarea calculatorului. Validarea agentului E14, cu multe simulări în paralel, a rulat
între 03:04 și 04:48; încetinirea a început ușor pe la 03:00, iar rata normală a revenit pe la 04:45. Cauza nu e totuși
sigură. Dacă fluxul camerei ar fi sosit sacadat, efectul ar fi arătat asemănător. În plus, în noaptea de 29.10,
lanțul de calcule al testului, la fel de greu, a rulat în intervalul 00:15–02:27, cu 11 procese, și a încetinit
colectarea doar ușor: pasul median a fost de 0,19–0,22 s în loc de 0,17 s, fără niciun interval încetinit. Pe sferturi
de oră, la fel părea și validarea din 28.10, 00:25–01:11. Pe ferestre de 10 minute se vede însă că ea a încetinit
puternic colectarea în ultimele ei minute (mai jos, „Încetinirile văzute pe ferestre de 10 minute”).

Din 29.10, `romana.vision.calitate` caută direct acest semn, adică rata mică a cadrelor prelucrate, pe intervale de
15 minute; opțiunea `--out-15min` scrie tabelul pe intervale. Un pas mai lung de 0,5 s, numit aici „pas lung”,
înseamnă cadre pierdute. Un interval e încetinit când cel puțin 40% dintre pașii traiectoriilor de vehicule depășesc
0,5 s.

Episoade de același fel apar și în alte zile:

- pe 27.10, 01:15–02:45, tot în timpul calculelor de noapte, cu o revenire scurtă pe la 02:15–02:30; sfertul de oră
  02:15 rămâne sub prag;
- pe 26.10, 16:45–17:00;
- pe 25.10, mai scurt, 02:55–03:08; acesta rămâne sub prag, pentru că se împarte între două sferturi de oră.

Pe 21, 22 și 29.10 (ziua întreagă) nu apar. Regula a fost aplicată jurnalelor brute, adică celor complete, păstrate
local, din 21.10–29.10 (29.10 până la 09:15). Ies încetinite exact cele 9 intervale de mai sus, cu 44–83% pași lungi;
celelalte 375 au sub 30% pași lungi, cu mediana 6%. Pe ziua întreagă de 29.10, lanțul de calcule al confirmării nu a
găsit niciun interval încetinit: pașii lungi au avut mediana 3,5% și cel mult 8% pe sfert de oră.

Dintre ferestrele folosite în teste, adică orele din care s-au construit scenariile, doar cea liniștită din 28.10
(03:30–04:30) a căzut pe o încetinire. Debitul măsurat în ea, de 56 veh/h, e deci subestimat. Decizia testului rămânea
aceeași și fără ferestrele de noapte (§ 9.10), dar testul însuși, cu câștigul de −7% al planului 12/14/12, a fost retras
pe 2.11, fiindcă rula pe un geamăn cu coliziuni și teleportări în masă (§ 6.5, § 9.11). Celelalte ferestre ale zilei
de test nu sunt încetinite: pasul median e de 0,17–0,23 s, iar pașii lungi sunt cel mult 9%. Nici ferestrele zilei de
validare, 26.10, nu trec pragul: pasul median e de 0,17–0,31 s, cu cel mult 16% pași lungi pe oră. La prânz, rata a
fost totuși vizibil sub cea normală (mai jos, „Prânzul numărătorii de referință”).

Opțiunea `--fara-incetinite` din `romana.bridge.scenarii_zi` scoate intervalele încetinite din alegerea ferestrelor.
Pe 28.10, fereastra liniștită s-ar muta astfel pe 02:45–03:45, iar pe 26.10 nu se schimbă nimic. Opțiunea e dezactivată
implicit, pentru ca zilele deja prelucrate să rămână reproductibile, adică să dea aceleași rezultate la o nouă rulare.
Măsura nouă (§ 9.11) scoate însă mereu sferturile încetinite, după o regulă mai strictă: un sfert e încetinit și când pasul
median trece de 0,22 s. Motivul: pe 26.10, pe Magheru, se numărau 380–420 de vehicule pe sfert la un pas median de cel mult
0,22 s, 292 la un pas între 0,22 și 0,26 s și doar 146 la unul și mai lung, deci numărătoarea scădea mult înainte să apară pașii
lungi. După această regulă se scot 23 de sferturi pe 25.10 și 17 pe 26.10, printre ele cele șase dintre 12:00 și 13:30, în care
cade al doilea clip al numărătorii de referință. Pe 1–4.11 se scoate unul singur, sfertul de la 08:00 din 2.11.
Calculele grele rulează de acum la prioritate scăzută cât timp camera colectează, astfel încât sistemul să dea
întâietate colectării.

**Veghea fluxului de cadre (29.10).** Modulul `calitate` găsește o problemă abia după încheierea zilei. Autorul a cerut
însă ca orice semn de felul „imaginii înghețate” să fie văzut și analizat pe loc. De aceea, modulul
`romana.vision.veghe`, pornit cu `scripts\2d_veghe.bat`, rulează alături de `run_vision`, modulul care prelucrează
imaginea în timp real, fără să intervină în el. Veghea citește:

- în fiecare secundă, starea curentă a analizei, din `outputs/live/state.json`: rata cadrelor prelucrate, ora ultimului
  cadru și reconectările la fluxul camerei;
- la fiecare 15 s, previzualizarea cu persoanele estompate, pe care o ține doar în memorie;
- la fiecare minut, traiectoriile noi din jurnal.

La primul semn de problemă, veghea se oprește. Întâi scrie alerta, apoi un instantaneu de diagnostic, adică o
descriere a stării calculatorului în acel moment:

- procesele, ordonate după cât procesor folosesc, plus rândul lui `run_vision`, oricare i-ar fi locul în listă;
- performanța procesorului, adică cât de repede lucrează față de frecvența lui nominală;
- memoria;
- cât din placa grafică folosește fiecare proces;
- ultimele rânduri din jurnalul de erori al modulului de viziune;
- lista de redare HLS a camerei (playlistul), adică lista segmentelor video disponibile pe serverul camerei, citită de
  două ori, la 8 s distanță, ca să se vadă dacă avansează și cât de în urmă e ultimul segment.

Instantaneul ajută la deosebirea unei cauze de la noi, din prelucrare, de una din teren, din fluxul camerei. Semnele
urmărite și pragurile lor sunt:

| Semnul | Pragul la care veghea dă alerta |
|---|---|
| `run_vision` nu mai rulează | imediat |
| niciun cadru prelucrat | 3 minute; întreruperile scurte ale fluxului se refac singure și doar se notează |
| pauze de peste 2,5 s între cadre (redare sacadată) | 10 în 5 minute |
| rata cadrelor prelucrate (normal ≈6/s) | sub 3,5/s în cel puțin 75% din citirile ultimelor 3 minute |
| episoade de reconectare a fluxului | 4 în 30 de minute |
| nicio traiectorie nouă | 5 minute |
| pași lungi, de peste 0,5 s, între punctele vehiculelor | cel puțin 15% în ultimele 10 minute |
| previzualizarea nu se schimbă deloc, deși se prelucrează cadre (cadre identice) | 4 citiri la rând (1 minut) |
| vehiculele oprite au poziții identice, punct cu punct; semnul se vede abia după ce înghețarea trece | cel puțin jumătate |

Înainte de noapte, codul vegherii a fost verificat de doi agenți independenți. După observațiile lor, pragurile
fluxului au fost calibrate pe jurnalele de erori ale modulului de viziune. Pragurile au fost alese trecând jurnalele
brute din 21–29.10 prin aceleași reguli, ca și cum veghea ar fi rulat atunci; opțiunea care face asta este
`--reluare`. Pe 29.10, ziua întreagă, nu apare niciun semn fals. Singurul semn al zilei e oprirea planificată de
dimineață (08:33–08:46), văzută după 6 minute; după miezul nopții urmează doar capătul obișnuit al jurnalului. Toate
episoadele cunoscute sunt prinse: pe 28.10, încetinirea e semnalată la 03:53, la 7 minute după început. Redarea
sacadată din 21–22.10 apare aproape toată ziua, deci problema ar fi fost văzută din prima zi.

**Pentru specialiști.** Detaliile pe care se sprijină pragurile:

- *Întreruperile fluxului.* Pe 26 și 28.10, fluxul camerei s-a întrerupt de câteva ori, cu conexiuni eșuate și citiri
  care au depășit timpul de așteptare de 30 s, și s-a refăcut singur. Cele cinci întreruperi care au oră în jurnalul
  de erori au oprit imaginea 33–73 s. Pe 26.10, cele de la 10:15 și 11:21 (a doua, de 9,5 s) au coincis cu reconectări
  ale Wi-Fi-ului laptopului, consemnate în jurnalul Windows, deci au venit, foarte probabil, din rețeaua locală, nu de
  la cameră. Pe 28.10 au fost trei întreruperi în 25 de minute, între ≈22:30 și 23:00, plus trei episoade de 2–3 minute
  (00:23–00:26, 00:29–00:33 și 18:36–18:40), cu doar câteva secunde de imagine între goluri. Cel mai lung gol fără
  niciun cadru, de 144 s (28.10, 00:30), rămâne sub pragul de 3 minute. Erorile de dinainte de 22:28 nu au oră în
  jurnal, așa că aceste trei episoade sunt doar probabil reconectări; cauza lor, prelucrarea sau serverul camerei, nu
  e stabilită. Contorul de reconectări crește la fiecare încercare eșuată; de aceea, creșterile apropiate în timp
  formează un singur episod.
- *Rata cadrelor.* Rata raportată de `run_vision` este o medie mobilă, care iese prea mare când pașii scurți se
  amestecă cu pași lungi. De aceea, semnul ratei este dublat de semnul din jurnal, cel al pașilor lungi.
- *Imaginea înghețată, dar recodificată.* Dacă imaginea îngheață, dar camera o recodifică totuși, cadrele ies aproape
  identice. Pentru acest caz nu există încă un prag: diferența dintre previzualizări se notează pe minut, pentru
  calibrare. Ziua, pe 29.10, 15:58–17:10, diferența medie dintre două previzualizări luate la 15 s una de alta e de
  ≈20–25 de niveluri de gri, pe scara de la 0 la 255, cu mediana 23. Ea urmează mai ales traficul: seara, deși e
  întuneric, rămâne la ≈19–25, iar între 22:00 și 01:00 scade la ≈13–17, cu un minim de 10.
- *Reluarea.* În reluare, o traiectorie ajunge în jurnal la 30 de cadre prelucrate după ultima ei detecție, ca în
  `run_vision`; indicatorii calculați pe fiecare minut sunt în `docs/rezultate/veghe_reluare.csv`. Pe 29.10, ziua
  întreagă, pașii lungi au mediana 3,7%, percentila 99 de 8,8%, adică 99% dintre minute au cel mult atât, și maximul
  13,2%, cu lanțul de calcule al testului rulând în paralel (00:15–02:27). Pozițiile identice ajung la cel mult 2,9%.
  Pe zilele normale, pozițiile identice ajung la cel mult 3,7%, iar cel mai lung timp fără traiectorii noi e de cel
  mult 1,5 minute în afara încetinirilor și a golurilor de cadre. El a ajuns la 1,6 minute în încetinirile din 27.10,
  la 2,7 minute în cea din 28.10 și la 2,4 minute la golul de cadre de 144 s din 28.10, 00:30. Fac excepție opririle,
  repornirile și capătul fiecărui jurnal, după miezul nopții, unde mai sosesc doar traiectoriile lungi începute în
  acea zi.

Veghea a rulat din 29.10, 15:16 (versiunea verificată, de la 15:57), până pe 30.10, la 08:30. Atunci a fost oprită,
chiar înainte de încheierea colectării. Ea a notat în fișierul ei CSV pauzele de cel puțin 10 s, iar din 16:27 a pus
lângă fiecare și lista de redare citită la începutul ei. Un ultim segment rămas mult în urmă indică fluxul camerei,
iar unul la zi indică livrarea segmentelor sau partea noastră.

În după-amiaza și seara de 29.10, veghea a notat două pauze: la 16:23, de 16 s, și la 17:46, de 12 s. Ea le măsoară pe
starea curentă a analizei, scrisă cel mult o dată pe secundă, așa că le poate găsi cu până la ≈1 s mai lungi decât în
jurnal. La a doua pauză, lista de redare era la zi: la cele două citiri, ultimul segment era în urmă cu 6 și 8 s, iar
secvența avansa. Camera din teren trimitea deci normal, iar întârzierea a apărut după ea – la livrarea segmentului, pe
drumul prin rețea, la descărcare sau la prelucrare –, fără să se poată spune unde. Amândouă sunt goluri reale în
jurnal, de 16,2 și 11,4 s fără niciun punct, cu 45 și 63 de urmăriri care continuă peste gol. Niciuna nu a avut
reconectări, erori ale fluxului, deconectări de Wi-Fi sau evenimente Windows.

În noaptea de 30.10, lanțul de calcule al confirmării a rulat în intervalul 00:15–03:20, iar simulările lui în
intervalul 00:23–03:19, în 11 procese la prioritate scăzută. Cât au rulat simulările, veghea nu a notat nicio pauză de
cel puțin 10 s, nicio reconectare și niciun minut fără traiectorii noi. Rata a scăzut de la ≈5,9 la ≈4,8 cadre/s, după
mediana citirilor pe minut, cu ≈5% pași lungi și cel mult 9,4% într-un minut, deci fără încetiniri. Singura alertă,
„rată mică”, a venit în jurul orei 01:58: de la 01:56, rata stătea la 3,2–3,4 cadre/s. Alerta a coincis cu lucrul
activ al asistentului pe același calculator. Pe lângă simulări, rula atunci și o reluare a vegherii, pornită de
asistent (01:57–02:02), care încărca nucleele procesorului. La 02:05, aplicația Claude Desktop folosea ≈55–59% din
placa grafică integrată, pe care rulează și detectorul, și ≈1,2 nuclee. Rata mică a continuat cât veghea a stat
oprită după alertă: între 01:59 și 02:06, jurnalul de traiectorii arată ≈3,2–3,3 cadre/s, fără goluri de cadre și fără
minute fără traiectorii noi. Veghea a fost repornită la 02:06, cu semnul ratei dezactivat. De la 02:07, imediat după
încheierea lucrului activ, rata a revenit la 4,5–5,3 cadre/s, deși simulările continuau, iar de la 03:19, odată cu
încheierea lor, a urcat la ≈5,9. La 03:21, veghea a fost repornită cu toate semnele. La publicarea confirmării, ea a
notat la 04:34 o singură citire de 4,0 cadre/s, cât asistentul lucra în GitHub Desktop, apoi 5,4 la 04:35 și 4,4 la
04:36, în timp ce rula o reproducere formată din două simulări. Veghea notează rata o dată pe minut, ca citire de
moment, nu ca medie a minutului. Dimineața, între 06:35 și 08:30, cu agenți ai asistentului lucrând în fundal și cu
editare de fișiere, dar fără calcule grele, rata a stat la ≈6 cadre/s și n-a coborât sub 5,8. De la 03:21 până la
oprirea de la 08:30, veghea n-a mai notat nicio pauză, nicio reconectare și niciun minut fără traiectorii noi. Din 1.11,
09:07, veghea rulează din nou lângă colectare, iar de la 14:59 și lângă paznicul descris mai jos; după fiecare alertă, ea a
fost pornită din nou. Rândurile ei de minut stau la baza fișei senzorului și a verigii „Veghea” din starea senzorului, amândouă descrise la
sfârșitul subcapitolului.

**Microînghețările (verificate pe 30.10, noaptea).** De câteva ori pe zi, imaginea stă pe loc 10–30 s, iar jurnalul de
traiectorii nu primește în acest timp niciun punct nou. Jurnalele zilelor întregi arată astfel de goluri, de exemplu:
pe 26.10 la 19:40, de 18 s; pe 28.10 la 12:37, tot de 18 s; pe 29.10 la 07:06, de 26 s, și la 12:43, de 22 s. Ele
apăreau și înainte de introducerea tamponului de redare: pe 21.10 la 16:18, un gol de 11 s.

Golurile izolate de zi însumează ≈0,1–0,2% din timpul înregistrat. Împreună cu întreruperile fluxului și cu
încetinirile, totalul ajunge până la ≈0,4%. Efectul asupra numărătorilor e neglijabil, dar nu nul: după cam jumătate
dintre goluri, imaginea se reia de unde rămăsese, iar după celelalte sare înainte și se pierd câteva traversări. În
dispecerat, imaginea stă pe loc tot atât, iar dacă golul trece de ≈15 s, peste ea apare un mesaj de felul
„Imaginea s-a oprit de 18 s. De obicei revine singură.”; după 3 minute, mesajul spune doar de cât timp s-a oprit. Cu
imaginea ascunsă, același lucru îl spun rândul de stare al camerei, „camera: nicio măsurătoare nouă de …”, și veriga
„Camera” din starea senzorului.

De ce se oprește imaginea? Fluxul camerei sosește pe bucăți, numite segmente: câte un segment de ≈3,8 MB la fiecare
6 s. Fiecare segment se descarcă într-o secundă, apoi rețeaua tace ≈5 s, până la următorul. Tamponul de redare
păstrează cadrele sosite și le redă uniform, cu o întârziere fixă de 8 s. El acoperă însă doar câteva secunde de
întârziere peste cele 6 s ale unui segment. Dacă un segment întârzie mai mult, tamponul se golește și imaginea se
oprește. După o oprire de cel mult 3 s, redarea se reia imediat și recuperează întârzierea sărind peste o parte din
cadre. După o oprire mai lungă, redarea se reancorează: se mută pe cel mai nou cadru sosit și îl arată abia după ce
tamponul se umple din nou, ceea ce durează până la 8 s. Așadar, un segment care întârzie mult oprește imaginea cam cât
întârzierea lui, nu cu 8 s mai puțin. Tot de aici rezultă că, atunci când prelucrarea merge în ritm normal, o
microînghețare ține cel puțin ≈11 s: cele 3 s după care redarea se reancorează, plus cele 8 s ale reancorării.

Unele microînghețări coincid cu probleme ale rețelei laptopului. Jurnalul Windows arată că serviciul de nume (DNS),
care traduce numele serverelor în adrese de rețea, nu a răspuns la timp pe 28.10 la 12:37:18, chiar în golul de la
12:37, și pe 25.10 la 11:55, tot într-un gol. De aceea, din 29.10, 23:58, veghea notează la fiecare pauză și ce s-a
petrecut în minutele dinainte: câți octeți au sosit prin rețea și cât procesor a folosit `run_vision`. Din aceste
urme se deosebesc cazurile:

- o descărcare oprită: rețeaua tace mult peste cele 5 s obișnuite, iar tăcerea începe înaintea pauzei;
- o prelucrare oprită: rețeaua merge;
- o descărcare doar încetinită: datele sosesc într-un ritm mic, fără rafale.

Golurile de 8,0–8,5 s sunt un caz aparte. A fost unul pe 22.10, la 21:48, și au fost 41 de la 25.10 încoace; pe
29.10, niciunul. Toate cad în încetiniri, cele mai multe chiar la începutul lor, când rata scăzuse la ≈1–2 cadre pe
secundă. Iată când: pe 25.10 la 02:55–02:58 și între 07:42 și 10:46; pe 26.10 între 16:37 și 17:05 și la
21:07–21:08; în noaptea spre 27.10; pe 28.10 la 00:53–00:55 și la 03:48. Vin câte unul până la trei, de obicei la
≈30–65 s unul de altul.

Foarte probabil, ele sunt reancorări ale redării, nu reconectări ale fluxului. Mecanismul ar fi acesta: când calculele
grele încetinesc decodarea fluxului în imagini, cadrele ajung în tampon mai încet decât curge timpul real, iar cel mai
nou cadru rămâne tot mai în urmă. Când întârzierea lui trece de 3 s, redarea se reancorează pe el și îl arată abia
după 8 s. Imaginea stă deci 8 s plus un pas între două cadre, apoi continuă de unde a rămas. Se vede și în date: pe
25–27.10, toate cele 26 de vehicule care se mișcau chiar înaintea acestor goluri sunt regăsite după ele, față de ≈86%
la cadrele obișnuite din aceleași ferestre. Mai departe în încetinire, pauzele devin de ≈5–6 s, iar imaginea sare
înainte: după ele se mai regăsesc doar ≈1/3 dintre vehiculele în mișcare. Probabil că atunci FFmpeg, programul prin
care se citește fluxul, sare peste segmente.

**Pentru specialiști.** Și o reconectare rapidă ar putea lăsa un gol de ≈8 s, dar ea e puțin probabilă. În noaptea
spre 27.10 au fost 16 astfel de goluri, iar jurnalul de erori al acelei rulări nu are niciun rând după 26.10, 23:20.
Argumentul e doar de sprijin, fiindcă jurnalul prinde doar erorile FFmpeg, nu și avertismentele. În plus,
reconectările sigure, cele în care citirea fluxului a expirat, au oprit imaginea mult mai mult: 33–73 s. Pe atunci,
contorul de reconectări nu era urmărit.

În noaptea spre 29.10 au apărut și perechi de goluri de 19–45 s, la 00:26, 01:35 și 03:24. Toate au căzut în timpul
calculelor grele rulate la prioritate normală: întâi simulările testului, apoi verificarea sensibilității la o fază de
pietoni mai lungă. Nu s-a stabilit dacă vin de la prelucrare sau de la serverul camerei.

**Încetinirile văzute pe ferestre de 10 minute.** Socotită pe un sfert de oră întreg, o încetinire de câteva minute se
diluează printre minutele normale. Ferestrele de 10 minute arată și aceste încetiniri mai scurte. Măsurile sunt
aceleași ca mai sus: pasul median, adică valoarea din mijloc a timpilor dintre două puncte succesive ale unei
traiectorii, normal de 0,17 s, și ponderea pașilor lungi, cei de peste 0,5 s. Orele din lista de mai jos sunt cele la
care veghea dă semnul în reluare, adică la trecerea jurnalelor vechi prin regulile ei. Fereastra privește 10 minute în
urmă, deci încetinirile încep, de fapt, cu 1–7 minute mai devreme. Pentru fiecare zi, de la 25.10 la 29.10, lista dă
și calculele grele care rulau atunci pe același calculator, aflate după orele fișierelor scrise în acele momente:

- **25.10:** mai multe episoade între 07:47 și 11:08, cu reveniri între ele, plus două scurte, la 12:56 și 14:39.
  Rulau antrenările agenților E8–E9, validările E7–E9 și evaluările. În plus, între ≈10:35 și ≈11:33, toate
  procesele Python, inclusiv `run_vision`, au fost trecute din afară la prioritate scăzută și limitate la 8–9 din cele
  12 nuclee logice.
- **26.10:** 12:25–12:36, 13:10–13:17 și 21:11–21:18, cu 15–25% pași lungi. Rulau antrenarea agentului E11, în
  intervalul 10:21–13:37, și lucrul pentru zonele noi: cadre și clipuri luate din același flux și prelucrate în
  paralel, la prânz și cu detectorul YOLO pe aceeași placă grafică.
- **27.10:** 02:41–03:13, 03:47–03:58, 04:34–04:44 și 05:28–05:46. În noaptea de 27.10 rulau validarea și testul
  agenților E12/E13, evaluările cu capacitatea calibrată și experimentele de capacitate (§ 9.9 și § 6.4).
  Reantrenarea E12/E13, încheiată la 01:01, nu a lăsat niciun semn.
- **28.10:** 00:58–01:10, cu până la 85% pași lungi și un pas median de 0,68 s; de la 00:40, pasul median era deja
  0,24–0,29 s. Încetinirea coincide cu validările din 28.10: cade chiar în ultimele minute ale validării din acea
  noapte, care s-a încheiat la 01:11, exact când rata și-a revenit.
- **29.10:** nicio încetinire, deși testul din acea noapte a rulat tot la prioritate normală.

Așadar, calculele grele nu încetinesc colectarea de fiecare dată. Coincidențele fac totuși din ele cauza cea mai
probabilă, dar nu una sigură: în acele momente, încărcarea procesorului și a memoriei nu era înregistrată continuu.

Tot pe 29.10 a ieșit la iveală o problemă cu prioritatea calculelor. Când mai multe programe cer procesorul în același
timp, Windows îl servește întâi pe cel cu prioritatea mai mare. Scripturile lanțurilor de noapte, adică ale seriilor de
calcule pornite automat peste noapte, cereau o prioritate scăzută, pentru ca Windows să dea întâietate colectării.
Cererea nu se aplica însă: din cauza unei erori de programare, Windows o respingea.

**Pentru specialiști.** Scripturile apelau `SetPriorityClass(GetCurrentProcess(), …)` prin `ctypes`, fără tipuri
declarate. Tipul implicit al `ctypes` este int, de 32 de biți, așa că rezultatul lui `GetCurrentProcess()` era
trunchiat. Ca argument, valoarea era apoi extinsă la 64 de biți cu zerouri, nu cu semnul. Apelul primea astfel
0xFFFFFFFF în locul pseudo-handle-ului procesului curent, care pe 64 de biți este −1. `SetPriorityClass` întorcea 0,
cu eroarea 6 („handle invalid”). Comportamentul a fost verificat direct.

Prin urmare, calculele de noapte din 28.10 și testul din noaptea de 29.10 au rulat la prioritate normală. Lanțul de
confirmare din noaptea de 30.10 a primit prioritatea scăzută din afară, lucru verificat. De acum, `run_vision` își
ridică singur prioritatea peste normal, chiar la pornire. Procesul de colectare pornit pe 29.10 la 08:46 era anterior
acestei schimbări, așa că a rulat la prioritate normală până la 15:16. Atunci prioritatea i-a fost ridicată din afară,
lucru verificat și el.

**Prânzul numărătorii de referință (26.10).** La prânzul zilei de 26.10, când s-au înregistrat clipurile numărătorii
de referință, colectarea în timp real a prelucrat mai puține cadre decât de obicei. Măsurat minut cu minut, între
11:50 și 12:30, pasul median a fost de 0,20–0,40 s în loc de 0,17 s, iar pașii lungi au ajuns până la 31% într-un
minut. Încetinirea a cuprins și intervalele celor două clipuri: cât s-a înregistrat clipul 1, la 11:58, pasul median
al colectării a fost de 0,22–0,28 s, iar cât s-a înregistrat clipul 2, la 12:19, de 0,26–0,35 s. În schimb, același
lanț de prelucrare, rulat după aceea pe clipuri, a mers la rata întreagă: pas median de 0,17 s și 2,7% pași lungi.

Probabil de aici vine o parte din diferența dintre numărarea în timp real a acelei ore și numărarea automată pe
clipuri (§ 5.4). Cât anume nu s-a măsurat, fiindcă o rată redusă nu se poate simula fără imagini. Cauza probabilă e
chiar lucrul pentru numărătoarea de referință, care rula în paralel: înregistrarea clipurilor din același flux și
prelucrarea lor. Toate acestea veneau peste antrenarea agentului E11, în intervalul 10:21–13:37. Singură, antrenarea
încetinise colectarea doar puțin: pe ferestre de 10 minute, între 10:30 și 11:50, pasul median a fost de 0,19–0,21 s.

Factorii de corecție (§ 4.3) se obțin împărțind referința la numărarea automată făcută la rata întreagă. Numărarea la
rata întreagă e chiar ce face colectarea în zilele fără încetiniri, cum sunt ziua de test 28.10, în afară de noapte, și
ziua de confirmare 29.10.

**Golurile din colectare (29.10).** O oprire a colectării lasă sferturi de oră fără date. Până pe 29.10, alegerea
ferestrelor nu ținea cont de ele, iar de atunci le ocolește.

Scenariile unei zile se construiesc din ferestre de câte o oră, de exemplu ora de vârf sau ora cea mai liniștită.
Scriptul `scenarii_zi` le alege cu o fereastră glisantă de o oră, care parcurge ziua întreagă, sfert cu sfert.
Fereastra număra însă rânduri din profilul zilei, adică din tabelul cu debitele pe sferturi de oră, nu minute. Un
sfert fără date nu avea niciun rând, așa că fereastra unea sferturile de o parte și de alta a golului într-o „oră”
care nu a existat. Zilele 21.10 și 22.10 au astfel de goluri: orele false existau și acolo, dar niciuna nu a fost
aleasă. Într-o probă pe datele din 28.10, cu un gol pus lângă vârf, scriptul se oprea cu o eroare. De pe 29.10,
profilul zilei se întinde pe grila completă de 15 minute, adică pe toate sferturile de oră, cu sau fără date. Golurile
rămân goale, deci nicio fereastră nu mai trece peste ele. O verificare separată, făcută tot de agenți Claude, a arătat că ferestrele și
profilurile zilelor 21–28.10 au rămas identice.

Mai e un efect. Sfertul în care colectarea repornește are date doar de la repornire, dar `recount`, care reface
numărătorile din jurnal, îi dă durata întreagă. De exemplu, pe 21.10, sfertul 21:30 are 88 de intrări, față de 347 în
sfertul următor, pentru că colectarea repornise abia la 21:41. Opțiunea `--exclude HH:MM-HH:MM` scoate explicit din
alegerea ferestrelor sfertul opririi, golul și sfertul repornirii. Oprirea de pe 29.10, pentru repornirea
calculatorului, a fost pusă după 08:30. Aceeași oprire, aplicată de probă pe datele din 28.10, lasă fereastra de
dimineață 07:30–08:30 neschimbată, vehicul cu vehicul. Pe 29.10, lanțul de confirmare a rulat
`scenarii_zi --exclude 08:30-09:00`: sferturile 08:30 și 08:45 au ieșit din alegere, iar fereastra de dimineață
07:30–08:30 a rămas întreagă (§ 9.10).

**Citirea sigură și repornirea automată (1.11.2026).** Jurnalul zilei este scris din multe bucăți comprimate separat. O oprire
bruscă, de exemplu o pană de curent, poate lăsa o bucată neterminată sau stricată. Cititorul vechi se oprea la ea și pierdea
ce urma, uneori fără niciun semn. `romana.vision.repara` citește bucată cu bucată, sare doar peste cele stricate și le numără.
Pe fișierele întregi nu schimbă nimic: numărătorile din 29 și 30.10 ies identice, octet cu octet.

`romana.vision.paznic`, pornit cu `scripts\2e_paznic.bat`, repornește colectarea dacă procesul lipsește la două verificări la
rând sau dacă nu mai dă semne de viață de 5 minute, iar camera răspunde. Dacă problema e la cameră sau la rețea, doar așteaptă,
fiindcă `run_vision` se reconectează singur. Înainte să pornească din nou colectarea, paznicul verifică jurnalul zilei cu
`romana.vision.repara`. Dacă găsește bucăți stricate, face lângă fișier o copie reparată și păstrează originalul, fără să
șteargă nimic. Colectarea are întâietate: o verificare eșuată nu îi oprește pornirea. Paznicul nu pornește niciodată
o a doua colectare: dacă găsește mai multe colectări în același timp sau un proces despre care nu poate ști dacă e
colectarea, lasă hotărârea omului. Înaintea oricărei opriri voite se pune fișierul `outputs/live/fara_repornire`,
altfel paznicul pornește colectarea la loc. Paznicul se lansează direct, nu printr-un alt shell, iar după oprirea lui se
verifică dacă a dispărut. Fiecare repornire se notează în `outputs/logs/reporniri_<zi>.csv`, iar prelucrarea de noapte scoate
din ferestrele scenariilor sferturile de oră atinse. Din 1.11, paznicul a pornit colectarea la loc de trei ori, după cele
trei opriri voite, și de fiecare dată a găsit jurnalul zilei întreg. Paznicul însuși nu pornește singur: după o
repornire a laptopului, el, veghea și prelucrările de noapte se pornesc de mână. Așa s-a întâmplat la a treia oprire, pe
8.11: colectarea s-a oprit curat la 11:12, laptopul a repornit pentru actualizările Windows, iar paznicul, pornit de mână la
11:27, a găsit jurnalul zilei întreg și a pornit colectarea la loc la 11:28 (`outputs/logs/reporniri_2026-11-08.csv`).

**Căderile sursei (9 și 10.11.2026).** De două ori, fluxul n-a mai sosit de la serverul camerei, deși internetul laptopului
mergea. Pe 9.11, ≈19:10–19:24, serverul fluxului n-a mai primit conexiuni, cu o revenire scurtă pe la 19:19–19:20; pe 10.11,
≈00:26–01:13, serverul răspundea, dar spunea că fluxul nu există. De fiecare dată, `run_vision` a rămas pornit și s-a
reconectat singur, iar paznicul n-a repornit nimic, fiindcă lista de redare a camerei nu se putea citi. Veghea s-a oprit cu
alerta „fără cadre”, la 19:13:50 și la 00:29:27, și n-a repornit singură: a fost pornită din nou abia după 5 minute de cadre
neîntrerupte, la 19:29 și la 01:18, de un script de lucru care nu face parte din depozit. Golul care a dus la alertă nu s-a
încheiat cât a mers veghea, deci nu e notat ca pauză, iar de la alertă până la repornire veghea nu are rânduri de minut. Până
pe 10.11, fișa senzorului nu vedea deci aceste căderi și le socotea minutele cu cadre. De atunci, fișa ia din fiecare alertă
„fără cadre” ora ultimului cadru, scrisă în ea, și socotește căderea de acolo până la primul rând al vegherii de după
repornire: pe 9.11, 19:10–19:30, și pe 10.11, 00:26–01:19, în total cel mult ≈1 h 12 min. E o margine de sus, fiindcă
veghea a fost pornită din nou abia la câteva minute după revenirea fluxului. Minutele căderii se socotesc fără cadre, dar nu
ca o oprire, fiindcă în tot acest timp colectarea a rămas pornită. Invers, o alertă „fără cadre” venită dintr-o colectare
blocată sau oprită nu e o cădere a sursei: golul ei e deja o oprire, cu repornirea scrisă de paznic. Iar dacă în timpul
golului a mers o veghe pornită cu `--fara cadre`, pauza notată de ea la revenirea cadrelor dă chiar sfârșitul căderii. Pe
cele două căderi reale, aceste reguli, adăugate tot pe 10.11, după o verificare, nu schimbă nimic.

**Fișa senzorului (5–6.11.2026).** Camera, împreună cu modulul de viziune, este senzorul proiectului, în sensul Internetului
lucrurilor (§ 3). Colectarea merge pe laptop din 1.11, 09:04, zi și noapte, iar procesul ei n-a căzut niciodată neprevăzut; s-a
oprit doar de trei ori, anunțat: pe 1.11, pe 5.11 și pe 8.11. Pe 9 și pe 10.11 a lipsit o vreme doar fluxul camerei, cum scrie mai sus. Cât de bine a lucrat o arată fișa senzorului, `python -m romana.vision.fisa_senzor`, care calculează cifrele
colectării până la ora dată cu `--pana-la`, mereu cu aceleași definiții. Ea citește rândurile de minut și alertele „fără
cadre” ale vegherii, urmele paznicului, starea prelucrărilor de noapte și numărătorile din `data/counts/`; imaginile și
traiectoriile nu le atinge.
Jurnalele vegherii și ale paznicului rămân pe calculatorul autorului, deci fișa se poate calcula doar acolo. Fișa citată
aici, calculată până la sfârșitul zilei de 5.11, adică până pe 6.11, la 00:00, e publicată în
`docs/rezultate/fisa_senzor_2026-11-06_0000.json`, cu tabelul în `docs/rezultate/fisa_senzor_2026-11-06_0000.md`.
Definițiile sunt în `python -m romana.vision.fisa_senzor --help`, iar testele, în `tests/test_fisa_senzor.py`. Fișa află
pauzele și, din 10.11, căderile sursei doar din jurnalele vegherii: un minut fără rândul ei, în afara opririlor și a
căderilor, se socotește cu cadre, iar câte astfel de minute sunt arată câmpul `fara_rand_veghe` din fișierul JSON: 31 în
fișa citată aici, care nu cuprinde nicio cădere a sursei. Fiindcă e calculată fix până la
miezul nopții, tabelul ei are și un rând al zilei de 6.11, doar cu zerouri; din 10.11, fișa nu mai scrie acest rând, iar
totalurile rămân aceleași.

În cele ≈111 ore scurse între 1.11, 09:04, și 6.11, 00:00, colectarea a fost pornită 98,8% din timp, adică ≈110 ore, iar analiza a
avut cadre în 98,8% din minute, cu o mediană de 5,98 cadre analizate pe secundă. Au fost 30 de pauze de cel puțin 10 s, de
715 s în total, cea mai lungă de 51 s, și 10 episoade de reconectare la fluxul camerei (15 creșteri ale contorului), toate
refăcute singure. Cele două opriri anunțate, pe 1.11, 21:44–22:48, și pe 5.11, 20:07–20:22, au ținut 64 și, respectiv, 15 minute;
după fiecare, paznicul a pornit colectarea la loc. Toate cele 6 prelucrări de noapte s-au încheiat fără eroare: 4 ale măsurii
vechi și 2 ale măsurii noi. În același timp, modulul de viziune a numărat 284 152 de vehicule intrate în piață, fără factorii
de corecție: 265 034 de autoturisme, 8 669 de autobuze și troleibuze, 9 732 de camioane, 433 de motociclete și 284 de
biciclete. Pietonii apar doar ca totaluri pe zi, 120 076 de numărări în total. Numărătorile fiecărei zile vin din renumărarea ei de noapte.
Fișierul zilei de 1.11 din `data/counts/` mai are intervalul 08:15–08:27, din timpul prezentării bornei M1, dinaintea colectării
continue: cu el, pe 1–5.11 sunt 284 247 de intrări de vehicule și 120 095 de numărări de pietoni, cifrele din banda paginii 6 a
prezentării bornei M2.

**Starea senzorului în dispecerat (9.11.2026).** Fișa se calculează abia mai târziu, din jurnale. Ca operatorul să vadă pe loc
dacă senzorul merge, dispeceratul are panoul „Starea senzorului”, care stă în locul imaginii camerei când aceasta e ascunsă (§ 4.5, § 8).
Panoul arată cinci verigi, în ordinea drumului datelor. Fiecare are una dintre stările „în regulă”, „de urmărit”, „problemă”
sau „nu se știe”, o frază, ora ultimului semn de viață și regula ei, scrisă dedesubt. Ultimul rând arată ultima fișă a
senzorului, publicată sau nu; o fișă calculată din 10.11 spune acolo și câte căderi ale sursei camerei a avut.

| Veriga | Ce citește | De urmărit | Problemă |
|---|---|---|---|
| Camera | starea analizei, scrisă în fiecare secundă | starea e veche de 15 s, fluxul camerei lipsește sau rata e sub 3,5 cadre/s | starea e veche de 10 minute sau lipsește |
| Numărătorile | ultimul sfert de oră încheiat din `data/counts/` | niciun sfert nou de 17 minute | niciun sfert nou de o oră |
| Veghea | rândurile ei de minut și alertele din ultimele 24 de ore | tăcută de 3 minute, sub 3,5 cadre/s, cel puțin 10 pauze de peste 2,5 s în 5 minute, cel puțin 4 episoade de reconectare în 30 de minute sau oprită de o alertă | tăcută de 10 minute sau, după o alertă, de 3 minute |
| Paznicul | ultima lui notă; „în regulă” vine în fiecare oră | nicio notă de 1 h 2 min sau altă notă decât „în regulă” și „repornirea ține”, până la următoarea dintre ele | nicio notă de 2 ore |
| Prelucrarea de noapte | cele două lanțuri ale ultimei nopți, de la 00:15 și de la 03:30 | un lanț încă nepornit, cu starea necitibilă, cu o atenționare sau în curs de peste 2 ore | un lanț eșuat sau care lipsește |

„Nu se știe” înseamnă că datele verigii lipsesc sau nu se pot citi. Excepțiile sunt în tabel: o stare a camerei sau un lanț de
noapte care lipsește e o problemă, iar un lanț cu starea necitibilă e de urmărit. Dacă o citire eșuează sau se pierde legătura cu
serverul, panoul se marchează pe loc „date vechi”, la fel ca după 25 s fără nicio citire reușită. Un cititor de ecran, programul
care citește pagina cu voce tare pentru persoanele cu deficiențe de vedere, anunță doar trecerea unei verigi la „problemă”.

**Pentru specialiști.** Panoul citește `GET /api/senzor` (`src/romana/dashboard/senzor.py`). Serverul doar citește fișierele,
scoate căile locale din texte și răspunde mereu cu codul 200; starea o calculează cel mult o dată la 5 s, oricâte pagini ar
cere-o. Pagina o cere la fiecare 10 s, doar cât panoul se vede; fiindcă serverul păstrează o stare calculată cel mult 5 s,
jumătate din acest interval, fiecare cerere a paginii primește o stare calculată din nou. Pragurile vegherii, ale paznicului și
ale lanțurilor de noapte, ca și verificarea încheierii lanțului vechi, sunt copii ale celor din `veghe`, `paznic`, `lant_zilnic`
și `lant_cor`, ca serverul să nu încarce bibliotecile lor grele; `tests/test_senzor.py` verifică să rămână la fel.

## 5. Puntea cameră → simulare: cererea de trafic calibrată

Camera numără vehiculele care intră în piață și ies din ea, dar simularea are nevoie de vehicule concrete, fiecare cu
traseul lui prin rețea. Puntea descrisă în acest capitol transformă numărătorile în **cererea de trafic** a simulării:
câte vehicule vor să treacă prin piață, de unde vin și încotro merg. Cererea este calibrată, adică volumele ei vin din
datele camerei. Astfel, agentul de inteligență artificială care învață să comande semafoarele se antrenează pe
**trafic real**, nu pe trafic aleatoriu.

### 5.1 Estimarea matricei O–D (Furness)

Primul pas estimează câte vehicule merg de la fiecare intrare a pieței la fiecare ieșire. Aceste numere formează un
tabel numit matricea origine–destinație, prescurtat O–D. Intrările și ieșirile se află pe brațele pieței, adică pe
străzile care se întâlnesc în ea. Fiecare linie a tabelului corespunde unui braț pe care vehiculele intră în piață,
numit origine, iar fiecare coloană unui braț pe care ies, numit destinație. Căsuța de la întâlnirea lor arată câte
vehicule pe oră (veh/h) fac acel drum. Numărul de vehicule care trec într-o oră se numește debit.

Camera nu urmărește însă fiecare vehicul de la intrare până la ieșire: stâlpii ascund uneori vehiculele, autobuzele le
acoperă pe cele din spatele lor, iar unele brațe sunt departe de cameră. De aceea se combină trei surse de informație
(`bridge/od_estimation.py`):

* **totalurile pe linii** $T_o$, adică numărul de vehicule intrate pe brațul $o$. Aceasta este cea mai fiabilă
  măsurătoare.
* **totalurile pe coloane** $U_d$, adică numărul de vehicule ieșite pe brațul $d$. Ele se folosesc doar în modurile
  vechi: `medie` aduce suma ieșirilor și pe cea a intrărilor la media lor, iar `intrari` ajustează proporțional
  ieșirile, astfel încât suma lor să fie $\sum T$, totalul intrărilor. În modul implicit, `doar_intrari`, ieșirile nu
  se folosesc.
* **matricea de pornire** $S_{od}$, numită și „sămânța” metodei: virajele complete observate, adică vehiculele
  urmărite de la intrare până la ieșire, plus $w \cdot p_{od}$. Aici $p$ este o distribuție a priori a destinațiilor,
  stabilită dinainte în `config/demand.json`. Ea servește doar la regularizare: acoperă golurile când observațiile
  lipsesc. Ponderea ei este $w = 2$ vehicule-echivalent, adică valorează cât două vehicule observate.

Matricea se echilibrează apoi prin metoda Furness, numită și IPF (*iterative proportional fitting*, ajustare
proporțională iterativă)[^ortuzar]. Plecând de la matricea de pornire, metoda înmulțește pe rând coloanele și liniile
cu câte un factor, astfel încât sumele lor să se potrivească cu totalurile măsurate. Ultimul pas se face pe linii,
deci totalurile lor sunt respectate exact. Cu `echilibrare: "doar_intrari"` se ajustează doar liniile. Factorii de
corecție a detecției pe brațe, `factor_corectie_detectie`, sunt rapoartele dintre numărul real de vehicule și cel
numărat de cameră. Ei vin din numărătoarea de referință adnotată (§ 4.3).

**Echilibrarea intrărilor și a ieșirilor.** În primele date de zi, din 21.10, numărate cu zonele inițiale, suma
ieșirilor a depășit-o pe cea a intrărilor cu ≈30%. De exemplu, în intervalul 12:00–12:15, numărătorile au dat
1.856 veh/h la intrări față de 2.436 veh/h la ieșiri. Cu zonele actuale, diferența este de ≈40% pe 21–26.10 și de ≈20% pe
zilele întregi din 28.10 încoace (§ 4.3). O asemenea
diferență nu poate fi reală pe un interval de 15 minute, pentru că pe inelul pieței, drumul circular din mijlocul ei,
încap doar câteva zeci de vehicule. Diferența vine de la cameră, care **subnumără intrările** de la marginea
imaginii, adică prinde mai puține decât sunt: pe Magheru și pe Dacia est, vehiculele apar deja parțial în zona de
numărare, în spatele chioșcului și al stației de autobuz. Totodată, camera **supranumără ieșirile** spre străzile
parțial ascunse: un vehicul pierdut lângă o stradă pare că a ieșit pe ea.

Pentru comparație s-a folosit și numărarea pe linii de control, numite în engleză *screen lines*: linii imaginare
trasate peste drum, la care se numără vehiculele care le traversează. Această numărare a dat erori de sens opus,
≈745 de intrări și ≈1.330 de ieșiri pe oră, deci adevărul părea să fie între cele două metode. Cum nu exista o
numărătoare manuală de referință, cele două sume au fost tratate ca măsurători ale aceluiași debit și aduse la
**media** lor înainte de echilibrarea Furness. Acesta este modul `echilibrare: "medie"`, în care fiecare parte își
păstrează distribuția pe brațe.

**Două calibrări ale cererii (25.10.2026).** Auditul numărării (§ 4.3) a arătat că ieșirile de pe brațele îndepărtate
sunt supranumărate, pentru că detectorul pierde acolo vehicule. Autorul a observat, în plus, că semaforul controlează
doar intrările. De aceea s-a adăugat modul `echilibrare: "doar_intrari"`, care este acum cel implicit în
`config/demand.json`. În acest mod, volumele vin numai din intrări, iar proporțiile de viraj, adică ce parte din
vehiculele unui braț merge în fiecare direcție, vin din traiectoriile complete și din distribuția a priori. Ieșirile
brute nu se mai folosesc. Intrările pot fi însă și ele subnumărate: vehiculele pot fi ascunse de chioșc, de autobuze
sau, în aglomerație, unele de altele. Cele două calibrări, `doar_intrari` și `medie`, păreau astfel să încadreze
cererea reală între o margine de jos și una de sus, ca în tabelul de mai jos. Ulterior s-a văzut că cererea reală
este de circa două ori marginea de sus (§ 4.6, § 9.1).

| Calibrarea | Ce folosește | Vârful zilelor lucrătoare | Scenariile de evaluare, în istoricul git |
|---|---|---|---|
| **marginea de jos** – `doar_intrari` | doar intrările | ≈1 640–1 980 veh/h | cele din 25–26.10 |
| **marginea de sus** – `medie` | media intrărilor și a ieșirilor | ≈2 400–3 000 veh/h | cele din 23–25.10 |

Rezultatele se raportează pentru ambele calibrări (§ 9.2). Incertitudinea din interiorul fiecăreia era considerată
acoperită de scenariile de sensibilitate ×0,8 și ×1,2 (§ 5.4), în care cererea este scăzută, respectiv crescută
proporțional.

**Cererea calibrată pe numărătoarea de referință (26.10.2026).** Numărătoarea de referință (§ 4.3) a măsurat, pe
fiecare braț, ce parte din intrările reale prinde camera. Cu zonele de numărare refăcute, intrările numărate se
înmulțesc cu factorii de corecție măsurați: Magheru 1,09; Dacia est 0,88; Dacia vest 1,12; Lascăr Catargiu 2,52.
Ieșirile servesc doar la proporțiile de viraj, pentru că se folosește modul `echilibrare: "doar_intrari"`. Cu această
calibrare, vârful zilelor 21–22.10 ajunge la ≈2 520–2 560 veh/h prin piață: aproape de fosta margine de sus, de
≈2 400–2 510 veh/h, și mult peste marginea de jos, de ≈1 640 veh/h. Cererea reală era deci mai aproape de marginea de
sus, probabil chiar peste ea, pentru că zilele 21–22.10 sunt subnumărate (§ 4.6). Scenariile `zi_*` din
`sumo/scenarios`, ale măsurii vechi, folosesc această calibrare (§ 5.4); scenariile măsurii noi, `cor_zi_*`, folosesc cererea
descrisă mai jos.

**Cererea măsurii noi (2.11.2026, înghețată pe 3.11).** Măsura nouă, `cor_`, are fișierul ei, `config/demand_v2.json`, scris de
`python -m romana.bridge.cerere_v2` din `config/demand.json`, care a rămas neatins, și din factorii din `config/factori_v2.json`. Valorile
s-au înghețat pe 3.11, la commitul `cffd50e`, înainte de a privi datele din 3.11 (§ 9.11). Cererea nouă se deosebește de cea veche în mai
multe puncte, descrise mai jos. Intrările vin din zonele noi (§ 4.3), iar pietonii sunt numărați pe persoane.

Factorii de corecție pot fi diferiți ziua și pe întuneric; valorile lor sunt în § 4.3. Eticheta unui sfert de oră se ia după înălțimea Soarelui la începutul lui,
cu pragul de 3,5° sub orizont. Detecția nu se schimbă la apus, ci cu Soarele la ≈4° sub orizont, cu o abatere de ≈1° între zile; am
măsurat asta pe 6 seri și 4 dimineți, pe indici care nu depind de volum. În această bandă de lumină nu există clipuri de referință.
Gradele sunt ale formulei aproximative din cod, care în octombrie–noiembrie pune Soarele cu ≈0,24° mai sus decât o efemeridă exactă:
pragul de 3,5° e, de fapt, ≈3,75° sub orizont.

Două proporții de viraj sunt fixate, fiindcă traiectoriile rupte le arată greșit, iar `cote_fixe` le declară. Amândouă s-au numărat
direct, pe felii, de doi adnotatori, pe clipurile din 1.11 și 2.11:

- din Lascăr Catargiu, spre Dacia vest merg ≈3–5%: pe banda ieșirii trec, în etapa Magheru–Catargiu, 23,5 vehicule la 478,5 intrări
  fără inel, adică 4,9%, dar 10 dintre ele vin dintr-un singur clip; fără el rămân 3,2%, cât dă și o numărare automată separată. În
  cerere, 0,04;
- din Dacia est, spre Catargiu ies ≈40%: pe 8 etape ale Bulevardului Dacia văzute cap-coadă, ieșirile spre Catargiu sunt 0,41 din
  intrări, cu o incertitudine mare între etape (0,32–0,52) și 0,34–0,48 după cum se aleg ferestrele. Duminica și lunea nu se deosebesc,
  deci în cerere rămâne 0,40, în toate zilele.

Restul rândului Dacia est e ales, nu numărat: Dacia vest 0,305 și Căderea Bastiliei 0,07 vin din distribuția a priori, iar Mendeleev
urcă la 0,085, fiindcă la vârful din 25.10 sunt mai multe traiectorii complete spre el; diferența se ia din Magheru și din întoarcere.
Pe banda ieșirii spre Dacia vest, Dacia est pare să ducă mai mult, ≈0,33–0,42, dar acolo iese și o parte din vehiculele rămase pe inel,
deci rezultatele se dau și cu 0,39. Două lucruri nu intră în cerere și rămân limite declarate: vehiculele de pe Magheru care ocolesc pe
inel, ≈5–6% din Magheru în zilele lucrătoare și ≈8–10% duminica, față de 1,1–3,0% în cerere, și drumul de sus spre Magheru, care în
geamăn nu are rută. Varianta cu ocolirea pe inel, de 6%, se raportează separat.

O verificare grosieră: ieșirea spre Magheru, numărată de cameră fără factori, e ziua la 0,97–1,08 din virajul Lascăr Catargiu →
Magheru din cerere (1,19 în zorii din 25.10), iar pe întuneric la 0,77–0,88, unde detectorul vede mai prost zona de ieșire. Raportul nu poate fi mai precis,
fiindcă pe aceeași ieșire ajung și vehicule din alte direcții.

Două viraje de pe Magheru se iau din numărul traiectoriilor complete, înmulțit cu un factor, nu din proporții. Spre Dacia est,
factorul e 1,25, numărat vehicul cu vehicul (§ 6.5, cauza 5). Spre Căderea Bastiliei, factorul e 1,94, o ipoteză declarată, pentru că
acea ieșire e pe un braț îndepărtat. În fine, rutele și pietonii sunt cei din § 6.5.

### 5.2 De la O–D la vehicule în SUMO

Matricea O–D spune doar câte vehicule merg de la fiecare intrare la fiecare ieșire. SUMO, simulatorul de trafic al
proiectului, are însă nevoie de vehicule concrete, fiecare cu traseul lui complet prin rețea. Trecerea se face în
patru pași:

1. Se generează un set mare de **rute candidate realiste**: cele mai scurte drumuri care pornesc de la marginea
   rețelei, calculate cu `randomTrips.py` și `duarouter`. Se păstrează doar rutele care pornesc și se termină pe
   artere, adică pe bulevarde și străzi principale, și care au cel mult 15% din lungime pe străzi rezidențiale. Se
   adaugă rute garantate pentru fiecare pereche intrare → ieșire, ca niciun viraj să nu rămână fără rută. Așa se fac rutele
   măsurii vechi. Pe 2.11 s-a văzut însă că alegerea lor e prea liberă: pe 26.10, ≈72% din traficul de pe Magheru pornea de pe
   Calea Victoriei, prin 4 semafoare. În geamănul corectat, rutele pornesc de pe bulevardul brațului de intrare și se termină pe
   cel de ieșire, câte una pe pereche (§ 6.5).
2. Pentru fiecare tip de vehicul și fiecare interval de 15 minute, numărul de vehicule de pe fiecare viraj se scrie
   într-un fișier de viraje, ca relație `edgeRelation` de la muchia de intrare a brațului de origine la muchia de
   ieșire a brațului de destinație. În rețeaua SUMO, o muchie este un tronson de drum.
3. `routeSampler.py`[^sumo-turns] alege din setul de rute candidate exact atâtea rute câte trebuie pentru a reproduce
   virajele, prin optimizare liniară, o metodă matematică care găsește cea mai bună combinație. Calitatea potrivirii
   se raportează prin indicatorul GEH, o măsură obișnuită în ingineria traficului pentru diferența dintre volumul
   cerut și cel reprodus. Nepotrivirile rămase se scriu în fișierele `mismatch_*.xml`.
4. Se adaugă separat traficul de pe străzile vecine care **nu** trece prin piață. Camera nu îl vede, așa că acest
   trafic de fond intră ca o fracțiune declarată din volumul observat, `fond_fractiune`, implicit 15%, pe rute care
   evită piața.

Astfel, intersecțiile vecine din rețeaua simulată primesc traficul care intră cu adevărat în Piața Romană și iese din
ea pe brațele lor. Așa se respectă cerința ca agentul să nu fie antrenat pe un trafic care nu corespunde realității.

### 5.3 Scenariul de referință (până la datele de zi)

Pentru Piața Romană nu există date oficiale publice despre volumul traficului. Singura cifră publică găsită este o
estimare neoficială din 2011/2012: ~3.446 veh/h pe Magheru spre Romană, obținută dintr-un singur ciclu de semafor,
adică dintr-o singură succesiune completă a culorilor[^wizard]. De aceea, până la colectarea datelor de zi s-au
folosit trei scenarii ipotetice, declarate explicit:

* *moderat*: 0,7× volumele de vârf, adică 1.442 veh/h prin piață;
* *vârf*: 720 veh/h pe Magheru, 620 pe Catargiu, 390 pe Dacia est și 330 pe Dacia vest, în total 2.060 veh/h;
* *aglomerat*: 1,2× volumele de vârf, adică 2.472 veh/h.

Fiecare scenariu are un trafic de fond de 15% și 1.200 de pietoni/h prin zona pieței. Și numărul pietonilor este o
valoare ipotetică, care ține seama de stația de metrou M2 și de Academia de Studii Economice (ASE). Traficul este
format din 88% autoturisme, 4% autobuze și troleibuze, 3% camioane, 3% motociclete și 2% biciclete.

Volumul de vârf a fost ales astfel încât planul fix de referință, adică programul cu durate fixe presupus pentru
semaforul real, să funcționeze aproape de saturație: cererea se apropia de numărul maxim de vehicule pe care
intersecția îl putea servi. Alegerea s-a făcut pe replica fidelă a rețelei, cu valorile implicite din SUMO pentru
comportamentul șoferilor (§ 6.4). Peste ≈1,0× volumul de vârf, inelul se suprasatura: primea mai multe vehicule decât
putea servi, iar cozile creșteau. Acest lucru părea să corespundă congestiei cunoscute a pieței. Scenariile au servit
la dezvoltarea și verificarea lanțului de prelucrare, apoi au fost completate cu scenariile construite din
numărătorile reale (§ 5.4). Planul fix de referință era însă doar o presupunere, iar camera a infirmat-o apoi: ziua, ciclul real
are ≈125–155 s, nu ≈91 s (§ 6.3, § 6.5).

### 5.4 Scenariile din date reale (Borna 9)

Un scenariu reproduce în simulatorul SUMO o oră de trafic înregistrată de cameră: câte vehicule de fiecare tip intră
pe fiecare braț, încotro virează și câți pietoni traversează. Pe aceste scenarii se antrenează agenții AI și se
compară strategiile de semaforizare. Secțiunea arată ce zile au fost înregistrate, cum se aleg orele din care se fac
scenariile, ce scenarii s-au construit, cât de fidele sunt și unde sunt folosite.

**Zilele înregistrate.** Datele au fost colectate în aceste intervale:

- **de miercuri 21.10.2026, ora 11:45, până joi 22.10.2026, ora 11:00**: ziua, seara, noaptea și vârful de
  dimineață. Imaginile au fost prelucrate în ritm de ≈5–6 cadre/s, dar urmărirea vehiculelor a fost sacadată, mai
  ales ziua (§ 4.6);
- **duminică 25.10.2026, de la 01:14 până la ≈17:00**: noaptea, dimineața, prânzul și după-amiaza;
- **de luni 26.10.2026, ora 09:11, până marți 27.10.2026, ora 06:04**. Din ziua de marți există doar noaptea: datele
  ei sunt publicate, dar nu au scenarii;
- **miercuri 28.10.2026, de la 00:10 la 24:00**: ziua de test (§ 9.10);
- **joi 29.10.2026, de la 00:00 la 24:00**: ziua de confirmare (§ 9.10). Colectarea s-a oprit 13 minute, 08:33–08:46,
  pentru repornirea calculatorului. De aceea, sferturile de oră care încep la 08:30 și la 08:45 nu intră în alegerea
  orelor pentru scenarii (§ 4.6);
- **vineri 30.10.2026, de la 00:00 la 08:30**: noaptea și dimineața. Atunci colectarea s-a oprit, iar pe 1.11 s-a reluat. Datele
  sunt publicate, dar nu au scenarii;
- **din duminică 1.11.2026, de la 09:04**: colectarea merge pe laptop zi și noapte, iar procesul ei n-a căzut niciodată
  neprevăzut; s-a oprit doar de trei ori, anunțat, pe 1.11, pe 5.11 și pe 8.11. Pe 9 și pe 10.11 a lipsit o vreme doar fluxul
  camerei. Veghea și paznicul o urmăresc, opririle și repornirile se notează, iar
  sferturile de oră atinse ies din scenarii (§ 4.6). Zilele 1, 2 și 3.11 sunt de antrenare, 4.11 e ziua de validare, 5 și 6.11 sunt
  zilele de test, iar 7.11, ziua de generalizare; ultimele trei s-au prelucrat fără simulările strategiilor, fiindcă niciun candidat
  n-a trecut de validare (§ 9.11). Datele zilelor 1–7.11 sunt publicate, cu jurnalul vehiculelor, iar orele scenariilor măsurii noi,
  `cor_zi_*`, făcute pentru 1–7.11, sunt în câmpul `ferestre` din `sumo/demand/cor_zi_<zi>_rezumat.json`; în text, cele din
  1 și 2.11 sunt în tabelul din § 6.5, iar cele din 7.11, în § 9.11. De la 8.11 se publică doar numărătorile, fără jurnalul de traiectorii.

Vehiculele din toate zilele sunt numărate cu zonele din 26.10, desenate pe imaginea camerei; zilele măsurii noi, `cor_`, se
numără și cu zonele ei, din `config/camera_v2.json` (§ 4.3). La
pietoni, zilele 21–27.10 sunt numărate cu zonele de trecere de dinainte de corectura din 28.10 (§ 4.4). Pe 26.10,
pietonii numărați astfel sunt cu ≈4% mai puțini decât cu zonele corectate. Pentru 21–22.10, numărarea a dat
≈200 000 de traiectorii, ≈31 000 de intrări în piață și ≈8 000 de viraje urmărite complet, adică vehicule văzute de
la brațul de intrare până la cel de ieșire. Numărul traiectoriilor este cel de după reunirea fragmentelor: urmărirea
se întrerupe uneori și rupe traseul unui vehicul în bucăți, iar înainte de numărare bucățile care se potrivesc sunt
legate la loc.

**Profilul zilelor.** Profilul unei zile arată cum crește și scade traficul de la o oră la alta. Măsura folosită este
debitul echilibrat, în vehicule pe oră (veh/h): media dintre suma intrărilor și suma ieșirilor numărate de cameră,
fără factorii de corecție. Profilurile au forma așteptată:

- în 21–22.10, vârful de seară este la 17:15–18:15, iar dimineața apare un platou, adică un trafic ridicat și aproape
  constant, între 08:00 și 10:45;
- luni 26.10, vârful este la 15:00–16:00;
- joi 29.10, un platou de ≈4 000–5 200 veh/h ține între 07:00 și 17:15, cu vârful la 13:00–14:00;
- duminică, traficul crește abia de la 08:30, iar vârful vine după-amiaza, la 15:30–16:30;
- noaptea trec câteva sute de vehicule pe oră.

**Alegerea orelor.** Pentru o zi scrisă în forma AAAA-LL-ZZ (anul, luna, ziua), comanda
`python -m romana.bridge.scenarii_zi --zi AAAA-LL-ZZ` alege automat, după debitul echilibrat, ferestrele zilei, adică
orele din care se construiesc scenariile:

- ora de vârf;
- ora cea mai liniștită;
- dimineața 07:30–08:30, prânzul 12:00–13:00 și seara 17:30–18:30, dar numai dacă nu se suprapun cu vârful.

Comanda construiește câte un scenariu pentru fiecare fereastră, plus două variante de sensibilitate, adică aceleași
ore cu alt volum de trafic: vârful ×1,2, cu 20% mai multe vehicule, și ora liniștită ×0,8, cu 20% mai puține.

**Scenariile măsurii vechi.** Din 2.11, măsura veche se mai calculează noaptea doar pentru istoric și nu mai decide nimic;
scenariile măsurii noi, `cor_zi_*`, pentru 25 și 26.10 și 1–7.11, se fac cu `scenarii_zi --masura cor`, iar orele lor sunt în
câmpul `ferestre` din `sumo/demand/cor_zi_<zi>_rezumat.json` (pentru 25 și 26.10 și 1–2.11, și în tabelul din § 6.5). Scenariile din tabel, `zi_*`, folosesc zonele și regulile de numărare din 26.10.2026 (§ 4.3, § 4.4),
datele renumărate cu ele și cererea calibrată (§ 5.1), adică intrările numărate, înmulțite cu factorii de corecție.
Volumul calibrat obținut astfel este altă măsură decât debitul echilibrat după care se aleg ferestrele: la vârful de
luni, debitul echilibrat este de 4 653 veh/h, iar volumul calibrat, de 5 009 veh/h. La pietoni, ziua de 28.10 și cele
de după ea sunt numărate cu zonele de trecere corectate chiar pe 28.10. Coloanele tabelului:

- *Vehicule prin piață*: volumul calibrat, în vehicule pe oră;
- *Fond*: traficul de fond, adică vehiculele de pe străzile vecine care nu trec prin piață;
- *Pietoni/h*: pietonii pe oră din scenariu;
- *Marginea de jos* și *Marginea de sus*: pentru comparație, aceleași ferestre în cele două calibrări anterioare ale
  cererii (§ 5.1). Scenariile lor se găsesc în istoricul git, adică în versiunile salvate ale proiectului (§ 11.8):
  marginea de jos la commitul `e1d0f77`, marginea de sus la commitul `7a79502`.

| Scenariu | Fereastra | Vehicule prin piață (veh/h) | Fond (veh/h) | Pietoni/h | Marginea de jos (veh/h) | Marginea de sus (veh/h) |
|---|---|---|---|---|---|---|
| `zi_2026-10-21_pranz` (miercuri) | 12:00–13:00 | 1 948 | 292 | 3 059 | 1 194 | ≈1 780 |
| `zi_2026-10-21_varf` | 17:15–18:15 | 2 515 | 377 | 3 107 | 1 636 | ≈2 510 |
| `zi_2026-10-21_varf_x1_2` | vârf × 1,2 | 3 017 | 453 | 3 107 | 1 963 | ≈3 020 |
| `zi_2026-10-21_linistit` | 23:00–00:00 | 766 | 115 | 376 | 649 | ≈860 |
| `zi_2026-10-21_linistit_x0_8` | liniștit × 0,8 | 613 | 92 | 376 | 519 | ≈690 |
| `zi_2026-10-22_dimineata` (joi) | 07:30–08:30 | 2 209 | 331 | 2 826 | 1 534 | ≈2 220 |
| `zi_2026-10-22_varf` | 09:45–10:45 | 2 556 | 383 | 2 829 | 1 646 | ≈2 400 |
| `zi_2026-10-22_varf_x1_2` | vârf × 1,2 | 3 067 | 460 | 2 829 | 1 975 | ≈2 880 |
| `zi_2026-10-22_linistit` | 02:30–03:30 | 165 | 25 | 32 | 162 | ≈300 |
| `zi_2026-10-22_linistit_x0_8` | liniștit × 0,8 | 132 | 20 | 32 | 130 | ≈240 |
| `zi_2026-10-25_dimineata` (duminică) | 07:30–08:30 | 854 | 128 | 574 | 704 | – |
| `zi_2026-10-25_pranz` | 12:00–13:00 | 3 911 | 587 | 2 536 | – | – |
| `zi_2026-10-25_varf` | 15:30–16:30 | 4 683 | 702 | 2 775 | – | – |
| `zi_2026-10-25_varf_x1_2` | vârf × 1,2 | 5 620 | 843 | 2 775 | – | – |
| `zi_2026-10-25_linistit` | 05:15–06:15 | 387 | 58 | 232 | 349 | – |
| `zi_2026-10-25_linistit_x0_8` | liniștit × 0,8 | 309 | 46 | 232 | 279 | – |
| `zi_2026-10-26_pranz` (luni) | 12:00–13:00 | 3 381 | 507 | 3 902 | – | – |
| `zi_2026-10-26_varf` | 15:00–16:00 | 5 009 | 751 | 5 707 | – | – |
| `zi_2026-10-26_varf_x1_2` | vârf × 1,2 | 6 010 | 902 | 5 707 | – | – |
| `zi_2026-10-26_seara` | 17:30–18:30 | 3 357 | 504 | 4 670 | – | – |
| `zi_2026-10-26_linistit` | 21:30–22:30 | 1 004 | 151 | 870 | – | – |
| `zi_2026-10-26_linistit_x0_8` | liniștit × 0,8 | 803 | 120 | 870 | – | – |
| `zi_2026-10-28_dimineata` (miercuri) | 07:30–08:30 | 4 064 | 610 | 3 430 | – | – |
| `zi_2026-10-28_varf` | 12:15–13:15 | 5 286 | 793 | 5 043 | – | – |
| `zi_2026-10-28_varf_x1_2` | vârf × 1,2 | 6 343 | 952 | 5 043 | – | – |
| `zi_2026-10-28_seara` | 17:30–18:30 | 3 042 | 456 | 4 862 | – | – |
| `zi_2026-10-28_linistit` | 03:30–04:30; prelucrare încetinită, valori subestimate (§ 4.6) | 38 | 6 | 2 | – | – |
| `zi_2026-10-28_linistit_x0_8` | liniștit × 0,8 | 30 | 5 | 2 | – | – |
| `zi_2026-10-29_dimineata` (joi) | 07:30–08:30 | 4 603 | 690 | 3 605 | – | – |
| `zi_2026-10-29_pranz` | 12:00–13:00 | 5 175 | 776 | 5 182 | – | – |
| `zi_2026-10-29_varf` | 13:00–14:00 | 5 282 | 792 | 4 843 | – | – |
| `zi_2026-10-29_varf_x1_2` | vârf × 1,2 | 6 339 | 951 | 4 843 | – | – |
| `zi_2026-10-29_seara` | 17:30–18:30 | 3 388 | 508 | 4 455 | – | – |
| `zi_2026-10-29_linistit` | 03:15–04:15 | 342 | 51 | 25 | – | – |
| `zi_2026-10-29_linistit_x0_8` | liniștit × 0,8 | 273 | 41 | 25 | – | – |

Pentru duminică, datele complete, până la 17:00, au mutat vârful la 15:30–16:30, iar fereastra de prânz a devenit un
scenariu separat. De aceea, în tabel, prânzul și vârful de duminică nu au valori din calibrările anterioare.

**Cât de fidele sunt scenariile.** Un scenariu trebuie să reproducă virajele măsurate, adică numărul de vehicule pe
fiecare relație de viraj, de la un braț de intrare la un braț de ieșire. Potrivirea se măsoară cu indicatorul GEH,
care compară debitul simulat cu cel măsurat. O valoare sub 5 este considerată, de obicei, o potrivire bună.
`routeSampler` este instrumentul din SUMO care alege rutele vehiculelor astfel încât să reproducă virajele. El lucrează
separat pe fiecare tip de vehicul. La autoturisme, atinge GEH < 5 la 89–100% dintre relații, după scenariu, în medie
la ≈94%. La celelalte tipuri, atinge GEH < 5 la 100% dintre relații, cu o singură excepție: camioanele la vârful ×1,2
din 22.10, cu ≈94%.

**Două observații despre cifre.** Luni 26.10 este prima zi lucrătoare înregistrată cu urmărire continuă (§ 4.6).
Colectarea a început la 09:11, deci ziua nu are vârful de dimineață. Zilele 21–22.10 sunt subnumărate, iar vârfurile
lor, de ≈2 500 de vehicule/h, sunt aproximativ jumătate din cel de luni, de ≈5 000.

A doua observație privește prânzul zilei de luni. Numărătoarea de referință, făcută cadru cu cadru pe clipuri ale
camerei (§ 4.3), dă ≈6 200 de vehicule/h, dar scenariul calibrat al aceleiași ore, `zi_2026-10-26_pranz`, are doar
3 381. Scenariul pornește de la numărarea în timp real a acelei ore, care a dat mult mai puțin decât numărarea
automată făcută de program pe aceleași clipuri: pe Magheru, ≈900–1 160 veh/h în valori brute, adică fără factorii
de corecție, față de ≈2 800 veh/h. Diferența nu e lămurită complet. În acea oră, colectarea în timp real a prelucrat
mai puține cadre decât lanțul de prelucrare rulat pe clipuri, ceea ce explică probabil o parte din ea (§ 4.6,
„Prânzul numărătorii de referință”).

**Unde se folosesc scenariile.** Rezultatele din capitolul 9 se sprijină pe aceste scenarii și pe calibrările
anterioare astfel:

- rezultatele din § 9.1–9.4 și din § 9.5, fără E12–E14, au fost obținute pe calibrările anterioare, adică pe
  marginile de jos și de sus;
- reevaluarea pe cererea calibrată este în § 9.8; tot pe cererea calibrată sunt rezultatele agenților E12 și E13 și
  analiza locului unde se pierde timpul la vârfurile din 21–22.10 (§ 9.6);
- testul pe ziua de luni 26.10 este în § 9.9 și folosește capacitatea calibrată, adică șoferi simulați care păstrează față de vehiculul
  din față un interval de timp mai scurt decât valoarea implicită din SUMO; pe aceleași scenarii sunt agentul E14 și analiza locului
  unde se pierde timpul la vârful de luni (§ 9.6). Aceste rezultate s-au retras pe 2.11: rețeaua părea să preia debitul observat doar
  fiindcă vehiculele se ciocneau și erau teleportate (§ 6.5);
- testul final, pe miercuri 28.10, și confirmarea, pe joi 29.10, sunt în § 9.10; și ele, cu tot cu câștigul de −7% al planului
  12/14/12, s-au retras pe 2.11, din același motiv (§ 6.5). Regulile zilelor de după 1.11 și validarea din 4.11 sunt în § 9.11.

Din 28.10, scenariile `zi_*` folosesc capacitatea calibrată (§ 6.4), retrasă pe 2.11 (§ 6.5); de atunci ele mai servesc doar pentru
istoric, iar scenariile măsurii noi, `cor_zi_*`, rulează pe geamănul corectat. Agenții de dinainte de E14 au fost antrenați pe
scenariile din 21–22.10, iar E14, pe cele de luni, cu rezultat negativ (§ 9.5). Agentul E15 s-a antrenat pe 3.11, pe geamănul
corectat și înghețat, doar pe orele din 25 și 26.10 și 1.11 care trec poarta (§ 9.11). Ziua de duminică
25.10 a servit ca test de generalizare, adică pentru a vedea cum se descurcă agenții într-o zi pe care nu au văzut-o
la antrenare. Ziua de luni 26.10 a servit întâi ca test, apoi ca zi de validare a protocolului din § 9.9; testul s-a
făcut pe miercuri 28.10, iar confirmarea, pe joi 29.10. Din 1.11, rolurile zilelor sunt cele din § 9.11: 25 și 26.10 au
devenit zile de antrenare, iar 28 și 29.10 sunt închise.

**Compoziția traficului.** Măsurătorile din prima zi, 21.10, au dat ≈93% autoturisme, ≈4% autobuze și troleibuze,
≈3% camioane și sub 0,5% biciclete și motociclete. Ponderea bicicletelor și a motocicletelor a fost mult sub ipoteza
inițială, de 2% biciclete și 3% motociclete, într-o zi de octombrie cu 12–15 °C. Duminică, la prânz, au fost ≈95%
autoturisme și ≈3% autobuze. Scenariile ipotetice `referinta_*` (§ 5.3) rămân în proiect pentru comparație, dar
agenții sunt antrenați **doar** pe scenariile din date reale.

### 5.5 Geamănul digital live

Geamănul digital este o copie a pieței în simulator. El rulează în paralel cu traficul real: programul
`bridge/live_twin.py` ține SUMO pornit continuu, în timp real, opțional cu interfața grafică SUMO-GUI. Traficul din
simulare urmează debitele măsurate de cameră, iar modul de control ales în dispecerat conduce semaforul simulat.

**Vehiculele.** În fiecare secundă, geamănul citește debitele curente publicate de modulul de viziune și introduce
vehicule pe brațele pieței. Vehiculele apar la momente întâmplătoare, dar numărul lor mediu pe oră este cel măsurat:
sosirile urmează un proces Poisson, modelul obișnuit pentru sosiri independente unele de altele. Destinațiile se aleg
după proporțiile de viraj observate. Pe geamănul corectat, rândul Dacia est și virajul Lascăr Catargiu → Dacia vest au cotele
fixe din § 5.1, iar virajul Magheru → Dacia est nu se ia din numărul lui, ca în scenarii, ci dintr-o cotă declarată, 0,14. Tipurile de vehicule se aleg după compoziția ipotetică din profilul de referință
(§ 5.3), nu după compoziția măsurată (§ 5.4), iar bicicliștii primesc rute permise bicicletelor. Debitele sunt cele
brute ale camerei, fără factorii de corecție (§ 5.1) și fără traficul de fond (§ 5.2).

**Pietonii.** Pietonii sunt introduși tot la momente întâmplătoare, după un proces Poisson, pe trasee pietonale care
trec prin piață. Debitul lor este cel măsurat pe trecerile vizibile, înmulțit cu factorul de extrapolare de la aceste
treceri la toată piața. Pe geamănul corectat, fiecare pieton traversează o singură dată, pe un braț, iar debitul se înmulțește
și cu factorul cererii efective de pietoni, 0,25 (§ 6.5). Geamănul poate introduce însă cel mult un pieton pe secundă, deci peste
3 600 de pietoni/h introduce mai puțini decât cere debitul. Pragul se depășea în zilele lucrătoare la prânz, la vârf și seara pe
varianta veche, pornită acum doar cu `--geaman-vechi` (§ 5.4); cu cererea efectivă, debitul rămâne sub el.

**Când lipsesc datele camerei.** Dacă fluxul camerei lipsește, adică ultima stare publicată de modulul de viziune e
mai veche de 60 s, sau dacă intervalul de numărare de 15 minute abia a început, geamănul păstrează ultimele debite
bune ale camerei, cel mult 20 de minute. După aceea trece pe profilul de referință și **afișează explicit** acest
lucru în dispecerat. Colectarea se reconectează automat la cameră, paznicul o repornește dacă procesul cade, iar veghea dă
alerta pe loc. În dispecerat, starea senzorului arată care verigă s-a oprit, iar fișa senzorului numără pauzele notate de
veghe (§ 4.6).

**Pașii simulării.** Simularea avansează în pași de 0,2 s, repartizați de-a lungul fiecărei secunde reale, ca
mișcarea să pară fluentă în SUMO-GUI. Controlerul semaforului lucrează însă pe secunde întregi.

**Geamănul corectat (2.11.2026).** Geamănul în timp real rulează acum pe rețeaua, tipurile de vehicule, rutele și pietonii din § 6.5, iar
planul implicit este planul observat. Debitele rămân cele brute, de la colectarea în curs, cu zonele vechi, cel puțin până după prezentarea M3, pe 15.11: colectarea păstrează `config/camera.json` neschimbat, ca măsura veche să rămână comparabilă (§ 9.11). Lascăr Catargiu e deci sub traficul real și ziua, nu doar seara, când aproape dispare: între 07:00 și 16:00, zona veche numără de 2–3 ori mai puțin decât
zona nouă înmulțită cu factorul ei de zi, 1,16 (§ 4.3), pe 25–26.10 și pe 1.11, iar pe 2–4.11, de 4–7 ori mai puțin (intrările din `data/counts`, față de cele din `data/counts_cor`). Dispeceratul nu arată cererea măsurii noi. Din geamănul în timp real nu iese nicio cifră raportată. Opțiunea `--geaman-vechi` pornește varianta de dinainte, doar pentru comparație.

**Modurile de control.** Din dispecerat se alege unul dintre aceste moduri:

- agentul IA, antrenat în simularea veche și neverificat pe geamănul corectat;
- planul fix de referință, cu fazele nord–sud, est–vest și pietoni, adică ipoteza de dinaintea măsurării programului real, cu un
  ciclu de ≈91 s infirmat de cameră; rămâne doar pentru comparație (§ 6.3, § 6.5);
- Max-Pressure, o regulă clasică, fără învățare, care dă verde fazei cu cea mai mare diferență dintre cozile
  dinaintea semaforului și cele de după el;
- manual, în care operatorul alege direcția, iar semaforul ajunge la ea pe pași siguri, urmăriți în dispecerat (§ 7.2, § 8);
- „Planul observat”, numit la borna M1 „Program pe cazuri de trafic” (§ 9.2, § 9.9). În cod, acest mod poate comuta automat
  între strategii după debitul echilibrat măsurat de cameră, adică media dintre intrări și ieșiri, dar varianta lui implicită e
  un plan fix, care nu comută.

Fără o comandă din dispecerat, geamănul pornește pe planul observat, 72/48/3. Între 29.10 și 2.11 a pornit pe planul 12/14/12, ales de
testul din § 9.10, retras între timp. În cod, varianta se alege cu `VARIANTA_PROGRAM`. Un plan fix este același în toate cazurile de
trafic, deci programul nu comută.

**Proba din 30.10, istorică.** O probă scurtă, fără fereastra grafică, a verificat pe 30.10, la 07:06, varianta implicită de
atunci, planul 12/14/12, retras pe 2.11 (§ 6.5). Comanda
`romana.bridge.live_twin --durata 300 --viteza 0` a simulat 300 s cât de repede s-a putut, pe debitele măsurate
atunci de cameră, de ≈3 500 veh/h, și a notat secundă cu secundă etapa semaforului: verde, galben sau roșu de
degajare. Proba a confirmat că, în acest mod, semaforul simulat ține verdele 12/14/12 s. După fiecare verde urmează
galbenul de 3 s și roșul de degajare de 2 s, în care intersecția se golește, deci ciclul complet are 53 s.

## 6. Rețeaua rutieră în SUMO

Ca să compare strategii de semaforizare, proiectul folosește o copie fidelă a străzilor din jurul pieței, construită
în SUMO, un program care simulează separat fiecare vehicul, biciclist și pieton. Această rețea rutieră este scheletul
geamănului digital, adică al simulării care reproduce piața. Capitolul descrie, pe rând, zona acoperită, replica
pieței, semaforul ei și încercările de a lega simularea de traficul real: prima a fost greșită (§ 6.4), iar § 6.5 spune ce a rămas.

### 6.1 Construcție reproductibilă

Scriptul `network/build_network.py` construiește rețeaua automat, așa că ea poate fi refăcută oricând. El pornește de
la extrasul zonei din harta OpenStreetMap[^osm] (OSM) și rulează pe el `netconvert`[^sumo], programul din SUMO care
transformă harta într-o rețea de simulare. Dreptunghiul prelucrat, de 2,2 × 1,6 km, include Piața Romană și primele
intersecții semaforizate de pe fiecare braț. În tabelul de mai jos, prima coloană dă numele controlerului fiecărei
intersecții, adică al obiectului din simulare care îi comandă semafoarele. În numele intersecțiilor, semnul × leagă
străzile care se intersectează.

| Numele în proiect | Intersecția | Distanța față de piață | Se vede pe cameră | Intră în coridorul controlat |
|---|---|---|---|---|
| `romana` | Piața Romană: Magheru – Lascăr Catargiu – Dacia | – | da | da, este controlerul principal |
| `dacia_eminescu` | Bd. Dacia × Str. M. Eminescu × Calea Dorobanți, pe brațul Dacia est | ~215 m | nu | da |
| `magheru_enescu` | Bd. Magheru × Str. G. Enescu / Tache Ionescu, la sud de piață | ~350 m | nu | da |
| `catargiu_manu` | Bd. Lascăr Catargiu × Str. Gh. Manu, la nord-vest de piață | ~490 m | nu | da |
| `dacia_victoriei` | Bd. Dacia × Calea Victoriei, pe brațul Dacia vest | ~480 m | nu | da |
| `dacia_polona` | Bd. Dacia × Str. Polonă | ~525 m | nu | nu, pentru că aici Bd. Dacia are sens unic, doar spre ieșirea din piață |

Scriptul recunoaște semafoarele **după coordonatele geografice**, adică după centrul geometric al nodurilor comandate
de fiecare semafor. Nodurile sunt punctele în care se leagă tronsoanele de drum. Identificatorii dați de `netconvert`
nu sunt folosiți, pentru că se schimbă la fiecare nouă generare a rețelei.

Străzile Mendeleev și Căderea Bastiliei au sens unic, doar spre ieșirea din piață. Acest lucru este confirmat atât de
etichetele OSM `oneway=yes`, prin care harta marchează un sens unic, cât și de traiectoriile observate pe cameră.

**Coridorul controlat** cuprinde piața și cei 4 vecini imediați care o alimentează. Varianta „coridor” a agentului de
inteligență artificială comandă deodată toate aceste intersecții. Intersecția Bd. Dacia × Str. Polonă a fost scoasă din
coridor după o observație a autorului, confirmată de OSM. Pe ambele tronsoane dintre Calea Dorobanți și Str. Polonă,
Bd. Dacia are eticheta `oneway=yes`; doar autobuzele circulă în contrasens, conform etichetei `oneway:bus=no`. Așadar,
la Polonă traficul obișnuit doar pleacă din piață. Intersecția rămâne totuși în simulare, cu programul ei actual.

Piața Victoriei și Piața Universității sunt mai departe, la ≈0,9 km și, respectiv, ≈1,5 km, cu alte intersecții
semaforizate între ele și Piața Romană. Prima abia intră în colțul de nord-vest al rețelei, iar a doua rămâne în afara
ei. Camera publică a Pieței Victoriei arată pasajul și nu este folosită (§ 4.1).

Denumirea străzii este **Calea Dorobanți**; în OSM, ea apare ca „Calea Dorobanților”.

### 6.2 Replica fidelă a pieței (Borna 8)

**Principiul.** Infrastructura din simulare rămâne exact cea din realitate: inelul pieței, axa centrală nord–sud
(N–S), benzile și virajele marcate, sensurile unice, benzile dedicate STB, trotuarele, trecerile de pietoni și
pozițiile reale ale semafoarelor. Inelul este drumul circular din jurul insulei centrale. Proiectul schimbă **doar
modul în care semafoarele existente răspund traficului**, adică programul lor: ordinea și durata fazelor. O fază este
intervalul în care anumite mișcări au verde. Programul este singurul lucru care se poate pune în practică pe automatul
real, adică pe dispozitivul din teren care comandă semafoarele. Geamănul corectat din 2.11 păstrează străzile, benzile, trecerile
și semafoarele din OSM; alegerile lui de modelare, de exemplu legăturile dintre benzi pe care OSM nu le precizează și prioritatea
pe cele 4 treceri de pe ieșiri, sunt declarate în § 6.5.

La import, `netconvert` preia din etichetele OSM trotuarele, accesul bicicletelor, benzile de viraj și restricțiile de
pe benzi. Apoi reconstruiește trecerile de pietoni și zonele lor de așteptare la toate intersecțiile. Rețeaua rezultată
are 6.943 de muchii, adică tronsoane de drum între două noduri, și 924 de noduri. Ea mai are 53 de semafoare, 225 de
benzi dedicate autobuzelor și trotuare pe toate arterele.

**Pentru specialiști.** Opțiunile corespunzătoare sunt `--osm.sidewalks` pentru trotuare, `--osm.turn-lanes` și
`--osm.lane-access` pentru benzile de viraj și restricțiile pe benzi, `--crossings.guess` și `--walkingareas` pentru
treceri și zonele de așteptare. Opțiunea `--osm.crossings`, care ar citi trecerile direct din OSM, face ca
netconvert 1.28 să se oprească brusc, cu eroare, pe acest extras.

În OSM, piața are **16 semafoare fizice**: pe intrări, pe inel, pe axa centrală și la treceri. Ca în realitate, unde
toate sunt comandate de un singur automat de intersecție, în simulare ele formează un singur controler, `romana`. Din
el fac parte semafoarele aflate la cel mult 80 m de centrul pieței: opțiunea `--tls.join` le grupează, iar
`--tls.join-exclude` le lasă pe celelalte separate. Controlerul comandă 61 de legături, adică mișcări cu semnal
propriu: 54 pentru vehicule, fiecare legând o bandă pe care vehiculele sosesc de o bandă pe care pleacă, și 7 treceri
de pietoni.

*Istoric.* În Bornele 3–7, adică în etapele 3–7 ale proiectului, piața fusese modelată ca un singur nod agregat: un
punct care ținea locul întregii piețe. Motivul era că, la primul import din OSM, vehiculele intrau în blocaj circular
pe segmentele interne foarte scurte, adică se așteptau unele pe altele în cerc. În Borna 8, cu programul construit pe
grupuri de semnal, s-a constatat că inelul se bloca atunci când semnalele de pe brațele de ieșire primeau roșu și
opreau vehiculele deja intrate pe inel. Cu ieșirile pe verde în toate fazele de vehicule (§ 6.3), replica fidelă
funcționează, iar nodul agregat, care nu respecta realitatea, a fost abandonat.

### 6.3 Grupurile de semnal și fazele semaforului Piața Romană

Semaforul pieței funcționează pe faze, iar un ciclu înseamnă parcurgerea o dată a tuturor fazelor dintr-un plan.
Fiecare fază dă verde unor **grupuri de semnal**. Un grup de semnal reunește legăturile cu același rol în trafic, de
exemplu legăturile unei intrări în piață. Programul nu este cel propus automat de `netconvert`, ci este construit pe
aceste grupuri, definite în `config/network.json`, la cheia `romana_grupuri`. Fiecare legătură de vehicule intră într-un
grup după muchia OSM pe care stau vehiculele la linia de oprire:

| Grupul | Numărul de legături | Rolul |
|---|---|---|
| `intrare_magheru`, `intrare_catargiu`, `intrare_dacia_est`, `intrare_dacia_vest` | 12 / 3 / 4 / 2 | intrările în piață |
| `axa_ns_centru` | 6 | axa centrală N–S, prin mijlocul pieței |
| `inel_dacia` | 11 | inelul din jurul insulei, pe direcția Dacia |
| `iesire_magheru_catargiu`, `iesire_dacia` | 12 / 4 | semnalele de pe brațele de ieșire |
| `pietoni` | 7 | trecerile de pietoni, grupate automat |

Pe aceste grupuri sunt definite cinci faze:

| Faza | Ce are verde | Face parte din planul fix |
|---|---|---|
| 0 | N–S: Magheru ↔ Lascăr Catargiu prin centru | da, 36 s |
| 1 | E–V (est–vest): Dacia în jurul insulei | da, 28 s |
| 2 | Pietoni: toate trecerile, axa centrală se golește | da, 12 s |
| 3 | N–S, cu intrările Dacia deschise, deci fără dozare | nu |
| 4 | E–V, cu intrările Magheru/Catargiu deschise, deci fără dozare | nu |

Planul fix de referință repetă mereu fazele 0–2, cu aceleași durate, într-un ciclu de ≈91 s: cele 3 faze, fiecare
urmată de un galben de 3 s și de un roșu de degajare de 2 s, în care intersecția se golește. Legăturile care rămân
verzi și în faza următoare își păstrează verdele și în timpul roșului de degajare. Planul a fost o ipoteză, fiindcă programul
semaforului nu e public, iar camera a infirmat-o: ziua, ciclul real are ≈125–155 s, iar un ciclu de ≈91 s nu apare (§ 6.5).
Planul rămâne în proiect doar ca reper pentru comparații.

Semnalele de pe ieșiri au verde în toate fazele de vehicule, pentru că fiecare ieșire primește vehicule în ambele faze
principale. Trecerile de pe ieșiri primesc verde în faza de pietoni. **Trecerile de pietoni primesc verde automat** în
orice fază în care traseul niciunui flux de vehicule cu verde nu le taie. Este o verificare de siguranță la construcția
programului; în plus, `build_network.py` refuză un program în care o trecere nu primește niciodată verde. Așa arată programul
rețelei vechi. Geamănul corectat din 2.11 păstrează grupurile și fazele, dar toate cele 7 treceri au verde și într-o etapă de
vehicule: pe cele 4 de pe ieșiri, pietonii merg printre vehiculele care virează, după programul măsurat din cameră pe Dacia și,
prin analogie, pe celelalte brațe. La planul observat, a treia etapă e doar golirea centrului, de 3 s, fără pietoni (§ 6.5).

Fazele 3–4 există ca opțiuni. În ele, intrările din cealaltă direcție sunt deschise în același timp, deci semaforul nu
mai limitează câte vehicule intră pe inel: de aici denumirea „fără dozare”. Evaluarea a arătat că, deschizând intrările
spre un inel deja ocupat, aceste faze blochează piața (§ 7.4). De aceea, strategiile adaptive, care decid fazele după
trafic, aleg implicit doar dintre fazele 0–2.

Intersecțiile vecine păstrează programele de tip `actuated` generate de `netconvert`, care prelungesc verdele cât timp
sosesc vehicule. Alegerea e doar o aproximare: și sistemul BTMS al municipalității funcționează adaptiv, dar programele reale
ale vecinilor nu se cunosc, iar asta e o limită declarată (§ 6.5, § 9.11). Excepție face varianta „coridor”, în care vecinii
sunt conduși de agent.

### 6.4 Capacitatea geamănului, calibrată pe 27.10 și retrasă pe 2.11

> **Corectură din 2.11.2026.** Alegerea de mai jos, `tau` = 0,8 s, a fost greșită: cu pasul de simulare de 1 s produce coliziuni și
> teleportări în masă, care nu s-au văzut fiindcă avertismentele erau oprite. Subcapitolul rămâne ca istoric, iar explicația și
> geamănul corectat sunt în § 6.5.

Chiar și cu o geometrie fidelă, geamănul poate să nu facă față traficului real. Debitul este numărul de vehicule care
trec printr-un loc într-o oră, iar capacitatea este debitul maxim pe care îl poate prelua piața. Capacitatea depinde și
de cât de strâns circulă șoferii. Pe scurt: cu parametrii impliciți ai SUMO, geamănul se blochează la vârful de luni
26.10, iar dacă șoferii simulați păstrează față de vehiculul din față un interval de 0,8 s în loc de 1,0 s, preia practic tot traficul.

Verificarea s-a făcut pe luni 26.10, prima zi lucrătoare înregistrată continuu (§ 4.6), pe două scenarii:

- vârful cu cererea calibrată, adică cu intrările numărate de cameră și corectate după numărătoarea de referință:
  scenariul `zi_2026-10-26_varf`, 15:00–16:00, cu ≈5 000 de vehicule/h prin piață;
- vârful ×1,2, adică același vârf cu 20% mai mult trafic: ≈6 000 de vehicule/h, aproape de numărătoarea de referință
  de la prânz, ≈6 200 (§ 4.3). Diferența dintre acea numărătoare și scenariul calibrat al aceleiași ore este discutată
  în § 5.4.

Cu parametrii impliciți ai SUMO pentru șoferi, geamănul **se blochează**. Acești parametri țin de modelul Krauss, care
descrie cum urmează un șofer vehiculul din față: intervalul de timp dorit până la el, `tau` = 1,0 s, distanța minimă 2,5 m și
imperfecțiunea `sigma` = 0,5. Distanța minimă este spațiul lăsat la oprire până la vehiculul din față, iar
imperfecțiunea arată cât de neregulat își ține șoferul viteza. Din cele 5 681 de vehicule ale vârfului, 2 121 rămân
neintroduse: până la final nu găsesc loc să intre în rețea. Pe intrarea Magheru trec 436 de vehicule pe oră, față de
≈2 360 cerute de scenariu și ≈3 070 în numărătoarea de referință.

Tabelul de mai jos arată ce se întâmplă cu alte valori ale parametrilor. Toate simulările din tabel folosesc planul fix
și seed-ul 1, adică aceeași valoare care pornește generatorul de numere aleatoare al simulării:

| Parametrii șoferilor: `tau` / distanța minimă / `sigma` | Vârful de luni: vehicule neintroduse la final | Vârful ×1,2: vehicule neintroduse la final |
|---|---|---|
| 1,0 s / 2,5 m / 0,5 (valorile implicite) | 2 121 (blocaj) | 3 135 (blocaj) |
| 1,0 s / 2,5 m / 0 | 1 771 (blocaj) | – |
| 1,0 s / 2,0 m / 0,5 | 2 051 (blocaj) | – |
| 0,9 s / 2,5 m / 0,5 | 588 | – |
| 0,9 s / 2,0 m / 0,5 | 473 | 1 000 |
| **0,8 s / 2,5 m / 0,5** | **15** | **45** |
| 0,8 s / 2,0 m / 0,5 | 19 | 19 |
| 0,8 s / 2,0 m / 0,3 | 10 | 19 |

Parametrul decisiv este acest interval de timp. Cu **`tau` = 0,8 s**, geamănul preia practic tot traficul vârfului de luni
și al vârfului ×1,2, fără blocaje: la final rămân neintroduse doar 15 vehicule din ≈5 700, respectiv 45 din ≈6 800.
Distanța minimă și imperfecțiunea contează puțin. Calibrarea schimbă un singur parametru față de valorile implicite,
iar valoarea de 0,8 s a fost aleasă prin încercări: dintre valorile încercate, este cea mai mică modificare a unui
singur parametru după care nu mai rămân sute de vehicule neintroduse. Cu 0,9 s rămân încă 588.

**Pentru specialiști.** Calibrarea este în `sumo/demand/vtypes_capacitate.add.xml` și, pentru participanții
indisciplinați, în `vtypes_capacitate_indisciplinat.add.xml`, cu scenariile `capacitate_zi_*` și
`capacitate_indisciplinat_zi_*`, generate cu `romana.bridge.indisciplinat --vtypes … --prefix …`.

Cu parametrii impliciți, pe intrările pieței trec doar 35–44% din vehiculele care trec cu `tau` = 0,8 s: în ora
măsurată, 1 689 față de 3 830 la vârf și 1 613 față de 4 576 la vârful ×1,2. Geamănul calibrat, cel cu `tau` = 0,8 s,
nu este saturat, adică nu a ajuns la limita lui: la final rămân neintroduse doar 15–45 de vehicule. Așadar,
capacitatea geamănului cu parametrii impliciți este cel mult o treime până la jumătate din cea reală.

Rezultatele din § 9.1–9.8, cu excepțiile enumerate la sfârșitul subcapitolului, sunt obținute cu parametrii impliciți,
pe următoarele date:

- Cererea din 21–22.10, din care s-a numărat doar aproximativ jumătate (§ 4.6). Cum capacitatea geamănului este și ea
  redusă, la cel mult o treime până la jumătate din cea reală, gradul de saturare, adică raportul dintre cerere și
  capacitate, este cel puțin egal cu cel real, probabil mai mare, iar valorile absolute sunt mai mici.
- Datele din duminica 25.10 (§ 9.3, § 9.4), înregistrată continuu, deci cu o cerere apropiată de cea reală, dar pe un
  geamăn suprasaturat, în care cererea depășește capacitatea. De aici vine, probabil, și faptul că agenții își pierd
  avantajul la vârful de duminică.

**Din 28.10 până pe 2.11, geamănul calibrat a fost varianta folosită implicit**, prin decizia autorului. Intervalul
`tau` = 0,8 s este scris în tipurile de vehicule generate de `romana.bridge.build_demand`, adică în
`sumo/demand/vtypes.add.xml`, și în `vtypes_indisciplinat.add.xml`. Prin urmare, scenariile `zi_*` și
`indisciplinat_zi_*` ale măsurii vechi îl folosesc și acum, doar pentru istoric. Din 2.11, geamănul în timp real, scenariile
măsurii noi, `cor_zi_*`, și antrenarea agentului E15 folosesc tipurile de vehicule ale geamănului corectat, cu `tau` = 1,0 s,
din `sumo/demand/vtypes_v2.add.xml` (§ 6.5).

**Pentru specialiști.** Fișierele `vtypes_capacitate*.add.xml` și scenariile `capacitate_*` au acum aceleași valori.
Ele rămân doar pentru reproducerea § 9.9, a analizei cu capacitatea calibrată din § 9.6 și a validării E14, care le
folosesc numele.

Rezultatele din § 9.1–9.8, afară de rândul lui E15 din § 9.5, sunt istorice. Cele mai multe s-au obținut cu tipurile de
vehicule care aveau parametrii impliciți ai SUMO, din commitul `75592d3`, adică dintr-o versiune salvată a codului (Anexa A).
Pe capacitatea calibrată au rulat validarea E14 (§ 9.5), analiza din § 9.6 care o folosește, evaluarea pe ziua de luni din
§ 9.9 și testul final, pe miercuri 28.10, cu confirmarea, pe joi 29.10, din § 9.10, la care trimite și § 9.7. Acestea s-au
retras pe 2.11: cu `tau` = 0,8 s și pasul de 1 s, geamănul avea coliziuni și teleportări în masă (§ 6.5).

### 6.5 Geamănul corectat: coliziunile ascunse și programul real (2.11.2026)

**Pe scurt.** Pe 2.11 s-au găsit două greșeli grave în geamăn, ambele din alegerile noastre de simulare, nu din date. Prima: din 28.10, simulările de evaluare rulau cu vehicule care se ciocnesc și sunt mutate instantaneu mai departe pe drum, adică teleportate. Geamănul părea să facă față traficului real doar din această cauză, deci rezultatele obținute pe el, inclusiv câștigul de −7% al planului 12/14/12 din § 9.10, **nu mai sunt valabile**. A doua: prima corectură, din aceeași noapte, potrivea debitele cu camera lăsând vehiculele să treacă prin pietoni. A găsit-o o revizie separată, făcută de alți agenți Claude decât cei care au scris corectura, cerută tocmai ca să o dărâme.

Geamănul de acum nu mai are teleportări în masă, iar atingerile dintre vehicule și pietoni au scăzut mult, fără să ajungă la zero. **Geamănul nu e validat.** Pe unele măsuri se apropie de cameră, pe altele nu, iar lista e mai jos. Concluziile mari nu depind de el: ciclul real și faptul că planurile scurte nu duc traficul la orele încărcate vin direct din cameră (mai jos). Geamănul nu poate decide încă între planuri apropiate. Cifrele de mai jos sunt cele de la înghețul din 3.11 (§ 9.11), făcut înainte de a privi datele din 3.11. Pe primele două zile judecate după îngheț, geamănul nu a trecut poarta pe nicio oră: pe 0 din 5 ore pe 3.11, ultima zi de antrenare, și pe 0 din 4 ore pe 4.11, ziua de validare. Cauza principală e Dacia vest: la orele încărcate ale acestor zile, geamănul duce acolo cam jumătate din traficul camerei. De aceea, validarea a fost doar descriptivă și niciun candidat nu a trecut de ea: runda s-a încheiat fără un program nou, iar planul observat, 72/48/3, rămâne (§ 9.11, `docs/rezultate/cor_decizie_2026-11-04.json`). Asta nu arată că planul observat e cel mai bun, ci doar că geamănul nu a putut judeca. Geamănul rămâne cel înghețat; reparațiile țin de o rundă nouă, cu reguli publicate înaintea datelor ei.

**Ce a mers prost.** Subcapitolul 6.4 a ales intervalul `tau` = 0,8 s, iar simularea avansează cu pași de 1 s. Un șofer simulat își
poate reconsidera viteza doar o dată pe pas, așa că, dacă intervalul dorit e mai mic decât pasul, nu mai poate frâna la timp. SUMO
avertizează exact asupra acestui lucru, dar simulările rulau cu avertismentele oprite (`--no-warnings`), iar acțiunea implicită la o
coliziune este teleportarea. Vehiculul ciocnit sare mai departe, inclusiv peste linia de oprire, pe roșu. Tabelul arată câte astfel de
evenimente sunt într-o singură oră de simulare, în zilele testului final (seed 1):

| Scenariul | Strategia | Vehicule sosite | Teleportări | Vehicule în coliziuni |
|---|---|---|---|---|
| vârful din 28.10 | 12/14/12 | 5 316 | 15 393 | 30 716 |
| vârful din 28.10 | 36/28/12 | 5 349 | 14 741 | 29 428 |
| prânzul din 29.10 | 36/28/12 | 5 071 | 14 309 | 28 514 |
| vârful din 28.10, participanți indisciplinați | 12/14/12 | 5 228 | 12 016 | 24 004 |

Un vehicul era teleportat, în medie, de aproape trei ori pe drum. Capacitatea pe care § 6.4 credea că a calibrat-o era, în mare parte,
efectul acestor salturi. Geamănul în timp real are pasul de 0,2 s, deci acolo nu apar astfel de ciocniri.

**Socoteala care ar fi dat de gol rezultatul.** Pe verde, camera măsoară pe Magheru ≈1,6 vehicule pe secundă. Planul 12/14/12 dă verde pe
Magheru 12 s dintr-un ciclu de 53 s, adică cel mult 12/53 × 1,6 × 3 600 ≈ 1 300 de vehicule pe oră. La vârf, camera numără ≈2 600 (2 618 pe 4.11, 08:30–09:30, și 2 652 pe 5.11, 07:30–08:30; pe 28.10, ziua testului, 2 387). Un
asemenea plan nu poate duce traficul, oricât de des ar veni verdele. Socoteala nu are nevoie de geamăn: vine direct din cameră.

**Ce arată camera despre programul real.** Programul semaforului nu e public, deci planul de referință 36/28/12 a fost o ipoteză. Dar
vehiculele trec prin zonele de intrare în valuri, după cum au verde. Comanda `python -m romana.vision.program_real` caută, pe ferestre
de 10 minute, perioada cu care se repetă valurile de pe Magheru, apoi suprapune ciclurile. Se folosește doar jurnalul public al
vehiculelor.

![Trecerile prin zonele de intrare, suprapuse pe ciclul real](imagini/program_real.png)

*Figura 6.1 – Programul real, măsurat din cameră, luni 26.10, la vârf. Magheru și Lascăr Catargiu curg împreună ≈70 s, apoi vine
rândul Bulevardului Dacia. Pe Dacia vest, zona prinde și câteva vehicule din afara verdelui ei. Sunt date detectate, fără factorii de
corecție. Rezultate: `docs/rezultate/program_real_2026-10-26.csv`.*

| Ziua și ora | Ciclul real | Magheru curge | Dacia est curge |
|---|---|---|---|
| luni 26.10, 12:00–13:00 | ≈140 s | – | ≈28 s |
| luni 26.10, 15:00–16:00, vârful măsurii vechi | ≈138 s (130–165 s) | ≈71 s | ≈26 s |
| luni 26.10, 17:30–18:30 | ≈132 s | – | ≈25 s |
| luni 26.10, 22:00–23:00 | ≈130 s | – | – |
| duminică 1.11, 12:00–14:00 | ≈151 s (146–157 s) | ≈77 s | ≈26 s |
| duminică 1.11, 19:00–21:00 | ≈130 s (122–141 s) | – | – |

Pe 2, 3, 4, 5 și 6.11, cinci zile lucrătoare, programul s-a măsurat din nou, după criterii scrise pe 5.11, la 20:55, când zilele 2–4.11
trecuseră deja, dar publicate înaintea rulărilor care dau verdictele, în `docs/rezultate/program_real_criterii.json`. Toate cele cinci
zile au destule date: fiecare are 61–70 de măsurători de încredere, de câte 20 de minute, iar criteriile cer cel puțin 30. Mediana
ciclului e ≈133–137 s, iar pe fiecare zi, în nouă măsurători de încredere din zece, ciclul are cel puțin 115 s. Mai strâns, pe
fiecare dintre zilele 2–5.11, cel puțin opt măsurători de încredere din zece au ciclul între 123 și 150 s: percentila 10 a zilei e
de 123,6–125,5 s, iar percentila 90, de 147,0–149,4 s. Acesta e intervalul din prezentarea bornei M2; pe 6.11, cele două percentile
sunt de 126,05 și 148,26 s. Intervalul de ≈125–155 s din celelalte capitole vine din măsurarea de pe 2.11, pe zilele de 26.10 și
1.11, din tabelul de mai sus. Căutarea obișnuită
acoperă doar 100–200 s, așa că o probă separată a lărgit-o la 80–240 s: nicio măsurătoare de încredere nu cade între 85 și 97 s, deci
un ciclu de ≈91 s nu apare. Medianele pe ore variază în cursul zilei, de la ≈122 la ≈154 s pe cele cinci zile: între cea mai mică și cea mai mare sunt 23–29 s, după zi.
Înaintea fiecărei rulări, ziua de 1.11 s-a măsurat din nou, ca probă, și a dat exact rezultatele publicate. Zilele de 5 și 6.11 s-au
judecat separat, fiecare a doua zi, după ce prelucrarea ei de noapte s-a încheiat fără eroare. Așa cer criteriile pentru 5.11; ziua de
6.11 nu e în lista lor, dar criteriile, publicate dinaintea ei, i s-au aplicat neschimbate.

Sâmbăta de 7.11, judecată la fel pe 8.11, cu aceleași criterii, neschimbate, e și ea măsurată: toate cele 72 de măsurători ale zilei
sunt de încredere. Mediana zilei e de 133,4 s, percentila 10, de 125,1 s, iar percentila 90, de 149,07 s. Medianele pe ore merg de la
123,6 s, la ora 06, până la 153,1 s, la ora 17, iar căutarea lărgită la 80–240 s nu găsește nicio măsurătoare între 85 și 97 s. E
singura zi de weekend judecată după criterii: duminica de 1.11 s-a măsurat pe 2.11, înaintea lor, și rămâne doar reper. Și sâmbăta,
deci, în opt măsurători de încredere din zece ciclul e între ≈125 și ≈149 s, iar programul se schimbă în cursul zilei.
Rezultatele sunt în `docs/rezultate/program_real_<zi>.csv`, iar verdictele, în `docs/rezultate/program_real_verdict_2026-11-02_04.json`,
`program_real_verdict_2026-11-05.json`, `program_real_verdict_2026-11-06.json` și `program_real_verdict_2026-11-07.json`.

Ciclul se schimbă în cursul zilei, ceea ce se potrivește cu un sistem adaptiv. Curgerea e o margine de jos a verdelui: la trafic slab,
coada se golește înainte de sfârșitul verdelui, așa că durata nu se poate citi din ea. Tot din jurnal se vede și când traversează
pietonii. Pe trecerea de pe Dacia est, cea mai vizibilă, ei merg în etapa Magheru–Catargiu, printre vehiculele care virează, nu într-o
fază doar a lor.

Din vârful zilei de luni, 26.10, s-a dedus **planul observat**, 72/48/3: 72 s de verde pentru Magheru–Catargiu, 48 s pentru Dacia și 3 s de golire
a centrului, fără pietoni, într-un ciclu de ≈138 s. Pietonii traversează în timpul celorlalte două etape. Semaforul real își schimbă
ciclul în cursul zilei, deci planul doar îl aproximează. Din 2.11, el e programul implicit al geamănului în timp real (§ 5.5) și una
dintre cele două referințe ale regulii din § 9.11.

**A doua greșeală: pietoni prin care se trece.** Cu `tau` = 1,0 s dispar aproape toate ciocnirile dintre vehicule pe care le vede SUMO, dar Magheru trecea doar o parte din traficul măsurat. Prima corectură a acoperit diferența cu un parametru al SUMO, `jmIgnoreJunctionFoeProb` = 0,5, cu motivul că în cameră vehiculele continuă să vireze și când trec pietonii. Parametrul înseamnă însă altceva: la o intersecție, șoferul ignoră pur și simplu, cu probabilitatea dată, pietonii din cale. Revizia a măsurat 1 621 de coliziuni între vehicule și pietoni într-o oră, cu vehiculele la ≈5 m/s, și 825 de intrări pe o trecere cu un pieton chiar în cale. Contorul de ciocniri nu le vedea, fiindcă SUMO nu verifică implicit ciocnirile din interiorul intersecțiilor. Potrivirea cu camera era deci un artefact, la fel ca teleportările. Scos parametrul, Magheru cobora la ≈2 080 de vehicule pe oră, față de ≈2 680 în cameră.

**Cauzele găsite apoi.** S-au găsit una câte una, urmărind fiecare bandă și fiecare trecere și comparând mereu cu camera:

1. *Rutele porneau de oriunde din rețea.* Camera vede doar piața, așa că alegerea rutelor era liberă: ≈72% din traficul de pe Magheru pornea de pe Calea Victoriei, prin 4 semafoare, iar aproape tot traficul de pe Catargiu, din Piața Victoriei, prin 7.
2. *O bandă nu ducea nicăieri.* Muchia 778823270, virajul la dreapta de pe Magheru spre Dacia est, rămăsese fără nicio legătură mai departe, iar vehiculele care o nimereau blocau și banda vecină până la teleportarea de după 300 s.
3. *Legături ghicite.* OSM nu spune mereu ce bandă duce în ce bandă, deci `netconvert` a ghicit. Pe Dacia vest spre inel și pe inel spre Dacia est rămăsese practic o singură bandă, iar traiectoriile arată două fire de vehicule.
4. *Șoferi care nu văd.* La o legătură care cedează trecerea, un șofer simulat vede implicit doar de la 4,5 m, așa că încetinește aproape până la oprire, chiar dacă nu vine nimeni.
5. *Un viraj umflat de proporții.* Virajul Magheru → Dacia est intra în cerere cu ≈670 de vehicule pe oră, deși camera numără direct 348 de traiectorii complete. Virajul se calcula din proporții, iar traiectoriile spre Catargiu, îndepărtat, ajung mult mai rar complete decât cele spre Dacia est, din prim-plan, deci cota ieșea aproape dublă. Cu atâtea vehicule, banda dreaptă rămânea plină, iar benzile vecine se blocau după ea. Virajul se ia acum din numărul lui, înmulțit cu un factor din numărătoarea de referință, fiindcă nici aici nu toate traiectoriile ajung complete: 1,25, numărat vehicul cu vehicul pe 36 de bucăți din etapa Magheru–Catargiu (intervalul de încredere 1,18–1,35). O primă estimare, ≈1,5, număra și vehiculele venite din Dacia vest, care trec prin același loc în altă etapă.
6. *Pietonii, la momentul greșit.* A treia etapă a planului dădea verde tuturor trecerilor până cu 5 s înainte de etapa N–S, iar traversarea celei de pe Magheru ține ≈10 s, deci primele vehicule așteptau mereu ultimii pietoni. Numărătoarea de referință din 2.11 arată că, pe Dacia est, pietonii pornesc aproape toți odată, la ≈28 s de la începutul valului de pe Magheru, iar la valurile de peste 90 s mai târziu. Geamănul urmează acum acest program pe Dacia, la etapele a căror durată se știe dinainte. Pe Magheru, pietonii merg după sfârșitul etapei N–S. Pe celelalte treceri, camera nu-i vede destul, deci programul e prin analogie. Înaintea oricărei schimbări de etapă, pietonii au 6 s să termine traversarea, cu vehiculele încă pe verde (`control/faze.py`).
7. *Modelul pietonilor din SUMO.* Îi ținea blocați pe zebră și pe insulele înguste mult mai mult decât se vede în cameră. Prea puțină răbdare îi face să forțeze roșul, iar prea multă îi ține pe loc: cu 150 s, un pieton pierdea ≈160 s. Valorile alese sunt la mijloc. Cei ≈5–7% care intră pe roșu vin din mecanismul de deblocare, la ≈60 s, fără să aleagă un gol, deci procentul nu e o dovadă de realism.
8. *Un pieton din geamăn nu e un om.* Numărătoarea de referință din 2.11 arată că detectorul pierde mulțimile: pe aceleași bucăți, adnotatorii găsesc pe o zebră de pe Dacia est, în medie, de 1,86 ori mai multe persoane decât numără el, iar în mulțimile dense numărul lor e doar un ordin de mărime (§ 4.4). Dacă toți acești oameni sunt puși în SUMO, vehiculele care virează spre Dacia est întârzie mult mai mult decât în cameră. Deja cu 0,66 agenți pe Dacia est la o persoană numărată de detector, de 2,6 ori mai mulți decât în geamănul final, la vârful din 26.10, debitul de pe Magheru rămâne același, dar un sfert dintre vehiculele care virează au nevoie de peste ≈8,9 s ca să treacă din zona de intrare în cea de ieșire, față de ≈5,9 s în cameră. Pe zebră, oamenii merg în grup, iar SUMO îi tratează pe fiecare separat, așa că un pieton simulat oprește mașinile cam cât un grup. De aceea, cererea de pietoni din geamăn e **efectivă**: e aleasă ca vehiculele să treacă printre pietoni ca în cameră, nu e numărul real. Valoarea, 0,25 agenți la o persoană numărată de detector pe Dacia est, s-a ales pe vârful din 26.10, cu cererea finală, dintre 0,15, 0,25, 0,33 și 0,42: e singura la care cele patru rânduri ale comparației despre pietoni stăteau sub pragurile calculate atunci, pe acea oră. Cu pragurile înghețate, mediana pe 12 ore, timpii virajului Magheru → Dacia est rămân peste prag la orice valoare încercată: în geamăn, vehiculele virează mai repede decât în cameră. Timpul pierdut de pietoni în geamăn nu e deci cel real, iar rezultatele se dau și cu pietonii cântăriți altfel.

**Geamănul corectat.** Se construiește cu `python -m romana.network.retea_v2`, din `config/retea_v2.json`, în fișiere separate: `sumo/net/romana_v2.net.xml`, `network_info_v2.json`, `tls_actuated_v2.add.xml`, `sumo/demand/vtypes_v2.add.xml` și `vtypes_indisciplinat_v2.add.xml`. Străzile, benzile, trecerile și semafoarele rămân cele din OSM; rețeaua, fazele și scenariile vechi nu s-au atins.

| Ce s-a schimbat | Cum | De ce e îndreptățit |
|---|---|---|
| Intervalul șoferilor, `tau` | 1,0 s, valoarea implicită, egală cu pasul | sub pas apar coliziuni |
| Rutele | pornesc de pe bulevardul brațului și se termină pe cel de ieșire: intrările la 148–566 m de piață, ieșirile la 130–346 m | camera nu vede mai departe; ruta de pe Magheru trece prin două semafoare reale, cu program presupus |
| Legăturile dintre benzi | 9 șterse și 7 noi, în `config/retea_v2.json` | a se vedea mai jos |
| Vederea la legăturile care cedează | 40 m în loc de 4,5 m, în toată rețeaua | un șofer real vede dacă vine cineva; afectează 1 743 de legături, deci e o alegere globală, nu o reparație locală |
| Virajul Magheru → Dacia est | din numărul lui, cu un factor din referință, nu din proporții | se vede bine, în prim-plan; din proporții ieșea aproape dublu |
| Pietonii | fiecare traversează o dată, pe un braț; cererea e efectivă, nu numărul real | cauza 8; pe celelalte brațe e o ipoteză, verificată ca ordin de mărime doar pe zebra de pe Magheru |
| Verdele trecerilor | după programul măsurat din cameră, pe Dacia | pentru Magheru–Catargiu și Dacia vest, camera vede prea puțini pietoni: același program, prin analogie, ipoteză |
| Prioritatea pe cele 4 treceri de pe ieșiri | vehiculele au „G”, iar trecerea „g”, invers față de convenția `netconvert` și de regula de circulație | în cameră, vehiculele curg și în timpul pietonilor; cu convenția inversă, pierderea crește cu 32–42%, iar Dacia est scade cu 14–18% |
| Modelul pietonilor | benzi de mers de 0,3 m, ieșire rapidă din blocaj pe zebră, răbdare de 60 s pe trotuar | banda e mai îngustă decât pietonul, deci vehiculele pot atinge pietoni, iar atingerile se numără; valoarea 0,3 e aleasă pe debit: cu 0,64, Magheru scade cu 18% |

Parametrii `sigma` și `minGap`, aleși inițial pe debitul din cameră, au revenit la valorile vechi din `vtypes.add.xml`. Alegerea s-a făcut chiar pe rândurile de profil, care astfel nu mai sunt independente.

*Pentru specialiști: legăturile.* Regula proiectului cere o rețea fidelă, deci o legătură schimbată trebuie să aibă un motiv. Benzile și geometria muchiilor sunt identice cu rețeaua generată din OSM, `romana.net.xml`; reconstruirea schimbă poligonul unui nod la 489 m și numerotarea internă la câteva noduri depărtate. Dintre legături, cele de pe Dacia vest spre inel (778823266 → 778823265), de pe inel spre Dacia est (448266586 → 1214130905 și 448266584) și ieșirea din banda-capcană (778823270 → 119238380#0) au motivele de mai sus. Celelalte, de pe 778823265 și 778823271, sunt cele care le completează, ca banda nouă să nu rămână fără continuare. Ele nu sunt măsurate direct, deci sunt o alegere de modelare, declarată aici.

**Semaforul rejucat.** Un plan fix doar aproximează semaforul real: ciclul lui diferă de la o oră la alta, iar pe aceeași oră variază cu zeci de secunde. Modulul `control/rejucat.py` ia începutul și sfârșitul fiecărui val de vehicule de pe Magheru, din jurnalul public al zilei, și face din ele programul semaforului. Etapa E–V e restul ciclului, tăiată la 60 s prin ipoteză. Pe orele încărcate ale comparației de la îngheț, 78–95% din oră vine din valuri măsurate, iar pe cele liniștite, 0–44%, deci acolo programul e în mare parte presupus. Sub 80% nu i se spune „semaforul real”: așa sunt orele liniștite și vârful din 2.11, cu 78%.

**Cum se compară cu camera.** Semaforul fiind același, camera și geamănul se pot pune pe același ceas: secundele de la începutul fiecărui val. Comanda e `python -m romana.control.valideaza_geaman`. Prima variantă a comparației era prea slabă, iar revizia a arătat-o: un model fără nicio fizică, cu debit constant în fereastra rejucată, trecea mai multe rânduri de profil decât geamănul, un geamăn fără niciun pieton trecea și el, iar unul cu 44% mai puțină pierdere abia se deosebea. De aceea, „reproduce camera”, cum scrie în mesajul unui commit din 2.11, nu rezistă, iar „pietonii nu mai sunt fantome”, din alt mesaj, e prea tare.

Comparația s-a rescris. Nu mai are un scor total, ci rânduri pe grupuri, iar un rând al cărui interval dintre seed-uri trece peste prag rămâne nedecis. Are și gemeni greșiți dinadins, ca să se vadă ce rânduri deosebesc ceva. Profilurile verifică ceasul și ferestrele, nu dinamica. Măsurile s-au stabilit în mai multe runde, pe aceleași ore, după ce s-au văzut rezultatele. S-au înghețat pe 3.11, la un commit numit (§ 9.11), iar prima judecată curată e o zi nouă.

**Ce se potrivește și ce nu, la îngheț.** Comparația finală s-a făcut pe zilele de antrenare: 12 ore din 25.10, 26.10, 1.11 și 2.11, câte 5 seed-uri, cu semaforul rejucat. Rezultatele sunt în `docs/rezultate/validare_geaman.csv`, iar pragurile, în `docs/rezultate/praguri_geaman.json`. Tabelul dă debitul pe fiecare intrare, în vehicule pe oră, în geamăn și în cameră (numărătoarea înmulțită cu factorul de corecție), cu abaterea; apoi partea din vehicule care nu intră sau nu ajung la destinație până la sfârșitul rulării, adică după cele 15 minute de golire de după oră, teleportările pe rulare și verdictul porții. La sfârșitul orei propriu-zise mai pot aștepta vehicule chiar unde coloana arată 0,0%: la vârful din 26.10, ≈94 pe Dacia vest.

| Ora | Magheru | Lascăr Catargiu | Dacia est | Dacia vest | Neintrate | Teleportări | Poarta |
|---|---|---|---|---|---|---|---|
| luni 26.10, vârf, 14:30–15:30 | 2 669 / 2 676 (0%) | 1 669 / 1 731 (−4%) | 483 / 475 (+2%) | 587 / 766 (−23%) | 0,0% | 0 | trece |
| luni 26.10, seara, 17:30–18:30 | 1 822 / 1 884 (−3%) | 1 051 / 1 030 (+2%) | 551 / 548 (+1%) | 590 / 1 063 (−44%) | 6,4% | 0 | nu: neintrate |
| luni 26.10, liniștit, 23:00–00:00 | 819 / 801 (+2%) | 649 / 633 (+3%) | 119 / 116 (+3%) | 127 / 126 (0%) | 0,0% | 0 | trece |
| duminică 25.10, vârf, 15:30–16:30 | 2 356 / 2 350 (0%) | 1 677 / 1 640 (+2%) | 308 / 303 (+1%) | 372 / 385 (−3%) | 0,0% | 0 | trece |
| duminică 25.10, liniștit, 06:30–07:30 | 597 / 585 (+2%) | 362 / 366 (−1%) | 92 / 90 (+2%) | 90 / 102 (−12%) | 0,0% | 0 | trece |
| duminică 1.11, vârf, 13:15–14:15 | 2 438 / 2 482 (−2%) | 1 506 / 1 538 (−2%) | 386 / 393 (−2%) | 459 / 459 (0%) | 0,0% | 0 | trece |
| duminică 1.11, prânz, 12:00–13:00 | 2 463 / 2 386 (+3%) | 1 536 / 1 517 (+1%) | 369 / 394 (−6%) | 344 / 362 (−5%) | 0,0% | 0 | trece |
| duminică 1.11, seara, 17:30–18:30 | 2 242 / 2 231 (+1%) | 1 400 / 1 404 (0%) | 386 / 369 (+4%) | 675 / 654 (+3%) | 0,0% | 0 | trece |
| duminică 1.11, liniștit, 23:00–00:00 | 651 / 625 (+4%) | 509 / 497 (+2%) | 107 / 108 (−1%) | 65 / 66 (−1%) | 0,0% | 0 | trece |
| luni 2.11, vârf, 13:00–14:00 | 2 650 / 2 592 (+2%) | 1 909 / 1 897 (+1%) | 583 / 591 (−1%) | 482 / 955 (−50%) | 4,1% | 0 | nu: neintrate |
| luni 2.11, prânz, 12:00–13:00 | 2 767 / 2 765 (0%) | 1 503 / 1 498 (0%) | 499 / 568 (−12%) | 342 / 995 (−66%) | 7,7% | 0 | nu: debit Dacia est, neintrate |
| luni 2.11, liniștit, 03:15–04:15 | 198 / 196 (+1%) | 93 / 95 (−3%) | 21 / 21 (+1%) | 97 / 87 (+12%) | 0,0% | 28 | nu: teleportări |

![Geamănul lângă cameră, pe același ceas, la vârful din 26.10](imagini/geaman_camera.png)

*Figura 6.2 – Vârful din luni 26.10, 14:30–15:30: câte vehicule trec, pe ciclu, la fiecare 10 s de la începutul valului de pe Magheru, în cameră și în geamăn (media celor 5 seed-uri), cu semaforul rejucat. Ieșirea spre Dacia est e dată ca parte din total, fiindcă ieșirile nu intră în cerere. Pe Dacia est, geamănul pornește cu ≈10 s mai devreme decât camera.*

* *Se apropie.* Pe 8 din cele 12 ore, debitele de pe Magheru, Lascăr Catargiu și Dacia est sunt la cel mult 6,3% de cameră, toate vehiculele intră, iar teleportările și ciocnirile văzute de SUMO lipsesc sau sunt excepții. Trec toate orele de duminică, inclusiv cele două ținute deoparte, și două ore de luni, 26.10: vârful și ora liniștită.
* *Nu se potrivește.* Dacia vest în zilele lucrătoare de antrenare: geamănul duce cel mult ≈590 de vehicule pe oră, fiindcă vehiculele trec prea încet chiar după linia de oprire, cum a arătat diagnoza din 4.11 (§ 9.11), iar camera, cu factorul de corecție, dă 766–1 063, deci rămân vehicule neintrate. De aceea pică poarta seara din 26.10 și vârful și prânzul din 2.11, ziua cu cel mai mult trafic pe Dacia vest; pe 2.11, la prânz, scade și Dacia est, cu 12%. Ora liniștită din 2.11 are 28 de teleportări pe rulare. Cauza s-a găsit pe 4.11 (§ 9.11): noaptea, valurile de pe Magheru sunt prea rare, iar programul rejucat ia drept ciclu o distanță mult prea lungă dintre ele, așa că vehiculele de pe Dacia stau 300 s la roșu și sunt teleportate. Refăcut pe ritmul intrărilor, programul nu mai dă teleportări într-o probă pe noaptea de 2.11; reparația ține de o rundă nouă, după M3, cu zile noi și cu reguli publicate înaintea datelor ei (§ 9.11). Ziua de 2.11 nu trece pe nicio oră, deci, după regula din § 9.11, ar fi doar descriptivă. Tot la vârful din 26.10, virajul Magheru → Dacia est trece piața mai repede decât în cameră: mediana e 2,6 s față de 3,1 s, iar un sfert dintre vehicule au nevoie de peste 3,6 s, față de 5,9 s. Nu se potrivesc nici debitul de vârf pe 20 s de pe Dacia est (0,60 față de 0,74 vehicule pe secundă), histograma pietonilor și formele ieșirilor, iar ieșirea spre Dacia est din secundele 24–60 ale etapei N–S, 4,9 față de 6,1 vehicule pe etapă, rămâne nedecisă.
* *Gemenii greșiți dinadins.* Geamănul cu vehicule mai rapide se deosebește de cel de bază pe 15–33 de rânduri din fiecare oră, afară de ora liniștită din 2.11. Geamănul fără niciun pieton, în schimb, se deosebește pe cel mult 4 rânduri dintr-o oră, iar pe jumătate din ore pe niciunul. Comparația cu camera nu poate deci confirma pietonii din geamăn.

**Ce spune geamănul despre planuri.** Planurile scurte nu duc traficul la orele încărcate: socoteala din cameră, de mai sus, dă pentru 12/14/12 cel mult ≈1 300 de vehicule pe oră pe Magheru, față de ≈2 600 numărate. Grila de după îngheț o confirmă, pe cele 8 ore ale zilelor de antrenare care trec poarta, cu variantele lor ×0,8 și ×1,2, adică pe 14 scenarii, și cu 3 seed-uri, pe toate cele 84 de perechi, cu orele liniștite cu tot: 12/14/12 pierde de ≈7,5 ori mai mult timp decât semaforul rejucat cu participanții disciplinați și de ≈5,7 ori mai mult cu cei indisciplinați, iar 36/28/12, cu ≈⅔ și, respectiv, cu ≈¼ mai mult. Planurile cu ciclul între ≈93 și ≈138 s se deosebesc între ele cu câteva procente, cât rezultatul retras, deci aici nu se dă niciun procent ca rezultat: grila a servit doar la alcătuirea listei de candidați a regulii din § 9.11. Rezultatele sunt în `docs/rezultate/grila_inghet_normal.csv` și `grila_inghet_indisciplinat.csv`, iar planurile 52/35/3 și 36/24/3 și agentul E15, încercați apoi doar pe orele care trec poarta, în `grila_inghet_ciclu.csv` și `grila_inghet_e15.csv`.

**Ce rămâne nesigur.** Setările s-au ales pe orele de antrenare și pe rândurile de comparație, în mai multe runde. Pietonii din geamăn sunt o cerere efectivă, iar cei de pe celelalte brațe se văd slab: zebra de pe Magheru se poate număra pe clipuri, cele de pe Lascăr Catargiu și Dacia vest nu. Pe Dacia vest nu e sigură nici cererea: factorul ei variază de la 1,03 la 1,58 între clipuri, iar o cincime din numărătoarea automată cade în bucăți în care adnotatorii nu văd aproape niciun vehicul, deci la vârfurile zilelor lucrătoare debitul real poate fi de ordinul 750–1 250 de vehicule pe oră. Pe întuneric și pe ploaie, detectorul poate pierde mult mai multe vehicule decât acoperă factorul; rândul porții prinde asta doar la trafic mare, iar pragul lui stă pe o singură seară. Semafoarele vecine sunt programele generate de `netconvert`. Pe Dacia est, primele vehicule vin la ≈12 s după începutul etapei din program, iar în geamăn imediat, din cauze nelămurite. Nu există o măsurare a lungimii cozilor, deci potrivirea e verificată pe ce trece prin zone, nu direct pe timpii de așteptare. Geamănul în timp real din dispecerat are proporții declarate și debite brute, deci nu arată geamănul de mai sus; Lascăr Catargiu e acolo ziua de 2–3 ori sub cel real pe 25–26.10 și pe 1.11 și de 4–7 ori pe 2–4.11, iar seara aproape dispare (§ 5.5).

## 7. Controlul inteligent al semafoarelor

Acest capitol arată cum învață un program, numit agent, să conducă semaforul Pieței Romane. În simulare, agentul alege
o fază, adică un grup de mișcări care au verde împreună, și primește o notă, numită recompensă. Metoda se numește
învățare prin întărire (RL, din engleză *reinforcement learning*). Regulile de siguranță sunt impuse separat (§ 7.2),
iar agentul este comparat cu patru strategii clasice și, din 2.11, cu două referințe luate din cameră, planul observat și
semaforul rejucat (§ 6.5, § 7.4), după măsurătorile descrise în § 7.5. Rezultatul rundei de alegere e în § 9.11: pe 4.11, ziua de
validare, geamănul nu s-a potrivit cu camera pe nicio oră, deci validarea a fost doar descriptivă și niciun candidat, nici
agentul E15, n-a putut trece de ea. Runda s-a încheiat fără un program nou, iar în geamăn rămâne planul observat, 72/48/3.
Asta nu arată că planul observat e cel mai bun, ci doar că geamănul nu a putut judeca.

### 7.1 Formularea ca problemă de decizie Markov

O problemă de decizie Markov descrie matematic „jocul” agentului. La fiecare pas, agentul vede starea intersecției,
alege o acțiune și primește o recompensă; ce urmează depinde doar de starea de acum și de acțiunea aleasă. Pentru
Piața Romană, elementele ei sunt următoarele.

**Pasul de decizie** este de 5 s simulate.

**Starea**, numită și observație, este ceea ce „vede” agentul. Pentru fiecare semafor controlat, ea cuprinde:

* faza verde curentă, codificată „one-hot”: un șir de zerouri, cu un singur 1 pe poziția fazei active;
* indicatorul „verde minim îndeplinit” și durata verdelui curent, raportată la verdele maxim;
* pentru fiecare bandă de intrare, coada, adică numărul de vehicule oprite, și densitatea, adică numărul tuturor
  vehiculelor de pe bandă; ambele sunt raportate la capacitatea de stocare a benzii, care arată câte vehicule încap pe
  ea: lungimea benzii împărțită la 7,5 m;
* pentru fiecare zonă de așteptare a unei treceri controlate, numărul de pietoni care așteaptă, raportat la 15.

Aceste raportări aduc toate valorile pe aceeași scară, de la 0 la 1; operația se numește normalizare. Aceeași funcție,
`observation()` din `control/signals.py`, servește antrenarea, evaluarea și geamănul digital.

**Acțiunea** este faza verde cerută de agent. La Piața Romană, el alege implicit una dintre cele 3 faze ale planului
de referință: nord–sud (N–S), est–vest (E–V) și pietoni. Agentul E15 alege doar între N–S și E–V, iar golirea centrului vine singură. Agentul decide deci **ordinea și durata** fazelor, exact ce se poate
programa pe automatul existent. Fazele „fără dozare” (§ 6.3) pot fi permise cu opțiunea `--toate-fazele`. În varianta
coridor, agentul ia câte o decizie pentru fiecare dintre cele 5 semafoare ale coridorului; spațiul acțiunilor este
atunci de tip `MultiDiscrete`, adică un șir de alegeri, câte una pentru fiecare semafor.

**Recompensa** este nota primită după fiecare pas, cu atât mai mică cu cât așteaptă mai mulți participanți:

$r_t = -\frac{1}{100}\left(\sum_{\ell} q_\ell(t) + \sum_{c} p_c(t) + b(t)\right)$

În formulă:

* $r_t$ este recompensa la momentul $t$;
* $q_\ell$ este numărul de vehicule oprite pe banda de intrare $\ell$;
* $p_c$ este numărul de pietoni care așteaptă la trecerea $c$;
* $b$ este numărul de vehicule care nu pot intra în rețea, blocate la margine;
* Σ înseamnă suma pe toate benzile de intrare, respectiv pe toate trecerile.

Un pieton care așteaptă și un vehicul neintrodus cântăresc deci cât un vehicul oprit.

*Lecție din Borna 8.* Când penalizarea pentru $b$ era mică, de numai 0,002, agentul din varianta coridor a învățat să
„ascundă” coada în afara rețelei. În scenariul moderat, cozile din piață aveau doar 4–8 vehicule, dar așteptarea medie
ajungea la ≈450 s, iar la final rămâneau ≈400 de vehicule. Este un exemplu clasic de exploatare a recompensei
(*reward hacking*): agentul își îmbunătățește nota fără să rezolve problema reală. Modelele au fost reantrenate cu
formula de mai sus, iar evaluarea raportează și întârzierea la intrarea în rețea.

**Pentru specialiști.** Varianta „cozi în amonte”, numită v2, a fost introdusă în Borna 9. Pe scenariile din date
reale, la vârf, benzile scurte de la linia de oprire, de 30–90 m, sunt pline orice ar decide agentul. Atunci suma
cozilor de pe benzile de intrare, $\sum_\ell q_\ell$, nu mai variază, iar cozile care cresc spre intersecțiile vecine
nu se văd, de exemplu pe Bd. Dacia dinspre Calea Victoriei. Opțiunea `--obs-amonte` adaugă la stare coada din amonte,
adică de pe tronsoanele dinaintea intrării, pe ≈250 m, raportată la capacitatea lor de stocare. Această coadă
se calculează pentru fiecare intrare a fiecărui controler, adică a fiecărui automat de semafor condus de agent.
Starea primește și numărul de vehicule neintroduse. Recompensa adaugă la $\sum_\ell q_\ell$ și vehiculele oprite pe
aceste benzi din amonte, notate cu $u$, fiecare bandă fiind numărată o singură dată:

$r_t = -\frac{1}{100}\left(\sum_{\ell} q_\ell + \sum_{u} q_u + \sum_{c} p_c + b\right)$

Opțiunea se salvează în `models/*.json`, în câmpul `obs_amonte`, deci evaluarea și geamănul digital folosesc automat
aceeași stare.

### 7.2 Siguranța prin construcție

Agentul nu aprinde direct culorile, ci cere doar faza verde următoare. Modulul `control/signals.py` impune apoi
regulile de siguranță, oricare ar fi cererea:

* galben 3 s;
* roșu general 2 s, numit și roșu de degajare, pe legăturile care se schimbă;
* verde minim 10 s;
* verde maxim 90 s, după care faza trece forțat la următoarea.

O legătură este o mișcare controlată de semafor, cu semnalul ei, de exemplu de pe o bandă de intrare spre una de
ieșire. Ciorna inițială sărea direct de la o fază verde la alta, fără galben (vezi
`legacy/google_ai_draft/README.md`).

Pe geamănul corectat (§ 6.5), `control/faze.py` adaugă programul pietonilor. Îl respectă orice strategie care cere faze,
deci agentul, Max-Pressure și comanda manuală din dispecerat: din etapa N–S se poate trece mai departe abia după 35 s, ca
pietonii de pe Dacia, care pornesc la 28 s, să aibă măcar 7 s de verde, iar înaintea oricărei schimbări pietonii au 6 s să
termine traversarea, cu vehiculele încă pe verde. În simulările de evaluare, la planurile fixe, la semaforul rejucat și la
actuated, ferestrele pietonilor sunt scrise direct în programul semaforului, cu aceleași 6 s de degajare.

### 7.3 Algoritmul de învățare

Agentul învață cu algoritmul PPO (Proximal Policy Optimization)[^ppo] din biblioteca Stable-Baselines3[^sb3]. PPO
corectează strategia agentului în pași mici, fără salturi bruște de comportament. Strategia este o rețea neuronală
MLP 128 × 128, adică un perceptron multistrat cu două straturi ascunse a câte 128 de neuroni.

Un episod de antrenare înseamnă o oră de trafic, pe un scenariu ales aleator din setul de antrenare, cu un seed SUMO
tot aleator. Seed-ul este valoarea care pornește generatorul de numere aleatoare al simulării. PPO a fost preferat lui
DQN[^dqn], un alt algoritm de învățare prin întărire, pentru că lucrează firesc cu acțiunile `MultiDiscrete` ale
variantei coridor.

Simularea rulează prin `libsumo`, care oferă aceleași comenzi ca interfața TraCI, dar fără comunicație prin socket,
adică fără mesaje printr-o conexiune de rețea. Antrenarea folosește de obicei **8 procese paralele**, adică 8 simulări
simultane, create cu `SubprocVecEnv`; numărul lor se alege cu opțiunea `--medii`, implicit 6. Fișierele modelelor îl
notează: 7 la agentul oficial, 3 la E15. Cu 8 procese, pe procesorul i5-13420H al laptopului se ajunge la ≈55–70 de pași
de decizie pe secundă, față de ≈18 cu un singur proces. Replica fidelă, cu pietoni, cere mult
mai multe calcule decât rețeaua veche, în care piața era modelată ca un singur nod agregat (§ 6.2).

Lucrările de referință pentru învățarea prin întărire aplicată semafoarelor sunt IntelliLight[^intellilight],
PressLight[^presslight], CoLight[^colight], MPLight[^mplight] și sintezele lui Wei et al.[^survey2019][^survey2021].
Mediul de antrenare, adică programul care leagă agentul de simulare, a fost scris în stilul bibliotecii
sumo-rl[^sumorl].

**Pentru specialiști.** Pe Windows, PYTHONPATH-ul setat de instalatorul SUMO face ca varianta `libsumo` din
instalare, căreia îi lipsesc DLL-uri, să o ascundă pe cea din pachetul pip `libsumo`; de aceea `control/env.py`
încarcă explicit pachetul pip. Parametrii algoritmului PPO sunt următorii:

| Parametru | Valoare | Ce înseamnă |
|---|---|---|
| Rata de învățare | 3·10⁻⁴ | mărimea fiecărei corecții a rețelei |
| Tranziții pe corecție | ≈1.024 | pași de decizie adunați înaintea unei corecții |
| Lot | 128 | tranziții prelucrate deodată |
| Epoci | 10 | de câte ori se parcurg tranzițiile adunate la o corecție |
| Factorul de actualizare | γ = 0,98 | cât contează recompensele viitoare față de cele imediate |
| Parametrul GAE | λ_GAE = 0,95 | la estimarea generalizată a avantajului (GAE), cât de departe în viitor se caută urmările unei decizii |
| Coeficientul de entropie | 0,01 | cât este încurajat agentul să încerce și alte faze |

Agentul E15 pornește altfel: întâi imită planul observat, 72/48/3, pe ≈40 000 de pași de decizie, cu opțiunea
`--bc-plan`, și abia apoi învață cu PPO. La el, coeficientul de entropie e 0,003, iar corecțiile sunt limitate mai
strâns (`models/ppo_e15.json`, `control/train.py`).

### 7.4 Linii de bază

Agentul este comparat cu patru metode clasice, care nu învață din experiență. În literatura de specialitate scrisă în
engleză, ele se numesc *baselines*, de unde titlul „linii de bază”; în text le spunem și strategii de referință.

1. **Planul fix de referință** este programul din rețea: verde 36 s pentru N–S, 28 s pentru E–V și 12 s pentru
   pietoni, cu un ciclu de ≈ 91 s. Ciclul este durata după care fazele se repetă, cu tot cu galbenul și roșul de
   degajare dintre ele (§ 6.3). Planul a fost o ipoteză, fiindcă programul semaforului nu e public, și camera a
   infirmat-o: ziua, ciclul real are ≈125–155 s, iar un ciclu de ≈91 s nu apare (§ 6.5). Față de acest plan se
   raportează, de regulă, procentele din § 9.2–9.9; testul din § 9.10 a judecat față de programul realist, iar regula din § 9.11
   compară cu planul observat, 72/48/3, și cu semaforul rejucat.
2. **Planul fix Webster**[^webster] are ciclul optim, cel cu întârzierea medie cea mai mică, dat de formula
   $C_0 = \frac{1{,}5L + 5}{1 - Y}$ și limitat la 60–150 s. Aici $L$ este timpul pierdut, în care vehiculele nu
   circulă efectiv: 7 s pe fază, plus întreaga fază de pietoni. Mărimea $Y = \sum_i y_i$ adună, pentru fiecare fază de
   vehicule $i$, valoarea $y_i$: cel mai mare raport dintre debit și debitul de saturație, printre intrările care au
   verde în acea fază. Debitul de saturație, adică cel mai mare debit care poate trece pe o bandă la verde, este de
   1800 veh/h/bandă și se socotește numai pe benzile de autoturisme, fără benzile STB. Verdele se împarte proporțional
   cu $y_i$, iar faza de pietoni își păstrează durata.
3. **Actuated SUMO** este un program de semafor care reacționează la vehiculele detectate. Pe aceleași 3 faze,
   prelungește verdele cât timp detectoarele văd vehicule la intervale mai mici de 3 s, cu un verde de minimum 10 s și
   maximum 60 s.
4. **Max-Pressure**[^maxpressure] alege la fiecare decizie faza cu presiunea cea mai mare. Presiunea unei faze este
   $\sum (\text{coadă amonte} - \text{coadă aval})$, adică suma, pe legăturile ei verzi, a diferențelor dintre coada
   dinaintea semaforului și coada de după el. La treceri, „coada” din amonte este numărul de pietoni care așteaptă;
   altfel faza de pietoni nu ar fi aleasă niciodată. Algoritmul nu învață, dar are garanții teoretice de stabilitate,
   adică se poate demonstra că ține cozile sub control când cererea poate fi servită. Un agent RL trebuie să-l
   egaleze sau să-l depășească pentru a fi convingător.

Pe replica fidelă, Max-Pressure, când putea folosi toate cele 5 faze, alegea mereu fazele „fără dozare”, care au cele
mai multe legături verzi, deci presiunea cea mai mare. Așa bloca piața complet: în scenariul moderat, cu 1 seed,
rămâneau în rețea 1.226 de vehicule, față de 107 la planul fix. Restrâns la fazele planului de referință, nu mai blochează
piața: rămân 97 de vehicule, în medie pe 5 seed-uri. Rezultatele complete sunt în
`docs/rezultate/scenarii_referinta/` (Anexa A).

**Referințele din cameră (din 2.11).** Pe geamănul corectat, comparația se face și cu două referințe luate din cameră:
planul observat, 72/48/3, un plan fix cu ciclul de ≈138 s, dedus din cameră la vârful din 26.10, și semaforul rejucat,
care refolosește începutul și sfârșitul fiecărui val de vehicule de pe Magheru din ziua simulată (§ 6.5). Pe orele
liniștite, unde la îngheț doar 0–44% din oră vine din valuri măsurate, semaforul rejucat e în mare parte presupus, așa că el contează doar pe orele acoperite cel puțin
80% de valuri măsurate. Un candidat trebuie să le bată pe amândouă, iar actuated doar se raportează alături (§ 9.11). Tot
pe geamănul corectat, actuated are etapele planului observat, N–S, E–V și golirea centrului de 3 s, cu ferestrele
pietonilor (§ 6.5), și lungește verdele doar în fereastra pietonilor: verdele N–S ține între 39 și 93 s, iar cel E–V,
între 16 și 60 s (`sumo/net/tls_actuated_v2.add.xml`).

### 7.5 Metrici

Metricile, adică măsurătorile după care se compară strategiile, vin din fișierul `tripinfo` al SUMO. Ele acoperă
toată durata scenariului, plus 15 minute de golire, în care traficul deja pornit își poate termina drumul, și se
calculează **separat pe categorii de participanți**:

* **vehiculele motorizate:** timpul mediu de așteptare, ca medie și ca mediană pe seed-uri; pierderea de timp
  (*timeLoss*), adică întârzierea față de mersul cu viteza dorită; întârzierea la intrarea în rețea (*departDelay*);
  durata medie a călătoriei; vehiculele sosite; emisiile de CO₂, după modelul HBEFA din SUMO;
* **bicicliștii**, de tip `vType` bicycle: așteptarea și pierderea de timp medii;
* **pietonii**, din `personinfo`/`walk`: pierderea de timp medie a deplasării;
* **indicatorii generali:** pierderea de timp totală a tuturor participanților, în ore, inclusiv întârzierea la
  intrare; vehiculele rămase în rețea sau neintroduse la final; coada medie de vehicule la Piața Romană și numărul
  mediu de pietoni care așteaptă la trecerile ei, ambele măsurate la fiecare 5 s;
* **semnele unui geamăn greșit**, numărate în timpul simulării și raportate din 2.11 la fiecare strategie: teleportările,
  ciocnirile văzute de SUMO și vehiculele în mișcare care ating pietoni (§ 9.11). Până atunci nu erau urmărite, iar
  teleportările în masă au făcut geamănul să pară că duce traficul real (§ 6.5).

Se raportează media ± abaterea standard pe seed-urile de test 1–10. Abaterea standard arată cât variază rezultatul de
la un seed la altul, iar mediana este valoarea din mijloc a rezultatelor ordonate. La unele strategii și evaluări s-au
folosit doar seed-urile 1–5; în runda din § 9.11, grila de după îngheț are seed-urile 1–3, iar validarea din 4.11,
seed-urile 11–15. Cap. 9 și Anexa A precizează unde. În `docs/rezultate/rezultate.md`, pe 5 seed-uri sunt
calculate rezultatele de duminică și, în zilele lucrătoare, cele pentru Max-Pressure, planul 46/48/12, agentul oficial
și E9.

De reținut: o parte din întârzieri se produce la semafoarele de la marginea zonei modelate, de exemplu pe Str. Știrbei
Vodă și pe Str. Ion Câmpineanu, pe rutele care pornesc de acolo. Aceste întârzieri depind foarte puțin de strategia de
la Piața Romană; de aceea, nu schimbă clasamentul strategiilor, dar măresc valorile absolute. Pe geamănul corectat
(§ 6.5), rutele vehiculelor care trec prin piață pornesc de pe bulevardul fiecărui braț, la 148–566 m de piață, deci nu
mai trec pe acolo; doar ruta de pe Magheru mai trece prin două semafoare, cu program presupus. La semafoarele de la
marginea zonei mai ajunge doar traficul de fond (§ 5.2).

## 8. Interfața om-calculator: dispeceratul

**Pe scurt.** Dispeceratul este consola operatorului: o pagină web din care un om urmărește semaforul din simulare și poate
interveni oricând. Sistemul schimbă singur fazele, iar omul supervizează; de aici principiul de proiectare, **automatizarea
conduce, omul supervizează**. Comenzile ajung doar la semaforul din simulare, nu la semafoarele din piață, iar pagina spune
asta tot timpul. Între bornele M1 și M2, pagina a fost evaluată și reparată cu evaluatori AI. Sondarea cu oameni a avut loc între 3.11, seara,
și sâmbătă, 7.11, la 18:00: persoanele invitate de autor au putut încerca două variante ale dispeceratului, cea de la M1 și cea
reparată după M1. S-au publicat doar rezultatele colegilor, singurul grup în care s-au numărat răspunsurile a cel puțin trei
persoane. Aceste rezultate arată unde se încurcă oamenii, nu care variantă e mai bună: pe amândouă, la fiecare sarcină în care omul
preia comanda sau o dă înapoi calculatorului au reușit câte 2 din 3, față de 3 din 3 la fiecare sarcină în care doar citește
ecranul („Rezultatele sondării”, mai jos). După M2, banda de sus a paginii, care rămâne pe ecran la derulare, urmărește fiecare
comandă, iar în locul imaginii camerei poate sta starea senzorului. Geamănul din această pagină nu are cererea măsurii noi: numărările sunt brute, fără corecții, iar Lascăr Catargiu apare ziua de 2–3 ori sub traficul real pe 25–26.10 și pe 1.11 și de 4–7 ori pe 2–4.11; seara, aproape deloc (§ 5.5).

Scriptul `scripts\7_dashboard.bat` pornește serverul și deschide pagina la `http://localhost:8050`; serverul răspunde doar pe
calculatorul care îl rulează. Cu adresa terminată în `?imagine=0`, pagina pornește fără imaginea camerei, cu starea senzorului
în locul ei, iar cu `?imagine=1`, cu imaginea; spre deosebire de alegerea făcută cu butonul, cea din adresă nu se ține minte.
Demonstrația bornei M3, pornită cu `scripts\M3_demonstratie.bat`, deschide pagina cu `?imagine=0` (§ 11.5). Serverul folosește Flask, o bibliotecă Python pentru
aplicații web, iar pagina este scrisă în HTML și JavaScript simplu, fără un cadru de dezvoltare pentru interfață.

![Dispeceratul, versiunea bornei M2](imagini/dispecerat_m2.jpg)

*Figura 8.1 – Dispeceratul la borna M2, într-o stare fixată, cu date simulate pentru captură. Imaginea camerei lipsește din
figură, fiindcă pagina o arată doar local (§ 4.5). Stânga: ce culoare are semaforul și ce cozi sunt. Mijloc: cine conduce și
cum se schimbă. Dreapta: camera, cozile din ultimele 10 minute și traficul măsurat. Figura se reface cu
`python -m romana.dashboard.capturi --versiune m2 --figura docs/imagini/dispecerat_m2.jpg`.*

**Cine conduce.** Prima întrebare a unui operator este cine schimbă acum culorile. Pagina răspunde în cuvinte, în banda de
sus, care rămâne pe ecran și la derulare, iar modurile sunt împărțite după cine decide:

| Numele de pe ecran | Cine decide | Ce face |
|---|---|---|
| Planul observat | un calculator, singur | un plan fix dedus din cameră, la vârful zilei de luni 26.10: 72/48/3, cu ciclul de ≈138 s, aproape de mediana zilei, ≈133–137 s, măsurată de cameră pe 2–7.11 (§ 6.5) |
| Agent IA | un calculator, singur | agentul oficial alege faza după cozi (§ 7); e antrenat pe simularea veche, pe traficul din 21.10, și neverificat pe geamănul corectat, iar în runda din § 9.11, în care niciun candidat n-a trecut de validare, nu a fost candidat. Pe un calculator fără agentul antrenat, butonul e indisponibil și spune de ce |
| Plan de referință | un calculator, singur | planul fix 36/28/12, ipoteza de la începutul proiectului, cu un ciclu de ≈91 s pe care camera l-a infirmat; păstrat doar pentru comparație (§ 7.4). Pe geamănul corectat, verdele minim lungește etapa de pietoni: cele 12 s devin ≈16 s, cu timpul în care pietonii termină traversarea, de aceea ecranul scrie „≈16 s pietoni” (`bridge/live_twin.py`) |
| Presiune maximă | un calculator, singur | la câteva secunde dă verde direcției cu cele mai lungi cozi (§ 7.4) |
| Comandă manuală | un om, de la acest ecran | omul alege direcția, iar semaforul ajunge la ea singur, pe pași: pietonii își termină traversarea în 6 s, dacă li se închide trecerea, apoi vin galbenul de 3 s și roșul de 2 s. Verdele ales ține cel mult ≈100 s: după verdele maxim de 90 s, semaforul îl încheie la următoarea lui hotărâre, din 5 în 5 s, iar dacă se închide o trecere, vehiculele mai au verde cât pietonii își termină traversarea. Apoi semaforul trece singur, o vreme, pe altă fază și revine la alegerea omului (§ 7.2) |

**Ce s-a schimbat după M2.** Fiecare comandă e urmărită în banda de sus până se aplică, iar o fază aleasă în modul manual, pas
cu pas, până la verdele cerut. Banda spune pasul de acum și cât mai ține, de exemplu „pietonii își termină traversarea, încă
4 s”, apoi peste câte secunde hotărăște semaforul din nou, fiindcă hotărăște la fiecare 5 s, și în cât timp vine verdele cerut;
pe geamănul corectat, cazul cel mai lung are 60 s simulate. Dacă simularea nu citește sau nu aplică o comandă la timp, pagina o
spune limpede, iar după o reîncărcare a paginii urmărirea continuă. Butonul „Ascunde imaginea” pune în locul imaginii camerei
starea senzorului (§ 4.6). Sub imagine, pagina numără acum „participanți urmăriți”, nu „vehicule urmărite”, cum scria pe
ecranele M1 și M2, pentru că urmărirea ține și pietonii; debitul de pietoni e în „numărări/oră”, nu în „persoane/oră”, ca la
M2, fiindcă un pieton se numără o dată pe fiecare trecere (§ 4.4).

**Pentru specialiști.** Termenul unei faze cerute e timpul simulat până la ea, socotit când simularea citește comanda, plus 3 s;
pagina anunță o comandă pe care simularea n-a citit-o în 10 s sau o fază neaplicată până la termen. După o reîncărcare, ultimele
5 comenzi se refac din jurnalul serverului, iar ultima, dacă e mai nouă de 70 s și încă neaplicată, e urmărită mai departe.

**Evaluarea cu evaluatori AI.** Pagina a fost arătată unor evaluatori care nu știau ce defecte cunoaște autorul: 5 evaluatori
euristici, fiecare cu alt rol, un evaluator care parcurge 5 sarcini de operator și un audit de accesibilitate. Rolurile sunt un
specialist în ergonomie, un dispecer de trafic, cineva fără nicio pregătire în trafic, un specialist în erori și stări degradate
și un specialist în vizualizarea datelor și în limba română. Ei au văzut capturi ale paginii în 15 stări fixate, de exemplu cu
camera oprită, cu serverul căzut sau pe telefon, și codul ei. Apoi problemele au fost reunite într-o singură listă, iar câte doi
verificatori independenți au confirmat sau au infirmat fiecare problemă. Severitatea urmează scara lui Nielsen: 1 cosmetică, 2
minoră, 3 majoră și 4 catastrofală. Toți sunt modele de limbaj: găsesc ce se vede și ce se citește în cod, nu ce simte un om, așa
că evaluarea nu înlocuiește sondarea cu oameni. Rezultatele complete, cu dovezi și recomandări, sunt în `docs/rezultate/evaluare_m1/` și
`docs/rezultate/evaluare_m2/`.

| | Versiunea M1 | Prima versiune reparată | A doua versiune reparată |
|---|---|---|---|
| Probleme după reunire | 44 | 50 | 49 |
| Confirmate de verificatori | 44, apoi 43 după recitire | 48 | 45 |
| Confirmate, cu severitatea cel puțin 3 | **9**, apoi **8** după recitire | **1** | **1** |

Fiecare rundă găsește probleme noi, tot mai fine, deci lista nu se golește. Numărul total spune puțin: verificatorii au confirmat aproape tot, inclusiv un artefact. Problema „pe telefon pagina e mai lată
decât ecranul” din versiunea M1 era o greșeală a capturii: fereastra fără cadru a navigatorului are cel puțin 500 px. Am recitit-o
și am infirmat-o abia după ce o confirmaseră amândoi verificatorii. De aceea, contează severitatea, nu numărul, iar o problemă
se crede doar după ce e citită direct. Tot din această cauză, a doua listă nu arată că pagina s-a înrăutățit: e mai lungă fiindcă
pagina are acum mai mult de spus și fiindcă evaluatorii găsesc mereu ceva.

**Ce s-a reparat.** Cele 8 probleme de severitate 3 din versiunea M1 și remedierea lor:

| Problema din versiunea M1 | Ce face pagina acum |
|---|---|
| La căderea serverului, pagina rămâne înghețată și pare activă | o alertă sus spune ce lipsește, iar valorile vechi devin palide și își arată vechimea |
| Debitele rămân prezentate ca actuale după oprirea camerei | tabelul spune de când sunt datele; după un timp, valorile nu mai apar ca actuale |
| Cu geamănul oprit, schema desenează o stare falsă | schema păstrează ultimele valori, palide și cu vechimea lor, în loc de semafoare roșii și cozi zero, iar comenzile se blochează până revine simularea |
| Butonul „Agent AI” indisponibil arată ca unul activ | o comandă care nu se poate da spune motivul, pe ecran, nu doar într-o etichetă care apare la trecerea cu mausul |
| O comandă eșuată nu primește niciun mesaj | comanda e urmărită pe ecran: se trimite, cerere primită, aplicată sau neaplicată, cu un istoric și cu „Reveniți la” |
| Culorile cozilor se confundă cu luminile semaforului | cozile au o singură culoare, cu cifră și bară; semaforul are cercuri cu literele V, G și R; există legendă |
| Modurile nu spun dacă decide calculatorul sau un om | modurile sunt grupate exact după această întrebare și au o frază de explicație |
| Imaginea camerei nu se reconectează după o întrerupere | fluxul se reia singur |

**Proba pe sistemul adevărat.** Capturile folosesc date simulate, deci reparațiile s-au încercat și cu geamănul și serverul reale,
pe 2.11, la prioritate scăzută. Trecerea la planul de referință a fost aplicată în 2,2 s, iar comanda manuală a fost primită în
2,1 s. Verdele cerut vine după galben, roșu și verdele minim al fazei curente; în geamănul corectat, și după ce pietonii
de pe Dacia își primesc verdele și termină traversarea, deci poate întârzia până la 60 s simulate (§ 6.5, § 7.2). Pagina de la
M2 arăta între timp „urmează”, dar aștepta doar 30 s: apoi scria că simularea n-a aplicat încă comanda și o trecea „neaplicată”,
deși geamănul o aplica mai târziu. În timpul probei din 2.11, colectarea a mers cu 5,9 cadre/s. Pe 5.11, între 19:20 și 19:28, proba s-a repetat pe dispeceratul înghețat pe 3.11 (`20c3932`), cu
geamănul pornit de mână, în SUMO-GUI. Preluarea comenzii manuale s-a aplicat în 3 s, verdele cerut pe Dacia, după galben și roșu, în
16,5 s, iar revenirea la „Planul observat”, în 2 s. Cu simularea oprită, alerta a apărut după ≈11 s, iar după repornire pagina și-a
revenit singură, fără reîncărcare, după ≈9 s; acești doi timpi sunt estimați, fără cronometru. Acestea sunt cifrele din benzile
paginilor 3 și 4 ale prezentării bornei M2. Cum a mers colectarea în total, cu pauzele, opririle și reconectările ei, arată fișa
senzorului (§ 4.6). Din seara de 8.11, pagina urmărește o fază cerută pas cu pas, până la termenul calculat din geamăn, cum
scrie mai sus.

**Sondarea cu oameni (`romana.dashboard.sondare`).** O pagină publică, deschisă cu un link, fără instalare: în stânga un ghid care îi
spune persoanei, pas cu pas, ce să facă, de la deschiderea ecranului până la închiderea lui, iar în dreapta dispeceratul. Laptopul care
colectează nu e implicat, fiindcă toată pagina rulează în browserul persoanei; cu sesiuni pe laptop, colectarea ar fi trebuit oprită
în zilele de test, iar o demonstrație în Chrome pe același calculator a coborât rata de la ≈6,0 la ≈4,9 cadre/s. Sunt 4 sarcini pe
fiecare variantă: cine schimbă culorile semaforului, unde e coada cea mai lungă, verde pe Bulevardul Dacia, înapoi la calculator. După
fiecare, ecranul se acoperă și persoana răspunde din ce a văzut. Situațiile sunt simulate, ca toți să aibă aceleași și răspunsul corect
să se știe, deci comenzile nu ajung la geamăn. Reacția la o comandă durează aici 5–16 s, după cât de repede se dă comanda: ≈5–10 s în primele 18 s ale sarcinii, înainte ca pietonii să-și primească verdele, și ≈11–16 s după aceea. În geamănul adevărat poate ajunge la 60 s simulate, fiindcă pietonii de pe Dacia își primesc întâi verdele, apoi au timp să termine traversarea (§ 6.5, § 7.2).
Imaginea camerei e fotografia publicată, cu persoanele și plăcuțele estompate: o cameră în direct ar arăta traficul adevărat, care poate
contrazice schema simulată, așa că persoana poate vedea piața în direct separat, pe site-ul Webcam România. În ambele variante, panoul
camerei spune că e o fotografie fixă și nu mai arată indicatorii de flux, de cadre pe secundă și de „vehicule urmărite”, cum se numeau pe ecranele M1 și M2, fiindcă ar fi falși. Variantele sunt cea de la
borna M1, păstrată neschimbată în `src/romana/dashboard/static/m1`, și cea a bornei M2, păstrată din 8.11 tot neschimbată, în
`src/romana/dashboard/static/m2`, în ordine schimbată de la o persoană la alta:
fixată în link pentru persoanele apropiate, la întâmplare pentru colegi. Varianta M1 păstrează și numele de atunci: planul simulat
pe ambele variante, 72/48/3, apare pe ea ca „Program pe cazuri de trafic (acum: plan fix scurt 12/14/12 s)”. La final, persoana vede
tot ce s-a notat și decide
dacă trimite (§ 4.5). Autorul a parcurs pagina în 10 minute, deci pagina anunță 10–20 de minute. Sondarea e formativă și nesupravegheată: arată ce nu se înțelege pe ecran, nu cât de bun e ecranul în general,
iar locul în care s-a blocat cineva se vede doar din timpi și apăsări. Textul trimis păstrează numărul apăsărilor la fiecare
sarcină; la sarcinile 3 și 4 păstrează și pe ce s-a apăsat: toate apăsările, dacă sunt cel mult 12, altfel primele 4 și ultimele
8, ca linkul spre formular să nu devină prea lung. Se dau doar totaluri pe grup, de forma „x din 4”, persoanele
apropiate autorului separat de colegi, și, separat, prima rundă, fără procente și fără valori p: și patru din patru ar da p = 0,125.
Răspunsurile date pe un ecran mai îngust de 900 px, de obicei de pe telefon, unde ghidul stă deasupra dispeceratului, se numără într-un
grup al lor, cu același prag de cel puțin 3 persoane ca celelalte grupuri.
Pagina nu se deosebește de restul codului: `--pachet` o construiește în `docs/sondare` din sursele din `src/romana/dashboard/static/`, iar GitHub Pages o servește.

**Integritatea răspunsurilor (din 3.11.2026, seara).** În seara invitațiilor s-a văzut o slăbiciune a primei versiuni a paginii:
ea scria răspunsul așteptat lângă unul greșit, iar textul pleacă printr-un formular Google completat dinainte, în care persoana îl
mai poate schimba. Un răspuns se putea deci corecta după ce persoana vedea ce se aștepta. De atunci, pagina, în versiunea v2, nu
mai scrie răspunsurile așteptate. La sfârșitul textului pune un cod de control, de forma „Cod de control: 4F7A-91C-2K”. Codul arată
la citire dacă s-au schimbat răspunsurile, timpii sau apăsările și păstrează, fără să le scrie, care răspunsuri se potriveau cu ce
arăta aplicația; ecranul final spune asta. Butonul „de la capăt” cere confirmarea că răspunde altă persoană și spune că un text
netrimis se șterge. Textul următor din aceeași filă spune „Încercarea: 2”, la fel și după butonul vechi, de pe prima versiune.

Regulile de numărare sunt publice din 3.11, seara, odată cu pagina v2, și se aplică tuturor răspunsurilor:

* un text schimbat după ce l-a scris pagina nu se numără: codul nu se potrivește, lipsește deși textul e de pe pagina nouă sau,
  la prima versiune, apare o corectură vizibilă, ca „X (așteptat: X)” ori un răspuns greșit fără adnotare. Foarte rar, un text cu
  toate răspunsurile bune, scris de o pagină veche rămasă în memoria browserului în minutele de după publicare, poate fi socotit
  schimbat;
* ce e scris în afara textului paginii, de exemplu un salut în același mesaj, se ignoră;
* aceeași trecere, primită de două ori, de exemplu prin formular și pe WhatsApp, se numără o singură dată, din copia cea mai bună;
* o a doua trecere în aceeași filă se numără doar dacă cel care a trimis spune că a răspuns altă persoană; autorul notează doar
  atât, fără nume, fiindcă aceeași persoană nu mai vede ecranele pentru prima oară;
* celelalte dubluri posibile, cu același grup, aceeași ordine și același ecran, se numără, iar autorul nu le scoate după ce le vede
  răspunsurile;
* totalurile se publică o singură dată, după închiderea sondajului și după confirmări, iar un rând cu mai puțin de trei persoane
  nu se publică.

Nu se poate opri cineva care deschide linkul în altă filă sau pe alt dispozitiv și o ia de la capăt. Sarcinile, întrebările și
ordinea lor au rămas aceleași, deci răspunsurile din cele două versiuni se adună. Cine a început pe prima versiune o termină pe ea
dacă nu reîncarcă pagina; după o reîncărcare, continuă pe v2 de la pasul la care a rămas.

*Pentru specialiști.* Codul conține amprenta FNV-1a pe 32 de biți a textului, adus întâi la o formă care nu ține de transport: forma
Unicode NFC, fără rânduri goale, cu spațiile strânse și cu ghilimelele și liniuțele tipografice înlocuite. Urmează biții răspunsurilor
așteptate, amestecați cu o a doua amprentă, care nu apare în text, totul în baza 32, fără literele I, L, O și U. Calculul e același în
`src/romana/dashboard/static/sondare_logica.js` și în `src/romana/dashboard/sondare.py`, iar testele îl verifică pe textele scrise chiar de pagină. Codul nu e o semnătură: cine îl
recalculează după codul public îl poate potrivi, dar o corectură de mână se vede. Rândurile „Ce a încurcat” nu intră în amprentă,
ca persoana să-și poată șterge din formular ce a scris liber, fără să-și piardă răspunsul. Analiza citește doar blocul scris de pagină, de la
rândul versiunii până la cod, cu aceleași reguli pentru spații și rânduri goale ca amprenta. Confirmările stau local, în
`outputs/sondare/confirmari.json`, iar `--rezumat` arată, la „de știut”, ce nu se numără și de ce.

**Rezultatele sondării (7.11.2026).** Sondarea s-a închis sâmbătă, 7.11, la 18:00. Toate textele sosite până atunci sunt complete;
unul nu s-a numărat, după regulile de numărare publicate pe 3.11, de mai sus. Niciun text nu a fost scris într-o fereastră mai
îngustă de 900 px, cum e cea a unui telefon, deci nu există un grup „telefon”. Un text care ar mai sosi după închidere nu se
numără, iar totalurile nu se publică a doua oară. Persoanele apropiate autorului au mai puțin de trei texte numărate, așa că,
după regula din 3.11, despre răspunsurile lor nu se publică nimic. Rămân colegii, cu 3 texte numărate, adică 3 persoane, după
regulile publicate; toate rezultatele de mai jos sunt ale lor. Cele două variante de mai sus se numesc aici „ecranul de la M1”,
dispeceratul prezentat la borna M1, păstrat neschimbat, și „ecranul de acum”, dispeceratul bornei M2, cu reparațiile de după M1,
înghețat pe 3.11, seara (figura 8.1); în fișierul public, ele sunt `m1` și `m2`.

| Sarcina sau întrebarea | Ce se numără | Ecranul de la M1 | Ecranul de acum |
|---|---|---|---|
| Sarcina 1: cine schimbă acum culorile semaforului | răspunsul corect | 3 din 3 | 3 din 3 |
| Sarcina 2: pe care stradă așteaptă cele mai multe mașini | răspunsul corect | 3 din 3 | 3 din 3 |
| Sarcina 3: verde pe Bulevardul Dacia | verdele pe Dacia, cerut până la „Am terminat” | 2 din 3 | 2 din 3 |
| Sarcina 4: înapoi la calculator | la apăsarea pe „Am terminat”, conduce din nou un calculator | 2 din 3 | 2 din 3 |
| După sarcina 3: ce culoare avea semaforul pe Magheru la apăsarea pe „Am terminat” | răspunsul corect | 0 din 3 | 1 din 3 |
| După sarcina 3: „Ați putut vedea în aplicație dacă s-a schimbat ce ați vrut?” | „Da, clar” | 1 din 3 | 2 din 3 |
| După sarcina 4: „Ați putut vedea în aplicație cine schimbă acum culorile?” | „Da, clar” | 1 din 3 | 3 din 3 |
| După fiecare ecran: „Cât de ușor v-a fost să folosiți această variantă?” | „Ușor” sau „Foarte ușor” | 0 din 3 | 1 din 3 |

La sarcini, o apăsare pe „Nu reușesc” nu se numără ca reușită. Întrebările la care au ajuns, pe un ecran, mai puțin de trei
persoane nu apar nici în tabel, nici în fișier, după regula din 3.11.

La primele două sarcini, în care persoana doar citește ecranul, au reușit 3 din 3 pe ambele ecrane; răspunsul corect diferă de la
primul ecran văzut la al doilea, deci nu vine din memorie. La sarcina 3, „verde pe Bulevardul Dacia”, și la sarcina 4, „înapoi la
calculator”, au reușit câte 2 din 3, la fiecare dintre ele și pe fiecare ecran. Sunt singurele sarcini în care omul trebuie să schimbe ceva în aplicație. Pe
ambele ecrane, verdele cerut de om se dă în doi pași: întâi modul manual, apoi direcția, ale cărei butoane apar abia în acest mod.
Aici e primul loc de cercetat într-o rundă nouă de reparații. Întrebarea de după sarcina 3, despre culoarea de pe Magheru, are
doar 0 din 3 răspunsuri corecte pe ecranul de la M1 și 1 din 3 pe cel de acum. Răspunsul corect e însă culoarea din
clipa în care persoana apasă „Am terminat”, iar schimbarea cerută vine abia după 5–16 s, deci întrebarea măsoară și momentul
apăsării, nu doar citirea schemei.

Pe ecranul de acum, „Da, clar” apare mai des la cele două întrebări despre ce arată aplicația. La „cine schimbă acum culorile”, au
răspuns așa 3 din 3, față de 1 din 3 pe ecranul de la M1; la „dacă s-a schimbat ce ați vrut”, 2 din 3, față de 1 din 3. Cele două
întrebări privesc chiar locurile reparate după M1: modurile împărțite după cine decide și comenzile urmărite până la aplicare. La
fel, pe ecranul de acum au răspuns „Ușor” sau „Foarte ușor” 1 din 3, față de 0 din 3 pe cel de la M1. Diferențele nu sunt însă o
dovadă. Ordinea a fost 2 la 1: doi dintre cei 3 au văzut întâi ecranul de la M1, deci pe cel de acum l-au văzut al doilea, după
ce exersaseră aceleași sarcini. La întrebarea de la sfârșit, „Care variantă v-a fost mai ușoară?”, 2 din 3 au ales ecranul de
acum, 1 din 3 pe cel de la M1, iar 0 din 3 au răspuns „La fel”. Nici preferința nu e un argument pentru ecranul de acum: cu 3
persoane, ea nu se poate despărți de ordinea în care au fost văzute ecranele. La „V-a ajutat cineva la sarcini?”, 0 din 3 au
răspuns „Da, la înțelegerea sarcinilor”.

Limitele sunt cele anunțate. Forma „x din 4” din descrierea sondării presupunea un grup de patru persoane; la colegi s-au numărat
3 texte, deci reușitele se dau ca „x din 3”, tot fără procente și fără valori p. Cu trei persoane, un rând „0 din 3” sau „3 din 3”
spune ce a făcut fiecare dintre ele la acel pas, fără să spună cine sunt; nimic nu se atribuie unei persoane, iar răspunsurile
rămân pseudonimizate, nu anonime (§ 4.5). Prima rundă, adică primul ecran văzut, e singura fără efectul exercițiului. Ea apare
doar ca număr de persoane: 2 au început cu ecranul de la M1 și 1 cu cel de acum. Reușitele ei sunt lăsate goale, fiindcă ar arăta
răspunsurile uneia sau a două persoane, iar regula din 3.11 nu publică un rând cu mai puțin de trei persoane. Sondarea rămâne
formativă: arată unde se încurcă oamenii, nu cât de bun e un ecran în general.

**Pentru specialiști.** Comanda `python -m romana.dashboard.sondare --publica` a scris fișierul public,
`docs/rezultate/sondare_m2.csv`, o singură dată, după închidere (Anexa A). Textele salvate local sunt identice, octet cu octet, cu
o a doua copie, luată direct din foaia formularului. O altă instanță a asistentului Claude le-a renumărat cu un program scris de
ea și a obținut aceleași totaluri. Fișierul are terminațiile de rând CRLF pe care le scrie modulul; în depozit, deci și pe
GitHub, Git îl păstrează cu LF, ca pe celelalte fișiere CSV (§ 11.8). Fișierul are doar rândurile colegilor. Pe lângă rândurile
„x din 3”, fișierul are rândurile preferinței și rândul ajutorului, în care coloana `persoane` spune câte dintre cele 3
persoane au ales acel răspuns. Coloana `persoane_prima_runda` spune câte persoane au început cu fiecare ecran, iar `reusite_prima_runda` e goală.
Fișierul nu are coduri, ore, mărimi de ecran, timpi, apăsări sau text liber. Codul scris pe 3.11, dimineața, ar fi pus în
fișierul public, la colegi, și mediana timpului și a apăsărilor pe fiecare sarcină. Pe 7.11, după închidere și înaintea singurei
publicări, codul s-a schimbat, iar medianele au rămas doar local: la trei persoane, mediana e chiar valoarea uneia dintre ele, iar ecranul de acord le spunea participanților că „în proiect apar doar
totaluri, nu ce a răspuns fiecare”. Textele primite nu intră în depozit: stau în foaia formularului și pe calculatorul
autorului, iar, fiindcă le-a citit asistentul Claude, au ajuns și la Anthropic (§ 4.5).

Tabelul următor arată cum respectă dispeceratul cele 10 euristici ale lui Nielsen, regulile practice pentru interfețe ușor de folosit.

| Euristica lui Nielsen[^nielsen] | Cum o aplică dispeceratul |
|---|---|
| Vizibilitatea stării sistemului | în cuvinte, cine conduce, ce direcție are verde și de cât timp; imaginea camerei și indicatorul ei; vechimea datelor; o comandă dată e urmărită în banda de sus până se aplică, iar o fază aleasă de mână, pas cu pas, până la verdele ei; cu imaginea ascunsă, starea senzorului spune, pe verigi, cum merge colectarea |
| Potrivirea cu lumea reală | schema păstrează orientarea reală a brațelor; numele străzilor, nu codurile din simulare; fazele poartă numele efectului lor, de exemplu „Verde pe Magheru și Lascăr Catargiu” |
| Controlul și libertatea utilizatorului | cinci moduri, între care se trece dintr-un clic și o confirmare; `Esc` renunță; „Reveniți la” readuce modul de dinainte; „Ascunde imaginea” scoate imaginea camerei de pe ecran și pune în locul ei starea senzorului, iar măsurarea merge mai departe; adresa cu `?imagine=0` deschide pagina direct așa |
| Consecvență și standarde | modurile au aceleași nume pe butoane, în confirmări și în starea afișată |
| Prevenirea erorilor | o schimbare de mod cere confirmare; în modul manual se alege doar direcția, iar degajarea pietonilor, galbenul și roșul se aplică singure; fazele obișnuite se aleg dintr-un clic, iar cele cu risc de blocare stau separat și cer confirmare |
| Recunoaștere în loc de reamintire | butoanele își explică efectul; fazele apar cu numele complet; legenda stă lângă schemă |
| Flexibilitate și eficiență în utilizare | tastele 1–5 aleg modul, iar cine nu le vrea le poate opri; un operator obișnuit nu trebuie să caute cu mausul |
| Design estetic și minimalist | o singură culoare de accent, iar restul în tonuri neutre; culorile semaforului apar doar pentru a arăta starea |
| Ajutor pentru recunoașterea și remedierea erorilor | alertele spun ce lipsește și ce trebuie pornit; o comandă blocată sau neaplicată își spune motivul; sub fiecare verigă a stării senzorului stă regula după care i se dă starea |
| Ajutor și documentație | butonul „Ajutor” explică modurile, tastele, ce înseamnă culorile, banda de sus și starea senzorului, fără a părăsi pagina |

Sunt respectate și regulile lui Shneiderman[^shneiderman] despre răspunsul informativ al interfeței, încheierea clară
a dialogului, prin confirmare urmată de starea actualizată, și sentimentul utilizatorului că el deține controlul.

Pentru accesibilitate, pagina are contrast ridicat, iar elementul activ se vede clar la folosirea tastaturii. Schema și
graficul au etichete ARIA, pe care le folosesc cititoarele de ecran pentru persoanele cu deficiențe de vedere. Setarea
`prefers-reduced-motion`, prin care utilizatorul cere mai puține animații, nu schimbă nimic: pagina de acum nu are animații;
versiunea M1 își oprea tranzițiile la această cerere. Așezarea urmează lățimea ferestrei:
de la 1 200 px în sus, comanda și schema stau alăturate, sus, iar camera, graficul și debitele, în coloana din dreapta; între 761 și
1 199 px, totul e pe o singură coloană, cu comanda și schema alăturate deasupra; sub 761 px, totul e pe o singură coloană, una sub alta.
Banda de sus rămâne pe ecran la derulare, iar de la 1 200 px, și coloana comenzii rămâne sub ea, cât încape în fereastră; sub
761 px, banda e mai scurtă, iar cine conduce se vede pe butonul apăsat, „● acum”, și sub fază. Cititorul de ecran nu rostește
starea senzorului la fiecare reîmprospătare: anunță doar o verigă care trece la „problemă”. Subsolul arată permanent atribuirile cerute pentru OSM,
Webcam România și SUMO, precum și legătura către codul sursă, publicat sub licența AGPL-3.0.

## 9. Rezultate

> **Corectură, 2.11.2026.** Concluziile care folosesc capacitatea calibrată, inclusiv cele despre planul 12/14/12, stau pe geamănul cu
> coliziuni și teleportări (§ 6.5), deci nu mai sunt valabile. Textul rămâne ca istoric al lucrului.

**Pe scurt.** Acest capitol arată, în cifre, cât timp câștigă sau pierd participanții la trafic cu fiecare fel de a
comanda semaforul. Toate comparațiile se fac în simulare, pe trafic reconstituit din datele camerei. Primele rezultate,
din § 9.2–9.4, sunt obținute pe calibrările anterioare, adică pe estimările mai vechi ale traficului. Evaluarea este
reluată în § 9.8–9.10 pe cererea calibrată, o estimare corectată a traficului, iar § 9.10 prezintă testul final de
atunci, câștigat de planul fix 12/14/12. Acel rezultat, cu tot cu câștigul de −7%, a fost retras pe 2.11, fiindcă
geamănul avea coliziuni și teleportări în masă (§ 6.5). Runda nouă, din § 9.11, s-a făcut pe geamănul corectat, cu
măsurile înghețate pe 3.11. Poarta, care compară geamănul cu camera oră cu oră, trece pe 8 din cele 12 ore comparate la
îngheț, din 25 și 26.10 și din 1 și 2.11, dar pe 0 din 5 ore pe 3.11 și pe 0 din 4 ore pe 4.11, ziua de validare.
Validarea a fost deci doar descriptivă, iar niciun candidat n-a trecut de ea. Runda s-a încheiat pe 5.11 fără un program
nou: în geamăn rămâne planul observat, 72/48/3 (`docs/rezultate/cor_decizie_2026-11-04.json`). Asta nu arată că planul
observat e cel mai bun, ci doar că geamănul nu a putut judeca.

### 9.1 Cum se evaluează

Fiecare strategie comandă semaforul în aceleași ore de trafic simulate, de mai multe ori. La final se adună timpul
pierdut de toți participanții și se compară cu cel obținut cu planul fix de referință. Strategiile se aleg pe un grup de
simulări și se verifică pe altul, iar fiecare diferență trece prin teste statistice.

**Scenariile.** Un scenariu reconstituie o oră de trafic din numărătorile camerei (§ 5.4). Evaluarea folosește 10
scenarii din zilele lucrătoare 21–22.10.2026: ora cea mai liniștită, prânzul, dimineața și vârful, plus variante de
sensibilitate, notate ×0,8 și ×1,2, cu traficul de vehicule înmulțit cu 0,8, respectiv cu 1,2. Se adaugă 5 scenarii din
duminica 25.10.2026, zi pe care nicio strategie nu a fost antrenată sau aleasă. Simularea fiecărui scenariu cuprinde ora
de cerere, în care participanții pornesc la drum, plus 15 minute de golire, în care cei rămași își pot încheia
deplasarea.

**Cele două calibrări ale cererii.** Cererea este traficul care vrea să treacă prin piață, iar calibrarea ei înseamnă
estimarea acestui trafic din numărătorile camerei. Camera nu numără perfect, de aceea cererea a fost estimată în două
feluri (§ 5.1). Marginea de sus folosește media dintre intrările și ieșirile măsurate, iar marginea de jos folosește doar
intrările. La vremea primelor evaluări se credea că adevărul se află între ele, așa că rezultatele sunt raportate pentru
ambele. Mai târziu, traficul din două clipuri video de câte 3 minute a fost numărat atent, cadru cu cadru: aceasta este
numărătoarea de referință (§ 4.3). Ea și înregistrarea continuă din 26.10 (§ 4.6) au arătat că cererea reală e de circa
două ori marginea de sus și de trei ori marginea de jos. De aceea, evaluarea a fost reluată pe cererea calibrată,
corectată cu ajutorul numărătorii de referință:

- reevaluarea este în § 9.8–9.9; § 9.9 folosește cele 6 scenarii din luni 26.10, zi care a servit apoi ca zi de
  validare;
- testul final, pe cele 6 scenarii din miercuri 28.10, și confirmarea, pe cele 7 din joi 29.10, sunt în § 9.10; fiecare
  zi este simulată atât cu participanți disciplinați, cât și cu participanți indisciplinați.

La testul final și la confirmare, decizia s-a luat pe baza pierderii totale exprimate în ore, față de strategia în vigoare
atunci, programul realist (§ 9.4). Rezultatele lor au fost retrase pe 2.11, fiindcă geamănul avea coliziuni și
teleportări în masă (§ 6.5). Zilele de validare și de test din noiembrie se judecă după reguli noi, scrise înainte de a le vedea:
o oră intră în decizie doar dacă geamănul corectat trece poarta, adică verificarea față de cameră pe acea oră, iar un
candidat trebuie să bată și planul observat, și semaforul rejucat. Pe ziua de validare, 4.11, poarta a trecut pe 0 din
4 ore, deci validarea a fost doar descriptivă: niciun candidat nu a trecut, runda s-a încheiat fără un program nou, iar
planul observat, 72/48/3, rămâne (§ 9.11).

**Ce se măsoară.** Indicatorul principal este pierderea totală de timp: suma timpului pierdut de toți participanții față
de un drum făcut tot timpul cu viteza dorită, fără opriri și fără încetiniri. Intră în calcul vehiculele, bicicliștii și
pietonii; la vehicule se adaugă și timpul cât așteaptă să poată intra în rețeaua de străzi simulată. Rezultatul fiecărei
strategii se exprimă ca diferență procentuală față de planul fix de referință, 36/28/12 s. Acest plan are trei faze:
trei grupuri de direcții care primesc verde pe rând. Notația dă secundele de verde ale fiecărei faze la o trecere prin
toate fazele, adică într-un ciclu: 36 s pentru axa nord–sud, 28 s pentru axa est–vest și 12 s pentru pietoni. La fel se
citesc și celelalte planuri fixe, de exemplu 46/48/12. Planul de referință este ipoteza proiectului pentru programul
actual al semaforului (§ 6.3, § 10). Camera a infirmat ipoteza pe 2.11: ziua, semaforul real are un ciclu de ≈125–155 s,
nu de ≈91 s. Măsurarea programului real pe 2–5.11 dă același rezultat: mediana zilei e de ≈135–137 s, iar un ciclu de
≈91 s nu apare (§ 6.5). Dacă nu se spune altfel, procentele din acest capitol sunt deci față de o ipoteză, nu față de
semaforul de pe stradă. Când textul spune simplu „planul fix” sau „planul fix actual”, „actual” înseamnă „presupus
actual la data scrierii”, iar vorba e despre acest plan. Un procent negativ înseamnă timp câștigat față de el, iar unul pozitiv, timp pierdut în plus.

**Strategiile comparate.** Strategiile clasice sunt descrise în § 7.4. Planul Webster este tot un plan fix, dar cu
duratele calculate după formula lui Webster din debitele de trafic, adică din numărul de vehicule care trec pe oră.
Actuated este semaforul acționat de trafic: el prelungește verdele cât timp detectoarele văd vehicule venind.
Max-Pressure alege la fiecare decizie faza cu cea mai mare diferență dintre cozile dinaintea intersecției și cele de
după ea. Agenții AI sunt programe antrenate cu metoda învățării prin întărire: au învățat, din multe încercări în
simulare, ce fază să aleagă și cât s-o țină (§ 7). În afară de agentul oficial, `ppo_romana`, agenții poartă numele
experimentului din care provin, de la E1 la E15 (§ 9.5).

**Alegere pe unele simulări, verificare pe altele.** Într-o simulare, felul în care conduc șoferii este tras la sorți,
iar momentele în care pleacă participanții sunt fixate în scenariu. Fiecare simulare depinde de un seed, valoarea care pornește generatorul de
numere aleatoare al simulării. Pentru ca o strategie să nu fie aleasă doar pentru că a avut noroc pe anumite simulări,
alegerea și raportarea folosesc seed-uri diferite:

- toate alegerile, adică ce agent, ce plan și ce strategie pe fiecare tip de trafic, s-au făcut pe seed-urile de
  validare 11–15; la primele alegeri, inclusiv la agentul oficial și la E3, s-au folosit seed-urile 11–13;
- rezultatele raportate sunt pe seed-urile de test 1–10, nefolosite la alegere, sau doar pe 1–5, unde se precizează.

Singura excepție este componenta pentru trafic greu a marginii de sus. Validarea a ales agentul E7, dar planul fix
46/48/12, mai simplu, a fost preferat după ce cele două variante s-au dovedit echivalente pe seed-urile de test 1–5
(p = 0,32, § 9.5).

**Cum se decide dacă o diferență e reală.** Strategiile se compară pe perechi de simulări: același scenariu și același
seed, o dată cu o strategie și o dată cu cealaltă. Pe aceste perechi se aplică două teste statistice. Testul t pe
perechi ține seama de media diferențelor și de cât de mult variază ele de la o pereche la alta. Testul Wilcoxon
folosește doar semnul diferențelor și ordinea lor după mărime, așa că o valoare extremă îl influențează puțin.
Fiecare test dă o valoare p, care arată cât de probabil ar fi să apară doar din întâmplare o diferență cel puțin la fel
de mare, dacă strategiile ar fi de fapt la fel de bune. Cu cât p e mai mic, cu atât rezultatul e mai greu de pus pe
seama întâmplării; sub 0,05, diferența se numește semnificativă. În tabele, coloana „p (t / Wilcoxon)” dă ambele
valori, în această ordine; la fel se citesc și perechile de valori p din text. Expresia „mai bun în k din n” numără
simulările în care strategia are o pierdere totală mai mică decât strategia cu care este comparată.

**Pentru specialiști.** Ceilalți indicatori din § 7.5 sunt publicați doar pentru evaluările pe marginile de jos și de
sus (§ 9.2–9.3). Pentru marginea de jos se găsesc în `docs/rezultate/rezultate.md` și `rezultate_brute.csv`, iar pentru
marginea de sus în `rezultate_brute_marginea_de_sus.csv`. Fișierele din § 9.4 și § 9.8–9.10 conțin doar pierderea
totală; cele din 28 și 29.10 o dau și pe tipuri de participanți.

### 9.2 Rezultatul principal pe calibrările anterioare: programul pe tipuri de trafic

Pe calibrările din 21–22.10, geamănul digital, adică copia simulată a pieței construită în programul de simulare SUMO,
avea capacitatea implicită: cu parametrii impliciți ai șoferilor, el putea trece mult mai puțin trafic decât trece piața
în realitate (§ 6.4); pe 2.11 s-a văzut că lipsa de capacitate venea din felul în care erau construite rutele,
benzile și legăturile geamănului, nu din parametrii șoferilor (§ 6.5). În aceste condiții și cu participanți
disciplinați, niciun agent AI folosit singur, la toate tipurile de trafic, nu era constant mai bun decât un plan fix bine reglat (§ 9.5). Soluția găsită atunci a fost un
**program pe tipuri de trafic**. Traficul se împarte în trei tipuri: lejer, moderat și greu. Pentru fiecare tip se
folosește strategia care a fost cea mai bună pe datele de validare, iar când două strategii dau practic același
rezultat, se alege cea mai simplă. Toate componentele se pot aplica pe automatul de semafor existent, pentru că se
schimbă doar programul lui.

Pe cererea calibrată și pe o zi nouă, cu capacitatea calibrată, agentul E13 folosit singur părea să bată constant planul
de referință (§ 9.9), iar planul scurt 12/14/12 ieșea la egalitate cu E13 (§ 9.9–9.10). Ambele rezultate au fost
retrase pe 2.11: geamănul „calibrat” părea să facă față traficului real doar din cauza coliziunilor și a teleportărilor
în masă (§ 6.5). În ziua de validare, 4.11, geamănul corectat nu a trecut poarta pe nicio oră, deci validarea a fost
doar descriptivă și niciun candidat nu a trecut. Rămâne planul observat, 72/48/3, dedus din cameră; asta nu arată că e
cel mai bun, ci doar că geamănul nu a putut judeca (§ 9.11).

Programul este integrat în geamănul digital, în `bridge/live_twin.py`, și în dispecerat, interfața prin care operatorul
urmărește și comandă semaforul (§ 8). În dispeceratul de la borna M1, modul de control se numea „Program pe cazuri de
trafic”; din 2.11, butonul lui se numește „Planul observat” (§ 8). Când varianta aleasă are mai multe strategii,
programul trece automat de la una la alta după debitul măsurat de cameră, calculat ca medie între intrările și ieșirile
numărate; un plan fix, cum e planul observat, nu comută (§ 5.5).
Pragurile dintre tipurile de trafic au fost la început 1 300 și 2 000 veh/h (vehicule pe oră), iar de pe 28.10 sunt
2 400 și 4 100 veh/h (§ 9.9). Până pe 29.10, varianta implicită a fost „programul realist” (§ 9.4). Între 29.10 și 2.11 a fost
planul fix 12/14/12, ales de testul final (§ 9.10), retras între timp. Din 2.11 este planul observat (§ 6.5).

Tabelul arată ce strategie folosește programul la fiecare tip de trafic, pentru fiecare calibrare:

| Calibrarea cererii | Trafic lejer | Trafic moderat (prânz) | Trafic greu (vârf, dimineață) |
|---|---|---|---|
| marginea de sus (media dintre intrări și ieșiri) | agentul E9 (`ppo_romana_lejer`) | agentul E3 (`ppo_romana_zn3`) | planul fix 46/48/12 s |
| marginea de jos (doar intrările) | actuated*, la egalitate cu agentul oficial, dar mai simplu | agentul E3 | planul fix actual, cu care toate alternativele au fost la egalitate |
| **condiții reale: participanți indisciplinați** (§ 9.4) – „programul realist” | agentul oficial (`ppo_romana`) | agentul E3 | agentul E3 |

\* Strategia actuated are nevoie să detecteze vehiculele la intrări, fie cu bucle inductive montate în carosabil, fie cu
o cameră, ca în acest proiect.

**Zilele lucrătoare, marginea de sus.** Fiecare strategie are 100 de simulări: 10 scenarii × 10 seed-uri de test.
Tabelul dă media pe scenarii a diferenței față de planul fix actual:

| Program pe tipuri de trafic | Actuated | Webster | Agent E3 | Plan 46/48/12 | Agent E7 | Agent E9 | Agent oficial | Max-Pressure |
|---|---|---|---|---|---|---|---|---|
| **−6,9%** | −2,8% | +0,2% | +0,8% | +1,4% | +1,9% | +3,4% | +5,4% | +11,3% |

Programul este semnificativ mai bun decât planul fix: diferența este de −6,9%, cu p = 0,0003 la testul t și 0,00002 la
testul Wilcoxon, iar programul e mai bun în 79 din 100 de simulări. Este semnificativ mai bun și decât actuated, cea mai
bună metodă clasică: față de ea, diferența este de −3,2% (p = 0,04 / 0,002), iar programul e mai bun în 68 din 100 de
simulări. Pe scenarii, diferența este de −6,8…−11,0% la orele liniștite, −5,1% la prânz și −4,4…−12,9% la vârf.
Dimineața este singurul scenariu în care programul pierde: +12,6%.

**Zilele lucrătoare, marginea de jos.** Programul, planul fix, actuated și agentul E3 au câte 100 de simulări, pe
seed-urile de test 1–10, iar celelalte strategii câte 50, pe seed-urile 1–5:

| Program pe tipuri de trafic | Actuated | Agent E3 | Agent E9 | Agent oficial | Plan 46/48/12 | Max-Pressure |
|---|---|---|---|---|---|---|
| **−1,5%** | −0,3% | +0,7% | +2,6% | +3,8% | +6,4% | +22,0% |

Aici traficul este mai mic: vârful are ≈1 650 veh/h, în loc de ≈2 500. La un asemenea vârf, planul fix actual este greu
de bătut, așa că programul îl păstrează. Programul câștigă constant la trafic lejer, cu −6,0…−7,3%. În cele 50 de
simulări în care diferă de planul fix, adică la trafic lejer și la prânz, este mai bun în 44 (Wilcoxon p = 0,0003). La
prânz însă, rezultatele agentului E3 sunt instabile pe această calibrare: −2,3% pe seed-urile 1–5, dar +11,7% în medie
pe seed-urile 1–10. De aceea, câștigul mediu al programului scade la −1,5%.

**Ce înseamnă.** Câștigul programului depinde de cât trafic este de fapt în piață și de cât de disciplinați sunt
participanții. El reprezintă ≈1,5% din timpul pierdut de toți participanții la marginea de jos, ≈7% la marginea de sus
și ≈16% cu participanți indisciplinați (§ 9.4), fără nicio lucrare pe stradă. Într-o oră aglomerată se pierd în geamăn
câteva sute de ore-om, deci câștigul ar fi însemnat zeci de ore-om în fiecare oră aglomerată. Cifra nu spune însă ce
s-ar câștiga pe stradă: procentele sunt față de planul de referință, o ipoteză pe care camera a infirmat-o, iar rutele
și legăturile dintre benzi ale geamănului de atunci s-au corectat abia pe 2.11 (§ 6.5).

### 9.3 Generalizarea pe o zi de weekend (duminică, 25.10.2026)

Generalizarea înseamnă aici cât de bine se descurcă strategiile pe o zi pe care nu au fost antrenate sau alese. Duminica
25.10 este o astfel de zi și are, în plus, alt tipar de trafic decât zilele lucrătoare: traficul e mic până la 08:30,
iar vârful vine la 15:30–16:30 (§ 5.4). Datele de atunci, folosite mai jos, se opresc înainte de acest vârf.

- **Marginea de sus.** Datele merg până la 11:30, iar evaluarea are 5 scenarii × 10 seed-uri. Programul obține −5,2%
  față de planul fix (p = 0,03) și este mai bun în 43 din 50 de simulări. Este semnificativ mai bun și decât actuated
  (p = 0,0006). Toți agenții AI folosiți singuri au bătut planul fix, inclusiv la vârful datelor de atunci, 09:30–10:30:
  E9 cu −6,5%, E3 cu −4,9% în medie și −7,2% la vârf, iar agentul oficial cu −4,9%. Celelalte strategii au obținut:
  Max-Pressure −4,5%, actuated −1,5%, Webster +0,4% și planul 46/48/12 +5,3%.
- **Marginea de jos.** Datele merg până la 13:50, iar evaluarea are 5 scenarii × 5 seed-uri. Vârful datelor de atunci,
  11:45–12:45, are ≈3 480 veh/h la intrări, mai mult decât orice scenariu de antrenare. Programul folosește regula
  aleasă pe validare pentru această calibrare și obține −4,5% față de planul fix. Este mai bun în toate cele 15
  simulări în care diferă de planul fix (Wilcoxon p = 0,0001). Aici, cea mai bună strategie a fost actuated: −6,2%,
  mai bună în 22 din 25 de simulări. Agenții AI au câștigat doar la trafic lejer și în dimineața de duminică, cu
  −1…−8%. La vârful foarte mare au fost la egalitate cu planul fix sau mai slabi. În medie, agentul oficial a obținut
  −2,0%, E3 −0,4% și E9 −0,3%.

**Concluzie.** Programul pe tipuri de trafic rămâne mai bun decât planul fix și pe o zi nouă, la ambele calibrări.
Planul fix 46/48/12, reglat pe vârfurile din zilele lucrătoare, nu se potrivește vârfului de duminică. Agenții AI se
descurcă bine pe o zi nouă când volumele de trafic sunt apropiate de cele de la antrenare, ca la marginea de sus. Nu se
descurcă însă bine la un vârf mult mai mare decât cele văzute la antrenare, ca la marginea de jos. Acesta este un
argument pentru reantrenarea periodică a agenților pe date noi.

### 9.4 Robustețea la participanți indisciplinați

Autorul a observat că șoferii și pietonii din București nu respectă întotdeauna regulile. Testul de robustețe verifică
cum se descurcă strategiile în aceste condiții. El folosește aceleași scenarii, calibrate pe marginea de jos, dar cu
tipurile de participanți din `sumo/demand/vtypes_indisciplinat.add.xml`:

- vehiculele intră în intersecție chiar dacă nu o pot elibera, după doar 1 s de așteptare, și o blochează; trec pe roșu
  în primele 2 s de roșu și pe galben târziu; schimbă banda agresiv;
- pietonii traversează pe roșu în primele 5 s de roșu și uneori ignoră vehiculele.

Testul are 5 scenarii × 10 seed-uri de test: prânzul și vârful din 21.10, dimineața, noaptea și vârful din 22.10
(`docs/rezultate/robustete_indisciplinat*.csv`). Indisciplina schimbă mult traficul. Cu planul fix, timpul pierdut crește
cu +31% la vârful din 21.10, cu +16% la cel din 22.10 și cu +7% dimineața, pentru că intersecția blocată și trecerile pe
roșu strică ritmul fazelor. La prânz și noaptea, timpul pierdut scade cu ≈15%: când intersecția nu e aglomerată până la
limita ei, trecerile pe roșu „câștigă” timp. Aceste comparații cu participanții disciplinați sunt făcute pe seed-urile
1–5.

Tabelul compară fiecare strategie cu planul fix, în aceleași condiții de indisciplină:

| Strategie | Medie | Vârf 21.10 | Vârf 22.10 | Dimineața | Prânz | Noaptea | Mai bun în | p (t / Wilcoxon) |
|---|---|---|---|---|---|---|---|---|
| **Agent E3** | **−14,1%** | −14,8% | −28,0% | −20,0% | −3,1% | −4,6% | 40 / 50 | 0,00001 / <0,00001 |
| **Agent E9** | **−9,9%** | −6,9% | −24,8% | −6,4% | −4,1% | −7,3% | 37 / 50 | 0,003 / 0,002 |
| Agent oficial | −0,1% | +5,2% | −11,0% | +3,5% | +15,7% | −14,1% | 30 / 50 | 0,99 (nesemnificativ) |
| Actuated | +6,4% | +0,4% | +4,0% | +7,4% | +30,6% | −10,6% | 25 / 50 | 0,23 (nesemnificativ) |

**Cu participanți indisciplinați, ca în realitate în București, specialiștii AI E3 și E9 sunt mult mai buni decât planul
fix pe această calibrare**, mai ales la vârf, unde diferența ajunge până la −28%. Ei au fost antrenați cu participanți
disciplinați, dar observă cozile reale și se adaptează din mers când intersecția se blochează, ceea ce un plan fix nu
poate face. Pe cererea calibrată însă, avantajul lui E9 scade, iar al lui E3 dispare (§ 9.8–9.10).

Programul pe tipuri de trafic ales pentru marginea de jos păstrează planul fix la vârf, așa că aici câștigă doar −2,7%,
nesemnificativ; pe seed-urile 1–5, câștigul era −1,5%. De aceea, pentru condițiile reale a fost ales un **„program
realist”**. Alegerea s-a făcut pe validare, adică pe seed-urile 11–15 ale acelorași scenarii cu participanți
indisciplinați (`docs/rezultate/validare_indisciplinat.csv`). Programul realist folosește:

- agentul oficial la trafic lejer, cu −13,3% pe validare;
- agentul E3 la trafic moderat, cu −3,5%, și la trafic greu, cu −19,4%; pentru comparație, planul 46/48/12 ajunge la
  +21% la traficul greu și la +22% pe toată validarea.

Rezultatele pe seed-urile de test 1–10:

| Program realist față de | Diferență medie | p (t / Wilcoxon) | Mai bun în |
|---|---|---|---|
| planul fix actual | **−16,0%**: noaptea −14,1%, prânz −3,1%, vârfuri −14,8% / −28,0%, dimineața −20,0% | 0,00001 / 0,000002 | **42 / 50** |
| actuated | **−18,4%** | <0,000001 / <0,000001 | 46 / 50 |

Până pe 29.10, programul realist a fost varianta implicită a modului „Program pe cazuri de trafic” din geamănul care
rulează în timp real. Setarea corespunzătoare era `VARIANTA_PROGRAM = "realist"`, în `bridge/live_twin.py`. Pe 29.10
l-a înlocuit câștigătorul testului din 28.10, planul fix 12/14/12 (§ 9.10), retras pe 2.11; de atunci, geamănul
pornește pe planul observat, 72/48/3 (§ 5.5, § 6.5). Varianta pentru participanți disciplinați
rămâne disponibilă sub numele `"marginea_sus"`.

**Programul realist pe duminică.** Testul s-a repetat pe duminica 25.10, cu participanți indisciplinați,
pe 5 scenarii × 10 seed-uri de test (`docs/rezultate/robustete_indisciplinat_duminica*.csv`). Strategiile nu
văzuseră această zi nici la antrenare, nici la alegere. Dimineața de duminică este tratată aici ca trafic lejer.
Programul realist obține −4,4% față de planul fix și este mai bun în 40 din 50 de simulări. Testul Wilcoxon arată o
diferență semnificativă (p = 0,035), dar testul t, sensibil la valorile extreme, nu (p = 0,53). Programul câștigă la
trafic lejer și dimineața, cu −9…−10%, și la vârf, cu −5,8%. La vârful ×1,2 însă, cu ≈4 200 veh/h, peste orice scenariu
de antrenare, agentul E3 pierde: +11,4%. Aici, cea mai bună strategie a fost agentul oficial folosit singur: −7,9% în
medie, mai bun în 44 din 50 de simulări (Wilcoxon p = 0,0001), cu −9,7% la vârf și −2,5% la vârful ×1,2. Față de
actuated, programul realist este la egalitate: −0,7%, nesemnificativ. Pe primele 5 seed-uri, rezultatul fusese −4,3%,
nesemnificativ (p = 0,37). Concluzia: când tiparul traficului diferă mult de cel de la antrenare, agenții trebuie
reantrenați pe date noi (§ 10).

*Notă de verificare:* prima rulare a testului a dat rezultate identice cu cele ale scenariilor normale. Cauza era
funcția care pornește simularea: ea înlocuia tipurile de participanți din scenariu cu cele standard. Defectul din
`control/env.py` a fost corectat pe 25.10.2026. Rezultatele de mai sus sunt din rularea corectată, iar rezultatele
scenariilor normale nu sunt afectate, lucru verificat.

### 9.5 Drumul până la rezultat: ce nu a mers

Rezultatul la care a dus acest drum, planul 12/14/12 din § 9.10, a fost retras pe 2.11 (§ 6.5), iar pe geamănul
corectat validarea din 4.11 a fost doar descriptivă, fiindcă poarta nu a trecut pe nicio oră, deci rămâne planul
observat (§ 9.11). Rezultatul de atunci nu venise din prima încercare. Tabelul de mai jos adună încercările care
nu au mers, dar și cele câteva care au fost păstrate. Experimentele cu agenți AI sunt numerotate E1–E15, în ordinea în care au fost făcute.
Dacă nu se spune altfel, fiecare procent arată cu cât se schimbă pierderea totală de timp a tuturor participanților față
de planul fix de referință: un procent negativ înseamnă mai puțin timp pierdut, deci o strategie mai bună. „Pe validare”
înseamnă pe seed-urile folosite la alegere, iar „pe test”, pe seed-uri nefolosite la alegere.

Tabelul folosește câțiva termeni din antrenarea agenților. A **reantrena** un agent înseamnă a-i continua antrenarea, de
regulă pe alte scenarii. Un agent antrenat **de la zero** pornește fără nicio experiență. Antrenarea se măsoară în
**pași**, adică în decizii luate în simulare. Pe parcurs se salvează **puncte intermediare**: versiuni ale agentului care
pot fi alese în locul celei finale. **Rata de învățare** arată cât de mult își schimbă agentul comportamentul la fiecare
actualizare. Un **specialist** este un agent antrenat pentru un singur tip de trafic.

| Încercarea | Rezultatul | Concluzia |
|---|---|---|
| Agentul oficial `ppo_romana`, evaluat pe 22.10 în 300 de simulări, pe datele numărate cu zonele inițiale ale camerei | −4,6% față de planul fix | rezultatul era construit pe zone greșite (§ 12.1, etapa 5) |
| Același agent, pe datele renumărate pe 23.10 cu zonele corecte | +5,2%: câștig la trafic lejer, pierdere la vârf | rezultatul nu se confirmă pe datele corecte |
| Trei variante ale agentului: v2 vede și cozile din amonte, adică de pe străzile care duc spre piață; v3 imită întâi un plan fix, apoi continuă să învețe prin întărire, cu algoritmul PPO; E1 cântărește mai mult urmările pe termen lung ale deciziilor | toate mai slabe decât v1, agentul oficial din primul rând al tabelului | negative |
| Coridorul: un singur agent comandă semafoarele pieței și ale celor 4 intersecții vecine | +35,4% | negativ; ar fi nevoie de agenți descentralizați, câte unul pentru fiecare intersecție, de tipul MPLight[^mplight] sau CoLight[^colight], și de mult mai mult timp de antrenare |
| E2 – reantrenare scurtă pe datele noi | +19,8% pe validare, față de +11,3% la agentul vechi | negativ |
| E3 – reantrenare cu o rată de învățare mică | în medie, cam la fel ca agentul vechi, dar −17,6% la prânz | **adoptat pentru traficul moderat** |
| E4 – agent nou, antrenat de la zero 1 000 000 de pași | +11,6…+12,9% pe validare | fără câștig: limita unui singur agent pentru toate tipurile de trafic |
| E5 – specialist pentru trafic greu, obținut prin reantrenare | +9,4% pe validare | negativ |
| E6 și E7 – specialiști pentru trafic greu, care pornesc de la planul 46/48/12 | E7: −9,3% pe validare, −7,0% pe test | echivalent statistic cu planul 46/48/12 (p = 0,32), deci se păstrează planul, mai simplu |
| E8 – specialist pentru trafic moderat | mai slab decât E3 | negativ |
| E9 – specialist pentru trafic lejer | pe test, la trafic lejer: −9,5%, față de −9,0% la agentul oficial; p = 0,001 | **adoptat pentru traficul lejer** în programul pentru marginea de sus |
| E10 – experimentul din 26.10: E3 a mai fost antrenat 200 000 de pași, cu rata de învățare 3·10⁻⁵, pe scenariile cu participanți indisciplinați | −6,6% pe validare, față de −13,4% la E3. Punctele intermediare, salvate la fiecare 25 000 de pași, variază între −5,4% și +7,2% (`docs/rezultate/validare_indisciplinat_e10.csv`) | negativ: reantrenarea strică felul în care decide E3, în loc să-l îmbunătățească, deci E3 rămâne |
| E11 – experimentul din 26.10: un agent nou, antrenat de la zero 1 000 000 de pași pe scenariile de zi lucrătoare, cu participanți disciplinați și indisciplinați amestecați | Cel mai bun punct intermediar, cel de la 500 000 de pași, obține −6,9% pe validarea cu participanți indisciplinați, față de −13,4% la E3. Modelul final ajunge la +4,6% (`docs/rezultate/validare_indisciplinat_e11.csv`) | negativ: nici antrenarea de la zero pe ambele comportamente nu ajunge la nivelul lui E3 |
| E12 și E13 – în noaptea de 26–27.10, E3 și agentul oficial au mai fost antrenați câte 300 000 de pași, cu rata de învățare 3·10⁻⁵, pe cele 20 de scenarii calibrate de zi lucrătoare din 21–22.10, cu participanți disciplinați și indisciplinați. Din E3 a rezultat E12, iar din agentul oficial, E13. Punctele intermediare de la +100 000 și +200 000 de pași au intrat și ele în alegere | Validarea s-a făcut cu participanți indisciplinați, pe seed-urile 11–15, cu medii pe perechi, ca în § 9.8–9.9. E12 obține −5,9% la punctul de la +100 000 de pași (`cand_romana_cal3_100k`), față de −2,3% la E3, dar modelul final ajunge la +1,7%. E13, adică modelul final `ppo_romana_cal`, obține −9,3%, față de −10,1% la agentul oficial, cel mai bun în validare. Cu media pe scenarii, convenția din `validare_calibrat_alegere.json` și din rândurile E10 și E11, cele cinci valori devin, în aceeași ordine, −6,3% / −3,0% / +1,1% / −9,6% / −10,5%. Pe test, adică pe seed-urile 1–5, s-a rulat programul realist cu fiecare componentă înlocuită cu varianta ei reantrenată: E13 în locul agentului oficial la trafic lejer și E12 în locul lui E3 în rest. Programul a fost fixat înainte de rulare. Față de planul fix, el obține −6,7% cu participanți indisciplinați și −3,9% cu disciplinați; e mai bun în 40 din 50 de perechi, respectiv în 37 din 50. Față de programul realist, diferența e de +1,0% (p = 0,86 / 0,59) și, respectiv, de −0,5% (p = 0,22 / 0,25). Fișierele: `validare_calibrat.csv`, `test_reantrenare_*.csv` | echivalent statistic cu programul realist, deci programul realist rămâne. Scenariile de antrenare din 21–22.10 sunt subnumărate (§ 4.6), iar geamănul avea capacitatea implicită (§ 6.4), așa că reantrenarea pe ele nu poate repara vârfurile |
| E14 – în noaptea de 27–28.10, E13 a mai fost antrenat 300 000 de pași, cu rata de învățare 3·10⁻⁵, pe cele 12 scenarii de luni 26.10 cu capacitatea calibrată, cu participanți disciplinați și indisciplinați. Punctele intermediare de la +100 000 și +200 000 de pași au intrat și ele în alegere | Validarea s-a făcut pe ziua de luni, pe seed-urile 11–15, cu ambele comportamente, adică pe 60 de perechi. Era aceeași zi ca la antrenare, deci testul îi era favorabil lui E14. Modelul final obține −6,3% față de planul fix, în timp ce E13 obține −7,9%, iar agentul oficial −7,6%. Direct față de E13, E14 iese mai slab, cu +2,2%, și e mai bun în 27 din 60 de perechi (p = 0,06 / 0,09). Punctele intermediare ies și mai slabe: +4,5% și +5,0% față de E13 (p ≤ 0,03). Fișierul: `validare_e14.csv` | negativ: nici reantrenarea pe geamănul calibrat, chiar pe ziua de validare, nu întrece E13, deci E14 nu devine candidat. Candidații finali ai protocolului din § 9.9 sunt planul 12/14/12, `TOD_DEBIT`, adică programul din planuri fixe pe cazuri de trafic, și E13; câștigătorul e în § 9.10. Ca și testul din § 9.10, validarea lui E14 stă pe geamănul cu coliziuni și teleportări în masă, deci rezultatul a fost retras pe 2.11 (§ 6.5) |
| E15 – antrenat în ziua de 3.11, pe geamănul înghețat, fără date din 3.11: agent nou, care imită întâi planul observat, 72/48, cu un acord de 94% pe 40 000 de decizii, apoi învață 300 000 de pași cu PPO, pe cele 14 scenarii ale zilelor de antrenare care trec poarta, cu participanți disciplinați și indisciplinați. Alege doar între N–S și E–V | Pe aceleași 14 scenarii, cu seed-urile 1–3, pierde cu 1,7% mai mult decât planul observat: cu 5,7% mai mult cu participanții disciplinați, mai ales la vârfurile ×1,2, și cu 5,0% mai puțin cu cei indisciplinați. Față de semaforul rejucat, pe orele acoperite cel puțin 80% de valuri măsurate, adică pe 48 de perechi, pierde cu 8,9% mai puțin, dar diferența nu e semnificativă. Cifrele sunt doar descriptive, ca toate cele ale grilei de după îngheț: diferențele dintre strategii apropiate au mărimea rezultatului retras (§ 6.5, § 9.11). Fișierul: `grila_inghet_e15.csv` | regula nu l-ar găsi eligibil pe zilele de antrenare; intră totuși pe lista candidaților, cum s-a scris pe 1.11, iar validarea decide; pe 4.11, validarea a fost doar descriptivă, deci n-a trecut niciun candidat (§ 9.11) |
| Grila de 10 planuri fixe, cu diferite combinații de durate de verde pentru axele N–S și E–V și pentru pietoni, pe datele din 21–22.10 și cu capacitatea implicită | planul actual 36/28/12 e cel mai bun în medie; 46/48/12 câștigă la vârf | **46/48/12 adoptat pentru traficul greu** în programul pentru marginea de sus |

**Lecția metodologică.** Diferențele de 1–2 puncte procentuale își schimbau semnul între seed-urile de validare și cele
de test. De aceea, validarea a trecut de la 3 la 5 seed-uri, iar rezultatele finale se raportează pe 10 seed-uri de test,
cu teste statistice.

### 9.6 Unde se pierde timpul la vârf

> **Corectură, după retragerea din 2.11.2026.** Partea despre capacitatea calibrată stă pe geamănul cu coliziuni și
> teleportări în masă (§ 6.5), deci nu mai e valabilă. Pe geamănul corectat, coada de pe Dacia vest nu dispare: în zilele
> lucrătoare de antrenare, geamănul duce acolo cel mult ≈590 de vehicule pe oră, față de 766–1 063 în cameră, cu factorul de corecție
> (§ 6.5), iar pe 3 și 4.11 nu trece poarta nicio oră, 0 din 5 și 0 din 4: orele încărcate pică mai ales din această cauză (§ 9.11). Coada de pe Calea
> Victoriei venea din rutele simulării, care porneau de oriunde din rețea: ≈72% din traficul de pe Magheru pornea de pe
> Calea Victoriei (§ 6.5). Textul rămâne ca istoric al lucrului.

La vârf, piața este cea mai aglomerată, așa că merită aflat unde anume se pierde atunci timpul. Pe geamănul cu
capacitate implicită, adică cu parametrii impliciți ai șoferilor din SUMO, jumătate sau mai mult din timpul vehiculelor
oprite sau rămase la intrare se aduna în coada de pe Bd. Dacia vest, care nici nu încăpea în rețea. Cu capacitatea
calibrată, această coadă dispare. Rămâne o coadă la marginea vestică a rețelei, pe Calea Victoriei, despre care nu se
știe încă dacă e reală.

Prima analiză s-a făcut pe cererea calibrată (§ 9.8), pe vârfurile din 21 și 22.10, cu geamănul cu capacitate implicită,
planul fix actual și seed-ul 1. Modulul `romana.control.localizare` (§ 11.8) a împărțit pe locuri timpul vehiculelor
care stau oprite sau așteaptă să intre în rețea:

| Vârful | Coada de intrare pe Bd. Dacia vest | Zona pieței: intrările și ≈250 m în amonte | La alte semafoare și pe alte străzi | Coada de intrare pe Dacia est / Magheru |
|---|---|---|---|---|
| 21.10, participanți disciplinați | **78%** | 11% | 10% | 1% / 0% |
| 22.10, participanți disciplinați | **66%** | 16% | 14% | 3% / 0,4% |
| 21.10, participanți indisciplinați | **64%** | 13% | 16% | 0,5% / 7% |
| 22.10, participanți indisciplinați | **50%** | 18% | 24% | 2% / 6% |

Așadar, pe geamănul cu capacitate implicită, la vârf, **între jumătate și trei sferturi din timpul vehiculelor oprite
sau încă neintrate în rețea** se pierde în coada de pe Bd. Dacia dinspre Calea Victoriei. Vehiculele din această coadă
nici nu încap în rețea, iar coada se întinde dincolo de zona modelată. Doar 11–18% din acest timp vine din opriri în
piața propriu-zisă (`docs/rezultate/localizare_varf_calibrat.csv`). Pe calibrarea anterioară, cea din 22.10 cu zonele
inițiale, ponderea cozii era de 68%, cu ≈24% în piață. Cu zona nouă a camerei, brațul Dacia vest e numărat aproape
complet (§ 4.3), iar coada lui a crescut. Grila de planuri fixe, făcută pe datele din 21–22.10 cu capacitatea implicită
și zonele inițiale, arăta că nici cel mai bun plan fix posibil nu câștigă mai mult de ≈5% la vârful din 21.10.

**Cu capacitatea calibrată (§ 6.4), concluzia se schimbă.** Capacitatea calibrată înseamnă că intervalul de timp pe care
șoferii simulați îl păstrează față de vehiculul din față a fost ajustat, astfel încât geamănul să facă față debitului observat. Analiza s-a refăcut pe
vârful de luni și pe vârful ×1,2, cu ambele comportamente (`docs/rezultate/localizare_varf_capacitate.csv`):

- La aceeași cerere, pe vârful de luni cu participanți disciplinați, timpul vehiculelor oprite sau încă neintrate în
  rețea scade de la 2 230 de vehicul-ore cu parametrii impliciți la 184 cu intervalul `tau` = 0,8 s. O
  vehicul-oră înseamnă o oră petrecută astfel de un singur vehicul.
- **Coada de pe Bd. Dacia vest practic dispare**: pe tronsonul ei de intrare rămâne ≈0,1% din acest timp.
- Cea mai mare parte a timpului rămas, 67–86%, este tot așteptare la intrarea în rețea, dar acum pe Calea Victoriei, la
  capătul vestic al rețelei. Tronsonul de intrare de acolo adună singur 55–75%. De pe el pornesc ≈1 650 de vehicule/h,
  care merg spre piață pe Str. C. A. Rosetti și Bd. Magheru. În zona pieței rămân 6–14%.

**Pentru specialiști.** În rețeaua SUMO, tronsonul de intrare de pe Bd. Dacia vest este muchia `-231435896`, iar cel de
pe Calea Victoriei este muchia `1165343128#0`.

Raportată la pierderea totală a tuturor participanților cu planul fix (§ 9.9), această coadă de la margine înseamnă
≈13–20% la vârf și ≈30–38% la vârful ×1,2. Nu s-a verificat încă dacă e o limită reală, de exemplu la intersecția
Str. C. A. Rosetti × Bd. Magheru, sau un efect al felului în care simularea introduce vehiculele la marginea rețelei.
Coada de pe Dacia vest, în schimb, părea o limită fizică; cu capacitatea calibrată părea să dispară, dar acel geamăn
trecea traficul prin coliziuni și teleportări (§ 6.5). Nici geamănul corectat nu duce pe Dacia vest traficul zilelor
lucrătoare, deși camera numără acolo 766–1 063 de vehicule pe oră (§ 6.5), deci frâna e a geamănului, nu a străzii:
diagnoza din 4.11 o găsește chiar după linia de oprire, în primii ≈16 m (§ 9.11). Coada de pe Calea Victoriei, rămasă
în geamănul cu capacitatea calibrată, se află la marginea zonei modelate, unde semaforul pieței are o influență mică. Pe 2.11 s-a văzut de
unde venea: rutele simulării porneau de oriunde din rețea, așa că ≈72% din traficul de pe Magheru pornea de pe Calea
Victoriei, prin 4 semafoare. În geamănul corectat, rutele pornesc de pe bulevardul fiecărui braț (§ 6.5), deci coada
aceasta nu spune nimic despre stradă.

### 9.7 Concluzie

> **Corectură, 2.11.2026.** Concluziile care folosesc capacitatea calibrată, inclusiv cele despre planul 12/14/12, stau pe geamănul cu
> coliziuni și teleportări (§ 6.5), deci nu mai sunt valabile. Textul rămâne ca istoric al lucrului.

Pe scurt, la data scrierii, cea mai bună soluție părea și cea mai simplă: planul fix 12/14/12, adică aceleași faze ale
semaforului, cu durate mai scurte. Concluzia a fost retrasă pe 2.11: geamănul trecea traficul prin coliziuni și
teleportări, iar socoteala din cameră arată că 12 s de verde dintr-un ciclu de 53 s nu pot duce traficul de vârf de pe
Magheru (§ 6.5). În ziua de validare, 4.11, geamănul corectat nu a trecut poarta pe nicio oră, deci validarea a fost
doar descriptivă, niciun candidat nu a trecut și rămâne planul observat, 72/48/3; asta nu arată că e cel mai bun, ci
doar că geamănul nu a putut judeca (§ 9.11). Concluziile de mai jos arată drumul de atunci. Punctele 1–5 pornesc de la
rezultatele pe calibrările anterioare, din 21, 22 și 25.10, obținute cu geamănul cu capacitate implicită (§ 6.4), cu
procente față de planul de referință, o ipoteză pe care camera a infirmat-o (§ 6.5). Ele spun apoi ce a rămas din
aceste rezultate pe cererea calibrată (§ 9.8) și pe geamănul calibrat (§ 9.9). Părțile care trimit la geamănul
calibrat, ca și punctele 6 și 7, care rezumă testele din § 9.9–9.10, sunt retrase.

1. **Pe calibrările anterioare, inteligența artificială, folosită cu discernământ pe infrastructura existentă, părea să
   merite.** Pe acele calibrări, un program pe tipuri de trafic a redus timpul pierdut de toți participanții, față de
   planul de referință, luat atunci drept programul actual, cu ≈1,5–7% când participanții respectă regulile. Când nu
   le respectă, cum se întâmplă în realitate în București, reducerea a fost de **≈16%**, semnificativă statistic, fără nicio lucrare pe stradă. Pe
   cererea calibrată, avantajul programului realist față de planul fix scade, iar cu participanți indisciplinați nu mai
   e semnificativ: −6,2% în § 9.8 și −3,9% pe 26.10, în § 9.9. Față de actuated, avantajul rămâne clar: −8…−12%.
   Procentele față de planul fix sunt, toate, față de o ipoteză: camera a arătat pe 2.11 că semaforul de pe stradă are
   ziua un ciclu de ≈125–155 s, nu de ≈91 s (§ 6.5).
2. **Pe calibrările anterioare, cu participanți care respectă regulile, un singur agent AI nu întrecea la vârf un plan
   fix bine reglat.** Era însă printre cele mai bune strategii la trafic lejer și moderat. Pe o zi nouă se descurca bine
   la volume apropiate de cele din antrenare, dar pentru situații foarte diferite are nevoie de reantrenare pe date noi.
   Pe ziua de luni, cu capacitatea calibrată, E13 obține în medie −9,7% față de planul fix cu participanți disciplinați,
   iar pe 10 seed-uri −7,9%. El câștigă în fiecare scenariu, inclusiv la vârf (§ 9.9). Planul fix scurt 12/14/12 ajunge
   însă la nivelul lui (§ 9.9–9.10).
3. **Calitatea datelor contează cel mai mult.** Corectarea zonelor și a felului de numărare a schimbat rezultatul mai
   mult decât orice algoritm. O înregistrare sacadată a înjumătățit cererea măsurată, fără să se observe (§ 4.6).
   De atunci, senzorul e păzit: din 29.10, veghea fluxului dă alerta la primul semn de problemă, iar din 1.11 paznicul
   repornește colectarea dacă procesul lipsește sau tace. Fișa senzorului, calculată din jurnalele locale ale
   colectării, arată cât a mers camera ca senzor IoT (§ 4.6). Incertitudinea măsurării cererii se exprimă printr-un interval, nu printr-un singur număr.
4. **Cu participanți indisciplinați, ca în București, avantajul AI crește.** Pe calibrarea marginii de jos, specialiștii
   E3 și E9 au redus timpul pierdut cu ≈10–14% față de planul fix, până la −28% la vârf, iar reducerea e semnificativă
   statistic (§ 9.4). Motivul: agenții se adaptează la blocaje pe care un plan fix nu le poate anticipa. Pe cererea
   calibrată, avantajul specialiștilor scade, iar E3 ajunge practic egal cu planul fix (§ 9.8–9.9). Agenții antrenați
   pe toate tipurile de trafic, oficialul și E13, păstrează în schimb ≈10% pe 26.10 (§ 9.9), dar doar ≈4–6% pe 28.10:
   E13 obține −3,8%, iar oficialul −5,9% din pierderea totală cu participanți indisciplinați
   (`test_28_indisciplinat.csv`).
5. **La vârf, pe geamănul cu capacitate implicită, coada de pe Dacia vest domina timpul pierdut** (§ 9.6). Cu
   capacitatea calibrată, această coadă părea să dispară, dar rămânea alta, o coadă de intrare la marginea vestică a rețelei,
   pe Calea Victoriei, cu ≈13–20% din pierderea totală la vârf. Pe 2.11 s-au lămurit amândouă (§ 6.5): acel geamăn
   trecea traficul prin coliziuni și teleportări, iar coada de pe Calea Victoriei venea din rutele simulării, care
   porneau de oriunde din rețea. Pe geamănul corectat, Dacia vest rămâne sub cameră în zilele lucrătoare, iar diagnoza
   din 4.11 găsește frâna, în geamăn, chiar după linia de oprire (§ 9.11).
6. *(Retras pe 2.11: geamănul care părea să facă față debitului real îl ducea prin coliziuni și teleportări, § 6.5.)*
   **Pe ziua de luni 26.10, nefolosită până atunci la antrenare sau la alegere, cu geamănul care face față debitului
   real (§ 9.9), toți agenții AI întrec actuated și, în medie, planul fix.** Pe 28.10, E3 nu mai întrece planul fix:
   +0,3% (§ 9.10). Cel mai constant este E13, agentul oficial reantrenat pe cererea calibrată: față de planul fix
   obține −9,5% cu participanți indisciplinați și −9,7% cu disciplinați. E13 câștigă în fiecare scenariu și e mai bun
   decât actuated în toate cele 60 de perechi. Cu participanți indisciplinați e la egalitate cu agentul oficial.
   Programul realist rămâne mai bun decât actuated, dar componenta lui pentru traficul greu, E3, nu își păstrează
   avantajul pe ziua nouă cu participanți indisciplinați.
7. *(Retras pe 2.11: geamănul trecea traficul prin coliziuni și teleportări, iar socoteala din cameră arată că 12 s de
   verde dintr-un ciclu de 53 s duc pe Magheru cel mult ≈1 300 de vehicule pe oră, față de ≈2 600 numărate la vârf,
   § 6.5. Nici ciclul de ≈91 s, numit mai jos „actual”, nu e cel de pe stradă: camera măsoară ziua ≈125–155 s, § 6.5.)*
   **Testul final (miercuri 28.10) și confirmarea (joi 29.10), § 9.10: câștigă planul fix scurt 12/14/12.** După
   regula fixată dinainte, pe ziua de test, nefolosită la alegere, toți cei trei candidați întrec semnificativ
   programul realist, cu ≈6–7% din pierderea totală. Candidații erau planul 12/14/12, programul din planuri fixe pe
   cazuri de trafic și E13. Între ei, diferențele nu sunt semnificative, așa că regula alege candidatul cel mai simplu,
   planul 12/14/12. Acesta a trecut în geamănul digital care rulează în timp real. Ciclul scurt, de ≈53 s în loc de
   ≈91 s, câștigă prin pietoni: −12% față de planul fix actual, în timp ce vehiculele pierd puțin, +1–2%. Cu acest
   plan, nicio trecere nu are mai puțin de 12 s de verde pe ciclu, cât durează faza de pietoni, la fel ca în planul de
   referință. Trecerile legate de o fază de vehicule au verde mai scurt, dar tot peste dublul timpului de traversare.
   Mai trebuie verificată doar faza de pietoni de 12 s, după normele de proiectare (§ 9.10, § 10). Chiar și cu faza de
   pietoni lungită la 18 s, ciclul scurt rămâne cu ≈8% mai bun decât ciclul actual cu aceeași fază (§ 9.10). Ziua de
   confirmare, joi 29.10, l-a confirmat: −7,0% din pierderea totală pe toată rețeaua simulată, nu doar în piață, față de programul realist (p = 7·10⁻⁸). Planul a
   fost mai bun în ambele comportamente și, de data aceasta, a avut cea mai mică pierdere totală dintre candidați.
   Câștigul vine tot de la pietoni: −15% față de planul fix actual. Cea mai bună combinație implementabilă găsită pe
   datele reale este deci și cea mai simplă: aceleași faze, cu durate mai scurte.

### 9.8 Reevaluarea pe cererea calibrată (26.10.2026)

Pe scurt, după refacerea zonelor camerei și calibrarea cererii pe numărătoarea de referință, strategiile au fost
evaluate din nou, fără reantrenarea agenților. Programul realist rămâne mai bun decât actuated, dar avantajul lui față
de planul fix scade și nu mai este semnificativ. Vârfurile ×1,2 rămân punctul slab.

Cu zonele refăcute și cererea calibrată pe numărătoarea de referință (§ 4.3, § 5.1), cele 10 scenarii de zi lucrătoare
au volume apropiate de fosta margine de sus. Agenții **nu au fost reantrenați** pe aceste scenarii: ei fuseseră
antrenați pe calibrările anterioare. Strategiile au fost evaluate din nou pe seed-urile de test 1–5, adică pe 50 de
perechi scenariu × seed (`docs/rezultate/calibrat_indisciplinat.csv`, `calibrat_normal.csv`). Programele pe tipuri de
trafic folosesc împărțirea din § 9.2: trafic lejer = scenariile liniștite, moderat = prânzul din 21.10, greu = restul.

| Față de planul fix, cu participanți indisciplinați | Diferența medie | Mai bun în | p (testul t / Wilcoxon) |
|---|---|---|---|
| Programul realist: agentul oficial la trafic lejer, E3 la moderat și greu | −6,2% | 36 / 50 | 0,46 / 0,10 |
| Agentul oficial singur | −5,6% | 37 / 50 | 0,45 / 0,07 |
| Agentul E9 singur | −3,5% | 31 / 50 | 0,12 / 0,03 |
| Agentul E3 singur | −0,7% | 26 / 50 | 0,48 / 0,34 |
| Actuated | +7,4% | 20 / 50 | <0,001 / <0,001 |
| Planul 46/48/12 | +12,0% | 7 / 50 | <0,001 / <0,001 |

Față de actuated, programul realist obține **−11,7%** și e mai bun în 44 din 50 de perechi (p < 0,001). Față de planul
fix, câștigul de −6,2% nu mai este semnificativ. Programul e mai bun în 9 din 10 scenarii, cu −2…−16%, dar la vârful
×1,2 din 22.10, cu ≈3 070 veh/h, peste orice volum din antrenare, agentul E3 pierde +26,5%.

Cu participanți disciplinați, programul realist obține −1,3% față de planul fix și e mai bun în 36 din 50 de perechi,
dar diferența nu e semnificativă (p = 0,57 / 0,25). Față de actuated obține −4,3%, tot nesemnificativ. Agenții folosiți
singuri ies între +1,0% și +3,6% față de planul fix, iar E3 obține −0,6% față de actuated. Și aici, vârfurile ×1,2 sunt
punctul slab: programul pierde +12% și +24%.

**Concluzia reevaluării.** Pe cererea calibrată, avantajul AI se păstrează față de actuated și, în majoritatea
situațiilor, față de planul fix, dar e mai mic decât pe calibrările anterioare. La volumele cele mai mari, agenții
trebuie **reantrenați pe scenariile calibrate**. Prima reantrenare pe scenariile calibrate din 21–22.10, cea din care au
rezultat E12 și E13 (§ 9.5), a dat un program echivalent statistic cu programul realist, deci nu a fost adoptată.
Explicația a venit ulterior: scenariile din 21–22.10 sunt subnumărate din cauza înregistrării sacadate (§ 4.6), iar
geamănul de atunci nu făcea față debitului real de luni (§ 6.4). Cauza nu ținea de parametrii șoferilor, cum se credea:
pe 2.11 s-au găsit rute care porneau de oriunde din rețea, o bandă fără continuare, legături ghicite între benzi și o
vedere de doar 4,5 m la legăturile care cedează, iar geamănul corectat, cu intervalul implicit `tau` = 1,0 s, duce
vârful de luni pe Magheru (§ 6.5). Evaluarea pe ziua de luni, cu capacitatea calibrată, din § 9.9, a fost retrasă:
acel geamăn trecea traficul prin coliziuni și teleportări (§ 6.5).

### 9.9 Testul pe o zi lucrătoare nouă, cu capacitatea calibrată (luni, 26.10.2026)

> **Corectură din 2.11.2026.** Acest subcapitol stă pe geamănul cu coliziuni și teleportări (§ 6.5), deci concluziile lui nu mai sunt
> valabile, inclusiv câștigul planului 12/14/12. Pe geamănul corectat, planul 12/14/12 este cel mai slab plan încercat la vârf. Textul
> rămâne ca istoric al lucrului. Regulile zilelor noi și rezultatul lor sunt în § 9.11: pe geamănul corectat, poarta, adică
> verificarea geamănului față de cameră, oră cu oră, trece pe 8 din cele 12 ore comparate la îngheț, din 25 și 26.10 și din
> 1 și 2.11, dar pe 0 din 5 ore pe 3.11 și pe 0 din 4 ore pe 4.11, mai ales din cauza Daciei vest. Validarea din 4.11 a
> fost deci doar descriptivă: niciun candidat nu a trecut, runda s-a încheiat fără un program nou, iar planul observat,
> 72/48/3, rămâne în geamănul în timp real.

**Pe scurt.** Acest test verifică strategiile pe o zi lucrătoare nouă, luni 26.10, cu un geamăn digital care poate
prelua traficul real. Toți agenții AI bat strategia actuated și, în medie, planul fix, iar cel mai constant dintre ei
este E13. Programul realist, strategia în vigoare la acea dată, nu mai este cea mai bună combinație. Pentru ca
alegerea următoare să nu se facă pe datele de test, ziua de luni a devenit zi de validare, iar noul test s-a făcut
pe miercuri 28.10, după un protocol fixat dinainte și descris spre sfârșitul acestui subcapitol.

**Ziua și strategiile.** Luni 26.10 este prima zi lucrătoare înregistrată continuu (§ 4.6). Până la acest test, ea
**nu a fost folosită nici la antrenarea, nici la alegerea vreunui agent sau program**. A servit însă la calibrarea
modelului pe care se face testul. Factorii de corecție, care ajustează ce numără camera pe fiecare braț, vin din
numărătoarea de referință din aceeași zi (§ 4.3), iar intervalul `tau` al șoferilor simulați a fost reglat pe vârful ei
(§ 6.4). Au fost evaluate trei strategii clasice și cinci agenți AI:

- planul fix de referință 36/28/12, numit și planul actual;
- strategia actuated, care prelungește verdele cât timp detectoarele văd vehicule;
- planul fix 46/48/12;
- agentul oficial și agenții E3, E9, E12 și E13; ultimii doi fuseseră aleși dinainte (§ 9.5).

În notația planurilor, cele trei numere sunt secundele de verde pentru direcția nord–sud (N–S), pentru direcția
est–vest (E–V) și pentru pietoni. Webster și Max-Pressure nu au fost rulate.

**Scenariile și rulările.** Evaluarea s-a făcut pe cele 6 scenarii ale zilei: prânz 12:00–13:00, vârf 15:00–16:00,
seara 17:30–18:30, liniștit 21:30–22:30, vârful ×1,2 și liniștitul ×0,8. Ultimele două sunt variante de
sensibilitate, în care cererea e înmulțită cu 1,2, respectiv cu 0,8. Geamănul a avut capacitatea calibrată, cu intervalul
`tau` = 0,8 s (§ 6.4). Fiecare scenariu există în două variante de comportament:
`capacitate_zi_2026-10-26_*`, cu participanți disciplinați, și `capacitate_indisciplinat_zi_2026-10-26_*`, cu
participanți indisciplinați, adică șoferi și pietoni care mai încalcă regulile. Toate au fost rulate cu
seed-urile 1–5, adică cu cinci valori de pornire ale generatorului de numere aleatoare al simulării. O pereche
înseamnă același scenariu, cu același seed, rulat cu fiecare strategie; rezultă 30 de perechi pentru fiecare
comportament. Programele pe tipuri de trafic folosesc categoriile din § 9.8: trafic lejer în scenariile liniștite,
moderat la prânz și greu în rest. Rezultatele sunt în `docs/rezultate/capacitate_indisciplinat_26.csv` și
`capacitate_normal_26.csv`.

Tabelul dă, pentru fiecare strategie, diferența medie pe perechi a pierderii totale de timp față de planul fix: un
minus înseamnă mai puțin timp pierdut. Urmează numărul de perechi în care strategia a pierdut mai puțin decât planul
fix și cele două valori p. „Singur” înseamnă că agentul conduce semaforul pe toate tipurile de trafic, nu doar într-o
componentă a unui program.

| Strategia, față de planul fix | Participanți indisciplinați | Participanți disciplinați |
|---|---|---|
| **E13 singur** (agentul oficial reantrenat, `ppo_romana_cal`) | **−9,5%**, mai bun în 27 / 30 (p = 0,0007 / 0,0001) | **−9,7%**, 28 / 30 (p = 0,0001 / 0,00001) |
| Agentul oficial singur | −10,0%, 26 / 30 (p = 0,001 / 0,0001) | −5,9%, 24 / 30 (p = 0,07 / 0,01) |
| Programul reantrenat (E13 la lejer, E12 în rest) | −7,1%, 24 / 30 (p = 0,010 / 0,008) | −6,5%, 22 / 30 (p = 0,02 / 0,04) |
| Programul realist (oficial la lejer, E3 în rest) | −3,9%, 18 / 30 (p = 0,85 / 0,73) | −6,4%, 24 / 30 (p = 0,04 / 0,009) |
| E12 singur | −5,9%, 23 / 30 (p = 0,01 / 0,02) | −6,2%, 22 / 30 (p = 0,02 / 0,03) |
| E9 singur | −5,4%, 19 / 30 (p = 0,07 / 0,22) | −7,0%, 23 / 30 (p = 0,01 / 0,003) |
| E3 singur | −1,9%, 18 / 30 (p = 0,92 / 0,90) | −5,2%, 24 / 30 (p = 0,04 / 0,009) |
| Actuated | +5,1%, 13 / 30 (p = 0,008 / 0,03) | +4,5%, 11 / 30 (p = 0,004 / 0,007) |
| Planul 46/48/12 | +10,1%, 4 / 30 (p = 0,02 / 0,002) | +7,9%, 5 / 30 (p = 0,005 / 0,0006) |

Prima valoare p vine din testul t pe perechi, a doua din testul Wilcoxon. Valoarea p arată cât de probabilă ar fi o
diferență cel puțin la fel de mare dacă cele două strategii ar fi, de fapt, la fel de bune. Sub 0,05, diferența se
consideră semnificativă, adică greu de pus pe seama întâmplării. Față de actuated, E13 este mai bun în **toate cele 60
de perechi**, cu −13,2% în ambele comportamente. Tot față de actuated, programul realist dă −8,3% cu participanți
indisciplinați (24 / 30) și −10,2% cu participanți disciplinați (28 / 30).

**Verificarea pe 10 seed-uri.** Seed-urile 6–10 confirmă concluziile principale, dar nu și ordinea exactă a
strategiilor. Ele au fost rulate pe 27–28.10, după ce protocolul de mai jos fusese fixat, iar rezultatele lor sunt în
`capacitate_indisciplinat_26_6_10.csv` și `capacitate_normal_26_6_10.csv`. Pe cele 60 de perechi ale fiecărui
comportament, față de planul fix, s-au obținut valorile de mai jos; prima este cu participanți indisciplinați, a doua
cu participanți disciplinați:

- E13 dă −9,2% / −7,9% și e mai bun în 53 / 60 în ambele comportamente;
- agentul oficial dă −8,5% / −6,3%, iar E9 −6,3% / −7,5%;
- programul realist dă −3,5% (p = 0,84 / 0,53) și −5,0% (p = 0,13 / 0,05).

Față de actuated, E13 e mai bun în 117 din 120 de perechi. Față de programul realist, E13 dă −5,3% (39 / 60) și −2,5%
(33 / 60), iar pe cele 120 de perechi reunite −3,9% (72 / 120, p < 0,000001 / 0,000006). Pe seed-urile noi, avantajul
lui E13 cu participanți disciplinați se îngustează: −7,9% pe 10 seed-uri, față de −9,7% pe seed-urile 1–5. Chiar și
așa, pe 10 seed-uri E13 rămâne cel mai bun în ambele comportamente.

**Ce arată testul.**

1. **Pe o zi nevăzută, cu un geamăn care poate prelua traficul real, toți agenții AI bat strategia actuated și, în
   medie, planul fix.** Față de actuated, diferența e semnificativă în ambele comportamente. Față de planul fix, ea e
   semnificativă pentru toți agenții, cu excepția lui E3 și E9 cu participanți indisciplinați. **E13 este cel mai
   constant:** câștigă în fiecare dintre cele 6 scenarii, în ambele comportamente, cu −1,7% … −17,6% pe scenariu. Cu
   participanți disciplinați este cel mai bun: −9,7%, față de −5,9% la agentul oficial. Cu participanți indisciplinați
   este la egalitate cu agentul oficial: −9,5% față de −10,0%, iar comparația directă dă +1,2% (p = 0,90 / 0,69).
   Tot cu participanți indisciplinați, agentul oficial iese însă mai slab decât planul fix la vârful ×1,2. Ca ordin
   de mărime, cu planul fix, pierderea totală de timp a tuturor participanților este, într-un scenariu, de ≈50 de
   ore-om în ora liniștită, ≈450–490 la prânz, ≈590–610 seara, ≈750–820 la vârf și ≈1 060 la vârful ×1,2.
2. **Programul realist nu mai este cea mai bună combinație.** Pentru traficul moderat și greu, el folosește agentul E3.
   Cu participanți indisciplinați, E3 iese mai slab decât planul fix seara (+4,7%) și la vârful ×1,2 (+6,4%), iar cu
   participanți disciplinați se descurcă bine (−5,2%). Față de programul realist, E13 dă −5,2% cu participanți
   indisciplinați (p = 0,002 / 0,006) și −3,1% cu disciplinați (p = 0,03 / 0,06). Combinația fusese aleasă pe
   21–22.10, pe date subnumărate, în care camera prinsese mai puține vehicule decât au trecut în realitate, și pe un
   geamăn cu capacitatea implicită. Ea nu se transferă complet pe ziua nouă. Agenții antrenați pe toate tipurile de
   trafic, agentul oficial și E13, generalizează mai bine, adică își păstrează mai ușor rezultatele pe o zi pe care nu
   au văzut-o.
3. **Planul 46/48/12 e acum mai slab decât planul actual (+8…+10%).** El fusese ales pentru vârf din grila de planuri
   din 21–22.10, adică dintr-o serie de planuri fixe încercate pe rând. Pe un geamăn cu capacitatea reală, dintre cele
   două planuri fixe testate, mai bun este cel actual, 36/28/12. Grila refăcută ulterior pe geamănul calibrat,
   prezentată mai jos la protocol, arată însă că nici planul actual nu e aproape de cel mai bun plan fix: câștigă
   ciclurile scurte.
4. **Reantrenarea pe scenariile calibrate a ajutat agentul oficial pe ziua nouă, dar doar cu participanți
   disciplinați.** În acest caz, E13, varianta lui reantrenată, dă −9,7%, față de −5,9% la agentul oficial. Cu
   participanți indisciplinați, cei doi sunt la egalitate: −9,5% față de −10,0%. Același tipar apărea și pe testul
   din 21–22.10 (§ 9.5): cu participanți disciplinați, E13 dădea −4,8%, iar agentul oficial +1,0%. Validarea din
   21–22.10 conținea însă doar participanți indisciplinați, la care cei doi erau la egalitate, deci nu avea cum să
   arate diferența.

**Ce nu se poate concluziona din acest test.** Alegerea unui nou program după rezultatele de mai sus ar însemna
alegerea pe datele de test, adică pe aceleași date pe care se măsoară rezultatul. De aceea, luni 26.10 devine **ziua
de validare** pentru alegerea următoare: ziua pe care se aleg strategiile, nu cea pe care se judecă rezultatul.
Protocolul testului următor s-a fixat pe 27.10, la ≈05:30, înainte de prelucrarea oricărei zile noi. Data testului a
fost mutată pe 28.10 în noaptea de 27–28.10, tot înainte de orice prelucrare. Protocolul, cu verificările și
schimbările de dinaintea testului, este următorul:

- **Candidatul este E13 singur.** Pe 26.10, E13 este cel mai bun cu participanți disciplinați și cel mai constant: e
  mai bun decât planul fix în 55 din 60 de perechi și câștigă în toate scenariile. Față de programul realist, pe cele
  60 de perechi reunite ale celor două comportamente, dă −4,1% și e mai bun în 38 / 60 (p = 0,0002 / 0,001).
- **Regula inițială, pentru E13, raportată în continuare.** După această regulă, E13 ar înlocui programul realist
  dacă ar fi îndeplinite două condiții. (a) Pe toate perechile reunite, din ambele comportamente, E13 pierde în medie
  mai puțin timp decât programul realist, adică diferența medie e negativă, iar testul Wilcoxon bilateral pe perechi
  dă p < 0,05. Un test bilateral caută diferențe în ambele sensuri. (b) În niciunul dintre comportamente, luat
  separat, E13 nu iese semnificativ mai slab, adică nu are la același test p < 0,05 cu diferența medie pozitivă. Pe
  26.10, regula ar fi fost îndeplinită.
- **E14, verificat înainte de test (28.10, ≈05:00).** E14 este E13 antrenat mai departe pe scenariile de luni, cu
  capacitatea calibrată (§ 9.5). A fost validat pe seed-urile 11–15 ale zilei de luni, înainte de prelucrarea zilei de
  28.10. Iese mai slab decât E13 (+2,2%, p = 0,06 / 0,09), deci nu devine candidat. Candidatul rămâne E13 singur.
- **Grila de planuri fixe pe geamănul calibrat, verificată înainte de test (28.10, ≈10:30).** Pe aceeași validare,
  adică pe ziua de luni 26.10, cu seed-urile 11–15 și cele 12 scenarii cu capacitatea calibrată, s-au încercat 23 de
  planuri fixe. Verdele N–S a variat în intervalul 12–44 s, verdele E–V în intervalul 10–36 s, iar faza de pietoni a
  rămas de 12 s (`grila_calibrat.csv`). Câștigă ciclurile scurte. Cel mai bun este planul **12/14/12**, cu un ciclu de
  ≈53 s, față de ≈91 s la planul de referință 36/28/12; ciclul este timpul după care fazele se reiau. Față de planul
  fix, planul 12/14/12 dă −9,3% și e mai bun în 53 / 60 de perechi (p < 0,000001). Pe aceleași date, E13 dă −7,9%. În
  comparația directă, planul 12/14/12 dă −0,9% față de E13 și e mai bun în 35 / 60 (p = 0,10 / 0,15), deci diferența
  nu e semnificativă. Dacă se alege câte un plan pentru fiecare categorie de trafic, validarea alege 16/10/12 la trafic
  lejer și moderat și 12/14/12 la trafic greu. Acest program din planuri fixe, `TOD_FIX`, dă −10,8% față de planul fix
  și −2,3% față de E13 (p = 0,05 / 0,01). El e însă ales chiar pe aceste date, deci estimarea e optimistă. Planul
  12/14/12 și programul din planuri fixe intră în test: la început ca strategii raportate doar informativ, apoi, după
  decizia autorului „cel mai bun câștigă”, descrisă mai jos, ca candidați.

    Aceste planuri au o limită. Verdele lor, de 10–14 s, respectă verdele minim impus de controler, de 10 s (§ 7.2),
    dar e aproape de timpul de degajare a pietonilor, adică de timpul de care are nevoie un pieton pornit la sfârșitul
    verdelui ca să ajungă pe partea cealaltă. Cea mai lungă trecere comandată de semaforul pieței are 12,8 m; la
    1,2 m/s, un pieton o parcurge în ≈11 s. Modelul nu impune separat acest timp, nici planurilor fixe, nici agenților
    (§ 10). Verificarea trecerilor, făcută după test (§ 9.10), a arătat că trecerile care au verde în fazele de
    vehicule îl au și în faza de pietoni. Limita privește deci doar faza de pietoni de 12 s, aceeași în toate planurile.

- **Cum câștigă agenții pe geamănul calibrat (diagnostic, 28.10).** S-au analizat trei scenarii de validare din ziua
  de luni, cu seed-ul 11: liniștit, prânz și vârf. În ele, E13 și agentul oficial schimbă faza aproape mereu imediat ce
  verdele minim o permite. În toate cele trei faze, mediana verdelui este de 11 s, adică jumătate dintre verzi durează
  cel mult 11 s, iar ciclul median este de 30–45 s (`durate_verde_agenti.csv`, `romana.control.durate_verde`). Faza
  E–V e sărită des: E13 îi dă de 1,3–3,4 ori mai puține verzi decât fazei N–S. Agenții lucrează deci chiar în zona
  verzilor scurte, aceeași în care câștigă și planurile fixe din grilă. În plus, ei aleg după cerere ordinea fazelor și
  faza pe care o sar.
- **Schimbarea protocolului înainte de test: „cel mai bun câștigă” (decizia autorului, 28.10, ≈12:30).** După
  rezultatul grilei, autorul a hotărât ca geamănul în timp real să primească cea mai bună strategie dintre candidații
  validați, oricare ar fi ea, iar celelalte să rămână în documentație ca încercări. Astfel, ideea proiectului se mută
  de la „un agent AI cu orice preț” la cea mai bună combinație care se poate pune în practică, aleasă pe cazuri de
  trafic din date reale (§ 1, § 2). Schimbarea s-a făcut înaintea oricărei prelucrări a zilei de 28.10. Până atunci, pe
  datele acestei zile se rulase doar planul fix, pe o oră incompletă, ca verificare tehnică a lanțului de prelucrare,
  fără comparații între strategii. Tot înainte de test, la observația autorului, s-au corectat zonele a două treceri de
  pietoni: zona de pe Mendeleev a fost mutată pe zebra reală, iar cele două zone de pe Dacia est au fost legate între
  ele (§ 4.4). Corectura schimbă doar numărul de pietoni, cu ≈ +4%, nu și vehiculele. Zilele 28.10 și 29.10 se numără
  cu zonele noi. Scenariile zilei de validare, 26.10, nu s-au refăcut, așa că au cu ≈4% mai puțini pietoni. Noul
  protocol are următoarele elemente:

    - *Cazurile de trafic se definesc după debitul echilibrat măsurat de cameră*, adică după numărul de vehicule pe
      oră (veh/h) calculat ca medie între intrări și ieșiri, ca în `scenarii_zi` și în geamănul în timp real: **lejer
      sub 2 400 veh/h, intens peste 4 100 veh/h, mediu între ele**. Pragurile sunt puse, cu rotunjire, la jumătatea
      distanței dintre ferestrele zilei de validare: 2 400 veh/h între fereastra liniștită, cu 1 213 veh/h, și cea de
      seară, cu 3 502 veh/h, iar 4 100 veh/h între prânz, cu 3 592 veh/h, și vârf, cu 4 653 veh/h. Pragurile vechi
      ale geamănului în timp real, 1 300 și 2 000 veh/h, veneau din zilele subnumărate 21–22.10; cu datele noi, ar fi
      pus aproape toată ziua la „intens”. Și pe cazurile noi, validarea alege aceleași planuri: 16/10/12 la trafic
      lejer și mediu și 12/14/12 la trafic intens. Programul rezultat, `TOD_DEBIT`, dă −10,2% față de planul fix și
      −1,7% față de E13. Pentru diferența față de E13, testul Wilcoxon dă p = 0,02, iar testul t nu arată o diferență
      semnificativă.
    - *Candidații*, fixați înainte de test, sunt, de la cel mai simplu la cel mai complex: planul 12/14/12, programul
      `TOD_DEBIT` și E13. Ei se compară cu strategia în vigoare, programul realist, evaluat pe aceleași cazuri după
      debit.
    - *Regula* (`romana.control.decizie`). Câștigă candidatul cu cea mai mică pierdere totală de timp pe toate
      perechile din 28.10, adică pe toate combinațiile de scenariu și seed, cu ambele comportamente. Candidatul trebuie
      însă să îndeplinească două condiții. (a) Să fie semnificativ mai bun decât programul realist: testul Wilcoxon
      bilateral dă p < 0,05, iar diferența medie în ore pe pereche e negativă, adică pierderea totală e mai mică. Așa
      este scrisă regula în versiunea codului salvată înaintea testului (commitul `508bfff`). (b) Să nu fie
      semnificativ mai slab în niciun comportament luat separat. Un candidat care îndeplinește ambele condiții este
      eligibil. Dacă primii doi candidați eligibili, cei cu pierderea totală cea mai mică, nu se deosebesc
      semnificativ, câștigă cel mai simplu de pus în practică. Dacă niciun candidat nu e eligibil, rămâne programul
      realist. Aplicată pe validare, unde planurile fixe sunt judecate chiar pe datele pe care au fost alese, regula
      ar alege planul 12/14/12: toți cei trei candidați bat programul realist, iar planul 12/14/12 și `TOD_DEBIT` sunt
      la egalitate (p = 0,83).
    - *Confirmarea pe 29.10.* Câștigătorul rămâne în geamănul în timp real, cu o singură excepție: cazul în care, pe
      ziua de confirmare, iese semnificativ mai slab decât programul realist, adică testul Wilcoxon dă p < 0,05, iar
      diferența medie e pozitivă. Atunci geamănul revine la programul realist. Pe 29.10, planul 12/14/12 a ieșit
      semnificativ mai bun, nu mai slab: −7,0% din pierderea totală, p = 7·10⁻⁸ (§ 9.10).
    - *Pragurile se reverifică* pe fiecare zi nouă. Dacă ferestrele unei zile se împart altfel între cazuri sau dacă
      un caz ar cere o treaptă intermediară, schimbarea se face doar după o nouă validare, nu pe datele de test.
    - *Măsura pe persoană, raportată fără să schimbe decizia.* Măsura principală dă aceeași greutate unei ore
      pierdute de un vehicul și uneia pierdute de un pieton, deci un troleibuz plin contează cât un autoturism. Camera
      nu vede câte persoane sunt într-un vehicul. Pentru liniile din piață nu există nici date publice de ocupare:
      doar vehiculele noi ale STB (Societatea de Transport București) au numărătoare automate de călători, iar restul
      se estimează din sondaje[^stb-ocupare]. De aceea, începând cu testul din 28.10, fiecare simulare păstrează
      separat, în aceeași rulare, pierderea fiecărui tip de participant: autoturisme, autobuze și troleibuze,
      camioane, motociclete, bicicliști și pietoni. Măsura pe persoană se calculează apoi cu ocupări declarate, adică
      cu un număr de persoane pe vehicul presupus explicit (`romana.control.ocupare`): 1,2 persoane pe autoturism,
      valoarea pentru naveta la orele de vârf[^eea-ocupare], și 20, 40 sau 70 de persoane pe autobuz sau troleibuz,
      adică aproximativ un sfert, jumătate și trei sferturi din capacitatea unui vehicul de 12 m. Regula se aplică și
      pe fiecare dintre aceste variante, ca analiză de sensibilitate: se raportează dacă și cum s-ar schimba
      câștigătorul. Pe câteva perechi de probă din ziua de luni, din scenariile liniștit ×0,8 și prânz, pietonii au
      reprezentat ≈63–73% din orele pierdute în măsura principală și ≈37–53% în măsura pe persoană, iar călătorii din
      autobuze ≈18–44%, după ipoteza de ocupare.

- **Testul se face pe prima zi lucrătoare nouă colectată complet: miercuri 28.10.** Ziua de marți 27.10 nu e
  completă: colectarea s-a oprit la 06:04, la închiderea calculatorului. Noaptea 00:00–06:04 e publicată în `data/`,
  dar din ea nu s-au generat scenarii. Pentru 28.10 se folosesc toate scenariile generate de `romana.bridge.scenarii_zi`
  și `romana.bridge.indisciplinat`, adică `zi_2026-10-28_*` și `indisciplinat_zi_2026-10-28_*`, cu capacitatea
  calibrată, implicită din 28.10 (§ 6.4). Rularea se face pe seed-urile 1–10, cu ambele comportamente. Se compară
  programul realist, agentul oficial, E3, E13, planul fix, actuated, planurile 12/14/12 și 16/10/12 și cele două
  programe din planuri fixe pe categorii de trafic: `TOD_FIX`, care stabilește categoria după numele scenariului, și
  `TOD_DEBIT`, care o stabilește după debit. Înainte de generarea scenariilor se verifică și dacă înregistrarea zilei
  a fost continuă (`romana.vision.calitate`, § 4.6). Joi 29.10, dacă e colectată complet, servește ca zi de
  confirmare, după regula de mai sus. Pe 29.10, colectarea s-a oprit 13 minute, 08:33–08:46, pentru repornirea
  calculatorului, după fereastra fixă de dimineață 07:30–08:30. Sferturile de oră 08:30–09:00 se exclud din alegerea
  ferestrelor cu `scenarii_zi --exclude 08:30-09:00` (§ 4.6), iar restul zilei servește la confirmare.
- **Ce urmează.** Geamănul în timp real (`live_twin.py`) primește câștigătorul prin setarea `VARIANTA_PROGRAM`, iar
  autorul a aprobat ca această trecere să se facă automat și să fie documentată. Variantele `e13`, `plan_scurt` și
  `tod_debit` și pragurile noi au fost introduse în cod înainte de test. Planurile fixe rulează acum în geamăn cu
  duratele exacte, urmărite secundă cu secundă; înainte, o verificare la fiecare 5 s le rotunjea în sus. Dacă
  dispeceratul nu dă nicio comandă, geamănul pornește acum în modul „program”; înainte pornea cu agentul oficial. În
  timp real, cazul de trafic se alege după debitul intervalului curent de 15 minute. Când debitul e aproape de un
  prag, programul poate deci comuta mai des decât în evaluare, unde cazul vine din media orei. Capacitatea calibrată
  a fost implicită în geamănul în timp real între 28.10 și 2.11 (§ 6.4); din 2.11, el rulează pe rețeaua și pe tipurile
  de vehicule ale geamănului corectat, cu `tau` = 1,0 s (§ 5.5, § 6.5). Dacă un plan fix câștigă, verzile lui scurte ar trebui
  verificate față de timpii de degajare a pietonilor înainte de o aplicare reală (§ 10). Rezultatul testului este
  în § 9.10.

**Limitele testului din 26.10.** Testul acoperă o singură zi lucrătoare, rulată pe 10 seed-uri; tabelul de mai sus
folosește doar seed-urile 1–5. Agenții sunt antrenați pe geamănul cu capacitate implicită. Ziua de test a contribuit
și la calibrare, prin factorii de corecție și prin intervalul `tau`. Reantrenarea pe ziua de luni cu capacitatea
calibrată (E14) nu a întrecut E13 (§ 9.5), iar reantrenarea pe mai multe zile rămâne un pas următor (§ 10). Planurile
fixe scurte și agenții folosesc același verde minim de 10 s, iar modelul nu le impune separat timpul de degajare a
pietonilor (§ 10).

### 9.10 Testul pe miercuri 28.10 și confirmarea pe joi 29.10, retrase pe 2.11: câștigase planul fix scurt 12/14/12

> **Corectură din 2.11.2026.** Acest subcapitol stă pe geamănul cu coliziuni și teleportări (§ 6.5), deci concluziile lui nu mai sunt
> valabile, inclusiv câștigul planului 12/14/12. Pe geamănul corectat, planul 12/14/12 este cel mai slab plan încercat la vârf. Tot pe
> 2.11 a căzut și ipoteza că semaforul de azi are ciclul de ≈91 s al planului de referință, pe care textul de mai jos îl numește „planul
> fix actual”: camera măsoară ziua un ciclu de ≈125–155 s (§ 6.5). Textul de mai jos rămâne ca istoric al lucrului.
>
> *Completare din 6.11:* pe 2–5.11, ciclul, măsurat din nou din cameră, a avut mediana zilei de ≈135–137 s, iar un ciclu de ≈91 s
> nu apare (§ 6.5). Ce s-a hotărât după corectură e în § 9.11: pe ziua de validare, 4.11, niciun candidat nu a trecut, deci în geamănul
> în timp real rămâne planul observat, 72/48/3.

**Pe scurt.** Testul final al proiectului s-a făcut pe datele de miercuri 28.10, o zi lucrătoare nouă. El a comparat
trei candidați, fixați dinainte, cu „programul realist”, strategia folosită atunci de geamănul digital în timp real.
A câștigat cel mai simplu candidat, planul fix scurt 12/14/12, ale cărui numere sunt secundele de verde ale celor
trei faze: nord–sud, est–vest și pietoni. Cu el, participanții la trafic pierd în total cu 6,9% mai puțin timp decât
cu programul realist, iar câștigul vine mai ales de la pietoni, care așteaptă mai puțin la treceri. Datele zilei
următoare, joi 29.10, au confirmat rezultatul.

Testul a urmat protocolul fixat dinainte (§ 9.9) și s-a făcut automat, în noaptea de 28 spre 29.10. Lanțul de
prelucrare a pornit la 00:15 și s-a încheiat la 02:27, fără nicio intervenție manuală. Pașii au fost: verificarea
continuității înregistrării, renumărarea traficului cu zonele corectate, publicarea jurnalului de traiectorii,
construirea scenariilor, simularea strategiilor, analizele și, la sfârșit, aplicarea regulii de decizie
(`romana.control.decizie`). Fișierele sunt în `docs/rezultate/`: `test_28_*.csv` și `decizie_2026-10-28*.json`
(Anexa A). Confirmarea pe joi 29.10 s-a făcut cu același lanț, în noaptea următoare, și este descrisă la sfârșitul
subcapitolului.

- **Ziua de test.** Ziua de 28.10 a fost înregistrată continuu, de la 00:10 la 24:00. Colectarea repornise chiar
  atunci, la 00:10. Calitatea înregistrării a fost ca pe 25–26.10 (§ 4.6): golurile de peste 1 s apar la 1–6% din
  traiectorii, iar densitatea este de 2,1–4,9 puncte pe secundă de traiectorie. Renumărarea cu zonele corectate pe
  28.10 dă, în 96 de intervale de 15 minute, 58 557 de intrări, 24 029 de viraje complete și 26 904 pietoni. Un viraj
  complet este un vehicul urmărit de la brațul pe care intră până la cel pe care iese. Jurnalul publicat are
  157 572 de traiectorii de vehicule.

  Din aceste date, `scenarii_zi` a ales patru ferestre de câte o oră (§ 5.4). Debitul lor este debitul echilibrat,
  adică media dintre numărul vehiculelor care intră în piață și numărul celor care ies (§ 9.9):

  | Fereastra | Intervalul orar | Debitul echilibrat |
  |---|---|---|
  | liniștit | 03:30–04:30 | 56 veh/h |
  | dimineața | 07:30–08:30 | 4 093 veh/h |
  | vârful | 12:15–13:15 | 4 934 veh/h |
  | seara | 17:30–18:30 | 3 010 veh/h |

  Lor li se adaugă două variante de sensibilitate, cu cererea de trafic înmulțită cu 1,2 și, respectiv, cu 0,8:
  vârful ×1,2 (5 921 veh/h) și liniștitul ×0,8 (44 veh/h). Fiecare dintre cele șase se simulează o dată cu
  participanți disciplinați și o dată cu participanți indisciplinați, deci rezultă 12 scenarii.

  Fiecare scenariu se simulează cu seed-urile 1–10. Seed-ul este valoarea care pornește generatorul de numere
  aleatoare al simulării. Plecările sunt fixate în scenariu, deci un seed schimbă doar felul în care conduc șoferii. O combinație
  scenariu–seed se numește pereche: pe ea, strategiile se compară în exact aceleași condiții. Rezultă 120 de perechi.
  Diferențele dintre strategii se judecă pe perechi, cu testul statistic Wilcoxon. Valoarea p arată cât de probabilă
  ar fi o diferență cel puțin la fel de mare dacă strategiile ar fi, de fapt, la fel de bune. Sub 0,05, diferența se
  consideră semnificativă, adică greu de pus pe seama întâmplării.

  Au fost simulate șapte strategii. Patru dintre ele funcționează fără învățare: planul fix de referință 36/28/12,
  metoda actuated și planurile scurte 12/14/12 și 16/10/12. Planul fix de referință este ipoteza proiectului pentru
  programul actual al semaforului, pe care camera a infirmat-o pe 2.11 (§ 6.5), iar metoda actuated prelungește verdele
  cât timp detectoarele văd vehicule.
  Celelalte trei sunt agenți de inteligență artificială antrenați în simulare: agentul oficial, E3 și E13. În total
  au fost 840 de simulări, care au durat ≈2 h pe 11 procese paralele. Programele pe cazuri de trafic, adică
  programul realist și `TOD_DEBIT`, își aleg strategia după cât trafic este. Ele nu s-au simulat separat: rezultatul
  lor se compune din simulările componentelor, după cazul de trafic al fiecărui scenariu.

- **Fereastra liniștită a căzut pe o încetinire a prelucrării.** Pe 26.10, înregistrarea pornise abia la 09:11, așa
  că fereastra liniștită fusese seara, la 1 213 veh/h. Pe 28.10, ziua a fost înregistrată întreagă, iar fereastra
  liniștită a ajuns noaptea, la 03:30–04:30. Tocmai atunci, între 03:46 și 04:28, calculatorul a prelucrat de 4–5
  ori mai puține cadre video pe secundă. Cauza cea mai probabilă este validarea agentului E14, care rula în paralel pe
  același calculator. La ≈1,4 cadre/s, urmărirea pierde vehiculele în mișcare, pentru că acestea se mută prea mult de
  la un cadru la altul (§ 4.6). Pe fiecare interval de 15 minute, numărul vehiculelor urmărite scade de la 150–240 la
  40–50, iar 80–85% dintre ele sunt mașini parcate. Pentru comparație, înainte de 03:30 și după 04:30, debitul
  echilibrat este de ≈190–450 veh/h. Prin urmare, debitul scenariilor „liniștit”, de 56 și 44 veh/h, este
  subestimat, iar cazul de trafic lejer nu e reprezentat corect în acest test. Fenomenul a fost descris întâi,
  greșit, ca o imagine înghețată. Verificarea directă de pe 29.10 a arătat că imaginea era vie (§ 4.6).

  **Pentru specialiști.** Rata cadrelor prelucrate e normală înainte de ≈03:05 și de la ≈04:47. Între aceste ore, în
  afara încetinirii puternice, ea e doar ușor redusă: pasul median dintre două puncte consecutive ale unei traiectorii
  este de 0,25–0,36 s.

  Efectul asupra deciziei este însă neglijabil. Noaptea se pierd cel mult ≈1,2 h pe simulare, iar toate orele
  pierdute noaptea, adunate, reprezintă doar 0,05% din total. Fără cele 40 de perechi de noapte, regula alege tot
  planul 12/14/12, chiar mai clar: pe cele 80 de perechi rămase, p = 0,000005 față de programul realist, iar separat
  p = 0,0004 cu participanți indisciplinați și 0,002 cu participanți disciplinați. `TOD_DEBIT` rămâne la egalitate cu
  el (p = 0,47). Media schimbărilor relative pe perechi, adică media procentelor calculate pereche cu pereche, are
  totuși un neajuns: în ea, o pereche de noapte, cu o pierdere foarte mică, cântărește cât una de la vârf. De aceea,
  mai jos se dă, pe lângă pierderea totală, care este criteriul regulii, și media pe cele 80 de perechi fără noapte.

- **Decizia.** Regula de decizie (§ 9.9) alege candidatul cu cea mai mică pierdere totală de timp, dar numai dintre
  candidații eligibili. Un candidat e eligibil dacă e semnificativ mai bun decât programul realist și nu iese
  semnificativ mai slab decât el în niciunul dintre cele două comportamente, luat separat. Dacă primii doi candidați
  eligibili nu se deosebesc semnificativ, câștigă cel mai simplu de pus în practică. Pe 28.10, toți cei trei
  candidați sunt eligibili:

  | Candidatul, de la cel mai simplu | Pierderea totală (h) | Față de programul realist | Diferența medie pe pereche | Perechile în care e mai bun (fără noapte) | Wilcoxon p: toate perechile / indisciplinați / disciplinați |
  |---|---|---|---|---|---|
  | planul fix 12/14/12 | 57 526 | −6,9% | −35,6 h | 60 / 120 (57 / 80) | 0,001 / 0,022 / 0,023 |
  | `TOD_DEBIT`: 16/10/12 la trafic lejer și mediu, 12/14/12 la trafic intens | 57 364 | −7,2% | −37,0 h | 60 / 120 (60 / 80) | 0,0002 / 0,033 / 0,002 |
  | agentul E13 (`ppo_romana_cal`) | 58 123 | −6,0% | −30,7 h | 74 / 120 (56 / 80) | 0,0001 / 0,048 / 0,0006 |
  | programul realist, în vigoare | 61 802 | – | – | – | – |

  Dintre candidați, cea mai mică pierdere totală o are `TOD_DEBIT`. Diferența față de planul 12/14/12 este de doar
  0,3% și nu e semnificativă (Wilcoxon p = 0,90). Regula alege atunci candidatul mai simplu: **planul fix 12/14/12**.
  În cod, alegerea se scrie `VARIANTA_PROGRAM = "plan_scurt"`. Nici E13 nu se deosebește semnificativ de el
  (p = 0,82). Pe 29.10, geamănul digital în timp real a trecut pe planul 12/14/12 (§ 5.5), iar dispeceratul îl
  afișa la modul „Program pe cazuri de trafic”. Autorul aprobase dinainte ca trecerea să se facă automat. Din 2.11, după
  retragerea testului, geamănul în timp real pornește pe planul observat, 72/48/3 (§ 5.5), iar dispeceratul numește modul
  „Planul observat” (§ 8).

- **Regula inițială pentru E13** ar fi fost îndeplinită. Înainte de schimbarea protocolului, E13 era singurul
  candidat. Regula cerea ca el să bată semnificativ programul realist pe toate perechile și să nu iasă semnificativ
  mai slab în niciunul dintre comportamente (§ 9.9). Pe 28.10, față de programul realist, E13 reduce pierderea în
  medie cu 30,7 h pe pereche, adică cu 6,0% din total, cu p = 0,0001 pe toate perechile. E mai bun și în fiecare
  comportament, luat separat: p = 0,048 cu participanți indisciplinați și 0,0006 cu participanți disciplinați.
  Așadar, după regula inițială, E13 ar fi înlocuit programul realist. Înainte de test s-a adoptat însă regula „cel
  mai bun câștigă”, iar după ea E13 e echivalent cu planul 12/14/12 și pierde la simplitate.

- **Toate strategiile**, pe cele 120 de perechi, apar în tabelul următor. Ultima coloană compară cu planul fix doar
  cele 80 de perechi fără noapte: media relativă pe perechi și, între paranteze, numărul perechilor în care strategia
  e mai bună.

  | Strategia | Pierderea totală (h) | Față de planul fix | Față de programul realist | Fără noapte, față de planul fix: media pe perechi (mai bun în) |
  |---|---|---|---|---|
  | planul 16/10/12 (raportat, nu candidat) | 56 747 | −7,9% | −8,2% | −8,1% (66 / 80) |
  | `TOD_DEBIT` | 57 364 | −6,9% | −7,2% | −7,4% (63 / 80) |
  | **planul 12/14/12 (câștigătorul)** | **57 526** | **−6,7%** | **−6,9%** | **−6,2% (59 / 80)** |
  | agentul oficial (raportat, nu candidat) | 57 823 | −6,2% | −6,4% | −5,1% (65 / 80) |
  | E13 | 58 123 | −5,7% | −6,0% | −4,8% (56 / 80) |
  | planul fix de referință 36/28/12 | 61 647 | – | −0,3% | – |
  | programul realist | 61 802 | +0,3% | – | +1,6% (43 / 80) |
  | E3 | 61 804 | +0,3% | 0,0% | – |
  | actuated | 67 871 | +10,1% | +9,8% | +13,1% (5 / 80) |

  `TOD_FIX` nu apare separat în tabel. El este programul din planuri fixe raportat în § 9.9, care alege planul după
  numele scenariului. Ziua de 28.10 nu are fereastră de prânz, așa că `TOD_FIX` folosește 16/10/12 noaptea și
  12/14/12 în rest. Practic, el coincide cu planul 12/14/12: 57 527 h.

  Pe comportamente, câștigătorul reduce pierderea față de programul realist cu 8,3% când participanții sunt
  indisciplinați, de la 31 036 h la 28 461 h, și cu 5,5% când sunt disciplinați, de la 30 766 h la 29 065 h.

  Programul realist iese practic egal cu planul fix. Motivul: la trafic mediu și intens, el folosește agentul E3,
  iar E3 nu mai bate planul fix pe 28.10 (+0,3% în tabelul de mai sus). Pe 26.10, E3 câștigase semnificativ doar cu
  participanți disciplinați (§ 9.9).

- **Strategiile raportate care nu erau candidați.** Planul 16/10/12, aplicat singur toată ziua, are cea mai mică
  pierdere totală a zilei: 56 747 h, cu 1,4% sub planul 12/14/12. Agentul oficial, aplicat singur, are 57 823 h.
  Niciunul nu se deosebește semnificativ de planul 12/14/12: p = 0,51 pentru planul 16/10/12 și 0,34 pentru agentul
  oficial. În orice caz, lista candidaților s-a fixat înainte de test, iar schimbarea ei după rezultate ar însemna
  alegerea pe datele de test. În plus, pe validare (26.10), 12/14/12 fusese mai bun decât 16/10/12 la trafic intens,
  iar pe 28.10 ordinea s-a inversat. Diferența dintre cele două planuri scurte se pierde deci în variațiile
  întâmplătoare de la o zi la alta.

  Concluzia care părea atunci solidă era alta: **în geamănul de atunci, ciclurile scurte (≈53 s) băteau ciclul de ≈91 s
  al planului de referință și programul realist**. A căzut și ea pe 2.11: ziua, semaforul real are un ciclu de
  ≈125–155 s, nu de ≈91 s, iar pe geamănul corectat planurile scurte nu duc traficul la orele încărcate (§ 6.5). Între cele
  două planuri scurte, ca și între ele și agenții E13 și oficial, diferențele nu sunt semnificative. În schimb, E3,
  aplicat singur, pierde cu 7,4% mai mult decât planul 12/14/12 (p = 2·10⁻⁵).

- **Pe cazuri de trafic.** Cazul unei ferestre se stabilește după debitul ei echilibrat: lejer sub 2 400 veh/h,
  intens peste 4 100 veh/h și mediu între ele. Tabelul dă pierderea totală pe fiecare caz, în ore:

  | Cazul și ferestrele lui | Programul realist | Planul fix | 12/14/12 | `TOD_DEBIT` | E13 | Agentul oficial | 16/10/12 |
  |---|---|---|---|---|---|---|---|
  | lejer: noaptea, 44–56 veh/h, debit subestimat din cauza prelucrării încetinite | 30,2 | 32,5 | 32,4 | 33,0 | 30,7 | 30,2 | 33,0 |
  | mediu: seara, 3 010 veh/h, și dimineața, 4 093 veh/h | 20 122 | 19 828 | 17 913 | 17 751 | 18 335 | 18 403 | 17 751 |
  | intens: vârful, 4 934 veh/h, și vârful ×1,2 | 41 650 | 41 787 | 39 580 | 39 580 | 39 758 | 39 390 | 38 963 |

  Față de programul realist, planul 12/14/12 reduce pierderea cu 11,0% la trafic mediu și cu 5,0% la trafic intens.
  Noaptea, în schimb, cei doi agenți, E13 și agentul oficial, sunt mai buni: în total, pe cele 40 de simulări de
  noapte, cu ei se pierde cu ≈2 h mai puțin timp decât cu planul 12/14/12.

- **Câștigul vine de la pietoni.** Pierderea de timp pe tipuri de participanți, în ore, pe cele 120 de perechi:

  | Tipul de participant | Planul fix | Programul realist | 12/14/12 | E13 |
  |---|---|---|---|---|
  | autoturisme | 21 719 | 22 599 | 22 097 | 22 865 |
  | autobuze și troleibuze | 674 | 709 | 685 | 713 |
  | camioane | 1 340 | 1 389 | 1 352 | 1 393 |
  | motociclete și bicicliști | 67 | 79 | 70 | 81 |
  | pietoni | 37 847 | 37 026 | 33 322 | 33 071 |
  | total | 61 647 | 61 802 | 57 526 | 58 123 |

  Față de planul fix actual, tot câștigul planului 12/14/12 vine de la pietoni, care pierd cu 12,0% mai puțin timp.
  Cu un ciclu de ≈53 s în loc de ≈91 s, verdele lor vine mai des, deci ei așteaptă mai puțin la treceri. Vehiculele
  pierd puțin mai mult timp: +1,7% autoturismele și autobuzele, +0,9% camioanele.

  Față de programul realist, planul 12/14/12 reduce pierderea cu 2,2% la autoturisme, cu 3,3% la autobuze, cu 2,6%
  la camioane și cu 10,0% la pietoni. Bicicliștii pierd cu un sfert mai puțin, 31 h față de 41 h, iar motocicletele
  rămân practic la fel, 39 h față de 38 h.

  Și agenții câștigă tot prin pietoni. Față de planul fix, E13 are pierderea pietonilor la −12,6%, iar pe cea a
  vehiculelor la +4…+6%.

- **Măsura pe persoană**, raportată doar informativ (§ 9.9), socotește orele pierdute de oameni: orele pierdute de un
  vehicul se înmulțesc cu numărul de persoane din el. Ea dă același câștigător la toate cele trei ipoteze despre
  câți călători are un autobuz: planul 12/14/12. Față de programul realist, planul reduce orele-persoană pierdute cu
  6,0%, 5,6% și 5,2%, la 20, 40 și, respectiv, 70 de călători pe autobuz. Și aici e la egalitate cu `TOD_DEBIT`
  (p = 0,49 / 0,80 / 0,91). E13 rămâne eligibil la 20 și 40 de călători, dar nu și la 70 (p = 0,056). Pietonii
  reprezintă 46%, 39% și 32% din orele-persoană, iar călătorii din autobuze și troleibuze 18%, 30% și 43%.

  **Pentru specialiști.** Pe persoană, media relativă pe perechi are semnul opus: +3,0…+4,6% pentru planul 12/14/12.
  Explicația e noaptea: acolo pierderea e aproape nulă, iar un singur autobuz oprit la roșu schimbă mult procentul.
  Regula judecă totuși diferența în ore (§ 9.9). Cu media relativă, niciun candidat nu ar fi eligibil pe persoană.

- **Față de validare.** Pe ziua de validare, 26.10, cu seed-urile 11–15 și fără noapte, planul 12/14/12 dăduse
  −9,3% față de planul fix, în media pe perechi. Pe ziua de test, tot fără noapte, dă −6,2% și e mai bun în 59 din
  80 de perechi, iar pierderea totală, pe toate cele 120 de perechi, scade cu 6,7%. Sensul e același, iar efectul e
  ceva mai mic, cum e de așteptat pe o zi nouă, nefolosită la alegere.

- **Reverificarea pragurilor.** Autorul a cerut ca pragurile dintre cazuri să fie reverificate pe fiecare zi nouă.
  Pe 28.10, ferestrele se împart între cazuri ca pe 26.10: liniștitul la „lejer”, seara la „mediu” și vârful la
  „intens”. Dimineața, care pe 28.10 intră tot la „mediu”, are 4 093 veh/h, cu doar 7 veh/h sub pragul de 4 100.
  O dimineață puțin mai aglomerată ar trece deci la „intens”. Pe 28.10, aceleași planuri scurte sunt cele mai bune
  și la trafic mediu, și la trafic intens, la 1–2% unul de altul. Datele nu cer așadar o treaptă intermediară, iar
  pragurile rămân 2 400 / 4 100 veh/h. Pentru câștigător, pragurile nici nu contează: planul 12/14/12 e același în
  toate cazurile, deci nu comută.

  Ziua de test nu acoperă însă cazul lejer real. Noaptea, debitul a fost subestimat din cauza prelucrării
  încetinite, iar intervalul 1 200–2 400 veh/h, care apare seara târziu, nu a intrat în nicio fereastră. Faptul că
  planul câștigător nu comută are și un avantaj practic. O încetinire a prelucrării, ca aceea din noaptea de 28.10,
  coboară de câteva ori debitul măsurat. Un program pe cazuri ar comuta atunci pe „lejer”, pe când un plan fix nu se
  schimbă.

- **Verdele pe treceri.** Un ciclu mai scurt ar putea lăsa pietonilor prea puțin timp de traversare. Verificarea de
  fezabilitate, făcută cu `romana.control.treceri`, arată dacă planul se poate aplica în realitate. Semaforul pieței
  comandă 7 treceri, lungi de 6,4–12,8 m. Patru dintre ele au verde doar în faza de pietoni. Faza aceasta are 12 s în
  toate planurile fixe din grilă, deci și în planul de referință. Pe aceste patru treceri, planul 12/14/12 nu
  scurtează verdele: el rămâne de 12 s pe ciclu, doar că vine mai des, la ≈53 s în loc de ≈91 s. Celelalte trei
  treceri au verde și într-o fază de vehicule, alăturată fazei de pietoni, așa că verdele lor ține neîntrerupt peste
  ambele faze. Acest verde continuu scade de la 45–53 s la 29–31 s, dar rămâne peste dublul timpului de traversare la
  1,0 m/s, care e de 6,4–12,8 s. Prin urmare, cu planul câștigător, nicio trecere nu are mai puțin de 12 s de verde pe
  ciclu, la fel ca în planul de referință.

  Rămâne de verificat, după normele de proiectare, faza de pietoni de 12 s de pe trecerea cea mai lungă, de 12,8 m.
  Traversarea ei durează 10,7 s la 1,2 m/s și 12,8 s la 1,0 m/s, iar după verde urmează 5 s de tranziție până la
  faza următoare. Întrebarea privește la fel și planul de referință. Punctul următor arată că o fază de pietoni mai
  lungă nu schimbă concluzia.

- **Sensibilitatea la o fază de pietoni mai lungă.** Verificarea aceasta s-a făcut după test și nu schimbă decizia.
  Timpul de degajare este timpul de care are nevoie un pieton pornit pe trecere la sfârșitul verdelui ca să ajungă
  pe partea cealaltă. Ghidurile europene îl calculează cu o viteză de mers de 1,2 m/s. În ghidurile german și
  britanic, o viteză mai mică, de până la 1,0 m/s, se folosește doar în cazuri speciale, de pildă acolo unde trec
  mulți pietoni lenți. Unele orașe, ca Singapore și Toronto, folosesc ca regulă 1,0 m/s[^rilsa][^trl-viteza]. Pentru
  România nu am găsit o normă publică. Pe trecerea de 12,8 m, degajarea durează ≈10,7 s, iar modelul are după faza de
  pietoni doar 5 s de tranziție.

  De aceea, testul s-a refăcut cu faza de pietoni prelungită cu 6 s, la 18 s, atât în planul scurt, cât și în planul
  de referință. Au fost 240 de simulări, pe aceleași scenarii și seed-uri (`sens_pietoni_28_*.csv`). Cu planul
  12/14/18, pierderea totală este de 56 535 h, cu 7,9% mai mică decât cu planul 36/28/18, de 61 359 h. Planul scurt
  e mai bun în 92 din 120 de perechi (Wilcoxon p < 0,000001) și în ambele comportamente (p = 0,00001 / 0,00008).
  Față de planul 12/14/12 este echivalent (p = 0,96): pietonii mai câștigă 3%, autoturismele, autobuzele și
  camioanele pierd 0,3–1,6%, iar motocicletele și bicicliștii pierd câteva ore.

  Avantajul ciclului scurt rămâne deci și dacă normele ar cere o fază de pietoni mai lungă. Estimarea e ușor
  favorabilă pietonilor: în simulare, cele 6 s în plus sunt verde pentru pietoni, nu doar timp de degajare. Pentru
  vehicule, costul ciclului mai lung e același, fie că cele 6 s sunt verde, fie că sunt timp de degajare. Geamănul
  digital în timp real a rămas pe 12/14/12, varianta decisă după regulă, până la retragerea din 2.11. La vremea aceea,
  dacă normele ar fi cerut o fază mai lungă, 12/14/18 ar fi fost candidatul firesc pentru o validare nouă. Pe geamănul
  corectat, însă, planurile scurte nu duc traficul la orele încărcate (§ 6.5), iar geamănul în timp real pornește pe
  planul observat, 72/48/3 (§ 5.5).

**Confirmarea pe joi 29.10.** Pe scurt: pe ziua de după test, cu planul 12/14/12 participanții la trafic au pierdut
din nou semnificativ mai puțin timp decât cu programul realist, deci planul a rămas atunci în geamănul digital în timp real.
Câștigul venea tot de la pietoni. Și confirmarea s-a făcut pe geamănul cu coliziuni, deci a fost retrasă pe 2.11, odată cu
testul (§ 6.5); de atunci, geamănul în timp real pornește pe planul observat, iar regulile noi sunt în § 9.11.

Lanțul confirmării a pornit singur pe 30.10, la 00:15, și s-a încheiat la 03:20, fără intervenție manuală și fără
erori. A verificat continuitatea înregistrării, a refăcut numărarea, a publicat jurnalul, a construit scenariile, a
simulat strategiile, a făcut analizele, apoi a aplicat regula de confirmare, cu comanda
`romana.control.decizie --confirma PLAN_12_14_12`. La final, cu titlu informativ, a refăcut și decizia, folosind doar
datele zilei noi. La construirea scenariilor, opțiunea `--exclude 08:30-09:00` a scos din alegerea ferestrelor
sferturile de oră atinse de oprirea de dimineață. Fișierele sunt în `docs/rezultate/`: `test_29_*.csv`,
`confirmare_2026-10-29.json` și `decizie_2026-10-29*.json` (Anexa A).

**Pentru specialiști.** Codul folosit de lanț n-a mai fost schimbat după 12:34 pe 29.10, iar schimbările din acea zi
nu ating regula. În `scenarii_zi` au intrat grila completă de 15 minute, cu care nicio fereastră nu mai trece peste
un sfert de oră fără date, opțiunea `--exclude` și opțiunea `--fara-incetinite`, oprită implicit. În `calitate` au
intrat verificarea ratei de cadre pe sferturi de oră, cu tabelul scris de `--out-15min`, și citirea jurnalului ca în
`recount`, cu ultimul bloc incomplet sărit: lanțul a citit jurnalul la 00:15, cât încă se scria. În `decizie`,
schimbarea privește doar afișarea diferențelor în ore. Ferestrele zilelor 21–28.10 au rămas identice (§ 4.6).

- **Ziua de confirmare.** Camera a înregistrat ziua de 29.10 de la 00:00 la 24:00. Colectarea s-a oprit doar 13
  minute, 08:33–08:46, pentru repornirea calculatorului, după fereastra fixă de dimineață. Golurile de peste 1 s apar
  la 1–3% din traiectorii, iar densitatea e de 3,2–4,9 puncte/s, adică puncte pe secundă de traiectorie. Niciun sfert
  de oră nu îndeplinește criteriul de prelucrare încetinită (§ 4.6). Renumărarea dă 60 691 de intrări, 27 128 de
  viraje complete și 24 678 de pietoni, în 96 de intervale de 15 minute. Un viraj complet este un vehicul urmărit de
  la intrare până la ieșire. Jurnalul publicat are 153 462 de traiectorii de vehicule,
  pregătite de lanț la 00:15–00:22. Atunci, jurnalul zilei avea toate fragmentele de traiectorie, în afară de unul
  singur, încheiat la 00:46: 238 524 din 238 525.

  `scenarii_zi` a ales cinci ferestre de câte o oră (§ 5.4). Debitul lor este debitul echilibrat, adică media dintre
  intrările și ieșirile numărate:

  | Fereastra | Ora | Debitul echilibrat, în veh/h |
  |---|---|---|
  | liniștitul | 03:15–04:15 | 442 |
  | dimineața | 07:30–08:30 | 4 322 |
  | prânzul | 12:00–13:00 | 4 816 |
  | vârful | 13:00–14:00 | 5 061 |
  | seara | 17:30–18:30 | 3 340 |

  Lor li se adaugă vârful ×1,2, cu 6 073 veh/h, și liniștitul ×0,8, cu 354 veh/h, adică aceleași ore cu traficul de
  vehicule înmulțit cu 1,2, respectiv cu 0,8. De data aceasta, fereastra liniștită e măsurată corect: noaptea nu are
  nicio încetinire. Cu ambele comportamente ale participanților rezultă 14 scenarii, iar pe seed-urile 1–10, 140 de
  perechi. O pereche este o combinație scenariu–seed, pe care strategiile se compară în aceleași condiții. Cele șapte
  strategii, aceleași ca pe 28.10, au însumat 980 de simulări, care au durat ≈3 h pe 11 procese.
- **Verdictul: confirmat.** Planul 12/14/12 pierde în total cu 7,0% mai puțin timp decât programul realist: 80 612 h
  față de 86 691 h, adică 43,4 h mai puțin pe pereche. E mai bun în 85 din 140 de perechi, iar testul Wilcoxon dă
  p = 7·10⁻⁸, deci diferența e semnificativă. Câștigă și cu fiecare comportament luat separat: −42,5 h pe pereche cu
  participanți indisciplinați, cu p = 0,0007, și −44,4 h cu participanți disciplinați, cu p = 0,00002. Protocolul
  cerea doar ca planul să nu iasă semnificativ mai slab, deci planul 12/14/12 a rămas atunci în geamănul în timp real.
- **Decizia refăcută doar pe 29.10.** Are rol informativ: regula nu se aplică din nou pe ziua de confirmare. Toți cei
  trei candidați sunt din nou eligibili: fiecare întrece semnificativ programul realist și nu e semnificativ mai slab
  cu niciun comportament. Pierderile lor totale sunt de 80 612 h pentru planul 12/14/12, 81 407 h pentru `TOD_DEBIT`
  și 83 376 h pentru E13, adică −7,0%, −6,1% și −3,8% față de programul realist. De data aceasta, planul 12/14/12 are
  și cea mai mică pierdere totală dintre candidați. Față de `TOD_DEBIT`, diferența nu e semnificativă, cu p = 0,24,
  deci câștigătorul ar fi același.

  Pe cele două zile reunite, de test și de confirmare, adică pe 260 de perechi, planul 12/14/12 dă −7,0% din
  pierderea totală față de programul realist, cu p = 4·10⁻¹⁰. Pentru fiecare comportament luat separat, p = 4·10⁻⁵ cu
  participanți indisciplinați și p = 2·10⁻⁶ cu participanți disciplinați. `TOD_DEBIT` dă −6,5% și e la egalitate cu
  planul 12/14/12, cu p = 0,64, iar E13 dă −4,7%.

  **Fără scenariile de seară (verificare din 1.11.2026).** Cifrele de mai sus privesc toată rețeaua simulată, nu doar piața.
  Seara, Lascăr Catargiu aproape nu mai este detectat (§ 4.3), deci scenariile de seară au puțin trafic de pe acest braț.
  Ca sensibilitate, totalurile s-au recalculat fără ele. Excluderea vine după test, deci nu schimbă decizia, ci arată cât
  se sprijină ea pe seară:

  | Zilele | Scenariile | Perechi | Planul 12/14/12 (h) | Față de programul realist | p | Față de planul de referință | `TOD_DEBIT` față de programul realist |
  |---|---|---:|---:|---:|---:|---:|---:|
  | 28 + 29.10 | toate | 260 | 138 138 | −7,0% | 4·10⁻¹⁰ | −6,9% | −6,5% |
  | 28 + 29.10 | fără seară | 220 | 117 806 | −5,7% | 6·10⁻⁶ | −5,1% | −6,2% |
  | 28.10 | toate | 120 | 57 526 | −6,9% | 0,0013 | −6,7% | −7,2% |
  | 28.10 | fără seară | 100 | 46 605 | −5,3% | 0,086 | −4,9% | −6,5% |
  | 29.10 | toate | 140 | 80 612 | −7,0% | 7·10⁻⁸ | −7,0% | −6,1% |
  | 29.10 | fără seară | 120 | 71 201 | −5,9% | 2·10⁻⁵ | −5,3% | −5,9% |

  Seara dă 31% din câștigul față de programul realist: 3 245 din 10 354 h. Câștigul rămâne semnificativ pe zilele reunite,
  dar pe 28.10 fără seară nu mai este, iar acolo regula ar alege `TOD_DEBIT`. Planul 12/14/12 a rămas în geamăn
  doar până pe 2.11, când testul a fost retras; de atunci rulează acolo planul observat, 72/48/3, iar la validarea din 4.11
  niciun candidat nu a trecut (§ 9.11).
- **Toate strategiile.** Tabelul le cuprinde pe toate, pe cele 140 de perechi din 29.10. Un procent negativ înseamnă
  mai puțin timp pierdut decât cu strategia din antetul coloanei. Ultimele două coloane lasă deoparte cele 40 de
  perechi de noapte, ca la testul din 28.10:

  | Strategia | Pierderea totală, în ore | Față de planul fix | Față de programul realist | Fără noapte: media pe perechi față de planul fix | Fără noapte: perechi în care e mai bună decât planul fix |
  |---|---|---|---|---|---|
  | **planul 12/14/12, câștigătorul** | **80 612** | **−7,0%** | **−7,0%** | **−7,5%** | **77 / 100** |
  | planul 16/10/12, raportat, nu candidat | 80 973 | −6,6% | −6,6% | −6,5% | 79 / 100 |
  | `TOD_DEBIT` | 81 407 | −6,1% | −6,1% | −6,0% | 77 / 100 |
  | agentul oficial, raportat, nu candidat | 82 654 | −4,6% | −4,7% | −4,8% | 68 / 100 |
  | E13 | 83 376 | −3,8% | −3,8% | −3,8% | 69 / 100 |
  | planul fix de referință 36/28/12 | 86 671 | – | 0,0% | – | – |
  | E3 | 86 688 | 0,0% | 0,0% | +0,1% | 46 / 100 |
  | programul realist | 86 691 | 0,0% | – | +0,1% | 46 / 100 |
  | actuated | 93 818 | +8,2% | +8,2% | +9,3% | 13 / 100 |

  Programul realist iese din nou practic egal cu planul fix, pentru că la trafic mediu și intens folosește E3. Între
  cele două planuri scurte, ordinea s-a inversat față de 28.10: acum 12/14/12 are pierderea cea mai mică, cu 0,4% sub
  16/10/12, dar diferența nu e semnificativă: p = 0,72. Ea rămâne deci în limitele variației întâmplătoare de la o zi
  la alta.

  Agentul oficial iese de data aceasta semnificativ mai slab decât planul 12/14/12: +2,5% din pierderea totală
  și +1,8% în media pe perechi, iar testul Wilcoxon dă p = 0,007. Pe 28.10, diferența nu fusese semnificativă, cu
  p = 0,34. E13 pierde și mai mult: +3,4% din total și +2,2% în media pe perechi. Totuși, față de planul 12/14/12,
  testul Wilcoxon nu iese semnificativ, cu p = 0,06, din cauza nopții: acolo E13 e mai bun în 39 din 40 de perechi,
  dar doar cu ≈0,3 h pe pereche. Fără noapte, E13 e mai bun doar în 40 din 100 de perechi, iar diferența devine
  semnificativă: testul Wilcoxon dă p = 0,002. Testul t pe toate perechile dă p = 0,0007. Între E13 și agentul
  oficial, diferența nu e semnificativă, cu p = 0,98.

  `TOD_FIX` nu apare în tabel. La fel ca planul 16/10/12 și agentul oficial, e doar raportat, nu candidat. El alege
  planul după numele scenariului, nu după debit: pe 29.10 a folosit 16/10/12 noaptea și la prânz, iar 12/14/12 în
  rest. Are cea mai mică pierdere totală a zilei, 80 094 h, cu 0,6% sub planul 12/14/12, pentru că la prânz 16/10/12
  a fost mai bun. Față de planul 12/14/12 e însă la egalitate: −0,5% în media pe perechi, cu p = 0,052.
- **Pe cazuri de trafic.** Cazurile se stabilesc după debitul echilibrat, cu pragurile de 2 400 și 4 100 veh/h: sub
  primul prag traficul e lejer, peste al doilea e intens, iar între ele e mediu. Pierderea totală, în ore:

  | Cazul și ferestrele lui | Programul realist | Planul fix | 12/14/12 | `TOD_DEBIT` | E13 | Agentul oficial | 16/10/12 |
  |---|---|---|---|---|---|---|---|
  | lejer: noaptea, adică liniștitul, cu 442 veh/h, și liniștitul ×0,8 | 274,4 | 294,9 | 281,1 | 279,4 | 269,2 | 274,4 | 279,4 |
  | mediu: seara, cu 3 340 veh/h | 11 007 | 11 500 | 9 411 | 10 207 | 10 641 | 10 159 | 10 207 |
  | intens: dimineața, cu 4 322 veh/h; prânzul, cu 4 816 veh/h; vârful, cu 5 061 veh/h, și vârful ×1,2 | 75 409 | 74 876 | 70 920 | 70 920 | 72 466 | 72 220 | 70 486 |

  Față de programul realist, planul 12/14/12 pierde cu 14,5% mai puțin timp la trafic mediu și cu 6,0% mai puțin la
  trafic intens. Noaptea pierde cu 2,4% mai mult, ≈7 h pe 40 de simulări: la trafic lejer, agenții rămân puțin mai
  buni, ca pe 28.10. La trafic mediu, 12/14/12 îl întrece acum cu 7,8% și pe 16/10/12, planul folosit acolo de
  `TOD_DEBIT`. Pe 28.10, la același caz, 16/10/12 fusese cu 0,9% mai bun.
- **Câștigul vine tot de la pietoni.** Pierderea pe tipuri de participanți, în ore, pe cele 140 de perechi:

  | Tipul de participant | Planul fix | Programul realist | 12/14/12 | E13 |
  |---|---|---|---|---|
  | autoturisme | 42 033 | 42 339 | 42 239 | 43 182 |
  | autobuze și troleibuze | 1 139 | 1 134 | 1 144 | 1 163 |
  | camioane | 2 442 | 2 456 | 2 457 | 2 492 |
  | motociclete și bicicliști | 119 | 126 | 121 | 138 |
  | pietoni | 40 937 | 40 636 | 34 652 | 36 400 |
  | total | 86 671 | 86 691 | 80 612 | 83 376 |

  Față de planul fix actual, cu planul 12/14/12 pietonii pierd cu 15,4% mai puțin timp, iar vehiculele cu 0,4–0,6%
  mai mult: autoturismele +0,5%, autobuzele +0,4%, camioanele +0,6%. Pe 28.10, situația fusese asemănătoare:
  pietonii −12,0%, vehiculele +0,9…+1,7%. Față de programul realist, autoturismele și camioanele rămân practic la
  fel: −0,2%, respectiv 0,0%. Autobuzele pierd cu 0,8% mai mult, iar pietonii cu 14,7% mai puțin.
- **Măsura pe persoană.** Ea socotește orele pierdute de fiecare om, nu de fiecare vehicul, deci un autobuz plin
  cântărește mai mult decât un autoturism. E doar raportată și nu schimbă decizia. La toate cele trei ipoteze despre
  numărul de călători dintr-un autobuz, câștigă tot planul 12/14/12. Spre deosebire de 28.10, el e aici semnificativ
  mai bun și decât `TOD_DEBIT`. E13 rămâne eligibil la 20 și 40 de călători, dar nu și la 70, unde nu mai e
  semnificativ mai bun decât programul realist: p = 0,14.

  | Călători pe autobuz | 20 | 40 | 70 |
  |---|---|---|---|
  | Planul 12/14/12 față de programul realist, din orele-persoană pierdute | −5,1% | −4,1% | −3,1% |
  | Valoarea p a diferenței față de programul realist | 1·10⁻⁸ | 3·10⁻⁸ | 7·10⁻⁷ |
  | Valoarea p a diferenței față de `TOD_DEBIT` | 0,004 | 0,002 | 0,002 |
  | Planul 12/14/12 față de programul realist, media schimbărilor relative pe perechi | −3,4% | −2,9% | −2,3% |
  | Ponderea pietonilor în orele-persoană | 34% | 28% | 23% |
  | Ponderea călătorilor din autobuze și troleibuze în orele-persoană | 20% | 33% | 46% |

  Cu noaptea măsurată corect, și media schimbărilor relative pe perechi are acum același semn ca diferența totală.
- **Față de validare și de test.** Față de planul fix, în media pe perechi fără noapte, planul 12/14/12 a dat −9,3% pe
  ziua de validare, 26.10, apoi −6,2% pe ziua de test și −7,5% pe ziua de confirmare. Din pierderea totală, pe
  ultimele două zile, a dat −6,7%, respectiv −7,0%. Sensul și ordinul de mărime se păstrează pe ambele zile noi,
  nefolosite la alegere.
- **Reverificarea pragurilor.** La cererea autorului, pragurile se reverifică pe fiecare zi nouă. Pe 29.10, ferestrele
  se împart altfel între cazuri. Dimineața, cu 4 322 veh/h, trece la „intens”; pe 28.10, cu 4 093 veh/h, stătea chiar
  sub prag, la „mediu”. Prânzul, fereastră nouă, cu 4 816 veh/h, e tot „intens”. Seara rămâne „mediu”, iar noaptea
  „lejer”. După protocol, pragurile se schimbă doar după o nouă validare, iar pentru câștigător nu contează: planul
  12/14/12 e același la orice trafic, deci nu comută. Nici acum datele nu cer o treaptă intermediară, adică un caz în
  plus, pentru că la trafic mediu și intens câștigă tot ciclurile scurte. Nici pe 29.10 nu intră în scenarii
  intervalul 1 200–2 400 veh/h, atins în acea zi la ≈05:45–06:30 și la ≈19:30–23:30, deci cazul lejer de zi rămâne
  netestat.
- **Ce rămânea atunci înainte de o aplicare reală:** verificarea fazei de pietoni de 12 s după normele de proiectare, adică
  dacă pietonii au destul timp să traverseze (§ 10). Dacă normele ar fi cerut mai mult, planul 12/14/18, cu faza de pietoni
  prelungită, păstra câștigul în geamănul de atunci. Această analiză de sensibilitate s-a făcut însă doar pe ziua de test,
  28.10, și e descrisă mai sus. Pe geamănul corectat, planurile scurte nu duc traficul la orele încărcate (§ 6.5), deci nici
  12/14/12, nici 12/14/18 nu mai sunt de aplicat; ce s-a hotărât apoi e în § 9.11.

Limitele testului și ale confirmării:

- Testul și confirmarea folosesc doar două zile lucrătoare noi, consecutive, din aceeași săptămână de octombrie.
- Pe 28.10, fereastra de noapte a cazului lejer a căzut pe o încetinire a prelucrării (§ 4.6); pe 29.10, noaptea e
  măsurată corect. Partea de zi a cazului lejer, 1 200–2 400 veh/h, n-a intrat însă în scenariile niciuneia dintre
  cele două zile.
- Agenții sunt antrenați pe geamănul cu capacitatea implicită.
- Verdele minim pentru pietoni nu este impus separat (§ 10).
- Geamănul în timp real comută după debitul măsurat pe 15 minute. Pentru câștigător asta nu contează, pentru că el
  nu comută.

### 9.11 Regulile pentru zilele noi, scrise înainte de a le vedea (1.11.2026)

**Pe scurt.** Zilele de 28 și 29.10 au ales planul din geamăn, deci nu mai pot fi folosite ca să aleagă altceva. Colectarea
merge mai departe din 1.11. Regulile de mai jos au intrat în istoricul public al depozitului pe 1.11, înainte de prima
prelucrare a unei zile noi, care pornește pe 2.11, la 00:15. Așa, o alegere potrivită după rezultat se poate vedea în istoric.
O schimbare făcută după acest moment se trece aici, cu data și motivul, și nu privește zilele deja prelucrate.

*Completare din 6.11:* cum s-a încheiat runda: din 2.11, odată cu geamănul corectat, un candidat trebuia să bată planul observat, 72/48/3, și semaforul rejucat
din cameră, iar o poartă verifica întâi, oră cu oră, dacă geamănul se potrivește cu camera. Poarta a trecut pe 8 din cele 12 ore
comparate la îngheț, din 25 și 26.10 și din 1 și 2.11, dar pe 0 din 5 ore pe 3.11 și pe 0 din 4 ore pe 4.11, ziua de validare, mai ales
fiindcă pe Dacia vest, în zilele lucrătoare, geamănul duce mult mai puține vehicule decât camera. Validarea a fost deci doar
descriptivă: niciun candidat nu a trecut, testul nu s-a deschis, iar runda s-a încheiat pe 5.11 fără un program nou. În geamăn rămâne
planul observat (`docs/rezultate/cor_decizie_2026-11-04.json`); asta nu arată că el e cel mai bun, ci doar că geamănul nu a putut
judeca. Programul real al semaforului, măsurat direct din cameră, fără geamăn, e în § 6.5.

*Completare din 8.11:* cele trei zile de după validare s-au prelucrat doar până la geamăn și poartă, fără strategii. Poarta a trecut
pe 1 din 5 ore pe 5.11, pe 1 din 4 ore pe 6.11 și pe toate cele 5 ore pe 7.11, sâmbăta, ziua de generalizare; pe Dacia vest, care nu
e un rând al porții, geamănul rămâne și sâmbăta sub cameră la vârf și la prânz. Pe 8.11, regula finală a răspuns că niciun candidat
nu a trecut de validare, deci a confirmat că runda zilelor noi s-a încheiat fără un program nou, iar în geamăn rămâne planul
observat, 72/48/3 (mai jos, la ziua de 7.11 și la regula finală din 8.11).

*(Regulile de aici până la „Schimbările din 2.11.2026” sunt cele scrise pe 1.11, lăsate cum erau, afară de notele în cursiv, ca să
se poată verifica în istoric. Unde le schimbă hotărârile din 2.11 și 3.11 de mai jos, acestea au întâietate: de pildă, referința a
devenit planul observat, 72/48/3, împreună cu semaforul rejucat, în locul planului 12/14/12; factorul pietonilor s-a înlocuit cu o
cerere efectivă; iar fără commit la termen runda s-ar fi suspendat, nu s-ar fi decis pe măsura veche.)*

**Ce rol are fiecare zi.**

| Zilele | Rolul | Ce se poate face cu ele |
|---|---|---|
| 25 și 26.10, 1, 2 și 3.11 | antrenare | antrenarea agenților, grilele de planuri și alcătuirea listei de candidați; rezultatele se pot privi oricum |
| 4.11 | validare | cernerea candidaților de pe listă, o singură dată, pe seed-urile 11–15 |
| 5 și 6.11 | test | doar testul candidaților trecuți de validare, pe seed-urile 1–10 |
| 7.11 (sâmbătă) | generalizare | aceiași candidați, pe o zi de weekend, pe seed-urile 1–10; se raportează și nu schimbă decizia |
| 28 și 29.10 | închise | nu intră la antrenare, la alegerea unei strategii sau la stabilirea pragurilor |
| 21, 22, 27 și 30.10 | fără rol | nu mai intră la antrenare, la alegerea unei strategii sau la stabilirea pragurilor |

Rolurile nu depind de vreme: sunt fixate acum, deși nu se știe ce vreme va fi în acele zile. O zi de validare, de test sau de
generalizare este completă dacă orele 07:30–08:30, 12:00–13:00 și 17:30–18:30 au date în fiecare sfert de oră și dacă
`romana.vision.calitate` nu găsește în ele niciun interval încetinit. Dacă vârful se suprapune peste una dintre aceste ore,
`scenarii_zi` o lasă deoparte, ca pe prânzul din 28.10, iar ziua rămâne completă. O zi nu pierde rolul din alt motiv: nici din
cauza vremii, nici a unui trafic neobișnuit, nici a rezultatelor.

Dacă ziua de validare nu este completă, validarea și cele două zile de test trec, în ordine, pe următoarele zile lucrătoare
complete. Dacă nu este completă o zi de test, rolul ei trece pe următoarea zi lucrătoare completă fără rol. Generalizarea rămâne
sâmbăta: dacă 7.11 nu este completă, trece pe 14.11. O zi care și-a pierdut rolul nu mai primește altul și nu intră nici la
antrenare. Lanțul nu verifică singur aceste condiții, așa că mutarea se scrie aici, cu motivul, și în `ROLURI` din
`romana.lant_zilnic`, înainte să fie prelucrată ziua care primește rolul.

Pe zilele de validare, de test și de generalizare, din ferestre se scot doar sferturile atinse de o oprire reală a colectării și
cele încetinite. *(La măsura nouă, un sfert e încetinit și când pasul median trece de 0,22 s, vezi § 4.6.)* O excludere dată de
mână se trece aici, cu ora opririi, și se comite înainte de a citi simulările zilei.

Prima zi nouă, 1.11, a început abia dimineața: are câteva minute din timpul prezentării bornei M1, apoi date continue de la
09:05. Nu are deci toate ferestrele, dar rămâne bună pentru antrenare, cu ce are. Sferturile de oră atinse de oprire și de
repornire, 08:00–09:15, sunt excluse din ferestre. *(Completare din 6.11: seara, după ce s-a scris acest paragraf, colectarea s-a oprit, anunțat, 21:44–22:48, deci datele de la 09:05 nu sunt continue, iar din ferestre sunt excluse și sferturile 21:30–23:00, vezi § 4.6.)*

**Ce se simulează noaptea.** Prelucrarea rulează singură, la 00:15, cu `romana.lant_zilnic`. Jurnalul fiecărui pas rămâne în
`outputs/lant/<zi>/`, iar rezultatele simulărilor în `outputs/validare/`, sub numele `test_<zi>_*`, oricare ar fi rolul zilei.
Nimic nu se copiază singur în documentație. Rezultatele zilelor de validare, de test și de generalizare se copiază în
`docs/rezultate/`, împreună cu `stare.json`, oricare ar fi ele, ca ordinea pașilor să se poată verifica. *(Pe măsura nouă, copia
lui se numește `stare_lant_cor_<zi>.json`.)*

* **Zilele de antrenare:** verificarea jurnalului, calitatea, numărătorile, publicarea jurnalului de vehicule, scenariile,
  simulările pe seed-urile 1–10 și analizele lor. Rezultatele nu decid nimic, dar pot sugera ce intră pe lista de candidați.
* **Ziua de validare:** la fel, dar pe seed-urile 11–15.
* **Zilele de test și de generalizare:** doar verificarea jurnalului, calitatea, numărătorile, publicarea jurnalului de vehicule
  și scenariile, care se comit așa cum au ieșit. Simulările pornesc abia după ce rezultatul validării este comis și numai dacă a
  rămas cel puțin un candidat, cu `python -m romana.lant_zilnic --zi <zi> --desigileaza --reia`, pentru toate cele trei zile.
  Lanțul rulează lista lui fixă de strategii; un candidat care nu e în ea și măsura nouă, dacă ea decide, se adaugă cu
  `romana.control.validare`, pe aceleași seed-uri. Rezultatele se citesc abia când toate sunt gata, nu zi cu zi.

**Două măsuri, ținute separat.** Verificarea bornei M1 a arătat că numărarea are două lipsuri: seara, Lascăr Catargiu aproape
nu mai este detectat, iar pietonii sunt numărați pe zone, deci unii de două ori. De aceea există două măsuri:

* **Măsura veche** folosește neschimbate fișierele `config/camera.json`, `config/demand.json` și `vtypes*`, împreună cu codul
  care numără și simulează, așa cum erau la commitul cu care pornește prelucrarea din 2.11, la 00:15. O schimbare de cod e
  permisă doar dacă dă aceleași rezultate, octet cu octet, pe zilele vechi. Așa, zilele noi rămân comparabile cu testele din 28
  și 29.10. Prelucrarea de noapte folosește această măsură.
* **Măsura nouă**, cu prefixul `cor_`, are zona din aval pe Lascăr Catargiu, pietonii numărați pe persoane și factorii de
  corecție verificați pe întuneric. Scenariile ei se fac și pentru 25 și 26.10. Nu există încă: intră ca variantă separată, cu
  fișiere proprii, și schimbă rezultatele vechi doar ca sensibilitate.

Rezultatele se pot aduna doar în cadrul aceleiași măsuri. Decizia se ia pe măsura nouă numai dacă zonele, factorii și codul ei au
un commit până pe 5.11, la 00:15, termenul listei de candidați. Ele se stabilesc doar din date și clipuri de până pe 3.11, iar
după acel commit nu se mai schimbă. Ce nu s-a putut verifica până atunci, de exemplu pe ploaie, rămâne ipoteză declarată. Fără
commit la termen, decizia se ia pe măsura veche, se spune deschis, iar E15 nu intră în această rundă. Termenul nu depinde de
rezultatele validării.

Vehiculele corectate se raportează separat de factorul pietonilor. Factorul se aplică pietonilor numărați pe persoane. Regula se
aplică la o singură valoare, 3,0, care păstrează cererea de pietoni din testele din 28 și 29.10: 2,5 pe numărările pe zone
înseamnă ≈3,0 pe persoane. Valorile 1,0, 1,5 și 2,5 sunt doar sensibilități, fiindcă valoarea factorului rămâne o ipoteză, și nu
pot schimba decizia.

**Cum se aleg candidații.** Lista candidaților se scrie aici, printr-un commit, de la cel mai simplu la cel mai complex, cel mult
trei. Termenul este 5.11, la 00:15, adică înaintea primei simulări a zilei de validare. După el, lista nu se mai schimbă, nici
dacă rolurile se mută, iar o strategie nouă nu mai poate intra în această rundă, oricât de bună ar ieși. Pe listă poate intra
orice strategie, chiar și planul de referință 36/28/12 sau programul realist, ca regula să poată merge și înapoi. Pe ziua de
validare se aplică, o singură dată, aceeași regulă ca la test, pe măsura de decizie: toate scenariile zilei, ambele
comportamente, seed-urile 11–15, pierderea totală în ore, față de planul 12/14/12. Testul se deschide doar pentru candidații
semnificativ mai buni decât planul 12/14/12 și care nu sunt semnificativ mai slabi în niciun comportament. Media procentelor pe
perechi se dă doar informativ.

**Ce poate schimba planul din geamăn.** *(Scris pe 1.11; din 2.11, planul 12/14/12 a ieșit din geamănul în timp real, iar un candidat
trebuie să bată planul observat, 72/48/3, și semaforul rejucat, vezi schimbările de mai jos.)* Planul 12/14/12 rămâne în geamăn. Reluarea testelor din 28 și 29.10 pe măsura nouă se
face abia după termenul listei, este doar o sensibilitate și nu poate schimba nimic. Planul se schimbă numai dacă un candidat
trecut de validare trece regula pe cele două zile de test reunite, aplicată o singură dată, cu planul 12/14/12 în locul
programului realist din § 9.10. Eligibil este candidatul semnificativ mai bun decât planul 12/14/12 și care nu este semnificativ
mai slab în niciun comportament. Dintre cei eligibili câștigă cel cu cea mai mică pierdere totală; dacă primii doi nu se
deosebesc semnificativ, câștigă cel mai simplu. Comanda este
`python -m romana.control.decizie <fișierele celor două zile de test> --in-vigoare PLAN_12_14_12 --candidati <lista>`.
Fișierele `decizie_<zi>.json` și `confirmare_<zi>.json` scrise de lanț compară tot cu programul realist și sunt doar descriptive.
O strategie care nu e pe listă se raportează, dar nu poate câștiga. Autorul poate refuza o schimbare care a trecut regula,
spunând de ce. Un candidat care n-a trecut-o nu se adoptă în această rundă.

Regula se aplică pe toate scenariile, cu seara cu tot, și pe validare, și la test. Separat, rezultatul se dă și fără scenariile
de seară, cu `romana.control.analiza --exclude "*seara*"`, fiindcă seara a adus 31% din câștigul față de programul realist pe
28–29.10. Această variantă nu schimbă decizia. Dacă alege altceva decât regula, se spune deschis.

Dacă lista e goală sau niciun candidat nu trece de validare, zilele de test și de generalizare rămân fără simulări, planul
12/14/12 rămâne în geamăn, iar rezultatul se notează aici *(din 2.11 rămâne planul observat, nu planul 12/14/12; așa s-a întâmplat
pe 4.11, vezi mai jos)*. La fel, planul rămâne dacă niciun candidat nu trece regula pe zilele
de test. În ambele cazuri, runda se încheie. O încercare nouă cere zile noi, cu roluri scrise înainte, nu aceleași zile cu alți
candidați. Dacă după deschiderea zilelor de test se găsește un defect și testul se reface, se publică ambele rezultate și
defectul se descrie; zilele și lista rămân aceleași.

**Pragurile.** Un program pe cazuri de trafic intră pe listă împreună cu pragurile lui, iar o variantă cu alte praguri este alt
candidat. Pe măsura nouă, debitele sunt mai mari, deci lista spune dacă programul folosește pragurile vechi, 2 400 și 4 100
veh/h, sau praguri noi. Praguri noi se calculează din zilele de antrenare, la jumătatea distanței dintre ferestre, ca pe 26.10.
După termenul listei nu se mai schimbă, nici pe validare, nici pe zilele de test. Măsura nouă are rezumatul ei de debite, separat
de cel al măsurii vechi, iar `romana.control.decizie` îl citește după prefixul `cor_`.

**Schimbările din 2.11.2026, cu motivul.** Geamănul pe care s-au scris aceste reguli rula cu coliziuni și teleportări în masă (§ 6.5), deci
regulile privitoare la planul 12/14/12 nu mai au sens așa cum sunt scrise. Toate schimbările de mai jos s-au făcut înaintea primei
simulări a zilei de validare, iar zilele de validare și de test nu au fost privite:

* Măsura nouă, `cor_`, folosește geamănul corectat. Măsura veche rămâne neatinsă și se calculează mai departe în fiecare noapte, doar
  pentru istoric, dar **nu mai poate decide nimic**. Dacă măsura nouă nu are commit la termen, runda se suspendă: nicio decizie nu se ia
  pe geamănul cu coliziuni.
* În locul planului 12/14/12, peste tot unde regula spune „față de planul 12/14/12”, un candidat trebuie să bată **și** planul observat,
  72/48/3, **și** semaforul rejucat (§ 6.5). Altfel, orice candidat ar trece ușor de un plan despre care știm acum că nu poate duce traficul.
  Semaforul rejucat contează doar pe orele acoperite cel puțin 80% de valuri măsurate. Comanda devine
  `python -m romana.control.decizie <fișiere> --in-vigoare PLAN_72_48_3 REAL --candidati <lista> --poarta <fișier>`. Planul 12/14/12 iese
  din geamănul în timp real.
* **Poarta.** Înainte de a citi rezultatele unei zile, `python -m romana.control.valideaza_geaman <scenariile zilei> --poarta <fișier>`
  compară geamănul cu camera, oră cu oră, pe rânduri numite: debitele de pe Magheru, Lascăr Catargiu și Dacia est, teleportările,
  ciocnirile văzute de SUMO și vehiculele rămase neintrate. O oră care nu trece iese din decizie, cu variantele ei. Dacă trec sub jumătate dintre ore, ziua e doar descriptivă.
  Măsurile se îngheață la un commit numit, înainte de a privi datele din 3.11.
* Dacă niciun candidat nu trece, rămâne planul observat, nu planul 12/14/12.
* Agentul E15 pornește prin imitarea planului observat, nu a planului 12/14/12, și alege doar între N–S și E–V. Comparația de la capăt se face cu cele două referințe de mai sus, rulate exact.
* Pe zilele de validare și de test se raportează, la fiecare strategie, teleportările, ciocnirile văzute de SUMO, vehiculele în mișcare care
  ating pietoni și vehiculele rămase neintrate.
* Măsura nouă se prelucrează noaptea, la 03:30, cu `romana.lant_cor`, după lanțul vechi. Zilele de test și de generalizare se opresc înaintea
  strategiilor până la `--desigileaza`. Lista candidaților stă în `config/candidati_v2.json`, iar jurnalele în `outputs/lant_cor/<zi>/`.
* Geamănul, așa cum a ieșit din prima corectură, nu era bun: făcea vehiculele să treacă prin pietoni (§ 6.5). S-a reparat înainte să fie
  publicat, iar parametrii vehiculelor au revenit la cei din `vtypes.add.xml`.
* Factorul pietonilor, 3,0, se înlocuiește cu o cerere efectivă (§ 6.5), fixată la commitul măsurii noi. Rezultatele se dau și cu pietonii
  cântăriți altfel. Virajul Magheru → Dacia est se ia din numărul lui, nu din proporții.
* Fișierele `test_<zi>_*` ale măsurii vechi nu mai intră în `docs/rezultate/`, ca să nu fie confundate cu rezultatele valabile.

**Schimbările din 3.11.2026, înaintea înghețului**, făcute înainte de a privi datele din 3.11:

* Cererea finală (§ 5.1): factorii de detecție, cotele numărate pe felii (Catargiu → Dacia vest 0,04; Dacia est → Catargiu 0,40, cu tot
  rândul Dacia est fixat), virajele Magheru → Dacia est (1,25) și Magheru → Căderea Bastiliei (1,94) luate din numărul lor și cererea
  efectivă de pietoni, 0,25 agenți la o persoană a detectorului (§ 6.5). Eticheta zi/întuneric a unui sfert se ia la începutul lui, cu
  pragul de 3,5° sub orizont.
* **Poarta are un rând nou, „pierdere de detecție pe întuneric”**, calculat doar din cameră. O oră cu Soarele, la mijlocul ei, la peste
  3,5° sub orizont, cu cel puțin 600 de intrări pe Magheru și cel puțin 100 de ieșiri spre Dacia est fără virajul de pe Magheru, iese din
  decizie, cu variantele ei, dacă aceste ieșiri sunt de cel puțin 1,8 ori intrările de pe Dacia vest: acolo detectorul pierde mult mai
  multe vehicule decât acoperă factorul. Pragul stă pe o singură seară, 2.11, cu ploaie, deci e o ipoteză declarată. Ziua, rândul e
  „fără obiect”, iar noaptea, sub minimul de trafic, „nejudecabil”; în ambele cazuri ora rămâne în decizie, dar factorii de întuneric nu
  sunt verificați pe ea. Așa sunt orele liniștite de noapte din 26.10, 1.11 și 2.11.
* Zilele de antrenare au sferturi scoase din alegerea ferestrelor, cu motivul în `config/excluderi_cor.json`, pe care îl citește singur
  `scenarii_zi --masura cor`: 25.10, 00:00–06:30, fiindcă detecția pe Lascăr Catargiu pierdea vehicule, cu tot cu ora dublată de la
  schimbarea orei; 1.11, 08:00–09:15 și 21:30–23:00, cu colectarea oprită; 2.11, 17:15–24:00, cu pierdere de detecție.
* Pragurile calculate se scriu ca mediana pe ore, nu ca media: ora liniștită din 2.11, cu sub un pieton pe oră pe zebra văzută de
  cameră, dădea pragul histogramei pietonilor 6×10⁸. Histograma se judecă doar cu cel puțin 30 de treceri în cameră.
* Sensibilitățile, raportate după îngheț și fără efect asupra deciziei: 0,15 și 0,42 agenți pe persoană; pietonii de pe celelalte brațe
  cu 1,53 în loc de 3,27; Catargiu → Dacia vest 0,08; Dacia est → Catargiu 0,32 și 0,48; Dacia est → Dacia vest 0,39; ocolirea pe inel
  a vehiculelor de pe Magheru, 6%; virajul Magheru → Dacia est cu factorul 1,08 și 1,40; ponderea pietonilor, 3 și 8.
* Cererea, scenariile și validarea au fost verificate adversarial înainte de îngheț, de alți agenți Claude decât cei care au făcut
  calculele. Constatările care au rezistat au schimbat textele, excluderile și trei reguli din cod, nu și valorile cererii.
* Măsurile s-au înghețat la commitul care adaugă acest paragraf, „Borna M2: înghețul măsurii noi”, înainte de a privi datele din 3.11.
  Pragurile sunt în `docs/rezultate/praguri_geaman.json`, iar comparația cu camera pe zilele de antrenare, în
  `docs/rezultate/validare_geaman.csv`.

**Lista candidaților, fixată pe 3.11.2026.** Lista s-a alcătuit după îngheț, doar din zilele de antrenare 25 și 26.10 și 1.11,
înainte de a privi datele din 3.11. Ziua de 2.11 nu contează: niciuna dintre orele ei nu trece poarta. Lista nu se mai schimbă până la
termen, deși și 3.11 este zi de antrenare; rezultatele acelei zile se raportează, dar nu mai mută nimic.

Pe zilele de antrenare trec poarta 8 ore, care, cu variantele lor ×0,8 și ×1,2, dau 14 scenarii. Pe ele, cu ambele comportamente și cu
seed-urile 1–3, adică pe 84 de perechi, s-au încercat semaforul rejucat, planul observat 72/48/3, planurile fixe 90/50/3, 60/40/3,
52/35/3, 45/30/3, 36/24/3, 36/28/12 și 12/14/12, programul actuated și agentul E15. Planurile cu golirea centrului de 3 s au aceleași
etape ca planul observat. Toate, afară de 90/50/3, păstrează raportul de 1,5 dintre verdele N–S și cel E–V, deci se deosebesc mai ales prin
ciclu: ≈158 s la 90/50/3, ≈138 s la planul observat, apoi ≈118, 105, 93 și 78 s. Pierderea totală scade pe măsură ce ciclul se scurtează, până la ≈93 s. La 78 s crește la loc, cât la planul
observat: cu participanții disciplinați, planul 36/24/3 pierde mult la vârfurile ×1,2.

Regula din § 9.11, aplicată pe aceste zile doar ca descriere, dă cifrele de mai jos. Ele nu sunt un rezultat: diferențele dintre
planurile apropiate au mărimea rezultatului retras (§ 6.5) și servesc doar la alcătuirea listei. Procentele privesc pierderea totală de timp.
Semaforul rejucat se compară doar pe orele acoperite cel puțin 80% de valuri măsurate, adică pe 48 de perechi, ca în regulă.

| Strategia | Față de planul observat | Disciplinați / indisciplinați | Față de semaforul rejucat | Regula |
|---|---|---|---|---|
| planul 45/30/3 | −7,9% | −4,3% / −13,9% | −18,4% | eligibil |
| planul 52/35/3 | −6,4% | −4,7% / −9,2% | −17,2% | eligibil |
| planul 60/40/3 | −5,6% | −3,5% / −9,2% | −16,6% | eligibil |
| planul 36/24/3 | +0,2% | +6,0% / −9,6% | −10,4% | nu |
| agentul E15 | +1,7% | +5,7% / −5,0% | −8,9% | nu |
| actuated | +8,6% | +10,3% / +5,7% | −2,6% | nu |

Candidații, de la cel mai simplu la cel mai complex:

1. **Planul 60/40/3.** Păstrează etapele planului de azi și îi scurtează ciclul de la ≈138 la ≈118 s, deci e schimbarea cea mai mică.
   Dacă semafoarele vecine sunt coordonate cu planul de azi, un ciclu apropiat strică mai puțin coordonarea. E o ipoteză: în geamăn,
   vecinii au programele generate de `netconvert`, nu pe cele reale (§ 6.3).
2. **Planul 45/30/3**, cu cea mai mică pierdere totală pe zilele de antrenare. Față de 60/40/3, pierde cu 2,4% mai puțin și e mai bun pe
   74 din 84 de perechi.
3. **Agentul E15**, fiindcă regulile scrise pe 1.11 l-au trecut pe listă dinainte: „intră pe ea ca un singur model”. Pe zilele de
   antrenare, regula nu l-ar găsi eligibil: în total pierde cu 1,7% mai mult decât planul observat, fiindcă, deși câștigă cu participanții
   indisciplinați, cu cei disciplinați pierde la vârfurile ×1,2; nici față de semaforul rejucat nu e semnificativ mai bun. Validarea decide
   și pentru el.

Programul actuated se raportează alături, fără să poată câștiga. Planul 52/35/3, eligibil și el, nu intră: s-a încercat abia după ce
s-a văzut grila, iar cu el lista ar avea trei planuri aproape la fel și nu ar mai avea loc pentru E15. Niciun candidat nu este program pe
cazuri de trafic, deci lista nu are praguri. Lista stă în `config/candidati_v2.json`, iar rezultatele, în
`docs/rezultate/grila_inghet_*.csv`. Modelul E15 s-a comis odată cu lista, în `models/ppo_e15.zip`, `.npz` și `.json`; ultimul păstrează
lista scenariilor de antrenare, cum cer regulile din 1.11. Înaintea lui, pe 2.11, s-a antrenat un pilot, `ppo_e15_pilot`, pe geamănul de
dinaintea înghețului, cu imitația planului 62/40; nu e pe listă și nu se publică.

**Cum se aplică regula pe zilele noi.** Odată cu lista s-au schimbat trei lucruri în cod, înaintea primei simulări a zilei de validare:

* regula primește un agent și prin calea modelului, ca în listă, și îl caută după numele lui din fișierele de rezultate, `ppo_e15`;
  înainte s-ar fi oprit;
* pe zilele de test și de generalizare, lanțul de noapte rulează doar candidații trecuți de validare, adică cei eligibili în
  `outputs/validare/cor_decizie_2026-11-04.json`; dacă nu trece niciunul, acele zile rămân fără simulări;
* lanțul nu mai rulează planul 36/28/12, pe care `validare` îl adăuga singur.

Bucla lanțului, pornită pe 3.11 înaintea acestor schimbări, s-a repornit după commit, ca să ruleze codul nou. Dacă pe ziua de validare trec
poarta sub jumătate dintre ore, validarea e doar descriptivă: niciun candidat nu trece de ea, chiar dacă regula l-ar găsi eligibil,
testul nu se deschide, iar runda se încheie. La fel, dacă regula nu se poate aplica, de exemplu fiindcă nicio oră trecută prin poartă nu e
acoperită de valuri măsurate, niciun candidat nu trece. Rolurile nu se mută din aceste cauze. Pe zilele de test, regula se aplică o
singură dată, pe cele două zile reunite, doar cu candidații trecuți de validare, dați cu numele din fișierele de rezultate:
`python -m romana.lant_cor --regula-finala`. Comanda ia din cod cele patru fișiere de rezultate ale zilelor de test, cele două porți,
numele fișierului de ieșire, `outputs/validare/cor_decizie_test_2026-11-05_2026-11-06.json`, și candidații trecuți de validare, în
ordinea listei. Ordinea contează: dacă primii doi nu se deosebesc semnificativ, câștigă cel scris primul, adică cel mai simplu, deci
nu se poate alege după rezultate. Comanda refuză să ruleze dacă decizia validării nu e comisă sau dacă vreuna dintre cele trei zile nu
și-a încheiat simulările. Fișierele `cor_decizie_<zi>.json` scrise de lanț pe fiecare zi de test sunt doar descriptive.

**Precizările din 3.11.2026, seara**, scrise înaintea primei simulări a zilei de validare, după o trecere în revistă a pașilor din
4–8.11. Ele nu schimbă nici regula, nici lista, nici pragurile, nici rolurile zilelor:

* Regula pe zilele de test se aplică o singură dată, după ce s-au încheiat simulările tuturor celor trei zile, cele două de test și cea
  de generalizare, cum scrie din 1.11; până atunci nu se citesc rezultatele niciuneia. După calendarul de acum, asta se întâmplă pe
  8.11, dimineața devreme, după ce prelucrarea de noapte a încheiat ziua de 7.11. Dacă rolurile se mută, data se mută cu ele.
* Pe zilele de test reunite, „sub jumătate dintre ore” se socotește pe orele ambelor zile la un loc, cum face comanda de mai sus.
* O zi de test sau de generalizare se desigilează după ce prelucrarea de noapte a încheiat-o fără simulări și numai după ce decizia
  validării, copiată în `docs/rezultate/`, a fost comisă: `python -m romana.lant_cor --zi <zi> --desigileaza --reia --procese 3`. Cu 3
  simulări în paralel, în loc de 8, camera are loc să lucreze, inclusiv în ora liniștită din noapte, care e și ea unul dintre scenarii.
  Numărul lor nu schimbă rezultatele: fiecare simulare pornește cu seed-ul ei, iar agentul ia mereu aceeași decizie în aceeași
  situație. O reluare cu alt număr de procese nu reface pașii încheiați. Lanțul vechi nu mai decide nimic, fiindcă măsura nouă a fost
  comisă înaintea termenului, deci zilele noi nu se mai desigilează și acolo: simulările lui, pe 11 procese, ar încărca fără folos
  nopțile zilelor de test.
* Tabelul care traduce câștigătorul în numele programului din geamănul în timp real, `varianta_live`, cuprinde acum planul observat și
  cei trei candidați, iar geamănul îi poate rula pe toți. Înainte, dacă ar fi câștigat un candidat, geamănul nu i-ar fi recunoscut
  numele și ar fi rulat, fără niciun avertisment, programul vechi din § 9.2; acum, la un nume necunoscut, se oprește la pornire.
  Tabelul nu face parte din regulă: nu schimbă nici cine e eligibil, nici cine câștigă. Geamănul în timp real rămâne pe planul
  observat până după M2, fiindcă dispeceratul numește încă modul „Planul observat”; trecerea la un câștigător vine odată cu numele
  lui pe ecran.

**Ce nu spune lista.** Grila are doar 3 seed-uri pe 8 ore, iar două dintre planuri s-au adăugat după ce s-a văzut prima parte. Cam
jumătate din câștigul planurilor, 47–54%, vine dintr-un singur scenariu ipotetic, vârful ×1,2 din 26.10, unde planul observat are un seed
cu o pierdere mult mai mare decât celelalte. Doar pe orele observate, fără variante, cele trei planuri rămân eligibile, iar 45/30/3 iese
cu 6,5% sub planul observat. La vârful observat din 26.10, singurul vârf de zi lucrătoare care trece poarta, planul observat rămâne cel mai
bun cu participanții disciplinați, iar ziua de validare, o miercuri, va avea probabil vârfuri asemănătoare. Tot acolo, geamănul duce pe
Dacia vest cu 23% mai puțin decât camera, 587 față de 766 de vehicule pe oră, deci un ciclu scurt poate părea mai bun decât ar fi pe
stradă; și de aceea 60/40/3 stă înaintea lui 45/30/3. Pe 2.11, o zi lucrătoare, nicio oră nu a trecut poarta, deci se poate ca și zilele de
validare și de test să aibă puține ore judecate (§ 6.5). Un ciclu mai scurt schimbă și coordonarea cu semafoarele vecine, iar geamănul, cu
programele generate de `netconvert` la vecini, nu poate arăta efectul real. Nici lista nu e independentă de ce s-a văzut înainte:
planurile 60/40/3 și 45/30/3 apăreau deja pe grilele din 2.11, făcute cu geamănul de dinaintea înghețului. Ce scria pe 1.11, că E15
pornește de la planul ales pe 28 și 29.10, nu mai e adevărat: E15 pornește de la planul observat.

**Ziua de 3.11, prelucrată pe 4.11, dimineața.** Ziua de 3.11, o marți, e ultima zi de antrenare și prima zi lucrătoare prelucrată cu
măsurile înghețate, care nu s-au potrivit pe ea. Geamănul nu trece poarta pe niciuna dintre cele 5 ore, deci ziua e doar descriptivă:

* La vârf, dimineața și la prânz, geamănul duce pe Dacia vest 410–510 vehicule pe oră, iar camera numără 820–920. La sfârșitul orei
  mai așteaptă să intre 290–395 de vehicule, mai ales pe Dacia vest, iar 2,4–5,4% din vehicule nu intră sau nu ajung la destinație
  până la final, peste pragul de 2%. Dimineața, și pe Dacia est trec cu 12% mai puține vehicule decât în cameră.
* În ora liniștită, noaptea, sunt 8,4 teleportări pe rulare, peste pragul de 5, iar pe Dacia est trec 38 de vehicule pe oră, față de
  35 în cameră, adică 10,5% în plus, la un prag de 10%.
* Seara, ieșirile spre Dacia est, fără virajul de pe Magheru, sunt de 2,2 ori intrările văzute pe Dacia vest, peste pragul de 1,8:
  acolo detectorul pierde, pe întuneric, mult mai multe vehicule decât acoperă factorul.

Cauza principală e cea cunoscută de pe 26.10 și 2.11: într-o zi lucrătoare, geamănul nu duce traficul de pe Dacia vest (§ 6.5, § 10).
Măsurile nu se schimbă din această cauză. Ziua de validare, 4.11, e tot o zi lucrătoare, deci poate ieși la fel; atunci se aplică ce
scrie mai sus: dacă trec poarta sub jumătate dintre ore, validarea e doar descriptivă, testul nu se deschide, iar planul observat
rămâne în geamăn. Rezultatele strategiilor din 3.11 sunt publicate, ca toate celelalte, dar nu se citează ca procente: pe ore care nu
trec poarta, ele nu spun nimic despre stradă. Lista candidaților rămâne aceeași.

**De ce nu trece ziua de 3.11: diagnoza din 4.11.** Pe 4.11, dimineața, agenți Claude au căutat cauza doar citind fișierele și
rulând probe în dosare separate. Fiecare constatare a trecut apoi pe la un alt agent, pus s-o dărâme, iar cifrele de care depinde
concluzia le-am recitit direct în fișiere. Nimic din ce urmează nu schimbă runda de acum.

* **Dacia vest.** Mașinile ajung la semafor, dar trec prea încet de el. Brațul e plin pe tot verdele, iar geamănul scoate de acolo
  ≈0,4 vehicule pe secundă de verde, adică 17–21 pe ciclu, față de 33–37 câte vede camera. Frâna stă chiar după linia de oprire, în
  primii ≈16 m, unde câteva noduri mărunte se leagă de inel: acolo cad 834 din cele 960 de secunde de mers încet pe verde, adunate
  pe toate vehiculele. Nu e vina drumului dinainte: cu un drum de plecare de 2 km, linia descarcă la fel, 520 față de 526 de vehicule pe oră, iar
  după ora simulată, când celelalte brațe se golesc, același braț trece 33–38 de vehicule pe ciclu.
* **Două probe, fiecare pe o singură oră,** arată unde se poate umbla, fără să lămurească mecanismul. Dacă se oprește regula prin
  care SUMO nu lasă un vehicul să intre într-un nod pe care n-ar putea să-l părăsească, keepClear, la prânz trec cu 26–39% mai
  multe vehicule, dar ciocnirile cu pietonii văzute de SUMO cresc de la 7 la 16. Dacă se scoate cedarea de la îmbinarea de după
  linie, la vârf trec cu 12% mai multe, dar apar 24 de ciocniri între vehicule. Niciuna nu ajunge singură la nivelul camerei.
* **Ora liniștită.** Toate teleportările sunt vehicule care au stat 300 s la roșu pe Dacia, în programul rejucat. Noaptea, camera
  vede pe Magheru prea puține mașini ca valurile să apară la fiecare ciclu, iar programul rejucat ia drept ciclu obișnuit mediana
  distanțelor dintre valuri: 358,8 s pe 3.11, deși ritmul intrărilor arată ≈124,5 s. Așa, roșul pe Dacia ajunge la 474 s. Cu planul
  observat nu e nicio teleportare, iar programul rejucat refăcut pe ritmul de 124,5 s le face să dispară într-o probă pe noaptea de
  2.11. Regula de decizie nu e atinsă, fiindcă ea compară cu programul rejucat doar orele acoperite în proporție de cel puțin 80% de
  valuri măsurate, iar ora liniștită are 0%. Ora ar pica oricum, pe Dacia est.

Reparațiile posibile țin de o rundă nouă, după M3, odată ce se încheie, pe 16.11, prelucrările de noapte de acum, cu zile noi și
cu roluri și reguli publicate înaintea datelor ei: întâi programul rejucat, cu ciclul luat din
ritmul intrărilor; apoi, ca schimbări declarate în fișierul de rețea, regula keepClear pe nodurile acelea și cedarea de la îmbinare,
după clipuri care arată cine cedează pe stradă. Geometria, benzile, trecerile și semafoarele rămân cele din OSM. Dacia est, sub cameră
dimineața, și pierderea de detecție de seară nu au fost cercetate.

**Ziua de validare, 4.11, prelucrată pe 5.11, dimineața.** Ziua de 4.11, o miercuri, e ziua de validare. Ora de dimineață, 07:30–08:30,
se suprapune cu vârful zilei, 08:00–09:00, deci, după regula din `scenarii_zi`, ziua are 4 ore observate, nu 5. Geamănul nu trece
poarta pe niciuna, deci și validarea e doar descriptivă:

* La vârf, la prânz și seara, geamănul duce pe Dacia vest 396–516 vehicule pe oră, iar camera numără 867–922. La sfârșitul orei mai
  așteaptă să intre 287–506 vehicule, aproape toate pe Dacia vest, iar 2,2–6,6% din vehicule nu intră sau nu ajung la destinație până
  la final, peste pragul de 2%. La vârf și seara, acesta e singurul rând care pică. La prânz, și debitul de pe Dacia est, cu 9,4% sub
  cameră, iese nedecis față de pragul de 10%.
* În ora liniștită, noaptea, sunt 25 de teleportări în fiecare dintre cele 5 rulări, peste pragul de 5, iar pe Dacia est trec 24 de
  vehicule pe oră, față de 29 în cameră, adică cu 18% mai puține.
* Seara, pierderea de detecție pe întuneric, care pe 3.11 scotea ora, e acum sub prag: 1,35, față de pragul de 1,8.

Tiparul e cel din 3.11, pe care îl explică diagnoza de mai sus; pe 4.11, cauzele nu le-am mai verificat separat. Decizia validării,
scrisă de lanț pe 5.11, la 04:16, s-a copiat octet cu octet în `docs/rezultate/cor_decizie_2026-11-04.json` și s-a comis la 04:23,
înaintea oricărei zile de test. Ea păstrează planul observat, 72/48/3, iar în geamăn varianta `plan_observat`; câmpul
`"castigator"` numește aici strategia care rămâne când nu trece niciun candidat, nu una care a câștigat. În fișier, planurile
60/40/3 și 45/30/3 apar totuși cu `"eligibil": true`. Fiindcă nicio oră nu a trecut poarta, regula s-a calculat, doar ca descriere,
pe toate scenariile zilei, iar câmpul `"descriptiv": true` al porții face ca niciunul să nu treacă de validare. Pe ore care nu trec
poarta, eligibilitatea nu spune nimic despre stradă. Fiindcă validarea e
descriptivă, niciun candidat nu trece de ea, deci zilele de 5, 6 și 7.11 se prelucrează noaptea doar până la geamăn și poartă, fără
strategii, chiar dacă s-ar desigila, iar `--regula-finala` răspunde că runda s-a încheiat și că rămâne planul observat. Rulările
strategiilor din 4.11 sunt publicate, ca toate celelalte, dar, ca pe 3.11, nu se citează ca procente. Runda se încheie fără un program
nou; reparațiile țin de o rundă nouă, după M3, cum scrie mai sus.

**Ziua de 5.11, prelucrată pe 6.11, dimineața.** Ziua de 5.11, o joi, e prima zi de test. Fiindcă niciun candidat nu a trecut
de validare, lanțul a rulat doar renumărarea, scenariile zilei, geamănul și poarta, fără strategii, între 03:30 și 03:46, cu codul 0
pe toți pașii. Scenariile lasă afară 20:00–20:30, când colectarea s-a oprit anunțat. Din cele 5 ore, poarta trece pe una, ora
liniștită. La vârf și la prânz pică doar rândul vehiculelor care nu intră sau nu ajung la destinație până la final; dimineața și
seara, același rând iese nedecis, iar dimineața ies nedecise și debitul de pe Dacia est și teleportările. Debitele pe Magheru și pe Catargiu
sunt în prag pe toate cele 5 ore. Ziua e doar descriptivă și nu schimbă rezultatul rundei (`docs/rezultate/poarta_cor_2026-11-05.json`,
`geaman_cor_2026-11-05.csv`, `stare_lant_cor_2026-11-05.json`).

**Ziua de 6.11, prelucrată pe 7.11, dimineața.** Ziua de 6.11, o vineri, e a doua zi de test. Ca pe 5.11, lanțul a rulat doar
renumărarea, scenariile zilei, geamănul și poarta, fără strategii, între 03:30 și 03:44, cu codul 0 pe toți pașii. Scenariile nu lasă
afară niciun interval. Ora de dimineață, 07:30–08:30, este chiar vârful zilei, deci, după regula din `scenarii_zi`, ziua are 4 ore
observate, nu 5. Din cele 4 ore, poarta trece pe una, seara. La vârf pică debitul de pe Dacia est, sub cameră, și rândul vehiculelor
care nu intră sau nu ajung la destinație până la final; tot acolo, una dintre cele 5 rulări iese din rând, cu 111 teleportări, așa că
debitele pe Magheru și pe Catargiu și teleportările ies nedecise. La prânz pică doar rândul vehiculelor neintrate sau nesosite, iar în
ora liniștită, doar debitul de pe Dacia est: 35 de vehicule pe oră în geamăn, față de 31 în cameră. Ziua e doar descriptivă și nu
schimbă rezultatul rundei, încheiate pe 5.11 fără un program nou: rămâne planul observat, 72/48/3
(`docs/rezultate/poarta_cor_2026-11-06.json`, `geaman_cor_2026-11-06.csv`, `stare_lant_cor_2026-11-06.json`).

**Ziua de 7.11, prelucrată pe 8.11, dimineața.** Ziua de 7.11, o sâmbătă, e ziua de generalizare. Ca pe 5 și 6.11, lanțul a rulat
doar renumărarea, scenariile zilei, geamănul și poarta, fără strategii, între 03:30 și 03:43, cu codul 0 pe toți pașii. Scenariile nu
lasă afară niciun interval, iar ziua are toate cele 5 ore: vârful, 13:00–14:00, ora liniștită, 04:30–05:30, dimineața, 07:30–08:30,
prânzul, 12:00–13:00, și seara, 17:30–18:30. Poarta trece pe toate cele 5 ore: pe fiecare, debitele pe Magheru, pe Catargiu și pe
Dacia est, teleportările, ciocnirile văzute de SUMO și vehiculele neintrate sau nesosite la final sunt în prag. Asta nu arată că
geamănul reproduce camera. Dacia vest nu e un rând al porții (`valideaza_geaman.py`, `POARTA`), iar acolo geamănul duce la vârf, în medie
pe cele 5 rulări, 506 vehicule pe oră, față de 701 în cameră, adică cu 28% mai puține, și la prânz 425, față de 570, cu 26% mai
puține. La sfârșitul orei mai așteaptă să intre 119 vehicule la vârf, dintre care 117 pe Dacia vest, și 46 la prânz, toate pe Dacia vest; la vârf, vehiculele
neintrate sau nesosite la final sunt 1,1% din vehicule, sub pragul de 2%. Pe celelalte trei ore, geamănul e sub cameră pe Dacia vest
cu 5–8%. Sâmbăta, în orele scenariilor, camera numără pe Dacia vest cel mult 701 vehicule pe oră, mai puține decât în orele încărcate
ale zilei de validare, 867–922 (mai sus). Fiindcă niciun candidat n-a trecut de validare, ziua nu are strategii de judecat: ca zi
de generalizare, se raportează și nu schimbă rezultatul rundei (`docs/rezultate/poarta_cor_2026-11-07.json`, `geaman_cor_2026-11-07.csv`, `stare_lant_cor_2026-11-07.json`).

**Regula finală, 8.11.** După toate cele trei zile, pe 8.11, la 07:01, `python -m romana.lant_cor --regula-finala` s-a oprit cu codul 1
și cu mesajul „niciun candidat nu a trecut de validare: runda s-a încheiat, rămâne planul observat”. Comanda verifică întâi că
decizia validării e comisă, adică `docs/rezultate/cor_decizie_2026-11-04.json` e identică octet cu octet cu cea scrisă de lanț,
apoi lista candidaților trecuți de validare (`comanda_regula_finala`, în `romana.lant_cor`). Fiindcă lista e goală, nu mai citește
rezultatele zilelor de test și nu scrie niciun fișier, deci `cor_decizie_test_2026-11-05_2026-11-06.json` nu există. Runda
zilelor noi s-a încheiat pe 5.11 fără un program nou: în geamănul în timp real rămâne planul observat, 72/48/3. O rundă nouă, cu un geamăn reparat, cere reguli noi,
publicate înaintea datelor ei.

**Ce s-a măsurat direct, fără geamăn.** Programul real al semaforului, măsurat din cameră pe 2–7.11, e în § 6.5; cifrele colectării sunt în fișa senzorului (§ 4.6).

**Agentul următor.** *(Scris pe 1.11; din 2.11, E15 imită planul observat, nu planul 12/14/12, vezi schimbările de mai sus.)* Un agent nou, numit E15, pornește prin imitarea planului 12/14/12 și continuă cu PPO. Agentul decide o dată
la 5 s, deci imitația ajunge la un verde de 15/15/15 s, cu un ciclu de 60 s în loc de 53 s; comparația de la capăt se face tot cu
planul 12/14/12, rulat exact. Se antrenează doar pe scenariile măsurii noi din zilele de antrenare, cu lista dată explicit, care
rămâne în fișierul modelului. Modelul se comite până la termenul listei de candidați și intră pe ea ca un singur model, ales doar
pe zilele de antrenare. Punctele intermediare nu se încearcă pe ziua de validare, iar o reantrenare după ce s-a văzut validarea
este alt agent, pentru altă rundă. Dacă E15 nu trece de validare, testul nu se deschide pentru el, iar rezultatul negativ se
notează.

**Ce nu se va putea spune din aceste zile.** *(Scris pe 1.11; din 2.11, referința e planul observat, 72/48/3, nu planul 12/14/12, iar candidații și E15 sunt cei din 3.11, vezi schimbările de mai sus. Pe 4.11 n-a trecut niciun candidat: asta nu arată că planul observat e cel mai bun, ci doar că geamănul n-a putut judeca.)* Rezultatele arată ce se întâmplă în geamăn, nu pe stradă. Un seed schimbă doar felul
în care conduc șoferii, nu și traficul zilei, deci valoarea p arată cât de sigur e rezultatul pe cererea acelor zile, nu și pe
alte zile. Pe 28 și 29.10, în testul și în confirmarea din § 9.10, retrase pe 2.11, planul 12/14/12 avea p = 4·10⁻¹⁰ pe 260 de
perechi, dar p = 0,02 dacă se numără doar cele 9 ferestre
observate, iar două zile sunt prea puține pentru un test între zile. Cu mai mulți candidați crește și șansa ca unul să treacă din
întâmplare, iar regula nu corectează asta. Pierderea totală nu este pierderea unei zile: ea adună câteva ore alese și variante
ipotetice, iar vârful ×1,2 a dat 31% din orele planului 12/14/12 pe 28–29.10. Câștigul depinde și de factorul pietonilor, care
rămâne o ipoteză. Câteva zile dintr-o singură săptămână de noiembrie nu spun nimic despre alte anotimpuri, iar o sâmbătă nu spune
nimic despre duminici. Dacă niciun candidat nu trece, asta nu arată că planul 12/14/12 este cel mai bun, ci doar că nu s-a găsit
unul mai bun. Nici candidații nu sunt independenți de 28 și 29.10: ei sunt cunoscuți din acele zile, iar E15 pornește de la planul
ales atunci. Istoricul arată ordinea pașilor, nu și ce a privit cineva pe calculatorul propriu.

## 10. Limitări, aspecte etice și lucrări viitoare

**Geamănul corectat** nu reproduce camera. Poarta lui, care îl compară cu camera oră cu oră, trece pe 8 din cele 12 ore comparate
la îngheț, din 25 și 26.10 și din 1 și 2.11, dar pe niciuna dintre cele 5 ore din 3.11, prima zi nouă de după îngheț, și pe niciuna
dintre cele 4 ore din 4.11, ziua de validare. De aceea, validarea a fost doar descriptivă: niciun candidat nu a trecut de ea, deci
rămâne planul observat, 72/48/3 (§ 9.11, `docs/rezultate/cor_decizie_2026-11-04.json`). Asta nu arată că planul observat e cel mai
bun, ci doar că geamănul nu a putut judeca. Cauza principală e Dacia vest: în ziua lucrătoare, geamănul trece vehiculele prea încet
chiar după semafor, așa că până la sfârșitul orei o parte din ele nu mai intră. Noaptea, în ora liniștită, semaforul rejucat a luat
pe 3.11 un ciclu de aproape trei ori prea lung, de unde teleportările, iar Dacia est iese și ea din prag (§ 9.11, diagnoza din 4.11).
Pe zilele de după, poarta a trecut pe 1 din 5 ore pe 5.11, pe 1 din 4 ore pe 6.11 și pe toate cele 5 ore pe 7.11, sâmbăta. Dacia vest
însă nu e un rând al porții, iar acolo geamănul a rămas și sâmbăta sub cameră, cu 26–28% la vârf și la prânz: o poartă trecută nu
face din geamăn unul validat (§ 9.11). În plus, cererea de pietoni e aleasă, nu numărată (§ 6.5). Rezultatele lui arată ce se întâmplă în geamăn, nu pe stradă.

Rezultatele din capitolul 9 nu pot fi mai sigure decât datele camerei și simularea din care provin. De aceea,
capitolul de față le arată deschis limitele, în trei grupe: limitele datelor camerei, ale simulării și ale folosirii
în realitate. Ultima grupă cuprinde și drepturile de folosire a codului, a datelor și a imaginilor camerei. La sfârșit
sunt enumerate lucrările care ar putea continua proiectul.

Primele limite țin de datele camerei:

* **Precizia numărării.** Cererea reală de trafic, adică numărul de vehicule care intră de fapt în piață, se
  cunoaște doar ca interval. Auditul numărării (§ 4.3) a arătat că erorile pot merge în ambele sensuri. Pe brațele
  îndepărtate, ieșirile sunt numărate în plus: pe inelul din fundal, drumul circular din jurul insulei centrale,
  detectorul pierde vehiculele mici, iar unele par ieșite pe aceste brațe. Intrările pot fi numărate în minus,
  fiindcă unele vehicule sunt ascunse de chioșc, de autobuze sau, în aglomerație, unele de altele. O numărătoare
  manuală pe teren nu e realistă pentru un singur om, cu peste 1 000 de vehicule pe oră și 6 brațe, cum a observat
  autorul. De aceea, ca în practica ingineriei de trafic, numărătoarea de referință s-a obținut dintr-o înregistrare
  adnotată, adică numărată atent pe imagini. Ea cuprinde două clipuri de câte 3 minute din 26.10, de la 11:58 și de
  la 12:19, fiecare numărat de doi adnotatori AI independenți (§ 4.3). Din această referință vin factorii de
  corecție pe braț, cu care se înmulțesc intrările numărate de cameră. Rămân trei limite. Adnotatorii sunt instanțe
  ale asistentului AI, nu oameni; o verificare umană pe câteva minute de înregistrare ar întări referința. Referința
  măsurii vechi acoperă doar 6 minute, dintr-o singură zi și o singură oră. În fine, factorii ei presupun că raportul
  dintre numărătoarea automată și cea reală e același la orice oră. Măsura nouă, `cor_`, are o referință mai largă,
  pe 11 clipuri din 1.11 și 2.11, cu factori separați pentru zi și pentru întuneric pe Magheru și pe Lascăr Catargiu
  (§ 4.3, `docs/rezultate/referinta_v2/`). Și ea e numărată tot de adnotatori AI, pe clipuri de câteva minute, la câteva
  ore din două zile, iar pe Dacia vest factorul variază între clipuri de la 1,03 la 1,58 (§ 6.5). În zilele de
  21–22.10, camera a numărat mai puține
  vehicule decât au trecut, din cauza înregistrării sacadate, cu opriri dese ale imaginii (§ 4.6). Factorii,
  măsurați pe înregistrarea continuă, nu corectează această lipsă, deși scenariile calibrate ale acelor zile îi
  folosesc (§ 5.1). Rezultatele obținute cu cele două calibrări anterioare, marginea de jos și cea de sus a cererii
  (§ 5.1), rămân raportate pentru transparență.
* **Brațele îndepărtate** – Lascăr Catargiu, Dacia vest și Căderea Bastiliei – apar mici în imagine. Virajele
  urmărite complet, de la intrare până la ieșire, sunt doar ≈25–45% din intrări (§ 4.3). Seara, Lascăr Catargiu aproape
  dispare din numărători (§ 4.3). De aceea, proporțiile de
  viraj, adică cât din traficul unui braț merge spre fiecare dintre celelalte, se sprijină parțial pe o distribuție
  presupusă dinainte, numită distribuție a priori (§ 5.1).
* **Pietonii** sunt numărați acum pe 10 zone de trecere, 3 în prim-plan și 7 în fundal (§ 4.4). Pe trecerile
  îndepărtate însă, persoanele sunt prea mici în imagine pentru detector, așa că rămâne extrapolarea la toată piața
  cu un factor de 2,5, ales, nu calculat, și declarat ca ipoteză. Numărarea pe zone îi numără de două ori pe
  unii dintre pietonii de pe Dacia est (§ 4.4). Toate acestea privesc măsura veche. Măsura nouă îi numără pe persoane, câte o
  dată, iar în geamăn pune o cerere efectivă, 0,25 agenți
  la o persoană numărată de detector pe Dacia est, aleasă ca vehiculele să treacă printre pietoni ca în cameră, nu
  numărul real (§ 6.5); pe toată piața pune, tot prin ipoteză, de 3,27 ori mai mulți agenți decât pe Dacia est, cu restul
  împărțit egal între celelalte trei brațe (§ 4.4). Traseele pietonilor în simulare sunt plauzibile, nu observate: în geamănul vechi, cele mai
  scurte drumuri prin zona pieței, iar în cel corectat, câte o singură traversare, pe un braț (§ 6.5).
* **Intersecțiile vecine** nu au cameră. Traficul lor propriu, care nu trece prin piață, este o fracțiune declarată
  ca ipoteză: 15% din traficul observat.
* **Zilele de date:** din octombrie, cinci zile lucrătoare și o duminică, plus părți din 27 și 30.10. Din 1.11, 09:04,
  colectarea merge pe laptop zi și noapte, iar procesul ei n-a căzut niciodată neprevăzut; s-a oprit doar de trei ori, anunțat.
  Pe 9.11, ≈19:10–19:24, și pe 10.11, ≈00:26–01:13, a lipsit doar fluxul camerei, iar colectarea s-a reconectat singură. O urmăresc
  veghea, din 29.10, și paznicul, din 1.11 (fișa senzorului, § 4.6). Duminica de 1.11, zilele lucrătoare 2–6.11 și sâmbăta
  de 7.11 sunt publicate, cu scenariile măsurii noi. Zilele de test, 5 și 6.11, și ziua de generalizare, 7.11, s-au prelucrat
  doar până la geamăn și poartă, fără strategii (§ 9.11). De la 8.11 se publică doar numărătorile. Toate zilele sunt de
  toamnă, cu vreme rece: vara, ploaia puternică sau evenimentele speciale nu sunt acoperite. Dintre zilele lucrătoare
  din octombrie, doar 26.10, 28.10 și 29.10 au fost înregistrate continuu, fără sacadările din primele zile. Ziua de
  test a rundei vechi, 28.10, a fost înregistrată de la 00:10 la 24:00, iar ziua de confirmare, 29.10, de la 00:00 la
  24:00 (§ 9.10); rezultatele lor s-au retras pe 2.11, fiindcă geamănul de atunci ducea traficul prin coliziuni și
  teleportări (§ 6.5). Numărătorile din 21–22.10 sunt prea mici (§ 4.6). Din ziua de 27.10 există doar noaptea,
  00:00–06:04. Din ziua de 30.10 există noaptea și dimineața, 00:00–08:30, publicate fără scenarii de simulare. În
  duminica de 25.10, vârful a depășit traficul din scenariile de antrenare, iar agenții AI, programele antrenate să
  comande singure semaforul, au pierdut din avantaj (§ 9.3). Într-o folosire reală, ei ar trebui reantrenați periodic
  pe date noi.

Următoarele limite țin de geamănul digital, replica pieței în simulatorul SUMO:

* **Trecerile de pietoni din rețea** sunt reconstruite automat de programul `netconvert`, cu opțiunea
  `--crossings.guess`. Nu sunt importate direct din OpenStreetMap (OSM), pentru că, la importul direct,
  netconvert 1.28 se oprea cu eroare. Pe 23.10, rețeaua a fost verificată cu capturile din cameră și din
  Google Street View[^streetview]. Ea are treceri pe toate brațele pieței: 12 segmente de trecere pe Magheru, 6 pe
  Lascăr Catargiu, 34 pe Dacia, 9 pe Mendeleev și 13 pe Căderea Bastiliei. Ca în rețea, străzile Mendeleev și
  Căderea Bastiliei au sens unic, de ieșire din piață. Tot ca în rețea, Magheru are 4 benzi spre piață și 3 dinspre
  piață, iar ambele brațe ale Bd. Dacia, vest și est, au câte 2 benzi pe sens. Pe brațele pieței nu există parcare
  pe carosabil, cu excepția străzilor Mendeleev și Căderea Bastiliei, cum a verificat autorul în Street View.
  Vehiculele parcate nu sunt modelate în SUMO; pe aceste două străzi ele ocupă doar marginea, în afara benzii de
  circulație.
* **Programul real al automatului**, adică al aparatului care comandă semafoarele intersecției, nu este public.
  Grupurile de semnal sunt semafoarele care schimbă culoarea împreună. Ele și planul fix de referință (§ 6.3) sunt
  reconstruite din geometria OSM și din conflictele dintre mișcări, adică din direcțiile care nu pot avea verde
  deodată. Nu au fost preluate de la Primăria Municipiului București (PMB) sau din sistemul de management al
  traficului BTMS. Ciclul planului are trei faze: verde pentru direcția nord–sud, verde pentru direcția est–vest și
  verde pentru pietoni. Duratele lor, 36 / 28 / 12 s, au fost ipoteze declarate ca atare, iar camera le-a infirmat:
  ziua, ciclul real are ≈125–155 s, nu ≈91 s, cât are acest plan cu tot cu tranziții (§ 6.5). De aceea, din 2.11,
  geamănul folosește planul observat, 72/48/3, cu ciclul de ≈138 s. Măsurarea s-a repetat pe 2–7.11, după criterii
  publicate înaintea rulărilor care dau verdictele: mediana zilei e de ≈133–137 s, iar un ciclu de ≈91 s nu apare (§ 6.5).
* **Comportamentul participanților** din simulare este cel al modelelor SUMO. Indisciplina – vehiculele care trec
  pe roșu sau blochează intersecția, pietonii care traversează pe roșu – este modelată prin tipurile de participanți
  din `vtypes_indisciplinat.add.xml` (§ 9.4). Parametrii ei sunt aleși, nu măsurați. Ea e folosită și în § 9.6,
  § 9.8 și § 9.9, apoi în § 9.10, unde acoperă jumătate din perechile de comparație ale testului din 28.10 și ale
  confirmării, ambele retrase pe 2.11 (§ 6.5). Agenții E10–E14 au fost antrenați și cu ea. Geamănul corectat are
  varianta lui, `vtypes_indisciplinat_v2.add.xml`, folosită în grila și în validarea din § 9.11, iar E15 e antrenat cu
  ambele comportamente. Traversările prin afara trecerilor nu pot fi modelate
  în SUMO.
* **Capacitatea geamănului** înseamnă cât trafic poate trece prin el. În geamănul vechi, cu parametrii impliciți ai
  șoferilor din SUMO, la intrări treceau doar ≈35–44% din vehiculele care treceau în geamănul calibrat pe 27.10, cu
  intervalul `tau` = 0,8 s (§ 6.4). Acela ducea însă traficul observat doar prin coliziuni și teleportări în masă,
  deci calibrarea s-a retras pe 2.11 (§ 6.5). Cu acești parametri impliciți sunt obținute rezultatele din
  § 9.1–9.8, cu excepțiile din § 6.4. Pentru 21–22.10, cererea numărată era aproximativ jumătate din cea reală.
  Gradul de saturare, adică raportul dintre cerere și cât poate trece prin geamăn, era deci cel puțin cel real,
  probabil mai mare, iar valorile absolute erau mai mici. În duminica de 25.10 (§ 9.3, § 9.4), înregistrată continuu,
  geamănul cu parametrii impliciți a primit o cerere apropiată de cea reală, mai mare decât putea trece prin el:
  a fost deci suprasaturat. Testul din § 9.9 și munca dintre 28.10 și 2.11 au folosit capacitatea calibrată, greșită,
  deci rezultatele lor, printre care câștigul de −7% al planului 12/14/12 și comparația dintre agenții E14 și E13, s-au
  retras tot pe 2.11 (§ 6.5, § 9.11). Măsura nouă folosește geamănul corectat, cu intervalul `tau` = 1,0 s, valoarea
  implicită: pe 8 din cele 12 ore comparate la îngheț, din 25 și 26.10 și din 1 și 2.11, debitele de pe Magheru,
  Lascăr Catargiu și Dacia est sunt la cel mult 6,3% de cameră, dar pe Dacia vest, în zilele lucrătoare, geamănul rămâne
  mult sub cameră (§ 6.5). Agentul antrenat pe el este E15 (§ 9.11).

Ultimele limite privesc folosirea sistemului pe un semafor real sau într-un alt produs:

* **Verdele minim și pietonii.** Controlerul semaforului impune un verde minim de 10 s, galbenul de 3 s și roșul
  general de 2 s dintre faze (§ 7.2). Nu impune însă separat timpul de degajare a pietonilor, adică timpul în care un
  pieton traversează toată trecerea. Cea mai lungă trecere comandată de semaforul pieței are 12,8 m, adică ≈11 s de
  mers la 1,2 m/s. Verificarea trecerilor cu `romana.control.treceri` (§ 9.10) arată cum stau planurile fixe.
  Trecerile care au verde într-o fază de vehicule îl au și în faza de pietoni, alăturată ei. Verdele lor neîntrerupt
  durează 27–33 s în planurile cu ciclu scurt și 45–53 s în planul de referință. Celelalte treceri au doar faza de
  pietoni, de 12 s în toate planurile. Cu planul 12/14/12, nicio trecere nu are deci mai puțin de 12 s de
  verde pe ciclu, la fel ca în planul de referință. Rămâne de verificat după normele de proiectare dacă faza de
  pietoni de 12 s e suficientă pe trecerea de 12,8 m, întrebare care privește și planul de referință. Pe ziua de 28.10,
  chiar cu faza de pietoni lungită la 18 s în ambele planuri, cu ciclul scurt, participanții la trafic pierdeau în total
  cu 7,9% mai puțin timp (§ 9.10). Rezultatul s-a obținut însă pe geamănul cu coliziuni și teleportări și s-a retras pe
  2.11 (§ 6.5, § 9.11): planul 12/14/12 lasă să treacă pe Magheru cel mult ≈1 300 de vehicule pe oră, față de ≈2 600 numărate la
  vârf, deci nu poate duce traficul. Agenții pot însă scurta faza de pietoni până la verdele minim de 10 s;
  mediana verzilor lor e de 11 s, adică jumătate dintre ele durează cel mult atât (§ 9.9). O aplicare reală ar cere
  verzi minime pe fază, calculate după lungimea trecerilor, mai ales pentru agenți. Verificarea trecerilor de mai sus
  privește planurile geamănului vechi. În geamănul corectat, pietonii primesc roșu cu 6 s înaintea vehiculelor din
  aceeași etapă, ca, împreună cu cele 5 s de tranziție, să aibă timpul de traversare al trecerii de 12,8 m la 1,2 m/s,
  iar controlerul nu lasă o strategie care schimbă des etapele, cum e un agent, să treacă la etapa următoare înainte ca
  pietonii să fi avut măcar 7 s de verde (§ 6.5, `control/faze.py`). Și acolo, verdele lor rămâne de verificat după
  normele de proiectare.
* **De la simulare la realitate.** Ce a învățat un agent în simulare nu se poate aplica direct pe un automat real.
  Ar fi nevoie de o validare în buclă închisă cu operatorul: probe pe semaforul real, în care sistemul decide, iar
  operatorul urmărește efectul și poate interveni oricând. Acesta este rolul dispeceratului. Ar mai fi nevoie de
  integrarea cu sistemul BTMS.
* **Licențe.** Codul este distribuit sub licența GNU AGPL v3 sau o versiune ulterioară. Ea este obligatorie pentru
  modulul de viziune, care folosește Ultralytics YOLO11, distribuit sub AGPL-3.0 împreună cu ponderile lui, adică
  parametrii învățați ai rețelei neuronale. Conform cerinței Ultralytics, licența a fost aleasă pentru tot codul.
  Cine redistribuie programul trebuie să ofere și codul sursă complet (AGPL § 6). Cine pune la dispoziție prin rețea
  o versiune modificată trebuie să le ofere utilizatorilor codul ei sursă (AGPL § 13). O integrare cu sursă închisă,
  adică nepublicată, de exemplu într-un automat comercial sau în BTMS, ar cere două lucruri. Primul e licența
  Enterprise a Ultralytics sau înlocuirea detectorului. Al doilea e o licență separată de la autor pentru codul
  proiectului. Datele derivate din OSM rămân sub licența ODbL 1.0 (§ 14.1). Fluxul camerei este folosit cu acordul
  scris al Webcam România din 27.10.2026, limitat la scopul academic și necomercial, cu sursa indicată (§ 14.1).
  O folosire comercială, de exemplu într-un produs pentru administrația drumului, ar cere un acord nou.

**Lucrări viitoare.** Proiectul poate continua cu:

* o rundă nouă, după M3, cu zile noi și cu roluri și reguli publicate înaintea datelor ei, cu reparațiile posibile găsite
  la diagnoza din 4.11:
  întâi semaforul rejucat, cu ciclul luat din ritmul intrărilor; apoi, ca schimbări declarate în fișierul de rețea și
  doar după clipuri care arată cine cedează pe stradă, regula keepClear și cedarea de la îmbinarea de după linia de
  oprire de pe Dacia vest (§ 9.11). Abia un geamăn care trece poarta și în zilele lucrătoare poate compara din nou
  planurile, inclusiv pe zile din alte anotimpuri;
* verificarea pe mai multe zile a pragului de încetinire, după care alegerea ferestrelor, adică a orelor simulate din
  fiecare zi, lasă deoparte intervalele în care prelucrarea imaginilor a încetinit: măsura nouă le scoate deja singură
  (`scenarii_zi --masura cor`, § 9.11), iar măsura veche, doar cu `--fara-incetinite` (§ 4.6);
* rata de cadre, adică numărul de imagini prelucrate pe secundă, scrisă direct în jurnalul colectării;
* o redare care, după o întârziere a fluxului, își reface treptat tamponul, adică rezerva de cadre, în loc să
  oprească imaginea 8 s;
* colectarea pe o conexiune prin cablu, nu prin Wi-Fi: unele microînghețări, adică opriri scurte ale imaginii,
  coincid cu probleme ale rețelei laptopului (§ 4.6);
* reantrenarea agenților pe mai multe zile, în geamănul corectat și după reparațiile lui, nu cu capacitatea
  calibrată, care s-a dovedit greșită (§ 6.5): E15, antrenat pe orele din 25 și 26.10 și 1.11 care trec poarta, nu a
  ieșit eligibil nici pe acestea (§ 9.11);
* verzi minime pe fază, calculate după trecerile de pietoni, pentru planurile fixe și pentru agenți, apoi
  reantrenarea și reevaluarea cu ele;
* verificarea pe stradă a intersecției Str. C. A. Rosetti × Bd. Magheru, care ar putea limita traficul spre piață.
  Coada de vehicule care aștepta să intre în simulare pe Calea Victoriei, la marginea rețelei (§ 9.6), s-a văzut în
  geamănul vechi, ale cărui rute porneau de oriunde din rețea: ≈72% din traficul de pe Magheru venea de pe Calea
  Victoriei. În geamănul corectat, rutele pornesc de pe bulevardul fiecărui braț, la 148–566 m de piață (§ 6.5);
* o recompensă – scorul după care învață agentul – care să dea prioritate transportului public, ponderată cu numărul
  de călători, obiectiv declarat și de PMB;
* coordonarea mai multor agenți, câte unul pe intersecție, prin metoda CoLight, cu „atenție pe graf”: fiecare agent
  cântărește ce se întâmplă la vecinii lui;
* validarea pe mai multe zile de date;
* compararea programului măsurat din cameră (§ 6.5, `docs/rezultate/program_real_*.csv`) cu programul oficial al
  automatului, dacă operatorul îl poate pune la dispoziție; planul fix de referință, cu ciclul lui de 91 s, e deja
  infirmat de cameră.

## 11. Ghid de utilizare

Acest capitol arată cum se instalează proiectul, cum se pornește și cum se verifică. Se adresează oricărui cititor,
fie el profesor, student, inginer de trafic sau pur și simplu curios.

Pașii urmează ordinea firească: pregătirea calculatorului și instalarea (§ 11.1, § 11.2), o verificare rapidă, de circa
zece minute (§ 11.3), rularea completă (§ 11.4) și demonstrația în timp real (§ 11.5). Harta fișierelor, problemele
frecvente și reproducerea exactă a rezultatelor (§ 11.6–11.8) se consultă la nevoie. Comenzile din tabele sunt scrise
pentru fereastra de comandă Windows (`cmd.exe`).

### 11.1 Cerințe

Tabelul arată ce îi trebuie calculatorului.

| Resursa | Cerința |
|---|---|
| Sistem | Windows 10/11; testat pe Windows 11, pe un laptop Lenovo V15 G4 cu procesor i5-13420H, 16 GB RAM și fără placă grafică NVIDIA |
| Python | versiunile 3.11–3.13; testat pe 3.12 |
| SUMO | simulatorul de trafic, versiunea 1.28: fie instalarea oficială de pe https://sumo.dlr.de, cu variabila de mediu `SUMO_HOME` definită, **fie** pachetul `eclipse-sumo` din `requirements.txt` |
| Spațiu pe disc | ~4 GB, pentru mediul Python și pentru modele |
| Internet | la instalare și pentru fluxul video al camerei |
| Opțional | o placă grafică pentru viziunea artificială: implicit placa Intel, prin OpenVINO, sau o placă NVIDIA, cu `runtime: "pytorch"` și `--device 0` |

### 11.2 Instalare (o singură dată)

```bat
git clone https://github.com/NiuninMatei/Semaforizare_Piata_Romana.git
cd Semaforizare_Piata_Romana
scripts\0_instalare.bat
```

Cele trei comenzi descarcă proiectul de pe GitHub, intră în directorul lui și pornesc instalarea. Scriptul creează
mediul virtual `.venv` și instalează în el dependențele, adică bibliotecile de care are nevoie proiectul. Mediul virtual
ține aceste biblioteci separat de restul calculatorului. Toate celelalte scripturi din `scripts\` activează automat
acest mediu.

### 11.3 Verificarea rapidă (fără cameră, ~10 minute)

Pentru a vedea proiectul la lucru nu este nevoie de cameră. Depozitul proiectului de pe GitHub conține deja
numărătorile, jurnalul de traiectorii, scenariile de simulare și modelele antrenate, deci rezultatele se pot reproduce
fără a colecta date noi. Jurnalul de traiectorii păstrează drumurile vehiculelor prin imaginea camerei.

| Pasul | Comanda | Ce trebuie să apară |
|---|---|---|
| Teste automate | `set PYTHONPATH=src` apoi `.venv\Scripts\python -m unittest discover tests` | mesajul `OK` la sfârșitul celor peste 960 de teste. Unele au nevoie de o unealtă în plus și, fără ea, sunt sărite: cele ale sondării folosesc Node.js și Chrome sau Edge, cele ale paginii dispeceratului, Chrome, iar cele ale pașilor din geamăn, SUMO. Testele verifică numărarea pe origine și destinație (O–D), pietonii, sensul de mers, renumărarea, statisticile pe perechi, validarea și comparația cu fișierele publicate, scenariile cu participanți indisciplinați, numărătoarea de referință, calibrarea camerei, recunoașterea prelucrării încetinite (`calitate`), veghea fluxului de cadre (`veghe`), paznicul colectării (`paznic`), fișa senzorului (`fisa_senzor`), starea senzorului (`senzor`), serverul și pagina dispeceratului (`dashboard`), pașii schimbării de fază (`pasi`), lacătul care ține geamănul într-un singur exemplar, programul real al semaforului (`program_real`), comparația geamănului cu camera și poarta (`valideaza_geaman`), lanțurile de noapte (`lant_zilnic`, `lant_cor`), verdele continuu pe treceri (`treceri`), golurile și intervalele excluse din `scenarii_zi` |
| Simulare vizuală | `scripts\8_simulare_gui.bat` | fereastra grafică a simulatorului, SUMO-GUI, cu ora de vârf din 21.10.2026; semaforul pieței este condus de agentul IA |
| Comparație vizuală | `scripts\8_simulare_gui.bat sumo\scenarios\zi_2026-10-21_varf.sumocfg --strategie fix_referinta` | aceeași oră, cu semaforul pe planul fix |
| Comparația în geamăn | `scripts\9_demo_comparatie.bat` (~4 min) | vârful din 26.10, simulat cu planul de referință, cu planul observat, cu Presiune maximă, un algoritm clasic fără învățare, și cu agentul IA; rezultatele apar pe categorii de participanți. Arată cum se compară strategiile, nu care e mai bună: pe o singură oră și pe câteva seed-uri, diferențele dintre planurile apropiate nu spun nimic. Pentru altă oră se adaugă `--scenariu` |
| Evaluare scurtă | `.venv\Scripts\python -m romana.control.evaluate --seeds 1 --procese 4 --scenarii sumo\scenarios\zi_2026-10-21_varf.sumocfg` | tabelul din `docs\rezultate\rezultate.md`, refăcut. **Atenție:** comanda rescrie fișierele publicate `rezultate.md`, `rezultate_brute.csv` și graficul; versiunea publicată se readuce cu `git checkout -- docs/rezultate` (§ 11.8) |

Comanda `set PYTHONPATH=src` îi arată lui Python unde se află codul proiectului. Ea este valabilă doar în fereastra în
care a fost dată, așa că evaluarea scurtă se pornește din aceeași fereastră.

Simularea vizuală, comparația vizuală și evaluarea scurtă folosesc scenariul `zi_2026-10-21_varf`, al măsurii vechi,
care rulează pe geamănul cu defectul din § 6.5, cu intervalul `tau` = 0,8 s. Ele arată cum lucrează programele, nu un
rezultat valabil, iar evaluarea scurtă nu reface cifrele publicate, obținute pe scenariile din commitul `e1d0f77`
(§ 11.8). Geamănul corectat apare în comparația din `scripts\9_demo_comparatie.bat`, iar în fereastra grafică, cu
`scripts\8_simulare_gui.bat sumo\scenarios\cor_zi_2026-10-26_varf.sumocfg`.

### 11.4 Rularea completă, pas cu pas

Fiecare pas are scriptul lui în directorul `scripts\`. Scripturile cu literă (2b, 2c, 2d, 2e, 3b, 3c) țin de pasul cu
același număr, iar sondarea, `7_sondare.bat`, apare ca pasul 7b.

| Pasul | Scriptul (din `scripts\`) | Ce face | Durata |
|---|---|---|---|
| 1 | `1_construieste_retea.bat` | regenerează rețeaua SUMO din extrasul OpenStreetMap (OSM) aflat în `data\osm` | ~2 min |
| 2 | `2_viziune_live.bat` | analizează în timp real imaginea camerei, într-o fereastră cu zonele desenate; tasta `q` oprește analiza. Scrie numărătorile în `data\counts` și jurnalul local în `data\trajectories_brute`. Versiunea care se poate publica, doar cu vehiculele, se obține cu `recount --publica` | cât se dorește; pentru un profil complet, o zi întreagă |
| 2d | `2d_veghe.bat [--pana-la "AAAA-LL-ZZ HH:MM"]` | supraveghează fluxul de cadre, adică imaginile succesive primite de la cameră, în paralel cu analiza în timp real. La primul semn de problemă se oprește cu mesajul `ALERTĂ` și scrie un diagnostic în `outputs\logs\veghe_alerta_*.json`. Printre semnele urmărite se numără scăderea ratei cadrelor, imaginea înghețată și jurnalul oprit (§ 4.6). Măsurătorile, minut cu minut, ajung în `outputs\logs\veghe_<zi>.csv` | cât rulează analiza în timp real |
| 2e | `2e_paznic.bat [--pana-la "AAAA-LL-ZZ HH:MM"]` | repornește colectarea dacă procesul lipsește sau tace, iar camera răspunde (§ 4.6). Înaintea unei opriri voite a colectării se pune fișierul `outputs\live\fara_repornire`, altfel paznicul o pornește la loc; cât timp fișierul există, paznicul nu repornește nimic, deci se șterge când colectarea trebuie să meargă din nou. Repornirile se notează în `outputs\logs\reporniri_<zi>.csv`, pe care le citește și fișa senzorului (§ 4.6) | continuu |
| 2b | `2b_calibrare_zone.bat` | redesenează zonele de numărare dacă operatorul mută camera | ~5 min |
| 2c | `2c_renumarare.bat --zi AAAA-LL-ZZ` | renumără o zi din jurnalul local de traiectorii, de exemplu după ce zonele au fost redesenate. Pe o copie a depozitului fără `data\trajectories_brute` se renumără doar vehiculele din jurnalul publicat; folosiți atunci `--out` cu alt director, ca pietonii din `data\counts` să nu se piardă | ~5 min |
| 3b | `3b_scenarii_zi.bat --zi AAAA-LL-ZZ` | găsește ora de vârf și ora cea mai liniștită a zilei. Adaugă dimineața, prânzul și seara, dacă sunt acoperite complet de date și nu se suprapun cu vârful. Apoi construiește scenariile SUMO, plus două variante de sensibilitate: vârful ×1,2 și liniștitul ×0,8 | ~5 min |
| 3c | `3c_lant_zilnic.bat --bucla --ora 00:15 --pana-la "AAAA-LL-ZZ HH:MM"` | prelucrează singur, în fiecare noapte, ziua precedentă, cu măsura veche; din 2.11, ea se calculează doar pentru istoric și nu mai decide nimic (§ 9.11). Rezultatele rămân în `outputs/validare/`, iar jurnalele pașilor în `outputs/lant/`. Măsura nouă, pe care se iau deciziile din § 9.11, se prelucrează după ea, implicit la 03:30, cu `python -m romana.lant_cor --bucla --pana-la "AAAA-LL-ZZ HH:MM"`, pornit după `scripts\_mediu.bat`, cu aceleași roluri ale zilelor; jurnalele ei rămân în `outputs/lant_cor/` | noapte de noapte |
| 3 | `3_genereaza_cerere.bat --nume X --de-la "..." --pana-la "..."` | construiește un singur scenariu, pe un interval de timp ales de utilizator | ~1 min |
| 4 | `4_antreneaza_ai.bat --nume X --pasi 500000 --medii 8 --scenarii <fișierele .sumocfg, enumerate>` | antrenează un agent PPO, adică un program de inteligență artificială care învață în simulare, prin încercări, să conducă semaforul (§ 7.3). Alte opțiuni: `--continua`, `--lr`, `--bc-plan`, `--coridor`. Fără un `--nume` nou se suprascrie `models\ppo_romana.zip`. Fișierele de scenariu se enumeră unul câte unul: caracterul `*` nu este înlocuit cu lista fișierelor nici de `cmd.exe`, nici de `train` | 1–3 h pe laptopul de test |
| 5 | `5_evalueaza.bat --scenarii <fișierele zi_* / referinta_*>` | compară strategiile între ele. Opțiunile `--seeds` și `--seed-start` stabilesc câte seed-uri se folosesc și care este primul dintre ele; un seed este valoarea care pornește generatorul de numere aleatoare al simulării. Alte opțiuni: `--planuri 46,48,12`, `--adauga`. Scenariile se dau cale cu cale, ca în § 11.3, pentru că `cmd.exe` nu înlocuiește `*` cu lista fișierelor. Fără `--scenarii`, scriptul se oprește cu `FileNotFoundError` înainte de orice simulare, la scenariile `capacitate_*` și `indisciplinat_*`, care nu au fișierul `od_estimat.json`. Scriptul rescrie fișierele publicate `rezultate_brute.csv`, `rezultate.md` și `comparatie_strategii.png` din `docs\rezultate\`; refacerea lor este descrisă în § 11.8 | ~1 h |
| 6 | `6_geaman_digital.bat` | pornește geamănul digital, adică replica virtuală a intersecției: simularea din SUMO-GUI, alimentată **în timp real** de cameră, cu semaforul condus de strategia aleasă în dispecerat | continuu |
| 7 | `7_dashboard.bat` | deschide dispeceratul, interfața web a operatorului, la http://localhost:8050; cu `?imagine=0` la capătul adresei, pagina pornește fără imaginea camerei, cu starea senzorului în locul ei | continuu |
| 7b | `7_sondare.bat` | sondarea dispeceratului cu oameni (§ 8), pe acest calculator, pentru probe; pagina adevărată e pe GitHub Pages, cu `--linkuri`, `--rezumat`, `--publica` pentru invitații și rezultate | 10–20 min de persoană |
| – | `PORNESTE_TOT.bat` | pornește pașii 2, 6 și 7 în trei ferestre: sistemul complet, în timp real | continuu |
| – | `M2_demonstratie.bat` | lansatorul demonstrației de la borna M2, scris pentru laptopul autorului, pe care colectarea merge deja: pornește doar dispeceratul și geamănul, fără SUMO-GUI și fără o a doua colectare, apoi deschide în Chrome prezentarea și dispeceratul; prezentarea o ia de pe laptop, din `outputs/`, care nu intră în depozit | cât ține demonstrația |
| – | `M3_demonstratie.bat [proba]` | lansatorul demonstrației bornei M3, tot pentru laptopul autorului: pornește doar ce lipsește dintre dispecerat și geamăn, fără SUMO-GUI și fără o a doua colectare, apoi deschide în Chrome prezentarea, `Prezentare_M3.pdf`, pe care o ia de pe Desktop sau din `outputs/prezentare/surse_m3`, care nu intră în depozit, și spune dacă lipsește, iar alături dispeceratul cu `?imagine=0`; cu `proba`, nu deschide Chrome și iese cu codul 1 dacă dispeceratul nu răspunde în 90 s (§ 11.5) | cât ține demonstrația |
| 10 | `10_documentatie_pdf.bat` | transformă documentația în PDF, cu pagini numerotate (`docs\DOCUMENTATIE.pdf`) | ~1 min |

### 11.5 Demonstrația în timp real (~20 de minute)

Demonstrația prezintă sistemul întreg, în timp real. Pe un calculator pe care nu rulează nimic, se pornește cu
`scripts\PORNESTE_TOT.bat`. Scriptul pornește însă colectarea fără să verifice dacă una rulează deja, pornită de mână sau de
paznic (pasul 2e din § 11.4), deci **nu se folosește cât merge colectarea**: ar porni o a doua. Atunci se pornesc doar pașii 6
și 7 din § 11.4 sau, pe laptopul autorului, lansatorul bornei M3, `scripts\M3_demonstratie.bat`. Acesta pornește doar ce
lipsește, fiecare într-o filă cu numele ei în Windows Terminal: dispeceratul, dacă nu răspunde, și geamănul, fără SUMO-GUI,
dacă nu rulează deja unul. Când dispeceratul răspunde sau, dacă nu răspunde, după 90 s, cu un mesaj care trimite la fila „Dispecerat”, lansatorul
deschide în Chrome o fereastră cu prezentarea și cu dispeceratul la `http://127.0.0.1:8050/?imagine=0`, adică fără imaginea camerei, cu starea senzorului în locul ei (§ 4.6, § 8).
Cu `scripts\M3_demonstratie.bat proba`, nu deschide Chrome și iese cu codul 1 dacă dispeceratul nu răspunde în 90 s. La proba
din 10.11, la 08:14, dispeceratul a răspuns în ≈3 s, toate verigile senzorului erau „în regulă”, a doua rulare n-a mai
pornit nimic, iar colectarea a rămas la ≈6 cadre/s. Oprirea se face cu Ctrl+C, întâi în fila „Geaman”, apoi în fila
„Dispecerat”; colectarea merge mai departe. La borna M2, `scripts\M2_demonstratie.bat` pornea împreună dispeceratul și
geamănul, fără să verifice dacă rulează deja un geamăn, și deschidea dispeceratul cu imaginea camerei. Dacă a pornit-o
paznicul, colectarea rulează fără fereastră, așa că fereastra de la pasul 1 din tabelul de mai jos lipsește, iar imaginea
camerei se vede în dispecerat, cu butonul „Arată imaginea”. Geamănul pornit de lansatorul bornei M3 rulează fără SUMO-GUI,
deci lipsește și fereastra de la pasul 2; semaforul se urmărește atunci doar în dispecerat. După pornire, ferestrele se aduc pe rând pe ecran, în ordinea în
care circulă datele:

| Pasul | Fereastra | Ce se arată |
|---|---|---|
| 1. Ochii sistemului | „Piata Romana – viziune artificiala” | participanții la trafic recunoscuți în imagine de YOLO11 și urmăriți de la un cadru la altul de ByteTrack; zonele de intrare, de ieșire și de trecere; debitele pe fiecare braț al pieței, în vehicule pe oră. Imaginea este redată fluent, cu o întârziere de 8 s |
| 2. Geamănul digital | SUMO-GUI | replica fidelă a rețelei, după OpenStreetMap; cele 16 semafoare ale pieței, conduse împreună, ca un singur controler; traficul generat în timp real din debitele măsurate de cameră |
| 3. Supravegherea umană | dispeceratul, http://localhost:8050 | imaginea camerei, ca flux video, sau, cu `?imagine=0`, starea senzorului în locul ei; faza curentă a semaforului, descrisă în cuvinte; cozile de pe brațe. Operatorul poate alege orice mod de control: „Planul observat”, „Agent IA”, „Plan de referință”, „Presiune maximă” sau „Comandă manuală”. Modul ales se aplică doar după confirmare, cu „Da, trec la …” sau, la comanda manuală, cu „Da, preiau comanda”; pentru o fază aleasă de mână, banda de sus arată pașii până la verdele ei |
| 4. Comparația în geamăn | `scripts\9_demo_comparatie.bat` | aceeași oră reală de trafic, simulată cu planul de referință, cu planul observat, cu Presiune maximă și cu agentul IA |
| 5. Rezultate și limite | capitolele 9 și 10 | rezultatele, cu cele retrase marcate ca atare (§ 6.5, § 9.11), și limitările declarate ale proiectului |

**Strategia implicită la pornire** este, din 2.11.2026, planul observat, 72/48/3, dedus din cameră
(§ 6.5). Notația înseamnă 72 s de verde pe direcția nord–sud, 48 s pe direcția est–vest și 3 s de golire a centrului, fără pietoni; pietonii traversează în timpul celorlalte două etape.
Validarea din 4.11 nu a schimbat strategia implicită: niciun candidat nu a trecut de ea, deci planul observat rămâne
(`docs/rezultate/cor_decizie_2026-11-04.json`, § 9.11). Geamănul în timp real rulează pe rețeaua, fazele și tipurile de
vehicule ale geamănului corectat, dar fără cererea măsurii noi: debitele sunt cele brute ale camerei, numărate cu zonele
măsurii vechi și fără factorii de corecție, iar unele proporții de viraj sunt declarate. De aceea nu arată geamănul din
§ 6.5; în timp real, Lascăr Catargiu apare ziua de 2–3 ori sub traficul real pe 25–26.10 și pe 1.11 și de 4–7 ori pe 2–4.11, iar seara aproape deloc (§ 5.5, § 8). Cel vechi se poate porni cu
`--geaman-vechi`, doar pentru comparație.

Celelalte variante se aleg din `VARIANTA_PROGRAM`, în `bridge/live_twin.py`. Una dintre ele este programul realist,
care comută între agentul oficial și agentul E3, doi agenți AI prezentați în capitolul 9. Dispeceratul arată în fiecare
moment ce componentă conduce semaforul.

### 11.6 Unde se găsesc lucrurile

Tabelul este harta depozitului: ce conține fiecare director și fiecare fișier important.

| Directorul sau fișierul | Conținutul |
|---|---|
| `docs/DOCUMENTATIE.md` | documentația, adică documentul de față. `docs/DOCUMENTATIE.pdf` are același conținut, cu pagini numerotate, și se generează cu `scripts\10_documentatie_pdf.bat` |
| `src/romana/vision/` | lanțul cameră → detecție → urmărire → numărare (`od_counter.py`, `recount.py`). Tot aici: numărătoarea de referință, făcută de adnotatori pe clipuri scurte (`referinta.py`), calibrarea camerei pe rețea, adică potrivirea imaginii pe harta străzilor (`calibrare_camera.py`), calitatea înregistrării (`calitate.py`), veghea fluxului de cadre (`veghe.py`), paznicul care repornește colectarea (`paznic.py`), fișa senzorului, cu cifrele colectării calculate din jurnale (`fisa_senzor.py`), și programul real al semaforului, măsurat din jurnalul vehiculelor (`program_real.py`) |
| `src/romana/bridge/` | puntea dintre cameră și simulare: estimarea matricei O–D, cererea de trafic pentru SUMO, scenariile fiecărei zile, scenariile cu participanți indisciplinați (`indisciplinat.py`) și geamănul digital în timp real |
| `src/romana/network/` | construirea replicii fidele a rețelei de străzi, din datele OSM |
| `src/romana/control/` | controlul semaforului: controlerul sigur (§ 7.2), mediul de antrenare Gymnasium, agentul PPO, strategiile de referință (§ 7.4) și evaluarea. Tot aici sunt modulele de analiză: validarea pe seed-uri (`validare.py`), statisticile pe perechi de simulări (`analiza.py`), localizarea întârzierilor la vârf (`localizare.py`), duratele de verde ale agenților (`durate_verde.py`), regula „cel mai bun câștigă”, cu cazurile de trafic după debit (`decizie.py`), măsura pe persoană, cu un număr declarat de oameni în fiecare vehicul (`ocupare.py`), pierderea totală pe cazuri de trafic și pe tipuri de participanți (`totaluri.py`), verdele pe treceri (`treceri.py`), capacitatea geamănului, adică cât trafic poate trece prin el (`capacitate.py`), fazele geamănului corectat (`faze.py`), pașii schimbării de fază, arătați în dispecerat (`pasi.py`), semaforul rejucat din valurile camerei (`rejucat.py`) și comparația geamănului cu camera, cu poarta din § 9.11 (`valideaza_geaman.py`). Lanțurile de noapte stau alături, în `src/romana/lant_zilnic.py` și `src/romana/lant_cor.py` |
| `src/romana/dashboard/` | dispeceratul, interfața web a operatorului: serverul (`server.py`), pagina (`static/index.html`), starea senzorului (`senzor.py`), capturile paginii în stări fixate (`capturi.py`), evaluarea ei cu evaluatori AI (`evaluare.py`) și sondarea (`sondare.py`); copiile neschimbate ale paginilor de la M1 și M2 stau în `static/m1` și `static/m2` |
| `config/` | configurarea: camera și zonele ei, rețeaua și grupurile de semnal (§ 6.3), parametrii cererii de trafic |
| `data/counts/`, `data/counts_cor/`, `data/trajectories/` | datele reale colectate: numărătorile agregate și traiectoriile vehiculelor, fără imagini și fără identificatori, adică pseudonimizate. Licența lor este în `data/LICENTA.txt`. Jurnalul complet, cu pietoni, rămâne doar local, în `data/trajectories_brute/`, exclus din Git |
| `sumo/scenarios/` | scenariile construite din date reale: `cor_zi_*` și `indisciplinat_cor_zi_*` sunt cele ale măsurii noi, pe geamănul corectat (§ 6.5, § 9.11); `zi_*`, `indisciplinat_zi_*` și `capacitate_*` sunt cele ale măsurii vechi, pe geamănul cu defectul din § 6.5, păstrate pentru istoric; `referinta_*` sunt scenariile ipotetice de la începutul proiectului |
| `models/` | agenții antrenați: fișierele `.zip`, în formatul bibliotecii Stable-Baselines3, și fișierele `.npz`, pentru rulare fără PyTorch |
| `docs/rezultate/` | datele brute ale evaluărilor, adică tabele CSV, grafice și tabelul detaliat generat automat, plus numărătorile de referință (`referinta/`, `referinta_v2/`). Cele mai multe fișiere sunt descrise în Anexa A; evaluările dispeceratului (`evaluare_m1/`, `evaluare_m2/`), în § 8, iar fișa senzorului (`fisa_senzor_2026-11-06_0000.json` și `.md`), în § 4.6 |
| `docs/imagini/` | figurile documentației. Două sunt imaginile camerei, figurile 4.1 și 4.2 (`camera_*.jpg`), obținute dintr-un singur cadru estompat din 28.10.2026 și publicate cu acordul scris al Webcam România; ele nu intră sub licențele proiectului (`LicenseRef-Toate-drepturile-rezervate`, § 14.1). Celelalte, figurile 6.1, 6.2 și 8.1, sunt figuri proprii, fără imagini ale camerei, sub licența documentației, CC BY 4.0 |
| `docs/prezentari/` | prezentările bornelor cursului, la disciplinele *Interfețe om-calculator* și *Internet of Things*, în PDF. Prezentarea M1 folosește același cadru estompat al camerei, cu sursa indicată; prezentarea M2 nu are imagini ale camerei |
| `docs/img/` | nu mai există: capturile camerei de aici s-au scos din istoric (§ 12.5), iar figurile proprii stau în `docs/imagini/` |
| `legacy/google_ai_draft/` | ciorna inițială, păstrată împreună cu raportul de audit |
| `README.md` | prezentarea scurtă, afișată pe pagina GitHub a proiectului |
| `LICENSE`, `LICENSES/` | textele licențelor: GNU AGPL v3 pentru cod și modele, ODbL 1.0 pentru date, CC BY 4.0 pentru documentație, CC0 1.0 pentru `build.bat`, `run.bat` și `output.add.xml` din ciornă, generate de osmWebWizard, SIL OFL 1.1 pentru fonturile Barlow ale dispeceratului și ale paginii de sondare, plus nota pentru imaginile camerei (`LicenseRef-Toate-drepturile-rezervate`) |
| `NOTICE`, `REUSE.toml`, `*/LICENTA.txt` | atribuirile pentru resursele preluate de la alți autori, harta „cale → licență” și notele de licență din `data/`, `sumo/` și `models/` (§ 14.1) |
| `.claude/CLAUDE.md` | instrucțiunile și starea lucrului pentru asistentul Claude Code; nu fac parte din documentație |

### 11.7 Probleme frecvente

Tabelul adună problemele întâlnite cel mai des și soluția fiecăreia.

| Ce se întâmplă | Cauza și soluția |
|---|---|
| `SUMO nu a fost găsit` | definiți variabila `SUMO_HOME` sau rulați `pip install eclipse-sumo==1.28.0` în `.venv` |
| `DLL load failed ... _libsumo` | calea adăugată în PYTHONPATH de instalatorul SUMO are întâietate față de pachetul instalat cu pip. Proiectul ocolește automat problema (`control/env.py`). Dacă eroarea persistă: `set ROMANA_USE_TRACI=1`, varianta mai lentă |
| viziunea prelucrează sub 2 cadre/s | fără placă grafică dedicată, verificați că în `config/camera.json` scrie `runtime: "openvino"`; cu placă grafică NVIDIA: `runtime: "pytorch"` și `--device 0` |
| `Cannot use optimization (scipy not installed)` | lipsește biblioteca scipy: rulați `pip install scipy` în `.venv` |
| camera nu răspunde | fluxul public al camerei poate fi temporar indisponibil, cum a fost pe 9 și pe 10.11 (§ 4.6). Colectarea se reconectează singură, iar geamănul digital păstrează ultimele debite bune cel mult 20 de minute, apoi trece pe profilul de trafic de referință și afișează acest lucru. Veghea se oprește cu alerta „fără cadre” și nu mai pornește singură: după ce fluxul revine și merge 5 minute fără întrerupere, porniți-o din nou cu `scripts\2d_veghe.bat`, doar dacă nu rulează deja una (§ 4.6, pasul 2d din § 11.4). În dispecerat, starea senzorului arată care verigă s-a oprit |
| imaginea pare înghețată sau numărătorile scad brusc | o oprire de 10–30 s, de câteva ori pe zi, este o microînghețare și trece singură; dispeceratul arată atunci, în locul imaginii, „Imaginea s-a oprit de N s. De obicei revine singură.”, iar după 3 minute doar de cât timp s-a oprit; cu imaginea ascunsă, vechimea apare în rândul de stare al camerei (§ 4.6). Altfel, `2d_veghe.bat` arată pe loc dacă a scăzut rata cadrelor prelucrate sau dacă fluxul camerei nu mai avansează. Rata scade din cauza calculelor grele rulate în paralel: porniți-le la prioritate scăzută. Diagnosticul este în `outputs\logs\veghe_alerta_*.json`, iar explicațiile, în § 4.6 |

### 11.8 Reproducerea rezultatelor și a calibrării

**Geamănul corectat și măsura nouă.** Rezultatele din § 6.5 se refac astfel, în această ordine:

| Ce | Comanda |
|---|---|
| rețeaua, fazele și tipurile de vehicule | `python -m romana.network.retea_v2` |
| cererea măsurii noi | `python -m romana.bridge.cerere_v2`, din `config/demand.json` și `config/factori_v2.json` |
| numărătorile măsurii noi | `python -m romana.vision.recount --zi <zi> --camera camera_v2.json --pe-persoane --out data/counts_cor` |
| scenariile | `python -m romana.bridge.scenarii_zi --zi <zi> --masura cor`, care citește singur excluderile din `config/excluderi_cor.json`, apoi `python -m romana.bridge.indisciplinat --scenarii "sumo/scenarios/cor_zi_*.sumocfg" --vtypes vtypes_indisciplinat_v2.add.xml --vechi vtypes_v2.add.xml` |
| programul real al semaforului, luni 26.10 (§ 6.5) | `python -m romana.vision.program_real --zi 2026-10-26 --interval 15:00-16:00 --interval 12:00-13:00 --interval 17:30-18:30 --interval 22:00-23:00 --pe-zi --out outputs/program_real_2026-10-26.csv`, cu intervalele din primele rânduri ale fișierului publicat `docs/rezultate/program_real_2026-10-26.csv`; profilurile pliate se scriu în plus cu `--profile outputs/profile_2026-10-26.json` |
| programul real pe 1–7.11; pe 2–7.11, după criteriile publicate înaintea rulărilor care dau verdictele, din `docs/rezultate/program_real_criterii.json` | `python -m romana.vision.program_real --zi <zi> --interval 09:30-10:30 --interval 12:00-14:00 --interval 17:30-18:30 --interval 19:00-21:00 --interval 23:00-23:59 --pe-zi --out outputs/program_real_<zi>.csv`, adică comanda din criterii, cu ieșirea în afara `docs/`. Pe 1.11 dă fișierul publicat octet cu octet, cu terminațiile de rând CRLF pe care le scrie modulul (în depozit, deci și pe GitHub, fișierele `program_real_<zi>.csv` sunt păstrate cu LF, după `.gitattributes`; amprentele lor sha256 din verdicte sunt ale fișierelor cu CRLF, cum le scoate Git pe Windows, deci pe o copie cu LF se compară după ce fiecare LF devine CRLF), iar pe 2–7.11 e chiar comanda care a scris `docs/rezultate/program_real_<zi>.csv`. Verdictele, cu verificările C0, C1 și C2, sunt în `docs/rezultate/program_real_verdict_2026-11-02_04.json`, pentru 2–4.11, în `program_real_verdict_2026-11-05.json`, pentru 5.11, în `program_real_verdict_2026-11-06.json`, pentru 6.11, și în `program_real_verdict_2026-11-07.json`, pentru 7.11; proba C0, cu căutarea lărgită la 80–240 s, e descrisă în fiecare, în câmpul `proba_C0` |
| geamănul lângă cameră, cu semaforul rejucat, la îngheț | `python -m romana.control.valideaza_geaman cor_zi_2026-10-26_varf cor_zi_2026-10-26_seara cor_zi_2026-10-26_linistit cor_zi_2026-10-25_varf cor_zi_2026-10-25_linistit cor_zi_2026-11-01_varf cor_zi_2026-11-01_pranz cor_zi_2026-11-01_seara cor_zi_2026-11-01_linistit cor_zi_2026-11-02_varf cor_zi_2026-11-02_pranz cor_zi_2026-11-02_linistit --seeds 1,2,3,4,5 --proba fara_pietoni --proba rapid --seeds-proba 1,2,3 --procese 8 --scrie-praguri docs/rezultate/praguri_geaman.json --poarta docs/rezultate/poarta_geaman.json --out docs/rezultate/validare_geaman.csv --figura docs/imagini/geaman_camera.png`; pe o zi nouă, cu `--praguri docs/rezultate/praguri_geaman.json` în loc de `--scrie-praguri` |
| strategiile, cu teleportări și ciocniri | `python -m romana.control.validare <strategii> --scenarii "cor_zi_<zi>_*" --seeds 1-10 --fara-alegere --out outputs/validare/<fișier>.csv` |
| decizia zilei de validare, 4.11 (§ 9.11) | `python -m romana.lant_cor --zi 2026-11-04 --uscat` arată, fără să ruleze nimic, comenzile exacte ale zilei: geamănul față de cameră, cu poarta, strategiile pe seed-urile 11–15 și regula din § 9.11. Decizia scrisă de lanț e copiată octet cu octet în `docs/rezultate/cor_decizie_2026-11-04.json`, iar poarta zilei e în `docs/rezultate/poarta_cor_2026-11-04.json` |

**Fișa senzorului** (§ 4.6) se calculează cu `python -m romana.vision.fisa_senzor --pana-la "AAAA-LL-ZZ HH:MM" --out-json outputs/fisa.json --out-md outputs/fisa.md`. Modulul citește jurnalele locale ale colectării, ale paznicului, ale vegherii și ale lanțurilor de noapte, din `outputs/`, care nu intră în depozit, plus numărătorile din `data/counts/`; pe o copie a depozitului fără aceste jurnale, fișa nu se poate reface. Rezultatul publicat, la tăietura din 6.11, 00:00, e `docs/rezultate/fisa_senzor_2026-11-06_0000.json`, cu tabelul scurt în fișierul `.md` cu același nume. Din 10.11, la o tăietură fix la miezul nopții, fișa nu mai scrie rândul gol al zilei care abia începe, ca rândul „vin. 06.11” din tabelul publicat; totalurile nu se schimbă, fiindcă rândul are doar zerouri. Tot din 10.11, fișa citește și alertele vegherii, `outputs/logs/veghe_alerta_*.json`, iar căderile sursei din alertele „fără cadre” le socotește ca minute fără cadre, cu o margine de sus (§ 4.6).

Această secțiune arată cum se verifică rezultatele: statisticile din capitolul 9 se recalculează exact din fișierele
publicate, iar o simulare repetată cu aceleași date dă exact același rezultat. Comenzile, de la paragraful „Pentru
specialiști” încolo, pot fi sărite la o primă lectură.

Se pot verifica patru lucruri:

1. **Geamănul corectat și măsura nouă** (§ 6.5, § 9.11) se refac, în ordine, cu comenzile din primul tabel, de mai
   sus, date cu Python din `.venv`, de exemplu după `scripts\_mediu.bat`.
2. **Statisticile din capitolul 9** se calculează direct din fișierele publicate în `docs\rezultate\` (Anexa A), fără
   nicio simulare, și dau exact cifrele din text. Comenzile sunt în al doilea tabel.
3. **Simulările** sunt deterministe: aceeași strategie, pe același scenariu și cu același seed, dă exact aceeași
   pierdere de timp. Condiția este ca scenariile să fie cele din momentul rulării. Comenzile sunt în al treilea tabel.
4. **Calibrarea din § 4.3** se reface din datele publicate în `docs\rezultate\referinta\`. Comenzile sunt în ultimul
   tabel.

**Pentru specialiști.** Toate comenzile se dau din rădăcina depozitului, adică din directorul principal al proiectului,
după `set PYTHONPATH=src`; în PowerShell, echivalentul este `$env:PYTHONPATH="src"`. Comenzile Python încep toate cu
`.venv\Scripts\python -m`; în tabele, acest început nu mai este scris.

**Statisticile, fără simulări.** Cifrele obținute pe capacitatea calibrată, adică cele din § 9.9 și § 9.10 și analiza
cu capacitatea calibrată din § 9.6, se reproduc exact cu comenzile de mai jos și cu cele din tabelul simulărilor, dar nu
mai sunt valabile: geamănul de atunci ducea traficul prin coliziuni și teleportări în masă, deci câștigul de −7% al
planului 12/14/12 și comparațiile agenților pe acel geamăn s-au retras pe 2.11 (§ 6.5, § 9.11). Comenzile rămân ca
istoria să se poată verifica. Modulul `romana.control.analiza` compară strategiile pe perechi de simulări, cu același
scenariu și același seed. Implicit, fiecare strategie și fiecare program se compară cu planul fix (`FIX`) și cu
actuated (`ACTUATED`), strategia clasică care prelungește verdele cât timp detectoarele văd vehicule (§ 7.4). De aceea,
actuated nu apare și ca strategie comparată. Rândurile „Actuated” din § 9.4 și § 9.8 se obțin cu
`--strategii ACTUATED --referinte FIX`.

| Cifrele din text | Comanda |
|---|---|
| § 9.8, participanți indisciplinați: programul realist, cu −6,2% față de planul fix și −11,7% față de actuated; agenții; planul 46/48/12 | `romana.control.analiza docs\rezultate\calibrat_indisciplinat.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --pe-scenarii` |
| § 9.8, participanți disciplinați: programul realist, cu −1,3% față de planul fix și −4,3% față de actuated; agenții, cu +1,0…+3,6% față de planul fix | aceeași comandă, pe `docs\rezultate\calibrat_normal.csv` |
| § 9.4, pe 10 seed-uri: agenții față de planul fix; programul realist, cu −16,0% față de planul fix și −18,4% față de actuated | `romana.control.analiza docs\rezultate\robustete_indisciplinat.csv docs\rezultate\robustete_indisciplinat_6_10.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --pe-scenarii` |
| Rândurile „Actuated”: § 9.4, +6,4%, mai bun în 25 / 50; § 9.8, +7,4%, mai bun în 20 / 50 | aceleași fișiere, cu `--strategii ACTUATED --referinte FIX` |
| § 9.4, programul realist pe duminică: −4,4%, mai bun în 40 / 50; dimineața de duminică intră în banda de trafic lejer | `romana.control.analiza docs\rezultate\robustete_indisciplinat_duminica.csv docs\rezultate\robustete_indisciplinat_duminica_6_10.csv --benzi "lejer=*linistit*,*dimineata;moderat=*pranz*;greu" --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3`. Cu benzile implicite, dimineața ar intra la „greu”, iar rezultatul ar fi −3,7% |
| § 9.2, programele pentru marginea de sus și pentru marginea de jos, cele două calibrări mai vechi ale cererii; § 9.3, duminica | marginea de sus: `romana.control.analiza docs\rezultate\rezultate_brute_marginea_de_sus.csv --exclude "*2026-10-25*" --program SUS=lejer:rl_ppo_romana_lejer,moderat:rl_ppo_romana_zn3,greu:plan_46_48_12 --referinte fix_referinta actuated`. Marginea de jos: `romana.control.analiza docs\rezultate\rezultate_brute.csv --exclude "*2026-10-25*" --program JOS=lejer:actuated,moderat:rl_ppo_romana_zn3,greu:fix_referinta --referinte fix_referinta actuated`. Duminica (§ 9.3): aceleași comenzi, cu `--scenarii "*2026-10-25*" --benzi "lejer=*linistit*,*dimineata;moderat=*pranz*;greu"` în loc de `--exclude` |
| § 9.5, validarea E12 / E13: −5,9% / −2,3% / +1,7% / −9,3% / −10,1%, medii pe perechi | `romana.control.analiza docs\rezultate\validare_calibrat.csv --referinte FIX` |
| § 9.5, programul reantrenat pe test: −6,7% / −3,9% față de planul fix și +1,0% / −0,5% față de programul realist; fără `--strategii` apar și agenții | `romana.control.analiza docs\rezultate\calibrat_indisciplinat.csv docs\rezultate\test_reantrenare_indisciplinat.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program REANTRENAT=lejer:ppo_romana_cal,moderat:cand_romana_cal3_100k,greu:cand_romana_cal3_100k --strategii REANTRENAT --referinte FIX REALIST`. La fel pe `calibrat_normal.csv` cu `test_reantrenare_normal.csv` |
| § 9.9, toate strategiile pe luni 26.10, față de planul fix și față de actuated | `romana.control.analiza docs\rezultate\capacitate_indisciplinat_26.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program REANTRENAT=lejer:ppo_romana_cal,moderat:cand_romana_cal3_100k,greu:cand_romana_cal3_100k --pe-scenarii`. Rândurile actuated și 46/48/12: `--strategii ACTUATED PLAN_46_48_12 --referinte FIX`. La fel pe `capacitate_normal_26.csv` |
| § 9.9, verificarea pe 10 seed-uri: E13, cu −9,2% / −7,9% față de planul fix și −3,9% față de programul realist pe 120 de perechi | `romana.control.analiza docs\rezultate\capacitate_indisciplinat_26.csv docs\rezultate\capacitate_indisciplinat_26_6_10.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --referinte FIX REALIST ACTUATED`. La fel cu fișierele `capacitate_normal_26*`. Pentru perechile reunite: toate cele patru fișiere și `--referinte FIX REALIST` |
| § 9.5 / § 9.9, validarea E14: −6,3% față de planul fix și +2,2% față de E13 | `romana.control.analiza docs\rezultate\validare_e14.csv --referinte FIX ppo_romana_cal`. O strategie dată ca referință nu mai apare și ca strategie comparată; de aceea, E13 față de planul fix se obține cu `--referinte FIX` |
| § 9.9, grila de planuri fixe pe geamănul calibrat: 12/14/12, cu −9,3% față de planul fix și −0,9% față de E13; `TOD_FIX`, cu −10,8% / −2,3% | `romana.control.analiza docs\rezultate\grila_calibrat.csv docs\rezultate\validare_e14.csv --program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --strategii PLAN_12_14_12 TOD_FIX --referinte FIX ppo_romana_cal`. Fără `--strategii` și cu `--referinte FIX` apar toate cele 23 de planuri. Alegerea pe fiecare bandă s-a făcut după media pe scenarii a diferențelor procentuale, ca în `romana.control.validare` |
| § 9.10, decizia pe miercuri 28.10: tabelul candidaților și câștigătorul | `romana.control.decizie docs\rezultate\test_28_indisciplinat.csv docs\rezultate\test_28_normal.csv --out outputs\validare\decizie.json`. Rezultatul publicat: `docs\rezultate\decizie_2026-10-28.json`. Debitele scenariilor vin din `sumo\demand\zi_2026-10-28_rezumat.json` |
| § 9.10, toate strategiile: pierderea totală de timp, apoi împărțită pe cele două comportamente ale participanților, pe cazuri de trafic și pe tipuri de participanți, și totalul fără noapte | `romana.control.totaluri docs\rezultate\test_28_indisciplinat.csv docs\rezultate\test_28_normal.csv`. Pentru confirmare: la fel, cu `test_29_*` |
| § 9.10, confirmarea pe joi 29.10: verdictul, decizia refăcută pe 29.10 și decizia pe ambele zile | `romana.control.decizie docs\rezultate\test_29_indisciplinat.csv docs\rezultate\test_29_normal.csv --confirma PLAN_12_14_12 --out outputs\validare\confirmare.json`; rezultatul publicat: `docs\rezultate\confirmare_2026-10-29.json`. Fără `--confirma` se obține decizia refăcută doar pe 29.10, publicată ca `decizie_2026-10-29.json`. Cu cele patru fișiere `test_28_*` și `test_29_*` se obțin ambele zile reunite; debitele vin din `sumo\demand\zi_2026-10-2[89]_rezumat.json` |
| § 9.10, testele pe perechi ale tuturor strategiilor, de exemplu 16/10/12 față de 12/14/12: p = 0,51 | `romana.control.analiza docs\rezultate\test_28_indisciplinat.csv docs\rezultate\test_28_normal.csv --program REALIST=lejer:ppo_romana,moderat:ppo_romana_zn3,greu:ppo_romana_zn3 --program TOD_DEBIT=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --benzi "<câmpul benzi_analiza din decizie_2026-10-28.json>" --referinte FIX REALIST TOD_DEBIT PLAN_12_14_12`. Pe fiecare comportament: un singur fișier și `--pe-scenarii`. Pentru confirmare: `test_29_*`, cu `benzi_analiza` din `decizie_2026-10-29.json`. `TOD_FIX` pe 29.10 (−0,5%, p = 0,052) se obține din cele două fișiere `test_29_*`, fără `--benzi`, cu `--program TOD_FIX=lejer:PLAN_16_10_12,moderat:PLAN_16_10_12,greu:PLAN_12_14_12 --strategii TOD_FIX --referinte PLAN_12_14_12`. Fără `--benzi` se folosesc benzile implicite, după numele scenariilor; cu `benzi_analiza`, `TOD_FIX` ar ieși identic cu `TOD_DEBIT`. Totalul lui `TOD_FIX`, 80 094 h, este suma rulărilor lui 16/10/12 pe liniștit, liniștit ×0,8 și prânz și a rulărilor lui 12/14/12 pe celelalte ferestre |
| § 9.10, măsura pe persoană, cu 20 / 40 / 70 de călători pe autobuz | `romana.control.ocupare docs\rezultate\test_28_indisciplinat.csv docs\rezultate\test_28_normal.csv --autobuz 40 --out outputs\validare\test_28_persoane_40.csv`, apoi `romana.control.decizie outputs\validare\test_28_persoane_40.csv --out outputs\validare\decizie_persoane_40.json`. Rezultatul publicat: `decizie_2026-10-28_persoane_40.json`; la fel cu 20 și 70. Pentru confirmare: `test_29_*`, publicat ca `decizie_2026-10-29_persoane_*.json` |
| § 9.10, sensibilitatea la o fază de pietoni de 18 s: 12/14/18 față de 36/28/18, −7,9% din total, mai bun în 92 / 120 | `romana.control.totaluri docs\rezultate\test_28_indisciplinat.csv docs\rezultate\test_28_normal.csv docs\rezultate\sens_pietoni_28_indisciplinat.csv docs\rezultate\sens_pietoni_28_normal.csv --referinte PLAN_36_28_18 FIX REALIST`. Testele pe perechi: `romana.control.analiza` cu aceleași patru fișiere și `--strategii PLAN_12_14_18 --referinte PLAN_36_28_18 PLAN_12_14_12` |
| § 9.10, verdele pe fiecare trecere de pietoni, care arată dacă planurile scurte sunt fezabile | `romana.control.treceri --plan 12,14,12 --plan 16,10,12 --plan 36,28,12`. Modulul încarcă rețeaua dintr-un scenariu, fără simulare |
| § 4.6 / § 9.10, prelucrarea încetinită din 28.10, la 03:45, 04:00 și 04:15, și celelalte episoade, din 27.10 și 26.10 | `romana.vision.calitate data\trajectories_brute\traiectorii_2026-10-2*.jsonl.gz --out-15min outputs\calitate_15min.csv`. Jurnalele brute există doar local |
| Corectarea câmpului `seeduri_validare` din fișierele de alegere existente | `romana.control.validare --corecteaza-alegeri docs\rezultate` |

**Simulările.** Determinismul lor a fost verificat pe rulări din `calibrat_normal.csv`, `calibrat_indisciplinat.csv`,
`robustete_indisciplinat.csv` și `validare_indisciplinat.csv`. Comenzile din tabelul de mai jos folosesc exact
strategiile și seed-urile din fișierul publicat. Numărul de simulări rulate în paralel se alege cu `--procese N`:
implicit 4 la `validare` și 1 la `evaluate`, iar `5_evalueaza.bat` trece 6.

Scenariile se regenerează însă, cu aceleași nume, la fiecare recalibrare a cererii. De aceea, un fișier de rezultate se
reproduce numai cu **versiunea scenariilor din momentul rulării**. Ea este dată în coloana „Scenariile”, aici și în
Anexa A:

- „arborele curent” înseamnă scenariile actuale, din versiunea de acum a depozitului;
- „tipurile vechi”, de exemplu la `calibrat_*.csv`, înseamnă că sunt necesare și tipurile de vehicule de dinainte de
  28.10, aduse cu `git checkout 75592d3 -- sumo/demand/vtypes.add.xml sumo/demand/vtypes_indisciplinat.add.xml`
  (Anexa A);
- codul unui commit, adică al unei versiuni salvate în istoricul git, de exemplu `e1d0f77`, înseamnă că scenariile se
  aduc temporar din istoric, ca în README: `git checkout e1d0f77 -- sumo/scenarios sumo/demand config/demand.json`, iar
  după rulare `git checkout HEAD -- sumo config/demand.json`.

Aducerea din istoric nu șterge fișierele apărute după acel commit: ele rămân cele curente, de exemplu
`indisciplinat_zi_2026-10-25_pranz`. De aceea, scenariile se dau explicit, unul câte unul, fără tipare cu `*`. O
variantă care nu atinge fișierele din directorul de lucru este arhiva commitului:
`git archive -o outputs\e1d0f77.tar e1d0f77 sumo`, dezarhivată cu `mkdir outputs\e1d0f77` și
`tar -xf outputs\e1d0f77.tar -C outputs\e1d0f77`. Scenariile se dau atunci prin cale:
`--scenarii outputs\e1d0f77\sumo\scenarios\<scenariu>.sumocfg`.

Rulările noi se scriu în `outputs\validare\`. Opțiunea `--compara` le compară cu fișierul publicat și arată rulările
comune, câte dintre ele sunt identice și diferența maximă. Modulul `romana.control.validare` refuză să suprascrie un
fișier existent din `docs\rezultate\` fără `--suprascrie`. În schimb, `romana.control.evaluate` scrie direct în
`docs\rezultate\`: rezultatul se compară cu `git diff --stat docs/rezultate`, apoi fișierele publicate se refac cu
`git checkout -- docs/rezultate`.

| Fișierul (secțiunea) | Scenariile | Comanda |
|---|---|---|
| scenariile `indisciplinat_*` (§ 9.4) | arborele curent | `romana.bridge.indisciplinat --verifica` verifică, fără să scrie nimic, că acestea sunt exact copiile scenariilor `zi_*` cu `vtypes_indisciplinat.add.xml`. Fără `--verifica`, comanda le regenerează lângă sursă |
| `calibrat_indisciplinat.csv`, `calibrat_normal.csv` (§ 9.8) | arborele curent, tipurile vechi | `romana.control.validare ACTUATED PLAN_46_48_12 models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_lejer.zip --scenarii "indisciplinat_zi_2026-10-2[12]_*" --seeds 1-5 --fara-alegere --out outputs\validare\calibrat_indisciplinat.csv --compara docs\rezultate\calibrat_indisciplinat.csv`. Pentru participanți disciplinați: `--scenarii "zi_2026-10-2[12]_*"`, cu `calibrat_normal` în loc de `calibrat_indisciplinat` |
| `calitate_inregistrare.csv` (§ 4.6) | – (din jurnalele de traiectorii) | `romana.vision.calitate data\trajectories\traiectorii_2026-10-2[125689].jsonl.gz --out outputs\calitate.csv`. Fișierul publicat a fost calculat din jurnalele brute, care există doar local; pe jurnalele publicate, cifrele ies practic aceleași |
| `veghe_reluare.csv` (§ 4.6) | – (din jurnalele de traiectorii) | `romana.vision.veghe --reluare data\trajectories_brute\traiectorii_2026-10-28.jsonl.gz --out outputs\veghe_28.csv`, la fel pentru 21, 22, 25, 26, 27 și 29, cu coloana `zi` adăugată. Jurnalele brute există doar local. Pe jurnalele publicate, care nu au pietoni și au fragmentele de traiectorie reunite, coloanele traiectoriilor și timpul fără traiectorii noi ies altfel |
| `capacitate_baleiaj.csv` (§ 6.4) | arborele curent; tipurile vechi pentru rândurile „standard” | `romana.control.capacitate zi_2026-10-26_varf t10s0=1.0:2.5:0 t10g20=1.0:2.0:0.5 t09g25=0.9:2.5:0.5 t09g20=0.9:2.0:0.5 t08g25=0.8:2.5:0.5 t08g20=0.8:2.0:0.5 t08s3=0.8:2.0:0.3 --out outputs\capacitate.csv`, apoi `zi_2026-10-26_varf_x1_2 t09g20=0.9:2.0:0.5 t08g20=0.8:2.0:0.5 t08s3=0.8:2.0:0.3`. Separat, pentru rândul adăugat pe 27.10, fără al doilea rând „standard”: `zi_2026-10-26_varf_x1_2 t08g25=0.8:2.5:0.5` |
| `localizare_varf_capacitate.csv` (§ 9.6) | arborele curent; pentru rândul `zi_2026-10-26_varf`, tipurile vechi | `romana.control.localizare capacitate_zi_2026-10-26_varf capacitate_zi_2026-10-26_varf_x1_2 capacitate_indisciplinat_zi_2026-10-26_varf capacitate_indisciplinat_zi_2026-10-26_varf_x1_2 zi_2026-10-26_varf --out outputs\localizare_capacitate.csv` |
| scenariile `capacitate_*` (§ 6.4) | arborele curent | `romana.bridge.indisciplinat --scenarii "sumo\scenarios\zi_2026-10-2[56]_*.sumocfg" --vtypes vtypes_capacitate.add.xml --prefix capacitate_`, apoi aceeași comandă cu `--vtypes vtypes_capacitate_indisciplinat.add.xml --prefix capacitate_indisciplinat_` |
| agenții E12 / E13 (§ 9.5) | arborele curent, tipurile vechi | pentru E12 se copiază `models\ppo_romana_zn3.*` în `models\ppo_romana_cal3.*`, iar pentru E13, `models\ppo_romana.*` în `models\ppo_romana_cal.*`. Apoi se rulează `romana.control.train --nume romana_cal3 --continua --lr 3e-5 --pasi 300000 --medii 8 --scenarii` cu cele 20 de fișiere `sumo\scenarios\zi_2026-10-2[12]_*.sumocfg` și `indisciplinat_zi_2026-10-2[12]_*.sumocfg`, apoi la fel cu `--nume romana_cal`. Punctele intermediare, adică modelele salvate pe parcursul antrenării, sunt în `outputs\train\<nume>\checkpoints`. Antrenarea PPO nu este deterministă pe mai multe procese, deci modelele refăcute diferă ușor de cele publicate |
| `validare_calibrat.csv` (§ 9.5) | arborele curent, tipurile vechi | `romana.control.validare ACTUATED models\ppo_romana.zip models\ppo_romana_zn3.zip models\cand_romana_cal3_100k.zip models\ppo_romana_cal3.zip models\ppo_romana_cal.zip --scenarii "indisciplinat_zi_2026-10-2[12]_*" --seeds 11-15 --out outputs\validare\validare_calibrat.csv --compara docs\rezultate\validare_calibrat.csv` |
| `test_reantrenare_indisciplinat.csv`, `test_reantrenare_normal.csv` (§ 9.5) | arborele curent, tipurile vechi | `romana.control.validare models\cand_romana_cal3_100k.zip models\ppo_romana_cal.zip --scenarii "indisciplinat_zi_2026-10-2[12]_*" --seeds 1-5 --fara-alegere --fara-fix --out outputs\validare\test_reantrenare_indisciplinat.csv --compara docs\rezultate\test_reantrenare_indisciplinat.csv`. Pentru participanți disciplinați: `--scenarii "zi_2026-10-2[12]_*"`, cu `test_reantrenare_normal` |
| `capacitate_indisciplinat_26.csv`, `capacitate_normal_26.csv` (§ 9.9) | arborele curent | `romana.control.validare ACTUATED PLAN_46_48_12 models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_lejer.zip models\cand_romana_cal3_100k.zip models\ppo_romana_cal.zip --scenarii "capacitate_indisciplinat_zi_2026-10-26_*" --seeds 1-5 --fara-alegere --out outputs\validare\capacitate_indisciplinat_26.csv --compara docs\rezultate\capacitate_indisciplinat_26.csv`. Pentru participanți disciplinați: `--scenarii "capacitate_zi_2026-10-26_*"`, cu `capacitate_normal_26` |
| `capacitate_indisciplinat_26_6_10.csv`, `capacitate_normal_26_6_10.csv` (§ 9.9) | arborele curent | aceeași comandă, cu `--seeds 6-10` și cu `_26_6_10` în locul lui `_26` în cele două nume de fișier |
| agentul E14 (§ 9.5) | arborele curent | se copiază `models\ppo_romana_cal.*` în `models\ppo_romana_e14.*`, apoi se rulează `romana.control.train --nume romana_e14 --continua --lr 3e-5 --pasi 300000 --medii 8 --scenarii` cu cele 12 fișiere `sumo\scenarios\capacitate_zi_2026-10-26_*.sumocfg` și `capacitate_indisciplinat_zi_2026-10-26_*.sumocfg`. Ca la E12 / E13, modelele refăcute diferă ușor de cel publicat |
| `validare_e14.csv` (§ 9.5) | arborele curent | `romana.control.validare ACTUATED models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_cal.zip models\cand_romana_e14_100k.zip models\cand_romana_e14_200k.zip models\ppo_romana_e14.zip --scenarii "capacitate_*zi_2026-10-26_*" --seeds 11-15 --out outputs\validare\validare_e14.csv`. Punctele intermediare nu sunt publicate: `cand_romana_e14_100k` și `cand_romana_e14_200k` sunt fișierele `outputs\train\romana_e14\checkpoints\romana_e14_901344_steps.zip` și `romana_e14_1001344_steps.zip` |
| `grila_calibrat.csv` (§ 9.9) | arborele curent | `romana.control.validare` cu cele 23 de planuri `PLAN_a_b_12`, pentru (a, b) = (28, 22), (28, 28), (28, 36), (36, 22), (36, 36), (44, 22), (44, 28), (44, 36), (20, 14), (20, 18), (20, 22), (24, 14), (24, 18), (24, 22), (28, 14), (28, 18), (12, 10), (12, 14), (12, 18), (16, 10), (16, 14), (16, 18), (20, 10), unde a și b sunt secundele de verde pentru nord–sud și est–vest, și cu `--scenarii "capacitate_*zi_2026-10-26_*" --seeds 11-15 --out outputs\validare\grila_calibrat.csv`. Grila a fost rulată pe 28.10 în trei tranșe, de 8 + 8 + 7 planuri, apoi reunite; fiecare rafinare s-a făcut în jurul celui mai bun plan de până atunci. Simulările sunt deterministe, iar planul fix a ieșit identic în toate tranșele |
| `durate_verde_agenti.csv` (§ 9.9) | arborele curent | `romana.control.durate_verde models\ppo_romana_cal.zip models\ppo_romana.zip --scenarii capacitate_zi_2026-10-26_linistit capacitate_zi_2026-10-26_pranz capacitate_zi_2026-10-26_varf --seed 11 --out outputs\durate_verde.csv` |
| `sens_pietoni_28_indisciplinat.csv`, `sens_pietoni_28_normal.csv` (§ 9.10) | arborele curent | `romana.control.validare PLAN_12_14_18 PLAN_36_28_18 --scenarii "indisciplinat_zi_2026-10-28_*" --seeds 1-10 --fara-alegere --fara-fix --procese 4 --out outputs\validare\sens_pietoni_28_indisciplinat.csv --compara docs\rezultate\sens_pietoni_28_indisciplinat.csv`. Pentru participanți disciplinați: `--scenarii "zi_2026-10-28_*"`, cu `sens_pietoni_28_normal`. Fiecare rulare durează ≈30 min pe 4 procese |
| `test_28_indisciplinat.csv`, `test_28_normal.csv` (§ 9.10) | arborele curent | `romana.control.validare ACTUATED models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_cal.zip PLAN_12_14_12 PLAN_16_10_12 --scenarii "indisciplinat_zi_2026-10-28_*" --seeds 1-10 --fara-alegere --procese 11 --out outputs\validare\test_28_indisciplinat.csv --compara docs\rezultate\test_28_indisciplinat.csv`. Pentru participanți disciplinați: `--scenarii "zi_2026-10-28_*"`, cu `test_28_normal`. Fiecare rulare durează ≈1 h pe 11 procese |
| `test_29_indisciplinat.csv`, `test_29_normal.csv` (§ 9.10, confirmarea) | arborele curent | aceeași comandă, cu `2026-10-29` în locul lui `2026-10-28` în scenarii și cu `test_29` în locul lui `test_28` în cele două nume de fișier; fiecare rulare durează ≈1,5 h pe 11 procese. Scenariile zilei se construiesc cu `romana.bridge.scenarii_zi --zi 2026-10-29 --exclude 08:30-09:00`, apoi cu `romana.bridge.indisciplinat --scenarii "sumo\scenarios\zi_2026-10-29_*.sumocfg"` |
| `localizare_varf_calibrat.csv` (§ 9.6) | arborele curent, tipurile vechi | `romana.control.localizare zi_2026-10-21_varf zi_2026-10-22_varf indisciplinat_zi_2026-10-21_varf indisciplinat_zi_2026-10-22_varf --out outputs\localizare_varf.csv`, care dă aceleași valori ca fișierul publicat |
| `robustete_indisciplinat.csv`, `robustete_indisciplinat_6_10.csv` (§ 9.4) | `e1d0f77` | `romana.control.validare ACTUATED models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_lejer.zip --scenarii indisciplinat_zi_2026-10-21_pranz indisciplinat_zi_2026-10-21_varf indisciplinat_zi_2026-10-22_varf indisciplinat_zi_2026-10-22_linistit indisciplinat_zi_2026-10-22_dimineata --seeds 1-5 --fara-alegere --out outputs\validare\robustete_indisciplinat.csv --compara docs\rezultate\robustete_indisciplinat.csv`. Pentru seed-urile 6–10: `--seeds 6-10`, cu `robustete_indisciplinat_6_10` în cele două nume de fișier |
| `robustete_indisciplinat_duminica.csv`, `robustete_indisciplinat_duminica_6_10.csv` (§ 9.4) | `e1d0f77` | `romana.control.validare ACTUATED models\ppo_romana.zip models\ppo_romana_zn3.zip --scenarii indisciplinat_zi_2026-10-25_dimineata indisciplinat_zi_2026-10-25_linistit indisciplinat_zi_2026-10-25_linistit_x0_8 indisciplinat_zi_2026-10-25_varf indisciplinat_zi_2026-10-25_varf_x1_2 --seeds 1-5 --fara-alegere --out outputs\validare\robustete_indisciplinat_duminica.csv --compara docs\rezultate\robustete_indisciplinat_duminica.csv`. Pentru seed-urile 6–10: `--seeds 6-10`, cu `robustete_indisciplinat_duminica_6_10` |
| `validare_indisciplinat.csv` + `_alegere.json`, alegerea programului realist (§ 9.4) | `e1d0f77` | `romana.control.validare ACTUATED PLAN_46_48_12 models\ppo_romana.zip models\ppo_romana_zn3.zip models\ppo_romana_lejer.zip --scenarii indisciplinat_zi_2026-10-21_pranz indisciplinat_zi_2026-10-21_varf indisciplinat_zi_2026-10-22_varf indisciplinat_zi_2026-10-22_linistit indisciplinat_zi_2026-10-22_dimineata --seeds 11-15 --out outputs\validare\validare_indisciplinat.csv --compara docs\rezultate\validare_indisciplinat.csv`. Alegerea, scrisă în `outputs\validare\validare_indisciplinat_alegere.json`, se compară cu cea publicată |
| `validare_intrari.csv` + `_alegere.json`, componentele marginii de jos (§ 9.2) | `e1d0f77` | `romana.control.validare ACTUATED PLAN_46_48_12 models\ppo_romana.zip models\ppo_romana_lejer.zip models\ppo_romana_zn3.zip models\ppo_romana_greu_e7_400k.zip --scenarii "zi_2026-10-2[12]_*" --seeds 11-15 --out outputs\validare\validare_intrari.csv --compara docs\rezultate\validare_intrari.csv` |
| `rezultate_brute.csv`, `rezultate.md` și graficul, pentru marginea de jos (§ 9.2–9.3) | `e1d0f77` | `romana.control.evaluate`, pornit direct sau prin `scripts\5_evalueaza.bat`, cu scenariile, strategiile, modelele și seed-urile din fișier, date explicit prin `--scenarii`, `--strategii`, `--model`, `--seeds` și `--seed-start` |
| `rezultate_brute_marginea_de_sus.csv` și validările marginii de sus din 23–25.10 (Anexa A) | `7a79502` | aceleași module: `romana.control.evaluate`, respectiv `romana.control.validare`, cu strategiile, scenariile și seed-urile din fișier |
| fișierele din 21–22.10 (Anexa A) | `1619a30`, `8176be5`, `a845bf9` | au fost produse cu codul de atunci, dinaintea corecturii din `control/env.py` și dinaintea modulului `validare`. Se refac numai cu toate fișierele acelui commit, într-un director separat, de exemplu cu `git worktree add ..\romana_8176be5 8176be5` |

**Calibrarea din § 4.3** se reface din datele publicate în `docs\rezultate\referinta\`. Ea are două părți: factorii de
corecție ai numărării automate și modelul camerei. Ultimul rând arată cum se face o numărătoare de referință nouă.

| Ce se reface | Comanda |
|---|---|
| Factorii de corecție și procentele „prins”, adică partea din numărătoarea de referință pe care o prinde numărarea automată (§ 4.3) | `romana.vision.referinta factori --clip docs\rezultate\referinta\clip1\traiectorii docs\rezultate\referinta\referinta_clip1.csv --clip docs\rezultate\referinta\clip2\traiectorii docs\rezultate\referinta\referinta_clip2.csv`, care dă aceleași valori ca în `factori.json`, cu sau fără `--fara-reunire`. La 2560 px: directoarele `clip1_2560` și `clip2_2560`. Cu zonele vechi: în plus `--camera outputs\camera_e1d0f77.json`, după ce se rulează, în cmd, `git show e1d0f77:config/camera.json > outputs\camera_e1d0f77.json` |
| Modelul camerei, adică omografia care duce punctele din imagine pe planul străzii (§ 4.3) | `romana.vision.calibrare_camera potrivire docs\rezultate\referinta\corespondente_camera.json --out outputs\calibrare_camera`, care dă exact `model_camera.json` și `erori_camera.csv`. Zonele derivate din rețea: `romana.vision.calibrare_camera zone outputs\calibrare_camera\model.json`, într-un fișier separat de `config\camera.json` |
| O numărătoare de referință nouă, pe un clip nou, făcută local | reperele rețelei, cu o grilă de 5 m, pentru corespondențe: `romana.vision.calibrare_camera repere --harta outputs\calibrare_camera\harta.png`. Foile de contact pentru adnotatori: `romana.vision.referinta foi tinte.json clip.mp4`. Lanțul de prelucrare din timp real, aplicat pe clip, cu ieșirile în `outputs\referinta\clip\`: `romana.vision.referinta viziune clip.mp4`. Publicarea, doar cu vehiculele: `romana.vision.referinta publica outputs\referinta\clip\traiectorii docs\rezultate\referinta\clip\traiectorii`. Referința este un fișier CSV `tinta,bucata,adnotator,numar` sau `tinta,bucata,numar`, cu numărul final pe bucată |

Clipurile, foile de contact și suprapunerile conțin imagini ale camerei. De aceea rămân doar local, în `outputs\`,
director exclus din Git, numai pe durata calibrării, și se șterg după aceea (§ 4.5, § 14.1). În depozit ajung numai
date fără imagini: numărătorile adnotatorilor; traiectoriile vehiculelor din clipuri, fără pietoni, ca la
`recount --publica`; factorii de corecție; corespondențele calibrării, care sunt doar coordonate. Pe aceste fișiere,
`referinta factori` dă exact factorii, intervalele de încredere și procentele din § 4.3, aceleași ca pe jurnalele
complete ale clipurilor. La fel, `calibrare_camera potrivire` reface exact modelul camerei. Jurnalele complete, cu
pietoni, sunt necesare doar pentru zebrele de pe Dacia est și rămân la autor, în `outputs\referinta\`.

## 12. Jurnalul proiectului

Acest capitol spune povestea construirii proiectului: ce s-a încercat, ce nu a mers, ce s-a corectat și de ce.
Istoricul exact al modificărilor se află pe GitHub, în commit-uri, adică în versiunile salvate succesiv ale
proiectului. Mesajele commit-urilor care țin de o bornă, adică de un pas mare al lucrului (§ 12.3), încep cu
„Borna N: …”.

**Echipa.** Autorul, Niunin Matei-Gabriel, a coordonat lucrul. El a stabilit obiectivele și regulile: rețeaua
trebuie să fie fidelă realității, în simulare intră toți participanții, datele sunt reale și se schimbă doar
programul semaforului. Tot el a verificat pe teren și în imagini, a corectat greșelile și a venit cu ideile-cheie.
Implementarea a făcut-o asistentul AI Claude, dezvoltat de Anthropic, prin programul Claude Code, rulat local pe
laptopul autorului. Pentru ciorna inițială, până la 18.10.2026, asistentul a fost modulul AI Google (capitolul 13).

### 12.1 Etapele proiectului

Etapele de mai jos urmează firul lucrului. Proiectul a pornit de la o ciornă neverificată și a ajuns, pe 28 și 29.10,
la un plan de semaforizare ales pe o zi nouă de trafic și confirmat pe ziua următoare. Rezultatul s-a retras pe 2.11:
geamănul pe care rula trecea traficul prin coliziuni și teleportări (etapa 12, § 6.5). Pe geamănul corectat, validarea
din 4.11 nu a putut alege niciun candidat, deci nu se propune un program nou, iar în geamăn rămâne planul observat,
72/48/3 (etapa 13, § 9.11). Procentele „față de planul fix” din etapele de mai jos privesc planul de referință,
36/28/12, o ipoteză despre programul semaforului pe care camera a infirmat-o pe 2.11 (§ 6.5). Cele mai mari schimbări
de rezultat au venit din corectarea datelor și a simulării, nu din algoritm (§ 12.4).

**Etapa 0 – de la ciornă la un proiect serios (până la 20.10.2026).** Ciorna inițială folosea trafic aleatoriu,
într-un scenariu generat automat cu `osmWebWizard`. Scenariul ajungea în blocaj, iar agentul AI al ciornei nu fusese
verificat. Ciorna a fost analizată amănunțit și păstrată în `legacy/`, iar proiectul a fost reorganizat pe borne
(§ 12.3). Regula de bază, stabilită de autor: **nu se schimbă nimic din infrastructură** – doar felul în care
semafoarele existente răspund traficului.

**Etapa 1 – rețeaua fidelă și toți participanții (noaptea de 20–21.10).** Rețeaua a fost refăcută ca replică
fidelă după OpenStreetMap (OSM), cu trecerile de pietoni, trotuarele și benzile STB, rezervate transportului public.
Cele 16 semafoare fizice ale pieței sunt comandate de un singur controler, prin grupuri de semnal: toate semafoarele
dintr-un grup arată mereu aceeași culoare. Au apărut trei probleme, toate rezolvate:

* Importul trecerilor din OSM bloca `netconvert`, programul care construiește rețeaua, așa că trecerile au fost
  reconstruite din geometria străzilor.
* Inelul pieței se bloca singur, pentru că ieșirile primeau roșu. Acum ieșirile au verde în fazele de vehicule.
* Strategiile de referință, cu care se compară agenții, aveau defecte. Programul actuated, care prelungește verdele
  cât timp detectoarele văd vehicule, avea faze greșite. Planul Webster se calculează cu formula clasică a ciclului
  optim, dar codul lui citea datele după chei vechi, adică după denumiri depășite. Max-Pressure, care alege faza cu
  cea mai mare diferență între cozile de dinaintea intersecției și cele de după ea, bloca inelul: alegea faze care
  deschideau intrările spre inel fără dozare, adică fără să limiteze câte vehicule intră.

Cea mai instructivă lecție a venit de la **agentul care trișa**. Agentul pentru coridor, care comanda piața împreună
cu intersecțiile vecine, ținea vehiculele în afara rețelei, ca să nu apară în cozi. De atunci, vehiculele care
așteaptă să intre contează în recompensă, adică în scorul după care învață agentul, la fel ca vehiculele oprite.

**Etapa 2 – ochii sistemului (21.10).** În zona modelată există o singură cameră publică, cea din Piața Romană, așa
că intersecțiile vecine sunt simulate din datele ei. La început, detecția participanților la trafic rula pe
procesor, cu doar 0,9 cadre/s. Mutată pe placa grafică Intel cu ajutorul OpenVINO, un set de unelte pentru rețele
neuronale, a ajuns la ~5–6 cadre/s. Unele numărări erau absurde: întoarceri false „Magheru → Magheru” sau mașini de
pe inel numărate ca intrări pe Dacia vest. De aici a venit regula de numărare pe traiectoria întreagă (§ 4.3): un
vehicul este numărat abia la capătul traiectoriei, după tot drumul lui prin imagine. În simulare, rutele porneau de
la linia de oprire și blocau intrarea vehiculelor; acum pornesc de la capătul bulevardelor. Au existat și piedici
practice. Programul git părea să nu aibă, în linia de comandă, datele de autentificare pentru GitHub, așa că
modificările s-au trimis pe GitHub, până pe 3.11, prin aplicația GitHub Desktop. Pe 3.11 s-a văzut că datele existau,
dar git nu știa singur ce cont să folosească; de atunci, modificările se trimit direct din linia de comandă. În plus,
laptopul funcționa în modul de economisire a energiei.

**Etapa 3 – primele rezultate pe date reale (22.10).** Din două zile de trafic real s-au construit 10 scenarii și
s-au rulat 300 de simulări. Rezultatul agentului AI: −4,6% timp pierdut față de planul fix, care are mereu aceleași
durate de verde și servește drept referință. Autorul a făcut două corecturi: strada se numește Calea Dorobanți, iar
intersecția Dacia × Polonă e sens unic de ieșire, deci nu intră în coridor. Patru experimente au ieșit negative:

* un agent care vede și cozile din amonte, adică de pe străzile care duc spre piață;
* un agent pornit de la imitarea unui plan fix;
* un agent cu orizont lung, care ține seama mai mult de efectele îndepărtate ale deciziilor;
* coordonarea a 4 intersecții vecine, care a dat chiar +35% timp pierdut.

Un diagnostic important: 68% din întârzierea de la vârf venea din coada de pe Bd. Dacia vest, dincolo de piață.
Analiza a fost refăcută pe 27.10, după calibrările din Etapa 8: pe cererea calibrată ponderea iese 50–78%, iar cu
capacitatea calibrată a geamănului digital, adică a copiei simulate a pieței, coada dispărea (§ 9.6). Acest ultim
rezultat s-a retras pe 2.11: geamănul calibrat trecea traficul prin coliziuni și teleportări (etapa 12, § 6.5). Pe
geamănul corectat, Dacia vest rămâne punctul lui slab: în zilele lucrătoare, geamănul duce acolo mai puține vehicule
decât numără camera (§ 6.5, § 9.11).

**Etapa 4 – tot sistemul, pornit în timp real (seara de 22.10).** Când camera, geamănul și dispeceratul au rulat
împreună, au ieșit la iveală defecte reale (§ 12.2, P1–P5, O8). Modulul de viziune se oprea când dispeceratul citea
imaginea în același timp. Geamănul revenea la fiecare 15 minute pe datele de rezervă. Imaginea mergea 2 s și stătea
4 s, dispeceratul arăta doar 1 cadru/s, iar vehiculele „săreau” în SUMO. Privind imaginea analizată, autorul a
observat că zonele de numărare erau desenate greșit. Cea mai memorabilă greșeală:
**marcajul de staționare interzisă, confundat cu trecerea de pietoni de pe Magheru**.

**Etapa 5 – datele corectate răstoarnă rezultatul (23.10).** Autorul a desenat el însuși zonele pe capturi ale
camerei. Ele au fost apoi așezate automat pe cadrul complet prin potrivire SIFT, o metodă care regăsește aceleași
puncte caracteristice în două imagini. Scara 3288/1920 a fost dedusă din potrivirile sigure. Localizarea automată a
mers abia după ce a fost corectată citirea fondului transparent al desenelor. Renumărarea a crescut numărul
virajelor urmărite complet, adică al vehiculelor văzute de la intrare până la ieșire, de la 2 800 la 4 995. Pe
scenariile corecte, agentul care dădea −4,6% a ajuns la **+5,2%**. Rezultatul frumos era construit pe date greșite,
iar acest lucru a fost raportat ca atare. Autorul a corectat și o greșeală a asistentului: acesta „văzuse” pe Dacia
est, în Street View, o singură bandă pe sens. În realitate sunt două, iar rețeaua era corectă.

**Etapa 6 – specialiști în loc de un agent universal (24–25.10).** Experimentele cu agenți, numerotate E1–E15, sunt
rezumate în § 9.5. O reantrenare scurtă (E2) a înrăutățit agentul. Următoarea reantrenare (E3), cu pași de învățare
de 10 ori mai mici, deci mai prudentă, l-a făcut cel mai bun la prânz. Ideea care a deblocat proiectul a fost un
**program pe tipuri de trafic**: agentul AI acolo unde e cel mai bun, un plan fix bine reglat la vârf. Un agent
antrenat de la zero, cu 1 milion de pași de antrenare (E4), nu a fost mai bun. Au urmat specialiștii, adică agenți
antrenați pentru un singur tip de trafic. Cei pentru trafic greu (E5–E7) au ajuns cel mult la nivelul celui mai bun
plan fix, iar cel pentru trafic lejer (E9) a fost puțin, dar sigur, mai bun.

Diferențele de 1–2 puncte procentuale își schimbau semnul între seed-urile de validare și cele de test. Un seed este
valoarea care pornește generatorul de numere aleatoare al simulării: seed-urile de validare servesc la alegerea
strategiei, iar cele de test la verificarea ei. De aici au venit validarea cu 5 seed-uri, stabilită dinainte, și
testele statistice pe perechi, în care două strategii sunt comparate pe aceleași scenarii și seed-uri. S-a lucrat
în condiții reale: dintr-o cafenea cu prize, până la plecarea autobuzului, cu opriri pentru masă și cu procesorul
limitat cât timp autorul avea nevoie de el.

**Etapa 7 – „ești sigur că numeri corect?” (25.10).** Întrebarea autorului a dus la o verificare amănunțită a
numărării. Camera număra 1,6 ieșiri pentru fiecare intrare. Explicația: pe inelul din fundal, detectorul pierde
vehiculele mici oriunde, iar o mașină pierdută în dreptul ieșirii Catargiu părea „ieșită”. Potrivit principiului
conservării, câte vehicule intră în piață, atâtea trebuie să și iasă. O calibrare după acest principiu a arătat că
ieșirile spre Dacia vest și Căderea Bastiliei nu pot fi deosebite de vehiculele pierdute. **Ideea autorului:**
semaforul controlează doar intrările, deci volumele de trafic se iau doar din intrări (§ 5.1).

Tot de la autor a venit testul cu participanți indisciplinați, adică șoferi și pietoni care nu respectă întotdeauna
regulile, ca pe străzile din București (§ 9.4). Prima rulare a testului a dat rezultate identice cu cele normale.
Așa a fost descoperit un defect: simularea ignora tipurile de participanți din scenariu. După corectare, testul a
adus cel mai puternic argument pentru AI: cu participanți indisciplinați, specialiștii AI au redus timpul pierdut cu
≈10–14% față de planul fix, iar la vârf diferența a ajuns până la −28%.

**Etapa 8 – măsurarea măsurării (26–28.10).** O numărătoare de referință, făcută ca să se vadă cât de bine numără
camera, a dat factorii de corecție pentru fiecare braț al pieței și zonele finale (§ 4.3). Pentru ea, două clipuri
au fost adnotate, adică numărate atent, fiecare de doi adnotatori AI independenți. Prima zi lucrătoare prelucrată
după aceea, luni 26.10, a ieșit cu de până la trei ori mai multe vehicule decât miercuri 21.10, la aceleași ore.
Cauza nu era camera și nici codul, ci înregistrarea: înainte de tamponul de redare adăugat fluxului video HLS pe
22.10 seara, urmărirea mergea în rafale și pierdea vehicule (§ 4.6). Debitul real, adică numărul real de vehicule
pe oră, a scos la iveală și o limită a geamănului: cu parametrii impliciți ai șoferilor simulați, el nu putea trece
traficul de luni. Calibrarea intervalului `tau` al șoferilor simulați părea să rezolve problema (§ 6.4). Pe 2.11 s-a
văzut însă că geamănul calibrat ducea traficul în mare parte prin coliziuni și teleportări, deci rezultatele obținute
pe el s-au retras (etapa 12, § 6.5).

Reantrenarea agenților pe zilele subnumărate din 21–22.10 (E12/E13) nu a schimbat alegerea. Pe validare, agentul
oficial, cel din Etapa 3, a rămas cel mai bun, iar pe test programul reantrenat a ieșit echivalent cu programul
realist, combinația de agenți AI aflată atunci în vigoare. Pe ziua de luni, nefolosită la antrenare, și cu geamănul
calibrat, agenții AI au bătut strategia actuated și, în medie, planul fix. Cel mai constant a fost agentul oficial
reantrenat, E13 (§ 9.9). Alegerea finală a fost lăsată pentru o zi nouă, miercuri 28.10, după un protocol fixat
dinainte. Reantrenarea pe ziua de luni cu geamănul calibrat (E14) nu l-a întrecut pe E13 (§ 9.5). Grila de planuri
fixe, adică seria de planuri cu durate diferite încercate pe rând, a fost refăcută pe geamănul calibrat. Ea a arătat
că un plan cu ciclu scurt, 12/14/12, ajunge pe validare la nivelul lui E13, așa că planul a intrat în test ca
referință raportată, adică afișată în rezultate pentru comparație (§ 9.9). Notația 12/14/12 înseamnă 12 s de verde
pentru axa nord–sud, 14 s pentru axa est–vest și 12 s pentru pietoni. Ciclul este timpul în care semaforul trece o
dată prin toate fazele. Rezultatele din acest paragraf obținute pe geamănul calibrat s-au retras pe 2.11 (etapa 12,
§ 6.5).

**Etapa 9 – cel mai bun câștigă (28.10).** Rezultatul grilei a schimbat întrebarea proiectului. Autorul a hotărât ca
fluidizarea să se construiască pe cazuri de trafic din date reale: trafic lejer, mediu sau intens. Fiecare caz
primește cea mai bună strategie, fie ea plan fix sau agent AI, în locul unui singur agent impus dinainte (§ 1).
Înainte de testul pe ziua de 28.10 au fost fixate trei lucruri: regula „cel mai bun câștigă”, împărțirea traficului
în cazuri după debitul măsurat de cameră și variantele de program din geamănul care rulează în timp real (§ 9.9).

**Etapa 10 – testul final (noaptea de 28 spre 29.10).** Lanțul de prelucrare al testului a rulat singur, între
00:15 și 02:27. El a verificat înregistrarea, a renumărat vehiculele, a construit scenariile, a rulat 840 de simulări
și a aplicat regula de decizie. Candidații erau trei: planul fix 12/14/12, programul `TOD_DEBIT`, care alege un plan
fix după debitul măsurat, și agentul E13. Toți trei au bătut programul realist. Între ei, diferențele nu au fost
semnificative statistic, adică puteau fi puse pe seama întâmplării, așa că a câștigat cel mai simplu: planul fix
12/14/12. El a trecut apoi în geamănul care rulează în timp real (§ 9.10). Câștigul venea de la pietoni, datorită
ciclului mai scurt.

Verificarea de după test a găsit o scădere bruscă a numărătorilor în noaptea zilei de test, în intervalul
03:46–04:28. Tocmai pe acest interval a căzut fereastra liniștită, adică ora aleasă pentru scenariul de trafic
liniștit. La început, cauza a fost descrisă ca o imagine înghețată. Verificarea directă, cerută de autor, a arătat
însă o încetinire a prelucrării: calculatorul analiza doar ≈1,4 cadre/s, cel mai probabil din cauza calculelor
rulate în paralel (§ 4.6). Chiar și fără ferestrele de noapte, decizia ar fi fost aceeași. Rezultatul testului s-a
retras însă pe 2.11: geamănul pe care rula avea coliziuni și teleportări în masă (etapa 12, § 6.5).

**Etapa 11 – confirmarea (joi 29.10, prelucrată în noaptea de 30.10).** Ziua de confirmare a fost înregistrată
întreagă, cu o singură oprire, de 13 minute, pentru repornirea calculatorului. Oprirea a fost pusă după fereastra de
dimineață, care are o oră fixă, și a fost scoasă explicit din alegerea ferestrelor. În aceeași zi a apărut veghea
fluxului de cadre, un program care semnalează singur o oprire, o încetinire sau o înghețare a imaginii (§ 4.6).
Microînghețările, adică opririle scurte ale imaginii, de 10–30 s, au fost explicate în noaptea de 30.10. Lanțul
confirmării a rulat singur, între 00:15 și 03:20, și a făcut 980 de simulări.

Planul 12/14/12 a fost confirmat. Față de programul realist, el a redus pierderea totală de timp: diferența este de
−7,0% (p = 7·10⁻⁸). Valoarea p arată cât de probabilă ar fi o diferență cel puțin la fel de mare dacă cele două
programe ar fi, de fapt, la fel de bune. Planul a fost mai bun în ambele comportamente ale participanților,
disciplinat și indisciplinat. De data aceasta a avut și cea mai mică pierdere totală dintre candidați; pe 28.10
câștigase prin regula simplității, la egalitate cu `TOD_DEBIT`. Geamănul care rulează în timp real a rămas pe acest
plan până pe 2.11, iar de atunci rulează planul observat (§ 9.10, § 9.11). Câștigul venea tot de la pietoni. Colectarea datelor de la cameră s-a oprit pe 30.10, la 08:30, și s-a reluat pe 1.11 (§ 9.11). Datele din noaptea și dimineața zilei de
30.10 sunt publicate, dar din ele nu s-au mai construit scenarii. Rezultatul a fost retras pe 2.11 (etapa 12).

**Etapa 12 – retragerea rezultatului și înghețul geamănului corectat (1–3.11).** La verificarea bornei M1 s-a văzut că,
seara, Lascăr Catargiu aproape dispare din numărători; numărătoarea de referință pe clipuri de seară a dus la o măsură
nouă, `cor_` (§ 4.3). Pe 2.11 s-au găsit cele două greșeli din geamăn: vehicule care se ciocneau și erau teleportate, apoi,
în prima corectură, vehicule care treceau prin pietoni. Rezultatul de −7% s-a retras, iar tot din cameră s-a măsurat
programul real al semaforului, cu un ciclu de ≈125–155 s (§ 6.5). Pe 3.11, după o numărare directă, pe felii, a ieșirilor
pe care detectorul nu le poate urmări și după o verificare adversarială a cererii, măsurile s-au înghețat la un commit
numit, înainte de a privi datele din 3.11 (§ 9.11).

**Etapa 13 – zilele noi și camera ca senzor (4–8.11).** Pe primele două zile judecate după îngheț, geamănul corectat nu a trecut poarta
pe nicio oră: pe 0 din 5 ore pe 3.11, ultima zi de antrenare, și pe 0 din 4 ore pe 4.11, ziua de validare. Cauza
principală e tot Dacia vest, unde, în orele încărcate, geamănul duce cam jumătate din traficul măsurat de cameră.
După regula scrisă dinainte, validarea a fost doar descriptivă: s-a încheiat pe 5.11, la 04:16, fără ca vreun candidat
să treacă, deci nu se propune un program nou, iar în geamăn rămâne planul observat, 72/48/3
(`docs/rezultate/cor_decizie_2026-11-04.json`, § 9.11). Asta nu arată că planul observat e cel mai bun, ci doar că
geamănul nu a putut judeca. Măsurarea programului real, care nu depinde de geamăn, a trecut în schimb toate
verificările: după criterii publicate pe 5.11, înaintea rulărilor care dau verdictele, camera a măsurat programul real
în toate cele patru zile lucrătoare, 2–5.11: ciclul are mediana zilei de ≈135–137 s, iar un ciclu de ≈91 s nu apare
(§ 6.5). Tot pe 5.11, modulul `romana.vision.fisa_senzor`, cu testele lui, a început să refacă din
jurnalele locale ale colectării cifrele senzorului, cu aceleași definiții la fiecare rulare. Fișa de la sfârșitul zilei
de 5.11 arată că, din 1.11, 09:04, colectarea a mers zi și noapte, fără nicio cădere neprevăzută, și s-a oprit doar de
două ori, anunțat (§ 4.6). Zilele de test, 5 și 6.11, și sâmbăta de 7.11, ziua de generalizare, s-au prelucrat apoi doar până
la geamăn și poartă: poarta a trecut pe câte o oră în zilele de test și pe toate cele 5 ore sâmbăta, dar pe Dacia vest,
în orele încărcate, geamănul rămâne sub cameră. Pe 8.11, regula finală a confirmat că runda s-a încheiat fără un program nou. Programul real
s-a măsurat, după aceleași criterii, și pe 6 și 7.11, deci toate cele șase zile judecate, 2–7.11, sunt măsurate (§ 6.5, § 9.11).
Pe 8.11, la 11:12–11:28, colectarea s-a oprit a treia oară, anunțat, pentru actualizările Windows, iar paznicul a găsit jurnalul
zilei întreg și a pornit-o la loc (§ 4.6).

### 12.2 Observațiile autorului și corecturile

Rândurile marcate cu O sunt observațiile autorului, iar cele marcate cu P sunt problemele tehnice găsite pe parcurs.
Ultima coloană spune ce s-a făcut în fiecare caz.

| # | Observația sau problema | Ce s-a făcut |
|---|---|---|
| O1 | Zona trecerii de pe Magheru era desenată pe marcajul de staționare interzisă din fața chioșcului | zona a fost mutată pe zebra reală; ulterior, toate zonele au fost înlocuite cu cele desenate de autor (23.10) |
| O2–O7 | Zonele erau desenate greșit: pe Magheru, prea late; pe Mendeleev, prea sus; pe Dacia vest, suprapuse; pe Catargiu, prea jos, prinzând inelul; pe Căderea Bastiliei, prea jos; pe Dacia est, deasupra intrării reale. Lipseau 5 treceri | zonele au fost redesenate pe 22.10, apoi înlocuite, pe 23.10, cu decupajele desenate de autor pe capturi ale camerei și localizate automat (§ 4.3) |
| O8 | Mișcarea din dispecerat și din SUMO era sacadată | dispeceratul primește un flux video continuu (MJPEG), iar simularea avansează în pași de 0,2 s |
| O9 | Comparația măsurată nu arăta bicicliștii și pietonii | `9_demo_comparatie.bat` afișează numărul lor și cât așteaptă |
| O10 | Trecerea de pe Căderea Bastiliei trebuie să fie deasupra ieșirii | zona trecerii a fost mutată deasupra zonei de ieșire |
| O11 | Și Mendeleev este sens unic, nu doar Căderea Bastiliei | corectat în documentație; rețeaua era corectă |
| O12 | Dacia are 2 benzi pe sens, fără parcare; doar Mendeleev și Căderea Bastiliei au parcare | concluzia greșită a fost retrasă; rețeaua era corectă |
| O13 | Numărarea ieșirilor e de încredere? | verificarea amănunțită a arătat că ieșirile îndepărtate sunt numărate în plus (§ 4.3), așa că volumele se iau doar din intrări |
| O14 | Participanții din București sunt indisciplinați | testul de robustețe cu participanți indisciplinați (§ 9.4) |
| O15 | Prea multe documente | o singură documentație, acest document, și un README scurt pentru pagina de GitHub |
| P1 | Viziunea se oprea când dispeceratul citea imaginea | imaginea se scrie atomic, adică dintr-o dată, ca să nu fie citită pe jumătate scrisă, iar citirile simultane sunt tolerate |
| P2 | Geamănul revenea pe date de rezervă la începutul fiecărui interval de 15 min | geamănul păstrează ultimele debite bune ale camerei |
| P3 | Imaginea camerei mergea 2 s și stătea 4 s, pentru că camera trimite bucăți de 6 s | un tampon de redare de 8 s: un cadru la fiecare 0,17 s, fără pauzele regulate; rămân câteva microînghețări de 10–30 s pe zi. Abia pe 27.10 s-a văzut că opririle afectaseră și numărarea din 21–22.10 (§ 4.6) |
| P4 | Fereastra camerei tăia imaginea | fereastra poate fi redimensionată |
| P5 | SUMO-GUI pornea arătând toată rețeaua | vederea pornește centrată pe piață |
| P6 | Programul din geamănul în timp real comuta după intrările camerei, iar pragurile erau exprimate în altă unitate | comutarea se face pe aceeași măsură ca în scenarii (§ 9.2) |
| O16 | Fluidizarea cere un ansamblu de planuri și agenți, pe cazuri de trafic, nu un singur agent; cel mai bun câștigă (28.10) | regula „cel mai bun câștigă”, cazurile după debit, cu pragurile 2 400 / 4 100 veh/h, și variantele noi din geamănul în timp real, toate fixate înainte de testul pe ziua de 28.10 (§ 9.9); pragurile se reverifică pe fiecare zi nouă |
| P7 | Pragurile programului din geamănul în timp real, 1 300 / 2 000 veh/h, veneau din zilele subnumărate, iar planurile fixe rulau în geamăn cu duratele rotunjite la 5 s | pragurile au fost luate din ziua de validare: 2 400 / 4 100 veh/h; planurile fixe sunt urmărite secundă cu secundă (§ 9.9) |
| O17 | Plăcuțele de înmatriculare ale tuturor vehiculelor să fie estompate, pentru o imagine uniformă; trecerea de pe Mendeleev stătea peste locul taxiurilor; zonele trecerii de pe Dacia est nu erau legate între ele (28.10) | plăcuțele au fost estompate la toate vehiculele; trecerea de pe Mendeleev a fost mutată pe zebra marcată în OSM; zona de peste intrarea Dacia est a fost prelungită, după traiectoriile pietonilor, până la cea de peste ieșire; numărătorile se refac din jurnal, fără o colectare nouă (§ 4.4) |
| O18 | Era chiar o imagine înghețată pe 28.10, 03:40–04:30, sau doar același cadru fără vehicule? De ce aflu abia a doua zi? (29.10) | doi verificatori AI independenți au cercetat direct pozițiile vehiculelor, traversările și rata de cadre: imaginea era vie, dar calculatorul prelucrase de 4–5 ori mai puține cadre. Descrierea a fost corectată în § 4.6 și § 9.10, iar `calitate` caută acum rata de cadre. Calculele grele rulează la prioritate scăzută cât timp camera colectează, iar anomaliile îi sunt spuse autorului imediat, cu gradul de certitudine |
| P8 | Geamănul calibrat din 27.10 trecea traficul prin coliziuni și teleportări: intervalul `tau` = 0,8 s era sub pasul de simulare de 1 s, iar avertismentele erau oprite (2.11) | în geamănul corectat, `tau` e din nou 1,0 s; avertismentele rămân oprite, dar ciocnirile, și cele din intersecții, se numără la fiecare rulare; rezultatele obținute pe geamănul calibrat, inclusiv −7%, s-au retras pe 2.11 (§ 6.5) |
| P9 | Prima corectură potrivea debitele cu camera lăsând vehiculele să treacă prin pietoni (2.11) | parametrul care o făcea s-a scos; geamănul corectat se compară cu camera pe același ceas: pe unele măsuri se apropie de ea, pe altele nu (§ 6.5) |
| P10 | În orele încărcate, geamănul corectat duce pe Dacia vest cam jumătate din traficul măsurat de cameră (3–4.11) | cauza a fost căutată pe 4.11, doar citind fișiere și cu probe separate; reparațiile țin de o rundă nouă, după M3, iar runda de acum s-a încheiat fără un program nou (§ 9.11) |

### 12.3 Bornele

Bornele sunt pașii mari ai lucrului, marcați pe GitHub prin commit-urile „Borna N: …”. Numerotarea lor nu coincide
cu cea a etapelor din § 12.1.

| Bornă | Data | Ce cuprinde |
|---|---|---|
| Ciornă | 18.10.2026 | ciorna făcută cu modulul AI Google: un scenariu `osmWebWizard` cu trafic aleatoriu, un script YOLOv8 cu 3 linii de numărare și un agent PPO cu 2000 de pași de antrenare |
| B0 | 20.10.2026 | verificarea amănunțită a ciornei: erori de sintaxă, funcția `hash()` nedeterministă, adică cu alte valori la fiecare rulare, lipsa galbenului între faze, scenariul în blocaj; restructurarea proiectului |
| B1 | 20.10.2026 | rețeaua SUMO, generată reproductibil din OSM, cu semafoarele identificate după poziția lor geografică |
| B2 | 20.10.2026 | viziunea: fluxul HLS, detecția cu YOLO11 și urmărirea cu ByteTrack, zonele, matricea O–D, adică de unde vin și încotro merg vehiculele |
| B3 | 20.10.2026 | estimarea matricei O–D prin metoda Furness, alegerea rutelor cu routeSampler, scenariile |
| B4 | 20–21.10.2026 | mediul de învățare prin întărire (RL), agenții PPO pentru piață și pentru coridor, strategiile Webster, actuated și Max-Pressure, evaluarea |
| B5 | 20.10.2026 | geamănul digital în timp real, dispeceratul web, mesajele MQTT, scripturile pentru Windows |
| B6 | 20–21.10.2026 | documentația |
| B7 | 21–22.10.2026 | viziunea pe lumină de zi, OpenVINO, jurnalul de traiectorii și renumărarea, colectarea de date în intervalul 21.10, 11:45 – 22.10, 11:00, cu urmărire sacadată (§ 4.6) |
| B8 | 21.10.2026 | replica fidelă a rețelei, toți participanții, inclusiv pietonii și bicicliștii, strategiile de referință corectate |
| B9 | 21–30.10.2026 | scenariile din date reale, agenții pe date reale, verificarea în timp real, zonele desenate de autor, renumărarea, specialiștii și programul pe tipuri de trafic, evaluarea statistică, ziua de weekend, cererea calculată din intrări, testul de robustețe, licențele și curățarea istoricului, zonele refăcute pe numărătoarea de referință și cererea calibrată, calitatea înregistrării, capacitatea geamănului, testul pe ziua de luni și protocolul pentru 28.10, acordul Webcam România, regula „cel mai bun câștigă”, testul final pe 28.10, câștigat de planul fix 12/14/12, veghea fluxului de cadre și confirmarea pe 29.10, prelucrată pe 30.10 (§ 4.6, § 9.10); rezultatele obținute cu capacitatea calibrată, inclusiv câștigul planului 12/14/12, s-au retras pe 2.11, fiindcă geamănul calibrat trecea traficul prin coliziuni și teleportări (§ 6.5, § 9.11) |

**Bornele cursului.** Separat de pașii de mai sus, la disciplinele *Interfețe om-calculator* și *Internet of Things*
(IOT & IOC) proiectul se prezintă în cinci borne, M1–M5. Commit-urile lucrului dintre două prezentări încep cu
„Borna M2: …”, „Borna M3: …” și așa mai departe, deci formează lista schimbărilor de la o bornă la alta. Prezentările
se află în `docs/prezentari/`.

| Bornă | Data | Prezentarea |
|---|---|---|
| M1 | 01.11.2026 | proiectul cap-coadă și demonstrația dispeceratului (`docs/prezentari/Prezentare_M1.pdf`) |
| M2 | 08.11.2026 | camera publică, ca senzor IoT: colectarea merge pe laptop din 1.11, 09:04, zi și noapte, fără nicio cădere neprevăzută, și s-a oprit doar de două ori, anunțat; fișa senzorului, cu cifrele colectării refăcute din jurnale (§ 4.6); programul real al semaforului, măsurat din cameră pe 2–5.11 după criterii publicate înaintea rulărilor care dau verdictele (§ 6.5); numărătoarea pe întuneric; dispeceratul evaluat și reparat cu evaluatori AI; geamănul corectat și retragerea rezultatului de −7%; regula fixată dinainte și validarea din 4.11, la care niciun candidat nu a trecut, deci rămâne planul observat, 72/48/3; pagina publică a sondării, cu ecranul din M1 și cel de acum, pe care o poate încerca oricine (`docs/prezentari/Prezentare_M2.pdf`) |

**Schimbările de la M1 la M2.** Lista completă este în istoricul Git, în commit-urile „Borna M2: …”. Pe scurt:

* **Dispeceratul:** evaluare cu 7 evaluatori AI, pe 15 stări, înainte și după reparații; moduri împărțite după cine decide, comenzi
  urmărite până la aplicare, date vechi marcate, alerte, legendă, ajutor, taste (§ 8). Pagina de sondare cu oameni, publică și fără
  laptop, cu versiunea M1 și cea nouă, în ordine schimbată de la o persoană la alta (§ 8, § 4.5).
* **Numărătoarea:** referință nouă pe clipuri de seară, felii timp-spațiu, separarea celor trei fluxuri de pe Lascăr Catargiu, zonă nouă,
  pietoni numărați pe persoane, factori după lumină (§ 4.3). Loturi de adnotare prin interfața de programare, cu o gardă pentru credit.
* **Programul real:** ciclul și etapele semaforului, măsurate din jurnalul public al vehiculelor. Pe 2–5.11, după criterii
  publicate înaintea rulărilor care dau verdictele, toate cele patru zile sunt măsurate: ciclul se schimbă de-a lungul zilei,
  cu mediana zilei de ≈135–137 s, iar un ciclu de ≈91 s nu apare; acestea sunt zilele citate de prezentarea bornei M2. Ziua de
  6.11, judecată pe 7.11 după aceleași criterii, e și ea măsurată, cu mediana de ≈133 s (§ 6.5).
* **Geamănul:** s-a găsit defectul coliziunilor, s-a construit geamănul corectat; o revizie separată, făcută de alți agenți Claude, a găsit că prima corectură făcea vehiculele să treacă prin pietoni; s-au găsit mai multe cauze, iar geamănul se compară acum cu camera pe același ceas, fără să fie validat; rezultatul de −7% s-a retras
  (§ 6.5, § 9.11).
* **Înghețul (3.11):** cererea finală, cu ieșirile greu de urmărit numărate direct pe felii; o verificare adversarială a cererii, a
  scenariilor și a textelor; poarta, cu rândul nou al pierderii de detecție pe întuneric; pragurile și comparația cu camera pe zilele
  de antrenare (§ 5.1, § 6.5, § 9.11).
* **Lista candidaților (3.11):** grila planurilor fixe pe zilele de antrenare, agentul E15 și lista pentru zilele noi: planurile
  60/40/3 și 45/30/3 și E15, în `config/candidati_v2.json`; o verificare adversarială a listei; lanțul de noapte rulează pe zilele
  de test doar candidații trecuți de validare (§ 6.5, § 9.11).
* **Pregătirea zilelor noi (3.11, seara):** o trecere în revistă a pașilor pentru 4–8.11, apoi o verificare adversarială a
  reparațiilor; regula pe zilele de test se rulează dintr-o singură comandă, cu fișierele și ordinea candidaților fixate în cod,
  abia după toate cele trei zile; desigilarea pe 3 procese; geamănul în timp real poate rula candidații (§ 9.11). Pe pagina
  sondării, schema rămâne pe ecran și pe laptopurile obișnuite, iar răspunsurile de pe telefon se numără separat; apoi pagina
  s-a înghețat (§ 8). README spune ce rulează azi și marchează rezultatele retrase.
* **Integritatea sondajului (3.11, seara):** prima versiune a paginii arăta răspunsurile așteptate, iar textul se putea corecta
  în formular; pagina v2 nu le mai arată, pune la final un cod de control, care arată dacă s-au schimbat răspunsurile, timpii sau
  apăsările, și marchează a doua trecere în aceeași filă; analiza citește ambele versiuni, cu regulile de numărare publice. Sarcinile
  și întrebările au rămas aceleași; o revizie adversă, din cinci unghiuri, înainte de publicare (§ 8).
* **Ziua de 3.11 (4.11, dimineața):** prima zi lucrătoare prelucrată cu măsurile înghețate; geamănul nu trece poarta pe nicio oră,
  mai ales din cauza Daciei vest, deci ziua e doar descriptivă, iar lista candidaților rămâne aceeași; numărătorile, jurnalul
  vehiculelor, scenariile și rezultatele ei sunt publice (§ 9.11).
* **Diagnoza zilei de 3.11 (4.11):** pe Dacia vest, geamănul trece vehiculele prea încet chiar după semafor, iar teleportările de
  noapte vin din programul rejucat, care noaptea ia un ciclu de aproape trei ori prea lung; probele arată unde se poate repara,
  într-o rundă nouă, după M2. Runda de acum nu se schimbă (§ 9.11).
* **Ziua de validare, 4.11 (5.11, dimineața):** ca pe 3.11, geamănul nu trece poarta pe nicio oră, tot din cauza Daciei vest și a
  teleportărilor de noapte, deci validarea e doar descriptivă: niciun candidat nu trece, zilele de test nu se deschid, iar în geamăn
  rămâne planul observat. Decizia s-a comis înainte de a privi datele zilelor de test; numărătorile, jurnalul vehiculelor,
  scenariile și rezultatele zilei sunt publice (§ 9.11).
* **Ziua de 5.11, prima zi de test (6.11, dimineața):** doar geamănul și poarta, fără strategii: poarta trece pe 1 din 5 ore, ora
  liniștită; ziua e doar descriptivă (§ 9.11).
* **Ziua de 6.11, a doua zi de test (7.11, dimineața):** doar geamănul și poarta, fără strategii: poarta trece pe 1 din 4 ore,
  seara; ziua e doar descriptivă (§ 9.11).
* **Date în siguranță:** paznicul colectării (§ 4.6); prelucrarea de noapte și regulile zilelor noi, comise înainte de a privi
  datele zilelor pe care le judecă (§ 9.11).
* **Fișa senzorului (5–6.11):** modulul `romana.vision.fisa_senzor`, cu testele lui, reface din jurnalele locale ale colectării
  cifrele senzorului: orele de funcționare, cadrele pe secundă, pauzele, opririle, reconectările, prelucrările de noapte și
  vehiculele intrate, pe clase; pietonii, doar ca totaluri pe zi. Fișa de la sfârșitul zilei de 5.11 e publicată în
  `docs/rezultate/fisa_senzor_2026-11-06_0000.json`, cu tabelul scurt în fișierul `.md` cu același nume (§ 4.6).
* **Sondarea cu oameni (3–7.11):** închisă pe 7.11, la 18:00. S-au publicat o singură dată doar rezultatele colegilor, singurul
  grup cu cel puțin trei texte numărate, în `docs/rezultate/sondare_m2.csv`. La fiecare dintre primele două sarcini, care cer
  doar citirea ecranului, au reușit 3 din 3 pe ambele variante, iar la fiecare dintre cele două în care omul preia comanda sau
  o dă înapoi, 2 din 3 (§ 8).

**Schimbările de la M2 la M3.** Prezentarea bornei M2 e publicată la commitul `9510367`; lucrul de după ea e în commit-urile
„Borna M3: …”. Pe scurt, până acum:

* **Ziua de 7.11 și regula finală (8.11):** sâmbăta de 7.11, ziua de generalizare, s-a prelucrat pe 8.11, la 03:30–03:43, doar
  până la geamăn și poartă, fără strategii: poarta trece pe 5 din 5 ore, dar pe Dacia vest, care nu e un rând al porții, geamănul
  rămâne sub cameră la vârf și la prânz. Rezultatele erau gata înaintea prezentării M2, dar nu apar în ea. Regula finală, rulată
  pe 8.11, la 07:01, răspunde că niciun candidat nu a trecut de validare, deci confirmă că runda zilelor noi s-a încheiat pe 5.11
  fără un program nou; în geamăn rămâne planul observat, 72/48/3. Numărătorile, jurnalul vehiculelor, scenariile și rezultatele
  zilei sunt publice (§ 9.11).
* **Programul real pe 7.11 (8.11):** după aceleași criterii, sâmbăta e măsurată, cu mediana zilei de 133,4 s; toate cele șase zile
  judecate, 2–7.11, sunt măsurate (§ 6.5).
* **Datele:** jurnalul de traiectorii al zilei de 7.11 e ultimul publicat; de la 8.11 se publică doar numărătorile (§ 5.4).
  Colectarea s-a oprit anunțat a treia oară pe 8.11, la 11:12–11:28, pentru actualizările Windows, iar paznicul a găsit jurnalul
  zilei întreg și a pornit-o la loc (§ 4.6).
* **Dispeceratul de la M2 (8.11):** copia lui, neschimbată, stă în `src/romana/dashboard/static/m2`; pagina sondării, capturile și
  evaluarea ecranului M2 o citesc de acolo, deci nu se mai schimbă odată cu dispeceratul (§ 8).
* **Geamănul în timp real (8.11):** rulează într-un singur exemplar: o a doua lansare iese cu codul 3, înainte să pornească SUMO
  (commitul `d866261`).
* **Comanda urmărită pas cu pas (8.11):** o funcție calculează din controler pasul schimbării de fază, adică verdele,
  degajarea pietonilor, galbenul sau roșul, și în câte secunde ajunge verdele cerut; pe geamănul corectat, cazul cel mai lung are
  60 s simulate (`src/romana/control/pasi.py`, commitul `c2384b1`). Seara, geamănul a început să publice acești pași, iar
  dispeceratul îi arată în banda de sus până la verdele cerut, cu un termen calculat din geamăn și cu urmărirea păstrată după o
  reîncărcare a paginii (commitul `0b72089`, § 8). O verificare adversarială a găsit 26 de constatări, toate reparate.
* **Veghea:** își citește contoarele de sistem fără să mai deschidă o fereastră de consolă pe ecranul laptopului (commitul
  `6b6a333`).
* **Starea senzorului (9.11):** panoul din locul imaginii ascunse arată cum merg camera, numărătorile, veghea, paznicul și
  prelucrarea de noapte, fiecare cu regula ei; adresa cu `?imagine=0` deschide pagina direct așa, iar
  `scripts\M3_demonstratie.bat` pornește doar ce lipsește din demonstrație (commitul `d0a10a9`, § 4.6, § 11.5). O verificare
  adversarială a confirmat 45 de constatări, reparate în patru runde, fiecare verificată din nou; trec 105 teste ale panoului
  și 111 ale dispeceratului.
* **Căderile sursei (9 și 10.11):** serverul de flux al camerei n-a mai dat fluxul pe 9.11, ≈19:10–19:24, și pe 10.11,
  ≈00:26–01:13; colectarea s-a reconectat singură, iar veghea, care nu repornește singură, a fost pornită din nou după 5 minute de cadre
  neîntrerupte (§ 4.6).
* **Fișa senzorului (10.11):** la o tăietură fix la miezul nopții, nu mai scrie rândul gol al zilei care abia începe (commitul
  `fee7395`). Tot atunci, fișa a început să vadă căderile sursei: le socotește din alertele vegherii, de la ultimul cadru
  până la repornirea ei, ca minute fără cadre, iar panoul le pomenește la ultima fișă (§ 4.6).
* **Istoricul de pe GitHub (9.11):** la cererea autorului, GitHub a anunțat că a șters referința `refs/pull/1/head` și
  commit-urile vechi pe care le mai ținea (§ 12.5).

### 12.4 Ce am învățat

1. **Datele bune contează mai mult decât algoritmul.** Cele mai mari schimbări de rezultat nu au venit din AI, ci din
   corecturi: întâi a zonelor de pe cameră și a felului în care se numără, apoi, pe 2.11, a geamănului (lecția 6).
2. **Un rezultat bun trebuie să supraviețuiască verificării.** Când datele au fost corectate, rezultatul agentului a
   trecut de la −4,6% la +5,2%. El a fost raportat așa cum era, iar soluția a fost căutată mai departe.
3. **AI-ul e util acolo unde e potrivit, iar „potrivit” depinde de cât de fidel e geamănul.** Pe geamănul cu
   capacitatea implicită, un singur agent nu bătea un plan fix bine reglat la vârf, dar, combinat cu planuri
   clasice, aducea un câștig semnificativ. Pe geamănul calibrat din 27.10, care părea să treacă debitul real, agentul
   reantrenat a bătut singur planul de referință, 36/28/12, în fiecare scenariu al unei zile noi, iar un plan fix cu
   ciclu scurt, 12/14/12, a ajuns la nivelul agentului (§ 9.9). Pe 2.11 s-a văzut că acel geamăn trecea traficul prin
   coliziuni și teleportări, deci aceste rezultate s-au retras (§ 6.5). Pe geamănul corectat, nicio oră din primele zile de
   după îngheț, 3 și 4.11, nu a trecut poarta, iar pe zilele de test, 5 și 6.11, a trecut doar câte una, deci geamănul nu a
   putut încă judeca între strategii (§ 9.11). Pe sâmbăta de 7.11, poarta a trecut pe toate cele 5 ore, dar pe Dacia vest,
   care nu e un rând al ei, geamănul a rămas sub cameră: o poartă trecută nu face din geamăn unul validat.
4. **Rezultatele negative sunt tot rezultate.** Coridorul, agentul universal și specialiștii nereușiți au îngustat
   drumul spre soluția bună. Toate aceste încercări sunt documentate.
5. **Ochiul omului rămâne indispensabil.** Descoperirea marcajului confundat cu o trecere, lămurirea benzii „lipsă” de
   pe Dacia și ideea de a lua volumele doar din intrări au venit toate de la autor.
6. **Un simulator care „merge” trebuie verificat ca orice altă măsurătoare.** Pe 2.11 s-a văzut că rezultatul prezentat la borna M1
   stătea pe un geamăn cu ≈15 000 de teleportări pe oră. Trei lucruri simple l-ar fi dat de gol mai devreme: avertismentele lăsate
   pornite, o socoteală de hârtie a capacității și compararea geamănului cu camera, ciclu cu ciclu. Niciun test statistic nu îl putea
   prinde: p = 4·10⁻¹⁰, pe cele 260 de perechi din 28 și 29.10, arăta doar că două strategii diferă pe același model greșit
   (§ 6.5, § 9.11).

### 12.5 Post-scriptum: curățarea istoricului depozitului (26.10.2026)

După ce depozitul a devenit public, o verificare a licențelor și a protecției datelor (§ 14.1) a găsit trei nereguli
în fișierele publicate anterior:

1. Capturi ale camerei Webcam România erau incluse în `docs/img/` și în PDF-ul documentației, deși toate drepturile
   asupra lor sunt rezervate operatorului camerei.
2. Una dintre aceste capturi arăta persoane neestompate.
3. Jurnalele de traiectorii conțineau și traiectoriile individuale ale pietonilor. Acestea sunt date pseudonimizate,
   nu anonime: o traiectorie nu conține imagini și nu spune cine este persoana, dar ar putea fi legată, în principiu,
   de alte imagini ale aceleiași camere (§ 4.5).

Măsurile luate, în ordine:

* Capturile au fost scoase din versiunea curentă, iar jurnalele publicate păstrează doar traiectoriile vehiculelor.
  Pietonii apar numai în numărătorile din `data/counts`, fără traiectorii individuale.
* Aceleași fișiere au fost eliminate din **tot istoricul** depozitului, cu `git filter-repo`: capturile, versiunile
  vechi ale PDF-ului care le conțineau și versiunile vechi ale jurnalelor de traiectorii. Restul conținutului fiecărui
  commit a rămas neschimbat: codul, textul documentației, datele de vehicule, mesajele, autorii și datele
  calendaristice. S-au schimbat doar identificatorii commit-urilor. Corespondența dintre identificatorii vechi și cei
  noi ai celor 105 commit-uri este în `docs/corespondenta_commituri.txt`, pentru ca istoricul urmărit de profesorul
  coordonator să rămână verificabil.
* PDF-ul de atunci, fără imagini ale camerei, și jurnalele curente, doar cu vehicule, au fost readăugate într-un
  commit nou. O copie a istoricului original este păstrată doar local, de autor, și nu este publicată.
* Pe 26.10.2026, autorul a cerut în scris, prin e-mail, acordul Webcam România pentru analiza fluxului și pentru
  publicarea a 1–2 capturi estompate. **Acordul a venit în scris pe 27.10.2026** (§ 14.1). Curățarea istoricului
  rămâne justificată: capturile vechi aveau persoane neestompate, iar acordul nu le acoperă. Commit-urile vechi au
  rămas o vreme accesibile pe GitHub prin referința `refs/pull/1/head`, pe care numai GitHub o putea șterge. Ea aparținea
  unei propuneri automate de actualizare a bibliotecilor de care depinde codul. La cererea trimisă de autor către
  GitHub Support pe 26.10.2026, GitHub a răspuns pe 9.11.2026 că a șters referința și commit-urile vechi; în aceeași zi s-a
  verificat că lista referințelor depozitului n-o mai are, iar commit-urile vechi nu se mai găsesc.
* Pe 28.10.2026 a fost publicat, în limitele acordului, un singur cadru estompat, verificat bucată cu bucată
  (figurile 4.1 și 4.2, § 4.5).

## 13. Asistență generativă

Regulile de integritate academică cer ca folosirea asistenților generativi să fie declarată. Un asistent generativ
este un program de inteligență artificială (AI) care scrie text și cod la cerere. Proiectul a folosit doi astfel de
asistenți:

* **până la 18.10.2026 inclusiv**, pentru ciorna păstrată în `legacy/google_ai_draft/`: modulul AI integrat de Google
  în browserul Chrome[^google-ai];
* **începând cu 20.10.2026**, pentru Bornele 0–9, adică reperele de lucru ale proiectului, și pentru lucrul la bornele
  cursului, M1, M2 și M3 (§ 12.3): Claude, asistentul AI dezvoltat de Anthropic, cu modelul Claude Opus 5.5. Claude a rulat
  prin Claude Code, în aplicația Claude pentru desktop[^claude], direct pe calculatorul autorului.

**Contribuția declarată a asistentului.** Claude a făcut cea mai mare parte a muncii de execuție:

* auditul ciornei și arhitectura sistemului;
* **aproape tot codul sursă**: viziunea artificială, estimarea cererii, rețeaua SUMO, mediul de învățare, agenții,
  strategiile de referință, evaluarea, geamănul digital, dispeceratul și testele;
* colectarea și calibrarea datelor de pe cameră, inclusiv adnotarea clipurilor numărătorii de referință, făcută de
  instanțe separate ale asistentului, care au lucrat independent una de alta (§ 4.3); din 1.11.2026, aceste instanțe rulează
  în loturi, prin interfața de programare Claude, pe un credit promoțional de 200 USD al autorului, cu aceeași regulă de
  independență;
* evaluarea dispeceratului, făcută tot de instanțe separate, cu roluri diferite, și verificată de altele (§ 8); ele sunt
  declarate peste tot ca evaluatori AI, nu ca oameni, iar testul cu oameni rămâne separat;
* numărarea răspunsurilor sondării cu oameni, din textele primite, și renumărarea lor de o altă instanță, cu un program
  scris de ea (§ 8, § 4.5);
* antrenarea și evaluarea modelelor;
* diagnosticarea erorilor;
* redactarea acestei documentații și a prezentărilor bornelor cursului, din `docs/prezentari/`;
* verificările adversariale ale geamănului, ale cererii, ale listei de candidați, ale codului dispeceratului, ale textelor
  publice și ale prezentărilor, făcute de instanțe separate ale asistentului, puse să caute greșeli; ele nu sunt verificări făcute de
  oameni și nici independente de Claude (§ 6.5, § 9.11).

Asistentul a lucrat autonom în depozitul proiectului, cu acordul explicit al autorului de a controla calculatorul.
Acordul a inclus și publicarea commit-urilor pe GitHub: până pe 3.11, prin aplicația GitHub Desktop, iar de atunci
direct din linia de comandă, cu conectarea contului aprobată de autor. Un commit este o versiune
salvată a proiectului. Fiecare commit făcut de asistent poartă în istoricul Git linia `Co-Authored-By: Claude …`.

**Contribuția autorului.** Niunin Matei-Gabriel a definit tema, cerințele și principiile proiectului: rețeaua din
simulare trebuie să fie replica fidelă a celei reale, simularea cuprinde toți participanții la trafic, cererea de
trafic se calibrează pe datele camerei, iar lucrul se organizează pe borne și se face local, pe calculatorul autorului.
Autorul a coordonat și a îndrumat munca, a luat deciziile de ansamblu, a pus la dispoziție echipamentul și
permisiunile și a verificat rezultatele. Tot de la el au venit ideile și corecturile-cheie (§ 12.2):

* zonele de pe imaginea camerei, desenate chiar de el, împreună cu observația că marcajul de staționare interzisă
  fusese confundat cu o trecere de pietoni;
* verificarea rețelei în Street View;
* auditul numărării, pornit de întrebarea „ești sigur că numeri corect?”;
* calcularea cererii doar din intrări;
* testul cu participanți indisciplinați;
* organizarea documentației într-un singur document.

Deciziile de proiectare și rezultatele experimentale au fost verificate rulând codul, dar asta nu le face corecte de la sine: rezultatul de −7% a trecut de aceste verificări și s-a retras abia pe 2.11, după ce geamănul a fost privit din nou (§ 6.5). Afirmațiile
despre lumea reală se sprijină pe sursele de mai jos.

## 14. Bibliografie și licențe

### 14.1 Licențele proiectului și drepturile de autor

O licență stabilește ce au voie alții să facă cu o lucrare, de exemplu să o copieze, să o modifice sau să o
redistribuie, și în ce condiții. Proiectul este public pe GitHub și are **mai multe licențe, pe părți**, pentru că
sursele folosite impun reguli diferite. Programul care folosește biblioteca de viziune Ultralytics se distribuie numai
sub GNU AGPL v3[^ultralytics-licenta]. Datele OpenStreetMap cer ca orice bază de date derivată din ele să rămână sub
ODbL 1.0[^osm]. Imaginile camerei nu pot primi deloc o licență din partea proiectului, pentru că drepturile asupra
lor nu aparțin autorului[^webcam-termeni]. Regula de bază: drepturile autorilor surselor au întâietate, iar acolo
unde o licență este ambiguă, s-a ales varianta sigură.

Pe scurt, cele trei licențe principale ale proiectului prevăd următoarele:

* **GNU AGPL v3**, pentru cod: oricine poate folosi, modifica și redistribui programul, inclusiv în scop comercial,
  cu condiția ca orice versiune distribuită, precum și orice versiune modificată oferită altora prin rețea, să rămână
  sub aceeași licență, iar codul ei sursă să fie pus la dispoziția celor care o primesc sau o folosesc;
* **ODbL 1.0**, pentru bazele de date: datele pot fi folosite, redistribuite și adaptate liber, cu indicarea sursei,
  iar o bază de date derivată, folosită public, trebuie să rămână sub aceeași licență;
* **CC BY 4.0**, pentru documentație, rezultate și figurile proprii: acestea pot fi copiate, adaptate și
  redistribuite, inclusiv în scop comercial, cu condiția menționării autorului.

| Partea proiectului | Unde se află | Licența | Motivul |
|---|---|---|---|
| Codul sursă, scripturile, testele, configurările | `src/` (fără fonturile de mai jos), `scripts/`, `tests/`, `config/`, `requirements.txt`; codul ciornei din `legacy/` | GNU AGPL v3 sau ulterioară (`AGPL-3.0-or-later`)[^agpl] | obligatorie pentru modulul de viziune, care folosește Ultralytics YOLO11, aflat sub AGPL-3.0; extinsă la tot codul, ca variantă sigură, conform cerinței Ultralytics ca întregul proiect să fie publicat sub această licență |
| Modelele antrenate | `models/` | AGPL-3.0-or-later | alegerea autorului: aceeași licență ca a codului care le încarcă; poartă atribuirea OSM, adică mențiunea sursei OpenStreetMap, pentru că au fost antrenate pe rețeaua derivată[^osmf-atribuire] |
| Extrasul OSM, rețeaua, cererea, scenariile | `data/osm/`, `sumo/`, `legacy/google_ai_draft/osm*` | ODbL 1.0 | impusă de OpenStreetMap: sunt baze de date derivate, care trebuie să păstreze aceeași licență |
| Fișierele ciornei generate de osmWebWizard | `legacy/google_ai_draft/build.bat`, `run.bat`, `output.add.xml` | CC0 1.0 | generate automat de `osmWebWizard.py` (Eclipse SUMO 1.28.0): nu se revendică drepturi asupra lor; în măsura în care ar exista, autorul renunță la ele |
| Numărătorile și traiectoriile | `data/counts/`, `data/counts_cor/`, `data/trajectories/`; traiectoriile vehiculelor din clipurile numărătorii de referință (`docs/rezultate/referinta/clip*/traiectorii/`) | ODbL 1.0, în măsura în care asupra lor există drepturi | alegerea autorului: aceeași licență ca a cererii care încorporează numărătorile; faptele în sine nu sunt protejate |
| Documentația, rezultatele, figurile proprii | `docs/` (fără pagina sondării, din rândul următor, fără traiectoriile de mai sus și fără imaginile camerei din `docs/imagini/` și din PDF-uri), `README.md`, `NOTICE` | CC BY 4.0[^ccby] | alegerea autorului; nicio sursă nu impune alt regim |
| Pagina publică a sondării | `docs/sondare/` și `docs/.nojekyll`, fără fonturile `.woff2` din rândul următor | AGPL-3.0-or-later | e cod, construit din dispecerat și pus în `docs/` doar ca să-l servească GitHub Pages |
| Fonturile Barlow și Barlow Semi Condensed | fișierele `.woff2` din `src/romana/dashboard/static/fonturi/` și din `docs/sondare/fonturi/` | SIL OFL 1.1[^barlow] | impusă de autorii fonturilor |

Textele integrale ale licențelor se află în `LICENSE` (AGPL), `LICENSES/ODbL-1.0.txt`, `LICENSES/CC-BY-4.0.txt`,
`LICENSES/CC0-1.0.txt` și `LICENSES/OFL-1.1.txt`. Atribuirile cerute pentru materialele terților și harta detaliată „cale → licență”, care dă
licența fiecărui fișier sau director, se află în fișierele `NOTICE` și `REUSE.toml`. Directoarele `data/`, `sumo/` și
`models/` conțin fiecare câte o notă de licență, `LICENTA.txt`.

**De ce AGPL.** Ultralytics distribuie sub AGPL-3.0 atât biblioteca, cât și ponderile preantrenate ale YOLO11,
adică parametrii deja învățați ai rețelei neuronale care detectează obiectele. Tot sub AGPL-3.0 se află și
programul de urmărire ByteTrack folosit, pentru că este implementarea din Ultralytics[^yolo11][^bytetrack]. Prin
urmare, programul combinat cu Ultralytics, adică modulul de viziune, se distribuie numai sub AGPL-3.0. Celelalte
module – cererea, rețeaua, controlul și dispeceratul – nu încarcă biblioteca Ultralytics și comunică cu modulul de
viziune doar prin fișiere. Ele ar putea purta și o altă licență, compatibilă, cum sunt MIT, Apache-2.0 sau GPL-3.0.
S-a ales totuși AGPL-3.0-or-later pentru tot codul. Alegerea respectă poziția Ultralytics, care cere
„Open-source your entire project under AGPL-3.0”, adică publicarea întregului proiect ca sursă deschisă, sub
AGPL-3.0. În plus, este coerentă și cea mai sigură. AGPL nu permite restricții suplimentare, cum ar fi
„doar uz academic” sau „necomercial” (AGPL § 7 și § 10).

**Pentru specialiști.** Ultralytics își declară licența în trei feluri: „AGPL-3.0” în fișierul de licență,
„AGPLv3 or later” în metadatele pachetului și „AGPL-3.0-only” în `ultralytics-platform`, un pachet de care depinde.
Formula „AGPL-3.0-or-later”, adică versiunea 3 a licenței sau orice versiune ulterioară, rămâne compatibilă cu toate
aceste variante și este cea recomandată de textul licenței. Celelalte componente sunt și ele compatibile:

* Eclipse SUMO: codul proiectului este un client TraCI/`libsumo`. TraCI este interfața prin care un program extern
  comandă simularea, iar `libsumo` oferă aceeași interfață sub formă de bibliotecă. Licența SUMO exclude astfel de
  programe din lucrările derivate, adică din cele care ar trebui să preia licența SUMO. La distribuirea unui pachet
  combinat cu SUMO se folosește opțiunea GPL-2.0-or-later a licenței sale duble[^sumo];
* clientul MQTT Paho, sub opțiunea EDL-1.0, al cărei text este cel al licenței BSD-3-Clause[^mosquitto];
* OpenCV și OpenVINO, sub Apache-2.0[^opencv][^openvino];
* PyTorch, sub o combinație de licențe permisive, adică licențe care permit reutilizarea cu condiții minime, cum ar
  fi păstrarea mențiunii de autor: BSD-3-Clause, Apache-2.0, BSD-2-Clause, BSL-1.0 și MIT[^pytorch];
* NumPy, pandas, SciPy, Flask și Python-Markdown, sub licențe de tip BSD; Matplotlib, sub licența Matplotlib,
  de tip PSF[^pydata][^flask][^markdown-py];
* Stable-Baselines3 și Gymnasium, sub MIT[^sb3];
* FFmpeg, sub LGPL[^ffmpeg];
* Python, sub licența PSF[^python].

Dispeceratul, adică interfața web a operatorului, rulează doar pe calculatorul local, dar o copie a lui, cu date simulate,
e publică în pagina sondării, servită de GitHub Pages (§ 8). Subsolul dispeceratului și cel al ecranelor din sondare au o legătură
către codul sursă. Astfel, cerința din AGPL § 13, de a oferi sursa unei versiuni modificate folosite prin rețea, este
îndeplinită pentru pagina publică și ar rămâne îndeplinită și dacă dispeceratul ar fi făcut vreodată accesibil din
rețea. AGPL permite și folosirea comercială, cu condiția publicării sursei. O integrare cu sursă închisă, adică fără publicarea codului,
ar cere două lucruri: pentru detector, licența Enterprise a Ultralytics sau înlocuirea lui; pentru codul proiectului,
o licență separată de la autor. Ar fi cazul, de exemplu, al integrării într-un automat de semaforizare comercial sau
în BTMS, sistemul de management al traficului din București.

**Datele OpenStreetMap.** Extrasul din `data/osm/` și tot ce derivă din el – rețeaua, rutele și scenariile – se
distribuie numai sub ODbL 1.0. Notificarea cerută de ODbL § 4.2, adică mențiunea sursei și a licenței, apare:

* în directoare, în fișierele `sumo/LICENTA.txt` și `data/LICENTA.txt`;
* în `NOTICE` și în această documentație;
* ca comentariu XML în fișierele generate de `build_demand.py` începând cu 26.10; în rețeaua geamănului corectat,
  `sumo/net/romana_v2.net.xml`, generată de `retea_v2.py`, comentariul există deja, iar în `romana.net.xml` va apărea la
  următoarea regenerare cu `build_network.py`.

Rezultatele, graficele și modelele sunt *lucrări produse*, adică lucrări obținute din folosirea datelor, care nu sunt
ele însele baze de date. Ele poartă notificarea cerută de ODbL § 4.3 prin această documentație, prin `NOTICE`, prin
`models/LICENTA.txt` și, pentru tabelele generate, în capul fișierelor `docs/rezultate/**/rezultate.md`. Textul
notificării este:

„Conține informații din OpenStreetMap (https://www.openstreetmap.org), puse la dispoziție aici sub Open Database
License (ODbL) 1.0 – https://opendatacommons.org/licenses/odbl/1-0/. © OpenStreetMap contributors –
https://www.openstreetmap.org/copyright”.

ODbL § 4.6 cere să fie oferită și baza de date derivată sau metoda prin care a fost obținută. Cerința este
îndeplinită prin `sumo/net/`, `sumo/demand/`, `sumo/scenarios/`, `src/romana/network/build_network.py`,
`config/network.json` și, pentru rețeaua geamănului corectat, `src/romana/network/retea_v2.py` și
`config/retea_v2.json`. Istoricul git al depozitului https://github.com/NiuninMatei/Semaforizare_Piata_Romana
păstrează versiunile exacte ale scenariilor folosite pentru fiecare model sau rezultat, iar scenariile de antrenare
sunt listate în `models/*.json`. Rețeaua nu a fost modificată cu informații din surse Google: Street View a servit
doar la verificarea vizuală (§ 10).

**Imaginile camerei.** Sursa lor este fluxul public Webcam România (webcamromania.ro)[^webcam]. Drepturile asupra
imaginilor aparțin operatorului camerei, care nu este identificat public; Webcam România declară că nu deține
drepturi asupra fluxurilor[^webcam-termeni].

Proiectul analizează fluxul în memorie, iar pentru previzualizarea locală suprascrie continuu un singur cadru
estompat. Capturile și scurtele clipuri folosite la desenarea zonelor și la numărătoarea de referință nu sunt acte provizorii, adică nu sunt copii
trecătoare, făcute automat în cursul unui proces tehnic. Sunt copii păstrate local, numai pe durata calibrării,
nepublicate, care se șterg după încheierea ei. Copiile celor citite de asistentul Claude au rămas în jurnalele
locale ale sesiunilor lui și se șterg odată cu jurnalul local complet (§ 4.5).

Temeiul principal invocat este excepția pentru actele provizorii de reproducere, prevăzută de art. 35 alin. (3) din
Legea nr. 8/1996[^legea8]. Prevederea transpune art. 5 alin. (1) din Directiva 2001/29/CE[^infosoc] și se aplică,
prin art. 120, și drepturilor conexe, adică drepturilor înrudite cu dreptul de autor, cum sunt cele ale
producătorilor de înregistrări audiovizuale. Numărătorile rezultate sunt simple fapte, potrivit art. 9 lit. f) din
aceeași lege.

În subsidiar, adică pentru cazul în care acest temei nu ar fi acceptat, s-ar putea invoca excepțiile pentru
extragerea de text și de date, care permit analiza automată a conținutului digital pentru obținerea de informații.
Ele sunt prevăzute de art. 36^1 și 36^2, care transpun art. 3–4 din Directiva (UE) 2019/790[^dsm]. Există însă două
rezerve: art. 36^1 privește doar organizațiile de cercetare și instituțiile de patrimoniu cultural, iar art. 36^2 nu
se aplică dacă titularul și-a rezervat drepturile prin mijloace care pot fi citite automat. Fișierul `robots.txt` al
unui site le arată programelor automate ce nu au voie să acceseze. Cel al site-ului webcamromania.ro exclude listele
de redare HLS (`.m3u8`), adică fișierele care indică bucățile fluxului video. Prin urmare, această excepție este
incertă.

Din acest motiv, pe 26.10.2026, autorul a cerut în scris, prin e-mail, acordul Webcam România. A rugat-o totodată
ca, dacă drepturile aparțin operatorului camerei, să indice titularul sau să-i transmită acestuia cererea.
**Acordul a venit în scris pe 27.10.2026**, pentru:

- (a) analiza automată a fluxului în scop academic și necomercial, cu indicarea sursei („Webcam România –
  https://webcamromania.ro”);
- (b) publicarea a 1–2 capturi ale camerei, cu persoanele estompate.

Răspunsul nu a indicat alt titular, așa că acordul este al singurei părți identificabile. Dacă operatorul camerei se
face cunoscut și obiectează, capturile se retrag și analiza fluxului se oprește. Autorul păstrează corespondența.
Utilizarea rămâne în limitele acordului: academică, necomercială și cu sursa indicată.

Depozitul și PDF-ul conțin două imagini dintr-un singur cadru al camerei, din 28.10.2026, ora 09:30:
`docs/imagini/camera_piata_romana.jpg` și `docs/imagini/camera_zone.jpg`, adică figurile 4.1 și 4.2. Persoanele,
plăcuțele de înmatriculare ale tuturor vehiculelor și textul publicitar suprapus de cameră sunt estompate (§ 4.5),
iar sursa este scrisă pe imagine. Prezentarea bornei M1 (`docs/prezentari/Prezentare_M1.pdf`) folosește același cadru,
inclusiv în captura dispeceratului, cu aceeași estompare și cu sursa indicată. Proiectul nu acordă nicio licență asupra acestor imagini, iar ele nu intră sub
CC BY 4.0; în `REUSE.toml` sunt marcate cu adnotarea `LicenseRef-Toate-drepturile-rezervate`. Capturile publicate
anterior, cu persoane neestompate, au fost eliminate din tot istoricul depozitului (§ 12.5).

**Datele de trafic.** Numărătorile și traiectoriile sunt informații factuale, iar, potrivit art. 9 lit. f) din
Legea nr. 8/1996, „simplele fapte și date” nu sunt protejate. Licența ODbL se acordă asupra lor în măsura în care
asupra bazei de date există drepturi de autor sau drepturi *sui generis*, adică drepturile speciale pe care legea le
dă celui care a investit substanțial în alcătuirea unei baze de date. Datele nu reproduc nicio imagine. Traiectoriile
nu conțin imagini și nici identificatori: sunt date pseudonimizate, care nu pot fi atribuite unei persoane anume fără
informații suplimentare. Traiectoriile individuale ale pietonilor nu sunt publicate, ci doar numărătorile agregate
(§ 4.5, § 12.5). Rezultatul produs de un program sub o licență GNU nu intră sub licența programului decât dacă
reproduce părți din el[^gpl-faq]. Prin urmare, datele nu devin AGPL din cauza YOLO11.

**Conținutul realizat cu asistenți generativi** (cap. 13). Prin termenii săi de utilizare, Anthropic îi cedează
utilizatorului toate drepturile sale asupra rezultatelor, dacă astfel de drepturi există[^claude]. Pentru ciornă,
termenii Google precizează că Google nu revendică proprietatea asupra conținutului generat[^google-ai]. Licențele de
mai sus se aplică în măsura în care asupra acestui conținut există drepturi de autor.

**Ce nu acoperă licențele proiectului:**

* citatele din surse terțe, preluate cu indicarea sursei, potrivit art. 35 din Legea nr. 8/1996. Aceste surse sunt
  presa, pagina și termenii Webcam România, termenii Ultralytics, Anthropic și Google, precum și ghidurile Fundației
  OpenStreetMap (OSMF);
* imaginile camerei, ale căror drepturi aparțin operatorului camerei: cele două din `docs/imagini/`, adică
  figurile 4.1 și 4.2, reproducerile aceluiași cadru din `docs/prezentari/` și capturile vechi, eliminate din istoric și, cum a anunțat GitHub pe 9.11.2026, șterse
  și de pe GitHub (§ 12.5);
* mărcile comerciale menționate;
* subseturile de fonturi Microsoft încorporate în PDF-uri, a căror licență permite încorporarea;
* bibliotecile terțe, care rămân sub licențele lor (§ 14.2) și nu sunt incluse în depozit.

### 14.2 Resursele folosite și licențele lor

Fiecare sursă este citată în text printr-o notă de subsol. Tabelul de mai jos arată licența sau termenii de utilizare
ai fiecărei resurse folosite efectiv în proiect.

| Resursa folosită | Licența sau termenii de utilizare |
|---|---|
| Claude (Anthropic), modelul Claude Opus 5.5, prin Claude Code – asistentul AI care a scris cea mai mare parte a codului și a documentației (§ 13) | Termenii Anthropic: drepturile Anthropic asupra rezultatelor, dacă există, sunt cedate utilizatorului; folosirea AI trebuie atribuită, adică menționată explicit (§ 13)[^claude] |
| Modulul AI Google din Chrome – ciorna inițială (`legacy/`) | Termenii Google: Google nu revendică proprietatea asupra conținutului generat[^google-ai] |
| Datele OpenStreetMap: extrasul, rețeaua rutieră, rutele | ODbL 1.0 – „© OpenStreetMap contributors”; bazele derivate rămân tot sub ODbL 1.0[^osm][^osmf-atribuire] |
| Eclipse SUMO 1.28.0: simulatorul, `sumolib`, `traci`, `libsumo`, `routeSampler` | EPL-2.0 OR GPL-2.0-or-later; codul proiectului este un client TraCI, iar pentru un pachet combinat se folosește opțiunea GPL-2.0-or-later[^sumo] |
| Ultralytics YOLO11 (`ultralytics` 8.4.183, cu dependența `ultralytics-platform` 0.1.90) și ponderile YOLO11 preantrenate | AGPL-3.0 pentru cod și ponderi (`ultralytics-platform`: AGPL-3.0-only) sau licența Enterprise[^yolo11][^ultralytics-licenta] |
| Setul de imagini COCO, pe care au fost antrenate ponderile | adnotările © COCO Consortium, CC BY 4.0; imaginile, conform Flickr Terms of Use; setul nu este redistribuit[^coco] |
| ByteTrack: implementarea din Ultralytics (folosită) / codul original (nefolosit direct) | AGPL-3.0 / MIT[^bytetrack] |
| Stable-Baselines3, Gymnasium | MIT[^sb3] |
| sumo-rl – model de proiectare pentru mediul de învățare prin întărire (instalat, dar neimportat în cod) | MIT[^sumorl] |
| PyTorch | BSD-3-Clause, cu componente Apache-2.0, BSD-2-Clause, BSL-1.0 și MIT[^pytorch] |
| NumPy, pandas, SciPy, Matplotlib | BSD-3-Clause; Matplotlib License (de tip PSF)[^pydata] |
| OpenCV | Apache-2.0[^opencv] |
| Intel OpenVINO, pentru rularea detectorului YOLO pe placa grafică Intel | Apache-2.0[^openvino] |
| FFmpeg, folosit prin OpenCV | LGPL-2.1-or-later[^ffmpeg] |
| Flask | BSD-3-Clause[^flask] |
| Python-Markdown, pentru exportul PDF | BSD-3-Clause[^markdown-py] |
| psutil, pentru veghea fluxului de cadre, paznicul colectării și prioritatea proceselor | BSD-3-Clause[^psutil] |
| Biblioteca `anthropic`, pentru loturile de adnotare și de evaluare, instalată separat și neinclusă în depozit | Apache-2.0[^anthropic-sdk] |
| Eclipse Paho MQTT (client) / Mosquitto (broker, adică server de mesaje, opțional și neinclus) | EPL-2.0 OR EDL-1.0 (BSD-3-Clause); proiectul folosește opțiunea EDL-1.0[^mosquitto] |
| Fluxul video al camerei Piața Romană (sursa: Webcam România) | drepturile asupra imaginilor aparțin operatorului camerei, neidentificat public; Webcam România declară că nu deține drepturi asupra fluxurilor. Fluxul este analizat în memorie, în scop academic și necomercial, cu acordul scris al Webcam România din 27.10.2026, care permite și publicarea a 1–2 capturi cu persoanele estompate. Pentru capturile publicate s-a folosit un singur cadru, din 28.10.2026 (figurile 4.1 și 4.2)[^webcam][^webcam-termeni] |
| Google Street View, doar pentru verificarea vizuală a rețelei (§ 10) | Termenii suplimentari Google Maps / Google Earth; nicio informație preluată, nicio captură publicată[^streetview] |
| Fonturile Barlow și Barlow Semi Condensed, de pe Google Fonts, folosite în dispecerat | SIL Open Font License 1.1; incluse în depozit, ca paginile să nu ceară nimic din afară[^barlow] |
| Python 3.12 | PSF-2.0[^python] |
| Licențele proiectului (§ 14.1) | GNU AGPL v3[^agpl]; ODbL 1.0[^osm]; CC BY 4.0[^ccby]; CC0 1.0 (trei fișiere generate ale ciornei) |

[^wiki-romana]: Wikipedia, „Piața Romană” și „Piața Romană metro station”, https://en.wikipedia.org/wiki/Pia%C8%9Ba_Roman%C4%83, accesat 20.10.2026. Licență CC BY-SA 4.0. Folosită doar pentru fapte; nu s-a preluat text.
[^webcam]: Webcam România, „Webcam Piața Romană București – Live din Centrul Capitalei”, https://webcamromania.ro/webcam-orase/webcam-piata-romana-bucuresti/, accesat 20.10.2026. Flux: https://s5.webcamromania.ro/piataromanab/tracks-v1/mono.m3u8. Pagina: © 2016–2026 WebcamRomania.ro. Fluxul: drepturile asupra imaginilor aparțin operatorului camerei, neidentificat public; Webcam România declară că nu deține drepturi asupra fluxurilor („Termeni și condiții”, secțiunile 2 și 4). Fluxul este analizat doar în memorie; proiectul publică doar imagini estompate dintr-un singur cadru: figurile 4.1 și 4.2 și reproducerile lor din prezentarea bornei M1, cu acordul scris al Webcam România din 27.10.2026 (§ 14.1).
[^tomtom]: TomTom, „Bucharest traffic report – TomTom Traffic Index 2025”, https://www.tomtom.com/traffic-index/city/bucharest/, publicat în ianuarie 2026. © TomTom, citare cu atribuire.
[^rilsa]: FGSV, *Richtlinien für Lichtsignalanlagen (RiLSA)*, ediția 2015: viteza standard de degajare a pietonilor 1,2 m/s, cu abateri între 1,0 m/s (doar în cazuri speciale) și 1,5 m/s. Valorile sunt citate după un document al orașului München, https://muenchen-transparent.de/dokumente/6708749/datei, consultat pe 29.10.2026. Ghidul însuși nu a fost consultat: este o publicație FGSV, cu drepturi rezervate.
[^trl-viteza]: TRL, *PPR700 – Review of pedestrian walking speeds*: în Regatul Unit, timpul de degajare se calculează la viteza minimă de mers de 1,2 m/s, iar trecerile cu mulți pietoni lenți folosesc o viteză mai mică; Singapore și Toronto folosesc 1,0 m/s. https://www.trl.co.uk/uploads/trl/documents/PPR700%20-%20Review%20of%20pedestrian%20walking%20speeds.pdf, consultat pe 29.10.2026. Drepturi rezervate (TRL).
[^eea-ocupare]: European Environment Agency, gradul de ocupare al autoturismelor (indicatorul TERM 029, întrerupt; naveta la orele de vârf: ≈1,1–1,2 persoane pe autoturism), https://www.eea.europa.eu/en/analysis/publications/envissueno12/page029.html, consultat pe 28.10.2026. Conținut EEA, reutilizare cu atribuire.
[^stb-ocupare]: HotNews, „Care sunt cele mai aglomerate linii de transport public din București. Singura linie pe care se știe exact numărul de călători”, https://hotnews.ro/care-sunt-cele-mai-aglomerate-linii-de-transport-public-din-bucuresti-singura-linie-pe-care-se-stie-exact-numarul-de-calatori-49929; Informat.ro, despre gradul de încărcare afișat în Google Maps din numărătoarele vehiculelor noi, https://informat.ro/en/current-affairs/nicusor-dan-announces-that-the-google-maps-application-can-be-used-to-see-the-degree-of-load-of-means-of-transportation-in-bucharest-24094; consultate pe 28.10.2026, citate doar ca sursă a informației.
[^pmb-tomtom]: Primăria Municipiului București, „București, pe locul 20 în lume din punct de vedere al traficului…”, https://www.bucuresti.ro/articole/bucuresti-pe-locul-20-in-lume-din-punct-de-vedere-al-traficului-care-este-viteza-medie-cu-care-se-circula-in-oras-1751, 2026.
[^btms-267]: Business24, „București: extinderea sistemului de trafic – rețea centralizată de intersecții”, https://business24.ro/trafic-inteligent/bucuresti-extindere-sistem-trafic-retea-centralizata-intersectii-1670366, 6.10.2026; B365, https://b365.ro/pmb-anunta-extinderea-sistemului-de-semaforizare-inteligenta-dar-nu-se-spune-si-ce-presupune-aminteste-ca-e-implementat-deja-in-267-de-intersectii-din-bucuresti-622733/. Drepturi rezervate (presă).
[^buletin-btms]: Buletin de București, „Sistemul de semaforizare inteligentă din București se extinde: patru noi intersecții integrate în BTMS”, https://buletin.de/bucuresti/sistemul-de-semaforizare-inteligenta-din-bucuresti-se-extinde-patru-noi-intersectii-integrate-in-btms-anul-acesta/, 2026; HCL PMB nr. 187/2026.
[^digi24-ai]: Citatul aparține Primăriei Municipiului București (anunț instituțional, fără vorbitor numit), preluat de Digi24, „Peste 90 de intersecții și treceri de pietoni din București vor avea semaforizare inteligentă. Anunțul făcut de Primăria Capitalei”, 14.05.2026, editor A.P., https://www.digi24.ro/stiri/actualitate/social/peste-90-de-intersectii-si-treceri-de-pietoni-din-bucuresti-vor-avea-semaforizare-inteligenta-anuntul-facut-de-primaria-capitalei-3770033, accesat 26.10.2026; vezi și Digi24, „Bucureștiul face primul pas către semaforizarea inteligentă: PMB modernizează aproape 100 de intersecții cu ajutorul AI”, https://www.digi24.ro/digieconomic/consumer/bucurestiul-face-primul-pas-catre-semaforizarea-inteligenta-pmb-modernizeaza-aproape-100-de-intersectii-cu-ajutorul-ai-101141, 2026; declarație PMB citată și de Stiripesurse/Capital.ro, 14.05.2026. Drepturi rezervate (presă).
[^economedia]: M. Podaru, „Explicații pentru ambuteiajele din București…” (despre sistemul „undă verde”, început ca proiect pilot în 2007 pe axa Unirii – Universitate – Romană – Victoriei, „după implementare fluența circulației crescând cu 30%”), Economedia, 10.05.2022, https://economedia.ro/explicatii-pentru-ambuteiajele-din-bucuresti-doar-260-de-intersectii-semaforizate-din-cele-440-sunt-si-integrate-in-sistemul-inteligent-cu-unda-verde-modernizarea-semafoarelor-ar-costa-50-de-mil.html, accesat 26.10.2026. Drepturi rezervate (presă).
[^adevarul-incendiu]: Digi24, „Incendiu în Piața Romană: semafoare scoase din funcțiune într-una dintre cele mai aglomerate intersecții din Capitală”, 8.05.2026, editor Ș.A., https://www.digi24.ro/stiri/actualitate/incendiu-in-piata-romana-semafoare-scoase-din-functiune-intr-una-dintre-cele-mai-aglomerate-intersectii-din-capitala-3761469, accesat 26.10.2026 (primele informații: focul ar fi izbucnit la cablurile electrice subterane); același eveniment relatat și de Adevărul, 8.05.2026. Drepturi rezervate (presă).
[^gdpr]: Regulamentul (UE) 2016/679 (GDPR), https://eur-lex.europa.eu/eli/reg/2016/679/oj; Legea nr. 190/2018. Reutilizare EUR-Lex conform Deciziei 2011/833/UE.
[^edpb]: European Data Protection Board, *Guidelines 3/2019 on processing of personal data through video devices*, v2.0, 2020, https://edpb.europa.eu.
[^itu-y2060]: ITU-T, Recomandarea Y.2060 *Overview of the Internet of things*, 2012, https://www.itu.int/rec/T-REC-Y.2060-201206-I.
[^mqtt]: OASIS, *MQTT Version 5.0*, OASIS Standard, 7.03.2019, https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html.
[^mosquitto]: R. A. Light, „Mosquitto: server and client implementation of the MQTT protocol”, *Journal of Open Source Software* 2(13):265, 2017, doi:10.21105/joss.00265, https://mosquitto.org. Licență EPL-2.0 OR EDL-1.0. Clientul Eclipse Paho MQTT Python 2.1.0, https://github.com/eclipse-paho/paho.mqtt.python: EPL-2.0 OR EDL-1.0 (textul EDL-1.0 este BSD-3-Clause, https://www.eclipse.org/org/documents/edl-v10.php); proiectul folosește opțiunea EDL-1.0, compatibilă cu AGPL-3.0.
[^webcam-buc]: Webcam România, „Webcam Live Municipiul București”, https://webcamromania.ro/webcam-live/municipiul-bucuresti/; pagina Piața Victoriei, https://webcamromania.ro/webcam-orase/webcam-piata-victoriei-bucuresti/, accesate 21.10.2026. Paginile: © WebcamRomania.ro; fluxurile video aparțin operatorilor camerelor.
[^openvino]: Intel, *OpenVINO Toolkit* 2026.4, https://docs.openvino.ai, licență Apache-2.0; exportul din Ultralytics: https://docs.ultralytics.com/integrations/openvino/.
[^opencv]: G. Bradski, „The OpenCV Library”, *Dr. Dobb's Journal of Software Tools*, 2000; https://opencv.org/license/ (Apache-2.0 de la versiunea 4.5.0).
[^ffmpeg]: FFmpeg, https://ffmpeg.org/legal.html. Pachetele precompilate `opencv-python` includ FFmpeg sub LGPL-2.1-or-later (https://github.com/opencv/opencv-python#licensing); varianta GPL apare doar la compilarea cu componente GPL.
[^yolo11]: G. Jocher, J. Qiu, *Ultralytics YOLO11*, v11.0.0, 2024, https://github.com/ultralytics/ultralytics, https://docs.ultralytics.com/models/yolo11. Licență AGPL-3.0 sau Enterprise, pentru cod și pentru ponderile preantrenate („All Ultralytics YOLO trained models fall under the AGPL-3.0 License by default”). Versiunea folosită: `ultralytics` 8.4.183; dependența `ultralytics-platform` 0.1.90 (https://github.com/ultralytics/sdk) este declarată AGPL-3.0-only.
[^coco]: T.-Y. Lin et al., „Microsoft COCO: Common Objects in Context”, ECCV 2014, doi:10.1007/978-3-319-10602-1_48, https://cocodataset.org; termeni: https://cocodataset.org/#termsofuse. Adnotări © COCO Consortium, CC BY 4.0; imaginile aparțin autorilor lor (Flickr Terms of Use). Setul nu este redistribuit de proiect; ponderile antrenate pe el sunt ale Ultralytics, sub AGPL-3.0 (nota YOLO11).
[^bytetrack]: Y. Zhang et al., „ByteTrack: Multi-Object Tracking by Associating Every Detection Box”, ECCV 2022, LNCS 13682, pp. 1–21, doi:10.1007/978-3-031-20047-2_1. Codul original: https://github.com/FoundationVision/ByteTrack (MIT, © 2021 Yifu Zhang), nefolosit direct. Implementarea folosită: Ultralytics, `ultralytics/trackers/byte_tracker.py` și `bytetrack.yaml`, AGPL-3.0.
[^botsort]: N. Aharon, R. Orfaig, B.-Z. Bobrovsky, „BoT-SORT: Robust Associations Multi-Pedestrian Tracking”, arXiv:2206.14651, 2022.
[^ortuzar]: J. de D. Ortúzar, L. G. Willumsen, *Modelling Transport*, ed. a 4-a, Wiley, 2011, cap. 5 (metoda Furness / IPF); K. P. Furness, „Time function iteration”, *Traffic Engineering and Control* 7(7), 1965.
[^sumo-turns]: Eclipse SUMO Documentation, „Turns – routeSampler.py”, https://sumo.dlr.de/docs/Tools/Turns.html și „Routes from Observation Points”, https://sumo.dlr.de/docs/Demand/Routes_from_Observation_Points.html, accesat 20.10.2026.
[^wizard]: Wizard Media, „Măsurători trafic outdoor București”, https://www.wizard-media.ro/panouri-2013/pag/masuratori-trafic-outdoor-bucuresti/, 2011/2012 – estimare neoficială, folosită doar ca ordin de mărime.
[^osm]: OpenStreetMap Foundation, „Copyright and License”, https://www.openstreetmap.org/copyright; Open Data Commons, *Open Database License (ODbL) v1.0*, https://opendatacommons.org/licenses/odbl/1-0/ (textul în `LICENSES/ODbL-1.0.txt`). Date © OpenStreetMap contributors. Extrasul din `data/osm/` și bazele de date derivate din el (rețeaua `sumo/net/`, rutele din `sumo/demand/`, scenariile din `sumo/scenarios/`, scenariul ciornei din `legacy/`) sunt distribuite sub ODbL 1.0. Rezultatele, graficele și modelele sunt lucrări produse (ODbL § 4.3).
[^sumo]: P. A. Lopez, M. Behrisch, L. Bieker-Walz, J. Erdmann, Y.-P. Flötteröd, R. Hilbrich, L. Lücken, J. Rummel, P. Wagner, E. Wießner, „Microscopic Traffic Simulation using SUMO”, *21st IEEE ITSC*, 2018, pp. 2575–2582, doi:10.1109/ITSC.2018.8569938. Eclipse SUMO 1.28.0, doi:10.5281/zenodo.23219601, https://sumo.dlr.de, licență EPL-2.0 OR GPL-2.0-or-later (licența secundară desemnată, https://github.com/eclipse-sumo/sumo/blob/main/NOTICE.md). Același NOTICE.md exclude aplicațiile client TraCI din lucrările derivate; pentru distribuirea unui pachet combinat cu SUMO se folosește opțiunea GPL-2.0-or-later, compatibilă cu AGPL-3.0.
[^ppo]: J. Schulman, F. Wolski, P. Dhariwal, A. Radford, O. Klimov, „Proximal Policy Optimization Algorithms”, arXiv:1707.06347, 2017.
[^sb3]: A. Raffin, A. Hill, A. Gleave, A. Kanervisto, M. Ernestus, N. Dormann, „Stable-Baselines3: Reliable Reinforcement Learning Implementations”, *JMLR* 22(268):1–8, 2021, https://jmlr.org/papers/v22/20-1364.html. Cod MIT; Gymnasium (Farama Foundation), MIT.
[^dqn]: V. Mnih et al., „Human-level control through deep reinforcement learning”, *Nature* 518:529–533, 2015, doi:10.1038/nature14236.
[^intellilight]: H. Wei, G. Zheng, H. Yao, Z. Li, „IntelliLight: A Reinforcement Learning Approach for Intelligent Traffic Light Control”, KDD 2018, pp. 2496–2505, doi:10.1145/3219819.3220096.
[^presslight]: H. Wei et al., „PressLight: Learning Max Pressure Control to Coordinate Traffic Signals in Arterial Network”, KDD 2019, doi:10.1145/3292500.3330949.
[^colight]: H. Wei et al., „CoLight: Learning Network-level Cooperation for Traffic Signal Control”, CIKM 2019, pp. 1913–1922, doi:10.1145/3357384.3357902.
[^mplight]: C. Chen et al., „Toward A Thousand Lights: Decentralized Deep Reinforcement Learning for Large-Scale Traffic Signal Control”, AAAI 2020, https://ojs.aaai.org/index.php/AAAI/article/view/5744.
[^survey2019]: H. Wei, G. Zheng, V. Gayah, Z. Li, „A Survey on Traffic Signal Control Methods”, arXiv:1904.08117, 2019.
[^survey2021]: H. Wei, G. Zheng, V. Gayah, Z. Li, „Recent Advances in Reinforcement Learning for Traffic Signal Control: A Survey of Models and Evaluation”, *ACM SIGKDD Explorations* 22(2), 2021, doi:10.1145/3447556.3447565.
[^sumorl]: L. N. Alegre, *SUMO-RL*, 2019, https://github.com/LucasAlegre/sumo-rl, v1.4.5 (MIT).
[^webster]: F. V. Webster, *Traffic Signal Settings*, Road Research Technical Paper No. 39, HMSO, Londra, 1958.
[^maxpressure]: P. Varaiya, „Max pressure control of a network of signalized intersections”, *Transportation Research Part C* 36:177–195, 2013, doi:10.1016/j.trc.2013.08.014.
[^nielsen]: J. Nielsen, R. Molich, „Heuristic evaluation of user interfaces”, CHI '90, doi:10.1145/97243.97281; J. Nielsen, „Enhancing the explanatory power of usability heuristics”, CHI '94, doi:10.1145/191666.191729; https://www.nngroup.com/articles/ten-usability-heuristics/.
[^shneiderman]: B. Shneiderman, C. Plaisant, M. Cohen, S. Jacobs, N. Elmqvist, N. Diakopoulos, *Designing the User Interface*, ed. a 6-a, Pearson, 2016; https://www.cs.umd.edu/users/ben/goldenrules.html.
[^flask]: Pallets, *Flask*, https://flask.palletsprojects.com (BSD-3-Clause).
[^barlow]: J. Tribby, *Barlow* și *Barlow Semi Condensed* (familii de fonturi), Google Fonts, https://fonts.google.com/specimen/Barlow (SIL OFL 1.1, https://openfontlicense.org). Subseturile latin și latin-ext sunt incluse în `src/romana/dashboard/static/fonturi` și în `docs/sondare/fonturi`; textul licenței, în `LICENSES/OFL-1.1.txt`.
[^google-ai]: Google, modulul de asistență AI integrat în browserul Chrome, folosit pentru ciorna proiectului până la 18.10.2026. Termenii Google, https://policies.google.com/terms, secțiunea „Your content”: „Some of our services allow you to generate original content. Google won't claim ownership over that content.”
[^claude]: Anthropic, *Claude* (model Claude Opus 5.5, ID `claude-opus-5-5`), asistent AI generativ, rulat prin *Claude Code* (aplicația Claude pentru desktop), https://www.anthropic.com/claude, https://www.anthropic.com/claude-code; termeni: Consumer Terms, § 4 („we assign to you all our right, title, and interest (if any) in Outputs”), https://www.anthropic.com/legal/consumer-terms; Usage Policy, care interzice predarea lucrărilor asistate de AI fără permisiune sau atribuire („Plagiarize or submit AI-assisted work without proper permission or attribution”), https://www.anthropic.com/legal/aup; accesate 26.10.2026. Folosit începând cu 20.10.2026 pentru implementare, experimente și documentație (contribuția detaliată în § 13). Pentru loturile prin interfața de programare, din 1.11.2026: Commercial Terms, https://www.anthropic.com/legal/commercial-terms.

[^anthropic-sdk]: Anthropic, *anthropic-sdk-python* 2.3.0, https://github.com/anthropics/anthropic-sdk-python (Apache-2.0).
[^agpl]: Free Software Foundation, *GNU Affero General Public License*, versiunea 3, 19.11.2007, https://www.gnu.org/licenses/agpl-3.0.html; textul integral în `LICENSE`.
[^ccby]: Creative Commons, *Attribution 4.0 International (CC BY 4.0)*, https://creativecommons.org/licenses/by/4.0/legalcode; textul în `LICENSES/CC-BY-4.0.txt`.
[^ultralytics-licenta]: Ultralytics, „Ultralytics Licensing”, https://www.ultralytics.com/license, accesat 26.10.2026: „Open-source your entire project under AGPL-3.0” sau licența Enterprise, pentru folosirile care nu respectă AGPL-3.0.
[^osmf-atribuire]: OpenStreetMap Foundation, *Attribution Guidelines*, 2021, https://osmfoundation.org/wiki/Licence/Attribution_Guidelines (atribuirea în baze de date, în publicații tipărite și PDF, pentru modele de învățare automată).
[^webcam-termeni]: Webcam România, „Termeni și condiții”, actualizați în mai 2026, https://webcamromania.ro/termeni-si-conditii/, accesat 26.10.2026. Secțiunea 2: site-ul nu deține drepturi asupra fluxurilor video transmise, care aparțin operatorilor camerelor. Secțiunea 4: „Fluxurile video aparțin proprietarilor originali”; reproducerea conținutului site-ului fără acordul scris al administratorului nu este permisă, iar citările scurte cu link către sursă sunt permise doar în condițiile uzanței jurnalistice. Secțiunea 12: contactul se face prin formularul de contact.
[^legea8]: Legea nr. 8/1996 privind dreptul de autor și drepturile conexe, republicată, forma consolidată la 01.05.2022 (inclusiv modificările aduse de Legea nr. 69/2022): art. 9 lit. f), art. 35, art. 36^1, art. 36^2, art. 120; https://legislatie.just.ro/Public/DetaliiDocumentAfis/259087.
[^infosoc]: Directiva 2001/29/CE privind armonizarea anumitor aspecte ale dreptului de autor și drepturilor conexe în societatea informațională, art. 5 alin. (1), https://eur-lex.europa.eu/eli/dir/2001/29/oj. Reutilizare EUR-Lex conform Deciziei 2011/833/UE.
[^dsm]: Directiva (UE) 2019/790 privind dreptul de autor și drepturile conexe pe piața unică digitală, art. 3–4, https://eur-lex.europa.eu/eli/dir/2019/790/oj. Reutilizare EUR-Lex conform Deciziei 2011/833/UE.
[^gpl-faq]: Free Software Foundation, „Frequently Asked Questions about the GNU Licenses”, „In what cases is the output of a GPL program covered by the GPL too?”, https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL.
[^pytorch]: A. Paszke et al., „PyTorch: An Imperative Style, High-Performance Deep Learning Library”, NeurIPS 2019; https://github.com/pytorch/pytorch, versiunea 2.14 (licență BSD-3-Clause; expresia din metadatele pachetului: Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT).
[^pydata]: C. R. Harris et al., „Array programming with NumPy”, *Nature* 585:357–362, 2020, doi:10.1038/s41586-020-2649-2 (BSD-3-Clause); pandas, https://pandas.pydata.org (BSD-3-Clause); P. Virtanen et al., „SciPy 1.0”, *Nature Methods* 17:261–272, 2020, doi:10.1038/s41592-019-0686-2 (BSD-3-Clause); J. D. Hunter, „Matplotlib: A 2D Graphics Environment”, *Computing in Science & Engineering* 9(3):90–95, 2007, doi:10.1109/MCSE.2007.55 (Matplotlib License, de tip PSF, https://matplotlib.org/stable/project/license.html).
[^markdown-py]: Python-Markdown 3.8.1, https://github.com/Python-Markdown/markdown (BSD-3-Clause).
[^psutil]: G. Rodola, *psutil* 7.2.2, https://github.com/giampaolo/psutil (BSD-3-Clause).
[^python]: Python Software Foundation, *Python 3.12*, https://docs.python.org/3/license.html (PSF-2.0).
[^streetview]: Google, Street View (Google Maps), consultat pe 23.10.2026 doar pentru verificarea vizuală a rețelei. Termeni: Google Maps/Google Earth Additional Terms of Service, https://www.google.com/help/terms_maps/. Din Street View nu s-a preluat nicio informație în rețeaua OSM/SUMO și nu se publică nicio captură.
[^windy]: Windy.com, Webcams, https://www.windy.com/webcams, consultat 21.10.2026; nefolosit (afișează aceeași cameră Webcam România).
[^meteoblue]: meteoblue, webcam-uri, https://www.meteoblue.com, consultat 21.10.2026; nefolosit (afișează aceeași cameră Webcam România).
[^youtube]: YouTube, transmisiile „Webcam România – Piața Victoriei” și „Calea Victoriei City Cam”, consultate 21.10.2026; nefolosite. Termeni: https://www.youtube.com/t/terms.

## Anexa A. Fișierele de rezultate (`docs/rezultate/`)

Această anexă descrie fișierele cu datele brute din care provin cifrele capitolului 9. Statisticile de acolo se
calculează din aceste fișiere cu `romana.control.analiza`, fără a mai rula simulări (§ 11.8). Pentru fiecare fișier,
tabelul de mai jos arată ce conține, pe ce versiune a scenariilor a fost produs și cu ce se reface.

Cele mai multe fișiere care provin din simulări sunt de două feluri. Unele au rezultatele complete ale evaluării:
fiecare rând descrie o simulare, cu scenariul, strategia, seed-ul și toți indicatorii din § 7.5. Celelalte
păstrează doar indicatorul principal, pierderea totală de timp; coloanele lor sunt `model, scenariu, seed, pierdere_h`.
Seed-ul este valoarea care pornește generatorul de numere aleatoare al simulării.

**Coloana „Scenariile”** arată pe ce versiune a scenariilor a fost produs fișierul. Valorile ei înseamnă:

- „arborele curent”: scenariile din versiunea actuală a depozitului.
- „arborele curent, tipurile vechi”: scenariile actuale, dar cu tipurile de vehicule de dinainte de 28.10, în care
  intervalul `tau` al șoferilor avea valoarea implicită din SUMO (§ 6.4). Tipurile vechi se aduc cu
  `git checkout 75592d3 -- sumo/demand/vtypes.add.xml sumo/demand/vtypes_indisciplinat.add.xml`, iar revenirea se face
  cu `git checkout HEAD -- sumo/demand`.
- Un cod de commit: scenariile unei versiuni mai vechi a depozitului, salvată în istoricul Git. Ele se aduc
  temporar cu `git checkout <commit> -- sumo/scenarios sumo/demand config/demand.json`, iar revenirea se face cu
  `git checkout HEAD -- sumo config/demand.json` (§ 11.8). Atenție: scenariile din arborele curent au aceleași nume,
  dar cererea lor a fost recalibrată pe 26.10, deci dau alte cifre. Mențiunea „cu codul de atunci” arată că fișierul
  a fost produs și cu codul din acel commit, deci se reface numai cu acel cod, nu cu cel actual.
- Liniuța: fișierul nu a fost produs prin rularea unor scenarii.
- „măsura nouă, `cor_`”: scenariile `cor_zi_*` și `indisciplinat_cor_zi_*`, construite cu cererea și excluderile
  înghețate la commitul `cffd50e` din 3.11, pe rețeaua și tipurile de vehicule ale geamănului corectat,
  `romana_v2.net.xml` și `vtypes*_v2.add.xml` (§ 6.5, § 9.11).

**Coloana „Se reproduce cu”** dă modulul care reface fișierul.

**Notațiile și termenii din tabel.**

- O steluță într-un nume ține locul oricărei continuări: `test_28_*.csv` înseamnă ambele fișiere ale testului din
  28.10.
- Semnul „+” arată că rândul cuprinde și fișierul de alegere al aceleiași validări, cu terminația `_alegere.json`;
  în el e trecută, între altele, strategia aleasă.
- Bara oblică desparte variantele aceluiași nume: `ppo_romana_final_a/b` înseamnă două modele, cu terminațiile a și b.
- „Ambele comportamente” înseamnă simulări cu participanți disciplinați și cu participanți indisciplinați.
- „Marginea de jos” și „marginea de sus” sunt cele două estimări ale cererii de trafic folosite înaintea cererii
  calibrate din 26.10: prima pornește doar de la intrările numărate, a doua, de la media dintre intrări și ieșiri.
- „Calibrat” are două sensuri în tabel. „Cererea calibrată” este cererea de trafic corectată după numărătoarea de
  referință din 26.10; pe ea se sprijină și „scenariile calibrate” și „vârfurile calibrate”. „Capacitatea calibrată”
  și „geamănul calibrat” înseamnă că, în plus, parametrii șoferilor din simulare au fost reglați astfel încât geamănul
  să poată trece traficul observat (§ 6.4).
- O pereche înseamnă două simulări cu același scenariu și același seed, câte una pentru fiecare dintre cele două
  strategii comparate.
- Punctele intermediare sunt modele salvate pe parcursul antrenării unui agent.
- În comenzile cu planuri fixe, literele a, b și c țin locul duratelor de verde, în secunde, pentru axa nord–sud,
  pentru axa est–vest și pentru pietoni, în aceeași ordine ca în notația 12/14/12.
- Numele strategiilor și ale agenților sunt explicate în legenda de la începutul documentului.

**Pentru specialiști.** Fișierele `validare_*`, `robustete_*` și `calibrat_*` au fost produse cu scripturile de lucru
din care provine modulul `romana.control.validare`, publicat pe 26.10. Modulul dă aceleași valori: s-a verificat pe
rulări din `calibrat_normal.csv`, `calibrat_indisciplinat.csv`, `robustete_indisciplinat.csv` și
`validare_indisciplinat.csv`. Unele validări conțin și candidați sau puncte intermediare ale antrenării care nu sunt
publicate în `models/`: `ppo_romana_final_a/b`, `ppo_romana_nou_375k/600k/800k/900k`, `ppo_romana_greu_e7`,
`ppo_romana_moderat_mij`, `romana_ind_*`, `romana_mix_*`, `ppo_romana_g99*`, `ppo_romana_v3_c*` și candidații
`cand_*`, în afară de `cand_romana_cal3_100k`. Rândurile lor nu se pot reface; celelalte, da.

**Rezultate retrase.** Fișierele care au dus la capacitatea calibrată sau au fost produse cu ea, adică pe geamănul cu
`tau` = 0,8 s, care trecea traficul prin coliziuni și teleportări (§ 6.5), au rămas doar ca istoric:
`capacitate_baleiaj.csv`, `localizare_varf_capacitate.csv`, `capacitate_*_26*.csv`, `durate_verde_agenti.csv`,
`grila_calibrat.csv`, `validare_e14*`, `test_28_*.csv`, `sens_pietoni_28_*.csv`, `decizie_2026-10-2*.json`,
`test_29_*.csv` și `confirmare_2026-10-29.json`. Ele se pot reface la fel, dar concluziile lor, inclusiv câștigul de
−7% al planului 12/14/12, s-au retras pe 2.11. Tot ca istoric rămâne `geaman_camera_2026-10-26.csv`, din prima
corectură.

| Fișier | Ce conține | Scenariile | Se reproduce cu |
|---|---|---|---|
| `rezultate_brute.csv`, `rezultate.md`, `comparatie_strategii.png` | Evaluarea pe scenariile „doar intrări”, adică pe marginea de jos a cererii, pentru zilele lucrătoare și pentru duminică, pe seed-urile de test; alături, tabelul detaliat pe categorii de participanți și graficul. | `e1d0f77` | `romana.control.evaluate`, care se pornește și cu `scripts\5_evalueaza.bat` |
| `rezultate_brute_marginea_de_sus.csv` | Evaluarea pe scenariile cu cererea „medie”, adică pe marginea de sus a cererii: 1 400 de simulări, pe zilele lucrătoare și pe dimineața de duminică, cu seed-urile 1–10. | `7a79502` | `romana.control.evaluate` |
| `rezultate_v1_si_experimente.csv` | Evaluarea din 22.10, făcută cu zonele inițiale ale camerei; cuprinde agentul v1 și experimentele v2 și v3 (§ 9.5). | `8176be5`, cu codul de atunci | `romana.control.evaluate` din acel commit |
| `scenarii_referinta/` | Evaluarea pe scenariile ipotetice de la început, `referinta_*`. | `a845bf9`, cu codul de atunci | `romana.control.evaluate` din acel commit |
| `calibrat_normal.csv`, `calibrat_indisciplinat.csv` | Reevaluarea pe cererea calibrată, cu participanți disciplinați, respectiv indisciplinați, pe seed-urile de test 1–5 (§ 9.8). | arborele curent, tipurile vechi | `romana.control.validare --seeds 1-5 --fara-alegere` |
| `calitate_inregistrare.csv` | Cât de continuă a fost urmărirea, oră cu oră, în zilele 21, 22, 25, 26, 28 și 29.10 (§ 4.6): numărul de traiectorii, golurile de peste 1 s și densitatea punctelor. | – | `romana.vision.calitate` |
| `veghe_reluare.csv` | Veghea fluxului de cadre, programul care supraveghează imaginile primite de la cameră, are și reguli care citesc jurnalul de traiectorii. Fișierul arată rezultatul acestor reguli, aplicate minut cu minut pe jurnalele brute din 21, 22 și 25–29.10 (§ 4.6). Un pas este intervalul de timp dintre două puncte succesive ale aceleiași traiectorii. Fiecare rând conține: numărul pașilor vehiculelor din ultimele 10 minute, procentul celor de peste 0,5 s și pasul median; traiectoriile încheiate, cu toate tipurile de participanți la un loc; cele ale vehiculelor în mișcare; vehiculele oprite și cele cu poziții identice; timpul fără traiectorii noi; semnele de problemă. Coloana `zi` arată jurnalul, iar `ora`, momentul evaluării. Rândurile cu data zilei următoare țin de traiectoriile începute în ziua jurnalului și încheiate după miezul nopții. | – | `romana.vision.veghe --reluare`, rulat pe câte o zi |
| `capacitate_baleiaj.csv` | Capacitatea geamănului digital, adică câte vehicule poate lăsa să treacă, pentru mai multe variante ale parametrilor care descriu șoferii (§ 6.4). Scenariile sunt vârful de luni și varianta lui ×1,2, cu cererea mărită cu 20%. Rândurile dau, pentru fiecare scenariu și fiecare variantă a parametrilor, vehiculele introduse în rețea, cele neintroduse, care nu au mai încăput în ea, și câte vehicule au intrat în piață pe fiecare braț. | arborele curent; tipurile vechi la rândurile „standard” | `romana.control.capacitate` |
| `localizare_varf_capacitate.csv` | Aceeași analiză ca în `localizare_varf_calibrat.csv`, din rândul următor, pe vârful de luni și pe vârful ×1,2, cu capacitatea calibrată și cu ambele comportamente; pentru comparație, și vârful de luni cu parametrii impliciți (§ 9.6). | arborele curent; rândul `zi_2026-10-26_varf`: tipurile vechi | `romana.control.localizare` |
| `localizare_varf_calibrat.csv` | Unde se pierde timpul la vârf (§ 9.6). Fișierul dă vehicul-orele de oprire din fiecare zonă, adică timpul petrecut oprit de toate vehiculele din zonă, adunat și exprimat în ore. Dă și vehiculele neintroduse, împărțite după muchia de plecare, adică tronsonul de drum de unde trebuiau să pornească, cu numele străzii și capătul față de piață, vest sau est. Analiza s-a făcut cu planul fix actual și seed 1, pe cele 4 vârfuri calibrate. | arborele curent, tipurile vechi | `romana.control.localizare` |
| `robustete_indisciplinat.csv`, `robustete_indisciplinat_6_10.csv` | Testul cu participanți indisciplinați, pe seed-urile 1–5, respectiv 6–10 (§ 9.4): actuated, agentul oficial, E3, E9 și planul fix, pe 5 scenarii de zi lucrătoare. | `e1d0f77` | `romana.control.validare --seeds 1-5` / `--seeds 6-10`, `--fara-alegere`; comanda completă e în § 11.8 |
| `robustete_indisciplinat_duminica.csv`, `robustete_indisciplinat_duminica_6_10.csv` | Același test pe duminica 25.10, pe seed-urile 1–5, respectiv 6–10 (§ 9.4): actuated, agentul oficial, E3 și planul fix. | `e1d0f77`: cele 5 scenarii de duminică de atunci, fără `pranz` | la fel ca în rândul de deasupra |
| `validare_indisciplinat.csv` + `_alegere.json` | Validarea din care s-a ales programul realist, pe seed-urile 11–15. | `e1d0f77` | `romana.control.validare --seeds 11-15` |
| `validare_intrari.csv` + `_alegere.json` | Validarea componentelor programului pentru marginea de jos a cererii, pe seed-urile 11–15. | `e1d0f77` | `romana.control.validare --seeds 11-15` |
| `validare_indisciplinat_e10.csv`, `validare_indisciplinat_e11.csv` | Validarea agenților E10 și E11 (§ 9.5), cu punctele lor intermediare. | `e1d0f77` | `romana.control.validare`; punctele intermediare nu sunt publicate |
| `validare_calibrat.csv` + `_alegere.json` | Validarea agenților E12 și E13 (§ 9.5) pe scenariile calibrate cu participanți indisciplinați, pe seed-urile 11–15. În comparație intră planul fix, actuated, agentul oficial, E3 și câte trei candidați pentru fiecare dintre cei doi agenți: punctele intermediare de la +100 000 și +200 000 de pași de antrenare și modelul final. | arborele curent, tipurile vechi | `romana.control.validare`; dintre candidați sunt publicați doar `cand_romana_cal3_100k`, `ppo_romana_cal3` și `ppo_romana_cal` |
| `capacitate_indisciplinat_26.csv`, `capacitate_normal_26.csv` | Testul pe luni 26.10, cu capacitatea calibrată (§ 9.9): planul fix, actuated, planul 46/48/12, agentul oficial, E3, E9, E12 și E13, pe seed-urile 1–5. | arborele curent | `romana.control.validare --seeds 1-5 --fara-alegere` |
| `capacitate_indisciplinat_26_6_10.csv`, `capacitate_normal_26_6_10.csv` | Aceleași strategii pe seed-urile 6–10, rulate după fixarea protocolului (§ 9.9). | arborele curent | `romana.control.validare --seeds 6-10 --fara-alegere` |
| `durate_verde_agenti.csv` | Duratele de verde alese de E13 și de agentul oficial pe trei scenarii de validare din luni 26.10, cu seed 11 (§ 9.9): mediana pe fiecare fază, de câte ori a primit verde fiecare fază și ciclul median. | arborele curent | `romana.control.durate_verde` |
| `program_real_2026-10-26.csv`, `program_real_2026-11-01.csv`, `program_real_2026-11-02.csv`, `program_real_2026-11-03.csv`, `program_real_2026-11-04.csv`, `program_real_2026-11-05.csv`, `program_real_2026-11-06.csv`, `program_real_2026-11-07.csv` | Programul real al semaforului, măsurat din jurnalul public al vehiculelor (§ 6.5): ciclul pe intervale și pe fiecare 20 de minute, cât curge fiecare intrare, debitul de vârf. | – (din jurnalul public al vehiculelor) | `romana.vision.program_real --zi <zi> --pe-zi --interval … --out …`; pentru 2–7.11, comanda exactă e în `program_real_criterii.json` |
| `program_real_criterii.json`, `program_real_verdict_2026-11-02_04.json`, `program_real_verdict_2026-11-05.json`, `program_real_verdict_2026-11-06.json`, `program_real_verdict_2026-11-07.json` | Criteriile după care se citește programul real pe zilele noi, comise și publicate pe 5.11, după zilele 2–4.11, dar înaintea rulărilor care dau verdictele: când e de încredere o măsurătoare de 20 de minute și când e măsurată o zi, plus trei verificări, dintre care una e o probă de control pentru ciclul de 91 s. Verdictele, pe 2, 3, 4, 5, 6 și 7.11: toate cele șase zile sunt măsurate și trec toate verificările, cu mediana zilei de ≈133–137 s. Zilele 2–4.11 s-au judecat pe 5.11, iar ziua de 5.11, separat, pe 6.11, după ce prelucrarea ei de noapte s-a încheiat cu codul 0. Zilele de 6 și 7.11, care nu sunt în lista criteriilor, s-au judecat la fel, pe 7 și pe 8.11, cu aceleași criterii, neschimbate (§ 6.5). Zilele de 26.10 și 1.11 apar doar ca reper (§ 6.5). | – (din jurnalul public al vehiculelor) | comanda din criterii reface fișierele zilelor; verdictul se reface aplicând criteriile pe ele, iar proba de control, după codul esențial scris în fișierul verdictului |
| `geaman_camera_2026-10-26.csv` | Vehicule pe ciclu și debit de vârf, pe fiecare intrare, în cameră și în prima corectură a geamănului, cea cu al doilea defect (§ 6.5). Rămâne doar ca istoric. | arborele curent | `romana.control.compara_camera` |
| `validare_geaman.csv`, `poarta_geaman.json`, `praguri_geaman.json` | Comparația geamănului corectat cu camera la îngheț (§ 6.5, § 9.11): pe 12 ore din zilele de antrenare, câte un rând pe măsură, cu camera, geamănul pe seed-uri, abaterea, pragul și verdictul, pentru geamănul de bază și pentru cei doi gemeni greșiți dinadins; verdictul porții pe fiecare oră; pragurile calculate, mediana pe ore, fixate pentru zilele noi. Fiecare rând poartă commitul, factorii și data rulării. | măsura nouă, `cor_` | `romana.control.valideaza_geaman` (comanda din § 11.8) |
| `grila_inghet_normal.csv`, `grila_inghet_indisciplinat.csv` | Grila de după îngheț, pe zilele de antrenare (25.10, 26.10, 1.11, 2.11), cu ambele comportamente și seed-urile 1–3: semaforul rejucat, planul observat 72/48/3, planurile 60/40/3, 45/30/3, 90/50/3, 36/28/12, 12/14/12 și programul actuated; câte un rând pe simulare, cu pierderea totală și pe tipuri de participanți, teleportările, ciocnirile și vehiculele nesosite (§ 6.5, § 9.11). | măsura nouă, `cor_` | `romana.control.validare <strategii> --scenarii "cor_zi_<zi>_*" --seeds 1,2,3 --fara-alegere --fara-fix` |
| `grila_inghet_ciclu.csv` | Planurile 36/24/3 și 52/35/3, cu același raport al verdelui ca planul observat, pe cele 14 scenarii ale zilelor de antrenare care trec poarta, cu ambele comportamente și seed-urile 1–3, în același format ca grila (§ 9.11). | măsura nouă, `cor_` | `romana.control.validare PLAN_36_24_3 PLAN_52_35_3 --scenarii <cele 28 de scenarii> --seeds 1,2,3 --fara-alegere --fara-fix` |
| `grila_inghet_e15.csv` | Agentul E15 pe aceleași 14 scenarii, cu ambele comportamente și seed-urile 1–3, în același format ca grila (§ 9.5, § 9.11). | măsura nouă, `cor_` | `romana.control.validare models/ppo_e15.zip --scenarii <cele 28 de scenarii> --seeds 1,2,3 --fara-alegere --fara-fix` |
| `poarta_cor_2026-11-03.json`, `geaman_cor_2026-11-03.csv`, `cor_test_2026-11-03_indisciplinat.csv`, `cor_test_2026-11-03_normal.csv`, `cor_decizie_2026-11-03.json`, `stare_lant_cor_2026-11-03.json` | Ziua de antrenare 3.11, prelucrată de lanțul măsurii noi pe 4.11 (§ 9.11): verdictul porții pe fiecare oră și comparația geamănului cu camera, pe 5 seed-uri; planul observat, semaforul rejucat, candidații și programul actuated pe cele 7 scenarii ale zilei, cu ambele comportamente și seed-urile 1–10; regula, aplicată doar descriptiv, fiindcă nicio oră nu trece poarta; pașii lanțului, cu comenzile, orele și codurile de ieșire, cu căile scrise față de depozit. | măsura nouă, `cor_` | `romana.lant_cor --zi 2026-11-03`; comenzile pașilor sunt în `stare_lant_cor_2026-11-03.json` |
| `poarta_cor_2026-11-04.json`, `geaman_cor_2026-11-04.csv`, `cor_test_2026-11-04_indisciplinat.csv`, `cor_test_2026-11-04_normal.csv`, `cor_decizie_2026-11-04.json`, `stare_lant_cor_2026-11-04.json` | Ziua de validare 4.11, prelucrată de lanțul măsurii noi pe 5.11 (§ 9.11), în același format ca ziua de 3.11: verdictul porții pe fiecare dintre cele 4 ore și comparația geamănului cu camera, pe 5 seed-uri; planul observat, semaforul rejucat, candidații și programul actuated pe cele 6 scenarii ale zilei, cu ambele comportamente și seed-urile de validare 11–15; decizia validării, scrisă de lanț la 04:16 și comisă la 04:23, înainte de a privi datele zilelor de test; pașii lanțului, cu comenzile, orele și codurile de ieșire. Nicio oră nu trece poarta, deci validarea e doar descriptivă: niciun candidat nu trece, iar planul observat, 72/48/3, rămâne. | măsura nouă, `cor_` | `romana.lant_cor --zi 2026-11-04`; comenzile pașilor sunt în `stare_lant_cor_2026-11-04.json` |
| `poarta_cor_2026-11-05.json`, `geaman_cor_2026-11-05.csv`, `stare_lant_cor_2026-11-05.json` | Ziua de 5.11, prima zi de test, prelucrată de lanțul măsurii noi pe 6.11 (§ 9.11): doar geamănul și poarta, fără strategii, fiindcă niciun candidat nu a trecut de validare; verdictul porții pe fiecare dintre cele 5 ore. | măsura nouă, `cor_` | `romana.lant_cor --zi 2026-11-05`; comenzile pașilor sunt în `stare_lant_cor_2026-11-05.json` |
| `poarta_cor_2026-11-06.json`, `geaman_cor_2026-11-06.csv`, `stare_lant_cor_2026-11-06.json` | Ziua de 6.11, a doua zi de test, prelucrată de lanțul măsurii noi pe 7.11 (§ 9.11), în același format ca ziua de 5.11: doar geamănul și poarta, fără strategii, fiindcă niciun candidat nu a trecut de validare; verdictul porții pe fiecare dintre cele 4 ore. | măsura nouă, `cor_` | `romana.lant_cor --zi 2026-11-06`; comenzile pașilor sunt în `stare_lant_cor_2026-11-06.json` |
| `poarta_cor_2026-11-07.json`, `geaman_cor_2026-11-07.csv`, `stare_lant_cor_2026-11-07.json` | Ziua de 7.11, sâmbăta de generalizare, prelucrată de lanțul măsurii noi pe 8.11 (§ 9.11), în același format ca zilele de test: doar geamănul și poarta, fără strategii, fiindcă niciun candidat nu a trecut de validare; verdictul porții pe fiecare dintre cele 5 ore. Poarta trece pe toate, dar pe Dacia vest, care nu e un rând al porții, geamănul rămâne sub cameră la vârf și la prânz. | măsura nouă, `cor_` | `romana.lant_cor --zi 2026-11-07`; comenzile pașilor sunt în `stare_lant_cor_2026-11-07.json` |
| `fisa_senzor_2026-11-06_0000.json`, `fisa_senzor_2026-11-06_0000.md` | Fișa senzorului (§ 4.6), la singura tăietură citată, de la 1.11, 09:04:46, până la 6.11, 00:00: timpul scurs și cel cu colectarea pornită, minutele cu cadre, cadrele analizate pe secundă, pauzele, reconectările, opririle anunțate și căderile neprevăzute, prelucrările de noapte și vehiculele intrate, pe zile și pe clase; pietonii, doar ca totaluri pe zi. JSON-ul e fișa întreagă, iar `.md`, tabelul scurt; rândul „vin. 06.11”, doar cu zerouri, e al zilei care abia începea la tăietură, iar codul din 10.11 nu-l mai scrie. | – (din jurnalele locale ale colectării, care nu intră în depozit) | `romana.vision.fisa_senzor --pana-la "2026-11-06 00:00" --out-json … --out-md …`, doar pe calculatorul care a colectat (§ 11.8) |
| `referinta_v2/` | Numărătoarea de referință a măsurii noi pe 11 clipuri din 1.11 și 2.11 (pe ținte și bucăți de 30 s), factorii de corecție pe zi, pe întuneric și pe tot, cu intervalele de încredere, și momentele pietonilor pe valuri, fără imagini (§ 4.3). | – (din clipuri) | `romana.vision.referinta factori` |
| `grila_calibrat.csv` | Grila de 23 de planuri fixe încercate pe geamănul calibrat (§ 9.9), pe luni 26.10, cu ambele comportamente și seed-urile 11–15, la care se adaugă planul fix de referință. | arborele curent | `romana.control.validare PLAN_a_b_12 …` |
| `test_28_indisciplinat.csv`, `test_28_normal.csv` | Testul pe miercuri 28.10 (§ 9.10): planul fix, actuated, agentul oficial, E3, E13 și planurile 12/14/12 și 16/10/12, pe seed-urile 1–10. Pierderea de timp e dată și pe tipuri de participanți, în coloanele `pierdere_h_<tip>`. | arborele curent | `romana.control.validare --seeds 1-10 --fara-alegere` |
| `sens_pietoni_28_indisciplinat.csv`, `sens_pietoni_28_normal.csv` | Sensibilitatea rezultatului la o fază de pietoni mai lungă (§ 9.10): planurile 12/14/18 și 36/28/18, pe aceleași scenarii și seed-uri ca testul din 28.10. Au fost rulate după test și se citesc împreună cu `test_28_*.csv`. | arborele curent | `romana.control.validare PLAN_12_14_18 PLAN_36_28_18 --seeds 1-10 --fara-alegere --fara-fix` |
| `decizie_2026-10-28.json`, `decizie_2026-10-28_persoane_20.json` / `_40` / `_70` | Decizia după regula „cel mai bun câștigă” (§ 9.10): debitele și cazurile de trafic ale scenariilor, candidații cu testele lor statistice, primii doi, câștigătorul și varianta de program pentru geamănul în timp real. Celelalte trei fișiere fac același calcul pe măsura pe persoană, care socotește timpul pierdut de oameni, nu de vehicule, cu 20 / 40 / 70 de călători pe autobuz. Fișierele intermediare pe persoană nu sunt publicate; le reface `romana.control.ocupare`. | – (din fișierele de test) | `romana.control.decizie`, `romana.control.ocupare` |
| `test_29_indisciplinat.csv`, `test_29_normal.csv` | Confirmarea pe joi 29.10 (§ 9.10): aceleași strategii și seed-uri ca testul din 28.10, cu pierderea de timp dată și pe tipuri de participanți. | arborele curent | `romana.control.validare --seeds 1-10 --fara-alegere` |
| `confirmare_2026-10-29.json` | Rezultatul confirmării (§ 9.10): debitele și cazurile de trafic ale scenariilor, comparația planului 12/14/12 cu programul realist, pe toate perechile la un loc și pe fiecare comportament, și verdictul. | – (din fișierele confirmării) | `romana.control.decizie --confirma PLAN_12_14_12` |
| `decizie_2026-10-29.json`, `decizie_2026-10-29_persoane_20.json` / `_40` / `_70` | Decizia refăcută doar pe datele din 29.10, cu titlu informativ (§ 9.10), și pe măsura pe persoană. | – (din fișierele confirmării) | `romana.control.decizie`, `romana.control.ocupare` |
| `validare_e14.csv` + `_alegere.json` | Validarea agentului E14 (§ 9.5) pe luni 26.10, cu ambele comportamente și seed-urile 11–15. În comparație intră planul fix, actuated, agentul oficial, E3, E13 și trei candidați E14: punctele intermediare de la +100 000 și +200 000 de pași de antrenare și modelul final. | arborele curent | `romana.control.validare`; dintre candidați e publicat doar modelul final, `ppo_romana_e14` |
| `test_reantrenare_indisciplinat.csv`, `test_reantrenare_normal.csv` | Testul agenților aleși, E12 (`cand_romana_cal3_100k`) și E13 (`ppo_romana_cal`), pe seed-urile 1–5. Rezultatele celorlalte strategii vin din `calibrat_*.csv`. | arborele curent, tipurile vechi | `romana.control.validare --seeds 1-5 --fara-alegere --fara-fix` |
| `validare_zone_noi`, `validare_e2_e3`, `validare_clasice`, `validare_nou_*`, `validare_greu*`, `validare_moderat_e8`, `validare_lejer_e9`, din 23–25.10, fiecare cu fișierul său `_alegere.json`, acolo unde există | Validările pentru marginea de sus a cererii, întâi pe seed-urile 11–13, apoi pe 11–15, din care s-au ales agenții, planurile și componentele programului. Un fișier `_alegere.json` conține scorul mediu al fiecărei strategii față de planul fix, strategia aleasă, seed-urile prezente în CSV și scenariile. | `7a79502` | `romana.control.validare`; seed-urile din fișierele de alegere au fost corectate cu `--corecteaza-alegeri`, iar testele pe seed-urile 1–10 nu au fișier de alegere |
| `validare_finala.csv` | Validarea din 22.10 din care s-a ales agentul oficial, pe seed-urile 11–13. | `8176be5`, cu codul de atunci | scripturi de lucru, cu rezultatele în formatul lui `romana.control.validare` |
| `grila_plan.csv`, `grila_plan_zone_noi.csv` | Grilele de planuri fixe (§ 9.5). | `1619a30`, cu codul de atunci, respectiv `7a79502` | scripturi de lucru nepublicate, cu aceeași funcție de simulare, `evaluate.run_one`; o grilă se reface cu `romana.control.validare PLAN_a_b_c …` sau cu `romana.control.evaluate --planuri a,b,c` |
| `calibrare_conservare*.csv` | Încercarea de a calibra numărarea ieșirilor după criteriul conservării vehiculelor: din piață ies tot atâtea vehicule câte intră (§ 4.3). | – (renumărare, fără simulări) | un script de lucru nepublicat, care reface numărarea cu `vision/recount.py` și cu pragurile `Params.capat_min_*` din `vision/od_counter.py` |
| `candidati_*.csv`, `alegere_agent*.json` | Candidații și alegerea agenților din primele experimente. Fișierul `alegere_agent.json` corespunde lui `validare_finala.csv`, iar `alegere_agent_zone_noi.json`, lui `validare_e2_e3.csv`. | `candidati_*`: `1619a30`; `alegere_agent.json`: `8176be5`, cu codul de atunci; `alegere_agent_zone_noi.json`: `7a79502` | scripturi de lucru, cu rezultatele în același format ca `romana.control.validare` |
| `referinta/` | Numărătoarea de referință din 26.10 (§ 4.3): numărătorile adnotatorilor pe bucăți de 30 s, în `referinta_clip1.csv` și `referinta_clip2.csv`, cu coloanele `tinta, bucata, adnotator, numar`; traiectoriile vehiculelor din cele două clipuri, obținute cu detectorul la 1600 px, în `clip1/` și `clip2/`, și la 2560 px, în `clip1_2560/` și `clip2_2560/`, fără pietoni și fără imagini, sub licența ODbL 1.0 (§ 14.1); factorii de corecție, în `factori.json`; calibrarea camerei, în `corespondente_camera.json`, `model_camera.json` și `erori_camera.csv`. | – | `romana.vision.referinta factori` și `romana.vision.calibrare_camera potrivire` (§ 11.8) |
| `evaluare_m1/probleme.csv`, `evaluare_m2/probleme_runda1.csv`, `evaluare_m2/probleme_runda2.csv` | Evaluarea dispeceratului cu evaluatori AI (§ 8), pe versiunea M1 și pe cele două versiuni reparate: câte un rând pe fiecare problemă rămasă după reunire, cu titlul, severitatea pe scara lui Nielsen, verdictul celor doi verificatori, evaluatorii care au găsit-o, euristicile încălcate, capturile, descrierea, dovada, recomandarea și motivele verificatorilor. | – (din capturile paginii și din codul ei) | `romana.dashboard.evaluare` (`trimite`, `reuneste`, `verifica`, `rezultat`), prin loturi la interfața de programare Claude; evaluatorii sunt modele de limbaj, deci o rulare nouă poate găsi alte probleme |
| `sondare_m2.csv` | Rezultatele sondării cu oameni (§ 8), publicate o singură dată, după închiderea din 7.11, 18:00. Fișierul are doar rândurile colegilor, grupul `c`, singurul cu cel puțin trei texte numărate. Rândurile „x din 3” privesc sarcinile și întrebările din tabelul din § 8, pe fiecare dintre cele două variante ale dispeceratului: `m1`, cea de la borna M1, și `m2`, cea a bornei M2, înghețată pe 3.11. Numele din coloana `masura` sunt prescurtări: `culoarea pe Magheru` și `a văzut schimbarea` sunt întrebările de după sarcina 3, `a văzut cine conduce` e întrebarea de după sarcina 4, „Ați putut vedea în aplicație cine schimbă acum culorile?”, iar `ușor sau foarte ușor`, întrebarea „Cât de ușor v-a fost să folosiți această variantă?”. În ele, `persoane` spune câte persoane au trecut prin pas, iar `reusite`, câte au reușit sau au dat răspunsul numărat în § 8; `persoane_prima_runda` spune câte persoane au început cu acea variantă, iar `reusite_prima_runda` rămâne goală. În rândurile `varianta preferată`, `persoane` spune câte persoane au ales varianta din coloana `versiune`: `m1`, `m2` sau `la fel`. În rândul `a avut nevoie de ajutor la sarcini`, `persoane` spune câte au răspuns „Da, la înțelegerea sarcinilor”; celelalte răspunsuri nu se numără. Fișierul nu are coduri, ore, mărimi de ecran, timpi, apăsări sau text liber. Coloanele: `grup, masura, versiune, persoane, reusite, persoane_prima_runda, reusite_prima_runda`. | – (din textele trimise prin formular) | `romana.dashboard.sondare --publica`, o singură dată; fără textele primite, care nu sunt publice, fișierul nu se poate reface din depozit |
