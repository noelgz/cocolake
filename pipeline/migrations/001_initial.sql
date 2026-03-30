-- Sources table from the old sources.toml idea
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    source_type VARCHAR(50)  NOT NULL,  -- rss, hackernews, devto, github, web_scraper
    config      JSONB        NOT NULL DEFAULT '{}',
    enabled     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Articles table with one row per URL
CREATE TABLE IF NOT EXISTS articles (
    id              SERIAL PRIMARY KEY,
    url             VARCHAR(2048) NOT NULL UNIQUE,
    title           VARCHAR(1024) NOT NULL,
    source_id       INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    source_name     VARCHAR(255)  NOT NULL,
    published_at    TIMESTAMPTZ,
    raw_content     TEXT,
    category        VARCHAR(100)  NOT NULL DEFAULT 'Data Engineering',
    summary_en      TEXT          NOT NULL DEFAULT '',
    summary_es      TEXT          NOT NULL DEFAULT '',
    relevance_score FLOAT         NOT NULL DEFAULT 0.5
        CHECK (relevance_score BETWEEN 0 AND 1),
    tags            TEXT[]        NOT NULL DEFAULT '{}',
    first_seen_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_articles_url        ON articles (url);
CREATE INDEX IF NOT EXISTS idx_articles_first_seen ON articles (first_seen_at);
CREATE INDEX IF NOT EXISTS idx_articles_category   ON articles (category);
CREATE INDEX IF NOT EXISTS idx_articles_source     ON articles (source_id);

-- One digest per day
CREATE TABLE IF NOT EXISTS digests (
    id                    SERIAL PRIMARY KEY,
    date                  DATE        NOT NULL UNIQUE,
    generated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_sources_checked INTEGER     NOT NULL DEFAULT 0,
    total_raw_collected   INTEGER     NOT NULL DEFAULT 0,
    total_published       INTEGER     NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_digests_date ON digests (date);

-- Which articles belong to each digest
CREATE TABLE IF NOT EXISTS digest_articles (
    digest_id  INTEGER NOT NULL REFERENCES digests(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    position   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (digest_id, article_id)
);
