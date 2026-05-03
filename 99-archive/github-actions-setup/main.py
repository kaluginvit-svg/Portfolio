from datetime import datetime, timezone
import pytz
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Time API", description="Простой тестовый бэкенд")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой эндпоинт с приветствием."""
    return {"message": "Time API", "docs": "/docs"}


@app.get("/time")
@app.get("/time/")
async def get_server_time():
    """Текущее время по UTC (ISO 8601)."""
    now = datetime.now(timezone.utc)
    return {
        "time": now.isoformat(),
        "timestamp": round(now.timestamp(), 6),
    }


@app.get("/datetime")
@app.get("/datetime/")
async def get_server_datetime():
    """Полная дата и время по UTC (ISO 8601)."""
    now = datetime.now(timezone.utc)
    return {
        "datetime": now.isoformat(),
        "date": now.date().isoformat(),
        "time": now.time().isoformat(),
        "timestamp": round(now.timestamp(), 6),
    }


@app.get("/date")
@app.get("/date/")
async def get_server_date():
    """Текущая дата по UTC (ISO 8601)."""
    now = datetime.now(timezone.utc)
    return {
        "date": now.date().isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
    }


@app.get("/convert")
@app.get("/convert/")
async def convert_timezone(
    from_tz: str = Query("UTC", description="Исходный часовой пояс (например UTC, Europe/Moscow)"),
    to_tz: str = Query(..., description="Целевой часовой пояс (например Europe/London, America/New_York)"),
    dt: str | None = Query(None, description="Дата и время в ISO 8601 (если не указано — текущий момент в from_tz)"),
):
    """Конвертация времени из одного часового пояса в другой (pytz)."""
    try:
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)
    except pytz.UnknownTimeZoneError as e:
        raise HTTPException(status_code=400, detail=f"Неверный часовой пояс: {e!s}")

    if dt is None:
        now = datetime.now(from_zone)
    else:
        try:
            now = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            if now.tzinfo is None:
                now = from_zone.localize(now)
            else:
                now = now.astimezone(from_zone)
        except (ValueError, pytz.exceptions.AmbiguousTimeError, pytz.exceptions.NonExistentTimeError) as e:
            raise HTTPException(status_code=400, detail=f"Неверный формат даты/времени: {e!s}")

    converted = now.astimezone(to_zone)
    return {
        "from_tz": from_tz,
        "to_tz": to_tz,
        "original": now.isoformat(),
        "converted": converted.isoformat(),
        "timestamp": round(converted.timestamp(), 6),
    }


@app.get("/health")
async def health():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}
