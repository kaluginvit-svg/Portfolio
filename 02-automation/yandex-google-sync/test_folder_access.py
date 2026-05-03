#!/usr/bin/env python3
"""Проверка доступа к корневым папкам Яндекс.Диск и Google Drive (без синхронизации)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _load_dotenv() -> None:
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _p(*a, **kw) -> None:
    kw.setdefault("flush", True)
    print(*a, **kw)


def main() -> int:
    _load_dotenv()
    from sync_app.config import Settings
    from sync_app.google_auth import get_credentials
    from sync_app.google_client import GoogleDriveClient
    from sync_app.yandex_client import YandexDiskClient

    s = Settings.from_env()
    ok_all = True

    # --- Yandex ---
    _p("=== Яндекс.Диск ===")
    _p(f"Путь синхронизации: {s.yandex_sync_path!r}")
    token_exists = s.yandex_token_path.is_file()
    _p(f"Файл токена: {s.yandex_token_path} ({'есть' if token_exists else 'НЕТ'})")
    if not token_exists:
        _p("FAIL: нет yandex_token.json — выполните: python main.py yandex-login")
        ok_all = False
    else:
        try:
            ya = YandexDiskClient(
                s.yandex_client_id,
                s.yandex_client_secret,
                s.yandex_token_path,
                oauth_token_url=s.yandex_oauth_token_url,
            )
            meta = ya.get_meta(s.yandex_sync_path.rstrip("/") or "/")
            name = meta.get("name", "?")
            typ = meta.get("type", "?")
            _p(f"OK: ресурс доступен, имя={name!r}, тип={typ!r}")
            data = ya.list_dir(s.yandex_sync_path.rstrip("/") or "/", limit=20, offset=0)
            emb = (data.get("_embedded") or {}).get("items") or []
            _p(f"    элементов в первой странице списка: {len(emb)}")
        except Exception as e:
            _p(f"FAIL: {type(e).__name__}: {e}")
            ok_all = False

    _p()

    # --- Google ---
    _p("=== Google Drive ===")
    fid = (s.google_sync_folder_id or "").strip()
    if not fid:
        _p("FAIL: GOOGLE_SYNC_FOLDER_ID пустой в .env — укажите ID папки из URL Drive.")
        ok_all = False
    else:
        _p(f"Папка (fileId): {fid[:12]}...")
        try:
            creds = get_credentials(
                service_account_json=s.google_service_account_file,
                oauth_token_json=s.google_oauth_token_json,
                oauth_client_secrets=s.google_oauth_client_secrets_file,
                oauth_token_path=s.state_dir / "google_token.json",
            )
            drive = GoogleDriveClient(creds, shared_drive=s.google_use_shared_drive)
            g = drive.service.files().get(
                fileId=fid,
                fields="id, name, mimeType, capabilities",
                supportsAllDrives=s.google_use_shared_drive,
            ).execute()
            _p(f"OK: папка доступна, имя={g.get('name')!r}, mime={g.get('mimeType')!r}")
            resp = (
                drive.service.files()
                .list(
                    q=f"'{fid}' in parents and trashed = false",
                    pageSize=10,
                    fields="files(id, name)",
                    supportsAllDrives=s.google_use_shared_drive,
                    includeItemsFromAllDrives=s.google_use_shared_drive,
                )
                .execute()
            )
            n = len(resp.get("files", []))
            _p(f"    дочерних объектов (первая страница): {n}")
        except Exception as e:
            _p(f"FAIL: {type(e).__name__}: {e}")
            ok_all = False

    _p()
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
