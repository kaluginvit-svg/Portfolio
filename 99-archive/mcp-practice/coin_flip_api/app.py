from flask import Flask, jsonify, send_from_directory
import random
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Путь к директории со статическими файлами
static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.route("/")
def root():
    """Главная страница - возвращает HTML интерфейс"""
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return send_from_directory(static_dir, "index.html")
    return jsonify({
        "message": "Coin Flip API",
        "endpoints": {
            "/flip": "Подбросить монетку один раз",
            "/flip/<count>": "Подбросить монетку несколько раз",
        }
    })


@app.route("/flip", methods=["GET"])
def flip_coin():
    """Подбросить монетку один раз"""
    result = random.choice(["орел", "решка"])
    return jsonify({
        "result": result,
        "flip": 1
    })


@app.route("/flip/<int:count>", methods=["GET"])
def flip_multiple(count):
    """Подбросить монетку несколько раз
    
    Args:
        count: Количество подбрасываний (от 1 до 100)
    """
    if count < 1:
        return jsonify({"error": "Количество должно быть больше 0"}), 400
    if count > 100:
        return jsonify({"error": "Максимальное количество подбрасываний: 100"}), 400
    
    results = [random.choice(["орел", "решка"]) for _ in range(count)]
    heads_count = results.count("орел")
    tails_count = results.count("решка")
    
    return jsonify({
        "results": results,
        "statistics": {
            "total": count,
            "орел": heads_count,
            "решка": tails_count
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
