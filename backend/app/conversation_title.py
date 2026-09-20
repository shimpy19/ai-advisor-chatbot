import logging

from app.database import SessionLocal
from app.llm.client import get_client, get_model
from app.models import Conversation

logger = logging.getLogger(__name__)

DEFAULT_TITLE = "New conversation"
MAX_TITLE_LENGTH = 60


def maybe_generate_title(conversation: Conversation, first_user_message: str) -> None:
    """Best-effort: give the conversation a short auto-generated title from the
    traveler's first message, mirroring the auto-titling ChatGPT/Claude do. Only acts
    on a conversation still at its default title. Never raises — a failed or slow
    title generation must not break the chat turn it's attached to."""
    if conversation.title != DEFAULT_TITLE:
        return

    try:
        response = get_client().chat.completions.create(
            model=get_model(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a short title (3-6 words, no punctuation at the end, no "
                        "surrounding quotes) summarizing what this traveler wants to talk "
                        "about. Reply with ONLY the title, nothing else."
                    ),
                },
                {"role": "user", "content": first_user_message},
            ],
            max_tokens=20,
        )
        title = response.choices[0].message.content
    except Exception:
        logger.warning("Could not generate a conversation title", exc_info=True)
        return

    title = (title or "").strip().strip('"').strip()
    if title:
        conversation.title = title[:MAX_TITLE_LENGTH]


def generate_title_task(conversation_id: str, first_user_message: str) -> None:
    """FastAPI BackgroundTasks entry point: runs after the chat response has already
    been sent, so the extra OpenRouter call for the title doesn't add to the user's
    perceived reply latency. Opens its own DB session rather than reusing the
    request's — background tasks for a sync route run in a different worker thread,
    and empirically the request's session doesn't reliably persist writes made from
    there, so a fresh session is the safe, standard pattern for background DB work."""
    db = SessionLocal()
    try:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None:
            return
        maybe_generate_title(conversation, first_user_message)
        db.commit()
    finally:
        db.close()
