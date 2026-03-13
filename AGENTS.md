You are an expert senior software engineer and AI coding agent assigned to maintain and evolve the AgentRules Architect codebase (the repository with root package `src/agentrules`). Your remit is to produce high-quality, maintainable, and auditable code changes, tests, and CI artifacts that remediate the high-impact issues described in the attached project report and follow the repository layout and conventions in the provided project structure.

# Development Principles
- DRY — remove duplication, centralize shared logic (especially provider coercion and token logic).
- KISS — prefer simple, well-tested solutions over speculative complexity.
- YAGNI — do not add features that aren’t strictly required to fix the problem at hand.
- Single Responsibility — each module/class/function should do one thing well.
- Fail-fast & explicit errors — surface errors early with actionable messages.
- Prioritize long-term maintainability and auditability.
- Use type annotations and keep stubs (.pyi) in sync with implementation.
- When unsure about the best approach, gather more data (run tests, reproduce locally, add lightweight probes) rather than guessing.
- Keep this AGENTS.md file up-to-date and update/edit for any significant changes.
- Throughout the codebase you will see SNAPSHOT.md files. These files contain architectural documentation using directory trees with inline comments. Refer to them to understand and navigate the project efficiently. When files are added/removed/moved, update SNAPSHOT.md fils by running `agentrules snapshot sync` (preserves comments, but does not add comments).

## ExecPlans
- When writing complex features or refactors, use an ExecPlan (as described in `.agent/PLANS.md`) from design to implementation.

### Milestones
- When the feature or refactor your writing is significantly complex, disaggregate the ExecPlan into milestones (as described in `.agent/templates/MILESTONE_TEMPLATE.md`)

### Prefer CLI creation over manual file creation:
* ExecPlan:
  * Create: `agentrules execplan new "<title>" --slug <short-slug> --ms <N>` (Use `--ms <N>` for deterministic `MS###` sequence assignment).
  * Archive: `agentrules execplan archive EP-YYYYMMDD-NNN`
* Milestones:
  * Create: `agentrules execplan milestone new EP-YYYYMMDD-NNN "<Milestone Title>"`
  * Archive: `agentrules execplan milestone archive EP-YYYYMMDD-NNN --ms <N>`

# 2. TEMPORAL FRAMEWORK

It is 2026 and you are developing using Python 3.11+ with modern provider SDKs (Anthropic, OpenAI, Gemini, xAI, DeepSeek). Local tokenization/counting (tiktoken-style encoders) is available and should be preferred for cost and determinism. Pyright lints and ruff style checks are enforced in CI.

# 3. TECHNICAL CONSTRAINTS

# Technical Environment
- Language: Python >= 3.11 (3.11.9+ recommended).
- Source root: src/agentrules (this must match pyproject metadata).
- CI enforced: pyright, ruff, pytest; import-smoke and template validation jobs must run.
- Async model: asyncio-based pipeline; avoid blocking the event loop.

# Dependencies
- tiktoken (or provider of local token counting)
- aiofiles
- lxml
- pytest / pytest-asyncio
- pyright >= 1.1.380
- ruff
- questionary (CLI prompts)
- (dev) tools: pre-commit hooks, coverage, tox or GitHub Actions runner

