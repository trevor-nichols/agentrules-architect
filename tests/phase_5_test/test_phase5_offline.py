import unittest
from unittest.mock import patch

from tests.utils.offline_stubs import patch_factory_offline


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
        from agentrules.core.analysis.phase_5 import Phase5Analysis
        p5 = Phase5Analysis()
        res = await p5.run(all_results)
        self.assertIn('report', res)
        self.assertEqual(res.get('phase'), 'Consolidation')

    async def test_phase5_raises_when_architect_returns_error_payload(self):
        class _BrokenArchitect:
            async def consolidate_results(self, all_results, prompt=None):
                return {"error": "Separator is found, but chunk is longer than limit"}

        all_results = {"phase1": {}, "phase2": {}, "phase3": {}, "phase4": {}}
        with patch("agentrules.core.analysis.phase_5.get_architect_for_phase", return_value=_BrokenArchitect()):
            from agentrules.core.analysis.phase_5 import Phase5Analysis

            with self.assertRaisesRegex(RuntimeError, "chunk is longer than limit"):
                await Phase5Analysis().run(all_results)


if __name__ == '__main__':
    unittest.main()
