import unittest
from pathlib import Path
from core.utils.file_system.tree_generator import get_project_tree
from ..utils.offline_stubs import patch_factory_offline
import asyncio


class Phase1OfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase1_runs_offline_and_executes_tool(self):
        tree = get_project_tree(Path('tests/tests_input'))
        if len(tree) >= 2 and tree[0] == '<project_structure>' and tree[-1] == '</project_structure>':
            tree = tree[1:-1]
        # Import after patch to ensure factory functions are patched for the analysis class
        from core.analysis.phase_1 import Phase1Analysis
        p1 = Phase1Analysis()
        res = await p1.run(tree, {"dependencies": {"flask": "latest"}})
        self.assertIn('initial_findings', res)
        self.assertIn('documentation_research', res)
        # Tool path exercised offline
        doc = res['documentation_research']
        self.assertTrue('tool_calls' in doc or 'function_calls' in doc or 'executed_tools' in doc)


if __name__ == '__main__':
    unittest.main()
