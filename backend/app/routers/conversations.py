from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, TripPlan
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdate,
    TripPlanOut,
    TripPlanUpdate,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _get_conversation_or_404(db: Session, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


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
    return _get_conversation_or_404(db, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationDetail)
def rename_conversation(
    conversation_id: str, payload: ConversationUpdate, db: Session = Depends(get_db)
) -> Conversation:
    conversation = _get_conversation_or_404(db, conversation_id)
    conversation.title = payload.title
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)) -> None:
    conversation = _get_conversation_or_404(db, conversation_id)
    db.delete(conversation)
    db.commit()


@router.patch("/{conversation_id}/trip-plan", response_model=TripPlanOut)
def update_trip_plan(
    conversation_id: str, payload: TripPlanUpdate, db: Session = Depends(get_db)
) -> TripPlan:
    conversation = _get_conversation_or_404(db, conversation_id)

    trip_plan = conversation.trip_plan
    if trip_plan is None:
        trip_plan = TripPlan(conversation_id=conversation.id)
        db.add(trip_plan)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(trip_plan, field, value)

    db.commit()
    db.refresh(trip_plan)
    return trip_plan
