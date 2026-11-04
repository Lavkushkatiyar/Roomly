# Roomly guest voice interface

The frontend is a React JavaScript application built with Vite. Guests enter a
room number and preferred language on the welcome screen. Roomly reuses an
existing room or creates it through `POST /hotel_room/`, then saves its room ID
and selected language in browser local storage for the active guest session.
The voice flow records audio, sends it to `POST /voice/ingest`, and displays
the returned transcript and proposed service tasks.

The welcome screen offers English (`en-IN`), Hindi (`hi-IN`), Hinglish
(`hi-en`), Tamil (`ta-IN`), Telugu (`te-IN`), Kannada (`kn-IN`), Malayalam
(`ml-IN`), Marathi (`mr-IN`), Bengali (`bn-IN`), Gujarati (`gu-IN`), and
Punjabi (`pa-IN`).

## Development

From the repository's `frontend` directory, install dependencies and start the
backend at `http://127.0.0.1:8000`. Configure the frontend before recording:

```sh
npm ci
cp roomly/.env.example roomly/.env.local
npm run dev
```

During development, Vite proxies `/voice` to `VITE_BACKEND_URL`, which defaults
to `http://127.0.0.1:8000`, along with the room, request, and speech endpoints.
For a deployed frontend, serve the frontend and API behind the same origin, or
configure backend CORS and set `VITE_API_BASE_URL` to the backend origin.
Microphone access requires a supported browser and a secure context, such as
`localhost` or HTTPS.

## Checks

Run these from the `frontend` directory:

```sh
npm run lint
npm run build
```
