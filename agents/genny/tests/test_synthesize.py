from __future__ import annotations

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_synthesize as synth

SECRET = "sk-ant-synthesis-secret-key"

CARDS = [
    {
        "vertical": "AI Filmmaking",
        "date": "2026-07-23",
        "source": "Runway Changelog",
        "title": "Runway ships controllable frame editing",
        "summary": "Editors revise generated plates before conform.",
    },
    {
        "vertical": "Digital Humans",
        "date": "2026-07-22",
        "source": "ElevenLabs Blog",
        "title": "ElevenLabs adds multilingual dubbing",
        "summary": "Voice cloning now covers 30 languages.",
    },
]


def base_env(**overrides):
    env = {"ANTHROPIC_API_KEY": SECRET}
    env.update(overrides)
    return env


def api_response(text="Lead. Top signals: Runway shipped editing [C1]."):
    payload = {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}
    return io.BytesIO(json.dumps(payload).encode("utf-8"))


class FakeHTTP:
    def __init__(self, body):
        self._body = body

    def read(self, _limit=-1):
        return self._body.read()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class GatingTests(unittest.TestCase):
    def test_no_key_returns_none_without_network(self) -> None:
        with mock.patch.object(synth.urllib.request, "urlopen") as opener:
            result = synth.synthesize_brief(CARDS, env={})
        self.assertIsNone(result)
        opener.assert_not_called()

    def test_disabled_flag_returns_none_without_network(self) -> None:
        with mock.patch.object(synth.urllib.request, "urlopen") as opener:
            result = synth.synthesize_brief(CARDS, env=base_env(GENLENS_SYNTHESIS="0"))
        self.assertIsNone(result)
        opener.assert_not_called()

    def test_empty_cards_returns_none(self) -> None:
        with mock.patch.object(synth.urllib.request, "urlopen") as opener:
            result = synth.synthesize_brief([], env=base_env())
        self.assertIsNone(result)
        opener.assert_not_called()

    def test_fallback_key_var_is_honored(self) -> None:
        env = {"GENLENS_MODEL_API_KEY": SECRET}
        with mock.patch.object(
            synth.urllib.request, "urlopen", return_value=FakeHTTP(api_response())
        ):
            result = synth.synthesize_brief(CARDS, env=env)
        self.assertIsNotNone(result)


class RequestShapeTests(unittest.TestCase):
    def _capture_request(self, env=None):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeHTTP(api_response())

        with mock.patch.object(synth.urllib.request, "urlopen", side_effect=fake_urlopen):
            synth.synthesize_brief(CARDS, env=env or base_env())
        return captured["request"]

    def test_request_carries_key_header_and_card_facts(self) -> None:
        request = self._capture_request()
        self.assertEqual(request.headers.get("X-api-key"), SECRET)
        self.assertEqual(request.headers.get("Anthropic-version"), synth.ANTHROPIC_VERSION)
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], synth.DEFAULT_MODEL)
        self.assertIn("only these facts", body["messages"][0]["content"])
        self.assertIn("Runway ships controllable frame editing", body["messages"][0]["content"])
        self.assertIn("Never add a number", body["system"])

    def test_model_override_is_honored(self) -> None:
        request = self._capture_request(env=base_env(GENLENS_SYNTH_MODEL="claude-sonnet-5"))
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], "claude-sonnet-5")


class ResponseHandlingTests(unittest.TestCase):
    def test_success_returns_text(self) -> None:
        with mock.patch.object(
            synth.urllib.request, "urlopen", return_value=FakeHTTP(api_response())
        ):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIn("Runway", result)

    def test_em_dashes_are_stripped(self) -> None:
        body = api_response("Runway shipped editing — a real change [C1].")
        with mock.patch.object(synth.urllib.request, "urlopen", return_value=FakeHTTP(body)):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertNotIn("—", result)
        self.assertIn("editing, a real change", result)

    def test_refusal_returns_none(self) -> None:
        payload = {"stop_reason": "refusal", "content": []}
        body = io.BytesIO(json.dumps(payload).encode("utf-8"))
        with mock.patch.object(synth.urllib.request, "urlopen", return_value=FakeHTTP(body)):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIsNone(result)

    def test_empty_text_returns_none(self) -> None:
        body = io.BytesIO(json.dumps({"content": [{"type": "text", "text": "  "}]}).encode())
        with mock.patch.object(synth.urllib.request, "urlopen", return_value=FakeHTTP(body)):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIsNone(result)

    def test_http_error_returns_none(self) -> None:
        error = urllib.error.HTTPError(synth.API_URL, 500, "server error", None, None)
        with mock.patch.object(synth.urllib.request, "urlopen", side_effect=error):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIsNone(result)

    def test_timeout_returns_none(self) -> None:
        with mock.patch.object(synth.urllib.request, "urlopen", side_effect=TimeoutError()):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIsNone(result)

    def test_malformed_json_returns_none(self) -> None:
        with mock.patch.object(
            synth.urllib.request, "urlopen", return_value=FakeHTTP(io.BytesIO(b"not json"))
        ):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertIsNone(result)

    def test_secret_never_appears_in_output(self) -> None:
        with mock.patch.object(
            synth.urllib.request, "urlopen", return_value=FakeHTTP(api_response())
        ):
            result = synth.synthesize_brief(CARDS, env=base_env())
        self.assertNotIn(SECRET, result)


class ComposeIntegrationTests(unittest.TestCase):
    def test_synthesized_section_splices_above_briefing_standard(self) -> None:
        import genlens_compose_brief as composer

        with mock.patch.object(
            composer.synthesize, "synthesize_brief", return_value="SYNTHETIC LEAD [C1]"
        ):
            markdown = composer.compose("active", 5, 12, lens="genny")

        self.assertIn("## This Week", markdown)
        self.assertIn("SYNTHETIC LEAD [C1]", markdown)
        self.assertLess(
            markdown.index("## This Week"),
            markdown.index("## Briefing Standard"),
            "synthesized section must sit above the deterministic brief",
        )

    def test_no_synthesis_leaves_brief_unchanged(self) -> None:
        import genlens_compose_brief as composer

        with mock.patch.object(
            composer.synthesize, "synthesize_brief", return_value=None
        ):
            markdown = composer.compose("active", 5, 12, lens="genny")

        self.assertNotIn("## This Week", markdown)
        self.assertIn("## Briefing Standard", markdown)


if __name__ == "__main__":
    unittest.main()
