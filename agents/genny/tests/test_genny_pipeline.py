from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import genlens_compose_brief as composer
import genlens_signal_ledger as ledger


class GennyPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        self.official_source = {
            "name": "Official Product Updates",
            "url": "https://vendor.example.com/news/",
            "source_type": "official_updates",
            "priority": "high",
            "watch_for": ["AI", "production", "release"],
        }

    def review(
        self,
        vertical: str,
        title: str,
        summary: str,
        *,
        source: dict | None = None,
        url: str = "https://vendor.example.com/news/release",
    ) -> tuple[bool, int, str]:
        return composer.quality_review(
            vertical,
            source or self.official_source,
            title,
            summary,
            url,
            self.today,
        )

    def test_every_google_news_source_has_an_explicit_trust_boundary(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "data" / "genny_sources.json"
        registry = json.loads(source_path.read_text())
        search_sources = [
            source
            for sources in registry["verticals"].values()
            for source in sources
            if "news.google.com" in str(source.get("rss") or "")
        ]

        self.assertGreater(len(search_sources), 0)
        for source in search_sources:
            with self.subTest(source=source["name"]):
                self.assertEqual(source.get("source_type"), "news_search")
                self.assertGreater(len(source.get("trusted_domains", [])), 0)
                self.assertGreater(len(source.get("primary_domains", [])), 0)
                self.assertTrue(set(source["primary_domains"]) <= set(source["trusted_domains"]))

    def test_generic_engine_and_renderer_releases_are_not_ai_production_signals(self) -> None:
        cases = [
            (
                "Game Development / Real-Time 3D",
                "Godot 4.6.1 maintenance release",
                "The game engine update fixes editor crashes and improves platform compatibility for developers.",
            ),
            (
                "ArchViz",
                "V-Ray 7.4 for Blender released",
                "The architectural visualization renderer update adds material controls and general rendering fixes.",
            ),
        ]

        for vertical, title, summary in cases:
            with self.subTest(vertical=vertical):
                accepted, _score, reason = self.review(vertical, title, summary)
                self.assertFalse(accepted)
                self.assertEqual(reason, "missing explicit generative-AI production mechanism")

    def test_broad_ai_infrastructure_is_not_a_digital_human_signal(self) -> None:
        accepted, _score, reason = self.review(
            "Digital Humans",
            "NVIDIA announces Vera Rubin AI infrastructure",
            "The new AI compute platform increases data-center performance for training foundation models.",
        )

        self.assertFalse(accepted)
        self.assertEqual(reason, "missing vertical-specific production mechanism")

    def test_source_that_explicitly_negates_ai_workflow_is_rejected(self) -> None:
        accepted, _score, reason = self.review(
            "AI Design / Motion Graphics",
            "Addicted to Creation: a conversation with an independent designer",
            "The design conversation was not about tools, production pipelines, or AI; it focused on personal practice.",
            source={
                **self.official_source,
                "name": "Motionographer",
                "url": "https://motionographer.com/",
                "source_type": "blog",
            },
            url="https://motionographer.com/2026/07/addicted-to-creation",
        )

        self.assertFalse(accepted)
        self.assertEqual(reason, "source explicitly negates an AI production signal")

    def test_weak_source_reputation_checks_source_metadata_and_url(self) -> None:
        accepted, _score, reason = self.review(
            "Product Photography",
            "PixPix launches AI product photography workflow",
            "The company says its new generative AI workflow creates catalog product images for merchants.",
            source={
                **self.official_source,
                "name": "EIN News",
                "url": "https://www.einpresswire.com/",
                "source_type": "news_search",
            },
            url="https://www.einpresswire.com/article/ai-product-photography",
        )

        self.assertFalse(accepted)
        self.assertEqual(reason, "weak aggregator source")

        compact_domain = self.review(
            "Digital Humans",
            "ElevenLabs launches AI avatars for enterprise video",
            "ElevenLabs introduced generative AI avatars with synthetic voices and lip-sync controls for video teams.",
            source={**self.official_source, "name": "The Futurum Group"},
            url="https://futurumgroup.com/insights/elevenlabs-avatars",
        )
        self.assertFalse(compact_domain[0])
        self.assertEqual(compact_domain[2], "weak aggregator source")

    def test_unconfirmed_product_claim_and_empty_evidence_are_rejected(self) -> None:
        unconfirmed = self.review(
            "Social / Short-Form Video",
            "Gemini may power a new CapCut AI video workflow",
            "ByteDance and Google have not confirmed the generative AI feature or when the short-form tool will launch.",
        )
        empty = self.review(
            "Product Photography",
            "Meta launches AI product photography tools",
            "",
        )

        self.assertFalse(unconfirmed[0])
        self.assertEqual(unconfirmed[2], "unconfirmed product claim")
        self.assertFalse(empty[0])
        self.assertEqual(empty[2], "missing substantive source evidence")

    def test_news_search_requires_an_explicitly_trusted_publisher(self) -> None:
        source = {
            **self.official_source,
            "name": "AI Product Photography News Search",
            "rss": "https://news.google.com/rss/search?q=ai+product+photography",
            "source_type": "news_search",
            "trusted_domains": ["adobe.com", "photoroom.com"],
            "primary_domains": ["adobe.com", "photoroom.com"],
        }
        rejected = self.review(
            "Product Photography",
            "Startup launches AI product photography workflow",
            "The new generative AI product photography workflow creates catalog images for ecommerce operators.",
            source=source,
            url="https://issuewire.com/startup-ai-product-photography",
        )
        accepted = self.review(
            "Product Photography",
            "Adobe launches AI product photography workflow",
            "Adobe introduced a generative AI product photography workflow for creating ecommerce catalog images.",
            source=source,
            url="https://blog.adobe.com/en/publish/ai-product-photography",
        )

        self.assertFalse(rejected[0])
        self.assertEqual(rejected[2], "untrusted news-search publisher")
        self.assertTrue(accepted[0], accepted[2])

        reviews: list[dict] = []
        review_id = composer.append_candidate_review(
            reviews,
            lens="genny",
            vertical="Product Photography",
            source=source,
            title="Adobe launches AI product photography workflow",
            summary="Adobe introduced a generative AI product photography workflow for creating ecommerce catalog images.",
            url="https://blog.adobe.com/en/publish/ai-product-photography",
            date=self.today,
            status="published",
            score=8,
            reason="publishable",
            source_name="Adobe",
        )
        self.assertTrue(review_id)
        self.assertEqual(reviews[0]["confidence"], "primary-source")
        self.assertTrue(reviews[0]["authoritative"])

    def test_verified_ai_production_changes_remain_publishable(self) -> None:
        cases = [
            (
                "AI Filmmaking",
                "Foundry releases SmartRoto for Nuke",
                "SmartRoto adds an AI-assisted VFX rotoscoping workflow so film teams can isolate moving subjects faster.",
            ),
            (
                "Digital Humans",
                "Reallusion launches Headshot 3.1",
                "Headshot 3.1 adds AI-assisted facial generation and digital-human character controls for iClone artists.",
            ),
            (
                "AI Design / Motion Graphics",
                "Runway introduces Aleph 2.0 in Figma Weave",
                "Aleph adds generative AI frame editing and video design controls directly inside the Figma Weave workflow.",
            ),
            (
                "Music Production / Audio",
                "Music labels announce AI-generated song labeling rules",
                "The new labeling policy requires music services to disclose synthetic and generative AI tracks to listeners.",
            ),
        ]

        for vertical, title, summary in cases:
            with self.subTest(vertical=vertical):
                accepted, score, reason = self.review(vertical, title, summary)
                self.assertTrue(accepted, reason)
                self.assertGreaterEqual(score, 5)

    def test_analysis_and_event_promos_do_not_become_change_signals(self) -> None:
        fashion_analysis = self.review(
            "Fashion / Apparel / Textile",
            "A Label Is More Than Just a Carrier for Language",
            "Fashion regulators are scrutinizing sustainability and AI disclosure claims, raising questions about future labeling.",
        )
        conference_promo = self.review(
            "Digital Humans",
            "Reallusion at SIGGRAPH 2026 with HP and NVIDIA RTX",
            "Join Reallusion at its booth to see AI Studio, AccuFACE, digital-human animation, and creator demonstrations.",
        )

        self.assertFalse(fashion_analysis[0])
        self.assertEqual(fashion_analysis[2], "missing concrete AI-production ecosystem change")
        self.assertFalse(conference_promo[0])
        self.assertEqual(conference_promo[2], "event promotion without title-level product change")

    def test_recommendation_classifier_ignores_page_chrome_pricing_and_briefs_labeling(self) -> None:
        runway = ledger.decision_enrichment(
            status="published",
            title="Runway introduces Aleph 2.0 in Figma Weave",
            summary="Enterprise Pricing. Aleph adds generative AI frame editing to the design workflow.",
            verticals=["AI Design / Motion Graphics"],
        )
        labeling = ledger.decision_enrichment(
            status="published",
            title="Music labels announce AI-generated song labeling rules",
            summary="Platforms must disclose synthetic tracks to listeners.",
            verticals=["Music Production / Audio"],
        )
        pricing = ledger.decision_enrichment(
            status="published",
            title="Shopify updates duties-inclusive pricing strategy",
            summary="Managed Markets changes international merchant pricing.",
            verticals=["Commerce / Conversion"],
        )

        self.assertEqual(runway["recommended_action"], "test")
        self.assertEqual(labeling["recommended_action"], "brief")
        self.assertEqual(pricing["recommended_action"], "budget")

        lawsuit = ledger.decision_enrichment(
            status="published",
            title="Suno faces AI training copyright lawsuit",
            summary="A production music firm filed the legal action over model training data.",
            verticals=["Music Production / Audio"],
        )
        self.assertEqual(lawsuit["recommended_action"], "brief")


if __name__ == "__main__":
    unittest.main()
