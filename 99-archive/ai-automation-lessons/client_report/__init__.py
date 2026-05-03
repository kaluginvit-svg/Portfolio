"""
Генератор клиентских отчётов: ProxyAPI → структурированные данные → PDF (WeasyPrint).
"""

from __future__ import annotations

from .ai_processor import (
    ProcessingResult,
    generate_commercial_proposal,
    process_dialog_with_ai,
)
from .cost_report import (
    CostEstimate,
    compute_cost_usd,
    get_price_per_1m_from_env,
    print_token_cost_report,
    resolve_usd_rub_rate,
)
from .pdf_generator import (
    build_report_filename,
    generate_kp_pdf,
    generate_report_pdf,
    html_to_pdf,
    render_kp_html,
    render_report_html,
)

__all__ = [
    "CostEstimate",
    "ProcessingResult",
    "build_report_filename",
    "compute_cost_usd",
    "generate_commercial_proposal",
    "generate_kp_pdf",
    "generate_report_pdf",
    "get_price_per_1m_from_env",
    "html_to_pdf",
    "print_token_cost_report",
    "process_dialog_with_ai",
    "render_kp_html",
    "render_report_html",
    "resolve_usd_rub_rate",
]
