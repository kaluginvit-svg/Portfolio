"""OAuth2 user credentials — Google Drive file creation & Sheets."""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

log = logging.getLogger("crm.google.oauth")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]


def _paths(project_root: Path, client_secret_path: str, token_path: str) -> tuple[Path, Path]:
    client_secret_path = client_secret_path.strip().strip('"').strip("'").replace("\\", "/")
    token_path = token_path.strip().strip('"').strip("'").replace("\\", "/")
    secret = Path(client_secret_path)
    if not secret.is_absolute():
        secret = project_root / secret
    tok = Path(token_path)
    if not tok.is_absolute():
        tok = project_root / tok
    tok.parent.mkdir(parents=True, exist_ok=True)
    return secret, tok


def _token_store_is_json(tok_path: Path) -> bool:
    return tok_path.suffix.lower() == ".json"


def load_credentials(
    project_root: Path,
    client_secret_path: str,
    token_relative: str,
) -> Credentials | None:
    _, tok_path = _paths(project_root, client_secret_path, token_relative)
    if not tok_path.exists():
        return None
    if _token_store_is_json(tok_path):
        creds = Credentials.from_authorized_user_file(str(tok_path))
    else:
        with tok_path.open("rb") as f:
            creds = pickle.load(f)
        if not isinstance(creds, Credentials):
            return None
    if creds.expired and creds.refresh_token:
        log.info("[google] Refreshing OAuth token")
        creds.refresh(Request())
        save_credentials(project_root, client_secret_path, token_relative, creds)
    return creds


def save_credentials(
    project_root: Path,
    client_secret_path: str,
    token_relative: str,
    creds: Credentials,
) -> None:
    _, tok_path = _paths(project_root, client_secret_path, token_relative)
    if _token_store_is_json(tok_path):
        payload = creds.to_json()
        tok_path.write_text(payload, encoding="utf-8")
    else:
        with tok_path.open("wb") as f:
            pickle.dump(creds, f)
    log.info("[google] Token saved")


def credentials_valid(creds: Credentials | None) -> bool:
    if creds is None:
        return False
    return bool(creds.valid or (creds.expired and creds.refresh_token))


def build_auth_url(
    project_root: Path,
    client_secret_path: str,
    redirect_uri: str,
) -> str:
    secret_path, _ = _paths(project_root, client_secret_path, "ignored")
    if not secret_path.exists():
        raise FileNotFoundError(f"OAuth client secrets not found: {secret_path}")
    flow = Flow.from_client_secrets_file(
        str(secret_path),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url


def exchange_code(
    project_root: Path,
    client_secret_path: str,
    redirect_uri: str,
    code: str,
    token_relative: str,
) -> Credentials:
    secret_path, _ = _paths(project_root, client_secret_path, token_relative)
    flow = Flow.from_client_secrets_file(
        str(secret_path),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    save_credentials(project_root, client_secret_path, token_relative, creds)
    return creds


def drive_service_from_creds(creds: Credentials):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def sheets_service_from_creds(creds: Credentials):
    return build("sheets", "v4", credentials=creds, cache_discovery=False)
