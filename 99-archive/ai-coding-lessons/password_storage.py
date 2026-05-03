"""Запись хешей паролей в файл (внутренний слой)."""
import hashlib
import secrets

from settings import ITERATIONS, PASSWORDS_FILE, SALT_BYTES


def append_password_hash(user_id: int, password: str) -> None:
    """Сохраняет PBKDF2-SHA256 в файл. Для внешнего кода — api.store_password."""
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )
    line = (
        f"{user_id}:"
        f"{salt.hex()}:"
        f"{ITERATIONS}:"
        f"{dk.hex()}\n"
    )
    with PASSWORDS_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
