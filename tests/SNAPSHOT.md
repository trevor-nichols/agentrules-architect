```
.
├── __init__.py                    # Test package initializer to enable imports.
├── fakes/                         # Contains fake objects for testing without live APIs.
│   └── vendor_responses.py        # Defines fake response objects mimicking vendor SDKs for offline tests.
├── final_analysis_test/           # Tests for the final analysis phase of the pipeline.
│   ├── __init__.py                # Test package marker for final_analysis_test.
│   ├── output/                    # Directory for storing final analysis test outputs.
│   ├── run_test.py                # Script to run an offline test of the final analysis phase.
│   ├── test_date.py               # Tests dynamic insertion of the current date into the final analysis prompt.
│   ├── test_final_analysis.py     # Live SDK tests for the final analysis phase against various models.
│   └── test_final_offline.py      # Offline unit test for the final analysis phase.
├── live/                          # Contains tests that make live API calls.
│   └── test_live_smoke.py         # Live smoke test to check API key configuration and basic final analysis functionality.
├── offline/                       # Contains offline tests that use stubs/mocks.
│   ├── __init__.py                # Test package marker for offline tests.
│   └── test_offline_smoke.py      # Offline smoke tests for various analysis phases using stubs.
├── phase_1_test/                  # Tests for Phase 1 (Initial Discovery).
│   ├── __init__.py                # Test package marker for phase_1_test.
│   ├── output/                    # Directory for storing Phase 1 test outputs.
│   ├── run_test.py                # Script to run an offline test of Phase 1.
│   └── test_phase1_offline.py     # Offline unit test for Phase 1, including tool execution.
├── phase_2_test/                  # Tests for Phase 2 (Methodical Planning).
│   ├── __init__.py                # Test package marker for phase_2_test.
│   ├── output/                    # Directory for storing Phase 2 test outputs.
│   │   └── analysis_plan.xml      # An example XML output of an analysis plan from a test run.
│   ├── run_test.py                # Script to run an offline test of Phase 2.
│   └── test_phase2_offline.py     # Offline unit test for Phase 2, focusing on plan parsing.
├── phase_3_test/                  # Tests for Phase 3 (Deep Analysis).
│   ├── __init__.py                # Test package marker for phase_3_test.
│   ├── debug_parser.py            # A script for debugging the agent parser on Phase 2 outputs.
│   ├── output/                    # Directory for storing Phase 3 test outputs.
│   ├── run_test.py                # Script to run an offline test of Phase 3.
│   ├── test3_input.xml            # Sample XML analysis plan used as input for Phase 3 tests.
│   └── test_phase3_offline.py     # Offline unit test for Phase 3.
├── phase_4_test/                  # Tests for Phase 4 (Synthesis).
│   ├── __init__.py                # Test package marker for phase_4_test.
│   ├── output/                    # Directory for storing Phase 4 test outputs.
│   ├── run_test.py                # Script to run an offline test of Phase 4.
│   └── test_phase4_offline.py     # Offline unit test for Phase 4.
├── phase_5_test/                  # Tests for Phase 5 (Consolidation).
│   ├── __init__.py                # Test package marker for phase_5_test.
│   ├── output/                    # Directory for storing Phase 5 test outputs.
│   ├── run_test.py                # Script to run an offline test of Phase 5.
│   └── test_phase5_offline.py     # Offline unit test for Phase 5.
├── test_cli_services.py           # Unit tests for CLI helper functions and the pipeline runner.
├── test_env.py                    # A script to check if necessary API key environment variables are set.
├── test_openai_responses.py       # Unit tests for OpenAI's 'responses' API request preparation and parsing.
├── test_smoke_discovery.py        # A minimal smoke test to ensure the test runner is working.
├── tests_input/                   # Contains sample project files used as input for various tests.
│   ├── index.html                 # Sample HTML file for a simple web app.
│   ├── main.py                    # Sample Python Flask server file.
│   └── requirements.txt           # Sample project requirements file.
├── unit/                          # Contains unit tests for individual components.
│   ├── __init__.py                # Unit test package marker.
│   ├── agents/                    # Unit tests specifically for agent implementations and helpers.
│   │   ├── __init__.py            # Agent unit test package marker.
│   │   ├── test_anthropic_agent_parsing.py # Tests parsing of Anthropic agent responses with text and tool use.
│   │   ├── test_anthropic_request_builder.py # Tests the construction of requests for the Anthropic API.
│   │   ├── test_deepseek_agent_parsing.py # Tests parsing of DeepSeek agent responses for chat and reasoner models.
│   │   ├── test_deepseek_helpers.py # Unit tests for DeepSeek configuration, request building, and response parsing helpers.
│   │   ├── test_gemini_agent_parsing.py # Tests parsing of Gemini agent responses, including function calls.
│   │   ├── test_openai_agent_parsing.py # Tests parsing of OpenAI agent responses and parameter passing.
│   │   └── test_openai_helpers.py   # Unit tests for OpenAI configuration, request building, and response parsing helpers.
│   ├── test_agent_parser_basic.py # Unit tests for the XML/JSON agent plan parser.
│   ├── test_agents_anthropic_parse.py # More tests for parsing text and tool calls from Anthropic agent responses.
│   ├── test_agents_deepseek.py      # Unit tests for DeepSeek agent behavior (chat vs. reasoner).
│   ├── test_agents_gemini_error.py  # Tests error handling for the Gemini agent when its client is not initialized.
│   ├── test_agents_openai_params.py # Tests that correct parameters are sent in OpenAI API requests.
│   ├── test_cli.py                  # Unit tests for the command-line interface.
│   ├── test_config_service.py       # Unit tests for the application's configuration service.
│   ├── test_file_retriever.py       # Unit tests for file system utilities like listing and reading files.
│   ├── test_model_config_helper.py  # Tests the helper function for resolving model configuration names.
│   ├── test_model_overrides.py      # Tests applying user-defined model overrides from configuration.
│   ├── test_phases_edges.py         # Unit tests for edge cases and fallback logic in analysis phases.
│   ├── test_streaming_support.py    # Unit tests for streaming functionality across different AI providers.
│   ├── test_tavily_tool.py          # Unit tests for the Tavily web search tool integration.
│   └── test_tool_manager.py         # Unit tests for adapting tool schemas for different providers.
└── utils/                         # Contains utility scripts and helpers for testing.
    ├── __init__.py                # Test utilities package marker.
    ├── clean_cr_test.py           # A test script for the `AGENTS.md` file cleaning utility.
    ├── inputs/                    # Directory for test utility inputs.
    ├── offline_stubs.py           # Provides a dummy architect for running tests without making real API calls.
    ├── outputs/                   # Directory for test utility outputs.
    └── run_tree_generator.py      # A utility script to generate and print a project's directory tree.
```
