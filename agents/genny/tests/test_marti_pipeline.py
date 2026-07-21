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

    def test_official_updates_score_like_release_notes(self) -> None:
        item = {
            "title": "Optimize campaign reach with new video campaign groups",
            "summary": "Google Ads adds a campaign control for advertisers and measurement teams.",
            "url": "https://blog.google/products/ads-commerce/video-campaign-groups/",
            "date": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        }
        common = {
            "name": "Google Ads and Commerce",
            "priority": "high",
            "watch_for": ["Google Ads", "campaign", "measurement"],
        }
        official = composer.quality_review(
            "Paid Media / Creative Performance",
            {**common, "source_type": "official_updates"},
            item["title"], item["summary"], item["url"], item["date"],
        )
        releases = composer.quality_review(
            "Paid Media / Creative Performance",
            {**common, "source_type": "release_notes"},
            item["title"], item["summary"], item["url"], item["date"],
        )
        self.assertTrue(official[0])
        self.assertEqual(official[1], releases[1])

    def test_shutdown_is_a_displacement_signal_but_free_trial_is_not(self) -> None:
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        shutdown_source = {
            "name": "Zapier Blog",
            "source_type": "blog",
            "priority": "high",
            "watch_for": ["shutdown", "migration", "replacement", "workflow"],
        }
        accepted = composer.quality_review(
            "Stack Consolidation / Displacement",
            shutdown_source,
            "Relay.app is shutting down: export your workflows and move to Zapier",
            "Relay customers can migrate their automation workflows before the service closes.",
            "https://zapier.com/blog/relay-alternatives",
            today,
        )
        self.assertTrue(accepted[0])

        rejected = composer.quality_review(
            "Marketing Data / Identity",
            {
                "name": "RudderStack Blog",
                "source_type": "blog",
                "priority": "high",
                "watch_for": ["customer data", "CDP", "warehouse"],
            },
            "Get the full power of RudderStack free for 30 days",
            "Start a free trial of the customer data platform.",
            "https://www.rudderstack.com/blog/rudderstack-30-day-free-trial",
            today,
        )
        self.assertFalse(rejected[0])
        self.assertIn("false-positive", rejected[2])

    def test_static_identity_explainer_is_not_a_marti_change_signal(self) -> None:
        accepted, _score, reason = composer.quality_review(
            "Marketing Data / Identity",
            {
                "name": "RudderStack Blog",
                "source_type": "blog",
                "priority": "high",
                "watch_for": ["customer data", "CDP", "warehouse"],
            },
            "How RudderStack handles customer data in transit",
            "RudderStack is data pipeline infrastructure, not a data broker. Here is how customer data is handled.",
            "https://www.rudderstack.com/blog/how-rudderstack-handles-customer-data-in-transit",
            dt.datetime.now(dt.timezone.utc).date().isoformat(),
        )

        self.assertFalse(accepted)
        self.assertEqual(reason, "missing concrete change or measured outcome")

    def test_page_footer_update_cannot_promote_static_marti_article(self) -> None:
        accepted, _score, reason = composer.quality_review(
            "Marketing Data / Identity",
            {
                "name": "RudderStack Blog",
                "source_type": "blog",
                "priority": "high",
                "watch_for": ["customer data", "CDP", "warehouse"],
            },
            "How RudderStack handles customer data in transit",
            (
                "Contact us to review your configuration. RudderStack Updates: "
                "a separate release adds real-time JavaScript SDK debugging."
            ),
            "https://www.rudderstack.com/blog/how-rudderstack-handles-customer-data-in-transit",
            dt.datetime.now(dt.timezone.utc).date().isoformat(),
        )

        self.assertFalse(accepted)
        self.assertEqual(reason, "missing concrete change or measured outcome")

    def test_sparse_official_feed_item_is_enriched_before_marti_scoring(self) -> None:
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        feed = f"""<?xml version="1.0"?>
<rss><channel><item>
  <title>Optimize your reach and frequency across campaigns with video campaign groups</title>
  <link>https://blog.google/products/ads-commerce/video-campaign-groups/</link>
  <pubDate>{today}</pubDate>
</item></channel></rss>""".encode()
        article = b"""<html><head>
<meta content="Coordinate reach and frequency across campaigns." property="og:description">
</head><body>
<p>Video campaign groups are now available globally in Google Ads, with unified reporting across campaigns.</p>
</body></html>"""

        class Headers:
            def get(self, name, default=""):
                return "text/html" if name.lower() == "content-type" else default

        class FakeResponse:
            def __init__(self, body: bytes):
                self.body = body
                self.headers = Headers()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, *_args):
                return self.body

        source = {
            "name": "Google Ads and Commerce",
            "rss": "https://example.com/google-ads.xml",
            "source_type": "official_updates",
            "priority": "high",
            "watch_for": ["Google Ads", "campaign", "measurement"],
        }
        with mock.patch.object(
            composer.urllib.request,
            "urlopen",
            side_effect=[FakeResponse(feed), FakeResponse(article)],
        ):
            items = composer.fetch_rss(source, "Paid Media / Creative Performance", 5)

        self.assertEqual(len(items), 1)
        self.assertIn("now available globally", items[0]["summary"])
        self.assertNotIn("requires manual review", items[0]["summary"].lower())

    def test_article_enrichment_finds_late_layer_specific_evidence(self) -> None:
        navigation = "".join(
            f"<p>Archive navigation entry {index} introduces unrelated product updates and resources.</p>"
            for index in range(40)
        )
        navigation += "<p>" + ("Google Search SEO updates and release archive navigation. " * 60) + "</p>"
        article = f"""<html><head>
<meta name="description" content="Search documentation and archived announcements.">
</head><body>
{navigation}
<p>Following an earlier experiment, Google introduced platform properties, a new Search Console property type. Site owners can now track search terms that lead to their social channels.</p>
</body></html>""".encode()

        class Headers:
            def get(self, name, default=""):
                return "text/html" if name.lower() == "content-type" else default

        class FakeResponse:
            headers = Headers()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, *_args):
                return article

        with mock.patch.object(composer.urllib.request, "urlopen", return_value=FakeResponse()):
            excerpt = composer.fetch_article_excerpt(
                "https://developers.google.com/search/blog/platform-properties",
                composer.MARTI_REQUIRED_PATTERNS["SEO / AEO / Content Systems"],
            )

        self.assertIn("new Search Console property type", excerpt)
        self.assertNotIn("Archive navigation entry", excerpt)
        self.assertTrue(composer.has_marti_event_evidence(excerpt))


if __name__ == "__main__":
    unittest.main()
