"""Export reports to data/exports."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config import EXPORTS_DIR
from services.contract_service import contract_risk_scan
from services.finance_service import calculate_kpis, plan_vs_fact
from services.investment_service import evaluate_investment
from services.treasury_service import liquidity_forecast, payment_calendar
from utils.helpers import slug_filename

logger = logging.getLogger(__name__)

VALID_REPORT_TYPES = frozenset(
    {
        "kpis",
        "plan_vs_fact",
        "liquidity_forecast",
        "payment_calendar",
        "contract_risks",
        "investment_evaluation",
    }
)


def export_report(
    report_type: str,
    output_format: str | None = "json",
    output_path: str | None = None,
    *,
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
    liquidity_days: int = 90,
    payment_start: str | None = None,
    payment_end: str | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    rt = report_type.strip().lower()
    if rt not in VALID_REPORT_TYPES:
        raise ValueError(f"Unknown report_type: {report_type}")

    fmt = (output_format or "json").strip().lower()
    if fmt not in {"json", "txt"}:
        raise ValueError("output_format must be json or txt")

    payload: dict[str, Any] = {"report_type": rt}

    if rt == "kpis":
        payload["data"] = calculate_kpis(period_start, period_end, company_name)
    elif rt == "plan_vs_fact":
        payload["data"] = plan_vs_fact(period_start, period_end, company_name)
    elif rt == "liquidity_forecast":
        payload["data"] = liquidity_forecast(liquidity_days, company_name)
    elif rt == "payment_calendar":
        payload["data"] = payment_calendar(payment_start, payment_end, company_name)
    elif rt == "contract_risks":
        payload["data"] = contract_risk_scan()
    elif rt == "investment_evaluation":
        if project_id is None:
            raise ValueError("project_id is required for investment_evaluation export")
        payload["data"] = evaluate_investment(project_id)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = EXPORTS_DIR / slug_filename(f"report_{rt}", "json" if fmt == "json" else "txt")

    if fmt == "json":
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        lines = [f"report_type: {rt}", "", json.dumps(payload.get("data"), ensure_ascii=False, indent=2)]
        path.write_text("\n".join(lines), encoding="utf-8")

    logger.info("Report written to %s", path)
    return {"path": str(path), "report_type": rt}
