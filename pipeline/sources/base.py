from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from pipeline.utils import http_client

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Base source that fetches data and turns it into articles"""

    name: str = "Unknown"

    @abstractmethod
    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        """Fetch raw items from the external source"""
        ...

    @abstractmethod
    def parse_entry(self, raw: dict) -> dict:
        """Turn one raw item into the article shape we use"""
        ...

    async def collect(self, **kwargs) -> list[dict]:
        """Common flow: fetch, parse, and return valid articles"""
        async with http_client() as http:
            raw_entries = await self.fetch_raw(http, **kwargs)

        articles = []
        for entry in raw_entries:
            try:
                article = self.parse_entry(entry)
                if article.get("title"):
                    articles.append(article)
            except Exception as exc:
                logger.warning("%s: failed to parse entry: %s", self.name, exc)

        logger.info("%s: collected %d articles", self.name, len(articles))
        return articles
