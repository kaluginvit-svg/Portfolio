import os
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import seo


# Корень фронтенда: отдельная папка frontend/ в корне проекта или монтированная в Docker
_BACKEND_ROOT = Path(__file__).resolve().parent.parent  # backend/app -> backend
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", str(_BACKEND_ROOT.parent / "frontend")))


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="SEO-ядро агент",
    description="Генерация SEO-ядра по ссылке с помощью ChatGPT",
    lifespan=lifespan,
)

app.include_router(seo.router)

_static_dir = FRONTEND_DIR / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

templates = Jinja2Templates(directory=str(FRONTEND_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
