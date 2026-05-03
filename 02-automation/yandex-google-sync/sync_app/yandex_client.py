"""Yandex Disk REST API: list tree, download, upload, delete."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import httpx

from sync_app import yandex_oauth

BASE = "https://cloud-api.yandex.net/v1/disk"


@dataclass
class YandexFileMeta:
    rel_path: str  # posix relative to sync root
    disk_path: str  # full path on disk
    is_dir: bool
    size: int | None
    md5: str | None
    modified: str | None  # ISO from API


class YandexDiskClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_path: Path,
        *,
        oauth_token_url: str = "https://oauth.yandex.com/token",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = token_path
        self._oauth_token_url = oauth_token_url
        self._access: str | None = None
        self._refresh: str | None = None

    def _load(self) -> None:
        data = yandex_oauth.load_tokens(self.token_path)
        if not data:
            raise FileNotFoundError(f"Yandex tokens not found: {self.token_path}")
        self._access = data.get("access_token")
        self._refresh = data.get("refresh_token")

    def _save_merged(self, new_data: dict) -> None:
        old = yandex_oauth.load_tokens(self.token_path) or {}
        old.update(new_data)
        yandex_oauth.save_tokens(self.token_path, old)

    def ensure_access(self) -> str:
        if not self._access:
            self._load()
        assert self._access
        return self._access

    def refresh_if_needed(self) -> None:
        self.ensure_access()
        # Caller can retry on 401
        pass

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"OAuth {self.ensure_access()}"}

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        timeout = kwargs.pop("timeout", 120.0)
        extra_headers = kwargs.pop("headers", {})

        def once() -> httpx.Response:
            h = {**self._auth_headers(), **extra_headers}
            # Disk download href redirects (302) to storage.yandex.net — must follow.
            with httpx.Client(timeout=timeout, follow_redirects=True) as c:
                return c.request(method, url, headers=h, **kwargs)

        r = once()
        if r.status_code == 401 and self._refresh:
            data = yandex_oauth.refresh_access_token(
                self.client_id,
                self.client_secret,
                self._refresh,
                token_url=self._oauth_token_url,
            )
            self._access = data.get("access_token")
            if "refresh_token" in data:
                self._refresh = data["refresh_token"]
            self._save_merged(data)
            r = once()
        return r

    def get_meta(self, path: str) -> dict:
        url = f"{BASE}/resources?{urllib.parse.urlencode({'path': path})}"
        r = self._request("GET", url)
        r.raise_for_status()
        return r.json()

    def list_dir(self, path: str, limit: int = 200, offset: int = 0) -> dict:
        q = {"path": path, "limit": limit, "offset": offset}
        url = f"{BASE}/resources?{urllib.parse.urlencode(q)}"
        r = self._request("GET", url)
        r.raise_for_status()
        return r.json()

    def iter_folder_flat(self, root_path: str) -> list[YandexFileMeta]:
        """Recursive listing; root_path is sync root (e.g. /sync)."""
        root_path = root_path.rstrip("/") or "/"
        out: list[YandexFileMeta] = []

        def walk(disk_path: str, rel: str) -> None:
            offset = 0
            while True:
                data = self.list_dir(disk_path, limit=200, offset=offset)
                emb = data.get("_embedded") or {}
                items = emb.get("items") or []
                if not items:
                    break
                for it in items:
                    name = it.get("name") or ""
                    p = it.get("path") or ""
                    t = it.get("type")
                    is_dir = t == "dir"
                    rel_path = f"{rel}/{name}".strip("/") if rel else name
                    if is_dir:
                        out.append(
                            YandexFileMeta(
                                rel_path=rel_path + "/",  # trailing slash for dirs
                                disk_path=p,
                                is_dir=True,
                                size=None,
                                md5=None,
                                modified=it.get("modified"),
                            )
                        )
                        walk(p, rel_path)
                    else:
                        out.append(
                            YandexFileMeta(
                                rel_path=rel_path,
                                disk_path=p,
                                is_dir=False,
                                size=it.get("size"),
                                md5=it.get("md5"),
                                modified=it.get("modified"),
                            )
                        )
                if len(items) < 200:
                    break
                offset += len(items)

        walk(root_path, "")
        return out

    def get_download_link(self, path: str) -> str:
        url = f"{BASE}/resources/download?{urllib.parse.urlencode({'path': path})}"
        r = self._request("GET", url)
        r.raise_for_status()
        return r.json()["href"]

    def download_file(self, disk_path: str) -> bytes:
        href = self.get_download_link(disk_path)
        r = self._request("GET", href)
        r.raise_for_status()
        return r.content

    def upload_bytes(self, disk_path: str, content: bytes, overwrite: bool = True) -> None:
        q = {"path": disk_path, "overwrite": str(overwrite).lower()}
        url = f"{BASE}/resources/upload?{urllib.parse.urlencode(q)}"
        r = self._request("GET", url)
        r.raise_for_status()
        href = r.json()["href"]
        up = self._request("PUT", href, content=content)
        up.raise_for_status()

    def mkdir(self, disk_path: str) -> None:
        q = {"path": disk_path}
        url = f"{BASE}/resources?{urllib.parse.urlencode(q)}"
        r = self._request("PUT", url)
        if r.status_code in (201, 409):
            return
        r.raise_for_status()

    def ensure_parent_dirs(self, root: str, rel_file: str) -> None:
        """Create folder chain for rel_file (file path) under root."""
        parts = rel_file.strip("/").replace("\\", "/").split("/")[:-1]
        cur = root.rstrip("/") or "/"
        for p in parts:
            cur = f"{cur}/{p}".replace("//", "/")
            self.mkdir(cur)

    def delete(self, disk_path: str, permanently: bool = False) -> None:
        q: dict[str, str] = {"path": disk_path}
        if permanently:
            q["permanently"] = "true"
        url = f"{BASE}/resources?{urllib.parse.urlencode(q)}"
        r = self._request("DELETE", url)
        if r.status_code in (204, 404):
            return
        r.raise_for_status()

    def path_under_root(self, root: str, rel_path: str) -> str:
        root = root.rstrip("/") or "/"
        rel = rel_path.strip("/")
        if not rel:
            return root
        return f"{root}/{rel}".replace("//", "/")
