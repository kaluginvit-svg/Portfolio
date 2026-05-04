// Package repository — доступ к данным (SQLite, файл паролей).
package repository

import (
	"database/sql"
)

// UserSQLite вставляет пользователей в таблицу users.
type UserSQLite struct {
	DB *sql.DB
}

// Insert сохраняет name и JSON тегов в колонку tags, возвращает lastInsertID.
func (r *UserSQLite) Insert(name, tagsJSON string) (int64, error) {
	res, err := r.DB.Exec(`INSERT INTO users (name, tags) VALUES (?, ?)`, name, tagsJSON)
	if err != nil {
		return 0, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return 0, err
	}
	return id, nil
}
