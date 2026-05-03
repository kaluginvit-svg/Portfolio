"""Квизы «Прояснить ситуацию» и «Рассчитать выплаты» + контакты и webhook."""

from __future__ import annotations

import logging
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.config import Settings
from app.handlers.render import show_step
from app.handlers.ui import edit_or_send
from app.keyboards import quiz_keyboards as qkb
from app.legal_docs import consent_doc_path, policy_doc_path, resolve_legal_urls
from app.quizzes.calculate_engine import compute_payment_result
from app.quizzes.clarify_derived import compute_clarify_derived
from app.quizzes.config_calculate import CALCULATE_STEPS
from app.quizzes.config_clarify import CLARIFY_STEPS
from app.quizzes.consultant_format import format_calculate_consultant_message, format_clarify_consultant_message
from app.quizzes.engine import current_step, is_quiz_questions_finished, total_visible, visible_steps
from app.quizzes.webhook_payload import QUIZ_CALCULATE, QUIZ_CLARIFY, build_quiz_webhook_payload
from app.repositories.lead_repository import LeadRepository
from app.services import webhook_lead
from app.states.questionnaire import QuestionnaireStates as Q
from app.states.quiz_flow import QuizFlowStates as Z
from app.texts import messages
from app.utils.phone import normalize_phone

log = logging.getLogger(__name__)
router = Router()

STEPS_MAP = {
    QUIZ_CLARIFY: CLARIFY_STEPS,
    QUIZ_CALCULATE: CALCULATE_STEPS,
}

_QUIZ_TITLE_HTML = {
    QUIZ_CLARIFY: "🧭 <b>Квиз «Прояснить ситуацию»</b>",
    QUIZ_CALCULATE: "🔢 <b>Квиз «Рассчитать выплаты»</b>",
}


def _steps(quiz_type: str):
    return STEPS_MAP[quiz_type]


def _legal_urls(settings: Settings) -> tuple[str, str]:
    return resolve_legal_urls(
        public_base_url=settings.legal_docs_public_base_url,
        consent_url_override=settings.personal_data_consent_url,
        policy_url_override=settings.personal_data_policy_url,
    )


async def _render_question(anchor: Message, state: FSMContext) -> None:
    data = await state.get_data()
    qtype = data.get("quiz_type")
    if not qtype:
        return
    answers: dict[str, str] = dict(data.get("quiz_answers") or {})
    idx = int(data.get("quiz_step_index") or 0)
    steps = _steps(qtype)
    vis = visible_steps(steps, answers)
    n = len(vis)
    if idx < 0:
        idx = 0
    if idx >= n:
        await _after_questions(anchor, state)
        return
    step = vis[idx]
    head = _QUIZ_TITLE_HTML.get(qtype, "")
    prog = f"\n\n<i>Вопрос {idx + 1} из {n}</i>"
    text = f"{head}\n\n{step.question}{prog}" if head else f"{step.question}{prog}"
    markup = qkb.for_quiz_step(step) if step.input_type == "choice" else qkb.region_nav()
    await edit_or_send(anchor, text=text, reply_markup=markup, state=state)


async def _after_questions(anchor: Message, state: FSMContext) -> None:
    data = await state.get_data()
    qtype = data.get("quiz_type")
    answers: dict[str, str] = dict(data.get("quiz_answers") or {})
    if qtype == QUIZ_CLARIFY:
        derived = compute_clarify_derived(answers)
        await state.update_data(quiz_derived=derived)
        short = "Спасибо. Осталось оставить контакт — консультант свяжется с вами."
    else:
        calc = compute_payment_result(answers)
        await state.update_data(quiz_calc_result=calc)
        short = (
            f"{calc['headline_prefix']}: <b>{calc['headline_amount']}</b>\n"
            f"Ориентир доли: {calc['personal_share_text']}\n\n"
            "Оставьте имя и телефон — мы уточним детали."
        )
    await state.set_state(Z.lead_name)
    await anchor.answer(short, parse_mode="HTML")
    await anchor.answer(
        "Как вас зовут?",
        reply_markup=qkb.quiz_lead_name_nav(),
        parse_mode="HTML",
    )


