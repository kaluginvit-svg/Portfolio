from pathlib import Path

from src.domain.session_manager import SessionManager
from src.storage.local_state import LocalStateStore


def test_start_and_stop_session(tmp_path: Path) -> None:
    manager = SessionManager(LocalStateStore(tmp_path / "state.sqlite3"))

    started = manager.start(chat_id=123)
    assert started.already_active is False

    repeated = manager.start(chat_id=123)
    assert repeated.already_active is True
    assert repeated.session.session_id == started.session.session_id

    stopped = manager.stop(chat_id=123)
    assert stopped is not None
    assert stopped.session_id == started.session.session_id
    assert manager.status(chat_id=123) is None


def test_stop_without_active_session(tmp_path: Path) -> None:
    manager = SessionManager(LocalStateStore(tmp_path / "state.sqlite3"))

    assert manager.stop(chat_id=123) is None
