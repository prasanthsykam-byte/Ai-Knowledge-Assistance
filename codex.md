# AI Knowledge Assistance — Codex

## Purpose

This codex documents conventions, principles, and practical rules for the "AI Knowledge Assistance" project. It exists to keep design decisions consistent, make contributions straightforward, and ensure safe, reproducible behavior.

## Vision

Build a reliable, privacy-conscious assistant that helps users find, summarize, and act on knowledge from structured and unstructured sources.

## Principles

- User-first: prioritize clarity, relevance, and control for users.
- Safety and privacy: minimize data exposure and follow least privilege for any stored data.
- Reproducibility: prefer deterministic processing pipelines and clear versioning for models and data.
- Simplicity: favor small, testable modules over complex monoliths.

## Repo Structure (high level)

- `server.js`: main server entry.
- `public/`: front-end static assets (`index.html`, `app.js`, `styles.css`).
- `data/`: dataset, indexes, or cached knowledge artifacts.
- `codex.md`: this file — project conventions and policies.

Adjustments to structure should be documented in PR descriptions.

## Contribution Guidelines

- Open issues for significant changes or new features.
- Small fixes can be opened as PRs directly against `main` (or `develop` if used).
- Include tests for non-trivial logic and update docs when behaviors change.

PR checklist:
- Clear title and description.
- Reference relevant issue(s).
- Include short manual test steps or automated tests.
- Verify linting and formatting pass.

## Coding Standards

- JavaScript / Node:
  - Use ES2019+ features where supported by target Node.js.
  - Prefer descriptive names; avoid single-letter vars unless conventional.
  - Keep functions small and focused.
  - Use promises/async-await; avoid callback pyramids.

- Frontend:
  - Keep UI code modular; separate DOM concerns from state and data fetching.

- Formatting:
  - Use a consistent formatter (Prettier recommended). Follow existing project style.

## Commit Messages

- Use imperative style: "Add", "Fix", "Refactor".
- Prefix with area when helpful: `server:`, `ui:`, `data:`.
- Keep body concise; reference issues when applicable.

## Branching & Releases

- Use feature branches for non-trivial work: `feature/xxx`, `fix/yyy`.
- Keep `main` stable; open a PR to merge into `main`.

## Testing

- Unit tests for core logic (parsers, transformers, ranking).
- Integration tests for important paths (end-to-end query→response flow).
- Manual test notes should be provided for UI changes.

## Security & Privacy

- Do not store user-provided secrets, credentials, or raw PII in `data/` or logs.
- Mask or redact sensitive fields before logging or persisting.
- Follow applicable data retention and deletion policies; delete ephemeral data promptly.

## Data Handling

- Keep raw source datasets separate from derived indexes (e.g., embeddings, vector stores).
- Record provenance: source name, snapshot timestamp, and transformation steps.

## Model Usage & Inference

- Pin model versions where reproducibility matters. Document model provider and version.
- Prefer server-side inference for sensitive data; if client-side inference is used, document risk and mitigations.

## API Design

- Keep endpoints small and predictable.
- Favor JSON-based contracts with explicit schemas.
- Validate inputs and return clear error codes/messages.

## Deployment

- Document deployment steps in `README.md` or a `DEPLOY.md`.
- Prefer environment-driven configuration; secrets must be injected via environment variables or secret managers.

## Observability

- Log actionable events (warnings, errors, high-latency responses).
- Avoid logging raw user content unless explicitly required; if logged, redact sensitive parts.

## Licensing & Attribution

- Respect upstream licenses for third-party code and models.
- Add attribution where required by provider terms.

## Glossary

- Assistant: the application helping users discover knowledge.
- Index: derived structure (embedding store, search index) built from source data.

## Contacts

For architectural questions, open an issue or contact the primary maintainers listed in `README.md`.

## Iteration & Evolution

This codex is a living document. Propose changes by opening a PR and referencing the rationale. Keep entries concise and actionable.
