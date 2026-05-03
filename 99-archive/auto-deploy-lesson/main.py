from typing import Optional, List

from fastapi import FastAPI, status, HTTPException, Query
from pydantic import BaseModel, Field

# --- Модели ---

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0, le=1_000_000)
    tags: List[str] = []


class ItemCreate(ItemBase):
    """Тело запроса для создания Item (без id)."""
    pass


class ItemUpdate(BaseModel):
    """Тело запроса для частичного обновления Item."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0, le=1_000_000)
    tags: Optional[List[str]] = None


class Item(ItemBase):
    id: int


class ItemList(BaseModel):
    items: List[Item]
    total: int
    page: int
    size: int


# --- Хранилище в памяти (для демо) ---
_items: dict[int, Item] = {}
_next_id = 1


def _get_next_id() -> int:
    global _next_id
    n = _next_id
    _next_id += 1
    return n


# --- Приложение ---

app = FastAPI(
    title="FastAPI Template App",
    description="Шаблонное FastAPI-приложение для автодеплоя на VPS",
    version="1.0.1",
)


# --- Корень и сервис ---

@app.get("/", summary="Главная страница", tags=["root"])
def read_root() -> dict:
    return {"message": "FastAPI работает 🚀", "docs": "/docs"}


@app.get("/health", summary="Проверка здоровья сервиса", tags=["service"])
def health() -> dict:
    return {"status": "ok", "docs": "/docs"}


@app.get("/info", summary="Информация о приложении", tags=["service"])
def info() -> dict:
    return {
        "app": "FastAPI Template App",
        "version": "1.0.1",
        "items_count": len(_items),
    }


# --- CRUD Items ---

@app.get(
    "/items",
    response_model=ItemList,
    summary="Список Items с пагинацией и поиском",
    tags=["items"],
)
def list_items(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поиск по имени"),
) -> ItemList:
    items_list = list(_items.values())
    if search:
        search_lower = search.lower()
        items_list = [i for i in items_list if search_lower in i.name.lower()]
    total = len(items_list)
    start = (page - 1) * size
    page_items = items_list[start : start + size]
    return ItemList(items=page_items, total=total, page=page, size=size)


@app.get(
    "/items/{item_id}",
    response_model=Item,
    summary="Получить Item по ID",
    tags=["items"],
)
def get_item(item_id: int) -> Item:
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item не найден")
    return _items[item_id]


@app.post(
    "/items",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    summary="Создать Item",
    tags=["items"],
)
def create_item(body: ItemCreate) -> Item:
    item_id = _get_next_id()
    item = Item(id=item_id, **body.model_dump())
    _items[item_id] = item
    return item


@app.put(
    "/items/{item_id}",
    response_model=Item,
    summary="Полностью обновить Item",
    tags=["items"],
)
def update_item(item_id: int, body: ItemCreate) -> Item:
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item не найден")
    item = Item(id=item_id, **body.model_dump())
    _items[item_id] = item
    return item


@app.patch(
    "/items/{item_id}",
    response_model=Item,
    summary="Частично обновить Item",
    tags=["items"],
)
def patch_item(item_id: int, body: ItemUpdate) -> Item:
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item не найден")
    current = _items[item_id]
    data = body.model_dump(exclude_unset=True)
    updated = current.model_copy(update=data)
    _items[item_id] = updated
    return updated


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить Item",
    tags=["items"],
)
def delete_item(item_id: int) -> None:
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item не найден")
    del _items[item_id]
