import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import router
from app.config import settings
from app.core.errors import PDFInsightError
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Insight API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(PDFInsightError)
async def handle_pdf_insight_error(request: Request, exc: PDFInsightError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"error": "Wystąpił nieoczekiwany błąd serwera."})


app.include_router(router, prefix="/api")
