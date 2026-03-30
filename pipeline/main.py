from __future__ import annotations

import asyncio
import logging
import os
import unicodedata
import sys
from collections import Counter
from datetime import datetime, timezone

from pipeline.config import (
    LLM_CONTEXT_ARTICLE_LIMIT,
    LLM_CONTEXT_CONTENT_CHARS,
    MAX_ARTICLE_AGE_DAYS,
    MAX_ARTICLES_FINAL,
    MIN_ARTICLES_AFTER_FRESHNESS_FILTER,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_CATEGORY_KEYWORDS = {
    "AWS": ["redshift", "s3 ", "glue", "athena", "emr", "lake formation", "kinesis", "sagemaker"],
    "Data Engineering": ["pipeline", "etl", "elt", "airflow", "dagster", "dbt", "iceberg", "spark", "kafka", "flink", "orchestrat"],
    "Analytics": ["analytics", "warehouse", "dashboard", "looker", "tableau", "metabase", "bi ", "superset"],
    "ML/AI": ["machine learning", "mlops", "feature store", "model serving", "llm", "vector", "embedding"],
    "Open Source Tools": ["open source", "open-source", "release", "github", "apache"],
    "Case Studies": ["case study", "how we", "migration", "architecture", "scale"],
}
_TRANSLITERATED_NON_TARGET_MARKERS = (
    "masshtab",
    "pierievod",
    "arkhit",
    "razrabot",
    "dlia",
    "komand",
    "vnutri",
    "prakhtik",
    "poshag",
)


async def run_pipeline():
    from dotenv import load_dotenv
    load_dotenv()

    from pipeline.agents import create_editor
    from pipeline.config import GEMINI_API_KEY
    from common.source_plugins import collect_source, validate_source_config
    from common.db import close_pool, run_migrations
    from common import repository

    # Start the database bits first!
    logger.info("Initializing database...")
    await run_migrations()

    # Load sources from DB
    sources = await repository.load_sources()
    logger.info("Loaded %d sources from database", len(sources))

    valid_sources = []
    for source in sources:
        cfg = source["config"] if isinstance(source.get("config"), dict) else {}
        try:
            cfg = validate_source_config(source["source_type"], cfg)
        except ValueError as exc:
            logger.warning("Skipping invalid source '%s': %s", source.get("name", "?"), exc)
            continue

        normalized = {**source, "config": cfg}
        valid_sources.append(normalized)

    source_counts = Counter(source["source_type"] for source in valid_sources)
    counts_text = ", ".join(
        f"{source_type}={count}"
        for source_type, count in sorted(source_counts.items())
    ) or "no valid sources"
    logger.info(
        "Validated %d sources (%s)",
        len(valid_sources),
        counts_text,
    )

    use_llm = os.getenv("USE_LLM", "true").lower() == "true" and bool(GEMINI_API_KEY)
    if not use_llm:
        logger.info("Running in rule-based editorial mode (LLM disabled or API key missing)")

    # Step 1: collect articles
    logger.info("Collecting from all configured sources...")
    raw_articles, collection_stats = await _collect_articles(
        collect_source=collect_source,
        sources=valid_sources,
    )

    raw_articles = [article for article in raw_articles if isinstance(article, dict) and article.get("title")]
    raw_articles, duplicate_count = _dedupe_articles(raw_articles)
    if duplicate_count:
        logger.info("Dropped %d duplicate raw articles before curation", duplicate_count)

    recent_articles, stale_count = _filter_recent_articles(raw_articles)
    if stale_count:
        if len(recent_articles) >= min(MIN_ARTICLES_AFTER_FRESHNESS_FILTER, len(raw_articles)):
            logger.info(
                "Dropped %d stale articles older than %d days",
                stale_count,
                MAX_ARTICLE_AGE_DAYS,
            )
            raw_articles = recent_articles
        else:
            logger.warning(
                "Freshness filter would leave only %d/%d articles, keeping original set for coverage",
                len(recent_articles),
                len(raw_articles),
            )

    raw_articles, language_rejections = _filter_supported_language_articles(raw_articles)
    if language_rejections:
        preview = [
            f"{reason}: {article.get('title', '?')[:70]}"
            for article, reason in language_rejections[:3]
        ]
        logger.info(
            "Dropped %d article(s) outside the supported language filter: %s",
            len(language_rejections),
            preview,
        )

    if collection_stats["attempted"] and collection_stats["succeeded"] == 0 and raw_articles:
        observed_sources = len({article.get("source") for article in raw_articles if article.get("source")})
        collection_stats["succeeded"] = min(collection_stats["attempted"], observed_sources)
        collection_stats["failed"] = max(
            0,
            collection_stats["attempted"] - collection_stats["succeeded"],
        )

    raw_articles.sort(key=_published_sort_key, reverse=True)
    total = len(raw_articles)
    logger.info(
        "Collected %d usable raw articles (sources attempted=%d, succeeded=%d, empty_or_failed=%d)",
        total,
        collection_stats["attempted"],
        collection_stats["succeeded"],
        collection_stats["failed"],
    )

    if not raw_articles:
        logger.error("No articles collected — aborting")
        await close_pool()
        return

    # Step 2: curate and summarize
    sources_checked = collection_stats["attempted"] or len({a.get("source") for a in raw_articles if a.get("source")})

    if use_llm:
        context = _build_editor_context(raw_articles)
        logger.info(
            "Sending %d of %d article(s) to the editor with up to %d chars per article",
            len(context),
            len(raw_articles),
            LLM_CONTEXT_CONTENT_CHARS,
        )

        editor = create_editor()
        digest = await editor.run(
            f"Curate these {len(context)} articles into the daily Cocolake digest.",
            context=context,
        )
    else:
        digest = _rule_based_curate(raw_articles)

    if not isinstance(digest, list) or not digest:
        logger.warning("Editor returned empty/invalid — switching to rule-based curation")
        digest = _rule_based_curate(raw_articles)
    else:
        digest = _postprocess_digest(digest)
        if not digest:
            logger.warning("Post-processing removed all editor articles — switching to rule-based curation")
            digest = _rule_based_curate(raw_articles)

    # Step 3: save to DB
    article_ids = await repository.insert_articles(digest)
    await repository.save_digest(
        article_ids=article_ids,
        total_collected=total,
        sources_checked=sources_checked,
    )

    await close_pool()
    logger.info("Pipeline complete")


def _rule_based_curate(articles: list[dict]) -> list[dict]:
    """Pick articles with keywords when the LLM is off or fails"""
    scored = []
    for article in articles:
        if not _is_supported_publication_language(article):
            continue

        best_cat, best_hits = _best_category_match(article)

        if best_hits == 0:
            continue

        scored.append({
            **article,
            "category": best_cat,
            "relevance_score": round(
                min(1.0, 0.4 + best_hits * 0.12) * _freshness_multiplier(article.get("published_at")),
                3,
            ),
            "summary_en": (article.get("content") or article["title"])[:250],
            "summary_es": (article.get("content") or article["title"])[:250],
            "tags": [],
        })

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored[:MAX_ARTICLES_FINAL]


def _build_editor_context(articles: list[dict]) -> list[dict]:
    candidates = [_context_candidate(article) for article in articles]
    candidates.sort(
        key=lambda candidate: (
            candidate["priority_score"],
            candidate["published_sort_key"],
        ),
        reverse=True,
    )

    selected: list[dict] = []
    selected_keys: set[str] = set()
    source_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for candidate in candidates:
        if len(selected) >= LLM_CONTEXT_ARTICLE_LIMIT:
            break
        if source_counts[candidate["source"]] > 0:
            continue
        _append_context_candidate(
            selected,
            selected_keys,
            source_counts,
            category_counts,
            candidate,
        )

    remaining = [
        candidate
        for candidate in candidates
        if _article_key(candidate["article"]) not in selected_keys
    ]

    while remaining and len(selected) < LLM_CONTEXT_ARTICLE_LIMIT:
        best_idx = max(
            range(len(remaining)),
            key=lambda index: _context_selection_key(
                remaining[index],
                source_counts=source_counts,
                category_counts=category_counts,
            ),
        )
        candidate = remaining.pop(best_idx)
        _append_context_candidate(
            selected,
            selected_keys,
            source_counts,
            category_counts,
            candidate,
        )

    logger.info(
        "Editor context mix: %s",
        ", ".join(
            f"{source}={count}"
            for source, count in sorted(source_counts.items())
        ) or "no sources",
    )
    return selected


def _best_category_match(article: dict) -> tuple[str, int]:
    text = f"{article.get('title', '')} {article.get('content', '')}".lower()

    best_cat = ""
    best_hits = 0
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_cat = cat

    return best_cat, best_hits


def _context_candidate(article: dict) -> dict:
    best_cat, best_hits = _best_category_match(article)
    return {
        "article": article,
        "source": str(article.get("source") or "Unknown"),
        "category": best_cat or "General",
        "priority_score": round(
            (1.0 + best_hits) * _freshness_multiplier(article.get("published_at")),
            3,
        ),
        "published_sort_key": _published_sort_key(article),
    }


def _context_selection_key(
    candidate: dict,
    *,
    source_counts: Counter[str],
    category_counts: Counter[str],
) -> tuple[float, float, float, float]:
    return (
        -float(source_counts[candidate["source"]]),
        -float(category_counts[candidate["category"]]),
        candidate["priority_score"],
        candidate["published_sort_key"],
    )


def _append_context_candidate(
    selected: list[dict],
    selected_keys: set[str],
    source_counts: Counter[str],
    category_counts: Counter[str],
    candidate: dict,
) -> None:
    article = candidate["article"]
    key = _article_key(article)
    if key in selected_keys:
        return

    selected.append(_truncate_context_article(article))
    selected_keys.add(key)
    source_counts[candidate["source"]] += 1
    category_counts[candidate["category"]] += 1


def _truncate_context_article(article: dict) -> dict:
    slim = {**article}
    content = slim.get("content")
    if content and len(content) > LLM_CONTEXT_CONTENT_CHARS:
        slim["content"] = content[:LLM_CONTEXT_CONTENT_CHARS] + "…"
    return slim


async def _collect_articles(
    *,
    collect_source,
    sources: list[dict],
) -> tuple[list[dict], dict]:
    raw_articles: list[dict] = []
    stats = {"attempted": 0, "succeeded": 0, "failed": 0, "details": []}

    for source in sources:
        try:
            articles = await collect_source(source)
        except Exception as exc:
            logger.warning(
                "Source '%s' (%s) failed during collection: %s",
                source.get("name", "?"),
                source.get("source_type", "?"),
                exc,
            )
            articles = []

        raw_articles.extend(articles)
        _record_source_stat(
            stats,
            name=source["name"],
            source_type=source["source_type"],
            count=len(articles),
        )

    return raw_articles, stats


def _record_source_stat(stats: dict, *, name: str, source_type: str, count: int) -> None:
    stats["attempted"] += 1
    if count > 0:
        stats["succeeded"] += 1
    else:
        stats["failed"] += 1
    stats["details"].append({
        "name": name,
        "source_type": source_type,
        "count": count,
    })


def _dedupe_articles(articles: list[dict]) -> tuple[list[dict], int]:
    deduped = []
    seen: set[str] = set()
    duplicates = 0

    for article in articles:
        key = _article_key(article)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(article)

    return deduped, duplicates


def _article_key(article: dict) -> str:
    url = str(article.get("url", "")).strip()
    if url:
        return url
    title = str(article.get("title", "")).strip().lower()
    source = str(article.get("source", "")).strip().lower()
    return f"{source}:{title}"


def _filter_supported_language_articles(
    articles: list[dict],
) -> tuple[list[dict], list[tuple[dict, str]]]:
    kept = []
    rejected = []
    for article in articles:
        reason = _language_filter_reason(article)
        if reason:
            rejected.append((article, reason))
            continue
        kept.append(article)
    return kept, rejected


def _is_supported_publication_language(article: dict) -> bool:
    return _language_filter_reason(article) is None


def _language_filter_reason(article: dict) -> str | None:
    text = _article_language_text(article)
    lower = text.lower()

    if not _looks_latin_friendly(text):
        return "non_latin_script"

    transliterated_hits = sum(1 for marker in _TRANSLITERATED_NON_TARGET_MARKERS if marker in lower)
    if transliterated_hits >= 2:
        return "transliterated_local_language"

    return None


def _article_language_text(article: dict) -> str:
    tags = article.get("tags") or []
    tags_text = " ".join(str(tag) for tag in tags) if isinstance(tags, list) else ""
    return " ".join(
        str(value)
        for value in (
            article.get("title", ""),
            article.get("url", ""),
            article.get("content", ""),
            tags_text,
            article.get("source", ""),
        )
        if value
    )


def _looks_latin_friendly(text: str) -> bool:
    total_letters = 0
    non_latin_letters = 0

    for char in text:
        if not char.isalpha():
            continue
        total_letters += 1
        try:
            unicode_name = unicodedata.name(char)
        except ValueError:
            continue
        if "LATIN" not in unicode_name:
            non_latin_letters += 1

    if total_letters == 0:
        return True

    return (non_latin_letters / total_letters) <= 0.15


def _filter_recent_articles(
    articles: list[dict],
    *,
    max_age_days: int = MAX_ARTICLE_AGE_DAYS,
    now: datetime | None = None,
) -> tuple[list[dict], int]:
    recent = []
    stale = 0
    for article in articles:
        age = _article_age_days(article, now=now)
        if age is not None and age > max_age_days:
            stale += 1
            continue
        recent.append(article)
    return recent, stale


def _article_age_days(article: dict, *, now: datetime | None = None) -> float | None:
    published_at = _parse_datetime(article.get("published_at"))
    if published_at is None:
        return None
    current_time = now or datetime.now(timezone.utc)
    age_seconds = max(0.0, (current_time - published_at).total_seconds())
    return age_seconds / 86_400


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _freshness_multiplier(published_at: str | None) -> float:
    age = _article_age_days({"published_at": published_at})
    if age is None:
        return 0.9
    if age <= 1:
        return 1.0
    if age <= 3:
        return 0.96
    if age <= 7:
        return 0.9
    if age <= 14:
        return 0.75
    return 0.55


def _published_sort_key(article: dict) -> float:
    published_at = _parse_datetime(article.get("published_at"))
    return published_at.timestamp() if published_at else float("-inf")


def _postprocess_digest(digest: list[dict]) -> list[dict]:
    cleaned, _ = _dedupe_articles([
        article for article in digest
        if isinstance(article, dict) and article.get("title") and article.get("url")
    ])
    cleaned, _ = _filter_supported_language_articles(cleaned)

    normalized = []
    for article in cleaned:
        adjusted_score = float(article.get("relevance_score", 0.5) or 0.5)
        adjusted_score *= _freshness_multiplier(article.get("published_at"))
        normalized.append({
            **article,
            "relevance_score": round(max(0.0, min(1.0, adjusted_score)), 3),
            "tags": article.get("tags") or [],
        })

    normalized.sort(
        key=lambda article: (
            article.get("relevance_score", 0.0),
            _published_sort_key(article),
        ),
        reverse=True,
    )
    return normalized[:MAX_ARTICLES_FINAL]


def main():
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    sys.exit(main() or 0)
