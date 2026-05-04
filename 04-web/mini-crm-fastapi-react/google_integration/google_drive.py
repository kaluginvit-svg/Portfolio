"""Google Drive — create spreadsheets in folder (OAuth user)."""

from __future__ import annotations

import logging

from google.oauth2.credentials import Credentials

from google_integration.oauth_service import drive_service_from_creds

log = logging.getLogger("crm.google.drive")


def create_spreadsheet_in_folder(
    creds: Credentials,
    *,
    title: str,
    parent_folder_id: str,
) -> str:
    """Create empty Google Spreadsheet in folder; return file ID."""
    service = drive_service_from_creds(creds)
    body = {
        "name": title,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [parent_folder_id],
    }
    file = service.files().create(body=body, fields="id", supportsAllDrives=True).execute()
    fid = file.get("id")
    log.info("[google.drive] Created spreadsheet id=%s name=%s", fid, title)
    return fid


def list_files_in_folder(creds: Credentials, folder_id: str, page_size: int = 50) -> list[dict]:
    """List files directly in folder (for debugging)."""
    service = drive_service_from_creds(creds)
    q = f"'{folder_id}' in parents and trashed = false"
    res = (
        service.files()
        .list(
            q=q,
            pageSize=page_size,
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
        )
        .execute()
    )
    return res.get("files", [])
