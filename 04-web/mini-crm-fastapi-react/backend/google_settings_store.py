import json
import logging
from pathlib import Path

from backend.config import _project_root, settings

log = logging.getLogger("crm.api.settings")


def settings_path() -> Path:
    return _project_root() / settings.google_settings_path


def read_google_settings() -> dict:
    p = settings_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log.warning("Invalid google_settings.json")
        return {}


def write_google_settings(payload: dict) -> None:
    p = settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("[api] Saved Google integration paths (no secrets logged)")


def resolved_google_token_path() -> str:
    """Путь к pickle-токену: из google_settings.json либо дефолт из Settings / GOOGLE_TOKEN_PATH."""
    raw = read_google_settings()
    v = raw.get("google_token_path")
    if isinstance(v, str) and v.strip():
        return v.strip().replace("\\", "/")
    return settings.google_token_path.replace("\\", "/")
