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
    prompt = db.get(SystemPrompt, 1)
    prompt.content = payload.content
    db.commit()
    db.refresh(prompt)
    return prompt
