from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["BaseArticle", "Article", "DailyDigest"]


class BaseArticle(BaseModel):
    """Fields every article step needs"""

    title: str
    url: str
    source: str
    published_at: str | None = None


class Article(BaseArticle):
    """A ready article with summaries and score"""

    category: str = "Data Engineering"
    summary_en: str = ""
    summary_es: str = ""
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class DailyDigest(BaseModel):
    """The full daily digest"""

    date: str
    generated_at: str
    total_sources_checked: int = 0
    total_raw_collected: int = 0
    total_published: int = 0
    articles: list[Article]
