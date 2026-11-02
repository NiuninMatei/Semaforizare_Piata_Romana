@echo off
rem Demonstratie (~4 min): aceeasi ora de trafic real cu planul de referinta, planul observat, Presiune maxima si agentul IA
rem Fara parametri: varful din 26.10, 5 seed-uri. Ex.: 9_demo_comparatie.bat --scenariu sumo\scenarios\cor_zi_2026-11-01_varf.sumocfg
call "%~dp0_mediu.bat"
python -m romana.control.demo %*
pause
