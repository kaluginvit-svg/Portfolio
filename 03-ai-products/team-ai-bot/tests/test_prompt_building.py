from src.utils.text import format_documents_for_prompt


class FakeDocument:
    content = "2026-04-28 10:00 UTC, Ivan: предлагаю вариант A"
    meta = {"author_name": "Ivan", "created_at": "2026-04-28T10:00:00+00:00"}


def test_format_documents_for_prompt() -> None:
    prompt_context = format_documents_for_prompt([FakeDocument()])

    assert "Ivan" in prompt_context
    assert "вариант A" in prompt_context
