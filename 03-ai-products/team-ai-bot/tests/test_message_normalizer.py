from datetime import datetime, timezone

from src.domain.models import ChatMessageRecord
from src.utils.text import clean_text, truncate_for_telegram


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  hello   team\n\nworld  ") == "hello team world"


def test_chat_message_record_content_and_meta() -> None:
    record = ChatMessageRecord(
        chat_id=1,
        message_id=2,
        user_id=3,
        username="ivan",
        author_name="Ivan",
        text="Выбираем вариант A",
        created_at=datetime(2026, 4, 28, 10, 0, tzinfo=timezone.utc),
        session_id="session-1",
    )

    assert "Ivan: Выбираем вариант A" in record.content
    assert record.meta["chat_id"] == "1"
    assert record.meta["session_id"] == "session-1"
    assert record.document_id == "1:2:session-1"


def test_truncate_for_telegram() -> None:
    result = truncate_for_telegram("x" * 100, 60)

    assert len(result) <= 60
    assert "ответ обрезан" in result
