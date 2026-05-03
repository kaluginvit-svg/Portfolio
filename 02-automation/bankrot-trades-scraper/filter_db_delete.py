"""
Перенос записей из .db в БД «garbage» (имя.garbage.db) с меткой _garbage_label = garbage.
Исходная таблица announcements очищается от отобранных строк (копия сохраняется в garbage-файле).

Условия переноса:
- «Описание» содержит одно из заданных слов/фраз
- «Начальная цена, руб.» < 5000 (число)
- «Классификация имущества» содержит «Оружие»
- Если в «Описание» есть «кадастровый», но нет ни одного из префиксов 66:, 50:, 23:, 78:, 72: — переносить
- Если в «Описание» есть «Право требования» или «Дебиторская задолженность», но в «Вид торгов» нет «Публичное предложение» — переносить
- Если в «Место жительства» указан исключённый регион/область — переносить только если в «Описание» есть «земельный участок» или «помещение»
- Если в «Описание» есть «VIN», но в «Место жительства» нет ни одного из разрешённых — переносить
- В «Описание» есть «Хабаровск» или «Хабаровский край» — переносить
- В «Описание» встречается сочетание «прицеп» и «трактор*» (в любом порядке, в т.ч. «прицеп тракторый» / «тракторный») — переносить
- В «Описание» есть «Доля в уставном капитале», «Вид торгов» не «Публичное предложение», и числовая «Начальная цена, руб.» не меньше 500000; если цена < 500000 или не удалось разобрать в число — по этому правилу запись не трогаем (остаётся в основной БД)

Запуск: python filter_db_delete.py
"""
import argparse
import re
import sqlite3
from pathlib import Path
from typing import Pattern

BASE_DIR = Path(__file__).resolve().parent

# Слова/фразы в поле «Описание» — при совпадении запись удаляется
DESCRIPTION_KEYWORDS = [
    "УАЗ", "UAZ", "Урал", "ПАЗ", "Зил", "ЗИЛ", "ВАЗ", "VAZ",
    "Lada", "LADA", "Лада", "ЛАДА", "ЗАЗ", "ГАЗ",
    "1/5 доля", "1/6 доля", "1/4 доля", "1/3 доля",
    "Logan", "Логан", "1/4 доли", "1/3 доли", "УРАЛ", "МАЗ",
    "Renault", "Рено", "РЕНО", "Дэу", "ДЭУ", "DAEWOO", "Пежо",
    "PEUGEOT", "Peugeot", "Шевроле", "CHEVROLET", "Chevrolet",
    "ПЕЖО", "ШЕВРОЛЕ", "лада", "Lifan", "LIFAN", "Lifan", "ЛИФАН",
    "МЗСА", "LADA", "SsangYong", "RENAULT", "Черри", "Cherry", "САННИ",
    "SANNY", "Виста", "VISTA", "Фокус", "FOCUS", "FAW", "VITZ", "COLT",
    "Geely", "GEELY", "Газель", "ГАЗЕЛЬ", "NEXT", "WISH", "Caldina",
    "ФИАТ", "FIAT", "Haval", "ХАВАЛ", "HAVAL", "ХАВАЛ", "ХАВАЛ", "Демио", "Demio",
    "Tiggo", "ON-DO", "SERENA", "BELGEE", "PASSO", "BYD", "BAIC", "Spectra", 
    "БОГДАН", "CORSA", "LUXGEN", "FUSO", "ON DO", "DATSUN", "Elantra"
]

MIN_PRICE = 5000

WEAPON_MARKER = "Оружие"

# Если в «Описание» есть любое из KADASTROVYI_MARKERS, в том же поле должен быть хотя бы один из этих префиксов; иначе запись удаляется
KADASTROVYI_MARKERS = ("кадастровый", "кадастровым", "кад.")
KADASTROVYI_REQUIRED_PREFIXES = ("66:", "50:", "23:", "78:", "72:")

# Если в «Описание» есть любое из этих словосочетаний, в «Вид торгов» должно быть PUBLICHNOE_PREDLOZHENIE; иначе удалять
DESCRIPTION_DEBT_MARKERS = ("Право требования", "Дебиторская задолженность")
PUBLICHNOE_PREDLOZHENIE = "Публичное предложение"

