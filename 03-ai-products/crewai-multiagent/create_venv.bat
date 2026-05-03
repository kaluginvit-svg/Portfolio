@echo off
chcp 65001 >nul
echo Creating Python venv...
python -m venv venv
if %errorlevel% equ 0 (
    echo.
    echo venv created in folder: venv
    echo.
    echo To activate: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    echo.
) else (
    echo Error. Check that Python is installed and in PATH.
)
pause
