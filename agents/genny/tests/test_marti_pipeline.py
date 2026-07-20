from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_compose_brief as composer
import genlens_send_email as email


class MartiPipelineTests(unittest.TestCase):
    def test_marti_active_layers_are_distinct_from_genny(self) -> None:
        marti = composer.verticals_for_mode("active", "marti")
        genny = composer.verticals_for_mode("active", "genny")
        self.assertEqual(len(marti), 3)
        self.assertFalse(set(marti) & set(genny))

    def test_marti_source_registry_exists(self) -> None:
        self.assertTrue(composer.source_path_for_lens("marti").exists())
        data = composer.load_sources("marti")
        self.assertEqual(set(composer.MARTI_ACTIVE_LAYERS), set(data["verticals"]) & set(composer.MARTI_ACTIVE_LAYERS))

    def test_recent_window_rejects_old_items(self) -> None:
        today = dt.datetime.now(dt.timezone.utc).date()
        self.assertTrue(composer.likely_recent("Current release", today.isoformat()))
        self.assertFalse(composer.likely_recent("Old release", (today - dt.timedelta(days=46)).isoformat()))

    def test_convergence_requires_both_lenses(self) -> None:
        self.assertEqual(composer.convergence_candidates({"genny": [], "marti": []}), [])
        pairs = composer.convergence_candidates({
            "genny": [{"title": "Product image workflow API", "summary": "Commerce creative pipeline", "url": "https://example.com/genny/release"}],
            "marti": [{"title": "Commerce campaign API", "summary": "Creative conversion workflow", "url": "https://example.com/marti/release"}],
        })
        self.assertGreaterEqual(len(pairs), 1)

    def test_housekeeping_does_not_become_marti_card(self) -> None:
        markdown = """# Marti Briefing

## Agentic Marketing Workflows

- No qualified feed signals — feeds were quiet.
- **[n8n ships an agent workflow update](https://example.com/blog/release)** — Adds campaign automation.
"""
        items = email.public_briefing_items(markdown)
        self.assertEqual([item["title"] for item in items], ["n8n ships an agent workflow update"])

    def test_email_uses_marti_identity(self) -> None:
        markdown = """# Marti Briefing

## Paid Media / Creative Performance

- **[Google Ads changes campaign measurement](https://example.com/news/release)** — Adds a new attribution control.
"""
        rendered = email.render_briefing_html(markdown)
        self.assertIn("Marti Stack Intelligence", rendered)
        self.assertNotIn("Creative AI signals worth acting on.", rendered)


if __name__ == "__main__":
    unittest.main()
