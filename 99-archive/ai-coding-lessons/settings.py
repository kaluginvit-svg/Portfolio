"""Пути и параметры криптографии (одна точка конфигурации)."""
import os
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", "users.db")
PASSWORDS_FILE = Path(os.environ.get("PASSWORDS_FILE", "passwords.txt"))
SALT_BYTES = 16
ITERATIONS = 390_000
