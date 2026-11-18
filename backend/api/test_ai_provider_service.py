import json
import urllib.error
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from .ai_provider_service import check_ai_provider_status, query_ai


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.data


class AIProviderServiceTests(TestCase):
    @override_settings(
        AI_PROVIDER="openai",
        AI_FALLBACK_PROVIDER="",
        OPENAI_API_KEY="test-openai-key",
        OPENAI_MODEL="test-model",
        OPENAI_BASE_URL="https://api.example.test/v1",
        AI_MODEL_PRICING_USD_PER_1M={"test-model": {"input": "0.15", "output": "0.6"}},
    )
    @patch("api.ai_provider_service.urllib.request.urlopen")
    def test_openai_compatible_request_uses_server_config_and_parses_content(self, urlopen):
        urlopen.return_value = FakeResponse({
            "choices": [{"message": {"content": "grounded answer"}}],
            "usage": {"prompt_tokens": 40, "completion_tokens": 12},
        })

        prompt = "SENSITIVE PROMPT CONTENT"
        text, success, error = query_ai(prompt, format_json=True)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(text, "grounded answer")
        from .models import AIUsageEvent

        event = AIUsageEvent.objects.get()
        self.assertEqual(event.provider, "openai")
        self.assertEqual(event.model, "test-model")
        self.assertEqual(event.prompt_tokens, 40)
        self.assertEqual(event.completion_tokens, 12)
        self.assertTrue(event.success)
        self.assertGreaterEqual(event.latency_ms, 0)
        self.assertEqual(event.estimated_cost_usd, Decimal("0.0000132000"))
        self.assertNotIn(prompt, str(event))
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.example.test/v1/chat/completions")
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["response_format"], {"type": "json_object"})

    @override_settings(
        AI_PROVIDER="openai_compatible",
        AI_FALLBACK_PROVIDER="",
        OPENAI_API_KEY="",
        OPENAI_MODEL="local-model",
        OPENAI_BASE_URL="http://localhost:9000/v1",
    )
    @patch("api.ai_provider_service.urllib.request.urlopen")
    def test_custom_compatible_endpoint_can_be_configured_without_api_key(self, urlopen):
        urlopen.return_value = FakeResponse({
            "choices": [{"message": {"content": "local answer"}}]
        })

        text, success, error = query_ai("Explain this source.")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(text, "local answer")
        self.assertIsNone(urlopen.call_args.args[0].get_header("Authorization"))

    @override_settings(
        AI_PROVIDER="gemini",
        AI_FALLBACK_PROVIDER="",
        GEMINI_API_KEY="test-gemini-key",
        GEMINI_MODEL="gemini-test",
        GEMINI_BASE_URL="https://gemini.example.test/v1beta",
    )
    @patch("api.ai_provider_service.urllib.request.urlopen")
    def test_gemini_request_decodes_candidate_text(self, urlopen):
        urlopen.return_value = FakeResponse({
            "candidates": [{"content": {"parts": [{"text": "Gemini answer"}]}}],
            "usageMetadata": {"promptTokenCount": 17, "candidatesTokenCount": 6},
        })

        text, success, error = query_ai("Explain this source.")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(text, "Gemini answer")
        from .models import AIUsageEvent

        event = AIUsageEvent.objects.get()
        self.assertEqual(event.prompt_tokens, 17)
        self.assertEqual(event.completion_tokens, 6)
        request = urlopen.call_args.args[0]
        self.assertIn("models/gemini-test:generateContent", request.full_url)
        self.assertNotIn("test-gemini-key", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-gemini-key")

    @override_settings(
        AI_PROVIDER="anthropic",
        AI_FALLBACK_PROVIDER="",
        ANTHROPIC_API_KEY="test-anthropic-key",
        ANTHROPIC_MODEL="claude-test",
        ANTHROPIC_BASE_URL="https://anthropic.example.test/v1",
    )
    @patch("api.ai_provider_service.urllib.request.urlopen")
    def test_anthropic_request_decodes_text_blocks(self, urlopen):
        urlopen.return_value = FakeResponse({
            "content": [{"type": "text", "text": "Claude answer"}],
            "usage": {"input_tokens": 21, "output_tokens": 8},
        })

        text, success, error = query_ai("Explain this source.")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(text, "Claude answer")
        from .models import AIUsageEvent

        event = AIUsageEvent.objects.get()
        self.assertEqual(event.prompt_tokens, 21)
        self.assertEqual(event.completion_tokens, 8)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://anthropic.example.test/v1/messages")
        self.assertEqual(request.get_header("X-api-key"), "test-anthropic-key")

    @override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="", AI_FALLBACK_PROVIDER="")
    def test_status_does_not_claim_unconfigured_provider_can_generate(self):
        status = check_ai_provider_status()
        self.assertFalse(status["is_configured"])
        self.assertFalse(status["can_generate"])

    @override_settings(AI_PROVIDER="ollama", AI_FALLBACK_PROVIDER="", OLLAMA_MODEL="local-model")
    @patch("api.ollama_service.urllib.request.urlopen")
    def test_ollama_usage_metadata_is_recorded(self, urlopen):
        urlopen.return_value = FakeResponse({
            "response": "Local answer",
            "prompt_eval_count": 24,
            "eval_count": 9,
        })

        text, success, error = query_ai("Local prompt", model="local-model")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(text, "Local answer")
        from .models import AIUsageEvent

        event = AIUsageEvent.objects.get()
        self.assertEqual(event.provider, "ollama")
        self.assertEqual(event.prompt_tokens, 24)
        self.assertEqual(event.completion_tokens, 9)

    @override_settings(
        AI_PROVIDER="openai",
        AI_FALLBACK_PROVIDER="ollama",
        OPENAI_API_KEY="test-openai-key",
    )
    @patch("api.ai_provider_service.query_ollama", return_value=("fallback answer", True, None))
    @patch(
        "api.ai_provider_service.urllib.request.urlopen",
        side_effect=urllib.error.URLError("network unavailable")
    )
    def test_failed_primary_uses_configured_fallback(self, urlopen, query_ollama):
        text, success, error = query_ai("Explain this source.")
        self.assertTrue(success)
        self.assertEqual(text, "fallback answer")
        self.assertIsNone(error)
        query_ollama.assert_called_once()

        from .models import AIUsageEvent

        events = list(AIUsageEvent.objects.order_by("id"))
        self.assertEqual(len(events), 2)
        self.assertFalse(events[0].success)
        self.assertEqual(events[0].failure_code, "provider_request_failed")
        self.assertTrue(events[1].success)
        self.assertTrue(events[1].fallback_used)
