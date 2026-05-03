"""
HTTP-слой на Flask: только вызовы публичного api, без прямого доступа к репозиториям.
Запуск из каталога проекта: flask --app app run
или: python app.py
"""
from flask import Flask, jsonify, request

from api import add_user, store_password

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/users")
def create_user():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "ожидается JSON-объект"}), 400

    name = data.get("name")
    if not name or not isinstance(name, str):
        return jsonify({"error": "поле name (строка) обязательно"}), 400

    tags = data.get("tags")
    if tags is not None and not isinstance(tags, list):
        return jsonify({"error": "поле tags должно быть массивом или отсутствовать"}), 400

    password = data.get("password")
    if password is not None and not isinstance(password, str):
        return jsonify({"error": "поле password должно быть строкой или отсутствовать"}), 400

    try:
        user_id = add_user(name, tags)
        if password:
            store_password(user_id, password)
    except Exception:
        app.logger.exception("create_user failed")
        return jsonify({"error": "не удалось сохранить пользователя"}), 500

    return jsonify({"id": user_id}), 201


if __name__ == "__main__":
    app.run(debug=True)
