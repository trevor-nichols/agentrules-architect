.
├── __init__.py                # Package initializer for agentrules, filters warnings.
├── __main__.py                # Main entry point for running the agentrules CLI application.
├── analyzer.py                # Core orchestration logic for the multi-phase analysis pipeline.
├── cli/                       # Contains all code related to the command-line interface.
│   ├── __init__.py            # CLI package initializer.
│   ├── app.py                 # Defines the main Typer application and registers subcommands.
│   ├── bootstrap.py           # Initializes the CLI runtime environment (logging, config, .env).
│   ├── commands/              # Defines the subcommands for the CLI.
│   │   ├── __init__.py        # Commands package initializer.
│   │   ├── analyze.py         # Implements the 'analyze' subcommand.
│   │   ├── configure.py       # Implements the 'configure' subcommand for settings.
│   │   └── keys.py            # Implements the 'keys' subcommand to display provider API keys.
│   ├── context.py             # Defines a shared context object and helpers for the CLI.
│   ├── services/              # Contains business logic used by the CLI commands.
│   │   ├── __init__.py        # Services package initializer.
│   │   ├── configuration.py   # Service layer for managing application settings.
│   │   └── pipeline_runner.py # Service for executing the analysis pipeline from the CLI.
│   └── ui/                    # Contains user interface components for the CLI.
│       ├── __init__.py        # UI package initializer.
│       ├── analysis_view.py   # Renders analysis progress using the Rich library.
│       ├── main_menu.py       # Implements the interactive main menu for the CLI.
│       ├── settings/          # Interactive flows for configuring different application settings.
│       │   ├── __init__.py    # Settings UI package initializer.
│       │   ├── exclusions/    # UI flows for managing file and directory exclusion rules.
│       │   │   ├── __init__.py # Main interactive flow for configuring exclusion rules.
│       │   │   ├── editor.py  # Prompt helpers for adding or removing exclusion entries.
│       │   │   └── summary.py # Renders a table summarizing current exclusion rules.
│       │   ├── logging.py     # Interactive flow for configuring logging verbosity.
│       │   ├── menu.py        # The main settings menu that navigates to other settings pages.
│       │   ├── models/        # UI flows for configuring which AI models to use for each phase.
│       │   │   ├── __init__.py # Main interactive flow for configuring model presets.
│       │   │   ├── researcher.py # Specific UI flow for configuring the researcher agent model.
│       │   │   └── utils.py   # Shared utilities for building model selection prompts.
│       │   ├── outputs.py     # Interactive flow for configuring output generation preferences.
│       │   └── providers.py   # Interactive flow for managing provider API keys.
│       └── styles.py          # Defines shared styles for Questionary prompts.
├── config/                    # Contains default configurations like prompts, models, and exclusions.
│   ├── __init__.py            # Config package initializer.
│   ├── agents.py              # Defines available AI model configurations and presets for analysis phases.
│   ├── exclusions.py          # Defines default lists of excluded directories, files, and extensions.
│   ├── prompts/               # Contains prompt templates for each analysis phase.
│   │   ├── __init__.py        # Prompts package initializer.
│   │   ├── final_analysis_prompt.py # Prompt template for the final analysis phase.
│   │   ├── phase_1_prompts.py # Prompt templates for Phase 1 (Initial Discovery).
│   │   ├── phase_2_prompts.py # Prompt template for Phase 2 (Methodical Planning).
│   │   ├── phase_3_prompts.py # Prompt template for Phase 3 (Deep Analysis).
│   │   ├── phase_4_prompts.py # Prompt template for Phase 4 (Synthesis).
│   │   └── phase_5_prompts.py # Prompt template for Phase 5 (Consolidation).
│   └── tools.py               # Defines tool configurations for use by AI agents.
├── core/                      # Contains the core application logic for analysis and agent interaction.
│   ├── __init__.py            # Core package initializer.
│   ├── agent_tools/           # Tools that AI agents can use, such as web search.
│   │   ├── tool_manager.py    # Manages and converts tool definitions for different AI providers.
│   │   └── web_search/        # Contains web search tool implementations.
│   │       ├── __init__.py    # Web search tools package initializer.
│   │       └── tavily.py      # Implements web search functionality using the Tavily API.
│   ├── agents/                # Contains AI agent implementations for different providers.
│   │   ├── __init__.py        # Agents package initializer, exports factory function.
│   │   ├── anthropic/         # Implementation for Anthropic (Claude) models.
│   │   │   ├── __init__.py    # Exports the Anthropic architect class.
│   │   │   ├── architect.py   # Main implementation of the BaseArchitect for Anthropic models.
│   │   │   ├── client.py      # Manages the Anthropic SDK client.
│   │   │   ├── prompting.py   # Prompt formatting helpers for Anthropic models.
│   │   │   ├── request_builder.py # Constructs API request payloads for Anthropic.
│   │   │   ├── response_parser.py # Parses and normalizes responses from Anthropic.
│   │   │   └── tooling.py     # Tool configuration helpers for Anthropic.
│   │   ├── base.py            # Defines the abstract BaseArchitect class for all AI models.
│   │   ├── deepseek/          # Implementation for DeepSeek models.
│   │   │   ├── __init__.py    # Exports the DeepSeek architect class.
│   │   │   ├── architect.py   # Main implementation of the BaseArchitect for DeepSeek models.
│   │   │   ├── client.py      # Manages the DeepSeek API client (via OpenAI SDK).
│   │   │   ├── compat.py      # Backwards compatibility wrapper for legacy DeepSeekAgent.
│   │   │   ├── config.py      # Model-specific defaults and configuration for DeepSeek.
│   │   │   ├── prompting.py   # Prompt formatting helpers for DeepSeek models.
│   │   │   ├── request_builder.py # Constructs API request payloads for DeepSeek.
│   │   │   ├── response_parser.py # Parses and normalizes responses from DeepSeek.
│   │   │   └── tooling.py     # Tool configuration helpers for DeepSeek.
│   │   ├── factory/           # Factory for creating AI agent instances.
│   │   │   ├── __init__.py    # Factory package initializer.
│   │   │   └── factory.py     # Implements the factory for creating architect instances based on config.
│   │   ├── gemini/            # Implementation for Google Gemini models.
│   │   │   ├── __init__.py    # Exports the Gemini architect class.
│   │   │   ├── architect.py   # Main implementation of the BaseArchitect for Gemini models.
│   │   │   ├── client.py      # Manages the Gemini SDK client.
│   │   │   ├── errors.py      # Defines custom exceptions for the Gemini provider.
│   │   │   ├── legacy.py      # Backwards compatibility wrapper for legacy GeminiAgent.
│   │   │   ├── prompting.py   # Prompt formatting helpers for Gemini models.
│   │   │   ├── response_parser.py # Parses and normalizes responses from Gemini.
│   │   │   └── tooling.py     # Tool configuration helpers for Gemini.
│   │   ├── openai/            # Implementation for OpenAI models.
│   │   │   ├── __init__.py    # Exports the OpenAI architect class.
│   │   │   ├── architect.py   # Main implementation of the BaseArchitect for OpenAI models.
│   │   │   ├── client.py      # Manages the OpenAI SDK client.
│   │   │   ├── compat.py      # Backwards compatibility wrapper for legacy OpenAIAgent.
│   │   │   ├── config.py      # Model-specific defaults and configuration for OpenAI.
│   │   │   ├── request_builder.py # Constructs API request payloads for OpenAI.
│   │   │   └── response_parser.py # Parses and normalizes responses from OpenAI.
│   │   └── xai/               # Implementation for xAI (Grok) models.
│   │       ├── __init__.py    # Exports the xAI architect class.
│   │       ├── architect.py   # Main implementation of the BaseArchitect for xAI models.
│   │       ├── client.py      # Manages the xAI API client (via OpenAI SDK).
│   │       ├── config.py      # Model-specific defaults and configuration for xAI.
│   │       ├── prompting.py   # Prompt formatting helpers for xAI models.
│   │       ├── request_builder.py # Constructs API request payloads for xAI.
│   │       ├── response_parser.py # Parses and normalizes responses from xAI.
│   │       └── tooling.py     # Tool configuration helpers for xAI.
│   ├── analysis/              # Contains the logic for each phase of the analysis pipeline.
│   │   ├── __init__.py        # Exports all analysis phase classes.
│   │   ├── events.py          # Defines data classes for events emitted during analysis.
│   │   ├── final_analysis.py  # Implements the logic for the final analysis phase.
│   │   ├── phase_1.py         # Implements the logic for Phase 1 (Initial Discovery).
│   │   ├── phase_2.py         # Implements the logic for Phase 2 (Methodical Planning).
│   │   ├── phase_3.py         # Implements the logic for Phase 3 (Deep Analysis).
│   │   ├── phase_4.py         # Implements the logic for Phase 4 (Synthesis).
│   │   └── phase_5.py         # Implements the logic for Phase 5 (Consolidation).
│   ├── configuration/         # Runtime configuration package used by CLI and analyzer flows.
│   │   ├── __init__.py        # Exposes ConfigManager singleton and shared constants.
│   │   ├── constants.py       # Paths, env var names, and other config constants.
│   │   ├── environment.py     # Applies persisted settings to process environment/logging.
│   │   ├── manager.py         # Facade coordinating repositories, services, and environment.
│   │   ├── models.py          # Dataclasses representing persisted CLI configuration.
│   │   ├── repository.py      # TOML-backed persistence adapter for configuration.
│   │   ├── serde.py           # Conversion helpers between dataclasses and dict payloads.
│   │   ├── model_presets.py   # Maps user selections to concrete model preset configs.
│   │   ├── utils.py           # Coercion/validation helpers shared across services.
│   │   └── services/          # Domain-specific helpers for providers, outputs, exclusions, etc.
│   │       ├── __init__.py
│   │       ├── exclusions.py
│   │       ├── features.py
│   │       ├── logging.py
│   │       ├── outputs.py
│   │       ├── phase_models.py
│   │       └── providers.py
│   ├── streaming.py           # Defines common data structures for model response streaming.
│   ├── types/                 # Contains shared data type definitions.
│   │   ├── __init__.py        # Exports core type definitions.
│   │   ├── agent_config.py    # Defines a TypedDict for agent configurations.
│   │   ├── models.py          # Defines the ModelConfig type and various preset model configurations.
│   │   └── tool_config.py     # Defines TypedDicts for tool configurations.
│   ├── logging/               # Central logging configuration helpers.
│   │   ├── __init__.py        # Exports the Rich logging configuration facade.
│   │   └── config.py          # Configures Rich handlers and request filters.
│   └── utils/                 # Contains various utility functions.
│       ├── async_stream.py    # Helper to adapt synchronous streaming iterators to async generators.
│       ├── constants.py       # Defines shared constants like default filenames.
│       ├── dependency_scanner/ # Modular dependency manifest scanner.
│       │   ├── __init__.py    # Exports public API and registry builder.
│       │   ├── constants.py   # Shared manifest filename and pattern constants.
│       │   ├── discovery.py   # Finds manifest files while respecting exclusion rules.
│       │   ├── metadata.py    # Helper utilities for manifest typing and summaries.
│       │   ├── models.py      # Dataclasses describing parsed manifests.
│       │   ├── registry.py    # Parser registry and registration primitives.
│       │   ├── scan.py        # Orchestrates discovery, parsing, and summary building.
│       │   └── parsers/       # Ecosystem-specific manifest parsers.
│       │       ├── __init__.py    # Builds and registers all default parsers.
│       │       ├── helpers.py     # Shared parser utilities such as excerpt trimming.
│       │       ├── python.py      # Python manifests: requirements, pyproject, setup.*.
│       │       ├── javascript.py  # npm/yarn manifests (package.json).
│       │       ├── php.py         # Composer manifests (composer.json).
│       │       ├── go.py          # Go module manifests (go.mod).
│       │       ├── java.py        # Java/Kotlin manifests (Gradle, Maven).
│       │       ├── dotnet.py      # .NET SDK project manifests (*.csproj, *.fsproj, *.vbproj).
│       │       ├── ruby.py        # Gemfile and gemspec manifests.
│       │       ├── swift.py       # Swift Package Manager manifests.
│       │       ├── elixir.py      # Elixir mix.exs manifests.
│       │       ├── clojure.py     # Clojure deps.edn and project.clj manifests.
│       │       ├── dart.py        # Dart and Flutter manifest files (pubspec.yaml).
│       │       ├── toml_based.py  # Cargo.toml, Project.toml, and generic TOML support.
│       │       └── generic.py     # Fallback parser for unclassified manifests.
│       ├── file_creation/     # Utilities that create files as part of the output.
│       │   ├── cursorignore.py # Manages the creation and content of .cursorignore files.
│       │   └── phases_output.py # Saves the output of each analysis phase to separate files.
│       ├── file_system/       # Utilities for file system operations.
│       │   ├── __init__.py    # Exports file system utility functions.
│       │   ├── file_retriever.py # Retrieves and formats file contents from a project directory.
│       │   ├── gitignore.py   # Loads and applies .gitignore patterns.
│       │   └── tree_generator.py # Generates an ASCII tree representation of the project structure.
│       ├── formatters/        # Utilities for formatting output files.
│       │   ├── __init__.py    # Formatters package initializer.
│       │   └── clean_agentrules.py # Cleans the generated rules file to ensure correct format.
│       ├── model_config_helper.py # Utility to get the string name of a model configuration object.
│       ├── offline.py         # Provides dummy architects for running in offline mode.
│       └── parsers/           # Utilities for parsing AI model outputs.
│           ├── __init__.py    # Parsers package initializer.
│           └── agent_parser.py # Parses agent definitions from Phase 2's XML-like output.
