import unittest
from pathlib import Path
from unittest.mock import patch

from agentrules.core.utils.file_system.tree_generator import get_project_tree
from tests.utils.offline_stubs import patch_factory_offline


class FinalOfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_final_analysis(self):
        consolidated = {"report": "consolidated text"}
        tree = get_project_tree(Path('tests/tests_input'))
        if len(tree) >= 2 and tree[0] == '<project_structure>' and tree[-1] == '</project_structure>':
            tree = tree[1:-1]
        from agentrules.core.analysis.final_analysis import FinalAnalysis
        fa = FinalAnalysis()
        res = await fa.run(consolidated, tree)
        self.assertIn('analysis', res)
        self.assertTrue(res['analysis'].startswith('You are'))

    async def test_final_analysis_raises_when_architect_returns_error_payload(self):
        class _BrokenArchitect:
            async def final_analysis(self, consolidated_report, prompt=None):
                return {"error": "Final transport failed"}

        tree = ["src/"]
        consolidated = {"report": "consolidated text"}
        with patch(
            "agentrules.core.agents.factory.factory.get_architect_for_phase",
            return_value=_BrokenArchitect(),
        ):
            from agentrules.core.analysis.final_analysis import FinalAnalysis

            with self.assertRaisesRegex(RuntimeError, "Final transport failed"):
                await FinalAnalysis().run(consolidated, tree)


if __name__ == '__main__':
    unittest.main()
