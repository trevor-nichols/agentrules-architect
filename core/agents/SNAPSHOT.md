.
├── __init__.py                # Initializes the agents package and provides public shortcuts.
├── anthropic.py               # Implements the BaseArchitect for Anthropic's Claude models.
├── base.py                    # Defines the abstract base class for all AI model agents.
├── deepseek.py                # Implements the BaseArchitect for DeepSeek's AI models.
├── factory/                   # Contains the factory for creating architect/agent instances.
│   ├── __init__.py            # Exposes the main architect factory function.
│   └── factory.py             # Creates agent instances based on configuration (factory pattern).
├── gemini.py                  # Implements the BaseArchitect for Google's Gemini models.
├── openai.py                  # Implements the BaseArchitect for OpenAI's GPT models.