from __future__ import annotations

import logging

import httpx

from pipeline.sources.base import BaseSource
from pipeline.utils import parse_date, truncate

logger = logging.getLogger(__name__)


class DevtoSource(BaseSource):
    name = "Dev.to"

    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        tag = kwargs.get("tag", "dataengineering")
        try:
            resp = await http.get(
                "https://dev.to/api/articles",
                params={"tag": tag, "top": 1, "per_page": 10},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Dev.to tag '%s' failed: %s", tag, exc)
            return []

    def parse_entry(self, raw: dict) -> dict:
        return {
            "title": raw.get("title", ""),
            "url": raw.get("url", ""),
            "source": "Dev.to",
            "published_at": parse_date(raw.get("published_at")),
            "content": truncate(raw.get("description") or ""),
            "tags": raw.get("tag_list", []),
        }


_source = DevtoSource()


async def search_devto(tag: str) -> list[dict]:
    return await _source.collect(tag=tag)
