import os

# До импорта приложения отключаем bootstrap БД в lifespan (свой engine в фикстуре)
os.environ["CRM_SKIP_INIT_DB"] = "1"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    def override():
        db = SessionTesting()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
