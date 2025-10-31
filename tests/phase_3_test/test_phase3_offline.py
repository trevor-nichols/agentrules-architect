import unittest
from pathlib import Path
from core.utils.file_system.tree_generator import get_project_tree
from ..utils.offline_stubs import patch_factory_offline


class Phase3OfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase3_runs_with_minimal_plan(self):
        analysis_plan = {
            'agents': [
                {
                    'id': 'agent_1',
                    'name': 'Agent One',
                    'description': 'desc',
                    'file_assignments': ['tests/tests_input/main.py']
                }
            ]
        }
        tree = get_project_tree(Path('tests/tests_input'))
        if len(tree) >= 2 and tree[0] == '<project_structure>' and tree[-1] == '</project_structure>':
            tree = tree[1:-1]
        from core.analysis.phase_3 import Phase3Analysis
        p3 = Phase3Analysis()
        res = await p3.run(analysis_plan, tree, Path('tests/tests_input'))
        self.assertIn('findings', res)
        self.assertIsInstance(res['findings'], list)


if __name__ == '__main__':
    unittest.main()
