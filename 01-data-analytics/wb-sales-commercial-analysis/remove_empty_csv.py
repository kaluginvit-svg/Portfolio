# -*- coding: utf-8 -*-
"""Удаление полностью пустых столбцов и строк из CSV."""
import pandas as pd
from pathlib import Path

path = Path(r"C:\_Рабочая_папка\Проекты_программирование\Задание\Еженедельный детализированный отчет №449073642_666952.xlsx - Sheet1.csv")

df = pd.read_csv(path, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='skip')

def is_empty(val):
    if pd.isna(val):
        return True
    return str(val).strip() == ''

# Пустые столбцы: все ячейки пустые
empty_cols = [c for c in df.columns if df[c].apply(is_empty).all()]
# Пустые строки: все ячейки в строке пустые
empty_rows = df.apply(lambda row: row.apply(is_empty).all(), axis=1)

df_clean = df.drop(columns=empty_cols).drop(index=df.index[empty_rows])

df_clean.to_csv(path, sep=',', index=False, encoding='utf-8')

print(f"Удалено пустых столбцов: {len(empty_cols)}")
print(f"Удалено пустых строк: {empty_rows.sum()}")
print(f"Было: {df.shape[0]} строк, {df.shape[1]} столбцов")
print(f"Стало: {len(df_clean)} строк, {len(df_clean.columns)} столбцов")
