@echo off
rem Borna M3 (15.11.2026): porneste DOAR dispeceratul si geamanul (fara --gui), in file numite ale Windows Terminal,
rem apoi, cand raspunde dispeceratul, o fereastra noua de Chrome: fila 1 = prezentarea, incadrata in pagina; fila 2 = dispeceratul,
rem cu imaginea camerei ascunsa (?imagine=0): in locul ei sta panoul "Starea senzorului". Adresa e 127.0.0.1, ca serverul.
rem Colectarea camerei merge deja separat (paznicul): NU porniti PORNESTE_TOT.bat, care ar porni o a doua colectare.
rem Se porneste doar ce lipseste: dispeceratul, daca nu raspunde; geamanul, daca lacatul lui (outputs\live\geaman.lock)
rem e liber. Daca amandoua ruleaza deja, se deschide doar Chrome.
rem Proba fara Chrome:  scripts\M3_demonstratie.bat proba   (porneste ce lipseste si spune adresa, fara nicio fereastra de
rem Chrome; iese cu codul 1 daca dispeceratul nu raspunde in 90 s).
rem Oprirea: in fila "Geaman", apoi in fila "Dispecerat", Ctrl+C (fara text selectat); apoi se inchide fereastra.
rem Daca o fila s-a oprit, in ea se poate scrie din nou comanda ei (mediul ramane setat in fila).
setlocal
for %%I in ("%~dp0..") do set "RAD=%%~fI"
set "ADRESA=http://127.0.0.1:8050/?imagine=0"
set "PDF=%USERPROFILE%\Desktop\Prezentare_M3.pdf"
if not exist "%PDF%" set "PDF=%RAD%\outputs\prezentare\surse_m3\Prezentare_M3.pdf"
if not exist "%PDF%" echo Atentie: lipseste Prezentare_M3.pdf (nici pe Desktop, nici in outputs\prezentare\surse_m3): prima fila din Chrome va fi goala.
set "PDF=%PDF:\=/%"
rem Lacatul geamanului, ca in live_twin.ia_lacatul: cod 0 = liber (niciun geaman), cod 3 = il tine deja un geaman.
rem Orice alt cod (de ex. o eroare la import) porneste totusi geamanul: el insusi refuza sa ruleze de doua ori.
set "PYTHONPATH=%RAD%\src"
"%RAD%\.venv\Scripts\python.exe" -c "import sys; from romana.bridge.live_twin import ia_lacatul; sys.exit(0 if ia_lacatul() else 3)"
set "LACAT=%ERRORLEVEL%"
curl -s -o nul http://127.0.0.1:8050/
if errorlevel 1 goto porneste
if "%LACAT%"=="3" goto deschide
echo Dispeceratul ruleaza deja, geamanul nu: pornesc doar geamanul.
wt -w new nt --title "Geaman" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.bridge.live_twin"
goto deschide
:porneste
if "%LACAT%"=="3" goto doar_dispecerat
wt -w new nt --title "Dispecerat" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.dashboard.server" ; nt --title "Geaman" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.bridge.live_twin"
goto asteapta
:doar_dispecerat
echo Un geaman ruleaza deja: pornesc doar dispeceratul.
wt -w new nt --title "Dispecerat" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.dashboard.server"
:asteapta
for /l %%N in (1,1,45) do (
  curl -s -o nul http://127.0.0.1:8050/ && goto deschide
  ping -n 3 127.0.0.1 >nul
)
echo Dispeceratul nu raspunde dupa 90 s: vedeti fila "Dispecerat". Pagina incearca singura din nou, la fiecare secunda.
if /i "%~1"=="proba" exit /b 1
:deschide
if /i "%~1"=="proba" (
  echo Proba: dispeceratul e la %ADRESA% ; Chrome nu se deschide.
  goto :eof
)
start "" chrome --new-window "file:///%PDF%#view=Fit" "%ADRESA%"
