@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Create venv first.
  exit /b 1
)
set "LOG=%~dp0fetch_bankrot_trades_table.log"

rem Диапазон дат в этом файле: DD.MM.YYYY (как у Python: --from / --to).
rem Оставьте обе строки пустыми — скрипт запустится без --from/--to.
rem Либо задайте период аргументами (имеет приоритет):
rem   script.bat 01.04.2026 04.04.2026
rem Режим первой опцией:
rem   script.bat wide 01.04.2026 04.04.2026   (широкая БД: отдельная колонка на каждое найденное поле)
rem   script.bat slim 01.04.2026 04.04.2026   (компактная БД: фиксированные колонки)
rem Карточки на fedresurs.ru/bankruptmessages/{GUID}. Старый портал: set FEDRESURS_CARD_OLD_PORTAL=1
rem БД --table: компактная схема (фиксированные колонки), по строке на каждый распознанный лот.
rem БД --table-wide: широкая схема (каждое найденное поле/значение → отдельная колонка), строка на лот.
set "DATE_FROM="
set "DATE_TO="

set "MODE=slim"
if /i "%~1"=="wide" ( set "MODE=wide" & shift )
if /i "%~1"=="slim" ( set "MODE=slim" & shift )

set "TABLE_FLAG=--table"
if /i "%MODE%"=="wide" set "TABLE_FLAG=--table-wide"

if not "%~1"=="" (
  if "%~2"=="" (
    venv\Scripts\python.exe -u fetch_bankrot_trades.py --manual-type %TABLE_FLAG% --from "%~1" --to "%~1" --log-file "%LOG%"
  ) else (
    venv\Scripts\python.exe -u fetch_bankrot_trades.py --manual-type %TABLE_FLAG% --from "%~1" --to "%~2" --log-file "%LOG%"
  )
  goto :done
)

if not "%DATE_FROM%"=="" (
  if not "%DATE_TO%"=="" (
    venv\Scripts\python.exe -u fetch_bankrot_trades.py --manual-type %TABLE_FLAG% --from "%DATE_FROM%" --to "%DATE_TO%" --log-file "%LOG%"
  ) else (
    venv\Scripts\python.exe -u fetch_bankrot_trades.py --manual-type %TABLE_FLAG% --from "%DATE_FROM%" --to "%DATE_FROM%" --log-file "%LOG%"
  )
  goto :done
)

venv\Scripts\python.exe -u fetch_bankrot_trades.py --manual-type %TABLE_FLAG% --log-file "%LOG%"

:done
pause
