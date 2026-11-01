@echo off
rem Configurare comuna: mediul virtual si calea catre cod
set "RADACINA=%~dp0.."
set "PYTHONPATH=%RADACINA%\src"
set "PYTHONIOENCODING=utf-8"
if exist "%RADACINA%\.venv\Scripts\activate.bat" call "%RADACINA%\.venv\Scripts\activate.bat"
rem Node.js sta doar in mediul proiectului: pentru testele logicii sondarii
if exist "%RADACINA%\.venv\nodejs\node.exe" set "PATH=%RADACINA%\.venv\nodejs;%PATH%"
cd /d "%RADACINA%"
