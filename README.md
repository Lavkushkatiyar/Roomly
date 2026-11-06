# ROOMLY

ROOMLY is a browser-based, voice-first hotel concierge built around Gnani AI
speech services. Guests choose a language, speak a request, hear a response,
review a structured proposal and confirm before the application creates hotel
service-request records. It is designed to make common hotel-service
interactions more accessible than navigating forms or waiting on a phone line.

The speech experience is powered by **Gnani Prisma for speech recognition** and
**Gnani Timbre for speech generation**. A separate, replaceable reasoning
provider interprets the transcript and returns schema-validated conversation
intents and service-request proposals.

## Gnani AI-powered voice experience

**Prisma STT** receives a completed guest recording and returns transcript text.
That text is persisted as a raw input and passed to the reasoning provider.
ROOMLY sends the selected language explicitly. The app maps its Hinglish value
(`hi-en`) to Gnani's supported `hi-IN` code at the STT boundary.

**Timbre TTS** turns assistant text into spoken audio. The backend configures
`timbre-v3.0`, requests mono 48 kHz, 16-bit linear PCM in a WAV container, and
selects the `Avinash` voice for all 11 configured guest-language values.
Predefined greetings, delayed processing acknowledgements, continuation
prompts and closing messages use the same TTS route. Some scripted speech uses
inline delivery tags such as `<slow>`, `<pauses>` and `<excited>`.

The primary conversation path is:

```text
Guest microphone
      |
      v
Browser recording and WAV conversion
      |
      v
Gnani Prisma STT (/stt/v3)
      |
      v
Transcript + persisted raw input
      |
      v
Configured reasoning provider
      |
      v
Pydantic-validated conversation intent and task proposal
      |
      v
Backend confirmation validation and persistence
      |
      v
Gnani Timbre TTS (/api/v1/tts/inference)
      |
      v
Spoken response in the browser
```

The exact Prisma model version used by a deployed account is not configured in
the application request. The API response contains a `model` field; test
fixtures use `prisma-v2.5`. Verify the live provider response before describing
that fixture value as the deployed model.

## Engineering methodology

ROOMLY's voice pipeline is implemented as distinct capture, provider,
reasoning, validation, persistence and playback steps. The boundaries are
covered by automated checks rather than relying solely on a successful
end-to-end provider call.

At the documentation audit baseline, the backend suite collected **97 test
cases and all 97 passed**; these include parameterized cases and come from 66
test functions. The collected distribution was:

| Test location | Collected cases | Passed |
|---|---:|---:|
| `tests/api` | 7 | 7 |
| `tests/providers` | 14 | 14 |
| `tests/services` | 67 | 67 |
| `tests/unit` | 6 | 6 |
| `tests/test_health.py` | 3 | 3 |
| **Total** | **97** | **97** |

These are backend pytest tests, including provider/client tests and API tests;
they are not live-provider benchmarks or full browser end-to-end tests. The
frontend currently has lint and production-build checks but no test script.

Git history contained **146 commits at the pre-documentation audit baseline**
(`git rev-list --count HEAD`). This is a point-in-time count, not a claim that
the project has more than 150 commits. Incremental feature and fix commits help
keep changes traceable and make regressions easier to associate with a
specific behavior.

The GitHub Actions workflow runs on pushes and pull requests. It installs the
frontend dependencies and runs lint/build; a separate quality job provisions
PostgreSQL and runs pytest, Ruff lint/format checks and Pyright. There is no
automated deployment job in the inspected workflow. The workflow currently
selects Python 3.12, while project metadata requires Python 3.14 or newer; this
configuration mismatch should be resolved and CI success verified before
presenting the pipeline as reliably green.

Pydantic models define request and response shapes, the reasoning providers
return typed data, and backend services own database operations. The
`ReasoningProvider` protocol separates provider behavior from ingestion logic.
Gnani errors and invalid provider responses are surfaced through explicit
error paths, while conversation endpoint tests check confirmation and
conversation lifecycle behavior.

## Technology stack

| Responsibility | Technologies in the repository |
|---|---|
| Frontend | React 19, Vite, JavaScript/JSX, Axios, browser `MediaRecorder`, Web Audio API and native `Audio` playback |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, HTTPX |
| Database | PostgreSQL, SQLAlchemy ORM, Alembic migrations |
| Speech | Gnani Prisma STT and Gnani Timbre TTS |
| Reasoning | Ollama and OpenRouter adapters behind a provider protocol/factory |
| Validation | Pytest, pytest-asyncio, Respx, Ruff, Pyright |
| CI | GitHub Actions |

The frontend is JavaScript, not TypeScript. No Docker or deployment
configuration is present in the tracked repository. The active reasoning
provider is chosen through `REASONING_PROVIDER`; code defaults to Ollama
(`qwen3:8b`). OpenRouter is implemented, but should not be described as the
active provider without verifying the deployment's environment. The
OpenRouter adapter currently hard-codes
`nvidia/nemotron-3.5-super-vl:free`.

## Key capabilities

- Browser microphone capture, WAV conversion and voice submission.
- Explicit guest-language selection; no automatic language detection.
- Prisma transcription followed by typed reasoning output.
- Structured hotel-service proposals with categories, priorities and staff
  summaries.
