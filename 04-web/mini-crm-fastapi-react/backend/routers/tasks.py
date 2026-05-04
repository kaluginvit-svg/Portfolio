from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.exceptions import AppException
from backend.models import Client, Deal, Task
from backend.schemas import PaginatedTasks, TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ensure_relations(db: Session, client_id: int | None, deal_id: int | None) -> None:
    if client_id is not None and db.get(Client, client_id) is None:
        raise AppException("validation", f"Клиент id={client_id} не существует", status=422)
    if deal_id is not None and db.get(Deal, deal_id) is None:
        raise AppException("validation", f"Сделка id={deal_id} не существует", status=422)


@router.post("", response_model=TaskRead, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    _ensure_relations(db, body.client_id, body.deal_id)
    t = Task(
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        priority=body.priority.value,
        done=body.done,
        client_id=body.client_id,
        deal_id=body.deal_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("", response_model=PaginatedTasks)
def list_tasks(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    q: str | None = Query(None),
    done: bool | None = Query(None),
    priority: str | None = Query(None),
):
    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Task.title.ilike(like))
        count_stmt = count_stmt.where(Task.title.ilike(like))
    if done is not None:
        stmt = stmt.where(Task.done == done)
        count_stmt = count_stmt.where(Task.done == done)
    if priority:
        stmt = stmt.where(Task.priority == priority)
        count_stmt = count_stmt.where(Task.priority == priority)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.order_by(Task.id).offset(skip).limit(limit)).scalars().all()
    return PaginatedTasks(total=total, skip=skip, limit=limit, items=rows)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t:
        raise AppException("not_found", "Задача не найдена", status=404)
    return t


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t:
        raise AppException("not_found", "Задача не найдена", status=404)
    data = body.model_dump(exclude_unset=True)
    if "priority" in data and data["priority"] is not None:
        data["priority"] = data["priority"].value
    if "client_id" in data or "deal_id" in data:
        cid = data.get("client_id", t.client_id)
        did = data.get("deal_id", t.deal_id)
        _ensure_relations(db, cid, did)
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t:
        raise AppException("not_found", "Задача не найдена", status=404)
    db.delete(t)
    db.commit()
    return None
