import httpx2
from sqlalchemy.orm import Session

from app.models import Conversation
from app.schemas import TravelerProfileOut, TripPlanOut
from app.traveler_profile import apply_traveler_profile_update
from app.trip_plan import apply_trip_plan_update

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOLIDAYS_URL = "https://date.nager.at/api/v3/PublicHolidays"

TIMEOUT = 10.0

# WMO weather interpretation codes, as used by Open-Meteo.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_exchange_rate(base_currency: str, target_currency: str, amount: float = 1) -> dict:
    base_currency = base_currency.upper()
    target_currency = target_currency.upper()

    # Frankfurter returns HTTP 422 "bad currency pair" for from==to instead of a 1:1 rate.
    if base_currency == target_currency:
        return {
            "base_currency": base_currency,
            "target_currency": target_currency,
            "rate": 1.0,
            "amount": amount,
            "converted_amount": round(amount, 2),
            "date": None,
        }

    with httpx2.Client(timeout=TIMEOUT) as client:
        response = client.get(
            FRANKFURTER_URL, params={"from": base_currency, "to": target_currency}
        )
    response.raise_for_status()
    data = response.json()
    rate = data["rates"][target_currency]
    return {
        "base_currency": base_currency,
        "target_currency": target_currency,
        "rate": rate,
        "amount": amount,
        "converted_amount": round(rate * amount, 2),
        "date": data["date"],
    }


def get_weather(location: str) -> dict:
    with httpx2.Client(timeout=TIMEOUT) as client:
        geo_response = client.get(GEOCODING_URL, params={"name": location, "count": 1})
        geo_response.raise_for_status()
        results = geo_response.json().get("results")
        if not results:
            return {"error": f"Could not find a location matching '{location}'"}

        place = results[0]
        forecast_response = client.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current_weather": "true",
                "timezone": "auto",
            },
        )
    forecast_response.raise_for_status()
    forecast = forecast_response.json()
    current = forecast["current_weather"]

    return {
        "location": place.get("name", location),
        "country": place.get("country"),
        "temperature_celsius": current["temperature"],
        "windspeed_kmh": current["windspeed"],
        "conditions": WEATHER_CODES.get(current["weathercode"], "Unknown"),
        "local_time": current["time"],
        "timezone": forecast.get("timezone"),
    }


def get_public_holidays(country_code: str, year: int) -> dict:
    with httpx2.Client(timeout=TIMEOUT) as client:
        response = client.get(f"{HOLIDAYS_URL}/{year}/{country_code.upper()}")
    if response.status_code == 404:
        return {"error": f"No holiday data for country code '{country_code}'"}
    response.raise_for_status()
    holidays = response.json()
    return {
        "country_code": country_code.upper(),
        "year": year,
        "holidays": [{"date": h["date"], "name": h["localName"]} for h in holidays],
    }


def update_trip_plan_tool(db: Session, conversation: Conversation, **fields) -> dict:
    """Bound per-request with db/conversation via functools.partial — the model only
    ever supplies destination/start_date/end_date/days/remove_days."""
    try:
        trip_plan = apply_trip_plan_update(db, conversation, fields)
    except ValueError as exc:
        return {"error": str(exc)}

    db.flush()  # populate DB-side defaults (id, updated_at, ...) without committing
    return TripPlanOut.model_validate(trip_plan).model_dump(mode="json")


def update_traveler_profile_tool(db: Session, conversation: Conversation, **fields) -> dict:
    """Bound per-request with db/conversation via functools.partial, same as
    update_trip_plan_tool — `conversation` is unused here since the traveler profile
    is a global singleton, not conversation-scoped, but keeping the same (db,
    conversation) shape avoids a second dispatch-binding mechanism for one tool."""
    try:
        profile = apply_traveler_profile_update(db, fields)
    except ValueError as exc:
        return {"error": str(exc)}

    db.flush()
    return TravelerProfileOut.model_validate(profile).model_dump(mode="json")
