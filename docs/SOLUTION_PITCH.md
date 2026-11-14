# ROOMLY --- Speech Is the Interface. The Workflow Is the Product.

## Problem

Hotel guests often need to contact the front desk for routine services
or to report an issue. Traditional interactions can be inconvenient,
especially when guests are more comfortable speaking in a language other
than the hotel's default language. A voice interface alone does not
solve the operational problem: the guest's request must be understood,
validated, confirmed, and recorded correctly.

## Solution

ROOMLY is a voice-first, multilingual hotel guest-service assistant. It
lets guests speak naturally to request services or report issues, then
guides the interaction through a structured workflow so that a request
is created only after the guest confirms it.

ROOMLY is built around one principle: **Speech is the interface. The
workflow is the product.**

## Intended Users

-   **Hotel guests:** People who want a convenient, conversational way
    to request assistance or hotel services in a supported language.
-   **Hotel teams:** Staff who need guest requests captured as
    structured records rather than left as unstructured conversations.

## How ROOMLY Works

1.  A guest starts a voice interaction and speaks naturally.
2.  **Gnani Prisma** converts the guest's speech into text.
3.  The application interprets the request and prepares structured
    request details.
4.  The application validates the proposed details and presents them to
    the guest.
5.  The guest explicitly confirms or declines the request.
6.  Only a confirmed request is persisted.

This confirmation-first workflow keeps the application---not the
language model---in control of whether a service request is created.

## Gnani AI Technology

ROOMLY integrates Gnani AI speech technology:

-   **Gnani Prisma --- Speech-to-Text (STT):** Transcribes the guest's
    spoken request.
-   **Gnani Timbre --- Text-to-Speech (TTS):** Generates the assistant's
    spoken response.

The documented language experience covers English, Hindi, Kannada,
Tamil, Telugu, Bengali, Marathi, Gujarati, Punjabi, and Malayalam, with
Hinglish code-mixed speech. The exact language and voice combinations
should be understood in line with what has been verified in the running
application.

## Engineering and Differentiation

ROOMLY is a complete application built around speech technology, not
just a demonstration that connects speech APIs. It includes a React
frontend, a FastAPI backend, structured validation, PostgreSQL
persistence, Redis-backed rate limiting, Docker-based packaging, and
GitHub Actions CI.

The project was developed independently as a solo effort, with **125+
test cases** and **180+ incremental commits**. Its modular architecture,
provider abstractions, technical documentation, and deployment
instructions are intended to make the implementation understandable,
testable, and maintainable.

The central distinction is the workflow: ROOMLY turns a natural-language
guest interaction into a validated service request, while requiring
explicit guest confirmation before persistence.

------------------------------------------------------------------------

**Project:** ROOMLY\
**Gnani AI integrations:** Prisma STT and Timbre TTS\
**Development:** Solo-built
