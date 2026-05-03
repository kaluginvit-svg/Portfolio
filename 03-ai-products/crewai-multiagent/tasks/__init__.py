"""Задачи SEO Crew: parse -> analyze -> recommend."""
from .task_parse import task_parse
from .task_analyze import task_analyze
from .task_recommend import task_recommend

__all__ = ["task_parse", "task_analyze", "task_recommend"]
