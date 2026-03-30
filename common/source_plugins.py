from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Awaitable, Callable

from pydantic import BaseModel, ConfigDict, HttpUrl, StringConstraints, ValidationError

SourceType = str
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RSSConfig(_ConfigModel):
    url: HttpUrl


class HackerNewsConfig(_ConfigModel):
    query: NonEmptyStr


class DevtoConfig(_ConfigModel):
    tag: NonEmptyStr


class GitHubConfig(_ConfigModel):
    language: NonEmptyStr


class WebScraperConfig(_ConfigModel):
    url: HttpUrl


SourceCollector = Callable[[dict], Awaitable[list[dict]]]


@dataclass(frozen=True)
class SourcePlugin:
    """Everything the app needs for one source type!"""

    config_model: type[_ConfigModel]
    collector: SourceCollector


async def _collect_rss(source: dict) -> list[dict]:
    # Keep this import here so the API can use this file
    # without loading every pipeline collector too early
    from pipeline.sources.rss import fetch_rss_feed

    return await fetch_rss_feed(
        feed_name=source["name"],
        url=source["config"]["url"],
    )


async def _collect_hackernews(source: dict) -> list[dict]:
    from pipeline.sources.hackernews import search_hackernews

    return await search_hackernews(source["config"]["query"])


async def _collect_devto(source: dict) -> list[dict]:
    from pipeline.sources.devto import search_devto

    return await search_devto(source["config"]["tag"])


async def _collect_github(source: dict) -> list[dict]:
    from pipeline.sources.github_trending import search_github

    return await search_github(source["config"]["language"])


async def _collect_web_scraper(source: dict) -> list[dict]:
    from pipeline.sources.web_scraper import scrape_web

    return await scrape_web(source["config"]["url"])


SOURCE_PLUGINS: dict[str, SourcePlugin] = {
    "rss": SourcePlugin(
        config_model=RSSConfig,
        collector=_collect_rss,
    ),
    "hackernews": SourcePlugin(
        config_model=HackerNewsConfig,
        collector=_collect_hackernews,
    ),
    "devto": SourcePlugin(
        config_model=DevtoConfig,
        collector=_collect_devto,
    ),
    "github": SourcePlugin(
        config_model=GitHubConfig,
        collector=_collect_github,
    ),
    "web_scraper": SourcePlugin(
        config_model=WebScraperConfig,
        collector=_collect_web_scraper,
    ),
}

SUPPORTED_SOURCE_TYPES = tuple(SOURCE_PLUGINS.keys())

__all__ = [
    "SourceType",
    "SUPPORTED_SOURCE_TYPES",
    "SOURCE_PLUGINS",
    "SourcePlugin",
    "collect_source",
    "get_source_plugin",
    "validate_source_config",
]


def get_source_plugin(source_type: str) -> SourcePlugin:
    plugin = SOURCE_PLUGINS.get(source_type)
    if plugin is None:
        supported = ", ".join(SUPPORTED_SOURCE_TYPES)
        raise ValueError(
            f"unsupported source_type '{source_type}'. Expected one of: {supported}"
        )
    return plugin


def validate_source_config(source_type: str, config: dict | None) -> dict:
    """Check and clean the config for one source type"""
    plugin = get_source_plugin(source_type)

    try:
        validated = plugin.config_model.model_validate(config or {})
    except ValidationError as exc:
        messages = "; ".join(err["msg"] for err in exc.errors())
        raise ValueError(
            f"invalid config for source_type '{source_type}': {messages}"
        ) from exc

    return validated.model_dump(mode="json")


async def collect_source(source: dict) -> list[dict]:
    """Collect articles for one checked source row"""
    plugin = get_source_plugin(source["source_type"])
    return await plugin.collector(source)
