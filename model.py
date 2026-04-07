from __future__ import annotations

from config import get_settings
from services.langchain_service import LangChainSupportService
from services.support_service import SupportCopilotService

_SETTINGS = get_settings()
_SERVICE = SupportCopilotService(
    LangChainSupportService(
        api_key=_SETTINGS["OPENAI_API_KEY"],
        timeout=_SETTINGS["OPENAI_TIMEOUT_SECONDS"],
        model_aliases=_SETTINGS["MODEL_ALIASES"],
    )
)
_LEGACY_MODEL_MAPPING = {
    "llama": "fast",
    "granite": "balanced",
    "mistral": "smart",
}


def generate_response(model_alias: str, user_prompt: str) -> dict:
    resolved_alias = _LEGACY_MODEL_MAPPING.get(model_alias, model_alias)
    model_id = _SETTINGS["MODEL_ALIASES"][resolved_alias]
    return _SERVICE.generate_ticket_payload(
        user_message=user_prompt,
        model_alias=resolved_alias,
        model_id=model_id,
    )


def llama_response(_system_prompt: str, user_prompt: str) -> dict:
    return generate_response("fast", user_prompt)


def granite_response(_system_prompt: str, user_prompt: str) -> dict:
    return generate_response("balanced", user_prompt)


def mistral_response(_system_prompt: str, user_prompt: str) -> dict:
    return generate_response("smart", user_prompt)
