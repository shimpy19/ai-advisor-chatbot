from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, TripPlan
from app.routers.helpers import get_conversation_or_404
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
    TripPlanOut,
    TripPlanUpdate,
)
from app.trip_plan import apply_trip_plan_update

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationDetail, status_code=201)
def create_conversation(
    payload: ConversationCreate = ConversationCreate(), db: Session = Depends(get_db)
) -> Conversation:
    conversation = Conversation()
    if payload.title:
        conversation.title = payload.title
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)) -> list[Conversation]:
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> Conversation:
    return get_conversation_or_404(db, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationDetail)
def rename_conversation(
    conversation_id: str, payload: ConversationUpdate, db: Session = Depends(get_db)
) -> Conversation:
    conversation = get_conversation_or_404(db, conversation_id)
    conversation.title = payload.title
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)) -> None:
    conversation = get_conversation_or_404(db, conversation_id)
    db.delete(conversation)
    db.commit()


@router.patch("/{conversation_id}/trip-plan", response_model=TripPlanOut)
def update_trip_plan(
    conversation_id: str, payload: TripPlanUpdate, db: Session = Depends(get_db)
) -> TripPlan:
    conversation = get_conversation_or_404(db, conversation_id)
    try:
        trip_plan = apply_trip_plan_update(db, conversation, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.commit()
    db.refresh(trip_plan)
    return trip_plan
