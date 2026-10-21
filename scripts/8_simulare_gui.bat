@echo off
rem Deschide in SUMO-GUI un scenariu calibrat, cu agentul AI la semaforul Pietei Romane
call "%~dp0_mediu.bat"
set "SCEN=%~1"
if "%SCEN%"=="" set "SCEN=sumo\scenarios\zi_2026-10-21_varf.sumocfg"
python -m romana.control.run_gui --scenariu "%SCEN%" %2 %3 %4
pause
