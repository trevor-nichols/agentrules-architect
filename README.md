# 🤖 AgentRules Architect

<div align="center">

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![PyPI](https://img.shields.io/pypi/v/agentrules.svg)](https://pypi.org/project/agentrules/)
[![OpenAI](https://img.shields.io/badge/OpenAI-supported-blue.svg)](https://openai.com/)
[![Codex Runtime](https://img.shields.io/badge/Codex%20app--server-supported-orange.svg)](https://github.com/openai/codex)
[![Anthropic](https://img.shields.io/badge/Anthropic-supported-purple.svg)](https://www.anthropic.com/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-purple.svg)](docs/claude-code-runtime.md)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-supported-red.svg)](https://deepseek.com/)
[![Google](https://img.shields.io/badge/Google-supported-green.svg)](https://ai.google.dev/)
[![xAI](https://img.shields.io/badge/xAI-supported-black.svg)](https://x.ai/)
[![Built By](https://img.shields.io/badge/Built%20By-trevor-nichols-orange.svg)](https://github.com/trevor-nichols)

**Multi-provider repository analysis, agent rules generation, and ExecPlan tooling.**

[Demo](#-cli-demo) • [Highlights](#-highlights) • [Features](#-feature-overview) • [Requirements](#-requirements) • [Installation](#-installation) • [Local Runtimes](#-configure-local-runtimes-optional) • [CLI](#-cli-at-a-glance) • [Configuration](#-configuration--preferences) • [Architecture](#-project-architecture) • [Outputs](#-output-artifacts) • [Development](#-development-workflow)

</div>

## 🎥 CLI Demo

![AgentRules CLI demo](docs/assets/media/demo.gif)

## Why AgentRules Architect?

AgentRules Architect analyzes a repository, coordinates specialized model-backed architects, and writes durable rules artifacts such as `AGENTS.md` or a custom rules filename like `CLAUDE.md`. It is built around a six-phase pipeline, a Rich/Typer CLI, persistent TOML configuration, provider-specific request adapters, local runtime integrations, and optional planning artifacts for longer agent-led work.

## 🔥 Highlights

- 📦 **PyPI package** – ships with console-script and `python -m agentrules` entry points.
- 🧭 **Interactive CLI** – `agentrules` launches a guided main menu, while subcommands cover analysis, configuration, keys, snapshots, ExecPlans, scaffolds, and tree previews.
- 🗂️ **Persistent settings** – API keys, model presets, logging, and output preferences live in `~/.config/agentrules/config.toml` (override with `AGENTRULES_CONFIG_DIR`).
- 🧠 **Broad provider matrix** – presets span Anthropic, Claude Code, OpenAI, Codex app-server, Google Gemini, DeepSeek, and xAI, with phase-by-phase model selection from the CLI or config file.
- 🧰 **Local runtime support** – route phases through Codex app-server or Claude Code without treating those runtimes as ordinary API-key providers.
- 🔌 **Unified tool management** – `ToolManager` adapts canonical JSON tool schemas for each provider; Tavily web search is available to researcher agents with one toggle.
- ✅ **Test & quality backbone** – unit/integration tests, offline stubs, Pyright, and Ruff provide confidence without hitting live APIs.

## ✨ Feature Overview

- 🌐 Multi-provider orchestration with consistent streaming telemetry.
- 🔍 Six-phase pipeline: discovery → planning → deep dives → synthesis → consolidation → final AGENTS.md generation.
- 🧩 Researcher tooling via Tavily search with provider-aware tool translation.
- 📊 Rich terminal UI (Rich) showing per-agent progress, duration, and failures in real time.
- 🪵 Configurable outputs: `AGENTS.md`, `SNAPSHOT.md` (enabled by default), `.cursorignore`, optional `.agent/` scaffold templates, and per-phase markdown/json snapshots.
- 🧭 ExecPlan and milestone commands for long-running work with deterministic IDs and registry validation.
- 🔧 Declarative model presets plus runtime overrides via CLI or TOML.

## 🧮 Analysis Pipeline

All CLI entry points ultimately execute the `AnalysisPipeline` orchestrator (`src/agentrules/core/pipeline`) that wires the six analysis phases together and streams progress events to the Rich console.

1. **Phase 1 – Initial Discovery** (`core/analysis/phase_1.py`) inventories the repo tree, surfaces tech stack signals, and collects dependency metadata that later phases reuse.
2. **Phase 2 – Methodical Planning** (`core/analysis/phase_2.py`) asks the configured model to draft an XML-ish agent plan, then parses it into structured agent definitions (with a safe fallback extractor).
3. **Phase 3 – Deep Analysis** (`core/analysis/phase_3.py`) spins up specialized architects per agent definition, hydrates them with file excerpts, and runs them in parallel; if no plan exists it falls back to three default agents.
4. **Phase 4 – Synthesis** (`core/analysis/phase_4.py`) stitches together Phase 3 findings, elevates cross-cutting insights, and flags follow-up prompts for the final steps.
5. **Phase 5 – Consolidation** (`core/analysis/phase_5.py`) produces a canonical report object that downstream tooling (rules generator, metrics, exporters) consumes.
6. **Final Analysis** (`core/analysis/final_analysis.py`) produces the narrative summary that drives `AGENTS.md`, output toggles, and console highlights.

The pipeline captures metrics (elapsed time, agent counts) and hands them to the output writer so offline runs and full analyses share the same persistence path.

## 🛠 Requirements

- Python **3.11.9+** (matches Pyright target and packaged metadata).
- API key(s), OAuth runtime auth, or both for at least one model provider:
  - Anthropic
  - Claude Code (local runtime via Claude OAuth / SDK)
  - OpenAI
  - Codex app-server (local runtime via ChatGPT auth)
  - DeepSeek
  - Google Gemini
  - xAI
  - Tavily (optional, enables live web search tooling)
- Current preset IDs live in `src/agentrules/config/agents.py`.
- Dependency declarations live in `pyproject.toml`.
- Dev tooling includes `pytest`, Ruff, and Pyright.

## 📦 Installation

### Install from PyPI

```bash
pip install -U agentrules
```

- Package page: <https://pypi.org/project/agentrules/>
- Test index page: <https://test.pypi.org/project/agentrules/>

### Install from source

```bash
git clone https://github.com/trevor-nichols/agentrules-architect.git
cd agentrules-architect
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Need a one-liner? Use the helper script:

```bash
./scripts/bootstrap_env.sh           # set PYTHON_BIN=/abs/path/to/python to override interpreter
```

### Quick smoke test

```bash
agentrules --version
agentrules analyze /path/to/project
```

Prefer module execution during development? Invoke the CLI with Python’s module flag—the package ships a `__main__` entry point:

```bash
python -m agentrules analyze /path/to/project
```

Need to install directly from GitHub instead of PyPI?

```bash
pip install "git+https://github.com/trevor-nichols/agentrules-architect.git#egg=agentrules"
```

Need to validate against TestPyPI specifically?

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple agentrules
```

## 🔐 Configure API Keys

Run the interactive configurator to store credentials securely:

```bash
agentrules configure
```

- Keys are saved to `~/.config/agentrules/config.toml` (override with `AGENTRULES_CONFIG_DIR`).
- Values are mirrored into environment variables on the next launch.
- Use `agentrules configure --provider openai` for quick single-key updates.
- Show current status with:

```bash
agentrules keys
```

## 🧰 Configure Local Runtimes (Optional)

AgentRules supports local runtime providers separately from API-key providers.

- Open `agentrules` -> `Settings` -> `Codex runtime`
- Configure:
  - executable path (`codex` by default)
  - `CODEX_HOME` strategy (`managed` or `inherit`)
  - optional managed home override
- Use `Sign in with ChatGPT` to authenticate runtime-backed model access.
- Open `agentrules` -> `Settings` -> `Claude Code runtime`
- Configure:
  - Claude Agent SDK runtime resolution
  - optional explicit `claude` executable path
  - API-key environment sanitization for Claude Code child processes
- Authenticate Claude Code outside AgentRules with Claude Code's OAuth flow.

After runtime setup, choose Codex or Claude Code presets under `Settings -> Model presets per phase`.

See [docs/codex-runtime.md](docs/codex-runtime.md) and [docs/claude-code-runtime.md](docs/claude-code-runtime.md) for setup, auth flow, model catalog behavior, and live smoke instructions.

## 🧭 CLI At A Glance

- `agentrules` – interactive main menu (analyze, configure models/outputs, check keys).
- `agentrules analyze /path/to/project` – full six-phase analysis.
- `agentrules analyze /path/to/project --rules-filename CLAUDE.md` – one-run override for output rules filename.
- `agentrules snapshot generate [path]` – create (or refresh) `SNAPSHOT.md` in the current directory by default.
- `agentrules snapshot sync [path]` – sync an existing snapshot as project files evolve (also creates if missing).
- `agentrules execplan new "Title"` – create a new ExecPlan markdown file under `.agent/exec_plans/active/<slug>/`.
- `agentrules execplan complete EP-YYYYMMDD-NNN [--date YYYYMMDD]` – move a full ExecPlan directory under `.agent/exec_plans/complete/YYYY/MM/DD/EP-YYYYMMDD-NNN_<slug>/`.
- `agentrules execplan list [--path]` – list active ExecPlans with compact milestone progress (`completed/total`).
- `agentrules execplan milestone new EP-YYYYMMDD-NNN "Title" [--ms N]` – create a milestone under a specific ExecPlan (auto sequence by default, or explicit `MS###` when provided).
- `agentrules execplan milestone list EP-YYYYMMDD-NNN [--active-only]` – list milestones for one ExecPlan.
- `agentrules execplan milestone complete EP-YYYYMMDD-NNN --ms <N>` – move an active milestone sequence into the `milestones/complete/` directory.
- `agentrules execplan milestone remaining EP-YYYYMMDD-NNN [--path]` – show active milestones left for one ExecPlan.
- `agentrules execplan-registry [build|check|update]` – manage `.agent/exec_plans/registry.json` from ExecPlan front matter.
- `agentrules scaffold sync [--check|--force]` – sync `.agent/PLANS.md` and `.agent/templates/MILESTONE_TEMPLATE.md` with packaged defaults.
- `agentrules configure --models` – assign presets per phase with guided prompts; the Phase 1 → Researcher entry lets you toggle the agent On/Off once a Tavily key is configured.
- `agentrules configure --outputs` – toggle `.cursorignore`, `.agent/` scaffold generation, `phases_output/`, and custom rules filename.
- `agentrules configure --logging` – set verbosity (`quiet`, `standard`, `verbose`) or export via `AGENTRULES_LOG_LEVEL`.
- `agentrules tree [path]` – preview the exclusion-aware project tree and optionally save it.

## 🧭 ExecPlan & Milestones

ExecPlans are long-horizon execution artifacts for work that is too large for a single prompt/session and too risky to run as ad hoc edits.
They give humans and agents a durable plan, explicit scope, and audit trail that can survive context switching across days or weeks.

This follows the same general planning pattern used for larger Codex work: start with an implementation plan, then execute it iteratively in smaller scoped chunks (see [OpenAI Codex docs](https://developers.openai.com/codex) and [How OpenAI uses Codex](https://openai.com/index/how-openai-uses-codex/)).

Think of the model in three layers:

- **ExecPlan (strategic layer)** – one high-level objective, constraints, success criteria, and overall rollout strategy.
- **Milestones (delivery layer)** – concrete sub-deliverables within that plan, sequenced (`MS001`, `MS002`, ...) and independently completable.
- **Task checklists (execution layer)** – fine-grained implementation/validation steps inside each plan or milestone document.

Why this exists:

- Keep long-running work coherent across multiple agent runs.
- Make progress and remaining scope visible at a glance.
- Reduce regressions by forcing explicit sequencing, verification, and rollback thinking.
- Preserve design decisions and rationale in one canonical place.

ExecPlans and milestones use canonical IDs and deterministic file locations:

- ExecPlan ID: `EP-YYYYMMDD-NNN`
- Milestone ID: `EP-YYYYMMDD-NNN/MS###`
- Active ExecPlan path: `.agent/exec_plans/active/<plan-slug>/EP-YYYYMMDD-NNN_<plan-slug>.md`
- Complete ExecPlan path: `.agent/exec_plans/complete/YYYY/MM/DD/EP-YYYYMMDD-NNN_<plan-slug>/EP-YYYYMMDD-NNN_<plan-slug>.md`
- Active milestone path: `.agent/exec_plans/active/<plan-slug>/milestones/active/MS###_<milestone-slug>.md`
- Complete milestone path: `.agent/exec_plans/active/<plan-slug>/milestones/complete/MS###_<milestone-slug>.md`

Milestone creation is parent-first and sequence-safe:

- Users provide parent ExecPlan ID + milestone title.
- CLI/API assign `MS###` automatically, or accept `--ms N` to request a specific sequence.
- Sequence is monotonic per plan across active and completed milestones (`MS001`, `MS002`, ...).
- `.agent/templates/MILESTONE_TEMPLATE.md` is a guidance scaffold for authors.
  Generated milestone files come from an internal file template used by `execplan milestone new`.

Examples:

```bash
# 1) Create an ExecPlan
agentrules execplan new "Auth Refresh" --date 20260207

# 2) Create milestones for that plan (auto-assigns MS001, then MS002, ...)
agentrules execplan milestone new EP-20260207-001 "Design callback flow"
agentrules execplan milestone new EP-20260207-001 "Implement callback flow"

# Optional: request an explicit sequence (must be unused)
agentrules execplan milestone new EP-20260207-001 "Backfill docs" --ms 5

# 3) List milestones (all or active-only)
agentrules execplan milestone list EP-20260207-001
agentrules execplan milestone list EP-20260207-001 --active-only

# Optional: compact "what's left" view for active milestones only
agentrules execplan milestone remaining EP-20260207-001

# 4) Complete a finished milestone
agentrules execplan milestone complete EP-20260207-001 --ms 1

# 5) Complete the ExecPlan directory
agentrules execplan complete EP-20260207-001 --date 20260212

# Optional: list all active plans with compact milestone progress
agentrules execplan list
```

## ⚙️ Configuration & Preferences

- **Config file**: `~/.config/agentrules/config.toml`
  - `providers` – API keys per provider.
  - `codex` – local runtime settings (`cli_path`, `home_strategy`, `managed_home`).
  - `claude_code` – Claude Code SDK runtime settings, request limits, and environment sanitization preferences.
  - `models` – preset IDs applied to each phase (`phase1`, `phase2`, `final`, `researcher`, …).
  - `outputs` – `generate_cursorignore`, `generate_agent_scaffold`, `generate_phase_outputs`, `generate_snapshot`, `rules_filename`, `snapshot_filename`.
    - `generate_snapshot` defaults to `true` and writes `SNAPSHOT.md` at project root after each analysis run (toggle anytime in `agentrules configure --outputs`).
  - `features` – `researcher_mode` (`on`/`off`) to control Phase 1 web research (managed from the Researcher row in the models wizard).
  - `exclusions` – add/remove directories, files, or extensions; choose to respect `.gitignore`.
- **Runtime helpers** (via `agentrules/core/configuration/manager.py`):
  - `ConfigManager.get_effective_exclusions()` resolves overrides with defaults from `config/exclusions.py`.
  - `ConfigManager.should_generate_phase_outputs()` and related methods toggle output writers in `core/utils/file_creation`.
- **Environment variables**:
  - `AGENTRULES_CONFIG_DIR` – alternate config root.
  - `AGENTRULES_LOG_LEVEL` – overrides persisted verbosity.
  - `AGENTRULES_RULES_FILENAME` – runtime override for generated rules filename (for example `CLAUDE.md`).
  - `CODEX_HOME` – used when Codex `home_strategy = "inherit"`.
  - `CLAUDE_CODE_OAUTH_TOKEN` – optional Claude Code automation token for environments that cannot use an interactive login.
- **Rules filename precedence**:
  1. `agentrules analyze --rules-filename <name>`
  2. `AGENTRULES_RULES_FILENAME`
  3. `outputs.rules_filename` in `config.toml` (set via `agentrules configure --outputs`)
  4. `AGENTS.md` default

## 🧠 Model Presets & Providers

Presets live in `config/agents.py` via the `MODEL_PRESETS` dictionary. Each preset bundles:

- Provider (`ModelProvider`)
- Model name plus reasoning/temperature configuration
- Human-readable label and description for the CLI wizard

The app currently exposes presets across these providers:

- Anthropic
- Claude Code (local runtime)
- OpenAI
- Codex App Server (local runtime)
- Google Gemini
- DeepSeek
- xAI

Choose any available preset per phase through the CLI (`agentrules configure --models`) or by editing `config.toml` / `config/agents.py`. At runtime the values populate `MODEL_CONFIG`, which the pipeline consumes while resolving phase architects (`src/agentrules/core/agents/factory/factory.py`).

> **Preset tip:** Preset keys are compatibility IDs, not release markers. Static presets live in `config/agents.py`, while Codex runtime selections in the settings UI are discovered from the live app-server catalog.

## 🧠 Reasoning & Advanced Configuration

- **Reasoning modes:** Anthropic presets use fixed-budget or adaptive thinking depending on the Claude family, Gemini presets use provider-native thinking controls, OpenAI presets map to reasoning effort or temperature based on model family, DeepSeek V4 presets explicitly select thinking/non-thinking plus high/max effort, and xAI presets keep their model-specific reasoning behavior (`src/agentrules/core/types/models.py`). Saved `deepseek-chat` and `deepseek-reasoner` preset keys are redirected to equivalent V4 Flash modes before those aliases retire on July 24, 2026.
- **Runtime modes:** Codex presets route phases through `codex app-server`, with runtime-discovered model/effort variants available from the live model catalog. Claude Code presets route phases through the Claude Agent SDK while preserving Claude Code's runtime behavior.
- **Agent planning:** Phase 2 generates agent manifests that Phase 3 converts into live architects; when parsing fails the fallback extractor and default agents keep the pipeline running (`core/analysis/phase_2.py`, `core/analysis/phase_3.py`).
- **Provider-specific tools:** `create_researcher_config` enables Tavily-backed tool use for whichever preset you promote to the Researcher role, and the CLI’s Researcher row simply flips that on/off (`core/types/models.py`, `config/tools.py`).
- **Prompt customization:** Fine-tune behaviour by editing the phase prompts under `src/agentrules/config/prompts/`—heavy modifications should stay aligned with the YAML/XML formats expected by the parser utilities.
- **Token-aware runs:** Architects emit token preflight logs using configured context limits/estimators, and Phase 3 uses limit-aware batching plus summarization when a model’s max input tokens are provided.
- **Direct overrides:** Advanced users can swap presets or tweak reasoning levels by modifying `MODEL_PRESETS`/`MODEL_PRESET_DEFAULTS` in `config/agents.py`; the configuration manager merges those with TOML overrides at runtime.

## 🔍 Tooling & Research Agents

- `core/agent_tools/tool_manager.py` normalizes JSON tool schemas for each provider.
- `config/tools.py` exposes `TOOL_SETS` and a `with_tools_enabled` helper for models that accept function/tool calls.
- Tavily search (`tavily_web_search`) ships as the default researcher tool. Add `TAVILY_API_KEY` in the provider settings to automatically enable the Researcher agent, then pick the model (or flip it back `Off`) from the models wizard’s Researcher entry. When disabled—or when no key is present—documentation research is skipped; our contributor smoke tests use deterministic stubs to keep CI free of external calls. The dependency agent automatically downgrades from “knowledge gaps” mode to its legacy full catalog so downstream agents still receive usable dependency data when research is unavailable.

## 🧱 Project Architecture

- `agentrules/` – Typer CLI, interactive Questionary flows, Rich UI, configuration services, and pipeline runner (`agentrules/SNAPSHOT.md`).
- `core/` – provider-specific architects (`core/agents`), analysis phases (`core/analysis`), tool adapters (`core/agent_tools`), streaming primitives, and filesystem utilities (`core/SNAPSHOT.md`).
- `config/` – preset definitions, exclusions, prompts, and tool bindings (`config/SNAPSHOT.md`).
- `tests/` – live smoke tests, deterministic offline stubs for CI, provider fixtures, and unit coverage for helpers and phases.
- `pyproject.toml` – package metadata, scripts, Ruff/Pyright config, and dependency declarations.

## 🧾 Output Artifacts

By default the pipeline produces:

- `AGENTS.md` (or your custom rules filename) – cleaned, standardized agent instructions.
- `SNAPSHOT.md` – full project tree snapshot (no depth limit by default) generated at the project root after the pipeline finishes.
- `.cursorignore` – generated when enabled to keep editor agents focused on relevant files.
- `.agent/` scaffold – generated when enabled (`.agent/PLANS.md` and `.agent/templates/MILESTONE_TEMPLATE.md`).
- `phases_output/` – per-phase markdown/JSON snapshots for auditing and downstream automation.
- Want a concrete sample? See `docs/examples/phases_output/` for a full run’s phase artifacts.
- Rich console logs summarizing model usage, timing, and file counts.

Toggle outputs with `agentrules configure --outputs` or via the config TOML.

## 🛠 Development Workflow

- Install dev extras: `pip install -e ".[dev]"`
- Format & lint: `ruff format . && ruff check .`
- Static typing: `pyright`
- Run targeted tests: `python tests/phase_3_test/run_test.py`
- Deterministic smoke runs (CI/local without API calls): `agentrules analyze --offline tests/tests_input`
- Full suite: `pytest`
- Releases are Release Please-driven: merges to `main` update/open a release PR, and merging that PR creates the `vX.Y.Z` tag + GitHub release automatically.
- GitHub Actions publishes package artifacts with Trusted Publishing (OIDC) via `.github/workflows/publish-pypi.yml` (no long-lived PyPI API token).
- Run a safe preflight publish first from Actions with `workflow_dispatch` and `repository = testpypi`; publish to production PyPI on release-tag push or manual `repository = pypi`.
- Keep docs and presets in sync when adding providers (`config/agents.py`, `config/tools.py`, `core/agents/*`).

### Release Process (PyPI)

1. Merge feature PRs into `main` using Conventional Commit-style titles/messages (for example `feat: ...`, `fix: ...`).
2. `.github/workflows/release-please.yml` updates or opens a release PR with the version bump and changelog.
3. (Optional, recommended) run `.github/workflows/publish-pypi.yml` manually with `repository = testpypi` from the release PR head commit.
4. Merge the release PR. Release Please creates/pushes the matching `vX.Y.Z` tag and publishes a GitHub release.
5. The tag push triggers `.github/workflows/publish-pypi.yml` to publish to production PyPI.
6. One-time setup for new projects:
   - Configure a repo secret `RELEASE_PLEASE_TOKEN` (PAT or GitHub App token) with permission to create/update PRs, tags, and releases. This ensures tag pushes from Release Please trigger downstream workflows.
   - Configure Trusted Publishers on TestPyPI and PyPI for repository `trevor-nichols/agentrules-architect`, workflow `.github/workflows/publish-pypi.yml`, and environments `testpypi`/`pypi`.

## 🤝 Contributing

See `CONTRIBUTING.md` for detailed guidelines on workflows, testing, and pull request expectations. Issues and PRs are welcome—just ensure Ruff/Pyright/tests pass before submitting.

## 📄 License

Released under the MIT License. See `LICENSE` for details.
