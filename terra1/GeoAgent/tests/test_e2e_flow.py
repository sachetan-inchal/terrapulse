import unittest
import asyncio
from geoagent.core.factory import for_anymap
from geoagent.core.config import GeoAgentConfig
import litellm
import httpx


class MockAnyMap:
    def __init__(self):
        self.center = [0.0, 0.0]
        self.zoom = 1
        self.markers = []

    def set_center(self, lng, lat):
        self.center = [lng, lat]

    def set_zoom(self, zoom):
        self.zoom = zoom

    def fly_to(self, lat, lon, zoom=None):
        self.center = [lon, lat]
        if zoom is not None:
            self.zoom = zoom

    def add_marker(self, lon, lat, popup=None, tooltip=None):
        self.markers.append({"lon": lon, "lat": lat, "popup": popup, "tooltip": tooltip})


class TestMultiTurnAndRateLimitFlow(unittest.TestCase):
    def test_complete_sequence_bengaluru_navigation(self):
        """Test full multi-turn sequence:
        User asks -> Model calls locate -> Tool returns coordinates ->
        Model calls map navigation (set_center/fly_to) -> Map updates -> Model responds.
        """
        mock_map = MockAnyMap()
        agent = for_anymap(
            mock_map,
            config=GeoAgentConfig(provider="litellm", model="groq/openai/gpt-oss-120b"),
            fast=True,
        )

        turn = 0
        executed_tool_calls = []

        async def mock_acompletion(*args, **kwargs):
            nonlocal turn
            turn += 1
            if turn == 1:
                # Turn 1: Model outputs reasoning + calls locate_geographical_feature
                class Chunk1:
                    class Choice:
                        class Delta:
                            content = None
                            reasoning_content = "The user wants to locate Bengaluru. I will call locate_geographical_feature."
                            tool_calls = [
                                type("TC", (), {
                                    "index": 0,
                                    "id": "call_locate_1",
                                    "function": type("F", (), {
                                        "name": "locate_geographical_feature",
                                        "arguments": '{"name": "Bengaluru"}'
                                    })()
                                })()
                            ]
                        delta = Delta()
                        finish_reason = "tool_calls"
                    choices = [Choice()]
                async def gen1():
                    yield Chunk1()
                return gen1()

            elif turn == 2:
                # Turn 2: After locate returns, model calls fly_to to move the map
                class Chunk2:
                    class Choice:
                        class Delta:
                            content = None
                            reasoning_content = "Bengaluru is at 12.9716, 77.5946. Now navigating map."
                            tool_calls = [
                                type("TC", (), {
                                    "index": 0,
                                    "id": "call_flyto_2",
                                    "function": type("F", (), {
                                        "name": "fly_to",
                                        "arguments": '{"lat": 12.9716, "lon": 77.5946, "zoom": 12}'
                                    })()
                                })()
                            ]
                        delta = Delta()
                        finish_reason = "tool_calls"
                    choices = [Choice()]
                async def gen2():
                    yield Chunk2()
                return gen2()

            else:
                # Turn 3: Final response
                class Chunk3:
                    class Choice:
                        class Delta:
                            content = "I have located Bengaluru and navigated the map to latitude 12.9716, longitude 77.5946 at zoom level 12."
                            reasoning_content = "Final confirmation."
                            tool_calls = None
                        delta = Delta()
                        finish_reason = "stop"
                    choices = [Choice()]
                async def gen3():
                    yield Chunk3()
                return gen3()

        orig_acompletion = litellm.acompletion
        litellm.acompletion = mock_acompletion
        try:
            resp = agent.chat("Locate Bengaluru on the map.")
            self.assertTrue(resp.success, f"Expected success=True, got {resp.error_message}")
            self.assertIn("12.9716", resp.answer_text)
            self.assertEqual(resp.executed_tools, ["locate_geographical_feature", "fly_to"])
            # Verify the map actually moved!
            self.assertAlmostEqual(mock_map.center[1], 12.9716, places=3)
            self.assertAlmostEqual(mock_map.center[0], 77.5946, places=3)
            self.assertEqual(mock_map.zoom, 12)
        finally:
            litellm.acompletion = orig_acompletion

    def test_simulated_groq_429_rate_limit(self):
        """Simulate Groq 429 during a tool turn and verify tools are not re-executed twice."""
        mock_map = MockAnyMap()
        agent = for_anymap(
            mock_map,
            config=GeoAgentConfig(provider="litellm", model="groq/openai/gpt-oss-120b"),
            fast=True,
        )

        turn = 0
        rate_limit_triggered = False

        async def mock_acompletion_with_429(*args, **kwargs):
            nonlocal turn, rate_limit_triggered
            turn += 1
            if turn == 1:
                # Model calls fly_to
                class Chunk1:
                    class Choice:
                        class Delta:
                            content = None
                            reasoning_content = "Navigating to Bengaluru"
                            tool_calls = [
                                type("TC", (), {
                                    "index": 0,
                                    "id": "call_flyto_429",
                                    "function": type("F", (), {
                                        "name": "fly_to",
                                        "arguments": '{"lat": 12.9716, "lon": 77.5946, "zoom": 12}'
                                    })()
                                })()
                            ]
                        delta = Delta()
                        finish_reason = "tool_calls"
                    choices = [Choice()]
                async def gen1():
                    yield Chunk1()
                return gen1()

            elif turn == 2:
                # Turn 2: Rate limit 429 when model tries to formulate response after tool executed!
                rate_limit_triggered = True
                req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
                resp = httpx.Response(429, headers={'retry-after': '0.5'}, json={'error': {'message': 'rate_limit_exceeded'}}, request=req)
                raise litellm.exceptions.RateLimitError(message='Rate limit reached. Please try again in 0.5s.', response=resp, model='groq/openai/gpt-oss-120b', llm_provider='groq')

            elif turn == 3:
                # Turn 3: Successful retry of model call
                class Chunk3:
                    class Choice:
                        class Delta:
                            content = "Successfully centered on Bengaluru after retry."
                            reasoning_content = None
                            tool_calls = None
                        delta = Delta()
                        finish_reason = "stop"
                    choices = [Choice()]
                async def gen3():
                    yield Chunk3()
                return gen3()

        orig_acompletion = litellm.acompletion
        litellm.acompletion = mock_acompletion_with_429
        try:
            resp = agent.chat("Fly to Bengaluru.")
            self.assertTrue(resp.success)
            self.assertTrue(rate_limit_triggered)
            self.assertIn("Successfully centered on Bengaluru", resp.answer_text)
            # Tool was only executed once!
            self.assertEqual(resp.executed_tools, ["fly_to"])
            self.assertAlmostEqual(mock_map.center[1], 12.9716, places=3)
            self.assertAlmostEqual(mock_map.center[0], 77.5946, places=3)
        finally:
            litellm.acompletion = orig_acompletion


if __name__ == "__main__":
    unittest.main()
