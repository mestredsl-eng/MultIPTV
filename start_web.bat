@echo off
cd /d "%~dp0"
python -m flask --app app.app run --host=0.0.0.0 --port=5000
pause
