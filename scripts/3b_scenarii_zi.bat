@echo off
rem Construieste automat scenariile SUMO ale unei zile de date reale (varf, pranz, linistit + sensibilitati).
rem Exemplu: 3b_scenarii_zi.bat --zi 2026-10-21
call "%~dp0_mediu.bat"
python -m romana.bridge.scenarii_zi %*
pause
