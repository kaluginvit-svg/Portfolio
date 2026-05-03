"""Задача: SEO-анализ текста страницы."""
from crewai import Task
from agents import analyst
from .task_parse import task_parse

task_analyze = Task(
    description="По тексту из контекста: 1) темы страницы 2) ключевые слова по темам 3) краткая оценка (сильные/слабые места).",
    agent=analyst,
    expected_output="Темы, ключевые слова, оценка SEO.",
    context=[task_parse],
)
