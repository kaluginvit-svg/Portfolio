// Package jsonutil — разбор json.RawMessage для валидации полей форм.
package jsonutil

import "encoding/json"

// StringField — обязательная непустая строка.
func StringField(raw *json.RawMessage, required bool) (string, bool) {
	if raw == nil || len(*raw) == 0 {
		if required {
			return "", false
		}
		return "", true
	}
	var s string
	if err := json.Unmarshal(*raw, &s); err != nil {
		return "", false
	}
	if required && s == "" {
		return "", false
	}
	return s, true
}

// StringFieldOptional — отсутствие / null / пустая строка → ""; иначе строка; неверный тип → err.
func StringFieldOptional(raw *json.RawMessage) (string, error) {
	if raw == nil || len(*raw) == 0 {
		return "", nil
	}
	var s string
	if err := json.Unmarshal(*raw, &s); err != nil {
		return "", err
	}
	return s, nil
}

// ParseTags: отсутствие или null → nil; массив строк; иначе err.
func ParseTags(raw json.RawMessage) ([]string, error) {
	if len(raw) == 0 || string(raw) == "null" {
		return nil, nil
	}
	var tags []string
	if err := json.Unmarshal(raw, &tags); err != nil {
		return nil, err
	}
	return tags, nil
}
