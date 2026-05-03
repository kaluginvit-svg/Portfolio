import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv


DATA_FILE = Path("data/payments.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

LOCAL_TZ = datetime.now().astimezone().tzinfo
UNIT_CHOICES = {
    "Неделя": "week",
    "Месяц": "month",
    "Год": "year",
}
YES_NO = {"Да": True, "Нет": False}


class PaymentForm(StatesGroup):
    title = State()
    unit = State()
    times_per_unit = State()
    amount = State()
    due_at = State()
    add_more = State()


def load_payments() -> list:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return []


def save_payments(payments: list) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as fh:
        json.dump(payments, fh, ensure_ascii=False, indent=2)


def parse_dt(text: str) -> datetime | None:
    try:
        dt = datetime.strptime(text.strip(), "%d.%m.%Y %H:%M")
        return dt.replace(tzinfo=LOCAL_TZ)
    except ValueError:
        return None


def interval_for(payment: dict) -> timedelta:
    base = {
        "week": timedelta(days=7),
        "month": timedelta(days=30),
        "year": timedelta(days=365),
    }.get(payment["unit"], timedelta(days=30))
    return base / max(payment["times_per_unit"], 1)


def ensure_next_due(payment: dict) -> tuple[datetime, bool]:
    """Return next due datetime; bool indicates if payment was mutated."""
    due = datetime.fromisoformat(payment["due_at"])
    changed = False
    now = datetime.now(tz=LOCAL_TZ)
    step = interval_for(payment)
    while due <= now:
        due += step
        changed = True
    if changed:
        payment["due_at"] = due.isoformat()
    return due, changed


async def send_reminder(bot: Bot, payment_id: str, lead: str) -> None:
    payments = load_payments()
    payment = next((p for p in payments if p["id"] == payment_id), None)
    if not payment:
        return
    text = (
        f"Напоминание о платеже «{payment['title']}» "
        f"({payment['amount']}). До платежа: {lead}."
    )
    await bot.send_message(payment["user_id"], text)


async def reschedule_payment(bot: Bot, payment_id: str, scheduler: AsyncIOScheduler) -> None:
    payments = load_payments()
    payment = next((p for p in payments if p["id"] == payment_id), None)
    if not payment:
        return
    due = datetime.fromisoformat(payment["due_at"])
    due += interval_for(payment)
    payment["due_at"] = due.isoformat()
    save_payments(payments)
    schedule_payment(bot, payment, scheduler)


def schedule_payment(bot: Bot, payment: dict, scheduler: AsyncIOScheduler) -> None:
    due, changed = ensure_next_due(payment)
    if changed:
        payments = load_payments()
        for idx, p in enumerate(payments):
            if p["id"] == payment["id"]:
                payments[idx] = payment
                break
        save_payments(payments)

    now = datetime.now(tz=LOCAL_TZ)
    offsets = [
        ("за день", timedelta(days=1)),
        ("за час", timedelta(hours=1)),
        ("за 30 минут", timedelta(minutes=30)),
    ]
    for label, delta in offsets:
        run_at = due - delta
        if run_at > now:
            scheduler.add_job(
                send_reminder,
                "date",
                id=f"{payment['id']}-{label}",
                replace_existing=True,
                run_date=run_at,
                args=[bot, payment["id"], label],
            )

    scheduler.add_job(
        reschedule_payment,
        "date",
        id=f"{payment['id']}-reschedule",
        replace_existing=True,
        run_date=due,
        args=[bot, payment["id"], scheduler],
    )


def schedule_existing(bot: Bot, scheduler: AsyncIOScheduler) -> None:
    for payment in load_payments():
        schedule_payment(bot, payment, scheduler)


def unit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=label) for label in UNIT_CHOICES.keys()],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def yes_no_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def ask_for_payment(message: Message, state: FSMContext) -> None:
    await state.set_state(PaymentForm.title)
    await message.answer("Как назовём платёж?", reply_markup=ReplyKeyboardRemove())


