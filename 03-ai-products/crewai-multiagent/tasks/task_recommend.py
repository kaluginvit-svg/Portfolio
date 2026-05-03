"""Задача: рекомендации и логика действий на основе SEO-анализа."""
from crewai import Task
from agents import core_engineer
from .task_analyze import task_analyze

task_recommend = Task(
    description="По анализу из контекста: приоритетные ключевые слова, шаги по доработке страницы, метрики/KPI.",
    agent=core_engineer,
    expected_output="Приоритеты, шаги, метрики.",
    context=[task_analyze],  # только анализ — экономия токенов; при необходимости добавить task_parse
)
