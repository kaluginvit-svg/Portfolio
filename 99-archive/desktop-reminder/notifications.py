"""Уведомления для напоминаний: Win10 Toast или popup на Tkinter."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Callable

# Toast уведомления отключены для стабильности (избегаем WNDPROC/WPARAM ошибок)
ToastNotifier = None

from database import (
    ReminderDatabase,
    STATUS_OVERDUE,
    STATUS_PENDING,
    DATETIME_FMT,
)


class NotificationManager:
    def __init__(
        self,
        root: tk.Tk,
        db: ReminderDatabase,
        interval_ms: int = 1000,
        allow_toast: bool = False,
    ) -> None:
        self.root = root
        self.db = db
        self.interval_ms = interval_ms
        # Принудительно отключаем системные toast-уведомления
        self.notifier = None
        self._toast_available = False
        self._is_running = False

    def _check_toast(self) -> bool:
        return False  # toast отключены

    # Запуск фонового мониторинга
    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._poll()

    def stop(self) -> None:
        self._is_running = False

    def _poll(self) -> None:
        if not self._is_running:
            return
        now = datetime.now()
        self.db.mark_overdue(now)

        due = self.db.get_due_reminders(now)
        for reminder in due:
            self._show_notification(reminder)
            self.db.update_status(reminder["id"], STATUS_OVERDUE)

        self.root.after(self.interval_ms, self._poll)

    def _show_notification(self, reminder: dict) -> None:
        title_raw = reminder.get("title") or "Напоминание"
        title = f"Напоминание: {title_raw}"
        desc = reminder.get("description") or ""
        timing = reminder.get("remind_at", "")
        body_content = f"{desc}\nВремя: {timing}".strip() or "Наступило время напоминания."

        self._show_popup(title, body_content)

    def _safe_show_toast(self, title: str, body: str) -> bool:
        """Безопасный вызов Win10 Toast, чтобы не ловить WNDPROC/TypeError."""
        if not self.notifier:
            return False
        try:
            # threaded=False снижает риск проблем с оконной процедурой
            return bool(
                self.notifier.show_toast(
                    title,
                    body,
                    duration=10,
                    threaded=False,
                    icon_path=None,
                )
            )
        except (Exception, TypeError):
            return False

    def _show_popup(self, title: str, body: str) -> None:
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.attributes("-topmost", True)
        popup.geometry("340x200")
        ttk.Label(popup, text=title, font=("Segoe UI", 11, "bold"), wraplength=320).pack(
            padx=10, pady=(10, 6)
        )
        ttk.Label(popup, text=body, wraplength=320).pack(padx=10, pady=6)
        ttk.Button(popup, text="Закрыть", command=popup.destroy).pack(pady=10)
        popup.after(30_000, popup.destroy)  # закрыть через 30 секунд
        popup.focus_force()

    # Публичные утилиты
    def show_manual_notification(self, title: str, message: str) -> None:
        self._show_notification({"title": title, "description": message, "remind_at": datetime.now().strftime(DATETIME_FMT)})

    def test_notification(self) -> None:
        self.show_manual_notification("Тестовое уведомление", "Проверка системы уведомлений.")


__all__ = ["NotificationManager"]

