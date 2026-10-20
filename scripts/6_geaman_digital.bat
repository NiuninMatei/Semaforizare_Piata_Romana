@echo off
rem SUMO-GUI alimentat live de camera, semafor condus de AI (mod schimbabil din dashboard)
call "%~dp0_mediu.bat"
python -m romana.bridge.live_twin --gui %*
pause
