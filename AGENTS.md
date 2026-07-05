# Project Conventions (steering)

Single source of truth for every AI agent (Claude Code, Kiro, Codex) and human contributor.
React frontend + Django backend for a private photo/message sharing app, deployed with Docker Compose behind nginx.

## Commands

```bash
npm run dev            # run backend (Django) + frontend (React) together, from repo root
uv run pytest          # backend tests (coverage gate: 80%, enforced in CI)
npm run lint           # frontend lint (CI runs with --max-warnings=0)
npm run build          # frontend production build
uv run python manage.py runserver   # backend only
```

A single `.env` at the repo root configures backend, Docker Compose and the React dev server. Copy `.env.example` to start.

## Architecture — domain-driven layering (backend)

The backend follows a strict layered design. **Each layer has one responsibility; never skip a layer.**

| Layer | Location | Responsibility |
|---|---|---|
| Views (API) | `backend/core/views/` | HTTP only: parse request, call ONE service method, return `Response`. **Zero business logic.** |
| Services | `backend/core/services/` | ALL domain logic lives here: orchestration, rules, WebSocket broadcasts, logging. |
| Serializers | `backend/core/serializers/` | Validation and representation only. |
| Repository interfaces | `backend/core/interface/` | Abstract storage contracts (`PhotoSaverRepository`) + implementations (`AwsPhotoSaver`). |
| Models | `backend/core/models/` | Persistence schema. Keep them thin. |
| Dependencies | `backend/core/dependencies.py` | Composition root: singletons are instantiated here (`photo_repository`), selected via env vars. |
| Exceptions | `backend/core/exceptions/` | Domain exceptions (`BusinessError` subclasses) mapped to HTTP codes by `custom_exception_handler`. Raise domain exceptions from services; never return HTTP codes from a service. |
| WebSocket | `backend/core/websocket/` | Consumer, message enum (`WebSocketMessageType`), send utils. |

Rules that follow from this:
- A view that contains an `if` about domain state is a smell — move it to the service.
- New storage/back-ends (e.g. local disk instead of S3) are added by implementing the repository interface and wiring it in `dependencies.py`, never by branching inside services (Open/Closed).
- Any state change that other users should see MUST broadcast a WebSocket event from the service (`_broadcast_change` pattern, message types in `core/websocket/messages.py`, mirrored in `frontend/src/types/websockets.ts`).
- User-facing error messages are in French; code, comments and logs are in English.

## Design principles (non-negotiable)

All five SOLID principles apply to every class, plus Tell-Don't-Ask:

- **S — Single Responsibility**: every class has exactly one reason to change. If a service method grows unrelated concerns (e.g. image processing inside an upload flow), extract a dedicated module.
- **O — Open/Closed**: open for extension, closed for modification. New behavior = a new implementation behind an existing seam (interface, enum, message type), not a new `if`/`elif` branch inside working code.
- **L — Liskov Substitution**: any implementation of an interface must be usable wherever the interface is expected, without surprises. A new `PhotoSaverRepository` implementation must honor the full contract (same return types, same exceptions — raise `CloudUploadError` on failure, never a different error family or a silent `None`). If an implementation needs to weaken a precondition or skip a method, the abstraction is wrong — fix the interface, don't cheat in the subclass.
- **I — Interface Segregation**: keep interfaces small and client-focused. No class should be forced to implement methods it doesn't need. If `PhotoSaverRepository` grows methods only one caller uses, split it into focused contracts rather than fattening the ABC with `pass`/`NotImplementedError` stubs.
- **D — Dependency Inversion**: high-level code (services) depends on abstractions (`core/interface/`), never on concrete implementations (`AwsPhotoSaver`, boto3). Concretes are chosen and instantiated in one place only: `dependencies.py` (the composition root).
- **Tell, Don't Ask**: push behavior into the object that owns the data. Don't fetch an object's fields to make decisions outside it; give the object (or its service) the operation to perform.
- **Extensibility first**: when adding a feature, ask "what will the next variant of this look like?" and leave the seam (interface, enum, message type) ready for it.

## Frontend rules (React + TypeScript)

- **No business logic in the frontend.** The backend is the single source of truth: validation, permissions, computations, filtering rules all live in Django services. The frontend renders state and forwards intents.
- Server state goes through **react-query** hooks in `frontend/src/queries/` (one file per resource). Never `fetch`/`axios` directly in a component.
- Real-time sync goes through the WebSocket context (`contexts/WebSocketProvider.tsx`) with `bind`/`unbind` in custom hooks (`hooks/usePhotosWithWebSocket.ts` is the reference pattern).
- **Minimize `useEffect`.** Before writing one, prefer in order: derived values computed during render, event handlers, react-query options (`onSuccess`, `enabled`), a custom hook that already encapsulates the effect. A `useEffect` that syncs two pieces of state is a bug factory.
- Components stay presentational; anything reusable or stateful moves to `hooks/` or `services/`.
- Types live in `frontend/src/types/`; WebSocket payload interfaces in `types/websocket-interfaces.ts` must mirror the backend payloads exactly.

## Tests

Backend tests live in `backend/core/tests/`, mirroring the source tree (`tests/services/`, `tests/views/`, ...). Follow the existing patterns exactly:

- **AAA structure**: Arrange, Act, Assert — separated by blank lines, in that order, visible in every test.
- **Naming**: `test_given<Context>_when<Action>_then<Outcome>` (see `tests/interface/test_aws.py`). Match the file-local naming style when extending an existing file.
- **One reason to fail**: one behavior per test. Asserting an upload happened and the URL is correct = two tests. Multiple assertions are fine only when they describe a single behavior.
- **Isolation**: unit tests mock collaborators at the module under test (`@patch("core.services.album_service.photo_repository")`), reuse fixtures from `tests/conftest.py`, and never hit S3/SMTP/real network. View tests use `APIRequestFactory` + `force_authenticate`.
- WebSocket broadcasts are patched (`send_ws_message_to_user`, `User`) — see the `setUp` patcher pattern in `tests/services/test_album_service.py`.
- **Coverage: aim for ~100%.** The CI gate is 80%, but that is a floor, not a target. Every new function, branch and error path ships with its tests in the same change — happy path, edge cases, and failure modes (exceptions, 4xx responses, empty inputs). Untested code is treated as unfinished code. Behavior changes update the tests that enshrined the old behavior.

## Readability & naming

- Names are **impeccable or the code doesn't merge**: full words, intention-revealing, no abbreviations (`source_album_id`, not `src_id`; `handlePhotoUploaded`, not `handler1`).
- Python: PEP8 `snake_case` for new functions/methods (some legacy `camelCase` methods exist — don't imitate them in new code, don't mass-rename either).
- TypeScript: `camelCase` values, `PascalCase` components/types, hooks prefixed `use`.
- Comments explain **why**, never what the next line does. If a comment paraphrases the code, delete it and improve the names instead.
- Small functions with one job; deep nesting is a signal to extract a well-named helper.
