import unittest

from google.protobuf.struct_pb2 import Struct

from core.agents.gemini import GeminiArchitect
from tests.fakes.vendor_responses import GeminiGenerateContentResponseFake, _FunctionCallFake


class _GeminiFakeModelsService:
    def generate_content(self, model, contents, config=None):
        s = Struct(); s.update({"query": "flask"})
        fc = _FunctionCallFake("tavily_search", s)
        return GeminiGenerateContentResponseFake(text="hello", function_call=fc)


class _GeminiFakeClient:
    def __init__(self):
        self.models = _GeminiFakeModelsService()


class GeminiArchitectParsingTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_text_and_function_calls(self):
        arch = GeminiArchitect()
        # Inject fake client
        arch.client = _GeminiFakeClient()  # type: ignore
        res = await arch.analyze({"x": 1})
        self.assertEqual(res.get("findings"), "hello")
        self.assertIn("function_calls", res)
        fc = res["function_calls"][0]
        self.assertEqual(fc["name"], "tavily_search")
        self.assertEqual(fc["args"].get("query"), "flask")
