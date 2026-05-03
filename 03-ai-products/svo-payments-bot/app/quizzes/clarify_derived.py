"""Вычисление derived-полей квиза «Прояснить ситуацию»."""

from __future__ import annotations

from typing import Any

CONSULTANT_STEPS_BY_BLOCKER: dict[str, tuple[str, str, str]] = {
    "no_start": (
        "Уточнить, что человек уже знает о своей ситуации и какие документы у него есть на руках прямо сейчас.",
        "Объяснить стартовую последовательность действий простыми шагами: что нужно получить сначала, что проверить потом.",
        "Дать понятный маршрут до первого практического результата, чтобы человек понял, с чего начинать без лишних действий.",
    ),
    "missing_death_certificate": (
        "Уточнить, на каком этапе сейчас получение свидетельства о смерти и есть ли уже подтверждающие документы.",
        "Проверить, можно ли параллельно готовить остальные части пакета, чтобы не терять время.",
        "Дать человеку следующий порядок действий до момента, когда можно будет выходить на полноценную подачу.",
    ),
    "missing_military_notice": (
        "Уточнить, какой именно документ уже запрашивали и что человеку говорили по срокам или порядку получения.",
        "Проверить, какие части пакета уже готовы и чего не хватает именно из документов по обстоятельствам.",
        "Дать человеку ближайший маршрут: что дожидаться, что можно готовить параллельно и когда возвращаться к подаче.",
    ),
    "kinship_gap": (
        "Уточнить, какие документы по родству уже есть и где именно в цепочке подтверждения образовался пробел.",
        "Проверить, достаточно ли текущих документов для подтверждения связи заявителя с погибшим.",
        "Сказать, какие документы или связки документов нужно добрать, чтобы закрыть вопрос по родству полностью.",
    ),
    "package_unclear": (
        "Уточнить, какие документы уже собраны фактически, а какие человек только предполагает нужными.",
        "Проверить полноту пакета и отделить обязательные документы от второстепенных.",
        "Дать человеку финальный список того, что нужно добрать до готовности к подаче.",
    ),
    "not_filed_yet": (
        "Уточнить, насколько пакет реально готов и чего именно человеку не хватает для выхода на подачу.",
        "Проверить, куда в его ситуации правильнее подавать документы в первую очередь.",
        "Дать человеку чёткий маршрут подачи: куда идти, в какой последовательности и с чем на руках.",
    ),
    "partial_filing": (
        "Уточнить, что уже было подано официально и есть ли подтверждение приёма документов.",
        "Проверить, какие документы или сведения ещё требуется донести для завершения подачи.",
        "Сформировать для человека ближайший план закрытия подачи без повторных потерь времени.",
    ),
    "waiting_after_filing": (
        "Уточнить дату подачи, маршрут подачи и наличие подтверждения, что документы действительно приняты.",
        "Понять, где именно сейчас может находиться кейс и похоже ли это на обычное ожидание или на зависание.",
        "Дать следующий рабочий сценарий: запрос статуса, сопровождение, дожим или иное действие по ситуации.",
    ),
    "response_after_filing": (
        "Уточнить, какой именно ответ или обратная связь уже были получены и в каком виде.",
        "Сопоставить этот ответ с текущим этапом дела и понять, что он реально означает для кейса.",
        "Дать конкретный следующий шаг: что донести, что оспаривать, куда обращаться дальше или как сопровождать дело.",
    ),
}

PRIMARY_LABELS: dict[str, str] = {
    "no_start": "Не начинал путь",
    "missing_death_certificate": "Нет свидетельства о смерти",
    "missing_military_notice": "Нет документа из части",
    "kinship_gap": "Не до конца закрыт вопрос по родству",
    "package_unclear": "Неясен состав полного пакета",
    "not_filed_yet": "Официальной подачи ещё не было",
    "partial_filing": "Подали только часть документов",
    "waiting_after_filing": "Слишком долго нет движения после подачи",
    "response_after_filing": "Есть проблемный ответ после подачи",
}

