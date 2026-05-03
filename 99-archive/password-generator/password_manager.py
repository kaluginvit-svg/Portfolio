import getpass
import hashlib
import sqlite3
import string
import sys
from pathlib import Path
from secrets import choice

from cryptography.fernet import Fernet


DB_PATH = Path("vault.db")
KEY_FILE = Path(".key")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS credentials (
            name TEXT PRIMARY KEY,
            login TEXT NOT NULL,
            password BLOB NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    conn.commit()


def get_setting(conn: sqlite3.Connection, key: str):
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None


def set_setting(conn: sqlite3.Connection, key: str, value: str):
    conn.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def load_or_create_key() -> Fernet:
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    return Fernet(key)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def prompt_set_master(conn: sqlite3.Connection):
    print("Настройка мастер-пароля.")
    while True:
        pw1 = getpass.getpass("Введите мастер-пароль: ")
        pw2 = getpass.getpass("Повторите мастер-пароль: ")
        if not pw1:
            print("Пароль не может быть пустым.")
            continue
        if pw1 != pw2:
            print("Пароли не совпадают, попробуйте ещё раз.")
            continue
        set_setting(conn, "master_hash", hash_password(pw1))
        print("Мастер-пароль установлен.")
        break


def verify_master(conn: sqlite3.Connection):
    stored_hash = get_setting(conn, "master_hash")
    if stored_hash is None:
        prompt_set_master(conn)
        return

    for attempt in range(3):
        password = getpass.getpass("Введите мастер-пароль: ")
        if hash_password(password) == stored_hash:
            return
        print("Неверный пароль. Осталось попыток:", 2 - attempt)
    print("Доступ запрещён.")
    sys.exit(1)


def encrypt_password(fernet: Fernet, password: str) -> bytes:
    return fernet.encrypt(password.encode("utf-8"))


def decrypt_password(fernet: Fernet, token: bytes) -> str:
    return fernet.decrypt(token).decode("utf-8")


def add_entry(conn: sqlite3.Connection, fernet: Fernet, name: str, login: str, password: str):
    encrypted = encrypt_password(fernet, password)
    try:
        conn.execute(
            "INSERT INTO credentials(name, login, password) VALUES(?, ?, ?)",
            (name, login, encrypted),
        )
        conn.commit()
        print(f'Запись "{name}" сохранена.')
    except sqlite3.IntegrityError:
        print(f'Запись с названием "{name}" уже существует.')


def get_entry(conn: sqlite3.Connection, fernet: Fernet, name: str):
    cur = conn.execute(
        "SELECT login, password FROM credentials WHERE name = ?", (name,)
    )
    row = cur.fetchone()
    if not row:
        print("Запись не найдена.")
        return
    login, password_enc = row
    password = decrypt_password(fernet, password_enc)
    print(f"Название: {name}")
    print(f"Логин: {login}")
    print(f"Пароль: {password}")


def list_entries(conn: sqlite3.Connection):
    cur = conn.execute("SELECT name, login FROM credentials ORDER BY name")
    rows = cur.fetchall()
    if not rows:
        print("Нет сохранённых записей.")
        return
    for name, login in rows:
        print(f"{name} — {login}")


def delete_entry(conn: sqlite3.Connection, name: str):
    cur = conn.execute("DELETE FROM credentials WHERE name = ?", (name,))
    conn.commit()
    if cur.rowcount:
        print("Запись удалена.")
    else:
        print("Запись не найдена.")


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(choice(alphabet) for _ in range(length))


def generate_password_custom(
    length: int,
    use_upper: bool,
    use_lower: bool,
    use_digits: bool,
    use_symbols: bool,
) -> str:
    pool = ""
    if use_upper:
        pool += string.ascii_uppercase
    if use_lower:
        pool += string.ascii_lowercase
    if use_digits:
        pool += string.digits
    if use_symbols:
        pool += string.punctuation
    if not pool:
        raise ValueError("Нужно выбрать хотя бы один тип символов.")
    return "".join(choice(pool) for _ in range(length))


def prompt_length(default: int = 16) -> int:
    raw = input(f"Длина пароля [{default}]: ").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        return max(8, value)
    except ValueError:
        print("Некорректное число, использую значение по умолчанию.")
        return default


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "[д/н]" if not default else "[Д/н]"
    while True:
        ans = input(f"{prompt} {hint}: ").strip().lower()
        if not ans and default is not None:
            return default
        if ans in ("д", "y", "yes", "да"):
            return True
        if ans in ("н", "n", "no", "нет"):
            return False
        print("Введите д/н.")


def interactive_loop(conn: sqlite3.Connection, fernet: Fernet):
    actions = {
        "1": "add",
        "2": "get",
        "3": "list",
        "4": "delete",
        "5": "new",
        "0": "exit",
        # Русские команды
        "добавить": "add",
        "получить": "get",
        "список": "list",
        "удалить": "delete",
        "новый": "new",
        "выход": "exit",
        # Английские эквиваленты тоже работают
        "add": "add",
        "get": "get",
        "list": "list",
        "delete": "delete",
        "new": "new",
        "exit": "exit",
        "quit": "exit",
    }

    while True:
        print("\nВыберите действие:")
        print(" 1) добавить — сохранить пароль")
        print(" 2) получить — показать логин и пароль по названию")
        print(" 3) список   — показать все пароли")
        print(" 4) удалить  — удалить пароль")
        print(" 5) новый    — сгенерировать новый пароль")
        print(" 0) выход    — завершить работу")
        choice = input("> ").strip().lower()
        command = actions.get(choice)

        if command is None:
            print("Неизвестная команда, попробуйте снова.")
            continue
        if command == "exit":
            print("Выход.")
            break
        if command == "add":
            name = input("Название: ").strip()
            login = input("Логин: ").strip()
            if not name or not login:
                print("Название и логин не могут быть пустыми.")
                continue

            password = None
            if ask_yes_no("Сгенерировать пароль?"):
                length = prompt_length()
                while True:
                    use_upper = ask_yes_no("Использовать заглавные буквы?", default=True)
                    use_lower = ask_yes_no("Использовать строчные буквы?", default=True)
                    use_digits = ask_yes_no("Использовать цифры?", default=True)
                    use_symbols = ask_yes_no("Использовать спецсимволы?", default=False)
                    try:
                        password = generate_password_custom(
                            length, use_upper, use_lower, use_digits, use_symbols
                        )
                        print(f"Сгенерированный пароль: {password}")
                        break
                    except ValueError as exc:
                        print(exc)
                        print("Нужно выбрать хотя бы один тип символов. Повторите.")
            else:
                password = getpass.getpass("Пароль: ")
                if not password:
                    print("Пароль не может быть пустым.")
                    continue

            add_entry(conn, fernet, name, login, password)
        elif command == "get":
            name = input("Название: ").strip()
            if not name:
                print("Название не может быть пустым.")
                continue
            get_entry(conn, fernet, name)
        elif command == "list":
            list_entries(conn)
        elif command == "delete":
            name = input("Название: ").strip()
            if not name:
                print("Название не может быть пустым.")
                continue
            confirm = input(f'Удалить "{name}"? [д/н]: ').strip().lower()
            if confirm in ("д", "y", "yes", "да"):
                delete_entry(conn, name)
            else:
                print("Отменено.")
        elif command == "new":
            length = prompt_length()
            print(generate_password(length))


def main():
    fernet = load_or_create_key()
    conn = get_connection()
    init_db(conn)
    verify_master(conn)
    interactive_loop(conn, fernet)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)

