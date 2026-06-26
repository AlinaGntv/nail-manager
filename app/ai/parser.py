import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class AIResponse(BaseModel):
    """Validated JSON response returned by the AI manager prompt."""

    model_config = ConfigDict(extra="forbid")

    lead_ready: bool
    reply: str = Field(min_length=1)
    name: str | None = None
    phone: str | None = None
    service: str | None = None
    datetime: str | None = None

    @model_validator(mode="after")
    def validate_ready_payload(self) -> "AIResponse":
        """Ensure ready leads contain all required appointment fields."""
        if self.lead_ready and not all([self.name, self.phone, self.service, self.datetime]):
            raise ValueError("Ready lead must include name, phone, service, and datetime")
        return self


def parse_ai_response(raw_content: str) -> AIResponse:
    """Parse and validate raw AI JSON content."""
    try:
        payload: dict[str, Any] = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValidationError.from_exception_data(
            title="AIResponse",
            line_errors=[
                {
                    "type": "json_invalid",
                    "loc": ("__root__",),
                    "msg": "Invalid JSON",
                    "input": raw_content,
                    "ctx": {"error": str(exc)},
                }
            ],
        ) from exc

    return AIResponse.model_validate(payload)