# Доля в УК: при непубличных торгах переносим только если начальная цена (число) >= 500000
SHARE_CAPITAL_MARKER = "Доля в уставном капитале"
SHARE_CAPITAL_MIN_PRICE = 500_000

# Поле «Место жительства»: при совпадении с любым из этих значений — удалять только если в «Описание» есть «земельный участок» или «помещение»
RESIDENCE_EXCLUDE = (
    "Хабаровск", "Приморский край", "Тыва", "Хабаровский край",
    "Камчатский край", "Адыгея", "Амурская область", "Алтайский",
    "Сахалинская область", "Сахалин",
    "Смоленская", "Мордовия", "Пензенская", "Коми", "Ростовская", "Ярославская",
    "Республика Саха",
)
RESIDENCE_DELETE_REQUIRES_DESC = ("земельный участок", "помещение")

# В поле «Описание» — при вхождении подстроки переносить в garbage
DESCRIPTION_HABAROVSK_MARKERS = ("Хабаровск", "Хабаровский край")

# Если в «Описание» есть VIN, в «Место жительства» должен быть хотя бы один из этих регионов; иначе удалять
VIN_MARKER = "VIN"
RESIDENCE_VIN_ALLOWED = (
    "Екатеринбург", "Свердловская", "Челябинская", "Челябинск",
    "Пермский", "Пермь", "Курганская", "Курган", "Тюменская", "Тюмень",
)


def _find_columns(cursor) -> dict[str, str | None]:
    """Находит колонки: описание, цена, классификация, вид торгов, место жительства по PRAGMA table_info."""
    cursor.execute("PRAGMA table_info(announcements)")
    rows = cursor.fetchall()
    out = {"description": None, "price": None, "classification": None, "trade_type": None, "residence": None}
    for row in rows:
        name = (row[1] or "").strip()
        low = name.lower().replace("_", " ")
        if "описание" in low or name == "Описание":
            out["description"] = name
        if ("начальн" in low or "начальная" in low) and ("цен" in low or "руб" in low):
            out["price"] = name
        if "классифик" in low and "имуществ" in low:
            out["classification"] = name
        if "вид" in low and "торг" in low:
            out["trade_type"] = name
        if "место" in low and "житель" in low:
            out["residence"] = name
    return out


def _quote_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _tractor_trailer_in_description(desc: str) -> bool:
    """«Прицеп тракторый» / тракторный и т.п. в любом порядке в тексте."""
    if not desc:
        return False
    d = desc.lower().replace("ё", "е")
    if re.search(
        r"прицеп.{0,80}трактор(ный|ый|ых|ом|ому)?|трактор(ный|ый|ых|ом|ому)?.{0,80}прицеп",
        d,
        re.DOTALL,
    ):
        return True
    return False


def _ensure_garbage_table(src_cur, dst_cur) -> list[str]:
    """Создаёт или дополняет таблицу announcements в БД garbage по схеме источника. Возвращает имена колонок данных (без rowid)."""
    src_cur.execute("PRAGMA table_info(announcements)")
    src_cols = [r[1] for r in src_cur.fetchall()]
    dst_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='announcements'")
    if not dst_cur.fetchone():
        parts = [f"{_quote_ident(c)} TEXT" for c in src_cols]
        parts.append("_garbage_label TEXT")
        dst_cur.execute(f"CREATE TABLE announcements ({', '.join(parts)})")
    else:
        dst_cur.execute("PRAGMA table_info(announcements)")
        dst_col_set = {r[1] for r in dst_cur.fetchall()}
        for c in src_cols:
            if c not in dst_col_set:
                dst_cur.execute(f"ALTER TABLE announcements ADD COLUMN {_quote_ident(c)} TEXT")
        if "_garbage_label" not in dst_col_set:
            dst_cur.execute("ALTER TABLE announcements ADD COLUMN _garbage_label TEXT")
    return src_cols


