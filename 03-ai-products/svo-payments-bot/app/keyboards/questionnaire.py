"""Inline-клавиатуры шагов анкеты."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards.common import attach_nav, nav_rows

DOC_KEYS = ("death", "unit", "kin", "all", "none", "what")


def scenario_choice(*, show_resume: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if show_resume:
        rows.append(
            [InlineKeyboardButton(text="▶️ Продолжить незавершённую анкету", callback_data="draft:resume")]
        )
    # Сначала квизы (ТЗ), чтобы не путать с длинной анкетой «sc:*».
    rows.extend(
        [
            [InlineKeyboardButton(text="🧭 Прояснить ситуацию (квиз)", callback_data="qz:clarify")],
            [InlineKeyboardButton(text="🔢 Рассчитать выплаты (квиз)", callback_data="qz:calc")],
            [InlineKeyboardButton(text="📋 Как раньше: выплаты с нуля", callback_data="sc:first")],
            [InlineKeyboardButton(text="📋 Как раньше: уже подали", callback_data="sc:filed")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def deceased_status() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎖 Военнослужащий по контракту", callback_data="de:contract")],
            [InlineKeyboardButton(text="🪖 Мобилизованный", callback_data="de:mob")],
            [InlineKeyboardButton(text="🤝 Доброволец", callback_data="de:vol")],
            [InlineKeyboardButton(text="🛡 Росгвардия / иное ведомство", callback_data="de:rg")],
            [InlineKeyboardButton(text="❓ Не знаю", callback_data="de:unk")],
        ]
    )
    return attach_nav(kb)


def applicant_role() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💍 Супруг / супруга", callback_data="ap:spouse")],
            [InlineKeyboardButton(text="👩 Мать", callback_data="ap:mother")],
            [InlineKeyboardButton(text="👨 Отец", callback_data="ap:father")],
            [InlineKeyboardButton(text="🧒 Ребёнок до 18 лет", callback_data="ap:c18")],
            [InlineKeyboardButton(text="🎓 Ребёнок 18–23, учусь очно", callback_data="ap:st")],
            [InlineKeyboardButton(text="📎 Представитель семьи", callback_data="ap:rep")],
            [InlineKeyboardButton(text="❓ Сложный / спорный статус", callback_data="ap:complex")],
        ]
    )
    return attach_nav(kb)


def complex_status() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Жили вместе, брак не зарегистрирован", callback_data="cx:coh")],
            [InlineKeyboardButton(text="Есть спор о родстве", callback_data="cx:kin")],
            [InlineKeyboardButton(text="Нужна помощь определить статус", callback_data="cx:hlp")],
        ]
    )
    return attach_nav(kb)


def recipients() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣ Только я", callback_data="rc:1"),
                InlineKeyboardButton(text="2️⃣ Я и ещё 1", callback_data="rc:2"),
            ],
            [
                InlineKeyboardButton(text="3️⃣ Я и ещё 2", callback_data="rc:3"),
                InlineKeyboardButton(text="4️⃣ Я и ещё 3", callback_data="rc:4"),
            ],
            [InlineKeyboardButton(text="👨‍👩‍👧‍👦 4 и более", callback_data="rc:many")],
        ]
    )
    return attach_nav(kb)


def documents(selected: set[str]) -> InlineKeyboardMarkup:
    def m(k: str, label: str) -> str:
        return ("✅ " if k in selected else "📄 ") + label

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=m("death", "Свидетельство о смерти"), callback_data="dc:death")],
            [InlineKeyboardButton(text=m("unit", "Извещение / документы из части"), callback_data="dc:unit")],
            [InlineKeyboardButton(text=m("kin", "Документы о родстве"), callback_data="dc:kin")],
            [InlineKeyboardButton(text=m("all", "Есть почти всё"), callback_data="dc:all")],
            [InlineKeyboardButton(text=m("none", "Пока ничего не собирали"), callback_data="dc:none")],
            [InlineKeyboardButton(text=m("what", "Не понимаю, что нужно"), callback_data="dc:what")],
            [InlineKeyboardButton(text="✅ Готово", callback_data="dc:done")],
        ]
    )
    return attach_nav(kb)


def problem_type() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="😶 Вообще нет ответа", callback_data="pr:none")],
            [InlineKeyboardButton(text="📎 Сказали: неполный пакет", callback_data="pr:inc")],
            [InlineKeyboardButton(text="❌ Получили отказ", callback_data="pr:rej")],
            [InlineKeyboardButton(text="💸 Часть выплат пришла, часть нет", callback_data="pr:part")],
            [InlineKeyboardButton(text="🤷 Не можем понять, где зависло", callback_data="pr:stuck")],
        ]
    )
    return attach_nav(kb)


def submitted_to() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 В воинскую часть", callback_data="su:unit")],
            [InlineKeyboardButton(text="📮 В военкомат", callback_data="su:vk")],
            [InlineKeyboardButton(text="🛡 В СОГАЗ", callback_data="su:sog")],
            [InlineKeyboardButton(text="🧾 В СФР / МФЦ", callback_data="su:sfr")],
            [InlineKeyboardButton(text="🔀 В несколько мест", callback_data="su:multi")],
        ]
    )
    return attach_nav(kb)


def waiting() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏱ До 1 месяца", callback_data="wt:w1")],
            [InlineKeyboardButton(text="⏳ 1–3 месяца", callback_data="wt:w2")],
            [InlineKeyboardButton(text="🗓 3–6 месяцев", callback_data="wt:w4")],
            [InlineKeyboardButton(text="📆 Больше 6 месяцев", callback_data="wt:w6")],
        ]
    )
    return attach_nav(kb)


def result_actions() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить разбор ситуации", callback_data="rs:lead")],
            [InlineKeyboardButton(text="Новый предварительный расчёт", callback_data="rs:again")],
            *nav_rows(with_home=False),
        ]
    )


def lead_skip_contact() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить", callback_data="ld:skip_contact")]]
    )
    return attach_nav(kb)


def lead_skip_comment() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить", callback_data="ld:skip_comment")]]
    )
    return attach_nav(kb)


def consent() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Согласен", callback_data="pd:yes"),
                InlineKeyboardButton(text="❌ Не согласен", callback_data="pd:no"),
            ],
        ]
    )
    return attach_nav(kb)


def consent_refused(contact_callback: str = "pd:contacts") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться к выбору ситуации", callback_data="pd:restart")],
            [InlineKeyboardButton(text="📌 Контакты", callback_data=contact_callback)],
        ]
    )


def region_only_nav() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nav_rows())


def lead_name_nav() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nav_rows())


def lead_phone_nav() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nav_rows())
