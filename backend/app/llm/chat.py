import functools
import json
import logging
from datetime import datetime, timezone

import httpx2
from sqlalchemy.orm import Session

from app.core_directive import CORE_DIRECTIVE
from app.digest import format_digest_compact, get_recent_trip_digest
from app.llm.client import get_client, get_model
from app.llm.tools import CONTEXT_AWARE_TOOLS, TOOL_DISPATCH, TOOL_SCHEMAS
from app.models import Conversation, Message, SystemPrompt, TravelerProfile
from app.traveler_profile import format_traveler_profile_compact
from app.trip_plan import format_trip_plan_compact

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5


def _build_dispatch(db: Session, conversation: Conversation) -> dict:
    """A per-request copy of TOOL_DISPATCH with context-aware tools (e.g.
    update_trip_plan) bound to this request's db/conversation — the model never
    supplies those itself."""
    dispatch = dict(TOOL_DISPATCH)
    for name in CONTEXT_AWARE_TOOLS:
        dispatch[name] = functools.partial(dispatch[name], db, conversation)
    return dispatch


def _message_to_dict(m: Message) -> dict:
    if m.role == "assistant" and m.tool_calls:
        return {"role": "assistant", "content": m.content, "tool_calls": m.tool_calls}
    if m.role == "tool":
        return {"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content}
    return {"role": m.role, "content": m.content}


def _execute_tool_call(tool_call, dispatch: dict) -> str:
    name = tool_call.function.name
    func = dispatch.get(name)
    if func is None:
        logger.warning("Model requested unknown tool: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        arguments = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        logger.warning("Could not parse arguments for tool %s: %r", name, tool_call.function.arguments)
        return json.dumps({"error": f"Invalid arguments for {name}"})

    try:
        result = func(**arguments)
    except httpx2.HTTPError as exc:
        # Expected: the external API is down, rate-limited, or returned an error status.
        logger.warning("Tool %s failed calling its external API: %s", name, exc)
        result = {"error": f"Could not complete {name}: the external service is unavailable."}
    except Exception:
        # Unexpected: a real bug (e.g. schema/implementation drift) — log the full
        # traceback so it's discoverable, but still degrade gracefully for the user.
        logger.exception("Unexpected error executing tool %s with arguments %s", name, arguments)
        result = {"error": f"An unexpected error occurred while running {name}."}

    return json.dumps(result)


def run_chat_turn(db: Session, conversation: Conversation, user_content: str) -> Message:
    """Persist the user's message, run the model (with tool calls as needed), persist
    and return its final reply. Intermediate tool exchanges are only flushed, not
    committed, so a failed or exhausted turn leaves no orphaned state behind."""
    user_message = Message(
        conversation_id=conversation.id, role="user", kind="text", content=user_content
    )
    db.add(user_message)
    db.commit()

    # The traveler's custom instructions (tone, style, extra rules — see the settings
    # page) come first and are optional; CORE_DIRECTIVE always follows, both here and
    # after the conversation history, so it can't be diluted by a long conversation
    # or overridden by whatever the custom prompt says.
    system_prompt = db.get(SystemPrompt, 1)
    context_messages = []
    if system_prompt.content.strip():
        context_messages.append({"role": "system", "content": system_prompt.content})
    context_messages += [_message_to_dict(m) for m in conversation.messages]
    context_messages.append({"role": "system", "content": CORE_DIRECTIVE})
    # Placed last (not merged into the opening system message) so it gets stronger
    # recency weighting than earlier turns — otherwise the model can trust its own
    # prior reply over a fresher state, e.g. after the user edits the plan directly.
    traveler_profile = db.get(TravelerProfile, 1)
    digest_rows = get_recent_trip_digest(db, conversation)
    # The model has no built-in notion of "now" — without this, it guesses at a
    # plausible-looking date (often landing near its training cutoff), so any
    # relative date the traveler gives ("this Monday", "next week", "in 3 days")
    # resolves to the wrong year entirely.
    today = datetime.now(timezone.utc).date()
    state_block = "\n\n".join(
        [
            f"Today's date is {today.isoformat()} ({today.strftime('%A')}).",
            format_traveler_profile_compact(traveler_profile),
            format_digest_compact(digest_rows),
            format_trip_plan_compact(conversation.trip_plan),
        ]
    )
    context_messages.append(
        {
            "role": "system",
            "content": (
                "IMPORTANT: the following is CURRENT, authoritative information — the "
                "traveler's saved profile, other trips they've discussed elsewhere, "
                "and this conversation's trip plan. It may have changed since earlier "
                "in this conversation (e.g. via direct edits) — treat it as more up "
                "to date than anything said earlier.\n\n" + state_block
            ),
        }
    )

    dispatch = _build_dispatch(db, conversation)

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                response = get_client().chat.completions.create(
                    model=get_model(),
                    messages=context_messages,
                    tools=TOOL_SCHEMAS,
                )
            except Exception as exc:
                raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

            try:
                choice_message = response.choices[0].message
            except IndexError as exc:
                raise RuntimeError("OpenRouter returned no choices in its response.") from exc

            if choice_message.tool_calls:
                tool_calls_dump = [tc.model_dump() for tc in choice_message.tool_calls]
                db.add(
                    Message(
                        conversation_id=conversation.id,
                        role="assistant",
                        kind="tool_call_request",
                        content=choice_message.content,
                        tool_calls=tool_calls_dump,
                    )
                )
                context_messages.append(
                    {
                        "role": "assistant",
                        "content": choice_message.content,
                        "tool_calls": tool_calls_dump,
                    }
                )

                for tool_call in choice_message.tool_calls:
                    result_content = _execute_tool_call(tool_call, dispatch)
                    db.add(
                        Message(
                            conversation_id=conversation.id,
                            role="tool",
                            kind="tool_result",
                            content=result_content,
                            tool_call_id=tool_call.id,
                        )
                    )
                    context_messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": result_content}
                    )

                db.flush()
                continue

            if not choice_message.content:
                raise RuntimeError("The advisor returned an empty response.")

            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                kind="text",
                content=choice_message.content,
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            return assistant_message

        raise RuntimeError("The advisor made too many tool calls without producing a final answer.")
    except RuntimeError:
        db.rollback()
        raise
