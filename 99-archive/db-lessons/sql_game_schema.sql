-- ============================================================
-- БАЗА ДАННЫХ ДЛЯ SQL ИГРЫ
-- ============================================================
-- Создание таблиц для игры-обучалки по SQL
-- ============================================================

PRAGMA foreign_keys = ON;

-- Таблица заданий
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 5),  -- Уровень сложности (1-5)
    title TEXT NOT NULL,                                   -- Название задания
    description TEXT NOT NULL,                             -- Описание задания
    hint TEXT,                                             -- Подсказка
    sql_example TEXT,                                      -- Пример правильного запроса
    expected_columns TEXT,                                 -- Ожидаемые столбцы (через запятую)
    expected_row_count INTEGER,                            -- Ожидаемое количество строк (если важно)
    points INTEGER NOT NULL DEFAULT 10,                    -- Очки за выполнение
    category TEXT NOT NULL                                 -- Категория (SELECT, WHERE, JOIN, etc.)
);

-- Таблица результатов игроков
CREATE TABLE IF NOT EXISTS player_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    task_id INTEGER NOT NULL,
    sql_query TEXT NOT NULL,                               -- Запрос игрока
    is_correct BOOLEAN NOT NULL,                           -- Правильность запроса
    points_earned INTEGER NOT NULL DEFAULT 0,              -- Заработанные очки
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_tasks_level ON tasks(level);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category);
CREATE INDEX IF NOT EXISTS idx_player_results_player ON player_results(player_name);