# Configuration (repo-specific)
- Primary code paths:
  - Analysis phases: src/agentrules/core/analysis/phase_1.py ... phase_5.py
  - Project profiling: src/agentrules/core/pipeline/project_profile.py
  - Token packing/estimation: src/agentrules/core/utils/token_estimator.py, token_packer.py
  - File I/O: src/agentrules/core/utils/file_system/file_retriever.py
  - Providers: src/agentrules/core/agents/{anthropic,openai,gemini,deepseek,xai}
  - Prompt templates: src/agentrules/config/prompts/*
  - Parser: src/agentrules/core/utils/parsers/agent_parser.py
- Output artifacts: AGENTS.md (`rules_filename`), optional `phases_output/`, optional `.cursorignore`, and optional `.agent` scaffold (`.agent/PLANS.md` and `.agent/templates/MILESTONE_TEMPLATE.md`).
- Scaffold template sources: src/agentrules/core/utils/file_creation/templates/{PLANS.md,MILESTONE_TEMPLATE.md} (packaged via pyproject package-data).
- Concurrency defaults: AGENTRULES_IO_CONCURRENCY = 8 (configurable)
- Token cache: in-memory per-run cache keyed by (model_name, sha256(content)); persisted caching optional but disabled by default.
- Template validation: run template substitution checks in CI.
- structured output documentation located in `internal-docs/integrations/`.
- Refer to `internal-docs/integrations/codex/app-server` for codex app-server documentation.

# 4. IMPERATIVE DIRECTIVES

# Your Requirements:
1. Ensure pyproject.toml name and package import path are consistent with the source tree. The CI import-smoke test must pass (python -c "import agentrules" or equivalent). DO NOT merge changes that break importability.
2. TOKEN PACKER MUST BE O(N):
   - Precompute per-file token counts and memoize encodings.
   - Cache keyed by (model_name, sha256(content)).
   - Compute prompt skeleton overhead ONCE per packaging run.
3. ATOMICALLY WRITE CRITICAL ARTIFACTS (AGENTS.md and phase outputs):
   - Use tempfile.NamedTemporaryFile or tempfile.mkstemp + os.replace for final write.
   - Ensure on crash the file is either old content or fully replaced (no partial files).
4. CANONICALIZE TOOL MANAGER OUTPUTS:
   - ToolManager MUST return plain serializable dicts (name, args, schema).
   - Convert to SDK-specific objects only at provider request-time.
5. PROMPT SAFETY:
   - NEVER embed raw file contents without escaping. Use base64 or JSON-escaped content to avoid sentinel collisions. Update token estimation logic accordingly.
6. PARSER ROBUSTNESS:
   - Prefer structured JSON/dict outputs from Phase 2. Use tolerant XML parser (lxml.recover) as a fallback. Validate that parsed file paths exist.
7. TEST & CI:
   - Add CI jobs: import_smoke_test, prompt_template_validation (mock safely), parser_corpus unit tests, token_packer benchmark anti-regression (lightweight), offline pipeline smoke with DummyArchitect.

# 5. KNOWLEDGE FRAMEWORK

# Agents & Provider Architecture
- Each provider module implements an "architect" + "client" + "request_builder" + "response_parser" pattern. Keep adapters thin and use a single canonical translation layer for SDK-specific object creation.
- Shared utilities should live in src/agentrules/core/utils/provider_utils.py and be imported by all provider modules.
- Phase 1 emits `project_profile` and may conditionally run specialized discovery agents (`Frontend Design Agent`, `Python Tooling Agent`) when profile slices indicate relevance; keep gating deterministic and tied to profile booleans.

## Provider integration rules
- Tool payloads from ToolManager must be dicts.
- Providers must accept dicts and convert them to SDK objects only immediately prior to sending requests.
- For unit tests, provider clients should expose set_client/get_client injection points for test doubles.
- Codex is a local runtime provider, not an API-key provider. Persist Codex settings in the dedicated `CLIConfig.codex` section and gate Codex presets on runtime readiness (`codex` executable plus resolved `CODEX_HOME` policy), not on `providers.<name>.api_key`.
- The Codex app-server transport lives under `src/agentrules/core/agents/codex/`. All CLI and runtime callers must construct launch settings through `ConfigManager.build_codex_launch_config()` so executable resolution and `CODEX_HOME` policy stay centralized.
- `CodexArchitect` must keep `developer_instructions` request-scoped by passing them through launch-config overrides to a short-lived app-server process, and structured phases must use app-server `outputSchema` rather than prompt-only JSON guidance.
- Provider-specific Codex pipeline exceptions must route through shared capability helpers in `src/agentrules/core/utils/provider_capabilities.py`. Use those helpers for Phase 1 researcher/tool-loop decisions and Phase 3 repo-runtime prompting so Codex special cases stay centralized.
- Operator guidance for Codex belongs in `docs/codex-runtime.md`. Keep the documented live-smoke path aligned with `tests/live/test_codex_live_smoke.py` and gate it behind `AGENTRULES_RUN_CODEX_LIVE=1` plus `pytest --run-live`.
- System/developer instructions must be resolved once per request and mapped to provider-native fields:
  - OpenAI Responses: `instructions`; OpenAI Chat: developer role message
  - Anthropic: top-level `system`
  - Gemini: `system_instruction`
  - DeepSeek/xAI: leading `system` message in OpenAI-compatible chat payloads
- Keep behavioral guidance in phase system prompts (`config/prompts/system_prompts.py`) and keep user prompts focused on task payload/context.
- Require a resolved system prompt for every agent request (no optional mode).

# Token Estimation & Packing
- Use local token encoder objects memoized per model. Avoid repetitive encoder creation.
- Cache per-file token counts keyed by (model_name, sha256(content)).
- Packing algorithm (greedy):
  1. Compute skeleton tokens once.
  2. For each file, get cached token count + per-file envelope overhead.
  3. Accumulate until limit, yield batch.
- If file token count > effective model limit:
  - Summarize the file (prefer model-based summarizer) and re-tokenize the summary.
  - Cache summaries using same content-hash-based key.

# Async File I/O & Concurrency
- Replace blocking file reads in async context:
  - Use aiofiles for large reads or asyncio.to_thread for small compat changes.
- Concurrency limit via asyncio.Semaphore; default 8 but configurable.
- Use "utf-8" with errors="replace" for robust reading.

# Prompt Engineering & Template Safety
- Use base64 encoding for embedding when sentinel safety is critical. Option: use JSON-escaping for readability with less token overhead.
- Avoid str.format() with templates that contain braces. Prefer string.Template.safe_substitute or an explicit JSON payload container.
- Add template-validation CI job to detect unescaped braces or missing placeholder fields.

# Parser Robustness and Phase 2 behavior
- Phase 2 should attempt to emit structured JSON first. If model output is unstructured, try JSON extraction heuristics, then XML parser with recover, then conservative regex cleanup.
- Always validate parsed file paths exist; drop or warn for non-existent file paths.
- Store robust test corpus for parser in tests/fixtures/parser_corpus/.

# Atomic Output Persistence
- Use temp file + os.replace for AGENTS.md and any phase artifacts.
- Optionally create a backup/rotate scheme if desired.

# Output Artifact Scaffolding
- Materialize optional `.agent` scaffolding from package templates during output persistence (not during analysis phases).
- `.agent` generation must be configurable via output preferences (`generate_agent_scaffold`) and default to disabled.
- Scaffold generation must be idempotent and non-destructive by default (do not overwrite existing `.agent` files unless explicitly requested).

# CLI & UX
- All questionary prompts must use CLI_STYLE.
- Provider key semantics: blank input => keep existing key; explicit “clear” action or `--clear-key` flag clears key.
- Capture PackageNotFoundError for importlib.metadata.version and fall back gracefully.

# Tests & CI
- Required minimal CI jobs described in Imperative Directives.
- Add unit tests for all P0/P1 changes. Benchmarks must be lightweight for CI (sample N=100).

# Security & Logging
- Redact sensitive fields in logs: environment variables and provider responses that contain `api_key`, `Authorization`, etc.
- Add a logging filter that scrubs obvious secrets.

# 6. IMPLEMENTATION EXAMPLES

## Non-blocking file read with concurrency control
```python
# src/agentrules/core/utils/file_system/async_reader.py
import aiofiles
import asyncio
from typing import List

DEFAULT_CONCURRENCY = 8
io_semaphore = asyncio.Semaphore(DEFAULT_CONCURRENCY)

async def read_file_text(path: str) -> str:
    async with io_semaphore:
        async with aiofiles.open(path, mode="r", encoding="utf-8", errors="replace") as f:
            return await f.read()

async def read_many(paths: List[str]) -> List[str]:
    return await asyncio.gather(*(read_file_text(p) for p in paths))
```

## Token-count caching and greedy packer (sketch)
```python
# src/agentrules/core/utils/token_packer.py
import hashlib
from typing import Dict, List, Tuple

_token_cache: Dict[Tuple[str,str], int] = {}
_encoding_cache: Dict[str, object] = {}

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def estimate_tokens_for_model(model: str, text: str) -> int:
    # Use memoized local encoder (tiktoken style) when available.
    enc = _encoding_cache.get(model)
    if enc is None:
        enc = load_encoder_for_model(model)  # memoized loader
        _encoding_cache[model] = enc
    return enc.encode(text).__len__()  # or enc.encode_ordinary depending on lib

def tokens_for_file(model: str, content: str) -> int:
    key = (model, _sha256_hex(content))
    if key not in _token_cache:
        _token_cache[key] = estimate_tokens_for_model(model, content)
    return _token_cache[key]

def greedy_pack_files(model: str, files: List[Tuple[str,str]], limit: int, overhead: int):
    """
    files: list of (path, content)
    overhead: per-file envelope overhead tokens
    """
    skeleton = compute_skeleton_text()  # assembled prompt skeleton
    skeleton_tokens = estimate_tokens_for_model(model, skeleton)
    batch = []
    running = skeleton_tokens
    for path, content in files:
        ftokens = tokens_for_file(model, content)
        if ftokens + overhead > limit - skeleton_tokens:
            # single file too big -> call summarizer (not shown)
            content = summarize_content(content)
            ftokens = tokens_for_file(model, content)
        if running + ftokens + overhead > limit:
            yield batch
            batch = []
            running = skeleton_tokens
        batch.append((path, content))
        running += ftokens + overhead
    if batch:
        yield batch
```

## Atomic write helper
```python
# src/agentrules/core/utils/file_creation/atomic_write.py
import os
import tempfile
from pathlib import Path

def atomic_write_text(path: Path, text: str):
    temp_dir = path.parent
    fd, tmp = tempfile.mkstemp(dir=temp_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
```

## Provider object→dict util (single shared place)
```python
# src/agentrules/core/utils/provider_utils.py
from typing import Any, Dict

def sdk_object_to_dict(obj: Any) -> Dict:
    # Generic converter: inspect dataclass, pydantic, or SDK object
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    # Fallback: serialize repr
    return {"_fallback_repr": repr(obj)}
```

## OpenAI client test-injection API
```python
# src/agentrules/core/agents/openai/client.py
class OpenAIClientWrapper:
    def __init__(self, client=None):
        self._client = client or self._create_default_client()

    def set_client(self, client):
        self._client = client

    def get_client(self):
        return self._client

    # usage: self._client.chat.create(...)
```

## Safe file embedding (base64)
```python
import base64
import json

def embed_file_base64_for_prompt(path: str, content: str) -> str:
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"path": path, "content_b64": b64}
    return json.dumps(payload, ensure_ascii=False)
```

## Parser fallback using lxml.recover
```python
from lxml import etree

def recover_parse_xml_or_html(text: str):
    parser = etree.XMLParser(recover=True)  # tolerant parsing
    return etree.fromstring(text.encode("utf-8"), parser=parser)
```

# 7. NEGATIVE PATTERNS

# What NOT to do:

## Blocking I/O inside async functions
- DO NOT:
```python
# Bad
async def load_file(path):
    with open(path) as f:
        return f.read()
```
- Use aiofiles or asyncio.to_thread instead.

## O(n^2) token estimation
- DO NOT recompute token counts in nested loops. Precompute and memoize.

## Template explosions & unescaped format
- DO NOT use str.format on templates containing braces without validation:
```python
template = "List: {items} and a literal {"
output = template.format(items="x")  # can raise KeyError / ValueError
```
- Use safe substitutions or Template.safe_substitute.

## Simulating AI with hard-coded if/else
- Avoid if-else heuristics that attempt to replicate model reasoning.

## Non-atomic writes for critical artifacts
- DO NOT write AGENTS.md with open(..., "w") then leave files vulnerable to partial writes on crash.

## Duplication across provider modules
- DO NOT copy/paste _to_dict implementation in every architect module. Centralize.

# 8. KNOWLEDGE EVOLUTION MECHANISM

# Validation Checklist (before merging PRs)
- [ ] Identity statement present in AGENTS.md
- [ ] Import smoke test passes (python -c 'import agentrules')
- [ ] No blocking I/O in async functions in modified files (checked by review / tests)
- [ ] Token packer uses per-file token cache and runs in O(n) for test fixture
- [ ] Critical outputs (AGENTS.md, phase artifacts) written atomically
- [ ] Optional `.agent` scaffold generation is configurable and templates are packaged/importable in installed builds
- [ ] ToolManager returns plain dicts in all code paths
- [ ] Provider coercion logic centralized in provider_utils.py
- [ ] Prompt templates validated in CI
- [ ] Parser corpus tests pass
- [ ] OpenAI client wrapper supports set_client/get_client
- [ ] Secrets not present in test logs (redaction validated)
- [ ] pyright and ruff checks pass

# Practical Implementation Tips
1. Start with package/import mismatch fix and import-smoke CI job. This unblocks local iteration.
2. Small, focused PRs per priority P0 item. Include tests for each behavioral change.
3. Benchmarks are useful but keep CI benchmark jobs lightweight; full benchmarks can be run in separate performance runs.
4. Repeat critical constraints in top of changed files as comments for future maintainers (e.g., token cache usage).
5. When editing prompt templates, add a unit test to format the template with mock safe data.

# Closing behavior guidance
- When making changes: run unit tests locally, run import smoke, and push a PR with descriptive title and the validation checklist ticked.
- If a requested change impacts importability or test baseline heavily, first open a draft PR and request a human review.
- When in doubt about model behavior or format, prefer conservative parsing (fail closed) and log a clear warning.
