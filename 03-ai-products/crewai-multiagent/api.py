"""
FastAPI сервер для SEO-анализа через веб-интерфейс.

Запуск:
    uvicorn api:app --reload --host 0.0.0.0 --port 8001
    python api.py

После запуска откройте: http://localhost:8001/docs
"""
import os
import sys
import traceback
from typing import Optional
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator

# Проверка импорта перед запуском
try:
    from seo_crew import run_seo_analysis
    print("✓ Импорт seo_crew успешен")
except ImportError as e:
    print(f"✗ ОШИБКА: Не удалось импортировать seo_crew: {e}")
    print("Убедитесь, что все зависимости установлены: pip install -r requirements.txt")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"✗ ОШИБКА при импорте: {e}")
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(
    title="SEO Crew API",
    description="API для автоматизированного SEO-анализа веб-страниц",
    version="1.0.0"
)

# Настройка CORS для работы фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def normalize_url(url: str) -> str:
    """Нормализация URL: добавление протокола если отсутствует."""
    url = url.strip()
    if not url:
        raise ValueError("URL не может быть пустым")
    
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    
    return url


class SeoAnalysisRequest(BaseModel):
    """Запрос на SEO-анализ."""
    url: str
    save_to_file: Optional[bool] = True

    @validator("url")
    def validate_url(cls, v):
        """Валидация и нормализация URL."""
        return normalize_url(v)


# Кэширование пути к index.html
_index_path = os.path.join(static_dir, "index.html") if os.path.exists(static_dir) else None


@app.get("/")
def root():
    """Главная страница - редирект на фронтенд или информация об API."""
    if _index_path and os.path.exists(_index_path):
        return FileResponse(_index_path)
    
    return {
        "message": "SEO Crew API",
        "docs": "/docs",
        "frontend": "/static/index.html",
        "endpoints": {
            "/analyze": "POST - запустить SEO-анализ",
            "/health": "GET - проверить статус сервера"
        }
    }


@app.get("/health")
def health_check():
    """Проверка работоспособности сервера."""
    return {"status": "ok", "service": "SEO Crew API"}


def _run_analysis(url: str, save_to_file: bool) -> tuple:
    """
    Внутренняя функция для запуска анализа.
    
    Returns:
        tuple: (result, tasks_count)
    """
    result = run_seo_analysis(url, save_to_file=save_to_file)
    tasks_count = len(result.tasks_output) if hasattr(result, 'tasks_output') else 0
    return result, tasks_count


@app.post("/analyze")
def analyze_seo(req: SeoAnalysisRequest):
    """
    Запустить SEO-анализ страницы по URL.
    
    Returns:
        JSON с результатом анализа
    """
    try:
        result, tasks_count = _run_analysis(req.url, req.save_to_file)
        return {
            "status": "success",
            "url": req.url,
            "result": str(result),
            "tasks_completed": tasks_count
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении анализа: {str(e)}")


@app.post("/analyze/text", response_class=PlainTextResponse)
def analyze_seo_text(req: SeoAnalysisRequest):
    """
    То же, что /analyze, но возвращает только текстовый результат (без JSON).
    """
    try:
        result, _ = _run_analysis(req.url, req.save_to_file)
        return str(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Запуск FastAPI сервера...")
    print("=" * 60)
    
    # Проверка зависимостей
    try:
        import fastapi
        import uvicorn
        print(f"✓ FastAPI версия: {fastapi.__version__}")
        print(f"✓ Uvicorn установлен")
    except ImportError as e:
        print(f"✗ ОШИБКА: Не установлены зависимости: {e}")
        print("Выполните: pip install fastapi uvicorn")
        sys.exit(1)
    
    print("\nСервер будет доступен по адресам:")
    print("  - http://localhost:8001")
    print("  - http://127.0.0.1:8001")
    print("\nДокументация API: http://localhost:8001/docs")
    print("Проверка здоровья: http://localhost:8001/health")
    print("=" * 60)
    print("\nДля остановки нажмите Ctrl+C\n")
    
    try:
        # Используем строку импорта для поддержки reload
        uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
    except KeyboardInterrupt:
        print("\n\nСервер остановлен.")
    except OSError as e:
        error_msg = str(e).lower()
        if "address already in use" in error_msg or "address is already in use" in error_msg:
            print(f"\n✗ ОШИБКА: Порт 8001 уже занят!")
            print("\nРешения:")
            print("1. Остановите другой процесс на порту 8001")
            print("2. Или измените порт в api.py")
        else:
            print(f"\n✗ ОШИБКА при запуске сервера: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ОШИБКА при запуске сервера: {e}")
        print("\nВозможные причины:")
        print("1. Порт 8001 уже занят")
        print("2. Проблемы с зависимостями: pip install -r requirements.txt")
        print("3. Проблемы с .env файлом")
        traceback.print_exc()
        sys.exit(1)
