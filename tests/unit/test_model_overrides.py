import os
import tempfile
import unittest
from importlib import reload

from agentrules.core.agents.base import ModelProvider


class ModelOverrideTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["AGENTRULES_CONFIG_DIR"] = self.temp_dir.name

        import agentrules.core.configuration as configuration_package
        import agentrules.core.configuration.constants as configuration_constants
        import agentrules.core.configuration.manager as configuration_manager_module
        import agentrules.core.configuration.model_presets as model_config
        import agentrules.core.configuration.repository as configuration_repository
        from agentrules.config import agents as agents_module

        reload(configuration_constants)
        reload(configuration_repository)
        reload(configuration_manager_module)
        reload(configuration_package)
        configuration_package.get_config_manager.cache_clear()

        reload(agents_module)
        reload(model_config)

        self.config_manager = configuration_package.get_config_manager()
        self.model_config = model_config
        self.agents_module = agents_module

    def tearDown(self) -> None:
        self.model_config.apply_user_overrides({})
        from agentrules.core.configuration import get_config_manager

        get_config_manager.cache_clear()
        self.temp_dir.cleanup()
        os.environ.pop("AGENTRULES_CONFIG_DIR", None)

    def test_apply_user_overrides_updates_phase_mapping(self) -> None:
        default_key = self.agents_module.MODEL_PRESET_DEFAULTS["phase1"]
        default_config = self.agents_module.MODEL_PRESETS[default_key]["config"]

        # Ensure defaults applied
        self.model_config.apply_user_overrides({})
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase1"], default_config)

        # Apply override
        self.config_manager.set_phase_model("phase1", "claude-sonnet-reasoning")
        self.model_config.apply_user_overrides()
        expected = self.agents_module.MODEL_PRESETS["claude-sonnet-reasoning"]["config"]
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase1"], expected)

        # Remove override and ensure default restored
        self.config_manager.set_phase_model("phase1", None)
        self.model_config.apply_user_overrides()
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase1"], default_config)

    def test_openai_registry_includes_new_gpt5_codex_and_snapshot_presets(self) -> None:
        self.assertIn("gpt-5.2-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt-5.3-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt-5.4-2026-03-05", self.agents_module.MODEL_PRESETS)

    def test_codex_registry_includes_derived_runtime_presets(self) -> None:
        self.assertIn("codex-gpt-5.1-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("codex-gpt-5.2-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("codex-gpt-5.3-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("codex-gpt-5.4", self.agents_module.MODEL_PRESETS)

        preset = self.agents_module.MODEL_PRESETS["codex-gpt-5.3-codex"]
        self.assertEqual(preset["provider"], ModelProvider.CODEX)
        self.assertEqual(preset["config"].provider, ModelProvider.CODEX)
        self.assertEqual(preset["config"].model_name, "gpt-5.3-codex")

    def test_codex_presets_are_gated_by_runtime_availability(self) -> None:
        unavailable = self.model_config.get_available_presets_for_phase(
            "phase3",
            provider_availability={
                "anthropic": False,
                "openai": False,
                "codex": False,
                "deepseek": False,
                "gemini": False,
                "xai": False,
            },
        )
        unavailable_keys = {preset.key for preset in unavailable}
        self.assertIn(self.agents_module.MODEL_PRESET_DEFAULTS["phase3"], unavailable_keys)
        self.assertNotIn("codex-gpt-5.3-codex", unavailable_keys)

        available = self.model_config.get_available_presets_for_phase(
            "phase3",
            provider_availability={
                "anthropic": False,
                "openai": False,
                "codex": True,
                "deepseek": False,
                "gemini": False,
                "xai": False,
            },
        )
        available_keys = {preset.key for preset in available}
        self.assertIn("codex-gpt-5.3-codex", available_keys)

    def test_anthropic_registry_includes_claude_sonnet_46_presets(self) -> None:
        self.assertIn("claude-sonnet-4.6", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-high", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-medium", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-low", self.agents_module.MODEL_PRESETS)

    def test_xai_registry_includes_new_grok41_fast_presets(self) -> None:
        self.assertIn("grok-4-1-fast-reasoning", self.agents_module.MODEL_PRESETS)
        self.assertIn("grok-4-1-fast-non-reasoning", self.agents_module.MODEL_PRESETS)

    def test_gemini_registry_includes_new_gemini3_preview_presets(self) -> None:
        self.assertIn("gemini-3-flash-preview", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3.1-flash-lite-preview", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3.1-pro-preview", self.agents_module.MODEL_PRESETS)
