import asyncio
import unittest

from ..utils.offline_stubs import patch_factory_offline
from core.agents.factory import factory


class OfflineSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        patch_factory_offline()

    async def test_phase2_plan_offline(self):
        arch = factory.get_architect_for_phase('phase2')
        res = await arch.create_analysis_plan({'foo': 'bar'})
        self.assertIn('plan', res)
        self.assertTrue(isinstance(res['plan'], str))

    async def test_phase4_synthesis_offline(self):
        arch = factory.get_architect_for_phase('phase4')
        res = await arch.synthesize_findings({'findings': []})
        self.assertIn('analysis', res)
        self.assertIsInstance(res['analysis'], str)

    async def test_phase5_consolidation_offline(self):
        arch = factory.get_architect_for_phase('phase5')
        res = await arch.consolidate_results({'x': 1})
        self.assertIn('report', res)
        self.assertEqual(res.get('phase'), 'Consolidation')

    async def test_final_offline(self):
        arch = factory.get_architect_for_phase('final')
        res = await arch.final_analysis({'report': 'x'})
        self.assertIn('analysis', res)
        self.assertTrue(res['analysis'].startswith('You are'))

    async def test_researcher_tool_call(self):
        # Researcher: should emit a tool call
        arch = factory.get_researcher_architect('Researcher Agent', 'research docs', ['find docs'], prompt_template=None)
        res = await arch.analyze({'dependencies': {}}, tools=[{'type':'function','function':{'name':'tavily_web_search','description':'','parameters':{'type':'object','properties':{}}}}])
        # Either tool_calls or function_calls present depending on provider; stub uses tool_calls
        self.assertTrue('tool_calls' in res or 'function_calls' in res)


if __name__ == '__main__':
    unittest.main()
