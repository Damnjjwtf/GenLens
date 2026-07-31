from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_compose_brief as composer
import genlens_exa_search as exa


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.body


class ExaSearchTests(unittest.TestCase):
    def test_build_query_is_intent_oriented(self) -> None:
        query = exa.build_query("AI Filmmaking", ["video generation", "ComfyUI"])
        self.assertIn("AI Filmmaking", query)
        self.assertIn("concrete change", query)
        self.assertIn("ComfyUI", query)
        self.assertIn("product homepages", query)

    def test_search_sends_date_window_and_extracts_highlights(self) -> None:
        captured: dict[str, object] = {}

        def opener(request, timeout, context):
            captured["headers"] = dict(request.headers)
            captured["timeout"] = timeout
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(json.dumps({
                "results": [
                    {
                        "id": "https://example.com/article",
                        "title": "A concrete AI video workflow ships",
                        "url": "https://example.com/article",
                        "publishedDate": "2026-07-30T12:00:00Z",
                        "highlights": ["The release adds an AI video workflow for production teams."],
                    },
                    {"title": "Undated result", "url": "https://example.com/undated", "highlights": ["skip"]},
                ]
            }).encode("utf-8"))

        rows = exa.search(
            "recent AI video production release",
            api_key="test-exa-key",
            max_age_days=45,
            opener=opener,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["date"], "2026-07-30")
        self.assertEqual(rows[0]["summary"], "The release adds an AI video workflow for production teams.")
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(captured["headers"]["X-api-key"], "test-exa-key")
        self.assertIn("startPublishedDate", captured["payload"])
        self.assertEqual(captured["payload"]["contents"]["highlights"]["maxCharacters"], 900)

    def test_exa_quality_gate_rejects_homepages_and_reddit(self) -> None:
        source = {
            "name": "Exa semantic discovery",
            "source_type": "exa_search",
            "priority": "medium",
            "watch_for": ["video", "AI", "workflow"],
        }
        title = "A video model launches a controllable AI filmmaking workflow"
        summary = "The release adds reference controls and a repeatable generative video pipeline for commercial production teams."
        accepted, _score, reason = composer.quality_review(
            "AI Filmmaking", source, title, summary,
            "https://example.com/blog/video-model-launches", "2026-07-30",
        )
        self.assertTrue(accepted, reason)
        rejected = composer.quality_review(
            "AI Filmmaking", source, title, summary,
            "https://example.com/", "2026-07-30",
        )
        self.assertFalse(rejected[0])
        self.assertEqual(rejected[2], "rejected-url")
        reddit = composer.quality_review(
            "AI Filmmaking", source, title, summary,
            "https://www.reddit.com/r/Filmmakers/comments/abcdefgh/workflow/", "2026-07-30",
        )
        self.assertFalse(reddit[0])
        self.assertEqual(reddit[2], "community discovery requires corroboration")

    def test_exa_collection_is_disabled_without_key(self) -> None:
        rows = [("genny", "AI Filmmaking")]
        with patch.dict("os.environ", {}, clear=True):
            collected = composer.collect_exa_candidates(
                rows,
                {"genny": {"verticals": {"AI Filmmaking": []}}},
                {("genny", "AI Filmmaking"): ([], [], [], 0)},
                "genny",
                max_queries=1,
            )
        self.assertEqual(collected[("genny", "AI Filmmaking")][0], [])


if __name__ == "__main__":
    unittest.main()
