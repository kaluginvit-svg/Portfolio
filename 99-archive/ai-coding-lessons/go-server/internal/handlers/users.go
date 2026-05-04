package handlers

import (
	"encoding/json"
	"log"
	"net/http"

	"userserver/internal/httputil"
	"userserver/internal/jsonutil"
	"userserver/internal/models"
	"userserver/internal/service"
)

func newCreateUserHandler(svc *service.UserService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if !httputil.MethodAllowed(w, r, http.MethodPost) {
			return
		}

		var raw models.CreateUserBody
		if err := json.NewDecoder(r.Body).Decode(&raw); err != nil {
			_ = httputil.WriteJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "ожидается JSON-объект"})
			return
		}

		name, ok := jsonutil.StringField(raw.Name, true)
		if !ok {
			_ = httputil.WriteJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "поле name (строка) обязательно"})
			return
		}

		tags, err := jsonutil.ParseTags(raw.Tags)
		if err != nil {
			_ = httputil.WriteJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "поле tags должно быть массивом или отсутствовать"})
			return
		}

		passStr, err := jsonutil.StringFieldOptional(raw.Password)
		if err != nil {
			_ = httputil.WriteJSON(w, http.StatusBadRequest, models.ErrorResponse{Error: "поле password должно быть строкой или отсутствовать"})
			return
		}

		id, err := svc.CreateUser(name, tags, passStr)
		if err != nil {
			log.Printf("create user: %v", err)
			_ = httputil.WriteJSON(w, http.StatusInternalServerError, models.ErrorResponse{Error: "не удалось сохранить пользователя"})
			return
		}

		_ = httputil.WriteJSON(w, http.StatusCreated, models.IDResponse{ID: id})
	}
}