- A confirmation-first workflow: confirmed tasks are persisted; proposals are
  not submitted merely because they were generated.
- Conversation history and pending proposal state stored through existing
  database models.
- TTS greetings, processing acknowledgements, continuation prompts and
  localized closing scripts.
- Conversation ending through the existing end intent, while pending
  proposals remain open for confirmation.

This is a browser call simulator, not a PBX, SIP or hotel telephone integration.

## Architecture overview

```mermaid
flowchart LR
    Guest[Guest in browser] --> UI[React guest-call UI]
    UI -->|WAV + language + conversation ID| API[FastAPI]
    API --> STT[Gnani Prisma]
    STT --> Transcript[Transcript]
    Transcript --> Reasoner[Configured reasoning provider]
    Reasoner --> Contract[Pydantic conversation result]
    Contract --> Workflow[Confirmation and lifecycle services]
    Workflow --> DB[(PostgreSQL)]
    Workflow --> TTS[Gnani Timbre]
    TTS -->|WAV audio| API
    API --> UI
```

## Supported languages

ROOMLY configures 11 selectable languages. Configuration does not mean each
language has been evaluated with a live speech provider.

| App language code | Guest selection | STT handling |
|---|---|---|
| `en-IN` | English | Passed through |
| `hi-IN` | Hindi | Passed through |
| `hi-en` | Hinglish | Mapped to `hi-IN` for Gnani STT |
| `ta-IN` | Tamil | Passed through |
| `te-IN` | Telugu | Passed through |
| `kn-IN` | Kannada | Passed through |
| `ml-IN` | Malayalam | Passed through |
| `mr-IN` | Marathi | Passed through |
| `bn-IN` | Bengali | Passed through |
| `gu-IN` | Gujarati | Passed through |
| `pa-IN` | Punjabi | Passed through |

The TTS voice mapping is covered by parameterized service tests for all 11
codes. STT provider tests exercise English and the Hinglish-to-Hindi mapping;
these use mocked provider responses, not live recognition-quality evaluation.
Conversation closure tests include English and Hindi. No automated test matrix
establishes live STT/TTS quality for all languages.

## Local setup

### Prerequisites

- Python 3.14 or newer, matching `pyproject.toml` and `.python-version`.
- `uv`, Node.js 22, npm, and PostgreSQL.
- A Gnani API key ID and credentials for the selected reasoning provider.
- For the default reasoning configuration: an accessible Ollama service and
  the configured model. OpenRouter can instead be selected by environment.

### Configure the backend

The root `.env.example` is empty, so create a local `.env` without committing
secrets. The settings class reads environment variables and `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/roomly
GNANI_API_KEY_ID=YOUR_GNANI_KEY_ID
REASONING_PROVIDER=ollama
REASONING_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Set `REASONING_PROVIDER=openrouter` to select the OpenRouter adapter. Never
commit real credentials. Create the PostgreSQL database, then from the
repository root:

```bash
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The CI workflow currently installs Python 3.12 despite the project declaring
Python 3.14 or newer. Local setup above follows the project metadata; CI's
Python version requires maintainer verification.

### Configure and run the frontend

`frontend/roomly/.env.example` documents the frontend backend URL variable.
Create `frontend/roomly/.env.local` with the API base URL used by the Axios
client:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/
```

Then:

```bash
cd frontend
npm ci
npm run dev
```

The backend's configured CORS origin is `http://localhost:5173`. The Vite
development server is available at that origin by default. The API docs are
available at `http://127.0.0.1:8000/docs`.

### Run validation

From the repository root:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

From `frontend/`:

```bash
npm run lint
npm run build
```

No Docker Compose or Dockerfile is present, so the repository does not provide
a Docker-based local setup.

## Detailed technical documentation

- [Gnani Prisma STT](docs/GNANI_PRISMA_STT.md)
- [Gnani Timbre TTS](docs/GNANI_TIMBRE_TTS.md)
- [Reasoning provider](docs/REASONING_PROVIDER.md)
- [System architecture](docs/SYSTEM_ARCHITECTURE.md)

## Limitations and future scope

- Prisma's exact deployed model version is returned by the provider but is not
  fixed in the STT request; verify it from a production response.
- There are no published live latency, transcription-accuracy or language
  quality benchmarks.
- The selected reasoning provider depends on runtime configuration; code
  defaults to Ollama, and OpenRouter has a hard-coded model ID.
- The CI Python version conflicts with the project's declared minimum.
- Frontend automated tests, browser end-to-end tests, and provider sandbox/live
  tests are not configured.
- The Gnani concurrency lock is process-local; multiple backend workers do not
  share a distributed request queue.
- There is no real hotel PBX/SIP integration or automated deployment pipeline.

## Verification items

- Confirm the exact Prisma model version enabled for the deployment.
- Confirm which reasoning provider and model are deployed; do not infer them
  from application defaults.
- Resolve the Python 3.12 CI versus Python 3.14 project metadata mismatch.
- Benchmark STT, reasoning and TTS latency and evaluate recognition quality
  across the configured guest languages.
