import logging
import os
import sys
import tempfile
import unittest
from importlib import reload
from pathlib import Path


class ConfigServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["AGENTRULES_CONFIG_DIR"] = self.temp_dir.name
        self._codex_home_backup = os.environ.pop("CODEX_HOME", None)

        import agentrules.core.configuration as configuration_package
        import agentrules.core.configuration.constants as configuration_constants
        import agentrules.core.configuration.manager as configuration_manager_module
        import agentrules.core.configuration.repository as configuration_repository

        reload(configuration_constants)
        reload(configuration_repository)
        reload(configuration_manager_module)
        reload(configuration_package)
        configuration_package.get_config_manager.cache_clear()

        self.configuration = configuration_package
        self.config_manager = configuration_package.get_config_manager()
        self._env_backup = {}
        for env_var in self.configuration.PROVIDER_ENV_MAP.values():
            self._env_backup[env_var] = os.environ.pop(env_var, None)
        self._verbosity_backup = os.environ.pop(self.configuration.VERBOSITY_ENV_VAR, None)
        self._rules_filename_backup = os.environ.pop(self.configuration.RULES_FILENAME_ENV_VAR, None)
        self._offline_backup = os.environ.pop("OFFLINE", None)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        self.configuration.get_config_manager.cache_clear()
        os.environ.pop("AGENTRULES_CONFIG_DIR", None)
        for env_var, value in self._env_backup.items():
            if value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = value
        if self._verbosity_backup is None:
            os.environ.pop(self.configuration.VERBOSITY_ENV_VAR, None)
        else:
            os.environ[self.configuration.VERBOSITY_ENV_VAR] = self._verbosity_backup
        if self._rules_filename_backup is None:
            os.environ.pop(self.configuration.RULES_FILENAME_ENV_VAR, None)
        else:
            os.environ[self.configuration.RULES_FILENAME_ENV_VAR] = self._rules_filename_backup
        if self._codex_home_backup is None:
            os.environ.pop(self.configuration.CODEX_HOME_ENV_VAR, None)
        else:
            os.environ[self.configuration.CODEX_HOME_ENV_VAR] = self._codex_home_backup
        if self._offline_backup is None:
            os.environ.pop("OFFLINE", None)
        else:
            os.environ["OFFLINE"] = self._offline_backup

    def test_set_provider_key_persists_and_sets_env(self) -> None:
        self.config_manager.set_provider_key("openai", "test-key-123")
        config = self.config_manager.load()

        self.assertIn("openai", config.providers)
        self.assertEqual(config.providers["openai"].api_key, "test-key-123")
        self.assertEqual(os.environ.get("OPENAI_API_KEY"), "test-key-123")

    def test_get_current_provider_keys_masks_missing(self) -> None:
        keys = self.config_manager.get_current_provider_keys()
        self.assertIsInstance(keys, dict)
        self.assertIn("openai", keys)
        self.assertIsNone(keys.get("openai"))

    def test_codex_runtime_config_persists_and_serializes_dedicated_section(self) -> None:
        self.config_manager.set_codex_cli_path("/usr/local/bin/codex")
        self.config_manager.set_codex_managed_home("~/agentrules-codex-home")

        config = self.config_manager.load()
        self.assertEqual(config.codex.cli_path, "/usr/local/bin/codex")
        self.assertEqual(config.codex.home_strategy, "managed")
        self.assertEqual(config.codex.managed_home, "~/agentrules-codex-home")
        self.assertEqual(
            os.environ.get(self.configuration.CODEX_HOME_ENV_VAR),
            os.path.expanduser("~/agentrules-codex-home"),
        )

        persisted = self.configuration.CONFIG_FILE.read_text(encoding="utf-8")
        self.assertIn("[codex]", persisted)
        self.assertIn('cli_path = "/usr/local/bin/codex"', persisted)
        self.assertIn('managed_home = "~/agentrules-codex-home"', persisted)

    def test_codex_effective_home_defaults_to_managed_config_dir(self) -> None:
        expected = str(self.configuration.CONFIG_DIR / self.configuration.DEFAULT_CODEX_HOME_DIRNAME)
        self.assertEqual(self.config_manager.get_effective_codex_home(), expected)
        self.config_manager.apply_config_to_environment()
        self.assertEqual(os.environ.get(self.configuration.CODEX_HOME_ENV_VAR), expected)

    def test_codex_inherit_home_uses_existing_environment_value(self) -> None:
        inherited_home = str(Path(self.temp_dir.name) / "existing-codex-home")
        os.environ[self.configuration.CODEX_HOME_ENV_VAR] = inherited_home

        self.config_manager.set_codex_home_strategy("inherit")

        self.assertEqual(self.config_manager.get_effective_codex_home(), inherited_home)
        self.config_manager.apply_config_to_environment()
        self.assertEqual(os.environ.get(self.configuration.CODEX_HOME_ENV_VAR), inherited_home)

    def test_codex_inherit_home_allows_unset_environment_value(self) -> None:
        self.config_manager.set_codex_home_strategy("inherit")

        self.assertIsNone(self.config_manager.get_effective_codex_home())
        self.config_manager.apply_config_to_environment()
        self.assertIsNone(os.environ.get(self.configuration.CODEX_HOME_ENV_VAR))

    def test_codex_availability_uses_resolved_executable(self) -> None:
        self.config_manager.set_codex_cli_path(sys.executable)
        self.assertTrue(self.config_manager.is_codex_available())
        availability = self.config_manager.get_provider_availability()
        self.assertTrue(availability["codex"])

    def test_build_codex_launch_config_uses_resolved_executable_and_home(self) -> None:
        self.config_manager.set_codex_cli_path(sys.executable)
        self.config_manager.set_codex_managed_home("~/agentrules-codex-home")

        launch = self.config_manager.build_codex_launch_config(
            cwd=self.temp_dir.name,
            config_overrides={"developer_instructions": "Test instructions"},
        )

        self.assertEqual(launch.executable_path, sys.executable)
        self.assertEqual(launch.codex_home, os.path.expanduser("~/agentrules-codex-home"))
        self.assertEqual(launch.cwd, self.temp_dir.name)
        self.assertEqual(launch.config_overrides["developer_instructions"], "Test instructions")

    def test_set_phase_model_persists_override(self) -> None:
        self.config_manager.set_phase_model("phase1", "claude-sonnet-reasoning")
        cfg = self.config_manager.load()
        self.assertEqual(cfg.models["phase1"], "claude-sonnet-reasoning")
        overrides = self.config_manager.get_model_overrides()
        self.assertEqual(overrides["phase1"], "claude-sonnet-reasoning")

        self.config_manager.set_phase_model("phase1", None)
        cfg = self.config_manager.load()
        self.assertNotIn("phase1", cfg.models)

    def test_set_logging_verbosity_normalizes_and_persists(self) -> None:
        self.config_manager.set_logging_verbosity("Verbose")
        cfg = self.config_manager.load()
        self.assertEqual(cfg.verbosity, "verbose")

        self.config_manager.set_logging_verbosity(None)
        cfg = self.config_manager.load()
        self.assertIsNone(cfg.verbosity)

    def test_resolve_log_level_honors_env_override(self) -> None:
        self.config_manager.set_logging_verbosity("quiet")
        os.environ[self.configuration.VERBOSITY_ENV_VAR] = "verbose"
        level = self.config_manager.resolve_log_level()
        self.assertEqual(level, logging.DEBUG)

    def test_resolve_log_level_defaults_to_quiet(self) -> None:
        self.config_manager.set_logging_verbosity(None)
        os.environ.pop(self.configuration.VERBOSITY_ENV_VAR, None)
        level = self.config_manager.resolve_log_level()
        self.assertEqual(level, logging.WARNING)

    def test_researcher_mode_enables_when_tavily_key_added(self) -> None:
        self.assertEqual(self.config_manager.get_researcher_mode(), "off")
        self.assertFalse(self.config_manager.has_tavily_credentials())
        self.assertFalse(self.config_manager.is_researcher_enabled())

        self.config_manager.set_provider_key("tavily", "tavily-test-key")
        self.assertTrue(self.config_manager.has_tavily_credentials())
        self.assertEqual(self.config_manager.get_researcher_mode(), "on")
        self.assertTrue(self.config_manager.is_researcher_enabled())

    def test_researcher_mode_resets_when_tavily_key_removed(self) -> None:
        self.config_manager.set_provider_key("tavily", "tavily-test-key")
        self.assertEqual(self.config_manager.get_researcher_mode(), "on")

        self.config_manager.set_provider_key("tavily", None)
        self.assertFalse(self.config_manager.has_tavily_credentials())
        self.assertEqual(self.config_manager.get_researcher_mode(), "off")
        self.assertFalse(self.config_manager.is_researcher_enabled())

    def test_researcher_mode_explicit_overrides(self) -> None:
        self.config_manager.set_researcher_mode("off")
        self.assertEqual(self.config_manager.get_researcher_mode(), "off")
        self.assertFalse(self.config_manager.is_researcher_enabled())

        self.config_manager.set_researcher_mode("on")
        self.assertEqual(self.config_manager.get_researcher_mode(), "on")
        self.assertFalse(self.config_manager.is_researcher_enabled())

        self.config_manager.set_provider_key("tavily", "tavily-test-key")
        self.assertTrue(self.config_manager.is_researcher_enabled())

    def test_codex_researcher_enabled_without_tavily_credentials(self) -> None:
        self.config_manager.set_phase_model("researcher", "codex-gpt-5.3-codex")
        self.config_manager.set_researcher_mode("on")

        self.assertFalse(self.config_manager.has_tavily_credentials())
        self.assertEqual(self.config_manager.get_researcher_mode(), "on")
        self.assertTrue(self.config_manager.is_researcher_enabled())

    def test_removing_tavily_key_does_not_disable_codex_researcher_mode(self) -> None:
        self.config_manager.set_phase_model("researcher", "codex-gpt-5.3-codex")
        self.config_manager.set_researcher_mode("on")

        self.config_manager.set_provider_key("tavily", None)

        self.assertEqual(self.config_manager.get_researcher_mode(), "on")
        self.assertTrue(self.config_manager.is_researcher_enabled())

    def test_tree_depth_defaults_set_and_reset(self) -> None:
        self.assertEqual(self.config_manager.get_tree_max_depth(), 5)

        self.config_manager.set_tree_max_depth(7)
        self.assertEqual(self.config_manager.get_tree_max_depth(), 7)

        cfg = self.config_manager.load()
        self.assertEqual(cfg.exclusions.tree_max_depth, 7)

        self.config_manager.reset_tree_max_depth()
        self.assertEqual(self.config_manager.get_tree_max_depth(), 5)
        cfg = self.config_manager.load()
        self.assertIsNone(cfg.exclusions.tree_max_depth)

    def test_generate_agent_scaffold_preference_persists(self) -> None:
        self.assertFalse(self.config_manager.should_generate_agent_scaffold())

        self.config_manager.set_generate_agent_scaffold(True)
        cfg = self.config_manager.load()
        self.assertTrue(cfg.outputs.generate_agent_scaffold)
        self.assertTrue(self.config_manager.should_generate_agent_scaffold())

        self.config_manager.set_generate_agent_scaffold(False)
        cfg = self.config_manager.load()
        self.assertFalse(cfg.outputs.generate_agent_scaffold)
        self.assertFalse(self.config_manager.should_generate_agent_scaffold())

    def test_generate_snapshot_preference_persists(self) -> None:
        self.assertTrue(self.config_manager.should_generate_snapshot())

        self.config_manager.set_generate_snapshot(True)
        cfg = self.config_manager.load()
        self.assertTrue(cfg.outputs.generate_snapshot)
        self.assertTrue(self.config_manager.should_generate_snapshot())

        self.config_manager.set_generate_snapshot(False)
        cfg = self.config_manager.load()
        self.assertFalse(cfg.outputs.generate_snapshot)
        self.assertFalse(self.config_manager.should_generate_snapshot())

    def test_snapshot_filename_persists_and_normalizes(self) -> None:
        self.config_manager.set_snapshot_filename("SNAPSHOT.custom.md")
        self.assertEqual(self.config_manager.get_snapshot_filename(), "SNAPSHOT.custom.md")

        self.config_manager.set_snapshot_filename("nested/SNAPSHOT.md")
        self.assertEqual(self.config_manager.get_snapshot_filename(), "SNAPSHOT.md")

    def test_managed_outputs_use_root_relative_paths(self) -> None:
        self.config_manager.set_rules_filename("CLAUDE.custom.md")
        self.config_manager.set_snapshot_filename("SNAPSHOT.custom.md")
        self.config_manager.remove_exclusion_entry("directories", "phases_output")
        self.config_manager.remove_exclusion_entry("files", "CLAUDE.custom.md")
        self.config_manager.remove_exclusion_entry("files", "SNAPSHOT.custom.md")

        directories, files, _extensions = self.config_manager.get_effective_exclusions()
        managed_paths = self.config_manager.get_managed_output_relative_paths()

        self.assertNotIn("phases_output", directories)
        self.assertNotIn("CLAUDE.custom.md", files)
        self.assertNotIn("SNAPSHOT.custom.md", files)
        self.assertEqual(
            managed_paths,
            {".cursorignore", "CLAUDE.custom.md", "SNAPSHOT.custom.md", "phases_output"},
        )

    def test_rules_tree_depth_defaults_set_and_normalizes(self) -> None:
        self.assertEqual(self.config_manager.get_rules_tree_max_depth(), 3)

        self.config_manager.set_rules_tree_max_depth(6)
        self.assertEqual(self.config_manager.get_rules_tree_max_depth(), 6)
        cfg = self.config_manager.load()
        self.assertEqual(cfg.outputs.rules_tree_max_depth, 6)

        self.config_manager.set_rules_tree_max_depth(0)
        self.assertEqual(self.config_manager.get_rules_tree_max_depth(), 3)
        cfg = self.config_manager.load()
        self.assertEqual(cfg.outputs.rules_tree_max_depth, 3)

    def test_resolve_rules_filename_uses_config_by_default(self) -> None:
        self.config_manager.set_rules_filename("CLAUDE.md")
        self.assertEqual(self.config_manager.resolve_rules_filename(), "CLAUDE.md")

    def test_resolve_rules_filename_env_overrides_config(self) -> None:
        self.config_manager.set_rules_filename("AGENTS.md")
        os.environ[self.configuration.RULES_FILENAME_ENV_VAR] = "CLAUDE.md"
        self.assertEqual(self.config_manager.resolve_rules_filename(), "CLAUDE.md")

    def test_resolve_rules_filename_invalid_env_falls_back_to_config(self) -> None:
        self.config_manager.set_rules_filename("AGENTS.md")
        os.environ[self.configuration.RULES_FILENAME_ENV_VAR] = "nested/CLAUDE.md"
        self.assertEqual(self.config_manager.resolve_rules_filename(), "AGENTS.md")

    def test_resolve_rules_filename_cli_override_beats_env(self) -> None:
        os.environ[self.configuration.RULES_FILENAME_ENV_VAR] = "CLAUDE.md"
        self.assertEqual(self.config_manager.resolve_rules_filename(override="CURSOR.md"), "CURSOR.md")
