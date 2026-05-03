"""Telegram-бот-помощник: сохраняет факты в Pinecone и отвечает с top-10 по search_vectors (pine.py).

Стек: pyTelegramBotAPI (telebot) + PineconeVectorClient из pine.py + ProxyAPI (OpenAI SDK).

Запуск: .\\venv\\Scripts\\python.exe bot.py

Сохранить запись: /запомни текст или /remember текст (или строка, начинающаяся с «Запомни:»).
Любой другой текст — вопрос: перед ответом подтягиваются 10 ближайших векторов из Pinecone, затем ответ LLM.
В лог (INFO) пишется RAG retrieval: chat_id, запрос, для каждого hit — порядковый номер, id вектора, score (+ category из metadata, если есть).

Переменные .env: TELEGRAM_BOT_TOKEN, PROXYAPI_*, PINECONE_*, PROXYAPI_CHAT_MODEL, опционально RAG_TOP_K (по умолчанию 10),
PROXYAPI_CHAT_MAX_COMPLETION_TOKENS (лимит ответа), PROXYAPI_CHAT_TEMPERATURE — если не задана, temperature в запрос не передаётся
(нужно для o-series и моделей, где допустимо только значение по умолчанию).
"""

from __future__ import annotations

import logging
import os
import re
import sys
import uuid
from pathlib import Path

import telebot
from dotenv import load_dotenv
from openai import OpenAI
from telebot import types

from pine import PineconeVectorClient

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
_log = logging.getLogger("memory_bot")

_oai: OpenAI | None = None
_pc: PineconeVectorClient | None = None
_index_dim: int | None = None


def _openai() -> OpenAI:
    global _oai
    if _oai is None:
        base = os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1").rstrip("/")
        key = os.getenv("PROXYAPI_API_KEY")
        if not key:
            sys.exit("В .env нужен PROXYAPI_API_KEY.")
        _oai = OpenAI(base_url=base, api_key=key)
    return _oai


def _pine() -> PineconeVectorClient:
    global _pc
    if _pc is None:
        host = os.getenv("PINECONE_INDEX_HOST", "").strip()
        idx_name = os.getenv("PINECONE_INDEX_NAME", "").strip()
        if host:
            _pc = PineconeVectorClient(index_host=host)
        elif idx_name:
            _pc = PineconeVectorClient(index_name=idx_name)
        else:
            _pc = PineconeVectorClient(index_name="nemo")
    return _pc


def _embedding_dim() -> int | None:
    global _index_dim
    if _index_dim is None:
        stats = _pine().check_index()
        _index_dim = getattr(stats, "dimension", None)
    return _index_dim


def embed_text(text: str) -> list[float]:
    """Один текст → вектор под размерность индекса (как в test.py / pine)."""
    model = os.getenv("PROXYAPI_EMBEDDING_MODEL", "text-embedding-3-small")
    dim = _embedding_dim()
    oai = _openai()
    if dim is not None and "text-embedding-3" in model:
        r = oai.embeddings.create(input=text, model=model, dimensions=dim)
    else:
        r = oai.embeddings.create(input=text, model=model)
    return list(r.data[0].embedding)


def save_memory_to_pinecone(text: str, *, chat_id: int, user_id: int) -> str:
    """Записывает одно «воспоминание» в Pinecone; id уникальный, в metadata — фраза и чат."""
    vec = embed_text(text)
    mem_id = f"tg-{chat_id}-{uuid.uuid4().hex}"
    _pine().upsert_vectors(
        [
            {
                "id": mem_id,
                "values": vec,
                "metadata": {
                    "phrase": text[:4000],
                    "source": "telegram",
                    "chat_id": str(chat_id),
                    "user_id": str(user_id),
                },
            }
        ],
        show_progress=False,
    )
    return mem_id


def _score_str(match: object) -> str:
    sc = getattr(match, "score", None)
    if isinstance(sc, (int, float)):
        return f"{sc:.6f}"
    return repr(sc)


def log_retrieval_for_answer(*, chat_id: int, query: str, hits: object) -> None:
    """В консоль: какие id попали в контекст ответа и их score (для отладки RAG)."""
    matches = getattr(hits, "matches", []) or []
    q = query.replace("\n", " ").strip()
    if len(q) > 160:
        q = q[:157] + "..."
    _log.info("RAG retrieval chat_id=%s matches=%s query=%r", chat_id, len(matches), q)
    for i, m in enumerate(matches, 1):
        meta = getattr(m, "metadata", None) or {}
        cat = ""
        if isinstance(meta, dict):
            cat = str(meta.get("category") or "").strip()
        cat_bit = f" category={cat!r}" if cat else ""
        _log.info("  #%s id=%s score=%s%s", i, getattr(m, "id", "?"), _score_str(m), cat_bit)


