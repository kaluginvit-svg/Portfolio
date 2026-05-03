"""GUI-приложение напоминалок для Windows 10 на tkinter."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from db import (
    ReminderDB,
    ALL_STATUSES,
    STATUS_PENDING,
    STATUS_DONE,
    STATUS_OVERDUE,
    STATUS_CANCELLED,
    DATETIME_FMT,
)


class ReminderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Напоминания")
        self.root.geometry("850x600")

        self.db = ReminderDB()
        # Отключаем Win10 toast, используем только popup для стабильности
        self.notifier = None
        self.poll_interval_ms = 10_000  # проверка каждые 10 секунд

        self._build_ui()
        self.refresh_table()
        self.poll_due_reminders()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # UI
    def _build_ui(self) -> None:
        form = ttk.LabelFrame(self.root, text="Новое напоминание")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Заголовок:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.title_entry = ttk.Entry(form)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Описание:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.desc_text = tk.Text(form, height=3, width=40)
        self.desc_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text=f"Дата и время ({DATETIME_FMT}):").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.datetime_entry = ttk.Entry(form)
        self.datetime_entry.insert(0, datetime.now().strftime(DATETIME_FMT))
        self.datetime_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        quick_frame = ttk.Frame(form)
        quick_frame.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(quick_frame, text="Напомнить через:").pack(side="left", padx=(0, 6))
        quick_presets = [
            (1, "1 мин"),
            (5, "5 мин"),
            (15, "15 мин"),
            (60, "1 час"),
        ]
        for minutes, label in quick_presets:
            ttk.Button(
                quick_frame,
                text=label,
                command=lambda m=minutes: self.set_quick_time(m),
                width=14,
            ).pack(side="left", padx=2)

        add_btn = ttk.Button(form, text="Добавить", command=self.add_reminder)
        add_btn.grid(row=4, column=1, sticky="e", padx=5, pady=5)

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
        self.filter_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        ttk.Button(controls, text="Обновить", command=self.refresh_table).pack(side="left", padx=5)
        ttk.Button(controls, text="Отметить как Готово", command=lambda: self.mark_selected(STATUS_DONE)).pack(
            side="left", padx=5
        )
        ttk.Button(controls, text="Отметить как Отменено", command=lambda: self.mark_selected(STATUS_CANCELLED)).pack(
            side="left", padx=5
        )
        ttk.Button(controls, text="Удалить", command=self.delete_selected).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "title", "description", "remind_at", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("description", text="Описание")
        self.tree.heading("remind_at", text="Дата/время")
        self.tree.heading("status", text="Статус")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("title", width=180)
        self.tree.column("description", width=260)
        self.tree.column("remind_at", width=120, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Цвета по статусам
        self.tree.tag_configure(STATUS_DONE, background="#c7f5c1")       # светло-зелёный
        self.tree.tag_configure(STATUS_PENDING, background="#fff9c4")    # светло-жёлтый
        self.tree.tag_configure(STATUS_OVERDUE, background="#ffd6d6")    # светло-красный
        self.tree.tag_configure(STATUS_CANCELLED, background="#e0e0e0")  # серый

    # CRUD
    def add_reminder(self) -> None:
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        dt_raw = self.datetime_entry.get().strip()

        if not title:
            messagebox.showwarning("Ошибка", "Заполните заголовок.")
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

        self.refresh_table()
        messagebox.showinfo("Готово", "Напоминание добавлено.")

    def set_quick_time(self, minutes: int) -> None:
        dt = datetime.now() + timedelta(minutes=minutes)
        self.datetime_entry.delete(0, tk.END)
        self.datetime_entry.insert(0, dt.strftime(DATETIME_FMT))

    def delete_selected(self) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return

        if messagebox.askyesno("Удалить", "Точно удалить выбранное напоминание?"):
            self.db.delete_reminder(reminder_id)
            self.refresh_table()

    def mark_selected(self, status: str) -> None:
        reminder_id = self._selected_id()
        if reminder_id is None:
            return
        self.db.update_status(reminder_id, status)
        self.refresh_table()

    def _selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Сначала выберите напоминание в списке.")
            return None
        return int(sel[0])

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        status_filter = self.status_filter.get()
        status = status_filter if status_filter in ALL_STATUSES else None
        for row in self.db.get_reminders(status=status):
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

    # Notifications and polling
    def poll_due_reminders(self) -> None:
        now = datetime.now()
        due = self.db.due_reminders(now)
        for reminder in due:
            self.show_notification(reminder)
            self.db.update_status(reminder["id"], STATUS_OVERDUE)

        if due:
            self.refresh_table()

        self.root.after(self.poll_interval_ms, self.poll_due_reminders)

    def show_notification(self, reminder: dict) -> None:
        title = f"Напоминание: {reminder.get('title')}"
        desc = reminder.get("description") or ""
        timing = reminder.get("remind_at", "")
        body = f"{desc}\nВремя: {timing}".strip()

        self._popup_window(title, body)

    def _popup_window(self, title: str, body: str) -> None:
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.attributes("-topmost", True)
        popup.geometry("320x180")
        ttk.Label(popup, text=title, font=("Segoe UI", 11, "bold"), wraplength=300).pack(
            padx=10, pady=(10, 5)
        )
        ttk.Label(popup, text=body, wraplength=300).pack(padx=10, pady=5)
        ttk.Button(popup, text="Закрыть", command=popup.destroy).pack(pady=10)

    def on_close(self) -> None:
        self.db.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    ReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

