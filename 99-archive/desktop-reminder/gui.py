"""Графический интерфейс напоминалок на Tkinter."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional

from database import (
    ReminderDatabase,
    ALL_STATUSES,
    STATUS_DONE,
    STATUS_CANCELLED,
    STATUS_OVERDUE,
    STATUS_PENDING,
    DATETIME_FMT,
)
from notifications import NotificationManager


class ReminderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Десктоп-напоминалка")
        self.root.geometry("900x620")

        self.db = ReminderDatabase()
        # allow_toast=False по умолчанию, чтобы избежать системных WNDPROC ошибок; при желании включите True
        self.notifier = NotificationManager(root, self.db, interval_ms=1000, allow_toast=False)

        self._build_ui()
        self.refresh_reminders()
        self.notifier.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # UI
    def _build_ui(self) -> None:
        form = ttk.LabelFrame(self.root, text="Новое напоминание")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Название:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.title_entry = ttk.Entry(form)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Описание:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.desc_text = tk.Text(form, height=3, width=40)
        self.desc_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text=f"Дата и время ({DATETIME_FMT}):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.datetime_entry = ttk.Entry(form)
        self.datetime_entry.insert(0, datetime.now().strftime(DATETIME_FMT))
        self.datetime_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        quick_frame = ttk.Frame(form)
        quick_frame.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(quick_frame, text="Быстрое время:").pack(side="left", padx=(0, 6))
        for minutes in (1, 5, 15):
            ttk.Button(
                quick_frame,
                text=f"+{minutes} мин",
                command=lambda m=minutes: self.set_quick_time(m),
                width=8,
            ).pack(side="left", padx=2)

        add_btn = ttk.Button(form, text="Добавить", command=self.add_reminder)
        add_btn.grid(row=4, column=1, sticky="e", padx=5, pady=8)

        form.columnconfigure(1, weight=1)

        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=10, pady=5)

        ttk.Label(controls, text="Фильтр по статусу:").pack(side="left", padx=5)
        self.status_filter = tk.StringVar(value="Все")
        filter_values = ("Все",) + ALL_STATUSES
        self.filter_combobox = ttk.Combobox(
            controls, values=filter_values, state="readonly", textvariable=self.status_filter, width=12
        )
        self.filter_combobox.current(0)
        self.filter_combobox.pack(side="left", padx=5)
        self.filter_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_reminders())

        ttk.Button(controls, text="Обновить", command=self.refresh_reminders).pack(side="left", padx=5)
        ttk.Button(controls, text="Отметить как Готово", command=self.mark_as_done).pack(side="left", padx=5)
        ttk.Button(controls, text="Отметить как Отменено", command=self.mark_as_cancelled).pack(side="left", padx=5)
        ttk.Button(controls, text="Удалить", command=self.delete_reminder).pack(side="left", padx=5)
        ttk.Button(controls, text="Тест уведомления", command=self.notifier.test_notification).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "title", "description", "remind_at", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Название")
        self.tree.heading("description", text="Описание")
        self.tree.heading("remind_at", text="Дата/время")
        self.tree.heading("status", text="Статус")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("title", width=200)
        self.tree.column("description", width=280)
        self.tree.column("remind_at", width=140, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)

        self.tree.bind("<Double-1>", self.on_double_click)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.status_bar = ttk.Label(self.root, text="", relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")
        self.update_status_bar()

        # Цветовые теги для статусов
        self.tree.tag_configure(STATUS_DONE, background="#c7f5c1")       # светло-зелёный
        self.tree.tag_configure(STATUS_PENDING, background="#fff9c4")    # светло-жёлтый
        self.tree.tag_configure(STATUS_OVERDUE, background="#ffd6d6")    # светло-красный
        self.tree.tag_configure(STATUS_CANCELLED, background="#e0e0e0")  # серый

    # Helpers
    def set_quick_time(self, minutes: int) -> None:
        dt = datetime.now() + timedelta(minutes=minutes)
        self.datetime_entry.delete(0, tk.END)
        self.datetime_entry.insert(0, dt.strftime(DATETIME_FMT))

    def update_status_bar(self) -> None:
        self.status_bar.config(text=f"Всего напоминаний: {self.db.get_reminders_count()}")

    def _selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Сначала выберите напоминание.")
            return None
        return int(sel[0])

    # CRUD actions
    def add_reminder(self) -> None:
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        dt_raw = self.datetime_entry.get().strip()

        if not title:
            messagebox.showwarning("Ошибка", "Введите название.")
            return

        try:
            remind_at = datetime.strptime(dt_raw, DATETIME_FMT)
        except ValueError:
            messagebox.showerror("Ошибка", f"Неверный формат даты. Используйте {DATETIME_FMT}")
            return

        self.db.add_reminder(title, description, remind_at)
        self.title_entry.delete(0, tk.END)
        self.desc_text.delete("1.0", tk.END)
        self.datetime_entry.delete(0, tk.END)
        self.datetime_entry.insert(0, datetime.now().strftime(DATETIME_FMT))

        self.refresh_reminders()
        messagebox.showinfo("Готово", "Напоминание добавлено.")

    def refresh_reminders(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        status_filter = self.status_filter.get()
        status = status_filter if status_filter in ALL_STATUSES else None
        reminders = self.db.get_all_reminders(status=status)
        for row in reminders:
            self.tree.insert(
                "",
                "end",
                iid=row["id"],
                values=(
                    row["id"],
                    row["title"],
                    row["description"],
                    row["remind_at"],
                    row["status"],
                ),
                tags=(row["status"],),
            )
        self.update_status_bar()

    def mark_as_done(self) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return
        self.db.update_status(reminder_id, STATUS_DONE)
        self.refresh_reminders()

    def mark_as_cancelled(self) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return
        self.db.update_status(reminder_id, STATUS_CANCELLED)
        self.refresh_reminders()

    def delete_reminder(self) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return
        if messagebox.askyesno("Удалить", "Удалить выбранное напоминание?"):
            self.db.delete_reminder(reminder_id)
            self.refresh_reminders()

    # Events
    def on_double_click(self, event) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return
        reminder = self.db.get_reminder_by_id(reminder_id)
        if not reminder:
            return
        messagebox.showinfo(
            "Детали напоминания",
            f"Название: {reminder['title']}\n"
            f"Описание: {reminder['description']}\n"
            f"Время: {reminder['remind_at']}\n"
            f"Статус: {reminder['status']}",
        )

    def on_closing(self) -> None:
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.notifier.stop()
            self.db.close()
            self.root.destroy()


def run() -> None:
    root = tk.Tk()
    app = ReminderApp(root)
    app.root.mainloop()


if __name__ == "__main__":
    run()

