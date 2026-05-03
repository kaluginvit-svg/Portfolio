# Домашка VPg03: агент (create_agent) + tool из урока + свой tool. venv: pip install -r requirements_lesson_agent.txt
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from openai import APIStatusError, APITimeoutError, AuthenticationError
from pydantic import BaseModel, Field

_env = Path(__file__).resolve().parent / ".env"
if not _env.exists():
    print(f"Нет .env: {_env}", file=sys.stderr)
    sys.exit(1)
load_dotenv(_env)


@tool
def get_weather_for_location(city: str) -> str:
    """Погода в городе (как в уроке, пока заглушка)."""
    return f"В {city} сейчас около +21 °C, переменная облачность, ветер слабый."


@tool
def count_words(text: str) -> int:
    """Свой tool: число слов по пробелам (оценка длины ТЗ перед генерацией кода)."""
    return len(text.split())


class WeatherResponse(BaseModel):
    """Структурированный ответ (аналог ResponseFormat из урока).

    Два поля нужны, иначе при вопросе про слова схема только с погодой не «закрывается»
    и агент с ToolStrategy уходит в бесконечные вызовы count_words.
    """

    weather_conditions: str | None = Field(
        default=None,
        description="Погода или None, если вопрос не о погоде",
    )
    words_in_text: int | None = Field(
        default=None,
        description="Число слов (из count_words), если пользователь просил посчитать слова; иначе None",
    )


def build_agent():
    api_key, base_url = os.getenv("PROXY_API"), os.getenv("URL")
    if not api_key or not base_url:
        raise ValueError("В .env: PROXY_API, URL")
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=api_key,
        base_url=base_url,
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        max_tokens=800,
        timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        max_retries=0,  # без скрытых повторов запроса при сбоях — меньше «лишних» вызовов API
    )
    return create_agent(
        llm,
        tools=[get_weather_for_location, count_words],
        system_prompt=(
            "По-русски, кратко. Погода — get_weather_for_location, число слов — count_words. "
            "После того как count_words вернул число, не вызывай его снова: один раз оформи ответ "
            "через финальный structured tool WeatherResponse (words_in_text=число, weather_conditions=None). "
            "Для погоды: weather_conditions из tool, words_in_text=None."
        ),
        # ProviderStrategy шлёт json_schema в API — многие модели/прокси дают 400; ToolStrategy работает через tools.
        response_format=ToolStrategy(WeatherResponse),
        checkpointer=MemorySaver(),
    )


def main() -> None:
    agent, thread = build_agent(), "vp03-hw-1"
    cfg = {"configurable": {"thread_id": thread}, "recursion_limit": 30}
    for text in (
        "Какая погода в Москве?",
        "Сколько слов в фразе: «Сделай REST API для задач с SQLite»?",
    ):
        print(f"→ запрос к API (один invoke = несколько шагов модели внутри агента): {text!r}", flush=True)
        r = agent.invoke({"messages": [HumanMessage(text)]}, config=cfg)
        print(r.get("structured_response"))


if __name__ == "__main__":
    try:
        main()
    except AuthenticationError:
        print("Проверь PROXY_API и URL в .env", file=sys.stderr)
        sys.exit(1)
    except APITimeoutError:
        print(
            "Таймаут LLM: увеличь LLM_TIMEOUT в .env или проверь прокси/провайдера",
            file=sys.stderr,
        )
        sys.exit(1)
    except APIStatusError as e:
        if e.status_code in (402, 429):
            print(
                "402/429: пополни баланс у провайдера в URL или смени ключ/endpoint в .env",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
