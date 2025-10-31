.
├── __init__.py                # Marks the `core` directory as a Python package.
├── agent_tools/               # Contains tools that AI agents can use, such as web search.
│   ├── tool_manager.py        # Manages and converts tool definitions for different LLM providers.
│   └── web_search/            # Contains implementations for web search tools.
│       ├── __init__.py        # Exposes the Tavily search tool functionality.
│       └── tavily.py          # Implements a web search tool using the Tavily API.
├── agents/                    # Contains all agent implementations, organized by LLM provider.
│   ├── __init__.py            # Exposes a factory for creating architect instances.
│   ├── anthropic/             # Implementation for Anthropic's Claude models.
│   │   ├── __init__.py        # Exposes the AnthropicArchitect class.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for Anthropic models.
│   │   ├── client.py          # Manages the Anthropic SDK client.
│   │   ├── prompting.py       # Contains prompt formatting helpers for Anthropic models.
│   │   ├── request_builder.py # Constructs API request payloads for Anthropic models.
│   │   ├── response_parser.py # Parses and normalizes responses from the Anthropic API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Anthropic models.
│   ├── base.py                # Defines the abstract BaseArchitect class and core enums.
│   ├── deepseek/              # Implementation for DeepSeek models.
│   │   ├── __init__.py        # Exposes the DeepSeekArchitect class.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for DeepSeek models.
│   │   ├── client.py          # Manages the OpenAI SDK client for the DeepSeek-compatible API.
│   │   ├── compat.py          # A backward-compatibility wrapper for a legacy DeepSeek agent.
│   │   ├── config.py          # Defines model-specific defaults for DeepSeek.
│   │   ├── prompting.py       # Contains prompt formatting helpers for DeepSeek models.
│   │   ├── request_builder.py # Constructs API request payloads for DeepSeek models.
│   │   ├── response_parser.py # Parses and normalizes responses from the DeepSeek API.
│   │   └── tooling.py         # Helper for preparing tool configurations for DeepSeek models.
│   ├── factory/               # Contains the factory for creating agent instances.
│   │   ├── __init__.py        # Exposes the architect factory function.
│   │   └── factory.py         # Implements a factory to create agent instances based on configuration.
│   ├── gemini/                # Implementation for Google's Gemini models.
│   │   ├── __init__.py        # Exposes the GeminiArchitect class.
│   │   ├── architect.py       # Main implementation of the BaseArchitect for Gemini models.
│   │   ├── client.py          # Manages the Google GenAI (Gemini) SDK client.
│   │   ├── errors.py          # Defines custom exceptions for the Gemini provider.
│   │   ├── legacy.py          # A backward-compatibility wrapper for a legacy Gemini agent.
│   │   ├── prompting.py       # Contains prompt formatting helpers for Gemini models.
│   │   ├── response_parser.py # Parses and normalizes responses from the Gemini API.
│   │   └── tooling.py         # Helper for preparing tool configurations for Gemini models.
│   └── openai/                # Implementation for OpenAI models (GPT series).
│       ├── __init__.py        # Exposes the OpenAIArchitect class.
│       ├── architect.py       # Main implementation of the BaseArchitect for OpenAI models.
│       ├── client.py          # Manages the OpenAI SDK client.
│       ├── compat.py          # A backward-compatibility wrapper for a legacy OpenAI agent.
│       ├── config.py          # Defines model-specific defaults for OpenAI.
│       └── request_builder.py # Constructs API request payloads for OpenAI models.
│       └── response_parser.py # Parses and normalizes responses from the OpenAI API.
├── analysis/                  # Contains the logic for the multi-phase analysis pipeline.
│   ├── __init__.py            # Exposes analysis classes for all phases.
│   ├── final_analysis.py      # Implements the final analysis phase to generate cursor rules.
│   ├── phase_1.py             # Implements Phase 1: Initial project discovery and research.
│   ├── phase_2.py             # Implements Phase 2: Creation of a methodical analysis plan.
│   ├── phase_3.py             # Implements Phase 3: Deep analysis of code files by specialized agents.
│   ├── phase_4.py             # Implements Phase 4: Synthesis of findings from the deep analysis.
│   └── phase_5.py             # Implements Phase 5: Consolidation of all findings into a single report.
├── types/                     # Contains shared data structures and type definitions.
│   ├── __init__.py            # Exposes key type definitions from the package.
│   ├── agent_config.py        # Defines a TypedDict for agent configurations.
│   ├── models.py              # Defines the ModelConfig type and various predefined model settings.
│   └── tool_config.py         # Defines TypedDict structures for agent tool configurations.
└── utils/                     # Contains various utility modules for file I/O, formatting, and parsing.
    ├── file_creation/         # Utilities for creating output files.
    │   ├── cursorignore.py    # Manages the creation and modification of .cursorignore files.
    │   └── phases_output.py   # Saves the output of each analysis phase to separate files.
    ├── file_system/           # Utilities for interacting with the file system.
    │   ├── __init__.py        # Exposes key file system utility functions.
    │   ├── file_retriever.py  # Retrieves and formats file contents from a project, respecting exclusions.
    │   └── tree_generator.py  # Generates a visual ASCII tree of a project's structure.
    ├── formatters/            # Utilities for formatting output files.
    │   ├── __init__.py        # Exposes the clean_cursorrules function.
    │   └── clean_cursorrules.py # Cleans up the final .cursorrules file by removing extraneous text.
    ├── model_config_helper.py # Helper to retrieve the string name of a model configuration.
    ├── offline.py             # Provides dummy architect stubs for running the pipeline without API calls.
    └── parsers/               # Utilities for parsing model outputs.
        ├── __init__.py        # Exposes key agent parser functions.
        └── agent_parser.py    # Parses agent definitions and file assignments from Phase 2 output.