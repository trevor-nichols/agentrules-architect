.
├── __init__.py                # Initializes the config package.
├── agents.py                  # Configures AI models for each analysis phase.
├── exclusions.py              # Defines files, directories, and extensions to exclude from analysis.
├── prompts/                   # Contains prompt templates for different analysis phases.
│   ├── __init__.py            # Initializes the prompts package and imports all prompts.
│   ├── final_analysis_prompt.py # Defines the prompt for generating the final AGENTS.md file.
│   ├── phase_1_prompts.py     # Defines prompts for the initial discovery phase agents.
│   ├── phase_2_prompts.py     # Defines the prompt for the methodical planning phase.
│   ├── phase_3_prompts.py     # Defines prompts for the deep code analysis phase.
│   ├── phase_4_prompts.py     # Defines the prompt for the synthesis phase.
│   ├── phase_5_prompts.py     # Defines the prompt for the final report consolidation phase.
└── tools.py                   # Configures tools (e.g., web search) available to AI agents.
