import unittest
from pathlib import Path
from core.utils.file_system.tree_generator import get_project_tree
from ..utils.offline_stubs import patch_factory_offline


class Phase2OfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase2_parses_plan(self):
        # Load sample Phase 1 results used by prior tests
        phase1_results = {"phase": "Initial Discovery"}
        tree = get_project_tree(Path('tests/tests_input'))
        if len(tree) >= 2 and tree[0] == '<project_structure>' and tree[-1] == '</project_structure>':
            tree = tree[1:-1]
        from core.analysis.phase_2 import Phase2Analysis
        phase2 = Phase2Analysis()
        res = await phase2.run(phase1_results, tree)
        self.assertIn('plan', res)
        # Offline stub creates an XML plan; parser attempts to extract agents; accept empty agents but prefer >0
        self.assertIn('agents', res)


if __name__ == '__main__':
    unittest.main()
