# Roomly guest voice interface

The frontend is a React JavaScript application built with Vite. It records
audio in the browser, sends it to the existing `POST /voice/ingest` endpoint,
and displays the returned transcript and proposed service tasks.

## Development

From the repository's `frontend` directory, install dependencies and start the
backend at `http://127.0.0.1:8000`. Configure the frontend before recording:

```sh
npm ci
cp roomly/.env.example roomly/.env.local
npm run dev
```

Set `VITE_ROOM_ID` in `roomly/.env.local` to the UUID of an existing hotel
room. Room UUIDs can be read from the backend's `GET /hotel_room/` endpoint.
Set `VITE_ROOM_NUMBER` to the corresponding room number shown in the header.
`VITE_GUEST_LANGUAGE` defaults to `en-IN`; the backend also supports `hi-IN`.

During development, Vite proxies `/voice` to `VITE_BACKEND_URL`, which defaults
to `http://127.0.0.1:8000`. For a deployed frontend, serve the frontend and API
behind the same origin, or configure backend CORS and set `VITE_API_BASE_URL`
to the backend origin.
Microphone access requires a supported browser and a secure context, such as
`localhost` or HTTPS.

## Checks

Run these from the `frontend` directory:

```sh
npm run lint
npm run build
```
