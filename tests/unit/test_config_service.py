import os
import tempfile
import unittest
from importlib import reload


class ConfigServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["AGENTRULES_CONFIG_DIR"] = self.temp_dir.name
        from agentrules import config_service

        reload(config_service)
        self.config_service = config_service
        self._env_backup = {}
        for env_var in self.config_service.PROVIDER_ENV_MAP.values():
            self._env_backup[env_var] = os.environ.pop(env_var, None)
        self._verbosity_backup = os.environ.pop(self.config_service.VERBOSITY_ENV_VAR, None)
        self._offline_backup = os.environ.pop("OFFLINE", None)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("AGENTRULES_CONFIG_DIR", None)
        for env_var, value in self._env_backup.items():
            if value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = value
        if self._verbosity_backup is None:
            os.environ.pop(self.config_service.VERBOSITY_ENV_VAR, None)
        else:
            os.environ[self.config_service.VERBOSITY_ENV_VAR] = self._verbosity_backup
        if self._offline_backup is None:
            os.environ.pop("OFFLINE", None)
        else:
            os.environ["OFFLINE"] = self._offline_backup

    def test_set_provider_key_persists_and_sets_env(self) -> None:
        self.config_service.set_provider_key("openai", "test-key-123")
        config = self.config_service.load_config()

        self.assertIn("openai", config.providers)
        self.assertEqual(config.providers["openai"].api_key, "test-key-123")
        self.assertEqual(os.environ.get("OPENAI_API_KEY"), "test-key-123")

    def test_get_current_provider_keys_masks_missing(self) -> None:
        keys = self.config_service.get_current_provider_keys()
        self.assertIsInstance(keys, dict)
        self.assertIn("openai", keys)
        self.assertIsNone(keys.get("openai"))

    def test_set_phase_model_persists_override(self) -> None:
        self.config_service.set_phase_model("phase1", "claude-sonnet-reasoning")
        cfg = self.config_service.load_config()
        self.assertEqual(cfg.models["phase1"], "claude-sonnet-reasoning")
        overrides = self.config_service.get_model_overrides()
        self.assertEqual(overrides["phase1"], "claude-sonnet-reasoning")

        self.config_service.set_phase_model("phase1", None)
        cfg = self.config_service.load_config()
        self.assertNotIn("phase1", cfg.models)

    def test_set_logging_verbosity_normalizes_and_persists(self) -> None:
        self.config_service.set_logging_verbosity("Verbose")
        cfg = self.config_service.load_config()
        self.assertEqual(cfg.verbosity, "verbose")

        self.config_service.set_logging_verbosity(None)
        cfg = self.config_service.load_config()
        self.assertIsNone(cfg.verbosity)

    def test_resolve_log_level_honors_env_override(self) -> None:
        self.config_service.set_logging_verbosity("quiet")
        os.environ[self.config_service.VERBOSITY_ENV_VAR] = "verbose"
        level = self.config_service.resolve_log_level()
        self.assertEqual(level, self.config_service.logging.DEBUG)

    def test_resolve_log_level_defaults_to_quiet(self) -> None:
        self.config_service.set_logging_verbosity(None)
        os.environ.pop(self.config_service.VERBOSITY_ENV_VAR, None)
        level = self.config_service.resolve_log_level()
        self.assertEqual(level, self.config_service.logging.WARNING)

    def test_researcher_mode_auto_requires_tavily_key(self) -> None:
        self.assertEqual(self.config_service.get_researcher_mode(), "auto")
        self.assertFalse(self.config_service.has_tavily_credentials())
        self.assertFalse(self.config_service.is_researcher_enabled())

        self.config_service.set_provider_key("tavily", "tavily-test-key")
        self.assertTrue(self.config_service.has_tavily_credentials())
        self.assertTrue(self.config_service.is_researcher_enabled())

    def test_researcher_mode_explicit_overrides(self) -> None:
        self.config_service.set_researcher_mode("off")
        self.assertEqual(self.config_service.get_researcher_mode(), "off")
        self.assertFalse(self.config_service.is_researcher_enabled())

        self.config_service.set_researcher_mode("on")
        self.assertEqual(self.config_service.get_researcher_mode(), "on")
        self.assertTrue(self.config_service.is_researcher_enabled())

    def test_tree_depth_defaults_set_and_reset(self) -> None:
        self.assertEqual(self.config_service.get_tree_max_depth(), 4)

        self.config_service.set_tree_max_depth(7)
        self.assertEqual(self.config_service.get_tree_max_depth(), 7)

        cfg = self.config_service.load_config()
        self.assertEqual(cfg.exclusions.tree_max_depth, 7)

        self.config_service.reset_tree_max_depth()
        self.assertEqual(self.config_service.get_tree_max_depth(), 4)
        cfg = self.config_service.load_config()
        self.assertIsNone(cfg.exclusions.tree_max_depth)
