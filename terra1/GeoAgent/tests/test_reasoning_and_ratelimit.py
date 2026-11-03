import unittest
import asyncio
from geoagent.core.model import GeoAgentLiteLLMModel
from geoagent.core.config import GeoAgentConfig
from geoagent.core.retry import GeoAgentRetryStrategy, parse_retry_delay
import litellm
import httpx


class TestReasoningAndRateLimit(unittest.TestCase):
    def test_reasoning_content_filtering(self):
        """Verify that reasoningContent blocks are filtered out before Chat Completions formatting."""
        model = GeoAgentLiteLLMModel(model_id="groq/openai/gpt-oss-120b")
        messages = [
            {"role": "user", "content": [{"text": "Where is Mount Everest?"}]},
            {
                "role": "assistant",
                "content": [
                    {"reasoningContent": {"reasoningText": {"text": "Thinking deeply...", "signature": "sig1"}}},
                    {"text": "Mount Everest is on the border of Nepal and China."},
                    {"toolUse": {"toolUseId": "call_1", "name": "locate_geographical_feature", "input": {"name": "Mount Everest"}}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"toolResult": {"toolUseId": "call_1", "content": [{"text": "Found at lat 27.9881, lon 86.925"}]}}
                ]
            }
        ]

        formatted = model.format_request_messages(messages)
        self.assertEqual(len(formatted), 3)
        self.assertEqual(formatted[0]["role"], "user")
        self.assertEqual(formatted[1]["role"], "assistant")
        self.assertEqual(formatted[2]["role"], "tool")

        # Verify assistant message has text and tool_calls preserved, but no reasoningContent
        assistant_content = formatted[1].get("content")
        self.assertEqual(assistant_content, [{'text': 'Mount Everest is on the border of Nepal and China.', 'type': 'text'}])
        self.assertEqual(formatted[1]["tool_calls"][0]["function"]["name"], "locate_geographical_feature")
        self.assertEqual(formatted[2]["content"], "Found at lat 27.9881, lon 86.925")

    def test_parse_retry_delay(self):
        req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
        resp = httpx.Response(429, headers={'retry-after': '3.5'}, json={'error': {'message': 'rate_limit_exceeded'}}, request=req)
        err = litellm.exceptions.RateLimitError(message='Rate limit', response=resp, model='groq/openai/gpt-oss-120b', llm_provider='groq')
        self.assertEqual(parse_retry_delay(err), 3.5)

        err_msg = Exception("Rate limit exceeded. Please try again in 4.2s.")
        self.assertEqual(parse_retry_delay(err_msg), 4.2)

        err_default = Exception("Rate limit reached")
        self.assertEqual(parse_retry_delay(err_default, default=5.0), 5.0)

    def test_retry_strategy_is_retryable(self):
        strat = GeoAgentRetryStrategy(max_attempts=3)
        req = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
        resp = httpx.Response(429, headers={'retry-after': '1'}, json={'error': {'message': 'rate_limit_exceeded'}}, request=req)
        err = litellm.exceptions.RateLimitError(message='Rate limit', response=resp, model='groq/openai/gpt-oss-120b', llm_provider='groq')
        self.assertTrue(strat.is_retryable(err))

        err_429 = Exception("GroqException: 429 Too Many Requests")
        self.assertTrue(strat.is_retryable(err_429))

        err_normal = ValueError("Invalid input")
        self.assertFalse(strat.is_retryable(err_normal))


if __name__ == "__main__":
    unittest.main()
