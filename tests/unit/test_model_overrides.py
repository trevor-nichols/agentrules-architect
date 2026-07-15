import os
import tempfile
import unittest
from importlib import reload

from agentrules.core.agents.base import ModelProvider, ReasoningMode
from agentrules.core.types import models as model_types


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

    def test_apply_user_overrides_remaps_legacy_gemini_preview_presets_without_warning_by_default(self) -> None:
        self.config_manager.set_phase_model("phase3", "gemini-3-pro-preview")
        self.config_manager.set_phase_model("phase4", "gemini-3.1-flash-lite-preview")

        with self.assertNoLogs("agentrules.core.configuration.model_presets", level="WARNING"):
            applied = self.model_config.apply_user_overrides()

        self.assertEqual(applied["phase3"], "gemini-3.1-pro-preview")
        self.assertEqual(applied["phase4"], "gemini-3.1-flash-lite")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].model_name, "gemini-3.1-pro-preview")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].model_name, "gemini-3.1-flash-lite")

    def test_apply_user_overrides_can_warn_for_legacy_gemini_preview_runtime_remap(self) -> None:
        self.config_manager.set_phase_model("phase3", "gemini-3-pro-preview")
        self.config_manager.set_phase_model("phase4", "gemini-3.1-flash-lite-preview")

        with self.assertLogs("agentrules.core.configuration.model_presets", level="WARNING") as captured:
            applied = self.model_config.apply_user_overrides(warn_deprecated=True)

        self.assertEqual(applied["phase3"], "gemini-3.1-pro-preview")
        self.assertEqual(applied["phase4"], "gemini-3.1-flash-lite")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].model_name, "gemini-3.1-pro-preview")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].model_name, "gemini-3.1-flash-lite")
        self.assertTrue(any("gemini-3-pro-preview" in message for message in captured.output))
        self.assertTrue(any("gemini-3.1-flash-lite-preview" in message for message in captured.output))

    def test_apply_user_overrides_remaps_legacy_xai_presets_without_warning_by_default(self) -> None:
        self.config_manager.set_phase_model("phase3", "grok-4-0709")
        self.config_manager.set_phase_model("phase4", "grok-code-fast")

        with self.assertNoLogs("agentrules.core.configuration.model_presets", level="WARNING"):
            applied = self.model_config.apply_user_overrides()

        self.assertEqual(applied["phase3"], "grok-4.3-reasoning-medium")
        self.assertEqual(applied["phase4"], "grok-build-0.1")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].model_name, "grok-4.3")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].reasoning, ReasoningMode.MEDIUM)
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].model_name, "grok-build-0.1")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].reasoning, ReasoningMode.ENABLED)

    def test_apply_user_overrides_can_warn_for_legacy_xai_runtime_remap(self) -> None:
        self.config_manager.set_phase_model("phase3", "grok-4-fast-non-reasoning")
        self.config_manager.set_phase_model("phase4", "grok-code-fast")

        with self.assertLogs("agentrules.core.configuration.model_presets", level="WARNING") as captured:
            applied = self.model_config.apply_user_overrides(warn_deprecated=True)

        self.assertEqual(applied["phase3"], "grok-4.3-non-reasoning")
        self.assertEqual(applied["phase4"], "grok-build-0.1")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].model_name, "grok-4.3")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].reasoning, ReasoningMode.DISABLED)
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].model_name, "grok-build-0.1")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].reasoning, ReasoningMode.ENABLED)
        self.assertTrue(any("grok-4-fast-non-reasoning" in message for message in captured.output))
        self.assertTrue(any("grok-code-fast" in message for message in captured.output))

    def test_apply_user_overrides_remaps_legacy_deepseek_presets(self) -> None:
        self.config_manager.set_phase_model("phase3", "deepseek-chat")
        self.config_manager.set_phase_model("phase4", "deepseek-reasoner")

        with self.assertLogs("agentrules.core.configuration.model_presets", level="WARNING") as captured:
            applied = self.model_config.apply_user_overrides(warn_deprecated=True)

        self.assertEqual(applied["phase3"], "deepseek-v4-flash-non-reasoning")
        self.assertEqual(applied["phase4"], "deepseek-v4-flash")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].model_name, "deepseek-v4-flash")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"].reasoning, ReasoningMode.DISABLED)
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].model_name, "deepseek-v4-flash")
        self.assertEqual(self.agents_module.MODEL_CONFIG["phase4"].reasoning, ReasoningMode.HIGH)
        self.assertTrue(any("deepseek-chat" in message for message in captured.output))
        self.assertTrue(any("deepseek-reasoner" in message for message in captured.output))

    def test_get_configured_presets_preserves_legacy_deepseek_keys(self) -> None:
        configured = self.model_config.get_configured_presets(
            {"phase3": "deepseek-chat", "phase4": "deepseek-reasoner"}
        )

        self.assertEqual(configured["phase3"], "deepseek-chat")
        self.assertEqual(configured["phase4"], "deepseek-reasoner")

    def test_deepseek_registry_includes_v4_presets_and_legacy_configs_use_v4(self) -> None:
        expected_keys = {
            "deepseek-v4-flash",
            "deepseek-v4-flash-non-reasoning",
            "deepseek-v4-pro",
            "deepseek-v4-pro-max",
            "deepseek-v4-pro-non-reasoning",
            "deepseek-chat",
            "deepseek-reasoner",
        }
        self.assertTrue(expected_keys.issubset(self.agents_module.MODEL_PRESETS))
        self.assertEqual(self.agents_module.MODEL_PRESETS["deepseek-chat"]["config"].model_name, "deepseek-v4-flash")
        self.assertEqual(
            self.agents_module.MODEL_PRESETS["deepseek-reasoner"]["config"].model_name,
            "deepseek-v4-flash",
        )

    def test_get_active_presets_remaps_legacy_gemini_preview_presets_for_runtime(self) -> None:
        active = self.model_config.get_active_presets(
            {
                "phase3": "gemini-3-pro-preview",
                "phase4": "gemini-3.1-flash-lite-preview",
            }
        )

        self.assertEqual(active["phase3"], "gemini-3.1-pro-preview")
        self.assertEqual(active["phase4"], "gemini-3.1-flash-lite")

    def test_get_active_presets_remaps_legacy_xai_presets_for_runtime(self) -> None:
        active = self.model_config.get_active_presets(
            {
                "phase3": "grok-4-0709",
                "phase4": "grok-code-fast",
            }
        )

        self.assertEqual(active["phase3"], "grok-4.3-reasoning-medium")
        self.assertEqual(active["phase4"], "grok-build-0.1")

    def test_get_active_presets_respects_explicit_empty_overrides(self) -> None:
        self.config_manager.set_phase_model("phase3", "gemini-3-pro-preview")
        active = self.model_config.get_active_presets({})

        self.assertEqual(active["phase3"], self.agents_module.MODEL_PRESET_DEFAULTS["phase3"])

    def test_get_configured_presets_preserves_legacy_gemini_preview_presets(self) -> None:
        configured = self.model_config.get_configured_presets(
            {
                "phase3": "gemini-3-pro-preview",
                "phase4": "gemini-3.1-flash-lite-preview",
            }
        )

        self.assertEqual(configured["phase3"], "gemini-3-pro-preview")
        self.assertEqual(configured["phase4"], "gemini-3.1-flash-lite-preview")

    def test_get_configured_presets_preserves_legacy_xai_presets(self) -> None:
        configured = self.model_config.get_configured_presets(
            {
                "phase3": "grok-4-fast-non-reasoning",
                "phase4": "grok-code-fast",
            }
        )

        self.assertEqual(configured["phase3"], "grok-4-fast-non-reasoning")
        self.assertEqual(configured["phase4"], "grok-code-fast")

    def test_get_configured_presets_respects_explicit_empty_overrides(self) -> None:
        self.config_manager.set_phase_model("phase3", "gemini-3-pro-preview")
        configured = self.model_config.get_configured_presets({})

        self.assertEqual(configured["phase3"], self.agents_module.MODEL_PRESET_DEFAULTS["phase3"])

    def test_get_active_preset_key_remaps_legacy_gemini_preview_presets_for_runtime(self) -> None:
        self.assertEqual(
            self.model_config.get_active_preset_key("phase3", {"phase3": "gemini-3-pro-preview"}),
            "gemini-3.1-pro-preview",
        )
        self.assertEqual(
            self.model_config.get_active_preset_key("phase4", {"phase4": "gemini-3.1-flash-lite-preview"}),
            "gemini-3.1-flash-lite",
        )

    def test_get_active_preset_key_remaps_legacy_xai_presets_for_runtime(self) -> None:
        self.assertEqual(
            self.model_config.get_active_preset_key("phase3", {"phase3": "grok-4-0709"}),
            "grok-4.3-reasoning-medium",
        )
        self.assertEqual(
            self.model_config.get_active_preset_key("phase4", {"phase4": "grok-code-fast"}),
            "grok-build-0.1",
        )

    def test_get_model_config_for_preset_key_remaps_legacy_gemini_preview_presets_for_runtime(self) -> None:
        phase3_config = self.model_config.get_model_config_for_preset_key("gemini-3-pro-preview")
        phase4_config = self.model_config.get_model_config_for_preset_key("gemini-3.1-flash-lite-preview")

        assert phase3_config is not None
        assert phase4_config is not None
        self.assertEqual(phase3_config.model_name, "gemini-3.1-pro-preview")
        self.assertEqual(phase4_config.model_name, "gemini-3.1-flash-lite")

    def test_get_model_config_for_preset_key_remaps_legacy_xai_presets_for_runtime(self) -> None:
        phase3_config = self.model_config.get_model_config_for_preset_key("grok-4-fast-non-reasoning")
        phase4_config = self.model_config.get_model_config_for_preset_key("grok-code-fast")

        assert phase3_config is not None
        assert phase4_config is not None
        self.assertEqual(phase3_config.model_name, "grok-4.3")
        self.assertEqual(phase3_config.reasoning, ReasoningMode.DISABLED)
        self.assertEqual(phase4_config.model_name, "grok-build-0.1")
        self.assertEqual(phase4_config.reasoning, ReasoningMode.ENABLED)

    def test_apply_user_overrides_respects_explicit_empty_overrides(self) -> None:
        default_key = self.agents_module.MODEL_PRESET_DEFAULTS["phase3"]
        default_config = self.agents_module.MODEL_PRESETS[default_key]["config"]

        self.config_manager.set_phase_model("phase3", "gemini-3-pro-preview")
        self.model_config.apply_user_overrides({})

        self.assertEqual(self.agents_module.MODEL_CONFIG["phase3"], default_config)

    def test_legacy_exported_gemini_constants_preserve_original_model_names(self) -> None:
        self.assertEqual(model_types.GEMINI_3_PRO_PREVIEW.model_name, "gemini-3-pro-preview")
        self.assertEqual(
            model_types.GEMINI_3_1_FLASH_LITE_PREVIEW.model_name,
            "gemini-3.1-flash-lite-preview",
        )

    def test_default_phase_presets_use_gpt55_default(self) -> None:
        self.assertTrue(self.agents_module.MODEL_PRESET_DEFAULTS)
        self.assertTrue(all(value == "gpt55-default" for value in self.agents_module.MODEL_PRESET_DEFAULTS.values()))

    def test_apply_user_overrides_accepts_dynamic_codex_runtime_model(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview")

        self.config_manager.set_phase_model("phase3", runtime_model_key)
        self.model_config.apply_user_overrides()

        phase3_config = self.agents_module.MODEL_CONFIG["phase3"]
        self.assertEqual(phase3_config.provider, ModelProvider.CODEX)
        self.assertEqual(phase3_config.model_name, "gpt-6-codex-preview")
        self.assertEqual(phase3_config.reasoning, ReasoningMode.DYNAMIC)

    def test_apply_user_overrides_accepts_codex_runtime_default_key(self) -> None:
        self.config_manager.set_phase_model("phase3", self.model_config.CODEX_RUNTIME_DEFAULT_KEY)
        self.model_config.apply_user_overrides()

        phase3_config = self.agents_module.MODEL_CONFIG["phase3"]
        self.assertEqual(phase3_config.provider, ModelProvider.CODEX)
        self.assertEqual(phase3_config.model_name, self.model_config.CODEX_RUNTIME_DEFAULT_MODEL_NAME)
        self.assertEqual(phase3_config.reasoning, ReasoningMode.DYNAMIC)

    def test_dynamic_codex_runtime_key_generates_preset_info(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview")

        preset_info = self.model_config.get_preset_info(runtime_model_key)

        self.assertIsNotNone(preset_info)
        assert preset_info is not None
        self.assertEqual(preset_info.provider, ModelProvider.CODEX)
        self.assertIn("gpt-6-codex-preview", preset_info.label)

    def test_codex_runtime_default_key_generates_preset_info(self) -> None:
        preset_info = self.model_config.get_preset_info(self.model_config.CODEX_RUNTIME_DEFAULT_KEY)

        self.assertIsNotNone(preset_info)
        assert preset_info is not None
        self.assertEqual(preset_info.provider, ModelProvider.CODEX)
        self.assertEqual(preset_info.key, self.model_config.CODEX_RUNTIME_DEFAULT_KEY)
        self.assertIn("runtime default", preset_info.label.lower())

    def test_legacy_codex_gpt54_resolves_to_runtime_model_name(self) -> None:
        model_name = self.model_config.resolve_codex_model_name_for_preset_key("codex-gpt-5.4")

        self.assertEqual(model_name, "gpt-5.4")

    def test_legacy_codex_runtime_gpt54_key_resolves_to_runtime_model_name(self) -> None:
        model_name = self.model_config.resolve_codex_model_name_for_preset_key(
            "codex-runtime:gpt-5.4-2026-03-05|effort=medium"
        )

        self.assertEqual(model_name, "gpt-5.4")

    def test_apply_user_overrides_accepts_legacy_codex_runtime_model_key(self) -> None:
        self.config_manager.set_phase_model("phase3", "codex-runtime:gpt-5.4-2026-03-05|effort=medium")
        self.model_config.apply_user_overrides()

        phase3_config = self.agents_module.MODEL_CONFIG["phase3"]
        self.assertEqual(phase3_config.provider, ModelProvider.CODEX)
        self.assertEqual(phase3_config.model_name, "gpt-5.4-2026-03-05")
        self.assertEqual(phase3_config.reasoning, ReasoningMode.MEDIUM)

    def test_dynamic_codex_runtime_key_with_effort_generates_reasoning_variant(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key(
            "gpt-6-codex-preview",
            reasoning_effort="high",
        )

        preset_info = self.model_config.get_preset_info(runtime_model_key)

        self.assertIsNotNone(preset_info)
        assert preset_info is not None
        self.assertEqual(preset_info.provider, ModelProvider.CODEX)
        self.assertIn("(high)", preset_info.label.lower())

    def test_apply_user_overrides_accepts_dynamic_codex_runtime_model_with_default_effort(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key(
            "gpt-6-codex-preview",
            reasoning_effort="medium",
        )

        self.config_manager.set_phase_model("phase3", runtime_model_key)
        self.model_config.apply_user_overrides()

        phase3_config = self.agents_module.MODEL_CONFIG["phase3"]
        self.assertEqual(phase3_config.provider, ModelProvider.CODEX)
        self.assertEqual(phase3_config.model_name, "gpt-6-codex-preview")
        self.assertEqual(phase3_config.reasoning, ReasoningMode.MEDIUM)

    def test_apply_user_overrides_accepts_dynamic_codex_runtime_model_with_explicit_effort(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key(
            "gpt-6-codex-preview",
            reasoning_effort="low",
        )

        self.config_manager.set_phase_model("phase3", runtime_model_key)
        self.model_config.apply_user_overrides()

        phase3_config = self.agents_module.MODEL_CONFIG["phase3"]
        self.assertEqual(phase3_config.provider, ModelProvider.CODEX)
        self.assertEqual(phase3_config.model_name, "gpt-6-codex-preview")
        self.assertEqual(phase3_config.reasoning, ReasoningMode.LOW)

    def test_runtime_codex_catalog_presets_include_catalog_models(self) -> None:
        catalog_entries = [
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-5.3-codex",
                display_name="GPT-5.3 Codex",
                description="Already defined internally.",
                is_default=True,
            ),
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only.",
            ),
        ]

        presets = self.model_config.build_codex_runtime_preset_infos(catalog_entries)
        preset_keys = {preset.key for preset in presets}

        self.assertIn(self.model_config.CODEX_RUNTIME_DEFAULT_KEY, preset_keys)
        self.assertIn(self.model_config.make_codex_runtime_preset_key("gpt-5.3-codex"), preset_keys)
        self.assertIn(self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview"), preset_keys)

    def test_runtime_codex_catalog_presets_expand_reasoning_variants(self) -> None:
        catalog_entries = [
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-6-codex-preview",
                display_name="GPT-6 Codex Preview",
                description="Runtime-only.",
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    self.model_config.CodexRuntimeModelReasoningOption(
                        reasoning_effort="none",
                        description="Disable reasoning.",
                    ),
                    self.model_config.CodexRuntimeModelReasoningOption(
                        reasoning_effort="medium",
                        description="Balanced reasoning.",
                    ),
                    self.model_config.CodexRuntimeModelReasoningOption(
                        reasoning_effort="xhigh",
                        description="Maximum depth.",
                    ),
                ),
            ),
        ]

        presets = self.model_config.build_codex_runtime_preset_infos(catalog_entries)
        preset_keys = {preset.key for preset in presets}

        self.assertNotIn(
            self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview"),
            preset_keys,
        )
        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="none"),
            preset_keys,
        )
        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="medium"),
            preset_keys,
        )
        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-6-codex-preview", reasoning_effort="xhigh"),
            preset_keys,
        )

    def test_runtime_codex_catalog_presets_include_no_effort_and_supported_efforts(self) -> None:
        catalog_entries = [
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-5.2-codex",
                display_name="GPT-5.2 Codex",
                description="Doc-shaped entry.",
                default_reasoning_effort="medium",
                supported_reasoning_efforts=(
                    self.model_config.CodexRuntimeModelReasoningOption(
                        reasoning_effort="low",
                        description="Lower latency.",
                    ),
                ),
            ),
        ]

        presets = self.model_config.build_codex_runtime_preset_infos(catalog_entries)
        preset_keys = {preset.key for preset in presets}

        self.assertNotIn(
            self.model_config.make_codex_runtime_preset_key("gpt-5.2-codex"),
            preset_keys,
        )
        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-5.2-codex", reasoning_effort="low"),
            preset_keys,
        )
        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-5.2-codex", reasoning_effort="medium"),
            preset_keys,
        )

    def test_runtime_codex_catalog_presets_dedupe_alias_equivalent_models(self) -> None:
        catalog_entries = [
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-5.4-2026-03-05",
                display_name="GPT-5.4",
                description="Legacy identifier.",
                default_reasoning_effort="medium",
            ),
            self.model_config.CodexRuntimeModelCatalogEntry(
                model="gpt-5.4",
                display_name="GPT-5.4",
                description="Canonical identifier.",
                default_reasoning_effort="medium",
            ),
        ]

        presets = self.model_config.build_codex_runtime_preset_infos(catalog_entries)
        preset_keys = {preset.key for preset in presets}

        self.assertIn(
            self.model_config.make_codex_runtime_preset_key("gpt-5.4", reasoning_effort="medium"),
            preset_keys,
        )
        self.assertNotIn(
            self.model_config.make_codex_runtime_preset_key("gpt-5.4-2026-03-05", reasoning_effort="medium"),
            preset_keys,
        )

    def test_runtime_codex_preset_key_round_trips_reasoning_effort(self) -> None:
        runtime_model_key = self.model_config.make_codex_runtime_preset_key(
            "gpt-6-codex-preview",
            reasoning_effort="xhigh",
        )

        selection = self.model_config.parse_codex_runtime_preset_selection(runtime_model_key)

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.model_name, "gpt-6-codex-preview")
        self.assertEqual(selection.reasoning_effort, "xhigh")

    def test_openai_registry_includes_new_gpt5_codex_and_snapshot_presets(self) -> None:
        self.assertIn("gpt55-none", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt55-default", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt55-xhigh", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt-5.2-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt-5.3-codex", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt-5.4-2026-03-05", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt54-mini-none", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt54-mini-xhigh", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt54-nano-none", self.agents_module.MODEL_PRESETS)
        self.assertIn("gpt54-nano-xhigh", self.agents_module.MODEL_PRESETS)

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
                "claude_code": False,
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
                "claude_code": False,
                "openai": False,
                "codex": True,
                "deepseek": False,
                "gemini": False,
                "xai": False,
            },
        )
        available_keys = {preset.key for preset in available}
        self.assertIn("codex-gpt-5.3-codex", available_keys)

    def test_claude_code_registry_includes_derived_runtime_presets(self) -> None:
        self.assertIn("claude-code-sonnet-4.6", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-code-sonnet-4.6-reasoning-high", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-code-opus-4.6-reasoning-max", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-code-opus-4.7-reasoning-xhigh", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-code-opus-4.8-reasoning-max", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-code-haiku", self.agents_module.MODEL_PRESETS)

        base_preset = self.agents_module.MODEL_PRESETS["claude-sonnet-4.6"]
        preset = self.agents_module.MODEL_PRESETS["claude-code-sonnet-4.6"]
        self.assertEqual(preset["provider"], ModelProvider.CLAUDE_CODE)
        self.assertEqual(preset["config"].provider, ModelProvider.CLAUDE_CODE)
        self.assertEqual(preset["config"].model_name, "claude-sonnet-4-6")
        self.assertEqual(base_preset["config"].estimator_family, "anthropic_api")
        self.assertEqual(preset["config"].estimator_family, "tiktoken")
        self.assertEqual(
            self.agents_module.MODEL_PRESETS["claude-code-sonnet-4.6-reasoning-high"]["config"].estimator_family,
            "tiktoken",
        )

    def test_claude_code_presets_are_gated_by_runtime_availability(self) -> None:
        unavailable = self.model_config.get_available_presets_for_phase(
            "phase3",
            provider_availability={
                "anthropic": False,
                "claude_code": False,
                "openai": False,
                "codex": False,
                "deepseek": False,
                "gemini": False,
                "xai": False,
            },
        )
        unavailable_keys = {preset.key for preset in unavailable}
        self.assertNotIn("claude-code-sonnet-4.6", unavailable_keys)

        available = self.model_config.get_available_presets_for_phase(
            "phase3",
            provider_availability={
                "anthropic": False,
                "claude_code": True,
                "openai": False,
                "codex": False,
                "deepseek": False,
                "gemini": False,
                "xai": False,
            },
        )
        available_keys = {preset.key for preset in available}
        self.assertIn("claude-code-sonnet-4.6", available_keys)

    def test_anthropic_registry_includes_claude_sonnet_46_presets(self) -> None:
        self.assertIn("claude-sonnet-4.6", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-high", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-medium", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-sonnet-4.6-reasoning-low", self.agents_module.MODEL_PRESETS)

    def test_anthropic_registry_includes_claude_opus_47_and_48_presets(self) -> None:
        self.assertIn("claude-opus-4.7", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-opus-4.7-reasoning-xhigh", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-opus-4.8", self.agents_module.MODEL_PRESETS)
        self.assertIn("claude-opus-4.8-reasoning-max", self.agents_module.MODEL_PRESETS)

    def test_xai_registry_includes_new_grok41_fast_presets(self) -> None:
        self.assertIn("grok-4-1-fast-reasoning", self.agents_module.MODEL_PRESETS)
        self.assertIn("grok-4-1-fast-non-reasoning", self.agents_module.MODEL_PRESETS)

    def test_xai_registry_includes_canonical_grok43_and_build_presets(self) -> None:
        self.assertIn("grok-4.3", self.agents_module.MODEL_PRESETS)
        self.assertIn("grok-4.3-reasoning-medium", self.agents_module.MODEL_PRESETS)
        self.assertIn("grok-4.3-non-reasoning", self.agents_module.MODEL_PRESETS)
        self.assertIn("grok-build-0.1", self.agents_module.MODEL_PRESETS)
        self.assertEqual(self.agents_module.MODEL_PRESETS["grok-4.3"]["config"].model_name, "grok-4.3")
        self.assertEqual(
            self.agents_module.MODEL_PRESETS["grok-4.3-reasoning-medium"]["config"].reasoning,
            ReasoningMode.MEDIUM,
        )
        self.assertEqual(
            self.agents_module.MODEL_PRESETS["grok-4.3-non-reasoning"]["config"].reasoning,
            ReasoningMode.DISABLED,
        )
        self.assertEqual(
            self.agents_module.MODEL_PRESETS["grok-build-0.1"]["config"].model_name,
            "grok-build-0.1",
        )

    def test_gemini_registry_includes_current_gemini3_presets(self) -> None:
        self.assertIn("gemini-3.5-flash", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3-flash-preview", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3.1-flash-lite", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3.1-flash-lite-preview", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3.1-pro-preview", self.agents_module.MODEL_PRESETS)
        self.assertIn("gemini-3-pro-preview", self.agents_module.MODEL_PRESETS)
