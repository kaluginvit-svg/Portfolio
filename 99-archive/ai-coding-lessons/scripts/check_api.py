#!/usr/bin/env python3
"""
Проверка эндпоинтов HTTP API (Flask / тот же контракт в Docker).

Базовый URL: переменная окружения API_BASE (по умолчанию http://127.0.0.1:5000).

Запуск:
  python scripts/check_api.py
  set API_BASE=http://127.0.0.1:8080
  python scripts/check_api.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple


def _base() -> str:
    return os.environ.get("API_BASE", "http://127.0.0.1:5000").rstrip("/")


def _request_json(
    method: str,
    path: str,
    body: Optional[dict[str, Any]] = None,
) -> Tuple[int, str]:
    url = _base() + path
    headers: dict[str, str] = {}
    if method == "POST" and body is None:
        data: Optional[bytes] = b""
        headers["Content-Type"] = "application/json; charset=utf-8"
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    return _do_request(req)


def _request_raw_post(path: str, raw: bytes) -> Tuple[int, str]:
    url = _base() + path
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    return _do_request(req)


def _do_request(req: urllib.request.Request) -> Tuple[int, str]:
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        return e.code, raw


def _fail(name: str, detail: str) -> None:
    print(f"FAIL: {name}: {detail}", file=sys.stderr)


def _ok(name: str) -> None:
    print(f"OK:   {name}")


def main() -> int:
    code, body = _request_json("GET", "/health")
    if code != 200:
        _fail("GET /health", f"status={code} body={body}")
        return 1
    try:
        j = json.loads(body)
    except json.JSONDecodeError as e:
        _fail("GET /health", f"not json: {e}")
        return 1
    if j.get("status") != "ok":
        _fail("GET /health", f"unexpected: {j!r}")
        return 1
    _ok("GET /health")

    code, body = _request_json("POST", "/users", body=None)
    if code != 400:
        _fail("POST /users (нет JSON-объекта)", f"expected 400, got {code} body={body}")
        return 1
    _ok("POST /users — тело не объект JSON → 400")

    code, body = _request_raw_post("/users", b"{not-json")
    if code != 400:
        _fail("POST /users (битый JSON)", f"expected 400, got {code} body={body}")
        return 1
    _ok("POST /users — битый JSON → 400")

    code, body = _request_json("POST", "/users", body={"name": ""})
    if code != 400:
        _fail("POST /users (empty name)", f"expected 400, got {code}")
        return 1
    _ok("POST /users — пустое name → 400")

    code, body = _request_json("POST", "/users", body={"name": "x", "tags": "not-a-list"})
    if code != 400:
        _fail("POST /users (tags not list)", f"expected 400, got {code}")
        return 1
    _ok("POST /users — tags не массив → 400")

    code, body = _request_json("POST", "/users", body={"name": "x", "password": 123})
    if code != 400:
        _fail("POST /users (password not str)", f"expected 400, got {code}")
        return 1
    _ok("POST /users — password не строка → 400")

    code, body = _request_json(
        "POST",
        "/users",
        body={"name": "docker_tester", "tags": ["a"], "password": "secret"},
    )
    if code != 201:
        _fail("POST /users (success)", f"expected 201, got {code} body={body}")
        return 1
    try:
        j = json.loads(body)
    except json.JSONDecodeError as e:
        _fail("POST /users (success)", f"not json: {e}")
        return 1
    if "id" not in j:
        _fail("POST /users (success)", f"no id: {j!r}")
        return 1
    _ok("POST /users — успешное создание → 201")

    code, _ = _request_json("GET", "/users")
    if code != 405:
        _fail("GET /users", f"expected 405, got {code}")
        return 1
    _ok("GET /users — метод не разрешён → 405")

    code, _ = _request_json("POST", "/health")
    if code != 405:
        _fail("POST /health", f"expected 405, got {code}")
        return 1
    _ok("POST /health — метод не разрешён → 405")

    print(f"Все проверки пройдены (API_BASE={_base()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
