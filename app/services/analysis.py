import json
import logging

from pydantic import ValidationError

from app.core.errors import AnalysisFailedError, SuspiciousContentError
from app.core.security import looks_like_prompt_injection
from app.schemas.analysis import AnalysisResult
from app.services.llm.base import LLMClient, LLMUnavailableError
from app.services.llm.prompts import RETRY_PROMPT_SUFFIX, SYSTEM_PROMPT, build_user_prompt
from app.services.pdf_extraction import ExtractedDocument

logger = logging.getLogger(__name__)


def analyze_document(
    document: ExtractedDocument, file_name: str, llm_client: LLMClient
) -> AnalysisResult:
    if looks_like_prompt_injection(document.text):
        raise SuspiciousContentError()

    user_prompt = build_user_prompt(document.text, file_name, document.pages)

    result = _call_and_validate(llm_client, user_prompt)
    if result is not None:
        return result

    logger.warning("Gemini response failed schema validation, retrying once")
    result = _call_and_validate(llm_client, user_prompt + RETRY_PROMPT_SUFFIX)
    if result is not None:
        return result

    raise AnalysisFailedError()


def _call_and_validate(llm_client: LLMClient, user_prompt: str) -> AnalysisResult | None:
    try:
        raw_response = llm_client.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_content=user_prompt,
            schema=AnalysisResult,
        )
    except LLMUnavailableError as exc:
        logger.warning("LLM provider call failed: %s", exc)
        return None

    try:
        data = json.loads(raw_response)
        return AnalysisResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("Invalid AI response: %s", exc)
        return None
