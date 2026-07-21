from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_convergence as convergence
import genlens_signal_ledger as ledger


class ConvergenceTests(unittest.TestCase):
    def review(
        self,
        *,
        lens: str,
        vertical: str,
        title: str,
        summary: str,
        url: str,
    ) -> dict:
        return ledger.make_candidate_review(
            lens=lens,
            vertical=vertical,
            source_name="Official source",
            source_url=url.rsplit("/", 1)[0],
            source_type="official_updates",
            source_priority="high",
            title=title,
            summary=summary,
            url=url,
            published_at="2026-07-21",
            status="published",
            score=9,
            reason="published in brief",
        )

    def unified_payload(self, *, include_marti: bool = True, related: bool = True, bridge: bool = True) -> dict:
        reviews = [
            self.review(
                lens="genny",
                vertical="AI Filmmaking",
                title="Runway launches generative video creative asset workflow",
                summary=(
                    "The new API gives production teams frame-level editing control and scales campaign-ready video asset output."
                    if bridge
                    else "The new API gives production teams frame-level editing control for campaign-ready video assets."
                ),
                url="https://runwayml.com/news/video-creative-api",
            )
        ]
        if include_marti:
            if related:
                reviews.append(self.review(
                    lens="marti",
                    vertical="Paid Media / Creative Performance",
                    title="Meta launches automated video ad creative workflow",
                    summary=(
                        "The new API helps campaign teams scale generation and testing of video creative assets across paid media."
                        if bridge
                        else "The new API helps campaign teams generate and test video creative assets across paid media."
                    ),
                    url="https://about.fb.com/news/video-ad-creative-api",
                ))
            else:
                reviews.append(self.review(
                    lens="marti",
                    vertical="Lifecycle / Retention",
                    title="Salesforce updates customer retention email controls",
                    summary="CRM teams can change lifecycle segmentation rules for customer email journeys.",
                    url="https://salesforce.com/news/retention-email-controls",
                ))
        records = ledger.build_run_records(
            reviews,
            run_lens="unified",
            mode="expanded",
            observed_at="2026-07-21T12:00:00+00:00",
        )
        return {
            "schema_version": ledger.SCHEMA_VERSION,
            "generated_at": "2026-07-21T12:00:00+00:00",
            "latest_run": {
                "lens": "unified",
                "mode": "expanded",
                "observed_at": "2026-07-21T12:00:00+00:00",
                "observed_signal_ids": [row["id"] for row in records],
                "counts": {"published": len(records), "qualified": 0, "rejected": 0},
            },
            "records": records,
        }

    def test_candidate_requires_a_current_signal_from_both_lenses(self) -> None:
        self.assertEqual(convergence.build_candidates(self.unified_payload(include_marti=False)), [])
        self.assertEqual(convergence.build_candidates(self.unified_payload(related=False)), [])
        self.assertEqual(convergence.build_candidates(self.unified_payload(bridge=False)), [])

    def test_candidate_retains_exact_evidence_and_asserts_no_causality(self) -> None:
        rows = convergence.build_candidates(self.unified_payload())

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertRegex(row["id"], r"^conv_[a-f0-9]{20}$")
        self.assertEqual({item["lens"] for item in row["evidence"]}, {"genny", "marti"})
        self.assertTrue(row["shared"]["workflows"])
        self.assertTrue(row["shared"]["mechanisms"])
        self.assertIn("no causal relationship is asserted", row["hypothesis"])
        self.assertEqual(row["status"], "candidate")
        self.assertEqual(row["confidence"], "hypothesis")

    def test_unverified_candidate_never_enters_publishable_brief(self) -> None:
        artifact = convergence.build_artifact(self.unified_payload(), convergence.empty_reviews())
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "latest_unified_brief.md"
            brief.write_text("# Unified Brief\n\n## Signals\n\n- Source-backed signal.\n")
            convergence.update_brief(brief, artifact)

            rendered = brief.read_text()
            self.assertNotIn("Verified Convergence", rendered)
            self.assertNotIn(artifact["records"][0]["hypothesis"], rendered)

    def test_attributed_review_is_required_before_verified_publication(self) -> None:
        payload = self.unified_payload()
        artifact = convergence.build_artifact(payload, convergence.empty_reviews())
        candidate_id = artifact["records"][0]["id"]
        conclusion = "Video-model editing is moving directly into paid-media creative operations."
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            reviews_path = root / "reviews.json"
            brief_path = root / "brief.md"
            convergence.atomic_write_json(candidates_path, artifact)
            brief_path.write_text("# Unified Brief\n")

            event, created = convergence.record_review(
                candidates_path=candidates_path,
                reviews_path=reviews_path,
                candidate_id_value=candidate_id,
                status="verified",
                actor_id="jonathan",
                note="Both sources describe the same video-asset handoff; no conversion lift is claimed.",
                conclusion=conclusion,
                idempotency_key="message-verified-1",
                recorded_at="2026-07-21T13:00:00+00:00",
            )
            self.assertTrue(created)
            self.assertEqual(event["actor_id"], "jonathan")

            verified = convergence.build_artifact(payload, convergence.load_reviews(reviews_path))
            convergence.validate_artifact(verified)
            convergence.update_brief(brief_path, verified)
            rendered = brief_path.read_text()

            self.assertEqual(verified["verified_count"], 1)
            self.assertIn(conclusion, rendered)
            self.assertIn("runwayml.com", rendered)
            self.assertIn("about.fb.com", rendered)
            self.assertNotIn("Potential shared", rendered)

    def test_review_log_is_idempotent_and_conflicts_fail_closed(self) -> None:
        payload = self.unified_payload()
        artifact = convergence.build_artifact(payload, convergence.empty_reviews())
        candidate_id = artifact["records"][0]["id"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            reviews_path = root / "reviews.json"
            convergence.atomic_write_json(candidates_path, artifact)
            kwargs = {
                "candidates_path": candidates_path,
                "reviews_path": reviews_path,
                "candidate_id_value": candidate_id,
                "status": "rejected",
                "actor_id": "jonathan",
                "note": "The shared vocabulary does not prove one operator workflow.",
                "conclusion": "",
                "idempotency_key": "message-rejected-1",
                "recorded_at": "2026-07-21T13:00:00+00:00",
            }
            _event, created = convergence.record_review(**kwargs)
            _event, replay_created = convergence.record_review(**kwargs)
            self.assertTrue(created)
            self.assertFalse(replay_created)
            self.assertEqual(len(convergence.load_reviews(reviews_path)["events"]), 1)

            with self.assertRaisesRegex(ValueError, "Idempotency key"):
                convergence.record_review(**{**kwargs, "status": "verified", "conclusion": "A different conclusion that is long enough."})

    def test_schema_version_matches_runtime(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "data" / "genlens_convergence.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertEqual(schema["properties"]["schema_version"]["const"], convergence.SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
