@echo off
rem Renumara traficul din jurnalul de traiectorii (local: data\trajectories_brute; altfel data\trajectories, publicat: doar vehiculele, pseudonimizat), cu zonele curente din config\camera.json.
rem Fara jurnalul local, folositi --out cu alt director, ca pietonii din data\counts sa nu se piarda.
rem Exemple: 2c_renumarare.bat --zi 2026-10-21      2c_renumarare.bat --zi 2026-10-21 --directii
call "%~dp0_mediu.bat"
python -m romana.vision.recount %*
pause
