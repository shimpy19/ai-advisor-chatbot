from dataclasses import dataclass
from datetime import date, datetime

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


@dataclass
class DuplicateTrip:
    conversation_id: str
    title: str
    destination: str
    start_date: str | None
    end_date: str | None
    updated_at: datetime


def _dates_overlap(
    start1: str | None, end1: str | None, start2: str | None, end2: str | None
) -> bool:
    """True if the two date ranges overlap, or if we can't tell because one or both
    sides are missing/malformed dates — a missing date doesn't rule out a match, it
    just means we fall back to the destination match alone."""
    try:
        s1, e1, s2, e2 = (date.fromisoformat(d) for d in (start1, end1, start2, end2))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return True
    return s1 <= e2 and s2 <= e1


def find_duplicate_trip(db: Session, conversation: Conversation) -> DuplicateTrip | None:
    """If another conversation already has a trip plan for roughly the same
    destination (and, when both have dates, overlapping ones), return it — most
    recently updated first — so the UI can nudge the traveler to continue planning
    there instead of splitting the same trip across conversations."""
    trip_plan = conversation.trip_plan
    if trip_plan is None or not trip_plan.destination:
        return None

    destination = trip_plan.destination.strip().lower()
    if not destination:
        return None

    candidates = (
        db.query(Conversation)
        .join(TripPlan, TripPlan.conversation_id == Conversation.id)
        .filter(Conversation.id != conversation.id, TripPlan.destination.isnot(None))
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    for other in candidates:
        other_plan = other.trip_plan
        other_destination = (other_plan.destination or "").strip().lower()
        if not other_destination:
            continue
        if destination not in other_destination and other_destination not in destination:
            continue
        if not _dates_overlap(
            trip_plan.start_date, trip_plan.end_date, other_plan.start_date, other_plan.end_date
        ):
            continue
        return DuplicateTrip(
            conversation_id=other.id,
            title=other.title,
            destination=other_plan.destination,
            start_date=other_plan.start_date,
            end_date=other_plan.end_date,
            updated_at=other.updated_at,
        )
    return None


def format_digest_compact(rows: list[tuple]) -> str:
    if not rows:
        return "No other trips have been discussed in other conversations."
    lines = ["Other trips the traveler has discussed in different conversations:"]
    for title, destination, start_date, end_date in rows:
        date_bit = f", {start_date or '?'} to {end_date or '?'}" if (start_date or end_date) else ""
        lines.append(f'- "{title}": {destination or "destination not yet set"}{date_bit}')
    return "\n".join(lines)
