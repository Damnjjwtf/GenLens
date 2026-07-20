from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

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

    def test_google_news_item_removes_publisher_suffix_and_repeated_description(self) -> None:
        title = "Drive international conversion with automated duties-inclusive pricing from Shopify Managed Markets - Shopify"
        cleaned_title = composer.clean_google_news_title(title, "Shopify")
        description = (
            '<a href="https://news.google.com/rss/articles/example">'
            "Drive international conversion with automated duties-inclusive pricing from Shopify Managed Markets"
            '</a>&nbsp;&nbsp;<font color="#6f6f6f">Shopify</font>'
        )

        self.assertEqual(
            cleaned_title,
            "Drive international conversion with automated duties-inclusive pricing from Shopify Managed Markets",
        )
        self.assertEqual(
            composer.clean_google_news_summary(description, cleaned_title, "Shopify"),
            "",
        )
        self.assertEqual(
            composer.strip_text("creators&amp;mdash;even those without websites"),
            "creators—even those without websites",
        )
        self.assertEqual(
            composer.clean_excerpt(
                "Merchants can use managed pricing across international markets. "
                "Pricing will account for cross-bor..."
            ),
            "Merchants can use managed pricing across international markets.",
        )

    def test_google_news_resolver_returns_original_source_url(self) -> None:
        wrapper = b'<c-wiz><div data-n-a-sg="signature" data-n-a-ts="1784585625"></div></c-wiz>'
        original_url = "https://changelog.shopify.com/posts/duties-inclusive-pricing"
        rpc_result = json.dumps(["garturlres", original_url, 1])
        batch = (")]}'\n\n" + json.dumps([["wrb.fr", "Fbv4je", rpc_result]])).encode()

        class FakeResponse:
            def __init__(self, body: bytes):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, *_args):
                return self.body

        google_url = "https://news.google.com/rss/articles/encoded-id?oc=5"
        with mock.patch.object(
            composer.urllib.request,
            "urlopen",
            side_effect=[FakeResponse(wrapper), FakeResponse(batch)],
        ):
            resolved = composer.resolve_google_news_url(
                google_url,
                expected_source_url="https://changelog.shopify.com",
            )

        self.assertEqual(resolved, original_url)


if __name__ == "__main__":
    unittest.main()
