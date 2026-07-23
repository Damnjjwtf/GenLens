#!/usr/bin/env python3
"""Compose a GenLens briefing Markdown file from the source registry.

This is deliberately mechanical: it gathers source-backed RSS items, groups them
by vertical, and writes a briefing file that the Resend template can render.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import ssl
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import genlens_signal_ledger as signal_ledger

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATH = Path(os.environ.get("GENLENS_SOURCE_PATH", "/root/.hermes/profiles/genny/data/genny_sources.json"))
if not SOURCE_PATH.exists():
    SOURCE_PATH = BASE_DIR / "data" / "genny_sources.json"
MARTI_SOURCE_PATH = Path(os.environ.get("MARTI_SOURCE_PATH", "/root/.hermes/profiles/genny/data/marti_sources.json"))
if not MARTI_SOURCE_PATH.exists():
    MARTI_SOURCE_PATH = BASE_DIR / "data" / "marti_sources.json"
OUT_PATH = Path(os.environ.get("GENLENS_BRIEF_OUT", "/root/.hermes/profiles/genny/state/latest_brief.md"))
ROLE_SIGNALS_PATH = Path(os.environ.get("GENLENS_ROLE_SIGNALS_PATH", "/root/.hermes/profiles/genny/data/role_signals.json"))
if not ROLE_SIGNALS_PATH.exists():
    ROLE_SIGNALS_PATH = BASE_DIR / "data" / "role_signals.json"

PHASE_1_VERTICALS = [
    "Product Photography",
    "AI Filmmaking",
    "Digital Humans",
]

PHASE_2_VERTICALS = [
    "Music Production / Audio",
    "AI Design / Motion Graphics",
    "Fashion / Apparel / Textile",
]

PHASE_3_VERTICALS = [
    "Advertising / Brand Content",
    "ArchViz",
    "Podcast / Long-Form Audio",
    "Education / E-Learning Content",
    "Social / Short-Form Video",
    "Game Development / Real-Time 3D",
]

ACTIVE_VERTICALS = PHASE_1_VERTICALS
EXPANDED_VERTICALS = PHASE_1_VERTICALS + PHASE_2_VERTICALS + PHASE_3_VERTICALS + [
    "Cross-Vertical Watchlist",
]

MARTI_PHASE_1_LAYERS = [
    "Agentic Marketing Workflows",
    "Paid Media / Creative Performance",
    "Stack Consolidation / Displacement",
]

MARTI_PHASE_2_LAYERS = [
    "Lifecycle / Retention",
    "Measurement / Attribution",
    "Commerce / Conversion",
]

MARTI_PHASE_3_LAYERS = [
    "SEO / AEO / Content Systems",
    "Sales / Marketing Convergence",
    "Marketing Data / Identity",
]

MARTI_ACTIVE_LAYERS = MARTI_PHASE_1_LAYERS
MARTI_EXPANDED_LAYERS = MARTI_PHASE_1_LAYERS + MARTI_PHASE_2_LAYERS + MARTI_PHASE_3_LAYERS

PHASE_BY_VERTICAL = {
    **{vertical: "Phase 1 - Active Core" for vertical in PHASE_1_VERTICALS},
    **{vertical: "Phase 2 - Deferred / On Deck" for vertical in PHASE_2_VERTICALS},
    **{vertical: "Phase 3 - Candidate Watch" for vertical in PHASE_3_VERTICALS},
    "Cross-Vertical Watchlist": "Cross-Vertical Watchlist",
}

MARTI_PHASE_BY_LAYER = {
    **{layer: "Marti Phase 1 - Active Core" for layer in MARTI_PHASE_1_LAYERS},
    **{layer: "Marti Phase 2 - Deferred / On Deck" for layer in MARTI_PHASE_2_LAYERS},
    **{layer: "Marti Phase 3 - Candidate Watch" for layer in MARTI_PHASE_3_LAYERS},
}

NOISE_PATTERNS = re.compile(
    r"\b(quote of the day|read before posting|potential students|wishlist|giveaway|rumor thread|cloud gaming|signed synths|skip to (?:main )?content|customer stories|case studies|all posts|all articles)\b",
    re.I,
)

GLOBAL_SIGNAL_TERMS = {
    "ai", "generative", "synthetic", "automation", "workflow", "pipeline", "model",
    "render", "rendering", "vfx", "virtual production", "3d", "mocap", "avatar",
    "video", "image", "design", "production", "studio", "tool", "platform",
    "cost", "time", "faster", "launch", "release", "beta", "marketing",
    "campaign", "ads", "advertising", "agent", "orchestration", "automation",
    "attribution", "analytics", "conversion", "commerce", "crm", "lifecycle",
    "retention", "audience", "measurement", "api", "integration", "pricing",
}

VERTICAL_SIGNAL_TERMS = {
    "Product Photography": {"product", "ecommerce", "background", "lighting", "retouch", "commerce", "catalog", "presale"},
    "AI Filmmaking": {"film", "vfx", "cinematic", "video", "virtual production", "compositing", "camera", "lighting"},
    "Digital Humans": {"avatar", "voice", "character", "human", "mocap", "animation", "lip", "speech", "robotics"},
    "Advertising / Brand Content": {"brand", "campaign", "creative", "asset", "content", "agency", "experiential", "marketing"},
    "ArchViz": {"archviz", "architectural visualization", "render", "visualization", "real-time", "3d", "vray", "corona", "enscape"},
    "AI Design / Motion Graphics": {"motion", "design", "animation", "figma", "interactive", "prototype", "creative studio"},
    "Music Production / Audio": {"audio", "music", "sound", "plugin", "mix", "master", "stem", "voice", "synth"},
    "Fashion / Apparel / Textile": {"fashion", "apparel", "garment", "textile", "3d", "sustainability", "planning", "sample"},
    "Podcast / Long-Form Audio": {"podcast", "audio", "transcript", "voice", "editing", "show notes", "riverside", "descript"},
    "Education / E-Learning Content": {"learning", "training", "education", "course", "instructional", "l&d", "avatar", "localization"},
    "Social / Short-Form Video": {"social", "short-form", "tiktok", "reels", "clips", "creator", "template", "capcut"},
    "Game Development / Real-Time 3D": {"game", "unreal", "unity", "godot", "real-time", "npc", "procedural", "asset"},
    "Cross-Vertical Watchlist": {"video", "image", "model", "local", "workflow", "agent", "benchmark", "release", "generation"},
    "Agentic Marketing Workflows": {"agent", "automation", "orchestration", "workflow", "n8n", "zapier", "campaign", "marketing ops"},
    "Paid Media / Creative Performance": {"ads", "advertising", "campaign", "creative", "roas", "cac", "cpm", "bidding", "performance max", "advantage+"},
    "Stack Consolidation / Displacement": {"pricing", "acquisition", "sunset", "migration", "consolidation", "open source", "integration", "replacement"},
    "Lifecycle / Retention": {"email", "sms", "push", "lifecycle", "retention", "crm", "journey", "segmentation"},
    "Measurement / Attribution": {"attribution", "analytics", "incrementality", "measurement", "conversion", "mmm", "reporting"},
    "Commerce / Conversion": {"commerce", "shopify", "checkout", "merchandising", "conversion", "storefront", "personalization"},
    "SEO / AEO / Content Systems": {"seo", "aeo", "answer engine", "citation", "search", "structured data", "content system"},
    "Sales / Marketing Convergence": {"gtm", "revops", "outbound", "sales", "crm", "sequencing", "pipeline"},
    "Marketing Data / Identity": {"cdp", "identity", "warehouse", "reverse etl", "consent", "first-party data", "clean room"},
}

SKIP_URL_PATTERNS = re.compile(
    r"(privacy|terms|login|signup|subscribe|contact|about|careers|cookie|facebook|instagram|linkedin|twitter|x\.com|youtube)",
    re.I,
)

DISCOVERY_SOURCE_PATTERNS = re.compile(
    r"(/blog/?|/news/?|/learn/?|/insights/?|/resources/?|/magazine/?|/articles?/?|/research/?|/paper|arxiv\.org|github\.com/.+/(releases|commits|pulls)|feed|rss)",
    re.I,
)

BRIEFABLE_URL_PATTERNS = re.compile(
    r"(/blog/|/inside-photoroom/|/news/|/news/stories/|/learn/|/insights/|/resources/|/magazine/|/articles?/|/posts/|/products/ads-commerce/|/research/|/case-stud|/customer-stor|/press|/release|/announc|/update|/changelog|/paper|arxiv\.org/abs/|github\.com/.+/(releases|commits|pulls)|/20\d{2}/)",
    re.I,
)

LANDING_PAGE_PATTERNS = re.compile(
    r"(^/$|/pricing/?$|/features?/?$|/solutions?/?$|/customers?/?$|/tools?/?$|/product/?$|/products/?$|/platform/?$|/templates?/?$|/use-cases?/?$|/ai-[a-z-]+/?$|/realtime/?$|/background-remover/?$|/image-generator/?$)",
    re.I,
)

NEWS_TITLE_PATTERNS = re.compile(
    r"\b(announc|launch|release|update|introduc|acquir|raises?|funding|study|report|research|case study|workflow|benchmarks?|pricing|license|policy|rights|compliance|production|pipeline|integrat|ships?|available|deprecat|sunset|shut(?:ting)? down|beta|sdk|api|v\d+(?:\.\d+)*)\b",
    re.I,
)

HIGH_VALUE_SIGNAL_PATTERNS = re.compile(
    r"\b(announc|launch|release|update|introduc|acquir|raises?|funding|study|report|research|case study|customer story|benchmark|pricing|license|policy|rights|compliance|deprecat|sunset|shut(?:ting)? down|sdk|api|integration|open source|generally available|now (?:available|supports?|lets?|allows?|requires?|uses?|includes?)|can now|must now|will now|beta|v\d+(?:\.\d+)*)\b",
    re.I,
)

MARTI_CHANGE_PATTERNS = re.compile(
    r"\b(announc(?:e[ds]?|ing)?|launch(?:es|ed|ing)?|releas(?:e[ds]?|ing)?|updat(?:e[ds]?|ing)|introduc(?:e[ds]?|ing)|add(?:s|ed|ing)?|acquir(?:e[ds]?|ing)?|pricing change|policy change|deprecat(?:e[ds]?|ing)?|sunset|shut(?:ting)? down|migration|sdk|api|integration|open source|generally available|available globally|roll(?:s|ed|ing) out|new (?:feature|report|control|capability|integration|tool|panel)|now (?:available|supports?|lets?|allows?|requires?|uses?|includes?)|can now|must now|will now|beta|v\d+(?:\.\d+)*)\b",
    re.I,
)

MARTI_OUTCOME_PATTERNS = re.compile(
    r"\b(case study|customer story|roi|roas|cac|conversion|retention|reduc(?:e|ed|tion)|increas(?:e|ed)|lift|sav(?:e|ed|ings)|improv(?:e|ed|ement))\b",
    re.I,
)

NUMERIC_EVIDENCE_PATTERNS = re.compile(
    r"(?:\$\s?\d|\b\d+(?:\.\d+)?\s?(?:%|x|hours?|days?|weeks?|months?)\b)",
    re.I,
)

LOW_VALUE_TITLE_PATTERNS = re.compile(
    r"\b(best|top|what is|how to|how i (?:built|made|created)|guide to|ultimate guide|walkthrough|tutorial|step-by-step|"
    r"building (?:a|an|the)|tips|examples|template|guide|category|all articles|learn more|resources|use cases|customer stories|"
    r"case studies|compare|vs\.?|which .* fits|make money|start a podcast|embed a video|gaming headphones|signed synths?|"
    r"supersaw sound|record cutting)\b",
    re.I,
)

STATIC_COMPARISON_TITLE_PATTERNS = re.compile(
    r"\bcapabilities\s*(?:and|&)\s*limitations\b",
    re.I,
)

WEAK_SOURCE_PATTERNS = re.compile(
    r"\b(quasa|bitcoin world|startup story|startup fortune|digital terminal|gigazine|futurum\s*group|ein\s*news|einpresswire|mezha)\b",
    re.I,
)

FALSE_POSITIVE_PATTERNS = re.compile(
    r"\b(project runway|new episodes air|drops trailer|recurring judge|free minutes|free trial|free for \d+ days?|percent off|% off|coupon|promo code|pricing explained|free plan features|\d+\s+tools that automate|tools that automate your creative workflow|we(?:'|’)re going to|conference schedule|register for (?:the )?event)\b",
    re.I,
)

CATEGORY_URL_PATTERNS = re.compile(
    r"(/category/|/tag/|/topics?/|/collections?/|/blog/?(?:#.*)?$|/news/?(?:#.*)?$|/learn/?(?:#.*)?$|/resources/?(?:#.*)?$)",
    re.I,
)

YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
TITLE_DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(20\d{2})\b",
    re.I,
)
ARTICLE_READS_PER_SOURCE = 1
RSS_ARTICLE_READS_PER_SOURCE = 4
SITEMAP_ARTICLE_READS_PER_SOURCE = int(os.environ.get("GENLENS_SITEMAP_ARTICLE_READS", "8"))
MAX_ITEM_AGE_DAYS = int(os.environ.get("GENLENS_MAX_ITEM_AGE_DAYS", "45"))
# Outer eligibility cap (MAX_ITEM_AGE_DAYS) stays generous so still-relevant
# multi-week signals (acquisitions, rulings) are not dropped. FRESH_DAYS is the
# softer "this week" tier used only for the relative-age label shown on cards.
FRESH_WINDOW_DAYS = int(os.environ.get("GENLENS_FRESH_DAYS", "7"))
MAX_PER_SOURCE = int(os.environ.get("GENLENS_MAX_PER_SOURCE", "2"))
MAX_PER_DOMAIN = int(os.environ.get("GENLENS_MAX_PER_DOMAIN", "2"))
MAX_PER_TOPIC_CLUSTER = int(os.environ.get("GENLENS_MAX_PER_TOPIC_CLUSTER", "1"))
GOOGLE_NEWS_BATCH_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"

MARTI_REQUIRED_PATTERNS = {
    "Agentic Marketing Workflows": re.compile(r"(?=.*\b(agent|automation|orchestration|workflow|mcp)\b)(?=.*\b(marketing|campaign|ads?|crm|sales|content|commerce|growth)\b)", re.I),
    "Paid Media / Creative Performance": re.compile(r"\b(ads?|advertising|campaign|creative performance|roas|cac|cpm|bidding|performance max|advantage\+|marketer)\b", re.I),
    "Stack Consolidation / Displacement": re.compile(r"\b(pricing change|acquisition|sunset|shut(?:ting)? down|migration|consolidation|replacement|open source|marketing automation|cdp|analytics platform|stack)\b", re.I),
    "Lifecycle / Retention": re.compile(r"\b(lifecycle|retention|email|sms|push notification|journey|segmentation|loyalty|marketing cloud|customer engagement)\b", re.I),
    "Measurement / Attribution": re.compile(r"\b(attribution|incrementality|measurement|marketing mix|conversion tracking|experiments?|campaign analytics|roas|cac)\b", re.I),
    "Commerce / Conversion": re.compile(r"\b(commerce|shopify|checkout|merchant|merchandising|storefront|conversion|shopping|retail)\b", re.I),
    "SEO / AEO / Content Systems": re.compile(r"\b(seo|aeo|answer engine|search console|google search|structured data|citation|zero-click|content system)\b", re.I),
    "Sales / Marketing Convergence": re.compile(r"\b(gtm|revops|outbound|sales hub|marketing hub|sales and marketing|crm pipeline|lead routing|sequencing)\b", re.I),
    "Marketing Data / Identity": re.compile(r"\b(cdp|customer data|identity resolution|reverse etl|consent|first-party data|clean room|marketing data|warehouse-native)\b", re.I),
}

# Genny is a production-intelligence lens, not a broad creative-technology news
# feed. A publishable item must name the affected production workflow, an AI
# mechanism (or a known AI-production product), and a concrete ecosystem event.
# Keeping these contracts separate from VERTICAL_SIGNAL_TERMS prevents a high
# keyword score from promoting generic renderer, engine, or infrastructure news.
GENNY_REQUIRED_PATTERNS = {
    "Product Photography": re.compile(r"\b(product (?:photo(?:graphy|s?)|imag(?:e|es|ery))|e-?commerce imag(?:e|es|ery)|catalog|packshot|retouch(?:ing)?|background remov(?:al|er)|virtual try-on|merchandising)\b", re.I),
    "AI Filmmaking": re.compile(r"\b(film(?:making)?|video|vfx|roto(?:scop(?:e|ing))?|composit(?:e|ing)|footage|shot|storyboard|cinematic|post-production|virtual production|lionsgate|netflix|runway)\b", re.I),
    "Digital Humans": re.compile(r"\b(digital humans?|avatars?|headshots?|facial?|faces?|lip[ -]?sync|voices?|dubbing|synthetic presenters?|characters?|mocap|motion capture|accuface|iclone|reallusion|elevenlabs|synthesia|heygen)\b", re.I),
    "Music Production / Audio": re.compile(r"\b(music|audio|songs?|tracks?|vocals?|voices?|sound|stems?|mix(?:ing)?|master(?:ing)?|music labels?|suno|udio)\b", re.I),
    "AI Design / Motion Graphics": re.compile(r"\b(design|motion graphics?|animation|figma|weave|frames?|creative canvas|prototype|storyboard)\b", re.I),
    "Fashion / Apparel / Textile": re.compile(r"\b(fashion|apparel|textile|garments?|clothing|virtual models?|digital samples?|try-on)\b", re.I),
    "Advertising / Brand Content": re.compile(r"\b(advertis(?:ing|ements?)|ads?|brand content|campaign creative|creative assets?|commercials?|agency production)\b", re.I),
    "ArchViz": re.compile(r"\b(archviz|architectural visuali[sz]ation|architecture render(?:ing)?|building visuali[sz]ation|interior visuali[sz]ation|enscape|twinmotion)\b", re.I),
    "Podcast / Long-Form Audio": re.compile(r"\b(podcasts?|long-form audio|episodes?|show notes|transcripts?|descript|riverside)\b", re.I),
    "Education / E-Learning Content": re.compile(r"\b(e-?learning|education(?:al)? content|training (?:videos?|content)|course (?:content|authoring)|instructional design|workplace training|learning and development|l&d|locali[sz]ed training|ai tutor|rise|storyline)\b", re.I),
    "Social / Short-Form Video": re.compile(r"\b(social video|short-form|tiktok|reels?|shorts?|creator video|capcut|meta edits|instagram edits)\b", re.I),
    "Game Development / Real-Time 3D": re.compile(r"\b(game development|games?|unity|unreal|godot|real-time 3d|npcs?|procedural game|game assets?)\b", re.I),
    "Cross-Vertical Watchlist": re.compile(r"\b(creative production|production workflow|content production|generative video|generative image|vfx|animation|design workflow|audio production|3d production|creator workflow)\b", re.I),
}

GENNY_AI_MECHANISM_PATTERNS = re.compile(
    r"\b(ai|artificial intelligence|generative|synthetic media|machine learning|neural|diffusion|foundation model|"
    r"text-to-(?:image|video|audio|3d)|image-to-video|video generation|image generation|voice clon(?:e|ing)|"
    r"runway|aleph|smartroto|headshot|accuface|elevenlabs|synthesia|heygen|suno|udio|midjourney|"
    r"stable diffusion|flux|firefly|sora|veo|kling|luma|pika|gemini|copilot)\b",
    re.I,
)

# An AI agent controlling an engine is automation, but it is not automatically
# generative-content production. Game signals must describe the creation or
# editing of a game-production artifact such as an asset, level, scene, NPC, or
# gameplay system.
GAME_GENERATIVE_PRODUCTION_PATTERNS = re.compile(
    r"\b(generative|text-to-(?:3d|image)|image-to-3d|ai-generated|"
    r"ai (?:npcs?|characters?|assets?|props?|objects?|levels?|scenes?|gameplay|worlds?|ui|interfaces?)|"
    r"(?:3d object|ui|sprite|texture) generator|"
    r"(?:game|3d) (?:assets?|characters?|levels?|scenes?).{0,60}\bai\b|"
    r"\bai\b.{0,60}(?:game assets?|npcs?|level design|scene generation|procedural content|gameplay)|"
    r"ai agents?.{0,24}(?:can |to )?(?:create|build|generate|edit).{0,60}(?:games?|scenes?|assets?|props?|levels?|npcs?))\b",
    re.I,
)

GENNY_EVENT_PATTERNS = re.compile(
    r"\b(announc(?:e[ds]?|ing)?|launch(?:es|ed|ing)?|releas(?:e[ds]?|ing)?|updat(?:e[ds]?|ing)|"
    r"introduc(?:e[ds]?|ing)|add(?:s|ed|ing)?|acquir(?:e[ds]?|ing)?|invest(?:s|ed|ing|ment)?|"
    r"ship(?:s|ped|ping)?|"
    r"partnership|partners? with|equity stake|funding|raises?|sues?|lawsuit|settlement|"
    r"policy change|(?:new|updated?) (?:disclosure|licensing|rights|consent) (?:rule|requirement|policy|program)|"
    r"deprecat(?:e[ds]?|ing)?|sunset|"
    r"shut(?:ting)? down|migration|sdk|api|integration|open source|generally available|available globally|"
    r"roll(?:s|ed|ing) out|new (?:ai|generative|feature|model|tool|capability|integration|workflow)|"
    r"now (?:available|supports?|lets?|allows?|requires?|uses?|includes?)|now (?:you|teams?|creators?|users?) can|can now|must now|will now|"
    r"beta|v\d+(?:\.\d+)*)\b",
    re.I,
)

UNCONFIRMED_SIGNAL_PATTERNS = re.compile(
    r"\b(?:has|have|had) not confirmed\b|\bhaven['’]t confirmed\b|\bnot (?:yet )?confirmed\b|"
    r"\bneither .{0,80}\bconfirmed\b|\bno confirmation (?:from|by)\b",
    re.I,
)

NEGATED_AI_SIGNAL_PATTERNS = re.compile(
    r"\bnot (?:a conversation )?about .{0,100}\b(?:ai|artificial intelligence|generative|tools?|pipelines?)\b|"
    r"\b(?:ai|artificial intelligence|generative|tools?|pipelines?) (?:was|were|is|are) not (?:the )?(?:focus|subject|topic)\b",
    re.I,
)

EVENT_PROMO_TITLE_PATTERNS = re.compile(
    r"\b(?:at|heads? to|heading to|join(?:s|ing)? us at)\s+(?:siggraph|nab|ces|ibc|gdc)\b|"
    r"\b(?:siggraph|nab|ces|ibc|gdc)\s+20\d{2}\b",
    re.I,
)

ROUNDUP_SIGNAL_PATTERNS = re.compile(
    r"\b(?:daily|weekly) (?:show|roundup|round-up|digest)\b|\bthis week(?:'s)? (?:roundup|news)\b",
    re.I,
)

TITLE_LEVEL_PRODUCT_CHANGE_PATTERNS = re.compile(
    r"\b(announc|launch|release|introduc|adds?|updates?|acquir|partnership|equity stake|lawsuit|"
    r"new (?:ai|generative|feature|model|tool|capability)|v\d+(?:\.\d+)*)\b",
    re.I,
)


def has_marti_event_evidence(text: str) -> bool:
    if MARTI_CHANGE_PATTERNS.search(text):
        return True
    return bool(MARTI_OUTCOME_PATTERNS.search(text) and NUMERIC_EVIDENCE_PATTERNS.search(text))


def has_genny_event_evidence(text: str) -> bool:
    return bool(GENNY_EVENT_PATTERNS.search(text))


def required_pattern_for_vertical(vertical: str) -> re.Pattern[str] | None:
    return MARTI_REQUIRED_PATTERNS.get(vertical) or GENNY_REQUIRED_PATTERNS.get(vertical)


def verified_ssl_context() -> ssl.SSLContext:
    explicit_bundle = os.environ.get("GENLENS_CA_BUNDLE", "").strip()
    if explicit_bundle:
        return ssl.create_default_context(cafile=explicit_bundle)
    try:
        import certifi  # type: ignore[import-not-found]
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def source_path_for_lens(lens: str) -> Path:
    return MARTI_SOURCE_PATH if lens == "marti" else SOURCE_PATH


def load_sources(lens: str = "genny") -> dict[str, Any]:
    return json.loads(source_path_for_lens(lens).read_text())


def strip_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    for _ in range(3):
        decoded = html.unescape(value)
        if decoded == value:
            break
        value = decoded
    return re.sub(r"\s+", " ", value).strip()


def clean_excerpt(value: str) -> str:
    text = strip_text(value)
    if re.search(r"\b[\w-]+\.\.\.$", text):
        prefix = text[:-3].rstrip()
        sentence_end = max(prefix.rfind(". "), prefix.rfind("! "), prefix.rfind("? "))
        if sentence_end >= 40:
            return prefix[:sentence_end + 1]
        return re.sub(r"\s+\S+$", "", prefix).rstrip(" ,;:-") + "…"
    return text


def truncate_text(value: str, limit: int) -> str:
    text = clean_excerpt(value)
    if len(text) <= limit:
        return text
    clipped = text[:limit + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return clipped + "…"


def parse_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            return parsed.date().isoformat()
    except Exception:
        pass
    return strip_text(value)[:24]


def parsed_iso_date(value: str) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except Exception:
        return None


def relative_age(value: str, today: dt.date | None = None) -> str:
    """Human-readable freshness label for a card date.

    Returns 'date unverified' when no date parses, so undated items are flagged
    rather than silently presented as current.
    """
    parsed = parsed_iso_date(value)
    if not parsed:
        return "date unverified"
    today = today or dt.datetime.now(dt.timezone.utc).date()
    age = (today - parsed).days
    if age < 0:
        return parsed.isoformat()
    if age == 0:
        return "today"
    if age == 1:
        return "1d ago"
    if age < 7:
        return f"{age}d ago"
    if age < 30:
        return f"{age // 7}w ago"
    return f"{age // 30}mo ago"


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(node):
        local = child.tag.split("}", 1)[-1].lower()
        if local in names:
            return strip_text(child.text)
    return ""


def child_link(node: ET.Element) -> str:
    for child in list(node):
        local = child.tag.split("}", 1)[-1].lower()
        if local == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def child_source(node: ET.Element) -> tuple[str, str]:
    for child in list(node):
        if child.tag.split("}", 1)[-1].lower() == "source":
            return strip_text(child.text), child.attrib.get("url", "").strip()
    return "", ""


def is_google_news_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return source_domain(url) == "news.google.com" and "/rss/articles/" in parsed.path


def clean_google_news_title(title: str, publisher: str = "") -> str:
    cleaned = strip_text(title)
    if publisher:
        cleaned = re.sub(rf"\s+-\s+{re.escape(publisher)}\s*$", "", cleaned, flags=re.I)
    return cleaned.strip()


def clean_google_news_summary(summary: str, title: str, publisher: str = "") -> str:
    cleaned = strip_text(summary)
    if publisher:
        cleaned = re.sub(rf"\s+{re.escape(publisher)}\s*$", "", cleaned, flags=re.I)
    cleaned = cleaned.strip()
    title_key = canonical_title(title)
    summary_key = canonical_title(cleaned)
    if title_key and (summary_key == title_key or cleaned.lower().startswith(title.lower())):
        return ""
    return cleaned


def parse_google_news_batch_response(body: str) -> str:
    def find_url(value: Any) -> str:
        if isinstance(value, list):
            if len(value) >= 3 and value[0] == "wrb.fr" and value[1] == "Fbv4je":
                try:
                    result = json.loads(value[2])
                except (TypeError, json.JSONDecodeError):
                    result = None
                if isinstance(result, list) and len(result) > 1:
                    candidate = str(result[1])
                    if urllib.parse.urlparse(candidate).scheme in {"http", "https"}:
                        return candidate
            for child in value:
                found = find_url(child)
                if found:
                    return found
        return ""

    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("["):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        found = find_url(payload)
        if found:
            return found
    return ""


def resolve_google_news_url(url: str, expected_source_url: str = "") -> str:
    """Resolve a Google News RSS wrapper to its original publisher URL.

    Google does not expose the canonical article URL in the RSS item. Its article
    wrapper provides a short-lived signature used by the same batch endpoint as
    the Google News web client. Any failure returns the original wrapper URL so a
    feed outage cannot stop the briefing.
    """
    if not is_google_news_url(url):
        return url
    article_id = urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1]
    if not article_id:
        return url
    locale_url = url + ("&" if "?" in url else "?") + "hl=en-US&gl=US&ceid=US:en"
    ctx = verified_ssl_context()
    try:
        req = urllib.request.Request(locale_url, headers={"User-Agent": "GennySourceReviewer/1.0"})
        with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
            wrapper = response.read(1_500_000).decode("utf-8", "replace")
        signature_match = re.search(r'data-n-a-sg=["\']([^"\']+)', wrapper)
        timestamp_match = re.search(r'data-n-a-ts=["\'](\d+)', wrapper)
        if not signature_match or not timestamp_match:
            return url
        request_value = [
            "garturlreq",
            [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1], "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
            article_id,
            int(timestamp_match.group(1)),
            signature_match.group(1),
        ]
        rpc = ["Fbv4je", json.dumps(request_value, separators=(",", ":"))]
        form = urllib.parse.urlencode({"f.req": json.dumps([[rpc]], separators=(",", ":"))}).encode()
        batch_req = urllib.request.Request(
            GOOGLE_NEWS_BATCH_URL,
            data=form,
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": "GennySourceReviewer/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(batch_req, timeout=6, context=ctx) as response:
            resolved = parse_google_news_batch_response(response.read(1_000_000).decode("utf-8", "replace"))
    except Exception:
        return url
    if not resolved or is_google_news_url(resolved):
        return url
    if expected_source_url:
        expected_domain = source_domain(expected_source_url)
        resolved_domain = source_domain(resolved)
        if expected_domain and not (
            resolved_domain == expected_domain or resolved_domain.endswith("." + expected_domain)
        ):
            return url
    return resolved


def normalized_path(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return parsed.path.rstrip("/") + ("/" if parsed.path.endswith("/") else "")


def is_discovery_source(source: dict[str, Any]) -> bool:
    """Whether a manual source page is worth crawling for article links."""
    url = source.get("url", "")
    if source.get("rss") or source.get("sitemap"):
        return True
    if source.get("source_type") in {"news", "blog", "research", "publication", "release_notes"}:
        return True
    return bool(DISCOVERY_SOURCE_PATTERNS.search(url))


def is_briefable_url(url: str) -> bool:
    if not url or SKIP_URL_PATTERNS.search(url):
        return False
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if LANDING_PAGE_PATTERNS.search(path):
        return False
    if CATEGORY_URL_PATTERNS.search(path):
        return False
    return bool(BRIEFABLE_URL_PATTERNS.search(url))


def likely_recent(title: str, date: str = "") -> bool:
    current_year = dt.datetime.now(dt.timezone.utc).year
    parsed = parsed_iso_date(date)
    if not parsed:
        title_date = TITLE_DATE_PATTERN.search(title or "")
        if title_date:
            try:
                parsed = dt.datetime.strptime(" ".join(title_date.groups()), "%B %d %Y").date()
            except Exception:
                parsed = None
    if parsed:
        age = (dt.datetime.now(dt.timezone.utc).date() - parsed).days
        return age <= MAX_ITEM_AGE_DAYS
    values = [date, title]
    years: list[int] = []
    for value in values:
        years.extend(int(match) for match in YEAR_PATTERN.findall(value or ""))
    if not years:
        return True
    return max(years) >= current_year - 1


def canonical_title(value: str) -> str:
    value = strip_text(value).lower()
    value = re.sub(r"\s+[-|]\s+(?:[^-|\n]{2,50})$", "", value)
    value = re.sub(r"\b(announces?|launches?|releases?|introduces?|raises?|major|new|the|a|an|to|for|with|and|of|in|on|at|by|from)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    words = [word for word in value.split() if len(word) > 2]
    return " ".join(words[:10])


def topic_cluster_key(item: dict[str, str]) -> str:
    title_key = canonical_title(item.get("title", ""))
    if title_key:
        return title_key
    url = item.get("url", "")
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:12]


def source_domain(url: str) -> str:
    if not url:
        return ""
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def domain_matches_any(url: str, domains: list[str]) -> bool:
    domain = source_domain(url)
    normalized = [str(value).lower().removeprefix("www.") for value in domains]
    return bool(domain and any(domain == value or domain.endswith(f".{value}") for value in normalized))


def review_source_type(source: dict[str, Any], url: str) -> str:
    """Classify the evidence publisher, not merely its discovery channel."""
    source_type = str(source.get("source_type") or "unknown")
    if source_type == "official_sitemap":
        return "official_updates"
    if domain_matches_any(url, list(source.get("primary_domains", []))):
        return "official_updates"
    return source_type


def article_metadata_from_html(
    body: str,
    required_pattern: re.Pattern[str] | None = None,
) -> tuple[str, str, str]:
    """Extract title, evidence excerpt, and publication date from an article.

    Modern first-party update pages often expose cleaner evidence in OpenGraph
    or JSON-LD than in their rendered paragraph markup. Keeping this parser pure
    makes the daily sitemap path testable without network access.
    """
    descriptions: list[str] = []
    titles: list[str] = []
    date_values: list[str] = []
    for tag in re.findall(r"<meta\b[^>]*>", body, re.I | re.S):
        attributes = {
            name.lower(): html.unescape(value)
            for name, _quote, value in re.findall(
                r"([:\w-]+)\s*=\s*([\"'])(.*?)\2",
                tag,
                re.I | re.S,
            )
        }
        description_type = str(attributes.get("name") or attributes.get("property") or "").lower()
        content = clean_excerpt(str(attributes.get("content") or ""))
        if description_type in {"description", "og:description", "twitter:description"} and content:
            descriptions.append(content)
        if description_type in {"og:title", "twitter:title"} and content:
            titles.append(content)
        if description_type in {
            "article:published_time",
            "date",
            "datepublished",
            "publishdate",
            "pub_date",
        } and content:
            date_values.append(content)

    for tag in re.findall(r"<time\b[^>]*>", body, re.I | re.S):
        attributes = {
            name.lower(): html.unescape(value)
            for name, _quote, value in re.findall(
                r"([:\w-]+)\s*=\s*([\"'])(.*?)\2",
                tag,
                re.I | re.S,
            )
        }
        datetime_value = clean_excerpt(str(attributes.get("datetime") or ""))
        if datetime_value:
            date_values.append(datetime_value)

    structured_bodies: list[str] = []

    def collect_structured(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                collect_structured(child)
            return
        if not isinstance(value, dict):
            return
        headline = clean_excerpt(str(value.get("headline") or value.get("name") or ""))
        description = clean_excerpt(str(value.get("description") or ""))
        article_body = clean_excerpt(str(value.get("articleBody") or ""))
        published = clean_excerpt(str(value.get("datePublished") or ""))
        if headline:
            titles.append(headline)
        if description:
            descriptions.append(description)
        if article_body:
            structured_bodies.append(article_body)
        if published:
            date_values.append(published)
        for graph_key in ("@graph", "mainEntity", "itemListElement"):
            if graph_key in value:
                collect_structured(value[graph_key])

    structured_scripts = [
        script
        for attributes, script in re.findall(r"<script\b([^>]*)>(.*?)</script>", body, re.I | re.S)
        if re.search(r"\btype\s*=\s*[\"']application/ld\+json[\"']", attributes, re.I)
    ]
    for script in structured_scripts:
        try:
            collect_structured(json.loads(html.unescape(script).strip()))
        except (TypeError, json.JSONDecodeError):
            continue

    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if title_match:
        titles.append(clean_excerpt(title_match.group(1)))

    paragraphs = [clean_excerpt(match.group(1)) for match in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.I | re.S)]
    for article_body in structured_bodies:
        paragraphs.extend(
            sentence
            for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", article_body)
            if 60 <= len(sentence) <= 2_000
        )
    # Large developer portals sometimes wrap their entire navigation tree in a
    # single paragraph-like element. Exclude those blocks so article evidence
    # wins even when the page shell contains release/search vocabulary.
    paragraphs = [p for p in paragraphs if 60 <= len(p) <= 2_000]
    evidence_paragraphs = [p for p in paragraphs if has_marti_event_evidence(p) or has_genny_event_evidence(p)]
    if required_pattern:
        vertical_paragraphs = [p for p in paragraphs if required_pattern.search(p)]
        vertical_ai_paragraphs = [
            p for p in vertical_paragraphs if GENNY_AI_MECHANISM_PATTERNS.search(p)
        ]
        relevant_descriptions = [
            description
            for description in descriptions
            if required_pattern.search(description)
            and (has_marti_event_evidence(description) or has_genny_event_evidence(description))
        ]
        relevant_evidence = [p for p in evidence_paragraphs if required_pattern.search(p)]
        coherent_evidence = [
            p for p in relevant_evidence if GENNY_AI_MECHANISM_PATTERNS.search(p)
        ]
    else:
        vertical_paragraphs = []
        vertical_ai_paragraphs = []
        relevant_descriptions = []
        relevant_evidence = []
        coherent_evidence = []
    # A coherent metadata description is usually cleaner than a page paragraph
    # polluted by navigation, JSON-LD, or pricing/footer chrome. Use it first;
    # fall back to article paragraphs when metadata is generic or absent.
    candidates = (
        relevant_descriptions
        or coherent_evidence
        or relevant_evidence
        or vertical_ai_paragraphs
        or vertical_paragraphs
        or evidence_paragraphs
        or paragraphs
    )
    candidates = sorted(candidates, key=len, reverse=True)
    selected = candidates[:2] or descriptions[:1]
    excerpt_text = " ".join(dict.fromkeys(selected))
    if required_pattern and excerpt_text:
        sentences = [
            clean_excerpt(sentence)
            for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", excerpt_text)
        ]
        relevant_sentences = [sentence for sentence in sentences if required_pattern.search(sentence)]
        if relevant_sentences:
            relevant_sentences.sort(
                key=lambda sentence: (
                    bool(GENNY_AI_MECHANISM_PATTERNS.search(sentence)),
                    has_genny_event_evidence(sentence) or has_marti_event_evidence(sentence),
                    len(sentence),
                ),
                reverse=True,
            )
            focused_sentences: list[str] = []
            for sentence in relevant_sentences[:3]:
                if len(sentence) <= 300:
                    focused_sentences.append(sentence)
                    continue
                match = required_pattern.search(sentence)
                if not match:
                    continue
                start = max(0, match.start() - 130)
                end = min(len(sentence), match.end() + 170)
                if start:
                    start = sentence.find(" ", start) + 1
                if end < len(sentence):
                    boundary = sentence.rfind(" ", start, end)
                    end = boundary if boundary > start else end
                focused = sentence[start:end].strip(" ,;:-")
                focused_sentences.append(("…" if start else "") + focused + ("…" if end < len(sentence) else ""))
            excerpt_text = " ".join(dict.fromkeys(focused_sentences))
        else:
            match = required_pattern.search(excerpt_text)
            if match and len(excerpt_text) > 300:
                start = max(0, match.start() - 130)
                end = min(len(excerpt_text), match.end() + 170)
                if start:
                    start = excerpt_text.find(" ", start) + 1
                if end < len(excerpt_text):
                    boundary = excerpt_text.rfind(" ", start, end)
                    end = boundary if boundary > start else end
                excerpt_text = (
                    ("…" if start else "")
                    + excerpt_text[start:end].strip(" ,;:-")
                    + ("…" if end < len(excerpt_text) else "")
                )
    title = next((value for value in titles if value), "")
    title = re.sub(r"\s+[|–—-]\s+[^|–—-]{2,60}$", "", title).strip()
    date = ""
    for value in date_values:
        match = re.search(r"(?<!\d)(20\d{2}-\d{2}-\d{2})(?!\d)", value)
        if match:
            date = match.group(1)
            break
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                date = dt.datetime.strptime(value.strip(), fmt).date().isoformat()
                break
            except ValueError:
                continue
        if date:
            break
    return title, truncate_text(excerpt_text, 320), date


def fetch_article_metadata(
    url: str,
    required_pattern: re.Pattern[str] | None = None,
) -> tuple[str, str, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GennySourceReviewer/1.0"})
        ctx = verified_ssl_context()
        with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
            ctype = response.headers.get("content-type", "")
            if "html" not in ctype:
                return "", "", ""
            body = response.read(1_200_000).decode("utf-8", "replace")
    except Exception:
        return "", "", ""
    return article_metadata_from_html(body, required_pattern)


def fetch_article_excerpt(url: str, required_pattern: re.Pattern[str] | None = None) -> str:
    return fetch_article_metadata(url, required_pattern)[1]


def quality_review(vertical: str, source: dict[str, Any], title: str, summary: str, url: str, date: str = "") -> tuple[bool, int, str]:
    is_news_search = bool(
        source.get("source_type") == "news_search"
        or is_google_news_url(str(source.get("rss") or ""))
        or "news search" in str(source.get("name") or "").lower()
    )
    if not is_briefable_url(url) and not is_news_search:
        return False, 0, "rejected-url"
    text = f"{title} {summary}"
    source_context = " ".join(
        str(value or "")
        for value in (source.get("name"), source.get("url"), source.get("rss"), url)
    )
    if FALSE_POSITIVE_PATTERNS.search(text):
        return False, 0, "false-positive entertainment/deal/pricing item"
    if WEAK_SOURCE_PATTERNS.search(f"{text} {source_context}"):
        return False, 0, "weak aggregator source"
    if is_news_search:
        trusted_domains = list(source.get("trusted_domains", []))
        if not trusted_domains or not domain_matches_any(url, trusted_domains):
            return False, 0, "untrusted news-search publisher"
    if UNCONFIRMED_SIGNAL_PATTERNS.search(text):
        return False, 0, "unconfirmed product claim"
    if STATIC_COMPARISON_TITLE_PATTERNS.search(title):
        return False, 0, "generic/how-to/category title"
    genny_required = GENNY_REQUIRED_PATTERNS.get(vertical)
    if genny_required:
        if len(strip_text(summary)) < 40:
            return False, 0, "missing substantive source evidence"
        if NEGATED_AI_SIGNAL_PATTERNS.search(text):
            return False, 0, "source explicitly negates an AI production signal"
        if EVENT_PROMO_TITLE_PATTERNS.search(title) and not TITLE_LEVEL_PRODUCT_CHANGE_PATTERNS.search(title):
            return False, 0, "event promotion without title-level product change"
        if ROUNDUP_SIGNAL_PATTERNS.search(text) and not TITLE_LEVEL_PRODUCT_CHANGE_PATTERNS.search(title):
            return False, 0, "multi-item roundup without atomic change"
        if not genny_required.search(text):
            return False, 0, "missing vertical-specific production mechanism"
        if not GENNY_AI_MECHANISM_PATTERNS.search(text):
            return False, 0, "missing explicit generative-AI production mechanism"
        if vertical == "Game Development / Real-Time 3D" and not GAME_GENERATIVE_PRODUCTION_PATTERNS.search(text):
            return False, 0, "missing generative game-production mechanism"
        coherent_genny_evidence = any(
            genny_required.search(field)
            and GENNY_AI_MECHANISM_PATTERNS.search(field)
            and has_genny_event_evidence(field)
            for field in (title, summary)
        )
        if not coherent_genny_evidence and review_source_type(source, url) == "official_updates":
            # A leaf-sitemap article title and its structured excerpt are one
            # first-party evidence unit. Allow the event verb in the headline
            # to pair with the AI production mechanism in the article summary.
            coherent_genny_evidence = bool(
                genny_required.search(text)
                and GENNY_AI_MECHANISM_PATTERNS.search(text)
                and has_genny_event_evidence(text)
            )
        if not coherent_genny_evidence:
            return False, 0, "missing concrete AI-production ecosystem change"
    marti_required = MARTI_REQUIRED_PATTERNS.get(vertical)
    if marti_required and not marti_required.search(text):
        return False, 0, "missing layer-specific marketing mechanism"
    coherent_marti_evidence = bool(
        marti_required
        and (
            (marti_required.search(title) and has_marti_event_evidence(title))
            or (marti_required.search(summary) and has_marti_event_evidence(summary))
        )
    )
    if marti_required and not coherent_marti_evidence:
        return False, 0, "missing concrete change or measured outcome"
    if re.search(r"\b(air force|defense department|military fleet|access control|jita|database internals?|retrieval infrastructure|vectors?)\b", text, re.I) and vertical in MARTI_REQUIRED_PATTERNS:
        return False, 0, "off-layer enterprise or platform infrastructure"
    if source.get("name") == "Motionographer" and not re.search(r"\b(ai|tool|tools|pipeline|workflow|automation|generative)\b", text, re.I):
        return False, 0, "motion/design culture item without AI workflow signal"
    if vertical == "Digital Humans" and re.search(r"\b(music v\d|music generation|music marketplace|tracks)\b", text, re.I) and not re.search(r"\b(avatar|voiceover|dubbing|synthetic presenter|dialogue|speech|voice cloning)\b", text, re.I):
        return False, 0, "off-vertical music item"
    if vertical == "Digital Humans" and re.search(r"\b(geforce now|gaming|nemotron|langchain|open models|icml|agent orchestration|robotics|jetson|edge ai)\b", text, re.I) and not re.search(r"\b(avatar|voice|digital human|synthetic presenter|character|mocap|lip sync|eleven|synthesia|heygen|reallusion|headshot|robotics)\b", text, re.I):
        return False, 0, "off-vertical broad tech item"
    if vertical == "Music Production / Audio" and re.search(r"\b(gaming headphones|record cutting|vinyl cutting|guitar|synth)\b", text, re.I) and not re.search(r"\b(ai|generative|stem|mastering|voice|model|automation|workflow|plugin)\b", text, re.I):
        return False, 0, "off-vertical gear item"
    if vertical == "Agentic Marketing Workflows" and re.search(r"\b(retrieval infrastructure|vectors?|database internals?|storage engine)\b", text, re.I) and not re.search(r"\b(marketing|campaign|crm|operator|workflow automation|marketing ops)\b", text, re.I):
        return False, 0, "platform infrastructure without a marketing-operator workflow"
    required_terms = [str(term).lower() for term in source.get("required_terms", [])]
    if required_terms and not any(term in text.lower() for term in required_terms):
        return False, 0, "missing required source term"
    measured_outcome = bool(MARTI_OUTCOME_PATTERNS.search(text) and NUMERIC_EVIDENCE_PATTERNS.search(text))
    if LOW_VALUE_TITLE_PATTERNS.search(title) and not HIGH_VALUE_SIGNAL_PATTERNS.search(title) and not measured_outcome:
        return False, 0, "generic/how-to/category title"
    if not likely_recent(title, date):
        return False, 0, "stale item"

    score = 0
    if HIGH_VALUE_SIGNAL_PATTERNS.search(text):
        score += 3
    if review_source_type(source, url) in {"official_updates", "release_notes", "github_releases"}:
        score += 3
    if NEWS_TITLE_PATTERNS.search(text):
        score += 1
    score += min(3, relevance_score(vertical, source, title, summary))
    if re.search(r"\b(\d+[%x]?|\$\d+|\d+\s?(?:days?|hours?|minutes?|weeks?|months?))\b", text, re.I):
        score += 1
    if summary and not summary.lower().startswith("qualified source lead"):
        score += 1

    if source.get("priority") == "high":
        score += 1
    passed = score >= 5
    reason = "publishable" if passed else "weak production signal"
    return passed, score, reason


def is_briefable_item(vertical: str, source: dict[str, Any], title: str, summary: str, url: str, date: str = "") -> bool:
    return quality_review(vertical, source, title, summary, url, date)[0]


def append_candidate_review(
    reviews: list[dict[str, Any]] | None,
    *,
    lens: str,
    vertical: str,
    source: dict[str, Any],
    title: str,
    summary: str,
    url: str,
    date: str,
    status: str,
    score: int,
    reason: str,
    source_name: str = "",
) -> str:
    if reviews is None:
        return ""
    review = signal_ledger.make_candidate_review(
        lens=lens,
        vertical=vertical,
        source_name=source_name or str(source.get("name") or "Source"),
        source_url=str(source.get("url") or ""),
        source_type=review_source_type(source, url),
        source_priority=str(source.get("priority") or "medium"),
        title=title,
        summary=summary,
        url=url,
        published_at=date,
        status=status,
        score=score,
        reason=reason,
    )
    for existing in reviews:
        if existing.get("review_id") != review["review_id"]:
            continue
        existing_rank = signal_ledger.STATUS_PRIORITY.get(str(existing.get("status")), -1)
        review_rank = signal_ledger.STATUS_PRIORITY.get(str(review.get("status")), -1)
        if (review_rank, int(review.get("score") or 0)) > (
            existing_rank,
            int(existing.get("score") or 0),
        ):
            existing.update(review)
        return str(existing["review_id"])
    reviews.append(review)
    return str(review["review_id"])


def fetch_rss(
    source: dict[str, Any],
    vertical: str,
    limit: int,
    reviews: list[dict[str, Any]] | None = None,
    lens: str = "genny",
) -> list[dict[str, str]]:
    rss = source.get("rss")
    if not rss:
        return []
    req = urllib.request.Request(rss, headers={"User-Agent": "GennyBriefComposer/1.0"})
    ctx = verified_ssl_context()
    with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
        body = response.read(1_500_000)
    root = ET.fromstring(body)
    nodes = [n for n in root.iter() if n.tag.split("}", 1)[-1].lower() in {"item", "entry"}]
    out: list[dict[str, str]] = []
    article_reads = 0
    for node in nodes[:limit]:
        title = child_text(node, ("title",))
        if not title:
            continue
        summary = child_text(node, ("description", "summary", "content", "encoded"))
        url = child_link(node)
        date = parse_date(child_text(node, ("pubdate", "published", "updated", "date")))
        publisher, publisher_url = child_source(node)
        source_name = publisher or str(source.get("name") or "Source")
        if NOISE_PATTERNS.search(title):
            append_candidate_review(
                reviews,
                lens=lens,
                vertical=vertical,
                source=source,
                title=title,
                summary=summary,
                url=url,
                date=date,
                status="rejected",
                score=0,
                reason="noise title",
                source_name=source_name,
            )
            continue
        if is_google_news_url(url):
            title = clean_google_news_title(title, publisher)
            summary = clean_google_news_summary(summary, title, publisher)
            if not likely_recent(title, date):
                append_candidate_review(
                    reviews,
                    lens=lens,
                    vertical=vertical,
                    source=source,
                    title=title,
                    summary=summary,
                    url=url,
                    date=date,
                    status="rejected",
                    score=0,
                    reason="stale item",
                    source_name=source_name,
                )
                continue
            resolved_url = resolve_google_news_url(url, publisher_url)
            if resolved_url != url:
                url = resolved_url
                summary = fetch_article_excerpt(url, required_pattern_for_vertical(vertical)) or summary
                article_reads += 1
        if (
            vertical in MARTI_REQUIRED_PATTERNS
            and article_reads < RSS_ARTICLE_READS_PER_SOURCE
            and (not summary or not has_marti_event_evidence(f"{title} {summary}"))
        ):
            summary = fetch_article_excerpt(url, MARTI_REQUIRED_PATTERNS.get(vertical)) or summary
            article_reads += 1
        if (
            vertical in GENNY_REQUIRED_PATTERNS
            and article_reads < RSS_ARTICLE_READS_PER_SOURCE
            and (len(strip_text(summary)) < 40 or not has_genny_event_evidence(f"{title} {summary}"))
        ):
            summary = fetch_article_excerpt(url, GENNY_REQUIRED_PATTERNS.get(vertical)) or summary
            article_reads += 1
        if vertical in MARTI_REQUIRED_PATTERNS and not summary:
            continue
        passed, score, reason = quality_review(vertical, source, title, summary, url, date)
        review_id = append_candidate_review(
            reviews,
            lens=lens,
            vertical=vertical,
            source=source,
            title=title,
            summary=summary,
            url=url,
            date=date,
            status="qualified" if passed else "rejected",
            score=score,
            reason=reason,
            source_name=source_name,
        )
        if not passed:
            continue
        if relevance_score(vertical, source, title, summary) <= 0:
            signal_ledger.update_review_status(
                reviews or [],
                review_id,
                "rejected",
                "missing vertical relevance",
            )
            continue
        out.append({
            "title": title,
            "url": url,
            "date": date,
            "summary": truncate_text(summary, 260),
            "source": source_name,
            "priority": source.get("priority", "medium"),
            "score": str(score),
            "review": reason,
            "_review_id": review_id,
        })
        if len(out) >= min(limit, MAX_PER_SOURCE):
            break
    return out


def parse_sitemap_rows(body: bytes, source: dict[str, Any]) -> list[dict[str, str]]:
    """Parse and bound one official URL-set sitemap.

    Registry entries point to leaf URL sets, not sitemap indexes. Every accepted
    URL must stay on the source's own domain and match its explicit path scope.
    """
    root = ET.fromstring(body)
    if root.tag.split("}", 1)[-1].lower() != "urlset":
        raise ValueError("official sitemap must be a leaf urlset")
    source_url = str(source.get("url") or source.get("sitemap") or "")
    source_host = source_domain(source_url)
    include_patterns = [re.compile(str(value), re.I) for value in source.get("include_patterns", [])]
    exclude_patterns = [re.compile(str(value), re.I) for value in source.get("exclude_patterns", [])]
    rows: list[dict[str, str]] = []
    for index, node in enumerate(list(root)):
        fields = {
            child.tag.split("}", 1)[-1].lower(): strip_text(child.text)
            for child in list(node)
        }
        url = fields.get("loc", "")
        if not url or urllib.parse.urlparse(url).scheme not in {"http", "https"}:
            continue
        if source_host and source_domain(url) != source_host:
            continue
        if include_patterns and not any(pattern.search(url) for pattern in include_patterns):
            continue
        if any(pattern.search(url) for pattern in exclude_patterns):
            continue
        rows.append({
            "url": url,
            "date": fields.get("lastmod", "")[:10],
            "_index": str(index),
        })
    return sorted(
        rows,
        key=lambda row: (
            bool(parsed_iso_date(row.get("date", ""))),
            row.get("date", ""),
            int(row.get("_index", "0")),
        ),
        reverse=True,
    )


def fetch_sitemap(
    source: dict[str, Any],
    vertical: str,
    limit: int,
    reviews: list[dict[str, Any]] | None = None,
    lens: str = "genny",
) -> list[dict[str, str]]:
    sitemap = str(source.get("sitemap") or "")
    if not sitemap or source.get("source_type") != "official_sitemap":
        return []
    req = urllib.request.Request(sitemap, headers={"User-Agent": "GennyBriefComposer/1.0"})
    ctx = verified_ssl_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
        body = response.read(3_500_000)
    rows = parse_sitemap_rows(body, source)
    out: list[dict[str, str]] = []
    article_reads = 0
    max_reads = max(1, min(int(source.get("sitemap_article_reads") or SITEMAP_ARTICLE_READS_PER_SOURCE), 20))
    required_pattern = required_pattern_for_vertical(vertical)
    for row in rows:
        sitemap_date = row.get("date", "")
        if sitemap_date and not likely_recent("", sitemap_date):
            continue
        if article_reads >= max_reads:
            break
        article_reads += 1
        url = row["url"]
        title, summary, published_date = fetch_article_metadata(url, required_pattern)
        date = published_date or sitemap_date
        if not title:
            title = urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1])
            title = re.sub(r"[-_]+", " ", title).strip().title()
        if not date:
            append_candidate_review(
                reviews,
                lens=lens,
                vertical=vertical,
                source=source,
                title=title,
                summary=summary,
                url=url,
                date="",
                status="rejected",
                score=0,
                reason="missing publication date for daily discovery",
            )
            continue
        passed, score, reason = quality_review(vertical, source, title, summary, url, date)
        review_id = append_candidate_review(
            reviews,
            lens=lens,
            vertical=vertical,
            source=source,
            title=title,
            summary=summary,
            url=url,
            date=date,
            status="qualified" if passed else "rejected",
            score=score,
            reason=reason,
        )
        if not passed:
            continue
        if relevance_score(vertical, source, title, summary) <= 0:
            signal_ledger.update_review_status(
                reviews or [],
                review_id,
                "rejected",
                "missing vertical relevance",
            )
            continue
        out.append({
            "title": title,
            "url": url,
            "date": date,
            "summary": truncate_text(summary, 260),
            "source": str(source.get("name") or "Official update"),
            "priority": str(source.get("priority") or "high"),
            "score": str(score),
            "review": reason,
            "_review_id": review_id,
        })
        if len(out) >= min(limit, MAX_PER_SOURCE):
            break
    return out


def fetch_manual_links(
    source: dict[str, Any],
    vertical: str,
    limit: int,
    reviews: list[dict[str, Any]] | None = None,
    lens: str = "genny",
) -> list[dict[str, str]]:
    url = source.get("url")
    if not url:
        return []
    if not is_discovery_source(source):
        return []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GennyBriefComposer/1.0"})
        ctx = verified_ssl_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx) as response:
            ctype = response.headers.get("content-type", "")
            if "html" not in ctype:
                return []
            body = response.read(900_000).decode("utf-8", "replace")
    except Exception:
        return []

    base_host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    article_reads = 0
    for match in re.finditer(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", body, re.I | re.S):
        href = urllib.parse.urljoin(url, html.unescape(match.group(1).strip()))
        if href in seen or SKIP_URL_PATTERNS.search(href):
            continue
        host = urllib.parse.urlparse(href).netloc.removeprefix("www.")
        if host and base_host and host != base_host:
            continue
        title = strip_text(match.group(2))
        if len(title) < 8 or len(title) > 180 or NOISE_PATTERNS.search(title):
            continue
        if LOW_VALUE_TITLE_PATTERNS.search(title) and not HIGH_VALUE_SIGNAL_PATTERNS.search(title):
            append_candidate_review(
                reviews,
                lens=lens,
                vertical=vertical,
                source=source,
                title=title,
                summary="",
                url=href,
                date="",
                status="rejected",
                score=0,
                reason="generic/how-to/category title",
            )
            continue
        if not is_briefable_url(href):
            append_candidate_review(
                reviews,
                lens=lens,
                vertical=vertical,
                source=source,
                title=title,
                summary="",
                url=href,
                date="",
                status="rejected",
                score=0,
                reason="rejected-url",
            )
            continue
        if article_reads >= ARTICLE_READS_PER_SOURCE:
            break
        article_reads += 1
        excerpt = fetch_article_excerpt(href, required_pattern_for_vertical(vertical))
        passed, score, reason = quality_review(vertical, source, title, excerpt, href)
        review_id = append_candidate_review(
            reviews,
            lens=lens,
            vertical=vertical,
            source=source,
            title=title,
            summary=excerpt,
            url=href,
            date="",
            status="qualified" if passed else "rejected",
            score=score,
            reason=reason,
        )
        if not passed:
            continue
        if score <= 0:
            signal_ledger.update_review_status(
                reviews or [],
                review_id,
                "rejected",
                "non-positive quality score",
            )
            continue
        seen.add(href)
        out.append({
            "title": title,
            "url": href,
            "date": "",
            "summary": excerpt or "Source item passed the GenLens quality gate; verify details before publishing.",
            "source": source.get("name", "Source"),
            "priority": source.get("priority", "medium"),
            "score": str(score),
            "review": reason,
            "_review_id": review_id,
        })
        if len(out) >= limit:
            break
    return out


def relevance_score(vertical: str, source: dict[str, Any], title: str, summary: str) -> int:
    text = " ".join([
        title,
        summary,
    ]).lower()
    score = 0
    source_terms = {str(term).lower() for term in source.get("watch_for", []) if str(term).strip()}
    for term in GLOBAL_SIGNAL_TERMS | VERTICAL_SIGNAL_TERMS.get(vertical, set()) | source_terms:
        if term in text:
            score += 1
    # Trusted narrow sources can pass with one strong match. Broad editorial
    # feeds need at least two matches to avoid random news padding.
    if source.get("priority") == "high" and score >= 1:
        return score
    return score if score >= 2 else 0


def verticals_for_mode(mode: str, lens: str = "genny") -> list[str]:
    if lens == "marti":
        return MARTI_ACTIVE_LAYERS if mode == "active" else MARTI_EXPANDED_LAYERS
    return ACTIVE_VERTICALS if mode == "active" else EXPANDED_VERTICALS


def phase_for_vertical(vertical: str, lens: str) -> str:
    if lens == "marti":
        return MARTI_PHASE_BY_LAYER.get(vertical, "Marti - Other")
    return PHASE_BY_VERTICAL.get(vertical, "Other")


def item_key(item: dict[str, str]) -> str:
    url = item.get("url", "").split("#", 1)[0].rstrip("/")
    if url:
        return url.lower()
    return re.sub(r"\W+", "", item.get("title", "").lower())


def priority_weight(priority: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(priority, 1)


TOPIC_TOKEN_STOPWORDS = {
    "about", "adds", "after", "announces", "available", "direct", "every",
    "from", "inside", "introduces", "launches", "new", "now",
    "release", "releases", "the", "their", "through", "updates", "version",
    "with", "your",
}


def topic_tokens(title: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", title.lower())
        if len(token) >= 3 and token not in TOPIC_TOKEN_STOPWORDS
    }


def is_near_duplicate_topic(left: set[str], right: set[str]) -> bool:
    if not left or not right:
        return False
    overlap = len(left & right)
    return overlap >= 3 and overlap / min(len(left), len(right)) >= 0.75


def rank_items(
    items: list[dict[str, str]],
    reviews: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    source_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    topic_counts: dict[str, int] = {}
    topic_token_sets: list[set[str]] = []
    ordered_items = sorted(
        items,
        key=lambda item: (
            priority_weight(item.get("priority", "medium")),
            int(item.get("score", "0") or 0),
            item.get("date", ""),
        ),
        reverse=True,
    )
    for item in ordered_items:
        key = item_key(item)
        review_id = item.get("_review_id", "")
        if not key:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "missing signal key")
            continue
        if key in seen:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "duplicate signal")
            continue
        tokens = topic_tokens(item.get("title", ""))
        if any(is_near_duplicate_topic(tokens, existing) for existing in topic_token_sets):
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "cross-source near-duplicate signal")
            continue
        source_bucket = f"{item.get('source', 'Source')}:{source_domain(item.get('url', ''))}"
        domain = source_domain(item.get("url", ""))
        if source_counts.get(source_bucket, 0) >= MAX_PER_SOURCE:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "source concentration limit")
            continue
        if domain and domain_counts.get(domain, 0) >= MAX_PER_DOMAIN:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "domain concentration limit")
            continue
        topic = topic_cluster_key(item)
        if topic_counts.get(topic, 0) >= MAX_PER_TOPIC_CLUSTER:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "topic concentration limit")
            continue
        seen.add(key)
        source_counts[source_bucket] = source_counts.get(source_bucket, 0) + 1
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        topic_token_sets.append(tokens)
        deduped.append(item)
    return deduped


def compose(
    mode: str,
    per_vertical: int,
    rss_limit: int,
    include_manual: bool = False,
    lens: str = "genny",
    ledger_out: Path | None = None,
) -> str:
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    lenses = ["genny", "marti"] if lens == "unified" else [lens]
    data_by_lens = {name: load_sources(name) for name in lenses}
    vertical_rows = [
        (name, vertical)
        for name in lenses
        for vertical in verticals_for_mode(mode, name)
    ]
    total_sources = sum(
        len(data_by_lens[name].get("verticals", {}).get(vertical, []))
        for name, vertical in vertical_rows
    )
    product_name = {"genny": "GenLens", "marti": "Marti", "unified": "Marti-Genny"}[lens]
    priority_rule = {
        "genny": "Prioritize tool releases, production workflow shifts, cost/time deltas, licensing/compliance, and credible pipeline case studies.",
        "marti": "Prioritize agent and API releases, pricing changes, stack displacement, campaign economics, measurement changes, and credible operator case studies.",
        "unified": "Prioritize verified production or distribution shifts with a concrete workflow, economic, measurement, rights, or role consequence.",
    }[lens]
    lines = [
        f"# {product_name} Briefing - {today}",
        "",
        f"{mode.title()} source-backed draft for the {lens} lens across {len(vertical_rows)} verticals/layers and {total_sources} configured sources. Daily mode uses feed/news sources; manual/vendor pages are retained for verification and source audits.",
        "",
        "## Briefing Standard",
        "",
        f"- {priority_rule}",
        "- Treat source links as leads, not finished facts. Do not invent numbers or claims.",
        "- If a vertical has weak live signals, show the watch queue instead of padding with generic news.",
        "",
    ]
    current_phase = ""
    coverage_gaps: list[str] = []
    candidate_reviews: list[dict[str, Any]] = []
    for current_lens, vertical in vertical_rows:
        phase = phase_for_vertical(vertical, current_lens)
        sources = data_by_lens[current_lens].get("verticals", {}).get(vertical, [])
        candidates: list[dict[str, str]] = []
        errors: list[str] = []
        for source in sources:
            try:
                if source.get("rss"):
                    candidates.extend(fetch_rss(
                        source,
                        vertical,
                        rss_limit,
                        reviews=candidate_reviews,
                        lens=current_lens,
                    ))
                elif source.get("sitemap"):
                    candidates.extend(fetch_sitemap(
                        source,
                        vertical,
                        rss_limit,
                        reviews=candidate_reviews,
                        lens=current_lens,
                    ))
                elif include_manual:
                    candidates.extend(fetch_manual_links(
                        source,
                        vertical,
                        max(2, rss_limit // 2),
                        reviews=candidate_reviews,
                        lens=current_lens,
                    ))
            except (urllib.error.URLError, ET.ParseError, TimeoutError) as exc:
                errors.append(f"{source.get('name', 'Source')}: {exc}")
            except Exception as exc:
                errors.append(f"{source.get('name', 'Source')}: {exc}")
        picked = rank_items(candidates, candidate_reviews)
        for item in picked[:per_vertical]:
            signal_ledger.update_review_status(
                candidate_reviews,
                item.get("_review_id", ""),
                "published",
                "published in brief",
            )
        if not picked and not sources:
            continue
        if not picked:
            audit_sources = [s for s in sources if is_discovery_source(s)]
            feed_names = ", ".join(
                s.get("name", "source")
                for s in audit_sources
                if s.get("rss") or s.get("sitemap")
            ) or "none"
            manual_names = ", ".join(
                s.get("name", "source")
                for s in audit_sources
                if not s.get("rss") and not s.get("sitemap")
            )
            if audit_sources:
                if include_manual:
                    gap = f"{vertical}: checked feeds/pages but rejected homepage, product, generic marketing, stale, or weak-relevance links."
                else:
                    gap = f"{vertical}: no qualified feed signals. Feed sources checked: {feed_names}. Manual sources on deck for audit: {manual_names[:180] or 'none'}."
            else:
                names = ", ".join(s.get("name", "source") for s in sources[:6])
                gap = f"{vertical}: watch-only sources are useful for verification, not daily news: {names}."
            if errors:
                gap += f" Feed issues: {'; '.join(errors[:3])}."
            coverage_gaps.append(gap)
            continue
        if phase != current_phase:
            lines.append(f"## {phase}")
            lines.append("")
            current_phase = phase
        lines.append(f"## {vertical}")
        lines.append("")
        lines.append(f"_Sources checked: {len(sources)}. Candidate leads found: {len(picked)}._")
        lines.append("")
        # Freshest first: dated items by date descending, undated items last so
        # unverified-age leads never crowd out confirmed-recent signals.
        picked.sort(
            key=lambda row: parsed_iso_date(row.get("date", "")) or dt.date.min,
            reverse=True,
        )
        for item in picked[:per_vertical]:
            chips = [relative_age(item.get("date", ""))]
            chips.append(item.get("source", "Source"))
            chip_text = " ".join(f"`{chip}`" for chip in chips)
            summary = item.get("summary") or "Source item requires manual review for production impact."
            url = item.get("url", "")
            title = item["title"]
            linked_title = f"[{title}]({url})" if url else f"**{title}**"
            source_link = f" [Source]({url})" if url else ""
            lines.append(f"- **{linked_title}** — {summary} {chip_text}{source_link}".strip())
        if len(picked) > per_vertical:
            overflow = ", ".join(item["title"] for item in picked[per_vertical:per_vertical + 4])
            coverage_gaps.append(f"{vertical}: more leads available for review after the published set: {overflow}.")
        lines.append("")
    if mode == "expanded" and "genny" in lenses:
        lines.extend(render_market_intelligence_section())
    if lens == "unified":
        coverage_gaps.append(
            "Unified: cross-lens candidates are generated in a separate convergence review artifact. "
            "Only conclusions with an attributed human verification event may be appended to this briefing."
        )
    if coverage_gaps:
        lines.extend([
            "## Source Coverage Notes",
            "",
            f"_Not rendered as briefing cards. These are curation tasks for the {product_name} source list._",
            "",
        ])
        for gap in coverage_gaps[:12]:
            lines.append(f"- {gap}")
        lines.append("")
    if ledger_out is not None:
        signal_ledger.write_signal_ledger(
            ledger_out,
            candidate_reviews,
            run_lens=lens,
            mode=mode,
        )
    return "\n".join(lines).strip() + "\n"


def list_value(row: dict[str, Any], key: str) -> list[str]:
    value = row.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value:
        return [str(value)]
    return []


def render_market_intelligence_section() -> list[str]:
    if not ROLE_SIGNALS_PATH.exists():
        return []
    try:
        data = json.loads(ROLE_SIGNALS_PATH.read_text())
    except Exception:
        return []
    roles = [row for row in data.get("roles", []) if isinstance(row, dict)]
    if not roles:
        return []

    observed = [row for row in roles if str(row.get("status", "")).lower() == "observed"]
    emerging = [row for row in roles if str(row.get("status", "")).lower() == "emerging"]
    forecast = [row for row in roles if str(row.get("status", "")).lower() == "forecast"]

    def names(rows: list[dict[str, Any]], limit: int = 4) -> str:
        values = [str(row.get("role") or row.get("title") or "Untitled role") for row in rows[:limit]]
        return ", ".join(values)

    tool_counts: dict[str, int] = {}
    for row in roles:
        for tool in list_value(row, "tools"):
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    top_tools = ", ".join(tool for tool, _ in sorted(tool_counts.items(), key=lambda item: item[1], reverse=True)[:8])

    build_role = next((row for row in emerging), roles[0])
    build_name = str(build_role.get("role") or build_role.get("title") or "AI creative workflow proof")
    build_tools = ", ".join(list_value(build_role, "tools")[:6]) or "current GenLens tool stack"

    lines = [
        "## GenLens",
        "",
        "_Genny Market Intelligence layer: jobs and tool clusters converted into role radar, proof-builds, and product opportunities._",
        "",
    ]
    if observed:
        lines.append(f"- **Role Radar** — Observed roles now tracked: {names(observed)}. `observed`")
    if emerging:
        lines.append(f"- **Emerging Role Gap** — Repeating tool/workflow patterns point toward: {names(emerging)}. `emerging`")
    if forecast:
        lines.append(f"- **18-Month Forecast** — Evidence-backed future roles to watch: {names(forecast)}. `forecast`")
    if top_tools:
        lines.append(f"- **Tool Graph** — Current recurring stack terms: {top_tools}. `tool cluster`")
    lines.append(f"- **Build This** — Proof-build prompt: create a portfolio artifact for **{build_name}** using {build_tools}; ship a live artifact, process notes, and time/cost delta. `proof build`")
    lines.append("- **Product Lab** — GenLens can package these into Emerging Creative AI Roles, Tool Stack Blueprints, Hiring Briefs, Proof-Build Generator, and Source Quality Dashboard. `product opportunity`")
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["active", "expanded"], default="expanded")
    parser.add_argument("--lens", choices=["genny", "marti", "unified"], default="genny")
    parser.add_argument("--out", default=str(OUT_PATH))
    parser.add_argument("--per-vertical", type=int, default=5)
    parser.add_argument("--rss-limit", type=int, default=12)
    parser.add_argument("--ledger-out", default="")
    parser.add_argument("--include-manual", action="store_true", help="Also crawl manual blog/news pages. Slower; use for audits, not normal cron.")
    args = parser.parse_args()
    out = Path(args.out)
    suffix = "" if args.lens == "genny" else f"_{args.lens}"
    ledger_out = Path(args.ledger_out) if args.ledger_out else out.parent / f"signal_ledger{suffix}.json"
    text = compose(
        args.mode,
        max(1, min(args.per_vertical, 10)),
        max(1, min(args.rss_limit, 20)),
        args.include_manual,
        args.lens,
        ledger_out,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
