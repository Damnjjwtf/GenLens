from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_career_intel as career
import genlens_role_radar as role_radar


class CareerIntelTests(unittest.TestCase):
    def primary_source(self) -> dict[str, object]:
        return {
            "name": "Public ATS Creative AI Roles",
            "type": "rss",
            "evidence_tier": "primary",
            "trust": "high",
            "verticals": ["AI Filmmaking"],
        }

    def strong_item(self, url: str, **overrides: str) -> dict[str, str]:
        item = {
            "title": "Creative Technologist, Generative AI",
            "summary": "Hiring a creative technologist to build generative AI production workflows with ComfyUI and APIs.",
            "url": url,
            "raw_url": url,
            "publisher": "Acme",
            "publisher_url": "https://acme.example/",
            "date": dt.date.today().isoformat(),
        }
        item.update(overrides)
        return item

    def test_google_news_wrapper_is_not_replaced_by_publisher_homepage(self) -> None:
        wrapper = "https://news.google.com/rss/articles/abc123?oc=5"
        self.assertEqual(
            career.resolved_google_news_url(wrapper, "https://boards.greenhouse.io/acme"),
            wrapper,
        )

    def test_direct_ats_posting_can_be_observed_primary_evidence(self) -> None:
        candidate = career.candidate_from_item(
            self.strong_item("https://boards.greenhouse.io/acme/jobs/123456"),
            self.primary_source(),
        )
        self.assertTrue(candidate["accepted"])
        self.assertEqual(candidate["verification_status"], "verified-direct-posting")
        self.assertEqual(candidate["evidence_tier"], "primary")
        self.assertEqual(candidate["status"], "observed")

    def test_ats_subdomain_posting_is_direct_evidence(self) -> None:
        candidate = career.candidate_from_item(
            self.strong_item("https://apply.workable.com/acme/j/ABC123/"),
            self.primary_source(),
        )
        self.assertEqual(candidate["verification_status"], "verified-direct-posting")
        self.assertEqual(candidate["status"], "observed")

    def test_primary_rss_scan_attempts_to_resolve_google_wrapper(self) -> None:
        wrapper = "https://news.google.com/rss/articles/abc123?oc=5"
        direct = "https://apply.workable.com/acme/j/ABC123/"
        xml = f"""<?xml version="1.0"?>
        <rss><channel><item>
          <title>Creative Technologist, Generative AI</title>
          <link>{wrapper.replace('&', '&amp;')}</link>
          <source url="https://apply.workable.com">Workable</source>
          <pubDate>Fri, 24 Jul 2026 12:00:00 GMT</pubDate>
          <description>Hiring a creative technologist for generative AI workflows.</description>
        </item></channel></rss>""".encode()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return xml

        with (
            mock.patch.object(career.urllib.request, "urlopen", return_value=Response()),
            mock.patch.object(career.brief_web, "resolve_google_news_url", return_value=direct) as resolver,
        ):
            items = career.fetch_rss("https://example.com/feed", 1, resolve_primary_wrappers=True)
        self.assertEqual(items[0]["url"], direct.rstrip("/"))
        resolver.assert_called_once_with(wrapper, "https://apply.workable.com")

    def test_primary_search_lead_is_downgraded_until_direct_posting_resolves(self) -> None:
        wrapper = "https://news.google.com/rss/articles/abc123?oc=5"
        candidate = career.candidate_from_item(
            self.strong_item(
                wrapper,
                raw_url=wrapper,
                publisher_url="https://boards.greenhouse.io/acme",
            ),
            self.primary_source(),
        )
        self.assertEqual(candidate["verification_status"], "lead-needs-direct-url")
        self.assertEqual(candidate["configured_evidence_tier"], "primary")
        self.assertEqual(candidate["evidence_tier"], "secondary")
        self.assertNotEqual(candidate["status"], "observed")

    def test_demand_source_never_becomes_observed_role(self) -> None:
        source = {
            "name": "Freelance Demand",
            "type": "rss",
            "evidence_tier": "demand",
            "trust": "medium",
            "verticals": ["Cross-Vertical Watchlist"],
        }
        candidate = career.candidate_from_item(
            self.strong_item("https://example.com/freelance/creative-ai"),
            source,
        )
        self.assertEqual(candidate["status"], "market-demand")

    def test_stale_post_is_rejected_even_when_other_signals_are_strong(self) -> None:
        stale = (dt.date.today() - dt.timedelta(days=career.MAX_SIGNAL_AGE_DAYS + 1)).isoformat()
        candidate = career.candidate_from_item(
            self.strong_item("https://boards.greenhouse.io/acme/jobs/123456", date=stale),
            self.primary_source(),
        )
        self.assertFalse(candidate["accepted"])
        self.assertEqual(candidate["date_status"], "stale")
        self.assertIn("stale posting date", candidate["reasons"])

    def test_tracking_parameters_do_not_create_duplicate_ids(self) -> None:
        clean = "https://jobs.example.com/jobs/123"
        tracked = clean + "?utm_source=newsletter&gclid=abc"
        self.assertEqual(
            career.fingerprint("Creative Technologist", clean),
            career.fingerprint("Creative Technologist", tracked),
        )

    def test_company_page_links_do_not_invent_a_posting_date(self) -> None:
        links = career.html_links(
            '<a href="/careers/job/123">Creative Technologist</a>',
            "https://example.com/",
        )
        self.assertEqual(links[0]["date"], "")

    def test_corrupt_existing_ledger_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "career_signals.json"
            path.write_text("{bad json")
            with self.assertRaisesRegex(ValueError, "Cannot read existing career signal ledger"):
                career.load_existing(path)

    def test_fresh_signal_replaces_legacy_scoring_and_preserves_first_seen(self) -> None:
        url = "https://boards.greenhouse.io/acme/jobs/123456"
        old = {
            "id": "legacy-id",
            "title": "Creative Technologist, Generative AI",
            "url": url + "?utm_source=old",
            "score": 95,
            "accepted": True,
            "first_seen_at": "2026-07-01T00:00:00Z",
            "last_seen_at": "2026-07-01T00:00:00Z",
        }
        fresh = career.candidate_from_item(self.strong_item(url), self.primary_source())
        fresh["score"] = 70
        merged = career.merge_signals([old], [fresh])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["score"], 70)
        self.assertEqual(merged[0]["first_seen_at"], "2026-07-01T00:00:00Z")

    def test_role_radar_excludes_stale_and_inactive_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "career_signals.json"
            path.write_text(json.dumps({
                "signals": [
                    {"title": "Current", "accepted": True, "date_status": "current"},
                    {"title": "Stale", "accepted": True, "date_status": "stale"},
                    {"title": "Inactive", "accepted": True, "active": False},
                ]
            }))
            rows = role_radar.career_signal_rows(path)
        self.assertEqual([row["title"] for row in rows], ["Current"])

    def test_role_radar_rejects_invalid_ledger_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "career_signals.json"
            path.write_text(json.dumps({"signals": ["not-an-object"]}))
            with self.assertRaisesRegex(ValueError, "invalid contract"):
                role_radar.career_signal_rows(path)

    def test_primary_feed_with_only_unresolved_leads_is_not_marked_keep(self) -> None:
        stat = career.empty_source_stat(self.primary_source())
        stat.update({"checked": 4, "accepted": 4, "verified": 0, "verification_leads": 4, "avg_score": 50})
        self.assertEqual(career.summarize_source_stat(stat)["action"], "resolve-direct-urls")

    def test_blocked_company_page_routes_to_public_ats_fallback(self) -> None:
        stat = career.empty_source_stat({
            "name": "Example Career Page",
            "type": "company_watchlist",
            "evidence_tier": "primary",
            "trust": "high",
        })
        stat["error"] = "fetch failed - Forbidden"
        self.assertEqual(career.summarize_source_stat(stat)["action"], "use-public-ats-fallback")

    def test_seeded_roles_inherit_registry_evidence_boundary(self) -> None:
        rows = role_radar.role_rows({
            "source": "User-provided transcript",
            "evidence_tier": "primary-pasted",
            "verification_status": "verified-pasted-source",
            "roles": [{"title": "Creative Technologist", "status": "observed"}],
        })
        self.assertEqual(rows[0]["evidence_source"], "User-provided transcript")
        self.assertEqual(rows[0]["evidence_tier"], "primary-pasted")
        self.assertEqual(rows[0]["verification_status"], "verified-pasted-source")


if __name__ == "__main__":
    unittest.main()
