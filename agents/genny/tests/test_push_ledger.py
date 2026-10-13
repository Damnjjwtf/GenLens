from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import genlens_push_ledger as sender


class PushLedgerTests(unittest.TestCase):
    def record(self):
        return {"id": "sig_" + "a" * 20, "observation_count": 1, "status": "qualified"}

    def test_event_id_is_repeatable_and_actor_scoped(self):
        record = self.record()
        first = sender.event_for("genny", record)
        second = sender.event_for("genny", dict(reversed(list(record.items()))))
        marti = sender.event_for("marti", record)
        self.assertEqual(first["event_id"], second["event_id"])
        self.assertNotEqual(first["event_id"], marti["event_id"])
        self.assertEqual(first["idempotency_key"], first["event_id"])

    def test_checkpoint_skips_acknowledged_event(self):
        event = sender.event_for("genny", self.record())
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "acks.json"
            with mock.patch.object(sender, "send_event", return_value={"ok": True}) as post:
                first = sender.push([event], checkpoint, url="https://example.org/api/ingest/signals", token="x" * 40)
                second = sender.push([event], checkpoint, url="https://example.org/api/ingest/signals", token="x" * 40)
            self.assertEqual(first["acked"], 1)
            self.assertEqual(second["acked"], 0)
            self.assertEqual(post.call_count, 1)
            self.assertIn(event["event_id"], sender.read_checkpoint(checkpoint)["acknowledged"])

    def test_failed_push_does_not_record_an_acknowledgement(self):
        event = sender.event_for("genny", self.record())
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "acks.json"
            with mock.patch.object(sender, "send_event", side_effect=RuntimeError("network down")):
                with self.assertRaises(RuntimeError):
                    sender.push([event], checkpoint, url="https://example.org/api", token="x" * 40)
            self.assertFalse(checkpoint.exists())

    def test_dry_run_does_not_require_credentials_or_write_state(self):
        event = sender.event_for("genny", self.record())
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "acks.json"
            with mock.patch.object(sender, "send_event") as post:
                report = sender.push([event], checkpoint, url=None, token=None, dry_run=True)
            self.assertEqual(report["pending"], 1)
            self.assertEqual(report["acked"], 0)
            self.assertFalse(checkpoint.exists())
            post.assert_not_called()

    def test_endpoint_requires_tls_outside_local_development(self):
        sender.validate_endpoint("https://example.org/api/ingest/signals")
        sender.validate_endpoint("http://localhost:3000/api/ingest/signals")
        with self.assertRaises(ValueError):
            sender.validate_endpoint("http://some-remote-host.example/ingest")

    def test_corrupted_checkpoint_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "acks.json"
            checkpoint.write_text("{invalid JSON", encoding="utf-8")
            with self.assertRaises(ValueError):
                sender.read_checkpoint(checkpoint)
            self.assertEqual(checkpoint.read_text(encoding="utf-8"), "{invalid JSON")


if __name__ == "__main__":
    unittest.main()
