"""Модели шага квиза."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

StepInputType = Literal["choice", "text"]


@dataclass(frozen=True)
class QuizOption:
    value: str
    label: str


@dataclass(frozen=True)
class QuizStep:
    id: str
    question: str
    input_type: StepInputType
    options: tuple[QuizOption, ...] = ()
    """Показать шаг, если функция возвращает True (по уже собранным ответам)."""
    visible_if: Callable[[dict[str, str]], bool] | None = None


def always_visible(_: dict[str, str]) -> bool:
    return True


def after_filing_only(answers: dict[str, str]) -> bool:
    return answers.get("clarify_doc_5") != "not_yet"
