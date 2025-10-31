.
├── __init__.py                # Marks the directory as a Python package.
├── agent_tools/               # Contains tools that can be used by AI agents.
│   ├── tool_manager.py        # Manages and converts tool definitions for different AI model providers.
│   └── web_search/            # Contains tools for performing web searches.
│       ├── __init__.py        # Exposes the Tavily search tool functions and schema.
│       └── tavily.py          # Implements a web search tool using the Tavily API.
├── agents/                    # Contains agent classes for different large language models.
│   ├── __init__.py            # Exposes the agent factory and ModelProvider enum for easy access.
│   ├── anthropic.py           # Implements the architect class for interacting with Anthropic's Claude models.
│   ├── base.py                # Defines the abstract base class `BaseArchitect` for all model agents.
│   ├── deepseek.py            # Implements the architect class for interacting with DeepSeek models.
│   ├── factory/               # Contains the factory for creating agent instances.
│   │   ├── __init__.py        # Exposes the architect factory function.
│   │   └── factory.py         # Creates specific AI agent instances based on configuration.
│   ├── gemini.py              # Implements the architect class for interacting with Google's Gemini models.
│   └── openai.py              # Implements the architect class for interacting with OpenAI models.
├── analysis/                  # Modules for each phase of the multi-phase analysis process.
│   ├── __init__.py            # Exposes all phase analysis classes for easy import.
│   ├── final_analysis.py      # Implements the final analysis phase to generate .cursorrules.
│   ├── phase_1.py             # Implements the initial discovery and research phase of the analysis.
│   ├── phase_2.py             # Implements the analysis planning phase, defining agents for deep analysis.
│   ├── phase_3.py             # Implements the deep analysis phase where agents analyze specific files.
│   ├── phase_4.py             # Implements the synthesis phase to combine findings from deep analysis.
│   └── phase_5.py             # Implements the consolidation phase to create a single comprehensive report.
├── types/                     # Contains custom type definitions and data structures.
│   ├── __init__.py            # Exposes type definitions for configurations.
│   ├── agent_config.py        # Defines a TypedDict for specifying agent configurations per phase.
│   ├── models.py              # Defines the ModelConfig structure and predefined model configurations.
│   └── tool_config.py         # Defines TypedDicts for tool configurations used by agents.
└── utils/                     # Contains helper functions and utility modules.
    ├── file_creation/         # Utilities for creating and managing output files.
    │   ├── cursorignore.py    # Manages the creation and modification of .cursorignore files.
    │   └── phases_output.py   # Saves the output of each analysis phase to files.
    ├── file_system/           # Utilities for file system operations like reading files and trees.
    │   ├── __init__.py        # Exposes file retriever and tree generator functions.
    │   ├── file_retriever.py  # Retrieves and formats file contents, respecting exclusion rules.
    │   └── tree_generator.py  # Generates a visual ASCII tree of the project structure.
    ├── formatters/            # Utilities for formatting files.
    │   ├── __init__.py        # Exposes the clean_cursorrules function.
    │   └── clean_cursorrules.py # Cleans the final .cursorrules file to ensure correct formatting.
    ├── model_config_helper.py # Utility to get the human-readable name of a model configuration.
    ├── offline.py             # Provides stub classes for running the pipeline without real API calls.
    └── parsers/               # Utilities for parsing text and model outputs.
        ├── __init__.py        # Exposes agent parser functions.
        └── agent_parser.py    # Parses agent definitions from the Phase 2 output.