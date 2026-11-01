---
id: EP-20260505-001/MS004
execplan_id: EP-20260505-001
ms: 4
title: Centralize Provider Object Coercion
status: completed
domain: backend
owner: '@codex'
created: 2026-05-05
updated: '2026-05-05'
tags:
- provider-utils
- response-parser
- claude-code
risk: low
links:
  issue: ''
  docs: ''
  pr: ''
---

# Centralize Provider Object Coercion

This milestone is a living document. Keep the YAML front matter accurate as work proceeds.

## Objective

Centralize SDK/object-to-dict coercion so Claude Code response parsing follows the repository's provider architecture pattern. At the end of this milestone, Claude Code no longer owns a private `_to_dict` helper, and future providers have a shared utility for converting SDK objects into plain serializable dictionaries.

## Definition of Done

- [x] `src/agentrules/core/utils/provider_utils.py` exists with a tested `sdk_object_to_dict()` helper.
- [x] `src/agentrules/core/agents/claude_code/response_parser.py` imports and uses the shared helper.
- [x] The Claude Code response parser no longer defines a local `_to_dict`.
- [x] Tests cover dicts, mappings, dataclasses, Pydantic-style `model_dump()`, SDK-style `to_dict()` / `dict()`, and public-attribute fallback.
- [x] Existing Claude Code parser tests still pass.

## Scope

### In Scope
- Create `src/agentrules/core/utils/provider_utils.py`.
- Create `tests/unit/utils/test_provider_utils.py`.
- Update `src/agentrules/core/agents/claude_code/response_parser.py` to call the shared helper for usage dictionaries and tool input dictionaries.
- Keep output plain Python dictionaries/lists/scalars suitable for logging and serialization.
- Include defensive exception handling in the helper so an unusual SDK object cannot crash response parsing merely because one conversion method raises.

### Out of Scope
- Do not bulk-refactor every existing provider-specific `_to_dict` helper in this milestone unless it is mechanically safe and already covered by tests.
- Do not add JSON serialization or redaction behavior to this helper. Secret redaction belongs in logging filters.
- Do not change the canonical result shape returned by any provider.

## Workstreams & Tasks

- [x] Utility design: implement `sdk_object_to_dict(value: Any) -> dict[str, Any] | None` using predictable conversion order.
- [x] Parser integration: replace Claude Code local calls and delete the local helper.
- [x] Tests: add utility fixtures for each supported object shape and keep existing parser tests unchanged where possible.
- [x] Architecture note: document in the helper docstring that provider adapters should convert SDK objects to plain dicts at boundaries.

## Risks & Mitigations

- Risk: A fallback through `__dict__` may expose private SDK internals.
  Mitigation: Filter keys beginning with `_` and prefer explicit SDK/datataclass/Pydantic conversion methods first.
- Risk: Different providers may need slightly different coercion semantics.
  Mitigation: Keep the helper intentionally small and return `None` when it cannot confidently produce a dict. Providers can still handle provider-specific shapes around the shared helper.

## Validation / QA Plan

- Run `PYTHONPATH=src .venv/bin/pytest tests/unit/utils/test_provider_utils.py tests/unit/agents/test_claude_code_response_parser.py`.
- Run `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/utils/provider_utils.py src/agentrules/core/agents/claude_code/response_parser.py tests/unit/utils/test_provider_utils.py tests/unit/agents/test_claude_code_response_parser.py`.
- Run `PYTHONPATH=src .venv/bin/pyright`.
- Green means the shared helper handles all fixture shapes, Claude Code parser output is unchanged, and pyright reports no new typing errors.

## Changelog

- 2026-05-05: Milestone created.
- 2026-05-05: Drafted central provider object coercion scope from Claude Code runtime review finding 4.
- 2026-05-05: Added shared provider SDK object coercion helper, switched Claude Code parsing to it, synced snapshots, and added focused tests.

## Validation Results

- 2026-05-05: `PYTHONPATH=src .venv/bin/pytest tests/unit/utils/test_provider_utils.py tests/unit/agents/test_claude_code_response_parser.py` passed with 15 tests.
- 2026-05-05: `PYTHONPATH=src .venv/bin/ruff check src/agentrules/core/utils/provider_utils.py src/agentrules/core/agents/claude_code/response_parser.py tests/unit/utils/test_provider_utils.py tests/unit/agents/test_claude_code_response_parser.py` passed.
- 2026-05-05: `PYTHONPATH=src .venv/bin/pyright` passed with 0 errors.
- 2026-05-05: `PYTHONPATH=src .venv/bin/agentrules snapshot sync` updated `SNAPSHOT.md` for the new utility and tests.
