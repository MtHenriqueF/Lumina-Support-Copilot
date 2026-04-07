from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_settings() -> dict:
    model_aliases = {
        "fast": os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"),
        "balanced": os.getenv("OPENAI_MODEL_BALANCED", "gpt-4.1-mini"),
        "smart": os.getenv("OPENAI_MODEL_SMART", "gpt-4.1"),
    }

    default_model_alias = os.getenv("DEFAULT_MODEL_ALIAS", "balanced").strip().lower() or "balanced"
    if default_model_alias not in model_aliases:
        default_model_alias = "balanced"

    return {
        "APP_NAME": os.getenv("APP_NAME", "Lumina Support Copilot"),
        "APP_SUBTITLE": os.getenv(
            "APP_SUBTITLE",
            "Classifique tickets, priorize atendimento e gere respostas claras com suporte de IA.",
        ),
        "APP_ENV": os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")),
        "DEBUG": _as_bool(os.getenv("FLASK_DEBUG"), default=False),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO").upper(),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "").strip(),
        "OPENAI_TIMEOUT_SECONDS": _as_float(os.getenv("OPENAI_TIMEOUT_SECONDS"), default=30.0),
        "DEFAULT_MODEL_ALIAS": default_model_alias,
        "MODEL_ALIASES": model_aliases,
        "MESSAGE_MAX_CHARS": _as_int(os.getenv("MESSAGE_MAX_CHARS"), default=4000),
    }


def build_model_catalog(model_aliases: dict[str, str]) -> list[dict[str, str]]:
    metadata = {
        "fast": {
            "label": "Fast",
            "hint": "Triagem rapida e menor custo.",
        },
        "balanced": {
            "label": "Balanced",
            "hint": "Melhor equilibrio entre qualidade e latencia.",
        },
        "smart": {
            "label": "Smart",
            "hint": "Analise mais forte para casos complexos.",
        },
    }

    catalog = []
    for alias, provider_model in model_aliases.items():
        entry = metadata.get(alias, {"label": alias.title(), "hint": "Modelo configurado via .env."})
        catalog.append(
            {
                "value": alias,
                "label": entry["label"],
                "hint": entry["hint"],
                "provider_model": provider_model,
            }
        )

    return catalog
