.
├── __init__.py                # Main entry point for the core project analyzer package.
├── agent_tools/               # Manages tools and utilities available to AI agents.
│   ├── tool_manager.py        # Central manager for converting tool definitions to provider-specific formats.
│   └── web_search/            # Implements web search functionality as an agent tool.
│       ├── __init__.py        # Exposes the Tavily web search tool functions and schema.
│       └── tavily.py          # Implements a web search tool using the Tavily API.
├── agents/                    # Contains AI agent implementations for various model providers.
│   ├── __init__.py            # Provides a public shortcut for creating agent instances via a lazy import.
│   ├── anthropic/             # Implements the agent architect for Anthropic's Claude models.
│   │   ├── __init__.py        # Exposes the AnthropicArchitect class for public use.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for Anthropic models.
│   │   ├── client.py          # Manages the Anthropic SDK client instance and request execution.
│   │   ├── prompting.py       # Provides prompt templating and formatting for Anthropic agents.
│   │   ├── request_builder.py # Constructs request payloads for the Anthropic Messages API.
│   │   ├── response_parser.py # Parses and normalizes responses from the Anthropic API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Anthropic models.
│   ├── base.py                # Defines the abstract BaseArchitect class and core enums for all agents.
│   ├── deepseek/              # Implements the agent architect for DeepSeek's AI models.
│   │   ├── __init__.py        # Exposes the DeepSeekArchitect and legacy DeepSeekAgent classes.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for DeepSeek models.
│   │   ├── client.py          # Manages the OpenAI SDK client configured for DeepSeek's API.
│   │   ├── compat.py          # Provides a backward-compatibility wrapper for the legacy DeepSeekAgent.
│   │   ├── config.py          # Defines model-specific defaults and configuration for DeepSeek agents.
│   │   ├── prompting.py       # Provides prompt templating and formatting for DeepSeek agents.
│   │   ├── request_builder.py # Constructs request payloads for the DeepSeek Chat Completions API.
│   │   ├── response_parser.py # Parses and normalizes responses from the DeepSeek API.
│   │   └── tooling.py         # Helper for preparing tool configurations for DeepSeek models.
│   ├── factory/               # Contains the factory for creating specific agent instances.
│   │   ├── __init__.py        # Exposes the primary architect factory function.
│   │   └── factory.py         # Creates architect instances based on configuration (provider, phase, etc.).
│   ├── gemini/                # Implements the agent architect for Google's Gemini models.
│   │   ├── __init__.py        # Exposes the GeminiArchitect, legacy agent, and re-exports genai SDK.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for Gemini models.
│   │   ├── client.py          # Manages the Gemini SDK client and asynchronous request execution.
│   │   ├── errors.py          # Defines custom exceptions for the Gemini provider implementation.
│   │   ├── legacy.py          # Provides a backward-compatibility wrapper for the legacy GeminiAgent.
│   │   ├── prompting.py       # Provides prompt templating and formatting for Gemini agents.
│   │   ├── response_parser.py # Parses and normalizes responses from the Gemini API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Gemini models.
│   ├── openai/                # Implements the agent architect for OpenAI's GPT models.
│   │   ├── __init__.py        # Exposes the OpenAIArchitect and legacy OpenAIAgent classes.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for OpenAI models.
│   │   ├── client.py          # Manages the OpenAI SDK client instance and request execution.
│   │   ├── compat.py          # Provides a backward-compatibility wrapper for the legacy OpenAIAgent.
│   │   ├── config.py          # Defines model-specific defaults and configuration for OpenAI agents.
│   │   ├── request_builder.py # Constructs request payloads for the OpenAI Chat and Responses APIs.
│   │   └── response_parser.py # Parses and normalizes responses from the OpenAI API.
│   └── xai/                   # Implements the agent architect for xAI's Grok models.
│       ├── __init__.py        # Exposes the XaiArchitect class for public use.
│       ├── architect.py       # Main implementation of the BaseArchitect for xAI's Grok models.
│       ├── client.py          # Manages the OpenAI SDK client configured for xAI's API.
│       ├── config.py          # Defines model-specific defaults and configuration for xAI agents.
│       ├── prompting.py       # Provides prompt templating and formatting for xAI agents.
│       ├── request_builder.py # Constructs request payloads for the xAI Chat Completions API.
│       ├── response_parser.py # Parses and normalizes responses from the xAI API.
│       └── tooling.py         # Helper for preparing tool configurations for xAI models.
├── analysis/                  # Contains the logic for the multi-phase project analysis pipeline.
│   ├── __init__.py            # Exposes all analysis phase classes for easy import.
│   ├── final_analysis.py      # Implements the final analysis phase (Phase 6), generating final rules.
│   ├── phase_1.py             # Implements Phase 1 (Initial Discovery) of the analysis.
│   ├── phase_2.py             # Implements Phase 2 (Methodical Planning) of the analysis.
│   ├── phase_3.py             # Implements Phase 3 (Deep Analysis) using specialized agents.
│   ├── phase_4.py             # Implements Phase 4 (Synthesis) of the deep analysis findings.
│   └── phase_5.py             # Implements Phase 5 (Consolidation) of all previous results.
├── streaming.py               # Defines common data structures for handling streaming model responses.
├── types/                     # Contains custom type definitions used across the project.
│   ├── __init__.py            # Exposes key type definitions for models and agent configurations.
│   ├── agent_config.py        # Defines a TypedDict for agent phase configurations.
│   ├── models.py              # Defines the ModelConfig structure and various pre-defined model configurations.
│   └── tool_config.py         # Defines standard types for agent tool configurations.
└── utils/                     # Contains miscellaneous utility functions and helper modules.
    ├── async_stream.py        # Provides helpers for adapting synchronous iterators to async generators.
    ├── file_creation/         # Contains utilities for generating output files.
    │   ├── cursorignore.py    # Manages the creation and modification of .cursorignore files.
    │   └── phases_output.py   # Saves the output of each analysis phase to structured files.
    ├── file_system/           # Provides utilities for file system operations like tree generation.
    │   ├── __init__.py        # Exposes file retriever and tree generator functions.
    │   ├── file_retriever.py  # Retrieves file contents from a directory, respecting exclusion rules.
    │   └── tree_generator.py  # Generates an ASCII representation of the project's directory structure.
    ├── formatters/            # Contains utilities for formatting output files.
    │   ├── __init__.py        # Exposes the cursorrules file cleaning utility.
    │   └── clean_cursorrules.py # Cleans AGENTS.md files to ensure correct system prompt format.
    ├── model_config_helper.py # Helper function to get the human-readable name of a model configuration.
    ├── offline.py             # Provides stubs for running the analysis pipeline in offline mode.
    └── parsers/               # Contains parsers for extracting structured data from model outputs.
        ├── __init__.py        # Exposes the primary agent definition parser functions.
        └── agent_parser.py    # Parses agent definitions from Phase 2's output, with fallback logic.
