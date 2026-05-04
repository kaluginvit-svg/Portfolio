"""
Tkinter-симулятор отчётов: период, реквизиты, случайные показатели → Google Sheets как «документ»
(merge, рамки, ширины колонок). Таблица задаётся в терминале: URL или ID.

Примеры:
  python report_generator.py "https://docs.google.com/spreadsheets/d/XXXX/edit"
  set GOOGLE_SPREADSHEET_URL=https://...   && python report_generator.py
"""

from __future__ import annotations

import argparse
import datetime
import os
import random
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from google_sheets import (
    GoogleSheets,
    resolve_service_account_json,
    spreadsheet_id_from_url_or_id,
)

NUM_COLS = 5
N_META = 2
N_GAP = 1
N_HEADER = 1
N_FOOTER = 1
N_TITLE = 1

_BASE = Path(__file__).resolve().parent
_DEFAULT_SA = resolve_service_account_json(_BASE)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Симулятор отчётов в Google Sheets (сервисный аккаунт)."
    )
    p.add_argument(
        "spreadsheet",
        nargs="?",
        default=None,
        help="Полный URL таблицы или только spreadsheetId",
    )
    p.add_argument(
        "-u",
        "--url",
        dest="spreadsheet_opt",
        default=None,
        help="Альтернатива: URL или ID (если не указан позиционный аргумент)",
    )
    return p.parse_args(argv)


def resolve_spreadsheet_id(cli_raw: str | None) -> str | None:
    raw = (cli_raw or "").strip()
    if not raw:
        for key in ("GOOGLE_SPREADSHEET_URL", "GOOGLE_SPREADSHEET_ID"):
            v = os.environ.get(key, "").strip()
            if v:
                raw = v
                break
    if not raw:
        return None
    sid = spreadsheet_id_from_url_or_id(raw)
    return sid if sid else None


def parse_date_iso(s: str) -> datetime.date:
    text = "".join((s or "").split())
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Не удалось распознать дату (ожидаю ГГГГ-ММ-ДД или ДД.ММ.ГГГГ): {s!r}")


def pad_row(values: list, width: int = NUM_COLS) -> list:
    row = list(values)
    while len(row) < width:
        row.append("")
    return row[:width]


def build_document_values(
    *,
    report_title: str,
    date_from: datetime.date,
    date_to: datetime.date,
    department: str,
    responsible: str,
    report_kind: str,
) -> tuple[list[list], int]:
    """Возвращает сетку values и число строк данных (метрик)."""
    if date_to < date_from:
        raise ValueError("Дата «по» раньше даты «с».")

    days = (date_to - date_from).days + 1
    period_text = (
        f"Отчётный период: {date_from.isoformat()} — {date_to.isoformat()} "
        f"({days} календарных дн.) — показатели условно усреднены / смоделированы"
    )
    org_text = (
        f"Подразделение: {department or '—'}    |    "
        f"Ответственный: {responsible or '—'}    |    "
        f"Тип: {report_kind or 'операционный'}"
    )
    rnd = lambda a, b: random.randint(a, b)
    metrics = [
        ("Выручка", "руб.", rnd(120_000, 890_000), rnd(-8, 15), "симуляция за период"),
        ("Заказы", "шт.", rnd(80, 1200), rnd(-12, 22), "случайный поток"),
        ("Средний чек", "руб.", rnd(900, 4500), rnd(-5, 8), ""),
        ("Визиты", "шт.", rnd(500, 8000), rnd(-20, 18), "в т.ч. повторные"),
        ("Конверсия", "%", round(random.uniform(1.2, 9.5), 2), round(random.uniform(-2, 3), 2), "в воронке"),
        ("Возвраты", "шт.", rnd(0, 45), rnd(-30, 40), ""),
        ("Себестоимость", "руб.", rnd(40_000, 400_000), rnd(-10, 12), "оценка"),
    ]
    header = ["Показатель", "Ед. изм.", "Значение", "Δ к пр. периоду, %*", "Примечание"]

    rows: list[list] = []
    rows.append(pad_row([report_title]))
    rows.append(pad_row([period_text]))
    rows.append(pad_row([org_text]))
    rows.append([""] * NUM_COLS)
    rows.append(pad_row(header))

    for name, unit, val, delta_pct, note in metrics:
        rows.append(pad_row([name, unit, val, delta_pct, note]))

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows.append(
        pad_row(
            [
                f"*Δ — вымышленное отклонение к условному «предыдущему» периоду (симулятор). "
                f"Сформировано: {stamp}."
            ]
        )
    )

    n_data = len(metrics)
    return rows, n_data


