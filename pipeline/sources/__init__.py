"""Source collectors from one simple place"""

from common.source_plugins import SOURCE_PLUGINS, collect_source
from pipeline.sources.rss import fetch_rss_feed, fetch_rss_feeds
from pipeline.sources.hackernews import search_hackernews
from pipeline.sources.devto import search_devto
from pipeline.sources.github_trending import search_github
from pipeline.sources.web_scraper import scrape_web

__all__ = [
    "SOURCE_PLUGINS",
    "collect_source",
    "fetch_rss_feed",
    "fetch_rss_feeds",
    "search_hackernews",
    "search_devto",
    "search_github",
    "scrape_web",
]
