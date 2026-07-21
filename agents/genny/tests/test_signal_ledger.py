from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_signal_ledger as ledger
import genlens_compose_brief as composer
import genlens_editorial_ops as editorial_ops


class SignalLedgerTests(unittest.TestCase):
    def candidate(self, **overrides):
        row = {
            "lens": "genny",
            "vertical": "AI Filmmaking",
            "source_name": "Runway Changelog",
            "source_url": "https://example.com/releases/",
            "source_type": "release_notes",
            "source_priority": "high",
            "title": "Runway adds controllable frame editing",
            "summary": "Editors can revise generated plates before conform.",
            "url": "https://example.com/releases/frame-editing?utm_source=rss",
            "published_at": "2026-07-20",
            "status": "published",
            "score": 8,
            "reason": "publishable",
        }
        row.update(overrides)
        return ledger.make_candidate_review(**row)

    def test_stable_id_ignores_tracking_and_fragment(self) -> None:
        first = "https://Example.com/posts/release/?utm_source=rss&b=2&a=1#details"
        second = "http://example.com/posts/release?a=1&b=2"

        self.assertEqual(
            ledger.canonicalize_url(first),
            "https://example.com/posts/release?a=1&b=2",
        )
        self.assertEqual(
            ledger.stable_signal_id(first, "ignored"),
            ledger.stable_signal_id(second, "different title"),
        )

    def test_json_schema_version_matches_runtime(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "data" / "genlens_signal_record.schema.json"
        schema = json.loads(schema_path.read_text())

        self.assertEqual(schema["properties"]["schema_version"]["const"], ledger.SCHEMA_VERSION)
        self.assertIn("recommended_action", schema["$defs"]["signal"]["required"])
        self.assertIn("rejection_reason", schema["$defs"]["signal"]["required"])

    def test_published_record_has_decision_and_evidence_contract(self) -> None:
        review = self.candidate()
        records = ledger.build_run_records(
            [review],
            run_lens="genny",
            mode="expanded",
            observed_at="2026-07-20T12:00:00+00:00",
        )

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertRegex(record["id"], r"^sig_[a-f0-9]{20}$")
        self.assertEqual(record["status"], "published")
        self.assertEqual(record["recommended_action"], "watch")
        self.assertEqual(record["confidence"], "primary-source")
        self.assertEqual(record["change"], review["title"])
        self.assertIsNone(record["mechanism"])
        self.assertIsNone(record["use_case"])
        self.assertIsNone(record["impact"])
        self.assertEqual(record["evidence"][0]["url"], review["canonical_url"])

    def test_direct_vendor_url_is_primary_even_when_discovered_by_search(self) -> None:
        review = self.candidate(
            source_name="Shopify",
            source_url="https://changelog.shopify.com/",
            source_type="news_search",
            url="https://changelog.shopify.com/posts/managed-markets",
        )

        self.assertTrue(review["authoritative"])
        self.assertEqual(review["confidence"], "primary-source")

    def test_rejection_reason_is_machine_readable(self) -> None:
        review = self.candidate(
            status="rejected",
            score=0,
            reason="generic/how-to/category title",
        )

        self.assertEqual(review["reason_code"], "generic-how-to-category-title")
        records = ledger.build_run_records(
            [review],
            run_lens="genny",
            mode="expanded",
            observed_at="2026-07-20T12:00:00+00:00",
        )
        self.assertEqual(records[0]["status"], "rejected")
        self.assertIsNone(records[0]["recommended_action"])

    def test_archive_merges_observations_under_one_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "signal_ledger.json"
            first = self.candidate()
            ledger.write_signal_ledger(
                path,
                [first],
                run_lens="genny",
                mode="expanded",
                observed_at="2026-07-20T12:00:00+00:00",
            )
            second = self.candidate(
                url="https://example.com/releases/frame-editing#update",
                status="rejected",
                score=0,
                reason="stale item",
            )
            ledger.write_signal_ledger(
                path,
                [second],
                run_lens="genny",
                mode="expanded",
                observed_at="2026-07-21T12:00:00+00:00",
            )

            data = json.loads(path.read_text())
            self.assertEqual(data["schema_version"], ledger.SCHEMA_VERSION)
            self.assertEqual(len(data["records"]), 1)
            record = data["records"][0]
            self.assertEqual(record["observation_count"], 2)
            self.assertEqual(record["first_observed_at"], "2026-07-20T12:00:00+00:00")
            self.assertEqual(record["last_observed_at"], "2026-07-21T12:00:00+00:00")
            self.assertEqual([row["status"] for row in record["history"]], ["published", "rejected"])
            self.assertEqual(data["latest_run"]["counts"]["rejected"], 1)

    def test_invalid_existing_ledger_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "signal_ledger.json"
            path.write_text("not-json")

            with self.assertRaisesRegex(ValueError, "risking history loss"):
                ledger.write_signal_ledger(
                    path,
                    [self.candidate()],
                    run_lens="genny",
                    mode="expanded",
                    observed_at="2026-07-20T12:00:00+00:00",
                )

            self.assertEqual(path.read_text(), "not-json")

    def test_multiple_layer_reviews_merge_into_one_record(self) -> None:
        url = "https://example.com/releases/shared-update"
        reviews = [
            self.candidate(url=url, vertical="AI Filmmaking", status="published"),
            self.candidate(url=url, vertical="Advertising / Brand Content", status="qualified"),
        ]
        records = ledger.build_run_records(
            reviews,
            run_lens="genny",
            mode="expanded",
            observed_at="2026-07-20T12:00:00+00:00",
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["verticals"],
            ["AI Filmmaking", "Advertising / Brand Content"],
        )
        self.assertEqual(len(records[0]["reviews"]), 2)

    def test_rss_review_captures_qualified_and_rejected_candidates(self) -> None:
        today = composer.dt.datetime.now(composer.dt.timezone.utc).date()
        old = today - composer.dt.timedelta(days=46)
        feed = f"""<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>Runway launches an AI video workflow API</title>
    <link>https://example.com/blog/runway-video-api</link>
    <description>Production teams can integrate generative video into an editing pipeline.</description>
    <pubDate>{today.isoformat()}</pubDate>
  </item>
  <item>
    <title>Runway launches an old AI video workflow</title>
    <link>https://example.com/blog/old-runway-workflow</link>
    <description>Production teams used an older generative video pipeline.</description>
    <pubDate>{old.isoformat()}</pubDate>
  </item>
</channel></rss>""".encode()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, *_args):
                return feed

        source = {
            "name": "Runway Changelog",
            "rss": "https://example.com/feed.xml",
            "source_type": "release_notes",
            "priority": "high",
            "watch_for": ["Runway", "video", "workflow"],
        }
        reviews = []
        with mock.patch.object(composer.urllib.request, "urlopen", return_value=FakeResponse()):
            items = composer.fetch_rss(
                source,
                "AI Filmmaking",
                10,
                reviews=reviews,
                lens="genny",
            )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            {review["status"] for review in reviews},
            {"qualified", "rejected"},
        )
        rejected = next(review for review in reviews if review["status"] == "rejected")
        self.assertEqual(rejected["reason_code"], "stale-item")

    def test_composer_writes_published_signal_to_ledger(self) -> None:
        source = {
            "name": "Runway Changelog",
            "rss": "https://example.com/feed.xml",
            "source_type": "release_notes",
            "priority": "high",
            "watch_for": ["Runway", "video", "workflow"],
        }
        registry = {"verticals": {"AI Filmmaking": [source]}}

        def fake_fetch(_source, vertical, _limit, reviews=None, lens="genny"):
            review_id = composer.append_candidate_review(
                reviews,
                lens=lens,
                vertical=vertical,
                source=source,
                title="Runway launches an AI video workflow API",
                summary="Production teams can integrate generative video into editing.",
                url="https://example.com/blog/runway-video-api",
                date="2026-07-20",
                status="qualified",
                score=8,
                reason="publishable",
            )
            return [{
                "title": "Runway launches an AI video workflow API",
                "summary": "Production teams can integrate generative video into editing.",
                "url": "https://example.com/blog/runway-video-api",
                "date": "2026-07-20",
                "source": "Runway Changelog",
                "priority": "high",
                "score": "8",
                "review": "publishable",
                "_review_id": review_id,
            }]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "signal_ledger.json"
            with mock.patch.object(composer, "load_sources", return_value=registry), mock.patch.object(
                composer,
                "fetch_rss",
                side_effect=fake_fetch,
            ):
                markdown = composer.compose(
                    "active",
                    5,
                    12,
                    lens="genny",
                    ledger_out=path,
                )
                without_ledger = composer.compose("active", 5, 12, lens="genny")

            data = json.loads(path.read_text())
            self.assertIn("Runway launches an AI video workflow API", markdown)
            self.assertEqual(data["latest_run"]["counts"]["published"], 1)
            self.assertEqual(data["records"][0]["status"], "published")
            self.assertEqual(data["records"][0]["reviews"][0]["quality_reason_code"], "publishable")
            self.assertEqual(data["records"][0]["reviews"][0]["reason_code"], "published-in-brief")
            self.assertEqual(markdown, without_ledger)

    def test_preflight_preserves_career_and_signal_ledger_artifacts(self) -> None:
        markdown = editorial_ops.render_preflight(
            analysis={
                "cards": 1,
                "linked_cards": 1,
                "vertical_count": 1,
                "signal_vertical_count": 1,
                "verticals": ["AI Filmmaking"],
                "source_counts": {"Runway": 1},
                "duplicates": {},
            },
            send_ready=True,
            reason="passed editorial gate",
            career_radar_path=Path("/tmp/career_radar.md"),
            signal_ledger_path=Path("/tmp/signal_ledger.json"),
        )

        self.assertIn("Career radar: `/tmp/career_radar.md`", markdown)
        self.assertIn("Signal ledger: `/tmp/signal_ledger.json`", markdown)


if __name__ == "__main__":
    unittest.main()
