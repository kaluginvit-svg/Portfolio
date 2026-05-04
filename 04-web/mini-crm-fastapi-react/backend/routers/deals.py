from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.exceptions import AppException
from backend.models import Client, Deal
from backend.schemas import DealCreate, DealRead, DealUpdate, PaginatedDeals

router = APIRouter(prefix="/deals", tags=["deals"])


def _ensure_client(db: Session, cid: int | None) -> None:
    if cid is None:
        return
    if db.get(Client, cid) is None:
        raise AppException("validation", f"Клиент id={cid} не существует", status=422)


@router.post("", response_model=DealRead, status_code=201)
def create_deal(body: DealCreate, db: Session = Depends(get_db)):
    _ensure_client(db, body.client_id)
    d = Deal(
        title=body.title,
        amount=body.amount,
        currency=body.currency,
        stage=body.stage.value,
        client_id=body.client_id,
        opened_at=body.opened_at,
        expected_close=body.expected_close,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.get("", response_model=PaginatedDeals)
def list_deals(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    q: str | None = Query(None),
    stage: str | None = Query(None),
):
    stmt = select(Deal)
    count_stmt = select(func.count()).select_from(Deal)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Deal.title.ilike(like))
        count_stmt = count_stmt.where(Deal.title.ilike(like))
    if stage:
        stmt = stmt.where(Deal.stage == stage)
        count_stmt = count_stmt.where(Deal.stage == stage)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.order_by(Deal.id).offset(skip).limit(limit)).scalars().all()
    return PaginatedDeals(total=total, skip=skip, limit=limit, items=rows)


@router.get("/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    d = db.get(Deal, deal_id)
    if not d:
        raise AppException("not_found", "Сделка не найдена", status=404)
    return d


@router.patch("/{deal_id}", response_model=DealRead)
def update_deal(deal_id: int, body: DealUpdate, db: Session = Depends(get_db)):
    d = db.get(Deal, deal_id)
    if not d:
        raise AppException("not_found", "Сделка не найдена", status=404)
    data = body.model_dump(exclude_unset=True)
    if "stage" in data and data["stage"] is not None:
        data["stage"] = data["stage"].value
    if "client_id" in data:
        _ensure_client(db, data["client_id"])
    for k, v in data.items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{deal_id}", status_code=204)
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    d = db.get(Deal, deal_id)
    if not d:
        raise AppException("not_found", "Сделка не найдена", status=404)
    db.delete(d)
    db.commit()
    return None
