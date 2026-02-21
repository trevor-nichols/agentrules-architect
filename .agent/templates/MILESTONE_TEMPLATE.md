# Milestone Template

**Instructions for Creating Milestone:**

* Base your milestone on the template shown within the `<MILESTONE_TEMPLATE>` tag.
* Create your milestone within `.agent/exec_plans/active/<short_slug>/milestones/active/`.
* When your milestone is complete, archive it in `.agent/exec_plans/active/<short_slug>/milestones/archive/`.
* Prefer CLI milestone workflow over manual file creation:
  - Create: `agentrules execplan milestone new EP-YYYYMMDD-NNN "<Milestone Title>"`
  - List: `agentrules execplan milestone list EP-YYYYMMDD-NNN` (or `--active-only`)
  - Archive: `agentrules execplan milestone archive EP-YYYYMMDD-NNN --ms <N>`
* Do not hand-pick `MS###` during creation. The CLI assigns the next monotonic sequence for that ExecPlan.

## Milestone identity and association (required)

Every milestone must be associated to exactly one ExecPlan via the canonical ExecPlan ID.

### Milestone ID

Use this exact format:

- `EP-YYYYMMDD-NNN/MS###`

Where:
- `EP-YYYYMMDD-NNN` is the parent ExecPlan ID.
- `MS###` is a per-plan sequence number, zero-padded (001–999).

Example: `EP-20260117-014/MS003`

### Filename convention

Use this exact filename format:

- `.agent/exec_plans/active/<short_slug>/milestones/active/MS###_<short-slug>.md`

Example:

- `.agent/exec_plans/active/<short_slug>/milestones/active/MS003_prototype-streaming.md`

When complete, archive to:

- `.agent/exec_plans/active/<short_slug>/milestones/archive/MS###_<short-slug>.md`

### Required YAML front matter (machine-readable)

Every milestone file must begin with YAML front matter as the very first bytes in the file, starting with `---` and ending with `---`. Keep the YAML simple: scalars and short lists only. Avoid multiline strings.

Required keys:
- `id`: `EP-YYYYMMDD-NNN/MS###`
- `execplan_id`: `EP-YYYYMMDD-NNN`
- `ms`: integer milestone sequence (e.g. 1, 2, 3)
- `title`: short milestone title
- `status`: `planned | in_progress | completed | blocked | archived`
- `domain`: `backend | frontend | console | infra | cross-cutting`
- `owner`: `@handle` (e.g. codex, claude, etc.)
- `created`: `YYYY-MM-DD`
- `updated`: `YYYY-MM-DD` (bump when materially revised)

Optional keys:
- `tags`: list
- `risk`: `low | med | high`
- `links`: map with keys like `issue`, `docs`, `pr`

<MILESTONE_TEMPLATE>
```md
---
id: EP-YYYYMMDD-NNN/MS###
execplan_id: EP-YYYYMMDD-NNN
ms: 1
title: "<Milestone: Short Name>"
status: planned
domain: backend
owner: "@handle-or-team"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
risk: low
links:
  issue: ""
  docs: ""
  pr: ""
---

<!-- SECTION: Metadata -->
# <Milestone: Short Name>

This milestone is a living document. Keep the YAML front matter accurate. Whenever you materially change the milestone content, update `updated` and add a note in `Changelog`.

---

<!-- SECTION: Objective -->
## Objective

1–3 sentences on what this milestone is supposed to accomplish.
Keep it outcome-focused ("what changes in the world when this is done"), not a task list.

---

<!-- SECTION: Definition of Done -->
## Definition of Done

Bullet list of concrete, verifiable end state:

- …
- …
- `hatch run lint` / `pnpm type-check` / tests all pass (or the project’s equivalent)
- Any new/changed run instructions are documented
- Milestone status is updated to `completed` (and then archived when appropriate)

---

<!-- SECTION: Scope -->
## Scope

### In Scope
- …

### Out of Scope
- …

---

<!-- SECTION: Current Health Snapshot -->
## Current Health Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Architecture/design | ✅ / ⚠️ / ⏳ | … |
| Implementation | ✅ / ⚠️ / ⏳ | … |
| Tests & QA | ✅ / ⚠️ / ⏳ | … |
| Docs & runbooks | ✅ / ⚠️ / ⏳ | … |

---

<!-- SECTION: Architecture / Design -->
## Architecture / Design Snapshot

Short summary of the important decisions + links. For example:

- Key decisions (algos, patterns, boundaries, provider choices).
- New modules / packages / tables introduced.
- How this plugs into existing services/agents/console.

If there’s a full design doc, summarize it here and link it in YAML `links` (or inline here if needed).

---

<!-- SECTION: Smoke Philosophy (optional) -->
## Smoke Philosophy (Optional)

Use this section when a milestone changes or expands smoke tests. Keep it short and action-oriented:

- Smoke tests are shallow, fast, end-to-end checks for service wiring and happy paths.
- Streaming/SSE smoke should verify connection + first event + clean termination only; contract shape is covered elsewhere.
- Provider-dependent smoke tests are gated behind explicit env flags; default CI stays deterministic.
- Prefer deterministic fixtures for baseline state; use public APIs to create/clean up when those APIs are in scope.

---

<!-- SECTION: Workstreams & Tasks -->
## Workstreams & Tasks

Top-level workstreams, each with its own mini checklist.

### Workstream A – <Name>

| ID | Area | Description | Status |
|----|------|-------------|-------|
| A1 | API | … | ✅ / ⏳ / ⚠️ |
| A2 | Tests | … | ✅ / ⏳ / ⚠️ |

### Workstream B – <Name>

(same table)

---

<!-- SECTION: Phases (optional if simple) -->
## Phases

Use when the milestone is multi-stage.

| Phase | Scope | Exit Criteria | Status |
| ----- | ----- | ------------- | ------ |
| P0 – Alignment | … | … | ✅ / ⏳ / ⚠️ |
| P1 – Impl | … | … | ✅ / ⏳ / ⚠️ |

---

<!-- SECTION: Dependencies -->
## Dependencies

- Other milestones / issues that must land first.
- External systems (Stripe, Vault, Redis, etc.).
- Link dependencies in YAML `links` when possible.

---

<!-- SECTION: Risks -->
## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| … | Low/Med/High | … |
| … | … | … |

---

<!-- SECTION: Validation / QA Plan -->
## Validation / QA Plan

- Commands to run (`hatch run lint`, `pytest …`, `pnpm lint`, `pnpm type-check`, Playwright, etc.).
- Any smoke tests or manual checks.
- What "green" looks like.
- If this milestone changes behavior, include a short before/after check that a human can verify.

---

<!-- SECTION: Deferred / Follow-ups (optional) -->
## Deferred / Follow-ups (Optional)

Use this section when non-blocking items are explicitly deferred:

- Known test failures to revisit later.
- Follow-on refactors that are out of scope for this milestone.
- Operational gaps to close post-merge.

---

<!-- SECTION: Rollout / Ops Notes -->
## Rollout / Ops Notes

- How this is enabled/rolled out (flags, envs, console commands).
- Migration steps, backfill, or one-time scripts.
- Rollback considerations.

---

<!-- SECTION: Changelog -->
## Changelog

- YYYY-MM-DD — Short note on what changed and why.
- YYYY-MM-DD — …
````

</MILESTONE_TEMPLATE>
