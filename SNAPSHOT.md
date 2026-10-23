<project_structure>
├── docs
│   ├── assets
│   │   └── media
│   ├── examples
│   │   └── phases_output
│   │       ├── final_analysis.md
│   │       ├── metrics.md
│   │       ├── phase1_discovery.md
│   │       ├── phase2_planning.md
│   │       ├── phase3_analysis.md
│   │       ├── phase4_synthesis.md
│   │       └── phase5_consolidation.md
│   ├── claude-code-runtime.md
│   ├── codex-runtime.md
│   ├── provider-model-audit-2026-10.md
│   ├── provider-model-lifecycle.md
│   ├── provider-system-prompts.md
│   └── structured-output-contracts.md
├── internal-docs/  # Internal documentation
├── scripts/  # Shell scripts
│   └── bootstrap_env.sh  # Script to set up virtual environment and install dependencies
├── src/  # Source code root
│   └── agentrules/  # Main package
│       ├── cli/  # Typer-based CLI implementation
│       │   ├── commands/  # CLI subcommand implementations
│       │   │   ├── __init__.py  # Commands package
│       │   │   ├── analyze.py  # `analyze` command implementation
│       │   │   ├── configure.py  # `configure` command implementation
│       │   │   ├── execplan.py  # `execplan` and `milestone` commands
│       │   │   ├── execplan_registry.py  # `execplan-registry` command
│       │   │   ├── keys.py  # `keys` command to show provider status
│       │   │   ├── scaffold.py  # `scaffold` command to sync templates
│       │   │   ├── snapshot.py  # `snapshot` command to manage snapshots
│       │   │   └── tree.py  # `tree` command to preview project structure
│       │   ├── services/  # CLI-specific business logic bridging core and UI
│       │   │   ├── __init__.py  # Services package
│       │   │   ├── claude_code_runtime.py
│       │   │   ├── codex_runtime.py  # Interaction with Codex local app-server
│       │   │   ├── configuration.py  # Interface to the core configuration manager
│       │   │   ├── output_validation.py  # Output filename validation logic
│       │   │   ├── pipeline_runner.py  # Executes the analysis pipeline
│       │   │   └── tree_preview.py  # Snapshot preview generator
│       │   ├── ui/  # Terminal user interface components
│       │   │   ├── settings/  # Interactive settings configuration menus
│       │   │   │   ├── exclusions/  # Exclusion rules UI
│       │   │   │   │   ├── __init__.py  # Exclusions menu
│       │   │   │   │   ├── editor.py  # Exclusion prompt helpers
│       │   │   │   │   ├── preview.py  # Tree preview for exclusion settings
│       │   │   │   │   └── summary.py  # Rich summary of exclusions
│       │   │   │   ├── models/  # Model presets UI
│       │   │   │   │   ├── __init__.py  # Models menu
│       │   │   │   │   ├── researcher.py  # Researcher specific model config
│       │   │   │   │   └── utils.py  # Shared model choice UI helpers
│       │   │   │   ├── __init__.py  # Settings package
│       │   │   │   ├── claude_code.py
│       │   │   │   ├── codex.py  # Codex runtime configuration UI
│       │   │   │   ├── logging.py  # Logging verbosity UI
│       │   │   │   ├── menu.py  # Settings top-level menu
│       │   │   │   ├── outputs.py  # Output generation preferences UI
│       │   │   │   └── providers.py  # Provider API key configuration UI
│       │   │   ├── __init__.py  # UI package
│       │   │   ├── analysis_view.py  # Rich-based UI for phase execution progress
│       │   │   ├── event_sink.py  # Bridges pipeline events to the UI
│       │   │   ├── main_menu.py  # Interactive main menu using questionary
│       │   │   └── styles.py  # Shared Questionary styles
│       │   ├── __init__.py  # CLI exports
│       │   ├── app.py  # Typer app definition and routing
│       │   ├── bootstrap.py  # Runtime bootstrapping (logging, config loading)
│       │   └── context.py  # Shared CLI context and helper functions
│       ├── config/  # Configuration definitions
│       │   ├── prompts/  # Prompt templates for analysis phases
│       │   │   ├── __init__.py  # Prompts package
│       │   │   ├── final_analysis_prompt.py  # Prompt for final rules generation
│       │   │   ├── phase_1_prompts.py  # Prompts for discovery agents
│       │   │   ├── phase_2_prompts.py  # Prompts for methodical planning
│       │   │   ├── phase_3_prompts.py  # Prompts for deep analysis of files
│       │   │   ├── phase_4_prompts.py  # Prompts for synthesis
│       │   │   └── phase_5_prompts.py  # Prompts for consolidation
│       │   ├── __init__.py  # Config package
│       │   ├── agents.py  # Model presets and mappings
│       │   ├── exclusions.py  # Default exclusion lists for directories, files, extensions
│       │   └── tools.py  # Definitions of available tools for models
│       ├── core/  # Core business logic and integrations
│       │   ├── agent_tools/  # Tooling implementations
│       │   │   ├── web_search/  # Web search tool implementations
│       │   │   │   ├── __init__.py  # Web search exports
│       │   │   │   └── tavily.py  # Tavily search integration
│       │   │   └── tool_manager.py  # Central manager for converting tools to provider schemas
│       │   ├── agents/  # Model provider integrations
│       │   │   ├── anthropic/  # Anthropic Claude integration
│       │   │   │   ├── __init__.py  # Anthropic package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for Anthropic
│       │   │   │   ├── capabilities.py  # Capability metadata for Claude models
│       │   │   │   ├── client.py  # Anthropic SDK wrapper
│       │   │   │   ├── prompting.py  # Anthropic prompt formatting
│       │   │   │   ├── request_builder.py  # Request construction for Anthropic
│       │   │   │   ├── response_parser.py  # Anthropic response parser
│       │   │   │   └── tooling.py  # Tool config resolution for Anthropic
│       │   │   ├── claude_code
│       │   │   │   ├── __init__.py
│       │   │   │   ├── architect.py
│       │   │   │   ├── client.py
│       │   │   │   ├── errors.py
│       │   │   │   ├── request_builder.py
│       │   │   │   └── response_parser.py
│       │   │   ├── codex/  # Codex App Server integration
│       │   │   │   ├── __init__.py  # Codex package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for Codex
│       │   │   │   ├── client.py  # JSON-RPC client for Codex app-server
│       │   │   │   ├── errors.py  # Codex specific exceptions
│       │   │   │   ├── model_selection.py
│       │   │   │   ├── models.py  # Dataclasses for Codex protocol types
│       │   │   │   ├── process.py  # Subprocess manager for Codex app-server
│       │   │   │   ├── protocol.py  # JSON-RPC protocol encoder/decoder
│       │   │   │   ├── reasoning.py
│       │   │   │   ├── request_builder.py  # Request construction for Codex
│       │   │   │   └── response_parser.py  # Codex turn notifications parser
│       │   │   ├── deepseek/  # DeepSeek integration
│       │   │   │   ├── __init__.py  # DeepSeek package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for DeepSeek
│       │   │   │   ├── client.py  # DeepSeek API client (OpenAI-compatible)
│       │   │   │   ├── compat.py  # Legacy DeepSeekAgent wrapper
│       │   │   │   ├── config.py  # DeepSeek default configurations
│       │   │   │   ├── prompting.py  # DeepSeek prompt formatting
│       │   │   │   ├── request_builder.py  # Request construction for DeepSeek
│       │   │   │   ├── response_parser.py  # DeepSeek response parser
│       │   │   │   └── tooling.py  # Tool config resolution for DeepSeek
│       │   │   ├── factory/  # Architect factory
│       │   │   │   ├── __init__.py  # Factory exports
│       │   │   │   └── factory.py  # Instantiates specific architect based on config
│       │   │   ├── gemini/  # Google Gemini integration
│       │   │   │   ├── __init__.py  # Gemini package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for Gemini
│       │   │   │   ├── capabilities.py  # Capability metadata for Gemini models
│       │   │   │   ├── client.py  # Gemini API client wrapper
│       │   │   │   ├── errors.py  # Gemini specific exceptions
│       │   │   │   ├── legacy.py  # Legacy GeminiAgent wrapper
│       │   │   │   ├── prompting.py  # Gemini prompt formatting
│       │   │   │   ├── response_parser.py  # Gemini response parser
│       │   │   │   └── tooling.py  # Tool config resolution for Gemini
│       │   │   ├── ollama/  # Ollama integration (directory placeholder)
│       │   │   ├── openai/  # OpenAI integration
│       │   │   │   ├── __init__.py  # OpenAI package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for OpenAI
│       │   │   │   ├── capabilities.py
│       │   │   │   ├── client.py  # OpenAI SDK wrapper
│       │   │   │   ├── compat.py  # Legacy OpenAIAgent wrapper
│       │   │   │   ├── config.py  # OpenAI default configurations
│       │   │   │   ├── request_builder.py  # Request construction for OpenAI
│       │   │   │   └── response_parser.py  # OpenAI response parser
│       │   │   ├── xai/  # xAI (Grok) integration
│       │   │   │   ├── __init__.py  # xAI package
│       │   │   │   ├── architect.py  # BaseArchitect implementation for xAI
│       │   │   │   ├── client.py  # xAI API client (OpenAI-compatible)
│       │   │   │   ├── config.py  # xAI default configurations
│       │   │   │   ├── prompting.py  # xAI prompt formatting
│       │   │   │   ├── request_builder.py  # Request construction for xAI
│       │   │   │   ├── response_parser.py  # xAI response parser
│       │   │   │   └── tooling.py  # Tool config resolution for xAI
│       │   │   ├── __init__.py  # Agents package exports
│       │   │   └── base.py  # Abstract BaseArchitect interface
│       │   ├── analysis/  # Analysis phase orchestration
│       │   │   ├── __init__.py  # Analysis package
│       │   │   ├── events.py  # Event system for UI updates
│       │   │   ├── final_analysis.py  # Final AGENTS.md generation logic
│       │   │   ├── phase_1.py  # Initial discovery and research logic
│       │   │   ├── phase_2.py  # Analysis planning logic
│       │   │   ├── phase_3.py  # Deep code analysis logic in batches
│       │   │   ├── phase_4.py  # Synthesis logic
│       │   │   └── phase_5.py  # Consolidation logic
│       │   ├── configuration/  # Application configuration manager
│       │   │   ├── services/  # Configuration sub-services
│       │   │   │   ├── __init__.py  # Config services package
│       │   │   │   ├── claude_code.py
│       │   │   │   ├── codex.py  # Codex runtime config getters/setters
│       │   │   │   ├── exclusions.py  # Exclusion overrides getters/setters
│       │   │   │   ├── features.py  # Feature toggles getters/setters
│       │   │   │   ├── logging.py  # Logging config getters/setters
│       │   │   │   ├── outputs.py  # Output options getters/setters
│       │   │   │   ├── phase_models.py  # Phase model overrides getters/setters
│       │   │   │   └── providers.py  # Provider credentials getters/setters
│       │   │   ├── __init__.py  # Configuration package exports
│       │   │   ├── constants.py  # Default config values and ENV var names
│       │   │   ├── environment.py  # Environment variable abstraction
│       │   │   ├── manager.py  # ConfigManager facade
│       │   │   ├── model_presets.py  # Available model presets and runtime resolving
│       │   │   ├── models.py  # Data structures for CLI configuration
│       │   │   ├── repository.py  # TOML file reading and writing
│       │   │   ├── serde.py  # Config serialization logic
│       │   │   └── utils.py  # Type coercion for config values
│       │   ├── execplan/  # Execution Plan domain logic
│       │   │   ├── templates/  # ExecPlan templates
│       │   │   │   ├── EXECPLAN_TEMPLATE.md
│       │   │   │   └── MILESTONE_FILE_TEMPLATE.md
│       │   │   ├── __init__.py  # ExecPlan package
│       │   │   ├── creator.py  # Creates and completes ExecPlans
│       │   │   ├── identity.py  # ExecPlan filename parsing
│       │   │   ├── locks.py  # Legacy file locking (now no-ops)
│       │   │   ├── milestones.py  # Manages ExecPlan milestones
│       │   │   ├── paths.py  # Path resolution and layout classification
│       │   │   └── registry.py  # Builds the ExecPlan JSON registry
│       │   ├── logging/  # Custom logging setup
│       │   │   ├── __init__.py  # Logging package
│       │   │   └── config.py  # Rich logger setup and filters
│       │   ├── pipeline/  # Pipeline orchestrator
│       │   │   ├── __init__.py  # Pipeline package
│       │   │   ├── config.py  # Data models for pipeline settings and results
│       │   │   ├── factory.py  # Builds default analysis pipeline
│       │   │   ├── orchestrator.py  # Executes all phases sequentially
│       │   │   ├── output.py  # Writes pipeline artifacts to disk
│       │   │   ├── project_profile.py
│       │   │   └── snapshot.py  # Collects project metadata before pipeline runs
│       │   ├── streaming/  # Shared streaming primitives
│       │   │   ├── __init__.py  # Streaming package
│       │   │   └── types.py  # Types for streaming chunks and events
│       │   ├── types/  # Core type definitions
│       │   │   ├── __init__.py  # Types package
│       │   │   ├── agent_config.py  # Agent configurations
│       │   │   ├── models.py  # Definitions for model configs
│       │   │   └── tool_config.py  # Definitions for tool schemas
│       │   ├── utils/  # Core utilities
│       │   │   ├── dependency_scanner/  # Parses dependency manifests
│       │   │   │   ├── parsers/  # Language-specific parsers
│       │   │   │   │   ├── __init__.py  # Parsers package
│       │   │   │   │   ├── clojure.py  # Clojure parser
│       │   │   │   │   ├── dart.py  # Dart parser
│       │   │   │   │   ├── dotnet.py  # .NET parser
│       │   │   │   │   ├── elixir.py  # Elixir parser
│       │   │   │   │   ├── generic.py  # Fallback text parser
│       │   │   │   │   ├── go.py  # Go parser
│       │   │   │   │   ├── helpers.py  # Common parsing helpers
│       │   │   │   │   ├── java.py  # Java/Kotlin parser
│       │   │   │   │   ├── javascript.py  # JavaScript/TypeScript parser
│       │   │   │   │   ├── php.py  # PHP parser
│       │   │   │   │   ├── python.py  # Python parser
│       │   │   │   │   ├── ruby.py  # Ruby parser
│       │   │   │   │   ├── swift.py  # Swift parser
│       │   │   │   │   └── toml_based.py  # Generic TOML parser
│       │   │   │   ├── __init__.py  # Scanner package
│       │   │   │   ├── constants.py  # Manifest file patterns
│       │   │   │   ├── discovery.py  # Locates manifests
│       │   │   │   ├── metadata.py  # Dependency summary builders
│       │   │   │   ├── models.py  # Dependency scanner types
│       │   │   │   ├── registry.py  # Maps parsers to file patterns
│       │   │   │   └── scan.py  # Orchestrates dependency scanning
│       │   │   ├── file_creation/  # Functions to write output files
│       │   │   │   ├── templates/  # File creation templates
│       │   │   │   │   ├── MILESTONE_TEMPLATE.md
│       │   │   │   │   └── PLANS.md
│       │   │   │   ├── agent_scaffold.py  # Generates the .agent directory scaffold
│       │   │   │   ├── atomic_write.py  # Atomically writes file contents
│       │   │   │   ├── cursorignore.py  # CLI and helper for managing .cursorignore
│       │   │   │   ├── phases_output.py  # Dumps individual phase outputs
│       │   │   │   ├── snapshot_artifact.py  # Generates SNAPSHOT.md with comments
│       │   │   │   └── snapshot_policy.py  # Paths excluded from snapshots
│       │   │   ├── file_system/  # Interacting with project files
│       │   │   │   ├── __init__.py  # File system package
│       │   │   │   ├── file_retriever.py  # Collects file paths and contents
│       │   │   │   ├── gitignore.py  # Gitignore file matcher
│       │   │   │   └── tree_generator.py  # Generates ASCII project trees
│       │   │   ├── formatters/  # Text formatters
│       │   │   │   ├── __init__.py  # Formatters package
│       │   │   │   └── clean_agentrules.py  # Cleans AGENTS.md output
│       │   │   ├── parsers/  # LLM output parsers
│       │   │   │   ├── __init__.py  # Parsers package
│       │   │   │   └── agent_parser.py  # Parses agent plans from Phase 2
│       │   │   ├── async_stream.py  # Adapts synchronous streams to async generators
│       │   │   ├── constants.py  # File constants
│       │   │   ├── model_config_helper.py  # Utility to find string name for model config
│       │   │   ├── offline.py  # Offline stubs for testing without network
│       │   │   ├── provider_capabilities.py  # Helpers for provider branching
│       │   │   ├── provider_utils.py
│       │   │   ├── release_metadata.py  # Validation script for GitHub tag releases
│       │   │   ├── structured_outputs.py  # JSON Schema builders for providers
│       │   │   ├── system_prompt.py  # Default system prompt formatter
│       │   │   ├── token_estimator.py  # Heuristic and tiktoken estimators
│       │   │   └── token_packer.py  # Batches files to respect context windows
│       │   └── __init__.py  # Core package
│       ├── __init__.py  # Package initialization
│       └── __main__.py  # Entry point for `python -m agentrules`
├── tests/  # Test suite
│   ├── fakes/  # Fake services for tests
│   │   ├── codex_app_server.py  # Fake Codex app-server for unit tests
│   │   └── vendor_responses.py  # Fake vendor SDK response objects
│   ├── final_analysis_test/  # Final phase tests
│   │   ├── output/  # Output artifacts
│   │   │   ├── cursor_rules.md
│   │   │   └── final_analysis_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── fa_test_input.json  # Mock input data for final analysis
│   │   ├── run_test.py  # Standalone final analysis runner
│   │   ├── test_date.py  # Date format testing
│   │   └── test_final_offline.py  # Offline tests for final analysis
│   ├── live/  # Tests hitting live APIs
│   │   ├── test_claude_code_live_smoke.py
│   │   ├── test_codex_live_smoke.py  # Live smoke tests for Codex integration
│   │   └── test_provider_model_live_smoke.py
│   ├── offline/  # Offline pipeline tests
│   │   ├── __init__.py  # Test package
│   │   └── test_offline_smoke.py  # Offline pipeline tests using DummyArchitect
│   ├── phase_1_test/  # Phase 1 tests
│   │   ├── output/  # Output artifacts
│   │   │   └── phase1_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── run_test.py  # Standalone phase 1 runner
│   │   ├── test_phase1_gemini_tool_turn.py
│   │   ├── test_phase1_offline.py  # Offline tests for phase 1
│   │   ├── test_phase1_profile_agents.py
│   │   └── test_phase1_researcher_guards.py  # Tests for researcher constraints
│   ├── phase_2_test/  # Phase 2 tests
│   │   ├── output/  # Output artifacts
│   │   │   ├── analysis_plan.xml  # Example output
│   │   │   └── phase2_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── run_test.py  # Standalone phase 2 runner
│   │   ├── test2_input.json  # Mock input data
│   │   └── test_phase2_offline.py  # Offline tests for phase 2
│   ├── phase_3_test/  # Phase 3 tests
│   │   ├── output/  # Output artifacts
│   │   │   └── phase3_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── debug_parser.py  # Standalone parser debug script
│   │   ├── run_test.py  # Standalone phase 3 runner
│   │   ├── test3_input.json  # Mock input data
│   │   ├── test3_input.xml  # Mock input data
│   │   └── test_phase3_offline.py  # Offline tests for phase 3
│   ├── phase_4_test/  # Phase 4 tests
│   │   ├── output/  # Output artifacts
│   │   │   ├── analysis.md
│   │   │   └── phase4_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── run_test.py  # Standalone phase 4 runner
│   │   ├── test4_input.json  # Mock input data
│   │   └── test_phase4_offline.py  # Offline tests for phase 4
│   ├── phase_5_test/  # Phase 5 tests
│   │   ├── output/  # Output artifacts
│   │   │   ├── consolidated_report.md
│   │   │   └── phase5_results.json  # Example output
│   │   ├── __init__.py  # Test package
│   │   ├── run_test.py  # Standalone phase 5 runner
│   │   ├── test5_input.json  # Mock input data
│   │   └── test_phase5_offline.py  # Offline tests for phase 5
│   ├── tests_input/  # Mock codebase used as test input
│   │   ├── phases_output/  # Mock phase outputs directory
│   │   ├── index.html  # Mock HTML file
│   │   └── main.py  # Mock Python file
│   ├── unit/  # Unit tests
│   │   ├── agents/  # Agent provider unit tests
│   │   │   ├── __init__.py  # Agents test package
│   │   │   ├── test_anthropic_agent_parsing.py  # Tests for Anthropic parser
│   │   │   ├── test_anthropic_capabilities.py  # Tests for Anthropic capability flags
│   │   │   ├── test_anthropic_client_compat.py  # Tests for Anthropic client
│   │   │   ├── test_anthropic_latest_contract.py
│   │   │   ├── test_anthropic_request_builder.py  # Tests for Anthropic request building
│   │   │   ├── test_claude_code_architect.py
│   │   │   ├── test_claude_code_client.py
│   │   │   ├── test_claude_code_request_builder.py
│   │   │   ├── test_claude_code_response_parser.py
│   │   │   ├── test_codex_architect.py  # Tests for Codex architect
│   │   │   ├── test_codex_client.py  # Tests for Codex client
│   │   │   ├── test_codex_request_builder.py  # Tests for Codex request building
│   │   │   ├── test_deepseek_agent_parsing.py  # Tests for DeepSeek parser
│   │   │   ├── test_deepseek_helpers.py  # Tests for DeepSeek helpers
│   │   │   ├── test_gemini_agent_parsing.py  # Tests for Gemini parser
│   │   │   ├── test_gemini_capabilities.py  # Tests for Gemini capability flags
│   │   │   ├── test_openai_agent_parsing.py  # Tests for OpenAI parser
│   │   │   ├── test_openai_gpt6_contract.py
│   │   │   ├── test_openai_helpers.py  # Tests for OpenAI helpers
│   │   │   ├── test_system_prompt_policy.py  # Tests for system prompt handling
│   │   │   ├── test_token_logging.py  # Tests for token usage logging
│   │   │   └── test_xai_helpers.py  # Tests for xAI helpers
│   │   ├── analysis/  # Analysis logic unit tests
│   │   │   └── test_phase3_packing.py  # Tests for batch token packing
│   │   ├── utils
│   │   │   ├── test_provider_capabilities.py
│   │   │   ├── test_provider_utils.py
│   │   │   ├── test_structured_outputs.py
│   │   │   ├── test_token_estimator.py
│   │   │   └── test_token_packer.py
│   │   ├── __init__.py  # Unit test package
│   │   ├── test_agent_parser_basic.py  # Unit tests for agent plan extraction
│   │   ├── test_agent_scaffold.py  # Unit tests for scaffold generation
│   │   ├── test_agents_anthropic_parse.py  # Unit tests for Anthropic response parsing
│   │   ├── test_agents_deepseek.py  # Unit tests for DeepSeek architect
│   │   ├── test_agents_gemini_error.py  # Unit tests for Gemini error cases
│   │   ├── test_agents_openai_params.py  # Unit tests for OpenAI params
│   │   ├── test_analysis_view.py  # Unit tests for terminal UI tracking
│   │   ├── test_clean_agentrules.py  # Unit tests for AGENTS.md cleaning
│   │   ├── test_cli.py  # Unit tests for Typer commands
│   │   ├── test_cli_claude_code_settings.py
│   │   ├── test_cli_codex_settings.py  # Unit tests for Codex settings UI
│   │   ├── test_cli_model_picker_ui.py  # Unit tests for model selection UI
│   │   ├── test_codex_runtime_service.py  # Unit tests for Codex runtime sync wrapper
│   │   ├── test_config_service.py  # Unit tests for configuration manager
│   │   ├── test_dependency_scanner.py  # Unit tests for manifest finding and parsing
│   │   ├── test_dependency_scanner_registry.py  # Unit tests for scanner registry
│   │   ├── test_execplan_cli.py  # Unit tests for execplan command
│   │   ├── test_execplan_creator.py  # Unit tests for creating ExecPlans
│   │   ├── test_execplan_identity.py  # Unit tests for parsing plan paths
│   │   ├── test_execplan_milestone_cli.py  # Unit tests for milestone CLI commands
│   │   ├── test_execplan_milestones.py  # Unit tests for milestone manipulation
│   │   ├── test_execplan_paths.py  # Unit tests for detecting ExecPlan files
│   │   ├── test_execplan_registry.py  # Unit tests for tracking plans in a JSON file
│   │   ├── test_execplan_registry_cli.py  # Unit tests for registry CLI command
│   │   ├── test_file_retriever.py  # Unit tests for getting file contents
│   │   ├── test_final_analysis_prompt.py  # Unit tests for final prompt rendering
│   │   ├── test_gemini_current_presets.py
│   │   ├── test_model_config_helper.py  # Unit tests for config name lookup
│   │   ├── test_model_overrides.py  # Unit tests for overriding defaults
│   │   ├── test_openai_lifecycle.py
│   │   ├── test_output_validation.py  # Unit tests for filename validations
│   │   ├── test_phase_events.py  # Unit tests for event emission in phases
│   │   ├── test_phase_prompt_separation.py  # Unit tests for prompt templating
│   │   ├── test_phases_edges.py  # Unit tests for edge cases across all phases
│   │   ├── test_phases_output.py  # Unit tests for saving phase artifacts
│   │   ├── test_pipeline_orchestrator.py
│   │   ├── test_pipeline_output_writer.py  # Unit tests for full pipeline execution output
│   │   ├── test_pipeline_snapshot.py  # Unit tests for grabbing project state before pipeline runs
│   │   ├── test_project_profile.py
│   │   ├── test_provider_model_compatibility_matrix.py
│   │   ├── test_release_metadata.py  # Unit tests for the release script
│   │   ├── test_settings_output_validation.py  # Unit tests for validating custom output filenames
│   │   ├── test_snapshot_artifact.py  # Unit tests for writing the snapshot
│   │   ├── test_streaming_support.py  # Unit tests for response streaming
│   │   ├── test_tavily_tool.py  # Unit tests for Tavily search
│   │   ├── test_tool_manager.py  # Unit tests for tool format conversion
│   │   └── test_tree_generator.py  # Unit tests for directory tree generation
│   ├── utils/  # Test helper utilities
│   │   ├── inputs/  # Mock input folder
│   │   │   └── .cursorrules
│   │   ├── outputs
│   │   ├── __init__.py  # Package init
│   │   ├── clean_cr_test.py  # Standalone script testing the format cleaner
│   │   ├── offline_stubs.py  # Dummy architects for testing
│   │   └── run_tree_generator.py  # Standalone script to test tree generator
│   ├── __init__.py  # Test initializer
│   ├── test_cli_services.py  # Unit tests for CLI services
│   ├── test_env.py  # Simple script to verify loaded environment variables
│   ├── test_openai_responses.py  # Unit tests for OpenAI Responses API
│   └── test_smoke_discovery.py  # Simple smoke test
├── typings/  # External type stubs
│   ├── google/  # Type stubs for google module
│   │   ├── genai/  # Type stubs for genai module
│   │   │   ├── __init__.pyi  # Type stub init
│   │   │   └── types.pyi  # Type stubs for genai types
│   │   ├── protobuf/  # Type stubs for protobuf module
│   │   │   ├── __init__.pyi  # Type stub init
│   │   │   └── struct_pb2.pyi  # Type stubs for struct_pb2
│   │   └── __init__.pyi  # Type stub init
│   ├── tavily/  # Type stubs for tavily module
│   │   └── __init__.pyi  # Type stub init
│   └── tomli_w/  # Type stubs for tomli_w module
│       └── __init__.pyi  # Type stub init
├── .release-please-config.json
├── .release-please-manifest.json
├── CHANGELOG.md
├── conftest.py  # pytest configuration, sets up live test markers
├── CONTRIBUTING.md
├── pyproject.toml  # Python project metadata and dependencies
├── requirements-dev.txt  # Development dependencies
└── uv.lock  # Dependency lock file
</project_structure>
