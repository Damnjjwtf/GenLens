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
    r"(/blog/|/news/|/news/stories/|/learn/|/insights/|/resources/|/magazine/|/articles?/|/posts/|/products/ads-commerce/|/research/|/case-stud|/customer-stor|/press|/release|/announc|/update|/changelog|/paper|arxiv\.org/abs/|github\.com/.+/(releases|commits|pulls)|/20\d{2}/)",
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
    r"\b(announc|launch|release|update|introduc|acquir|raises?|funding|study|report|research|case study|customer story|benchmark|pricing|license|policy|rights|compliance|deprecat|sunset|shut(?:ting)? down|sdk|api|integration|open source|generally available|beta|v\d+(?:\.\d+)*)\b",
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
    r"\b(best|top|what is|how to|guide to|ultimate guide|tips|examples|template|category|all articles|learn more|resources|use cases|customer stories|case studies|compare|vs\.?|which .* fits|make money|start a podcast|embed a video|gaming headphones|signed synths?|supersaw sound|record cutting)\b",
    re.I,
)

WEAK_SOURCE_PATTERNS = re.compile(
    r"\b(quasa|bitcoin world|startup story|startup fortune|digital terminal|gigazine|futurum group)\b",
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
MAX_ITEM_AGE_DAYS = int(os.environ.get("GENLENS_MAX_ITEM_AGE_DAYS", "45"))
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


def has_marti_event_evidence(text: str) -> bool:
    if MARTI_CHANGE_PATTERNS.search(text):
        return True
    return bool(MARTI_OUTCOME_PATTERNS.search(text) and NUMERIC_EVIDENCE_PATTERNS.search(text))


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
    if source.get("rss"):
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


def fetch_article_excerpt(url: str, required_pattern: re.Pattern[str] | None = None) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GennySourceReviewer/1.0"})
        ctx = verified_ssl_context()
        with urllib.request.urlopen(req, timeout=4, context=ctx) as response:
            ctype = response.headers.get("content-type", "")
            if "html" not in ctype:
                return ""
            body = response.read(700_000).decode("utf-8", "replace")
    except Exception:
        return ""

    descriptions: list[str] = []
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
    paragraphs = [clean_excerpt(match.group(1)) for match in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.I | re.S)]
    # Large developer portals sometimes wrap their entire navigation tree in a
    # single paragraph-like element. Exclude those blocks so article evidence
    # wins even when the page shell contains release/search vocabulary.
    paragraphs = [p for p in paragraphs if 60 <= len(p) <= 2_000]
    evidence_paragraphs = [p for p in paragraphs if has_marti_event_evidence(p)]
    if required_pattern:
        relevant_evidence = [p for p in evidence_paragraphs if required_pattern.search(p)]
    else:
        relevant_evidence = []
    candidates = relevant_evidence or evidence_paragraphs or paragraphs
    candidates = sorted(candidates, key=len, reverse=True)
    selected = candidates[:2] or descriptions[:1]
    return truncate_text(" ".join(dict.fromkeys(selected)), 320)


def quality_review(vertical: str, source: dict[str, Any], title: str, summary: str, url: str, date: str = "") -> tuple[bool, int, str]:
    is_news_search = source.get("source_type") == "news_search"
    if not is_briefable_url(url) and not is_news_search:
        return False, 0, "rejected-url"
    text = f"{title} {summary}"
    if FALSE_POSITIVE_PATTERNS.search(text):
        return False, 0, "false-positive entertainment/deal/pricing item"
    if WEAK_SOURCE_PATTERNS.search(text):
        return False, 0, "weak aggregator source"
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
    if source.get("source_type") in {"official_updates", "release_notes", "github_releases"}:
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
        source_type=str(source.get("source_type") or "unknown"),
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
                summary = fetch_article_excerpt(url, MARTI_REQUIRED_PATTERNS.get(vertical)) or summary
                article_reads += 1
        if (
            vertical in MARTI_REQUIRED_PATTERNS
            and article_reads < RSS_ARTICLE_READS_PER_SOURCE
            and (not summary or not has_marti_event_evidence(f"{title} {summary}"))
        ):
            summary = fetch_article_excerpt(url, MARTI_REQUIRED_PATTERNS.get(vertical)) or summary
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
        excerpt = fetch_article_excerpt(href, MARTI_REQUIRED_PATTERNS.get(vertical))
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


