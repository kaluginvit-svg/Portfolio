"""
Сборка LangChain-агента с вызовом инструментов (OpenAI Chat Completions).
"""
from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from tools import all_tools

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_AGENT_DIR, ".env"))

_log = logging.getLogger("local_agent.agent")

SYSTEM_PROMPT = """Ты локальный AI-ассистент в терминале. Отвечай на языке пользователя (часто русский).
Выбирай инструменты осознанно:
- Погода по городу → get_weather (только сейчас). Прогноз на конкретный локальный час (например «завтра в 12:00») → get_weather с forecast_local_date=YYYY-MM-DD и forecast_local_hour=0–23; дату «завтра» вычисли от текущего календаря; для «центра Москвы» используй city=Москва.
- Цена криптовалюты → crypto_price_tool (id: bitcoin, ethereum; валюта: usd, eur, rub).
- Курсы обычных валют (EUR/USD/RUB и т.д.) → get_fiat_exchange_rates (base + список quote через запятую; не крипта).
- QR-код (текст/URL в PNG в проекте) → generate_qr_code.
- Общая информация из сети → web_search.
- Произвольный HTTP → http_request.
- Чтение/запись файлов проекта → read_file / write_file (пути относительно корня проекта).
- Одна безопасная shell-команда в папке проекта → run_terminal_command.

Если не хватает данных (город, монета, валюта, путь) — кратко спроси уточнение.
После результата инструментов дай структурированный понятный ответ."""


def build_executor(
    model: str | None = None,
    temperature: float = 0.2,
    verbose: bool = False,
) -> AgentExecutor:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Задайте OPENAI_API_KEY в файле agent/.env (рядом с этим проектом)."
        )
    m = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    _log.info(
        "Сборка агента: model=%s base_url=%s temperature=%s verbose=%s",
        m,
        base_url or "(api.openai.com)",
        temperature,
        verbose,
    )
    llm = ChatOpenAI(
        model=m,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )
    tools = all_tools()
    _log.debug("Подключено инструментов: %s", [t.name for t in tools])
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        max_iterations=12,
        handle_parsing_errors=True,
    )
    _log.debug("AgentExecutor готов (max_iterations=12).")
    return executor


def lc_history_from_pairs(pairs: list[dict[str, str]]) -> list[Any]:
    """Преобразует сохранённые пары user/assistant в сообщения LangChain."""
    from langchain_core.messages import AIMessage, HumanMessage

    msgs: list[Any] = []
    for p in pairs[-20:]:
        u = p.get("user")
        a = p.get("assistant")
        if u:
            msgs.append(HumanMessage(content=u))
        if a:
            msgs.append(AIMessage(content=a))
    return msgs
