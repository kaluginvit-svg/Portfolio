// Package service — сценарии использования (создание пользователя + опционально пароль).
package service

import (
	"encoding/json"
	"fmt"

	"userserver/internal/repository"
)

// UserService оркестрирует репозитории без знания HTTP.
type UserService struct {
	Users    *repository.UserSQLite
	Password *repository.PasswordFile
}

// CreateUser добавляет тег "new", пишет в БД и при непустом password — в файл хешей.
func (s *UserService) CreateUser(name string, tags []string, password string) (int64, error) {
	rowTags := append(append([]string(nil), tags...), "new")
	payload, err := json.Marshal(rowTags)
	if err != nil {
		return 0, fmt.Errorf("marshal tags: %w", err)
	}

	id, err := s.Users.Insert(name, string(payload))
	if err != nil {
		return 0, err
	}

	if password != "" {
		if err := s.Password.AppendHash(id, password); err != nil {
			return 0, err
		}
	}
	return id, nil
}
