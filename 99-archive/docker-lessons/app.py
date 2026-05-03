from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """Главная страница."""
    return jsonify({
        "message": "Добро пожаловать в Flask API",
        "endpoints": ["/", "/info", "/calc/<a>/<b>"]
    })


@app.route("/info")
def info():
    """Информация о приложении."""
    return jsonify({
        "app": "Flask Demo",
        "version": "1.0",
        "description": "Простое API с эндпоинтами для примера"
    })


@app.route("/calc/<float:a>/<float:b>")
def calc(a, b):
    """Сумма и произведение двух чисел."""
    return jsonify({
        "a": a,
        "b": b,
        "sum": a + b,
        "product": a * b
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
