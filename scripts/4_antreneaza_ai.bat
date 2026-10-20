@echo off
rem Antrenarea agentului PPO; adaugati --coridor pentru a controla si cele 5 intersectii vecine,
rem --medii N pentru N simulari in paralel (implicit 6), --pasi N pentru durata antrenarii
call "%~dp0_mediu.bat"
python -m romana.control.train %*
pause
