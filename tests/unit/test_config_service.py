import logging
import os
import tempfile
import unittest
from importlib import reload


class ConfigServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["AGENTRULES_CONFIG_DIR"] = self.temp_dir.name

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
