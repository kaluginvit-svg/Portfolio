from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientStatusEnum(str, Enum):
    active = "active"
    archived = "archived"


class DealStageEnum(str, Enum):
    lead = "lead"
    qualified = "qualified"
    proposal = "proposal"
    won = "won"
    lost = "lost"


class TaskPriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=64)
    company: str | None = Field(None, max_length=255)
    status: ClientStatusEnum = ClientStatusEnum.active


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=64)
    company: str | None = Field(None, max_length=255)
    status: ClientStatusEnum | None = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DealBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(0, ge=0)
    currency: str = Field("RUB", max_length=8)
    stage: DealStageEnum = DealStageEnum.lead
    client_id: int | None = None
    opened_at: date | None = None
    expected_close: date | None = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    amount: float | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=8)
    stage: DealStageEnum | None = None
    client_id: int | None = None
    opened_at: date | None = None
    expected_close: date | None = None


class DealRead(DealBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriorityEnum = TaskPriorityEnum.medium
    done: bool = False
    client_id: int | None = None
    deal_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=512)
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriorityEnum | None = None
    done: bool | None = None
    client_id: int | None = None
    deal_id: int | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PaginatedClients(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[ClientRead]


class PaginatedDeals(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[DealRead]


class PaginatedTasks(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[TaskRead]


class GoogleSettings(BaseModel):
    client_secret_path: str = Field(..., min_length=1)
    parent_folder_id: str = Field(..., min_length=1)
    google_token_path: str | None = None


class GoogleSettingsRead(BaseModel):
    client_secret_path: str | None = None
    parent_folder_id: str | None = None
    google_token_path: str | None = None
    has_valid_token_guess: bool = False


class ReportExportResponse(BaseModel):
    file_id: str
    url: str
    title: str


class ApiError(BaseModel):
    code: str
    message: str
    detail: str | None = None
