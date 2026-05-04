package handlers

import (
	"net/http"

	"userserver/internal/httputil"
	"userserver/internal/models"
)

func handleHealth(w http.ResponseWriter, r *http.Request) {
	if !httputil.MethodAllowed(w, r, http.MethodGet) {
		return
	}
	_ = httputil.WriteJSON(w, http.StatusOK, models.HealthResponse{Status: "ok"})
}
