package repository

import "database/sql"

const ensureUsersSQL = `
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tags TEXT NOT NULL
);
`

// EnsureUsersTable создаёт таблицу users при первом запуске (удобно для Docker).
func EnsureUsersTable(db *sql.DB) error {
	_, err := db.Exec(ensureUsersSQL)
	return err
}
