"use strict";
const DATE_SONDARE = {
"VERSIUNE": "v2",
"FAZE": [
"N–S: Magheru ↔ Lascăr Catargiu prin centru",
"E–V: Dacia în jurul insulei",
"Pietoni: toate trecerile, axa centrală se golește",
"N–S, cu intrările Dacia deschise (fără dozare)",
"E–V, cu intrările Magheru/Catargiu deschise (fără dozare)",
"Golirea centrului, fără pietoni"
],
"PLAN": [
[
0,
72
],
[
1,
48
],
[
5,
3
]
],
"GALBEN": 3,
"ROSU": 2,
"VERDE_MIN": 10,
"INTARZIERE_PIETONI": 28,
"DEGAJARE_PIETONI": 6,
"PAS_COMANDA": 5,
"VERDE_PE_DACIA": [
1,
3,
4
],
"VERDE_PE_MAGHERU": [
0,
3,
4
],
"AUTOMATE": [
"ai",
"fix",
"max_pressure",
"program"
],
"COZI": [
{
"dacia_vest": 22,
"magheru": 11,
"catargiu": 6,
"dacia_est": 4,
"pietoni": 5
},
{
"magheru": 21,
"dacia_vest": 9,
"catargiu": 12,
"dacia_est": 6,
"pietoni": 3
}
],
"INTRARI": [
{
"magheru": 1180,
"catargiu": 410,
"dacia_vest": 690,
"dacia_est": 520
},
{
"magheru": 640,
"catargiu": 430,
"dacia_vest": 1120,
"dacia_est": 560
}
],
"IESIRI": {
"magheru": 870,
"mendeleev": 240,
"dacia_vest": 610,
"dacia_est": 480,
"caderea_bastiliei": 330,
"catargiu": 600
},
"ALEGE_CONDUCE": {
"calculator": "Un calculator, singur",
"om": "Un om, de la acest ecran"
},
"LUNGIME_TEXT": 300,
"URL_PROIECT": "https://github.com/NiuninMatei/Semaforizare_Piata_Romana",
"PE_TELEFON": [
[
"în partea din dreapta",
"în partea de jos"
],
[
"partea din dreapta",
"partea de jos"
],
[
"Partea din dreapta",
"Partea de jos"
],
[
"aplicația din dreapta",
"aplicația de jos"
],
[
"În stânga primiți",
"Sus primiți"
],
[
"Răspundeți în stânga",
"Răspundeți sus"
],
[
"Dacă în dreapta nu se vede tot, folosiți rotița mouse-ului sau două degete pe suprafața tactilă",
"Dacă jos nu se vede tot, derulați cu degetul"
]
],
"PASI": [
{
"id": "bun_venit",
"tip": "info",
"titlu": "Bun venit!",
"text": [
"Vă mulțumim că ne ajutați. Verificăm dacă o aplicație care arată semafoarele din Piața Romană și cozile de mașini, într-o simulare pe calculator, este ușor de înțeles. Este un proiect universitar.",
"**Verificăm aplicația, nu pe dumneavoastră: nu există răspunsuri bune sau greșite.** Dacă ceva nu merge sau nu se înțelege, e o problemă a aplicației, iar asta vrem să aflăm.",
"Durează între 10 și 20 de minute, pe un calculator. Vă puteți opri oricând, fără nicio explicație, cu butonul „Mă opresc aici”.",
"**Vă rugăm să nu discutați cu alți participanți la acest sondaj despre răspunsuri**, ca rezultatele să fie cât mai apropiate de opinia dumneavoastră reală."
],
"buton": "Mai departe"
},
{
"id": "acord",
"tip": "info",
"lung": true,
"titlu": "Ce se întâmplă cu răspunsurile",
"text_invitat": [
"Pagina nu cere nume, cont sau adresă de e-mail. Ce răspundeți, cât durează și ce apăsați se notează doar în această filă a browserului. Nu se înregistrează imagine sau sunet.",
"**La final vedeți tot ce s-a notat și decideți dacă trimiteți.** Dacă închideți fila înainte, totul dispare.",
"Dacă trimiteți, textul ajunge printr-un formular Google la persoana care v-a invitat. Fiindcă sunteți puțini, ea poate bănui al cui e un răspuns. O ajută Claude, un program de inteligență artificială, deci textul ajunge și la firma care îl face, Anthropic, din SUA.",
"În proiect apar doar totaluri, nu ce a răspuns fiecare. Răspunsurile se șterg după notarea proiectului și, dacă cereți, mai devreme.",
"GitHub, care găzduiește pagina, notează adresa IP a vizitatorilor, din motive de securitate. Google o vede dacă deschideți formularul."
],
"text_deschis": [
"Aceasta e o probă deschisă: nimic din ce faceți aici nu se trimite nicăieri, iar când închideți fila totul dispare.",
"Pagina nu cere nume, cont sau adresă de e-mail și nu folosește cookie-uri. Nu se înregistrează imagine sau sunet.",
"GitHub, care găzduiește pagina, notează adresa IP a vizitatorilor, din motive de securitate."
],
"buton": "Sunt de acord, începem"
},
{
"id": "profil_calculator",
"tip": "alegere",
"titlu": "Cât de des folosiți calculatorul?",
"eticheta": "Folosește calculatorul",
"optiuni": [
"Rar sau deloc",
"Uneori",
"În fiecare zi"
]
},
{
"id": "camera",
"tip": "info",
"titlu": "Piața, în direct",
"text": [
"Dacă doriți, puteți vedea cum arată acum Piața Romană, pe site-ul Webcam România. Se deschide într-o filă nouă; apoi reveniți aici. Nu e obligatoriu."
],
"link": {
"text": "Vedeți camera pe webcamromania.ro",
"adresa": "https://webcamromania.ro/webcam-orase/webcam-piata-romana-bucuresti/"
},
"buton": "Mai departe"
},
{
"id": "cum_lucram",
"tip": "info",
"lung": true,
"titlu": "Cum lucrăm",
"text": [
"Imaginați-vă că lucrați într-un centru care supraveghează semafoarele din Piața Romană. Încercați fără grijă: aici nu se dau note.",
"În stânga primiți, pe rând, câte o sarcină. O faceți în partea din dreapta, apoi apăsați „Am terminat”. Partea din dreapta se acoperă și răspundeți la o întrebare, din ce ați văzut.",
"Dacă în dreapta nu se vede tot, folosiți rotița mouse-ului sau două degete pe suprafața tactilă. Imaginea de la cameră e, aici, o fotografie fixă a pieței.",
"Dacă nu reușiți, apăsați „Nu reușesc”. Nu e nicio problemă.",
"Veți vedea, pe rând, două variante ale aceleiași aplicații."
],
"buton": "Am înțeles"
},
{
"id": "r1_deschide",
"tip": "deschide",
"versiune": "m1",
"runda": 0,
"titlu": "Pornim prima variantă",
"text": [
"Apăsați butonul de mai jos. Aplicația se deschide în partea din dreapta."
],
"buton": "Deschide aplicația",
"sit": {
"runda": 0,
"mod": "program"
}
},
{
"id": "r1_conduce",
"tip": "sarcina",
"sarcina": 1,
"eticheta": "Sarcina 1, cine schimbă culorile",
"versiune": "m1",
"runda": 0,
"ecran": true,
"text": [
"Uitați-vă la partea din dreapta, fără să apăsați nimic pe ea.",
"**Cine schimbă acum culorile semaforului: un calculator sau un om?**",
"Când ați aflat, apăsați „Am terminat”."
]
},
{
"id": "r1_conduce_r",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Cine schimbă acum culorile semaforului?",
"eticheta": "Cine schimbă culorile",
"optiuni": [
"Un calculator, singur",
"Un om, de la acest ecran",
"Nu pot spune"
],
"corect_din_banc": "conduce"
},
{
"id": "r1_coada",
"tip": "sarcina",
"sarcina": 2,
"eticheta": "Sarcina 2, cea mai lungă coadă",
"versiune": "m1",
"runda": 0,
"ecran": true,
"text": [
"**Pe care stradă așteaptă acum cele mai multe mașini la semafor?**",
"Când ați aflat, apăsați „Am terminat”."
]
},
{
"id": "r1_coada_r",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Pe care stradă așteaptă cele mai multe mașini?",
"eticheta": "Cele mai multe mașini",
"optiuni": [
"Magheru",
"Lascăr Catargiu",
"Dacia est",
"Dacia vest",
"Nu pot spune"
],
"corect": "Dacia vest"
},
{
"id": "r1_verde",
"tip": "sarcina",
"sarcina": 3,
"eticheta": "Sarcina 3, verde pe Dacia",
"versiune": "m1",
"runda": 0,
"ecran": true,
"verifica": "verde",
"sit": {
"mod": "program",
"nemiscat": true
},
"text": [
"**Dați verde pe Bulevardul Dacia**, ca și cum ați schimba dumneavoastră culorile semaforului.",
"Când credeți că ați reușit, apăsați „Am terminat”."
]
},
{
"id": "r1_verde_r",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Ce culoare avea semaforul pe Bulevardul Magheru când ați apăsat „Am terminat”?",
"eticheta": "Culoarea pe Magheru",
"optiuni": [
"Verde",
"Galben",
"Roșu",
"Nu pot spune"
],
"corect_din_banc": "magheru"
},
{
"id": "r1_verde_vazut",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Ați putut vedea în aplicație dacă s-a schimbat ce ați vrut?",
"eticheta": "A văzut schimbarea",
"optiuni": [
"Da, clar",
"Da, dar nu eram sigur(ă)",
"Nu"
]
},
{
"id": "r1_automat",
"tip": "sarcina",
"sarcina": 4,
"eticheta": "Sarcina 4, înapoi la calculator",
"versiune": "m1",
"runda": 0,
"ecran": true,
"verifica": "automat",
"pregateste": "manual_dacia",
"text": [
"**Lăsați din nou calculatorul să schimbe singur culorile semaforului**, ca să nu mai fie nevoie de dumneavoastră.",
"Când credeți că ați reușit, apăsați „Am terminat”."
]
},
{
"id": "r1_automat_vazut",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Ați putut vedea în aplicație cine schimbă acum culorile?",
"eticheta": "A văzut cine conduce",
"optiuni": [
"Da, clar",
"Da, dar nu eram sigur(ă)",
"Nu"
]
},
{
"id": "r1_inchide",
"tip": "inchide",
"versiune": "m1",
"runda": 0,
"ecran": true,
"acoperit": true,
"titlu": "Închideți aplicația",
"text": [
"Ați terminat sarcinile pe această variantă. Apăsați butonul de mai jos: aplicația din dreapta se închide."
],
"buton": "Închide aplicația"
},
{
"id": "r1_culori",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"titlu": "Pe desenul pieței, ce credeți că arată o linie roșie groasă pe o stradă?",
"eticheta": "Linia roșie",
"optiuni": [
"O coadă lungă de mașini",
"Semaforul e roșu pe strada aceea",
"Strada e închisă",
"Nu pot spune"
],
"corect": "O coadă lungă de mașini"
},
{
"id": "r1_real",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"titlu": "Dacă apăsați un buton în aplicație, se schimbă semaforul adevărat din piață?",
"eticheta": "Semaforul adevărat",
"optiuni": [
"Da",
"Nu",
"Nu pot spune"
],
"corect": "Nu"
},
{
"id": "r1_usor",
"tip": "alegere",
"versiune": "m1",
"runda": 0,
"titlu": "Cât de ușor v-a fost să folosiți această variantă?",
"eticheta": "Cât de ușor",
"optiuni": [
"Foarte greu",
"Greu",
"Nici greu, nici ușor",
"Ușor",
"Foarte ușor"
]
},
{
"id": "r1_incurcat",
"tip": "text",
"versiune": "m1",
"runda": 0,
"titlu": "Ce v-a încurcat la această variantă?",
"eticheta": "Ce a încurcat",
"text": [
"Puteți scrie câteva cuvinte sau puteți lăsa gol. Vă rugăm să nu scrieți nume sau lucruri personale."
],
"buton": "Mai departe"
},
{
"id": "r2_deschide",
"tip": "deschide",
"versiune": "m2",
"runda": 1,
"titlu": "Pornim a doua variantă",
"text": [
"Puteți face o pauză, dacă doriți. Urmează aceleași sarcini, pe o altă variantă a aplicației.",
"Situația din piață s-a schimbat, așa că uitați-vă din nou cu atenție.",
"Când sunteți gata, apăsați butonul de mai jos."
],
"buton": "Deschide aplicația",
"sit": {
"runda": 1,
"mod": "manual"
}
},
{
"id": "r2_conduce",
"tip": "sarcina",
"sarcina": 1,
"eticheta": "Sarcina 1, cine schimbă culorile",
"versiune": "m2",
"runda": 1,
"ecran": true,
"text": [
"Uitați-vă la partea din dreapta, fără să apăsați nimic pe ea.",
"**Cine schimbă acum culorile semaforului: un calculator sau un om?**",
"Când ați aflat, apăsați „Am terminat”."
]
},
{
"id": "r2_conduce_r",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Cine schimbă acum culorile semaforului?",
"eticheta": "Cine schimbă culorile",
"optiuni": [
"Un calculator, singur",
"Un om, de la acest ecran",
"Nu pot spune"
],
"corect_din_banc": "conduce"
},
{
"id": "r2_coada",
"tip": "sarcina",
"sarcina": 2,
"eticheta": "Sarcina 2, cea mai lungă coadă",
"versiune": "m2",
"runda": 1,
"ecran": true,
"text": [
"**Pe care stradă așteaptă acum cele mai multe mașini la semafor?**",
"Când ați aflat, apăsați „Am terminat”."
]
},
{
"id": "r2_coada_r",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Pe care stradă așteaptă cele mai multe mașini?",
"eticheta": "Cele mai multe mașini",
"optiuni": [
"Magheru",
"Lascăr Catargiu",
"Dacia est",
"Dacia vest",
"Nu pot spune"
],
"corect": "Magheru"
},
{
"id": "r2_verde",
"tip": "sarcina",
"sarcina": 3,
"eticheta": "Sarcina 3, verde pe Dacia",
"versiune": "m2",
"runda": 1,
"ecran": true,
"verifica": "verde",
"sit": {
"mod": "program",
"nemiscat": true
},
"text": [
"**Dați verde pe Bulevardul Dacia**, ca și cum ați schimba dumneavoastră culorile semaforului.",
"Când credeți că ați reușit, apăsați „Am terminat”."
]
},
{
"id": "r2_verde_r",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Ce culoare avea semaforul pe Bulevardul Magheru când ați apăsat „Am terminat”?",
"eticheta": "Culoarea pe Magheru",
"optiuni": [
"Verde",
"Galben",
"Roșu",
"Nu pot spune"
],
"corect_din_banc": "magheru"
},
{
"id": "r2_verde_vazut",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Ați putut vedea în aplicație dacă s-a schimbat ce ați vrut?",
"eticheta": "A văzut schimbarea",
"optiuni": [
"Da, clar",
"Da, dar nu eram sigur(ă)",
"Nu"
]
},
{
"id": "r2_automat",
"tip": "sarcina",
"sarcina": 4,
"eticheta": "Sarcina 4, înapoi la calculator",
"versiune": "m2",
"runda": 1,
"ecran": true,
"verifica": "automat",
"pregateste": "manual_dacia",
"text": [
"**Lăsați din nou calculatorul să schimbe singur culorile semaforului**, ca să nu mai fie nevoie de dumneavoastră.",
"Când credeți că ați reușit, apăsați „Am terminat”."
]
},
{
"id": "r2_automat_vazut",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Ați putut vedea în aplicație cine schimbă acum culorile?",
"eticheta": "A văzut cine conduce",
"optiuni": [
"Da, clar",
"Da, dar nu eram sigur(ă)",
"Nu"
]
},
{
"id": "r2_inchide",
"tip": "inchide",
"versiune": "m2",
"runda": 1,
"ecran": true,
"acoperit": true,
"titlu": "Închideți aplicația",
"text": [
"Ați terminat sarcinile pe această variantă. Apăsați butonul de mai jos: aplicația din dreapta se închide."
],
"buton": "Închide aplicația"
},
{
"id": "r2_usor",
"tip": "alegere",
"versiune": "m2",
"runda": 1,
"titlu": "Cât de ușor v-a fost să folosiți această variantă?",
"eticheta": "Cât de ușor",
"optiuni": [
"Foarte greu",
"Greu",
"Nici greu, nici ușor",
"Ușor",
"Foarte ușor"
]
},
{
"id": "r2_incurcat",
"tip": "text",
"versiune": "m2",
"runda": 1,
"titlu": "Ce v-a încurcat la această variantă?",
"eticheta": "Ce a încurcat",
"text": [
"Puteți scrie câteva cuvinte sau puteți lăsa gol. Vă rugăm să nu scrieți nume sau lucruri personale."
],
"buton": "Mai departe"
},
{
"id": "preferinta",
"tip": "alegere",
"titlu": "Care variantă v-a fost mai ușoară?",
"eticheta": "Mai ușoară",
"optiuni": [
"Prima",
"A doua",
"La fel"
]
},
{
"id": "vazut_inainte",
"tip": "alegere",
"titlu": "Ați mai văzut aplicația aceasta înainte de azi?",
"eticheta": "Văzut înainte",
"optiuni": [
"Nu",
"Da"
]
},
{
"id": "ajutor",
"tip": "alegere",
"titlu": "V-a ajutat cineva la sarcini?",
"eticheta": "A ajutat cineva",
"optiuni": [
"Nu",
"Doar la mouse sau la citit",
"Da, la înțelegerea sarcinilor"
]
},
{
"id": "final",
"tip": "final"
}
]
};
