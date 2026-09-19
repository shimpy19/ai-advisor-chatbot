import os
from functools import lru_cache

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def get_model() -> str:
    return os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
