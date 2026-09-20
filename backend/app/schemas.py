from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    kind: str
    content: str | None
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
    """All fields optional — only the ones present in the request body are applied.
    `days` entries are merged by day number (added or updated) rather than replacing
    the whole itinerary; day numbers refer to the CURRENT numbering and cannot also
    appear in `remove_days` in the same request. `remove_days` deletes specific days
    and renumbers the remaining ones to close any gap. Sending `days` as an empty list
    with no `remove_days` clears the entire itinerary."""

    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    days: list[dict[str, Any]] | None = None
    remove_days: list[int] | None = None


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


class MessageCreate(BaseModel):
    content: str


class ChatTurnResponse(BaseModel):
    message: MessageOut
    trip_plan: TripPlanOut | None


class SystemPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    updated_at: datetime


class SystemPromptUpdate(BaseModel):
    content: str
