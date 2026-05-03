# -*- coding: utf-8 -*-
"""
Обмен authorization code на access token Miro (OAuth 2.0).

Как получить AUTH_CODE:
  1. Откройте в браузере URL авторизации (скрипт выведет его по ключу --auth-url).
  2. Войдите в Miro и разрешите доступ приложению.
  3. После редиректа на redirect_uri в адресной строке будет параметр code=... — это AUTH_CODE.

Использование:
  set MIRO_CLIENT_ID=ваш_client_id
  set MIRO_CLIENT_SECRET=ваш_client_secret
  set MIRO_REDIRECT_URI=http://localhost:3000/callback
  python get_miro_token.py --code "eyJtaXJvLm9yaWdpbiI6ImV1MDEifQ_NEV9BP"

  Или интерактивно (скрипт спросит код и при необходимости client_id/secret/redirect_uri):
  python get_miro_token.py

  Только вывести URL для авторизации:
  python get_miro_token.py --auth-url
"""

import argparse
import os
import sys

try:
    import requests
except ImportError:
    print("Установите requests: pip install requests")
    sys.exit(1)

# OAuth endpoints Miro
MIRO_AUTH_URL = "https://miro.com/oauth/authorize"
MIRO_TOKEN_URL = "https://api.miro.com/v1/oauth/token"


def get_config():
    """Читает конфиг из переменных окружения или запрашивает в терминале."""
    client_id = os.environ.get("MIRO_CLIENT_ID", "").strip()
    client_secret = os.environ.get("MIRO_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("MIRO_REDIRECT_URI", "http://localhost:3000/callback").strip()
    if sys.stdin.isatty():
        if not client_id:
            client_id = input("MIRO_CLIENT_ID: ").strip()
        if not client_secret:
            client_secret = input("MIRO_CLIENT_SECRET: ").strip()
        if not redirect_uri:
            redirect_uri = input("MIRO_REDIRECT_URI [http://localhost:3000/callback]: ").strip() or "http://localhost:3000/callback"
    return client_id, client_secret, redirect_uri


def build_auth_url(client_id, redirect_uri):
    """Собирает URL для авторизации пользователя в Miro."""
    return (
        f"{MIRO_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={requests.utils.quote(redirect_uri)}"
        f"&scope=boards:read boards:write"
    )


def exchange_code_for_token(client_id, client_secret, redirect_uri, code):
    """Обменивает authorization code на access_token."""
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code.strip(),
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(MIRO_TOKEN_URL, data=data, timeout=30)
    if not resp.ok:
        print(resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Получить access token Miro по authorization code")
    parser.add_argument("--code", "-c", help="Authorization code из URL после редиректа")
    parser.add_argument("--auth-url", action="store_true", help="Только вывести URL для авторизации")
    args = parser.parse_args()

    client_id, client_secret, redirect_uri = get_config()

    if args.auth_url:
        if not client_id:
            print("Задайте MIRO_CLIENT_ID (или передайте для --code после).")
            sys.exit(1)
        print("Откройте в браузере и после входа скопируйте параметр code из URL:")
        print(build_auth_url(client_id, redirect_uri))
        return

    if not client_id or not client_secret:
        print("Задайте MIRO_CLIENT_ID и MIRO_CLIENT_SECRET (или введите в терминале).")
        sys.exit(1)

    code = args.code
    if not code and sys.stdin.isatty():
        code = input("Введите authorization code (code из URL после редиректа): ").strip()
    if not code:
        print("Нужен authorization code. Используйте --code или задайте при запросе.")
        sys.exit(1)

    result = exchange_code_for_token(client_id, client_secret, redirect_uri, code)
    access_token = result.get("access_token")
    if access_token:
        print("\n--- Access token (используйте как MIRO_ACCESS_TOKEN): ---")
        print(access_token)
        print("---")
    if result.get("refresh_token"):
        print("Refresh token:", result.get("refresh_token"))


if __name__ == "__main__":
    main()
