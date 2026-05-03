"""
Текст-агент: работа с OpenAI Chat Completions API.
Генерация текста и диалог с сохранением контекста.
"""

import json
import os
import logging
from typing import Any, Literal

from dotenv import load_dotenv
from openai import BadRequestError, NotFoundError, OpenAI

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore[misc, assignment]

load_dotenv()

# Конфигурация из .env (модели по умолчанию — только из .env)
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL") or "gpt-4o-mini"
FALLBACK_MODEL = os.environ.get("OPENAI_FALLBACK_MODEL") or os.environ.get("DEFAULT_MODEL") or "gpt-4o-mini"
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "30"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Claude — из .env
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.proxyapi.ru/anthropic")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL") or "claude-3-7-sonnet-20250219"
CLAUDE_MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "4096"))
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "medium").lower()  # low | medium | high

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_client(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> OpenAI:
    """Создаёт клиент OpenAI. Ключ — из аргумента, .env (OPENAI_API_KEY) или переменной окружения."""
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Укажите api_key или задайте переменную окружения OPENAI_API_KEY")
    return OpenAI(
        api_key=key,
        base_url=base_url or BASE_URL,
        timeout=timeout if timeout is not None else REQUEST_TIMEOUT,
    )


# Клиент по умолчанию (из .env), создаётся при первом вызове get_client или при импорте после загрузки .env
openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    global openai_client
    if openai_client is None:
        openai_client = get_client()
    return openai_client


anthropic_client: "Anthropic | None" = None
claude_client: OpenAI | None = None


def _get_anthropic_client() -> "Anthropic":
    """Клиент Anthropic для ProxyAPI (base_url=https://api.proxyapi.ru/anthropic)."""
    if Anthropic is None:
        raise ValueError("Установите пакет anthropic: pip install anthropic")
    key = ANTHROPIC_API_KEY
    if not key:
        raise ValueError("Задайте ANTHROPIC_API_KEY или OPENAI_API_KEY в .env")
    global anthropic_client
    if anthropic_client is None:
        anthropic_client = Anthropic(
            api_key=key,
            base_url=ANTHROPIC_BASE_URL,
        )
    return anthropic_client


def get_claude_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAI:
    """Клиент OpenAI-совместимый для Claude (fallback). Без аргументов — кэш из .env."""
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        raise ValueError("Задайте ANTHROPIC_API_KEY или OPENAI_API_KEY в .env")
    if api_key or base_url:
        return OpenAI(
            api_key=key,
            base_url=base_url or ANTHROPIC_BASE_URL,
            timeout=REQUEST_TIMEOUT,
        )
    global claude_client
    if claude_client is None:
        claude_client = OpenAI(
            api_key=key,
            base_url=ANTHROPIC_BASE_URL,
            timeout=REQUEST_TIMEOUT,
        )
    return claude_client


def _get_claude_client() -> OpenAI:
    return get_claude_client()


def _messages_to_anthropic(messages: list[dict]) -> list[dict]:
    """Конвертирует [{"role","content"}] в формат Anthropic: content = [{"type":"text","text": ...}]."""
    out = []
    for m in messages:
        role = m.get("role", "user")
        if role == "system":
            role = "user"
        content = m.get("content", "")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        out.append({"role": role, "content": content})
    return out


def _is_model_not_supported(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "model not supported" in msg or "model_not_supported" in msg


def generate_response(
    messages: list[dict],
    client: OpenAI | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> dict:
    """
    Запрос к Chat Completions API. Возвращает dict с ключами "text" и "reasoning".
    При 400 "Model not supported" повторяет запрос с FALLBACK_MODEL (gpt-4o-mini).
    """
    api_client = client or _get_openai_client()
    model = model or DEFAULT_MODEL
    for attempt_model in (model, FALLBACK_MODEL):
        try:
            resp = api_client.chat.completions.create(
                model=attempt_model,
                messages=messages,
                temperature=temperature,
                timeout=REQUEST_TIMEOUT,
            )
            text = (resp.choices[0].message.content or "").strip()
            if attempt_model != model:
                logger.info("OpenAI ответ получен (использована запасная модель %s)", attempt_model)
            else:
                logger.info("OpenAI ответ получен")
            return {"text": text, "reasoning": None}
        except BadRequestError as e:
            if _is_model_not_supported(e) and attempt_model == model and FALLBACK_MODEL != model:
                logger.warning("Модель %s не поддерживается, пробуем %s", model, FALLBACK_MODEL)
                continue
            logger.error(f"Ошибка при запросе OpenAI: {e}", exc_info=True)
            return {
                "text": "Ошибка при обращении к модели (OpenAI). Попробуйте ещё раз.",
                "reasoning": None,
            }
        except Exception as e:
            logger.error(f"Ошибка при запросе OpenAI: {e}", exc_info=True)
            return {
                "text": "Ошибка при обращении к модели (OpenAI). Попробуйте ещё раз.",
                "reasoning": None,
            }
    return {
        "text": "Модель не поддерживается прокси. Задайте в .env DEFAULT_MODEL или OPENAI_FALLBACK_MODEL (например gpt-4o-mini).",
        "reasoning": None,
    }


def _reasoning_dict(effort: str, reasoning_tokens: int | None, total_tokens: int | None) -> dict:
    """Единый формат показателей рассуждения для консоли."""
    return {
        "effort": effort,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
    }


def _do_claude_anthropic(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    effort: str,
) -> dict:
    """Запрос к Claude через официальный Anthropic SDK (ProxyAPI: base_url=.../anthropic)."""
    client = _get_anthropic_client()
    anthropic_messages = _messages_to_anthropic(messages)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=anthropic_messages,
        temperature=temperature,
    )
    text = ""
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text += getattr(block, "text", "") or ""
    text = text.strip()
    reasoning_tokens = None
    total_tokens = None
    if hasattr(resp, "usage") and resp.usage:
        inp = getattr(resp.usage, "input_tokens", None)
        out = getattr(resp.usage, "output_tokens", None)
        reasoning_tokens = getattr(resp.usage, "reasoning_tokens", None) or out
        if inp is not None and out is not None:
            total_tokens = inp + out
        elif hasattr(resp.usage, "total_tokens"):
            total_tokens = getattr(resp.usage, "total_tokens", None)
    reasoning = _reasoning_dict(effort, reasoning_tokens, total_tokens)
    return {"text": text, "reasoning": reasoning}


def _do_claude_request_openai(
    api_client: OpenAI,
    model: str,
    messages: list[dict],
    temperature: float,
    reasoning_effort: str,
) -> dict:
    """Один запрос к Claude через OpenAI-совместимый API (fallback)."""
    resp = api_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        timeout=REQUEST_TIMEOUT,
        extra_body={"reasoning": {"effort": reasoning_effort}},
    )
    msg = resp.choices[0].message
    text = (msg.content or "").strip()
    reasoning_tokens = None
    total_tokens = None
    raw_reasoning = getattr(resp, "reasoning", None)
    if isinstance(raw_reasoning, dict):
        reasoning_tokens = raw_reasoning.get("token_count") or raw_reasoning.get("reasoning_tokens")
    if hasattr(resp, "usage") and resp.usage:
        total_tokens = getattr(resp.usage, "total_tokens", None)
    reasoning = _reasoning_dict(reasoning_effort, reasoning_tokens, total_tokens)
    return {"text": text, "reasoning": reasoning}


def generate_response_claude(
    messages: list[dict],
    client: OpenAI | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    reasoning_effort: str | None = None,
) -> dict:
    """
    Запрос к Claude.     Сначала — официальный Anthropic API (base_url=.../anthropic, messages.create).
    При ошибке — fallback на OpenAI-эндпоинт или обычную модель.
    reasoning_effort берётся из .env (REASONING_EFFORT) или аргумента.
    """
    model = model or CLAUDE_MODEL
    effort = (reasoning_effort or REASONING_EFFORT).lower()
    # 1) Официальный эндпоинт ProxyAPI: https://api.proxyapi.ru/anthropic
    if Anthropic is not None:
        try:
            result = _do_claude_anthropic(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=CLAUDE_MAX_TOKENS,
                effort=effort,
            )
            logger.info("Claude ответ получен (Anthropic API)")
            return result
        except Exception as e:
            logger.warning("Anthropic API недоступен (%s), пробуем fallback", e)
    # 2) OpenAI-совместимый эндпоинт (если прокси отдаёт Claude через chat/completions)
    api_client = client or _get_claude_client()
    try:
        result = _do_claude_request_openai(
            api_client, model, messages, temperature, effort
        )
        logger.info("Claude ответ получен с reasoning")
        return result
    except NotFoundError:
        current_base = str(getattr(api_client, "base_url", "")).rstrip("/")
        if current_base != BASE_URL.rstrip("/"):
            logger.warning("Claude-эндпоинт вернул 404, пробуем OPENAI_BASE_URL: %s", BASE_URL)
            try:
                fallback_client = _get_openai_client()
                result = _do_claude_request_openai(
                    fallback_client, model, messages, temperature, effort
                )
                logger.info("Claude ответ получен (через общий эндпоинт)")
                return result
            except BadRequestError as e:
                if _is_model_not_supported(e):
                    return _claude_fallback_to_openai(messages, temperature)
            except Exception as e:
                logger.error("Ошибка при запросе Claude (fallback): %s", e, exc_info=True)
                return {
                    "text": "Ошибка при обращении к думающей модели (Claude). Попробуйте ещё раз.",
                    "reasoning": None,
                }
        return {
            "text": "Ошибка при обращении к думающей модели (Claude). Попробуйте ещё раз.",
            "reasoning": None,
        }
    except BadRequestError as e:
        if _is_model_not_supported(e):
            return _claude_fallback_to_openai(messages, temperature)
        logger.error("Ошибка при запросе Claude: %s", e, exc_info=True)
        return {
            "text": "Ошибка при обращении к думающей модели (Claude). Попробуйте ещё раз.",
            "reasoning": None,
        }
    except Exception as e:
        logger.error("Ошибка при запросе Claude: %s", e, exc_info=True)
        return {
            "text": "Ошибка при обращении к думающей модели (Claude). Попробуйте ещё раз.",
            "reasoning": None,
        }


def _claude_fallback_to_openai(messages: list[dict], temperature: float) -> dict:
    """Прокси не поддерживает Claude — отвечаем через обычную модель (DEFAULT_MODEL/FALLBACK)."""
    logger.warning("Модель Claude не поддерживается прокси, используем %s", FALLBACK_MODEL)
    result = generate_response(messages, model=FALLBACK_MODEL, temperature=temperature)
    if result.get("text") and not result["text"].startswith("Ошибка при обращении"):
        result["reasoning"] = _reasoning_dict(
            REASONING_EFFORT, None, None
        ) | {"fallback": f"Claude недоступен, ответ через {FALLBACK_MODEL}"}
    return result


def chat_completion(
    client: OpenAI,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Один запрос к Chat Completions API.
    Возвращает только текст ответа ассистента.
    """
    result = generate_response(messages, client=client, model=model, temperature=temperature)
    return result["text"]


def run_dialog(
    client: OpenAI,
    system_prompt: str = "Ты полезный помощник. Отвечай кратко и по делу.",
    model: str | None = None,
    temperature: float = 0.7,
) -> None:
    """
    Интерактивный диалог с нейросетью. Контекст сохраняется между сообщениями.
    Введи пустую строку или 'выход' / 'exit' для завершения.
    """
    messages = [{"role": "system", "content": system_prompt}]

    print("Диалог запущен. Пустая строка или 'выход' — завершить.\n")

    while True:
        user_input = input("Вы: ").strip()
        if not user_input or user_input.lower() in ("выход", "exit", "quit"):
            print("До свидания!")
            break

        messages.append({"role": "user", "content": user_input})
        reply = chat_completion(client, messages, model=model or DEFAULT_MODEL, temperature=temperature)
        messages.append({"role": "assistant", "content": reply})
        print(f"Ассистент: {reply}\n")


Mode = Literal["openai", "claude"]


class TextAgent:
    """Агент с историей диалога и переключением режимов openai / claude."""

    def __init__(self, mode: Mode = "openai", history_path: str = "history.json") -> None:
        self.mode: Mode = mode
        self.history_path = history_path
        self.messages: list[dict[str, Any]] = []
        self.reasoning_effort: str = REASONING_EFFORT  # для думающей модели: low | medium | high
        logger.info(f"Инициализация агента в режиме: {self.mode}")

    def load_history(self) -> None:
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                self.messages = json.load(f)
            logger.info(f"История загружена из {self.history_path}, сообщений: {len(self.messages)}")
        except FileNotFoundError:
            logger.info("История не найдена, начинаем с пустого контекста")
            self.messages = []

    def save_history(self) -> None:
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)
        logger.info(f"История сохранена в {self.history_path}, сообщений: {len(self.messages)}")

    def set_mode(self, mode: Mode) -> None:
        if mode not in ("openai", "claude"):
            raise ValueError("Неизвестный режим: " + mode)
        self.mode = mode
        logger.info(f"Режим переключен на: {self.mode}")

    def set_reasoning_effort(self, effort: str) -> None:
        """Уровень рассуждения для Claude: low, medium, high."""
        effort = effort.strip().lower()
        if effort not in ("low", "medium", "high"):
            raise ValueError("Уровень рассуждения: low, medium или high")
        self.reasoning_effort = effort
        logger.info(f"Уровень рассуждения (reasoning): {self.reasoning_effort}")

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def generate_response(self, prompt: str) -> dict:
        """Возвращает dict с ключами "text" и "reasoning"."""
        self.add_user_message(prompt)
        if self.mode == "openai":
            result = generate_response(self.messages)
        else:
            result = generate_response_claude(
                self.messages, reasoning_effort=self.reasoning_effort
            )
        self.add_assistant_message(result["text"])
        return result
