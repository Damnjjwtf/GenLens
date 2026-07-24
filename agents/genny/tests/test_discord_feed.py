from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import genlens_send_discord as discord_feed


class DiscordFeedTests(unittest.TestCase):
    def ledger(self, count: int = 8) -> dict:
        observed = [f"sig_{index:020x}" for index in range(count)]
        records = []
        for index, signal_id in enumerate(observed):
            records.append({
                "id": signal_id,
                "status": "published",
                "title": f"Verified Marti signal {index}",
                "summary": "The official source introduced a concrete marketing workflow change.",
                "canonical_url": f"https://vendor.example.com/change-{index}",
                "verticals": [f"Layer {index % 3}"],
                "score": 10 - index,
                "confidence": "primary-source",
                "source": {"name": "Vendor", "authoritative": True},
            })
        return {
            "latest_run": {"observed_at": "2026-07-24T15:00:00+00:00", "observed_signal_ids": observed},
            "records": records,
        }

    def test_webhook_validation_is_narrow(self) -> None:
        self.assertTrue(discord_feed.valid_discord_webhook(
            "https://discord.com/api/webhooks/1234567890/secret-token"
        ))
        self.assertFalse(discord_feed.valid_discord_webhook("http://discord.com/api/webhooks/1/token"))
        self.assertFalse(discord_feed.valid_discord_webhook("https://example.com/api/webhooks/1/token"))
        self.assertFalse(discord_feed.valid_discord_webhook("https://discord.com/channels/1/2"))

    def test_env_file_loads_webhook_without_overriding_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "# secret\n"
                "MARTI_DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/123/token'\n"
                "EXPORTED_VALUE=file-value\n"
            )
            previous_webhook = os.environ.pop("MARTI_DISCORD_WEBHOOK_URL", None)
            previous_export = os.environ.get("EXPORTED_VALUE")
            os.environ["EXPORTED_VALUE"] = "shell-value"
            try:
                discord_feed.load_env(path)
                self.assertEqual(
                    os.environ["MARTI_DISCORD_WEBHOOK_URL"],
                    "https://discord.com/api/webhooks/123/token",
                )
                self.assertEqual(os.environ["EXPORTED_VALUE"], "shell-value")
            finally:
                if previous_webhook is None:
                    os.environ.pop("MARTI_DISCORD_WEBHOOK_URL", None)
                else:
                    os.environ["MARTI_DISCORD_WEBHOOK_URL"] = previous_webhook
                if previous_export is None:
                    os.environ.pop("EXPORTED_VALUE", None)
                else:
                    os.environ["EXPORTED_VALUE"] = previous_export

    def test_real_brief_requires_promotion_but_test_does_not(self) -> None:
        status = {"promoted": False, "reason": "hold: Marti clean dated run streak=1/3"}
        self.assertEqual(
            discord_feed.delivery_readiness(status),
            (False, "hold: Marti clean dated run streak=1/3"),
        )
        self.assertEqual(
            discord_feed.delivery_readiness(status, test=True),
            (True, "Discord connection test"),
        )

    def test_payload_is_short_source_linked_and_card_limited(self) -> None:
        ledger = self.ledger()
        # This unit uses the already-shaped current records; schema validation is
        # covered by the signal-ledger suite and the CLI load path.
        original = discord_feed.current_published_records
        discord_feed.current_published_records = lambda _ledger: ledger["records"]
        try:
            payload = discord_feed.briefing_payload(
                ledger,
                {"promoted": True, "reviewed_card_occurrences": 20},
                max_cards=6,
            )
        finally:
            discord_feed.current_published_records = original

        embed = payload["embeds"][0]
        self.assertEqual(payload["username"], "Marti • GenLens")
        self.assertEqual(len(embed["fields"]), 6)
        self.assertIn("2 remain", embed["description"])
        self.assertIn("[Open source](https://vendor.example.com/change-0)", embed["fields"][0]["value"])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})

    def test_history_is_fail_closed_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            history = discord_feed.load_history(path)
            discord_feed.append_delivery(
                history,
                fingerprint="abc123",
                kind="test",
                message_id="message-1",
            )
            discord_feed.write_history(path, history)
            loaded = discord_feed.load_history(path)
            self.assertEqual(loaded["deliveries"][0]["fingerprint"], "abc123")

            path.write_text(json.dumps({"version": "broken"}))
            with self.assertRaises(ValueError):
                discord_feed.load_history(path)


if __name__ == "__main__":
    unittest.main()
