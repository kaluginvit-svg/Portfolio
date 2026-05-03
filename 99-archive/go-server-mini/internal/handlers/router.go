package handlers

import (
	"net/http"

	"userserver/internal/service"
)

// NewRouter регистрирует маршруты приложения.
func NewRouter(svc *service.UserService) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", handleHealth)
	mux.HandleFunc("/users", newCreateUserHandler(svc))
	return mux
}
