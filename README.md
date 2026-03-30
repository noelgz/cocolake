<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white" alt="Next.js 16" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white" alt="Tailwind CSS 4" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License" />
</p>

<h1 align="center">
  🐊 Cocolake
</h1>

<p align="center">
  <strong>Your daily data engineering news digest, curated with AI-assisted editing.</strong>
</p>

<p align="center">
  Cocolake collects, curates, and publishes a daily digest of the most relevant data engineering articles — from AWS blogs and Hacker News to GitHub trending repos — using deterministic source collection plus optional AI editing for ranking and bilingual summaries.
</p>

---

## Features

- **Deterministic Collection + AI Editing** — Every configured source is collected on each run, then optionally curated by Gemini
- **DB-Backed Source Registry** — Manage RSS, Hacker News, Dev.to, GitHub, and optional web scraper sources from PostgreSQL
- **Smart Categorization** — AWS, Data Engineering, Analytics, ML/AI, Open Source Tools, Case Studies
- **Bilingual Summaries** — Every article gets EN and ES summaries (LLM-generated or local fallback)
- **Freshness Guardrails** — Older articles are filtered or penalized before publication
- **Beautiful Dark UI** — Glassmorphism, animated gradients, skeleton loading, category-colored cards
- **Works Without AI** — Collects the same source pool and falls back to rule-based curation when no API key is set
- **Historical Navigation** — Browse past digests day by day
- **Zero Config Deploy** — Single `make run` builds and serves everything via Docker

## Demo

<p align="center">
  <img src="assets/Cocolake.gif" alt="Cocolake demo" width="900" />
</p>

## Architecture

<p align="center">
  <img src="assets/cocolake-arquitecture.svg" alt="Cocolake architecture" width="1000" />
</p>

**How the pipeline works:**

1. **Collection layer** fetches from every enabled RSS, Hacker News, Dev.to, GitHub, and optional web scraper source
2. **Editor step** either uses Gemini to select the top 15-20 and write bilingual summaries, or falls back to keyword-based ranking
3. **Repository layer** upserts curated articles, stores the daily digest in PostgreSQL, and the API exposes it to the frontend