SECONDARY_LINES: dict[str, str] = {
    "missing_death_certificate": "— Нет свидетельства о смерти",
    "missing_military_notice": "— Нет документа из части",
    "kinship_gap": "— Не до конца закрыт вопрос по родству",
    "package_unclear": "— Неясен состав полного пакета",
    "not_filed_yet": "— Официальной подачи ещё не было",
    "partial_filing": "— Подали только часть документов",
    "waiting_after_filing": "— Слишком долго нет движения после подачи",
    "response_after_filing": "— Есть проблемный ответ после подачи",
    "none": "",
}


def _death_label(v: str | None) -> str:
    return {
        "yes": "есть",
        "in_progress": "оформляют, ждут",
        "no": "нет",
    }.get(v or "", v or "")


def _military_label(v: str | None) -> str:
    return {
        "yes": "есть",
        "requested_waiting": "запросили, ждут",
        "no": "нет",
        "unsure": "не понимают, какой документ нужен",
    }.get(v or "", v or "")


def _kinship_label(v: str | None) -> str:
    return {
        "complete": "собраны",
        "partial": "частично собраны",
        "none": "нет",
        "unsure": "не понимают, чего не хватает",
    }.get(v or "", v or "")


def _pack_label(v: str | None) -> str:
    return {
        "ready": "готов",
        "collecting": "ещё в работе",
        "missing_details": "не хватает отдельных документов или сведений",
        "need_guidance": "не понимают, что входит в пакет",
    }.get(v or "", v or "")


def _filing_status_label(v: str | None) -> str:
    return {
        "not_yet": "Официально не подавали",
        "partial": "Подавали часть документов",
        "full_waiting": "Подали полный пакет",
        "unclear_submission": "Что-то передавали, но статус подачи неясен",
    }.get(v or "", v or "")


def _filing_route_label(v: str | None) -> str:
    if not v or v == "not_yet":
        return "не подавали"
    return {
        "military_unit": "воинская часть",
        "voenkomat": "военкомат",
        "sfr_mfc": "СФР / МФЦ",
        "sogaz": "СОГАЗ / страховая линия",
        "several": "в несколько мест",
        "other": "другое место",
    }.get(v, v)


def _user_focus_label(g1: str | None, g2: str | None) -> str:
    order = (g2, g1)
    keys = {
        "no_start": "Понять, с чего начать",
        "missing_docs": "Понять, каких документов не хватает",
        "filing_order": "Понять, куда и как подавать",
        "after_filing": "Понять, что делать после подачи",
        "authority_response": "Понять ответ ведомства",
        "next_steps": "Пошагово понять, что делать дальше",
        "check_package": "Проверить, всё ли готово по документам",
        "find_blocker": "Понять, где застопорилось дело",
        "full_overview": "Получить полную картину по ситуации",
    }
    for k in order:
        if k and k in keys:
            return keys[k]
    return ""


def _stage_score(a: dict[str, str]) -> int:
    stage = a.get("clarify_stage_1") or ""
    base = {
        "start": 12,
        "collecting_docs": 28,
        "ready_to_file": 58,
        "already_filed": 74,
        "post_filing_problem": 90,
    }.get(stage, 20)

    d1 = a.get("clarify_doc_1")
    base += {"yes": 8, "in_progress": 5, "no": -5}.get(d1 or "", 0)

    d2 = a.get("clarify_doc_2")
    base += {"yes": 7, "requested_waiting": 4, "no": -3, "unsure": 2}.get(d2 or "", 0)

    d3 = a.get("clarify_doc_3")
    base += {"complete": 8, "partial": 5, "none": -5, "unsure": 2}.get(d3 or "", 0)

    d4 = a.get("clarify_doc_4")
    base += {"ready": 8, "collecting": 4, "missing_details": 2, "need_guidance": 1}.get(d4 or "", 0)

    d5 = a.get("clarify_doc_5")
    base += {"not_yet": 0, "partial": 5, "full_waiting": 8, "unclear_submission": 3}.get(d5 or "", 0)

    if d5 and d5 != "not_yet":
        fb = a.get("clarify_feedback_1")
        base += {
            "just_waiting": 2,
            "waiting_too_long": 6,
            "need_more_documents": 5,
            "refusal": 8,
            "partial_payment": 7,
            "response_unclear": 6,
        }.get(fb or "", 0)
        if a.get("clarify_doc_6") == "several":
            base += 3

    return max(0, min(100, base))


