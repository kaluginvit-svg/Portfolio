"""
Агенты SEO Crew: Reader, Analyst, Core Engineer.
"""
import os
from dotenv import load_dotenv

from crewai import Agent, LLM
from crewai_tools import ScrapeWebsiteTool

load_dotenv()

# --- LLM для ProxyAPI ---
def _create_llm():
    """Создание LLM с настройками из .env."""
    base_url = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL_NAME") or "gpt-4o"
    api_key = os.getenv("OPENAI_API_KEY")
    max_tokens = os.getenv("OPENAI_MAX_TOKENS")
    
    if not (base_url and api_key):
        return None
    
    llm_kw = {
        "model": model,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key
    }
    
    if max_tokens:
        llm_kw["max_tokens"] = int(max_tokens)
    
    return LLM(**llm_kw)


_llm = _create_llm()
scrape_tool = ScrapeWebsiteTool()

reader = Agent(
    role="Reader",
    goal="По ссылке извлечь текст страницы без HTML, сохранив структуру.",
    backstory="Парсишь веб-страницы инструментом чтения сайта, отдаёшь чистый текст.",
    tools=[scrape_tool],
    llm=_llm,
    verbose=True,
    allow_delegation=False,
)

analyst = Agent(
    role="Analyst",
    goal="Найти темы и ключевые слова для SEO, дать краткую оценку.",
    backstory="SEO-аналитик: выделяешь темы, ключевые слова, сильные/слабые места.",
    llm=_llm,
    verbose=True,
    allow_delegation=False,
)

core_engineer = Agent(
    role="Core Engineer",
    goal="Дать рекомендации по SEO: приоритеты, шаги, метрики.",
    backstory="Формулируешь конкретные шаги и KPI на основе анализа.",
    llm=_llm,
    verbose=True,
    allow_delegation=False,
)
