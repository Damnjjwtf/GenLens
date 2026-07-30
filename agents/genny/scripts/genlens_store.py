#!/usr/bin/env python3
"""SQLite operational store for the Genny newsroom pipeline.

The append-only JSON ledger is the durable audit cache (see SPINE.md); this is
the operational working set the refresh, verify, cluster, and health-scoring
roles read and write between runs. Neon remains the hosted system of record.

Schema follows agents/genny/docs/NEWSROOM_ARCHITECTURE.md section 8. Stdlib
sqlite3 only, so it runs anywhere the rest of the Genny scripts do.

This module is deliberately storage-only: it holds candidates, run history,
verdicts, clusters, deliveries, and negative memory. It does not fetch,
verify, or publish. Those roles call into it.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = 1

DEFAULT_DB_PATH = Path("state/newsroom.db")

VALID_TIERS = {
    "first_party",   # Tier 1: official changelogs, releases, pricing, policy
    "trade",         # Tier 2: independent trade reporting (CG Channel, FXGuide)
    "newsletter",    # Tier 3: curated newsletters, lead-generating
    "discovery",     # Tier 4: X, Reddit, Google News, Last30Days, community
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    feed_url TEXT NOT NULL DEFAULT '',
    tier TEXT NOT NULL,
    vertical TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    daily_intake INTEGER NOT NULL DEFAULT 1,
    -- health fields, updated by the scorer
    fetch_attempts INTEGER NOT NULL DEFAULT 0,
    fetch_successes INTEGER NOT NULL DEFAULT 0,
    qualified_candidates INTEGER NOT NULL DEFAULT 0,
    duplicate_candidates INTEGER NOT NULL DEFAULT 0,
    last_signal_at TEXT,
    last_failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    ran_at TEXT NOT NULL,
    ok INTEGER NOT NULL,
    candidates_found INTEGER NOT NULL DEFAULT 0,
    failure_reason TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER REFERENCES sources(id),
    fingerprint TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    vertical TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    status TEXT NOT NULL DEFAULT 'new',   -- new | verified | rejected | published
    harvested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    accepted INTEGER NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    reviewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_key TEXT NOT NULL UNIQUE,
    canonical_candidate_id INTEGER REFERENCES candidates(id),
    member_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER REFERENCES candidates(id),
    lens TEXT NOT NULL DEFAULT 'genny',
    delivered_at TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'email'
);

CREATE TABLE IF NOT EXISTS rejections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL UNIQUE,
    reason TEXT NOT NULL DEFAULT '',
    rejected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_source_runs_source ON source_runs(source_id);
"""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (creating if needed) the newsroom database with the schema applied."""
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    conn.execute(
        "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
    return conn


def upsert_source(conn: sqlite3.Connection, source: Mapping[str, Any]) -> int:
    """Insert or update a source by its unique url. Returns the source id.

    Health fields are never overwritten here; only the scorer mutates those.
    """
    tier = str(source.get("tier", "")).strip()
    if tier not in VALID_TIERS:
        raise ValueError(f"unknown tier {tier!r}; expected one of {sorted(VALID_TIERS)}")
    now = _now()
    conn.execute(
        """
        INSERT INTO sources(name, url, feed_url, tier, vertical, priority,
                            daily_intake, created_at, updated_at)
        VALUES(:name, :url, :feed_url, :tier, :vertical, :priority,
               :daily_intake, :now, :now)
        ON CONFLICT(url) DO UPDATE SET
            name = excluded.name,
            feed_url = excluded.feed_url,
            tier = excluded.tier,
            vertical = excluded.vertical,
            priority = excluded.priority,
            daily_intake = excluded.daily_intake,
            updated_at = excluded.updated_at
        """,
        {
            "name": str(source.get("name", "")),
            "url": str(source["url"]),
            "feed_url": str(source.get("feed_url", "")),
            "tier": tier,
            "vertical": str(source.get("vertical", "")),
            "priority": str(source.get("priority", "medium")),
            "daily_intake": 1 if source.get("daily_intake", True) else 0,
            "now": now,
        },
    )
    conn.commit()
    row = conn.execute("SELECT id FROM sources WHERE url = ?", (str(source["url"]),)).fetchone()
    return int(row["id"])


def record_source_run(
    conn: sqlite3.Connection,
    source_id: int,
    *,
    ok: bool,
    candidates_found: int = 0,
    failure_reason: str | None = None,
) -> None:
    """Log one refresh attempt and roll it into the source's health counters."""
    now = _now()
    conn.execute(
        "INSERT INTO source_runs(source_id, ran_at, ok, candidates_found, failure_reason) "
        "VALUES(?, ?, ?, ?, ?)",
        (source_id, now, 1 if ok else 0, candidates_found, failure_reason),
    )
    conn.execute(
        """
        UPDATE sources SET
            fetch_attempts = fetch_attempts + 1,
            fetch_successes = fetch_successes + ?,
            last_failure_reason = CASE WHEN ? THEN last_failure_reason ELSE ? END,
            updated_at = ?
        WHERE id = ?
        """,
        (1 if ok else 0, 1 if ok else 0, failure_reason, now, source_id),
    )
    conn.commit()


