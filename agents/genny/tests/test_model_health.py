from __future__ import annotations

import io
import json
import socket
import sys
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_model_health as health

SECRET = "sk-ant-test-secret-value-1234"


def env(**overrides: str) -> dict[str, str]:
    base = {
        "GENLENS_MODEL_PROVIDER": "ollama",
        "GENLENS_MODEL_BASE_URL": "http://127.0.0.1:11434/v1",
        "GENLENS_MODEL_NAME": "qwen3:4b",
        "GENLENS_MODEL_TIMEOUT_SECONDS": "5",
        "GENLENS_MODEL_FALLBACK_PROVIDER": "none",
    }
    base.update(overrides)
    return base


class FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self, _limit: int = -1) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ConfigTests(unittest.TestCase):
    def test_defaults_apply_when_env_is_empty(self) -> None:
        config = health.load_config({})
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.base_url, "http://127.0.0.1:11434/v1")
        self.assertEqual(config.timeout_seconds, 15.0)
        self.assertEqual(config.fallback_provider, "none")

    def test_missing_model_name_is_a_config_error(self) -> None:
        config = health.load_config(env(GENLENS_MODEL_NAME=""))
        self.assertTrue(any("GENLENS_MODEL_NAME" in e for e in config.errors))
        doc = health.build_health_document(config, [], None)
        self.assertFalse(doc["healthy"])

    def test_invalid_timeout_and_url_are_config_errors(self) -> None:
        config = health.load_config(
            env(
                GENLENS_MODEL_TIMEOUT_SECONDS="soon",
                GENLENS_MODEL_BASE_URL="not-a-url",
            )
        )
        self.assertTrue(any("GENLENS_MODEL_TIMEOUT_SECONDS" in e for e in config.errors))
        self.assertTrue(any("GENLENS_MODEL_BASE_URL" in e for e in config.errors))


class EndpointValidationTests(unittest.TestCase):
    def test_local_provider_on_loopback_is_clean(self) -> None:
        config = health.load_config(env())
        self.assertEqual(health.validate_endpoint(config), [])

    def test_local_provider_on_public_host_is_flagged(self) -> None:
        config = health.load_config(
            env(GENLENS_MODEL_BASE_URL="http://209.74.85.95:11434/v1")
        )
        issues = health.validate_endpoint(config)
        self.assertEqual(len(issues), 1)
        self.assertIn("loopback", issues[0])
        doc = health.build_health_document(config, issues, None)
        self.assertFalse(doc["healthy"])

    def test_hosted_provider_requires_https(self) -> None:
        config = health.load_config(
            env(
                GENLENS_MODEL_PROVIDER="anthropic",
                GENLENS_MODEL_BASE_URL="http://api.anthropic.com/v1",
            )
        )
        issues = health.validate_endpoint(config)
        self.assertTrue(any("https" in issue for issue in issues))

    def test_hosted_provider_on_https_is_clean(self) -> None:
        config = health.load_config(
            env(
                GENLENS_MODEL_PROVIDER="anthropic",
                GENLENS_MODEL_BASE_URL="https://api.anthropic.com/v1",
                GENLENS_MODEL_NAME="claude-haiku-4-5",
            )
        )
        self.assertEqual(health.validate_endpoint(config), [])


