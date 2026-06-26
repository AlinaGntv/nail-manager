from openai import AsyncOpenAI
from pydantic import ValidationError

from app.ai.parser import AIResponse, parse_ai_response
from app.ai.prompts import build_system_prompt, build_user_prompt
from app.config import Settings
from app.utils.logger import logger


class OpenAILeadClient:
    """OpenAI Responses API client for appointment lead qualification."""

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.openai_model
        self._system_prompt = build_system_prompt(settings)

    async def get_response(
        self,
        message: str,
        known_name: str | None = None,
        known_phone: str | None = None,
        known_service: str | None = None,
        known_datetime: str | None = None,
    ) -> AIResponse:
        """Return validated AI appointment response, retrying invalid JSON once."""
        prompt = build_user_prompt(
            message=message,
            known_name=known_name,
            known_phone=known_phone,
            known_service=known_service,
            known_datetime=known_datetime,
        )

        last_error: Exception | None = None
        for attempt in range(1, 3):
            try:
                raw_content = await self._request_json(prompt)
                logger.info("OpenAI response attempt={}: {}", attempt, raw_content)
                return parse_ai_response(raw_content)
            except ValidationError as exc:
                last_error = exc
                logger.warning("Invalid OpenAI JSON attempt={}: {}", attempt, exc)

        raise RuntimeError("OpenAI returned invalid JSON after 2 attempts") from last_error

    async def _request_json(self, prompt: str) -> str:
        """Call OpenAI Responses API and return the output text."""
        response = await self._client.responses.create(
            model=self._model,
            instructions=self._system_prompt,
            input=prompt,
            temperature=0.3,
            text={"format": {"type": "json_object"}},
        )
        return response.output_text