def col_letter_index(n_cols: int) -> str:
    """A..Z для n_cols <= 26."""
    if n_cols < 1 or n_cols > 26:
        raise ValueError("NUM_COLS должен быть 1..26 для этого диапазона.")
    return chr(ord("A") + n_cols - 1)


class ReportApp(tk.Tk):
    def __init__(self, spreadsheet_id: str | None) -> None:
        super().__init__()
        self.title("Симулятор отчёта в Google Sheets")
        self.geometry("820x560")
        self._spreadsheet_from_cli = spreadsheet_id

        self._cred_path = tk.StringVar(value=str(_DEFAULT_SA) if _DEFAULT_SA else "")
        self._spreadsheet_id = tk.StringVar(
            value=spreadsheet_id or "",
        )
        self._report_title = tk.StringVar(value="Сводный операционный отчёт")
        today = datetime.date.today()
        first = today.replace(day=1)
        self._date_from = tk.StringVar(value=first.isoformat())
        self._date_to = tk.StringVar(value=today.isoformat())
        self._department = tk.StringVar(value="Продажи — регион Восток")
        self._responsible = tk.StringVar(value="")
        self._report_kind = tk.StringVar(value="Операционный / еженедельный")
        self._sheet_title = tk.StringVar(value=f"Отчёт_{today.isoformat()}")

        r = 0
        tk.Label(self, text="JSON сервисного аккаунта:").grid(
            row=r, column=0, sticky="w", padx=8, pady=3
        )
        tk.Entry(self, textvariable=self._cred_path, width=62).grid(
            row=r, column=1, sticky="we", padx=4
        )
        tk.Button(self, text="Файл…", command=self._pick_cred).grid(row=r, column=2, padx=4)

        r += 1
        tk.Label(self, text="Таблица (URL или ID):").grid(
            row=r, column=0, sticky="nw", padx=8, pady=3
        )
        self._spreadsheet_entry = tk.Entry(self, textvariable=self._spreadsheet_id, width=62)
        self._spreadsheet_entry.grid(row=r, column=1, columnspan=2, sticky="we", padx=4)
        r += 1
        hint = (
            "Из терминала: python report_generator.py \"https://docs.google…/d/ID/edit\""
            "\nили переменные окружения GOOGLE_SPREADSHEET_URL / GOOGLE_SPREADSHEET_ID."
        )
        tk.Label(self, text=hint, font=("Segoe UI", 8), fg="#555", justify="left").grid(
            row=r, column=1, columnspan=2, sticky="w", padx=4
        )

        if self._spreadsheet_from_cli:
            self._spreadsheet_entry.configure(state="disabled")

        r += 1
        frm = tk.LabelFrame(self, text="Параметры отчёта")
        frm.grid(row=r, column=0, columnspan=3, sticky="we", padx=8, pady=8)
        for c in range(3):
            frm.columnconfigure(c, weight=1 if c == 2 else 0)

        ir = 0
        tk.Label(frm, text="Заголовок документа:").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._report_title, width=50).grid(
            row=ir, column=1, columnspan=2, sticky="we", padx=6, pady=4
        )

        ir += 1
        tk.Label(frm, text="Дата с (ГГГГ-ММ-ДД):").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._date_from, width=16).grid(
            row=ir, column=1, sticky="w", padx=6, pady=4
        )
        tk.Label(frm, text="Дата по:").grid(row=ir, column=1, sticky="e", padx=6)
        tk.Entry(frm, textvariable=self._date_to, width=16).grid(row=ir, column=2, sticky="w", padx=6)

        ir += 1
        tk.Label(frm, text="Подразделение:").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._department, width=50).grid(
            row=ir, column=1, columnspan=2, sticky="we", padx=6, pady=4
        )

        ir += 1
        tk.Label(frm, text="Ответственный:").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._responsible, width=50).grid(
            row=ir, column=1, columnspan=2, sticky="we", padx=6, pady=4
        )

        ir += 1
        tk.Label(frm, text="Тип / назначение:").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._report_kind, width=50).grid(
            row=ir, column=1, columnspan=2, sticky="we", padx=6, pady=4
        )

        ir += 1
        tk.Label(frm, text="Имя листа в таблице:").grid(row=ir, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(frm, textvariable=self._sheet_title, width=50).grid(
            row=ir, column=1, columnspan=2, sticky="we", padx=6, pady=4
        )

        r += 1
        btn = tk.Frame(self)
        btn.grid(row=r, column=0, columnspan=3, pady=6)
        tk.Button(btn, text="Превью в окне", command=self._preview).pack(side="left", padx=8)
        tk.Button(btn, text="Записать отчёт в Google Sheets", command=self._write_sheet).pack(
            side="left", padx=8
        )

        r += 1
        self._log = scrolledtext.ScrolledText(self, height=12, wrap="word", font=("Consolas", 10))
        self._log.grid(row=r, column=0, columnspan=3, sticky="nsew", padx=8, pady=8)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(r, weight=1)

    def _pick_cred(self) -> None:
        path = filedialog.askopenfilename(
            title="JSON сервисного аккаунта",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if path:
            self._cred_path.set(path)

    def _logln(self, s: str) -> None:
        self._log.insert("end", s + "\n")
        self._log.see("end")

    def _current_spreadsheet_id(self) -> str:
        if self._spreadsheet_from_cli:
            return spreadsheet_id_from_url_or_id(self._spreadsheet_from_cli)
        return spreadsheet_id_from_url_or_id(self._spreadsheet_id.get())

    def _parse_form(self):
        cred = self._cred_path.get().strip()
        sid = self._current_spreadsheet_id()
        if not cred or not Path(cred).is_file():
            raise ValueError("Укажите существующий JSON сервисного аккаунта.")
        if not sid:
            raise ValueError(
                "Укажите таблицу: аргумент в терминале, переменная GOOGLE_SPREADSHEET_URL "
                "или поле «Таблица»."
            )
        d0 = parse_date_iso(self._date_from.get())
        d1 = parse_date_iso(self._date_to.get())
        return cred, sid, d0, d1

    def _preview(self) -> None:
        try:
            _, _, d0, d1 = self._parse_form()
        except ValueError as e:
            messagebox.showerror("Проверка данных", str(e))
            return
        self._log.delete("1.0", "end")
        try:
            vals, _ = build_document_values(
                report_title=self._report_title.get().strip() or "Отчёт",
                date_from=d0,
                date_to=d1,
                department=self._department.get().strip(),
                responsible=self._responsible.get().strip(),
                report_kind=self._report_kind.get().strip(),
            )
        except ValueError as e:
            messagebox.showerror("Период", str(e))
            return
        for row in vals:
            self._logln("\t".join(str(x) for x in row))

    def _write_sheet(self) -> None:
        try:
            cred, sid, d0, d1 = self._parse_form()
        except ValueError as e:
            messagebox.showerror("Проверка данных", str(e))
            return

        sheet_title = self._sheet_title.get().strip() or "Отчёт"
        try:
            vals, n_data = build_document_values(
                report_title=self._report_title.get().strip() or "Отчёт",
                date_from=d0,
                date_to=d1,
                department=self._department.get().strip(),
                responsible=self._responsible.get().strip(),
                report_kind=self._report_kind.get().strip(),
            )
        except ValueError as e:
            messagebox.showerror("Период", str(e))
            return

        end_col = col_letter_index(NUM_COLS)
        n_rows = len(vals)
        esc = sheet_title.replace("'", "''")
        rng = f"'{esc}'!A1:{end_col}{n_rows}"

        try:
            gs = GoogleSheets(credentials_path=cred, spreadsheet_id=sid)
            sh_id = gs.ensure_sheet(sheet_title)
            gs.clear_range(rng)
            gs.update_range(rng, vals, value_input_option="USER_ENTERED")

            gs.set_column_widths(
                sh_id,
                [240, 88, 110, 130, 260],
            )
            gs.format_document_report(
                sheet_id=sh_id,
                num_cols=NUM_COLS,
                n_main_title=N_TITLE,
                n_meta=N_META,
                n_gap=N_GAP,
                n_header=N_HEADER,
                n_data=n_data,
                n_footer=N_FOOTER,
                zebra_data=True,
            )

            self._logln(f"Готово: лист «{sheet_title}», {n_rows} строк, A1:{end_col}{n_rows}")
            messagebox.showinfo("Готово", "Отчёт записан и оформлен в таблице.")
        except Exception as e:
            messagebox.showerror("Ошибка API", str(e))


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    pos, opt = args.spreadsheet, args.spreadsheet_opt
    if pos and opt and pos.strip() != opt.strip():
        print(
            "Укажите таблицу одним способом: позиционный аргумент или --url.",
            file=sys.stderr,
        )
        sys.exit(2)
    sp_raw = (pos or opt or "").strip() or None
    sid = resolve_spreadsheet_id(sp_raw)
    app = ReportApp(spreadsheet_id=sid)
    app.mainloop()


if __name__ == "__main__":
    main()
