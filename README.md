
# ROOMLY — AI Voice-First Hotel Concierge

**A multilingual, voice-first hotel concierge powered by Gnani AI.**

## Problem Statement

Hotel guests often have to call reception, navigate phone menus, or wait for staff to get basic information or request assistance. Language barriers and unclear communication can make this process even more difficult.

**ROOMLY** solves this by providing a voice-based AI concierge that lets guests ask questions and request hotel services in their preferred language. Guests can speak naturally to report issues, request amenities, or get information about hotel facilities.

**No service request is created without the guest's explicit confirmation.**


# Gnani AI — Powering the Voice Experience

Gnani AI powers ROOMLY's voice interaction through two technologies:

- **Gnani Prisma (STT):** Converts guest speech into text.
- **Gnani Timbre (TTS):** Converts assistant responses into spoken audio.

A separate reasoning provider handles conversation understanding and service-request generation.

## Gnani Prisma — Speech-to-Text

ROOMLY captures guest audio and sends it to Prisma for transcription. The resulting text is passed to the reasoning layer.

| Configuration         | Version / Value |
| --------------------- | --------------- |
| Product               | Gnani Prisma    |
| Product documentation | v3.0            |
|

**Version note:** The `/stt/v3` endpoint does not confirm the runtime model version. ROOMLY uses the model reported by the provider; the current test fixture contains `prisma-v2.5`.

