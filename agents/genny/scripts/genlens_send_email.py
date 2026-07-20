#!/usr/bin/env python3
"""Send GenLens email through Resend."""
from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path("/root/.hermes/profiles/genny/.env")
RESEND_URL = "https://api.resend.com/emails"
KNOWN_VERTICALS = {
    "Product Photography",
    "AI Filmmaking",
    "Digital Humans",
    "Infrastructure",
    "Advertising / Brand Content",
    "ArchViz",
    "AI Design / Motion Graphics",
    "Music Production / Audio",
    "Fashion / Apparel / Textile",
    "Podcast / Long-Form Audio",
    "Education / E-Learning Content",
    "Social / Short-Form Video",
    "Game Development / Real-Time 3D",
    "Cross-Vertical Watchlist",
    "GenLens",
}

HOUSEKEEPING_TITLES = {
    "no qualified feed signals",
    "no qualified signals",
    "source check needed",
    "watch-only sources",
    "additional watchlist",
    "no verified signals ready",
}


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def render_test_html(preheader: str) -> str:
    preheader = html_lib.escape(preheader)
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GenLens Briefing Test</title>
  </head>
  <body style="margin:0;background:#070707;color:#f4f0e8;font-family:Inter,Arial,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#070707;">
      <tr>
        <td align="center" style="padding:28px 16px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;border:1px solid #2a2924;background:#11110f;">
            <tr>
              <td style="padding:26px 28px 18px;border-bottom:1px solid #2a2924;">
                <div style="font:700 13px/1.2 Inter,Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#d7ff66;">GenLens</div>
                <h1 style="margin:14px 0 8px;font:700 34px/1.04 Georgia,serif;color:#fffaf0;letter-spacing:0;">Daily signal test</h1>
                <p style="margin:0;color:#b9b4aa;font:400 15px/1.6 Inter,Arial,sans-serif;">Genny is connected to Resend and ready to send source-backed creative production briefings.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:22px 28px 6px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="padding:0 0 14px;">
                      <span style="display:inline-block;padding:6px 9px;border:1px solid #3f3b2e;color:#d7ff66;background:#171810;font:700 12px/1 Inter,Arial,sans-serif;">Product Photography</span>
                      <span style="display:inline-block;margin-left:6px;padding:6px 9px;border:1px solid #392b2b;color:#ffb199;background:#1b1210;font:700 12px/1 Inter,Arial,sans-serif;">AI Filmmaking</span>
                      <span style="display:inline-block;margin-left:6px;padding:6px 9px;border:1px solid #27323f;color:#a9d7ff;background:#10161d;font:700 12px/1 Inter,Arial,sans-serif;">Digital Humans</span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 24px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:separate;border-spacing:0 12px;">
                  <tr>
                    <td style="padding:18px;border:1px solid #2c2b27;background:#151512;">
                      <div style="color:#d7ff66;font:700 12px/1 Inter,Arial,sans-serif;text-transform:uppercase;letter-spacing:.08em;">Status</div>
                      <h2 style="margin:9px 0 7px;color:#fffaf0;font:700 20px/1.25 Inter,Arial,sans-serif;">Email pipeline is live</h2>
                      <p style="margin:0;color:#c9c3b8;font:400 14px/1.55 Inter,Arial,sans-serif;">Resend accepted the sender domain and Genny can now deliver polished GenLens emails from the Hermes gateway.</p>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:18px;border:1px solid #2c2b27;background:#151512;">
                      <div style="color:#a9d7ff;font:700 12px/1 Inter,Arial,sans-serif;text-transform:uppercase;letter-spacing:.08em;">Next</div>
                      <h2 style="margin:9px 0 7px;color:#fffaf0;font:700 20px/1.25 Inter,Arial,sans-serif;">Briefings can use the same shell</h2>
                      <p style="margin:0;color:#c9c3b8;font:400 14px/1.55 Inter,Arial,sans-serif;">Daily issues will map source-backed signals to the GenLens tools manifest, then render vertical sections with short summaries, chips, and links.</p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 26px;border-top:1px solid #2a2924;color:#837d73;font:400 12px/1.5 Inter,Arial,sans-serif;">
                Sent by Genny for GenLens. Signal over noise. Numbers over vibes.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def render_briefing_html(markdown: str) -> str:
    escaped_preheader = html_lib.escape(
        "Source-backed creative production intelligence from GenLens."
    )
    items = public_briefing_items(markdown)

    vertical_meta = {
        "Product Photography": {
            "accent": "#d7ff66",
            "label": "Product Photography",
        },
        "AI Filmmaking": {
            "accent": "#ffb199",
            "label": "AI Filmmaking",
        },
        "Digital Humans": {
            "accent": "#a9d7ff",
            "label": "Digital Humans",
        },
        "Infrastructure": {
            "accent": "#c9b6ff",
            "label": "Infrastructure",
        },
        "Advertising / Brand Content": {
            "accent": "#ffd36e",
            "label": "Advertising / Brand Content",
        },
        "ArchViz": {
            "accent": "#9ff0d0",
            "label": "ArchViz",
        },
        "AI Design / Motion Graphics": {
            "accent": "#ff9ee7",
            "label": "AI Design / Motion Graphics",
        },
        "Music Production / Audio": {
            "accent": "#b7ff9e",
            "label": "Music Production / Audio",
        },
        "Fashion / Apparel / Textile": {
            "accent": "#ffb6d5",
            "label": "Fashion / Apparel / Textile",
        },
        "Podcast / Long-Form Audio": {
            "accent": "#9bd6ff",
            "label": "Podcast / Long-Form Audio",
        },
        "Education / E-Learning Content": {
            "accent": "#ffe28a",
            "label": "Education / E-Learning",
        },
        "Social / Short-Form Video": {
            "accent": "#ff9f9f",
            "label": "Social / Short-Form Video",
        },
        "Game Development / Real-Time 3D": {
            "accent": "#9cffd9",
            "label": "Game Development / Real-Time 3D",
        },
        "Cross-Vertical Watchlist": {
            "accent": "#d7ff66",
            "label": "Cross-Vertical Watchlist",
        },
        "GenLens": {
            "accent": "#d7ff66",
            "label": "GenLens",
        },
    }

    counts: dict[str, int] = {}
    for item in items:
        vertical_name = str(item.get("vertical") or "GenLens")
        counts[vertical_name] = counts.get(vertical_name, 0) + 1

    if counts:
        map_html = "".join(
            f"""
            <tr>
              <td style="padding:8px 0;border-bottom:1px solid #242424;">
                <span style="display:inline-block;width:10px;height:10px;background:{vertical_meta.get(vertical, vertical_meta["GenLens"])["accent"]};margin-right:9px;"></span>
                <span style="font:700 12px/1.3 Arial,Helvetica,sans-serif;color:#f3f3ef;text-transform:uppercase;letter-spacing:.08em;">{html_lib.escape(vertical_meta.get(vertical, vertical_meta["GenLens"])["label"])}</span>
                <span style="float:right;font:700 12px/1.3 Arial,Helvetica,sans-serif;color:#8f8f88;">{count}</span>
              </td>
            </tr>
            """
            for vertical, count in counts.items()
        )
    else:
        map_html = """
            <tr>
              <td style="padding:10px 0;color:#b7b7ae;font:400 14px/1.5 Arial,Helvetica,sans-serif;">
                No publishable signals passed the source-quality gate. Genny should keep researching instead of padding the brief.
              </td>
            </tr>
        """

    cards = []
    for index, item in enumerate(items, start=1):
        meta = vertical_meta.get(item["vertical"], vertical_meta["GenLens"])
        title = html_lib.escape(item["title"])
        summary = html_lib.escape(item["summary"])
        source = html_lib.escape(item["source"] or "Source")
        raw_url = str(item.get("url") or "").strip()
        url = html_lib.escape(raw_url)
        chip_html = "".join(
            f'<span style="display:inline-block;margin:0 6px 6px 0;padding:5px 8px;border:1px solid #313131;color:#d9d9d2;background:#101010;font:700 11px/1 Arial,Helvetica,sans-serif;text-transform:uppercase;letter-spacing:.04em;">{html_lib.escape(chip)}</span>'
            for chip in item["chips"][:4]
        )
        title_html = (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color:#f7f7f2;text-decoration:none;border-bottom:3px solid {meta["accent"]};">{title}</a>'
            if url
            else title
        )
        source_html = (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color:{meta["accent"]};text-decoration:none;font:800 12px/1 Arial,Helvetica,sans-serif;text-transform:uppercase;letter-spacing:.08em;">Source: {source} →</a>'
            if url
            else ""
        )
        cards.append(
            f"""
            <tr>
              <td style="padding:0 30px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-top:1px solid #292929;">
                  <tr>
                    <td style="width:42px;padding:22px 14px 22px 0;vertical-align:top;color:{meta["accent"]};font:800 13px/1 Arial,Helvetica,sans-serif;">{index:02d}</td>
                    <td style="padding:20px 0 22px;vertical-align:top;">
                      <div style="margin:0 0 10px;color:{meta["accent"]};font:900 11px/1 Arial,Helvetica,sans-serif;text-transform:uppercase;letter-spacing:.13em;">{html_lib.escape(meta["label"])}</div>
                      <h2 style="margin:0 0 10px;color:#f7f7f2;font:800 24px/1.13 Arial,Helvetica,sans-serif;letter-spacing:0;">{title_html}</h2>
                      <p style="margin:0 0 14px;color:#c8c8c0;font:400 15px/1.62 Arial,Helvetica,sans-serif;">{summary}</p>
                      <div style="margin:0 0 12px;">{chip_html}</div>
                      <div>{source_html}</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GenLens Daily Intelligence</title>
  </head>
  <body style="margin:0;background:#050505;color:#f4f0e8;font-family:Arial,Helvetica,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escaped_preheader}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#050505;">
      <tr>
        <td align="center" style="padding:30px 12px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;background:#0b0b0a;border:1px solid #242424;">
            <tr>
              <td style="padding:30px 30px 24px;border-bottom:1px solid #242424;background:#0b0b0a;">
                <div style="font:900 12px/1 Arial,Helvetica,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#d7ff66;">GenLens Daily Intelligence</div>
                <h1 style="margin:16px 0 12px;color:#f7f7f2;font:900 42px/1.02 Arial,Helvetica,sans-serif;letter-spacing:0;">Creative AI signals worth acting on.</h1>
                <p style="margin:0;color:#bdbdb4;font:400 15px/1.6 Arial,Helvetica,sans-serif;max-width:560px;">No generic product pages. No stale listicles. Every item should point to a workflow shift, role shift, cost delta, rights issue, or tool capability a working Gen AD can use.</p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 30px 20px;border-bottom:1px solid #242424;background:#10100f;">
                <div style="margin:0 0 10px;font:900 11px/1 Arial,Helvetica,sans-serif;letter-spacing:.13em;text-transform:uppercase;color:#8f8f88;">Today's Map</div>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  {map_html}
                </table>
              </td>
            </tr>
            {''.join(cards)}
            <tr>
              <td style="padding:22px 30px 30px;border-top:1px solid #242424;color:#8a8a82;font:400 12px/1.55 Arial,Helvetica,sans-serif;">
                Sent by Genny for GenLens. Source-backed intelligence for AI production, synthetic talent, tools, roles, and workflow arbitrage.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def parse_briefing_items(markdown: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    vertical = "GenLens"
    current: dict[str, object] | None = None
    in_vertical_section = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if heading:
            candidate = strip_markdown(heading.group(1)).strip()
            if candidate in KNOWN_VERTICALS:
                if current:
                    items.append(current)
                    current = None
                vertical = candidate
                in_vertical_section = True
            else:
                in_vertical_section = False
            continue
        if not in_vertical_section:
            continue
        parsed_bullet = parse_bullet(line)
        if parsed_bullet:
            if current:
                items.append(current)
            title, rest = parsed_bullet
            url = extract_url(line)
            image = extract_image_url(line)
            chips = re.findall(r"`([^`]+)`", line)
            current = {
                "vertical": vertical,
                "title": title[:140] or "Untitled signal",
                "summary": clean_summary(rest)[:320] or "",
                "url": url,
                "source": source_from_url(url),
                "chips": chips,
                "image": image,
            }
            continue
        if current and not line.startswith("#"):
            image = extract_image_url(line)
            if image and not current.get("image"):
                current["image"] = image
                continue
            text = strip_markdown(line)
            if text:
                summary = str(current.get("summary") or "")
                current["summary"] = clean_summary((summary + " " + text).strip())[:420]
    if current:
        items.append(current)
    return items[:90]


def is_housekeeping_item(item: dict[str, object]) -> bool:
    title = str(item.get("title") or "").strip().lower()
    if title in HOUSEKEEPING_TITLES:
        return True
    if title.startswith("no qualified ") or title.startswith("source check "):
        return True
    return False


def public_briefing_items(markdown: str) -> list[dict[str, object]]:
    items = []
    for item in parse_briefing_items(markdown):
        if is_housekeeping_item(item):
            continue
        if not item.get("url") and str(item.get("vertical")) != "GenLens":
            continue
        items.append(item)
    return items


def parse_bullet(line: str) -> tuple[str, str] | None:
    if not re.match(r"^[-*]\s+", line):
        return None
    body = re.sub(r"^[-*]\s+", "", line).strip()
    bold = re.match(r"^\*\*(.+?)\*\*\s*(?:[—-]\s*|:\s*)?(.*)$", body)
    if bold:
        return strip_markdown(bold.group(1)), strip_markdown(bold.group(2))
    linked = re.match(r"^\[([^\]]+)\]\([^)]+\)\s*(?:[—-]\s*|:\s*)?(.*)$", body)
    if linked:
        return strip_markdown(linked.group(1)), strip_markdown(linked.group(2))
    parts = re.split(r"\s+—\s+|\s+-\s+|:\s+", body, maxsplit=1)
    if len(parts) == 2:
        return strip_markdown(parts[0]), strip_markdown(parts[1])
    return strip_markdown(body), ""


def extract_url(text: str) -> str:
    match = re.search(r"https?://[^\s)>\"]+", text)
    return match.group(0) if match else ""


def extract_image_url(text: str) -> str:
    image = re.search(r"!\[[^\]]*\]\((https?://[^)]+)\)", text)
    if image:
        return image.group(1).strip()
    labeled = re.search(r"(?:image|preview|thumbnail|og:image)\s*[:=]\s*(https?://[^\s)>\"]+)", text, re.I)
    if labeled:
        return labeled.group(1).strip()
    for url in re.findall(r"https?://[^\s)>\"]+", text):
        if re.search(r"\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)", url, re.I):
            return url
    return ""


def fetch_preview_image(url: str) -> str:
    if not url:
        return ""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GenLens-Genny/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            ctype = response.headers.get("content-type", "")
            if "text/html" not in ctype:
                return ""
            body = response.read(500_000).decode("utf-8", "replace")
    except Exception:
        return ""
    patterns = [
        r'<meta\s+[^>]*property=["\']og:image(?::secure_url)?["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta\s+[^>]*name=["\']twitter:image(?::src)?["\'][^>]*content=["\']([^"\']+)["\']',
        r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\'](?:og:image(?::secure_url)?|twitter:image(?::src)?)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.I)
        if match:
            return urllib.parse.urljoin(url, html_lib.unescape(match.group(1).strip()))
    return ""


def source_from_url(url: str) -> str:
    if not url:
        return ""
    host = re.sub(r"^https?://", "", url).split("/", 1)[0].lower()
    return host.removeprefix("www.")


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def clean_summary(text: str) -> str:
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"\s+", " ", text).strip(" -—")


def send_email(to: str, subject: str, text: str, html: str | None = None) -> dict:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("GENLENS_EMAIL_FROM", os.environ.get("RESEND_FROM", "")).strip()
    if not api_key:
        raise SystemExit("RESEND_API_KEY is not configured in /root/.hermes/profiles/genny/.env")
    if not sender:
        raise SystemExit("GENLENS_EMAIL_FROM or RESEND_FROM is not configured in /root/.hermes/profiles/genny/.env")

    payload = {
        "from": sender,
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html:
        payload["html"] = html

    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GenLens-Genny/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {"status": response.status}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Resend HTTP {exc.code}: {body}") from exc


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--text", default="")
    parser.add_argument("--text-file", default="")
    parser.add_argument("--html", default="")
    parser.add_argument("--template", choices=["none", "genlens-test", "genlens-briefing"], default="none")
    args = parser.parse_args()
    text = args.text
    if args.text_file:
        text = Path(args.text_file).read_text()
    if not text:
        raise SystemExit("--text or --text-file is required")
    body_html = args.html or None
    if args.template == "genlens-test":
        body_html = render_test_html(text)
    elif args.template == "genlens-briefing":
        body_html = render_briefing_html(text)
    result = send_email(args.to, args.subject, text, body_html)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
