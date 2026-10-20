@echo off
call "%~dp0_mediu.bat"
python -m romana.network.build_network
pause
