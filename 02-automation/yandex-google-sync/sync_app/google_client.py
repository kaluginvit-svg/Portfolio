"""Google Drive API: tree listing, changes, download, resumable upload."""

from __future__ import annotations

import io
import time
from dataclasses import dataclass
from typing import Callable

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

FOLDER_MIME = "application/vnd.google-apps.folder"


def _escape_drive_q_literal(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _retry(fn: Callable, max_attempts: int = 6) -> object:
    delay = 1.0
    last = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except HttpError as e:
            last = e
            status = e.resp.status if e.resp else 0
            if status in (403, 429) or status >= 500:
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            raise
    assert last
    raise last


@dataclass
class DriveFileMeta:
    rel_path: str
    file_id: str
    mime: str
    md5: str | None
    modified: str | None
    size: int | None


class GoogleDriveClient:
    def __init__(self, creds, shared_drive: bool = False) -> None:
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.shared_drive = shared_drive
        # Many methods accept only supportsAllDrives; includeItemsFromAllDrives is for list APIs.
        self._supports = {"supportsAllDrives": True} if shared_drive else {}
        self._kw_list = (
            {"supportsAllDrives": True, "includeItemsFromAllDrives": True}
            if shared_drive
            else {}
        )
        self._changes_start_kw = self._supports

    def _list_kwargs(self, q: str, page_token: str | None = None) -> dict:
        d = {
            "q": q,
            "spaces": "drive",
            "fields": "nextPageToken, files(id, name, mimeType, md5Checksum, modifiedTime, size, parents)",
            "pageSize": 100,
        }
        if page_token:
            d["pageToken"] = page_token
        d.update(self._kw_list)
        return d

    def iter_tree(self, root_folder_id: str) -> list[DriveFileMeta]:
        """All non-folder files under root (recursive). rel_path uses '/' ."""

        def walk(folder_id: str, rel: str) -> list[DriveFileMeta]:
            out: list[DriveFileMeta] = []
            page = None
            while True:
                kwargs = self._list_kwargs(
                    f"'{folder_id}' in parents and trashed = false",
                    page,
                )

                def call():
                    return self.service.files().list(**kwargs).execute()

                resp = _retry(call)
                for f in resp.get("files", []):
                    fid = f["id"]
                    name = f.get("name") or ""
                    mime = f.get("mimeType") or ""
                    rel_path = f"{rel}/{name}".strip("/") if rel else name
                    if mime == FOLDER_MIME:
                        out.extend(walk(fid, rel_path))
                    else:
                        out.append(
                            DriveFileMeta(
                                rel_path=rel_path,
                                file_id=fid,
                                mime=mime,
                                md5=f.get("md5Checksum"),
                                modified=f.get("modifiedTime"),
                                size=int(f["size"]) if f.get("size") else None,
                            )
                        )
                page = resp.get("nextPageToken")
                if not page:
                    break
            return out

        return walk(root_folder_id, "")

    def get_start_page_token(self) -> str:
        def call():
            return (
                self.service.changes()
                .getStartPageToken(**self._changes_start_kw)
                .execute()
            )

        return _retry(call)["startPageToken"]

    def consume_changes_pages(self, page_token: str) -> tuple[list[str], str]:
        """Read all pages of changes.list; returns (file_ids_touched, new_start_page_token)."""

        touched: list[str] = []
        token: str | None = page_token
        new_start: str | None = None
        while token:
            pt = token

            def call():
                return (
                    self.service.changes()
                    .list(
                        pageToken=pt,
                        fields="nextPageToken, newStartPageToken, changes(fileId, removed)",
                        **self._kw_list,
                    )
                    .execute()
                )

            resp = _retry(call)
            for ch in resp.get("changes", []):
                touched.append(ch["fileId"])
            new_start = resp.get("newStartPageToken") or new_start
            token = resp.get("nextPageToken")
        if not new_start:
            new_start = self.get_start_page_token()
        return touched, new_start

    def get_file(self, file_id: str) -> dict | None:
        def call():
            return (
                self.service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, md5Checksum, modifiedTime, size, parents, trashed",
                    **self._supports,
                )
                .execute()
            )

        try:
            return _retry(call)
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise

    def rel_path_for_file(self, file_id: str, sync_root_id: str) -> str | None:
        """Build posix rel path from sync root to file; None if not under root."""
        parts: list[str] = []
        cur = file_id
        guard = 0
        while cur and guard < 256:
            guard += 1
            meta = self.get_file(cur)
            if not meta or meta.get("trashed"):
                return None
            if cur == sync_root_id:
                return "/".join(reversed(parts)) if parts else ""
            name = meta.get("name") or ""
            parents = meta.get("parents") or []
            parts.append(name)
            if not parents:
                return None
            cur = parents[0]
        return None

    def download_media(self, file_id: str) -> bytes:
        request = self.service.files().get_media(fileId=file_id, **self._supports)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = _retry(lambda: downloader.next_chunk())
        return fh.getvalue()

    def ensure_folder(self, parent_id: str, name: str) -> str:
        esc = _escape_drive_q_literal(name)
        q = (
            f"name = '{esc}' and mimeType = '{FOLDER_MIME}' and "
            f"'{parent_id}' in parents and trashed = false"
        )
        kwargs = self._list_kwargs(q)
        resp = _retry(lambda: self.service.files().list(**kwargs).execute())
        files = resp.get("files", [])
        if files:
            return files[0]["id"]
        body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]}
        created = _retry(
            lambda: self.service.files()
            .create(body=body, fields="id", **self._supports)
            .execute()
        )
        return created["id"]

    def ensure_path(self, root_folder_id: str, rel_path: str) -> str:
        """Return folder id for parent of file rel_path (creates subfolders)."""
        rel_path = rel_path.strip("/").replace("\\", "/")
        if not rel_path:
            return root_folder_id
        parts = rel_path.split("/")
        if len(parts) == 1:
            return root_folder_id
        cur = root_folder_id
        for part in parts[:-1]:
            cur = self.ensure_folder(cur, part)
        return cur

    def create_file(self, root_folder_id: str, rel_path: str, data: bytes, mime: str | None = None) -> str:
        rel_path = rel_path.replace("\\", "/").strip("/")
        name = rel_path.split("/")[-1]
        parent_id = self.ensure_path(root_folder_id, rel_path)
        body = {"name": name, "parents": [parent_id]}
        media = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype=mime or "application/octet-stream",
            resumable=True,
        )
        request = self.service.files().create(body=body, media_body=media, fields="id", **self._supports)
        response = None
        while response is None:
            status, response = request.next_chunk()
        return response["id"]

    def update_file_media(self, file_id: str, data: bytes, mime: str | None = None) -> dict:
        media = MediaIoBaseUpload(
            io.BytesIO(data),
            mimetype=mime or "application/octet-stream",
            resumable=True,
        )
        request = self.service.files().update(
            fileId=file_id,
            media_body=media,
            fields="id, md5Checksum, modifiedTime",
            **self._supports,
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
        return response

    def delete_file(self, file_id: str) -> None:
        def call():
            return self.service.files().delete(fileId=file_id, **self._supports).execute()

        try:
            _retry(call)
        except HttpError as e:
            if e.resp.status == 404:
                return
            raise
