import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

WORDSTAT_TOKEN = os.getenv("WORDSTAT_TOKEN")
BASE_URL = os.getenv("WORDSTAT_BASE_URL", "https://api.wordstat.yandex.net")

if not WORDSTAT_TOKEN:
    raise ValueError("WORDSTAT_TOKEN не установлен в переменных окружения!")

headers = {
    "Content-Type": "application/json;charset=utf-8",
    "Authorization": f"Bearer {WORDSTAT_TOKEN}",
}

app = FastAPI(
    title="Yandex Wordstat MCP API",
    version="1.0.0",
    description="Wrapper around Yandex Wordstat API for SEO tools",
)

class TopRequestsRequest(BaseModel):
    phrase: Optional[str] = None
    phrases: Optional[List[str]] = None  # Массив фраз (не больше 128)
    numPhrases: Optional[int] = 50  # По умолчанию 50, максимум 2000
    regions: Optional[List[int]] = None  # [213] - Москва, [2] - СПб, [225] - Россия
    devices: Optional[List[str]] = None  # ["all"], ["desktop"], ["phone"], ["tablet"]

class DynamicsRequest(BaseModel):
    phrase: str  # В этом методе допускается только оператор +
    period: str  # "monthly", "weekly", "daily"
    fromDate: str  # YYYY-MM-DD (обязательный)
    toDate: Optional[str] = None  # YYYY-MM-DD
    regions: Optional[List[int]] = None
    devices: Optional[List[str]] = None

class RegionsRequest(BaseModel):
    phrase: str
    regionType: Optional[str] = "all"  # "cities", "regions", "all"
    devices: Optional[List[str]] = None

def call_wordstat(endpoint: str, payload: dict):
    """Вызов API Yandex Wordstat"""
    url = f"{BASE_URL}/v1/{endpoint}"
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if resp.status_code == 429:
            # Обработка превышения квоты
            retry_after = resp.headers.get("Retry-After", "неизвестно")
            raise HTTPException(
                status_code=429,
                detail=f"Превышена квота. Повторите попытку через {retry_after} секунд."
            )
        elif resp.status_code == 503:
            raise HTTPException(
                status_code=503,
                detail="Сервис временно недоступен. Попробуйте позже."
            )
        elif resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Wordstat error {resp.status_code}: {resp.text}",
            )
        
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запроса: {str(e)}")

@app.post("/v1/topRequests")
def top_requests(body: TopRequestsRequest):
    """Получить популярные запросы, содержащие указанную фразу"""
    if not body.phrase and not body.phrases:
        raise HTTPException(status_code=400, detail="Необходимо указать phrase или phrases")
    
    if body.phrases and len(body.phrases) > 128:
        raise HTTPException(status_code=400, detail="Максимум 128 фраз в массиве phrases")
    
    data = {}
    if body.phrase:
        data["phrase"] = body.phrase
    elif body.phrases:
        data["phrases"] = body.phrases
    
    if body.numPhrases:
        data["numPhrases"] = body.numPhrases
    
    if body.regions:
        data["regions"] = body.regions
    
    if body.devices:
        data["devices"] = body.devices
    
    raw = call_wordstat("topRequests", data)
    
    # Обработка ответа
    if body.phrase:
        # Одна фраза - возвращаем объект
        return {
            "source": "wordstat",
            "requestPhrase": raw.get("requestPhrase"),
            "totalCount": raw.get("totalCount"),
            "topRequests": raw.get("topRequests", []),
            "associations": raw.get("associations", [])
        }
    else:
        # Несколько фраз - возвращаем массив
        return {
            "source": "wordstat",
            "results": raw
        }

@app.post("/v1/dynamics")
def dynamics(body: DynamicsRequest):
    """Получить динамику числа запросов во времени"""
    data = {
        "phrase": body.phrase,
        "period": body.period,
        "fromDate": body.fromDate,
    }
    
    if body.toDate:
        data["toDate"] = body.toDate
    
    if body.regions:
        data["regions"] = body.regions
    
    if body.devices:
        data["devices"] = body.devices
    
    raw = call_wordstat("dynamics", data)
    
    return {
        "source": "wordstat",
        "phrase": body.phrase,
        "dynamics": raw.get("dynamics", [])
    }

@app.post("/v1/regions")
def regions(body: RegionsRequest):
    """Получить распределение запросов по регионам"""
    data = {
        "phrase": body.phrase,
    }
    
    if body.regionType:
        data["regionType"] = body.regionType
    
    if body.devices:
        data["devices"] = body.devices
    
    raw = call_wordstat("regions", data)
    
    return {
        "source": "wordstat",
        "phrase": body.phrase,
        "regions": raw.get("regions", [])
    }

@app.get("/v1/getRegionsTree")
def get_regions_tree():
    """Получить дерево регионов"""
    raw = call_wordstat("getRegionsTree", {})
    return raw

@app.get("/v1/userInfo")
def user_info():
    """Получить информацию о пользователе и квотах"""
    raw = call_wordstat("userInfo", {})
    return raw