async def _sync_quiz_index(state: FSMContext) -> None:
    """Если список видимых шагов укоротился — подправить индекс."""
    data = await state.get_data()
    qtype = data.get("quiz_type")
    if not qtype:
        return
    answers: dict[str, str] = dict(data.get("quiz_answers") or {})
    idx = int(data.get("quiz_step_index") or 0)
    steps = _steps(qtype)
    mx = total_visible(steps, answers)
    if idx > mx:
        await state.update_data(quiz_step_index=mx)


@router.callback_query(StateFilter(Q.choose_scenario), F.data.in_({"qz:clarify", "qz:calc"}))
async def quiz_entry(
    call: CallbackQuery,
    state: FSMContext,
    repo: LeadRepository,
) -> None:
    await call.answer()
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    await repo.delete_incomplete(uid)
    data = await state.get_data()
    keep = {
        k: data[k]
        for k in ("telegram_user_id", "telegram_username", "ui_message_id")
        if k in data
    }
    qtype = QUIZ_CLARIFY if call.data == "qz:clarify" else QUIZ_CALCULATE
    log.info("Старт квиза user=%s callback=%s quiz_type=%s", uid, call.data, qtype)
    await state.set_data(
        {
            **keep,
            "quiz_type": qtype,
            "quiz_answers": {},
            "quiz_step_index": 0,
            "quiz_derived": None,
            "quiz_calc_result": None,
            "quiz_lead_name": None,
            "quiz_lead_phone": None,
            "quiz_lead_phone_raw": None,
        }
    )
    await state.set_state(Z.question)
    await _render_question(call.message, state)


