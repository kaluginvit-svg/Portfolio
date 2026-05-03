"""
Графический интерфейс для системы бронирования на tkinter
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, date
from postgre_driver import PostgreSQLDriver
from backend import (
    create_tables,
    create_user, get_user_by_id, get_user_by_email, get_all_users, update_user, delete_user,
    create_table, get_table_by_id, get_table_by_number, get_all_tables, update_table, delete_table,
    create_booking, get_booking_by_id, get_bookings_by_user, get_bookings_by_table, 
    get_all_bookings, update_booking, delete_booking
)


class BookingSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Система бронирования ресторана")
        self.root.geometry("1200x700")
        
        # Подключение к БД
        self.db = PostgreSQLDriver()
        self.all_users = []
        self.all_tables = []
        try:
            self.db.connect()
            create_tables(self.db)
            self.status_text = "Подключено к БД"
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к БД:\n{e}")
            self.status_text = f"Ошибка подключения: {e}"
            self.db = None
        
        # Статусная строка (создаем раньше, чтобы была доступна при инициализации)
        self.status_bar = tk.Label(root, text=self.status_text, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Создание вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладки
        self.users_tab = ttk.Frame(self.notebook)
        self.tables_tab = ttk.Frame(self.notebook)
        self.bookings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.users_tab, text="Пользователи")
        self.notebook.add(self.tables_tab, text="Столы")
        self.notebook.add(self.bookings_tab, text="Бронирования")
        
        # Инициализация вкладок
        self.init_users_tab()
        self.init_tables_tab()
        self.init_bookings_tab()
        
        # Обработчик переключения вкладок для обновления статусной строки
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Инициализация статусной строки для текущей вкладки
        # Используем after для обновления после полной инициализации
        self.root.after(100, self.update_status_for_current_tab)
    
    def on_closing(self):
        """Закрытие подключения при выходе"""
        if self.db:
            self.db.disconnect()
        self.root.destroy()
    
    def on_tab_changed(self, event):
        """Обработчик переключения вкладок"""
        self.update_status_for_current_tab()
    
    def update_status_for_current_tab(self):
        """Обновление статусной строки для текущей вкладки"""
        if not self.db:
            self.status_bar.config(text=self.status_text)
            return
        
        try:
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 0:  # Пользователи
                users = get_all_users(self.db)
                self.update_status_bar(f"Пользователей: {len(users)}")
            elif current_tab == 1:  # Столы
                tables = get_all_tables(self.db)
                self.update_status_bar(f"Столов: {len(tables)}")
            elif current_tab == 2:  # Бронирования
                bookings = get_all_bookings(self.db)
                self.update_status_bar(f"Бронирований: {len(bookings)}")
        except Exception as e:
            self.status_bar.config(text=f"{self.status_text} | Ошибка: {e}")
    
    # ==================== Вкладка Пользователи ====================
    
    def init_users_tab(self):
        # Левая панель - форма
        left_frame = ttk.Frame(self.users_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Управление пользователями", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Форма
        form_frame = ttk.LabelFrame(left_frame, text="Данные пользователя", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        self.user_id_var = tk.StringVar()
        self.user_name_var = tk.StringVar()
        self.user_email_var = tk.StringVar()
        self.user_phone_var = tk.StringVar()
        self.user_role_var = tk.StringVar(value="client")
        self.user_active_var = tk.BooleanVar(value=True)
        
        ttk.Label(form_frame, text="ID (для редактирования):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.user_id_var, width=30).grid(row=0, column=1, pady=2)
        
        ttk.Label(form_frame, text="Имя *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.user_name_var, width=30).grid(row=1, column=1, pady=2)
        
        ttk.Label(form_frame, text="Email *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.user_email_var, width=30).grid(row=2, column=1, pady=2)
        
        ttk.Label(form_frame, text="Телефон:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.user_phone_var, width=30).grid(row=3, column=1, pady=2)
        
        ttk.Label(form_frame, text="Роль:").grid(row=4, column=0, sticky=tk.W, pady=2)
        role_combo = ttk.Combobox(form_frame, textvariable=self.user_role_var, values=["client", "admin"], width=27, state="readonly")
        role_combo.grid(row=4, column=1, pady=2)
        
        ttk.Label(form_frame, text="Активен:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(form_frame, variable=self.user_active_var).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # Кнопки
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Создать", command=self.create_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.update_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_user_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_user_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_users_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список
        right_frame = ttk.Frame(self.users_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Заголовок с поиском
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X, pady=5)
        ttk.Label(header_frame, text="Список пользователей", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Поиск
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=2)
        if not hasattr(self, 'user_search_var'):
            self.user_search_var = tk.StringVar()
        self.user_search_var.trace('w', self.filter_users)
        ttk.Entry(search_frame, textvariable=self.user_search_var, width=20).pack(side=tk.LEFT, padx=2)
        
        # Таблица
        columns = ("ID", "Имя", "Email", "Телефон", "Роль", "Активен")
        self.users_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=120)
        
        scrollbar_users = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar_users.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_users.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_tree.bind("<Double-1>", self.on_user_select)
        
        self.refresh_users_list()
    
    def create_user_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            data = {
                'name': self.user_name_var.get(),
                'email': self.user_email_var.get(),
                'phone': self.user_phone_var.get() or None,
                'role': self.user_role_var.get(),
                'is_active': self.user_active_var.get()
            }
            
            if not data['name'] or not data['email']:
                messagebox.showerror("Ошибка", "Имя и Email обязательны")
                return
            
            user_id = create_user(self.db, data)
            messagebox.showinfo("Успех", f"Пользователь создан с ID: {user_id}")
            self.clear_user_form()
            self.refresh_users_list()
            self.update_user_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать пользователя:\n{e}")
    
    def update_user_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            user_id = self.user_id_var.get()
            if not user_id:
                messagebox.showerror("Ошибка", "Введите ID пользователя для обновления")
                return
            
            data = {}
            if self.user_name_var.get():
                data['name'] = self.user_name_var.get()
            if self.user_email_var.get():
                data['email'] = self.user_email_var.get()
            if self.user_phone_var.get():
                data['phone'] = self.user_phone_var.get()
            if self.user_role_var.get():
                data['role'] = self.user_role_var.get()
            data['is_active'] = self.user_active_var.get()
            
            update_user(self.db, int(user_id), data)
            messagebox.showinfo("Успех", "Пользователь обновлен")
            self.clear_user_form()
            self.refresh_users_list()
            self.update_user_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить пользователя:\n{e}")
    
    def delete_user_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            user_id = self.user_id_var.get()
            if not user_id:
                messagebox.showerror("Ошибка", "Введите ID пользователя для удаления")
                return
            
            if messagebox.askyesno("Подтверждение", f"Удалить пользователя с ID {user_id}?"):
                delete_user(self.db, int(user_id))
                messagebox.showinfo("Успех", "Пользователь удален")
                self.clear_user_form()
                self.refresh_users_list()
                self.update_user_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить пользователя:\n{e}")
    
    def clear_user_form(self):
        """Очистка формы пользователя и удаление из БД, если есть ID"""
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        user_id = self.user_id_var.get()
        if user_id and user_id.strip():
            try:
                if messagebox.askyesno("Подтверждение", f"Удалить пользователя с ID {user_id} из БД?"):
                    delete_user(self.db, int(user_id))
                    messagebox.showinfo("Успех", "Пользователь удален из БД")
                    self.refresh_users_list()
                    self.update_user_combo()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить пользователя:\n{e}")
        
        # Очистка формы
        self.user_id_var.set("")
        self.user_name_var.set("")
        self.user_email_var.set("")
        self.user_phone_var.set("")
        self.user_role_var.set("client")
        self.user_active_var.set(True)
    
    def on_user_select(self, event):
        selection = self.users_tree.selection()
        if selection:
            item = self.users_tree.item(selection[0])
            values = item['values']
            if values:
                self.user_id_var.set(values[0])
                self.user_name_var.set(values[1])
                self.user_email_var.set(values[2])
                self.user_phone_var.set(values[3] if values[3] else "")
                self.user_role_var.set(values[4])
                self.user_active_var.set(values[5])
    
    def refresh_users_list(self):
        if not self.db:
            return
        
        # Очистка
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        try:
            users = get_all_users(self.db)
            self.all_users = users  # Сохраняем для фильтрации
            for user in users:
                self.users_tree.insert("", tk.END, values=(
                    user.get('id'),
                    user.get('name'),
                    user.get('email'),
                    user.get('phone') or '',
                    user.get('role'),
                    'Да' if user.get('is_active') else 'Нет'
                ))
            self.update_user_combo()
            self.update_status_bar(f"Пользователей: {len(users)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить пользователей:\n{e}")
    
    def filter_users(self, *args):
        """Фильтрация пользователей по поисковому запросу"""
        if not self.db:
            return
        
        search_text = self.user_search_var.get().lower()
        
        # Очистка
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        try:
            users = getattr(self, 'all_users', get_all_users(self.db))
            filtered_count = 0
            for user in users:
                # Поиск по имени, email, телефону
                if (search_text in str(user.get('name', '')).lower() or
                    search_text in str(user.get('email', '')).lower() or
                    search_text in str(user.get('phone', '')).lower() or
                    search_text in str(user.get('id', ''))):
                    self.users_tree.insert("", tk.END, values=(
                        user.get('id'),
                        user.get('name'),
                        user.get('email'),
                        user.get('phone') or '',
                        user.get('role'),
                        'Да' if user.get('is_active') else 'Нет'
                    ))
                    filtered_count += 1
            self.update_status_bar(f"Найдено пользователей: {filtered_count}")
        except Exception as e:
            pass
    
    def update_user_combo(self):
        """Обновление списка пользователей в комбобоксе"""
        if not self.db or not hasattr(self, 'booking_user_combo') or self.booking_user_combo is None:
            return
        try:
            users = get_all_users(self.db)
            user_options = [f"{u.get('id')} - {u.get('name')} ({u.get('email')})" for u in users]
            self.booking_user_combo['values'] = user_options
        except:
            pass
    
    # ==================== Вкладка Столы ====================
    
    def init_tables_tab(self):
        # Левая панель - форма
        left_frame = ttk.Frame(self.tables_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Управление столами", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Форма
        form_frame = ttk.LabelFrame(left_frame, text="Данные стола", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        self.table_id_var = tk.StringVar()
        self.table_number_var = tk.StringVar()
        self.table_capacity_var = tk.StringVar(value="2")
        self.table_description_var = tk.StringVar()
        self.table_location_var = tk.StringVar()
        self.table_available_var = tk.BooleanVar(value=True)
        
        ttk.Label(form_frame, text="ID (для редактирования):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.table_id_var, width=30).grid(row=0, column=1, pady=2)
        
        ttk.Label(form_frame, text="Номер стола *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.table_number_var, width=30).grid(row=1, column=1, pady=2)
        
        ttk.Label(form_frame, text="Вместимость *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.table_capacity_var, width=30).grid(row=2, column=1, pady=2)
        
        ttk.Label(form_frame, text="Описание:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.table_description_var, width=30).grid(row=3, column=1, pady=2)
        
        ttk.Label(form_frame, text="Расположение:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.table_location_var, width=30).grid(row=4, column=1, pady=2)
        
        ttk.Label(form_frame, text="Доступен:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Checkbutton(form_frame, variable=self.table_available_var).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # Кнопки
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Создать", command=self.create_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.update_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_table_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_table_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_tables_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список
        right_frame = ttk.Frame(self.tables_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Заголовок с поиском
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X, pady=5)
        ttk.Label(header_frame, text="Список столов", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Поиск
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=2)
        if not hasattr(self, 'table_search_var'):
            self.table_search_var = tk.StringVar()
        self.table_search_var.trace('w', self.filter_tables)
        ttk.Entry(search_frame, textvariable=self.table_search_var, width=20).pack(side=tk.LEFT, padx=2)
        
        # Таблица
        columns = ("ID", "Номер", "Вместимость", "Описание", "Расположение", "Доступен")
        self.tables_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.tables_tree.heading(col, text=col)
            self.tables_tree.column(col, width=120)
        
        scrollbar_tables = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
        self.tables_tree.configure(yscrollcommand=scrollbar_tables.set)
        
        self.tables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tables.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tables_tree.bind("<Double-1>", self.on_table_select)
        
        self.refresh_tables_list()
    
    def create_table_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            data = {
                'table_number': self.table_number_var.get(),
                'capacity': int(self.table_capacity_var.get()) if self.table_capacity_var.get() else 2,
                'description': self.table_description_var.get() or None,
                'location': self.table_location_var.get() or None,
                'is_available': self.table_available_var.get()
            }
            
            if not data['table_number']:
                messagebox.showerror("Ошибка", "Номер стола обязателен")
                return
            
            table_id = create_table(self.db, data)
            messagebox.showinfo("Успех", f"Стол создан с ID: {table_id}")
            self.clear_table_form()
            self.refresh_tables_list()
            self.update_table_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать стол:\n{e}")
    
    def update_table_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            table_id = self.table_id_var.get()
            if not table_id:
                messagebox.showerror("Ошибка", "Введите ID стола для обновления")
                return
            
            data = {}
            if self.table_number_var.get():
                data['table_number'] = self.table_number_var.get()
            if self.table_capacity_var.get():
                data['capacity'] = int(self.table_capacity_var.get())
            if self.table_description_var.get():
                data['description'] = self.table_description_var.get()
            if self.table_location_var.get():
                data['location'] = self.table_location_var.get()
            data['is_available'] = self.table_available_var.get()
            
            update_table(self.db, int(table_id), data)
            messagebox.showinfo("Успех", "Стол обновлен")
            self.clear_table_form()
            self.refresh_tables_list()
            self.update_table_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить стол:\n{e}")
    
    def delete_table_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            table_id = self.table_id_var.get()
            if not table_id:
                messagebox.showerror("Ошибка", "Введите ID стола для удаления")
                return
            
            if messagebox.askyesno("Подтверждение", f"Удалить стол с ID {table_id}?"):
                delete_table(self.db, int(table_id))
                messagebox.showinfo("Успех", "Стол удален")
                self.clear_table_form()
                self.refresh_tables_list()
                self.update_table_combo()  # Обновляем комбобокс в бронированиях
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить стол:\n{e}")
    
    def clear_table_form(self):
        """Очистка формы стола и удаление из БД, если есть ID"""
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        table_id = self.table_id_var.get()
        if table_id and table_id.strip():
            try:
                if messagebox.askyesno("Подтверждение", f"Удалить стол с ID {table_id} из БД?"):
                    delete_table(self.db, int(table_id))
                    messagebox.showinfo("Успех", "Стол удален из БД")
                    self.refresh_tables_list()
                    self.update_table_combo()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить стол:\n{e}")
        
        # Очистка формы
        self.table_id_var.set("")
        self.table_number_var.set("")
        self.table_capacity_var.set("2")
        self.table_description_var.set("")
        self.table_location_var.set("")
        self.table_available_var.set(True)
    
    def on_table_select(self, event):
        selection = self.tables_tree.selection()
        if selection:
            item = self.tables_tree.item(selection[0])
            values = item['values']
            if values:
                self.table_id_var.set(values[0])
                self.table_number_var.set(values[1])
                self.table_capacity_var.set(str(values[2]))
                self.table_description_var.set(values[3] if values[3] else "")
                self.table_location_var.set(values[4] if values[4] else "")
                self.table_available_var.set(values[5] == 'Да')
    
    def refresh_tables_list(self):
        if not self.db:
            return
        
        # Очистка
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        try:
            tables = get_all_tables(self.db)
            self.all_tables = tables  # Сохраняем для фильтрации
            for table in tables:
                self.tables_tree.insert("", tk.END, values=(
                    table.get('id'),
                    table.get('table_number'),
                    table.get('capacity'),
                    table.get('description') or '',
                    table.get('location') or '',
                    'Да' if table.get('is_available') else 'Нет'
                ))
            self.update_table_combo()
            self.update_status_bar(f"Столов: {len(tables)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить столы:\n{e}")
    
    def filter_tables(self, *args):
        """Фильтрация столов по поисковому запросу"""
        if not self.db:
            return
        
        search_text = self.table_search_var.get().lower()
        
        # Очистка
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        try:
            tables = getattr(self, 'all_tables', get_all_tables(self.db))
            filtered_count = 0
            for table in tables:
                # Поиск по номеру, описанию, расположению
                if (search_text in str(table.get('table_number', '')).lower() or
                    search_text in str(table.get('description', '')).lower() or
                    search_text in str(table.get('location', '')).lower() or
                    search_text in str(table.get('id', ''))):
                    self.tables_tree.insert("", tk.END, values=(
                        table.get('id'),
                        table.get('table_number'),
                        table.get('capacity'),
                        table.get('description') or '',
                        table.get('location') or '',
                        'Да' if table.get('is_available') else 'Нет'
                    ))
                    filtered_count += 1
            self.update_status_bar(f"Найдено столов: {filtered_count}")
        except Exception as e:
            pass
    
    def update_table_combo(self):
        """Обновление списка столов в комбобоксе"""
        if not self.db or not hasattr(self, 'booking_table_combo') or self.booking_table_combo is None:
            return
        try:
            tables = get_all_tables(self.db, available_only=True)
            table_options = [f"{t.get('id')} - Стол {t.get('table_number')} (вместимость: {t.get('capacity')})" for t in tables]
            self.booking_table_combo['values'] = table_options
        except:
            pass
    
    def select_user_for_booking(self):
        """Открыть диалог выбора пользователя"""
        if not self.db:
            return
        
        # Создаем окно выбора
        select_window = tk.Toplevel(self.root)
        select_window.title("Выбор пользователя")
        select_window.geometry("600x400")
        
        ttk.Label(select_window, text="Выберите пользователя:", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Таблица пользователей
        columns = ("ID", "Имя", "Email", "Телефон")
        user_tree = ttk.Treeview(select_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            user_tree.heading(col, text=col)
            user_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(select_window, orient=tk.VERTICAL, command=user_tree.yview)
        user_tree.configure(yscrollcommand=scrollbar.set)
        
        user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Загрузка данных
        try:
            users = get_all_users(self.db)
            for user in users:
                user_tree.insert("", tk.END, values=(
                    user.get('id'),
                    user.get('name'),
                    user.get('email'),
                    user.get('phone') or ''
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить пользователей:\n{e}")
            select_window.destroy()
            return
        
        def on_select():
            selection = user_tree.selection()
            if selection:
                item = user_tree.item(selection[0])
                user_id = item['values'][0]
                self.booking_user_id_var.set(str(user_id))
                select_window.destroy()
        
        ttk.Button(select_window, text="Выбрать", command=on_select).pack(pady=5)
        user_tree.bind("<Double-1>", lambda e: on_select())
    
    def select_table_for_booking(self):
        """Открыть диалог выбора стола"""
        if not self.db:
            return
        
        # Создаем окно выбора
        select_window = tk.Toplevel(self.root)
        select_window.title("Выбор стола")
        select_window.geometry("700x400")
        
        ttk.Label(select_window, text="Выберите стол:", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Таблица столов
        columns = ("ID", "Номер", "Вместимость", "Описание", "Расположение", "Доступен")
        table_tree = ttk.Treeview(select_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            table_tree.heading(col, text=col)
            table_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(select_window, orient=tk.VERTICAL, command=table_tree.yview)
        table_tree.configure(yscrollcommand=scrollbar.set)
        
        table_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Загрузка данных
        try:
            tables = get_all_tables(self.db)
            for table in tables:
                table_tree.insert("", tk.END, values=(
                    table.get('id'),
                    table.get('table_number'),
                    table.get('capacity'),
                    table.get('description') or '',
                    table.get('location') or '',
                    'Да' if table.get('is_available') else 'Нет'
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить столы:\n{e}")
            select_window.destroy()
            return
        
        def on_select():
            selection = table_tree.selection()
            if selection:
                item = table_tree.item(selection[0])
                table_id = item['values'][0]
                self.booking_table_id_var.set(str(table_id))
                select_window.destroy()
        
        ttk.Button(select_window, text="Выбрать", command=on_select).pack(pady=5)
        table_tree.bind("<Double-1>", lambda e: on_select())
    
    def update_status_bar(self, text):
        """Обновление статусной строки"""
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.config(text=f"{self.status_text} | {text}")
    
    # ==================== Вкладка Бронирования ====================
    
    def init_bookings_tab(self):
        # Левая панель - форма
        left_frame = ttk.Frame(self.bookings_tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Управление бронированиями", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Форма
        form_frame = ttk.LabelFrame(left_frame, text="Данные бронирования", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        self.booking_id_var = tk.StringVar()
        self.booking_user_id_var = tk.StringVar()
        self.booking_table_id_var = tk.StringVar()
        self.booking_date_var = tk.StringVar()
        self.booking_time_var = tk.StringVar()
        self.booking_duration_var = tk.StringVar(value="120")
        self.booking_guests_var = tk.StringVar(value="2")
        self.booking_status_var = tk.StringVar(value="pending")
        self.booking_notes_var = tk.StringVar()
        
        ttk.Label(form_frame, text="ID (для редактирования):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.booking_id_var, width=30).grid(row=0, column=1, pady=2)
        
        ttk.Label(form_frame, text="Пользователь *:").grid(row=1, column=0, sticky=tk.W, pady=2)
        user_frame = ttk.Frame(form_frame)
        user_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2)
        self.booking_user_combo = ttk.Combobox(user_frame, textvariable=self.booking_user_id_var, width=25, state="readonly")
        self.booking_user_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(user_frame, text="...", width=3, command=self.select_user_for_booking).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(form_frame, text="Стол *:").grid(row=2, column=0, sticky=tk.W, pady=2)
        table_frame = ttk.Frame(form_frame)
        table_frame.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2)
        self.booking_table_combo = ttk.Combobox(table_frame, textvariable=self.booking_table_id_var, width=25, state="readonly")
        self.booking_table_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(table_frame, text="...", width=3, command=self.select_table_for_booking).pack(side=tk.LEFT, padx=2)
        
        # Обновление списков при инициализации
        self.update_user_combo()
        self.update_table_combo()
        
        ttk.Label(form_frame, text="Дата (YYYY-MM-DD) *:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.booking_date_var.set(date.today().isoformat())  # Автозаполнение сегодняшней датой
        ttk.Entry(form_frame, textvariable=self.booking_date_var, width=30).grid(row=3, column=1, pady=2)
        
        ttk.Label(form_frame, text="Время (HH:MM) *:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.booking_time_var, width=30).grid(row=4, column=1, pady=2)
        
        ttk.Label(form_frame, text="Длительность (мин):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.booking_duration_var, width=30).grid(row=5, column=1, pady=2)
        
        ttk.Label(form_frame, text="Количество гостей:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.booking_guests_var, width=30).grid(row=6, column=1, pady=2)
        
        ttk.Label(form_frame, text="Статус:").grid(row=7, column=0, sticky=tk.W, pady=2)
        status_combo = ttk.Combobox(form_frame, textvariable=self.booking_status_var, 
                                    values=["pending", "confirmed", "cancelled", "completed"], 
                                    width=27, state="readonly")
        status_combo.grid(row=7, column=1, pady=2)
        
        ttk.Label(form_frame, text="Примечания:").grid(row=8, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=self.booking_notes_var, width=30).grid(row=8, column=1, pady=2)
        
        # Кнопки
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Создать", command=self.create_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить", command=self.update_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_booking_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_booking_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_bookings_list).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - список
        right_frame = ttk.Frame(self.bookings_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Заголовок с фильтрами
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X, pady=5)
        ttk.Label(header_frame, text="Список бронирований", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Фильтры
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.RIGHT)
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT, padx=2)
        if not hasattr(self, 'booking_status_filter_var'):
            self.booking_status_filter_var = tk.StringVar(value="Все")
        status_filter_combo = ttk.Combobox(filter_frame, textvariable=self.booking_status_filter_var,
                                          values=["Все", "pending", "confirmed", "cancelled", "completed"],
                                          width=12, state="readonly")
        status_filter_combo.set("Все")
        status_filter_combo.pack(side=tk.LEFT, padx=2)
        status_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_bookings_list())
        
        # Таблица
        columns = ("ID", "Пользователь", "Стол", "Дата", "Время", "Длительность", "Гости", "Статус")
        self.bookings_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.bookings_tree.heading(col, text=col)
            if col == "Пользователь":
                self.bookings_tree.column(col, width=150)
            elif col == "Стол":
                self.bookings_tree.column(col, width=100)
            else:
                self.bookings_tree.column(col, width=100)
        
        scrollbar_bookings = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscrollcommand=scrollbar_bookings.set)
        
        self.bookings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_bookings.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.bookings_tree.bind("<Double-1>", self.on_booking_select)
        
        self.refresh_bookings_list()
    
    def create_booking_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            # Извлечение ID из комбобокса (формат: "ID - Имя")
            user_id_str = self.booking_user_id_var.get()
            if " - " in user_id_str:
                user_id_str = user_id_str.split(" - ")[0]
            
            table_id_str = self.booking_table_id_var.get()
            if " - " in table_id_str:
                table_id_str = table_id_str.split(" - ")[0]
            
            data = {
                'user_id': int(user_id_str) if user_id_str else None,
                'table_id': int(table_id_str) if table_id_str else None,
                'booking_date': self.booking_date_var.get(),
                'booking_time': self.booking_time_var.get(),
                'duration_minutes': int(self.booking_duration_var.get()) if self.booking_duration_var.get() else 120,
                'guests_count': int(self.booking_guests_var.get()) if self.booking_guests_var.get() else 2,
                'status': self.booking_status_var.get(),
                'notes': self.booking_notes_var.get() or None
            }
            
            if not data['user_id'] or not data['table_id'] or not data['booking_date'] or not data['booking_time']:
                messagebox.showerror("Ошибка", "Заполните все обязательные поля")
                return
            
            booking_id = create_booking(self.db, data)
            messagebox.showinfo("Успех", f"Бронирование создано с ID: {booking_id}")
            self.clear_booking_form()
            self.refresh_bookings_list()
            self.update_user_combo()  # Обновляем списки
            self.update_table_combo()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать бронирование:\n{e}")
    
    def update_booking_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            booking_id = self.booking_id_var.get()
            if not booking_id:
                messagebox.showerror("Ошибка", "Введите ID бронирования для обновления")
                return
            
            data = {}
            
            # Извлечение ID из комбобокса
            if self.booking_user_id_var.get():
                user_id_str = self.booking_user_id_var.get()
                if " - " in user_id_str:
                    user_id_str = user_id_str.split(" - ")[0]
                data['user_id'] = int(user_id_str)
            
            if self.booking_table_id_var.get():
                table_id_str = self.booking_table_id_var.get()
                if " - " in table_id_str:
                    table_id_str = table_id_str.split(" - ")[0]
                data['table_id'] = int(table_id_str)
            
            if self.booking_date_var.get():
                data['booking_date'] = self.booking_date_var.get()
            if self.booking_time_var.get():
                data['booking_time'] = self.booking_time_var.get()
            if self.booking_duration_var.get():
                data['duration_minutes'] = int(self.booking_duration_var.get())
            if self.booking_guests_var.get():
                data['guests_count'] = int(self.booking_guests_var.get())
            if self.booking_status_var.get():
                data['status'] = self.booking_status_var.get()
            if self.booking_notes_var.get():
                data['notes'] = self.booking_notes_var.get()
            
            update_booking(self.db, int(booking_id), data)
            messagebox.showinfo("Успех", "Бронирование обновлено")
            self.clear_booking_form()
            self.refresh_bookings_list()
            self.update_user_combo()  # Обновляем списки
            self.update_table_combo()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить бронирование:\n{e}")
    
    def delete_booking_action(self):
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        try:
            booking_id = self.booking_id_var.get()
            if not booking_id:
                messagebox.showerror("Ошибка", "Введите ID бронирования для удаления")
                return
            
            if messagebox.askyesno("Подтверждение", f"Удалить бронирование с ID {booking_id}?"):
                delete_booking(self.db, int(booking_id))
                messagebox.showinfo("Успех", "Бронирование удалено")
                self.clear_booking_form()
                self.refresh_bookings_list()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить бронирование:\n{e}")
    
    def clear_booking_form(self):
        """Очистка формы бронирования и удаление из БД, если есть ID"""
        if not self.db:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        
        booking_id = self.booking_id_var.get()
        if booking_id and booking_id.strip():
            try:
                if messagebox.askyesno("Подтверждение", f"Удалить бронирование с ID {booking_id} из БД?"):
                    delete_booking(self.db, int(booking_id))
                    messagebox.showinfo("Успех", "Бронирование удалено из БД")
                    self.refresh_bookings_list()
                    self.update_user_combo()
                    self.update_table_combo()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить бронирование:\n{e}")
        
        # Очистка формы
        self.booking_id_var.set("")
        
        # Очистка комбобоксов (нужно временно изменить state)
        if hasattr(self, 'booking_user_combo') and self.booking_user_combo:
            self.booking_user_combo.config(state="normal")
            self.booking_user_id_var.set("")
            self.booking_user_combo.config(state="readonly")
        
        if hasattr(self, 'booking_table_combo') and self.booking_table_combo:
            self.booking_table_combo.config(state="normal")
            self.booking_table_id_var.set("")
            self.booking_table_combo.config(state="readonly")
        
        # Восстанавливаем дату по умолчанию (сегодняшняя дата)
        self.booking_date_var.set(date.today().isoformat())
        self.booking_time_var.set("")
        self.booking_duration_var.set("120")
        self.booking_guests_var.set("2")
        self.booking_status_var.set("pending")
        self.booking_notes_var.set("")
    
    def on_booking_select(self, event):
        selection = self.bookings_tree.selection()
        if selection:
            item = self.bookings_tree.item(selection[0])
            values = item['values']
            if values:
                self.booking_id_var.set(values[0])
                # Получаем полные данные бронирования
                try:
                    booking = get_booking_by_id(self.db, int(values[0]))
                    if booking:
                        user_id = booking.get('user_id', '')
                        table_id = booking.get('table_id', '')
                        
                        # Устанавливаем значения в комбобоксы
                        user_options = self.booking_user_combo['values']
                        for option in user_options:
                            if option.startswith(f"{user_id} - "):
                                self.booking_user_id_var.set(option)
                                break
                        else:
                            self.booking_user_id_var.set(str(user_id))
                        
                        table_options = self.booking_table_combo['values']
                        for option in table_options:
                            if option.startswith(f"{table_id} - "):
                                self.booking_table_id_var.set(option)
                                break
                        else:
                            self.booking_table_id_var.set(str(table_id))
                        
                        self.booking_date_var.set(str(booking.get('booking_date', '')))
                        # Форматирование времени (убираем секунды если есть)
                        booking_time = str(booking.get('booking_time', ''))
                        if booking_time and len(booking_time) > 5:
                            booking_time = booking_time[:5]
                        self.booking_time_var.set(booking_time)
                        self.booking_duration_var.set(str(booking.get('duration_minutes', 120)))
                        self.booking_guests_var.set(str(booking.get('guests_count', 2)))
                        self.booking_status_var.set(booking.get('status', 'pending'))
                        self.booking_notes_var.set(booking.get('notes', ''))
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")
    
    def refresh_bookings_list(self):
        if not self.db:
            return
        
        # Очистка
        for item in self.bookings_tree.get_children():
            self.bookings_tree.delete(item)
        
        try:
            # Фильтр по статусу
            status_filter = self.booking_status_filter_var.get() if hasattr(self, 'booking_status_filter_var') else "Все"
            if status_filter and status_filter != "Все":
                bookings = get_all_bookings(self.db, status=status_filter)
            else:
                bookings = get_all_bookings(self.db)
            
            # Получаем данные пользователей и столов для отображения
            users_dict = {}
            tables_dict = {}
            try:
                users = get_all_users(self.db)
                users_dict = {u.get('id'): u.get('name') for u in users}
                
                tables = get_all_tables(self.db)
                tables_dict = {t.get('id'): t.get('table_number') for t in tables}
            except:
                pass
            
            for booking in bookings:
                # Форматирование времени (убираем секунды если есть)
                booking_time = str(booking.get('booking_time', ''))
                if booking_time and len(booking_time) > 5:
                    booking_time = booking_time[:5]
                
                user_id = booking.get('user_id')
                table_id = booking.get('table_id')
                user_name = users_dict.get(user_id, f"ID: {user_id}")
                table_number = tables_dict.get(table_id, f"ID: {table_id}")
                
                self.bookings_tree.insert("", tk.END, values=(
                    booking.get('id'),
                    user_name,
                    f"Стол {table_number}",
                    str(booking.get('booking_date', '')),
                    booking_time,
                    booking.get('duration_minutes'),
                    booking.get('guests_count'),
                    booking.get('status')
                ))
            
            self.update_status_bar(f"Бронирований: {len(bookings)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить бронирования:\n{e}")


def main():
    root = tk.Tk()
    app = BookingSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
