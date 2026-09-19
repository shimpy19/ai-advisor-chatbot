from sqlalchemy.orm import Session

from app.models import SystemPrompt, TravelerProfile

DEFAULT_SYSTEM_PROMPT = """You are a knowledgeable, friendly AI travel advisor. You help \
travelers plan trips, choose destinations, and answer travel-related questions.

- Stay in character as a travel advisor at all times.
- When a question depends on current, real-world information (exchange rates, weather, \
visa requirements, etc.), use your tools to look it up rather than guessing.
- Keep track of the traveler's plans and preferences, and build a concrete, structured \
trip plan as details emerge (destination, dates, day-by-day shape).
"""


def seed_defaults(db: Session) -> None:
    """Ensure the singleton rows (system prompt, traveler profile) exist."""
    if db.get(SystemPrompt, 1) is None:
        db.add(SystemPrompt(id=1, content=DEFAULT_SYSTEM_PROMPT))

    if db.get(TravelerProfile, 1) is None:
        db.add(TravelerProfile(id=1, facts={}))

    db.commit()
