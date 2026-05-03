"""Google credentials: OAuth installed app or service account JSON."""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


def credentials_from_service_account(json_path: Path):
    return service_account.Credentials.from_service_account_file(
        str(json_path),
        scopes=SCOPES,
    )


def _is_oauth_client_secrets_payload(data: object) -> bool:
    """Файл из Cloud Console с ключами installed / web — это не user token.json."""
    if not isinstance(data, dict):
        return False
    return "installed" in data or "web" in data


def credentials_from_authorized_user_json(token_path: Path) -> Credentials:
    """Load saved OAuth user credentials (token.json); refresh if expired."""
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds
    raise RuntimeError(
        f"Google token file is invalid or missing refresh_token: {token_path}"
    )


def credentials_oauth_installed(client_secrets: Path, token_path: Path) -> Credentials:
    """Desktop OAuth: client JSON + файл пользовательского токена после браузера."""
    creds: Credentials | None = None
    if token_path.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except ValueError:
            creds = None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def get_credentials(
    *,
    service_account_json: Path | None,
    oauth_token_json: Path | None,
    oauth_client_secrets: Path | None,
    oauth_token_path: Path,
):
    if service_account_json and service_account_json.is_file():
        return credentials_from_service_account(service_account_json)

    # Файл в корне часто ошибочно назван google_token.json, но это JSON клиента (installed)
    candidates: list[tuple[Path, str]] = []
    if oauth_token_json and oauth_token_json.is_file():
        candidates.append((oauth_token_json, "GOOGLE_OAUTH_TOKEN_JSON / авто"))
    if oauth_client_secrets and oauth_client_secrets.is_file():
        candidates.append((oauth_client_secrets, "GOOGLE_OAUTH_CLIENT_SECRETS"))

    seen: set[Path] = set()
    for path, _src in candidates:
        rp = path.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _is_oauth_client_secrets_payload(raw):
            return credentials_oauth_installed(path, oauth_token_path)

    if oauth_token_json and oauth_token_json.is_file():
        return credentials_from_authorized_user_json(oauth_token_json)

    if oauth_client_secrets and oauth_client_secrets.is_file():
        return credentials_oauth_installed(oauth_client_secrets, oauth_token_path)

    raise FileNotFoundError(
        "Нужен один из вариантов: "
        "GOOGLE_SERVICE_ACCOUNT_JSON; "
        "полноценный google_token.json (token + refresh_token + client_id + client_secret); "
        "или JSON клиента OAuth (installed) — положите его как google_token.json или задайте "
        "GOOGLE_OAUTH_CLIENT_SECRETS, затем один раз выполните sync (откроется браузер)."
    )
