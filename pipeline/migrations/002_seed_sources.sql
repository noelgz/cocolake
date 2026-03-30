INSERT INTO sources (name, source_type, config) VALUES
    -- RSS feeds
    ('AWS Big Data Blog',       'rss', '{"url": "https://aws.amazon.com/blogs/big-data/feed/"}'),
    ('AWS Database Blog',       'rss', '{"url": "https://aws.amazon.com/blogs/database/feed/"}'),
    ('Snowflake Blog',          'rss', '{"url": "https://www.snowflake.com/feed/"}'),
    ('Databricks Blog',         'rss', '{"url": "https://www.databricks.com/feed"}'),
    ('dbt Blog',                'rss', '{"url": "https://www.getdbt.com/blog/rss.xml"}'),
    ('Netflix Tech Blog',       'rss', '{"url": "https://medium.com/feed/netflix-techblog"}'),
    ('Airbnb Tech Blog',        'rss', '{"url": "https://medium.com/feed/airbnb-engineering"}'),
    ('Spotify Engineering',     'rss', '{"url": "https://engineering.atspotify.com/feed/"}'),
    ('Data Engineering Weekly', 'rss', '{"url": "https://www.dataengineeringweekly.com/feed"}'),
    -- Hacker News
    ('HN: data engineering',         'hackernews', '{"query": "data engineering"}'),
    ('HN: spark/kafka/flink',        'hackernews', '{"query": "apache spark OR kafka OR flink"}'),
    -- Dev.to
    ('Dev.to: dataengineering', 'devto', '{"tag": "dataengineering"}'),
    ('Dev.to: data',            'devto', '{"tag": "data"}'),
    -- GitHub Trending
    ('GitHub Trending: Python', 'github', '{"language": "python"}')
ON CONFLICT (name) DO NOTHING;
