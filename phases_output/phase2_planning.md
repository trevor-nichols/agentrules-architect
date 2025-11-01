# Phase 2: Methodical Planning (Config: GEMINI_FLASH)

<reasoning>
I will create a team of four agents, each with a specialized focus to thoroughly analyze the project.

1.  **Orchestration and CLI Agent**: This agent will be responsible for understanding the overall application flow, CLI structure, and user interaction. This includes `main.py`, `__main__.py`, and all files within `src/agentrules/cli`.

2.  **LLM and Core Logic Agent**: This agent will focus on the artificial intelligence aspects, including how different LLMs are integrated, the core analysis pipeline, prompt management, and agent tooling. This covers `src/agentrules/core/agents`, `src/agentrules/config/prompts`, `src/agentrules/core/analysis`, `src/agentrules/core/agent_tools`, and related configuration.

3.  **Utilities and System Agent**: This agent will handle the foundational utilities, dependency scanning across various languages, file system interactions, and general helper functions. This encompasses `src/agentrules/core/utils`, `scripts/bootstrap_env.sh`, and general project configuration files like `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `conftest.py`.

4.  **Typing and Quality Agent**: This agent will specialize in type definitions, ensuring code quality, and understanding the static analysis setup. This includes all files in `typings/` and files related to logging and general configuration in `src/agentrules`.

This distribution ensures that each major component of the project is covered by an agent with appropriate expertise, leading to a comprehensive analysis.
</reasoning>

<analysis_plan>
<agent_1 name="Orchestration and CLI Agent">
<description>Focuses on the overall application flow, command-line interface structure, user interaction, and bootstrapping processes. This agent ensures the application's entry points and user-facing components are well understood.</description>
<file_assignments>
<file_path>main.py</file_path>
<file_path>src/agentrules/__main__.py</file_path>
<file_path>src/agentrules/analyzer.py</file_path>
<file_path>src/agentrules/cli/__init__.py</file_path>
<file_path>src/agentrules/cli/app.py</file_path>
<file_path>src/agentrules/cli/bootstrap.py</file_path>
<file_path>src/agentrules/cli/context.py</file_path>
<file_path>src/agentrules/cli/commands/__init__.py</file_path>
<file_path>src/agentrules/cli/commands/analyze.py</file_path>
<file_path>src/agentrules/cli/commands/configure.py</file_path>
<file_path>src/agentrules/cli/commands/keys.py</file_path>
<file_path>src/agentrules/cli/commands/tree.py</file_path>
<file_path>src/agentrules/cli/services/__init__.py</file_path>
<file_path>src/agentrules/cli/services/configuration.py</file_path>
<file_path>src/agentrules/cli/services/pipeline_runner.py</file_path>
<file_path>src/agentrules/cli/services/tree_preview.py</file_path>
<file_path>src/agentrules/cli/ui/__init__.py</file_path>
<file_path>src/agentrules/cli/ui/analysis_view.py</file_path>
<file_path>src/agentrules/cli/ui/main_menu.py</file_path>
<file_path>src/agentrules/cli/ui/styles.py</file_path>
<file_path>src/agentrules/cli/ui/settings/__init__.py</file_path>
<file_path>src/agentrules/cli/ui/settings/logging.py</file_path>
<file_path>src/agentrules/cli/ui/settings/menu.py</file_path>
<file_path>src/agentrules/cli/ui/settings/outputs.py</file_path>
<file_path>src/agentrules/cli/ui/settings/providers.py</file_path>
<file_path>src/agentrules/cli/ui/settings/exclusions/__init__.py</file_path>
<file_path>src/agentrules/cli/ui/settings/exclusions/editor.py</file_path>
<file_path>src/agentrules/cli/ui/settings/exclusions/preview.py</file_path>
<file_path>src/agentrules/cli/ui/settings/exclusions/summary.py</file_path>
<file_path>src/agentrules/cli/ui/settings/models/__init__.py</file_path>
<file_path>src/agentrules/cli/ui/settings/models/researcher.py</file_path>
<file_path>src/agentrules/cli/ui/settings/models/utils.py</file_path>
</file_assignments>
</agent_1>

<agent_2 name="LLM and Core Logic Agent">
<description>Specializes in understanding the integration and functionality of Large Language Models (LLMs), the core analysis pipeline, prompt engineering, agent behavior, and external tool usage.</description>
<file_assignments>
<file_path>src/agentrules/__init__.py</file_path>
<file_path>src/agentrules/config/__init__.py</file_path>
<file_path>src/agentrules/config/agents.py</file_path>
<file_path>src/agentrules/config/exclusions.py</file_path>
<file_path>src/agentrules/config/tools.py</file_path>
<file_path>src/agentrules/config/prompts/__init__.py</file_path>
<file_path>src/agentrules/config/prompts/final_analysis_prompt.py</file_path>
<file_path>src/agentrules/config/prompts/phase_1_prompts.py</file_path>
<file_path>src/agentrules/config/prompts/phase_2_prompts.py</file_path>
<file_path>src/agentrules/config/prompts/phase_3_prompts.py</file_path>
<file_path>src/agentrules/config/prompts/phase_4_prompts.py</file_path>
<file_path>src/agentrules/config/prompts/phase_5_prompts.py</file_path>
<file_path>src/agentrules/core/__init__.py</file_path>
<file_path>src/agentrules/core/analysis/__init__.py</file_path>
<file_path>src/agentrules/core/analysis/events.py</file_path>
<file_path>src/agentrules/core/analysis/final_analysis.py</file_path>
<file_path>src/agentrules/core/analysis/phase_1.py</file_path>
<file_path>src/agentrules/core/analysis/phase_2.py</file_path>
<file_path>src/agentrules/core/analysis/phase_3.py</file_path>
<file_path>src/agentrules/core/analysis/phase_4.py</file_path>
<file_path>src/agentrules/core/analysis/phase_5.py</file_path>
<file_path>src/agentrules/core/agent_tools/__init__.py</file_path>
<file_path>src/agentrules/core/agent_tools/tool_manager.py</file_path>
<file_path>src/agentrules/core/agent_tools/web_search/__init__.py</file_path>
<file_path>src/agentrules/core/agent_tools/web_search/tavily.py</file_path>
<file_path>src/agentrules/core/agents/__init__.py</file_path>
<file_path>src/agentrules/core/agents/base.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/__init__.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/architect.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/client.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/prompting.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/request_builder.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/response_parser.py</file_path>
<file_path>src/agentrules/core/agents/anthropic/tooling.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/__init__.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/architect.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/client.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/compat.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/config.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/prompting.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/request_builder.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/response_parser.py</file_path>
<file_path>src/agentrules/core/agents/deepseek/tooling.py</file_path>
<file_path>src/agentrules/core/agents/factory/__init__.py</file_path>
<file_path>src/agentrules/core/agents/factory/factory.py</file_path>
<file_path>src/agentrules/core/agents/gemini/__init__.py</file_path>
<file_path>src/agentrules/core/agents/gemini/architect.py</file_path>
<file_path>src/agentrules/core/agents/gemini/client.py</file_path>
<file_path>src/agentrules/core/agents/gemini/errors.py</file_path>
<file_path>src/agentrules/core/agents/gemini/legacy.py</file_path>
<file_path>src/agentrules/core/agents/gemini/prompting.py</file_path>
<file_path>src/agentrules/core/agents/gemini/response_parser.py</file_path>
<file_path>src/agentrules/core/agents/gemini/tooling.py</file_path>
<file_path>src/agentrules/core/agents/openai/__init__.py</file_path>
<file_path>src/agentrules/core/agents/openai/architect.py</file_path>
<file_path>src/agentrules/core/agents/openai/client.py</file_path>
<file_path>src/agentrules/core/agents/openai/compat.py</file_path>
<file_path>src/agentrules/core/agents/openai/config.py</file_path>
<file_path>src/agentrules/core/agents/openai/request_builder.py</file_path>
<file_path>src/agentrules/core/agents/openai/response_parser.py</file_path>
<file_path>src/agentrules/core/agents/xai/__init__.py</file_path>
<file_path>src/agentrules/core/agents/xai/architect.py</file_path>
<file_path>src/agentrules/core/agents/xai/client.py</file_path>
<file_path>src/agentrules/core/agents/xai/config.py</file_path>
<file_path>src/agentrules/core/agents/xai/prompting.py</file_path>
<file_path>src/agentrules/core/agents/xai/request_builder.py</file_path>
<file_path>src/agentrules/core/agents/xai/response_parser.py</file_path>
<file_path>src/agentrules/core/agents/xai/tooling.py</file_path>
<file_path>src/agentrules/core/streaming/__init__.py</file_path>
<file_path>src/agentrules/core/streaming/types.py</file_path>
<file_path>src/agentrules/core/types/__init__.py</file_path>
<file_path>src/agentrules/core/types/agent_config.py</file_path>
<file_path>src/agentrules/core/types/models.py</file_path>
<file_path>src/agentrules/core/types/tool_config.py</file_path>
</file_assignments>
</agent_2>

<agent_3 name="Utilities and System Agent">
<description>Focuses on general utility functions, file system interactions, dependency scanning across various languages, and shell scripting for environment setup. This agent ensures the underlying operational components are robust.</description>
<file_assignments>
<file_path>scripts/bootstrap_env.sh</file_path>
<file_path>src/agentrules/core/utils/__init__.py</file_path>
<file_path>src/agentrules/core/utils/async_stream.py</file_path>
<file_path>src/agentrules/core/utils/constants.py</file_path>
<file_path>src/agentrules/core/utils/model_config_helper.py</file_path>
<file_path>src/agentrules/core/utils/offline.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/__init__.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/constants.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/discovery.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/metadata.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/models.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/registry.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/scan.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/__init__.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/clojure.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/dart.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/dotnet.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/elixir.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/generic.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/go.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/helpers.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/java.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/javascript.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/php.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/python.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/ruby.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/swift.py</file_path>
<file_path>src/agentrules/core/utils/dependency_scanner/parsers/toml_based.py</file_path>
<file_path>src/agentrules/core/utils/file_creation/__init__.py</file_path>
<file_path>src/agentrules/core/utils/file_creation/cursorignore.py</file_path>
<file_path>src/agentrules/core/utils/file_creation/phases_output.py</file_path>
<file_path>src/agentrules/core/utils/file_system/__init__.py</file_path>
<file_path>src/agentrules/core/utils/file_system/file_retriever.py</file_path>
<file_path>src/agentrules/core/utils/file_system/gitignore.py</file_path>
<file_path>src/agentrules/core/utils/file_system/tree_generator.py</file_path>
<file_path>src/agentrules/core/utils/formatters/__init__.py</file_path>
<file_path>src/agentrules/core/utils/formatters/clean_cursorrules.py</file_path>
<file_path>src/agentrules/core/utils/parsers/__init__.py</file_path>
<file_path>src/agentrules/core/utils/parsers/agent_parser.py</file_path>
<file_path>pyproject.toml</file_path>
<file_path>requirements-dev.txt</file_path>
</file_assignments>
</agent_3>

<agent_4 name="Typing and Quality Agent">
<description>Focuses on type definitions, static analysis configuration, logging setup, and overall code quality. This agent ensures the codebase is maintainable, type-safe, and well-documented for development and debugging.</description>
<file_assignments>
<file_path>src/agentrules/config_service.py</file_path>
<file_path>src/agentrules/logging_setup.py</file_path>
<file_path>src/agentrules/model_config.py</file_path>
<file_path>typings/google/genai/__init__.pyi</file_path>
<file_path>typings/google/genai/types.pyi</file_path>
<file_path>typings/google/protobuf/__init__.pyi</file_path>
<file_path>typings/google/protobuf/struct_pb2.pyi</file_path>
<file_path>typings/google/__init__.pyi</file_path>
<file_path>typings/tavily/__init__.pyi</file_path>
<file_path>typings/tomli_w/__init__.pyi</file_path>
<file_path>conftest.py</file_path>
</file_assignments>
</agent_4>
</analysis_plan>