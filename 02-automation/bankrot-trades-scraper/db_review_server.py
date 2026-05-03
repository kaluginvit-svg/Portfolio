
"""
Сервер для просмотра и разметки записей из .db (таблица announcements).
Запуск: python db_review_server.py [порт]
Открыть в браузере: http://127.0.0.1:5000/

Требуется: pip install flask
"""
import base64
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "review_static"
app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")

# Папка с .db файлами — каталог скрипта (BASE_DIR уже задан выше)


def _get_db_path(filename: str) -> Path:
    """Путь к файлу .db в BASE_DIR (без выхода за пределы)."""
    if ".." in filename or os.path.sep in filename:
        raise ValueError("Invalid db file")
    path = BASE_DIR / filename
    if not path.is_file():
        raise ValueError("File not found")
    return path


def _connect_db(path: Path) -> sqlite3.Connection:
    """SQLite соединение с увеличенным timeout (защита от 'зависаний' при блокировках)."""
    conn = sqlite3.connect(path, timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        # Если режим недоступен (например, readonly FS) — всё равно продолжаем.
        pass
    return conn


def _find_display_columns(cursor) -> dict[str, str | None]:
    """По PRAGMA table_info находит колонки для отображения: описание, цена, url, вид торгов."""
    cursor.execute("PRAGMA table_info(announcements)")
    rows = cursor.fetchall()
    out = {"description": None, "price": None, "url": None, "trade_type": None}
    for row in rows:
        name = (row[1] or "").strip()
        low = name.lower().replace("_", " ")
        if "описание" in low or name == "Описание":
            out["description"] = name
        if ("начальн" in low or "начальная" in low) and ("цен" in low or "руб" in low):
            out["price"] = name
        if name.lower() == "url":
            out["url"] = name
        if "вид" in low and "торг" in low:
            out["trade_type"] = name
    return out


@app.route("/api/databases")
def list_databases():
    """Список .db файлов в BASE_DIR."""
    files = sorted(f.name for f in BASE_DIR.glob("*.db") if f.is_file())
    return jsonify(files)


@app.route("/api/record")
def get_record():
    """Запись по индексу (0-based). Включая число строк с тем же URL (lots_same_url)."""
    db_name = request.args.get("db")
    try:
        index = int(request.args.get("index", 0))
    except (TypeError, ValueError):
        index = 0
    if not db_name or not db_name.endswith(".db"):
        return jsonify({"error": "Invalid db"}), 400
    try:
        path = _get_db_path(db_name)
    except ValueError:
        return jsonify({"error": "File not found"}), 404
    conn = _connect_db(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM announcements")
        total = cur.fetchone()[0]
        if total == 0:
            conn.close()
            return jsonify({
                "rowid": None, "description": "", "price": "", "url": "", "trade_type": "",
                "total": 0, "index": 0,
                "lots_same_url": 0,
            })
        cols = _find_display_columns(cur)
        # ORDER BY rowid для стабильного порядка
        cur.execute("SELECT rowid, * FROM announcements ORDER BY rowid LIMIT 1 OFFSET ?", (index,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({
                "rowid": None, "description": "", "price": "", "url": "", "trade_type": "",
                "total": total, "index": index,
                "lots_same_url": 0,
            })
        rowid = row["rowid"]
        def _get(col_key: str) -> str:
            c = cols.get(col_key)
            if not c or c not in row.keys():
                return ""
            val = row[c]
            return str(val) if val is not None else ""

        url_col = cols.get("url")
        url_val_stripped = ((_get("url") or "").strip())
        lots_same_url = 0
        if url_col and url_val_stripped:
            qcol_u = _quote_sql_ident(url_col)
            cur.execute(f"SELECT COUNT(*) FROM announcements WHERE {qcol_u} = ?", (url_val_stripped,))
            lots_same_url = cur.fetchone()[0]

        conn.close()
        return jsonify({
            "rowid": rowid,
            "description": _get("description") or "",
            "price": _get("price") or "",
            "url": _get("url") or "",
            "trade_type": _get("trade_type") or "",
            "total": total,
            "index": index,
            "lots_same_url": lots_same_url,
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/record", methods=["DELETE"])
def delete_record():
    """Удалить запись по rowid из указанной db."""
    data = request.get_json(force=True, silent=True) or request.args
    db_name = data.get("db")
    rowid = data.get("rowid")
    if not db_name or not db_name.endswith(".db"):
        return jsonify({"error": "Invalid db"}), 400
    try:
        rowid = int(rowid)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid rowid"}), 400
    try:
        path = _get_db_path(db_name)
    except ValueError:
        return jsonify({"error": "File not found"}), 404
    conn = _connect_db(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT rowid, * FROM announcements WHERE rowid = ?", (rowid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Запись не найдена"}), 404
        snapshot = _snapshot_row_for_json(row)
        cur.execute("DELETE FROM announcements WHERE rowid = ?", (rowid,))
        conn.commit()
        deleted = cur.rowcount
        conn.close()
        return jsonify({"ok": True, "deleted": deleted, "snapshot": snapshot})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


def _quote_sql_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _snapshot_row_for_json(row: sqlite3.Row) -> dict:
    """Сериализация строки для JSON (bytes → base64). Без rowid — новый при INSERT."""
    out: dict = {}
    for name in row.keys():
        if str(name).lower() == "rowid":
            continue
        val = row[name]
        if isinstance(val, bytes):
            out[name] = {"__b64__": base64.b64encode(val).decode("ascii")}
        else:
            out[name] = val
    return out


def _snapshot_from_json(snapshot: dict) -> dict[str, object]:
    """Десериализация значений для INSERT."""
    out: dict[str, object] = {}
    for k, v in snapshot.items():
        if str(k).lower() == "rowid":
            continue
        if isinstance(v, dict) and "__b64__" in v:
            out[k] = base64.b64decode(v["__b64__"])
        else:
            out[k] = v
    return out


@app.route("/api/record/restore", methods=["POST"])
def restore_record():
    """Вставить строку обратно в announcements (после отмены удаления)."""
    data = request.get_json(force=True, silent=True) or {}
    db_name = data.get("db")
    snapshot = data.get("snapshot")
    if not db_name or not db_name.endswith(".db"):
        return jsonify({"error": "Invalid db"}), 400
    if not isinstance(snapshot, dict) or not snapshot:
        return jsonify({"error": "Invalid snapshot"}), 400
    try:
        path = _get_db_path(db_name)
    except ValueError:
        return jsonify({"error": "File not found"}), 404
    row_vals = _snapshot_from_json(snapshot)
    if not row_vals:
        return jsonify({"error": "Пустой снимок записи"}), 400
    conn = _connect_db(path)
    cur = conn.cursor()
    try:
        cols_sql = ", ".join(_quote_sql_ident(c) for c in row_vals.keys())
        placeholders = ", ".join("?" for _ in row_vals)
        cur.execute(
            f"INSERT INTO announcements ({cols_sql}) VALUES ({placeholders})",
            tuple(row_vals.values()),
        )
        new_rowid = cur.lastrowid
        cur.execute("SELECT COUNT(*) FROM announcements")
        total = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "new_rowid": new_rowid, "total": total})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/records-by-url", methods=["DELETE"])
def delete_records_by_url():
    """Удалить все строки с тем же URL, что у записи с указанным rowid."""
    data = request.get_json(force=True, silent=True) or {}
    db_name = data.get("db")
    rowid = data.get("rowid")
    if not db_name or not db_name.endswith(".db"):
        return jsonify({"error": "Invalid db"}), 400
    try:
        rowid = int(rowid)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid rowid"}), 400
    try:
        path = _get_db_path(db_name)
    except ValueError:
        return jsonify({"error": "File not found"}), 404
    conn = _connect_db(path)
    cur = conn.cursor()
    try:
        cols = _find_display_columns(cur)
        url_col = cols.get("url")
        if not url_col:
            conn.close()
            return jsonify({"error": "В таблице нет колонки URL"}), 400
        qcol = _quote_sql_ident(url_col)
        cur.execute(f"SELECT {qcol} FROM announcements WHERE rowid = ?", (rowid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({"error": "Запись не найдена"}), 404
        url_value = row[0]
        if url_value is None or not str(url_value).strip():
            conn.close()
            return jsonify({"error": "URL пустой — массовое удаление отменено"}), 400
        url_value = str(url_value).strip()
        cur.execute(f"DELETE FROM announcements WHERE {qcol} = ?", (url_value,))
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "deleted": deleted})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/test")
def test():
    """Проверка: открыть в браузере, должно показать «Сервер работает»."""
    return "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='background:#1a1b26;color:#c0caf5;font-family:sans-serif;padding:2rem;'><h1>Server OK</h1><p><a href='/'>Main app</a> | <a href='/min'>/min</a></p></body></html>"


# Минимальная страница для /min (проверка, что сервер отвечает)
_MINIMAL_HTML = b"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;}
html,body{margin:0;padding:0;width:100%;min-height:100vh;background:#0d1117;color:#e6edf3;font-family:sans-serif;font-size:18px;}
body{padding:2rem;}
h1{color:#58a6ff;} a{color:#58a6ff;}
</style></head><body>
<h1>DB Review</h1>
<p><strong>If you see this, server is working.</strong></p>
<p><a href="/">Main app</a> | <a href="/test">/test</a></p>
</body></html>"""


@app.route("/")
def index():
    """Главная — приложение просмотра записей из .db."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return Response(
            _MINIMAL_HTML,
            mimetype="text/html; charset=utf-8",
            status=500,
        )
    data = index_path.read_bytes()
    return Response(data, mimetype="text/html; charset=utf-8", headers={"Cache-Control": "no-store, no-cache"})


@app.route("/min")
def min_page():
    """Минимальная страница для проверки (без index.html)."""
    return Response(_MINIMAL_HTML, mimetype="text/html; charset=utf-8", headers={"Cache-Control": "no-store, no-cache"})


@app.errorhandler(404)
def not_found(e):
    """При 404 показываем страницу с ссылками на главную и тест."""
    html = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>404</title></head>
<body style="background:#1a1b26;color:#c0caf5;font-family:sans-serif;padding:2rem;">
<h1>Страница не найдена</h1>
<p>Попробуйте:</p>
<ul>
<li><a href="/" style="color:#7aa2f7;">Главная /</a></li>
<li><a href="/min" style="color:#7aa2f7;">/min</a></li>
<li><a href="/test" style="color:#7aa2f7;">/test</a></li>
<li><a href="/api/databases" style="color:#7aa2f7;">/api/databases</a></li>
</ul>
</body></html>"""
    return Response(html, status=404, mimetype="text/html; charset=utf-8")


if __name__ == "__main__":
    import sys
    import threading
    import webbrowser
    import time

    argv = [a for a in sys.argv[1:] if a not in ("--https", "-s")]
    use_https = "--https" in sys.argv[1:] or "-s" in sys.argv[1:]
    port = int(argv[0]) if argv else 3000
    if not STATIC_DIR.is_dir():
        print("Ошибка: папка review_static не найдена рядом со скриптом.")
        sys.exit(1)

    ssl_ctx = None
    if use_https:
        try:
            ssl_ctx = "adhoc"
            __import__("OpenSSL")
        except ImportError:
            print("Для HTTPS установите: pip install pyopenssl")
            sys.exit(1)

    scheme = "https" if ssl_ctx else "http"
    url = f"{scheme}://127.0.0.1:{port}/"
    print("=" * 60)
    print("  Просмотр записей .db")
    print("=" * 60)
    print(f"  Откройте в браузере:  {url}")
    print("=" * 60)
    if ssl_ctx:
        print("  Важно: в адресе должно быть HTTPS (не http).")
        print("  Иначе будет ошибка «Client sent an HTTP request to an HTTPS server».")
        print("  Сертификат: «Дополнительно» → «Перейти на сайт».")
    print("  Через 2 сек браузер откроется сам.")
    print("=" * 60)

    def open_browser():
        time.sleep(2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, ssl_context=ssl_ctx)