def _stage_label(score: int) -> str:
    if score <= 15:
        return "Не начинал путь"
    if score <= 35:
        return "Начальный сбор документов"
    if score <= 55:
        return "Сбор ключевого пакета"
    if score <= 70:
        return "Почти готов к подаче"
    if score <= 80:
        return "Подача идёт, пакет неполный"
    if score <= 88:
        return "Полный пакет подан, ожидание"
    return "После подачи нужен разбор и сопровождение"


def _journey_phase(a: dict[str, str]) -> tuple[str, str]:
    stage = a.get("clarify_stage_1") or ""
    d5 = a.get("clarify_doc_5")
    if stage == "post_filing_problem" or (d5 and d5 != "not_yet"):
        return "post_filing", "После подачи"
    if stage == "ready_to_file":
        return "ready_to_file", "Подготовка к подаче"
    if d5 in ("partial", "unclear_submission"):
        return "filing_in_progress", "Подача"
    if stage == "start":
        return "start", "До подачи"
    if stage == "already_filed":
        return "post_filing", "После подачи"
    if stage == "collecting_docs":
        return "document_collection", "До подачи"
    return "document_collection", "До подачи"


def _lead_temperature(a: dict[str, str], score: int) -> tuple[str, str]:
    stage = a.get("clarify_stage_1") or ""
    fb = a.get("clarify_feedback_1")
    if stage == "post_filing_problem" or fb in ("waiting_too_long", "refusal", "partial_payment", "response_unclear"):
        return "hot", "Горячий лид"
    if stage in ("already_filed", "ready_to_file") or a.get("clarify_doc_5") == "full_waiting" or score >= 70:
        return "warm", "Тёплый лид"
    return "cold", "Холодный лид"


def _current_case_state(a: dict[str, str]) -> str:
    d5 = a.get("clarify_doc_5")
    fb = a.get("clarify_feedback_1")
    stage = a.get("clarify_stage_1")
    if a.get("clarify_doc_6") == "several" and fb == "response_unclear":
        return "Человек обращался в несколько мест и запутался в маршруте"
    if fb == "waiting_too_long":
        return "После подачи слишком долго нет движения"
    if fb == "need_more_documents":
        return "После подачи попросили донести документы"
    if fb == "refusal":
        return "После подачи получен отказ"
    if fb == "partial_payment":
        return "После подачи пришла только часть выплат"
    if fb == "response_unclear":
        return "После подачи получен ответ, но его смысл непонятен"
    if d5 == "full_waiting" and fb == "just_waiting":
        return "Полный пакет подан, сейчас идёт ожидание"
    if d5 == "partial":
        return "Подача началась, но пакет ещё не завершён"
    if d5 == "not_yet":
        if stage == "start":
            return "Человек ещё не начал практические действия"
        pack = a.get("clarify_doc_4")
        kin = a.get("clarify_doc_3")
        if pack in ("collecting", "missing_details") or kin in ("none", "partial", "unsure"):
            return "Человек собирает документы и не может перейти к подаче"
        if pack == "ready" and kin == "complete":
            return "Документы в основном собраны, но человек не вышел на подачу"
        return "Человек собирает документы и не может перейти к подаче"
    return "Человек собирает документы и не может перейти к подаче"


