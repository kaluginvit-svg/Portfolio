import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config import _project_root
from backend.google_settings_store import resolved_google_token_path
from backend.database import get_db
from backend.exceptions import AppException
from backend.google_settings_store import read_google_settings
from backend.schemas import ReportExportResponse
from google_integration import google_drive, google_sheets, report_generator
from google_integration.oauth_service import credentials_valid, load_credentials

log = logging.getLogger("crm.api.reports")

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_title(kind: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"CRM_{kind}_{ts}"


def _ensure_google() -> tuple[str, object]:
    raw = read_google_settings()
    secret = raw.get("client_secret_path")
    folder = raw.get("parent_folder_id")
    if not secret or not folder:
        raise AppException(
            "google_not_configured",
            "Настройте Google: путь к client_secret JSON и ID родительской папки Drive",
            status=400,
        )
    creds = load_credentials(_project_root(), secret, resolved_google_token_path())
    if not credentials_valid(creds):
        raise AppException(
            "google_auth_required",
            "Нужна авторизация Google: откройте ссылку из «Войти через Google»",
            status=401,
        )
    return folder, creds


@router.post("/export/clients", response_model=ReportExportResponse)
def export_clients_report(db: Session = Depends(get_db)):
    folder, creds = _ensure_google()
    grid, _n = report_generator.clients_report_grid(db)
    title = _report_title("Clients")
    try:
        fid = google_drive.create_spreadsheet_in_folder(
            creds, title=title, parent_folder_id=folder
        )
        google_sheets.write_values(creds, spreadsheet_id=fid, range_a1="A1", values=grid)
        ncol = max(len(r) for r in grid) if grid else 8
        google_sheets.format_header_band(
            creds, spreadsheet_id=fid, num_rows=5, num_cols=min(ncol, 30)
        )
    except Exception as e:
        log.exception("[reports] clients export failed")
        raise AppException(
            "google_api_error",
            "Ошибка Google API при выгрузке клиентов",
            detail=str(e)[:500],
            status=502,
        ) from e
    url = f"https://docs.google.com/spreadsheets/d/{fid}/edit"
    log.info("[api] Report clients -> %s", url)
    return ReportExportResponse(file_id=fid, url=url, title=title)


@router.post("/export/deals", response_model=ReportExportResponse)
def export_deals_report(db: Session = Depends(get_db)):
    folder, creds = _ensure_google()
    grid, _n = report_generator.deals_report_grid(db)
    title = _report_title("Deals")
    try:
        fid = google_drive.create_spreadsheet_in_folder(
            creds, title=title, parent_folder_id=folder
        )
        google_sheets.write_values(creds, spreadsheet_id=fid, range_a1="A1", values=grid)
        ncol = max(len(r) for r in grid) if grid else 12
        google_sheets.format_header_band(
            creds, spreadsheet_id=fid, num_rows=5, num_cols=min(ncol, 30)
        )
    except Exception as e:
        log.exception("[reports] deals export failed")
        raise AppException(
            "google_api_error",
            "Ошибка Google API при выгрузке сделок",
            detail=str(e)[:500],
            status=502,
        ) from e
    url = f"https://docs.google.com/spreadsheets/d/{fid}/edit"
    log.info("[api] Report deals -> %s", url)
    return ReportExportResponse(file_id=fid, url=url, title=title)


@router.post("/export/tasks", response_model=ReportExportResponse)
def export_tasks_report(db: Session = Depends(get_db)):
    folder, creds = _ensure_google()
    grid, _n = report_generator.tasks_report_grid(db)
    title = _report_title("Tasks")
    try:
        fid = google_drive.create_spreadsheet_in_folder(
            creds, title=title, parent_folder_id=folder
        )
        google_sheets.write_values(creds, spreadsheet_id=fid, range_a1="A1", values=grid)
        ncol = max(len(r) for r in grid) if grid else 12
        google_sheets.format_header_band(
            creds, spreadsheet_id=fid, num_rows=5, num_cols=min(ncol, 30)
        )
    except Exception as e:
        log.exception("[reports] tasks export failed")
        raise AppException(
            "google_api_error",
            "Ошибка Google API при выгрузке задач",
            detail=str(e)[:500],
            status=502,
        ) from e
    url = f"https://docs.google.com/spreadsheets/d/{fid}/edit"
    log.info("[api] Report tasks -> %s", url)
    return ReportExportResponse(file_id=fid, url=url, title=title)
