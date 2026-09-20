from sqlalchemy.orm import Session

from app.models import TravelerProfile


def apply_traveler_profile_update(db: Session, updates: dict) -> TravelerProfile:
    """Merge-update the traveler's profile facts (the singleton row, id=1, seeded at
    startup so it's always present). `updates` may contain `facts` (key-value pairs to
    add or update — existing keys not mentioned are left untouched) and `remove_keys`
    (keys to delete). Always reassigns the whole `facts` dict rather than mutating it
    in place, so no Mutable wrapper is needed for change tracking.

    Does not commit — the caller controls the transaction boundary.
    """
    profile = db.get(TravelerProfile, 1)

    facts = updates.get("facts") or {}
    if not isinstance(facts, dict):
        raise ValueError("facts must be an object of key-value pairs.")

    new_facts = dict(profile.facts)
    new_facts.update(facts)

    remove_keys = updates.get("remove_keys") or []
    if isinstance(remove_keys, str):
        raise ValueError("remove_keys must be a list of key names, not a single string.")
    for key in remove_keys:
        new_facts.pop(key, None)

    profile.facts = new_facts
    return profile


def format_traveler_profile_compact(profile: TravelerProfile | None) -> str:
    """A compact, token-light text summary of the traveler's known facts."""
    if profile is None or not profile.facts:
        return "No traveler facts recorded yet."
    lines = ["Known facts about the traveler:"]
    for key, value in profile.facts.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)
