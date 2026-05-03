package repository

import (
	"os"
	"path/filepath"

	"userserver/internal/passwordhash"
)

// PasswordFile дописывает строки PBKDF2 в файл (как password_storage.py).
type PasswordFile struct {
	Path       string
	SaltBytes  int
	Iterations int
}

// AppendHash записывает одну строку в конец файла.
func (p *PasswordFile) AppendHash(userID int64, password string) error {
	line, err := passwordhash.FileLine(userID, password, p.SaltBytes, p.Iterations)
	if err != nil {
		return err
	}
	path := filepath.Clean(p.Path)
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(line)
	return err
}