class ProbeTests(unittest.TestCase):
    def test_successful_openai_compatible_model_list(self) -> None:
        config = health.load_config(env())
        payload = {"data": [{"id": "qwen3:4b"}, {"id": "llama3.2:1b"}]}
        with mock.patch.object(
            health.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            probe = health.probe_models(config)
        self.assertTrue(probe["ok"])
        self.assertEqual(probe["status_code"], 200)
        self.assertEqual(probe["model_count"], 2)
        self.assertTrue(probe["configured_model_present"])
        doc = health.build_health_document(config, [], probe)
        self.assertTrue(doc["healthy"])

    def test_configured_model_missing_from_list_is_unhealthy(self) -> None:
        config = health.load_config(env(GENLENS_MODEL_NAME="qwen3:8b"))
        payload = {"models": [{"name": "llama3.2:1b"}]}
        with mock.patch.object(
            health.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            probe = health.probe_models(config)
        self.assertTrue(probe["ok"])
        self.assertFalse(probe["configured_model_present"])
        doc = health.build_health_document(config, [], probe)
        self.assertFalse(doc["healthy"])

    def test_timeout_produces_actionable_error(self) -> None:
        config = health.load_config(env())
        with mock.patch.object(
            health.urllib.request, "urlopen", side_effect=socket.timeout()
        ):
            probe = health.probe_models(config)
        self.assertFalse(probe["ok"])
        self.assertIn("timed out after 5s", probe["error"])
        self.assertIn("is the runtime process up?", probe["error"])
        doc = health.build_health_document(config, [], probe)
        self.assertFalse(doc["healthy"])

    def test_http_401_hints_at_credentials_without_body(self) -> None:
        config = health.load_config(
            env(
                GENLENS_MODEL_PROVIDER="anthropic",
                GENLENS_MODEL_BASE_URL="https://api.anthropic.com/v1",
                GENLENS_MODEL_NAME="claude-haiku-4-5",
                GENLENS_MODEL_API_KEY=SECRET,
            )
        )
        error = urllib.error.HTTPError(
            url="https://api.anthropic.com/v1/models",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error": "bad key sk-ant-test"}'),
        )
        with mock.patch.object(health.urllib.request, "urlopen", side_effect=error):
            probe = health.probe_models(config)
        self.assertFalse(probe["ok"])
        self.assertEqual(probe["status_code"], 401)
        self.assertIn("credential rejected", probe["error"])
        self.assertNotIn("bad key", probe["error"])  # response body never surfaces

    def test_connection_error_is_redacted(self) -> None:
        config = health.load_config(env(GENLENS_MODEL_API_KEY=SECRET))
        error = urllib.error.URLError(f"refused for token {SECRET}")
        with mock.patch.object(health.urllib.request, "urlopen", side_effect=error):
            probe = health.probe_models(config)
        self.assertFalse(probe["ok"])
        self.assertNotIn(SECRET, probe["error"])
        self.assertIn(health.REDACTED, probe["error"])


class RedactionAndOutputTests(unittest.TestCase):
    def test_api_key_never_appears_in_json_output(self) -> None:
        payload = {"data": [{"id": "claude-haiku-4-5"}]}
        argv = ["--check", "--json"]
        test_env = env(
            GENLENS_MODEL_PROVIDER="anthropic",
            GENLENS_MODEL_BASE_URL="https://api.anthropic.com/v1",
            GENLENS_MODEL_NAME="claude-haiku-4-5",
            GENLENS_MODEL_API_KEY=SECRET,
        )
        buffer = io.StringIO()
        with mock.patch.object(
            health.urllib.request, "urlopen", return_value=FakeResponse(payload)
        ):
            with redirect_stdout(buffer):
                code = health.run(argv, test_env)
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertNotIn(SECRET, output)
        doc = json.loads(output)
        self.assertTrue(doc["healthy"])
        self.assertTrue(doc["api_key_configured"])
        self.assertEqual(doc["base_url_host"], "api.anthropic.com")

    def test_probe_sends_anthropic_headers_but_output_omits_them(self) -> None:
        config = health.load_config(
            env(
                GENLENS_MODEL_PROVIDER="anthropic",
                GENLENS_MODEL_API_KEY=SECRET,
            )
        )
        headers = health.probe_headers(config)
        self.assertEqual(headers["x-api-key"], SECRET)
        self.assertIn("anthropic-version", headers)
        doc = health.build_health_document(config, [], None)
        self.assertNotIn(SECRET, json.dumps(doc))

    def test_no_check_skips_probe_and_reports_config_only(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = health.run([], env())
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("probe: skipped", output)

    def test_exit_code_is_nonzero_when_unhealthy(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = health.run(["--json"], env(GENLENS_MODEL_NAME=""))
        self.assertEqual(code, 1)
        doc = json.loads(buffer.getvalue())
        self.assertFalse(doc["healthy"])


if __name__ == "__main__":
    unittest.main()
