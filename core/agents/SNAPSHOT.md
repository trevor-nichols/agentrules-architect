.
├── __init__.py                # Exposes a factory function for creating architect agents.
├── anthropic/                 # Contains the implementation for the Anthropic (Claude) agent.
│   ├── __init__.py            # Exposes the main AnthropicArchitect class for the package.
│   ├── architect.py           # Implements the BaseArchitect interface for Anthropic models.
│   ├── client.py              # Manages the Anthropic SDK client instance.
│   ├── prompting.py           # Provides prompt formatting helpers for Anthropic models.
│   ├── request_builder.py     # Constructs API request payloads for Anthropic models.
│   ├── response_parser.py     # Parses responses from the Anthropic API.
│   └── tooling.py             # Handles tool configuration for Anthropic models.
├── base.py                    # Defines the abstract BaseArchitect class and common enums.
├── deepseek/                  # Contains the implementation for the DeepSeek agent.
│   ├── __init__.py            # Exports DeepSeekArchitect and compatibility wrappers.
│   ├── architect.py           # Implements the BaseArchitect interface for DeepSeek models.
│   ├── client.py              # Manages the OpenAI-compatible DeepSeek client.
│   ├── compat.py              # Backwards-compatible wrapper matching the legacy agent API.
│   ├── config.py              # Provides model defaults and base URL resolution.
│   ├── prompting.py           # Houses prompt templates and formatting helpers.
│   ├── request_builder.py     # Prepares DeepSeek chat completion payloads.
│   ├── response_parser.py     # Normalises DeepSeek responses.
│   └── tooling.py             # Resolves tool configurations for DeepSeek models.
├── factory/                   # Contains the factory for creating different architect instances.
│   ├── __init__.py            # Exposes the main factory function.
│   └── factory.py             # Implements the logic to create architects based on configuration.
├── gemini/                    # Contains the implementation for the Google Gemini agent.
│   ├── __init__.py            # Exposes the GeminiArchitect and legacy agent classes.
│   ├── architect.py           # Implements the BaseArchitect interface for Gemini models.
│   ├── client.py              # Manages the Gemini SDK client and async requests.
│   ├── errors.py              # Defines custom exceptions for the Gemini provider.
│   ├── legacy.py              # Provides a backward-compatible wrapper for the Gemini agent.
│   ├── prompting.py           # Provides prompt formatting helpers for Gemini models.
│   ├── response_parser.py     # Parses responses from the Gemini API.
│   └── tooling.py             # Handles tool configuration for Gemini models.
└── openai/                    # Contains the implementation for the OpenAI agent.
    ├── __init__.py            # Exposes the OpenAIArchitect and legacy agent classes.
    ├── architect.py           # Implements the BaseArchitect interface for OpenAI models.
    ├── client.py              # Manages the OpenAI SDK client and executes requests.
    ├── compat.py              # Provides a backward-compatible wrapper for the OpenAI agent.
    ├── config.py              # Defines default configurations for different OpenAI models.
    ├── request_builder.py     # Constructs API request payloads for OpenAI models.
    └── response_parser.py     # Parses responses from the OpenAI API.
