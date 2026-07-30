from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_store as store


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = store.connect(":memory:")

    def tearDown(self) -> None:
        self.conn.close()

    def source(self, **overrides):
        row = {
            "name": "Runway Changelog",
            "url": "https://runwayml.com/changelog",
            "feed_url": "https://runwayml.com/changelog/feed.xml",
            "tier": "first_party",
            "vertical": "AI Filmmaking",
            "priority": "high",
        }
        row.update(overrides)
        return row

    def candidate(self, source_id, **overrides):
        row = {
            "source_id": source_id,
            "fingerprint": "fp-runway-frame-editing",
            "url": "https://runwayml.com/changelog/frame-editing",
            "title": "Runway adds controllable frame editing",
            "summary": "Editors revise generated plates before conform.",
            "vertical": "AI Filmmaking",
            "published_at": "2026-07-23",
        }
        row.update(overrides)
        return row

    def test_schema_is_created_with_version(self) -> None:
        version = self.conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()["value"]
        self.assertEqual(int(version), store.SCHEMA_VERSION)

    def test_upsert_source_is_idempotent_by_url(self) -> None:
        first = store.upsert_source(self.conn, self.source())
        second = store.upsert_source(self.conn, self.source(priority="medium"))
        self.assertEqual(first, second)
        rows = self.conn.execute("SELECT priority FROM sources").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["priority"], "medium")

    def test_unknown_tier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            store.upsert_source(self.conn, self.source(tier="totally_made_up"))

    def test_run_history_updates_health_counters(self) -> None:
        sid = store.upsert_source(self.conn, self.source())
        store.record_source_run(self.conn, sid, ok=True, candidates_found=3)
        store.record_source_run(self.conn, sid, ok=False, failure_reason="timeout")
        health = store.source_health(self.conn, sid)
        self.assertEqual(health["fetch_success_rate"], 0.5)
        self.assertEqual(health["last_failure_reason"], "timeout")

    def test_candidate_dedup_and_negative_memory(self) -> None:
        sid = store.upsert_source(self.conn, self.source())
        first = store.add_candidate(self.conn, self.candidate(sid))
        self.assertIsNotNone(first)
        # same fingerprint again is a no-op
        self.assertIsNone(store.add_candidate(self.conn, self.candidate(sid)))

        # reject it -> fingerprint enters negative memory
        store.record_review(self.conn, first, accepted=False, reason="homepage only")
        self.assertTrue(store.is_rejected(self.conn, "fp-runway-frame-editing"))
        # a fresh candidate with the same fingerprint never comes back
        revived = store.add_candidate(
            self.conn, self.candidate(sid, url="https://runwayml.com/other")
        )
        self.assertIsNone(revived)

    def test_accepted_review_marks_verified_and_credits_source(self) -> None:
        sid = store.upsert_source(self.conn, self.source())
        cid = store.add_candidate(self.conn, self.candidate(sid))
        store.record_review(self.conn, cid, accepted=True, score=8, reason="publishable")
        verified = store.verified_candidates(self.conn, vertical="AI Filmmaking")
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["id"], cid)
        health = store.source_health(self.conn, sid)
        self.assertEqual(health["qualified_candidates"], 1)

    def test_delivery_marks_published_and_removes_from_verified_queue(self) -> None:
        sid = store.upsert_source(self.conn, self.source())
        cid = store.add_candidate(self.conn, self.candidate(sid))
        store.record_review(self.conn, cid, accepted=True)
        store.record_delivery(self.conn, cid, lens="genny", channel="email")
        self.assertEqual(store.verified_candidates(self.conn), [])
        status = self.conn.execute(
            "SELECT status FROM candidates WHERE id = ?", (cid,)
        ).fetchone()["status"]
        self.assertEqual(status, "published")

    def test_import_registry_classifies_tiers(self) -> None:
        registry = {
            "verticals": {
                "AI Filmmaking": [
                    {"name": "Runway", "url": "https://runwayml.com/blog", "rss": "",
                     "priority": "high"},
                    {"name": "ComfyUI Commits", "url": "https://github.com/x/commits",
                     "rss": "https://github.com/x/commits.atom"},
                    {"name": "AI News Search", "url": "https://news.google.com/search?q=x",
                     "rss": "https://news.google.com/search?q=x", "source_type": "news_search"},
                ]
            }
        }
        imported = store.import_registry_sources(self.conn, registry)
        self.assertEqual(imported, 3)
        tiers = {
            r["name"]: (r["tier"], r["daily_intake"])
            for r in self.conn.execute("SELECT name, tier, daily_intake FROM sources")
        }
        # feedless homepage -> default first_party, still daily (first-party trusted)
        self.assertEqual(tiers["Runway"][0], "first_party")
        # google news search -> discovery, feed present so daily-eligible as a lead
        self.assertEqual(tiers["AI News Search"][0], "discovery")


if __name__ == "__main__":
    unittest.main()
