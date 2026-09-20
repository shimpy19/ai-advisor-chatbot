from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemPrompt
from app.schemas import SystemPromptOut, SystemPromptUpdate

router = APIRouter(prefix="/system-prompt", tags=["system-prompt"])


@router.get("", response_model=SystemPromptOut)
def get_system_prompt(db: Session = Depends(get_db)) -> SystemPrompt:
    return db.get(SystemPrompt, 1)


@router.put("", response_model=SystemPromptOut)
def update_system_prompt(
    payload: SystemPromptUpdate, db: Session = Depends(get_db)
) -> SystemPrompt:
    # No role guard needed here — the advisor's core behavior is fixed in
    # app/core_directive.py and always applied in chat.py regardless of what's saved
    # here, so this field can't actually steer the advisor away from travel advising.
    # That only covers role-steering, though: nothing here moderates content, checks
    # length, or guards against text aimed at a future reader of this field/the DB.
    # Trimmed here (not just client-side) so a whitespace-only save can't persist as
    # something that displays as non-empty while chat.py's own `.strip()` check treats
    # it as empty.
    prompt = db.get(SystemPrompt, 1)
    prompt.content = payload.content.strip()
    db.commit()
    db.refresh(prompt)
    return prompt
