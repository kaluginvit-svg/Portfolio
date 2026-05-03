// Package passwordhash — строка PBKDF2 для файла (совместимо с Python password_storage).
package passwordhash

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"golang.org/x/crypto/pbkdf2"
)

// FileLine возвращает user_id:salt_hex:iterations:dk_hex\n
func FileLine(userID int64, password string, saltBytes, iterations int) (string, error) {
	salt := make([]byte, saltBytes)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}
	dk := pbkdf2.Key([]byte(password), salt, iterations, 32, sha256.New)
	return fmt.Sprintf("%d:%s:%d:%s\n",
		userID,
		hex.EncodeToString(salt),
		iterations,
		hex.EncodeToString(dk),
	), nil
}
