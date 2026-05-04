from __future__ import annotations

import os
from io import BytesIO
from typing import Dict, List

from flask import Flask, jsonify, render_template, request, send_file
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


app = Flask(__name__, template_folder="templates", static_folder="static")


def _annuity_payment(principal: float, monthly_rate: float, months: int) -> float:
    """Calculate annuity monthly payment for given principal, rate and months."""
    if months <= 0:
        raise ValueError("Loan term must be greater than zero.")
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * (monthly_rate * factor) / (factor - 1)


def calculate_mortgage(
    principal: float,
    down_payment: float,
    years: float,
    annual_rate: float,
    extra_payments: List[Dict] | None = None,
    repay_mode: str = "reduce_term",
) -> dict:
    """
    Calculate monthly payment, total paid, overpayment and amortization schedule.
    Supports initial down payment, zero rates, and early repayments.
    repay_mode: "reduce_term" (сокращаем срок) или "reduce_payment" (снижаем платеж).
    """
    if principal <= 0 or years <= 0 or annual_rate < 0:
        raise ValueError("Invalid input values.")
    if down_payment < 0:
        raise ValueError("Invalid down payment.")

    financed_principal = principal - down_payment
    if financed_principal <= 0:
        raise ValueError("Down payment must be less than loan amount.")

    total_months = int(years * 12)
    if total_months <= 0:
        raise ValueError("Loan term must be greater than zero.")

    monthly_rate = annual_rate / 100 / 12

    extras: Dict[int, float] = {}
    for item in extra_payments or []:
        try:
            month = int(item.get("month", 0))
            amount = float(item.get("amount", 0))
        except (TypeError, ValueError):
            continue
        if month <= 0 or amount <= 0:
            continue
        extras[month] = extras.get(month, 0) + amount

    monthly_payment = _annuity_payment(financed_principal, monthly_rate, total_months)

    balance = financed_principal
    schedule = []
    total_interest = 0.0
    total_main_payments = 0.0
    paid_months = 0

    for current_month in range(1, total_months + 1):
        if balance <= 0:
            break

        interest = balance * monthly_rate
        principal_payment = monthly_payment - interest
        if principal_payment < 0:
            raise ValueError("Monthly payment is too small for the given rate.")

        if principal_payment > balance:
            principal_payment = balance
            monthly_payment = principal_payment + interest

        balance -= principal_payment
        total_interest += interest
        total_main_payments += principal_payment

        extra = extras.get(current_month, 0.0)
        extra_paid = min(extra, balance) if extra > 0 else 0.0
        balance -= extra_paid
        total_main_payments += extra_paid

        schedule.append(
            {
                "month": current_month,
                "payment": round(monthly_payment, 2),
                "interest": round(interest, 2),
                "principal": round(principal_payment, 2),
                "extra": round(extra_paid, 2),
                "balance": round(max(balance, 0.0), 2),
            }
        )
        paid_months = current_month

        if balance <= 0:
            break

        if extra_paid > 0 and repay_mode == "reduce_payment":
            remaining_months = total_months - current_month
            if remaining_months <= 0:
                break
            monthly_payment = _annuity_payment(balance, monthly_rate, remaining_months)

    total_paid_without_down = total_main_payments + total_interest
    total_paid = total_paid_without_down + down_payment
    overpayment = total_paid - principal

    return {
        "monthlyPayment": round(monthly_payment, 2),
        "totalPaid": round(total_paid, 2),
        "overpayment": round(overpayment, 2),
        "financedPrincipal": round(financed_principal, 2),
        "monthsActual": paid_months,
        "schedule": schedule,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    payload = request.get_json(silent=True) or {}

    try:
        principal = float(payload.get("amount", 0))
        down_payment = float(payload.get("downPayment", 0))
        years = float(payload.get("years", 0))
        rate = float(payload.get("rate", 0))
        repay_mode = payload.get("repayMode", "reduce_term")
        extra_payments = payload.get("extraPayments", [])

        result = calculate_mortgage(
            principal=principal,
            down_payment=down_payment,
            years=years,
            annual_rate=rate,
            extra_payments=extra_payments,
            repay_mode=repay_mode,
        )
        return jsonify({"success": True, "data": result})
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Проверьте введенные данные."}), 400


def build_excel(schedule: List[Dict], meta: Dict) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "График"

    headers = [
        "Месяц",
        "Платеж",
        "Проценты",
        "Тело кредита",
        "Досрочный платеж",
        "Остаток",
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for row in schedule:
        ws.append(
            [
                row["month"],
                row["payment"],
                row["interest"],
                row["principal"],
                row["extra"],
                row["balance"],
            ]
        )

    ws.append([])
    summary = [
        ("Сумма кредита", meta.get("principal")),
        ("Первоначальный взнос", meta.get("down_payment")),
        ("Финансируемая сумма", meta.get("financed_principal")),
        ("Ставка, %", meta.get("rate")),
        ("Срок, мес", meta.get("months_actual")),
        ("Общая выплата", meta.get("total_paid")),
        ("Переплата", meta.get("overpayment")),
    ]
    for label, val in summary:
        ws.append([label, val])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            value = str(cell.value) if cell.value is not None else ""
            if len(value) > max_length:
                max_length = len(value)
        ws.column_dimensions[col_letter].width = max_length + 2

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


@app.route("/export", methods=["POST"])
def export_excel():
    payload = request.get_json(silent=True) or {}
    try:
        principal = float(payload.get("amount", 0))
        down_payment = float(payload.get("downPayment", 0))
        years = float(payload.get("years", 0))
        rate = float(payload.get("rate", 0))
        repay_mode = payload.get("repayMode", "reduce_term")
        extra_payments = payload.get("extraPayments", [])

        result = calculate_mortgage(
            principal=principal,
            down_payment=down_payment,
            years=years,
            annual_rate=rate,
            extra_payments=extra_payments,
            repay_mode=repay_mode,
        )
        schedule = result["schedule"]
        buffer = build_excel(
            schedule,
            meta={
                "principal": principal,
                "down_payment": down_payment,
                "financed_principal": result["financedPrincipal"],
                "rate": rate,
                "months_actual": result["monthsActual"],
                "total_paid": result["totalPaid"],
                "overpayment": result["overpayment"],
            },
        )
        filename = "schedule.xlsx"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Проверьте введенные данные."}), 400


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(debug=debug, host=host, port=port)

