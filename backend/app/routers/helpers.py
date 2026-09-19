from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Conversation


def get_conversation_or_404(db: Session, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
