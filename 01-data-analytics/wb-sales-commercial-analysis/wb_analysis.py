# -*- coding: utf-8 -*-
"""
Анализ отчёта комиссионера WB: экономика продаж, потери, маржи, аномалии.
CSV: разделитель запятая, числа с запятой как десятичный разделитель (в кавычках).
"""
import pandas as pd
import numpy as np
from pathlib import Path

def to_num(s):
    """Преобразование строки с запятой как десятичным разделителем в float."""
    if pd.isna(s) or s == '' or str(s).strip() == '':
        return 0.0
    s = str(s).strip().replace(' ', '').replace('\u00a0', '')
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0

def load_report(path: str) -> pd.DataFrame:
    """Загрузка CSV отчёта WB (разделитель запятая, числа с запятой)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path, sep=',', encoding='utf-8', low_memory=False, on_bad_lines='skip')
    # Индексы колонок по заголовку: 9-Тип документа, 16-Вайлдберриз реализ, 31-К перечислению, 29-ВВ, 34-Доставка, 38-Штрафы, 39-Корректировка, 65-Перевозка, 67-Хранение, 69-Удержания, 70-Платная приемка, 27-Эквайринг
    col_list = list(df.columns)
    idx = {}
    for i, c in enumerate(col_list):
        cnorm = str(c).strip()
        if 'Тип документа' in cnorm:
            idx['doc_type'] = c
        if 'Вайлдберриз реализовал' in cnorm or 'реализовал Товар' in cnorm:
            idx['revenue_wb'] = c
        if 'К перечислению Продавцу' in cnorm:
            idx['to_seller'] = c
        if 'Вознаграждение Вайлдберриз' in cnorm and 'Корректировка' not in cnorm and 'НДС' in cnorm:
            idx['wb_commission'] = c
        if 'Услуги по доставке' in cnorm:
            idx['delivery'] = c
        if 'Общая сумма штрафов' in cnorm:
            idx['fines'] = c
        if 'Корректировка Вознаграждения' in cnorm:
            idx['correction'] = c
        if 'Возмещение издержек по перевозке' in cnorm:
            idx['transport'] = c
        if cnorm == 'Хранение':
            idx['storage'] = c
        if cnorm == 'Удержания':
            idx['withholdings'] = c
        if 'Платная приемка' in cnorm:
            idx['paid_accept'] = c
        if 'Эквайринг' in cnorm and 'Размер' not in cnorm and 'Тип платежа' not in cnorm:
            idx['acquiring'] = c
    # Fallback по позициям
    if 'doc_type' not in idx and len(col_list) > 9:
        idx['doc_type'] = col_list[9]
    if 'revenue_wb' not in idx and len(col_list) > 16:
        idx['revenue_wb'] = col_list[16]
    if 'to_seller' not in idx and len(col_list) > 31:
        idx['to_seller'] = col_list[31]
    if 'wb_commission' not in idx and len(col_list) > 29:
        idx['wb_commission'] = col_list[29]
    if 'delivery' not in idx and len(col_list) > 34:
        idx['delivery'] = col_list[34]
    if 'fines' not in idx and len(col_list) > 38:
        idx['fines'] = col_list[38]
    if 'correction' not in idx and len(col_list) > 39:
        idx['correction'] = col_list[39]
    if 'transport' not in idx and len(col_list) > 65:
        idx['transport'] = col_list[65]
    if 'storage' not in idx and len(col_list) > 67:
        idx['storage'] = col_list[67]
    if 'withholdings' not in idx and len(col_list) > 69:
        idx['withholdings'] = col_list[69]
    if 'paid_accept' not in idx and len(col_list) > 70:
        idx['paid_accept'] = col_list[70]
    if 'acquiring' not in idx and len(col_list) > 27:
        idx['acquiring'] = col_list[27]
    # Жёстко задаём по позициям (заголовок отчёта WB)
    pos = {'doc_type': 9, 'revenue_wb': 15, 'to_seller': 33, 'wb_commission': 31, 'delivery': 36,
           'fines': 38, 'correction': 39, 'transport': 65, 'storage': 67, 'withholdings': 69,
           'paid_accept': 70, 'acquiring': 28}
    for k, i in pos.items():
        if k not in idx and i < len(col_list):
            idx[k] = col_list[i]
    for col in idx.values():
        if col in df.columns:
            df[col] = df[col].apply(to_num)
    df.attrs['col_idx'] = idx
    return df

def run_analysis(csv_path: str):
    df = load_report(csv_path)
    idx = df.attrs.get('col_idx', {})
    ncol = len(df.columns)
    
    def get(dataset, key):
        if key not in idx or idx[key] not in dataset.columns:
            return 0.0
        return dataset[idx[key]].sum()
    
    # Тип документа по индексу 9
    doc_idx = 9
    if ncol > doc_idx:
        doc_ser = df.iloc[:, doc_idx].astype(str).str.strip().str.lower()
        sales = df[doc_ser.str.contains('продажа', na=False, case=False)]
        returns = df[doc_ser.str.contains('возврат', na=False, case=False)]
    else:
        sales = df
        returns = df.iloc[0:0]
    if len(sales) == 0 and len(returns) == 0:
        sales = df.copy()
        returns = df.iloc[0:0]
    
    revenue_wb = get(sales, 'revenue_wb')
    revenue_returns = get(returns, 'revenue_wb')
    to_seller_sales = get(sales, 'to_seller')
    to_seller_returns = get(returns, 'to_seller')
    wb_commission = get(sales, 'wb_commission') - get(returns, 'wb_commission')
    delivery = get(sales, 'delivery') - get(returns, 'delivery')
    storage = get(sales, 'storage') - get(returns, 'storage')
    transport = get(sales, 'transport') - get(returns, 'transport')
    fines = get(sales, 'fines') - get(returns, 'fines')
    correction = get(sales, 'correction') - get(returns, 'correction')
    withholdings = get(sales, 'withholdings') - get(returns, 'withholdings')
    paid_accept = get(sales, 'paid_accept') - get(returns, 'paid_accept')
    acquiring = get(sales, 'acquiring') - get(returns, 'acquiring') if 'acquiring' in idx else 0.0
    
    logistics_total = delivery + storage + transport + fines + correction + withholdings + paid_accept
    gross_revenue = revenue_wb - revenue_returns
    net_to_seller = to_seller_sales - to_seller_returns
    total_wb_deductions = gross_revenue - net_to_seller
    
    margin_before_logistics = net_to_seller + logistics_total
    margin_after_logistics = net_to_seller
    margin_after_internal = margin_after_logistics
    
    # Аномалии
    to_seller_col = idx.get('to_seller')
    fines_col = idx.get('fines')
    anomalies_negative = pd.DataFrame()
    anomalies_high_fines = pd.DataFrame()
    if to_seller_col and to_seller_col in df.columns:
        anomalies_negative = df[df[to_seller_col].apply(to_num) < 0]
    if fines_col and fines_col in df.columns:
        f = df[fines_col].apply(to_num)
        threshold = f.abs().quantile(0.99) if f.abs().max() > 0 else 500
        anomalies_high_fines = df[f.abs() > max(threshold, 500)]
    
    report = {
        'rows_total': len(df),
        'rows_sales': len(sales),
        'rows_returns': len(returns),
        'gross_revenue': gross_revenue,
        'net_to_seller': net_to_seller,
        'wb_commission': wb_commission,
        'logistics_total': logistics_total,
        'delivery': delivery,
        'storage': storage,
        'transport': transport,
        'fines': fines,
        'correction': correction,
        'withholdings': withholdings,
        'paid_accept': paid_accept,
        'acquiring': acquiring,
        'margin_before_logistics': margin_before_logistics,
        'margin_after_logistics': margin_after_logistics,
        'margin_after_internal': margin_after_internal,
        'total_wb_deductions': total_wb_deductions,
        'losses_fines': fines,
        'losses_storage': storage,
        'losses_returns_value': get(returns, 'to_seller'),
        'anomalies_negative_count': len(anomalies_negative),
        'anomalies_high_fines_count': len(anomalies_high_fines),
        'revenue_wb': revenue_wb,
        'revenue_returns': revenue_returns,
        'to_seller_sales': to_seller_sales,
        'to_seller_returns': to_seller_returns,
    }
    return report, df, sales, returns

def write_conclusion(r):
    lines = [
        "ЗАКЛЮЧЕНИЕ ПО ЭКОНОМИКЕ ПРОДАЖ WB",
        "=" * 50,
        "",
        "1. Экономика WB сейчас",
        "   Выручка с покупателей (валовая): {:.0f} руб. К перечислению продавцу после всех вычетов WB: {:.0f} руб. Доля вычетов WB от выручки: {:.1f}%.".format(
            r['gross_revenue'], r['net_to_seller'],
            100 * r['total_wb_deductions'] / r['gross_revenue'] if r['gross_revenue'] else 0),
        "",
        "2. Где теряются деньги?",
        "   Основные источники потерь: штрафы ({:.0f} руб.), хранение ({:.0f} руб.), возвраты (удержано {:.0f} руб.), доставка и прочие удержания WB.".format(
            r['losses_fines'], r['losses_storage'], r['losses_returns_value']),
        "",
        "3. Насколько прибыльны продажи?",
        "   Маржа после логистики WB (к перечислению): {:.0f} руб. ({:.1f}% от выручки).".format(
            r['margin_after_logistics'],
            100 * r['margin_after_logistics'] / r['gross_revenue'] if r['gross_revenue'] else 0),
        "",
        "4. Что менять?",
        "   Снижать штрафы (качество приёмки, сроки), оптимизировать хранение (оборачиваемость, объём остатков), сокращать возвраты (описание, размерная сетка), контролировать логистические расходы.",
        "",
        "5. Три показателя WB для еженедельного контроля:",
        "   • Доля «К перечислению» в выручке (целевой уровень не ниже 50–55%).",
        "   • Сумма штрафов и корректировок ВВ (тренд к снижению).",
        "   • Удельный вес возвратов в выручке и оборачиваемость (хранение).",
        ""
    ]
    return "\n".join(lines)

def main():
    import sys
    path = Path(__file__).parent / "Еженедельный детализированный отчет №449073642_666952.xlsx - Sheet1.csv"
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    report, df, sales, returns = run_analysis(str(path))
    
    print("=" * 60)
    print("EKONOMIKA PRODAZH WB (period otcheta)")
    print("=" * 60)
    print("Rows: {} (sales: {}, returns: {})".format(report['rows_total'], report['rows_sales'], report['rows_returns']))
    print()
    print("REVENUE:")
    print("  WB revenue (sales):    {:,.2f}".format(report['revenue_wb']))
    print("  WB revenue (returns):  -{:,.2f}".format(report['revenue_returns']))
    print("  Gross revenue:         {:,.2f}".format(report['gross_revenue']))
    print()
    print("WB DEDUCTIONS:")
    print("  WB commission:         {:,.2f}".format(report['wb_commission']))
    print("  Delivery:              {:,.2f}".format(report['delivery']))
    print("  Storage:               {:,.2f}".format(report['storage']))
    print("  Transport:             {:,.2f}".format(report['transport']))
    print("  Fines:                 {:,.2f}".format(report['fines']))
    print("  Correction:            {:,.2f}".format(report['correction']))
    print("  Withholdings:          {:,.2f}".format(report['withholdings']))
    print("  Paid accept:           {:,.2f}".format(report['paid_accept']))
    print("  Total logistics etc:   {:,.2f}".format(report['logistics_total']))
    print()
    print("TO SELLER:")
    print("  From sales:            {:,.2f}".format(report['to_seller_sales']))
    print("  From returns:          -{:,.2f}".format(report['to_seller_returns']))
    print("  Net to seller:         {:,.2f}".format(report['net_to_seller']))
    print()
    print("MARGINS:")
    print("  Before logistics:      {:,.2f}".format(report['margin_before_logistics']))
    print("  After logistics:       {:,.2f}".format(report['margin_after_logistics']))
    if report['gross_revenue']:
        print("  WB deductions %:        {:.1f}%".format(100 * report['total_wb_deductions'] / report['gross_revenue']))
        print("  To seller %:            {:.1f}%".format(100 * report['net_to_seller'] / report['gross_revenue']))
    print()
    print("LOSSES:")
    print("  Fines:                 {:,.2f}".format(report['losses_fines']))
    print("  Storage:               {:,.2f}".format(report['losses_storage']))
    print("  Returns withheld:      {:,.2f}".format(report['losses_returns_value']))
    print("  Total losses (est):    {:,.2f}".format(report['losses_fines'] + report['losses_storage'] + report['losses_returns_value']))
    print()
    print("ANOMALIES: negative to_seller={}, high_fines={}".format(report['anomalies_negative_count'], report['anomalies_high_fines_count']))
    
    conclusion_path = path.parent / "WB_zaklyuchenie.txt"
    with open(conclusion_path, 'w', encoding='utf-8') as f:
        f.write(write_conclusion(report))
    print()
    print("Conclusion saved:", conclusion_path)

if __name__ == '__main__':
    main()
