from __future__ import annotations

import unittest
from unittest.mock import patch

import pipeline.main as pipeline_main


class EditorContextTests(unittest.TestCase):
    def test_context_truncates_each_article_content(self):
        articles = [
            {
                "title": "One",
                "url": "https://example.com/1",
                "source": "RSS: Example",
                "content": "a" * 900,
            }
        ]

        with patch.object(pipeline_main, "LLM_CONTEXT_CONTENT_CHARS", 700), patch.object(
            pipeline_main, "LLM_CONTEXT_ARTICLE_LIMIT", 25
        ):
            context = pipeline_main._build_editor_context(articles)

        self.assertEqual(len(context), 1)
        self.assertEqual(len(context[0]["content"]), 701)
        self.assertTrue(context[0]["content"].endswith("…"))

    def test_context_limits_how_many_articles_go_to_llm(self):
        articles = [
            {
                "title": f"Article {index}",
                "url": f"https://example.com/{index}",
                "source": "RSS: Example",
                "content": "short text",
            }
            for index in range(40)
        ]

        with patch.object(pipeline_main, "LLM_CONTEXT_ARTICLE_LIMIT", 25):
            context = pipeline_main._build_editor_context(articles)

        self.assertEqual(len(context), 25)
        self.assertEqual(context[0]["title"], "Article 0")
        self.assertEqual(context[-1]["title"], "Article 24")

    def test_context_keeps_source_diversity_before_picking_more_from_one_source(self):
        articles = [
            {
                "title": "Alpha 1",
                "url": "https://example.com/a1",
                "source": "RSS: Alpha",
                "content": "spark kafka airflow",
            },
            {
                "title": "Alpha 2",
                "url": "https://example.com/a2",
                "source": "RSS: Alpha",
                "content": "spark kafka airflow",
            },
            {
                "title": "Beta 1",
                "url": "https://example.com/b1",
                "source": "RSS: Beta",
                "content": "spark kafka airflow",
            },
            {
                "title": "Gamma 1",
                "url": "https://example.com/c1",
                "source": "RSS: Gamma",
                "content": "spark kafka airflow",
            },
        ]

        with patch.object(pipeline_main, "LLM_CONTEXT_ARTICLE_LIMIT", 3):
            context = pipeline_main._build_editor_context(articles)

        self.assertEqual(len(context), 3)
        self.assertEqual(
            {article["source"] for article in context},
            {"RSS: Alpha", "RSS: Beta", "RSS: Gamma"},
        )


if __name__ == "__main__":
    unittest.main()
