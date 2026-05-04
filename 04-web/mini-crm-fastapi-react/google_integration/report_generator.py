"""Collect DB rows into 2D grids for spreadsheets."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models import Client, Deal, Task


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def metadata_block(*, title: str, row_count: int) -> list[list[str]]:
    return [
        ["Сформировано приложением mini-CRM (учебный кейс)"],
        ["Время выгрузки:", _now_iso()],
        ["Название отчёта:", title],
        ["Количество строк данных:", str(row_count)],
        [],
    ]


def clients_report_grid(session: Session) -> tuple[list[list[str]], int]:
    q = (
        session.execute(select(Client).order_by(Client.id))
        .scalars()
        .all()
    )
    meta = metadata_block(title="Клиенты", row_count=len(q))
    header = [["ID", "Имя", "Email", "Телефон", "Компания", "Статус", "Создан", "Обновлён"]]
    rows = [
        [
            str(c.id),
            c.name,
            c.email or "",
            c.phone or "",
            c.company or "",
            c.status,
            c.created_at.isoformat() if c.created_at else "",
            c.updated_at.isoformat() if c.updated_at else "",
        ]
        for c in q
    ]
    return meta + header + rows, len(rows)


def deals_report_grid(session: Session) -> tuple[list[list[str]], int]:
    q = (
        session.execute(
            select(Deal).options(joinedload(Deal.client)).order_by(Deal.id)
        )
        .scalars()
        .unique()
        .all()
    )
    meta = metadata_block(title="Сделки", row_count=len(q))
    header = [
        [
            "ID",
            "Название",
            "Сумма",
            "Валюта",
            "Стадия",
            "Клиент_ID",
            "Клиент",
            "Открыта",
            "Ожид. закрытие",
            "Создана",
            "Обновлена",
        ]
    ]
    rows = []
    for d in q:
        rows.append(
            [
                str(d.id),
                d.title,
                str(d.amount),
                d.currency,
                d.stage,
                str(d.client_id) if d.client_id else "",
                d.client.name if d.client else "",
                str(d.opened_at) if d.opened_at else "",
                str(d.expected_close) if d.expected_close else "",
                d.created_at.isoformat() if d.created_at else "",
                d.updated_at.isoformat() if d.updated_at else "",
            ]
        )
    return meta + header + rows, len(rows)


def tasks_report_grid(session: Session) -> tuple[list[list[str]], int]:
    q = (
        session.execute(
            select(Task)
            .options(joinedload(Task.client), joinedload(Task.deal))
            .order_by(Task.id)
        )
        .unique()
        .scalars()
        .all()
    )
    meta = metadata_block(title="Задачи", row_count=len(q))
    header = [
        [
            "ID",
            "Название",
            "Описание",
            "Срок",
            "Приоритет",
            "Выполнено",
            "Клиент_ID",
            "Сделка_ID",
            "Клиент",
            "Сделка",
            "Создана",
            "Обновлена",
        ]
    ]
    rows = []
    for t in q:
        rows.append(
            [
                str(t.id),
                t.title,
                (t.description or "")[:200],
                str(t.due_date) if t.due_date else "",
                t.priority,
                "да" if t.done else "нет",
                str(t.client_id) if t.client_id else "",
                str(t.deal_id) if t.deal_id else "",
                t.client.name if t.client else "",
                t.deal.title if t.deal else "",
                t.created_at.isoformat() if t.created_at else "",
                t.updated_at.isoformat() if t.updated_at else "",
            ]
        )
    return meta + header + rows, len(rows)