def _pick_primary_secondary(a: dict[str, str]) -> tuple[str, str | None]:
    """Возвращает (primary_key, secondary_key|None)."""
    death = a.get("clarify_doc_1")
    mil = a.get("clarify_doc_2")
    kin = a.get("clarify_doc_3")
    pack = a.get("clarify_doc_4")
    d5 = a.get("clarify_doc_5")
    fb = a.get("clarify_feedback_1")
    stage = a.get("clarify_stage_1")

    candidates: list[str] = []

    def add(key: str) -> None:
        if key not in candidates:
            candidates.append(key)

    if death == "no":
        add("missing_death_certificate")
    if mil == "no":
        add("missing_military_notice")
    if kin in ("none", "partial", "unsure"):
        add("kinship_gap")
    if pack == "need_guidance":
        add("package_unclear")
    if d5 == "partial":
        add("partial_filing")
    if fb == "waiting_too_long":
        add("waiting_after_filing")
    if fb in ("refusal", "partial_payment", "response_unclear", "need_more_documents"):
        add("response_after_filing")
    if d5 == "not_yet" and (stage == "ready_to_file" or pack == "ready"):
        add("not_filed_yet")
    if stage == "start":
        add("no_start")

    if not candidates:
        primary = "no_start"
    else:
        priority = [
            "missing_death_certificate",
            "missing_military_notice",
            "kinship_gap",
            "package_unclear",
            "response_after_filing",
            "waiting_after_filing",
            "partial_filing",
            "not_filed_yet",
            "no_start",
        ]
        primary = next((p for p in priority if p in candidates), candidates[0])

    secondary_key = None
    for c in candidates:
        if c != primary:
            secondary_key = c
            break

    return primary, secondary_key


def compute_clarify_derived(raw_answers: dict[str, str]) -> dict[str, Any]:
    a = dict(raw_answers)
    score = _stage_score(a)
    stage_label = _stage_label(score)
    journey_key, journey_ru = _journey_phase(a)
    temp_key, temp_ru = _lead_temperature(a, score)
    primary, secondary = _pick_primary_secondary(a)
    steps = CONSULTANT_STEPS_BY_BLOCKER.get(
        primary,
        CONSULTANT_STEPS_BY_BLOCKER["no_start"],
    )
    sec_line = SECONDARY_LINES.get(secondary, "") if secondary else SECONDARY_LINES["none"]

    filing_route_raw = a.get("clarify_doc_6")
    if (a.get("clarify_doc_5") or "") == "not_yet":
        filing_route_raw = "not_yet"

    g1 = a.get("clarify_goal_1")
    g2 = a.get("clarify_goal_2")
    user_focus = _user_focus_label(g1, g2)

    consultant_summary = (
        f"Этап «{stage_label}» ({score}/100), приоритет {temp_ru}. "
        f"Ключевой стопор: {PRIMARY_LABELS.get(primary, primary)}. "
        f"Запрос пользователя: {user_focus or '—'}."
    )

    return {
        "stage_score": score,
        "stage_label": stage_label,
        "journey_phase": journey_key,
        "journey_phase_label": journey_ru,
        "lead_temperature": temp_key,
        "lead_temperature_label": temp_ru,
        "death_certificate_status": _death_label(a.get("clarify_doc_1")),
        "military_notice_status": _military_label(a.get("clarify_doc_2")),
        "kinship_docs_status": _kinship_label(a.get("clarify_doc_3")),
        "submission_pack_status": _pack_label(a.get("clarify_doc_4")),
        "filing_status": _filing_status_label(a.get("clarify_doc_5")),
        "filing_route": filing_route_raw or "not_yet",
        "filing_route_label": _filing_route_label(filing_route_raw if filing_route_raw != "not_yet" else "not_yet"),
        "current_case_state": _current_case_state(a),
        "primary_blocker": primary,
        "primary_blocker_label": PRIMARY_LABELS.get(primary, primary),
        "secondary_blocker": secondary,
        "secondary_blocker_line": sec_line,
        "user_focus": user_focus,
        "user_focus_key": g2 or g1,
        "consultant_summary": consultant_summary,
        "consultant_step_1": steps[0],
        "consultant_step_2": steps[1],
        "consultant_step_3": steps[2],
    }
