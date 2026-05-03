@echo off

chcp 65001 >nul

cd /d "%~dp0"

echo Запуск синхронизации...

python -u main.py sync

echo.

pause

