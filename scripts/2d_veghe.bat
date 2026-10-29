@echo off
rem Veghea fluxului de cadre langa analiza live (2_viziune_live.bat): se opreste cu ALERTA si un diagnostic in
rem outputs\logs\veghe_alerta_*.json la primul semn de problema (rata cadrelor, imagine inghetata, jurnal oprit).
rem Exemple: 2d_veghe.bat      2d_veghe.bat --pana-la "2026-10-30 09:05"
call "%~dp0_mediu.bat"
python -m romana.vision.veghe %*
pause
