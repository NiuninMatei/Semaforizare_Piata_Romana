@echo off
rem Configurare comuna: mediul virtual si calea catre cod
set "RADACINA=%~dp0.."
set "PYTHONPATH=%RADACINA%\src"
set "PYTHONIOENCODING=utf-8"
if exist "%RADACINA%\.venv\Scripts\activate.bat" call "%RADACINA%\.venv\Scripts\activate.bat"
cd /d "%RADACINA%"
