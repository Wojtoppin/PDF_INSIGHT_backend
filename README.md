# PDF Insight — Backend

FastAPI backend for the [PDF Insight](.) recruitment project. Acts as a proxy
between the public frontend (React SPA on GitHub Pages) and Google Gemini:
it receives a PDF, extracts and validates its text, asks Gemini for a
structured analysis, and returns JSON matching a fixed schema. The Gemini API
key never reaches the browser.

```
Frontend (GitHub Pages) --PDF upload--> this backend --prompt--> Gemini
                          <--JSON result--            <--JSON response--
```

## Architecture & decisions

- **Backend re-extracts text from the raw PDF**, rather than trusting text
  the frontend might send. This makes the backend the single source of truth
  for page count/text, and is the natural place to add OCR later (see below).
- **Gemini sits behind a small `LLMClient` interface** (`app/services/llm/base.py`).
  `app/services/analysis.py` never imports the Gemini SDK directly — swapping
  providers later means writing one new adapter class.
- **Fully stateless** — no database. Analysis history is a frontend concern
  (browser-side storage), out of scope here.
- **No chunking for long documents in this version.** One PDF → one Gemini
  call. Splitting/merging is a "nice to have" in the brief; skipped to protect
  the delivery deadline.
- **Scanned PDFs (no text layer) are rejected with a clear error**, not sent
  to Gemini with near-empty text. `app/services/pdf_extraction.py` marks the
  exact spot where a real OCR fallback (pdf2image + pytesseract) can be
  dropped in later without touching anything else in the pipeline.
- **Two layers of prompt-injection defense**: a hardened system prompt that
  clearly delimits the document text as data-only, plus a keyword/pattern
  heuristic (`app/core/security.py`) that rejects documents containing common
  injection phrases (English + Polish) before they ever reach Gemini.
- **Schema validation is strict on the fields we define** (ISO 8601 dates,
  real ISO 4217 currency codes, the fixed `document.type` enum) **but ignores
  any extra field** Gemini adds — an unexpected field shouldn't burn the
  brief's one allowed retry. Invalid responses get exactly one retry, then a
  clear error, per the brief's rules.

## Project structure

```
app/
  main.py                 FastAPI app, CORS, exception handlers
  config.py                Environment-driven settings (pydantic-settings)
  api/routes.py             /api/analyze, /api/health
  core/
    errors.py               Domain exceptions -> HTTP responses
    security.py              Prompt-injection heuristic
    rate_limit.py             Per-IP rate limiter (slowapi)
  services/
    pdf_extraction.py         PyMuPDF text extraction + text-layer check
    analysis.py                Orchestrates extraction -> scan -> Gemini -> validate -> retry
    llm/
      base.py                   LLMClient protocol (provider-agnostic contract)
      gemini.py                  Gemini adapter
      prompts.py                  System/user prompt templates
  schemas/analysis.py          Pydantic models for the response schema
tests/                        pytest suite
```

## Running locally

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY to a real key

uvicorn app.main:app --reload
```

The API is then available at `http://localhost:8000`, with `/api/health` and
`/api/analyze` under it.

## Environment variables

See `.env.example` for the full list with descriptions:

| Variable            | Required | Default              | Purpose                                  |
|---------------------|----------|----------------------|-------------------------------------------|
| `GEMINI_API_KEY`    | yes      | —                    | Google Gemini API key                     |
| `GEMINI_MODEL`      | no       | `gemini-2.0-flash`   | Must support JSON structured output       |
| `ALLOWED_ORIGINS`   | no       | `http://localhost:5173` | Comma-separated CORS allow-list        |
| `MAX_FILE_SIZE_MB`  | no       | `10`                 | Rejects larger uploads before parsing     |
| `RATE_LIMIT`        | no       | `10/minute`          | Per-IP limit on `/api/analyze` (slowapi)  |

## Tests

```bash
pytest
```

Covers schema validation edge cases (invalid dates/currencies, unknown
document type, extra fields being ignored), the prompt-injection heuristic,
PDF extraction (including the no-text-layer case), and the `/api/analyze`
endpoint end-to-end with a fake LLM client (success, retry-then-fail, and
rejection paths).

## Known limitations

- **Rate limiting is in-memory**, which only works correctly on a single
  backend instance/process. If this is ever deployed behind multiple
  replicas or a serverless/scale-to-zero platform, swap `app/core/rate_limit.py`
  for a Redis-backed limiter.
- **The prompt-injection scanner is a best-effort keyword/pattern heuristic**,
  not a guarantee. It catches common, lazily-phrased attempts in English and
  Polish; a sufficiently creative attacker could still phrase an injection
  attempt in a way it misses. The system prompt (which explicitly tells
  Gemini to treat the document as data, never instructions) is the primary
  defense; the scanner is a cheap second layer.
- **No OCR.** Scanned/image-only PDFs are rejected with a clear error instead
  of silently producing a low-quality or empty analysis. `pdf_extraction.py`
  documents exactly where an OCR fallback would go.
- **No chunking for very long documents.** Extremely long PDFs are sent to
  Gemini as a single request; there's no splitting/merging of partial results.
