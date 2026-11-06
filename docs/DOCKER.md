# Running ROOMLY with Docker

ROOMLY uses Docker Compose to run the FastAPI backend and the production React frontend.

The existing PostgreSQL database and reasoning provider remain external dependencies. Compose does not create a replacement database or an Ollama container.

## Prerequisites

- Docker Engine.
- Docker Compose plugin.
- A reachable PostgreSQL database with ROOMLY's migrations applied.
- A Gnani AI API key ID.
- A configured reasoning provider.

## 1. Configure environment

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `DATABASE_URL`: connection URL for the existing PostgreSQL database.
- `GNANI_API_KEY_ID`: your Gnani API key ID.
- `REASONING_PROVIDER`: `ollama` or `openrouter`.
- `REASONING_MODEL`: model identifier accepted by the selected provider.
- `OLLAMA_BASE_URL`: URL reachable from the backend container when using Ollama.
- `OPENROUTER_API_KEY`: required only when using OpenRouter.

Do not commit `.env`. The committed `.env.example` contains placeholders only.

### PostgreSQL connection

The database hostname must be reachable from inside the backend container.

If PostgreSQL runs directly on the Docker host, use `host.docker.internal` instead of `localhost` in `DATABASE_URL`. For a managed database, use the provider's connection hostname and required SSL parameters.

### Ollama on the Docker host

The Compose configuration maps `host.docker.internal` to the host gateway. On Linux, Ollama must listen on an address reachable from Docker containers.

For a host-managed Ollama service, configure its service environment with:

```bash
OLLAMA_HOST=0.0.0.0:11434
```

Restart Ollama after changing the setting, ensure the configured model is available, and keep port 11434 restricted to trusted networks.

Alternatively, configure OpenRouter in `.env`:

```dotenv
REASONING_PROVIDER=openrouter
REASONING_MODEL=your-supported-model-id
OPENROUTER_API_KEY=your-api-key
```

## 2. Build and start

```bash
docker compose up --build -d
```

The backend starts first. The frontend waits for the backend health check before starting.

## 3. Open ROOMLY

| Component | URL |
|---|---|
| Guest call interface | http://localhost:8080 |
| FastAPI documentation | http://localhost:8000/docs |
| Backend health | http://localhost:8000/health |

The frontend uses a same-origin API base URL. Nginx serves the built React application and forwards ROOMLY API routes to FastAPI.

The browser microphone requires a secure context. `localhost` is permitted for local development; public deployments must use HTTPS.

## 4. Database migrations

Migrations are intentionally not run automatically when the container starts.

After confirming the target database and reviewing pending migrations, apply them explicitly:

```bash
docker compose exec backend alembic upgrade head
```

## 5. Logs and shutdown

```bash
docker compose logs -f backend frontend
docker compose down
```

To rebuild after changing application code:

```bash
docker compose up --build -d
```

## Container design

- Backend: Python 3.14, dependencies installed from the committed `uv.lock`, non-root runtime user, and an HTTP health check.
- Frontend: Node build stage followed by a small Nginx runtime image.
- API routing: Nginx proxies the voice, conversation, hotel-room, raw-input, task-extraction, and service-request endpoints to FastAPI.
- Database: existing PostgreSQL connection supplied through `DATABASE_URL`.
- Reasoning: external Ollama or OpenRouter provider configured through environment variables.
- Secrets: supplied at runtime through the untracked `.env` file.

No credentials are copied into either image. No database schema changes are introduced by Docker packaging.
