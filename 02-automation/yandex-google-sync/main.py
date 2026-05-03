#!/usr/bin/env python3
"""CLI: Yandex OAuth helper + one sync run."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Сразу видимый вывод в терминале Cursor / cmd (без задержки буфера)
os.environ.setdefault("PYTHONUNBUFFERED", "1")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Allow running without installing package
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sync_app.config import Settings
from sync_app.yandex_oauth import (
    build_authorize_url,
    exchange_code,
    obtain_tokens_interactive,
    save_tokens,
)


def _load_dotenv() -> None:
    env_path = _ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def cmd_yandex_login(args: argparse.Namespace) -> None:
    s = Settings.from_env()
    if not s.yandex_client_id or not s.yandex_client_secret:
        raise SystemExit("Set YANDEX_CLIENT_ID and YANDEX_CLIENT_SECRET")

    # Фиксированный Redirect в кабинете (часто https://oauth.yandex.ru/verification_code):
    # открываете ссылку, копируете код, затем: python main.py yandex-login --code КОД
    if getattr(args, "print_url", False):
        ru = s.yandex_redirect_uri or f"http://127.0.0.1:{args.port}/"
        print(
            build_authorize_url(
                s.yandex_client_id,
                ru,
                authorize_url=s.yandex_oauth_authorize_url,
                scope=s.yandex_oauth_scope,
            ),
            flush=True,
        )
        return

    code = (getattr(args, "code", None) or "").strip()
    if code:
        if not s.yandex_redirect_uri:
            raise SystemExit(
                "Укажите в .env YANDEX_REDIRECT_URI — ту же строку, что «Redirect URL» "
                "в приложении OAuth (например https://oauth.yandex.ru/verification_code)"
            )
        tokens = exchange_code(
            s.yandex_client_id,
            s.yandex_client_secret,
            code,
            s.yandex_redirect_uri,
            token_url=s.yandex_oauth_token_url,
        )
        save_tokens(s.yandex_token_path, tokens)
        print(f"Токены сохранены: {s.yandex_token_path}", flush=True)
        return

    obtain_tokens_interactive(
        s.yandex_client_id,
        s.yandex_client_secret,
        s.yandex_token_path,
        authorize_url=s.yandex_oauth_authorize_url,
        token_url=s.yandex_oauth_token_url,
        port=args.port,
        redirect_uri=s.yandex_redirect_uri,
        scope=s.yandex_oauth_scope,
    )


def cmd_sync(_args: argparse.Namespace) -> None:
    s = Settings.from_env()
    if not s.yandex_client_id:
        raise SystemExit("Missing YANDEX_CLIENT_ID")
    if os.environ.get("GOOGLE_OAUTH_TOKEN_JSON", "").strip():
        gpath = s.google_oauth_token_json
        if not gpath or not gpath.is_file():
            raise SystemExit(f"GOOGLE_OAUTH_TOKEN_JSON not found: {gpath}")
    if not s.google_sync_folder_id:
        raise SystemExit("Missing GOOGLE_SYNC_FOLDER_ID")
    go = s.google_oauth_token_json
    if (
        not s.google_service_account_file
        and not (go and go.is_file())
        and not s.google_oauth_client_secrets_file
    ):
        raise SystemExit(
            "Set GOOGLE_OAUTH_TOKEN_JSON and/or GOOGLE_SERVICE_ACCOUNT_JSON "
            "or GOOGLE_OAUTH_CLIENT_SECRETS"
        )
    from sync_app.engine import run_once

    run_once(s)


def main() -> None:
    _load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Yandex Disk ↔ Google Drive sync")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_y = sub.add_parser(
        "yandex-login",
        help="Получить токены Яндекса (браузер на localhost или код для verification_code)",
    )
    p_y.add_argument("--port", type=int, default=8899)
    p_y.add_argument(
        "--code",
        metavar="CODE",
        help="Код со страницы после входа (если Redirect URL = verification_code и т.п.)",
    )
    p_y.add_argument(
        "--print-url",
        action="store_true",
        help="Только вывести ссылку авторизации (открыть в браузере вручную)",
    )
    p_y.set_defaults(func=cmd_yandex_login)

    p_s = sub.add_parser("sync", help="Run one bidirectional sync cycle")
    p_s.set_defaults(func=cmd_sync)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
