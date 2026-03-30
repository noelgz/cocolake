"""RSS source that reads articles from feed URLs"""

from __future__ import annotations

import logging

import feedparser
import httpx

from pipeline.sources.base import BaseSource
from pipeline.utils import parse_date, strip_html, truncate

logger = logging.getLogger(__name__)


class RSSSource(BaseSource):
    name = "RSS"

    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        feeds = kwargs.get("feeds")
        if not feeds and kwargs.get("url"):
            feeds = {kwargs.get("feed_name", "Unknown"): kwargs["url"]}
        if not feeds:
            return []
        entries = []
        for feed_name, url in feeds.items():
            try:
                resp = await http.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:10]:
                    entry["_feed_name"] = feed_name
                    entries.append(entry)
            except Exception as exc:
                logger.warning("RSS '%s' failed: %s", feed_name, exc)
        return entries

    def parse_entry(self, raw: dict) -> dict:
        content = raw.get("summary", "") or ""
        if hasattr(raw, "content") and raw.content:
            content = raw.content[0].get("value", content)
        published = (
            raw.get("published")
            or raw.get("updated")
            or raw.get("published_parsed")
            or raw.get("updated_parsed")
        )

        return {
            "title": raw.get("title", "").strip(),
            "url": raw.get("link", ""),
            "source": f"RSS: {raw.get('_feed_name', 'Unknown')}",
            "published_at": parse_date(published),
            "content": truncate(strip_html(content)),
        }


_source = RSSSource()


async def fetch_rss_feed(feed_name: str, url: str) -> list[dict]:
    return await _source.collect(feed_name=feed_name, url=url)


async def fetch_rss_feeds(feeds: dict[str, str]) -> list[dict]:
    return await _source.collect(feeds=feeds)
