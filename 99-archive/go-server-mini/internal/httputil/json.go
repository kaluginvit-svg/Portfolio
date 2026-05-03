// Package httputil — мелкие помощники для JSON-ответов и методов.
package httputil

import (
	"encoding/json"
	"net/http"
)

const contentJSON = "application/json; charset=utf-8"

// WriteJSON выставляет Content-Type и код ответа.
func WriteJSON(w http.ResponseWriter, status int, v any) error {
	w.Header().Set("Content-Type", contentJSON)
	w.WriteHeader(status)
	return json.NewEncoder(w).Encode(v)
}

// MethodAllowed возвращает false и шлёт 405, если метод не совпадает.
func MethodAllowed(w http.ResponseWriter, r *http.Request, want string) bool {
	if r.Method != want {
		http.Error(w, http.StatusText(http.StatusMethodNotAllowed), http.StatusMethodNotAllowed)
		return false
	}
	return true
}
