@echo off
rem Exemplu: 3_genereaza_cerere.bat --nume dimineata --de-la "2026-10-21 07:30" --pana-la "2026-10-21 08:30"
call "%~dp0_mediu.bat"
if "%~1"=="" (python -m romana.bridge.build_demand --profil referinta --nume referinta_varf) else (python -m romana.bridge.build_demand %*)
pause
