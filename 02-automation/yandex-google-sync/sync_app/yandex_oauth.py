"""Yandex OAuth: exchange code, refresh tokens; CLI helper."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx

# Fallback, если scope не передан (конфиг задаёт два права отдельно)
DEFAULT_SCOPE = "cloud_api:disk.read cloud_api:disk.write"


def build_authorize_url(
    client_id: str,
    redirect_uri: str,
    *,
    authorize_url: str,
    state: str = "",
    scope: str | None = None,
) -> str:
    """Собирает URL авторизации; пробелы в scope кодируются как %20 (часто нужно для Яндекса)."""
    q: dict[str, str] = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope or DEFAULT_SCOPE,
    }
    if state:
        q["state"] = state
    qs = urllib.parse.urlencode(q, quote_via=urllib.parse.quote)
    base = authorize_url.rstrip("/").rstrip("?")
    return f"{base}?{qs}"


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    *,
    token_url: str,
) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=60.0) as c:
        r = c.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    *,
    token_url: str,
) -> dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    with httpx.Client(timeout=60.0) as c:
        r = c.post(token_url, data=data)
        r.raise_for_status()
        return r.json()


def save_tokens(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_tokens(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_path(path: str) -> str:
    if not path or path == "":
        return "/"
    return path


def obtain_tokens_interactive(
    client_id: str,
    client_secret: str,
    out_path: Path,
    *,
    authorize_url: str,
    token_url: str,
    port: int = 8899,
    redirect_uri: str | None = None,
    scope: str | None = None,
) -> None:
    """
    If redirect_uri is set, it must match the Redirect URL in the Yandex OAuth app exactly.
    Host/port/path are used to bind the local HTTP server (loopback only).
    If redirect_uri is None, uses http://127.0.0.1:{port}/
    """
    if redirect_uri:
        ru = redirect_uri.strip()
        u = urllib.parse.urlparse(ru)
        if u.scheme not in ("http", "https"):
            raise ValueError("YANDEX_REDIRECT_URI must start with http:// or https://")
        host = u.hostname or "127.0.0.1"
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(
                "Only loopback hosts are supported for the local callback server "
                "(127.0.0.1 or localhost)"
            )
        prt = u.port
        if prt is None:
            raise ValueError(
                "Redirect URI must include an explicit port for local HTTP callback "
                "(e.g. http://127.0.0.1:8899/)"
            )
        expect_path = _normalize_path(u.path)
        redirect_for_oauth = ru
    else:
        host = "127.0.0.1"
        prt = port
        expect_path = "/"
        redirect_for_oauth = f"http://127.0.0.1:{port}/"

    result: dict[str, str | None] = {"code": None, "error": None}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            req_path = _normalize_path(parsed.path)
            if req_path.rstrip("/") != expect_path.rstrip("/"):
                self.send_response(404)
                self.end_headers()
                return
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                result["code"] = qs["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK. You can close this tab.")
            elif "error" in qs:
                result["error"] = qs.get("error", ["unknown"])[0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"OAuth error. See console.")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer((host, prt), Handler)
    url = build_authorize_url(
        client_id,
        redirect_for_oauth,
        authorize_url=authorize_url,
        scope=scope,
    )
    print("Open this URL in a browser and approve access:\n", url, sep="")
    print("Waiting for redirect to:", redirect_for_oauth)
    server.handle_request()
    server.server_close()
    code = result["code"]
    if result["error"]:
        raise RuntimeError(f"OAuth error: {result['error']}")
    if not code:
        raise RuntimeError("No authorization code received")
    tokens = exchange_code(
        client_id,
        client_secret,
        code,
        redirect_for_oauth,
        token_url=token_url,
    )
    save_tokens(out_path, tokens)
    print(f"Tokens saved to {out_path}")
