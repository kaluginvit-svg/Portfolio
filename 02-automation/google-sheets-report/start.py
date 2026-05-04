"""
Минимальный пример: чтение и запись диапазона через JSON сервисного аккаунта.

Переменные окружения (необязательно):
  GOOGLE_SERVICE_ACCOUNT_JSON — явный путь к ключу;
    иначе рядом со скриптом ищется service_account.json или *.json с type=service_account
  GOOGLE_SPREADSHEET_ID — ID таблицы или GOOGLE_SPREADSHEET_URL — полный URL
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google_sheets import resolve_service_account_json, spreadsheet_id_from_url_or_id

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

BASE = Path(__file__).resolve().parent
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
_sheet_raw = (
    os.environ.get("GOOGLE_SPREADSHEET_URL", "").strip()
    or os.environ.get("GOOGLE_SPREADSHEET_ID", "").strip()
)
SPREADSHEET_ID = spreadsheet_id_from_url_or_id(_sheet_raw) if _sheet_raw else ""

READ_RANGE = "Лист1!A1:CI1000"
WRITE_RANGE = "Лист1!A1:CI1000"


def get_service():
    if SERVICE_ACCOUNT_JSON:
        path = Path(SERVICE_ACCOUNT_JSON).expanduser()
    else:
        found = resolve_service_account_json(BASE)
        path = found if found else BASE / "service_account.json"
    if not path.is_file():
        print(
            f"Нет файла ключа: {path}\n"
            "Положите JSON сервисного аккаунта в эту папку (как скачали из GCP, "
            "или переименуйте в service_account.json) либо задайте GOOGLE_SERVICE_ACCOUNT_JSON.",
            file=sys.stderr,
        )
        sys.exit(1)
    creds = Credentials.from_service_account_file(str(path), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_sheet(service):
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=READ_RANGE)
        .execute()
    )
    values = result.get("values", [])
    print("READ RESULT:")
    for row in values:
        print(row)


def write_sheet(service):
    body = {
        "values": [
            ["name", "age", "city"],
            ["Alice", "25", "Amsterdam"],
            ["Bob", "30", "Berlin"],
        ]
    }
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=SPREADSHEET_ID,
            range=WRITE_RANGE,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    print(f'Updated cells: {result.get("updatedCells")}')


def main():
    if not SPREADSHEET_ID:
        print(
            "Задайте таблицу: GOOGLE_SPREADSHEET_URL или GOOGLE_SPREADSHEET_ID "
            "(или отредактируйте start.py локально — не коммитьте свой ID в общий доступ).",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        service = get_service()
        read_sheet(service)
        write_sheet(service)
    except HttpError as err:
        print(f"Google API error: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()
