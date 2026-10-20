@echo off
rem Redesenarea zonelor de intrare/iesire daca s-a miscat camera
call "%~dp0_mediu.bat"
python -m romana.vision.calibrate_zones
pause
