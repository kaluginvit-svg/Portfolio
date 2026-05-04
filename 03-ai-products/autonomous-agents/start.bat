@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Запуск SEO-агента (бэкенд + фронтенд)...
docker compose -p seo-agent up -d

if errorlevel 1 (
    echo Ошибка запуска. Проверьте, что Docker запущен и вы в корне проекта.
    pause
    exit /b 1
)

echo Ожидание старта сервиса...
timeout /t 3 /nobreak >nul

start "" "http://localhost:8000"
echo Готово. Откройте http://localhost:8000 в браузере.
pause