def build_context_from_hits(hits: object) -> str:
    lines: list[str] = []
    for i, m in enumerate(getattr(hits, "matches", []) or [], 1):
        meta = getattr(m, "metadata", None) or {}
        phrase = ""
        if isinstance(meta, dict):
            phrase = str(meta.get("phrase") or meta.get("text") or "")
        sc = getattr(m, "score", None)
        sc_fmt = f"{sc:.4f}" if isinstance(sc, (int, float)) else "n/a"
        lines.append(f"[{i}] id={m.id!r} score={sc_fmt}\n{phrase}")
    return "\n\n".join(lines) if lines else "(в индексе ничего близкого не нашлось)"


def _text_from_assistant_message(msg: object) -> str:
    """Текст из ответа ассистента: обычный content, список блоков (новые API) или refusal."""
    raw = getattr(msg, "content", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    if isinstance(raw, list):
        chunks: list[str] = []
        for part in raw:
            if isinstance(part, dict):
                t = part.get("text")
                if isinstance(t, str):
                    chunks.append(t)
            else:
                t = getattr(part, "text", None)
                if isinstance(t, str):
                    chunks.append(t)
        return "\n".join(chunks).strip()
    ref = getattr(msg, "refusal", None)
    if isinstance(ref, str) and ref.strip():
        return f"Модель отказалась ответить: {ref.strip()}"
    return ""


def _fallback_answer_from_hits(hits: object) -> str:
    """Если LLM вернула пустоту — хотя бы цитаты из топ-чанков (иначе юзер видит пустое сообщение в Telegram)."""
    matches = getattr(hits, "matches", []) or []
    bullets: list[str] = []
    for m in matches[:7]:
        meta = getattr(m, "metadata", None) or {}
        if isinstance(meta, dict):
            t = str(meta.get("phrase") or meta.get("text") or "").strip()
            if t:
                bullets.append(f"• {t[:650]}")
    tip = (
        "\n\nПодсказка: для gpt-5/o попробуй увеличить PROXYAPI_CHAT_MAX_COMPLETION_TOKENS или сменить модель на gpt-4o-mini."
    )
    if not bullets:
        return "Модель вернула пустой ответ, а в найденных чанках нет текста." + tip
    return (
        "Модель не сформулировала ответ (часто так бывает у reasoning-моделей или при малом лимите токенов). "
        "Ближайшие записи из базы:\n\n"
        + "\n".join(bullets)
        + tip
    )


def answer_with_memories(user_text: str, *, chat_id: int) -> str:
    """Top-10 search_vectors → контекст → чат LLM (ProxyAPI)."""
    top_k = int(os.getenv("RAG_TOP_K", "10"))
    vec = embed_text(user_text)
    mf_raw = os.getenv("RAG_METADATA_FILTER", "").strip()
    mf: dict[str, object] | None = None
    if mf_raw:
        import json

        try:
            parsed = json.loads(mf_raw)
            mf = parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            _log.warning("RAG_METADATA_FILTER не JSON — игнорирую.")
    hits = _pine().search_vectors(
        vec,
        top_k=top_k,
        namespace=None,
        metadata_filter=mf,
        include_metadata=True,
    )
    log_retrieval_for_answer(chat_id=chat_id, query=user_text, hits=hits)
    context = build_context_from_hits(hits)

    chat_model = os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o-mini")
    system = (
        "Ты умный телеграм-помощник. У тебя есть выдержки из долговременной памяти (векторный поиск). "
        "Отвечай по-русски, опираясь на них; если данных мало — честно скажи. Не выдумывай факты."
    )
    user_block = f"Релевантные воспоминания (top-{top_k}):\n{context}\n\nСообщение пользователя:\n{user_text}"
    # o-series / часть прокси требуют max_completion_tokens; temperature им нельзя менять — не шлём, если нет в .env.
    cap = int(os.getenv("PROXYAPI_CHAT_MAX_COMPLETION_TOKENS", "1200"))
    create_kwargs: dict[str, object] = {
        "model": chat_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_block}],
        "max_completion_tokens": cap,
    }
    temp_raw = os.getenv("PROXYAPI_CHAT_TEMPERATURE", "").strip()
    if temp_raw:
        create_kwargs["temperature"] = float(temp_raw)
    comp = _openai().chat.completions.create(**create_kwargs)
    choices = getattr(comp, "choices", None) or []
    if not choices:
        _log.warning("Чат completions без choices — ответ только из RAG.")
        return _fallback_answer_from_hits(hits)
    ch0 = choices[0]
    msg = getattr(ch0, "message", None)
    finish = getattr(ch0, "finish_reason", None)
    reply = _text_from_assistant_message(msg) if msg is not None else ""
    if not reply:
        raw_dump = ""
        try:
            raw_dump = msg.model_dump_json()[:2500] if msg is not None and hasattr(msg, "model_dump_json") else repr(msg)
        except Exception:
            raw_dump = repr(msg)
        _log.warning(
            "Чат вернул пустой текст finish_reason=%s (часто length/stop при reasoning). raw=%s",
            finish,
            raw_dump,
        )
        reply = _fallback_answer_from_hits(hits)
    return reply


