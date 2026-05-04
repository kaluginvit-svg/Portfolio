import base64
import json
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import qrcode
from weasyprint import CSS, HTML


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
FONT_DIR = BASE_DIR / "fonts"
FONT_FILE = FONT_DIR / "DejaVuSans.ttf"
FONT_URL = "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/version_2_37/ttf/DejaVuSans.ttf"
FONT_ZIP_URL = "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip/download"


def ensure_environment() -> None:
    for folder in (DATA_DIR, TEMPLATE_DIR, OUTPUT_DIR, FONT_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def ensure_font() -> Optional[Path]:
    if FONT_FILE.exists():
        return FONT_FILE

    try:
        print("Downloading DejaVu Sans for Cyrillic support...")
        urllib.request.urlretrieve(FONT_URL, FONT_FILE)
        return FONT_FILE
    except Exception as exc:
        print(f"Could not download font from primary URL: {exc}")

    # Fallback: download zip from SourceForge and extract the TTF
    zip_path = FONT_DIR / "dejavu.zip"
    try:
        print("Trying fallback SourceForge download...")
        urllib.request.urlretrieve(FONT_ZIP_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [m for m in zf.namelist() if m.endswith("DejaVuSans.ttf")]
            if not members:
                raise FileNotFoundError("DejaVuSans.ttf not found in archive")
            zf.extract(members[0], FONT_DIR)
            extracted = FONT_DIR / members[0]
            extracted.rename(FONT_FILE)
            return FONT_FILE
    except Exception as exc:
        print(f"Could not download font from fallback: {exc}")
        return None
    finally:
        if zip_path.exists():
            try:
                zip_path.unlink()
            except OSError:
                pass


def list_data_files() -> List[Path]:
    files = []
    for pattern in ("*.csv", "*.json"):
        files.extend(sorted(DATA_DIR.glob(pattern)))
    return files


def list_template_files() -> List[Path]:
    return sorted(TEMPLATE_DIR.glob("*.html"))


def choose_option(options: List[Path], prompt: str) -> Path:
    for idx, item in enumerate(options, start=1):
        print(f"{idx}. {item.name}")
    while True:
        choice = input(prompt).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Введите номер из списка.")


def load_records(file_path: Path) -> List[Dict[str, Any]]:
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")

    with open(file_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return normalize_json_records(data)


def normalize_json_records(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [ensure_dict(item) for item in data]

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return [ensure_dict(item) for item in value]
        return [ensure_dict(data)]

    raise ValueError("JSON структура не поддерживается. Ожидается список или объект.")


def ensure_dict(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        return item
    raise ValueError("Каждая запись должна быть объектом со значениями полей.")


def find_invoice_key(records: List[Dict[str, Any]]) -> Optional[str]:
    candidates = ["invoice_id", "invoiceid", "invoice", "id"]
    for record in records:
        for key in record.keys():
            if key.lower() in candidates:
                return key
    return None


def build_invoice_map(records: List[Dict[str, Any]]) -> Tuple[Optional[str], Dict[str, Dict[str, Any]]]:
    invoice_key = find_invoice_key(records)
    if not invoice_key:
        return None, {}

    mapping: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if invoice_key in record:
            mapping[str(record[invoice_key])] = record
    return invoice_key, mapping


def choose_invoice(invoice_ids: List[str], invoice_map: Dict[str, Dict[str, Any]]) -> str:
    print("0. Все")
    for idx, inv in enumerate(invoice_ids, start=1):
        name = invoice_map.get(inv, {}).get("customer_name") or invoice_map.get(inv, {}).get("customer") or ""
        suffix = f" — {name}" if name else ""
        print(f"{idx}. {inv}{suffix}")
    while True:
        choice = input("Выберите номер счета-фактуры (0 - все): ").strip()
        if choice.isdigit():
            num = int(choice)
            if num == 0:
                return "__ALL__"
            if 1 <= num <= len(invoice_ids):
                return invoice_ids[num - 1]
        print("Введите номер из списка.")


def flatten_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, full_key))
        else:
            flat[full_key] = value
    return flat


def render_template(template_str: str, context: Dict[str, Any]) -> str:
    pattern = re.compile(r"{{\s*([\w\.\-]+)\s*}}")

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return str(context.get(key, ""))

    return pattern.sub(replace, template_str)


def build_css(font_path: Optional[Path]) -> str:
    if font_path and font_path.exists():
        font_face = (
            "@font-face {\n"
            "  font-family: 'DejaVuSansEmbedded';\n"
            f"  src: url('{font_path.as_uri()}') format('truetype');\n"
            "}\n"
        )
        family = "DejaVuSansEmbedded, 'DejaVu Sans', 'Roboto', Arial, sans-serif"
    else:
        font_face = ""
        family = "'DejaVu Sans', 'Roboto', Arial, sans-serif"

    return font_face + f"body {{ font-family: {family}; }}"


def sanitize_filename(value: str) -> str:
    clean = re.sub(r"[^\w\-\.]+", "_", value.strip())
    return clean or "invoice"


def make_qr_base64(payload: str) -> str:
    """Build a QR code PNG and return as data URI."""
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def generate_pdf(html_content: str, css_str: str, template_path: Path, output_path: Path) -> None:
    html = HTML(string=html_content, base_url=str(template_path.parent.resolve()))
    css = CSS(string=css_str, base_url=str(template_path.parent.resolve()))
    html.write_pdf(target=str(output_path), stylesheets=[css])


def open_pdf(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        print(f"Не удалось открыть файл автоматически: {exc}")


def main() -> None:
    ensure_environment()
    font_path = ensure_font()

    data_files = list_data_files()
    template_files = list_template_files()

    print("\nДоступные файлы данных:")
    if not data_files:
        print("  нет файлов. Добавьте CSV/JSON в папку /data")
        return
    selected_data = choose_option(data_files, "Выберите файл данных по номеру: ")

    print("\nДоступные HTML-шаблоны:")
    if not template_files:
        print("  нет шаблонов. Добавьте .html в папку /templates")
        return
    selected_template = choose_option(template_files, "Выберите шаблон по номеру: ")

    records = load_records(selected_data)
    invoice_key, invoice_map = build_invoice_map(records)
    if not invoice_map:
        print("Не удалось найти поле invoice id в данных.")
        return

    invoice_ids = list(invoice_map.keys())

    print("\nДоступные счета-фактуры:")
    chosen_id = choose_invoice(invoice_ids, invoice_map)

    template_text = selected_template.read_text(encoding="utf-8")
    if chosen_id == "__ALL__":
        records_to_render = [invoice_map[iid] for iid in invoice_ids]
    else:
        records_to_render = [invoice_map[chosen_id]]

    rendered_parts = []
    for idx, rec in enumerate(records_to_render):
        context = flatten_dict(rec)
        payload = (
            f"invoice:{rec.get(invoice_key or 'invoice_id')};"
            f"total:{rec.get('total')};"
            f"customer:{rec.get('customer_name') or rec.get('customer') or ''}"
        )
        context["qr_src"] = make_qr_base64(payload)
        rendered = render_template(template_text, context)
        if idx < len(records_to_render) - 1:
            rendered += "\n<div style=\"page-break-after: always;\"></div>"
        rendered_parts.append(rendered)

    rendered_html = "\n".join(rendered_parts)

    css_str = build_css(font_path)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_name = "invoice_all.pdf" if chosen_id == "__ALL__" else f"invoice_{sanitize_filename(chosen_id)}.pdf"
    output_file = OUTPUT_DIR / output_name

    generate_pdf(rendered_html, css_str, selected_template, output_file)
    print(f"\nPDF сохранен: {output_file}")
    open_pdf(output_file)


if __name__ == "__main__":
    main()

