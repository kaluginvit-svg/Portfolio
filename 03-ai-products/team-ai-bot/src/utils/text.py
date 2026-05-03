from __future__ import annotations


def clean_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().split())


def truncate_for_telegram(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    suffix = "\n\n...ответ обрезан из-за лимита Telegram."
    if limit <= len(suffix):
        return suffix[:limit]
    return value[: limit - len(suffix)].rstrip() + suffix


def format_documents_for_prompt(documents: list[object]) -> str:
    lines: list[str] = []
    for index, document in enumerate(documents, start=1):
        content = getattr(document, "content", "") or ""
        meta = getattr(document, "meta", {}) or {}
        author = meta.get("author_name") or meta.get("username") or "unknown"
        created_at = meta.get("created_at", "")
        lines.append(f"{index}. [{created_at}] {author}: {content}")
    return "\n".join(lines)
