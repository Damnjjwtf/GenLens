from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_decision_brief as decision_brief
import genlens_signal_ledger as ledger


class DecisionBriefTests(unittest.TestCase):
    def review(self, **overrides):
        row = {
            "lens": "marti",
            "vertical": "Stack Consolidation / Displacement",
            "source_name": "Relay",
            "source_url": "https://relay.app/blog/",
            "source_type": "official_updates",
            "source_priority": "high",
            "title": "Relay is shutting down and customers must migrate workflows",
            "summary": "The service closes in September and customers must export workflows.",
            "url": "https://relay.app/blog/shutdown",
            "published_at": "2026-07-21",
            "status": "published",
            "score": 9,
            "reason": "published in brief",
        }
        row.update(overrides)
        return ledger.make_candidate_review(**row)

    def test_brief_renders_current_published_recommendations_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            ledger.write_signal_ledger(
                path,
                [
                    self.review(),
                    self.review(
                        title="Static identity explainer",
                        summary="No concrete change.",
                        url="https://example.com/static-explainer",
                        status="rejected",
                        score=0,
                        reason="missing concrete change or measured outcome",
                    ),
                ],
                run_lens="marti",
                mode="expanded",
                observed_at="2026-07-21T12:00:00+00:00",
            )
            payload = decision_brief.load_ledger(path)
            markdown = decision_brief.render_decision_brief(payload)

        self.assertIn("Migrate —", markdown)
        self.assertIn("Relay is shutting down", markdown)
        self.assertNotIn("### Watch — Static identity explainer", markdown)
        self.assertIn("Rejected candidates retained for audit: 1", markdown)
        self.assertIn("not recorded user decisions", markdown)
        self.assertIn("do not count toward Weekly Verified Decision Actions", markdown)
        self.assertIn("Confirmation needed", markdown)

    def test_empty_published_set_does_not_manufacture_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            ledger.write_signal_ledger(
                path,
                [self.review(status="rejected", score=0, reason="stale item")],
                run_lens="marti",
                mode="expanded",
                observed_at="2026-07-21T12:00:00+00:00",
            )
            markdown = decision_brief.render_decision_brief(decision_brief.load_ledger(path))

        self.assertIn("do not manufacture a decision", markdown)


if __name__ == "__main__":
    unittest.main()
