from __future__ import annotations

import logging

import httpx

from pipeline.sources.base import BaseSource
from pipeline.utils import parse_date

logger = logging.getLogger(__name__)

_MIN_POINTS = 5


class HackerNewsSource(BaseSource):
    name = "Hacker News"

    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        query = kwargs.get("query", "data engineering")
        try:
            resp = await http.get(
                "https://hn.algolia.com/api/v1/search_by_date",
                params={"query": query, "tags": "story", "hitsPerPage": 10},
            )
            resp.raise_for_status()
            return [
                hit for hit in resp.json().get("hits", [])
                if (hit.get("points") or 0) >= _MIN_POINTS
            ]
        except Exception as exc:
            logger.warning("HN search '%s' failed: %s", query, exc)
            return []

    def parse_entry(self, raw: dict) -> dict:
        url = raw.get("url") or f"https://news.ycombinator.com/item?id={raw['objectID']}"
        return {
            "title": raw.get("title", ""),
            "url": url,
            "source": "Hacker News",
            "published_at": parse_date(raw.get("created_at")),
            "content": raw.get("story_text", "") or "",
            "points": raw.get("points", 0),
        }


_source = HackerNewsSource()


async def search_hackernews(query: str) -> list[dict]:
    return await _source.collect(query=query)
