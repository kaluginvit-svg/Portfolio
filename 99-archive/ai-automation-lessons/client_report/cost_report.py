"""
Оценка стоимости запроса к чату по токенам и ценам из .env.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class CostEstimate:
    """Стоимость в USD по тарифу за 1M токенов."""

    usd: float
    price_input_per_1m: float
    price_output_per_1m: float


def get_price_per_1m_from_env() -> tuple[float, float]:
    """USD за 1M входных и 1M выходных токенов (PRICE_INPUT_PER_1M_USD, PRICE_OUTPUT_PER_1M_USD)."""
    pin = float((os.getenv("PRICE_INPUT_PER_1M_USD") or "0").strip() or 0)
    pout = float((os.getenv("PRICE_OUTPUT_PER_1M_USD") or "0").strip() or 0)
    return pin, pout


def compute_cost_usd(prompt_tokens: int, completion_tokens: int) -> CostEstimate:
    pin, pout = get_price_per_1m_from_env()
    usd = (prompt_tokens / 1_000_000.0) * pin + (completion_tokens / 1_000_000.0) * pout
    return CostEstimate(usd=usd, price_input_per_1m=pin, price_output_per_1m=pout)


def resolve_usd_rub_rate(
    interactive: bool,
    cli_rate: float | None = None,
) -> float | None:
    """
    Курс рубля за $1: --usd-rub, затем USD_RUB_RATE из .env, иначе запрос в терминале (если interactive).
    """
    if cli_rate is not None and cli_rate > 0:
        return cli_rate
    raw = (os.getenv("USD_RUB_RATE") or "").strip()
    if raw:
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            pass
    if not interactive or not sys.stdin.isatty():
        return None
    print(
        "Курс USD/RUB — сколько рублей за 1 US dollar (Enter без оценки в рублях): ",
        end="",
        flush=True,
    )
    try:
        line = input().strip()
    except EOFError:
        return None
    if not line:
        return None
    try:
        return float(line.replace(",", "."))
    except ValueError:
        print("Не удалось разобрать число — оценка только в USD.", flush=True)
        return None


def _spaced_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def print_token_cost_report(
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: CostEstimate,
    usd_rub: float | None,
) -> None:
    print("", flush=True)
    print("--- Расход токенов (оценка) ---", flush=True)
    print(f"  Модель:           {model}", flush=True)
    print(f"  Вход (prompt):    {_spaced_int(prompt_tokens)}", flush=True)
    print(f"  Выход (completion): {_spaced_int(completion_tokens)}", flush=True)
    print(f"  Всего:            {_spaced_int(total_tokens)}", flush=True)
    print(
        f"  Тариф в .env:     ${cost.price_input_per_1m}/1M in, ${cost.price_output_per_1m}/1M out",
        flush=True,
    )
    print(f"  Оценка стоимости: ~${cost.usd:.6f} USD", flush=True)
    if cost.price_input_per_1m == 0 and cost.price_output_per_1m == 0:
        print(
            "  (цены $/1M токенов не заданы — укажите PRICE_INPUT_PER_1M_USD и PRICE_OUTPUT_PER_1M_USD в .env)",
            flush=True,
        )
    if usd_rub is not None and usd_rub > 0:
        rub = cost.usd * usd_rub
        print(f"  В рублях (~):     ~{rub:.2f} ₽ (курс {usd_rub:.2f} ₽/$)", flush=True)
    print("---", flush=True)
