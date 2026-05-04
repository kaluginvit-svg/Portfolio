from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.exceptions import AppException
from backend.models import Client
from backend.schemas import ClientCreate, ClientRead, ClientUpdate, PaginatedClients

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=201)
def create_client(body: ClientCreate, db: Session = Depends(get_db)):
    c = Client(
        name=body.name,
        email=body.email,
        phone=body.phone,
        company=body.company,
        status=body.status.value,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("", response_model=PaginatedClients)
def list_clients(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    q: str | None = Query(None, description="Поиск по имени, email, компании"),
    status: str | None = Query(None, description="active | archived"),
):
    stmt = select(Client)
    count_stmt = select(func.count()).select_from(Client)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (Client.name.ilike(like))
            | (Client.email.ilike(like))
            | (Client.company.ilike(like))
        )
        count_stmt = count_stmt.where(
            (Client.name.ilike(like))
            | (Client.email.ilike(like))
            | (Client.company.ilike(like))
        )
    if status:
        stmt = stmt.where(Client.status == status)
        count_stmt = count_stmt.where(Client.status == status)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.order_by(Client.id).offset(skip).limit(limit)).scalars().all()
    return PaginatedClients(total=total, skip=skip, limit=limit, items=rows)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise AppException("not_found", "Клиент не найден", status=404)
    return c


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, body: ClientUpdate, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise AppException("not_found", "Клиент не найден", status=404)
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = data["status"].value
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise AppException("not_found", "Клиент не найден", status=404)
    db.delete(c)
    db.commit()
    return None
