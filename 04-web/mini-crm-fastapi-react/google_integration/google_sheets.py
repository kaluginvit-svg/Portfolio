"""Google Sheets — write formatted report grids."""

from __future__ import annotations

import logging
from typing import Any

from google.oauth2.credentials import Credentials

from google_integration.oauth_service import sheets_service_from_creds

log = logging.getLogger("crm.google.sheets")


def write_values(
    creds: Credentials,
    *,
    spreadsheet_id: str,
    range_a1: str,
    values: list[list[Any]],
) -> None:
    service = sheets_service_from_creds(creds)
    body = {"values": values}
    (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    log.info("[google.sheets] Updated range %s rows=%s", range_a1, len(values))


def format_header_band(
    creds: Credentials,
    *,
    spreadsheet_id: str,
    sheet_id: int = 0,
    num_rows: int = 4,
    num_cols: int = 20,
) -> None:
    """Bold metadata + header rows (first visual block)."""
    service = sheets_service_from_creds(creds)
    requests: list[dict] = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                    }
                },
                "fields": "userEnteredFormat.textFormat.bold",
            }
        }
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()
