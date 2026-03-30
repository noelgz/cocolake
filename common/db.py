from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote_plus

import asyncpg

logger = logging.getLogger(__name__)
__all__ = ["DATABASE_URL", "MIGRATIONS_DIR", "get_pool", "close_pool", "run_migrations"]

_pool: asyncpg.Pool | None = None
_MIGRATION_LOCK_ID = 26032401


def _build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    host = os.getenv("POSTGRES_HOST", "localhost").strip() or "localhost"
    port = os.getenv("POSTGRES_PORT", "5432").strip() or "5432"
    database = os.getenv("POSTGRES_DB", "cocolake").strip() or "cocolake"
    user = quote_plus(os.getenv("POSTGRES_USER", "cocolake"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", "cocolake"))

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


DATABASE_URL = _build_database_url()

MIGRATIONS_DIR = Path(__file__).parent.parent / "pipeline" / "migrations"


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        logger.info("Database pool created")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def run_migrations() -> None:
    pool = await get_pool()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    async with pool.acquire() as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                   filename TEXT PRIMARY KEY,
                   applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
               )"""
        )
        await conn.fetchval("SELECT pg_advisory_lock($1)", _MIGRATION_LOCK_ID)
        try:
            rows = await conn.fetch("SELECT filename FROM schema_migrations")
            applied = {row["filename"] for row in rows}

            applied_now = 0
            for sql_file in migration_files:
                if sql_file.name in applied:
                    logger.info("Skipping migration: %s (already applied)", sql_file.name)
                    continue

                logger.info("Running migration: %s", sql_file.name)
                sql = sql_file.read_text()
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES ($1)",
                        sql_file.name,
                    )
                applied_now += 1
        finally:
            await conn.fetchval("SELECT pg_advisory_unlock($1)", _MIGRATION_LOCK_ID)

    logger.info("Migrations complete (%d new, %d total)", applied_now, len(migration_files))