def rank_items(
    items: list[dict[str, str]],
    reviews: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    source_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    topic_counts: dict[str, int] = {}
    for item in items:
        key = item_key(item)
        review_id = item.get("_review_id", "")
        if not key:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "missing signal key")
            continue
        if key in seen:
            signal_ledger.update_review_status(reviews or [], review_id, "rejected", "duplicate signal")
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
        deduped.append(item)
    return sorted(
        deduped,
        key=lambda item: (
            priority_weight(item.get("priority", "medium")),
            int(item.get("score", "0") or 0),
            item.get("date", ""),
        ),
        reverse=True,
    )


def convergence_candidates(items_by_lens: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    themes = {
        "creative-volume economics": {"creative", "variant", "campaign", "video", "image", "ads", "cpm", "roas"},
        "agentic production and distribution": {"agent", "automation", "workflow", "orchestration", "pipeline", "api"},
        "commerce asset conversion": {"commerce", "product", "catalog", "shopify", "conversion", "storefront"},
        "measurement and provenance": {"measurement", "attribution", "provenance", "rights", "compliance", "consent"},
    }
    genny_items = items_by_lens.get("genny", [])
    marti_items = items_by_lens.get("marti", [])
    candidates: list[dict[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for theme, terms in themes.items():
        def theme_match(item: dict[str, str]) -> bool:
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            return sum(1 for term in terms if term in text) >= 2

        genny = next((item for item in genny_items if theme_match(item)), None)
        marti = next((item for item in marti_items if theme_match(item)), None)
        if not genny or not marti:
            continue
        pair = (item_key(genny), item_key(marti))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        candidates.append({
            "theme": theme,
            "genny_title": genny.get("title", "Genny signal"),
            "genny_url": genny.get("url", ""),
            "marti_title": marti.get("title", "Marti signal"),
            "marti_url": marti.get("url", ""),
        })
    return candidates[:3]


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
    items_by_lens: dict[str, list[dict[str, str]]] = {name: [] for name in lenses}
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
        items_by_lens[current_lens].extend(picked[:per_vertical])
        if not picked and not sources:
            continue
        if not picked:
            audit_sources = [s for s in sources if is_discovery_source(s)]
            feed_names = ", ".join(s.get("name", "source") for s in audit_sources if s.get("rss")) or "none"
            manual_names = ", ".join(s.get("name", "source") for s in audit_sources if not s.get("rss"))
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
        for item in picked[:per_vertical]:
            chips = []
            if item.get("date"):
                chips.append(item["date"])
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
        convergence = convergence_candidates(items_by_lens)
        if convergence:
            lines.extend([
                "## GenLens",
                "",
                "_Convergence candidates connect one production signal with one distribution signal. They are prompts for editorial verification, not automatic causal claims._",
                "",
            ])
            for item in convergence:
                genny_link = f"[{item['genny_title']}]({item['genny_url']})" if item["genny_url"] else item["genny_title"]
                marti_link = f"[{item['marti_title']}]({item['marti_url']})" if item["marti_url"] else item["marti_title"]
                lines.append(f"- **Convergence candidate: {item['theme']}** — Genny: {genny_link}. Marti: {marti_link}. Verify the shared workflow or economic consequence before promotion. `convergence candidate`")
            lines.append("")
        else:
            coverage_gaps.append("Unified: no convergence candidate met the minimum two-term overlap in both lenses. Do not manufacture a cross-lens claim.")
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
