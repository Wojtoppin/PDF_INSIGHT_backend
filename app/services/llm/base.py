from typing import Protocol, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMUnavailableError(Exception):
    """Raised by an LLMClient adapter when the call to the provider itself
    fails (network error, transient outage, rate limit) — distinct from the
    provider returning a response that fails schema validation. Provider-
    agnostic on purpose, so app/services/analysis.py doesn't need to know
    which SDK-specific exceptions a given adapter can raise."""


class LLMClient(Protocol):
    """Minimal contract any provider adapter must satisfy.

    Swapping Gemini for another provider later means writing one new class
    that implements this method — app/services/analysis.py never changes.
    """

    def generate_structured(
        self, *, system_prompt: str, user_content: str, schema: type[SchemaT]
    ) -> str:
        """Return raw JSON text intended to match `schema`. Validation happens
        by the caller — this method's only job is talking to the provider."""
        ...
