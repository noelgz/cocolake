from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import httpx

from pipeline.sources.base import BaseSource
from pipeline.utils import parse_date

logger = logging.getLogger(__name__)


class GitHubTrendingSource(BaseSource):
    name = "GitHub Trending"

    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        language = kwargs.get("language", "python")
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        try:
            resp = await http.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": f"language:{language} created:>{since} stars:>5",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10,
                },
            )
            resp.raise_for_status()
            return resp.json().get("items", [])
        except Exception as exc:
            logger.warning("GitHub '%s' failed: %s", language, exc)
            return []

    def parse_entry(self, raw: dict) -> dict:
        return {
            "title": raw["full_name"],
            "url": raw["html_url"],
            "source": f"GitHub ({raw.get('language', 'unknown')})",
            "published_at": parse_date(raw.get("created_at")),
            "content": f"{raw.get('description', '')}. ⭐ {raw['stargazers_count']} stars.",
            "tags": [raw.get("language", ""), "open-source"],
        }


_source = GitHubTrendingSource()


async def search_github(language: str) -> list[dict]:
    return await _source.collect(language=language)
