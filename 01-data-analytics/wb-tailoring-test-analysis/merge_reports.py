# -*- coding: utf-8 -*-
"""Объединение 5 CSV отчётов с удалением пустых строк и столбцов."""
import csv
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = [
    "Еженедельный детализированный отчет №440856251_666952.xlsx - Sheet1.csv",
    "Еженедельный детализированный отчет №449073642_666952.xlsx - Sheet1.csv",
    "Еженедельный детализированный отчет №454757424_666952.xlsx - Sheet1.csv",
    "Еженедельный детализированный отчет №461732663_666952.xlsx - Sheet1.csv",
    "Еженедельный детализированный отчет №467397457_666952.xlsx - Sheet1.csv",
]
OUTPUT = os.path.join(ROOT, "отчет_объединенный.csv")


def is_empty_row(row):
    return not any(cell and str(cell).strip() for cell in row)


def main():
    all_rows = []
    header = None

    for fname in FILES:
        path = os.path.join(ROOT, fname)
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            row_header = next(reader)
            if header is None:
                header = row_header
            for row in reader:
                if len(row) != len(header):
                    row = row[:len(header)] if len(row) > len(header) else row + [""] * (len(header) - len(row))
                if not is_empty_row(row):
                    all_rows.append(row)

    # Индексы столбцов, в которых есть хотя бы одно непустое значение
    ncols = len(header)
    non_empty_cols = [False] * ncols
    for row in all_rows:
        for i, cell in enumerate(row):
            if i < ncols and cell and str(cell).strip():
                non_empty_cols[i] = True
                if all(non_empty_cols):
                    break

    kept_indices = [i for i in range(ncols) if non_empty_cols[i]]
    new_header = [header[i] for i in kept_indices]

    with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(new_header)
        for row in all_rows:
            writer.writerow([row[i] if i < len(row) else "" for i in kept_indices])

    print(f"Записано строк (без заголовка): {len(all_rows)}")
    print(f"Столбцов в итоге: {len(kept_indices)} (было {ncols})")
    print(f"Файл: {OUTPUT}")


if __name__ == "__main__":
    main()
