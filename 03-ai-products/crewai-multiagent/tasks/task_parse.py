"""Задача: парсинг страницы по URL и извлечение текста."""
from crewai import Task
from agents import reader

task_parse = Task(
    description="По ссылке {url} получи страницу инструментом чтения сайта. Верни чистый текст без HTML (заголовки, абзацы).",
    agent=reader,
    expected_output="Текст страницы без разметки для SEO-анализа.",
)
