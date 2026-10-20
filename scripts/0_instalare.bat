@echo off
rem Creeaza mediul virtual Python si instaleaza dependintele (o singura data)
cd /d "%~dp0.."
py -3 -m venv .venv || python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Instalare terminata. Daca aveti placa video NVIDIA, instalati PyTorch cu CUDA de pe https://pytorch.org pentru o viziune mai rapida.
pause
