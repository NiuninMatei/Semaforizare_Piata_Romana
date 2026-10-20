@echo off
call "%~dp0_mediu.bat"
start "" http://localhost:8050
python -m romana.dashboard.server
pause
