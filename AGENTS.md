# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: CLI entrypoint (Click). Analyzes a target project path.
- `core/agents/`: Provider adapters built on `BaseArchitect`.
- `core/analysis/`: Phase runners (`phase_1.py` … `final_analysis.py`).
- `core/utils/`: IO, formatting, file system helpers.
- `core/types/`: Typed configs (`ModelConfig`, `AgentConfig`).
- `config/`: Model selection (`agents.py`), exclusions, and prompts.
- `tests/`: Phase-specific runners and utilities. Example: `tests/phase_3_test/run_test.py`.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run analysis: `python main.py -p /path/to/target-project`
- Run all tests: `python -m unittest discover tests -v`
- Run a phase test: `python tests/phase_2_test/run_test.py`
- Env check: `python tests/test_env.py` (verifies API keys and `.env`)

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