async def handle_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Привет! Давай настроим напоминания о платежах.\n"
        "Я буду напоминать за день, за час и за 30 минут до каждой оплаты."
    )
    await state.set_state(PaymentForm.add_more)
    await message.answer("Начать вводить платежи?", reply_markup=yes_no_keyboard())


async def title_entered(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(PaymentForm.unit)
    await message.answer(
        "Как часто совершается платёж? Выбери единицу времени.",
        reply_markup=unit_keyboard(),
    )


async def unit_entered(message: Message, state: FSMContext) -> None:
    unit = UNIT_CHOICES.get(message.text.strip())
    if not unit:
        await message.answer("Пожалуйста, выбери вариант из кнопок.", reply_markup=unit_keyboard())
        return
    await state.update_data(unit=unit)
    await state.set_state(PaymentForm.times_per_unit)
    await message.answer(
        "Сколько раз в выбранную единицу времени? (введи число)",
        reply_markup=ReplyKeyboardRemove(),
    )


async def times_entered(message: Message, state: FSMContext) -> None:
    try:
        times = int(message.text.strip())
        if times < 1:
            raise ValueError
    except ValueError:
        await message.answer("Нужно целое число от 1 и выше. Попробуй ещё раз.")
        return
    await state.update_data(times_per_unit=times)
    await state.set_state(PaymentForm.amount)
    await message.answer("Какова сумма платежа?")


async def amount_entered(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.replace(",", ".").strip())
    except ValueError:
        await message.answer("Нужна сумма числом, пример: 1999.50")
        return
    await state.update_data(amount=amount)
    await state.set_state(PaymentForm.due_at)
    await message.answer(
        "Когда ближайший платеж? Формат: 15.01.2026 18:30 (дата и время)",
    )


async def due_entered(bot: Bot, scheduler: AsyncIOScheduler, message: Message, state: FSMContext) -> None:
    due = parse_dt(message.text)
    if not due:
        await message.answer("Не понял дату. Используй формат 15.01.2026 18:30")
        return
    data = await state.get_data()
    payment = {
        "id": uuid.uuid4().hex,
        "user_id": message.from_user.id,
        "title": data["title"],
        "unit": data["unit"],
        "times_per_unit": data["times_per_unit"],
        "amount": data["amount"],
        "due_at": due.isoformat(),
    }
    payments = load_payments()
    payments.append(payment)
    save_payments(payments)
    schedule_payment(bot, payment, scheduler)

    await message.answer(
        "Готово! Я буду напоминать за день, за час и за 30 минут до платежа.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(PaymentForm.add_more)
    await message.answer("Добавить ещё платежи?", reply_markup=yes_no_keyboard())


async def more_entered(message: Message, state: FSMContext) -> None:
    answer = YES_NO.get(message.text.strip())
    if answer is None:
        await message.answer("Выбери «Да» или «Нет» кнопками.", reply_markup=yes_no_keyboard())
        return
    if answer:
        await ask_for_payment(message, state)
    else:
        await state.clear()
        await message.answer("Ок! Если понадобится что-то поменять — напиши /start.", reply_markup=ReplyKeyboardRemove())


def setup_handlers(dp: Dispatcher, bot: Bot, scheduler: AsyncIOScheduler) -> None:
    dp.message.register(handle_start, CommandStart())
    dp.message.register(title_entered, PaymentForm.title)
    dp.message.register(unit_entered, PaymentForm.unit)
    dp.message.register(times_entered, PaymentForm.times_per_unit)
    dp.message.register(amount_entered, PaymentForm.amount)
    async def _due_wrapper(message: Message, state: FSMContext) -> None:
        await due_entered(bot, scheduler, message, state)

    dp.message.register(_due_wrapper, PaymentForm.due_at)
    dp.message.register(more_entered, PaymentForm.add_more)


async def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Укажите токен бота в переменной окружения BOT_TOKEN")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone=LOCAL_TZ)
    setup_handlers(dp, bot, scheduler)
    schedule_existing(bot, scheduler)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

