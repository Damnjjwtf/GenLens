from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_browser_research as browser
import genlens_compose_brief as composer


class BrowserResearchTests(unittest.TestCase):
    def test_task_is_read_only_and_source_scoped(self) -> None:
        task = browser.build_task(
            "https://example.com/blog",
            "AI Filmmaking",
            "genny",
            "dynamic-source",
            2,
        )
        self.assertIn("Read-only research", task)
        self.assertIn("Do not log in", task)
        self.assertIn("Do not use cookies", task)
        self.assertIn("same public source domain", task)

    def test_candidate_rejects_homepage_and_external_domain(self) -> None:
        self.assertFalse(browser.candidate_url_allowed("https://example.com/", "example.com")[0])
        self.assertFalse(browser.candidate_url_allowed("https://other.example/article-with-enough-length", "example.com")[0])
        self.assertTrue(browser.candidate_url_allowed("https://example.com/2026/08/a-specific-release", "example.com")[0])

    def test_normalize_requires_date_and_substantive_evidence(self) -> None:
        payload = {
            "status": "ok",
            "results": [
                {
                    "title": "A specific production workflow release",
                    "url": "https://example.com/blog/specific-production-workflow-release",
                    "published_at": "2026-08-01",
                    "evidence_excerpt": "The release adds a controllable generative video workflow for production teams, with a new reference pipeline and export controls.",
                    "claims_supported": ["reference controls"],
                },
                {
                    "title": "Undated homepage lead",
                    "url": "https://example.com/blog/another-specific-release",
                    "published_at": "",
                    "evidence_excerpt": "This evidence is long enough to show that the model must reject it when the source does not provide a publication date.",
                },
            ],
        }
        normalized = browser.normalize_results(payload, "https://example.com/blog", 3)
        self.assertEqual(normalized["status"], "ok")
        self.assertEqual(len(normalized["results"]), 1)
        self.assertEqual(normalized["results"][0]["date"], "2026-08-01")

    def test_private_hosts_are_blocked(self) -> None:
        allowed, reason = browser.public_url_allowed("http://127.0.0.1:8000/news")
        self.assertFalse(allowed)
        self.assertIn("private", reason)

    def test_collection_only_runs_for_feed_and_exa_gaps(self) -> None:
        rows = [("genny", "AI Filmmaking"), ("genny", "Product Photography")]
        data = {
            "genny": {
                "verticals": {
                    "AI Filmmaking": [{
                        "name": "Dynamic Film Source",
                        "url": "https://example.com/blog",
                        "priority": "high",
                        "watch_for": ["video", "AI", "workflow"],
                    }],
                    "Product Photography": [{
                        "name": "Dynamic Photo Source",
                        "url": "https://example.com/blog/photos",
                        "priority": "high",
                        "watch_for": ["product", "AI", "workflow"],
                    }],
                }
            }
        }
        feed = {
            ("genny", "AI Filmmaking"): ([{"title": "existing"}], [], [], 1),
            ("genny", "Product Photography"): ([], [], [], 1),
        }
        empty_exa = {
            key: ([], [], [], 0)
            for key in rows
        }
        candidate = [{
            "title": "A browser candidate",
            "url": "https://example.com/blog/a-specific-release",
            "date": "2026-08-01",
            "summary": "A dated browser result with substantive evidence.",
            "source": "Browser Use",
            "priority": "high",
            "score": "6",
            "review": "publishable",
            "_review_id": "review-1",
        }]
        with patch.object(composer, "fetch_browser_source", return_value=(candidate, [], "")) as fetch:
            collected = composer.collect_browser_candidates(
                rows, data, feed, empty_exa, "genny", max_tasks=3,
            )
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(collected[("genny", "AI Filmmaking")][0], [])
        self.assertEqual(collected[("genny", "Product Photography")][0], candidate)


if __name__ == "__main__":
    unittest.main()
