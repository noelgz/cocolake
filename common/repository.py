from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from common.db import get_pool
from common.models import Article

logger = logging.getLogger(__name__)
__all__ = [
    "load_sources",
    "add_source",
    "toggle_source",
    "insert_articles",
    "get_recent_article_urls",
    "save_digest",
    "get_latest_digest",
    "get_digest_by_date",
    "get_available_dates",
]


def _row_to_source(row) -> dict:
    data = dict(row)
    if isinstance(data.get("config"), str):
        data["config"] = json.loads(data["config"])
    return data


async def load_sources(*, enabled_only: bool = True) -> list[dict]:
    """Load source configs from the database"""
    pool = await get_pool()
    where = "WHERE enabled = TRUE" if enabled_only else ""
    rows = await pool.fetch(
        f"SELECT id, name, source_type, config, enabled FROM sources {where} ORDER BY id"
    )
    return [_row_to_source(row) for row in rows]


async def add_source(name: str, source_type: str, config: dict) -> dict:
    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO sources (name, source_type, config)
           VALUES ($1, $2, $3::jsonb)
           RETURNING id, name, source_type, config, enabled""",
        name,
        source_type,
        json.dumps(config),
    )
    return _row_to_source(row)


async def toggle_source(source_id: int, enabled: bool) -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        """UPDATE sources SET enabled = $2, updated_at = NOW()
           WHERE id = $1
           RETURNING id, name, source_type, config, enabled""",
        source_id,
        enabled,
    )
    return _row_to_source(row) if row else None


async def insert_articles(articles: list[dict]) -> list[int]:
    """Save curated articles and reuse old URLs when needed"""
    pool = await get_pool()
    article_ids: list[int] = []
    seen_urls: set[str] = set()
    skipped_duplicates = 0
    reused_existing = 0

    async with pool.acquire() as conn:
        for article in articles:
            try:
                validated = Article(**article)
            except Exception as exc:
                logger.warning(
                    "Skipping invalid article '%s': %s",
                    article.get("title", "?"),
                    exc,
                )
                continue

            url = validated.url.strip()
            if url in seen_urls:
                skipped_duplicates += 1
                continue
            seen_urls.add(url)

            row = await conn.fetchrow(
                """INSERT INTO articles (
                       url, title, source_name, published_at,
                       raw_content, category, summary_en, summary_es,
                       relevance_score, tags
                   )
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (url) DO NOTHING
                   RETURNING id""",
                url,
                validated.title,
                validated.source,
                _parse_ts(validated.published_at),
                article.get("content", ""),
                validated.category,
                validated.summary_en,
                validated.summary_es,
                validated.relevance_score,
                validated.tags,
            )
            if row is None:
                row = await conn.fetchrow(
                    "SELECT id FROM articles WHERE url = $1",
                    url,
                )
                reused_existing += 1
            article_ids.append(row["id"])

    logger.info(
        "Stored %d article references (%d duplicate URLs skipped in input, %d reused existing rows)",
        len(article_ids),
        skipped_duplicates,
        reused_existing,
    )
    return article_ids


async def get_recent_article_urls(days: int = 3) -> set[str]:
    """Get article URLs seen in the last N days"""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT url FROM articles
           WHERE first_seen_at >= NOW() - make_interval(days => $1)""",
        days,
    )
    return {row["url"] for row in rows}


async def save_digest(
    article_ids: list[int],
    total_collected: int = 0,
    sources_checked: int = 0,
) -> int:
    """Create today's digest and link its articles"""
    pool = await get_pool()
    today = datetime.now(timezone.utc).date()

    unique_article_ids = list(dict.fromkeys(article_ids))

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO digests (date, total_sources_checked,
                       total_raw_collected, total_published)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (date) DO UPDATE SET
                       generated_at = NOW(),
                       total_sources_checked = EXCLUDED.total_sources_checked,
                       total_raw_collected = EXCLUDED.total_raw_collected,
                       total_published = EXCLUDED.total_published
                   RETURNING id""",
                today,
                sources_checked,
                total_collected,
                len(unique_article_ids),
            )
            digest_id = row["id"]

            await conn.execute(
                "DELETE FROM digest_articles WHERE digest_id = $1",
                digest_id,
            )

            for pos, article_id in enumerate(unique_article_ids):
                await conn.execute(
                    """INSERT INTO digest_articles (digest_id, article_id, position)
                       VALUES ($1, $2, $3)""",
                    digest_id,
                    article_id,
                    pos,
                )

    logger.info("Saved digest %s with %d articles", today, len(unique_article_ids))
    return digest_id


async def get_latest_digest() -> dict | None:
    """Return the newest digest with its articles"""
    pool = await get_pool()
    digest_row = await pool.fetchrow(
        "SELECT * FROM digests ORDER BY date DESC LIMIT 1"
    )
    if not digest_row:
        return None
    return await _digest_with_articles(dict(digest_row))


async def get_digest_by_date(date_str: str) -> dict | None:
    pool = await get_pool()
    digest_row = await pool.fetchrow(
        "SELECT * FROM digests WHERE date = $1",
        date_str,
    )
    if not digest_row:
        return None
    return await _digest_with_articles(dict(digest_row))


async def get_available_dates() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT date FROM digests ORDER BY date DESC"
    )
    return [row["date"].isoformat() for row in rows]


async def _digest_with_articles(digest: dict) -> dict:
    """Add articles to a digest dict"""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT a.* FROM articles a
           JOIN digest_articles da ON da.article_id = a.id
           WHERE da.digest_id = $1
           ORDER BY da.position""",
        digest["id"],
    )
    articles = []
    for row in rows:
        articles.append({
            "title": row["title"],
            "url": row["url"],
            "source": row["source_name"],
            "published_at": row["published_at"].isoformat() if row["published_at"] else None,
            "category": row["category"],
            "summary_en": row["summary_en"],
            "summary_es": row["summary_es"],
            "relevance_score": row["relevance_score"],
            "tags": row["tags"],
        })

    return {
        "date": digest["date"].isoformat() if hasattr(digest["date"], "isoformat") else digest["date"],
        "generated_at": digest["generated_at"].isoformat(),
        "total_sources_checked": digest["total_sources_checked"],
        "total_raw_collected": digest["total_raw_collected"],
        "total_published": digest["total_published"],
        "articles": articles,
    }


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
