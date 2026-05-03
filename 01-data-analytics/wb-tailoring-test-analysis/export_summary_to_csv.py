# -*- coding: utf-8 -*-
"""
Скрипт экспорта всех итогов EDA из отчёта WB в одну сводную плоскую таблицу CSV.
Воспроизводит логику ноутбука wb_report_eda.ipynb: загрузка, предобработка и агрегации.

Широкая таблица для сводных: одна строка = одна запись, все метрики в отдельных колонках.
Колонки: section, sale_date, warehouse, category, size, nomenclature_code, product_name,
         sum_payout, cnt, avg_check, margin_pct, sum_retail, funnel_stage_label, rank,
         metric_name, value (metric_name/value — только для скаляров и воронки).
В сводной: фильтр по section, строки — нужное измерение, значения — sum_payout / cnt / avg_check / margin_pct.
"""
import os
import csv
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(ROOT, "отчет_объединенный.csv")
OUTPUT_CSV = os.path.join(ROOT, "отчет_сводный_итоги.csv")
MIN_DATE = pd.Timestamp("2025-07-28")


def clean_col(c):
    s = str(c).strip().lower().replace(" ", "_").replace("%", "pct").replace(",", "")
    return "".join("_" if not (x.isalnum() or x == "_") else x for x in s)


def find_col(df, key_substrings):
    if isinstance(key_substrings, str):
        key_substrings = [key_substrings]
    for c in df.columns:
        if all(k in c for k in key_substrings):
            return c
    return None


def find_col_funnel(dataf, key_substrings):
    if isinstance(key_substrings, str):
        key_substrings = [key_substrings]
    for c in dataf.columns:
        if all(k in c.lower() for k in key_substrings):
            return c
    return None


def to_num(ser):
    if ser.dtype == object:
        return pd.to_numeric(ser.astype(str).str.replace(",", "."), errors="coerce")
    return pd.to_numeric(ser, errors="coerce")


def to_num_funnel(ser):
    if ser.dtype == object:
        return pd.to_numeric(ser.astype(str).str.replace(",", "."), errors="coerce")
    return pd.to_numeric(ser, errors="coerce")


