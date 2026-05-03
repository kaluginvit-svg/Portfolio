"""Bidirectional sync engine."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from datetime import datetime, timezone

from googleapiclient.errors import HttpError

from sync_app.config import Settings
from sync_app.db import FileRow, IndexDB
from sync_app.google_auth import get_credentials
from sync_app.google_client import DriveFileMeta, FOLDER_MIME, GoogleDriveClient
from sync_app.yandex_client import YandexDiskClient, YandexFileMeta

log = logging.getLogger(__name__)

GOOGLE_APPS = "application/vnd.google-apps."


def _fp_y(m: YandexFileMeta) -> str:
    if m.md5:
        return m.md5
    return f"{m.size or 0}|{m.modified or ''}"


def _fp_y_meta(meta: dict) -> str:
    if meta.get("md5"):
        return meta["md5"]
    return f"{meta.get('size') or 0}|{meta.get('modified') or ''}"


def _fp_g(m) -> str:
    if m.md5:
        return m.md5
    return f"{m.size or 0}|{m.modified or ''}"


def _fp_g_meta(meta: dict | None) -> str:
    if not meta:
        return ""
    if meta.get("md5Checksum"):
        return meta["md5Checksum"]
    return f"{meta.get('size') or 0}|{meta.get('modifiedTime') or ''}"


def _cmp_time(a: str | None, b: str | None) -> int:
    """-1 if a newer, 0 tie/unknown, 1 if b newer."""
    if not a and not b:
        return 0
    if not a:
        return 1
    if not b:
        return -1
    if a == b:
        return 0
    return -1 if a > b else 1


def _is_skipped_drive_mime(mime: str) -> bool:
    return mime.startswith(GOOGLE_APPS) and mime != FOLDER_MIME


def _now_suffix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _lk(lock: threading.Lock | None):
    return lock if lock is not None else nullcontext()


def _bump(st: dict[str, int], st_lock: threading.Lock | None, key: str, n: int = 1) -> None:
    with _lk(st_lock):
        st[key] = st.get(key, 0) + n


def _process_rel(
    rel: str,
    settings: Settings,
    ya_files: dict[str, YandexFileMeta],
    g_files: dict[str, DriveFileMeta],
    db: IndexDB,
    db_lock: threading.Lock | None,
    st: dict[str, int],
    st_lock: threading.Lock | None,
    y_root: str,
    g_root: str,
    ya: YandexDiskClient,
    drive: GoogleDriveClient,
) -> None:
    y = ya_files.get(rel)
    g = g_files.get(rel)
    with _lk(db_lock):
        row = db.get_file(rel)

    if not y and not g:
        if row:
            with _lk(db_lock):
                db.delete_row(rel)
        return

    if settings.sync_deletions and row:
        if not y and g and row:
            log.info("Deleted on Yandex, removing Drive copy: %s", rel)
            drive.delete_file(g.file_id)
            with _lk(db_lock):
                db.delete_row(rel)
            _bump(st, st_lock, "deleted")
            return
        if not g and y and row.yandex_path:
            log.info("Deleted on Drive, removing Yandex copy: %s", rel)
            ya.delete(y.disk_path)
            with _lk(db_lock):
                db.delete_row(rel)
            _bump(st, st_lock, "deleted")
            return

    if y and not g:
        data = ya.download_file(y.disk_path)
        gid = drive.create_file(g_root, rel, data)
        g_meta = drive.get_file(gid)
        with _lk(db_lock):
            db.upsert_file(
                FileRow(
                    rel_path=rel,
                    yandex_path=y.disk_path,
                    google_file_id=gid,
                    yandex_md5=_fp_y(y),
                    yandex_mtime=y.modified,
                    google_md5=_fp_g_meta(g_meta),
                    google_mtime=(g_meta or {}).get("modifiedTime"),
                )
            )
        log.info("Yandex -> Drive (new): %s", rel)
        _bump(st, st_lock, "to_drive")
        return

    if g and not y:
        data = drive.download_media(g.file_id)
        y_path = ya.path_under_root(y_root, rel)
        ya.ensure_parent_dirs(y_root, rel)
        ya.upload_bytes(y_path, data, overwrite=True)
        y_meta = ya.get_meta(y_path)
        with _lk(db_lock):
            db.upsert_file(
                FileRow(
                    rel_path=rel,
                    yandex_path=y_path,
                    google_file_id=g.file_id,
                    yandex_md5=_fp_y_meta(y_meta),
                    yandex_mtime=y_meta.get("modified"),
                    google_md5=_fp_g(g),
                    google_mtime=g.modified,
                )
            )
        log.info("Drive -> Yandex (new): %s", rel)
        _bump(st, st_lock, "to_yandex")
        return

    assert y and g
    y_fp = _fp_y(y)
    g_fp = _fp_g(g)

    if not row:
        if y_fp != g_fp:
            c = _cmp_time(y.modified, g.modified)
            if c <= 0:
                data = ya.download_file(y.disk_path)
                drive.update_file_media(g.file_id, data)
                g_meta = drive.get_file(g.file_id)
                log.info("Initial align Y->G: %s", rel)
                _bump(st, st_lock, "to_drive")
                with _lk(db_lock):
                    db.upsert_file(
                        FileRow(
                            rel_path=rel,
                            yandex_path=y.disk_path,
                            google_file_id=g.file_id,
                            yandex_md5=y_fp,
                            yandex_mtime=y.modified,
                            google_md5=_fp_g_meta(g_meta),
                            google_mtime=(g_meta or {}).get("modifiedTime"),
                        )
                    )
            else:
                data = drive.download_media(g.file_id)
                ya.ensure_parent_dirs(y_root, rel)
                ya.upload_bytes(ya.path_under_root(y_root, rel), data, overwrite=True)
                y_meta = ya.get_meta(ya.path_under_root(y_root, rel))
                log.info("Initial align G->Y: %s", rel)
                _bump(st, st_lock, "to_yandex")
                with _lk(db_lock):
                    db.upsert_file(
                        FileRow(
                            rel_path=rel,
                            yandex_path=y_meta.get("path"),
                            google_file_id=g.file_id,
                            yandex_md5=_fp_y_meta(y_meta),
                            yandex_mtime=y_meta.get("modified"),
                            google_md5=g_fp,
                            google_mtime=g.modified,
                        )
                    )
        else:
            with _lk(db_lock):
                db.upsert_file(
                    FileRow(
                        rel_path=rel,
                        yandex_path=y.disk_path,
                        google_file_id=g.file_id,
                        yandex_md5=y_fp,
                        yandex_mtime=y.modified,
                        google_md5=g_fp,
                        google_mtime=g.modified,
                    )
                )
            _bump(st, st_lock, "indexed_same")
        return

    y_changed = row.yandex_md5 != y_fp
    g_changed = row.google_md5 != g_fp

    if not y_changed and not g_changed:
        if row.yandex_path != y.disk_path or row.google_file_id != g.file_id:
            with _lk(db_lock):
                db.upsert_file(
                    FileRow(
                        rel_path=rel,
                        yandex_path=y.disk_path,
                        google_file_id=g.file_id,
                        yandex_md5=y_fp,
                        yandex_mtime=y.modified,
                        google_md5=g_fp,
                        google_mtime=g.modified,
                    )
                )
        _bump(st, st_lock, "unchanged")
        return

    if y_changed and not g_changed:
        data = ya.download_file(y.disk_path)
        drive.update_file_media(g.file_id, data)
        g_meta = drive.get_file(g.file_id)
        with _lk(db_lock):
            db.upsert_file(
                FileRow(
                    rel_path=rel,
                    yandex_path=y.disk_path,
                    google_file_id=g.file_id,
                    yandex_md5=y_fp,
                    yandex_mtime=y.modified,
                    google_md5=_fp_g_meta(g_meta),
                    google_mtime=(g_meta or {}).get("modifiedTime"),
                )
            )
        log.info("Yandex -> Drive (update): %s", rel)
        _bump(st, st_lock, "to_drive")
        return

    if g_changed and not y_changed:
        data = drive.download_media(g.file_id)
        ya.ensure_parent_dirs(y_root, rel)
        y_path = ya.path_under_root(y_root, rel)
        ya.upload_bytes(y_path, data, overwrite=True)
        y_meta = ya.get_meta(y_path)
        with _lk(db_lock):
            db.upsert_file(
                FileRow(
                    rel_path=rel,
                    yandex_path=y_path,
                    google_file_id=g.file_id,
                    yandex_md5=_fp_y_meta(y_meta),
                    yandex_mtime=y_meta.get("modified"),
                    google_md5=g_fp,
                    google_mtime=g.modified,
                )
            )
        log.info("Drive -> Yandex (update): %s", rel)
        _bump(st, st_lock, "to_yandex")
        return

    policy = settings.conflict_policy
    if policy == "manual":
        log.warning("Conflict (manual skip): %s", rel)
        _bump(st, st_lock, "conflict")
        return

    if policy == "lww":
        winner = _cmp_time(y.modified, g.modified)
        if winner <= 0:
            data = ya.download_file(y.disk_path)
            drive.update_file_media(g.file_id, data)
            g_meta = drive.get_file(g.file_id)
            with _lk(db_lock):
                db.upsert_file(
                    FileRow(
                        rel_path=rel,
                        yandex_path=y.disk_path,
                        google_file_id=g.file_id,
                        yandex_md5=y_fp,
                        yandex_mtime=y.modified,
                        google_md5=_fp_g_meta(g_meta),
                        google_mtime=(g_meta or {}).get("modifiedTime"),
                    )
                )
            log.warning("Conflict LWW Yandex wins: %s", rel)
            _bump(st, st_lock, "conflict")
        else:
            data = drive.download_media(g.file_id)
            ya.ensure_parent_dirs(y_root, rel)
            y_path = ya.path_under_root(y_root, rel)
            ya.upload_bytes(y_path, data, overwrite=True)
            y_meta = ya.get_meta(y_path)
            with _lk(db_lock):
                db.upsert_file(
                    FileRow(
                        rel_path=rel,
                        yandex_path=y_path,
                        google_file_id=g.file_id,
                        yandex_md5=_fp_y_meta(y_meta),
                        yandex_mtime=y_meta.get("modified"),
                        google_md5=g_fp,
                        google_mtime=g.modified,
                    )
                )
            log.warning("Conflict LWW Drive wins: %s", rel)
            _bump(st, st_lock, "conflict")
        return

    if policy == "branch":
        y_wins = _cmp_time(y.modified, g.modified) <= 0
        lose_data = drive.download_media(g.file_id) if y_wins else ya.download_file(y.disk_path)
        win_data = ya.download_file(y.disk_path) if y_wins else drive.download_media(g.file_id)
        side_rel = f"{rel}.conflict-{_now_suffix()}"

        if y_wins:
            drive.update_file_media(g.file_id, win_data)
            drive.create_file(g_root, side_rel, lose_data)
            ya.ensure_parent_dirs(y_root, rel)
            ya.upload_bytes(ya.path_under_root(y_root, rel), win_data, overwrite=True)
            ya.ensure_parent_dirs(y_root, side_rel)
            ya.upload_bytes(ya.path_under_root(y_root, side_rel), lose_data, overwrite=True)
            log.warning("Conflict branch: Yandex wins; loser at %s", side_rel)
            _bump(st, st_lock, "conflict")
        else:
            ya.ensure_parent_dirs(y_root, rel)
            ya.upload_bytes(ya.path_under_root(y_root, rel), win_data, overwrite=True)
            drive.update_file_media(g.file_id, win_data)
            drive.create_file(g_root, side_rel, lose_data)
            ya.ensure_parent_dirs(y_root, side_rel)
            ya.upload_bytes(ya.path_under_root(y_root, side_rel), lose_data, overwrite=True)
            log.warning("Conflict branch: Drive wins; loser at %s", side_rel)
            _bump(st, st_lock, "conflict")

        y_meta = ya.get_meta(ya.path_under_root(y_root, rel))
        g_meta = drive.get_file(g.file_id)
        with _lk(db_lock):
            db.upsert_file(
                FileRow(
                    rel_path=rel,
                    yandex_path=y_meta.get("path"),
                    google_file_id=g.file_id,
                    yandex_md5=_fp_y_meta(y_meta),
                    yandex_mtime=y_meta.get("modified"),
                    google_md5=_fp_g_meta(g_meta),
                    google_mtime=(g_meta or {}).get("modifiedTime"),
                )
            )
        return

    log.warning("Unknown conflict policy %r; skip %s", policy, rel)


_tls = threading.local()


def _worker_init(settings: Settings, g_creds) -> None:
    """Один комплект клиентов и своё подключение SQLite на поток."""
    _tls.ya = YandexDiskClient(
        settings.yandex_client_id,
        settings.yandex_client_secret,
        settings.yandex_token_path,
        oauth_token_url=settings.yandex_oauth_token_url,
    )
    _tls.drive = GoogleDriveClient(g_creds, shared_drive=settings.google_use_shared_drive)
    _tls.db = IndexDB(settings.state_dir / "index.sqlite")


def _worker_process(
    rel: str,
    settings: Settings,
    ya_files: dict[str, YandexFileMeta],
    g_files: dict[str, DriveFileMeta],
    db_lock: threading.Lock,
    st: dict[str, int],
    st_lock: threading.Lock,
    y_root: str,
    g_root: str,
) -> None:
    ya = _tls.ya
    drive = _tls.drive
    db = _tls.db
    assert ya is not None and drive is not None and db is not None
    _process_rel(
        rel,
        settings,
        ya_files,
        g_files,
        db,
        db_lock,
        st,
        st_lock,
        y_root,
        g_root,
        ya,
        drive,
    )


def run_once(settings: Settings) -> None:
    state = settings.state_dir
    state.mkdir(parents=True, exist_ok=True)
    db_path = state / "index.sqlite"
    db = IndexDB(db_path)

    ya = YandexDiskClient(
        settings.yandex_client_id,
        settings.yandex_client_secret,
        settings.yandex_token_path,
        oauth_token_url=settings.yandex_oauth_token_url,
    )
    g_creds = get_credentials(
        service_account_json=settings.google_service_account_file,
        oauth_token_json=settings.google_oauth_token_json,
        oauth_client_secrets=settings.google_oauth_client_secrets_file,
        oauth_token_path=state / "google_token.json",
    )
    drive = GoogleDriveClient(g_creds, shared_drive=settings.google_use_shared_drive)

    y_root = settings.yandex_sync_path.rstrip("/") or "/"
    g_root = settings.google_sync_folder_id

    tok = db.get_kv("drive_page_token")
    if not tok:
        tok = drive.get_start_page_token()
        db.set_kv("drive_page_token", tok)
    else:
        try:
            _, new_tok = drive.consume_changes_pages(tok)
            db.set_kv("drive_page_token", new_tok)
        except HttpError as e:
            status = e.resp.status if e.resp else 0
            log.warning("Drive changes reset after HTTP %s: %s", status, e)
            tok = drive.get_start_page_token()
            db.set_kv("drive_page_token", tok)

    raw_ya = ya.iter_folder_flat(y_root)
    ya_files: dict[str, YandexFileMeta] = {
        m.rel_path.rstrip("/"): m for m in raw_ya if not m.is_dir and not m.rel_path.endswith("/")
    }

    raw_g = drive.iter_tree(g_root)
    g_files: dict[str, DriveFileMeta] = {}
    for m in raw_g:
        if _is_skipped_drive_mime(m.mime):
            log.info("Skip Google native doc (export not implemented): %s", m.rel_path)
            continue
        g_files[m.rel_path] = m

    all_rel = set(ya_files) | set(g_files) | {r.rel_path for r in db.all_rows()}

    log.info(
        "Скан: Яндекс root=%r — файлов %d; Drive folder=%s — файлов %d; уникальных путей %d",
        y_root,
        len(ya_files),
        g_root,
        len(g_files),
        len(all_rel),
    )

    st: dict[str, int] = {
        "to_drive": 0,
        "to_yandex": 0,
        "indexed_same": 0,
        "unchanged": 0,
        "deleted": 0,
        "conflict": 0,
    }

    rels = [r for r in sorted(all_rel) if not r.endswith("/")]

    workers = settings.sync_parallel_workers
    log.info("Потоков передачи файлов: %d (переменная SYNC_PARALLEL_WORKERS)", workers)

    if workers <= 1:
        for rel in rels:
            _process_rel(
                rel,
                settings,
                ya_files,
                g_files,
                db,
                None,
                st,
                None,
                y_root,
                g_root,
                ya,
                drive,
            )
    else:
        db_lock = threading.Lock()
        st_lock = threading.Lock()
        with ThreadPoolExecutor(
            max_workers=workers,
            initializer=_worker_init,
            initargs=(settings, g_creds),
        ) as ex:
            futs = [
                ex.submit(
                    _worker_process,
                    rel,
                    settings,
                    ya_files,
                    g_files,
                    db_lock,
                    st,
                    st_lock,
                    y_root,
                    g_root,
                )
                for rel in rels
            ]
            for f in as_completed(futs):
                f.result()

    log.info(
        "Итог: на Drive залито/обновлено=%d, на Яндекс=%d, только связано в индексе "
        "(одинаковое содержимое)=%d, без изменений=%d, удалений=%d, конфликтов=%d",
        st["to_drive"],
        st["to_yandex"],
        st["indexed_same"],
        st["unchanged"],
        st["deleted"],
        st["conflict"],
    )
