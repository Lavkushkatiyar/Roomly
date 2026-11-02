# Roomly guest voice interface

The frontend is a React and TypeScript application built with Vite. Its guest
screen records audio locally in the browser; it does not send recordings to a
backend or generate a transcript.

## Development

```sh
npm ci
npm run dev
```

Microphone access requires a supported browser and a secure context, such as
`localhost` or HTTPS.

## Checks

```sh
npm run typecheck
npm run lint
npm run build
```
