import unittest
from ..utils.offline_stubs import patch_factory_offline


class Phase4OfflineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase4_synthesis(self):
        phase3_results = {"phase": "Deep Analysis", "findings": []}
        from core.analysis.phase_4 import Phase4Analysis
        p4 = Phase4Analysis()
        res = await p4.run(phase3_results)
        self.assertIn('analysis', res)
        self.assertIsInstance(res['analysis'], str)


if __name__ == '__main__':
    unittest.main()
