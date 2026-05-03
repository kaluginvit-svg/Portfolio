"""
HTML (Jinja2) → PDF через WeasyPrint.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .report_sections import merge_sections_into_payload

# WeasyPrint подключаем только в html_to_pdf — иначе при старте main.py
# инициализируется GLib и в терминал сыпятся GIO-WARNING во время input().

_PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _PACKAGE_DIR.parent
TEMPLATES_DIR = _PACKAGE_DIR / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"


def _ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


_MONTHS_RU = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def _format_generation_date_ru(dt: datetime | None = None) -> str:
    """Дата для шаблона: «7 апреля 2026 г., 13:31»."""
    now = dt or datetime.now()
    return f"{now.day} {_MONTHS_RU[now.month - 1]} {now.year} г., {now.strftime('%H:%M')}"


def _normalize_next_steps_for_list(text: str) -> str:
    """Шаги через перенос или «;» → по строке на шаг (для {% for %} в шаблоне)."""
    s = (text or "").strip()
    if not s:
        return ""
    parts = [p.strip() for p in re.split(r"[\n;]+", s) if p.strip()]
    return "\n".join(parts)


def render_report_html(
    data: dict[str, Any],
    template_name: str = "report_template.html",
    *,
    mode: str = "full",
) -> str:
    """Подставляет данные в HTML-шаблон. mode: full | analysis | software | steps."""
    payload: dict[str, Any] = merge_sections_into_payload(dict(data), mode)
    if "generation_date" not in payload:
        payload["generation_date"] = _format_generation_date_ru()
    if "next_steps" in payload:
        payload["next_steps"] = _normalize_next_steps_for_list(str(payload["next_steps"]))

    so = payload.get("software_options")
    if not isinstance(so, list):
        payload["software_options"] = []
    rl = str(payload.get("response_letter", "") or "")
    if rl.strip():
        payload["response_letter_paragraphs"] = [p.strip() for p in rl.split("\n\n") if p.strip()]
    else:
        payload["response_letter_paragraphs"] = []

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(**payload)


def build_report_filename(prefix: str = "report") -> str:
    """Имя файла вида report_2026-04-07_14-30.pdf"""
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"{prefix}_{stamp}.pdf"


def html_to_pdf(html_string: str, output_path: str | Path) -> Path:
    """Конвертирует HTML-строку в PDF и сохраняет по пути output_path."""
    from weasyprint import HTML

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    base_url = TEMPLATES_DIR.as_uri() + "/"
    HTML(string=html_string, base_url=base_url).write_pdf(str(out))
    return out.resolve()


def generate_report_pdf(
    data: dict[str, Any],
    template_name: str = "report_template.html",
    *,
    mode: str = "full",
    filename: str | None = None,
) -> Path:
    """
    Рендерит шаблон и сохраняет PDF в reports/.

    mode: full | analysis | software | steps — какие секции показать.
    """
    _ensure_reports_dir()
    html_str = render_report_html(data, template_name=template_name, mode=mode)
    out_name = filename or build_report_filename()
    return html_to_pdf(html_str, REPORTS_DIR / out_name)


def render_kp_html(kp_data: dict[str, Any]) -> str:
    """Коммерческое предложение — тот же визуальный стиль."""
    payload = dict(kp_data)
    if "generation_date" not in payload:
        payload["generation_date"] = _format_generation_date_ru()
    blocks = payload.get("kp_blocks")
    if not isinstance(blocks, list):
        payload["kp_blocks"] = []
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("kp_template.html")
    return template.render(**payload)


def generate_kp_pdf(kp_data: dict[str, Any], filename: str | None = None) -> Path:
    _ensure_reports_dir()
    html_str = render_kp_html(kp_data)
    out_name = filename or build_report_filename(prefix="kp")
    return html_to_pdf(html_str, REPORTS_DIR / out_name)
