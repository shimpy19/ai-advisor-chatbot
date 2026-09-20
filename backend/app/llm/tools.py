from app.llm.tool_impls import (
    get_exchange_rate,
    get_public_holidays,
    get_weather,
    update_traveler_profile_tool,
    update_trip_plan_tool,
)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": (
                "Get the current exchange rate between two currencies, and optionally "
                "convert a specific amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "3-letter ISO 4217 currency code to convert from, e.g. USD",
                    },
                    "target_currency": {
                        "type": "string",
                        "description": "3-letter ISO 4217 currency code to convert to, e.g. EUR",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert. Defaults to 1 if not given.",
                    },
                },
                "required": ["base_currency", "target_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a named location (city, region, or country).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Place name, e.g. 'Tokyo' or 'Paris, France'",
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_public_holidays",
            "description": "Get the public holidays for a country in a given year.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "2-letter ISO 3166-1 alpha-2 country code, e.g. JP, HR, US",
                    },
                    "year": {
                        "type": "integer",
                        "description": "4-digit year",
                    },
                },
                "required": ["country_code", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_trip_plan",
            "description": (
                "Create or update the traveler's structured trip plan for this "
                "conversation. Only include the fields that are changing. For `days`, "
                "only include the day numbers being added or changed — existing days "
                "not mentioned are left untouched. Day numbers always refer to the "
                "CURRENT numbering shown in the trip plan above; a day cannot appear in "
                "both `days` and `remove_days` in the same call. Use `remove_days` to "
                "delete specific days — the remaining days are automatically renumbered "
                "to close any gap, so check the returned plan for the final numbering. "
                "Sending `days` as an empty list (with no `remove_days`) clears the "
                "entire itinerary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "The trip's destination."},
                    "start_date": {"type": "string", "description": "Trip start date, YYYY-MM-DD."},
                    "end_date": {"type": "string", "description": "Trip end date, YYYY-MM-DD."},
                    "days": {
                        "type": "array",
                        "description": (
                            "Days to add or update, by day number. Existing days not "
                            "listed here are left unchanged."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "day": {"type": "integer", "description": "Day number (1-indexed)."},
                                "title": {"type": "string", "description": "Short title for the day."},
                                "activities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Planned activities for the day.",
                                },
                            },
                            "required": ["day"],
                        },
                    },
                    "remove_days": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": (
                            "Day numbers to remove from the itinerary. Remaining days "
                            "are renumbered to close the gap."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_traveler_profile",
            "description": (
                "Record or update durable facts about the traveler that should be "
                "remembered across ALL their conversations, not just this trip — e.g. "
                "home airport, travel companions, dietary needs, budget preference, "
                "passport nationality. Only store facts that are durable and "
                "materially useful for future travel planning; skip trivial or "
                "one-off details. Before adding a new key, check the traveler "
                "profile shown in context — if a similar concept already exists "
                "under a different key (e.g. you're about to add 'food_preference' "
                "but 'diet' already captures it), update the EXISTING key instead "
                "of creating a near-duplicate. Use short, consistent keys. Use "
                "`remove_keys` to delete a fact that's no longer true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "facts": {
                        "type": "object",
                        "description": (
                            "Facts to add or update, as key-value pairs. Existing "
                            "keys not mentioned are left untouched."
                        ),
                        "additionalProperties": {"type": "string"},
                    },
                    "remove_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys to remove from the traveler's profile.",
                    },
                },
                "required": [],
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_exchange_rate": get_exchange_rate,
    "get_weather": get_weather,
    "get_public_holidays": get_public_holidays,
    "update_trip_plan": update_trip_plan_tool,
    "update_traveler_profile": update_traveler_profile_tool,
}

# Tools in this set need db/conversation bound in per-request (via functools.partial)
# rather than being pure functions of only the model-supplied arguments.
CONTEXT_AWARE_TOOLS = {"update_trip_plan", "update_traveler_profile"}

_schema_names = {schema["function"]["name"] for schema in TOOL_SCHEMAS}
_dispatch_names = set(TOOL_DISPATCH.keys())
assert _schema_names == _dispatch_names, (
    "TOOL_SCHEMAS and TOOL_DISPATCH are out of sync: "
    f"only in schemas={_schema_names - _dispatch_names}, only in dispatch={_dispatch_names - _schema_names}"
)
