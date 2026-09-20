import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models import Conversation, TripPlan

logger = logging.getLogger(__name__)


def _validate_dates(start_date: str | None, end_date: str | None) -> tuple[date, date] | None:
    """Returns (start, end) if both are well-formed and in order, None if either is
    absent. Raises ValueError (rather than silently ignoring) for malformed or
    reversed dates, since those are genuinely invalid input, not "nothing to check"."""
    if not start_date or not end_date:
        return None
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError(f"Dates must be in YYYY-MM-DD format: {exc}") from exc
    if end < start:
        raise ValueError(f"end_date ({end_date}) is before start_date ({start_date}).")
    return start, end


def _validate_day_numbers(day_numbers: list[int], start_date: str | None, end_date: str | None) -> None:
    parsed = _validate_dates(start_date, end_date)
    if parsed is None:
        return  # No date range known yet — nothing to validate against.
    start, end = parsed

    total_days = (end - start).days + 1
    invalid = sorted({d for d in day_numbers if d < 1 or d > total_days})
    if invalid:
        raise ValueError(
            f"Day number(s) {invalid} fall outside the trip's date range "
            f"({start_date} to {end_date}, {total_days} day(s) total). "
            f"Valid day numbers are 1-{total_days}."
        )


def _validate_day_entries(entries: list[dict]) -> None:
    for entry in entries:
        day = entry.get("day")
        if not isinstance(day, int):
            raise ValueError(f"Each day entry must include an integer 'day' number, got {day!r}.")


def _merge_days(
    existing_days: list[dict], upserts: list[dict] | None, removals: list[int] | None
) -> list[dict]:
    """Upsert the given days by day number, then remove any listed days. If any day was
    removed, the remaining days are renumbered contiguously (1..N) to close the gap.
    Day numbers in both `upserts` and `removals` always refer to the CURRENT numbering
    (before this call's removals are applied)."""
    by_day = {d["day"]: dict(d) for d in existing_days}

    for entry in upserts or []:
        by_day[entry["day"]] = dict(entry)

    if removals:
        for day_num in removals:
            by_day.pop(day_num, None)
        remaining = sorted(by_day.values(), key=lambda d: d["day"])
        return [{**d, "day": i + 1} for i, d in enumerate(remaining)]

    return sorted(by_day.values(), key=lambda d: d["day"])


def apply_trip_plan_update(db: Session, conversation: Conversation, updates: dict) -> TripPlan:
    """Create-or-update this conversation's trip plan.

    `updates` may contain `destination`, `start_date`, `end_date` (plain replace), `days`
    (list of {day, title?, activities?} to upsert by day number, referring to CURRENT day
    numbers — days not mentioned are left untouched; an explicit empty list with no
    `remove_days` clears the itinerary), and `remove_days` (day numbers to delete, closing
    the resulting gap by renumbering).

    All validation happens before any mutation, so a rejected update leaves the
    conversation's trip plan (including "no trip plan yet") completely untouched — it
    never partially applies or creates an empty placeholder row.

    Does not commit — the caller controls the transaction boundary.
    """
    existing = conversation.trip_plan
    existing_days = existing.days if existing else []
    effective_start = updates.get("start_date", existing.start_date if existing else None)
    effective_end = updates.get("end_date", existing.end_date if existing else None)

    days_provided = "days" in updates
    days_upserts = updates.get("days") or []
    remove_days = updates.get("remove_days") or []

    _validate_day_entries(days_upserts)

    conflict = {e["day"] for e in days_upserts} & set(remove_days)
    if conflict:
        raise ValueError(
            f"Day number(s) {sorted(conflict)} appear in both `days` and `remove_days` "
            "— remove them from one or the other."
        )

    if days_provided or remove_days:
        new_days = _merge_days(existing_days, days_upserts, remove_days) if (days_upserts or remove_days) else []
    else:
        new_days = existing_days

    # Validate the FINAL resulting days against the FINAL effective dates — this catches
    # both "added an out-of-range day" and "shrank the date range below existing days".
    if new_days:
        _validate_day_numbers([d["day"] for d in new_days], effective_start, effective_end)
    else:
        _validate_dates(effective_start, effective_end)  # still catch reversed/malformed dates

    # Validation passed — safe to actually create/attach and mutate now.
    trip_plan = existing
    if trip_plan is None:
        trip_plan = TripPlan()
        conversation.trip_plan = trip_plan  # sets the FK and keeps the in-memory relationship in sync

    if "destination" in updates:
        trip_plan.destination = updates["destination"]
    if "start_date" in updates:
        trip_plan.start_date = updates["start_date"]
    if "end_date" in updates:
        trip_plan.end_date = updates["end_date"]
    if days_provided or remove_days:
        trip_plan.days = new_days

    return trip_plan


def format_trip_plan_compact(trip_plan: TripPlan | None) -> str:
    """A compact, token-light text summary of the trip plan for LLM context — plain
    lines instead of repeated JSON punctuation/keys. Each day is formatted defensively
    so one malformed entry can't crash every future turn in the conversation."""
    if trip_plan is None:
        return "No trip plan has been started yet for this conversation."

    header_bits = []
    if trip_plan.destination:
        header_bits.append(trip_plan.destination)
    if trip_plan.start_date or trip_plan.end_date:
        header_bits.append(f"{trip_plan.start_date or '?'} to {trip_plan.end_date or '?'}")
    lines = [
        "Current trip plan: "
        + (", ".join(header_bits) if header_bits else "(no destination/dates set yet)")
    ]

    if not trip_plan.days:
        lines.append("(no days planned yet)")
    for day in trip_plan.days:
        try:
            line = f"Day {day.get('day')}"
            if day.get("title"):
                line += f": {day['title']}"
            activities = day.get("activities") or []
            if activities:
                line += " — " + ", ".join(str(a) for a in activities)
            lines.append(line)
        except Exception:
            logger.warning("Could not format trip plan day entry: %r", day)
            lines.append(f"Day {day.get('day', '?')}: (could not display this day's details)")

    return "\n".join(lines)
