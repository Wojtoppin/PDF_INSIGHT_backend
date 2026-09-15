from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.config import settings
from app.core.errors import InvalidFileError
from app.core.rate_limit import limiter
from app.schemas.analysis import AnalysisResult
from app.services.analysis import analyze_document
from app.services.llm.base import LLMClient
from app.services.llm.gemini import GeminiClient
from app.services.pdf_extraction import extract_text

router = APIRouter()

_PDF_MAGIC_BYTES = b"%PDF"


def get_llm_client() -> LLMClient:
    return GeminiClient()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalysisResult)
@limiter.limit(settings.rate_limit)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    llm_client: LLMClient = Depends(get_llm_client),
) -> AnalysisResult:
    if file.content_type != "application/pdf":
        raise InvalidFileError("Plik musi być w formacie PDF.")

    content = await file.read()

    if not content.startswith(_PDF_MAGIC_BYTES):
        raise InvalidFileError("Plik nie jest prawidłowym dokumentem PDF.")

    if len(content) > settings.max_file_size_bytes:
        raise InvalidFileError(
            f"Plik przekracza maksymalny dozwolony rozmiar ({settings.max_file_size_mb} MB)."
        )

    extracted = extract_text(content)

    return analyze_document(extracted, file.filename or "document.pdf", llm_client)
