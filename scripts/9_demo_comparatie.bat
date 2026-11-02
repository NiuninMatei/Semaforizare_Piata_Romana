@echo off
rem Demonstratie (~4 min): aceeasi ora de trafic real cu planul de referinta, planul ales 12/14/12, Presiune maxima si agentul IA
rem Fara parametri: pranzul din 26.10, 5 seed-uri. Ex.: 9_demo_comparatie.bat --scenariu sumo\scenarios\zi_2026-10-26_varf.sumocfg
call "%~dp0_mediu.bat"
python -m romana.control.demo %*
pause
