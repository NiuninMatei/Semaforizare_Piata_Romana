@echo off
call "%~dp0_mediu.bat"
python -m romana.control.evaluate --seeds 5 %*
pause
