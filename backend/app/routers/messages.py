from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.conversation_title import generate_title_task
from app.database import get_db
from app.llm.chat import run_chat_turn
from app.routers.helpers import get_conversation_or_404
from app.schemas import ChatTurnResponse, MessageCreate

router = APIRouter(prefix="/conversations", tags=["messages"])


@router.post("/{conversation_id}/messages", response_model=ChatTurnResponse)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    conversation = get_conversation_or_404(db, conversation_id)

    try:
        assistant_message = run_chat_turn(db, conversation, payload.content)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Deferred so the extra OpenRouter call for the title doesn't add to this
    # response's latency.
    background_tasks.add_task(generate_title_task, conversation.id, payload.content)

    return {"message": assistant_message, "trip_plan": conversation.trip_plan}
