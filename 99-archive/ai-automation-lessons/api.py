"""
Опциональный HTTP API (Flask): POST JSON с полем "transcript" → ProxyAPI → PDF в reports/.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

_PROJECT = Path(__file__).resolve().parent
load_dotenv(_PROJECT / ".env")

from client_report import compute_cost_usd, generate_report_pdf, process_dialog_with_ai

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/generate", methods=["POST"])
def generate():
    payload = request.get_json(silent=True) or {}
    transcript = payload.get("transcript") or payload.get("text") or ""
    if not str(transcript).strip():
        return jsonify({"error": "Укажите transcript (или text) в JSON теле запроса"}), 400
    try:
        result = process_dialog_with_ai(str(transcript))
        pdf_path = generate_report_pdf(result.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    try:
        rel = str(pdf_path.relative_to(_PROJECT))
    except ValueError:
        rel = str(pdf_path)

    cost = compute_cost_usd(result.prompt_tokens, result.completion_tokens)
    usd_rub_raw = payload.get("usd_rub")
    if usd_rub_raw is None:
        usd_rub_raw = os.getenv("USD_RUB_RATE")
    cost_rub: float | None = None
    usd_rub: float | None = None
    if usd_rub_raw is not None and str(usd_rub_raw).strip() != "":
        try:
            usd_rub = float(str(usd_rub_raw).replace(",", "."))
            if usd_rub > 0:
                cost_rub = cost.usd * usd_rub
        except ValueError:
            pass

    return jsonify(
        {
            "message": f"Отчёт успешно создан: {rel}",
            "path": rel,
            "data": result.data,
            "usage": {
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
            },
            "cost_usd": round(cost.usd, 8),
            "cost_rub": None if cost_rub is None else round(cost_rub, 2),
            "usd_rub_used": usd_rub,
        }
    )


def run(host: str = "127.0.0.1", port: int = 5000) -> None:
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
