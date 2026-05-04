// Package models — DTO запросов/ответов HTTP API.
package models

import "encoding/json"

// CreateUserBody — сырое тело POST /users (поля как в Flask, валидация через jsonutil).
type CreateUserBody struct {
	Name     *json.RawMessage `json:"name"`
	Tags     json.RawMessage    `json:"tags"`
	Password *json.RawMessage   `json:"password"`
}

// ErrorResponse — 4xx/5xx с телом JSON.
type ErrorResponse struct {
	Error string `json:"error"`
}

// IDResponse — 201 после создания пользователя.
type IDResponse struct {
	ID int64 `json:"id"`
}

// HealthResponse — GET /health.
type HealthResponse struct {
	Status string `json:"status"`
}
