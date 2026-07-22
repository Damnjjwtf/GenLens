from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_promotion as promotion
import genlens_signal_ledger as ledger


class PromotionTests(unittest.TestCase):
    def write_run_artifacts(self, root: Path, date: str, suffix: str = "") -> tuple[Path, Path]:
        reviews = []
        verticals = [
            "Agentic Marketing Workflows",
            "Paid Media / Creative Performance",
            "Lifecycle / Retention",
            "Commerce / Conversion",
        ]
        lines = [f"# Marti Briefing - {date}", ""]
        for index in range(8):
            vertical = verticals[index % len(verticals)]
            url = f"https://vendor{index}.example.com/news/change-{index}{suffix}"
            title = f"Vendor {index} launches marketing workflow {index}{suffix}"
            summary = "The official update adds an AI marketing workflow and a concrete operator control."
            reviews.append(ledger.make_candidate_review(
                lens="marti",
                vertical=vertical,
                source_name=f"Vendor {index}",
                source_url=f"https://vendor{index}.example.com/news/",
                source_type="official_updates",
                source_priority="high",
                title=title,
                summary=summary,
                url=url,
                published_at=date,
                status="published",
                score=8,
                reason="published in brief",
            ))
            lines.extend([
                f"## {vertical}",
                "",
                f"- **[{title}]({url})** — {summary} `{date}` `Vendor {index}` [Source]({url})",
                "",
            ])
        ledger_path = root / f"ledger-{date}{suffix}.json"
        brief_path = root / f"brief-{date}{suffix}.md"
        ledger.write_signal_ledger(
            ledger_path,
            reviews,
            run_lens="marti",
            mode="expanded",
            observed_at=f"{date}T08:00:00+00:00",
        )
        brief_path.write_text("\n".join(lines))
        return ledger_path, brief_path

    def record(self, root: Path, log: Path, date: str, suffix: str = "", **overrides):
        ledger_path, brief_path = self.write_run_artifacts(root, date, suffix)
        kwargs = {
            "log_path": log,
            "ledger_path": ledger_path,
            "brief_path": brief_path,
            "idempotency_key": f"marti-{date}{suffix}",
            "min_cards": 6,
            "min_verticals": 3,
            "new_link_count": 8,
            "recorded_at": f"{date}T09:00:00+00:00",
        }
        kwargs.update(overrides)
        return promotion.record_run(**kwargs)

    def test_one_dated_run_cannot_promote_marti(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.record(root, root / "promotion.json", "2026-07-21")

        self.assertTrue(result["run"]["issue_gate_passed"])
        self.assertFalse(result["status"]["promoted"])
        self.assertEqual(result["status"]["clean_dated_run_streak"], 1)
        self.assertEqual(result["status"]["reason"], "hold: Marti clean dated run streak=1/3")

    def test_repeated_same_day_runs_count_as_one_dated_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "promotion.json"
            self.record(root, log, "2026-07-21", "-a")
            self.record(root, log, "2026-07-21", "-b", recorded_at="2026-07-21T10:00:00+00:00")
            status = promotion.promotion_status(promotion.load_log(log))

        self.assertEqual(status["clean_dated_run_streak"], 1)

    def test_three_clean_runs_still_require_twenty_attributed_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "promotion.json"
            for date in ("2026-07-21", "2026-07-22", "2026-07-23"):
                self.record(root, log, date)
            status = promotion.promotion_status(promotion.load_log(log))

        self.assertEqual(status["clean_dated_run_streak"], 3)
        self.assertEqual(status["accepted_card_occurrences"], 20)
        self.assertEqual(status["reviewed_card_occurrences"], 0)
        self.assertFalse(status["promoted"])
        self.assertEqual(status["reason"], "hold: Marti human reviews=0/20")

    def test_twenty_reviews_promote_with_at_most_one_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "promotion.json"
            for date in ("2026-07-21", "2026-07-22", "2026-07-23"):
                self.record(root, log_path, date)
            log = promotion.load_log(log_path)
            occurrences = []
            for run in reversed(log["runs"]):
                occurrences.extend((run["id"], signal_id) for signal_id in run["signal_ids"])
            for index, (run_id, signal_id) in enumerate(occurrences[:20]):
                promotion.record_review(
                    log_path=log_path,
                    run_id=run_id,
                    signal_id=signal_id,
                    verdict="false_positive" if index == 0 else "accepted",
                    issue_type="relevance" if index == 0 else None,
                    actor_id="jonathan",
                    channel="cli",
                    note="Reviewed source, layer, evidence, and relevance.",
                    idempotency_key=f"review-{index}",
                    occurred_at=f"2026-07-24T{index:02d}:00:00+00:00",
                )
            status = promotion.promotion_status(promotion.load_log(log_path))

            second_run, second_signal = occurrences[1]
            promotion.record_review(
                log_path=log_path,
                run_id=second_run,
                signal_id=second_signal,
                verdict="false_positive",
                issue_type="layer",
                actor_id="jonathan",
                channel="cli",
                note="Second false positive after a deeper layer review.",
                idempotency_key="review-second-false-positive",
                occurred_at="2026-07-25T12:00:00+00:00",
            )
            failed = promotion.promotion_status(promotion.load_log(log_path))

        self.assertTrue(status["promoted"])
        self.assertEqual(status["false_positives"], 1)
        self.assertFalse(failed["promoted"])
        self.assertEqual(failed["false_positives"], 2)

    def test_exact_repeat_breaks_the_clean_run_streak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "promotion.json"
            self.record(root, log, "2026-07-21")
            repeated = self.record(root, log, "2026-07-22", exact_repeat=True)

        self.assertFalse(repeated["run"]["issue_gate_passed"])
        self.assertEqual(repeated["status"]["clean_dated_run_streak"], 0)

    def test_run_idempotency_and_corrupt_history_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "promotion.json"
            first = self.record(root, log, "2026-07-21")
            second = self.record(root, log, "2026-07-21")
            self.assertTrue(first["created"])
            self.assertFalse(second["created"])

            payload = json.loads(log.read_text())
            payload["runs"][0]["linked_cards"] = 0
            log.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "pass state does not match"):
                promotion.load_log(log)

    def test_schema_version_matches_runtime(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "data" / "genlens_promotion_log.schema.json"
        schema = json.loads(schema_path.read_text())

        self.assertEqual(schema["properties"]["log_version"]["const"], promotion.LOG_VERSION)


if __name__ == "__main__":
    unittest.main()
