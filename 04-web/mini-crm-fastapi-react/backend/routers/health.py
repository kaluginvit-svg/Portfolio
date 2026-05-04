import logging
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import _project_root, db_url_resolved
from backend.database import get_db

log = logging.getLogger("crm.api.health")

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1")).scalar()
    return {"status": "ok", "service": "mini-crm-api"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    url = db_url_resolved()
    db.execute(text("SELECT 1")).scalar()
    data_dir_ok = (_project_root() / "data").exists()
    if not data_dir_ok:
        (_project_root() / "data").mkdir(parents=True, exist_ok=True)
        data_dir_ok = True
    return {
        "ready": True,
        "database": url.split("///")[-1][:80] if "sqlite" in url else "configured",
        "data_dir": str(_project_root() / "data"),
    }
