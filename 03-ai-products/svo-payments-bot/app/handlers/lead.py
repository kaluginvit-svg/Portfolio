"""Лид-форма и согласие на ПДн."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.handlers.common import _go, _persist
from app.handlers.render import show_step
from app.repositories.lead_repository import LeadRepository
from app.services import formatter
from app.services import lead_service
from app.services import webhook_lead
from app.states.questionnaire import QuestionnaireStates as Q
from app.texts import messages
from app.utils.phone import normalize_phone

log = logging.getLogger(__name__)
router = Router()


@router.message(StateFilter(Q.lead_name), F.text)
async def lead_name(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    name = (message.text or "").strip()
    if not name or len(name) > 120:
        await message.answer(messages.name_invalid(), parse_mode="HTML")
        return
    await state.update_data(lead_name=name)
    await _go(message, state, repo, message.from_user.id, Q.lead_phone)


@router.message(StateFilter(Q.lead_phone), F.text)
async def lead_phone(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    raw = message.text or ""
    norm = normalize_phone(raw)
    if not norm:
        await message.answer(messages.phone_invalid(), parse_mode="HTML")
        return
    await state.update_data(phone=raw.strip(), normalized_phone=norm)
    await _go(message, state, repo, message.from_user.id, Q.lead_contact)


@router.callback_query(StateFilter(Q.lead_contact), F.data == "ld:skip_contact")
async def skip_contact(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    await state.update_data(contact_method=None)
    await _go(call.message, state, repo, call.from_user.id, Q.lead_comment)


@router.message(StateFilter(Q.lead_contact), F.text)
async def lead_contact_text(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    t = (message.text or "").strip()[:300]
    await state.update_data(contact_method=t or None)
    await _go(message, state, repo, message.from_user.id, Q.lead_comment)


@router.callback_query(StateFilter(Q.lead_comment), F.data == "ld:skip_comment")
async def skip_comment(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    await state.update_data(comment=None)
    await _go(call.message, state, repo, call.from_user.id, Q.consent)


@router.message(StateFilter(Q.lead_comment), F.text)
async def lead_comment_text(message: Message, state: FSMContext, repo: LeadRepository) -> None:
    if not message.from_user:
        return
    t = (message.text or "").strip()[:2000]
    await state.update_data(comment=t or None)
    await _go(message, state, repo, message.from_user.id, Q.consent)


@router.callback_query(StateFilter(Q.consent), F.data == "pd:no")
async def consent_no(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
    await call.answer()
    if not call.message or not call.from_user:
        return
    uid = call.from_user.id
    await state.update_data(pdn_consent=False)
    await repo.update_incomplete(uid, {"pdn_consent": 0})
    await state.set_state(Q.consent_refused)
    await show_step(call.message, state, Q.consent_refused)
    await _persist(state, repo, uid)


@router.callback_query(StateFilter(Q.consent_refused), F.data == "pd:restart")
async def refused_restart(call: CallbackQuery, state: FSMContext, repo: LeadRepository) -> None:
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
    await state.set_data(keep)
    await _go(call.message, state, repo, uid, Q.choose_scenario)


@router.callback_query(StateFilter(Q.consent_refused), F.data == "pd:contacts")
async def refused_contacts(call: CallbackQuery, settings: Settings) -> None:
    await call.answer()
    if call.message:
        await call.message.answer(settings.contact_text, parse_mode="HTML")


@router.callback_query(StateFilter(Q.consent), F.data == "pd:yes")
async def consent_yes(
    call: CallbackQuery,
    state: FSMContext,
    repo: LeadRepository,
    settings: Settings,
    bot: Bot,
) -> None:
    await call.answer()
    if not call.from_user or not call.message:
        return
    uid = call.from_user.id
    data = await state.get_data()
    await state.update_data(pdn_consent=True)

    finalize_fields = {
        "pdn_consent": True,
        "lead_name": data.get("lead_name"),
        "phone": data.get("phone"),
        "normalized_phone": data.get("normalized_phone"),
        "contact_method": data.get("contact_method"),
        "comment": data.get("comment"),
        "scenario": data.get("scenario"),
        "status_of_deceased": data.get("status_of_deceased"),
        "applicant_role": data.get("applicant_role"),
        "complex_status": data.get("complex_status"),
        "recipients_count": data.get("recipients_count"),
        "selected_documents": data.get("selected_documents"),
        "problem_type": data.get("problem_type"),
        "submitted_to": data.get("submitted_to"),
        "months_waiting": data.get("months_waiting"),
        "region": data.get("region"),
        "base_total": data.get("base_total"),
        "personal_share": data.get("personal_share"),
        "child_monthly_payment_applicable": bool(data.get("child_monthly_payment_applicable")),
        "estimated_lost_income": data.get("estimated_lost_income"),
        "telegram_username": data.get("telegram_username"),
        "telegram_first_name": None,
    }
    await lead_service.save_completed_lead(repo, uid, finalize_fields)

    admin_payload = {
        **data,
        "telegram_user_id": uid,
        "lead_name": finalize_fields["lead_name"],
        "phone": finalize_fields["phone"],
        "normalized_phone": finalize_fields["normalized_phone"],
        "contact_method": finalize_fields["contact_method"],
        "comment": finalize_fields["comment"],
        "pdn_consent": True,
        "base_total": finalize_fields["base_total"],
        "personal_share": finalize_fields["personal_share"],
        "child_monthly_payment_applicable": finalize_fields["child_monthly_payment_applicable"],
        "estimated_lost_income": finalize_fields["estimated_lost_income"],
    }

    if settings.lead_webhook_url:
        await webhook_lead.post_lead_completed(
            settings.lead_webhook_url,
            settings.lead_webhook_secret,
            admin_payload,
        )

    if settings.admin_chat_id:
        try:
            await bot.send_message(
                settings.admin_chat_id,
                formatter.format_admin_lead_message(admin_payload),
                parse_mode="HTML",
            )
        except Exception:
            log.exception("Не удалось отправить уведомление админу")

    await call.message.answer(messages.thank_you_completed(), parse_mode="HTML")
    await state.clear()
    log.info("Заявка завершена user=%s", uid)
