"""
Проверка доступа к Google Drive с текущими локальными настройками проекта.

Использует:
  - config/google_settings.json (client_secret_path, parent_folder_id; опционально google_token_path)
  - pickle по пути из настроек или data/google_token.pickle (дефолт: GOOGLE_TOKEN_PATH в .env)

Запуск из корня репозитория мини-CRM:
  PYTHONPATH=. python scripts/check_google_drive.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import _project_root  # noqa: E402
from backend.google_settings_store import (  # noqa: E402
    resolved_google_token_path,
    settings_path as google_settings_json_path,
)
from google_integration.google_drive import list_files_in_folder  # noqa: E402
from google_integration.oauth_service import (  # noqa: E402
    credentials_valid,
    drive_service_from_creds,
    load_credentials,
)


def main() -> int:
    os.chdir(ROOT)
    settings_file = google_settings_json_path()
    token_rel = resolved_google_token_path()
    token_path = Path(token_rel) if Path(token_rel).is_absolute() else _project_root() / token_rel

    print(f"[1] Корень проекта: {_project_root()}")
    print(f"[2] Файл настроек Google: {settings_file} {'есть' if settings_file.exists() else 'нет'}")

    if not settings_file.exists():
        print("\n[WARN] Нет config/google_settings.json — сохраните настройки в UI или создайте файл вручную.")
        return 2

    raw = json.loads(settings_file.read_text(encoding="utf-8"))
    secret_rel = raw.get("client_secret_path")
    folder_id = raw.get("parent_folder_id")

    print(f"[3] client_secret_path в настройках: {secret_rel!r}")
    print(f"[4] parent_folder_id в настройках: {(folder_id[:12] + '…') if folder_id and len(folder_id) > 12 else folder_id!r}")

    if not secret_rel:
        print("\n[WARN] Не указан client_secret_path.")
        return 2
    secret = Path(secret_rel)
    if not secret.is_absolute():
        secret = _project_root() / secret
    if not secret.exists():
        print(f"\n[WARN] Файл client secret не найден: {secret}")
        return 2

    print(f"[5] Токен пользователя: {token_path} {'есть' if token_path.exists() else 'нет'}")
    if not token_path.exists():
        print("\n[WARN] Нет сохранённого OAuth-токена (pickle). Выполните «Войти через Google» в интерфейсе.")
        return 3

    creds = load_credentials(_project_root(), secret_rel, token_rel)
    if not credentials_valid(creds):
        print("\n[WARN] Токен недействителен или не удалось обновить. Пройдите авторизацию снова.")
        return 3

    try:
        if folder_id:
            files = list_files_in_folder(creds, folder_id, page_size=5)
            print(f"\n[OK] Доступ к Google Drive есть. Файлов в указанной папке (первые до 5): {len(files)}")
            for f in files:
                nm = f.get("name", "")
                fid = f.get("id", "")
                print(f"    - {nm} ({fid})")
        else:
            drv = drive_service_from_creds(creds)
            drv.files().list(pageSize=1, fields="files(id,name)").execute()
            print("\n[OK] Доступ к Google Drive есть (тестовый list без папки).")
            print("    Укажите parent_folder_id в настройках, чтобы проверить именно вашу папку отчётов.")
            return 0
    except Exception as e:
        print(f"\n[ERR] Запрос к Drive API завершился ошибкой: {e}")
        print("Проверьте: включён ли Drive API, не истёк ли refresh token, добавлен ли redirect URI как в README.")
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