**Official documentation:** [Prisma v3.0 — Product](https://www.gnani.ai/resources/prisma-v3) · [STT API Reference](https://docs.gnani.ai/api/STT/speech-to-text)

## Gnani Timbre — Text-to-Speech

Timbre converts ROOMLY's responses into audio played directly to the guest.

| Configuration        | Version / Value         |
| -------------------- | ----------------------- |
| Product              | Gnani Timbre            |
| Configured model     | `timbre-v3.0`           |
| Voice                | `Avinash`               |



# Supported Languages

ROOMLY configures 11 selectable guest-language values.

| Application code | Guest language | STT handling |
|---|---|---|
| `en-IN` | English | Passed through |
| `hi-IN` | Hindi | Passed through |
| `hi-en` | Hinglish | Mapped to `hi-IN` |
| `ta-IN` | Tamil | Passed through |
| `te-IN` | Telugu | Passed through |
| `kn-IN` | Kannada | Passed through |
| `ml-IN` | Malayalam | Passed through |
| `mr-IN` | Marathi | Passed through |
| `bn-IN` | Bengali | Passed through |
| `gu-IN` | Gujarati | Passed through |
| `pa-IN` | Punjabi | Passed through |


The Avinash voice is mapped across all 11 configured guest-language values and covered by parameterized service tests.

**Official documentation:** [Timbre v3.0 — Product](https://www.gnani.ai/resources/timbre-v3) · [TTS API Reference](https://docs.gnani.ai/api/TTS/tts-inference)



## System Architecture

```mermaid
flowchart TB
    Guest(["Guest"])
    subgraph Frontend["Frontend · React 19"]
        UI["Guest Call Interface"]
        Mic["Microphone Capture"]
        Player["Audio Playback"]
    end

    subgraph Backend["Backend · FastAPI"]
        API["REST API"]
        STTService["Speech Recognition Service"]
        Conversation["Conversation Service"]
        Validation["Pydantic Validation"]
        Workflow["Confirmation & Task Workflow"]
        TTSService["Speech Generation Service"]
    end

    subgraph AI["AI Providers"]
        Prisma["Gnani Prisma · STT"]
        Reasoning["Ollama / OpenRouter · Reasoning"]
        Timbre["Gnani Timbre · TTS"]
    end

    DB[("PostgreSQL")]

    Guest --> UI
    UI --> Mic
    Mic --> API
    API --> STTService
    STTService <--> Prisma
    STTService --> Conversation
    Conversation <--> Reasoning
    Conversation --> Validation
    Validation --> Workflow
    Workflow <--> DB
    Workflow --> TTSService
    TTSService <--> Timbre
    TTSService --> API
    API --> Player
    Player --> Guest

    classDef gnani fill:#fff0e6,stroke:#d97706,color:#7c2d12
    classDef backend fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef frontend fill:#f3e8ff,stroke:#9333ea,color:#581c87
    classDef storage fill:#dcfce7,stroke:#16a34a,color:#14532d

    class Prisma,Timbre gnani
    class API,STTService,Conversation,Validation,Workflow,TTSService backend
    class UI,Mic,Player frontend
    class DB storage
```

## Technology

⚛️ React 19 · ⚡ Vite · 🐍 Python · 🚀 FastAPI · 📦 Pydantic · 🗄️ PostgreSQL · 🧠 Ollama / OpenRouter · 🎙️ Gnani Prisma · 🔊 Gnani Timbre · 🧪 Pytest · 🛠️ Ruff · 🔄 GitHub Actions


## Engineering Approach

ROOMLY is developed incrementally, with clear service boundaries and automated validation.

- Provider integrations are separated from application logic.
- Pydantic models define structured data contracts.
- Service and API behavior is covered by pytest.
- Ruff and Pyright support code quality.
- GitHub Actions validates frontend and backend changes.

## Documentation

| Document | Description |
|---|---|
| [Technical Guide](docs/TECHNICAL_GUIDE.md) | Technology stack, versions, architecture, setup, testing, and development workflow. |
| [Gnani Prisma STT](docs/GNANI_PRISMA_STT.md) | Prisma integration, API configuration, audio processing, and language mapping. |
| [Gnani Timbre TTS](docs/GNANI_TIMBRE_TTS.md) | Timbre integration, model configuration, voice selection, and audio output. |
| [Reasoning Provider](docs/REASONING_PROVIDER.md) | Provider abstraction, Ollama, OpenRouter, and structured AI responses. |
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | Application layers, request lifecycle, data flow, and service boundaries. |


## Project Scope

ROOMLY currently provides a browser-based hotel concierge call simulator. It does not implement PBX, SIP, or direct hotel telephone-system integration.

A service request is persisted only after the guest explicitly confirms the proposal.



# ROOMLY — Technical Guide

This document describes ROOMLY's architecture, technology choices, provider integrations, implementation details, development setup, and engineering practices.

For the project overview, see the root [README](../README.md).

# 1. Technology Stack and Versions

## 1.1 Application stack

| Layer | Technology | Version / configuration |
|---|---|---|
| Frontend framework | React | 19 |
| Frontend build tool | Vite | Project lockfile |
| Frontend language | JavaScript / JSX | ES modules |
| HTTP client | Axios | Project lockfile |
| Browser audio capture | MediaRecorder API | Browser-provided |
| Browser audio processing | Web Audio API | Browser-provided |
| Backend language | Python | 3.14 or newer, per project metadata |
| Backend framework | FastAPI | Project dependency |
| Data validation | Pydantic | Project dependency |
| ORM | SQLAlchemy | Project dependency |
| HTTP client | HTTPX | Project dependency |
| Database | PostgreSQL | Configured database |
| Database migrations | Alembic | Project dependency |
| STT | Gnani Prisma | `/stt/v3` endpoint |
| TTS | Gnani Timbre | `timbre-v3.0` configured |
| Reasoning | Ollama | Default model: `qwen3:8b` |
| Alternative reasoning | OpenRouter | Implemented adapter |
| Backend testing | Pytest | Project dependency |
| Async testing | pytest-asyncio | Project dependency |
| HTTP mocking | Respx | Project dependency |
| Linting | Ruff | Project dependency |
| Type checking | Pyright | Project dependency |
| CI | GitHub Actions | Workflow configuration |

**Version policy:** Where an exact dependency version is not explicitly established here, consult `pyproject.toml`, `uv.lock`, `package.json`, and `package-lock.json`. Do not infer a dependency version from the framework name alone.

# 2. Gnani AI Integrations

Gnani AI provides the speech recognition and speech generation capabilities used by ROOMLY.

The reasoning provider is a separate component. It receives transcribed text and generates structured conversation results.

## 2.1 Gnani Prisma — Speech-to-Text

**Purpose:** Convert guest audio into a text transcript.

### Product and integration versions

| Item | Value |
|---|---|
| Product | Gnani Prisma |
| Gnani product documentation | Prisma v3.0 |
| ROOMLY API endpoint | `/stt/v3` |
| Runtime model version | Returned by the provider in its response |
| Current test fixture model value | `prisma-v2.5` |
| Language selection | Explicit language code |
| Hinglish mapping | `hi-en` → `hi-IN` |

**Version clarification**

ROOMLY uses the `/stt/v3` API route. The route version does not independently prove that the deployed model is Prisma v3.0.

The provider response contains a model field. The current test fixture uses `prisma-v2.5`. Verify the model returned by a live provider response before claiming a specific deployed model version.

### Official documentation

- [Prisma v3.0 — Product page](https://www.gnani.ai/resources/prisma-v3)
- [Speech-to-Text API reference](https://docs.gnani.ai/api/STT/speech-to-text)
- [Gnani API introduction](https://docs.gnani.ai/api/introduction/introduction)

### Processing flow

1. The guest records speech through the browser.
2. The frontend submits the recording to the backend.
3. The backend prepares the audio in the required format.
4. The STT service sends the audio and language information to Gnani.
5. Prisma returns a transcription response.
6. ROOMLY extracts the transcript and passes it to the conversation service.

### Language handling

ROOMLY uses explicit guest-language selection rather than automatic language detection.

The application maps Hinglish (`hi-en`) to `hi-IN` for STT because the provider integration uses the Hindi language code for that selection.

STT tests currently exercise English and Hinglish mapping using mocked provider responses. They do not establish live transcription quality across all 11 configured languages.

## 2.2 Gnani Timbre — Text-to-Speech

**Purpose:** Convert assistant responses into spoken audio.

### Product and integration versions

| Item | Value |
|---|---|
| Product | Gnani Timbre |
| Configured model | `timbre-v3.0` |
| Configured voice | `Avinash` |
| Configured guest-language values | 11 |
| API endpoint | `/api/v1/tts/inference` |
| Audio channel | Mono |
| Sample rate | 48 kHz |
| Sample format | 16-bit linear PCM |
| Audio container | WAV |

ROOMLY uses the Avinash voice across all 11 configured guest-language values. Voice selection is covered by parameterized service tests.

### Official documentation

- [Timbre v3.0 — Product page](https://www.gnani.ai/resources/timbre-v3)
- [Text-to-Speech API reference](https://docs.gnani.ai/api/TTS/tts-inference)
- [Gnani API introduction](https://docs.gnani.ai/api/introduction/introduction)

### Speech generation flow

1. The conversation service generates the response text.
2. The TTS service selects the configured voice and language mapping.
3. The backend sends the text and audio configuration to Gnani Timbre.
4. Timbre generates audio.
5. The backend returns the generated audio to the frontend.
6. The browser plays the audio to the guest.

### Audio configuration

The current implementation configures:

- Mono audio.
- 48 kHz sample rate.
- 16-bit linear PCM.
- WAV audio output.

Some scripted responses include inline delivery tags such as `<slow>`, `<pauses>`, and `<excited>`.

**Version note:** The application configures `timbre-v3.0`. The API documentation may contain examples for earlier versions. The configured application request is the source of truth for ROOMLY's integration.

# 3. Reasoning Provider Architecture

ROOMLY separates speech processing from conversation reasoning.

The reasoning layer receives the transcript and determines what the guest wants, what the assistant should say, and whether a service-request proposal should be created.

## 3.1 Provider abstraction

The application uses a provider protocol and factory to separate reasoning-provider selection from the rest of the application.

Current providers:

| Provider | Role | Configuration |
|---|---|---|
| Ollama | Default local reasoning provider | `qwen3:8b` |
| OpenRouter | Alternative hosted reasoning provider | Implemented adapter |

The active provider is selected through `REASONING_PROVIDER`.

The application defaults to Ollama. OpenRouter is implemented, but its presence in the codebase does not mean it is the active deployment provider.

The current OpenRouter adapter uses the model ID `nvidia/nemotron-3.5-super-vl:free`.

## 3.2 Structured reasoning output

The reasoning layer returns structured data that is validated using Pydantic schemas.

This keeps the conversation service from relying on arbitrary unvalidated text for application decisions.

The structured result supports:

- Assistant response text.
- Conversation intent.
- Service-request proposal data.
- Task category and priority.
- Follow-up and closing behavior.

# 4. Application Architecture

## 4.1 High-level architecture

```mermaid
flowchart TB
    Guest(["Hotel Guest"])

    subgraph Client["Frontend"]
        UI["React Guest Call UI"]
        Capture["MediaRecorder"]
        Playback["Audio Playback"]
    end

    subgraph API["FastAPI Backend"]
        Routes["API Routes"]
        Input["Input Processing"]
        STT["STT Service"]
        Conversation["Conversation Service"]
        ProviderFactory["Reasoning Provider Factory"]
        Schemas["Pydantic Schemas"]
        TaskService["Task / Confirmation Services"]
        TTS["TTS Service"]
    end

    subgraph External["External AI Providers"]
        Prisma["Gnani Prisma"]
        Ollama["Ollama"]
        OpenRouter["OpenRouter"]
        Timbre["Gnani Timbre"]
    end

    Database[("PostgreSQL")]

    Guest --> UI
    UI --> Capture
    Capture --> Routes
    Routes --> Input
    Input --> STT
    STT <--> Prisma
    STT --> Conversation
    Conversation --> ProviderFactory
    ProviderFactory <--> Ollama
    ProviderFactory <--> OpenRouter
    Conversation --> Schemas
    Schemas --> TaskService
    TaskService <--> Database
    TaskService --> TTS
    TTS <--> Timbre
    TTS --> Routes
    Routes --> Playback
    Playback --> Guest
```

## 4.2 Main application layers

| Layer | Responsibility |
|---|---|
| Frontend | Guest interaction, audio capture, playback, and conversation state |
| API | HTTP endpoints and request/response handling |
| Input processing | Audio and guest input handling |
| STT service | Speech recognition provider integration |
| Conversation service | Conversation orchestration and reasoning |
| Provider factory | Reasoning-provider selection |
| Pydantic schemas | Input and output validation |
| Task services | Proposal confirmation and persistence |
| TTS service | Speech generation |
| Database | Conversation and service-request persistence |

## 4.3 Conversation lifecycle

```mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Greeting: Guest enters call
    Greeting --> Listening
    Listening --> Transcribing: Guest submits audio
    Transcribing --> Reasoning: Transcript available
    Reasoning --> Speaking: Assistant response generated
    Speaking --> Listening: Continue conversation
    Speaking --> PendingConfirmation: Proposal generated
    PendingConfirmation --> Persisted: Guest confirms
    PendingConfirmation --> Listening: Guest rejects or modifies
    Persisted --> Listening: Continue conversation
    Speaking --> Ended: End intent
    Listening --> Ended: Guest ends call
    Ended --> [*]
```

A service proposal is not persisted merely because the reasoning layer generated it. The guest must explicitly confirm it.

# 5. Supported Languages

ROOMLY configures 11 selectable guest-language values.

| Application code | Guest language | STT handling |
|---|---|---|
| `en-IN` | English | Passed through |
| `hi-IN` | Hindi | Passed through |
| `hi-en` | Hinglish | Mapped to `hi-IN` |
| `ta-IN` | Tamil | Passed through |
| `te-IN` | Telugu | Passed through |
| `kn-IN` | Kannada | Passed through |
| `ml-IN` | Malayalam | Passed through |
| `mr-IN` | Marathi | Passed through |
| `bn-IN` | Bengali | Passed through |
| `gu-IN` | Gujarati | Passed through |
| `pa-IN` | Punjabi | Passed through |

The TTS voice mapping is tested for all 11 configured codes.

These configuration and test results should not be interpreted as a complete live evaluation of speech recognition and speech generation quality in every language.

Automatic language detection is not implemented. The guest selects the language explicitly.

# 6. Local Development Setup

## 6.1 Prerequisites

Install the following:

- Python 3.14 or newer, as required by project metadata.
- `uv`.
- Node.js 22 and npm.
- PostgreSQL.
- Gnani API credentials.
- Credentials for the selected reasoning provider.

For the default reasoning configuration, Ollama must be running and the configured model must be available.

## 6.2 Backend environment

Create a `.env` file in the repository root.

The root `.env.example` is currently empty, so configure the required settings using the application's settings definitions.

Example configuration:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/roomly

GNANI_API_KEY_ID=YOUR_GNANI_KEY_ID

REASONING_PROVIDER=ollama
REASONING_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434

OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Use the environment variable names expected by the actual settings class. Do not commit credentials.

## 6.3 Database setup

Create the PostgreSQL database before starting the backend.

Install dependencies and apply migrations:

```bash
uv sync --locked
uv run alembic upgrade head
```

## 6.4 Start the backend

From the repository root:

```bash
uv run uvicorn app.main:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## 6.5 Frontend setup

Create `frontend/roomly/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/
```

Install and start:

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server uses:

```text
http://localhost:5173
```

The backend CORS configuration currently allows this origin.

## 6.6 Run validation

Backend:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Frontend:

```bash
npm run lint
npm run build
```

# 7. Testing and Engineering Methodology

ROOMLY uses automated tests to validate provider behavior, service logic, API behavior, and conversation workflows.

## 7.1 Backend test baseline

The documentation audit baseline collected 97 test cases, all passing.

| Test location | Cases | Passed |
|---|---:|---:|
| `tests/api` | 7 | 7 |
| `tests/providers` | 14 | 14 |
| `tests/services` | 67 | 67 |
| `tests/unit` | 6 | 6 |
| `tests/test_health.py` | 3 | 3 |
| **Total** | **97** | **97** |

These cases came from 66 test functions. Parameterized tests account for the difference between test functions and collected cases.

This is a historical audit baseline. Re-run the suite before publishing a current test count.

## 7.2 Test tooling

| Tool | Purpose |
|---|---|
| Pytest | Backend test execution |
| pytest-asyncio | Async test support |
| Respx | HTTPX request mocking |
| Ruff | Linting and formatting |
| Pyright | Static type checking |

Provider tests using mocked responses validate application behavior and request construction. They do not replace live provider tests or performance measurements.

## 7.3 Git and incremental development

The Git history contained 146 commits at the pre-documentation audit baseline.

To obtain the current count:

```bash
git rev-list --count HEAD
```

Development is organized around incremental feature, refactoring, and bug-fix commits. This keeps changes traceable and supports focused reviews.

## 7.4 Continuous integration

The GitHub Actions workflow runs on pushes and pull requests.

| Area | Checks |
|---|---|
| Frontend | Dependency installation, lint, production build |
| Backend | PostgreSQL service, pytest |
| Python quality | Ruff lint, Ruff format check, Pyright |
| Trigger | Push and pull request |

**Known CI issue:** The inspected workflow selects Python 3.12, while project metadata requires Python 3.14 or newer. Align these versions before relying on the workflow as a consistent validation environment.

The inspected workflow performs CI validation. It does not include an automated deployment job.

# 8. Important Implementation Decisions

## 8.1 Explicit language selection

The guest chooses a language before speaking. ROOMLY passes the corresponding language value through its speech-processing flow.

This is not automatic language detection.

## 8.2 Confirmation before persistence

A generated proposal is not treated as a completed service request.

The guest must confirm the proposal before the backend persists it. Rejected or modified proposals follow the conversation workflow rather than being silently submitted.

## 8.3 Separate speech and reasoning providers

Gnani Prisma and Timbre handle speech recognition and speech generation.

Ollama and OpenRouter handle reasoning. Keeping these responsibilities separate makes it possible to change the reasoning provider without coupling it to the speech integration.

## 8.4 Provider error handling

Provider interactions are separated from business logic. Provider failures, invalid responses, and request-level errors are handled through explicit service boundaries.

## 8.5 Serialized Gnani requests

The current implementation serializes Gnani requests and includes retry handling for rate-limit responses. The concurrency lock is process-local, not a distributed lock shared by multiple backend workers.

# 9. Current Limitations

- The exact deployed Prisma model version must be verified from a live provider response.
- No complete live language-quality evaluation is available for all 11 configured languages.
- No published end-to-end latency benchmark is available.
- The active reasoning provider depends on runtime configuration.
- The OpenRouter adapter currently uses a hard-coded model ID.
- Frontend automated tests and browser end-to-end tests are not configured.
- The inspected GitHub Actions workflow has a Python-version mismatch.
- The inspected workflow does not perform automated deployment.
- No Dockerfile or Docker Compose configuration is present in the tracked repository.
- The Gnani request lock is process-local.
- ROOMLY is a browser call simulator, not a PBX/SIP or hotel telephone-system integration.


