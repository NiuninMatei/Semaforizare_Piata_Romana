@echo off
rem Paznicul colectarii langa analiza live pornita fara fereastra: reporneste run_vision daca procesul moare sau ramane
rem fara cadre (doar daca playlistul camerei raspunde). Oprire anuntata: fisierul outputs\live\fara_repornire.
rem Urme in outputs\logs: paznic_ZI.log si reporniri_ZI.csv.
rem Exemple: 2e_paznic.bat --proba      2e_paznic.bat --pana-la "2026-11-08 09:00"
call "%~dp0_mediu.bat"
python -m romana.vision.paznic %*
pause
