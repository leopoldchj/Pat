# Copilot instructions

## Project context

Personal photo/message sharing app: React + TypeScript frontend (`frontend/`),
Django + DRF backend (`backend/`), Redis for WebSockets, S3 for photo storage,
Docker Compose + nginx for deployment.

All project conventions (architecture, SOLID, test patterns, naming) live in
the root **`AGENTS.md`** — read it and follow it for any code you write,
review or describe.

## Pull request descriptions

- Always follow the structure of `.github/pull_request_template.md`: keep its
  section headings (`Summary`, `Changes`, `How it was tested`, `Checklist`,
  `Notes for reviewers`) and fill every section that applies.
- Write in English, concise and factual. Lead with what changed and why.
- Group changes by area (Backend / Frontend / Infra) when the PR spans several.
- Explicitly flag breaking changes, schema/migration changes, and anything
  requiring a deploy step (cache flush, env var, migration).
- Mention the tests that cover the change; if a section of the checklist is
  not satisfied, say so instead of checking it.

## Code review focus

- Business logic in a Django view or a React component is a violation:
  it belongs in `backend/core/services/`.
- New tests must follow AAA structure and `test_given_when_then` naming,
  with a single reason to fail per test.
- Flag any new `useEffect` that could be derived state, an event handler
  or a react-query option instead.
