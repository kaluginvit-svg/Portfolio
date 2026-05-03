"""Конфиг шагов квиза «Прояснить ситуацию»."""

from __future__ import annotations

from app.quizzes.models import QuizOption, QuizStep, after_filing_only, always_visible

CLARIFY_STEPS: tuple[QuizStep, ...] = (
    QuizStep(
        id="clarify_stage_1",
        question="Что сейчас лучше всего описывает вашу ситуацию?",
        input_type="choice",
        options=(
            QuizOption("start", "Я только начинаю разбираться"),
            QuizOption("collecting_docs", "Уже собираю документы"),
            QuizOption("ready_to_file", "Документы почти готовы, хочу понять, куда и как подавать"),
            QuizOption("already_filed", "Уже подавал(а) документы"),
            QuizOption("post_filing_problem", "После подачи возникла проблема или непонятная ситуация"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_1",
        question="Есть ли у вас свидетельство о смерти?",
        input_type="choice",
        options=(
            QuizOption("yes", "Да, уже на руках"),
            QuizOption("in_progress", "Оформляем, ещё в процессе"),
            QuizOption("no", "Пока нет"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_2",
        question="Есть ли у вас извещение из части или другой документ по обстоятельствам?",
        input_type="choice",
        options=(
            QuizOption("yes", "Да, есть"),
            QuizOption("requested_waiting", "Запрашивали, ждём"),
            QuizOption("no", "Пока нет"),
            QuizOption("unsure", "Не понимаю, какой именно документ нужен"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_3",
        question="Есть ли у вас документы, подтверждающие родство?",
        input_type="choice",
        options=(
            QuizOption("complete", "Да, всё собрано"),
            QuizOption("partial", "Есть часть документов"),
            QuizOption("none", "Пока нет"),
            QuizOption("unsure", "Не понимаю, чего именно не хватает"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_4",
        question="Кроме основных документов, всё ли готово для подачи заявления?",
        input_type="choice",
        options=(
            QuizOption("ready", "Да, всё основное готово"),
            QuizOption("collecting", "Частично готово, ещё собираем"),
            QuizOption("missing_details", "Не хватает отдельных документов или сведений"),
            QuizOption("need_guidance", "Не понимаю, что должно входить в полный пакет"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_5",
        question="Уже подавали документы официально?",
        input_type="choice",
        options=(
            QuizOption("not_yet", "Нет, ещё не подавали"),
            QuizOption("partial", "Подавали часть документов"),
            QuizOption("full_waiting", "Подали полный пакет"),
            QuizOption("unclear_submission", "Что-то передавали, но не уверен(а), что это считается официальной подачей"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_doc_6",
        question="Куда вы подавали документы?",
        input_type="choice",
        options=(
            QuizOption("military_unit", "В воинскую часть"),
            QuizOption("voenkomat", "В военкомат"),
            QuizOption("sfr_mfc", "В СФР или МФЦ"),
            QuizOption("sogaz", "По страховой линии / в СОГАЗ"),
            QuizOption("several", "В несколько мест"),
            QuizOption("other", "В другое место"),
        ),
        visible_if=after_filing_only,
    ),
    QuizStep(
        id="clarify_feedback_1",
        question="Что сейчас происходит после подачи?",
        input_type="choice",
        options=(
            QuizOption("just_waiting", "Просто ждём, ответа ещё нет"),
            QuizOption("waiting_too_long", "Ждём уже слишком долго"),
            QuizOption("need_more_documents", "Попросили донести документы"),
            QuizOption("refusal", "Получили отказ"),
            QuizOption("partial_payment", "Пришла только часть выплат"),
            QuizOption("response_unclear", "Был ответ, но не понимаю, что он означает"),
        ),
        visible_if=after_filing_only,
    ),
    QuizStep(
        id="clarify_goal_1",
        question="Что сейчас мешает больше всего?",
        input_type="choice",
        options=(
            QuizOption("no_start", "Не понимаю, с чего начать"),
            QuizOption("missing_docs", "Не понимаю, каких документов не хватает"),
            QuizOption("filing_order", "Не понимаю, куда и в каком порядке подавать"),
            QuizOption("after_filing", "Не понимаю, что делать после подачи"),
            QuizOption("authority_response", "Не понимаю ответ ведомства"),
        ),
        visible_if=always_visible,
    ),
    QuizStep(
        id="clarify_goal_2",
        question="Что вам сейчас нужнее всего?",
        input_type="choice",
        options=(
            QuizOption("next_steps", "Пошагово понять, что делать дальше"),
            QuizOption("check_package", "Проверить, всё ли готово по документам"),
            QuizOption("find_blocker", "Понять, где сейчас застопорилось дело"),
            QuizOption("full_overview", "Получить общую картину по моей ситуации"),
        ),
        visible_if=always_visible,
    ),
)
