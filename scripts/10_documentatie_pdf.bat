@echo off
rem Exporta documentatia (docs\DOCUMENTATIE.md) in PDF cu pagini numerotate: docs\DOCUMENTATIE.pdf
call "%~dp0_mediu.bat"
python -m romana.doc_pdf
pause
