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

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("AGENTRULES_CONFIG_DIR", None)
        for env_var, value in self._env_backup.items():
            if value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = value

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
