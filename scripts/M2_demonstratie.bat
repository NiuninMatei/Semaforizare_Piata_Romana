@echo off
rem Borna M2 (8.11.2026): porneste DOAR dispeceratul si geamanul (fara --gui), in doua file numite ale Windows Terminal,
rem apoi, cand raspunde dispeceratul, o fereastra noua de Chrome: fila 1 = prezentarea, incadrata in pagina; fila 2 = dispeceratul.
rem Colectarea camerei merge deja separat (paznicul): NU porniti PORNESTE_TOT.bat, care ar porni o a doua colectare.
rem Daca dispeceratul raspunde deja (lansatorul a mai fost pornit), nu se mai porneste nimic a doua oara: se deschide doar Chrome.
rem Oprirea: in fila "Geaman", apoi in fila "Dispecerat", Ctrl+C (fara text selectat); apoi se inchide fereastra.
rem Daca o fila s-a oprit, in ea se poate scrie din nou comanda ei (mediul ramane setat in fila).
for %%I in ("%~dp0..") do set "RAD=%%~fI"
set "PDF=%USERPROFILE%\Desktop\Prezentare_M2.pdf"
if not exist "%PDF%" set "PDF=%RAD%\outputs\prezentare\surse_m2\Prezentare_M2.pdf"
set "PDF=%PDF:\=/%"
curl -s -o nul http://127.0.0.1:8050/ && goto deschide
wt -w new nt --title "Dispecerat" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.dashboard.server" ; nt --title "Geaman" --suppressApplicationTitle -d "%RAD%" cmd /k "scripts\_mediu.bat && python -m romana.bridge.live_twin"
for /l %%N in (1,1,45) do (
  curl -s -o nul http://127.0.0.1:8050/ && goto deschide
  ping -n 3 127.0.0.1 >nul
)
:deschide
start "" chrome --new-window "file:///%PDF%#view=Fit" "http://localhost:8050/"
