@echo off
rem Porneste sistemul complet: viziune live + geaman digital SUMO-GUI + dashboard
start "Viziune - Piata Romana" cmd /k ""%~dp02_viziune_live.bat""
timeout /t 8 >nul
start "Geaman digital SUMO" cmd /k ""%~dp06_geaman_digital.bat""
timeout /t 4 >nul
start "Dashboard" cmd /k ""%~dp07_dashboard.bat""
