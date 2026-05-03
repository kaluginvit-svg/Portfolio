-- ============================================================
-- SCHEMA.SQL - СТРУКТУРА БАЗЫ ДАННЫХ СПОРТИВНОГО КЛУБА
-- ============================================================
-- Этот файл создает все таблицы, ограничения и индексы
-- Запустите: sqlite3 sports_club.db < schema.sql
-- ============================================================

-- Включаем поддержку внешних ключей
PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. ТАБЛИЦА ТРЕНЕРОВ
-- ============================================================
CREATE TABLE IF NOT EXISTS trainers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    specialization TEXT NOT NULL,
    experience_years INTEGER NOT NULL CHECK(experience_years >= 0),
    hire_date DATE NOT NULL
);

-- ============================================================
-- 2. ТАБЛИЦА УЧАСТНИКОВ
-- ============================================================
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    birth_date DATE NOT NULL,
    age INTEGER NOT NULL CHECK(age >= 14),
    gender TEXT NOT NULL CHECK(gender IN ('М', 'Ж')),
    registration_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'Активный' CHECK(status IN ('Активный', 'Приостановлен', 'Неактивный'))
);

-- ============================================================
-- 3. ТАБЛИЦА ЗАНЯТИЙ
-- ============================================================
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trainer_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье')),
    start_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    max_participants INTEGER NOT NULL CHECK(max_participants > 0),
    room TEXT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE RESTRICT
);

-- ============================================================
-- 4. ТАБЛИЦА ПОСЕЩЕНИЙ
-- ============================================================
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'Посещено' CHECK(status IN ('Посещено', 'Пропущено', 'Отменено')),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- ============================================================
-- 5. ТАБЛИЦА ОПЛАТ
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date DATE NOT NULL,
    payment_method TEXT NOT NULL CHECK(payment_method IN ('Наличные', 'Карта', 'Банковский перевод', 'Онлайн')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'Оплачено' CHECK(status IN ('Оплачено', 'Ожидает оплаты', 'Возврат')),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- ============================================================
-- ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ПОИСКА
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_trainer_id ON classes(trainer_id);
CREATE INDEX IF NOT EXISTS idx_member_id_visits ON visits(member_id);
CREATE INDEX IF NOT EXISTS idx_class_id_visits ON visits(class_id);
CREATE INDEX IF NOT EXISTS idx_member_id_payments ON payments(member_id);
CREATE INDEX IF NOT EXISTS idx_visit_date ON visits(visit_date);

-- ============================================================
-- КОНЕЦ SCHEMA.SQL
-- ============================================================
