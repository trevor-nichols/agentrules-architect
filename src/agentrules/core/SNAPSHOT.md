.
├── __init__.py                # Marks the directory as the 'core' package.
├── agent_tools/               # Contains tools that can be used by AI agents.
│   ├── tool_manager.py        # Manages tool definitions and provider-specific format conversions.
│   └── web_search/            # Contains web search tool implementations.
│       ├── __init__.py        # Exports the Tavily web search tool schema and runner.
│       └── tavily.py          # Implements a web search tool using the Tavily API.
├── agents/                    # Contains implementations for different AI model providers.
│   ├── __init__.py            # Exports the main agent factory function and provider enum.
│   ├── anthropic/             # Contains the implementation for Anthropic (Claude) models.
│   │   ├── __init__.py        # Exports the AnthropicArchitect class.
│   │   ├── architect.py       # Implements the BaseArchitect for Anthropic models.
│   │   ├── client.py          # Helper for managing the Anthropic SDK client.
│   │   ├── prompting.py       # Provides prompt formatting helpers for Anthropic models.
│   │   ├── request_builder.py # Constructs request payloads for the Anthropic API.
│   │   ├── response_parser.py # Parses and normalizes responses from the Anthropic API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Anthropic models.
│   ├── base.py                # Defines the abstract BaseArchitect class for all AI models.
│   ├── deepseek/              # Contains the implementation for DeepSeek models.
│   │   ├── __init__.py        # Exports the DeepSeekArchitect and a compatibility agent.
│   │   ├── architect.py       # Implements the BaseArchitect for DeepSeek models.
│   │   ├── client.py          # Helper for managing the OpenAI SDK client for DeepSeek's API.
│   │   ├── compat.py          # Provides a backward-compatibility wrapper for the DeepSeek agent.
│   │   ├── config.py          # Defines model-specific defaults and configuration for DeepSeek.
│   │   ├── prompting.py       # Provides prompt formatting helpers for DeepSeek models.
│   │   ├── request_builder.py # Constructs request payloads for the DeepSeek API.
│   │   ├── response_parser.py # Parses and normalizes responses from the DeepSeek API.
│   │   └── tooling.py         # Helper for preparing tool configurations for DeepSeek models.
│   ├── factory/               # Contains the factory for creating agent instances.
│   │   ├── __init__.py        # Exports the main factory function.
│   │   └── factory.py         # Implements the factory for creating architect instances based on configuration.
│   ├── gemini/                # Contains the implementation for Google Gemini models.
│   │   ├── __init__.py        # Exports the GeminiArchitect and legacy agent.
│   │   ├── architect.py       # Implements the BaseArchitect for Gemini models.
│   │   ├── client.py          # Helper for creating and interacting with the Gemini SDK client.
│   │   ├── errors.py          # Defines custom exceptions for the Gemini provider.
│   │   ├── legacy.py          # Provides a backward-compatibility wrapper for the Gemini agent.
│   │   ├── prompting.py       # Provides prompt formatting helpers for Gemini models.
│   │   ├── response_parser.py # Parses and normalizes responses from the Gemini API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Gemini models.
│   ├── openai/                # Contains the implementation for OpenAI models.
│   │   ├── __init__.py        # Exports the OpenAIArchitect and legacy agent.
│   │   ├── architect.py       # Implements the BaseArchitect for OpenAI models.
│   │   ├── client.py          # Helper for managing the OpenAI SDK client.
│   │   ├── compat.py          # Provides a backward-compatibility wrapper for the OpenAI agent.
│   │   ├── config.py          # Defines model-specific defaults for OpenAI models.
│   │   ├── request_builder.py # Constructs request payloads for OpenAI APIs.
│   │   └── response_parser.py # Parses and normalizes responses from OpenAI APIs.
│   └── xai/                   # Contains the implementation for xAI (Grok) models.
│       ├── __init__.py        # Exports the XaiArchitect class.
│       ├── architect.py       # Implements the BaseArchitect for xAI models.
│       ├── client.py          # Helper for managing the OpenAI SDK client for xAI's API.
│       ├── config.py          # Defines model-specific defaults and configuration for xAI.
│       ├── prompting.py       # Provides prompt formatting helpers for xAI models.
│       ├── request_builder.py # Constructs request payloads for the xAI API.
│       ├── response_parser.py # Parses and normalizes responses from the xAI API.
│       └── tooling.py         # Helper for preparing tool configurations for xAI models.
├── configuration/             # Runtime configuration management and persistence.
│   ├── __init__.py            # Exposes the ConfigManager facade and cached accessor.
│   ├── constants.py           # Shared constants for config directories, verbosity, and env mappings.
│   ├── environment.py         # Applies persisted provider keys and verbosity into environment variables.
│   ├── manager.py             # High-level coordinator combining repositories and domain services.
│   ├── models.py              # Dataclasses describing the persisted CLI configuration schema.
│   ├── model_presets.py       # Maps user selections to concrete model preset configurations.
│   ├── repository.py          # TOML-backed persistence adapter for reading/writing config.
│   ├── serde.py               # Serialization helpers between dataclasses and dict payloads.
│   ├── utils.py               # Normalization helpers shared across configuration services.
│   └── services/              # Domain-specific helpers for providers, outputs, exclusions, etc.
│       ├── exclusions.py      # Manages inclusion/exclusion overrides for analysis.
│       ├── features.py        # Handles researcher feature toggles.
│       ├── logging.py         # Persists logging verbosity preferences.
│       ├── outputs.py         # Stores output generation preferences.
│       ├── phase_models.py    # Persists per-phase model overrides.
│       └── providers.py       # Persists provider credentials.
├── analysis/                  # Contains modules for each phase of the project analysis pipeline.
│   ├── __init__.py            # Exports the classes for each analysis phase.
│   ├── events.py              # Defines event primitives for monitoring the analysis pipeline.
│   ├── final_analysis.py      # Implements the final analysis phase to generate agent rules.
│   ├── phase_1.py             # Implements Phase 1: Initial project discovery and research.
│   ├── phase_2.py             # Implements Phase 2: Creates a plan and defines specialized agents.
│   ├── phase_3.py             # Implements Phase 3: In-depth file analysis by specialized agents.
│   ├── phase_4.py             # Implements Phase 4: Synthesizes findings from the deep analysis.
│   └── phase_5.py             # Implements Phase 5: Consolidates all findings into a final report.
├── logging/                   # Shared logging configuration and filtering utilities.
│   ├── __init__.py            # Exports the Rich-based logging configuration helper.
│   └── config.py              # Configures Rich handlers and filters provider noise.
├── streaming/                # Shared streaming primitives and helpers.
│   ├── __init__.py            # Re-exports common streaming types.
│   └── types.py               # Defines streaming event enums and chunk dataclass.
├── types/                     # Contains type definitions and data classes used across the project.
│   ├── __init__.py            # Exports various type definitions and model configurations.
│   ├── agent_config.py        # Defines a TypedDict for agent phase configurations.
│   ├── models.py              # Defines the ModelConfig structure and various pre-defined model presets.
│   └── tool_config.py         # Defines TypedDicts for tool configurations.
└── utils/                     # Contains various utility modules for cross-cutting concerns.
    ├── async_stream.py        # Provides a helper to adapt synchronous iterators into async generators.
    ├── constants.py           # Defines shared constants like default output filenames.
    ├── dependency_scanner/    # A tool for scanning and parsing project dependency files.
    │   ├── __init__.py        # Exports main functions and classes for the dependency scanner.
    │   ├── constants.py       # Defines filenames and patterns for known dependency manifest files.
    │   ├── discovery.py       # Discovers dependency manifest files in the project structure.
    │   ├── metadata.py        # Helper functions for processing dependency metadata.
    │   ├── models.py          # Defines data classes for dependency scanning results.
    │   ├── parsers/           # Contains parsers for specific dependency manifest formats.
    │   │   ├── __init__.py    # Builds and exports the central parser registry.
    │   │   ├── clojure.py     # Parsers for Clojure dependency files (deps.edn, project.clj).
    │   │   ├── dart.py        # Parser for Dart/Flutter pubspec.yaml files.
    │   │   ├── dotnet.py      # Parser for .NET project files (*.csproj, etc.).
    │   │   ├── elixir.py      # Parser for Elixir mix.exs files.
    │   │   ├── generic.py     # A generic fallback parser for unknown manifest files.
    │   │   ├── go.py          # Parser for Go module files (go.mod).
    │   │   ├── helpers.py     # Shared helper functions for parsers, like trimming excerpts.
    │   │   ├── java.py        # Parsers for Java/Kotlin dependency files (pom.xml, build.gradle).
    │   │   ├── javascript.py  # Parser for JavaScript package.json files.
    │   │   ├── php.py         # Parser for PHP composer.json files.
    │   │   ├── python.py      # Parsers for various Python dependency files.
    │   │   ├── ruby.py        # Parsers for Ruby dependency files (Gemfile, *.gemspec).
    │   │   ├── swift.py       # Parser for Swift Package.swift files.
    │   │   └── toml_based.py  # Generic parsers for TOML-based manifests like Cargo.toml.
    │   ├── registry.py        # Defines the registry for mapping file types to parsers.
    │   └── scan.py            # Orchestrates the dependency scanning process.
    ├── file_creation/         # Contains utilities for creating and managing files.
    │   ├── cursorignore.py    # Manages the creation and content of .cursorignore files.
    │   └── phases_output.py   # Saves the output of each analysis phase to structured files.
    ├── file_system/           # Contains utilities for interacting with the file system.
    │   ├── __init__.py        # Exports key functions for file retrieval and tree generation.
    │   ├── file_retriever.py  # Retrieves and formats file contents, respecting exclusion rules.
    │   ├── gitignore.py       # Helper for loading and applying .gitignore patterns.
    │   └── tree_generator.py  # Generates a visual tree representation of the project structure.
    ├── formatters/            # Contains code formatting utilities.
    │   ├── __init__.py        # Exports the clean_agentrules function.
    │   └── clean_agentrules.py # Cleans the final output file to ensure it starts with the system prompt.
    ├── model_config_helper.py # Helper to get the human-readable name of a model configuration.
    ├── offline.py             # Provides dummy architect classes for running the pipeline without API calls.
    └── parsers/               # Contains miscellaneous parsers.
        ├── __init__.py        # Exports key functions from the agent parser.
        └── agent_parser.py    # Parses agent definitions and file assignments from Phase 2 output.
