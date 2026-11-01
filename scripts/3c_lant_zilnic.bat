@echo off
rem Lantul zilnic de prelucrare al unei zile colectate: verificarea jurnalului, calitatea, renumararea, scenariile, testul pe seed-urile 1-10 (11-15 pe ziua de validare; zilele de test si de generalizare doar cu --desigileaza), analizele si decizia.
rem Fara --zi, ziua de ieri. --uscat doar afiseaza comenzile; --reia sare peste pasii incheiati (dupa o repornire); --bucla ruleaza noapte de noapte.
rem Cu --bucla --reia, la pornire reia si noptile pierdute, de la prima zi a buclei (outputs\lant\bucla.json sau --de-la AAAA-LL-ZZ).
rem Exemple: 3c_lant_zilnic.bat --uscat --zi 2026-11-01 --exclude 08:00-09:15      3c_lant_zilnic.bat --zi 2026-11-01 --reia
rem          3c_lant_zilnic.bat --bucla --reia --ora 00:15 --pana-la "2026-11-08 12:00"
call "%~dp0_mediu.bat"
python -m romana.lant_zilnic %*
pause
