from app.llm.tool_impls import get_exchange_rate, get_public_holidays, get_weather

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
]

TOOL_DISPATCH = {
    "get_exchange_rate": get_exchange_rate,
    "get_weather": get_weather,
    "get_public_holidays": get_public_holidays,
}

_schema_names = {schema["function"]["name"] for schema in TOOL_SCHEMAS}
_dispatch_names = set(TOOL_DISPATCH.keys())
assert _schema_names == _dispatch_names, (
    "TOOL_SCHEMAS and TOOL_DISPATCH are out of sync: "
    f"only in schemas={_schema_names - _dispatch_names}, only in dispatch={_dispatch_names - _schema_names}"
)
