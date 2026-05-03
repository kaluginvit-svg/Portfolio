"""SQLite index: file linkage + Drive changes page token."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileRow:
    rel_path: str
    yandex_path: str | None
    google_file_id: str | None
    yandex_md5: str | None
    yandex_mtime: str | None
    google_md5: str | None
    google_mtime: str | None


class IndexDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    rel_path TEXT PRIMARY KEY,
                    yandex_path TEXT,
                    google_file_id TEXT,
                    yandex_md5 TEXT,
                    yandex_mtime TEXT,
                    google_md5 TEXT,
                    google_mtime TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    k TEXT PRIMARY KEY,
                    v TEXT
                )
                """
            )

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get_kv(self, key: str) -> str | None:
        with self._conn() as c:
            row = c.execute("SELECT v FROM kv WHERE k = ?", (key,)).fetchone()
            return row["v"] if row else None

    def set_kv(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO kv(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v",
                (key, value),
            )

    def get_file(self, rel_path: str) -> FileRow | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM files WHERE rel_path = ?", (rel_path,)).fetchone()
            if not row:
                return None
            return FileRow(
                rel_path=row["rel_path"],
                yandex_path=row["yandex_path"],
                google_file_id=row["google_file_id"],
                yandex_md5=row["yandex_md5"],
                yandex_mtime=row["yandex_mtime"],
                google_md5=row["google_md5"],
                google_mtime=row["google_mtime"],
            )

    def upsert_file(self, row: FileRow) -> None:
        with self._conn() as c:
            c.execute(
                """
                INSERT INTO files(rel_path, yandex_path, google_file_id, yandex_md5, yandex_mtime, google_md5, google_mtime)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(rel_path) DO UPDATE SET
                    yandex_path = excluded.yandex_path,
                    google_file_id = excluded.google_file_id,
                    yandex_md5 = excluded.yandex_md5,
                    yandex_mtime = excluded.yandex_mtime,
                    google_md5 = excluded.google_md5,
                    google_mtime = excluded.google_mtime
                """,
                (
                    row.rel_path,
                    row.yandex_path,
                    row.google_file_id,
                    row.yandex_md5,
                    row.yandex_mtime,
                    row.google_md5,
                    row.google_mtime,
                ),
            )

    def delete_row(self, rel_path: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM files WHERE rel_path = ?", (rel_path,))

    def all_rows(self) -> list[FileRow]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM files").fetchall()
            return [
                FileRow(
                    rel_path=r["rel_path"],
                    yandex_path=r["yandex_path"],
                    google_file_id=r["google_file_id"],
                    yandex_md5=r["yandex_md5"],
                    yandex_mtime=r["yandex_mtime"],
                    google_md5=r["google_md5"],
                    google_mtime=r["google_mtime"],
                )
                for r in rows
            ]
