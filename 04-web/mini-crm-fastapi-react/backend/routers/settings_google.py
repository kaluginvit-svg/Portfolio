from pathlib import Path

from fastapi import APIRouter

from backend.config import _project_root
from backend.google_settings_store import (
    read_google_settings,
    resolved_google_token_path,
    write_google_settings,
)
from backend.schemas import GoogleSettings, GoogleSettingsRead
from google_integration.oauth_service import credentials_valid, load_credentials

router = APIRouter(prefix="/settings", tags=["settings"])


def _normalize_user_path(s: str) -> str:
    """Пробелы, кавычки; слэши как в POSIX (Windows-пути не ломают Docker/Linux)."""
    return s.strip().strip('"').strip("'").replace("\\", "/")


@router.get("/google", response_model=GoogleSettingsRead)
def get_google_settings():
    raw = read_google_settings()
    secret = raw.get("client_secret_path")
    folder = raw.get("parent_folder_id")
    tok = raw.get("google_token_path")
    has_token = False
    token_rel = resolved_google_token_path()
    if secret:
        p = Path(_normalize_user_path(secret))
        if not p.is_absolute():
            p = _project_root() / p
        if p.exists():
            creds = load_credentials(_project_root(), secret, token_rel)
            has_token = credentials_valid(creds)
    return GoogleSettingsRead(
        client_secret_path=secret,
        parent_folder_id=folder,
        google_token_path=tok if isinstance(tok, str) and tok.strip() else None,
        has_valid_token_guess=has_token,
    )


@router.put("/google", response_model=GoogleSettingsRead)
def put_google_settings(body: GoogleSettings):
    # Validate client secret file exists
    raw_secret = _normalize_user_path(body.client_secret_path)
    p = Path(raw_secret)
    if not p.is_absolute():
        p = _project_root() / p
    if not p.exists():
        from backend.exceptions import AppException

        root = _project_root()
        raise AppException(
            "invalid_config",
            "Файл client_secret JSON не найден по указанному пути",
            detail=(
                f"{p} — укажите путь от корня репозитория мини-CRM, например data/client_secret.json; "
                f"при Docker файл должен лежать в смонтированной папке data/, google_integration/ или config/. "
                f"Корень для проверки: {root}"
            ),
            status=422,
        )
    root = _project_root()
    try:
        rel = p.relative_to(root).as_posix()
    except ValueError:
        rel = str(p)
    payload = read_google_settings()
    payload["client_secret_path"] = rel
    payload["parent_folder_id"] = body.parent_folder_id.strip()
    if body.google_token_path and body.google_token_path.strip():
        payload["google_token_path"] = _normalize_user_path(body.google_token_path)
    else:
        payload.pop("google_token_path", None)
    write_google_settings(payload)
    return get_google_settings()
