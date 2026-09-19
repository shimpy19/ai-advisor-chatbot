from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class TripPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    destination: str | None
    start_date: str | None
    end_date: str | None
    days: list[dict[str, Any]]
    updated_at: datetime


class TripPlanUpdate(BaseModel):
    """All fields optional — only the ones present in the request body are applied."""

    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    days: list[dict[str, Any]] | None = None


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageOut]
    trip_plan: TripPlanOut | None


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationUpdate(BaseModel):
    title: str


class SystemPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    updated_at: datetime


class SystemPromptUpdate(BaseModel):
    content: str
