import unittest
from pathlib import Path
from core.utils.file_system.tree_generator import get_project_tree
from ..utils.offline_stubs import patch_factory_offline


class FinalOfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_final_analysis(self):
        consolidated = {"report": "consolidated text"}
        tree = get_project_tree(Path('tests/tests_input'))
        if len(tree) >= 2 and tree[0] == '<project_structure>' and tree[-1] == '</project_structure>':
            tree = tree[1:-1]
        from core.analysis.final_analysis import FinalAnalysis
        fa = FinalAnalysis()
        res = await fa.run(consolidated, tree)
        self.assertIn('analysis', res)
        self.assertTrue(res['analysis'].startswith('You are'))


if __name__ == '__main__':
    unittest.main()