@router.callback_query(StateFilter(Z.question), F.data.startswith("qza|"))
async def quiz_answer_cb(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if not call.message or not call.from_user or not call.data:
        return
    parts = call.data.split("|", 2)
    if len(parts) != 3:
        return
    _, step_id, value = parts
    data = await state.get_data()
    qtype = data.get("quiz_type")
    if not qtype:
        return
    answers: dict[str, str] = dict(data.get("quiz_answers") or {})
    idx = int(data.get("quiz_step_index") or 0)
    steps = _steps(qtype)
    vis = visible_steps(steps, answers)
    if idx >= len(vis) or vis[idx].id != step_id:
        await _sync_quiz_index(state)
        await _render_question(call.message, state)
        return
    answers[step_id] = value
    idx += 1
    await state.update_data(quiz_answers=answers, quiz_step_index=idx)
    if is_quiz_questions_finished(steps, answers, idx):
        await _after_questions(call.message, state)
    else:
        await _render_question(call.message, state)


@router.message(StateFilter(Z.question), F.text)
async def quiz_region_text(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    qtype = data.get("quiz_type")
    if not qtype:
        return
    answers = dict(data.get("quiz_answers") or {})
    idx = int(data.get("quiz_step_index") or 0)
    steps = _steps(qtype)
    step = current_step(steps, answers, idx)
    if not step or step.input_type != "text":
        await message.answer("Выберите вариант кнопкой под сообщением бота.", parse_mode="HTML")
        return
    region = (message.text or "").strip()
    if not region or len(region) > 200:
        await message.answer("Напишите регион коротко (до 200 символов).", parse_mode="HTML")
        return
    answers[step.id] = region
    idx += 1
    await state.update_data(quiz_answers=answers, quiz_step_index=idx)
    if is_quiz_questions_finished(steps, answers, idx):
        await _after_questions(message, state)
    else:
        await _render_question(message, state)


@router.callback_query(StateFilter(Z.question), F.data == "nav:back")
async def quiz_nav_back_q(call: CallbackQuery, state: FSMContext) -> None:
    if not call.from_user or not call.message:
        return
    data = await state.get_data()
    qtype = data.get("quiz_type")
    if not qtype:
        await call.answer()
        return
    answers = dict(data.get("quiz_answers") or {})
    idx = int(data.get("quiz_step_index") or 0)
    steps = _steps(qtype)
    vis = visible_steps(steps, answers)
    if idx <= 0:
        await call.answer()
        await state.set_data(
            {
                k: data[k]
                for k in ("telegram_user_id", "telegram_username", "ui_message_id")
                if k in data
            }
        )
        await state.set_state(Q.choose_scenario)
        await show_step(call.message, state, Q.choose_scenario)
        return
    await call.answer()
    idx -= 1
    if idx < len(vis):
        sid = vis[idx].id
        answers.pop(sid, None)
    await state.update_data(quiz_answers=answers, quiz_step_index=idx)
    await _render_question(call.message, state)


@router.message(StateFilter(Z.lead_name), F.text)
async def quiz_lead_name(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    name = (message.text or "").strip()
    if not name or len(name) > 120:
        await message.answer(messages.name_invalid(), parse_mode="HTML")
        return
    await state.update_data(quiz_lead_name=name)
    await state.set_state(Z.lead_phone)
    await message.answer(
        "Укажите телефон для связи (можно ввести вручную или отправить контактом).",
        reply_markup=qkb.phone_reply_kb(),
        parse_mode="HTML",
    )


@router.message(StateFilter(Z.lead_phone), F.contact)
async def quiz_lead_phone_contact(
    message: Message,
    state: FSMContext,
    settings: Settings,
) -> None:
    if not message.from_user or not message.contact or not message.contact.phone_number:
        return
    raw = message.contact.phone_number
    norm = normalize_phone(raw)
    if not norm:
        await message.answer(messages.phone_invalid(), parse_mode="HTML")
        return
    await state.update_data(quiz_lead_phone=norm, quiz_lead_phone_raw=raw)
    await _send_consent_prompt(message, state, settings)


@router.message(StateFilter(Z.lead_phone), F.text)
async def quiz_lead_phone_text(message: Message, state: FSMContext, settings: Settings) -> None:
    if not message.from_user:
        return
    raw = message.text or ""
    norm = normalize_phone(raw)
    if not norm:
        await message.answer(messages.phone_invalid(), parse_mode="HTML")
        return
    await state.update_data(quiz_lead_phone=norm, quiz_lead_phone_raw=raw.strip())
    await _send_consent_prompt(message, state, settings)


async def _send_consent_prompt(message: Message, state: FSMContext, settings: Settings) -> None:
    consent_url, policy_url = _legal_urls(settings)
    lines = [
        "Нажимая «Согласен и продолжить», вы соглашаетесь на обработку персональных данных.",
        "",
    ]
    if consent_url and policy_url:
        lines.append(f'<a href="{consent_url}">Согласие на обработку ПДн</a>')
        lines.append(f'<a href="{policy_url}">Политика обработки ПДн</a>')
    else:
        lines.append(
            "Документы «Согласие на обработку ПДн» и «Политика конфиденциальности» "
            "лежат в корне проекта; для ссылок задайте LEGAL_DOCS_PUBLIC_BASE_URL или "
            "PERSONAL_DATA_CONSENT_URL / PERSONAL_DATA_POLICY_URL."
        )
    text = "\n".join(lines)
    await state.set_state(Z.consent)
    await message.answer(
        text,
        reply_markup=qkb.quiz_consent_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    cpath = consent_doc_path()
    ppath = policy_doc_path()
    try:
        if cpath.is_file():
            await message.answer_document(FSInputFile(cpath))
        if ppath.is_file():
            await message.answer_document(FSInputFile(ppath))
    except Exception:
        log.exception("Не удалось отправить файлы ПДн")


@router.callback_query(StateFilter(Z.consent), F.data == "qz:consent:no")
async def quiz_consent_no(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if not call.message:
        return
    await state.set_state(Z.consent_refused)
    await call.message.answer(
        "Без согласия на обработку данных мы не можем отправить заявку. "
        "Если передумаете — нажмите «В начало».",
        reply_markup=qkb.quiz_consent_refused_kb(),
        parse_mode="HTML",
    )


@router.callback_query(StateFilter(Z.consent), F.data == "qz:consent:yes")
async def quiz_consent_yes(
    call: CallbackQuery,
    state: FSMContext,
    settings: Settings,
    bot: Bot,
) -> None:
    await call.answer()
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    data = await state.get_data()
    qtype = data.get("quiz_type")
    answers: dict[str, str] = dict(data.get("quiz_answers") or {})
    name = (data.get("quiz_lead_name") or "").strip()
    phone = (data.get("quiz_lead_phone") or "").strip()
    if not qtype or not name or not phone:
        await call.message.answer("Не хватает данных. Нажмите /start и пройдите квиз заново.", parse_mode="HTML")
        return
    consent_url, policy_url = _legal_urls(settings)
    payload = build_quiz_webhook_payload(
        quiz_type=qtype,
        raw_answers=answers,
        lead_name=name,
        lead_phone=phone,
        personal_data_consent=True,
        consent_doc_url=consent_url or "",
        policy_doc_url=policy_url or "",
    )
    if settings.lead_webhook_url:
        await webhook_lead.post_quiz_webhook(
            settings.lead_webhook_url,
            settings.lead_webhook_secret,
            payload,
        )
    if settings.admin_chat_id:
        try:
            if qtype == QUIZ_CLARIFY:
                d = compute_clarify_derived(answers)
                body = format_clarify_consultant_message(d)
            else:
                c = compute_payment_result(answers)
                body = format_calculate_consultant_message(lead_name=name, lead_phone=phone, calc=c)
            await bot.send_message(settings.admin_chat_id, body, parse_mode="HTML")
        except Exception:
            log.exception("Не удалось отправить уведомление по квизу админу")
    await call.message.answer(
        "Заявка принята. Спасибо! Мы свяжемся с вами по указанному телефону.",
        parse_mode="HTML",
    )
    await state.clear()
    log.info("Квиз завершён user=%s type=%s", uid, qtype)


@router.callback_query(StateFilter(Z.lead_name), F.data == "nav:back")
async def quiz_back_from_name(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if not call.message:
        return
    data = await state.get_data()
    qtype = data.get("quiz_type") or QUIZ_CLARIFY
    answers = dict(data.get("quiz_answers") or {})
    steps = _steps(qtype)
    vis = visible_steps(steps, answers)
    if not vis:
        await state.set_state(Z.question)
        await state.update_data(quiz_step_index=0)
        await _render_question(call.message, state)
        return
    last = vis[-1]
    answers.pop(last.id, None)
    new_vis = visible_steps(steps, answers)
    new_idx = max(0, len(new_vis) - 1)
    await state.update_data(quiz_answers=answers, quiz_step_index=new_idx, quiz_derived=None, quiz_calc_result=None)
    await state.set_state(Z.question)
    await _render_question(call.message, state)


@router.callback_query(StateFilter(Z.lead_phone), F.data == "nav:back")
async def quiz_back_from_phone(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if not call.message:
        return
    await state.set_state(Z.lead_name)
    await call.message.answer("Как вас зовут?", reply_markup=qkb.quiz_lead_name_nav(), parse_mode="HTML")


@router.callback_query(StateFilter(Z.consent), F.data == "nav:back")
async def quiz_back_from_consent(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    if not call.message:
        return
    await state.set_state(Z.lead_phone)
    await call.message.answer(
        "Укажите телефон для связи.",
        reply_markup=qkb.phone_reply_kb(),
        parse_mode="HTML",
    )
