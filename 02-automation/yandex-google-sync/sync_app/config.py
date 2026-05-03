"""Load settings from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Project root (directory containing main.py), for default google_token.json
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_google_oauth_token_path(env_value: str | None) -> Path | None:
    """
    GOOGLE_OAUTH_TOKEN_JSON: absolute or relative to project root.
    If unset, use <project_root>/google_token.json when that file exists.
    """
    raw = (env_value or "").strip()
    if raw:
        p = Path(raw)
        resolved = p.resolve() if p.is_absolute() else (_PROJECT_ROOT / p).resolve()
        return resolved
    candidate = _PROJECT_ROOT / "google_token.json"
    return candidate if candidate.is_file() else None


def _i(name: str, default: int, *, min_v: int = 1, max_v: int = 32) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(min_v, min(max_v, int(raw)))
    except ValueError:
        return default


def _b(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off", ""):
        return default
    return default


@dataclass
class Settings:
    state_dir: Path
    yandex_client_id: str
    yandex_client_secret: str
    # YANDEX_REDIRECT_URI: match OAuth app; else yandex-login uses http://127.0.0.1:{port}/
    yandex_redirect_uri: str | None
    # YANDEX_TOKEN_PATH or default SYNC_STATE_DIR/yandex_token.json
    yandex_token_path: Path
    # Права OAuth для Диска (должны быть включены у приложения на oauth.yandex.ru)
    yandex_oauth_scope: str
    # Эндпоинты OAuth (при invalid_scope попробуйте YANDEX_OAUTH_USE_RU=1)
    yandex_oauth_authorize_url: str
    yandex_oauth_token_url: str
    yandex_sync_path: str
    google_sync_folder_id: str
    google_oauth_client_secrets_file: Path | None
    google_service_account_file: Path | None
    # GOOGLE_OAUTH_TOKEN_JSON: ready token.json (user credentials)
    google_oauth_token_json: Path | None
    google_use_shared_drive: bool
    conflict_policy: str  # lww | branch | manual
    sync_deletions: bool
    full_scan_google_each_run: bool
    # Передача нескольких файлов одновременно (отдельный HTTP-клиент на поток).
    sync_parallel_workers: int

    @classmethod
    def from_env(cls) -> Settings:
        state = Path(os.environ.get("SYNC_STATE_DIR", ".sync_state")).resolve()
        secrets = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS")
        sa = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        gtok = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
        google_tok_path = _resolve_google_oauth_token_path(gtok)
        y_redirect = os.environ.get("YANDEX_REDIRECT_URI", "").strip()
        y_tok = os.environ.get("YANDEX_TOKEN_PATH", "").strip()
        yandex_token_path = Path(y_tok).resolve() if y_tok else (state / "yandex_token.json")
        # Два scope — как две галочки в консоли («чтение всего Диска» + «запись»)
        y_scope = os.environ.get("YANDEX_OAUTH_SCOPE", "").strip()
        if not y_scope:
            y_scope = "cloud_api:disk.read cloud_api:disk.write"
        use_ru = _b("YANDEX_OAUTH_USE_RU")
        auth_u = os.environ.get("YANDEX_OAUTH_AUTHORIZE_URL", "").strip()
        tok_u = os.environ.get("YANDEX_OAUTH_TOKEN_URL", "").strip()
        if not auth_u:
            auth_u = (
                "https://oauth.yandex.ru/authorize"
                if use_ru
                else "https://oauth.yandex.com/authorize"
            )
        if not tok_u:
            tok_u = (
                "https://oauth.yandex.ru/token"
                if use_ru
                else "https://oauth.yandex.com/token"
            )
        return cls(
            state_dir=state,
            yandex_client_id=os.environ.get("YANDEX_CLIENT_ID", "").strip(),
            yandex_client_secret=os.environ.get("YANDEX_CLIENT_SECRET", "").strip(),
            yandex_redirect_uri=y_redirect or None,
            yandex_token_path=yandex_token_path,
            yandex_oauth_scope=y_scope,
            yandex_oauth_authorize_url=auth_u,
            yandex_oauth_token_url=tok_u,
            yandex_sync_path=os.environ.get("YANDEX_SYNC_PATH", "/sync").strip(),
            google_sync_folder_id=os.environ.get("GOOGLE_SYNC_FOLDER_ID", "").strip(),
            google_oauth_client_secrets_file=Path(secrets).resolve() if secrets else None,
            google_service_account_file=Path(sa).resolve() if sa else None,
            google_oauth_token_json=google_tok_path,
            google_use_shared_drive=_b("GOOGLE_SHARED_DRIVE"),
            conflict_policy=os.environ.get("SYNC_CONFLICT_POLICY", "lww").strip().lower(),
            sync_deletions=_b("SYNC_DELETIONS"),
            full_scan_google_each_run=_b("GOOGLE_FULL_SCAN_EACH_RUN"),
            sync_parallel_workers=_i("SYNC_PARALLEL_WORKERS", 1, min_v=1, max_v=32),
        )
