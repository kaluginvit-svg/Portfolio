"""Навигация по шагам квиза по конфигу и ответам."""

from __future__ import annotations

from app.quizzes.models import QuizStep


def visible_steps(steps: tuple[QuizStep, ...], answers: dict[str, str]) -> list[QuizStep]:
    out: list[QuizStep] = []
    for s in steps:
        pred = s.visible_if
        if pred is None or pred(answers):
            out.append(s)
    return out


def index_of_step(visible: list[QuizStep], step_id: str) -> int | None:
    for i, s in enumerate(visible):
        if s.id == step_id:
            return i
    return None


def current_step(
    steps: tuple[QuizStep, ...],
    answers: dict[str, str],
    step_index: int,
) -> QuizStep | None:
    vis = visible_steps(steps, answers)
    if step_index < 0 or step_index >= len(vis):
        return None
    return vis[step_index]


def total_visible(steps: tuple[QuizStep, ...], answers: dict[str, str]) -> int:
    return len(visible_steps(steps, answers))


def is_quiz_questions_finished(
    steps: tuple[QuizStep, ...],
    answers: dict[str, str],
    step_index: int,
) -> bool:
    return step_index >= total_visible(steps, answers)
