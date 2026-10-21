@echo off
rem Renumara traficul din jurnalul anonim de traiectorii (data\trajectories), cu zonele curente din config\camera.json.
rem Exemple: 2c_renumarare.bat --zi 2026-10-21      2c_renumarare.bat --zi 2026-10-21 --directii
call "%~dp0_mediu.bat"
python -m romana.vision.recount %*
pause
