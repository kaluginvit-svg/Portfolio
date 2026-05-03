"""Конфиг шагов квиза «Рассчитать выплаты»."""

from __future__ import annotations

from app.quizzes.models import QuizOption, QuizStep, always_visible

CALCULATE_STEPS: tuple[QuizStep, ...] = (
    QuizStep(
        id="service_status",
        question="К какой категории относился погибший?",
        input_type="choice",
        options=(
            QuizOption("contract_mobilized", "Контрактник / мобилизованный"),
            QuizOption("volunteer", "Доброволец"),
            QuizOption("force_department", "Росгвардия / иное силовое ведомство"),
            QuizOption("unknown", "Не уверен(а)"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="applicant_role",
        question="Кто вы?",
        input_type="choice",
        options=(
            QuizOption("spouse_registered", "Супруг(а), брак зарегистрирован"),
            QuizOption("cohabitation_no_marriage", "Жили вместе, но брак не регистрировали"),
            QuizOption("parent", "Мать / отец"),
            QuizOption("child_under_18", "Ребёнок до 18 лет"),
            QuizOption("child_student_18_23", "Ребёнок 18–23, учусь очно"),
            QuizOption("representative_or_unknown", "Представитель семьи / не уверен(а)"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="recipients_count",
        question="Сколько всего человек входит в круг получателей разовых семейных выплат?",
        input_type="choice",
        options=(
            QuizOption("1", "1"),
            QuizOption("2", "2"),
            QuizOption("3", "3"),
            QuizOption("4", "4"),
            QuizOption("5_plus", "5 и более"),
            QuizOption("unknown", "Не уверен(а)"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="children_count",
        question="Есть ли дети, для которых нужно считать ежемесячные выплаты?",
        input_type="choice",
        options=(
            QuizOption("0", "Нет"),
            QuizOption("1", "1 ребёнок"),
            QuizOption("2", "2 ребёнка"),
            QuizOption("3_plus", "3 и более"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="death_basis",
        question="Что известно о причине смерти?",
        input_type="choice",
        options=(
            QuizOption("duty", "Гибель при исполнении обязанностей"),
            QuizOption("disease", "Смерть из-за заболевания, полученного при исполнении"),
            QuizOption("unknown", "Не уверен(а)"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="ambiguity_flag",
        question="Есть ли спор или неясность по браку, родству, составу семьи или статусу службы?",
        input_type="choice",
        options=(
            QuizOption("no", "Нет, всё стандартно"),
            QuizOption("yes", "Да, есть спор / неясность"),
            QuizOption("unknown", "Не уверен(а)"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="region",
        question="В каком регионе вы живёте? (можно написать коротко)",
        input_type="text",
        visible_if=always_visible,
    ),
    QuizStep(
        id="calc_mode",
        question="Какой расчёт вам показать?",
        input_type="choice",
        options=(
            QuizOption("federal_only", "Только федеральный"),
            QuizOption("federal_plus_region", "Федеральный + региональный ориентир"),
            QuizOption("unknown", "Не знаю"),
        ),
        visible_if=always_visible,
    ),
)
