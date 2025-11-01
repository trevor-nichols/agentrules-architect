import os
import tempfile
import unittest
from importlib import reload


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
