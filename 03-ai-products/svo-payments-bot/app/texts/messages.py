"""Тексты бота на русском."""

from __future__ import annotations

from typing import Any

from aiogram.fsm.state import State

from app.services import calculator as calc
from app.states.questionnaire import QuestionnaireStates as Q
from app.utils.money import format_money_ru


def welcome(*, has_saved_questionnaire: bool = False) -> str:
    """Без имени из профиля Telegram — нейтральное обращение."""
    extra = ""
    if has_saved_questionnaire:
        extra = (
            "У вас сохранён <b>незавершённый</b> предварительный расчёт — можете продолжить кнопкой ниже "
            "или выбрать любой другой вариант.\n\n"
        )
    return (
        "👋 Здравствуйте.\n\n"
        "Я помогу <b>предварительно</b> понять, какие выплаты могут быть положены вашей семье, "
        "из чего они складываются и что делать дальше.\n\n"
        "📌 Если документы ещё не подавали — станет понятнее, какие формы нужны и куда обращаться.\n"
        "⏳ Если уже подали — разберёмся, где чаще всего бывает задержка и как ускорить процесс.\n\n"
        "Сверху — два <b>коротких квиза</b> (помечены «квиз»); ниже — прежняя <b>длинная анкета</b>, если нужен старый сценарий.\n\n"
        f"{extra}"
        "<i>Это бесплатно и ни к чему вас не обязывает.</i>\n\n"
        "Выберите подходящий вариант:"
    )


def help_text() -> str:
    return (
        "📌 Короткая анкета: предварительный расчёт и при необходимости оформление заявки на разбор ситуации.\n\n"
        "/start — главный экран\n"
        "/restart — сбросить ответы и начать с выбора ситуации\n"
        "/help — эта справка"
    )


def _progress_line(state: State, data: dict[str, Any]) -> str:
    scenario = data.get("scenario")
    if state == Q.choose_scenario:
        return ""
    if scenario == "first_time":
        total = 6
        order = [
            Q.deceased,
            Q.applicant,
            Q.complex_detail,
            Q.recipients,
            Q.recipients_many,
            Q.documents,
            Q.region,
        ]
    else:
        total = 8
        order = [
            Q.deceased,
            Q.applicant,
            Q.complex_detail,
            Q.recipients,
            Q.recipients_many,
            Q.problem,
            Q.submitted,
            Q.waiting,
            Q.region,
        ]
    # Упрощённый номер шага без ветвления complex/many в счётчике
    step_map = {
        Q.deceased.state: 1,
        Q.applicant.state: 2,
        Q.complex_detail.state: 2,
        Q.recipients.state: 3,
        Q.recipients_many.state: 3,
        Q.documents.state: 4,
        Q.problem.state: 4,
        Q.submitted.state: 5,
        Q.waiting.state: 6,
        Q.region.state: total,
    }
    cur = step_map.get(state.state, 1)
    extra = ""
    if state == Q.complex_detail:
        extra = " · уточнение"
    if state == Q.recipients_many:
        extra = " · уточнение числа"
    return (
        f"\n\n<i>Вопрос {cur} из {total}{extra}. "
        f"Так предварительный расчёт будет ближе к вашим обстоятельствам.</i>"
    )