def main():
    df = pd.read_csv(FILE_PATH, encoding="utf-8-sig", low_memory=False)
    df.columns = [clean_col(c) for c in df.columns]

    col_hints = {
        "order_date": ["дата_заказа", "покупателем"],
        "sale_date": ["дата_продажи"],
        "quantity": ["кол_во"],
        "size": ["размер"],
        "price_retail": ["цена_розничная"],
        "wb_revenue": ["вайлдберриз_реализовал"],
        "payout": ["перечислению_продавцу"],
        "category": ["предмет"],
        "product_name": ["название"],
        "nomenclature_code": ["код_номенклатуры"],
        "warehouse": ["склад"],
    }
    rename_map = {}
    for std_name, hints in col_hints.items():
        found = find_col(df, hints)
        if found and found not in rename_map.values():
            rename_map[found] = std_name
    df = df.rename(columns=rename_map)

    for col in ["order_date", "sale_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["quantity", "price_retail", "wb_revenue", "payout"]:
        if col in df.columns:
            df[col] = to_num(df[col])

    df = df.drop_duplicates()
    critical = [c for c in ["sale_date", "payout", "category"] if c in df.columns]
    df = df.dropna(subset=critical)
    df = df[df["sale_date"] >= MIN_DATE].copy()

    # Широкая таблица: измерения + отдельные колонки метрик (удобно для сводных)
    rows_flat = []
    EMPTY = ""

    def row(
        section,
        sale_date=EMPTY,
        warehouse=EMPTY,
        category=EMPTY,
        size=EMPTY,
        nomenclature_code=EMPTY,
        product_name=EMPTY,
        sum_payout=None,
        cnt=None,
        avg_check=None,
        margin_pct=None,
        sum_retail=None,
        funnel_stage_label=EMPTY,
        rank=None,
        metric_name=EMPTY,
        value=None,
    ):
        rows_flat.append({
            "section": section,
            "sale_date": sale_date,
            "warehouse": warehouse,
            "category": category,
            "size": size,
            "nomenclature_code": nomenclature_code,
            "product_name": product_name,
            "sum_payout": sum_payout if sum_payout is not None else EMPTY,
            "cnt": cnt if cnt is not None else EMPTY,
            "avg_check": avg_check if avg_check is not None else EMPTY,
            "margin_pct": margin_pct if margin_pct is not None else EMPTY,
            "sum_retail": sum_retail if sum_retail is not None else EMPTY,
            "funnel_stage_label": funnel_stage_label,
            "rank": rank if rank is not None else EMPTY,
            "metric_name": metric_name,
            "value": value if value is not None else EMPTY,
        })

    # ---- Базовые метрики (скаляры) ----
    ship_col = [c for c in df.columns if "номер_поставки" in c or "поставк" in c]
    ship_col = ship_col[0] if ship_col else df.columns[1]
    n_shipments = df[ship_col].nunique()
    date_min = df["sale_date"].min()
    date_max = df["sale_date"].max()
    total_qty = df["quantity"].sum() if "quantity" in df.columns else 0
    total_wb = df["wb_revenue"].sum() if "wb_revenue" in df.columns else 0
    total_payout = df["payout"].sum() if "payout" in df.columns else 0

    row("базовые_метрики", metric_name="уникальных_поставок", value=n_shipments)
    row("базовые_метрики", metric_name="дата_начала", value=date_min)
    row("базовые_метрики", metric_name="дата_окончания", value=date_max)
    row("базовые_метрики", metric_name="суммарное_колво", value=total_qty)
    row("базовые_метрики", metric_name="выручка_wb", value=total_wb)
    row("базовые_метрики", metric_name="к_перечислению", value=total_payout)

    # ---- Воронка ----
    stages = []
    labels = []
    if "price_retail" in df.columns:
        qty = df["quantity"] if "quantity" in df.columns else 1
        retail = (df["price_retail"] * qty).sum()
        stages.append(retail)
        labels.append("Розничная выручка")
    if "wb_revenue" in df.columns:
        wb_rev = df["wb_revenue"].sum()
        stages.append(wb_rev)
        labels.append("Реализация WB (после скидок)")
    wb_comm_col = find_col_funnel(df, ["вознаграждение", "вв"]) or find_col_funnel(df, ["вознаграждение_вайлдберриз"])
    delivery_col = find_col_funnel(df, ["услуги", "доставк"]) or find_col_funnel(df, ["доставке_товара"])
    acquiring_col = find_col_funnel(df, ["эквайринг"]) or find_col_funnel(df, ["комиссии_за_организацию_платежей"])
    wb_comm = df[wb_comm_col].pipe(to_num_funnel).sum() if wb_comm_col else 0
    delivery = df[delivery_col].pipe(to_num_funnel).sum() if delivery_col else 0
    acquiring = df[acquiring_col].pipe(to_num_funnel).sum() if acquiring_col else 0
    if "wb_revenue" in df.columns and (wb_comm > 0 or delivery > 0 or acquiring > 0):
        wb_rev = df["wb_revenue"].sum()
        after_comm = wb_rev - wb_comm
        if wb_comm > 0:
            stages.append(after_comm)
            labels.append("После вычета вознаграждения WB")
        after_del = after_comm - delivery
        if delivery > 0:
            stages.append(after_del)
            labels.append("После вычета доставки")
        after_acq = after_del - acquiring
        if acquiring > 0:
            stages.append(after_acq)
            labels.append("После вычета эквайринга")
    if "payout" in df.columns:
        payout_sum = df["payout"].sum()
        stages.append(payout_sum)
        labels.append("К перечислению продавцу")
    for i, (lab, st) in enumerate(zip(labels, stages), start=1):
        row("воронка", sum_payout=st, funnel_stage_label=lab, rank=i)

    # ---- По коду номенклатуры ----
    code_col = "nomenclature_code" if "nomenclature_code" in df.columns else None
    if code_col and "payout" in df.columns:
        by_code = (
            df.groupby(code_col)
            .agg(sum_payout=("payout", "sum"), cnt=("payout", "count"))
            .assign(avg_check=lambda x: (x["sum_payout"] / x["cnt"]).round(2))
        )
        by_code = by_code.sort_values("sum_payout", ascending=False)
        for idx, r in by_code.iterrows():
            row(
                "по_коду_номенклатуры",
                nomenclature_code=idx,
                sum_payout=r["sum_payout"],
                cnt=r["cnt"],
                avg_check=r["avg_check"],
            )

    # ---- По складам ----
    wh_col = "warehouse" if "warehouse" in df.columns else None
    if wh_col and "payout" in df.columns:
        by_wh = (
            df.groupby(wh_col, dropna=False)
            .agg(sum_payout=("payout", "sum"), rows=("payout", "count"))
            .reset_index()
        )
        by_wh = by_wh.dropna(subset=[wh_col])
        for _, r in by_wh.iterrows():
            row("по_складам", warehouse=r[wh_col], sum_payout=r["sum_payout"], cnt=r["rows"])

    # ---- Топ-3 по складу и коду ----
    if wh_col and code_col and "payout" in df.columns:
        by_wh_code = (
            df.groupby([wh_col, code_col])
            .agg(sum_payout=("payout", "sum"), cnt=("payout", "count"))
            .reset_index()
        )
        if "product_name" in df.columns:
            first_name = df.groupby([wh_col, code_col])["product_name"].first().reset_index()
            by_wh_code = by_wh_code.merge(first_name, on=[wh_col, code_col], how="left")
        top3 = (
            by_wh_code.groupby(wh_col, group_keys=True)
            .apply(lambda g: g.nlargest(3, "sum_payout"), include_groups=False)
            .reset_index()
        )
        wh_in_top3 = wh_col if wh_col in top3.columns else top3.columns[0]
        for (wh_val, grp) in top3.groupby(wh_in_top3, sort=False):
            for rank_val, (_, r) in enumerate(grp.iterrows(), start=1):
                row(
                    "топ3_склад_код",
                    warehouse=r[wh_in_top3],
                    nomenclature_code=r[code_col],
                    product_name=r.get("product_name", ""),
                    sum_payout=r["sum_payout"],
                    cnt=r["cnt"],
                    rank=rank_val,
                )

    # ---- По дням ----
    if "sale_date" in df.columns and "payout" in df.columns:
        daily = df.groupby("sale_date").agg(payout=("payout", "sum"), rows=("payout", "count")).reset_index()
        for _, r in daily.iterrows():
            row(
                "по_дням",
                sale_date=str(r["sale_date"].date()) if pd.notna(r["sale_date"]) else "",
                sum_payout=r["payout"],
                cnt=r["rows"],
            )

    # ---- По категориям ----
    if "category" in df.columns and "payout" in df.columns:
        by_cat = (
            df.groupby("category")
            .agg(sum_payout=("payout", "sum"), rows=("payout", "count"))
            .reset_index()
        )
        by_cat = by_cat.sort_values("sum_payout", ascending=False)
        for _, r in by_cat.iterrows():
            row("по_категориям", category=r["category"], sum_payout=r["sum_payout"], cnt=r["rows"])

    # ---- По размерам ----
    size_col = "size" if "size" in df.columns else None
    if size_col and "payout" in df.columns:
        by_size = (
            df.groupby(size_col, dropna=False)
            .agg(sum_payout=("payout", "sum"), cnt=("payout", "count"))
            .reset_index()
        )
        by_size = by_size[
            by_size[size_col].notna() & (by_size[size_col].astype(str).str.strip() != "")
        ]
        by_size = by_size.sort_values("sum_payout", ascending=False).head(20)
        for _, r in by_size.iterrows():
            row("по_размерам", size=r[size_col], sum_payout=r["sum_payout"], cnt=r["cnt"])

    # ---- Маржа по категориям ----
    if "category" in df.columns and "payout" in df.columns and "price_retail" in df.columns:
        df_m = df[df["price_retail"] > 0].copy()
        df_m["payout_share"] = (df_m["payout"] / df_m["price_retail"] * 100).round(1)
        by_cat_m = (
            df_m.groupby("category")
            .agg(
                sum_payout=("payout", "sum"),
                sum_retail=("price_retail", "sum"),
                mean_share=("payout_share", "mean"),
                cnt=("payout", "count"),
            )
            .assign(margin_pct=lambda x: (x["sum_payout"] / x["sum_retail"] * 100).round(1))
        )
        for idx, r in by_cat_m.iterrows():
            row(
                "маржа_по_категориям",
                category=idx,
                sum_payout=r["sum_payout"],
                cnt=r["cnt"],
                margin_pct=r["margin_pct"],
                sum_retail=r["sum_retail"],
            )

    # ---- Топ товаров ----
    if "product_name" in df.columns and "payout" in df.columns:
        by_prod = (
            df.groupby("product_name")
            .agg(sum_payout=("payout", "sum"), cnt=("payout", "count"))
            .sort_values("sum_payout", ascending=False)
            .head(15)
        )
        for idx, r in by_prod.iterrows():
            row("топ_товары", product_name=idx, sum_payout=r["sum_payout"], cnt=r["cnt"])

    out = pd.DataFrame(rows_flat)
    cols = [
        "section",
        "sale_date",
        "warehouse",
        "category",
        "size",
        "nomenclature_code",
        "product_name",
        "sum_payout",
        "cnt",
        "avg_check",
        "margin_pct",
        "sum_retail",
        "funnel_stage_label",
        "rank",
        "metric_name",
        "value",
    ]
    out = out.reindex(columns=cols)

    # Форматирование для читаемого отчёта в Excel
    num_cols = ["sum_payout", "cnt", "avg_check", "margin_pct", "sum_retail"]
    for c in num_cols:
        if c in out.columns:
            s = pd.to_numeric(out[c], errors="coerce")
            if c == "cnt":
                out[c] = s.apply(lambda x: int(x) if pd.notna(x) and x == x else "")
            else:
                out[c] = s.apply(lambda x: round(x, 2) if pd.notna(x) and x == x else "")
    if "sale_date" in out.columns:
        out["sale_date"] = out["sale_date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else x
        )
    if "value" in out.columns:
        def fmt_value(v):
            if v is None or v == "" or (isinstance(v, float) and pd.isna(v)):
                return ""
            if hasattr(v, "strftime"):
                return v.strftime("%Y-%m-%d")
            if isinstance(v, (int, float)):
                return round(float(v), 2) if isinstance(v, float) else int(v)
            return v
        out["value"] = out["value"].apply(fmt_value)

    out.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        quoting=csv.QUOTE_MINIMAL,
    )
    print(f"Сводная таблица сохранена: {OUTPUT_CSV}")
    print(f"Строк: {len(out)}, разделов: {out['section'].nunique()}")


if __name__ == "__main__":
    main()
