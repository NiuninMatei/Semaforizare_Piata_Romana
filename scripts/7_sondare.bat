@echo off
rem Sondarea dispeceratului cu oameni: pagina din docs\sondare, pe acest calculator, pentru probe.
rem Pagina adevarata e pe GitHub Pages. Linkuri: --linkuri  Rezultate: --rezumat, --publica. Nu atinge colectarea si nici geamanul digital.
call "%~dp0_mediu.bat"
python -m romana.dashboard.sondare --local %*
pause