def _parse_price(s: str) -> float | None:
    """Из строки вида '720 000,00' или '5000' извлекает число. Не число -> None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    m = re.match(r"[\d\s,.]+", s)
    if not m:
        return None
    s = m.group(0).replace(" ", "").replace(",", ".")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _should_delete(
    row,
    cols: dict,
    rowid: int,
    extra_desc_contains: tuple[str, ...] = (),
    extra_desc_contains_ci: tuple[str, ...] = (),
    extra_desc_regex: tuple[Pattern[str], ...] = (),
) -> bool:
    """True, если запись подходит под условия переноса в garbage (хотя бы одно)."""
    desc_col = cols.get("description")
    price_col = cols.get("price")
    class_col = cols.get("classification")
    trade_type_col = cols.get("trade_type")
    residence_col = cols.get("residence")

    desc = ""
    if desc_col and desc_col in row.keys():
        desc = (row[desc_col] or "").strip()
    desc_lower = desc.lower()

    # Дополнительные пользовательские фильтры по полю «Описание» (БД).
    if desc:
        if any(s in desc for s in extra_desc_contains):
            return True
        if any(s.lower() in desc_lower for s in extra_desc_contains_ci):
            return True
        if any(rx.search(desc) for rx in extra_desc_regex):
            return True

    trade_type_val = ""
    if trade_type_col and trade_type_col in row.keys() and row[trade_type_col] is not None:
        trade_type_val = str(row[trade_type_col]).strip()

    price_num: float | None = None
    if price_col and price_col in row.keys():
        val = row[price_col]
        price_num = _parse_price(str(val)) if val is not None else None

    if desc_col and desc_col in row.keys():
        if any(m in desc for m in DESCRIPTION_HABAROVSK_MARKERS):
            return True
        if _tractor_trailer_in_description(desc):
            return True
        # Доля в УК + не публичное предложение + только при разобранной цене >= 500000
        # (неразборчивая цена price_num is None — запись по этому правилу не переносим)
        if SHARE_CAPITAL_MARKER in desc:
            if PUBLICHNOE_PREDLOZHENIE not in trade_type_val:
                if price_num is not None and price_num >= SHARE_CAPITAL_MIN_PRICE:
                    return True
        # Право требования / Дебиторская задолженность без «Публичное предложение» в Вид торгов — переносить
        if any(m in desc for m in DESCRIPTION_DEBT_MARKERS):
            if PUBLICHNOE_PREDLOZHENIE not in trade_type_val:
                return True
        for kw in DESCRIPTION_KEYWORDS:
            if kw in desc:
                return True
        # Кадастровый без кода региона: если есть маркер («кадастровый»/«кадастровым»), но нет 66:/50:/23:/78:/72: — удалять
        if any(m in desc_lower for m in KADASTROVYI_MARKERS):
            if not any(prefix in desc for prefix in KADASTROVYI_REQUIRED_PREFIXES):
                return True
        # VIN без разрешённого региона: если в описании есть VIN, в «Место жительства» должен быть один из RESIDENCE_VIN_ALLOWED
        if VIN_MARKER in desc:
            residence_val = ""
            if residence_col and residence_col in row.keys() and row[residence_col] is not None:
                residence_val = str(row[residence_col]).strip()
            if not any(region in residence_val for region in RESIDENCE_VIN_ALLOWED):
                return True

    if price_col and price_col in row.keys():
        if price_num is not None and price_num < MIN_PRICE:
            return True

    if class_col and class_col in row.keys():
        val = (row[class_col] or "").strip()
        if WEAPON_MARKER in val:
            return True

    if residence_col and residence_col in row.keys():
        val = (row[residence_col] or "").strip()
        if any(region in val for region in RESIDENCE_EXCLUDE):
            dlow = desc.lower()
            if any(phrase in dlow for phrase in RESIDENCE_DELETE_REQUIRES_DESC):
                return True

    return False


def _process_db(
    path: Path,
    extra_desc_contains: tuple[str, ...] = (),
    extra_desc_contains_ci: tuple[str, ...] = (),
    extra_desc_regex: tuple[Pattern[str], ...] = (),
) -> int:
    """Переносит строки в path.stem + '.garbage.db' с _garbage_label = garbage, затем удаляет из исходной БД."""
    garbage_path = path.parent / f"{path.stem}.garbage.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cols = _find_columns(cur)
    cur.execute("SELECT rowid, * FROM announcements")
    rows = cur.fetchall()
    to_delete: list[int] = []
    for row in rows:
        rowid = int(row["rowid"])
        if _should_delete(
            row,
            cols,
            rowid,
            extra_desc_contains=extra_desc_contains,
            extra_desc_contains_ci=extra_desc_contains_ci,
            extra_desc_regex=extra_desc_regex,
        ):
            to_delete.append(rowid)
    if not to_delete:
        conn.close()
        return 0

    gconn = sqlite3.connect(garbage_path)
    gcur = gconn.cursor()
    data_cols = _ensure_garbage_table(cur, gcur)
    quoted = ", ".join(_quote_ident(c) for c in data_cols)
    placeholders = ", ".join(["?"] * (len(data_cols) + 1))
    insert_sql = (
        f"INSERT INTO announcements ({quoted}, {_quote_ident('_garbage_label')}) "
        f"VALUES ({placeholders})"
    )

    for rowid in to_delete:
        cur.execute("SELECT * FROM announcements WHERE rowid = ?", (rowid,))
        one = cur.fetchone()
        if not one:
            continue
        values = [one[c] for c in data_cols]
        values.append("garbage")
        gcur.execute(insert_sql, values)
        cur.execute("DELETE FROM announcements WHERE rowid = ?", (rowid,))

    gconn.commit()
    conn.commit()
    gconn.close()
    conn.close()
    return len(to_delete)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Переносит подходящие строки из announcements в *.garbage.db и удаляет их из исходной БД. "
            "Доп. параметры фильтрации применяются к колонке 'Описание'."
        )
    )
    p.add_argument(
        "--desc-contains",
        action="append",
        default=[],
        help="Удалять, если подстрока встречается в 'Описание' (чувствительно к регистру). Можно указывать многократно.",
    )
    p.add_argument(
        "--desc-contains-ci",
        action="append",
        default=[],
        help="Удалять, если подстрока встречается в 'Описание' (без учёта регистра). Можно указывать многократно.",
    )
    p.add_argument(
        "--desc-regex",
        action="append",
        default=[],
        help="Удалять, если regex (Python) совпал с 'Описание'. Можно указывать многократно.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    db_files = sorted(BASE_DIR.glob("*.db"))
    db_files = [
        f for f in db_files
        if f.is_file() and not f.name.endswith(".garbage.db")
    ]
    if not db_files:
        print("В каталоге нет файлов .db")
        return

    print("Файлы в каталоге:")
    print("  0 — все файлы .db")
    for i, f in enumerate(db_files, 1):
        print(f"  {i} — {f.name}")

    try:
        raw = input("\nВведите номер (или несколько через пробел): ").strip()
    except EOFError:
        return
    if not raw:
        print("Не введён номер.")
        return

    indices = []
    for s in raw.split():
        try:
            n = int(s)
            if n == 0:
                indices = list(range(1, len(db_files) + 1))
                break
            if 1 <= n <= len(db_files):
                indices.append(n)
        except ValueError:
            pass

    if not indices:
        print("Нет выбранных файлов.")
        return

    to_process = [db_files[i - 1] for i in sorted(set(indices))]
    print("\nОбработка:", ", ".join(f.name for f in to_process))

    extra_desc_regex: tuple[Pattern[str], ...] = ()
    if args.desc_regex:
        extra_desc_regex = tuple(re.compile(pat) for pat in args.desc_regex if str(pat).strip())

    for path in to_process:
        try:
            moved = _process_db(
                path,
                extra_desc_contains=tuple(s for s in args.desc_contains if str(s).strip()),
                extra_desc_contains_ci=tuple(s for s in args.desc_contains_ci if str(s).strip()),
                extra_desc_regex=extra_desc_regex,
            )
            print(f"  {path.name}: перенесено в garbage — {moved} ({path.stem}.garbage.db)")
        except Exception as e:
            print(f"  {path.name}: ошибка — {e}")


if __name__ == "__main__":
    main()
