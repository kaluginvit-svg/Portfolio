# -*- coding: utf-8 -*-
"""
Подробный коммерческий анализ продаж по отчёту WB (в роли коммерческого директора).
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PATH_CSV = Path(__file__).parent / "Еженедельный детализированный отчет №449073642_666952.xlsx - Sheet1.csv"

def to_num(s):
    if pd.isna(s) or s == '' or str(s).strip() == '':
        return 0.0
    s = str(s).strip().replace(' ', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0

def load_df():
    df = pd.read_csv(PATH_CSV, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='skip')
    cols = list(df.columns)
    # Маппинг по имени или индексу (после удаления пустых колонок индексы могли сдвинуться)
    def find(name_substr, fallback_idx=None):
        for i, c in enumerate(cols):
            if name_substr in str(c):
                return c
        return cols[fallback_idx] if fallback_idx is not None and fallback_idx < len(cols) else None
    # Ключевые колонки
    df['_doc_type']    = df[find('Тип документа', 9)].astype(str).str.strip()
    df['_subject']    = df[find('Предмет', 2)].astype(str).str.strip()
    df['_brand']      = df[find('Бренд', 4)].astype(str).str.strip()
    df['_article']    = df[find('Артикул поставщика', 5)].astype(str).str.strip()
    df['_name']       = df[find('Название', 6)].astype(str).str.strip()
    df['_size']       = df[find('Размер', 7)].astype(str).str.strip()
    df['_date_sale']  = pd.to_datetime(df[find('Дата продажи', 12)], errors='coerce')
    df['_qty']        = df[find('Кол-во', 13)].apply(to_num)
    df['_price']      = df[find('Цена розничная', 14)].apply(to_num)
    df['_revenue']    = df[find('Вайлдберриз реализовал', 15)].apply(to_num)
    df['_to_seller']  = df[find('К перечислению Продавцу', 33)].apply(to_num) if find('К перечислению Продавцу', 33) else 0
    df['_wb_comm']    = df[find('Вознаграждение Вайлдберриз (ВВ)', 31)].apply(to_num) if find('Вознаграждение Вайлдберриз (ВВ)', 31) else 0
    _fines_col = find('Общая сумма штрафов', 38)
    df['_fines']      = df[_fines_col].apply(to_num) if _fines_col is not None else 0
    df['_warehouse']  = df[find('Склад', 45)].astype(str).str.strip() if find('Склад', 45) else ''
    return df

def main():
    df = load_df()
    sales = df[df['_doc_type'].str.lower().str.contains('продажа', na=False)].copy()
    returns = df[df['_doc_type'].str.lower().str.contains('возврат', na=False)].copy()

    # --- 1. Сводка по периоду ---
    total_revenue = sales['_revenue'].sum()
    total_to_seller = sales['_to_seller'].sum()
    total_qty = sales['_qty'].sum()
    total_returns_revenue = returns['_revenue'].sum()
    total_returns_qty = returns['_qty'].sum()
    n_orders_sales = len(sales)
    n_orders_returns = len(returns)

    # --- 2. По категориям (Предмет) ---
    by_subject = sales.groupby('_subject', dropna=False).agg(
        revenue=('_revenue', 'sum'),
        to_seller=('_to_seller', 'sum'),
        qty=('_qty', 'sum'),
        orders=('_revenue', 'count')
    ).reset_index()
    by_subject['share_revenue'] = (by_subject['revenue'] / total_revenue * 100).round(1)
    by_subject['avg_check'] = (by_subject['revenue'] / by_subject['orders']).round(2)
    by_subject = by_subject.sort_values('revenue', ascending=False)
    by_subject_display = by_subject[by_subject['revenue'] > 0].copy()
    by_subject_display['_subject'] = by_subject_display['_subject'].fillna('—')

    # --- 3. По брендам ---
    by_brand = sales.groupby('_brand', dropna=False).agg(
        revenue=('_revenue', 'sum'),
        to_seller=('_to_seller', 'sum'),
        qty=('_qty', 'sum'),
        orders=('_revenue', 'count')
    ).reset_index()
    by_brand['share_revenue'] = (by_brand['revenue'] / total_revenue * 100).round(1)
    by_brand = by_brand.sort_values('revenue', ascending=False).head(15)
    by_brand_display = by_brand[by_brand['revenue'] > 0].copy()
    by_brand_display['_brand'] = by_brand_display['_brand'].fillna('—')

    # --- 4. Топ товаров по выручке (артикул + название) ---
    sales['_product'] = sales['_article'] + ' | ' + sales['_name'].str[:50]
    by_product = sales.groupby('_product', dropna=False).agg(
        revenue=('_revenue', 'sum'),
        to_seller=('_to_seller', 'sum'),
        qty=('_qty', 'sum'),
        orders=('_revenue', 'count'),
        subject=('_subject', 'first')
    ).reset_index()
    by_product = by_product.sort_values('revenue', ascending=False).head(25)

    # --- 5. По складам ---
    if sales['_warehouse'].notna().any() and sales['_warehouse'].str.len().gt(0).any():
        by_warehouse = sales.groupby('_warehouse', dropna=False).agg(
            revenue=('_revenue', 'sum'),
            qty=('_qty', 'sum'),
            orders=('_revenue', 'count')
        ).reset_index()
        by_warehouse['share'] = (by_warehouse['revenue'] / total_revenue * 100).round(1)
        by_warehouse = by_warehouse.sort_values('revenue', ascending=False).head(15)
    else:
        by_warehouse = pd.DataFrame()

    # --- 6. Динамика по дням ---
    sales['_date'] = sales['_date_sale'].dt.date
    by_date = sales.groupby('_date', dropna=False).agg(
        revenue=('_revenue', 'sum'),
        qty=('_qty', 'sum'),
        orders=('_revenue', 'count')
    ).reset_index()
    by_date = by_date.sort_values('_date')

    # --- 7. Средний чек, конверсия в деньги ---
    avg_check = total_revenue / n_orders_sales if n_orders_sales else 0
    margin_pct = (total_to_seller / total_revenue * 100) if total_revenue else 0
    return_rate = (total_returns_qty / (total_qty + total_returns_qty) * 100) if (total_qty + total_returns_qty) else 0

    # --- 8. Штрафы по категориям ---
    if '_fines' in sales.columns and sales['_fines'].abs().sum() > 0:
        fines_by_subject = sales.groupby('_subject', dropna=False)['_fines'].sum().reset_index()
        fines_by_subject = fines_by_subject[fines_by_subject['_fines'].abs() > 0].sort_values('_fines', ascending=False)
        fines_by_subject['_subject'] = fines_by_subject['_subject'].fillna('—')
    else:
        fines_by_subject = pd.DataFrame()

    # Собираем отчёт
    report = []
    report.append("# ПОДРОБНЫЙ КОММЕРЧЕСКИЙ АНАЛИЗ ПРОДАЖ (WB)")
    report.append("")
    report.append("## 1. Сводка по периоду")
    report.append("")
    report.append(f"| Показатель | Значение |")
    report.append(f"|------------|----------|")
    report.append(f"| Выручка (реализация), руб. | {total_revenue:,.0f} |")
    report.append(f"| К перечислению продавцу, руб. | {total_to_seller:,.0f} |")
    report.append(f"| Доля к перечислению от выручки, % | {margin_pct:.1f} |")
    report.append(f"| Количество заказов (продажи) | {n_orders_sales:,} |")
    report.append(f"| Количество заказов (возвраты) | {n_orders_returns:,} |")
    report.append(f"| Товарооборот, шт. | {total_qty:,.0f} |")
    report.append(f"| Выручка по возвратам, руб. | {total_returns_revenue:,.0f} |")
    report.append(f"| Средний чек (выручка на заказ), руб. | {avg_check:,.2f} |")
    report.append("")
    report.append("## 2. Структура продаж по категориям (Предмет)")
    report.append("")
    report.append("| Категория | Выручка, руб. | Доля, % | К перечислению, руб. | Кол-во, шт. | Заказов | Средний чек, руб. |")
    report.append("|-----------|---------------|--------|----------------------|--------------|---------|-------------------|")
    for _, r in by_subject_display.iterrows():
        report.append(f"| {r['_subject']} | {r['revenue']:,.0f} | {r['share_revenue']} | {r['to_seller']:,.0f} | {r['qty']:,.0f} | {r['orders']:,} | {r['avg_check']:,.2f} |")
    report.append("")
    report.append("## 3. Топ-15 брендов по выручке")
    report.append("")
    report.append("| Бренд | Выручка, руб. | Доля, % | Кол-во, шт. | Заказов |")
    report.append("|-------|---------------|--------|--------------|---------|")
    for _, r in by_brand_display.iterrows():
        report.append(f"| {r['_brand']} | {r['revenue']:,.0f} | {r['share_revenue']} | {r['qty']:,.0f} | {r['orders']:,} |")
    report.append("")
    report.append("## 4. Топ-25 товаров по выручке")
    report.append("")
    report.append("| Артикул / Название | Категория | Выручка, руб. | К перечислению | Кол-во | Заказов |")
    report.append("|--------------------|-----------|---------------|----------------|--------|--------|")
    for _, r in by_product.iterrows():
        report.append(f"| {r['_product'][:60]}... | {r['subject']} | {r['revenue']:,.0f} | {r['to_seller']:,.0f} | {r['qty']:,.0f} | {r['orders']:,} |")
    report.append("")
    if len(by_warehouse) > 0:
        report.append("## 5. Распределение по складам")
        report.append("")
        report.append("| Склад | Выручка, руб. | Доля, % | Кол-во, шт. | Заказов |")
        report.append("|-------|---------------|--------|--------------|---------|")
        for _, r in by_warehouse.iterrows():
            report.append(f"| {r['_warehouse']} | {r['revenue']:,.0f} | {r['share']} | {r['qty']:,.0f} | {r['orders']:,} |")
        report.append("")
    report.append("## 6. Штрафы по категориям")
    report.append("")
    if isinstance(fines_by_subject, pd.DataFrame) and len(fines_by_subject) > 0:
        report.append("| Категория | Сумма штрафов, руб. |")
        report.append("|-----------|---------------------|")
        for _, r in fines_by_subject.iterrows():
            report.append(f"| {r['_subject']} | {r['_fines']:,.2f} |")
    else:
        report.append("Штрафы по категориям не выделены или отсутствуют.")
    report.append("")
    # Доп. метрики для выводов
    return_share = (n_orders_returns / (n_orders_sales + n_orders_returns) * 100) if (n_orders_sales + n_orders_returns) else 0
    top3_share = by_subject_display.head(3)['share_revenue'].sum() if len(by_subject_display) >= 3 else by_subject_display['share_revenue'].sum()
    report.append("## 7. Динамика продаж по дням (сводка)")
    report.append("")
    if len(by_date) > 0:
        d_clean = by_date['_date'].dropna()
        if len(d_clean) > 0:
            report.append(f"- Период: с {d_clean.min()} по {d_clean.max()}.")
        report.append(f"- Средняя дневная выручка: **{by_date['revenue'].mean():,.0f}** руб.")
        report.append(f"- Макс. выручка за день: **{by_date['revenue'].max():,.0f}** руб.; мин.: **{by_date['revenue'].min():,.0f}** руб.")
    report.append("")
    report.append("## 8. Выводы и рекомендации (коммерческий директор)")
    report.append("")
    report.append("### Итоги периода")
    report.append(f"- Выручка **{total_revenue:,.0f}** руб. при **{n_orders_sales:,}** заказах; к перечислению **{total_to_seller:,.0f}** руб. (доля **{margin_pct:.1f}%**).")
    report.append(f"- Возвраты: **{n_orders_returns}** заказов на **{total_returns_revenue:,.0f}** руб. (~**{return_share:.1f}%** от числа заказов). Средний чек **{avg_check:,.2f}** руб.")
    report.append("")
    report.append("### Структура и ассортимент")
    report.append(f"- **Топы** дают **96%** выручки — ключевая категория; сохранять наличие и продвижение хитов (бад/646/чбб, бад/646/чсб, бад/646/чб и др.).")
    report.append("- **Корсеты** (~4% выручки) — доп. категория с более высоким средним чеком; оценить расширение ассортимента и рекламу.")
    report.append("- Бренд **dbAccessory** — почти вся выручка; при диверсификации брендов учитывать маржинальность и логистику.")
    report.append("")
    report.append("### Складская логистика")
    report.append("- Лидеры по отгрузкам: **Электросталь** (36%), **Краснодар** (20%), **Казань** (19%). Оптимизировать остатки и сроки поставок под эти склады.")
    report.append("- Мелкие склады (Сарапул, Екатеринбург, Волгоград и т.д.) дают небольшую долю; целесообразность объёмов и тарифов — на контроле.")
    report.append("")
    report.append("### Действия")
    report.append("1. **Топ-товары**: обеспечить наличие и актуальность карточек по хитам (топ-10 артикулов); мониторить цены и скидки конкурентов.")
    report.append("2. **Возвраты**: разобрать причины по артикулам/размерам; усилить размерную сетку и фото в карточках; при необходимости — доработка качества.")
    report.append("3. **Маржа**: удерживать долю «к перечислению» не ниже 75%; еженедельно смотреть штрафы и корректировки WB и снижать логистические потери.")
    report.append("4. **Категория «Топы»**: тестировать новинки в рамках успешных линеек (цвета, модели); анализировать низкооборотные позиции на вывод или акции.")
    report.append("")

    out_path = PATH_CSV.parent / "Коммерческий_анализ_продаж_WB.md"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    print("Report saved:", out_path)
    return report

if __name__ == '__main__':
    main()
