@echo off
rem Antrenarea agentului PPO; adaugati --coridor pentru a controla si cele 5 intersectii vecine
call "%~dp0_mediu.bat"
python -m romana.control.train %*
pause
