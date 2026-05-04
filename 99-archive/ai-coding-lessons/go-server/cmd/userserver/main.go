package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"userserver/internal/config"
	"userserver/internal/handlers"
	"userserver/internal/repository"
	"userserver/internal/service"
)

func main() {
	cfg := config.Default()

	ensureParentDir(cfg.DBPath)
	ensureParentDir(cfg.PasswordsFile)

	db, err := sql.Open("sqlite", cfg.DBPath)
	if err != nil {
		log.Fatalf("sqlite open: %v", err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)

	if err := repository.EnsureUsersTable(db); err != nil {
		log.Fatalf("schema: %v", err)
	}

	svc := &service.UserService{
		Users: &repository.UserSQLite{DB: db},
		Password: &repository.PasswordFile{
			Path:       cfg.PasswordsFile,
			SaltBytes:  cfg.SaltBytes,
			Iterations: cfg.PBKDF2Iter,
		},
	}

	addr := config.ListenAddr()
	log.Printf("слушаю %s (cwd=%s)", addr, mustGetwd())

	if err := http.ListenAndServe(addr, handlers.NewRouter(svc)); err != nil {
		log.Fatal(err)
	}
}

func mustGetwd() string {
	wd, err := os.Getwd()
	if err != nil {
		return "."
	}
	return wd
}

func ensureParentDir(path string) {
	if path == "" {
		return
	}
	d := filepath.Dir(path)
	if d == "." || d == "" {
		return
	}
	if err := os.MkdirAll(d, 0755); err != nil {
		log.Fatalf("mkdir %s: %v", d, err)
	}
}
