# Roomly guest voice interface

The frontend is a React JavaScript application built with Vite. Its guest
screen records audio locally in the browser; it does not send recordings to a
backend or generate a transcript.

## Development

From the `frontend` directory:

```sh
npm ci
npm run dev
```

Microphone access requires a supported browser and a secure context, such as
`localhost` or HTTPS.

The development server prints the local URL when it starts.

## Checks

From the `frontend` directory:
```sh
npm run lint
npm run build
```