def question_text(state: State, data: dict[str, Any]) -> str:
    scenario = data.get("scenario")
    prog = _progress_line(state, data)

    if state == Q.deceased:
        return "📌 <b>Кем был погибший?</b>\nЕсли не уверены — нажмите «Не знаю»." + prog

    if state == Q.applicant:
        return (
            "👨‍👩‍👧 <b>Кто вы по отношению к погибшему?</b>\n"
            "От этого зависит, какие меры поддержки чаще рассматривают в первую очередь." + prog
        )

    if state == Q.complex_detail:
        return "⚠️ <b>Что ближе к вашей ситуации?</b>\nСпокойно выберите вариант — так я точнее подстрою подсказки." + prog

    if state == Q.recipients:
        return (
            "👨‍👩‍👧 <b>Кроме вас, кто ещё может претендовать на выплаты?</b>\n"
            "Нужно для ориентировочной доли на человека." + prog
        )

    if state == Q.recipients_many:
        return (
            "📌 <b>Напишите числом, сколько человек может быть получателями вместе с вами</b> "
            "(например, <code>6</code>).\n"
            "Допустимо от 5 до 30 — это только ориентир для расчёта." + prog
        )

    if state == Q.documents:
        return (
            "📄 <b>Что уже есть на руках?</b>\n"
            "Можно выбрать несколько вариантов, затем нажмите «Готово».\n\n"
            "<i>После этого останется указать регион.</i>" + prog
        )

    if state == Q.problem:
        return "⏳ <b>Что сейчас происходит?</b>\nВыберите ближайший вариант." + prog

    if state == Q.submitted:
        return "📌 <b>Куда уже подавали документы?</b>" + prog

    if state == Q.waiting:
        return "⏳ <b>Сколько уже ждёте ответа или движения по делу?</b>" + prog

    if state == Q.region:
        extra = "\n\n<i>Остался последний вопрос анкеты перед расчётом.</i>"
        return (
            "📌 <b>Из какого вы региона?</b>\n"
            "Напишите одним сообщением, например: <code>Ростовская область</code>." + extra + prog
        )

    if state == Q.lead_name:
        return (
            "📞 <b>Оформление заявки</b>\n"
            "Как к вам обращаться? Напишите имя одним сообщением."
        )

    if state == Q.lead_phone:
        name = (data.get("lead_name") or "").strip()
        if name:
            return f"{name}, <b>оставьте номер телефона для связи</b>.\nПодойдёт +7… или 8…"
        return "<b>Оставьте номер телефона для связи</b>.\nПодойдёт +7… или 8…"

    if state == Q.lead_contact:
        return (
            "💬 <b>Укажите Telegram или WhatsApp, если так удобнее.</b>\n"
            "Или нажмите «Пропустить»."
        )

    if state == Q.lead_comment:
        return (
            "📝 <b>Коротко опишите ситуацию, если хотите.</b>\n"
            "Или нажмите «Пропустить»."
        )

    if state == Q.consent:
        return (
            "🔒 <b>Согласие на обработку персональных данных</b>\n\n"
            "Для связи с вами и предварительного анализа ситуации нужно согласие.\n\n"
            "<i>Я даю согласие на обработку персональных данных для связи со мной и предварительного "
            "анализа моей ситуации.</i>"
        )

    if state == Q.consent_refused:
        return (
            "Без согласия я не могу сохранить заявку.\n\n"
            "При необходимости вы можете вернуться к выбору ситуации или связаться другим способом — кнопки ниже."
        )

    return ""


def _personalized_closing(data: dict[str, Any]) -> str:
    role = data.get("applicant_role")
    scenario = data.get("scenario")
    lines: list[str] = []
    if scenario == "first_time":
        lines.append(
            "📌 В начале пути важно не потерять время и деньги из‑за ошибок в пакете или маршруте обращений. "
            "Спокойная «дорожная карта» и готовые формы обычно экономят недели."
        )
    if scenario == "already_filed":
        lines.append(
            "⏳ Когда дело уже в работе, чаще всего решает сочетание: комплект документов, корректные обращения "
            "и понимание, на каком этапе справедливо «подтолкнуть» процесс."
        )
    if role in ("mother", "father"):
        lines.append(
            "👨‍👩‍👧 Родителям особенно важно не тащить всё в одиночку — есть понятная последовательность действий."
        )
    elif role == "spouse":
        lines.append(
            "💍 Вам, как близкому человеку, важна ясность и опора — здесь помогает структурированный разбор ситуации."
        )
    elif role in ("child_u18", "child_student"):
        lines.append("👶 Если вы ребёнок погибшего, отдельно проверим меры поддержки, которые могут относиться к детям.")
    return "\n\n".join(lines) if lines else ""


