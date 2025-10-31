import unittest
from ..utils.offline_stubs import patch_factory_offline


class Phase5OfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase5_consolidation(self):
        all_results = {
            "phase1": {},
            "phase2": {},
            "phase3": {},
            "phase4": {"analysis": "some findings"},
        }
        from core.analysis.phase_5 import Phase5Analysis
        p5 = Phase5Analysis()
        res = await p5.run(all_results)
        self.assertIn('report', res)
        self.assertEqual(res.get('phase'), 'Consolidation')


if __name__ == '__main__':
    unittest.main()
