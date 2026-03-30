"""Web scraper source for real blog pages!

Flow:
1. Get the HTML from the page
2. Try normal HTML parsing with BeautifulSoup
3. If that gives too little, try Gemini as backup
"""

from __future__ import annotations

import json
import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from pipeline.sources.base import BaseSource
from pipeline.utils import http_client, strip_html, truncate

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """\
Extract all blog post articles from this HTML page.
For each article return a JSON object with:
- title (string)
- url (absolute URL, use base_url if needed)
- published_at (ISO date string if visible, else null)
- content (first 300 chars of the article text)

base_url: {base_url}

Return ONLY a JSON array of objects. No markdown, no explanation.

HTML (truncated):
{html}"""


class WebScraperSource(BaseSource):
    name = "Web Scraper"

    async def fetch_raw(self, http: httpx.AsyncClient, **kwargs) -> list[dict]:
        url = kwargs.get("url", "")
        if not url:
            return []

        try:
            resp = await http.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as exc:
            logger.warning("Web scraper failed to fetch '%s': %s", url, exc)
            return []

        # Try normal HTML parsing first
        articles = self._structural_parse(html, url)

        if len(articles) >= 3:
            logger.info("Web scraper: structural parse found %d articles from %s", len(articles), url)
            return articles

        # If that was weak, try the LLM
        logger.info("Web scraper: structural parse found only %d, trying LLM for %s", len(articles), url)
        llm_articles = await self._llm_extract(html, url)
        return llm_articles if llm_articles else articles

    def _structural_parse(self, html: str, base_url: str) -> list[dict]:
        """Find articles with common HTML patterns"""
        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # Look for links inside blocks that feel like articles
        selectors = [
            "article",
            "[class*='post']",
            "[class*='article']",
            "[class*='entry']",
            "[class*='blog']",
            "[class*='card']",
        ]

        for selector in selectors:
            for container in soup.select(selector):
                link = container.find("a", href=True)
                if not link:
                    continue

                href = urljoin(base_url, link["href"])
                if href in seen_urls or href == base_url:
                    continue
                seen_urls.add(href)

                # Try heading tags first, then use the link text
                title_el = container.find(["h1", "h2", "h3", "h4"])
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                # Try to get a short text too
                snippet_el = container.find("p")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                # Try to get the date
                time_el = container.find("time")
                date = time_el.get("datetime", "") if time_el else ""

                articles.append({
                    "title": title,
                    "url": href,
                    "published_at": date or None,
                    "content": truncate(snippet, 500),
                    "_source_url": base_url,
                })

            if articles:
                break  # First good selector is enough here

        return articles

    async def _llm_extract(self, html: str, base_url: str) -> list[dict]:
        """Use Gemini to pull articles from the page HTML"""
        try:
            from pipeline import llm
        except Exception:
            return []

        # Keep the HTML short enough for the prompt
        soup = BeautifulSoup(html, "lxml")
        # Drop noisy parts first
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        clean_html = soup.get_text(separator="\n", strip=True)
        if len(clean_html) > 15000:
            clean_html = clean_html[:15000]

        prompt = _EXTRACT_PROMPT.format(base_url=base_url, html=clean_html)

        try:
            result = await llm.ask_json(prompt)
            if isinstance(result, list):
                articles = []
                for item in result:
                    if isinstance(item, dict) and item.get("title") and item.get("url"):
                        item["url"] = urljoin(base_url, item["url"])
                        item["_source_url"] = base_url
                        articles.append(item)
                logger.info("Web scraper LLM: extracted %d articles from %s", len(articles), base_url)
                return articles
        except Exception as exc:
            logger.warning("Web scraper LLM extraction failed for %s: %s", base_url, exc)

        return []

    def parse_entry(self, raw: dict) -> dict:
        source_url = raw.get("_source_url", "Unknown")
        # Pull the domain for display
        try:
            from urllib.parse import urlparse
            domain = urlparse(source_url).netloc.replace("www.", "")
        except Exception:
            domain = source_url

        return {
            "title": raw.get("title", "").strip(),
            "url": raw.get("url", ""),
            "source": f"Web: {domain}",
            "published_at": raw.get("published_at"),
            "content": truncate(strip_html(raw.get("content", "")), 1500),
        }


_source = WebScraperSource()


async def scrape_web(url: str) -> list[dict]:
    return await _source.collect(url=url)
