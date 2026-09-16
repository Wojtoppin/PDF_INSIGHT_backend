# Local development

This covers everything for working on the backend day-to-day: setup, running
it two different ways, testing, and the specific problems you're likely to
hit (all of them things that actually came up while building this).

## Prerequisites

- **Python 3.10 or newer.** The code uses `str | None` union syntax
  (PEP 604), which doesn't parse on Python 3.9. On macOS, the system
  `python3` from Xcode Command Line Tools is often 3.9 — check before
  creating a venv:

  ```bash
  python3 --version
  ```

  If it's below 3.10, install a newer one via Homebrew rather than fighting
  the system interpreter:

  ```bash
  brew install python@3.12
  /opt/homebrew/bin/python3.12 -m venv .venv
  ```

- **Docker Desktop**, only if you want to test the container locally (see
  below). Not required for day-to-day `uvicorn --reload` development.
- **A real Gemini API key** for anything that actually calls the model —
  get one at https://aistudio.google.com/apikey. Schema/extraction/security
  tests don't need one (see [Tests](#tests)).

## Setup

```bash
python3 -m venv .venv          # use the 3.10+ interpreter from above
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# edit .env: set GEMINI_API_KEY to a real key
```

## Running the dev server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

- API at `http://localhost:8000`, interactive docs (Swagger UI) at
  `http://localhost:8000/docs` — the easiest way to manually try
  `/api/analyze` with a real PDF without writing curl commands.
- `--reload` watches `.py` files and restarts automatically. It does **not**
  watch `.env` — if you change an env var, restart the process manually
  (Ctrl+C, rerun) to pick it up.

Manual smoke test from the command line instead of `/docs`:

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/some.pdf"
```

## Running it in Docker (matches production)

Useful for verifying anything platform-specific before deploying — e.g. this
is exactly how the `$PORT` behavior described below was caught.

```bash
docker build -t pdf-insight-backend:dev .

# Railway (and most PaaS platforms) inject $PORT at runtime instead of
# letting you pick a fixed port, so test with that in mind:
docker run --rm -p 9000:9000 \
  -e PORT=9000 \
  -e GEMINI_API_KEY="$(grep '^GEMINI_API_KEY=' .env | cut -d= -f2-)" \
  -e GEMINI_MODEL=gemini-3.6-flash \
  pdf-insight-backend:dev

curl http://localhost:9000/api/health
```

## Tests

```bash
source .venv/bin/activate
pytest
```

The suite doesn't call the real Gemini API — `tests/test_analyze_endpoint.py`
overrides the `LLMClient` dependency with a fake, so it runs fully offline
and deterministically. `tests/conftest.py` sets a dummy `GEMINI_API_KEY` for
this reason; you don't need a real key just to run `pytest`.

## Troubleshooting

**`TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`**
during test collection or app startup — you're running on Python 3.9. See
[Prerequisites](#prerequisites); recreate the venv with 3.10+.

**`404 NOT_FOUND ... This model models/X is no longer available`** from
Gemini — the model name in `GEMINI_MODEL` (`.env` or your deploy platform's
env vars) has been retired. Google's error message usually names the
replacement directly; update `GEMINI_MODEL` in both `.env` and
`app/config.py`'s default, and in `.env.example`.

**`503 UNAVAILABLE ... currently experiencing high demand`** from Gemini —
transient upstream overload, not a bug. The app already retries once
automatically (`app/services/analysis.py`); if it fails twice in a row you'll
get a clean `502` instead of a crash. Just retry the request.

**Docker build/run fails with `failed to connect to the docker API`** —
Docker Desktop isn't running. Start it, then retry.

**CORS errors in the browser console when calling from a local frontend** —
`ALLOWED_ORIGINS` in `.env` must exactly match the frontend's origin
(scheme + host + port, no path). `http://localhost:5173` and
`http://127.0.0.1:5173` are different origins as far as CORS is concerned.
