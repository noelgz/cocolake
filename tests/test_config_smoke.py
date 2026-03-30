from __future__ import annotations

import os
import unittest
from unittest.mock import patch

try:
    from common.source_plugins import SUPPORTED_SOURCE_TYPES, validate_source_config
except ModuleNotFoundError:
    SUPPORTED_SOURCE_TYPES = ()
    validate_source_config = None

try:
    from common import db
except ModuleNotFoundError:
    db = None


class ConfigSmokeTests(unittest.TestCase):
    def test_supported_source_types_match_expected_set(self):
        if not SUPPORTED_SOURCE_TYPES:
            self.skipTest("pydantic is not installed in this local environment")
        self.assertEqual(
            set(SUPPORTED_SOURCE_TYPES),
            {"rss", "hackernews", "devto", "github", "web_scraper"},
        )

    def test_validate_source_config_rejects_bad_rss_config(self):
        if validate_source_config is None:
            self.skipTest("pydantic is not installed in this local environment")
        with self.assertRaises(ValueError):
            validate_source_config("rss", {})

    def test_database_url_uses_explicit_value_when_present(self):
        if db is None:
            self.skipTest("asyncpg is not installed in this local environment")
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://demo:demo@host:5432/demo"}, clear=False):
            self.assertEqual(
                db._build_database_url(),
                "postgresql://demo:demo@host:5432/demo",
            )

    def test_database_url_can_be_built_from_parts(self):
        if db is None:
            self.skipTest("asyncpg is not installed in this local environment")
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "",
                "POSTGRES_HOST": "db",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "news",
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass",
            },
            clear=False,
        ):
            self.assertEqual(
                db._build_database_url(),
                "postgresql://user:pass@db:5432/news",
            )


if __name__ == "__main__":
    unittest.main()
