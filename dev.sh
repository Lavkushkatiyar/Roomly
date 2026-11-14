
#!/bin/bash

uv run uvicorn app.main:app --reload &
BACKEND_PID=$!

cd frontend
npm run dev &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null' EXIT

wait
