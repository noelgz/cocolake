from __future__ import annotations

import os

# Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
LLM_CONTEXT_CONTENT_CHARS = int(os.getenv("LLM_CONTEXT_CONTENT_CHARS", "700"))
LLM_CONTEXT_ARTICLE_LIMIT = int(os.getenv("LLM_CONTEXT_ARTICLE_LIMIT", "25"))

# Pipeline settings
MAX_ARTICLES_FINAL = int(os.getenv("MAX_ARTICLES_FINAL", "20"))
MAX_ARTICLE_AGE_DAYS = int(os.getenv("MAX_ARTICLE_AGE_DAYS", "7"))
MIN_ARTICLES_AFTER_FRESHNESS_FILTER = int(
    os.getenv("MIN_ARTICLES_AFTER_FRESHNESS_FILTER", "10")
)
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
HTTP_HEADERS = {
    "User-Agent": "Cocolake/1.0",
    "Accept": "text/html,application/xml,*/*",
}
