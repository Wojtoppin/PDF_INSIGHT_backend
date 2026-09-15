from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.services.llm.base import LLMUnavailableError

_client = genai.Client(api_key=settings.gemini_api_key)


class GeminiClient:
    """LLMClient adapter for Google Gemini. See app/services/llm/base.py for
    the contract this must satisfy to keep providers swappable."""

    def generate_structured(
        self, *, system_prompt: str, user_content: str, schema: type[BaseModel]
    ) -> str:
        try:
            response = _client.models.generate_content(
                model=settings.gemini_model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except genai_errors.APIError as exc:
            # Covers both client errors (bad request, quota) and server errors
            # (transient 5xx, "model overloaded"). The caller treats this the
            # same as an invalid response: retry once, then a clear error.
            raise LLMUnavailableError(str(exc)) from exc

        return response.text
