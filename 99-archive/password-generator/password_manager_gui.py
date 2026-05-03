import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from password_manager import (
    decrypt_password,
    encrypt_password,
    generate_password_custom,
    get_connection,
    get_setting,
    hash_password,
    init_db,
    load_or_create_key,
    set_setting,
)


class MasterPasswordDialog:
    def __init__(self, root, conn):
        self.root = root
        self.conn = conn

    def ensure(self) -> bool:
        stored = get_setting(self.conn, "master_hash")
        if stored is None:
            return self._set_master()
        return self._verify_master(stored)

    def _set_master(self) -> bool:
        while True:
            pw1 = simpledialog.askstring(
                "Мастер-пароль", "Придумайте мастер-пароль:", show="*", parent=self.root
            )
            if pw1 is None:
                return False
            pw2 = simpledialog.askstring(
                "Мастер-пароль", "Повторите мастер-пароль:", show="*", parent=self.root
            )
            if pw2 is None:
                return False
            if not pw1:
                messagebox.showerror("Ошибка", "Пароль не может быть пустым.")
                continue
            if pw1 != pw2:
                messagebox.showerror("Ошибка", "Пароли не совпадают.")
                continue
            set_setting(self.conn, "master_hash", hash_password(pw1))
            messagebox.showinfo("Готово", "Мастер-пароль установлен.")
            return True

    def _verify_master(self, stored_hash: str) -> bool:
        for _ in range(3):
            pw = simpledialog.askstring(
                "Мастер-пароль", "Введите мастер-пароль:", show="*", parent=self.root
            )
            if pw is None:
                return False
            if hash_password(pw) == stored_hash:
                return True
            messagebox.showerror("Ошибка", "Неверный пароль.")
        messagebox.showerror("Доступ", "Доступ запрещён.")
        return False


class PasswordGeneratorDialog(simpledialog.Dialog):
    def body(self, master):
        self.title("Генератор пароля")
        tk.Label(master, text="Длина (мин. 8):").grid(row=0, column=0, sticky="w")
        self.length_var = tk.StringVar(value="16")
        tk.Entry(master, textvariable=self.length_var, width=8).grid(row=0, column=1, sticky="w")

        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=False)

        tk.Checkbutton(master, text="Заглавные", variable=self.upper_var).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(master, text="Строчные", variable=self.lower_var).grid(row=1, column=1, sticky="w")
        tk.Checkbutton(master, text="Цифры", variable=self.digits_var).grid(row=2, column=0, sticky="w")
        tk.Checkbutton(master, text="Спецсимволы", variable=self.symbols_var).grid(row=2, column=1, sticky="w")
        return None

    def validate(self):
        try:
            length = int(self.length_var.get() or "16")
            self.length = max(8, length)
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Длина должна быть числом.")
            return False

    def apply(self):
        self.result = generate_password_custom(
            self.length,
            self.upper_var.get(),
            self.lower_var.get(),
            self.digits_var.get(),
            self.symbols_var.get(),
        )


class AddEntryDialog(simpledialog.Dialog):
    def __init__(self, master, fernet, conn):
        self.fernet = fernet
        self.conn = conn
        self.result = None
        super().__init__(master, title="Добавить пароль")

    def body(self, master):
        tk.Label(master, text="Название:").grid(row=0, column=0, sticky="w")
        tk.Label(master, text="Логин:").grid(row=1, column=0, sticky="w")
        tk.Label(master, text="Пароль:").grid(row=2, column=0, sticky="w")

        self.name_var = tk.StringVar()
        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Entry(master, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky="w")
        tk.Entry(master, textvariable=self.login_var, width=30).grid(row=1, column=1, sticky="w")
        tk.Entry(master, textvariable=self.password_var, width=30, show="*").grid(row=2, column=1, sticky="w")

        tk.Button(master, text="Сгенерировать", command=self._generate).grid(row=2, column=2, padx=6)
        return None

    def _generate(self):
        dlg = PasswordGeneratorDialog(self)
        if dlg.result:
            self.password_var.set(dlg.result)

    def validate(self):
        name = self.name_var.get().strip()
        login = self.login_var.get().strip()
        password = self.password_var.get()
        if not name or not login or not password:
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены.")
            return False
        self.result = (name, login, password)
        return True


class PasswordManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Менеджер паролей")
        self.geometry("520x420")

        self.conn = get_connection()
        init_db(self.conn)
        self.fernet = load_or_create_key()

        if not MasterPasswordDialog(self, self.conn).ensure():
            self.destroy()
            return

        self._build_ui()
        self.refresh_entries()

    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame, columns=("login",), show="headings", selectmode="browse")
        self.tree.heading("login", text="Логин")
        self.tree["displaycolumns"] = ("login",)
        self.tree.column("login", width=220)
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Добавить", command=self.add_entry).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Показать", command=self.show_entry).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_entry).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_entries).pack(side="left", padx=4)

    def refresh_entries(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        cur = self.conn.execute("SELECT name, login FROM credentials ORDER BY name")
        for name, login in cur.fetchall():
            self.tree.insert("", "end", iid=name, values=(login,))

    def add_entry(self):
        dlg = AddEntryDialog(self, self.fernet, self.conn)
        if dlg.result:
            name, login, password = dlg.result
            encrypted = encrypt_password(self.fernet, password)
            try:
                self.conn.execute(
                    "INSERT INTO credentials(name, login, password) VALUES(?, ?, ?)",
                    (name, login, encrypted),
                )
                self.conn.commit()
                self.refresh_entries()
                messagebox.showinfo("Готово", "Пароль сохранён.")
            except Exception as exc:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {exc}")

    def _selected_name(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def show_entry(self):
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Инфо", "Выберите запись.")
            return
        cur = self.conn.execute("SELECT login, password FROM credentials WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            messagebox.showerror("Ошибка", "Запись не найдена.")
            return
        login, password_enc = row
        try:
            password = decrypt_password(self.fernet, password_enc)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось расшифровать: {exc}")
            return
        msg = f"Название: {name}\nЛогин: {login}\nПароль: {password}"
        self.clipboard_clear()
        self.clipboard_append(password)
        messagebox.showinfo("Данные", msg)

    def delete_entry(self):
        name = self._selected_name()
        if not name:
            messagebox.showinfo("Инфо", "Выберите запись.")
            return
        if not messagebox.askyesno("Подтверждение", f'Удалить "{name}"?'):
            return
        cur = self.conn.execute("DELETE FROM credentials WHERE name = ?", (name,))
        self.conn.commit()
        if cur.rowcount:
            self.refresh_entries()
            messagebox.showinfo("Готово", "Удалено.")
        else:
            messagebox.showerror("Ошибка", "Запись не найдена.")


if __name__ == "__main__":
    app = PasswordManagerApp()
    app.mainloop()

