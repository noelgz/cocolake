from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import struct_time

import httpx

from pipeline.config import HTTP_TIMEOUT, HTTP_HEADERS


def http_client() -> httpx.AsyncClient:
    """HTTP client with our default settings"""
    return httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        headers=HTTP_HEADERS,
        follow_redirects=True,
    )


def parse_date(raw: str | struct_time | datetime | None) -> str | None:
    """Turn many date formats into one ISO string"""
    if not raw:
        return None

    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, struct_time):
        dt = datetime(*raw[:6], tzinfo=timezone.utc)
    else:
        text = str(raw).strip()
        if not text:
            return None

        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            try:
                dt = parsedate_to_datetime(text)
            except (TypeError, ValueError, IndexError):
                return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


def strip_html(text: str) -> str:
    """Remove HTML tags and extra spaces"""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def truncate(text: str, max_len: int = 1500) -> str:
    """Cut text at max_len when it gets too long"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"