def is_rejected(conn: sqlite3.Connection, fingerprint: str) -> bool:
    """Negative memory: has this exact story been killed before?"""
    row = conn.execute(
        "SELECT 1 FROM rejections WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    return row is not None


def add_candidate(conn: sqlite3.Connection, candidate: Mapping[str, Any]) -> int | None:
    """Add a harvested candidate. Returns its id, or None if it is a known
    rejection (negative memory) or a duplicate fingerprint already stored."""
    fingerprint = str(candidate["fingerprint"])
    if is_rejected(conn, fingerprint):
        return None
    existing = conn.execute(
        "SELECT id FROM candidates WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    if existing is not None:
        return None
    cur = conn.execute(
        """
        INSERT INTO candidates(source_id, fingerprint, url, title, summary,
                               vertical, published_at, status, harvested_at)
        VALUES(:source_id, :fingerprint, :url, :title, :summary,
               :vertical, :published_at, 'new', :now)
        """,
        {
            "source_id": candidate.get("source_id"),
            "fingerprint": fingerprint,
            "url": str(candidate.get("url", "")),
            "title": str(candidate.get("title", "")),
            "summary": str(candidate.get("summary", "")),
            "vertical": str(candidate.get("vertical", "")),
            "published_at": candidate.get("published_at"),
            "now": _now(),
        },
    )
    conn.commit()
    return int(cur.lastrowid)


def record_review(
    conn: sqlite3.Connection,
    candidate_id: int,
    *,
    accepted: bool,
    score: int = 0,
    reason: str = "",
) -> None:
    """Store a verifier verdict, update candidate status, and on rejection add
    the fingerprint to negative memory so it never resurfaces."""
    now = _now()
    conn.execute(
        "INSERT INTO signal_reviews(candidate_id, accepted, score, reason, reviewed_at) "
        "VALUES(?, ?, ?, ?, ?)",
        (candidate_id, 1 if accepted else 0, score, reason, now),
    )
    status = "verified" if accepted else "rejected"
    conn.execute("UPDATE candidates SET status = ? WHERE id = ?", (status, candidate_id))
    if accepted:
        conn.execute(
            """
            UPDATE sources SET qualified_candidates = qualified_candidates + 1,
                               last_signal_at = ?, updated_at = ?
            WHERE id = (SELECT source_id FROM candidates WHERE id = ?)
            """,
            (now, now, candidate_id),
        )
    else:
        row = conn.execute(
            "SELECT fingerprint FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if row is not None:
            conn.execute(
                "INSERT INTO rejections(fingerprint, reason, rejected_at) VALUES(?, ?, ?) "
                "ON CONFLICT(fingerprint) DO NOTHING",
                (row["fingerprint"], reason, now),
            )
    conn.commit()


def verified_candidates(
    conn: sqlite3.Connection, vertical: str | None = None
) -> list[sqlite3.Row]:
    """The daily editor reads these: verified, not-yet-published candidates."""
    if vertical is None:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE status = 'verified' "
            "ORDER BY published_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM candidates WHERE status = 'verified' AND vertical = ? "
            "ORDER BY published_at DESC",
            (vertical,),
        ).fetchall()
    return list(rows)


def record_delivery(
    conn: sqlite3.Connection,
    candidate_id: int,
    *,
    lens: str = "genny",
    channel: str = "email",
) -> None:
    """Mark a candidate published so it is not sent again."""
    now = _now()
    conn.execute(
        "INSERT INTO deliveries(candidate_id, lens, delivered_at, channel) VALUES(?, ?, ?, ?)",
        (candidate_id, lens, now, channel),
    )
    conn.execute("UPDATE candidates SET status = 'published' WHERE id = ?", (candidate_id,))
    conn.commit()


def source_health(conn: sqlite3.Connection, source_id: int) -> dict[str, Any]:
    """Derived health for the scorer: rates from the accumulated counters."""
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if row is None:
        raise KeyError(f"no source {source_id}")
    attempts = row["fetch_attempts"] or 0
    fetch_rate = (row["fetch_successes"] / attempts) if attempts else 0.0
    return {
        "source_id": source_id,
        "name": row["name"],
        "tier": row["tier"],
        "fetch_success_rate": round(fetch_rate, 3),
        "qualified_candidates": row["qualified_candidates"],
        "duplicate_candidates": row["duplicate_candidates"],
        "last_signal_at": row["last_signal_at"],
        "last_failure_reason": row["last_failure_reason"],
    }


def import_registry_sources(
    conn: sqlite3.Connection, registry: Mapping[str, Any], *, default_tier: str = "first_party"
) -> int:
    """Seed the store from an existing genny_sources.json-style registry.

    A source keeps an explicit `tier` if present; otherwise it is classified by
    a light heuristic (news_search -> discovery, blank feed homepage -> the
    default tier). Returns the number of sources imported. Feed verification and
    fine reclassification happen later, on the VPS, per the rollout.
    """
    count = 0
    for vertical, sources in registry.get("verticals", {}).items():
        for source in sources:
            tier = str(source.get("tier", "")).strip()
            if tier not in VALID_TIERS:
                if source.get("source_type") == "news_search":
                    tier = "discovery"
                else:
                    tier = default_tier
            feed = str(source.get("rss") or "").strip()
            upsert_source(
                conn,
                {
                    "name": source.get("name", ""),
                    "url": source.get("url", ""),
                    "feed_url": feed,
                    "tier": tier,
                    "vertical": vertical,
                    "priority": source.get("priority", "medium"),
                    "daily_intake": bool(feed) or tier == "first_party",
                },
            )
            count += 1
    return count