def _strip_save_prefix(text: str) -> str | None:
    t = text.strip()
    m = re.match(r"^запомни\s*:\s*(.+)$", t, flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        sys.exit("В .env задай TELEGRAM_BOT_TOKEN (токен от @BotFather).")

    bot = telebot.TeleBot(token, parse_mode=None)

    @bot.message_handler(commands=["start"])
    def on_start(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Я помню полезное: отправь «/запомни …» или «Запомни: …» — сохраню в Pinecone.\n"
            "Любой другой текст — отвечу, предварительно подтянув 10 ближайших записей из базы (search_vectors).",
        )

    @bot.message_handler(commands=["help", "помощь"])
    def on_help(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Команды:\n"
            "/запомни текст — сохранить\n"
            "/remember текст — то же\n"
            "Запомни: текст — без слэша\n"
            "Иначе — вопрос к ассистенту с RAG (top-10).\n"
            "Опция RAG_METADATA_FILTER — JSON фильтра Pinecone (например только этот чат).",
        )

    @bot.message_handler(commands=["запомни", "remember"])
    def on_remember_cmd(message: types.Message) -> None:
        raw = (message.text or "").strip()
        parts = raw.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(message, "Напиши текст после команды, например: /запомни пароль от Wi‑Fi гостевой")
            return
        payload = parts[1].strip()
        try:
            cid = message.chat.id
            uid = message.from_user.id if message.from_user else 0
            mem_id = save_memory_to_pinecone(payload, chat_id=cid, user_id=uid)
            bot.reply_to(message, f"Запомнил и записал в Pinecone.\nid: `{mem_id}`", parse_mode="Markdown")
        except Exception:
            _log.exception("save_memory")
            bot.reply_to(message, "Не удалось сохранить. Проверь ключи, индекс и размерность эмбеддинга.")

    @bot.message_handler(func=lambda m: m.text and _strip_save_prefix(m.text) is not None)
    def on_prefix_remember(message: types.Message) -> None:
        inner = _strip_save_prefix(message.text or "") or ""
        if not inner:
            return
        try:
            cid = message.chat.id
            uid = message.from_user.id if message.from_user else 0
            mem_id = save_memory_to_pinecone(inner, chat_id=cid, user_id=uid)
            bot.reply_to(message, f"Запомнил.\nid: `{mem_id}`", parse_mode="Markdown")
        except Exception:
            _log.exception("save_memory_prefix")
            bot.reply_to(message, "Не удалось сохранить.")

    @bot.message_handler(content_types=["text"])
    def on_any_text(message: types.Message) -> None:
        text = (message.text or "").strip()
        if not text or text.startswith("/"):
            return
        bot.send_chat_action(message.chat.id, "typing")
        try:
            ans = answer_with_memories(text, chat_id=message.chat.id)
        except Exception:
            _log.exception("answer_with_memories")
            bot.reply_to(message, "Ошибка при ответе. Проверь .env и лимиты API.")
            return
        ans = (ans or "").strip()
        if not ans:
            ans = "Пустой ответ — баг обработчика."
        if len(ans) > 4096:
            ans = ans[:4090] + "…"
        bot.reply_to(message, ans)

    _log.info("Старт polling (pyTelegramBotAPI)…")
    bot.infinity_polling(skip_pending=True, interval=0, timeout=60)


if __name__ == "__main__":
    main()
