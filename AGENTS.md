# AGENTS

A working agreement for this codebase. The goal is to ship in small, confident, testable steps while maintaining production quality. Prefer complete, usable features over throwaway MVPs or prototypes.

## Principles

- Minimal Testable Code (MTC): Ship the smallest change that can be run, verified, and used end‑to‑end by at least one real flow.
- Full implementation mindset: Aim for production‑ready behavior, not exploratory spikes. Avoid temporary hacks unless explicitly flagged.
- Iterative delivery: Break features into thin, vertical slices that each deliver user‑visible value and can be merged independently.
- Quality is non‑negotiable: Each iteration includes tests, docs, error handling, and observability appropriate to its scope.

## Minimal Testable Code (MTC)

An iteration qualifies as MTC only if it:

1. Runs end‑to‑end: A user or automated test can exercise the flow without manual patching or hidden steps.
2. Is verifiable: Has automated tests (unit and/or integration) that assert the new behavior and protect regressions.
3. Is observable: Emits useful logs/metrics/traces for new paths and errors.
4. Is documented: Includes concise notes on behavior, configs, and usage in README or inline docs.
5. Handles errors: Validates inputs, fails gracefully, and communicates actionable messages.
6. Meets baseline security: Avoids leaking secrets, enforces auth/permissions where applicable, and sanitizes inputs.

If an MTC affects UX, it must be discoverable and usable by the intended audience (or protected behind a documented feature flag).

## Full Implementation Over MVPs

When implementing features, bias toward production completeness for the chosen slice:

- No placeholder endpoints, stubbed UI, or dead code paths unless explicitly behind a feature flag and accompanied by tests and docs.
- Data integrity, migrations, and backward compatibility considered before merge.
- Performance and correctness constraints defined and measured where relevant.
- Configuration, defaults, and rollback strategy included.

“Full” does not mean “big.” Keep the slice small, but finish the slice.

## Iteration Pattern

1. Define the thin slice: one user story or system capability end‑to‑end.
2. List acceptance criteria: functional behavior, edge cases, and non‑functional needs (perf, security, observability).
3. Implement with tests first or alongside where appropriate.
4. Add instrumentation and docs.
5. Validate locally and/or in CI via automated checks.
6. Merge behind a flag if not yet broadly enabled.

## Delivery Checklist

- Code: Minimal, readable, and scoped to the slice.
- Tests: Passing unit/integration tests cover the new paths and errors.
- Docs: README or component docs updated with usage and configs.
- Observability: Logs/metrics/traces added where they aid debugging.
- Security: Secrets protected; inputs validated; least‑privilege respected.
- UX: Discoverable, accessible, and consistent with existing patterns.
- Changelog: `CHANGELOG.md` updated with user‑visible changes for this slice.
- TODOs: `todo.md` updated to mark completed tasks and link the PR/commit.

## Changelog and TODOs

- Changelog: Maintain `CHANGELOG.md` following a simple, consistent format (e.g., Keep a Changelog). For each merged slice, add entries under the appropriate version with clear sections such as Added, Changed, Fixed, Removed, and Security. Update the Unreleased section during development and move entries under a tagged version upon release.
- TODO completion: Treat `todo.md` as the source of truth for planned work. Every finished task must be marked as completed in `todo.md` in the same PR that implements it. Prefer GitHub‑style checkboxes (e.g., `- [x] Task name`) and include a brief note or link to the PR/commit for traceability. Do not silently remove items; if tasks are descoped or superseded, note the rationale.

## Non‑Goals

- MVPs for their own sake, prototypes that are not intended to ship, or speculative abstractions without a concrete, testable use.
- Large, multi‑week branches that cannot be merged independently.

## PR Expectations

- Keep PRs focused and reviewable (< ~300 LOC diff when possible).
- Include a brief description mapping code to acceptance criteria.
- Link to tests and screenshots or logs for key flows.
- Note any flags, migrations, or operational steps.

## Flags and Rollout

- Use feature flags to stage rollout when needed.
- Document default state, enablement criteria, and removal plan.
- Remove flags and dead paths promptly after stabilization.

## Ownership and Maintenance

- Owners ensure follow‑through to full completeness: docs, ops, and post‑merge cleanup.
- Leave the campsite cleaner: refactor adjacent issues only when they improve the current slice.

By following MTC with a full‑implementation mindset, we ship smaller changes faster without sacrificing reliability, usability, or maintainability.
