from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

CATEGORY_MAP = {
    "billing": "billing",
    "finance": "billing",
    "financial": "billing",
    "general": "general",
    "other": "general",
    "support": "general",
    "technical": "technical",
    "tech": "technical",
}
PRIORITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "low": "Low",
    "medium": "Medium",
    "med": "Medium",
    "normal": "Medium",
    "urgent": "High",
}


class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=280)
    sentiment: int = Field(ge=0, le=100)
    category: str
    priority: str
    language: str = Field(min_length=2, max_length=16)
    is_resolved: bool = False
    tags: list[str] = Field(default_factory=list)
    action: str = Field(min_length=1, max_length=320)
    response: str = Field(min_length=1, max_length=1200)

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, value: Any) -> int:
        if value is None or value == "":
            return 50

        try:
            score = int(float(value))
        except (TypeError, ValueError):
            score = 50

        return max(0, min(score, 100))

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        key = str(value or "general").strip().lower()
        return CATEGORY_MAP.get(key, "general")

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> str:
        key = str(value or "Medium").strip().lower()
        return PRIORITY_MAP.get(key, "Medium")

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value: Any) -> str:
        text = str(value or "en").strip()
        return text or "en"

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> list[str]:
        if value is None:
            return []

        raw_items = value
        if isinstance(value, str):
            raw_items = re.split(r"[,;|/]", value)

        if not isinstance(raw_items, list):
            return []

        normalized_tags: list[str] = []
        for item in raw_items:
            tag = str(item).strip().lower()
            if not tag or tag in normalized_tags:
                continue
            normalized_tags.append(tag[:32])
            if len(normalized_tags) == 8:
                break

        return normalized_tags
