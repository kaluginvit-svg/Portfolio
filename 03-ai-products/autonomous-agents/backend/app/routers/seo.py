import csv
import io
import json
from urllib.parse import unquote

import httpx
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.services.seo_analyzer import run_seo_analysis, run_seo_analysis_batch

router = APIRouter(prefix="/api", tags=["seo"])


@router.get("/status")
async def config_status():
    """Проверка: видит ли контейнер переменные окружения (ключ не показываем)."""
    return {
        "openai_api_key_set": bool(settings.openai_api_key and settings.openai_api_key.strip()),
        "openai_base_url": settings.openai_base_url or "(не задан)",
        "openai_model": settings.openai_model,
        "openai_ssl_verify": settings.openai_ssl_verify,
    }


class AnalyzeRequest(BaseModel):
    """Список URL — принимаются строки, нормализация на бэкенде."""
    url: str | None = None
    urls: list[str] | None = None


def sse_message(event: str, data: str) -> str:
    payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def _normalize_url(u: str) -> str:
    u = u.strip()
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    return u


def _urls_from_csv(content: str) -> list[str]:
    """Извлекает URL из CSV: колонка url/urls/link/ссылка или первая колонка."""
    content = content.strip()
    if content.startswith("\ufeff"):
        content = content[1:]
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []
    header = [c.strip().lower() for c in rows[0]]
    url_col = None
    for name in ("url", "urls", "link", "ссылка", "urls "):
        if name in header:
            url_col = header.index(name)
            break
    if url_col is None:
        url_col = 0
    out = []
    for row in rows[1:]:
        if url_col < len(row) and row[url_col].strip():
            out.append(_normalize_url(row[url_col].strip()))
    return list(dict.fromkeys(out))


def _urls_from_json(data: dict | list) -> list[str]:
    """Извлекает список URL из JSON. Поддерживает: ["url"], {"urls": ["url"]}, [{"url": "..."}]."""
    if isinstance(data, list):
        out = []
        for item in data:
            if isinstance(item, str) and item.strip():
                out.append(_normalize_url(item))
            elif isinstance(item, dict) and ("url" in item or "urls" in item):
                u = item.get("url") or (item.get("urls") or [])
                if isinstance(u, str):
                    out.append(_normalize_url(u))
                elif isinstance(u, list):
                    out.extend(_normalize_url(x) for x in u if isinstance(x, str) and x.strip())
        return list(dict.fromkeys(out))
    if isinstance(data, dict):
        urls = data.get("urls") or data.get("url")
        if isinstance(urls, str):
            return [_normalize_url(urls)]
        if isinstance(urls, list):
            return list(dict.fromkeys(_normalize_url(x) for x in urls if isinstance(x, str) and x.strip()))
    return []


async def stream_analysis(url: str):
    async for kind, payload in run_seo_analysis(url):
        yield sse_message(kind, payload)


async def stream_analysis_batch(urls: list[str]):
    async for kind, payload in run_seo_analysis_batch(urls):
        yield sse_message(kind, payload)


def _sse_headers():
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


@router.post("/analyze/file")
async def analyze_from_file(file: UploadFile = File(..., description="JSON или CSV со списком URL")):
    """Принимает JSON или CSV. JSON: ["url1"], {"urls": [...]}. CSV: колонка url/link/ссылка или первая колонка."""
    if not file.filename:
        raise HTTPException(400, "Выберите файл")
    ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    try:
        body = await file.read()
        text = body.decode("utf-8")
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {e}")

    if ext == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Невалидный JSON: {e}")
        urls = _urls_from_json(data)
    elif ext == "csv":
        urls = _urls_from_csv(text)
    else:
        raise HTTPException(400, "Нужен файл .json или .csv (в т.ч. экспорт из Google Таблиц)")

    if not urls:
        raise HTTPException(400, "В файле не найдено ни одного URL.")
    if len(urls) == 1:
        return StreamingResponse(
            stream_analysis(urls[0]),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )
    return StreamingResponse(
        stream_analysis_batch(urls),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


class SheetRequest(BaseModel):
    csv_url: str  # ссылка на опубликованную в веб таблицу (CSV)


def _is_local_path(s: str) -> bool:
    s = s.strip().lower()
    if s.startswith(("file:///", "file://")):
        return True
    if len(s) >= 2 and s[1] == ":" and s[0].isalpha():
        return True
    if s.startswith("/") or s.startswith("\\"):
        return True
    return False


@router.post("/analyze/sheet")
async def analyze_from_sheet(request: SheetRequest):
    """Принимает ссылку на таблицу, опубликованную в веб как CSV (Google Таблицы → Файл → Опубликовать в интернете → CSV)."""
    url = (request.csv_url or "").strip()
    if not url:
        raise HTTPException(400, "Укажите csv_url — ссылку на экспорт таблицы в CSV")
    if _is_local_path(url):
        raise HTTPException(
            400,
            "Это путь к файлу на компьютере. Для локального файла используйте поле «Файл .csv или .json» и выберите файл. Поле ниже — только для ссылки из интернета (https://...).",
        )
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            text = r.text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                400,
                "По ссылке таблица не найдена (404). Опубликуйте таблицу в интернете (Файл → Опубликовать в интернете → CSV) или загрузите файл через «Файл .csv».",
            )
        raise HTTPException(400, f"Не удалось загрузить таблицу по ссылке: {e}")
    except Exception as e:
        raise HTTPException(400, f"Не удалось загрузить таблицу по ссылке: {e}")
    urls = _urls_from_csv(text)
    if not urls:
        raise HTTPException(400, "В таблице не найдено ни одного URL. Нужна колонка url/link/ссылка или URL в первой колонке.")
    if len(urls) == 1:
        return StreamingResponse(
            stream_analysis(urls[0]),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )
    return StreamingResponse(
        stream_analysis_batch(urls),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@router.post("/analyze")
async def analyze_stream(request: Request):
    """Принимает JSON: {"urls": ["https://...", ...]} — список URL (массив строк)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(422, "Ожидается JSON в теле запроса с полем urls (массив строк)")
    if not isinstance(body, dict):
        raise HTTPException(400, "Тело запроса должно быть объектом с полем urls")
    urls_raw = body.get("urls")
    if urls_raw is None:
        raise HTTPException(422, "В теле запроса должно быть поле urls — массив URL (строк)")
    if not isinstance(urls_raw, list):
        raise HTTPException(400, "urls должен быть массивом строк")
    urls = list(dict.fromkeys(_normalize_url(str(u).strip()) for u in urls_raw if u is not None and str(u).strip()))
    if not urls:
        raise HTTPException(400, "В списке urls нет ни одного непустого URL")
    if len(urls) == 1:
        return StreamingResponse(
            stream_analysis(urls[0]),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )
    return StreamingResponse(
        stream_analysis_batch(urls),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@router.get("/analyze")
async def analyze_stream_get(url: list[str] | None = Query(None, description="URL для анализа (можно несколько)")):
    if not url:
        raise HTTPException(400, "Укажите хотя бы один параметр url (например: ?url=https://example.com)")
    normalized = [_normalize_url(unquote(u).strip()) for u in url if u and u.strip()]
    if not normalized:
        raise HTTPException(400, "Нет валидных URL")
    if len(normalized) == 1:
        return StreamingResponse(
            stream_analysis(normalized[0]),
            media_type="text/event-stream",
            headers=_sse_headers(),
        )
    return StreamingResponse(
        stream_analysis_batch(normalized),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )
