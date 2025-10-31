.
├── __init__.py                # Makes the 'tests' directory a Python package.
├── fakes/                     # Contains fake objects for offline testing.
│   └── vendor_responses.py    # Fake LLM vendor SDK response objects for offline tests.
├── final_analysis_test/       # Tests for the final analysis phase.
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── output/                # Directory for test outputs from this phase.
│   ├── run_test.py            # Script to run an offline test of the final analysis phase.
│   ├── test_date.py           # Tests dynamic date insertion into the final analysis prompt.
│   ├── test_final_analysis.py # Live (online) tests for the final analysis logic against various models.
│   └── test_final_offline.py  # Offline unit test for the final analysis phase.
├── live/                      # Contains tests that require live API calls.
│   └── test_live_smoke.py     # Smoke test for the final analysis using a live, configured provider.
├── offline/                   # Contains tests that run without API calls, using stubs.
│   ├── __init__.py            # Marks directory as a Python package.
│   └── test_offline_smoke.py  # Offline smoke tests for various analysis phases using stubs.
├── phase_1_test/              # Tests for Phase 1 (Initial Discovery).
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── output/                # Directory for test outputs from this phase.
│   ├── run_test.py            # Script to run an offline test of Phase 1.
│   └── test_phase1_offline.py # Offline unit test for Phase 1 analysis.
├── phase_2_test/              # Tests for Phase 2 (Methodical Planning).
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── output/                # Directory for test outputs from this phase.
│   │   └── analysis_plan.xml  # Sample output file from a Phase 2 test run.
│   ├── run_test.py            # Script to run an offline test of Phase 2.
│   └── test_phase2_offline.py # Offline unit test for Phase 2 analysis and plan parsing.
├── phase_3_test/              # Tests for Phase 3 (Deep Analysis).
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── debug_parser.py        # Utility script to debug the agent parser for Phase 2 outputs.
│   ├── output/                # Directory for test outputs from this phase.
│   ├── run_test.py            # Script to run an offline test of Phase 3.
│   ├── test3_input.xml        # Sample XML analysis plan used as input for Phase 3 tests.
│   └── test_phase3_offline.py # Offline unit test for Phase 3 analysis.
├── phase_4_test/              # Tests for Phase 4 (Synthesis).
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── output/                # Directory for test outputs from this phase.
│   ├── run_test.py            # Script to run an offline test of Phase 4.
│   └── test_phase4_offline.py # Offline unit test for Phase 4 analysis.
├── phase_5_test/              # Tests for Phase 5 (Consolidation).
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── output/                # Directory for test outputs from this phase.
│   ├── run_test.py            # Script to run an offline test of Phase 5.
│   └── test_phase5_offline.py # Offline unit test for Phase 5 analysis.
├── test_env.py                # Script to check environment variables and API key setup.
├── test_smoke_discovery.py    # A minimal test to ensure test discovery is working.
├── tests_input/               # A sample project used as input for various tests.
│   ├── index.html             # Sample HTML file for the test project.
│   ├── main.py                # Sample Python/Flask file for the test project.
│   └── requirements.txt       # Sample requirements file for the test project.
├── unit/                      # Contains various unit tests for core utilities and components.
│   ├── __init__.py            # Marks directory as a Python package.
│   ├── agents/                # Unit tests specifically for different agent implementations.
│   │   ├── __init__.py        # Marks directory as a Python package.
│   │   ├── test_anthropic_agent_parsing.py # Tests response parsing for the Anthropic agent.
│   │   ├── test_deepseek_agent_parsing.py # Tests response parsing for the DeepSeek agent.
│   │   ├── test_gemini_agent_parsing.py # Tests response parsing for the Gemini agent.
│   │   └── test_openai_agent_parsing.py # Tests response parsing for the OpenAI agent.
│   ├── test_agent_parser_basic.py # Unit tests for the agent plan parser utility.
│   ├── test_agents_anthropic_parse.py # Unit test for Anthropic agent response parsing logic.
│   ├── test_agents_deepseek.py    # Unit tests for the DeepSeek agent logic.
│   ├── test_agents_gemini_error.py # Unit tests for Gemini agent error handling.
│   ├── test_agents_openai_params.py # Unit tests for OpenAI model parameter generation.
│   ├── test_file_retriever.py     # Unit tests for file system utilities.
│   ├── test_model_config_helper.py # Unit tests for model configuration helper functions.
│   ├── test_phases_edges.py       # Tests edge cases and fallback logic in analysis phases.
│   ├── test_tavily_tool.py        # Unit tests for the Tavily web search tool integration.
│   └── test_tool_manager.py       # Unit tests for adapting tool schemas for different LLM providers.
└── utils/                     # Contains utilities and helpers for testing.
    ├── __init__.py            # Marks directory as a Python package.
    ├── clean_cr_test.py       # Test script for the `clean_cursorrules` utility.
    ├── inputs/                # Directory for test utility inputs.
    ├── offline_stubs.py       # Provides a dummy architect for running tests offline.
    ├── outputs/               # Directory for test utility outputs.
    └── run_tree_generator.py  # Utility script to generate and print a project directory tree.