"""
Локальный запуск API без Docker (для отладки). Для сдачи ДЗ основной способ —
  docker compose up --build
из корня репозитория (папка с docker-compose.yml).

  python start_backend.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend", "google_integration"],
    )
