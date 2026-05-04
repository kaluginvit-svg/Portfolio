from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """Корень репозитория мини-CRM (папка с `docker-compose.yml`)."""
    return Path(__file__).resolve().parent.parent


# Public alias for modules that prefer non-underscore name
def project_root() -> Path:
    return _project_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/crm.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    log_level: str = "INFO"
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    # Подпапка корня репозитория (рядом с БД в `data/`), не рядом с кодом модулей Google
    google_token_path: str = "data/google_token.pickle"
    google_settings_path: str = "config/google_settings.json"


settings = Settings()


def db_url_resolved() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///./"):
        rel = url.replace("sqlite:///./", "")
        return f"sqlite:///{_project_root() / rel}"
    return url
