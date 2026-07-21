from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_decision_queue as decisions
import genlens_signal_ledger as ledger


class DecisionQueueTests(unittest.TestCase):
    SIGNAL_ID = "sig_0123456789abcdefabcd"

    def test_schema_version_and_action_contract_match_runtime(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "data" / "genlens_decision_queue.schema.json"
        schema = json.loads(schema_path.read_text())

        self.assertEqual(schema["properties"]["queue_version"]["const"], decisions.QUEUE_VERSION)
        self.assertEqual(set(schema["$defs"]["action"]["enum"]), decisions.ACTIONS)
        self.assertEqual(set(schema["$defs"]["status"]["enum"]), decisions.ITEM_STATUSES)

    def write_ledger(self, path: Path) -> None:
        review = ledger.make_candidate_review(
            lens="marti",
            vertical="Stack Consolidation / Displacement",
            source_name="Zapier Blog",
            source_url="https://zapier.com/blog/",
            source_type="blog",
            source_priority="high",
            title="Relay.app is shutting down",
            summary="Operators need to migrate workflows before shutdown.",
            url="https://zapier.com/blog/relay-alternatives",
            published_at="2026-07-20",
            status="published",
            score=8,
            reason="published in brief",
        )
        review["signal_id"] = self.SIGNAL_ID
        ledger.write_signal_ledger(
            path,
            [review],
            run_lens="marti",
            mode="expanded",
            observed_at="2026-07-20T08:00:00+00:00",
        )

    def test_user_action_creates_queue_item_and_qualifies_for_wvda(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)

            result = decisions.record_action(
                queue_path=queue_path,
                ledger_path=ledger_path,
                signal_id=self.SIGNAL_ID,
                action="watch",
                actor_id="jonathan",
                actor_type="user",
                channel="cli",
                note="Track the Relay shutdown and migration window.",
                occurred_at="2026-07-20T12:00:00+00:00",
                idempotency_key="relay-watch-1",
            )

            data = json.loads(queue_path.read_text())
            self.assertFalse(result["deduplicated"])
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["status"], "queued")
            self.assertEqual(data["items"][0]["signal_id"], self.SIGNAL_ID)
            self.assertEqual(len(data["events"]), 1)
            self.assertTrue(data["events"][0]["qualifies_wvda"])

    def test_idempotency_key_prevents_duplicate_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)
            kwargs = {
                "queue_path": queue_path,
                "ledger_path": ledger_path,
                "signal_id": self.SIGNAL_ID,
                "action": "test",
                "actor_id": "jonathan",
                "actor_type": "user",
                "channel": "discord",
                "note": "Test the migration path in a sandbox.",
                "occurred_at": "2026-07-20T13:00:00+00:00",
                "idempotency_key": "relay-test-1",
            }

            first = decisions.record_action(**kwargs)
            second = decisions.record_action(**kwargs)
            data = json.loads(queue_path.read_text())

            self.assertFalse(first["deduplicated"])
            self.assertTrue(second["deduplicated"])
            self.assertEqual(len(data["events"]), 1)

            changed = dict(kwargs)
            changed["note"] = "A different decision must not reuse this key."
            with self.assertRaisesRegex(ValueError, "different decision event"):
                decisions.record_action(**changed)

    def test_agent_events_and_state_transitions_do_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)
            action = decisions.record_action(
                queue_path=queue_path,
                ledger_path=ledger_path,
                signal_id=self.SIGNAL_ID,
                action="watch",
                actor_id="genny",
                actor_type="agent",
                channel="api",
                note="Genny recommends monitoring this signal.",
                occurred_at="2026-07-20T12:00:00+00:00",
                idempotency_key="agent-watch-1",
            )
            transition = decisions.transition_item(
                queue_path=queue_path,
                item_id=action["item"]["id"],
                status="dismissed",
                actor_id="jonathan",
                actor_type="user",
                channel="cli",
                note="Not relevant to the current stack.",
                occurred_at="2026-07-20T14:00:00+00:00",
                idempotency_key="dismiss-1",
            )

            data = json.loads(queue_path.read_text())
            self.assertFalse(action["event"]["qualifies_wvda"])
            self.assertFalse(transition["event"]["qualifies_wvda"])
            self.assertEqual(data["items"][0]["status"], "dismissed")
            report = decisions.wvda_report(queue_path, week_start="2026-07-20")
            self.assertEqual(report["weekly_verified_decision_actions"], 0)

    def test_wvda_counts_unique_user_signal_actions_per_week(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)
            base = {
                "queue_path": queue_path,
                "ledger_path": ledger_path,
                "signal_id": self.SIGNAL_ID,
                "actor_id": "jonathan",
                "actor_type": "user",
                "channel": "cli",
            }
            decisions.record_action(
                **base,
                action="watch",
                note="Monitor the shutdown.",
                occurred_at="2026-07-20T12:00:00+00:00",
                idempotency_key="watch-1",
            )
            decisions.record_action(
                **base,
                action="watch",
                note="Reconfirmed the same watch decision.",
                occurred_at="2026-07-21T12:00:00+00:00",
                idempotency_key="watch-2",
            )
            decisions.record_action(
                **base,
                action="test",
                note="Start a migration proof.",
                occurred_at="2026-07-22T12:00:00+00:00",
                idempotency_key="test-1",
            )
            decisions.record_action(
                **base,
                action="adopt",
                note="This happened before the reporting week.",
                occurred_at="2026-07-13T12:00:00+00:00",
                idempotency_key="adopt-old",
            )

            report = decisions.wvda_report(queue_path, week_start="2026-07-20")
            self.assertEqual(report["qualifying_event_count"], 3)
            self.assertEqual(report["weekly_verified_decision_actions"], 2)
            self.assertEqual(report["by_action"], {"test": 1, "watch": 1})
            self.assertEqual(report["unique_signals"], 1)

    def test_unknown_signal_and_corrupt_queue_fail_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)

            with self.assertRaisesRegex(ValueError, "not present in the signal ledger"):
                decisions.record_action(
                    queue_path=queue_path,
                    ledger_path=ledger_path,
                    signal_id="sig_ffffffffffffffffffff",
                    action="watch",
                    actor_id="jonathan",
                    actor_type="user",
                    channel="cli",
                    note="Unknown signal.",
                    idempotency_key="unknown-1",
                )

            queue_path.write_text("not-json")
            with self.assertRaisesRegex(ValueError, "risking decision-history loss"):
                decisions.record_action(
                    queue_path=queue_path,
                    ledger_path=ledger_path,
                    signal_id=self.SIGNAL_ID,
                    action="watch",
                    actor_id="jonathan",
                    actor_type="user",
                    channel="cli",
                    note="Do not overwrite corrupt history.",
                    idempotency_key="corrupt-1",
                )
            self.assertEqual(queue_path.read_text(), "not-json")

    def test_tampered_state_history_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ledger.json"
            queue_path = Path(tmp) / "decisions.json"
            self.write_ledger(ledger_path)
            decisions.record_action(
                queue_path=queue_path,
                ledger_path=ledger_path,
                signal_id=self.SIGNAL_ID,
                action="plan",
                actor_id="jonathan",
                actor_type="user",
                channel="cli",
                note="Plan the migration sequence.",
                occurred_at="2026-07-20T12:00:00+00:00",
                idempotency_key="plan-1",
            )
            payload = json.loads(queue_path.read_text())
            payload["items"][0]["status"] = "completed"
            queue_path.write_text(json.dumps(payload))

            with self.assertRaisesRegex(ValueError, "does not match its event history"):
                decisions.load_queue(queue_path)


if __name__ == "__main__":
    unittest.main()
