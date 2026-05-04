import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.config import db_url_resolved

log = logging.getLogger("crm.db")

engine = create_engine(
    db_url_resolved(),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import os

    if os.environ.get("CRM_SKIP_INIT_DB"):
        return
    # Import models so metadata is populated
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    log.info("Database tables ensured")
