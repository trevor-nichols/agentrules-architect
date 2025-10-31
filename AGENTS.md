# Repository Guidelines

You are a professional software engineer in charge of the cursorrules-architect project.

# Development Guidelines
- run type-check (pyright) and linting (ruff check) commands after you edit or create files to check for errors.
- Use PEP 8 guidance
- Maintain a clean and readable codebase.
- Follow modern professional software engineering practices.

## Project Structure & Module Organization
- `main.py`: Typer entrypoint that forwards to the `agentrules` CLI app.
- `agentrules/cli/`: Modular Typer CLI package with command handlers, Questionary UI flows, and shared services.
- `core/agents/`: Provider adapters built on `BaseArchitect`.
- `core/analysis/`: Phase runners (`phase_1.py` … `final_analysis.py`).
- `core/utils/`: IO, formatting, file system helpers.
- `core/types/`: Typed configs (`ModelConfig`, `AgentConfig`).
- `config/`: Model selection (`agents.py`), exclusions, and prompts.
- `tests/`: Phase-specific runners and utilities. Example: `tests/phase_3_test/run_test.py`.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install deps (editing locally): `pip install -e .[dev]`
- Run interactive CLI: `agentrules`
- Run analysis directly: `agentrules analyze /path/to/target-project`
- Run all tests: `python -m unittest discover tests -v`
- Run a phase test: `python tests/phase_2_test/run_test.py`
- Env check: `python tests/test_env.py` (verifies API keys and `.env`)

## CLI Overview
- **Entry command**: Installing in editable mode registers the `agentrules` executable. Running it without arguments opens an interactive menu covering analysis, key configuration, and per-phase model overrides.
- **Interactive configuration**: The "Configure provider API keys" flow lets you pick a provider, enter a key, and persists it to `~/.config/agentrules/config.toml` (or `AGENTRULES_CONFIG_DIR`). Keys are mirrored into environment variables for subsequent runs.
- **Model presets**: "Configure models per phase" presents each phase (with Phase 1 broken into General vs. Researcher agents). Selecting a phase first chooses a base model, then—when multiple variants exist—prompts for effort/temperature settings. Selections are persisted in the same TOML file and applied at startup via `agentrules/model_config.py`.
- **Offline mode**: `agentrules analyze --offline …` (or `OFFLINE=1`) swaps in deterministic dummy architects and mocked Tavily calls for local smoke tests without provider traffic.
- **Outputs**: Successful runs write `.cursorrules`, `.cursorignore`, and phase-specific markdown files under `<target>/phases_output`, while logging progress via Rich spinners.

## Coding Style & Naming Conventions
- PEP 8, 4-space indentation, explicit type hints.
- Modules/functions: `snake_case`; classes: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
- Keep functions small and pure; fail fast on invalid inputs.
- Place prompts in `config/prompts/`; provider logic in `core/agents/`; avoid cross-layer imports.

## Testing Guidelines
- Framework: stdlib `unittest` + phase runners under `tests/*/run_test.py`.
- Add unit tests near related phase or util; name as `test_*.py`.
- Keep tests deterministic; store fixtures under `tests/**/` (see `test*_input.json`).
- Run `python -m unittest` before opening a PR.

## Commit & Pull Request Guidelines
- Git history favors short, descriptive messages; emojis appear occasionally. Prefer Conventional Commits for clarity (e.g., `feat:`, `fix:`, `docs:`).
- Commits: imperative mood, concise subject (<72 chars), explain rationale in body when helpful.
- PRs: include summary, linked issues, test plan (commands + results), and notes on config/docs updates. Keep diffs focused; add screenshots only when UI/docs output changes are relevant.

## Security & Configuration Tips
- API keys via env vars or `.env` (see `tests/test_env.py`). Never commit secrets.
- Update model choices in `config/agents.py`; exclusions in `config/exclusions.py`.
- Keep dependencies minimal; do not introduce networked tests.

## Agent-Specific Notes
- To add a model/provider: extend `core/agents/*` using `BaseArchitect`, add config in `core/types/models.py` and `config/agents.py`, and supply prompts in `config/prompts/`.
