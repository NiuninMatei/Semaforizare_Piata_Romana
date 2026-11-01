@echo off
rem Sondarea dispeceratului cu oameni: deschide ghidul in browser; raspunsurile se salveaza in outputs\sondare.
rem Nu atinge colectarea si nici geamanul digital. Rezultate: python -m romana.dashboard.sondare --rezumat
call "%~dp0_mediu.bat"
python -m romana.dashboard.sondare %*
pause