def result_screen(data: dict[str, Any]) -> str:
    rc = int(data.get("recipients_count") or 1)
    base = calc.get_base_total()
    share = calc.get_personal_share(rc)
    role = data.get("applicant_role")
    child_ok = calc.has_child_monthly_payment(role)
    scenario = data.get("scenario")

    months = data.get("months_waiting")
    if months is None and scenario == "already_filed":
        months = calc.months_from_waiting_key(data.get("waiting_key"))
    lost = calc.calculate_lost_income(share, int(months or 0)) if months is not None and scenario == "already_filed" else None

    fam = format_money_ru(base)
    sh = format_money_ru(share)

    parts: list[str] = [
        "✅ <b>Предварительный расчёт</b>\n",
        f"💰 Предварительно вашей семье могут ориентироваться выплаты от <b>{fam} ₽</b>.",
    ]
    if rc > 1:
        parts.append(
            f"Если получателей несколько, <b>ваша ориентировочная доля</b> может быть около <b>{sh} ₽</b> "
            "(деление условное, без учёта индивидуальных обстоятельств)."
        )
    parts.append("")
    parts.append("📌 <b>Из чего складывается базовая сумма</b>")
    parts.append(f"• 💰 Президентская выплата — {format_money_ru(calc.PRESIDENTIAL_PAYMENT)} ₽")
    parts.append(f"• 💰 Единовременное пособие — {format_money_ru(calc.BENEFIT_306_FZ)} ₽")
    parts.append(f"• 💰 Страховая / компенсационная выплата — {format_money_ru(calc.INSURANCE_PAYMENT)} ₽")
    if child_ok:
        parts.append(f"• 👶 Если есть право: ежемесячно ~{format_money_ru(calc.CHILD_MONTHLY_PAYMENT)} ₽ на ребёнка")
    parts.append("• ➕ Дополнительно могут быть региональные выплаты и другие меры поддержки")
    parts.append("")

    if scenario == "already_filed" and months and lost is not None and lost > 0:
        parts.append("⏳ <b>Про ожидание — простыми словами</b>")
        parts.append(
            "Каждый месяц без движения — это и стресс, и упущенная польза для семьи.\n"
            "Ниже — <b>не юридическая неустойка</b>, а <b>предварительная оценка</b> «упущенного дохода» "
            "при очень консервативной логике <b>1,2% в месяц</b> от вашей ориентировочной доли."
        )
        parts.append(f"Ориентировочная цена задержки: <b>{format_money_ru(lost)} ₽</b>.")
        parts.append("")

    parts.append("📌 <b>Что вы получите, обратившись ко мне</b>")
    parts.append(
        "• полный список выплат именно по вашей ситуации;\n"
        "• готовые формы заявлений и обращений;\n"
        "• дорожную карту: куда, что и с чем подавать;\n"
        "• предварительную оценку того, что может задерживать выплаты;\n"
        "• план: либо подать правильно с нуля, либо ускорить уже поданное дело."
    )
    pc = _personalized_closing(data)
    if pc:
        parts.append("")
        parts.append(pc)

    parts.append("")
    parts.append(
        "⚠️ <i>Это предварительный расчёт. Точный состав выплат зависит от статуса погибшего, "
        "состава получателей, документов и региона.</i>"
    )
    return "\n".join(parts)


def fallback_hint() -> str:
    return (
        "Пожалуйста, ответьте в формате анкеты: выберите вариант кнопкой под сообщением "
        "или нажмите /restart, чтобы вернуться к началу."
    )


def phone_invalid() -> str:
    return "⚠️ Не получилось распознать номер. Попробуйте в формате <code>+7…</code> или <code>8…</code>."


def region_invalid() -> str:
    return "⚠️ Напишите регион одним сообщением — без пустой строки."


def recipients_count_invalid() -> str:
    return "⚠️ Напишите целое число от 5 до 30."


def name_invalid() -> str:
    return "⚠️ Напишите, пожалуйста, имя текстом."


def thank_you_completed() -> str:
    return (
        "✅ Спасибо. Заявка отправлена.\n"
        "Я свяжусь с вами после предварительного анализа ситуации."
    )
