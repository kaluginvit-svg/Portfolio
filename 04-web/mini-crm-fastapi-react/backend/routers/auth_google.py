import logging

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from backend.config import _project_root, settings
from backend.google_settings_store import resolved_google_token_path
from backend.exceptions import AppException
from backend.google_settings_store import read_google_settings
from google_integration.oauth_service import build_auth_url, exchange_code

log = logging.getLogger("crm.api.auth")

router = APIRouter(tags=["auth"])


def _frontend_redirect() -> str:
    parts = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
    return parts[0] if parts else "http://localhost:5173"


@router.get("/auth/google/url")
def google_auth_url():
    raw = read_google_settings()
    secret = raw.get("client_secret_path")
    if not secret:
        raise AppException(
            "google_not_configured",
            "Сначала сохраните путь к client_secret и ID папки в настройках",
            status=400,
        )
    try:
        url = build_auth_url(
            _project_root(),
            secret,
            settings.google_redirect_uri,
        )
    except FileNotFoundError as e:
        raise AppException("invalid_config", str(e), status=422) from e
    return {"authorization_url": url}


@router.get("/auth/google/callback")
def google_callback(code: str | None = None, error: str | None = None):
    fe = _frontend_redirect()
    if error:
        log.warning("[auth] OAuth error from provider: %s", error)
        return RedirectResponse(f"{fe}/settings?google=error&reason={error}")
    if not code:
        raise AppException("oauth", "Не передан code", status=400)
    raw = read_google_settings()
    secret = raw.get("client_secret_path")
    if not secret:
        return RedirectResponse(f"{fe}/settings?google=error&reason=no_settings")
    try:
        exchange_code(
            _project_root(),
            secret,
            settings.google_redirect_uri,
            code,
            resolved_google_token_path(),
        )
    except Exception as e:
        log.exception("[auth] Token exchange failed")
        return RedirectResponse(f"{fe}/settings?google=error&reason=exchange")
    return RedirectResponse(f"{fe}/settings?google=connected")