Gemini 2.5 Flash is only used for the editorial step. If no API key is provided, the same collected article pool is still processed with rule-based curation — no LLM required.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (with Docker Compose)
- [Git](https://git-scm.com/)

That's it. No Python, no Node.js, no package managers needed locally.

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# App behavior
USE_LLM=true
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
LLM_CONTEXT_CONTENT_CHARS=700
LLM_CONTEXT_ARTICLE_LIMIT=25

# PostgreSQL
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_EXPOSE_PORT=5432
POSTGRES_DB=cocolake
POSTGRES_USER=cocolake
POSTGRES_PASSWORD=change-me

# Frontend -> API
API_PORT=8000
WEB_PORT=3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **No API key?** No problem. Set `USE_LLM=false` and Cocolake still collects every source, then uses rule-based curation instead of Gemini.
>
> **Running Python outside Docker?** Change `POSTGRES_HOST` from `db` to `localhost`, or set `DATABASE_URL` directly.

### 3. Run

```bash
make run
```

This will:
1. Build and run the pipeline (collects + curates articles)
2. Build and serve the frontend at **http://localhost:3000**

Open [http://localhost:3000](http://localhost:3000) and you're done.

## Commands

| Command | Description |
|---------|-------------|
| `make run` | Run pipeline + start web server |
| `make pipeline` | Only collect & curate articles |
| `make web` | Only start the web server |
| `make build` | Rebuild Docker images |
| `make clean` | Remove all containers, images & volumes |
| `make help` | Show all available commands |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | `""` | Google Gemini API key for editorial curation + bilingual summaries |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name used by the editor |
| `LLM_CONTEXT_CONTENT_CHARS` | `700` | Max content characters sent to Gemini for each article |
| `LLM_CONTEXT_ARTICLE_LIMIT` | `25` | Max number of collected articles sent to Gemini in one run |
| `USE_LLM` | `true` | Enable/disable AI editing (`false` = rule-based curation on the same collected pool) |
| `MAX_ARTICLE_AGE_DAYS` | `7` | Hard freshness limit before older articles are dropped |
| `MIN_ARTICLES_AFTER_FRESHNESS_FILTER` | `10` | Minimum articles to keep before relaxing the freshness filter |
| `POSTGRES_HOST` | `db` | PostgreSQL host used by API and pipeline |
| `POSTGRES_PORT` | `5432` | PostgreSQL port used by API and pipeline |
| `POSTGRES_EXPOSE_PORT` | `5432` | Host port published by Docker Compose |
| `POSTGRES_DB` | `cocolake` | PostgreSQL database name |
| `POSTGRES_USER` | `cocolake` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `change-me` | PostgreSQL password |
| `DATABASE_URL` | unset | Optional full override for the DB connection string |
| `API_PORT` | `8000` | Host port for the FastAPI service |
| `WEB_PORT` | `3000` | Host port for the web app |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API base URL baked into the frontend build |

## Project Structure

```
cocolake/
├── pipeline/                  # Python data pipeline
│   ├── main.py                # Entry point — orchestrates the pipeline
│   ├── agent.py               # Lightweight JSON agent wrapper used by the editor
│   ├── agents/
│   │   └── editor.py          # AI editor-in-chief for curation
│   ├── sources/
│   │   ├── rss.py             # RSS feed fetcher
│   │   ├── hackernews.py      # Hacker News search
│   │   ├── devto.py           # Dev.to article search
│   │   ├── github_trending.py # GitHub trending repos
│   │   └── web_scraper.py     # HTML/LLM fallback scraper
│   ├── llm.py                 # Gemini API wrapper
│   ├── config.py              # Pipeline settings and freshness constants
│   ├── Dockerfile
│   └── requirements.txt
├── common/                    # Shared backend modules used by API + pipeline
│   ├── source_plugins.py      # Single registry: config schema + runtime collector per source type
│   ├── db.py                  # Shared DB access
│   ├── repository.py          # Shared persistence layer
│   └── models.py              # Shared Pydantic models
├── api/                       # FastAPI service exposing digests + source management
├── web/                       # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx       # Main page with skeleton loading
│   │   │   └── globals.css    # Custom animations & glass effects
│   │   ├── components/
│   │   │   ├── Header.tsx     # Hero with animated stats & logo
│   │   │   ├── NewsCard.tsx   # Article cards with category colors
│   │   │   └── CategoryFilter.tsx
│   │   ├── i18n.ts            # Bilingual translations (EN/ES)
│   │   └── types.ts           # TypeScript interfaces
│   ├── nginx.conf             # Production server config
│   ├── Dockerfile             # Multi-stage: build → nginx
│   └── package.json
├── tests/                     # Focused regression tests for validation and pipeline helpers
├── docker-compose.yml         # DB + pipeline + API + web
├── Makefile                   # Developer shortcuts
└── .env                       # Your configuration (not committed)
```

## How It Works

### AI Editing (`USE_LLM=true`)

```
                  ┌──────────────────────────────┐
                  │ Deterministic Collection      │
                  │                               │
                  │  - RSS handler                │
                  │  - Hacker News handler        │
                  │  - Dev.to handler             │
                  │  - GitHub handler             │
                  │  - web_scraper handler        │
                  └──────────┬─────────────────────┘
                             │
                             ▼
                  ┌──────────────────────────────┐
                  │     Editor Agent              │
                  │     (single-shot reasoning)   │
                  │                               │
                  │  - Select top 15-20 articles  │
                  │  - Assign categories          │
                  │  - Score relevance (0-1)      │
                  │  - Write EN + ES summaries    │
                  │  - Add tags                   │
                  └───────────────────────────────┘
```

### Rule-Based Editing (`USE_LLM=false`)

When running without an API key, the pipeline still:
1. Fetches from all sources directly
2. Uses keyword matching to categorize articles into 6 categories
3. Scores based on keyword density plus freshness
4. Uses short raw-content extracts as summaries instead of LLM-written EN/ES summaries

### The Agent Framework

Cocolake includes a lightweight JSON agent wrapper (`pipeline/agent.py`) used for the editor step:

```python
from pipeline.agent import Agent

agent = Agent(
    name="Editor",
    instructions="Curate these raw articles into the daily digest...",
    tools=[],
    max_steps=3,
)

digest = await agent.run("Curate today's collected article pool", context=raw_articles)
```

The editor uses the same wrapper to return structured JSON, but without tool orchestration because article collection already happened upstream.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI** | Google Gemini 2.5 Flash (free tier) |
| **Agent Framework** | Custom JSON agent wrapper ([agent.py](pipeline/agent.py)) |
| **Backend** | Python 3.12, httpx, feedparser, Pydantic 2 |
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, TypeScript |
| **Serving** | nginx (static export) |
| **Infrastructure** | Docker Compose |

## Data Sources

| Source | What it collects |
|--------|-----------------|
| **RSS Feeds** | AWS Big Data, AWS Database, Snowflake, Databricks, dbt, Netflix Tech, Airbnb Engineering, Spotify Engineering, Data Engineering Weekly |
| **Hacker News** | Top stories matching data engineering queries |
| **Dev.to** | Community articles tagged `dataengineering`, `data` |
| **GitHub Trending** | Trending Python repositories in the data space |

## Development

### Running without Docker

**Pipeline:**

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pipeline.main
```

**Frontend:**

```bash
cd web
npm install
npm run dev
# → http://localhost:3000
```

### Adding a New Source

If you want to add another source of an existing type like `rss`, `devto`, or `github`, you do not need code changes. Add it through the API or insert a new row in the `sources` table.

If you want to add a brand-new source type:

1. Create `pipeline/sources/your_source.py`
2. Implement an async collector that returns standardized article dicts:

```python
async def search_your_source(query: str) -> list[dict]:
    # Return list of dicts with: title, url, source, published_at, content
    ...
```

3. Add its config schema and collector to `common/source_plugins.py`

That is enough for the pipeline and API to recognize the new type.

### Adding a New Category

1. Add keywords to `_CATEGORY_KEYWORDS` in `pipeline/main.py`
2. Add the category to the Editor instructions in `pipeline/agents/editor.py`
3. Add color maps in `web/src/components/NewsCard.tsx` (`CATEGORY_GRADIENT`, `CATEGORY_ACCENT`, `CATEGORY_TAG`, `CATEGORY_GLOW`)
4. Add an icon in `web/src/app/page.tsx` (`CATEGORY_ICONS`)

## FAQ

<details>
<summary><strong>Can I run it on a schedule?</strong></summary>

Yes. If you want, set up a local cron job to run `make pipeline` every day:

```bash
# Run every day at 7 AM
0 7 * * * cd /path/to/cocolake && make pipeline
```

</details>

<details>
<summary><strong>How much does the Gemini API cost?</strong></summary>

Nothing. Cocolake uses [Gemini 2.5 Flash](https://ai.google.dev/pricing) which has a generous free tier. A typical daily run uses ~2-3 API calls.

</details>

<details>
<summary><strong>Can I add my own RSS feeds?</strong></summary>

Yes. Add a new source row through the API or directly in the `sources` table with `source_type="rss"` and a config like `{"url": "https://myblog.com/feed.xml"}`.

</details>

<details>
<summary><strong>How do I change the language?</strong></summary>

The UI detects your browser language automatically (`navigator.language`). You can also toggle manually with the button in the top-right corner.

</details>

<details>
<summary><strong>I see errors in my IDE but it builds fine</strong></summary>

If you haven't run `npm install` locally in `web/`, your IDE will show missing module errors. This is expected — the project builds inside Docker. Run `cd web && npm install` if you want local IDE support.

</details>

## License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with 🐊 for data teams
  <br/>
  <sub>Powered by deterministic collection and optional Gemini editing</sub>
</p>
