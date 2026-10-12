@echo off
cd /d "%~dp0"
python -m autoplay run "sequences\example.json"
if errorlevel 1 pause