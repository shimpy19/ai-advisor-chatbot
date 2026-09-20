from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Conversation, TripPlan

DIGEST_LIMIT = 10


def get_recent_trip_digest(db: Session, conversation: Conversation) -> list[tuple]:
    """Other conversations' trip summaries, for the "Tier A" continuity nudge — the
    model can mention overlap in plain text, it never merges/writes across
    conversations. Runs on every chat turn, so it selects only the four scalar
    columns actually needed rather than loading full Conversation/TripPlan ORM
    objects."""
    return (
        db.query(Conversation.title, TripPlan.destination, TripPlan.start_date, TripPlan.end_date)
        .join(TripPlan, TripPlan.conversation_id == Conversation.id)
        .filter(
            Conversation.id != conversation.id,
            or_(
                TripPlan.destination.isnot(None),
                TripPlan.start_date.isnot(None),
                TripPlan.end_date.isnot(None),
            ),
        )
        .order_by(Conversation.updated_at.desc())
        .limit(DIGEST_LIMIT)
        .all()
    )


def format_digest_compact(rows: list[tuple]) -> str:
    if not rows:
        return "No other trips have been discussed in other conversations."
    lines = ["Other trips the traveler has discussed in different conversations:"]
    for title, destination, start_date, end_date in rows:
        date_bit = f", {start_date or '?'} to {end_date or '?'}" if (start_date or end_date) else ""
        lines.append(f'- "{title}": {destination or "destination not yet set"}{date_bit}')
    return "\n".join(lines)
