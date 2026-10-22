@echo off
rem Demonstratie (~2,5 min): aceeasi ora de trafic real cu planul fix actual, Max-Pressure si agentul AI
rem Fara parametri: pranzul din 21.10, 5 seed-uri. Ex.: 9_demo_comparatie.bat --scenariu sumo\scenarios\zi_2026-10-21_varf.sumocfg
call "%~dp0_mediu.bat"
python -m romana.control.demo %*
pause
