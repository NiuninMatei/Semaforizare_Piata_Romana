@echo off
rem Analiza live a camerei Piata Romana (q in fereastra = oprire). Parametri extra: --device 0 pentru GPU
call "%~dp0_mediu.bat"
python -m romana.vision.run_vision --show %*
pause
