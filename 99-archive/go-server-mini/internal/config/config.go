// Package config — пути, параметры PBKDF2 и адрес HTTP из окружения (как settings.py + listen).
package config

import "os"

// Config совпадает по смыслу с корневым settings.py.
type Config struct {
	DBPath        string
	PasswordsFile string
	SaltBytes     int
	PBKDF2Iter    int
}

// Default возвращает значения по умолчанию (переменные окружения как в Python: DB_PATH, PASSWORDS_FILE).
func Default() *Config {
	db := os.Getenv("DB_PATH")
	if db == "" {
		db = "users.db"
	}
	pw := os.Getenv("PASSWORDS_FILE")
	if pw == "" {
		pw = "passwords.txt"
	}
	return &Config{
		DBPath:        db,
		PasswordsFile: pw,
		SaltBytes:     16,
		PBKDF2Iter:    390_000,
	}
}

const defaultListen = ":8080"

// ListenAddr: HTTP_ADDR, иначе PORT, иначе :8080.
func ListenAddr() string {
	if a := os.Getenv("HTTP_ADDR"); a != "" {
		return a
	}
	if p := os.Getenv("PORT"); p != "" {
		if p[0] == ':' {
			return p
		}
		return ":" + p
	}
	return defaultListen
}
